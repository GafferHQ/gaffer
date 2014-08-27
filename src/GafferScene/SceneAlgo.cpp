//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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

#include "tbb/spin_mutex.h"
#include "tbb/task.h"

#include "Gaffer/Context.h"

#include "GafferScene/SceneAlgo.h"
#include "GafferScene/Filter.h"
#include "GafferScene/ScenePlug.h"
#include "GafferScene/PathMatcher.h"

using namespace std;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

bool GafferScene::exists( const ScenePlug *scene, const ScenePlug::ScenePath &path )
{
	ContextPtr context = new Context( *Context::current(), Context::Borrowed );
	Context::Scope scopedContext( context.get() );

	ScenePlug::ScenePath p; p.reserve( path.size() );
	for( ScenePlug::ScenePath::const_iterator it = path.begin(), eIt = path.end(); it != eIt; ++it )
	{
		context->set( ScenePlug::scenePathContextName, p );
		ConstInternedStringVectorDataPtr childNamesData = scene->childNamesPlug()->getValue();
		const vector<InternedString> &childNames = childNamesData->readable();
		if( find( childNames.begin(), childNames.end(), *it ) == childNames.end() )
		{
			return false;
		}
		p.push_back( *it );
	}

	return true;
}

namespace
{

/// \todo If we find similar usage patterns, we could make a parallelTraverse()
/// method in SceneAlgo.h. This would hide the details of traversing using tasks,
/// simply calling a functor in the right context for each location in the scene.
class MatchingPathsTask : public tbb::task
{

	public :

		typedef tbb::spin_mutex PathMatcherMutex;

		MatchingPathsTask(
			const Gaffer::IntPlug *filter,
			const ScenePlug *scene,
			const Gaffer::Context *context,
			PathMatcherMutex &pathMatcherMutex,
			PathMatcher &pathMatcher
		)
			:	m_filter( filter ), m_scene( scene ), m_context( context ), m_pathMatcherMutex( pathMatcherMutex ), m_pathMatcher( pathMatcher )
		{
		}

		virtual ~MatchingPathsTask()
		{
		}

		virtual task *execute()
		{

			ContextPtr context = new Context( *m_context, Context::Borrowed );
			context->set( ScenePlug::scenePathContextName, m_path );
			Context::Scope scopedContext( context.get() );

			const Filter::Result match = (Filter::Result)m_filter->getValue();
			if( match & Filter::ExactMatch )
			{
				PathMatcherMutex::scoped_lock lock( m_pathMatcherMutex );
				m_pathMatcher.addPath( m_path );
			}

			if( match & Filter::DescendantMatch )
			{
				ConstInternedStringVectorDataPtr childNamesData = m_scene->childNamesPlug()->getValue();
				const vector<InternedString> &childNames = childNamesData->readable();

				set_ref_count( 1 + childNames.size() );

				ScenePlug::ScenePath childPath = m_path;
				childPath.push_back( InternedString() ); // space for the child name
				for( vector<InternedString>::const_iterator it = childNames.begin(), eIt = childNames.end(); it != eIt; it++ )
				{
					childPath[m_path.size()] = *it;
					MatchingPathsTask *t = new( allocate_child() ) MatchingPathsTask( *this, childPath );
					spawn( *t );
				}
				wait_for_all();
			}

			return NULL;
		}

	protected :

		MatchingPathsTask( const MatchingPathsTask &other, const ScenePlug::ScenePath &path )
			:	m_filter( other.m_filter ),
				m_scene( other.m_scene ),
				m_context( other.m_context ),
				m_pathMatcherMutex( other.m_pathMatcherMutex ),
				m_pathMatcher( other.m_pathMatcher ),
				m_path( path )
		{
		}

	private :

		const IntPlug *m_filter;
		const ScenePlug *m_scene;
		const Context *m_context;
		PathMatcherMutex &m_pathMatcherMutex;
		PathMatcher &m_pathMatcher;
		ScenePlug::ScenePath m_path;

};

} // namespace

void GafferScene::matchingPaths( const Filter *filter, const ScenePlug *scene, PathMatcher &paths )
{
	matchingPaths( filter->matchPlug(), scene, paths );
}

void GafferScene::matchingPaths( const Gaffer::IntPlug *filterPlug, const ScenePlug *scene, PathMatcher &paths )
{
	ContextPtr context = new Context( *Context::current(), Context::Borrowed );
	Filter::setInputScene( context.get(), scene );
	MatchingPathsTask::PathMatcherMutex mutex;
	MatchingPathsTask *task = new( tbb::task::allocate_root() ) MatchingPathsTask( filterPlug, scene, context.get(), mutex, paths );
	tbb::task::spawn_root_and_wait( *task );
}
