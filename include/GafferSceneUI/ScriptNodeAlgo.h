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

#pragma once

#include "GafferSceneUI/Export.h"

#include "GafferScene/VisibleSet.h"

#include "Gaffer/Signals.h"

#include "IECore/PathMatcher.h"

namespace Gaffer
{

class ScriptNode;

} // namespace Gaffer

namespace GafferScene
{

class ScenePlug;

} // namespace GafferScene

namespace GafferSceneUI
{

namespace ScriptNodeAlgo
{

using ChangedSignal = Gaffer::Signals::Signal<void ( Gaffer::ScriptNode * ), Gaffer::Signals::CatchingCombiner<void>>;

/// Visible Set
/// ===========

/// The UI components coordinate with each other to perform on-demand scene
/// generation by managing a VisibleSet specifying which scene locations should
/// be shown. For instance, this allows the Viewer to show the objects from
/// locations exposed by expansion performed in the HierarchyView, and vice
/// versa.
GAFFERSCENEUI_API void setVisibleSet( Gaffer::ScriptNode *script, const GafferScene::VisibleSet &visibleSet );
GAFFERSCENEUI_API GafferScene::VisibleSet getVisibleSet( const Gaffer::ScriptNode *script );
/// Returns a signal emitted when the visible set for `script` is changed.
GAFFERSCENEUI_API ChangedSignal &visibleSetChangedSignal( Gaffer::ScriptNode *script );

/// Visible Set Utilities
/// =====================

/// Appends paths to the current expansion, optionally adding all ancestor paths too.
GAFFERSCENEUI_API void expandInVisibleSet( Gaffer::ScriptNode *script, const IECore::PathMatcher &paths, bool expandAncestors = true );
/// Appends descendant paths to the current expansion up to a specified maximum depth.
/// Returns a new PathMatcher containing the new leafs of this expansion.
GAFFERSCENEUI_API IECore::PathMatcher expandDescendantsInVisibleSet( Gaffer::ScriptNode *script, const IECore::PathMatcher &paths, const GafferScene::ScenePlug *scene, int depth = std::numeric_limits<int>::max() );

/// Path Selection
/// ==============

/// Similarly to Path Expansion, the UI components coordinate with each other to
/// perform scene selection, storing the paths to the currently selected
/// locations within the scene.
GAFFERSCENEUI_API void setSelectedPaths( Gaffer::ScriptNode *script, const IECore::PathMatcher &paths );
GAFFERSCENEUI_API IECore::PathMatcher getSelectedPaths( const Gaffer::ScriptNode *script );

/// When multiple paths are selected, it can be useful to know which was the last path to be
/// added. Because `PathMatcher` is unordered, this must be specified separately.
///
/// > Note : The last selected path is synchronised automatically with the list of selected
/// > paths. When `setLastSelectedPath()` is called, it adds the path to the main selection list.
/// > When `setSelectedPaths()` is called, an arbitrary path becomes the last selected path.
/// >
/// > Note : An empty path is considered to mean that there is no last selected path, _not_
/// > that the scene root is selected.
GAFFERSCENEUI_API void setLastSelectedPath( Gaffer::ScriptNode *script, const std::vector<IECore::InternedString> &path );
GAFFERSCENEUI_API std::vector<IECore::InternedString> getLastSelectedPath( const Gaffer::ScriptNode *script );

/// Returns a signal emitted when either the selected paths or last selected path change for `script`.
GAFFERSCENEUI_API ChangedSignal &selectedPathsChangedSignal( Gaffer::ScriptNode *script );

} // namespace ScriptNodeAlgo

} // namespace GafferSceneUI
