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
#include "GafferScene/ScenePlug.h"
#include "GafferScene/Filter.h"
#include "GafferScene/SceneAlgo.h"

using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

size_t FilterResults::g_firstPlugIndex = 0;

IE_CORE_DEFINERUNTIMETYPED( FilterResults )

FilterResults::FilterResults( const std::string &name )
	:	ComputeNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ScenePlug( "scene" ) );
	addChild( new FilterPlug( "filter" ) );
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

PathMatcherDataPlug *FilterResults::outPlug()
{
	return getChild<PathMatcherDataPlug>( g_firstPlugIndex + 2 );
}

const PathMatcherDataPlug *FilterResults::outPlug() const
{
	return getChild<PathMatcherDataPlug>( g_firstPlugIndex + 2 );
}

void FilterResults::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ComputeNode::affects( input, outputs );

	const ScenePlug *scenePlug = input->parent<ScenePlug>();
	if( scenePlug && scenePlug == this->scenePlug() )
	{
		const Filter *filter = runTimeCast<const Filter>( filterPlug()->source<Plug>()->node() );
		if( filter && filter->sceneAffectsMatch( scenePlug, static_cast<const ValuePlug *>( input ) ) )
		{
			outputs.push_back( filterPlug() );
		}
	}
	else if( input == filterPlug() )
	{
		outputs.push_back( outPlug() );
	}
}

void FilterResults::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ComputeNode::hash( output, context, h );

	if( output == outPlug() )
	{
		/// \todo This is potentially incredibly expensive, because depending
		/// on the filter it might visit every single location of a scene.
		/// Do better. Possibilities include :
		///
		/// - Using an __internalOut plug to do the work, and ensuring that the
		///   computation of the out plug pulls on __internalOut with a context
		///   which is as clean as possible (removing scene:path, scene:set,
		///   image:tileOrigin and image:channelName). This would give the hash
		///   cache a better chance of mitigating the expense.
		/// - Adding protected Filter virtual methods to perform all the work
		///   and exposing them via public methods on FilterPlug. Filters such
		///   as SetFilter could then have much faster implementations given
		///   their specific knowledge of the situation.
		/// - Using David Minor's "poor man's hash" trick whereby the dirty
		///   count of the input scene is used as a substitute for the true
		///   hash.
		/// - Coming up with a way of cheaply computing a hierarchy hash,
		///   that mythical beast that solves all our problems.
		PathMatcherDataPtr data = new PathMatcherData;
		SceneAlgo::matchingPaths( filterPlug(), scenePlug(), data->writable() );
		data->hash( h );
	}
}

void FilterResults::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output == outPlug() )
	{
		PathMatcherDataPtr data = new PathMatcherData;
		SceneAlgo::matchingPaths( filterPlug(), scenePlug(), data->writable() );
		static_cast<PathMatcherDataPlug *>( output )->setValue( data );
		return;
	}

	ComputeNode::compute( output, context );
}
