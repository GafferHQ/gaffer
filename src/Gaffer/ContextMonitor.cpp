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

#include "Gaffer/ContextMonitor.h"

#include "Gaffer/Context.h"
#include "Gaffer/Plug.h"
#include "Gaffer/Process.h"

using namespace std;
using namespace IECore;
using namespace Gaffer;

static ContextMonitor::Statistics g_emptyStatistics;

//////////////////////////////////////////////////////////////////////////
// ContextMonitor::Statistics
//////////////////////////////////////////////////////////////////////////

size_t ContextMonitor::Statistics::numUniqueContexts() const
{
	return m_contexts.size();
}

std::vector<IECore::InternedString> ContextMonitor::Statistics::variableNames() const
{
	vector<InternedString> result;
	for( VariableMap::const_iterator it = m_variables.begin(), eIt = m_variables.end(); it != eIt; ++it )
	{
		result.push_back( it->first );
	}
	return result;
}

size_t ContextMonitor::Statistics::numUniqueValues( IECore::InternedString variableName ) const
{
	VariableMap::const_iterator it = m_variables.find( variableName );
	if( it != m_variables.end() )
	{
		return it->second.size();
	}
	return 0;
}

ContextMonitor::Statistics & ContextMonitor::Statistics::operator += ( const Context *context )
{
	m_contexts.insert( context->hash() );
	vector<InternedString> names;
	context->names( names );
	for( vector<InternedString>::const_iterator it = names.begin(), eIt = names.end(); it != eIt; ++it )
	{
		m_variables[*it][context->variableHash( *it )] += 1;
	}
	return *this;
}

ContextMonitor::Statistics & ContextMonitor::Statistics::operator += ( const Statistics &rhs )
{
	m_contexts.insert( rhs.m_contexts.begin(), rhs.m_contexts.end() );
	for( VariableMap::const_iterator it = rhs.m_variables.begin(), eIt = rhs.m_variables.end(); it != eIt; ++it )
	{
		CountingMap &c = m_variables[it->first];
		for( CountingMap::const_iterator cIt = it->second.begin(), ceIt = it->second.end(); cIt != ceIt; ++cIt )
		{
			c[cIt->first] += cIt->second;
		}
	}
	return *this;
}

bool ContextMonitor::Statistics::operator == ( const Statistics &rhs )
{
	return m_contexts == rhs.m_contexts && m_variables == rhs.m_variables;
}

bool ContextMonitor::Statistics::operator != ( const Statistics &rhs )
{
	return !( *this == rhs );
}

//////////////////////////////////////////////////////////////////////////
// PerformanceMonitor
//////////////////////////////////////////////////////////////////////////

ContextMonitor::ContextMonitor( const GraphComponent *root )
	:	m_root( root )
{
}

ContextMonitor::~ContextMonitor()
{
}

const ContextMonitor::StatisticsMap &ContextMonitor::allStatistics() const
{
	collate();
	return m_statistics;
}

const ContextMonitor::Statistics &ContextMonitor::plugStatistics( const Plug *plug ) const
{
	collate();
	StatisticsMap::const_iterator it = m_statistics.find( plug );
	if( it == m_statistics.end() )
	{
		return g_emptyStatistics;
	}
	return it->second;
}

const ContextMonitor::Statistics &ContextMonitor::combinedStatistics() const
{
	collate();
	return m_combinedStatistics;
}

void ContextMonitor::processStarted( const Process *process )
{
	if( m_root && m_root != process->plug() && !m_root->isAncestorOf( process->plug() ) )
	{
		return;
	}
	ThreadData &threadData = m_threadData.local();
	threadData.statistics[process->plug()] += process->context();
}

void ContextMonitor::processFinished( const Process *process )
{
}

void ContextMonitor::collate() const
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
