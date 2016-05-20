
//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
//
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//
//      * Redistributions of source code must retain the above
//        copyright notice, this list of conditions and the following
//        disclaimer.
//
//      * Redistributions in binary form must reproduce the above
//        copyright notice, this list of conditions and the following
//        disclaimer in the documentation and/or other materials provided with
//        the distribution.
//
//      * Neither the name of John Haddon nor the names of
//        any other contributors to this software may be used to endorse or
//        promote products derived from this software without specific prior
//        written permission.
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

#include "boost/algorithm/string/predicate.hpp"

#include "GafferScene/Preview/RendererAlgo.h"

using namespace IECore;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
///////////////////////////////////////////////////////////////////////////

namespace
{

const std::string g_optionPrefix( "option:" );
const IECore::InternedString g_cameraOptionLegacyName( "option:render:camera" );
const IECore::InternedString g_resolutionOptionLegacyName( "option:render:resolution" );
const IECore::InternedString g_pixelAspectRatioOptionLegacyName( "option:pixelAspectRatio:resolution" );
const IECore::InternedString g_cropWindowOptionLegacyName( "option:cropWindow:resolution" );

IECore::InternedString optionName( const IECore::InternedString &globalsName )
{
	if(
		globalsName == g_cameraOptionLegacyName ||
		globalsName == g_resolutionOptionLegacyName ||
		globalsName == g_pixelAspectRatioOptionLegacyName ||
		globalsName == g_cropWindowOptionLegacyName
	)
	{
		/// \todo Just rename the options themselves in StandardOptions and remove this?
		return globalsName.string().substr( g_optionPrefix.size() + 7 );
	}

	return globalsName.string().substr( g_optionPrefix.size() );
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// Implementation of public API
//////////////////////////////////////////////////////////////////////////

namespace GafferScene
{

namespace Preview
{

void outputOptions( const IECore::CompoundObject *globals, IECoreScenePreview::Renderer *renderer )
{
	outputOptions( globals, /* previousGlobals = */ NULL, renderer );
}

void outputOptions( const IECore::CompoundObject *globals, const IECore::CompoundObject *previousGlobals, IECoreScenePreview::Renderer *renderer )
{
	// Output anything that has changed or was added since last time.

	CompoundObject::ObjectMap::const_iterator it, eIt;
	for( it = globals->members().begin(), eIt = globals->members().end(); it != eIt; ++it )
	{
		if( !boost::starts_with( it->first.string(), g_optionPrefix ) )
		{
			continue;
		}
		if( const Data *data = runTimeCast<Data>( it->second.get() ) )
		{
			bool changedOrAdded = true;
			if( previousGlobals )
			{
				if( const Data *previousData = previousGlobals->member<Data>( it->first ) )
				{
					changedOrAdded = *previousData != *data;
				}
			}
			if( changedOrAdded )
			{
				renderer->option( optionName( it->first ), data );
			}
		}
		else
		{
			throw IECore::Exception( "Global \"" + it->first.string() + "\" is not an IECore::Data" );
		}
	}

	// Remove anything that has been removed since last time.

	if( !previousGlobals )
	{
		return;
	}

	for( it = previousGlobals->members().begin(), eIt = previousGlobals->members().end(); it != eIt; ++it )
	{
		if( !boost::starts_with( it->first.string(), g_optionPrefix ) )
		{
			continue;
		}
		if( runTimeCast<Data>( it->second.get() ) )
		{
			if( !globals->member<Data>( it->first ) )
			{
				renderer->option( optionName( it->first ), NULL );
			}
		}
	}
}

void outputOutputs( const IECore::CompoundObject *globals, IECoreScenePreview::Renderer *renderer )
{
	outputOutputs( globals, /* previousGlobals = */ NULL, renderer );
}

void outputOutputs( const IECore::CompoundObject *globals, const IECore::CompoundObject *previousGlobals, IECoreScenePreview::Renderer *renderer )
{
	static const std::string prefix( "output:" );

	// Output anything that has changed or was added since last time.

	CompoundObject::ObjectMap::const_iterator it, eIt;
	for( it = globals->members().begin(), eIt = globals->members().end(); it != eIt; ++it )
	{
		if( !boost::starts_with( it->first.string(), prefix ) )
		{
			continue;
		}
		if( const Display *display = runTimeCast<Display>( it->second.get() ) )
		{
			bool changedOrAdded = true;
			if( previousGlobals )
			{
				if( const Display *previousDisplay = previousGlobals->member<Display>( it->first ) )
				{
					changedOrAdded = *previousDisplay != *display;
				}
			}
			if( changedOrAdded )
			{
				renderer->output( it->first.string().substr( prefix.size() ), display );
			}
		}
		else
		{
			throw IECore::Exception( "Global \"" + it->first.string() + "\" is not an IECore::Display" );
		}
	}

	// Remove anything that has been removed since last time.

	if( !previousGlobals )
	{
		return;
	}

	for( it = previousGlobals->members().begin(), eIt = previousGlobals->members().end(); it != eIt; ++it )
	{
		if( !boost::starts_with( it->first.string(), prefix ) )
		{
			continue;
		}
		if( runTimeCast<Display>( it->second.get() ) )
		{
			if( !globals->member<Display>( it->first ) )
			{
				renderer->output( it->first.string().substr( prefix.size() ), NULL );
			}
		}
	}
}

} // namespace Preview

} // namespace GafferScene
