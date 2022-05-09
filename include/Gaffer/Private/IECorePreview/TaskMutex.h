//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2019, Image Engine Design Inc. All rights reserved.
//
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//
//     * Redistributions of source code must retain the above copyright
//       notice, this list of conditions and the following disclaimer.
//
//     * Redistributions in binary form must reproduce the above copyright
//       notice, this list of conditions and the following disclaimer in the
//       documentation and/or other materials provided with the distribution.
//
//     * Neither the name of Image Engine Design nor the names of any
//       other contributors to this software may be used to endorse or
//       promote products derived from this software without specific prior
//       written permission.
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

#ifndef IECOREPREVIEW_TASKMUTEX_H
#define IECOREPREVIEW_TASKMUTEX_H

#include "IECore/Canceller.h"
#include "IECore/RefCounted.h"

#include "boost/container/flat_set.hpp"
#include "boost/noncopyable.hpp"

#include "tbb/spin_mutex.h"
#include "tbb/spin_rw_mutex.h"

#include "tbb/task_arena.h"
#include "tbb/task_group.h"
// Enable preview feature that allows us to construct a `task_scheduler_observer`
// for a specific `task_arena`. This feature becomes officially supported in
// Intel TBB 2019 Update 5, so it is not going to be removed.
#define TBB_PREVIEW_LOCAL_OBSERVER 1
#include "tbb/task_scheduler_observer.h"

#include <iostream>
#include <optional>
#include <thread>

namespace IECorePreview
{

/// Mutex where threads waiting for access can collaborate on TBB tasks
/// spawned by the holder. Useful for performing expensive delayed
/// initialisation of shared resources.
///
/// Based on an example posted by "Alex (Intel)" on the following thread :
///
/// https://software.intel.com/en-us/forums/intel-threading-building-blocks/topic/703652
///
/// Simple usage :
///
/// 	```
/// 	void performExpensiveInitialisationUsingTBB();
/// 	static bool g_initialised;
/// 	static TaskMutex g_mutex;
/// 	...
/// 	TaskMutex::ScopedLock lock( g_mutex );
/// 	if( !g_initialised )
/// 	{
/// 		lock.execute( []{ performExpensiveInitialisationUsingTBB(); } );
/// 		g_initialised = true;
/// 	}
/// 	// Use resource here, while lock is still held.
/// ```
///
/// Improved performance via reader locks :
///
/// 	```
/// 	...
/// 	// Optimistically take a reader lock, sufficient to allow us
/// 	// to read from the resource if it is already initialised.
/// 	TaskMutex::ScopedLock lock( g_mutex, /* write = */ false );
/// 	if( !g_initialised )
/// 	{
/// 		// Upgrade to writer lock, so we can initialise the shared resource.
/// 		lock.upgradeToWriter();
/// 		if( !g_initialised ) // Check again, we may not be the first to get a write lock
/// 		{
/// 			lock.execute( []{ performExpensiveInitialisationUsingTBB(); } );
/// 			g_initialised = true;
/// 		}
/// 	}
/// 	// Use resource here, while lock is still held.
/// ```
class TaskMutex : boost::noncopyable
{

	using InternalMutex = tbb::spin_rw_mutex;

	public :

		TaskMutex()
		{
		}

		/// Used to acquire a lock on the mutex and release it
		/// automatically in an exception-safe way. Equivalent to
		/// the `scoped_lock` of the standard TBB mutexes.
		class ScopedLock : boost::noncopyable
		{

			public :

				ScopedLock()
					:	m_mutex( nullptr ), m_lockType( LockType::None )
				{
				}

				ScopedLock( TaskMutex &mutex, bool write = true, bool acceptWork = true )
					:	ScopedLock()
				{
					acquire( mutex, write, acceptWork );
				}

				~ScopedLock()
				{
					if( m_mutex )
					{
						release();
					}
				}

				/// Acquires a lock on `mutex`. If `acceptWork` is true, then may perform
				/// work on behalf of `execute()` while waiting.
				void acquire( TaskMutex &mutex, bool write = true, bool acceptWork = true )
				{
					const LockType l = write ? LockType::Write : LockType::Read;
					tbb::internal::atomic_backoff backoff;
					while( !acquireOr( mutex, l, [acceptWork]( bool workAvailable ){ return acceptWork; } ) )
					{
						backoff.pause();
					}
				}

				/// Upgrades a previously-acquired reader lock to a full writer
				/// lock. Returns true if the upgrade was achieved without
				/// temporarily releasing the lock, and false otherwise.
				bool upgradeToWriter()
				{
					assert( m_mutex && (m_lockType == LockType::Read) );
					m_lockType = LockType::Write;
					return m_lock.upgrade_to_writer();
				}

				/// Calls `f` in a way that allows threads waiting for the lock to perform
				/// TBB tasks on its behalf. Should only be called by the holder of a write lock.
				template<typename F>
				void execute( F &&f )
				{
					assert( m_mutex && m_lockType == LockType::Write );

					ExecutionStateMutex::scoped_lock executionStateLock( m_mutex->m_executionStateMutex );
					assert( !m_mutex->m_executionState );
					m_mutex->m_executionState = new ExecutionState;
					executionStateLock.release();

					// Wrap `f` to capture any exceptions it throws. If we allow
					// `task_group::wait()` to see them, we hit a thread-safety
					// bug in `tbb::task_group_context::reset()`.
					std::exception_ptr exception;
					auto fWrapper = [&f, &exception] {
						try
						{
							f();
						}
						catch( ... )
						{
							exception = std::current_exception();
						}
					};

					std::optional<tbb::task_group_status> status;
					m_mutex->m_executionState->arena.execute(
						[this, &fWrapper, &status] {
							// Prior to TBB 2018 Update 3, `run_and_wait()` is buggy,
							// causing calls to `wait()` on other threads to return
							// immediately rather than do the work we want. Use
							// `static_assert()` to ensure we never build with a buggy
							// version.
							static_assert( TBB_INTERFACE_VERSION >= 10003, "Minumum of TBB 2018 Update 3 required" );
							status = m_mutex->m_executionState->taskGroup.run_and_wait( fWrapper );
						}
					);

					assert( (bool)status );

					executionStateLock.acquire( m_mutex->m_executionStateMutex );
					m_mutex->m_executionState = nullptr;

					if( exception )
					{
						std::rethrow_exception( exception );
					}
					else if( status.value() == tbb::task_group_status::canceled )
					{
						throw IECore::Cancelled();
					}
				}

				/// Acquires mutex or returns false. Never does TBB tasks.
				bool tryAcquire( TaskMutex &mutex, bool write = true )
				{
					const LockType l = write ? LockType::Write : LockType::Read;
					return acquireOr( mutex, l, []( bool workAvailable ){ return false; } );
				}

				/// Releases the lock. This will be done automatically
				/// by ~ScopedLock, but may be called explicitly to release
				/// the lock early.
				void release()
				{
					assert( m_mutex );
					if( m_lockType != LockType::WorkerRead )
					{
						m_lock.release();
					}
					m_mutex = nullptr;
					m_lockType = LockType::None;
				}

				/// Advanced API
				/// ============
				///
				/// These methods provide advanced usage required by complex requirements
				/// in Gaffer's LRUCache. They should not be considered part of the canonical
				/// API.

				enum class LockType
				{
					None,
					// Multiple readers may coexist.
					Read,
					// Only a single writer can exist at a time, and the presence
					// of a writer prevents read locks being acquired.
					Write,
					// Artificial read lock, available only to threads performing
					// TBB tasks on behalf of `execute()`. These readers are
					// protected only by the original write lock held by the caller
					// of `execute()`. This means the caller of `execute()` _must_
					// delay any writes until _after_ `execute()` has returned.
					// A WorkerRead lock can not be upgraded via `upgradeToWriter()`.
					WorkerRead,
				};

				/// Tries to acquire the mutex, returning true on success. On failure,
				/// calls `workNotifier( bool workAvailable )`. If work is available and
				/// `workNotifier` returns true, then this thread will perform TBB tasks
				/// spawned by `execute()` until the work is complete. Returns false on
				/// failure regardless of whether or not work is done.
				template<typename WorkNotifier>
				bool acquireOr( TaskMutex &mutex, LockType lockType, WorkNotifier &&workNotifier )
				{
					assert( !m_mutex );
					assert( m_lockType == LockType::None );
					assert( lockType != LockType::None );

					if( m_lock.try_acquire( mutex.m_mutex, /* write = */ lockType == LockType::Write ) )
					{
						// Success!
						m_mutex = &mutex;
						m_lockType = lockType == LockType::WorkerRead ? LockType::Read : lockType;
						return true;
					}

					// Failed to acquire the mutex by regular means. We now need to
					// consider our interaction with any execution state introduced by a
					// current call to `execute()`.

					ExecutionStateMutex::scoped_lock executionStateLock( mutex.m_executionStateMutex );
					if( lockType == LockType::WorkerRead && mutex.m_executionState && mutex.m_executionState->arenaObserver.containsThisThread() )
					{
						// We're already doing work on behalf of `execute()`, so we can
						// take a WorkerRead lock.
						m_mutex = &mutex;
						m_lockType = lockType;
						return true;
					}

					const bool workAvailable = mutex.m_executionState.get();
					if( !workNotifier( workAvailable ) || !workAvailable )
					{
						return false;
					}

					// Perform work on behalf of `execute()`.

					ExecutionStatePtr executionState = mutex.m_executionState;
					executionStateLock.release();

					executionState->arena.execute(
						[&executionState]{ executionState->taskGroup.wait(); }
					);

					return false;
				}

				/// Returns the type of the lock currently held. If `acquireOr( WorkerRead )`
				/// is called successfully, this will return `Read` for an external lock and
				/// `WorkerRead` for an internal lock acquired by virtue of performing tasks
				/// for `execute()`.
				LockType lockType() const
				{
					return m_lockType;
				}

			private :

				InternalMutex::scoped_lock m_lock;
				TaskMutex *m_mutex;
				LockType m_lockType;

		};

	private :

		// The actual mutex that is held by the ScopedLock.
		InternalMutex m_mutex;

		// Tracks worker threads as they enter and exit an arena, so we can determine
		// whether or not the current thread is inside the arena. We use this to detect
		// recursion and allow any worker thread to obtain a recursive lock provided
		// they are currently performing work in service of `ScopedLock::execute()`.
		class ArenaObserver : public tbb::task_scheduler_observer
		{

			public :

				ArenaObserver( tbb::task_arena &arena )
					:	tbb::task_scheduler_observer( arena )
				{
					observe( true );
				}

				~ArenaObserver() override
				{
					observe( false );
				}

				bool containsThisThread()
				{
					Mutex::scoped_lock lock( m_mutex );
					return m_threadIdSet.find( std::this_thread::get_id() ) != m_threadIdSet.end();
				}

			private :

				void on_scheduler_entry( bool isWorker ) override
				{
					assert( !containsThisThread() );
					Mutex::scoped_lock lock( m_mutex );
					m_threadIdSet.insert( std::this_thread::get_id() );
				}

				void on_scheduler_exit( bool isWorker ) override
				{
					assert( containsThisThread() );
					Mutex::scoped_lock lock( m_mutex );
					m_threadIdSet.erase( std::this_thread::get_id() );
				}

				using Mutex = tbb::spin_mutex;
				using ThreadIdSet = boost::container::flat_set<std::thread::id>;
				Mutex m_mutex;
				ThreadIdSet m_threadIdSet;

		};

		// The mechanism we use to allow waiting threads
		// to participate in the work done by `execute()`.
		struct ExecutionState : public IECore::RefCounted
		{
			ExecutionState()
				:	arenaObserver( arena )
			{
			}

			// Work around https://bugs.llvm.org/show_bug.cgi?id=32978
			~ExecutionState() noexcept( true ) override
			{
			}

			// Arena and task group used to allow
			// waiting threads to participate in work.
			tbb::task_arena arena;
			tbb::task_group taskGroup;
			// Observer used to track which threads are
			// currently inside the arena.
			ArenaObserver arenaObserver;
		};
		IE_CORE_DECLAREPTR( ExecutionState );

		using ExecutionStateMutex = tbb::spin_mutex;
		ExecutionStateMutex m_executionStateMutex; // Protects m_executionState
		ExecutionStatePtr m_executionState;

};

} // namespace IECorePreview

#endif // IECOREPREVIEW_TASKMUTEX_H
