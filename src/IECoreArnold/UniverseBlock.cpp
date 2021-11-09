//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
//
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//
//     * Redistributions of source code must retain the above copyright
//       notice, this list of conditions and the following disclaimer.
//
//     * Redistributions in binary form must reproduce the above copyright
//       notice, this list of conditions and the following disclaimer in the
//       documentation and/or other materials provided with the distribution.
//
//     * Neither the name of Image Engine Design nor the names of any
//       other contributors to this software may be used to endorse or
//       promote products derived from this software without specific prior
//       written permission.
//
//  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
//  IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
//  THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
//  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
//  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
//  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
//  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
//  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
//  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
//  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
//  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
//
//////////////////////////////////////////////////////////////////////////

#include "IECoreArnold/UniverseBlock.h"

#include "IECore/Exception.h"
#include "IECore/MessageHandler.h"

#include "boost/filesystem/operations.hpp"
#include "boost/tokenizer.hpp"

#include "ai_metadata.h"
#include "ai_msg.h"
#include "ai_plugins.h"
#include "ai_render.h"
#include "ai_universe.h"

#include "tbb/spin_mutex.h"

using namespace IECore;
using namespace IECoreArnold;

#if ARNOLD_VERSION_NUM >= 70000
#define IECOREARNOLD_MULTIPLE_UNIVERSES
#endif

namespace
{

void loadMetadata( const std::string &pluginPaths )
{
	typedef boost::tokenizer<boost::char_separator<char> > Tokenizer;
	#ifdef _WIN32
		const char *separator = ";";
	#else
		const char *separator = ":";
	#endif
	Tokenizer t( pluginPaths, boost::char_separator<char>( separator ) );
	for( Tokenizer::const_iterator it = t.begin(), eIt = t.end(); it != eIt; ++it )
	{
		try
		{
			for( boost::filesystem::recursive_directory_iterator dIt( *it ), deIt; dIt != deIt; ++dIt )
			{
				if( dIt->path().extension() == ".mtd" )
				{
					if( !AiMetaDataLoadFile( dIt->path().string().c_str() ) )
					{
						throw IECore::Exception( boost::str( boost::format( "Failed to load \"%s\"" ) % dIt->path().string() ) );
					}
				}
			}
		}
		catch( const std::exception &e )
		{
			IECore::msg( IECore::Msg::Debug, "UniverseBlock", e.what() );
		}
	}
}

void begin()
{
	// Default to logging errors / warnings only - we may not even be using this universe block to perform a render,
	// we might just be loading some shader metadata or something, so we don't want to be dumping lots of
	// unnecessary output.
#ifdef IECOREARNOLD_MULTIPLE_UNIVERSES
	AiMsgSetConsoleFlags( nullptr, AI_LOG_ERRORS | AI_LOG_WARNINGS );
#else
	AiMsgSetConsoleFlags( AI_LOG_ERRORS | AI_LOG_WARNINGS );
#endif

	AiBegin();

	const char *pluginPaths = getenv( "ARNOLD_PLUGIN_PATH" );
	if( pluginPaths )
	{
		AiLoadPlugins( pluginPaths );
		loadMetadata( pluginPaths );
	}
}

#ifdef IECOREARNOLD_MULTIPLE_UNIVERSES

class ArnoldAPIScope
{
	public :

		ArnoldAPIScope()
			:	m_sharedUniverse( nullptr )
		{
			begin();
		}

		~ArnoldAPIScope()
		{
			if( m_sharedUniverse )
			{
				AiUniverseDestroy( m_sharedUniverse );
			}
			AiEnd();
		}

		/// \todo This can probably be removed in future. Non-writable
		/// UniverseBlock users really just want `AiBegin()` to have been called
		/// so they can query plugins, and they don't need an actual universe at
		/// all. We just make one so we can implement the original UniverseBlock
		/// semantics.
		AtUniverse *sharedUniverse()
		{
			if( !m_sharedUniverse )
			{
				m_sharedUniverse = AiUniverse();
			}
			return m_sharedUniverse;
		}

	private :

		AtUniverse *m_sharedUniverse;
};

static ArnoldAPIScope g_apiScope;

#else

tbb::spin_mutex g_mutex;
int g_count = 0;
bool g_haveWriter = false;

#endif

} // namespace

UniverseBlock::UniverseBlock( bool writable )
	:	m_writable( writable )
{
#ifdef IECOREARNOLD_MULTIPLE_UNIVERSES
	m_universe = m_writable ? AiUniverse() : g_apiScope.sharedUniverse();
#else
	// Careful management of the default universe, so that there
	// can be multiple readers but only one writer.
	tbb::spin_mutex::scoped_lock lock( g_mutex );

	if( writable )
	{
		if( g_haveWriter )
		{
			throw IECore::Exception( "Arnold is already in use" );
		}
		else
		{
			g_haveWriter = true;
		}
	}
	m_universe = nullptr;

	g_count++;
	if( AiUniverseIsActive() )
	{
		return;
	}

	begin();
#endif
}

UniverseBlock::~UniverseBlock()
{
#ifdef IECOREARNOLD_MULTIPLE_UNIVERSES
	if( m_writable )
	{
		AiUniverseDestroy( m_universe );
	}
#else
	tbb::spin_mutex::scoped_lock lock( g_mutex );

	g_count--;
	if( m_writable )
	{
		g_haveWriter = false;
		// We _must_ call AiEnd() to clean up ready
		// for the next writer, regardless of whether
		// or not readers still exist.
		AiEnd();
		if( g_count )
		{
			// If readers do exist, restart the universe.
			// This is not threadsafe, since a reader on
			// another thread could be making Ai calls
			// in between shutdown and startup. But it is
			// the best we can do given that Arnold has
			// only one universe. The alternative is to
			// only shutdown when g_count reaches 0, but
			// then a long-lived reader can cause Arnold
			// state to be carried over from one writer
			// to the next.
			begin();
		}
	}
#endif
}
