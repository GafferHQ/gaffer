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

#include "GafferSceneUI/ContextAlgo.h"

#include "Gaffer/Context.h"
#include "Gaffer/ScriptNode.h"

#include "boost/bind/bind.hpp"

#include <unordered_map>

using namespace boost::placeholders;
using namespace Gaffer;
using namespace GafferSceneUI;

namespace
{

struct ChangedSignals
{
	ScriptNodeAlgo::ChangedSignal visibleSetChangedSignal;
	ScriptNodeAlgo::ChangedSignal selectedPathsChangedSignal;
	Gaffer::Signals::ScopedConnection connection;
};

void contextChanged( IECore::InternedString variable, ScriptNode *script, ChangedSignals *signals )
{
	if( ContextAlgo::affectsVisibleSet( variable ) )
	{
		signals->visibleSetChangedSignal( script );
	}

	if( ContextAlgo::affectsSelectedPaths( variable ) || ContextAlgo::affectsLastSelectedPath( variable ) )
	{
		signals->selectedPathsChangedSignal( script );
	}
}

ChangedSignals &changedSignals( ScriptNode *script )
{
	static std::unordered_map<const ScriptNode *, ChangedSignals> g_signals;
	ChangedSignals &result = g_signals[script];
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
	ContextAlgo::setVisibleSet( script->context(), visibleSet );
}

GafferScene::VisibleSet ScriptNodeAlgo::getVisibleSet( const Gaffer::ScriptNode *script )
{
	return ContextAlgo::getVisibleSet( script->context() );
}

ScriptNodeAlgo::ChangedSignal &ScriptNodeAlgo::visibleSetChangedSignal( Gaffer::ScriptNode *script )
{
	return changedSignals( script ).visibleSetChangedSignal;
}

void ScriptNodeAlgo::expandInVisibleSet( Gaffer::ScriptNode *script, const IECore::PathMatcher &paths, bool expandAncestors )
{
	ContextAlgo::expand( script->context(), paths, expandAncestors );
}

IECore::PathMatcher ScriptNodeAlgo::expandDescendantsInVisibleSet( Gaffer::ScriptNode *script, const IECore::PathMatcher &paths, const GafferScene::ScenePlug *scene, int depth )
{
	return ContextAlgo::expandDescendants( script->context(), paths, scene, depth );
}

void ScriptNodeAlgo::setSelectedPaths( Gaffer::ScriptNode *script, const IECore::PathMatcher &paths )
{
	ContextAlgo::setSelectedPaths( script->context(), paths );
}

IECore::PathMatcher ScriptNodeAlgo::getSelectedPaths( const Gaffer::ScriptNode *script )
{
	return ContextAlgo::getSelectedPaths( script->context() );
}

void ScriptNodeAlgo::setLastSelectedPath( Gaffer::ScriptNode *script, const std::vector<IECore::InternedString> &path )
{
	ContextAlgo::setLastSelectedPath( script->context(), path );
}

std::vector<IECore::InternedString> ScriptNodeAlgo::getLastSelectedPath( const Gaffer::ScriptNode *script )
{
	return ContextAlgo::getLastSelectedPath( script->context() );
}

ScriptNodeAlgo::ChangedSignal &ScriptNodeAlgo::selectedPathsChangedSignal( Gaffer::ScriptNode *script )
{
	return changedSignals( script ).selectedPathsChangedSignal;

}
