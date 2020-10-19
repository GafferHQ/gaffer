//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2019, Image Engine Design Inc. All rights reserved.
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

#include "GafferSceneTest/ContextSanitiser.h"

#include "GafferScene/FilterPlug.h"
#include "GafferScene/FilterResults.h"
#include "GafferScene/ScenePlug.h"

#include "Gaffer/Process.h"
#include "Gaffer/ScriptNode.h"

#include "IECore/MessageHandler.h"

using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;
using namespace GafferSceneTest;

/// \todo Remove
#ifndef IECORE_INTERNEDSTRING_WITH_TBB_HASHER

namespace IECore
{

size_t tbb_hasher( const InternedString &s )
{
	return tbb::tbb_hasher( s.string() );
}

} // namespace IECore

#endif

namespace
{

const InternedString g_internalOut( "__internalOut" );
const InternedString g_exists( "__exists" );
const InternedString g_sortedChildNames( "__sortedChildNames" );

} // namespace

ContextSanitiser::ContextSanitiser()
{
}

void ContextSanitiser::processStarted( const Gaffer::Process *process )
{
	if( const ScenePlug *scene = process->plug()->parent<ScenePlug>() )
	{
		if( process->context()->get<IECore::Data>( FilterPlug::inputSceneContextName, nullptr ) )
		{
			warn( *process, FilterPlug::inputSceneContextName );
		}

		if( process->plug() != scene->setPlug() )
		{
			if( process->context()->get<IECore::Data>( ScenePlug::setNameContextName, nullptr ) )
			{
				warn( *process, ScenePlug::setNameContextName );
			}
		}

		if(
			process->plug() != scene->boundPlug() &&
			process->plug() != scene->transformPlug() &&
			process->plug() != scene->attributesPlug() &&
			process->plug() != scene->objectPlug() &&
			process->plug() != scene->childNamesPlug() &&
			// Private plugs, so we have no choice but to test
			// for them by name.
			process->plug()->getName() != g_exists &&
			process->plug()->getName() != g_sortedChildNames
		)
		{
			if( process->context()->get<IECore::Data>( ScenePlug::scenePathContextName, nullptr ) )
			{
				warn( *process, ScenePlug::scenePathContextName );
			}
		}
	}

	if( process->plug()->parent<const FilterResults>() )
	{
		if( process->plug()->getName() == g_internalOut )
		{
			if( process->context()->get<IECore::Data>( ScenePlug::scenePathContextName, nullptr ) )
			{
				warn( *process, ScenePlug::scenePathContextName );
			}
			if( process->context()->get<IECore::Data>( ScenePlug::setNameContextName, nullptr ) )
			{
				warn( *process, ScenePlug::setNameContextName );
			}
		}
	}
}

void ContextSanitiser::processFinished( const Gaffer::Process *process )
{
}

void ContextSanitiser::warn( const Gaffer::Process &process, const IECore::InternedString &contextVariable )
{
	const Warning warning(
		PlugPair( process.plug(), process.parent() ? process.parent()->plug() : nullptr ),
		contextVariable
	);

	if( m_warningsEmitted.insert( warning ).second )
	{
		std::string message = boost::str(
			boost::format( "%s in context for %s %s" )
				% contextVariable.string()
				% process.plug()->relativeName(
					process.plug()->ancestor<ScriptNode>()
				)
				% process.type()
		);
		if( process.parent() )
		{
			message += boost::str(
				boost::format( " (called from %s %s)" )
					% process.parent()->plug()->relativeName(
						process.parent()->plug()->ancestor<ScriptNode>()
					)
					% process.parent()->type()
			);
		}
		IECore::msg(
			IECore::Msg::Warning, "ContextSanitiser",
			message
		);
	}
}
