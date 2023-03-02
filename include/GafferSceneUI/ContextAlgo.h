//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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

#pragma once

#include "GafferSceneUI/Export.h"

#include "GafferScene/VisibleSet.h"

#include "IECore/PathMatcher.h"

namespace Gaffer
{

class Context;

} // namespace Gaffer

namespace GafferScene
{

class ScenePlug;

} // namespace GafferScene

namespace GafferSceneUI
{

namespace ContextAlgo
{

/// VisibleSet
/// ==========

/// The UI components coordinate with each other to perform on-demand scene
/// generation by using the Context to store a VisibleSet specifying which
/// scene locations should be shown.
/// For instance, this allows the Viewer to show the objects from locations
/// exposed by expansion performed in the HierarchyView, and vice versa.
GAFFERSCENEUI_API void setVisibleSet( Gaffer::Context *context, const GafferScene::VisibleSet &visibleSet );
GAFFERSCENEUI_API GafferScene::VisibleSet getVisibleSet( const Gaffer::Context *context );

/// Returns true if the named context variable affects the result of `getVisibleSet()`.
/// This can be used from `Context::changedSignal()` to determine if the VisibleSet has been
/// changed.
GAFFERSCENEUI_API bool affectsVisibleSet( const IECore::InternedString &name );

/// Path Expansion
/// ==============

/// These are temporary legacy methods allowing access to `VisibleSet::expansions`
/// for the purposes of providing backwards compatibility.
GAFFERSCENEUI_API void setExpandedPaths( Gaffer::Context *context, const IECore::PathMatcher &paths );
GAFFERSCENEUI_API IECore::PathMatcher getExpandedPaths( const Gaffer::Context *context );

/// Returns true if the named context variable affects the result of `getExpandedPaths()`.
/// This can be used from `Context::changedSignal()` to determine if the expansion has been
/// changed.
GAFFERSCENEUI_API bool affectsExpandedPaths( const IECore::InternedString &name );

/// Appends paths to the current expansion, optionally adding all ancestor paths too.
GAFFERSCENEUI_API void expand( Gaffer::Context *context, const IECore::PathMatcher &paths, bool expandAncestors = true );

/// Appends descendant paths to the current expansion up to a specified maximum depth.
/// Returns a new PathMatcher containing the new leafs of this expansion.
GAFFERSCENEUI_API IECore::PathMatcher expandDescendants( Gaffer::Context *context, const IECore::PathMatcher &paths, const GafferScene::ScenePlug *scene, int depth = std::numeric_limits<int>::max() );

/// Clears the currently expanded paths
GAFFERSCENEUI_API void clearExpansion( Gaffer::Context *context );

/// Path Selection
/// ==============

/// Similarly to Path Expansion, the UI components coordinate with each other
/// to perform scene selection, again using the Context to store paths to the
/// currently selected locations within the scene.
GAFFERSCENEUI_API void setSelectedPaths( Gaffer::Context *context, const IECore::PathMatcher &paths );
GAFFERSCENEUI_API IECore::PathMatcher getSelectedPaths( const Gaffer::Context *context );

/// Returns true if the named context variable affects the result of `getSelectedPaths()`.
/// This can be used from `Context::changedSignal()` to determine if the selection has been
/// changed.
GAFFERSCENEUI_API bool affectsSelectedPaths( const IECore::InternedString &name );

/// When multiple paths are selected, it can be useful to know which was the last path to be
/// added. Because `PathMatcher` is unordered, this must be specified separately.
///
/// > Note : The last selected path is synchronised automatically with the list of selected
/// > paths. When `setLastSelectedPath()` is called, it adds the path to the main selection list.
/// > When `setSelectedPaths()` is called, an arbitrary path becomes the last selected path.
/// >
/// > Note : An empty path is considered to mean that there is no last selected path, _not_
/// > that the scene root is selected.
GAFFERSCENEUI_API void setLastSelectedPath( Gaffer::Context *context, const std::vector<IECore::InternedString> &path );
GAFFERSCENEUI_API std::vector<IECore::InternedString> getLastSelectedPath( const Gaffer::Context *context );
GAFFERSCENEUI_API bool affectsLastSelectedPath( const IECore::InternedString &name );

} // namespace ContextAlgo

} // namespace GafferSceneUI
