//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFER_PERFORMANCEMONITOR_H
#define GAFFER_PERFORMANCEMONITOR_H

#include "Gaffer/Monitor.h"

#include "IECore/RefCounted.h"

#include "boost/chrono.hpp"
#include "boost/unordered_map.hpp"

#include "tbb/enumerable_thread_specific.h"

#include <stack>

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( Plug )

/// A monitor which collects statistics about the frequency
/// and duration of hash and compute processes per plug.
class GAFFER_API PerformanceMonitor : public Monitor
{

	public :

		PerformanceMonitor();
		~PerformanceMonitor() override;

		IE_CORE_DECLAREMEMBERPTR( PerformanceMonitor )

		struct GAFFER_API Statistics
		{

			Statistics(
				size_t hashCount = 0,
				size_t computeCount = 0,
				boost::chrono::nanoseconds hashDuration = boost::chrono::nanoseconds( 0 ),
				boost::chrono::nanoseconds computeDuration = boost::chrono::nanoseconds( 0 )
			);

			size_t hashCount;
			size_t computeCount;
			boost::chrono::nanoseconds hashDuration;
			boost::chrono::nanoseconds computeDuration;

			Statistics & operator += ( const Statistics &rhs );

			bool operator == ( const Statistics &rhs );
			bool operator != ( const Statistics &rhs );

		};

		using StatisticsMap = boost::unordered_map<ConstPlugPtr, Statistics>;

		const StatisticsMap &allStatistics() const;
		const Statistics &plugStatistics( const Plug *plug ) const;
		const Statistics &combinedStatistics() const;


	protected :

		void processStarted( const Process *process ) override;
		void processFinished( const Process *process ) override;

	private :

		// For performance reasons we accumulate our statistics into
		// thread local storage while computations are running.
		struct ThreadData
		{
			// Stores the per-plug statistics captured by this thread.
			StatisticsMap statistics;
			// Stack of durations pointing into the statistics map.
			// The top of the stack is the duration we're billing the
			// current chunk of time to.
			using DurationStack = std::stack<boost::chrono::nanoseconds *>;
			DurationStack durationStack;
			// The last time measurement we made.
			boost::chrono::high_resolution_clock::time_point then;
		};

		tbb::enumerable_thread_specific<ThreadData, tbb::cache_aligned_allocator<ThreadData>, tbb::ets_key_per_instance> m_threadData;

		// Then when we want to query it, we collate it into m_statistics.
		void collate() const;
		mutable StatisticsMap m_statistics;
		mutable Statistics m_combinedStatistics;

};

IE_CORE_DECLAREPTR( PerformanceMonitor )

} // namespace Gaffer

#endif // GAFFER_PERFORMANCEMONITOR_H
