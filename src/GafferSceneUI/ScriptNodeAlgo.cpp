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

#include "GafferSceneUI/ScriptNodeAlgo.h"

#include "GafferScene/ScenePlug.h"
#include "GafferScene/VisibleSetData.h"

#include "Gaffer/Context.h"
#include "Gaffer/Metadata.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/NameValuePlug.h"
#include "Gaffer/CompoundDataPlug.h"
#include "Gaffer/MetadataAlgo.h"

#include "boost/algorithm/string/predicate.hpp"
#include "boost/bind/bind.hpp"

#include <unordered_map>

using namespace boost::placeholders;
using namespace Gaffer;
using namespace GafferScene;
using namespace GafferSceneUI;

namespace
{

const InternedString g_selectedPathsName( "ui:scene:selectedPaths" );
const InternedString g_lastSelectedPathName( "ui:scene:lastSelectedPath" );
const InternedString g_visibleSetName( "ui:scene:visibleSet" );
const std::string g_visibleSetBookmarkPrefix( "visibleSet:bookmark:" );

struct ChangedSignals
{
	ScriptNodeAlgo::ChangedSignal visibleSetChangedSignal;
	ScriptNodeAlgo::ChangedSignal selectedPathsChangedSignal;
	Gaffer::Signals::ScopedConnection connection;
};

void contextChanged( IECore::InternedString variable, ScriptNode *script, ChangedSignals *signals )
{
	if( variable == g_visibleSetName )
	{
		signals->visibleSetChangedSignal( script );
	}
	else if( variable == g_selectedPathsName || variable == g_lastSelectedPathName )
	{
		signals->selectedPathsChangedSignal( script );
	}
}

ChangedSignals &changedSignals( ScriptNode *script )
{
	// Deliberately "leaking" map as it may contain Python slots which can't
	// be destroyed during static destruction (because Python has already
	// shut down at that point).
	static std::unordered_map<const ScriptNode *, ChangedSignals> *g_signals = new std::unordered_map<const ScriptNode *, ChangedSignals>;
	ChangedSignals &result = (*g_signals)[script];
	if( !result.connection.connected() )
	{
		// Either we just made the signals, or an old ScriptNode
		// was destroyed and a new one made in its place.
		result.connection = const_cast<Context *>( script->context() )->changedSignal().connect(
			boost::bind( &contextChanged, ::_2, script, &result )
		);
	}
	return result;
}

bool expandWalk( const ScenePlug::ScenePath &path, const ScenePlug *scene, size_t depth, PathMatcher &expanded, PathMatcher &leafPaths )
{
	bool result = false;

	ConstInternedStringVectorDataPtr childNamesData = scene->childNames( path );
	const std::vector<InternedString> &childNames = childNamesData->readable();

	if( childNames.size() )
	{
		result |= expanded.addPath( path );

		ScenePlug::ScenePath childPath = path;
		childPath.push_back( InternedString() ); // room for the child name
		for( std::vector<InternedString>::const_iterator cIt = childNames.begin(), ceIt = childNames.end(); cIt != ceIt; cIt++ )
		{
			childPath.back() = *cIt;
			if( depth == 1 )
			{
				// at the bottom of the expansion - consider the child a leaf
				result |= leafPaths.addPath( childPath );
			}
			else
			{
				// continue the expansion
				result |= expandWalk( childPath, scene, depth - 1, expanded, leafPaths );
			}
		}
	}
	else
	{
		// we have no children, just mark the leaf of the expansion.
		result |= leafPaths.addPath( path );
	}

	return result;
}

} // namespace

/// Everything here is implemented as a shim on top of ContextAlgo. Our intention is to move everyone
/// over to using ScriptNodeAlgo, then to remove ContextAlgo and reimplement ScriptNodeAlgo using the
/// metadata API to store the state as metadata on the ScriptNode. This will bring several benefits :
///
/// - We can drop all the special cases for ignoring `ui:` metadata in Contexts. Using the context
///   for UI state was a terrible idea in the first place.
/// - Copying contexts during compute will be cheaper, since there will be fewer variables.
/// - We'll be able to serialise the UI state with the script if we want to.

void ScriptNodeAlgo::setVisibleSet( Gaffer::ScriptNode *script, const GafferScene::VisibleSet &visibleSet )
{
	script->context()->set( g_visibleSetName, visibleSet );
}

GafferScene::VisibleSet ScriptNodeAlgo::getVisibleSet( const Gaffer::ScriptNode *script )
{
	return script->context()->get<VisibleSet>( g_visibleSetName, VisibleSet() );
}

ScriptNodeAlgo::ChangedSignal &ScriptNodeAlgo::visibleSetChangedSignal( Gaffer::ScriptNode *script )
{
	return changedSignals( script ).visibleSetChangedSignal;
}

void ScriptNodeAlgo::expandInVisibleSet( Gaffer::ScriptNode *script, const IECore::PathMatcher &paths, bool expandAncestors )
{
	const auto *visibleSet = script->context()->getIfExists<VisibleSet>( g_visibleSetName );
	if( !visibleSet )
	{
		setVisibleSet( script, VisibleSet() );
		visibleSet = script->context()->getIfExists<VisibleSet>( g_visibleSetName );
	}
	VisibleSet &visible = *const_cast<VisibleSet*>(visibleSet);

	bool needUpdate = false;
	if( expandAncestors )
	{
		for( IECore::PathMatcher::RawIterator it = paths.begin(), eIt = paths.end(); it != eIt; ++it )
		{
			needUpdate |= visible.expansions.addPath( *it );
		}
	}
	else
	{
		for( IECore::PathMatcher::Iterator it = paths.begin(), eIt = paths.end(); it != eIt; ++it )
		{
			needUpdate |= visible.expansions.addPath( *it );
		}
	}

	if( needUpdate )
	{
		// We modified the expanded paths in place with const_cast to avoid unecessary copying,
		// so the context doesn't know they've changed. So we must let it know
		// about the change.
		setVisibleSet( script, *visibleSet );
	}
}

IECore::PathMatcher ScriptNodeAlgo::expandDescendantsInVisibleSet( Gaffer::ScriptNode *script, const IECore::PathMatcher &paths, const GafferScene::ScenePlug *scene, int depth )
{
	auto visibleSet = getVisibleSet( script );

	bool needUpdate = false;
	IECore::PathMatcher leafPaths;

	// \todo: parallelize the walk
	for( IECore::PathMatcher::Iterator it = paths.begin(), eIt = paths.end(); it != eIt; ++it )
	{
		needUpdate |= expandWalk( *it, scene, depth + 1, visibleSet.expansions, leafPaths );
	}

	if( needUpdate )
	{
		// If we modified the expanded paths, we need to set the value back on the context
		setVisibleSet( script, visibleSet );
	}

	return leafPaths;
}

void ScriptNodeAlgo::setSelectedPaths( Gaffer::ScriptNode *script, const IECore::PathMatcher &paths )
{
	script->context()->set( g_selectedPathsName, paths );

	if( paths.isEmpty() )
	{
		script->context()->remove( g_lastSelectedPathName );
	}
	else
	{
		std::vector<IECore::InternedString> lastSelectedPath = getLastSelectedPath( script );
		if( !(paths.match( lastSelectedPath ) & PathMatcher::ExactMatch) )
		{
			const PathMatcher::Iterator it = paths.begin();
			script->context()->set( g_lastSelectedPathName, *it );
		}
	}}

IECore::PathMatcher ScriptNodeAlgo::getSelectedPaths( const Gaffer::ScriptNode *script )
{
	return script->context()->get<PathMatcher>( g_selectedPathsName, IECore::PathMatcher() );
}

void ScriptNodeAlgo::setLastSelectedPath( Gaffer::ScriptNode *script, const std::vector<IECore::InternedString> &path )
{
	if( path.empty() )
	{
		script->context()->remove( g_lastSelectedPathName );
	}
	else
	{
		PathMatcher selectedPaths = getSelectedPaths( script );
		if( selectedPaths.addPath( path ) )
		{
			script->context()->set( g_selectedPathsName, selectedPaths );
		}
		script->context()->set( g_lastSelectedPathName, path );
	}
}

std::vector<IECore::InternedString> ScriptNodeAlgo::getLastSelectedPath( const Gaffer::ScriptNode *script )
{
	return script->context()->get<std::vector<IECore::InternedString>>( g_lastSelectedPathName, {} );
}

ScriptNodeAlgo::ChangedSignal &ScriptNodeAlgo::selectedPathsChangedSignal( Gaffer::ScriptNode *script )
{
	return changedSignals( script ).selectedPathsChangedSignal;
}

NameValuePlug *ScriptNodeAlgo::acquireRenderPassPlug( Gaffer::ScriptNode *script, bool createIfMissing )
{
	if( const auto renderPassPlug = script->variablesPlug()->getChild<NameValuePlug>( "renderPass" ) )
	{
		if( renderPassPlug->valuePlug<StringPlug>() )
		{
			return renderPassPlug;
		}
		else
		{
			throw IECore::Exception( fmt::format( "Plug type of {} is {}, but must be StringPlug", renderPassPlug->valuePlug()->fullName(), renderPassPlug->valuePlug()->typeName() ) );
		}
	}

	if( createIfMissing )
	{
		auto renderPassPlug = new NameValuePlug( "renderPass", new StringPlug(), "renderPass", Gaffer::Plug::Flags::Default | Gaffer::Plug::Flags::Dynamic );
		MetadataAlgo::setReadOnly( renderPassPlug->namePlug(), true );
		script->variablesPlug()->addChild( renderPassPlug );

		return renderPassPlug;
	}

	return nullptr;
}

void ScriptNodeAlgo::setCurrentRenderPass( Gaffer::ScriptNode *script, std::string renderPass )
{
	auto renderPassPlug = acquireRenderPassPlug( script );
	renderPassPlug->valuePlug<StringPlug>()->setValue( renderPass );
}

std::string ScriptNodeAlgo::getCurrentRenderPass( const Gaffer::ScriptNode *script )
{
	if( const auto renderPassPlug = acquireRenderPassPlug( const_cast<ScriptNode *>( script ), /* createIfMissing = */ false ) )
	{
		return renderPassPlug->valuePlug<StringPlug>()->getValue();
	}

	return "";
}

// Visible Set Bookmarks
// =====================

void ScriptNodeAlgo::addVisibleSetBookmark( Gaffer::ScriptNode *script, const std::string &name, const GafferScene::VisibleSet &visibleSet, bool persistent )
{
	Metadata::registerValue( script, g_visibleSetBookmarkPrefix + name, new GafferScene::VisibleSetData( visibleSet ), persistent );
}

GafferScene::VisibleSet ScriptNodeAlgo::getVisibleSetBookmark( const Gaffer::ScriptNode *script, const std::string &name )
{
	if( const auto bookmarkData = Metadata::value<VisibleSetData>( script, g_visibleSetBookmarkPrefix + name ) )
	{
		return bookmarkData->readable();
	}

	return GafferScene::VisibleSet();
}

void ScriptNodeAlgo::removeVisibleSetBookmark( Gaffer::ScriptNode *script, const std::string &name )
{
	Metadata::deregisterValue( script, g_visibleSetBookmarkPrefix + name );
}

std::vector<std::string> ScriptNodeAlgo::visibleSetBookmarks( const Gaffer::ScriptNode *script )
{
	std::vector<InternedString> keys;
	Metadata::registeredValues( script, keys );

	std::vector<std::string> result;
	for( const auto &key : keys )
	{
		if( boost::starts_with( key.string(), g_visibleSetBookmarkPrefix ) )
		{
			result.push_back( key.string().substr( g_visibleSetBookmarkPrefix.size(), key.string().size() ) );
		}
	}

	return result;
}
