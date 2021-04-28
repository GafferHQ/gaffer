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

#include "Gaffer/Context.h"

#include "tbb/task.h"

namespace GafferScene
{

namespace Detail
{

template <class ThreadableFunctor>
class TraverseTask : public tbb::task
{

	public :

		TraverseTask(
			const GafferScene::ScenePlug *scene,
			const Gaffer::ThreadState &threadState,
			ThreadableFunctor &f
		)
			:	m_scene( scene ), m_threadState( threadState ), m_f( f )
		{
		}

		TraverseTask(
			const GafferScene::ScenePlug *scene,
			const Gaffer::ThreadState &threadState,
			const ScenePlug::ScenePath &path,
			ThreadableFunctor &f
		)
			:	m_scene( scene ), m_threadState( threadState ), m_f( f ), m_path( path )
		{
		}


		~TraverseTask() override
		{
		}

		task *execute() override
		{
			ScenePlug::PathScope pathScope( m_threadState, &m_path );

			if( m_f( m_scene, m_path ) )
			{
				IECore::ConstInternedStringVectorDataPtr childNamesData = m_scene->childNamesPlug()->getValue();
				const std::vector<IECore::InternedString> &childNames = childNamesData->readable();

				set_ref_count( 1 + childNames.size() );

				ScenePlug::ScenePath childPath = m_path;
				childPath.push_back( IECore::InternedString() ); // space for the child name
				for( std::vector<IECore::InternedString>::const_iterator it = childNames.begin(), eIt = childNames.end(); it != eIt; it++ )
				{
					childPath[m_path.size()] = *it;
					TraverseTask *t = new( allocate_child() ) TraverseTask( *this, childPath );
					spawn( *t );
				}
				wait_for_all();
			}

			return nullptr;
		}

	protected :

		TraverseTask( const TraverseTask &other, const ScenePlug::ScenePath &path )
			:	m_scene( other.m_scene ),
			m_threadState( other.m_threadState ),
			m_f( other.m_f ),
			m_path( path )
		{
		}

	private :

		const GafferScene::ScenePlug *m_scene;
		const Gaffer::ThreadState &m_threadState;
		ThreadableFunctor &m_f;
		GafferScene::ScenePlug::ScenePath m_path;

};

template<typename ThreadableFunctor>
class LocationTask : public tbb::task
{

	public :

		LocationTask(
			const GafferScene::ScenePlug *scene,
			const Gaffer::ThreadState &threadState,
			const ScenePlug::ScenePath &path,
			ThreadableFunctor &f
		)
			:	m_scene( scene ), m_threadState( threadState ), m_path( path ), m_f( f )
		{
		}

		~LocationTask() override
		{
		}

		task *execute() override
		{
			ScenePlug::PathScope pathScope( m_threadState, &m_path );

			if( !m_f( m_scene, m_path ) )
			{
				return nullptr;
			}

			IECore::ConstInternedStringVectorDataPtr childNamesData = m_scene->childNamesPlug()->getValue();
			const std::vector<IECore::InternedString> &childNames = childNamesData->readable();
			if( childNames.empty() )
			{
				return nullptr;
			}

			std::vector<ThreadableFunctor> childFunctors( childNames.size(), m_f );

			set_ref_count( 1 + childNames.size() );

			ScenePlug::ScenePath childPath = m_path;
			childPath.push_back( IECore::InternedString() ); // space for the child name
			for( size_t i = 0, e = childNames.size(); i < e; ++i )
			{
				childPath.back() = childNames[i];
				LocationTask *t = new( allocate_child() ) LocationTask( m_scene, m_threadState, childPath, childFunctors[i] );
				spawn( *t );
			}
			wait_for_all();

			return nullptr;
		}

	private :

		const GafferScene::ScenePlug *m_scene;
		const Gaffer::ThreadState &m_threadState;
		const GafferScene::ScenePlug::ScenePath m_path;
		ThreadableFunctor &m_f;

};

template <class ThreadableFunctor>
struct ThreadableFilteredFunctor
{
	ThreadableFilteredFunctor( ThreadableFunctor &f, const GafferScene::FilterPlug *filter ): m_f( f ), m_filter( filter ){}

	bool operator()( const GafferScene::ScenePlug *scene, const GafferScene::ScenePlug::ScenePath &path )
	{
		IECore::PathMatcher::Result match = (IECore::PathMatcher::Result)m_filter->match( scene );

		if( match & IECore::PathMatcher::ExactMatch )
		{
			if( !m_f( scene, path ) )
			{
				return false;
			}
		}

		return ( match & IECore::PathMatcher::DescendantMatch ) != 0;
	}

	ThreadableFunctor &m_f;
	const FilterPlug *m_filter;

};

template<class ThreadableFunctor>
struct PathMatcherFunctor
{

	PathMatcherFunctor( ThreadableFunctor &f, const IECore::PathMatcher &filter )
		: m_f( f ), m_filter( filter )
	{
	}

	bool operator()( const GafferScene::ScenePlug *scene, const GafferScene::ScenePlug::ScenePath &path )
	{
		const unsigned match = m_filter.match( path );
		if( match & IECore::PathMatcher::ExactMatch )
		{
			if( !m_f( scene, path ) )
			{
				return false;
			}
		}

		return match & IECore::PathMatcher::DescendantMatch;
	}

	private :

		ThreadableFunctor &m_f;
		const IECore::PathMatcher &m_filter;

};

} // namespace Detail

namespace SceneAlgo
{

template <class ThreadableFunctor>
void parallelProcessLocations( const GafferScene::ScenePlug *scene, ThreadableFunctor &f, const ScenePlug::ScenePath &root )
{
	tbb::task_group_context taskGroupContext( tbb::task_group_context::isolated ); // Prevents outer tasks silently cancelling our tasks
	Detail::LocationTask<ThreadableFunctor> *task = new( tbb::task::allocate_root( taskGroupContext ) ) Detail::LocationTask<ThreadableFunctor>( scene, Gaffer::ThreadState::current(), root, f );
	tbb::task::spawn_root_and_wait( *task );
}

template <class ThreadableFunctor>
void parallelTraverse( const ScenePlug *scene, ThreadableFunctor &f, const ScenePlug::ScenePath &root )
{
	tbb::task_group_context taskGroupContext( tbb::task_group_context::isolated ); // Prevents outer tasks silently cancelling our tasks
	Detail::TraverseTask<ThreadableFunctor> *task = new( tbb::task::allocate_root( taskGroupContext ) ) Detail::TraverseTask<ThreadableFunctor>( scene, Gaffer::ThreadState::current(), root, f );
	tbb::task::spawn_root_and_wait( *task );
}

template <class ThreadableFunctor>
void filteredParallelTraverse( const ScenePlug *scene, const GafferScene::FilterPlug *filterPlug, ThreadableFunctor &f, const ScenePlug::ScenePath &root )
{
	Detail::ThreadableFilteredFunctor<ThreadableFunctor> ff( f, filterPlug );
	parallelTraverse( scene, ff, root );
}

template <class ThreadableFunctor>
void filteredParallelTraverse( const ScenePlug *scene, const IECore::PathMatcher &filter, ThreadableFunctor &f, const ScenePlug::ScenePath &root )
{
	Detail::PathMatcherFunctor<ThreadableFunctor> ff( f, filter );
	parallelTraverse( scene, ff, root );
}

} // namespace SceneAlgo

} // namespace GafferScene
