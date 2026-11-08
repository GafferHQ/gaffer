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

#include "GafferSceneUI/Private/SetMembershipInspector.h"

#include "GafferScene/EditScopeAlgo.h"
#include "GafferScene/ObjectSource.h"
#include "GafferScene/PathFilter.h"
#include "GafferScene/SceneNode.h"
#include "GafferScene/Set.h"
#include "GafferScene/SetAlgo.h"

#include "Gaffer/Private/IECorePreview/LRUCache.h"
#include "Gaffer/Metadata.h"
#include "Gaffer/MetadataAlgo.h"
#include "Gaffer/ParallelAlgo.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/Spreadsheet.h"
#include "Gaffer/StringPlug.h"

#include "boost/algorithm/string/join.hpp"

#include "fmt/format.h"

using namespace boost::placeholders;
using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;
using namespace GafferSceneUI::Private;

namespace
{

// This uses the same strategy that ValuePlug uses for the hash cache,
// using `plug->dirtyCount()` to invalidate previous cache entries when
// a plug is dirtied.
struct HistoryCacheKey
{
	HistoryCacheKey() {};
	HistoryCacheKey( const ValuePlug *plug )
		:	plug( plug ), contextHash( Context::current()->hash() ), dirtyCount( plug->dirtyCount() )
	{
	}

	bool operator==( const HistoryCacheKey &rhs ) const
	{
		return
			plug == rhs.plug &&
			contextHash == rhs.contextHash &&
			dirtyCount == rhs.dirtyCount
		;
	}

	const ValuePlug *plug;
	IECore::MurmurHash contextHash;
	uint64_t dirtyCount;
};

size_t hash_value( const HistoryCacheKey &key )
{
	size_t result = 0;
	boost::hash_combine( result, key.plug );
	boost::hash_combine( result, key.contextHash );
	boost::hash_combine( result, key.dirtyCount );
	return result;
}

using HistoryCache = IECorePreview::LRUCache<HistoryCacheKey, SceneAlgo::History::ConstPtr>;

HistoryCache g_historyCache(
	// Getter
	[] ( const HistoryCacheKey &key, size_t &cost, const IECore::Canceller *canceller ) {
		assert( canceller == Context::current()->canceller() );
		cost = 1;
		return SceneAlgo::history(
			key.plug, Context::current()->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName )
		);
	},
	// Max cost
	1000,
	// Removal callback
	[] ( const HistoryCacheKey &key, const SceneAlgo::History::ConstPtr &history ) {
		// Histories contain PlugPtrs, which could potentially be the sole
		// owners. Destroying plugs can trigger dirty propagation, so as a
		// precaution we destroy the history on the UI thread, where this would
		// be OK.
		ParallelAlgo::callOnUIThread(
			[history] () {}
		);
	}

);

ConstBoolDataPtr g_true = new BoolData( true );
ConstBoolDataPtr g_false = new BoolData( false );

EditScope *editScopeWithContainingProcessor( ScenePlug *scene )
{
	auto editScope = scene->ancestor<EditScope>();
	if( !editScope )
	{
		return nullptr;
	}

	auto setMemberShipProcessor = editScope->acquireProcessor( "SetMembershipEdits", /* createIfNecessary = */ false );
	if( setMemberShipProcessor && setMemberShipProcessor->isAncestorOf( scene ) )
	{
		return editScope;
	}

	return nullptr;
}

}  // namespace

SetMembershipInspector::SetMembershipInspector(
	const GafferScene::ScenePlugPtr &scene,
	const Gaffer::PlugPtr &editScope,
	IECore::InternedString setName
)
	:	Inspector( { scene->setPlug() }, "setMembership", setName.string(), editScope ),
		m_scene( scene ), m_setName( setName )
{
}

GafferScene::SceneAlgo::History::ConstPtr SetMembershipInspector::history() const
{
	if( !m_scene->existsPlug()->getValue() )
	{
		return nullptr;
	}

	return g_historyCache.get( HistoryCacheKey( m_scene->objectPlug() ), Context::current()->canceller() );
}

IECore::ConstObjectPtr SetMembershipInspector::value( const GafferScene::SceneAlgo::History *history ) const
{
	const auto &path = history->context->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName );
	ConstPathMatcherDataPtr setMembers = history->scene->set( m_setName );

	auto matchResult = (PathMatcher::Result)setMembers->readable().match( path );

	// Return nullptr for non-exact match so `fallbackValue()` has the opportunity to provide
	// an AncestorMatch.
	return matchResult & IECore::PathMatcher::Result::ExactMatch ? g_true : nullptr;
}

IECore::ConstObjectPtr SetMembershipInspector::fallbackValue( const GafferScene::SceneAlgo::History *history, std::string &description ) const
{
	const auto &path = history->context->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName );
	ConstPathMatcherDataPtr setMembers = history->scene->set( m_setName );

	auto matchResult = (PathMatcher::Result)setMembers->readable().match( path );

	const bool ancestorMatch = matchResult & IECore::PathMatcher::Result::AncestorMatch;
	if( ancestorMatch && path.size() )
	{
		ScenePlug::ScenePath currentPath = path;
		do
		{
			// We start the inheritance search from the parent in order to return the value that
			// would be inherited if the original location wasn't a member of the inspected set.
			currentPath.pop_back();
			if( setMembers->readable().match( currentPath ) & PathMatcher::Result::ExactMatch )
			{
				description = "Inherited from " + ScenePlug::pathToString( currentPath );
				break;
			}
		} while( !currentPath.empty() );
	}
	else
	{
		description = "Default value";
	}

	return ancestorMatch ? g_true : g_false;
}

bool SetMembershipInspector::hasEdit( const GafferScene::SceneAlgo::History *history ) const
{
	auto sceneNode = runTimeCast<SceneNode>( history->scene->node() );
	if( !sceneNode || history->scene != sceneNode->outPlug() || !sceneNode->enabledPlug()->getValue() )
	{
		return false;
	}

	if( runTimeCast<ObjectSource>( sceneNode ) )
	{
		return true;
	}
	if( const auto setSource = runTimeCast<GafferScene::Set>( sceneNode ) )
	{
		const std::string setNamePattern = setSource->namePlug()->getValue();
		if( !StringAlgo::matchMultiple( m_setName, setNamePattern ) )
		{
			return false;
		}

		unsigned filterResult;
		{
			Context::EditableScope filterScope( history->context.get() );
			const std::string setVariable = setSource->setVariablePlug()->getValue();
			if( !setVariable.empty() )
			{
				filterScope.set( setVariable, &m_setName );
			}
			filterResult = setSource->filterPlug()->match( setSource->inPlug() );
		}

		if( filterResult & PathMatcher::Result::ExactMatch )
		{
			return true;
		}
	}

	return false;
}

void SetMembershipInspector::edit( const IECore::Object *value, const GafferScene::SceneAlgo::History *history, bool dryRun ) const
{
	auto boolValue = runTimeCast<const IECore::BoolData>( value );
	if( !boolValue)
	{
		throw EditDisallowed( fmt::format( "Data of type \"{}\" is not compatible.", value->typeName() ) );
	}

	setSetMembership(
		boolValue->readable() ? EditScopeAlgo::SetMembership::Added : EditScopeAlgo::SetMembership::Removed,
		history, dryRun
	);
}

void SetMembershipInspector::edit( const IECore::Object *value, Gaffer::EditScope *editScope, const GafferScene::SceneAlgo::History *history, bool dryRun ) const
{
	auto boolValue = runTimeCast<const IECore::BoolData>( value );
	if( !boolValue )
	{
		throw EditDisallowed( fmt::format( "Data of type \"{}\" is not compatible.", value->typeName() ) );
	}

	setSetMembership(
		boolValue->readable() ? EditScopeAlgo::SetMembership::Added : EditScopeAlgo::SetMembership::Removed,
		editScope, history, dryRun
	);
}

void SetMembershipInspector::disableEdit( const GafferScene::SceneAlgo::History *history, bool dryRun ) const
{
	return setSetMembership( EditScopeAlgo::SetMembership::Unchanged, history, dryRun );
}

void SetMembershipInspector::disableEdit( Gaffer::EditScope *editScope, const GafferScene::SceneAlgo::History *history, bool dryRun ) const
{
	return setSetMembership( EditScopeAlgo::SetMembership::Unchanged, editScope, history, dryRun );
}

void SetMembershipInspector::setSetMembership( GafferScene::EditScopeAlgo::SetMembership membership, const GafferScene::SceneAlgo::History *history, bool dryRun ) const
{
	if( auto objectNode = runTimeCast<ObjectSource>( history->scene->node() ) )
	{
		auto setsPlug = objectNode->setsPlug();
		if( !setsPlug->settable() || Gaffer::MetadataAlgo::readOnly( objectNode->setsPlug() ) )
		{
			throw EditDisallowed( fmt::format( "{} is locked.", setsPlug->relativeName( setsPlug->ancestor<ScriptNode>() ) ) );
		}

		std::vector<std::string> sets;
		IECore::StringAlgo::tokenize( objectNode->setsPlug()->getValue(), ' ', sets );

		if( membership == EditScopeAlgo::SetMembership::Unchanged )
		{
			if( std::find( sets.begin(), sets.end(), m_setName.string() ) == sets.end() )
			{
				throw EditDisallowed( fmt::format( "{} has no edit to disable.", setsPlug->relativeName( setsPlug->ancestor<ScriptNode>() ) ) );
			}
		}

		if( dryRun )
		{
			return;
		}

		if( membership == EditScopeAlgo::SetMembership::Added )
		{
			if( std::find( sets.begin(), sets.end(), m_setName.string() ) == sets.end() )
			{
				sets.push_back( m_setName );
			}
		}
		else
		{
			sets.erase( std::remove( sets.begin(), sets.end(), m_setName.string() ), sets.end() );
		}

		objectNode->setsPlug()->setValue( boost::algorithm::join( sets, " " ) );
	}
	else if( auto editScope = editScopeWithContainingProcessor( history->scene.get() ) )
	{
		setSetMembership( membership, editScope, history, dryRun );
	}
	else
	{
		throw EditDisallowed( fmt::format( "Cannot edit nodes of type \"{}\".", history->scene->node()->typeName() ) );
	}
}

void SetMembershipInspector::setSetMembership( GafferScene::EditScopeAlgo::SetMembership membership, Gaffer::EditScope *editScope, const GafferScene::SceneAlgo::History *history, bool dryRun ) const
{
	if( auto reason = EditScopeAlgo::setMembershipReadOnlyReason( editScope, m_setName, membership ) )
	{
		throw EditDisallowed( fmt::format( "{} is locked.", reason->relativeName( reason->ancestor<ScriptNode>() ) ) );
	}

	if( dryRun )
	{
		return;
	}

	PathMatcher m;
	m.addPath( history->context->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName ) );

	EditScopeAlgo::setSetMembership( editScope, m, m_setName, membership );
}
