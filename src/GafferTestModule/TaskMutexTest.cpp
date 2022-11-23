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

#include "Gaffer/Private/IECorePreview/TaskMutex.h"

#include "tbb/enumerable_thread_specific.h"
#include "tbb/parallel_for.h"

#include <atomic>
#include <iostream>
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

		GAFFERTEST_ASSERT( lock.lockType() == TaskMutex::ScopedLock::LockType::Read )

		if( !initialised )
		{
			lock.upgradeToWriter();
			GAFFERTEST_ASSERT( lock.lockType() == TaskMutex::ScopedLock::LockType::Write );

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

		tbb::this_task_arena::isolate(
			[&mutex]() {
				TaskMutex::ScopedLock lock( mutex );
				GAFFERTEST_ASSERT( lock.lockType() == TaskMutex::ScopedLock::LockType::Write )
				std::this_thread::sleep_for( std::chrono::milliseconds( 1 ) );
			}
		);

	};

	tbb::this_task_arena::isolate(
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
		GAFFERTEST_ASSERT( lock.lockType() == TaskMutex::ScopedLock::LockType::Write )

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
		independentTasks.push_back( std::make_unique<TaskMutex>() );
	}

	tbb::parallel_for(
		tbb::blocked_range<size_t>( 0, independentTasks.size() ),
		[&]( const tbb::blocked_range<size_t> &r ) {
			for( size_t i = r.begin(); i < r.end(); ++i )
			{
				TaskMutex::ScopedLock lock( *independentTasks[i] );
				GAFFERTEST_ASSERT( lock.lockType() == TaskMutex::ScopedLock::LockType::Write )
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
				GAFFERTEST_ASSERT( lock.lockType() == TaskMutex::ScopedLock::LockType::Read );
				GAFFERTEST_ASSERTEQUAL( initialised, true );
			}
		}
	);
}

void testTaskMutexAcquireOr()
{
	TaskMutex mutex;
	TaskMutex::ScopedLock lock1( mutex );

	TaskMutex::ScopedLock lock2;
	bool workAvailable = true;
	const bool acquired = lock2.acquireOr(
		mutex, TaskMutex::ScopedLock::LockType::Write,
		[&workAvailable] ( bool wa ) { workAvailable = wa; return true; }
	);

	GAFFERTEST_ASSERT( !acquired );
	GAFFERTEST_ASSERT( !workAvailable );
}

void testTaskMutexExceptions()
{
	TaskMutex mutex;
	bool initialised = false;

	// Check that exceptions from `execute()` propagate
	// back to the caller.

	bool caughtException = false;
	try
	{
		TaskMutex::ScopedLock lock( mutex );
		lock.execute(
			[]{ throw IECore::Exception( "Oops!" ); }
		);
	}
	catch( const IECore::Exception &e )
	{
		caughtException = true;
		GAFFERTEST_ASSERTEQUAL( e.what(), std::string( "Oops!" ) );
	}

	GAFFERTEST_ASSERTEQUAL( caughtException, true );

	// Test that a subsequent non-throwing call can
	// still succeed.

	TaskMutex::ScopedLock lock( mutex );
	lock.execute(
		[&initialised]{ initialised = true; }
	);

	GAFFERTEST_ASSERTEQUAL( initialised, true );

}

void testTaskMutexWorkerExceptions()
{
	TaskMutex mutex;
	bool initialised = false;
	std::thread::id initialisingThread;
	std::atomic_int numAcquisitionExceptions( 0 );
	std::string executionException;

	// Check that exceptions thrown from worker threads propagate
	// back to the caller of `execute()`, and aren't thrown back
	// out to the poor worker thread who is just trying to acquire
	// the lock.

	auto initialise = [&]() {

		TaskMutex::ScopedLock lock;
		try
		{
			lock.acquire( mutex );
		}
		catch( ... )
		{
			numAcquisitionExceptions++;
			return;
		}

		if( !initialised )
		{
			initialisingThread = std::this_thread::get_id();
			try
			{
				lock.execute(
					[&]() {
						tbb::parallel_for(
							0, 1000,
							[&]( size_t i )
							{
								if( std::this_thread::get_id() != initialisingThread )
								{
									throw IECore::Exception( "Oops!" );
								}
								else
								{
									// Wait a bit so we don't just run through all the tasks
									// ourselves on the main thread.
									std::this_thread::sleep_for( std::chrono::milliseconds( 100 ) );
								}
							}
						);
					}
				);
			}
			catch( const IECore::Exception &e )
			{
				executionException = e.what();
			}
			initialised = true;
		}
	};

	tbb::parallel_for(
		0, 1000,
		[&initialise] ( int i ) {
			initialise();
		}
	);

	GAFFERTEST_ASSERTEQUAL( numAcquisitionExceptions.load(), 0 );
	GAFFERTEST_ASSERTEQUAL( executionException, "Oops!" );

}

void testTaskMutexDontSilentlyCancel()
{
	struct TestCancelled
	{
	};

	std::atomic_bool incorrectlyCancelled( false );

	auto runOrThrow = [&]( bool error ) {

		std::this_thread::sleep_for( std::chrono::milliseconds( 1 ) );

		if( error )
		{
			throw TestCancelled();
		}

		bool completed = false;

		// This lock.execute should simply run the functor, since we're creating a fresh
		// mutex that can't possibly have any contention.  But the tbb machinery we're
		// using implicitly does a check if the task group has been cancelled, which
		// means that if one of the other tasks in the parallel_for has thrown an
		// exception, the task group may have been cancelled, and this will not actually
		// execute the functor.  It should, in that case, throw IECore::Cancelled.
		TaskMutex mutex;
		TaskMutex::ScopedLock lock( mutex );
		lock.execute(
			[&]() {
				completed = true;
			}
		);

		// If we haven't thrown an exception yet, then the function should have run
		// A cancellation of the parent task shouldn't silently halt the lock.execute
		if( !completed )
		{
			incorrectlyCancelled = true;
		}
	};

	try
	{
		tbb::parallel_for(
			0, 1000,
			[&runOrThrow] ( int i ) {
				runOrThrow( ( i % 10 ) == 9 );
			}
		);
	}
	catch( TestCancelled &e )
	{
	}

	GAFFERTEST_ASSERT( !incorrectlyCancelled.load() );
}

void testTaskMutexCancellation()
{
	TaskMutex mutex;

	auto executeWithLock = [&mutex] () {

		TaskMutex::ScopedLock lock( mutex );
		lock.execute(
			[] () { std::this_thread::sleep_for( std::chrono::milliseconds( 10 ) ); }
		);

	};

	// Launch many tasks that all acquire the same mutex and call `execute()`.

	tbb::task_group_context context;
	tbb::parallel_for(
		0, 10000,
		[&executeWithLock, &context] ( int i ) {
			executeWithLock();
			if( i % 10 == 9 )
			{
				// Once a few tasks are launched, cancel the execution
				// of the `parallel_for()`. This will cause TBB to cancel
				// calls to `execute()` so that they don't run the functor.
				// This exposed a bug whereby cancellation left the TaskMutex
				// in an invalid state, triggering a debug assertion in
				// `execute()`.
				context.cancel_group_execution();
			}
		},
		context
	);

}

} // namespace

void GafferTestModule::bindTaskMutexTest()
{
	def( "testTaskMutex", &testTaskMutex );
	def( "testTaskMutexWithinIsolate", &testTaskMutexWithinIsolate );
	def( "testTaskMutexJoiningOuterTasks", &testTaskMutexJoiningOuterTasks );
	def( "testTaskMutexHeavyContention", &testTaskMutexHeavyContention );
	def( "testTaskMutexAcquireOr", &testTaskMutexAcquireOr );
	def( "testTaskMutexExceptions", &testTaskMutexExceptions );
	def( "testTaskMutexWorkerExceptions", &testTaskMutexWorkerExceptions );
	def( "testTaskMutexDontSilentlyCancel", &testTaskMutexDontSilentlyCancel );
	def( "testTaskMutexCancellation", &testTaskMutexCancellation );
}
