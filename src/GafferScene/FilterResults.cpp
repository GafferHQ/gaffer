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

GAFFER_NODE_DEFINE_TYPE( FilterResults )

FilterResults::FilterResults( const std::string &name )
	:	ComputeNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ScenePlug( "scene" ) );
	addChild( new FilterPlug( "filter" ) );
	addChild( new StringPlug( "root" ) );
	addChild( new PathMatcherDataPlug( "__internalOut", Gaffer::Plug::Out, new PathMatcherData ) );
	addChild( new PathMatcherDataPlug( "out", Gaffer::Plug::Out, new PathMatcherData ) );
	addChild( new StringVectorDataPlug( "outStrings", Gaffer::Plug::Out, new StringVectorData ) );
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

Gaffer::StringPlug *FilterResults::rootPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::StringPlug *FilterResults::rootPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

Gaffer::PathMatcherDataPlug *FilterResults::internalOutPlug()
{
	return getChild<PathMatcherDataPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::PathMatcherDataPlug *FilterResults::internalOutPlug() const
{
	return getChild<PathMatcherDataPlug>( g_firstPlugIndex + 3 );
}

Gaffer::PathMatcherDataPlug *FilterResults::outPlug()
{
	return getChild<PathMatcherDataPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::PathMatcherDataPlug *FilterResults::outPlug() const
{
	return getChild<PathMatcherDataPlug>( g_firstPlugIndex + 4 );
}

Gaffer::StringVectorDataPlug *FilterResults::outStringsPlug()
{
	return getChild<StringVectorDataPlug>( g_firstPlugIndex + 5 );
}

const Gaffer::StringVectorDataPlug *FilterResults::outStringsPlug() const
{
	return getChild<StringVectorDataPlug>( g_firstPlugIndex + 5 );
}

void FilterResults::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ComputeNode::affects( input, outputs );

	if( input->parent() == scenePlug() )
	{
		filterPlug()->sceneAffects( input, outputs );
	}

	if(
		input == filterPlug() ||
		input == rootPlug() ||
		input == scenePlug()->childNamesPlug()
	)
	{
		outputs.push_back( internalOutPlug() );
	}

	if( input == internalOutPlug() )
	{
		outputs.push_back( outPlug() );
	}

	if( input == outPlug() )
	{
		outputs.push_back( outStringsPlug() );
	}
}

void FilterResults::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ComputeNode::hash( output, context, h );

	if( output == internalOutPlug() )
	{
		ScenePlug::ScenePath rootPath;
		ScenePlug::stringToPath( rootPlug()->getValue(), rootPath );
		h.append( SceneAlgo::matchingPathsHash( filterPlug(), scenePlug(), rootPath ) );
	}
	else if( output == outPlug() )
	{
		ScenePlug::GlobalScope globalScope( context );
		internalOutPlug()->hash( h );
	}
	else if( output == outStringsPlug() )
	{
		outPlug()->hash( h );
	}
}

void FilterResults::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output == internalOutPlug() )
	{
		ScenePlug::ScenePath rootPath;
		ScenePlug::stringToPath( rootPlug()->getValue(), rootPath );
		PathMatcherDataPtr data = new PathMatcherData;
		SceneAlgo::matchingPaths( filterPlug(), scenePlug(), rootPath, data->writable() );
		static_cast<PathMatcherDataPlug *>( output )->setValue( data );
		return;
	}
	else if( output == outPlug() )
	{
		ScenePlug::GlobalScope globalScope( context );
		output->setFrom( internalOutPlug() );
		return;
	}
	else if( output == outStringsPlug() )
	{
		ConstPathMatcherDataPtr paths = outPlug()->getValue();
		StringVectorDataPtr strings = new StringVectorData();
		paths->readable().paths( strings->writable() );
		static_cast<StringVectorDataPlug *>( output )->setValue( strings );
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
