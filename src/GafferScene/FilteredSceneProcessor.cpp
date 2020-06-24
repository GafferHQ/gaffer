//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

#include "GafferScene/FilteredSceneProcessor.h"

#include "Gaffer/Context.h"

using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( FilteredSceneProcessor );

size_t FilteredSceneProcessor::g_firstPlugIndex = 0;

FilteredSceneProcessor::FilteredSceneProcessor( const std::string &name, IECore::PathMatcher::Result filterDefault )
	:	SceneProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new FilterPlug( "filter", Plug::In, filterDefault, IECore::PathMatcher::NoMatch, IECore::PathMatcher::EveryMatch, Plug::Default ) );
}

FilteredSceneProcessor::FilteredSceneProcessor( const std::string &name, size_t minInputs, size_t maxInputs )
	:	SceneProcessor( name, minInputs, maxInputs )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new FilterPlug( "filter", Plug::In, PathMatcher::NoMatch, PathMatcher::NoMatch, PathMatcher::EveryMatch, Plug::Default ) );
}

FilteredSceneProcessor::~FilteredSceneProcessor()
{
}

FilterPlug *FilteredSceneProcessor::filterPlug()
{
	return getChild<FilterPlug>( g_firstPlugIndex );
}

const FilterPlug *FilteredSceneProcessor::filterPlug() const
{
	return getChild<FilterPlug>( g_firstPlugIndex );
}

void FilteredSceneProcessor::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	SceneProcessor::affects( input, outputs );

	const ScenePlug *scenePlug = input->parent<ScenePlug>();
	if( scenePlug && scenePlug == inPlug() )
	{
		// We'll be passing this scene to the filter when we
		// call `filterValue()`, so we must give the filter
		// a chance to dirty any of its plugs that depend on
		// the scene.
		filterPlug()->sceneAffects( input, outputs );
	}
}

void FilteredSceneProcessor::filterHash( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	FilterPlug::SceneScope sceneScope( context, inPlug() );
	filterPlug()->hash( h );
}

IECore::PathMatcher::Result FilteredSceneProcessor::filterValue( const Gaffer::Context *context ) const
{
	FilterPlug::SceneScope sceneScope( context, inPlug() );
	return (IECore::PathMatcher::Result)filterPlug()->getValue();
}
