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

#include "GafferScene/GlobalsMonitor.h"

#include "GafferScene/ScenePlug.h"

#include "Gaffer/Process.h"

using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

GlobalsMonitor::GlobalsMonitor()
{
}

GlobalsMonitor::~GlobalsMonitor()
{
}

const Gaffer::ValuePlug *GlobalsMonitor::Dependency::globalsPlug() const
{
	return static_cast<const ValuePlug *>( plugs.front().get() ); /// \todo TYPES, RANGE
}

const Gaffer::ValuePlug *GlobalsMonitor::Dependency::dependency() const
{
	return static_cast<const ValuePlug *>( plugs.back().get() );
}

const GlobalsMonitor::DependencySet &GlobalsMonitor::dependencies() const
{
	return m_dependencies;
}

void GlobalsMonitor::processStarted( const Process *process )
{
	auto scenePlug = process->plug()->parent<ScenePlug>();
	if( !scenePlug || process->plug() == scenePlug->globalsPlug() )
	{
		return;
	}

	const Process *parentProcess = process->parent();
	while( parentProcess )
	{
		if( auto parentScenePlug = parentProcess->plug()->parent<const ScenePlug>() )
		{
			if( parentProcess->plug() == parentScenePlug->globalsPlug() )
			{
				//std::cerr << "DODGY " << parentProcess->plug()->fullName() << " -> " << process->plug()->fullName() << std::endl;
				Mutex::scoped_lock lock( m_mutex );
				m_processStartTimes[process] = Clock::now();
			}
			return;
		}
		parentProcess = parentProcess->parent();
	}
}

void GlobalsMonitor::processFinished( const Process *process )
{
	Mutex::scoped_lock lock( m_mutex, /* write = */ false );
	auto processIt = m_processStartTimes.find( process );
	if( processIt == m_processStartTimes.end() )
	{
		return;
	}

	const auto timeCost = Clock::now() - processIt->second;
	Dependency dependency;

	while( process )
	{
		const size_t startSize = dependency.plugs.size();
		for( const Plug *plug = process->destinationPlug(); ; plug = plug->source() )
		{
			dependency.plugs.push_back( plug );
			if( plug == process->plug() )
			{
				break;
			}
		}
		std::reverse( dependency.plugs.begin() + startSize, dependency.plugs.end() );

		if( auto scenePlug = process->plug()->parent<const ScenePlug>() )
		{
			if( process->plug() == scenePlug->globalsPlug() )
			{
				break;
			}
		}
		process = process->parent();
	}

	std::reverse( dependency.plugs.begin(), dependency.plugs.end() );

	lock.upgrade_to_writer();
	m_processStartTimes.erase( processIt );

	auto [dependencyIt, inserted] = m_dependencies.insert( dependency );
	const_cast<Dependency &>( *dependencyIt ).timeCost += timeCost; /// \todo FIX ME
}
