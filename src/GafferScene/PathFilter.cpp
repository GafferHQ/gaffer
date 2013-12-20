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

#include "boost/bind.hpp"

#include "Gaffer/Context.h"

#include "GafferScene/ScenePlug.h"
#include "GafferScene/PathFilter.h"

using namespace GafferScene;
using namespace Gaffer;
using namespace IECore;
using namespace std;

IE_CORE_DEFINERUNTIMETYPED( PathFilter );

size_t PathFilter::g_firstPlugIndex = 0;

PathFilter::PathFilter( const std::string &name )
	:	Filter( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	// we don't allow inputs to the paths plug, because then the paths could vary
	// from computation to computation - resulting in nonsense as far as descendant
	// matches go.
	addChild( new StringVectorDataPlug( "paths", Plug::In, new StringVectorData(), Plug::Default & ~Plug::AcceptsInputs ) );

	plugSetSignal().connect( boost::bind( &PathFilter::plugSet, this, ::_1 ) );
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

void PathFilter::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	if( input == pathsPlug() )
	{
		outputs.push_back( matchPlug() );
	}
}

void PathFilter::hashMatch( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	typedef IECore::TypedData<ScenePlug::ScenePath> ScenePathData;
	const ScenePathData *pathData = context->get<ScenePathData>( ScenePlug::scenePathContextName, 0 );
	if( pathData )
	{
		const ScenePlug::ScenePath &path = pathData->readable();
		h.append( &(path[0]), path.size() );
	}
	pathsPlug()->hash( h );
}

unsigned PathFilter::computeMatch( const Gaffer::Context *context ) const
{
	typedef IECore::TypedData<ScenePlug::ScenePath> ScenePathData;
	const ScenePathData *pathData = context->get<ScenePathData>( ScenePlug::scenePathContextName, 0 );
	if( pathData )
	{
		return m_matcher.match( pathData->readable() );
	}
	return NoMatch;
}

void PathFilter::plugSet( Gaffer::Plug *plug )
{
	if( plug == pathsPlug() )
	{
		ConstStringVectorDataPtr paths = pathsPlug()->getValue();
		m_matcher.init( paths->readable().begin(), paths->readable().end() );
	}
}

