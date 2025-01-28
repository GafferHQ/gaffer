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

#include "tbb/concurrent_queue.h"
#include "tbb/enumerable_thread_specific.h"
#include "tbb/parallel_for.h"
#include "tbb/task_arena.h"

#include <variant>

namespace GafferScene
{

namespace Detail
{

template<typename ThreadableFunctor>
void parallelProcessLocationsWalk( const GafferScene::ScenePlug *scene, const Gaffer::ThreadState &threadState, const ScenePlug::ScenePath &path, ThreadableFunctor &f, tbb::task_group_context &taskGroupContext )
{
	ScenePlug::PathScope pathScope( threadState, &path );

	if( !f( scene, path ) )
	{
		return;
	}

	IECore::ConstInternedStringVectorDataPtr childNamesData = scene->childNamesPlug()->getValue();
	const std::vector<IECore::InternedString> &childNames = childNamesData->readable();
	if( childNames.empty() )
	{
		return;
	}

	using ChildNameRange = tbb::blocked_range<std::vector<IECore::InternedString>::const_iterator>;
	const ChildNameRange loopRange( childNames.begin(), childNames.end() );

	auto loopBody = [&] ( const ChildNameRange &range ) {
		ScenePlug::ScenePath childPath = path;
		childPath.push_back( IECore::InternedString() ); // Space for the child name
		for( auto &childName : range )
		{
			ThreadableFunctor childFunctor( f );
			childPath.back() = childName;
			parallelProcessLocationsWalk( scene, threadState, childPath, childFunctor, taskGroupContext );
		}
	};

	if( childNames.size() > 1 )
	{
		tbb::parallel_for( loopRange, loopBody, taskGroupContext );
	}
	else
	{
		// Serial execution
		loopBody( loopRange );
	}
}

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
	Detail::parallelProcessLocationsWalk( scene, Gaffer::ThreadState::current(), root, f, taskGroupContext );
}

template <class ThreadableFunctor>
void parallelTraverse( const ScenePlug *scene, ThreadableFunctor &f, const ScenePlug::ScenePath &root )
{
	// `parallelProcessLocations()` takes a copy of the functor at each location, whereas
	// `parallelTraverse()` is intended to use the same functor for all locations. Wrap the
	// functor in a cheap-to-copy lambda, so that the functor itself won't be copied.
	auto reference = [&f] ( const ScenePlug *scene, const ScenePlug::ScenePath &path ) {
		return f( scene, path );
	};
	parallelProcessLocations( scene, reference, root );
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


template <class LocationFunctor, class GatherFunctor>
void parallelGatherLocations( const ScenePlug *scene, LocationFunctor &&locationFunctor, GatherFunctor &&gatherFunctor, const ScenePlug::ScenePath &root )
{
	// We use `parallelTraverse()` to run `locationFunctor`, passing the results to
	// `gatherFunctor` on the current thread via a queue. In testing, this proved to
	// have lower overhead than using TBB's `parallel_pipeline()`.

	using LocationResult = std::invoke_result_t<LocationFunctor, const ScenePlug *, const ScenePlug::ScenePath &>;
	using QueueValue = std::variant<std::monostate, LocationResult, std::exception_ptr>;
	tbb::concurrent_bounded_queue<QueueValue> queue;
	queue.set_capacity( tbb::this_task_arena::max_concurrency() );

	IECore::Canceller traverseCanceller;
	auto locationFunctorWrapper = [&] ( const ScenePlug *scene, const ScenePlug::ScenePath &path ) {
		IECore::Canceller::check( &traverseCanceller );
		queue.push( std::move( locationFunctor( scene, path ) ) );
		return true;
	};

	tbb::task_arena( tbb::task_arena::attach() ).enqueue(

		[&, &threadState = Gaffer::ThreadState::current()] () {

			Gaffer::ThreadState::Scope threadStateScope( threadState );
			try
			{
				SceneAlgo::parallelTraverse( scene, locationFunctorWrapper, root );
			}
			catch( ... )
			{
				queue.push( std::current_exception() );
				return;
			}
			queue.push( std::monostate() );
		}

	);

	while( true )
	{
		QueueValue value;
		queue.pop( value );
		if( auto locationResult = std::get_if<LocationResult>( &value ) )
		{
			try
			{
				gatherFunctor( *locationResult );
			}
			catch( ... )
			{
				// We can't rethrow until the `parallelTraverse()` has
				// completed, as it references the `queue` and
				// `traverseCanceller` from this stack frame.
				traverseCanceller.cancel();
				while( true )
				{
					queue.pop( value );
					if( std::get_if<std::exception_ptr>( &value ) || std::get_if<std::monostate>( &value ) )
					{
						throw;
					}
				}
			}
		}
		else if( auto exception = std::get_if<std::exception_ptr>( &value ) )
		{
			std::rethrow_exception( *exception );
		}
		else
		{
			// We use `monostate` to signal completion.
			break;
		}
	}
}

template<typename Predicate>
IECore::PathMatcher findAll( const ScenePlug *scene, Predicate &&predicate, const ScenePlug::ScenePath &root )
{
	tbb::enumerable_thread_specific<IECore::PathMatcher> threadResults;

	auto f = [&] ( const ScenePlug *scene, const ScenePlug::ScenePath &path ) {
		if( predicate( scene, path ) )
		{
			threadResults.local().addPath( path );
		}
		return true;
	};

	parallelTraverse( scene, f, root );

	return threadResults.combine(
		[] ( const IECore::PathMatcher &a, const IECore::PathMatcher &b ) {
			IECore::PathMatcher c = a;
			c.addPaths( b );
			return c;
		}
	);
}

} // namespace SceneAlgo

} // namespace GafferScene
