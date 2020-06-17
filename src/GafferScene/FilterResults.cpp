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

#include "GafferScene/FilterResults.h"

#include "GafferScene/Filter.h"
#include "GafferScene/SceneAlgo.h"
#include "GafferScene/ScenePlug.h"

using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

size_t FilterResults::g_firstPlugIndex = 0;

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( FilterResults )

FilterResults::FilterResults( const std::string &name )
	:	ComputeNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ScenePlug( "scene" ) );
	addChild( new FilterPlug( "filter" ) );
	addChild( new PathMatcherDataPlug( "__internalOut", Gaffer::Plug::Out, new PathMatcherData ) );
	addChild( new PathMatcherDataPlug( "out", Gaffer::Plug::Out, new PathMatcherData ) );
}

FilterResults::~FilterResults()
{
}

ScenePlug *FilterResults::scenePlug()
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

const ScenePlug *FilterResults::scenePlug() const
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

FilterPlug *FilterResults::filterPlug()
{
	return getChild<FilterPlug>( g_firstPlugIndex + 1 );
}

const FilterPlug *FilterResults::filterPlug() const
{
	return getChild<FilterPlug>( g_firstPlugIndex + 1 );
}

Gaffer::PathMatcherDataPlug *FilterResults::internalOutPlug()
{
	return getChild<PathMatcherDataPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::PathMatcherDataPlug *FilterResults::internalOutPlug() const
{
	return getChild<PathMatcherDataPlug>( g_firstPlugIndex + 2 );
}

Gaffer::PathMatcherDataPlug *FilterResults::outPlug()
{
	return getChild<PathMatcherDataPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::PathMatcherDataPlug *FilterResults::outPlug() const
{
	return getChild<PathMatcherDataPlug>( g_firstPlugIndex + 3 );
}

void FilterResults::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ComputeNode::affects( input, outputs );

	const ScenePlug *scenePlug = input->parent() == this->scenePlug() ? this->scenePlug() : nullptr;
	if( scenePlug )
	{
		if( filterPlug()->sceneAffectsMatch( scenePlug, static_cast<const ValuePlug *>( input ) ) )
		{
			outputs.push_back( filterPlug() );
		}
	}

	if(
		input == filterPlug() ||
		( scenePlug && input == scenePlug->childNamesPlug() )
	)
	{
		outputs.push_back( internalOutPlug() );
	}

	if( input == internalOutPlug() )
	{
		outputs.push_back( outPlug() );
	}
}

void FilterResults::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ComputeNode::hash( output, context, h );

	if( output == internalOutPlug() )
	{
		PathMatcherDataPtr data = new PathMatcherData;
		SceneAlgo::matchingPaths( filterPlug(), scenePlug(), data->writable() );
		data->hash( h );
	}
	else if( output == outPlug() )
	{
		ScenePlug::GlobalScope globalScope( context );
		globalScope.remove( SceneAlgo::historyIDContextName() );
		internalOutPlug()->hash( h );
	}
}

void FilterResults::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output == internalOutPlug() )
	{
		PathMatcherDataPtr data = new PathMatcherData;
		SceneAlgo::matchingPaths( filterPlug(), scenePlug(), data->writable() );
		static_cast<PathMatcherDataPlug *>( output )->setValue( data );
		return;
	}
	else if( output == outPlug() )
	{
		ScenePlug::GlobalScope globalScope( context );
		globalScope.remove( SceneAlgo::historyIDContextName() );
		output->setFrom( internalOutPlug() );
		return;
	}

	ComputeNode::compute( output, context );
}

Gaffer::ValuePlug::CachePolicy FilterResults::computeCachePolicy( const Gaffer::ValuePlug *output ) const
{
	if( output == internalOutPlug() )
	{
		return ValuePlug::CachePolicy::TaskCollaboration;
	}
	return ComputeNode::computeCachePolicy( output );
}

Gaffer::ValuePlug::CachePolicy FilterResults::hashCachePolicy( const Gaffer::ValuePlug *output ) const
{
	if( output == internalOutPlug() )
	{
		return ValuePlug::CachePolicy::TaskCollaboration;
	}
	return ComputeNode::hashCachePolicy( output );
}
