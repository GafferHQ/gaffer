//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2019, Image Engine Design Inc. All rights reserved.
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

#include "boost/python.hpp"

#include "TaskMutexTest.h"

#include "GafferTest/Assert.h"

#include "Gaffer/Private/IECorePreview/ParallelAlgo.h"
#include "Gaffer/Private/IECorePreview/TaskMutex.h"

#include "boost/make_unique.hpp"

#include "tbb/enumerable_thread_specific.h"
#include "tbb/parallel_for.h"

#include <thread>

using namespace IECorePreview;
using namespace boost::python;

namespace
{

void testTaskMutex()
{
	// Mutex and bool used to model lazy initialisation.
	TaskMutex mutex;
	bool initialised = false;

	// Tracking to see what various threads get up to.
	tbb::enumerable_thread_specific<int> didInitialisation;
	tbb::enumerable_thread_specific<int> didInitialisationTasks;
	tbb::enumerable_thread_specific<int> gotLock;

	// Lazy initialisation function, using an optimistic read lock
	// and only upgrading to a write lock to perform initialisation.

	auto initialise = [&]() {

		TaskMutex::ScopedLock lock( mutex, /* write = */ false );
		gotLock.local() = true;

		if( !initialised )
		{
			lock.upgradeToWriter();
			if( !initialised ) // Check again, because upgrading to writer may lose the lock temporarily.
			{
				// Simulate an expensive multithreaded
				// initialisation process.
				lock.execute(
					[&]() {
						tbb::parallel_for(
							tbb::blocked_range<size_t>( 0, 1000000 ),
							[&]( const tbb::blocked_range<size_t> &r ) {
								didInitialisationTasks.local() = true;
								std::this_thread::sleep_for( std::chrono::milliseconds( 10 ) );
							}
						);
					}
				);
				initialised = true;
				didInitialisation.local() = true;
			}
		}
	};

	// Generate a bunch of tasks that will each try to
	// do the lazy initialisation. Only one should do it,
	// but the rest should help out in doing the work.

	tbb::parallel_for(
		tbb::blocked_range<size_t>( 0, 1000000 ),
		[&]( const tbb::blocked_range<size_t> &r ) {
			for( size_t i = r.begin(); i < r.end(); ++i )
			{
				initialise();
			}
		}
	);

	// Only one thread should have done the initialisation,
	// but everyone should have got the lock, and everyone should
	// have done some work.
	GAFFERTEST_ASSERTEQUAL( didInitialisation.size(), 1 );
	GAFFERTEST_ASSERTEQUAL( gotLock.size(), tbb::tbb_thread::hardware_concurrency() );
	GAFFERTEST_ASSERTEQUAL( didInitialisationTasks.size(), tbb::tbb_thread::hardware_concurrency() );

}

void testTaskMutexWithinIsolate()
{
	TaskMutex mutex;

	auto getMutexWithinIsolate = [&mutex]() {

		ParallelAlgo::isolate(
			[&mutex]() {
				TaskMutex::ScopedLock lock( mutex );
				std::this_thread::sleep_for( std::chrono::milliseconds( 1 ) );
			}
		);

	};

	ParallelAlgo::isolate(
		[&]() {
			tbb::parallel_for(
				tbb::blocked_range<size_t>( 0, 1000000 ),
				[&]( const tbb::blocked_range<size_t> &r ) {
					getMutexWithinIsolate();
				}
			);
		}
	);

	// This test was written to guard against deadlocks
	// caused by an early version of TaskMutex. Hence
	// it doesn't assert anything; instead we're just very
	// happy if it gets this far.

}

void testTaskMutexJoiningOuterTasks()
{
	// Mutex and bool used to model lazy initialisation.
	TaskMutex mutex;
	bool initialised = false;

	// Tracking to see what various threads get up to.
	tbb::enumerable_thread_specific<int> didInitialisation;
	tbb::enumerable_thread_specific<int> didInitialisationTasks;
	tbb::enumerable_thread_specific<int> gotLock;

	// Lazy initialisation function
	auto initialise = [&]() {

		TaskMutex::ScopedLock lock( mutex );
		gotLock.local() = true;

		if( !initialised )
		{
			// Simulate an expensive multithreaded
			// initialisation process.
			lock.execute(
				[&]() {
					tbb::parallel_for(
						tbb::blocked_range<size_t>( 0, 1000000 ),
						[&]( const tbb::blocked_range<size_t> &r ) {
							didInitialisationTasks.local() = true;
							std::this_thread::sleep_for( std::chrono::milliseconds( 10 ) );
						}
					);
				}
			);
			initialised = true;
			didInitialisation.local() = true;
		}
	};

	// Outer tasks which are performed within a TaskMutex of their own,
	// but want to collaborate on the inner initialisation.

	using TaskMutexPtr = std::unique_ptr<TaskMutex>;
	std::vector<TaskMutexPtr> independentTasks;
	for( size_t i = 0; i < tbb::tbb_thread::hardware_concurrency() * 1000; ++i )
	{
		independentTasks.push_back( boost::make_unique<TaskMutex>() );
	}

	tbb::parallel_for(
		tbb::blocked_range<size_t>( 0, independentTasks.size() ),
		[&]( const tbb::blocked_range<size_t> &r ) {
			for( size_t i = r.begin(); i < r.end(); ++i )
			{
				TaskMutex::ScopedLock lock( *independentTasks[i] );
				lock.execute(
					[&]() {
						initialise();
					}
				);
			}
		}
	);

	// Only one thread should have done the initialisation,
	// but everyone should have got the lock, and everyone should
	// have done some work.
	GAFFERTEST_ASSERTEQUAL( didInitialisation.size(), 1 );
	GAFFERTEST_ASSERTEQUAL( gotLock.size(), tbb::tbb_thread::hardware_concurrency() );
	GAFFERTEST_ASSERTEQUAL( didInitialisationTasks.size(), tbb::tbb_thread::hardware_concurrency() );

}

void testTaskMutexHeavyContention( bool acceptWork )
{
	// Model what happens when initialisation has already occurred,
	// and we just have lots of threads hammering away on the mutex,
	// wanting to get in and out with just read access as quickly as
	// possible.
	TaskMutex mutex;
	bool initialised = true;

	tbb::parallel_for(
		tbb::blocked_range<size_t>( 0, 1000000 ),
		[&]( const tbb::blocked_range<size_t> &r ) {
			for( size_t i = r.begin(); i < r.end(); ++i )
			{
				TaskMutex::ScopedLock lock( mutex, /* write = */ false, acceptWork );
				GAFFERTEST_ASSERTEQUAL( initialised, true );
			}
		}
	);
}

void testTaskMutexRecursion()
{
	TaskMutex mutex;

	std::function<void ( int )> recurse;
	recurse = [&mutex, &recurse]( int depth ) {
		TaskMutex::ScopedLock lock( mutex );
		GAFFERTEST_ASSERT( lock.recursive() );
		if( depth > 100 )
		{
			return;
		}
		else
		{
			recurse( depth + 1 );
		}
	};

	TaskMutex::ScopedLock lock( mutex );
	lock.execute(
		[&recurse] { recurse( 0 ); }
	);
}

void testTaskMutexWorkerRecursion()
{
	TaskMutex mutex;
	tbb::enumerable_thread_specific<int> gotLock;

	std::function<void ( int )> recurse;
	recurse = [&mutex, &gotLock, &recurse] ( int depth ) {

		TaskMutex::ScopedLock lock( mutex );
		GAFFERTEST_ASSERT( lock.recursive() );
		gotLock.local() = true;

		if( depth > 4 )
		{
			std::this_thread::sleep_for( std::chrono::milliseconds( 10 ) );
		}
		else
		{
			tbb::parallel_for(
				0, 4,
				[&recurse, depth] ( int i ) {
					recurse( depth + 1 );
				}
			);
		}

	};

	TaskMutex::ScopedLock lock( mutex );
	lock.execute(
		[&recurse] { recurse( 0 ); }
	);

	GAFFERTEST_ASSERTEQUAL( gotLock.size(), tbb::tbb_thread::hardware_concurrency() );
}

void testTaskMutexAcquireOr()
{
	TaskMutex mutex;
	TaskMutex::ScopedLock lock1( mutex );

	TaskMutex::ScopedLock lock2;
	bool workAvailable = true;
	const bool acquired = lock2.acquireOr(
		mutex, /* write = */ true,
		[&workAvailable] ( bool wa ) { workAvailable = wa; return true; }
	);

	GAFFERTEST_ASSERT( !acquired );
	GAFFERTEST_ASSERT( !workAvailable );

}

} // namespace

void GafferTestModule::bindTaskMutexTest()
{
	def( "testTaskMutex", &testTaskMutex );
	def( "testTaskMutexWithinIsolate", &testTaskMutexWithinIsolate );
	def( "testTaskMutexJoiningOuterTasks", &testTaskMutexJoiningOuterTasks );
	def( "testTaskMutexHeavyContention", &testTaskMutexHeavyContention );
	def( "testTaskMutexRecursion", &testTaskMutexRecursion );
	def( "testTaskMutexWorkerRecursion", &testTaskMutexWorkerRecursion );
	def( "testTaskMutexAcquireOr", &testTaskMutexAcquireOr );
}
