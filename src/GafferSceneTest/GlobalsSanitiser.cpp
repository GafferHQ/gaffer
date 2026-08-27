//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2026, Cinesite VFX Ltd. All rights reserved.
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

#include "GafferSceneTest/GlobalsSanitiser.h"

#include "GafferScene/ScenePlug.h"

#include "Gaffer/Process.h"
#include "Gaffer/ScriptNode.h"

#include "IECore/MessageHandler.h"

#include "fmt/format.h"

using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;
using namespace GafferSceneTest;

GlobalsSanitiser::GlobalsSanitiser()
{
}

void GlobalsSanitiser::processStarted( const Gaffer::Process *process )
{
	const CompoundObjectPlug *dependentGlobals = nullptr;
	auto it = m_dependentGlobalsMap.find( process->parent() );
	if( it != m_dependentGlobalsMap.end() )
	{
		// If some globals were dependent on our parent process, then
		// they are dependent on us too.
		dependentGlobals = it->second;
	}

	if( const ScenePlug *scene = process->plug()->parent<ScenePlug>() )
	{
		if( process->plug() == scene->globalsPlug() )
		{
			dependentGlobals = scene->globalsPlug();
		}
		else if( dependentGlobals )
		{
			warn( *process, dependentGlobals );
			// No point issuing further warnings for upstream processes.
			dependentGlobals = nullptr;
		}
	}

	if( dependentGlobals )
	{
		m_dependentGlobalsMap[process] = dependentGlobals;
	}
}

void GlobalsSanitiser::processFinished( const Gaffer::Process *process )
{
	auto it = m_dependentGlobalsMap.find( process );
	if( it != m_dependentGlobalsMap.end() )
	{
		// We can't erase in a thread-safe manner, so just store null.
		// This does mean we accumulate entries, but we only intend to
		// use the sanitiser for short bursts anyway.
		it->second = nullptr;
	}
}

void GlobalsSanitiser::warn( const Gaffer::Process &process, const Gaffer::CompoundObjectPlug *dependentGlobals )
{
	const Warning warning( process.plug(), dependentGlobals );
	if( !m_warningsEmitted.insert( warning ).second )
	{
		return;
	}

	IECore::msg(
		IECore::Msg::Warning, "GlobalsSanitiser",
		fmt::format(
			"Globals {} depends on {}",
			dependentGlobals->relativeName( dependentGlobals->ancestor<ScriptNode>() ),
			process.plug()->relativeName( process.plug()->ancestor<ScriptNode>() )
		)
	);
}
