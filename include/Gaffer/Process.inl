//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2022, Image Engine Design Inc. All rights reserved.
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

#include "tbb/concurrent_hash_map.h"
#include "tbb/spin_mutex.h"
#include "tbb/task_arena.h"
#include "tbb/task_group.h"

#include <unordered_set>
#include <variant>

namespace Gaffer
{

/// Process Graph Overview
/// ======================
///
/// > Note : These notes (and the Process design itself) are heavily biased
/// towards ValuePlug and ComputeNode, and their associated ComputeProcess and
/// HashProcess.
///
/// It's tempting to think that because processes are stack-allocated, they each
/// have a single parent process waiting for them to complete, and that each
/// process is only waiting on a single child. It's also tempting to think that
/// there is a one-to-one correspondence between nodes and processes.
///
///    Node graph      Process graph
///    ----------      -------------
///
///     AddNode1            o    current process
///        |                |
///     AddNode2            o    waiting process (lower in stack)
///        |                |
///     AddNode3            o    waiting process (even lower in stack)
///
/// While that is true for the simple case shown above, the reality is far more
/// complicated due to contexts, multithreading, task collaboration and hash
/// aliasing.
///
/// Contexts
/// --------
///
/// Processes are operations being performed by a node for a particular plug, in
/// a _particular context_. The topology of the process graph does not
/// correspond directly to the topology of the node graph itself. Rather, the
/// process graph is generated dynamically in response to each process launching
/// upstream processes it depends on.
///
///      Loop <---       o  Loop,    loop:index=0
///       |      |       |
///       v      |       o  AddNode, loop:index=0
///      AddNode--       |
///                      o  Loop,    loop:index=1
///                      |
///                      o  AddNode, loop:index=1
///                      |
///                      o ...
///
/// As this example shows, cyclic _connections_ between plugs are even OK
/// provided that each process launches child _processes_ in a different context,
/// meaning that there are no cyclic dependencies between _processes_.
/// Even in this case, every process has only a single child and a single
/// parent, all living on the stack of a single thread, so the topology of
/// our process graph remains completely linear. But that ends as soon as
/// we consider multithreading.
///
/// Multithreading
/// --------------
///
/// A single process can use TBB tasks to launch many child processes that may
/// each be run on a different thread :
///
///      Random           o  o  o  current processes, one per thread
///        |               \ | /
///     Collect              o     waiting process
///
/// In this case, a single parent process may be waiting for multiple children
/// to complete. Our simple linear "graph" is now a directed tree (I'm using
/// terminology loosely here, I think the official term would be an
/// "arborescence").
///
/// This doesn't present any great obstacle in itself - the only new requirement
/// is that each TBB task scopes the ThreadState from the parent process, so
/// that we can associate the tasks's processes with the correct parent and run them in
/// the correct context. But it does highlight that a parent process may have
/// many children, and that processes may perform arbitrarily expensive amounts
/// of work.
///
/// Task collaboration
/// ------------------
///
/// Now that we know there can be processes in-flight on each thread, we need to
/// consider what happens if two or more threads simultaneously want a result
/// from the same not-yet-run upstream process. Gaffer cannot query the upstream
/// dependencies for a process before launching it, and therefore cannot perform
/// any up-front task scheduling. So in the example below, when two threads are
/// each running their own process and they dynamically turn out to require the
/// same upstream dependency, we need to deal with it dynamically.
///
///          AddNode1              ?  ?
///           /  \                 |  |
///    AddNode2  AddNode3          o  o
///
/// One approach is to simply allow each thread to run their own copy of the
/// process redundantly, and in fact this is a reasonable strategy that we do use
/// for lightweight processes.
///
///          AddNode1              o  o
///           /  \                 |  |
///    AddNode2  AddNode3          o  o
///
/// But where a process is expensive, duplication is not
/// an option. We need to arrange things such that we launch the upstream
/// compute on one thread, and have the other wait for its completion.
///
///         Collect                  o
///           /  \                  / \  < second thread waiting for process
///    AddNode2  AddNode3          o   o   launched by first thread
///
/// Ideally we don't want the waiting thread to simply block or spin though, as
/// that quickly reduces to only a single thread doing useful work. Instead we
/// want to provide the facility for waiting threads to _collaborate_, by
/// working on any TBB tasks spawned by the upstream process. We now have a new
/// requirement : we need to track the in-flight processes that are available
/// for collaboration, which we do in `Process::acquireCollaborativeResult()`.
/// And our process graphs can now contain diamond connections at collaboration
/// points, making them general directed acyclic graphs rather than simple
/// trees.
///
/// Hash aliasing
/// -------------
///
/// To track in-flight processes we need a way of identifying them, and we do
/// this using the same key that is used to cache their results. In the case of
/// ComputeProcess, the key is a hash generated by `ComputeNode::hash()`, which
/// must uniquely identify the result of the process.
///
/// But we have a problem : this hash can _alias_, and indeed it is encouraged
/// to. By aliasing, we mean that two processes can have the same hash provided
/// that they will generate the same result. For example, two different
/// SceneReader nodes will share hashes if they are each reading from the same
/// file. Or two locations within a scene will share hashes if they are known to
/// generate identical objects. In both cases, aliasing the hashes allows us to
/// avoid redundant computes and the creation of redundant cache entries. But this
/// adds complexity to the process graph - through hash aliasing, processes can
/// end up collaborating on nodes they have no actual connection to.
///
///      Collect1      Collect2        o   < Collect1 and Collect2 have the same
///         |             |           / \  < hash, so Expression2 is now
///    Expression1   Expression2     o   o < collaborating on Collect1!
///
/// Again, this is desirable as it reduces redundant work. But hashes can also
/// alias in less predictable ways. As `ExpressionTest.testHashAliasing`
/// shows, it's possible to create a node network such that a downstream node
/// depends on an upstream node with an _identical hash_. If we attempt process
/// collaboration in this case, we create a cyclic dependency that results in
/// a form of deadlock.
///
///    Expression1
///         |
///    Expression2           o-----
///         |                |    |
///    Expression3           o<----
///
/// This is _the_ key problem in our management of threaded collaborative
/// processes. We want node authors to be free to alias hashes without
/// constraint, to reduce redundant computes and cache pressure to the maximum
/// extent possible. But with the right node graph, _any_ aliasing may
/// lead to a cyclic dependency evolving dynamically in the corresponding
/// process graph.
///
/// In practice, such cyclic dependencies are rare, but not rare enough
/// that we can neglect them completely. Our stragegy is therefore to
/// perform collaboration wherever we can, but to replace it with one
/// additional "redundant" process where collaboration would cause a
/// cycle.
///
///    Expression1           o   < this process has the same hash...
///         |                |
///    Expression2           o
///         |                |
///    Expression3           o   < ...as this one
///
/// Conceptually this is relatively simple, but it is made trickier by the
/// constantly mutating nature of the process graph. Although all new processes
/// are always added at the leafs of the process "tree", collaboration can insert
/// arbitrary diamond dependencies between existing processes anywhere in the
/// graph, at any time, and from any thread, and our cycle checking must account
/// for this without introducing excessive overhead.
///
/// > Tip : At this point it is useful to forget about nodes and plugs and
/// connections and to instead consider the process graph largely in the
/// abstract. Processes are vertices in the graph. Dependencies are directed
/// edges between processes. Edge insertion may be attempted anywhere by
/// collaboration at any time, and cycles must be avoided.

/// A "vertex" in the process graph where collaboration may be performed. We
/// only track collaborative processes because non-collaborative processes can't
/// introduce edges that could lead to cycles.
class GAFFER_API Process::Collaboration : public IECore::RefCounted
{

	public :

		// Work around https://bugs.llvm.org/show_bug.cgi?id=32978
		~Collaboration() noexcept( true ) override;

		IE_CORE_DECLAREMEMBERPTR( Collaboration );

		// Arena and task group used to allow waiting threads to participate
		// in collaborative work.
		tbb::task_arena arena;
		tbb::task_group taskGroup;

		using Set = std::unordered_set<const Collaboration *>;
		// Collaborations depending directly on this one.
		Set dependents;

		// Returns true if this collaboration depends on `collaboration`, either
		// directly or indirectly via other collaborations it depends on.
		// The caller of this function must hold `g_dependentsMutex`.
		bool dependsOn( const Collaboration *collaboration ) const;

		// Protects access to `dependents` on _all_ Collaborations.
		static tbb::spin_mutex g_dependentsMutex;

};

/// Collaboration subclass specific to a single type of process, providing storage for the result
/// and tracking of the currently in-flight collaborations by cache key.
///
/// > Note : We track dependencies between all types of collaboration, not just between like types.
template<typename ProcessType>
class Process::TypedCollaboration : public Process::Collaboration
{
	public :

		std::variant<std::monostate, std::exception_ptr, typename ProcessType::ResultType> result;

		typename ProcessType::ResultType resultOrException() const
		{
			return std::visit(
				[] ( auto &&v ) -> typename ProcessType::ResultType
				{
					using T = std::decay_t<decltype( v )>;
					if constexpr( std::is_same_v<T, typename ProcessType::ResultType> )
					{
						return v;
					}
					else if constexpr( std::is_same_v<T, std::exception_ptr> )
					{
						std::rethrow_exception( v );
					}
					else
					{
						throw IECore::Cancelled();
					}
				},
				result
			);
		}

		IE_CORE_DECLAREMEMBERPTR( TypedCollaboration );

		using PendingCollaborations = tbb::concurrent_hash_map<typename ProcessType::CacheType::KeyType, std::vector<Ptr>>;
		static PendingCollaborations g_pendingCollaborations;

};

template<typename ProcessType>
typename Process::TypedCollaboration<ProcessType>::PendingCollaborations Process::TypedCollaboration<ProcessType>::g_pendingCollaborations;

template<typename ProcessType, typename... ProcessArguments>
typename ProcessType::ResultType Process::acquireCollaborativeResult(
	const typename ProcessType::CacheType::KeyType &cacheKey, ProcessArguments&&... args
)
{
	const ThreadState &threadState = ThreadState::current();
	const Collaboration *currentCollaboration = threadState.process() ? threadState.process()->m_collaboration : nullptr;

	// Check for any in-flight computes for the same cache key. If we find a
	// suitable one, we'll wait for it and use its result.

	using CollaborationType = TypedCollaboration<ProcessType>;
	using CollaborationTypePtr = typename CollaborationType::Ptr;

	typename CollaborationType::PendingCollaborations::accessor accessor;
	CollaborationType::g_pendingCollaborations.insert( accessor, cacheKey );

	for( const auto &candidate : accessor->second )
	{
		// Check to see if we can safely collaborate on `candidate` without
		// risking deadlock. We optimistically perform the cheapest checks
		// first; if we're not already in a collaboration, or if the
		// collaboration we're in already depends on the candidate (via another
		// thread of execution) then we're good to go.
		//
		// The call to `candidate->dependents.find()` is safe even though we
		// don't hold `g_dependentsMutex`, because we hold the accessor for
		// `candidate`, and that is always held by any writer of
		// `candidate->dependents`.
		if( currentCollaboration && candidate->dependents.find( currentCollaboration ) == candidate->dependents.end() )
		{
			// Perform much more expensive check for potential deadlock - we
			// mustn't become a dependent of `candidate` if it already depends
			// on us. This requires traversing all dependents of
			// `currentCollaboration` while holding `g_dependentsMutex` (so they
			// can't be modified while we read).
			tbb::spin_mutex::scoped_lock dependentsLock( Collaboration::g_dependentsMutex );
			if( !candidate->dependsOn( currentCollaboration ) )
			{
				// We're safe to collaborate. Add ourself as a dependent before
				// releasing `g_dependentsMutex`.
				candidate->dependents.insert( currentCollaboration );
			}
			else
			{
				continue;
			}
		}

		// We've found an in-flight process we can wait on without causing
		// deadlock. Join its `task_arena` and wait on the result, so we get to
		// work on any TBB tasks it has created.
		//
		// > Note : We need to own a reference to `collaboration` because the
		// thread that created it may drop its own reference as soon as we call
		// `release()`, because that allows the original `run_and_wait()` to
		// complete.
		//
		// > Caution : Now the primary `run_and_wait()` can return, any other
		//  waiting threads can also move on. That means that
		//  `collaboration->dependents` may now contain dangling pointers. Do
		//  not access them!

		CollaborationTypePtr collaboration = candidate;
		accessor.release();

		collaboration->arena.execute(
			[&]{ return collaboration->taskGroup.wait(); }
		);

		return collaboration->resultOrException();
	}

	// No suitable in-flight collaborations, so we'll create one of our own.
	// First though, check the cache one more time, in case another thread has
	// started and finished an equivalent collaboration since we first checked.

	if( auto result = ProcessType::g_cache.getIfCached( cacheKey ) )
	{
		return *result;
	}

	CollaborationTypePtr collaboration = new CollaborationType;
	if( currentCollaboration )
	{
		// No need to hold `m_dependentsMutex` here because other threads can't
		// access `collaboration->dependents` until we publish it.
		collaboration->dependents.insert( currentCollaboration );
	}

	collaboration->arena.execute(
		[&] {
			return collaboration->taskGroup.run_and_wait(
				[&] {
					// Publish ourselves so that other threads can collaborate
					// by calling `collaboration->taskGroup.wait()`.
					accessor->second.push_back( collaboration );
					accessor.release();

					try
					{
						ProcessType process( std::forward<ProcessArguments>( args )... );
						process.m_collaboration = collaboration.get();
						collaboration->result = process.run();
						// Publish result to cache before we remove ourself from
						// `g_pendingCollaborations`, so that other threads will
						// be able to get the result one way or the other.
						ProcessType::g_cache.setIfUncached(
							cacheKey, std::get<typename ProcessType::ResultType>( collaboration->result ),
							ProcessType::cacheCostFunction
						);
					}
					catch( ... )
					{
						// We want to manage the exception ourselves anyway,
						// but its also imperative that we don't allow `task_group::wait()`
						// to see it, because then we'd hit a thread-safety bug in
						// `tbb::task_group_context::reset()`.
						collaboration->result = std::current_exception();
					}

					// Now we're done, remove `collaboration` from the pending collaborations.
					[[maybe_unused]] const bool found = CollaborationType::g_pendingCollaborations.find( accessor, cacheKey );
					assert( found );
					auto toErase = std::find( accessor->second.begin(), accessor->second.end(), collaboration );
					assert( toErase != accessor->second.end() );
					accessor->second.erase( toErase );
					if( accessor->second.empty() )
					{
						CollaborationType::g_pendingCollaborations.erase( accessor );
					}
					accessor.release();
				}
			);
		}
	);

	return collaboration->resultOrException();
}

inline bool Process::forceMonitoring( const ThreadState &s, const Plug *plug, const IECore::InternedString &processType )
{
	if( s.m_mightForceMonitoring )
	{
		return Process::forceMonitoringInternal( s, plug, processType );
	}

	return false;
}

} // Gaffer
