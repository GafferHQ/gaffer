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

#include "GafferArnold/InteractiveArnoldRender.h"

#include "boost/unordered_set.hpp"

#include "ai_universe.h"

using namespace Gaffer;
using namespace GafferScene;
using namespace GafferArnold;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

using InstanceSet = boost::unordered_set<InteractiveArnoldRender *>;
InstanceSet &instances()
{
	static InstanceSet i;
	return i;
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// InteractiveArnoldRender
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( InteractiveArnoldRender );

InteractiveArnoldRender::InteractiveArnoldRender( const std::string &name )
	:	InteractiveRender( "Arnold", name )
{
	instances().insert( this );
}

InteractiveArnoldRender::~InteractiveArnoldRender()
{
	instances().erase( this );
}

void InteractiveArnoldRender::flushCaches( int flags )
{
	/// \todo Perhaps this makes more sense as a non-static method
	/// that can be called directly on individual instances?
	bool flushed = false;
	for( const auto &instance : instances() )
	{
		IntPlug *statePlug = instance->statePlug()->source<IntPlug>();
		if( !statePlug->settable() )
		{
			continue;
		}

		if( !instance->renderer() )
		{
			continue;
		}

		const State state = (InteractiveRender::State)statePlug->getValue();
		statePlug->setValue( Paused );

		instance->renderer()->command( "ai:cacheFlush", { { "flags", new IECore::IntData( flags ) } } );

		statePlug->setValue( state );

		flushed = true;
	}

	if( !flushed )
	{
		// No renderer or instance found so flush default cache so that new renders spinning up
		// later will see a refereshed texture cache.
		// This is needed because Arnold only has one texture cache between universes.
		AiUniverseCacheFlush( nullptr, flags );
	}
}
