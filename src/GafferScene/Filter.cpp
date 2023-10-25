//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#include "GafferScene/Filter.h"

#include "GafferScene/FilterPlug.h"
#include "GafferScene/ScenePlug.h"

#include "Gaffer/Context.h"

using namespace GafferScene;
using namespace Gaffer;

GAFFER_NODE_DEFINE_TYPE( Filter );

const IECore::InternedString Filter::inputSceneContextName( "scene:filter:inputScene" );
size_t Filter::g_firstPlugIndex = 0;

Filter::Filter( const std::string &name )
	:	ComputeNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new BoolPlug( "enabled", Gaffer::Plug::In, true ) );
	// FilteredSceneProcessor calls `Filter::affects()` via `FilterPlug::sceneAffects()`
	// when the processor's input scene is dirtied. This allows a Filter to declare any
	// scene dependencies of its own (see SetFilter for an example). But when the same
	// filter is connected to multiple FilteredSceneProcessors in a row, this can lead
	// to the declaration of circular dependencies as follows :
	//
	//    Processor1.in -> Filter.>out -> Processor1.out -> Processor2.in -> Filter.out
	//
	// This isn't actually a true dependency cycle, because the filter uses `Processor1.in`
	// and `Processor2.in` in completely different contexts. Dirty propagation takes place
	// independent of context though, so we use the `AcceptsDependencyCycles` flag to
	// show that any cycle is expected and harmless.
	addChild( new FilterPlug( "out", Gaffer::Plug::Out, Plug::Default | Plug::AcceptsDependencyCycles ) );
}

Filter::~Filter()
{
}

Gaffer::BoolPlug *Filter::enabledPlug()
{
	return getChild<Gaffer::BoolPlug>( g_firstPlugIndex );
}

const Gaffer::BoolPlug *Filter::enabledPlug() const
{
	return getChild<Gaffer::BoolPlug>( g_firstPlugIndex );
}

FilterPlug *Filter::outPlug()
{
	return getChild<FilterPlug>( g_firstPlugIndex + 1 );
}

const FilterPlug *Filter::outPlug() const
{
	return getChild<FilterPlug>( g_firstPlugIndex + 1 );
}

void Filter::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ComputeNode::affects( input, outputs );

	if( input == enabledPlug() )
	{
		outputs.push_back( outPlug() );
	}
}

void Filter::setInputScene( Gaffer::Context *context, const ScenePlug *scenePlug )
{
	context->set( inputSceneContextName, (uint64_t)scenePlug );
}

const ScenePlug *Filter::getInputScene( const Gaffer::Context *context )
{
	return (const ScenePlug *)( context->get<uint64_t>( inputSceneContextName, 0 ) );
}

void Filter::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ComputeNode::hash( output, context, h );
	if( output == outPlug() )
	{
		if( enabled( context ) )
		{
			/// \todo In SceneNode (and other enableable nodes) we
			/// require methods like hashMatch() to call the base class
			/// implementation, which then calls ComputeNode::hash(). We
			/// should do that here too, rather than calling ComputeNode::hash()
			/// unconditionally first. This would allow derived classes to
			/// avoid the redundant call to ComputeNode::hash() in the case
			/// that their hashMatch() implementation simply passes through an
			/// input hash.
			hashMatch( getInputScene( context ), context, h );
		}
	}
}

void Filter::compute( ValuePlug *output, const Context *context ) const
{
	if( output == outPlug() )
	{
		unsigned match = IECore::PathMatcher::NoMatch;
		if( enabled( context ) )
		{
			match = computeMatch( getInputScene( context ), context );
		}
		static_cast<FilterPlug *>( output )->setValue( match );
		return;
	}

	ComputeNode::compute( output, context );
}

Gaffer::ValuePlug::CachePolicy Filter::computeCachePolicy( const Gaffer::ValuePlug *output ) const
{
	if( output == outPlug() )
	{
		return ValuePlug::CachePolicy::Uncached;
	}
	return ComputeNode::computeCachePolicy( output );
}

void Filter::hashMatch( const ScenePlug *scene, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	/// \todo See comments in hash() method.
}

unsigned Filter::computeMatch( const ScenePlug *scene, const Gaffer::Context *context ) const
{
	return IECore::PathMatcher::NoMatch;
}

bool Filter::enabled( const Gaffer::Context *context ) const
{
	const BoolPlug *plug = enabledPlug();
	const BoolPlug *sourcePlug = plug->source<BoolPlug>();
	if( !sourcePlug || sourcePlug->direction() == Plug::Out )
	{
		// Value may be computed. We use a global scope for two reasons :
		//
		// - Because our implementation assumes the result is constant across
		//   the scene, and allowing it to vary by `scene:path` could produce
		//   results where AncestorMatch and DescendantMatch are not consistent across locations.
		// - To reduce pressure on the hash cache.
		//
		// > Note : `sourcePlug` will be null if the source is not a BoolPlug.
		// > In this case we call `getValue()` on `plug` and it will perform the
		// > appropriate type conversion.
		ScenePlug::GlobalScope globalScope( context );
		return sourcePlug ? sourcePlug->getValue() : plug->getValue();
	}
	else
	{
		// Value is not computed so context is irrelevant.
		// Avoid overhead of context creation.
		return sourcePlug->getValue();
	}
}
