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

#include "boost/tokenizer.hpp"

#include "ai_metadata.h"
#include "ai_msg.h"
#include "ai_plugins.h"
#include "ai_render.h"
#include "ai_universe.h"

#include "fmt/format.h"

#include <filesystem>

using namespace IECore;
using namespace IECoreArnold;

namespace
{

void loadMetadata( const std::string &pluginPaths )
{
	// Arnold issues warnings for non-existent nodes referenced in `.mtd` files,
	// which is very inconvenient if wanting to author metadata for use across
	// multiple Arnold versions. So we disable warnings while loading the metadata
	// and restore them at the end of this function.
	const int flags = AiMsgGetConsoleFlags( nullptr );
	AiMsgSetConsoleFlags( nullptr, AI_LOG_ERRORS );

	using Tokenizer = boost::tokenizer<boost::char_separator<char> >;
	#ifdef _WIN32
		const char *separator = ";";
	#else
		const char *separator = ":";
	#endif
	Tokenizer t( pluginPaths, boost::char_separator<char>( separator ) );
	for( const auto &pluginPath : t )
	{
		try
		{
			for( const auto &d : std::filesystem::recursive_directory_iterator( pluginPath ) )
			{
				if( d.path().extension() == ".mtd" )
				{
					if( !AiMetaDataLoadFile( d.path().string().c_str() ) )
					{
						throw IECore::Exception( fmt::format( "Failed to load \"{}\"", d.path().string() ) );
					}
				}
			}
		}
		catch( const std::exception &e )
		{
			IECore::msg( IECore::Msg::Debug, "UniverseBlock", e.what() );
		}
	}

	AiMsgSetConsoleFlags( nullptr, flags );
}

void begin()
{
	// Default to logging errors / warnings only - we may not even be using this universe block to perform a render,
	// we might just be loading some shader metadata or something, so we don't want to be dumping lots of
	// unnecessary output.
	AiMsgSetConsoleFlags( nullptr, AI_LOG_ERRORS | AI_LOG_WARNINGS );

	AiBegin();

	const char *pluginPaths = getenv( "ARNOLD_PLUGIN_PATH" );
	if( pluginPaths )
	{
		AiLoadPlugins( pluginPaths );
		loadMetadata( pluginPaths );
	}
}

class ArnoldAPIScope
{
	public :

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

		// Called to initalise the Arnold API on first use.
		// We then keep the API alive until shutdown, as
		// starting and stopping it has overhead we want to
		// avoid.
		static ArnoldAPIScope &acquire()
		{
			static ArnoldAPIScope g_apiScope;
			return g_apiScope;
		}

	private :

		ArnoldAPIScope()
			:	m_sharedUniverse( nullptr )
		{
			begin();
		}

		AtUniverse *m_sharedUniverse;
};

} // namespace

UniverseBlock::UniverseBlock( bool writable )
	:	m_writable( writable )
{
	ArnoldAPIScope &apiScope = ArnoldAPIScope::acquire();
	m_universe = m_writable ? AiUniverse() : apiScope.sharedUniverse();
}

UniverseBlock::~UniverseBlock()
{
	if( m_writable )
	{
		AiUniverseDestroy( m_universe );
	}
}
