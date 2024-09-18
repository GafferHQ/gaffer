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

const InternedString g_setMembershipContextVariableName( "setMembership:set" );

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

bool editSetMembership( Gaffer::Plug *plug, const std::string &setName, const ScenePlug::ScenePath &path, EditScopeAlgo::SetMembership setMembership )
{
	if( auto objectNode = runTimeCast<ObjectSource>( plug->node() ) )
	{
		std::vector<std::string> sets;
		IECore::StringAlgo::tokenize( objectNode->setsPlug()->getValue(), ' ', sets );

		if( setMembership == EditScopeAlgo::SetMembership::Added )
		{
			if( std::find( sets.begin(), sets.end(), setName ) == sets.end() )
			{
				sets.push_back( setName );
			}
		}
		else
		{
			sets.erase( std::remove( sets.begin(), sets.end(), setName ), sets.end() );
		}

		objectNode->setsPlug()->setValue( boost::algorithm::join( sets, " " ) );

		return true;
	}

	if( auto cells = runTimeCast<Gaffer::ValuePlug>( plug ) )
	{
		auto row = cells->parent<Spreadsheet::RowPlug>();
		auto editScope = cells->ancestor<EditScope>();
		if( row && editScope )
		{
			PathMatcher m;
			m.addPath( path );
			EditScopeAlgo::setSetMembership(
				editScope,
				m,
				setName,
				setMembership
			);

			return true;
		}
	}

	return false;
}

std::string nonDisableableReason( const Gaffer::Plug *plug, const std::string &setName )
{
	if( const GraphComponent *readOnlyReason = MetadataAlgo::readOnlyReason( plug ) )
	{
		return fmt::format( "{} is locked.", readOnlyReason->relativeName( readOnlyReason->ancestor<ScriptNode>() ) );
	}
	else if( auto objectNode = runTimeCast<const ObjectSource>( plug->node() ) )
	{
		std::vector<std::string> sets;
		IECore::StringAlgo::tokenize( objectNode->setsPlug()->getValue(), ' ', sets );
		if( std::find( sets.begin(), sets.end(), setName ) == sets.end() )
		{
			return fmt::format( "{} has no edit to disable.", plug->relativeName( plug->ancestor<ScriptNode>() ) );
		}
	}

	return "";
}

}  // namespace

SetMembershipInspector::SetMembershipInspector(
	const GafferScene::ScenePlugPtr &scene,
	const Gaffer::PlugPtr &editScope,
	IECore::InternedString setName
) :
Inspector( "setMembership", setName.string(), editScope ),
m_scene( scene ),
m_setName( setName )
{
	m_scene->node()->plugDirtiedSignal().connect(
		boost::bind( &SetMembershipInspector::plugDirtied, this, ::_1 )
	);

	Metadata::plugValueChangedSignal().connect( boost::bind( &SetMembershipInspector::plugMetadataChanged, this, ::_3, ::_4 ) );
	Metadata::nodeValueChangedSignal().connect( boost::bind( &SetMembershipInspector::nodeMetadataChanged, this, ::_2, ::_3 ) );
}

bool SetMembershipInspector::editSetMembership( const Result *inspection, const ScenePlug::ScenePath &path, EditScopeAlgo::SetMembership setMembership ) const
{
	return ::editSetMembership( inspection->acquireEdit().get(), m_setName.string(), path, setMembership );
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
	return matchResult & IECore::PathMatcher::Result::ExactMatch ? new BoolData( true ) : nullptr;
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

	return new BoolData( ancestorMatch );
}

Gaffer::ValuePlugPtr SetMembershipInspector::source( const GafferScene::SceneAlgo::History *history, std::string &editWarning ) const
{
	auto sceneNode = runTimeCast<SceneNode>( history->scene->node() );
	if( !sceneNode || history->scene != sceneNode->outPlug() || !sceneNode->enabledPlug()->getValue() )
	{
		return nullptr;
	}

	if( const auto objectSource = runTimeCast<ObjectSource>( sceneNode ) )
	{
		return objectSource->setsPlug();
	}
	if( const auto setSource = runTimeCast<GafferScene::Set>( sceneNode ) )
	{
		const std::string setNamePattern = setSource->namePlug()->getValue();
		if( !StringAlgo::matchMultiple( m_setName, setNamePattern ) )
		{
			return nullptr;
		}

		const FilterPlug *filterPlug = setSource->filterPlug();

		Context::EditableScope setNameScope( history->context.get() );
		setNameScope.set( g_setMembershipContextVariableName, &m_setName );

		PathMatcher::Result filterResult = (PathMatcher::Result)filterPlug->match( history->scene.get() );

		if( !( filterResult & ( PathMatcher::Result::ExactMatch | PathMatcher::Result::AncestorMatch ) ) )
		{
			return nullptr;
		}

		if( const auto spreadsheetSource = runTimeCast<Spreadsheet>( setSource->namePlug()->source<Plug>()->parent() ) )
		{
			if( const auto row = spreadsheetSource->rowsPlug()->row( m_setName ) )
			{
				return row->cellsPlug();
			}
		}

		return setSource->namePlug();
	}

	return nullptr;
}

Inspector::EditFunctionOrFailure SetMembershipInspector::editFunction( Gaffer::EditScope *editScope, const GafferScene::SceneAlgo::History *history ) const
{
	const GraphComponent *readOnlyReason = EditScopeAlgo::setMembershipReadOnlyReason(
		editScope,
		m_setName.string(),
		EditScopeAlgo::SetMembership::Added
	);

	if( readOnlyReason )
	{
		return fmt::format( "{} is locked.", readOnlyReason->relativeName( readOnlyReason->ancestor<ScriptNode>() ) );
	}
	else
	{
		InternedString setName = m_setName;
		return [
			editScope = editScope,
			setName,
			context = history->context
		] ( bool createIfNecessary ) {
			Context::Scope scope( context.get() );
			return EditScopeAlgo::acquireSetEdits( editScope, setName, createIfNecessary );
		};
	}
}

Inspector::DisableEditFunctionOrFailure SetMembershipInspector::disableEditFunction( Gaffer::ValuePlug *plug, const GafferScene::SceneAlgo::History *history ) const
{
	const std::string nonDisableableReason = ::nonDisableableReason( plug, m_setName );

	if( !nonDisableableReason.empty() )
	{
		return nonDisableableReason;
	}
	else
	{
		return [
			plug = PlugPtr( plug ),
			setName = m_setName,
			path = history->context->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName )
		] () {
			return ::editSetMembership( plug.get(), setName.string(), path, EditScopeAlgo::SetMembership::Unchanged );
		};
	}
}

void SetMembershipInspector::plugDirtied( Gaffer::Plug *plug )
{
	if( plug == m_scene->setPlug() )
	{
		dirtiedSignal()( this );
	}
}

void SetMembershipInspector::plugMetadataChanged( IECore::InternedString key, const Gaffer::Plug *plug )
{
	if( !plug )
	{
		// Assume readOnly metadata is only registered on instances.
		return;
	}
	nodeMetadataChanged( key, plug->node() );
}

void SetMembershipInspector::nodeMetadataChanged( IECore::InternedString key, const Gaffer::Node *node )
{
	if( !node )
	{
		// Assume readOnly metadata is only registered on instances.
		return;
	}

	EditScope *scope = targetEditScope();
	if( !scope )
	{
		return;
	}

	if(
		MetadataAlgo::readOnlyAffectedByChange( scope, node, key ) ||
		( MetadataAlgo::readOnlyAffectedByChange( key ) && scope->isAncestorOf( node ) )
	)
	{
		// Might affect `EditScopeAlgo::setMembershipEditReadOnlyReason()`
		// which we call in `editFunction()`.
		/// \todo Can we ditch the signal processing and call `setMembershipEditReadOnlyReason()`
		/// just-in-time from `editable()`? In the past that wasn't possible
		/// because editability changed the appearance of the UI, but it isn't
		/// doing that currently.
		dirtiedSignal()( this );
	}
}
