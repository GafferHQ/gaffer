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

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( PathFilter );

size_t PathFilter::g_firstPlugIndex = 0;

PathFilter::PathFilter( const std::string &name )
	:	Filter( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringVectorDataPlug( "paths", Plug::In, new StringVectorData ) );
	addChild( new PathMatcherDataPlug( "__pathMatcher", Plug::Out, new PathMatcherData ) );

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

Gaffer::PathMatcherDataPlug *PathFilter::pathMatcherPlug()
{
	return getChild<PathMatcherDataPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::PathMatcherDataPlug *PathFilter::pathMatcherPlug() const
{
	return getChild<PathMatcherDataPlug>( g_firstPlugIndex + 1 );
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
	else if( input == pathMatcherPlug() )
	{
		outputs.push_back( outPlug() );
	}
}

void PathFilter::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	Filter::hash( output, context, h );

	if( output == pathMatcherPlug() )
	{
		pathsPlug()->hash( h );
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

	Filter::compute( output, context );
}

void PathFilter::hashMatch( const ScenePlug *scene, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	typedef IECore::TypedData<ScenePlug::ScenePath> ScenePathData;
	const ScenePathData *pathData = context->get<ScenePathData>( ScenePlug::scenePathContextName, nullptr );
	if( pathData )
	{
		const ScenePlug::ScenePath &path = pathData->readable();
		h.append( &(path[0]), path.size() );
	}
	if( m_pathMatcher )
	{
		m_pathMatcher->hash( h );
	}
	else
	{
		pathMatcherPlug()->hash( h );
	}
}

unsigned PathFilter::computeMatch( const ScenePlug *scene, const Gaffer::Context *context ) const
{
	const ScenePlug::ScenePath &path = context->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName );
	ConstPathMatcherDataPtr pathMatcher = m_pathMatcher ? m_pathMatcher : pathMatcherPlug()->getValue();
	return pathMatcher->readable().match( path );
}
