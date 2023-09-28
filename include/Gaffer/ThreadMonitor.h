//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2023, Cinesite VFX Ltd. All rights reserved.
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

#pragma once

#include "Gaffer/Monitor.h"

#include "tbb/enumerable_thread_specific.h"

#include <unordered_map>

// Image Engine is on Boost 107300 which doesn't have the specialization of std::hash
// for boost smart pointers
#if BOOST_VERSION < 107400
namespace std
{

template <>
struct hash<Gaffer::ConstPlugPtr>
{
	size_t operator()( const Gaffer::ConstPlugPtr &p ) const
	{
		return std::hash<const void*>()( p.get() );
	}
};

} // namespace std
#endif


namespace Gaffer
{

IE_CORE_FORWARDDECLARE( Plug )

/// A monitor which collects information about which threads
/// initiated processes on each plug.
class GAFFER_API ThreadMonitor : public Monitor
{

	public :

		ThreadMonitor( const std::vector<IECore::InternedString> &processMask = { "computeNode:compute" } );
		~ThreadMonitor() override;

		IE_CORE_DECLAREMEMBERPTR( ThreadMonitor )

		/// Numeric identifier for a thread. Using our own identifier rather
		/// than `std::thread::id` so that we can bind it to Python (and assign
		/// human-readable contiguous values).
		using ThreadId = int;
		/// Returns the `ThreadId` for the calling thread.
		static ThreadId thisThreadId();
		/// Maps from `ThreadId` to the number of times a process has been
		/// invoked on that thread.
		using ProcessesPerThread = std::unordered_map<ThreadId, size_t>;
		/// Stores per-thread process counts per-plug.
		using PlugMap = std::unordered_map<ConstPlugPtr, ProcessesPerThread>;

		/// Query functions. These are not thread-safe, and must be called
		/// only when the Monitor is not active (as defined by `Monitor::Scope`).
		const PlugMap &allStatistics() const;
		const ProcessesPerThread &plugStatistics( const Plug *plug ) const;
		const ProcessesPerThread &combinedStatistics() const;

	protected :

		void processStarted( const Process *process ) override;
		void processFinished( const Process *process ) override;

	private :

		const std::vector<IECore::InternedString> m_processMask;

		// We collect statistics into a per-thread data structure to avoid contention.
		struct ThreadData
		{
			ThreadData();
			using ProcessesPerPlug = std::unordered_map<ConstPlugPtr, size_t>;
			ThreadId id;
			ProcessesPerPlug processesPerPlug;
		};
		mutable tbb::enumerable_thread_specific<ThreadData> m_threadData;

		// Then when we want to query it, we collate it into `m_statistics`.
		void collate() const;
		mutable PlugMap m_statistics;
		mutable ProcessesPerThread m_combinedStatistics;

};

IE_CORE_DECLAREPTR( ThreadMonitor )

} // namespace Gaffer
