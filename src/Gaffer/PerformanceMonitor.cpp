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
#include "Gaffer/Process.h"
#include "Gaffer/Plug.h"

using namespace Gaffer;

/// \todo If we expose ValuePlug::HashProcess and ValuePlug::ComputeProcess
/// then we can use the types defined there directly.
static IECore::InternedString g_hashType( "computeNode:hash" );
static IECore::InternedString g_computeType( "computeNode:compute" );
static PerformanceMonitor::Statistics g_emptyStatistics;

//////////////////////////////////////////////////////////////////////////
// PerformanceMonitor::Statistics
//////////////////////////////////////////////////////////////////////////

PerformanceMonitor::Statistics::Statistics( size_t hashCount, size_t computeCount )
	:	hashCount( hashCount ), computeCount( computeCount )
{
}

PerformanceMonitor::Statistics & PerformanceMonitor::Statistics::operator += ( const Statistics &rhs )
{
	hashCount += rhs.hashCount;
	computeCount += rhs.computeCount;
	return *this;
}

bool PerformanceMonitor::Statistics::operator == ( const Statistics &rhs )
{
	return hashCount == rhs.hashCount && computeCount == rhs.computeCount;
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

void PerformanceMonitor::processStarted( const Process *process )
{
	const IECore::InternedString type = process->type();
	if( type != g_hashType && type != g_computeType )
	{
		return;
	}

	Statistics &s = m_threadStatistics.local()[process->plug()];
	if( type == g_hashType )
	{
		s.hashCount++;
	}
	else
	{
		s.computeCount++;
	}
}

void PerformanceMonitor::processFinished( const Process *process )
{
}

void PerformanceMonitor::collate() const
{
	tbb::enumerable_thread_specific<StatisticsMap>::iterator it, eIt;
	for( it = m_threadStatistics.begin(), eIt = m_threadStatistics.end(); it != eIt; ++it )
	{
		StatisticsMap &m = *it;
		for( StatisticsMap::const_iterator mIt = m.begin(), meIt = m.end(); mIt != meIt; ++mIt )
		{
			m_statistics[mIt->first] += mIt->second;
		}
		m.clear();
	}
}
