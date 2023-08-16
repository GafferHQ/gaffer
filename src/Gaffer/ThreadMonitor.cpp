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

#include "Gaffer/ThreadMonitor.h"

#include "Gaffer/Plug.h"
#include "Gaffer/Process.h"

using namespace Gaffer;

namespace
{

static std::atomic<int> g_threadIdCounter = 0;
ThreadMonitor::ProcessesPerThread g_emptyStatistics;

} // namespace

ThreadMonitor::ThreadData::ThreadData()
	:	id( thisThreadId() )
{
}

ThreadMonitor::ThreadMonitor( const std::vector<IECore::InternedString> &processMask )
	:	m_processMask( processMask )
{
}

ThreadMonitor::~ThreadMonitor()
{
}

ThreadMonitor::ThreadId ThreadMonitor::thisThreadId()
{
	thread_local int id = g_threadIdCounter++;
	return id;
}

const ThreadMonitor::PlugMap &ThreadMonitor::allStatistics() const
{
	collate();
	return m_statistics;
}

const ThreadMonitor::ProcessesPerThread &ThreadMonitor::plugStatistics( const Plug *plug ) const
{
	collate();
	auto it = m_statistics.find( plug );
	if( it == m_statistics.end() )
	{
		return g_emptyStatistics;
	}
	return it->second;
}

const ThreadMonitor::ProcessesPerThread &ThreadMonitor::combinedStatistics() const
{
	collate();
	return m_combinedStatistics;
}

void ThreadMonitor::processStarted( const Process *process )
{
	if( std::find( m_processMask.begin(), m_processMask.end(), process->type() ) == m_processMask.end() )
	{
		return;
	}

	ThreadData &threadData = m_threadData.local();
	threadData.processesPerPlug[process->plug()]++;
}

void ThreadMonitor::processFinished( const Process *process )
{
}

void ThreadMonitor::collate() const
{
	for( auto &threadData : m_threadData )
	{
		for( const auto &[plug, count] : threadData.processesPerPlug )
		{
			m_statistics[plug][threadData.id] += count;
			m_combinedStatistics[threadData.id] += count;
		}
		threadData.processesPerPlug.clear();
	}
}
