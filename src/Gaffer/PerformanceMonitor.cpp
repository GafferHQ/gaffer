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

#include "Gaffer/PerformanceMonitor.h"

#include "Gaffer/Plug.h"
#include "Gaffer/Process.h"

using namespace Gaffer;

static IECore::InternedString g_hashType( "computeNode:hash" );
static IECore::InternedString g_computeType( "computeNode:compute" );
static PerformanceMonitor::Statistics g_emptyStatistics;

//////////////////////////////////////////////////////////////////////////
// PerformanceMonitor::Statistics
//////////////////////////////////////////////////////////////////////////

PerformanceMonitor::Statistics::Statistics( size_t hashCount, size_t computeCount, boost::chrono::nanoseconds hashDuration, boost::chrono::nanoseconds computeDuration )
	:	hashCount( hashCount ), computeCount( computeCount ), hashDuration( hashDuration ), computeDuration( computeDuration )
{
}

PerformanceMonitor::Statistics & PerformanceMonitor::Statistics::operator += ( const Statistics &rhs )
{
	hashCount += rhs.hashCount;
	computeCount += rhs.computeCount;
	hashDuration += rhs.hashDuration;
	computeDuration += rhs.computeDuration;
	return *this;
}

bool PerformanceMonitor::Statistics::operator == ( const Statistics &rhs )
{
	return
		hashCount == rhs.hashCount &&
		computeCount == rhs.computeCount &&
		hashDuration == rhs.hashDuration &&
		computeDuration == rhs.computeDuration
	;
}

bool PerformanceMonitor::Statistics::operator != ( const Statistics &rhs )
{
	return !( *this == rhs );
}

//////////////////////////////////////////////////////////////////////////
// PerformanceMonitor
//////////////////////////////////////////////////////////////////////////

PerformanceMonitor::PerformanceMonitor()
{
}

PerformanceMonitor::~PerformanceMonitor()
{
}

const PerformanceMonitor::StatisticsMap &PerformanceMonitor::allStatistics() const
{
	collate();
	return m_statistics;
}

const PerformanceMonitor::Statistics &PerformanceMonitor::plugStatistics( const Plug *plug ) const
{
	collate();
	StatisticsMap::const_iterator it = m_statistics.find( plug );
	if( it == m_statistics.end() )
	{
		return g_emptyStatistics;
	}
	return it->second;
}

const PerformanceMonitor::Statistics &PerformanceMonitor::combinedStatistics() const
{
	collate();
	return m_combinedStatistics;
}


void PerformanceMonitor::processStarted( const Process *process )
{
	const IECore::InternedString type = process->type();
	if( type != g_hashType && type != g_computeType )
	{
		return;
	}

	ThreadData &threadData = m_threadData.local();

	boost::chrono::high_resolution_clock::time_point now = boost::chrono::high_resolution_clock::now();
	if( !threadData.durationStack.empty() )
	{
		*(threadData.durationStack.top()) += now - threadData.then;
	}
	threadData.then = now;

	Statistics &s = threadData.statistics[process->plug()];
	if( type == g_hashType )
	{
		s.hashCount++;
		threadData.durationStack.push( &s.hashDuration );
	}
	else
	{
		s.computeCount++;
		threadData.durationStack.push( &s.computeDuration );
	}
}

void PerformanceMonitor::processFinished( const Process *process )
{
	const IECore::InternedString type = process->type();
	if( type != g_hashType && type != g_computeType )
	{
		return;
	}

	ThreadData &threadData = m_threadData.local();
	boost::chrono::high_resolution_clock::time_point now = boost::chrono::high_resolution_clock::now();
	*(threadData.durationStack.top()) += now - threadData.then;
	threadData.durationStack.pop();
	threadData.then = now;
}

void PerformanceMonitor::collate() const
{
	tbb::enumerable_thread_specific<ThreadData, tbb::cache_aligned_allocator<ThreadData>, tbb::ets_key_per_instance>::iterator it, eIt;
	for( it = m_threadData.begin(), eIt = m_threadData.end(); it != eIt; ++it )
	{
		StatisticsMap &m = it->statistics;
		for( StatisticsMap::const_iterator mIt = m.begin(), meIt = m.end(); mIt != meIt; ++mIt )
		{
			m_statistics[mIt->first] += mIt->second;
			m_combinedStatistics += mIt->second;
		}
		m.clear();
	}
}
