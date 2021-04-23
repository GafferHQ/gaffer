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

#include "GafferScene/PathFilter.h"

#include "GafferScene/ScenePlug.h"

#include "Gaffer/Context.h"

#include "boost/bind.hpp"

using namespace GafferScene;
using namespace Gaffer;
using namespace IECore;
using namespace std;

namespace
{

// Special value used at the end of `rootSizes`,
// to indicate that there are roots at descendant
// locations.
const int g_descendantRoots = numeric_limits<int>::max();

} // namespace

GAFFER_NODE_DEFINE_TYPE( PathFilter );

size_t PathFilter::g_firstPlugIndex = 0;

PathFilter::PathFilter( const std::string &name )
	:	Filter( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringVectorDataPlug( "paths", Plug::In, new StringVectorData ) );
	addChild( new FilterPlug( "roots" ) );
	addChild( new PathMatcherDataPlug( "__pathMatcher", Plug::Out, new PathMatcherData ) );
	addChild( new IntVectorDataPlug( "__rootSizes", Plug::Out, new IntVectorData() ) );

	plugDirtiedSignal().connect( boost::bind( &PathFilter::plugDirtied, this, ::_1 ) );
}

PathFilter::~PathFilter()
{
}

Gaffer::StringVectorDataPlug *PathFilter::pathsPlug()
{
	return getChild<Gaffer::StringVectorDataPlug>( g_firstPlugIndex );
}

const Gaffer::StringVectorDataPlug *PathFilter::pathsPlug() const
{
	return getChild<Gaffer::StringVectorDataPlug>( g_firstPlugIndex );
}

FilterPlug *PathFilter::rootsPlug()
{
	return getChild<FilterPlug>( g_firstPlugIndex + 1 );
}

const FilterPlug *PathFilter::rootsPlug() const
{
	return getChild<FilterPlug>( g_firstPlugIndex + 1 );
}

Gaffer::PathMatcherDataPlug *PathFilter::pathMatcherPlug()
{
	return getChild<PathMatcherDataPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::PathMatcherDataPlug *PathFilter::pathMatcherPlug() const
{
	return getChild<PathMatcherDataPlug>( g_firstPlugIndex + 2 );
}

Gaffer::IntVectorDataPlug *PathFilter::rootSizesPlug()
{
	return getChild<IntVectorDataPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::IntVectorDataPlug *PathFilter::rootSizesPlug() const
{
	return getChild<IntVectorDataPlug>( g_firstPlugIndex + 3 );
}

void PathFilter::plugDirtied( const Gaffer::Plug *plug )
{
	if( plug == pathsPlug() )
	{
		//\todo: share this logic with Switch::variesWithContext()
		Plug* sourcePlug = pathsPlug()->source();
		if( sourcePlug->direction() == Plug::Out && IECore::runTimeCast<const ComputeNode>( sourcePlug->node() ) )
		{
			// pathsPlug() is receiving data from a plug whose value is context varying, meaning
			// we need to use the intermediate pathMatcherPlug() in computeMatch() instead:

			m_pathMatcher = nullptr;
		}
		else
		{
			// pathsPlug() value is not context varying, meaning we can save on graph evaluations
			// by just precomputing it here and directly using it in computeMatch():

			ConstStringVectorDataPtr paths = pathsPlug()->getValue();
			m_pathMatcher = new PathMatcherData;
			m_pathMatcher->writable().init( paths->readable().begin(), paths->readable().end() );
		}
	}
}

void PathFilter::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	Filter::affects( input, outputs );

	if( input == pathsPlug() )
	{
		outputs.push_back( pathMatcherPlug() );
	}
	else if( input == rootsPlug() )
	{
		outputs.push_back( rootSizesPlug() );
	}
	else if( input == pathMatcherPlug() || input == rootSizesPlug() )
	{
		outputs.push_back( outPlug() );
	}

	if( input->parent<ScenePlug>() )
	{
		rootsPlug()->sceneAffects( input, outputs );
	}
}

void PathFilter::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	Filter::hash( output, context, h );

	if( output == pathMatcherPlug() )
	{
		pathsPlug()->hash( h );
	}
	else if( output == rootSizesPlug() )
	{
		hashRootSizes( context, h );
	}
}

void PathFilter::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output == pathMatcherPlug() )
	{
		ConstStringVectorDataPtr paths = pathsPlug()->getValue();
		PathMatcherDataPtr pathMatcherData = new PathMatcherData;
		pathMatcherData->writable().init( paths->readable().begin(), paths->readable().end() );
		static_cast<PathMatcherDataPlug *>( output )->setValue( pathMatcherData );
		return;
	}
	else if( output == rootSizesPlug() )
	{
		static_cast<IntVectorDataPlug *>( output )->setValue( computeRootSizes( context ) );
		return;
	}

	Filter::compute( output, context );
}

void PathFilter::hashMatch( const ScenePlug *scene, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	const ScenePlug::ScenePath *path = context->getIfExists<ScenePlug::ScenePath>( ScenePlug::scenePathContextName );

	if( !path )
	{
		// This is a special case used by the Prune and Isolate nodes
		// to request a hash representing the effects of the filter
		// across the entire scene. Although it duplicates some logic
		// from the case below it is deliberately kept separate to
		// emphasise its different role. Ideally we would separate this
		// out into a specific query of some sort.
		if( rootsPlug()->getInput() )
		{
			rootsPlug()->hash( h );
		}
		if( m_pathMatcher )
		{
			m_pathMatcher->hash( h );
		}
		else
		{
			pathMatcherPlug()->hash( h );
		}
		return;
	}

	// Standard case

	h.append( path->data(), path->size() );

	if( m_pathMatcher )
	{
		m_pathMatcher->hash( h );
	}
	else
	{
		pathMatcherPlug()->hash( h );
	}

	if( rootsPlug()->getInput() )
	{
		rootSizesPlug()->hash( h );
	}
}

unsigned PathFilter::computeMatch( const ScenePlug *scene, const Gaffer::Context *context ) const
{
	const ScenePlug::ScenePath &path = context->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName );
	ConstPathMatcherDataPtr pathMatcher = m_pathMatcher ? m_pathMatcher : pathMatcherPlug()->getValue();

	if( !rootsPlug()->getInput() )
	{
		return pathMatcher->readable().match( path );
	}

	ConstIntVectorDataPtr rootSizes = rootSizesPlug()->getValue();
	ScenePlug::ScenePath relativePath = path;
	unsigned result = PathMatcher::NoMatch;

	size_t previousRootSize = 0;
	for( const int rootSize : rootSizes->readable() )
	{
		if( rootSize == g_descendantRoots )
		{
			if( !pathMatcher->readable().isEmpty() )
			{
				result |= PathMatcher::DescendantMatch;
			}
			break;
		}
		relativePath.erase( relativePath.begin(), relativePath.begin() + rootSize - previousRootSize );
		result |= pathMatcher->readable().match( relativePath );
		previousRootSize = rootSize;
	}

	return result;
}

void PathFilter::hashRootSizes( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	const ScenePlug::ScenePath &path = context->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName );
	if( path.size() )
	{
		ScenePlug::ScenePath parentPath( path.begin(), path.begin() + path.size() - 1 );
		ScenePlug::PathScope parentScope( context, &parentPath );
		rootSizesPlug()->hash( h );
	}
	rootsPlug()->hash( h );
	h.append( (uint64_t)path.size() );
}

ConstIntVectorDataPtr PathFilter::computeRootSizes( const Gaffer::Context *context ) const
{
	const ScenePlug::ScenePath &path = context->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName );

	// Start with the root sizes from our parent.

	ConstIntVectorDataPtr parentRootSizes;
	if( path.size() )
	{
		ScenePlug::ScenePath parentPath( path.begin(), path.begin() + path.size() - 1 );
		ScenePlug::PathScope parentScope( context, &parentPath );
		parentRootSizes = rootSizesPlug()->getValue();
		// If the parent has no descendant roots, then we already have
		// all the roots we need.
		if( !parentRootSizes->readable().size() || parentRootSizes->readable().back() != g_descendantRoots )
		{
			return parentRootSizes;
		}
	}

	// Then figure out if there is a new root here,
	// and if there are still any descendant roots.

	const unsigned m = rootsPlug()->getValue();

	IntVectorDataPtr resultData = new IntVectorData();
	auto &result = resultData->writable();
	if( parentRootSizes )
	{
		result = parentRootSizes->readable();
		assert( result.back() == g_descendantRoots );
		result.pop_back();
	}

	if( m & PathMatcher::ExactMatch )
	{
		result.push_back( path.size() );
	}

	if( m & PathMatcher::DescendantMatch )
	{
		result.push_back( g_descendantRoots );
	}

	return resultData;
}
