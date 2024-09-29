//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2024, Cinesite VFX Ltd. All rights reserved.
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
#include "Gaffer/ValuePlug.h"

#include "boost/functional/hash.hpp"

#include <chrono>
#include <unordered_map>
#include <unordered_set>

namespace GafferScene
{

/// A monitor which detects dependencies of the scene globals on other
/// properties of the scene. Such dependencies can have a dramatic impact on
/// RenderPassEditor and Dispatch performance and should generally be avoided.
class GAFFER_API GlobalsMonitor : public Gaffer::Monitor
{

	public :

		GlobalsMonitor();
		~GlobalsMonitor() override;

		IE_CORE_DECLAREMEMBERPTR( GlobalsMonitor )

		/// Records a dependency of the scene globals on some other property of
		/// the scene.
		struct GAFFER_API Dependency
		{
			/// The `ScenePlug::globalsPlug()` which has the dependency.
			const Gaffer::ValuePlug *globalsPlug() const;
			/// The upstream ScenePlug child that is depended upon.
			const Gaffer::ValuePlug *dependency() const;
			/// The full chain of the dependency, starting with `globalsPlug()`
			/// and ending with `dependency()`, and including any intermediate
			/// dependencies and connections.
			std::vector<Gaffer::ConstPlugPtr> plugs;
			/// The time spent evaluating the dependency.
			std::chrono::nanoseconds timeCost = std::chrono::nanoseconds( 0 );
		};

		struct GAFFER_API DependencySetHash /// \todo CAN WE REMOVE FROM PUBLIC API? MAYBE JUST EXPOSE `vector<Dependency>`?
		{
			size_t operator() ( const Dependency &v ) const
			{
				size_t result = 0;
				for( const auto &p : v.plugs )
				{
					boost::hash_combine( result, std::hash<const void *>()( p.get() ) );
				}
				return result;
			}
		};

		struct GAFFER_API DependencySetEqual { bool operator() ( const Dependency &a, const Dependency &b ) const { return a.plugs == b.plugs; } };
		using DependencySet = std::unordered_set<Dependency, DependencySetHash, DependencySetEqual>;
		const DependencySet &dependencies() const;

	protected :

		void processStarted( const Gaffer::Process *process ) override;
		void processFinished( const Gaffer::Process *process ) override;

	private :

		using Clock = std::chrono::high_resolution_clock;
		using TimePoint = Clock::time_point;
		using ProcessStartTimes = std::unordered_map<const Gaffer::Process *, TimePoint>;
		using Mutex = tbb::spin_rw_mutex;

		Mutex m_mutex;
		ProcessStartTimes m_processStartTimes;
		DependencySet m_dependencies;

		// For performance reasons we accumulate our statistics into
		// thread local storage while computations are running.
		// struct ThreadData
		// {
		// 	// Stores the per-plug statistics captured by this thread.
		// 	StatisticsMap statistics;
		// 	// Stack of durations pointing into the statistics map.
		// 	// The top of the stack is the duration we're billing the
		// 	// current chunk of time to.
		// 	using DurationStack = std::stack<boost::chrono::nanoseconds *>;
		// 	DurationStack durationStack;
		// 	// The last time measurement we made.
		// 	boost::chrono::high_resolution_clock::time_point then;
		// };

		//tbb::enumerable_thread_specific<ThreadData, tbb::cache_aligned_allocator<ThreadData>, tbb::ets_key_per_instance> m_threadData;

		// Then when we want to query it, we collate it into m_statistics.
		// void collate() const;
		// mutable StatisticsMap m_statistics;
		// mutable Statistics m_combinedStatistics;

};

IE_CORE_DECLAREPTR( GlobalsMonitor )

} // namespace GafferScene
