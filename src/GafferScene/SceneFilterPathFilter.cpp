//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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

#include "GafferScene/SceneFilterPathFilter.h"

#include "GafferScene/Filter.h"
#include "GafferScene/ScenePath.h"
#include "GafferScene/ScenePlug.h"

#include "Gaffer/Context.h"

#include "boost/bind/bind.hpp"

using namespace boost::placeholders;
using namespace GafferScene;

SceneFilterPathFilter::SceneFilterPathFilter( FilterPtr sceneFilter, IECore::CompoundDataPtr userData )
	:	PathFilter( userData ), m_sceneFilter( sceneFilter )
{
	m_plugDirtiedConnection = sceneFilter->plugDirtiedSignal().connect(
		boost::bind( &SceneFilterPathFilter::plugDirtied, this, ::_1 )
	);
}

SceneFilterPathFilter::~SceneFilterPathFilter()
{
}

struct SceneFilterPathFilter::Remove
{

	Remove( const Filter *filter )
		:	m_filter( filter )
	{
	}

	bool operator () ( const  Gaffer::PathPtr &path )
	{
		const ScenePath *scenePath = IECore::runTimeCast<const ScenePath>( path.get() );
		if( !scenePath )
		{
			return false;
		}

		// We need to construct a new context based on the ScenePath context.
		// Constructing contexts does have an associated cost though, so we
		// only reconstruct when absolutely necessary - generally all the paths
		// we visit will be using the exact same context and we need construct
		// only once.
		const Gaffer::Context *pathContext = scenePath->getContext();
		if( m_baseContext != pathContext )
		{
			m_baseContext = pathContext;
			m_context = new Gaffer::Context( *pathContext );
		}

		// Set context up so we can evaluate the scene filter, and return
		// based on that.
		Filter::setInputScene( m_context.get(), scenePath->getScene() );
		m_context->set( ScenePlug::scenePathContextName, path->names() );
		Gaffer::Context::Scope s( m_context.get() );
		return !( m_filter->outPlug()->getValue() & ( IECore::PathMatcher::DescendantMatch | IECore::PathMatcher::ExactMatch ) );
	}

	private :

		const Filter *m_filter;
		Gaffer::ConstContextPtr m_baseContext;
		Gaffer::ContextPtr m_context;

};

void SceneFilterPathFilter::doFilter( std::vector<Gaffer::PathPtr> &paths, const IECore::Canceller *canceller ) const
{
	paths.erase(
		std::remove_if(
			paths.begin(),
			paths.end(),
			Remove( m_sceneFilter.get() )
		),
		paths.end()
	);
}

void SceneFilterPathFilter::plugDirtied( const Gaffer::Plug *plug )
{
	if( plug == m_sceneFilter->outPlug() )
	{
		changedSignal()( this );
	}
}
