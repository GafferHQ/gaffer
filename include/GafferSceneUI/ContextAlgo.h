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

#ifndef GAFFERSCENEUI_CONTEXTALGO_H
#define GAFFERSCENEUI_CONTEXTALGO_H

#include "IECore/PathMatcher.h"

#include "GafferSceneUI/Export.h"

namespace Gaffer
{

class Context;

} // namespace Gaffer

namespace GafferSceneUI
{

namespace ContextAlgo
{

/// Path Expansion
/// ==============

/// The UI components coordinate with each other to perform on-demand scene
/// generation by using the Context to store paths to the currently expanded
/// locations within the scene. For instance, this allows the Viewer show the
/// objects from locations exposed by expansion performed in the SceneHierarchy,
/// and vice versa.
///
/// By convention, an expanded location is one whose children are visible,
/// meaning that they are listed below it in the SceneHierarchy and their objects
/// are drawn in the Viewer. Conversely, a collapsed location's children are
/// not listed in the SceneHierarchy and the location itself is drawn as a
/// the bounding box of the children.
///
/// As a consequence of this definition, it is not necessary to expand locations
/// without children. For a simple node such as Sphere, it is only necessary
/// to expand the root location ("/") to view the geometry. For nodes which
/// construct a deeper hierarchy, if the name of a location is visible in
/// the SceneHierarchy, then it's geometry will be displayed in the Viewer.

GAFFERSCENEUI_API void setExpandedPaths( Gaffer::Context *context, const IECore::PathMatcher &paths );
GAFFERSCENEUI_API IECore::PathMatcher getExpandedPaths( const Gaffer::Context *context );

/// Appends paths to the current expansion, optionally adding all ancestor paths too.
GAFFERSCENEUI_API void expand( Gaffer::Context *context, const IECore::PathMatcher &paths, bool expandAncestors = true );

/// Appends descendant paths to the current expansion up to a specified maximum depth.
/// Returns a new PathMatcher containing the new leafs of this expansion.
GAFFERSCENEUI_API IECore::PathMatcher expandDescendants( Gaffer::Context *context, const IECore::PathMatcher &paths, const GafferScene::ScenePlug *scene, int depth = Imath::limits<int>::max() );

/// Clears the currently expanded paths
GAFFERSCENEUI_API void clearExpansion( Gaffer::Context *context );

/// Path Selection
/// ==============

/// Similarly to Path Expansion, the UI components coordinate with each other
/// to perform scene selection, again using the Context to store paths to the
/// currently selected locations within the scene.

GAFFERSCENEUI_API void setSelectedPaths( Gaffer::Context *context, const IECore::PathMatcher &paths );
GAFFERSCENEUI_API IECore::PathMatcher getSelectedPaths( const Gaffer::Context *context );

} // namespace ContextAlgo

} // namespace GafferSceneUI

#endif // GAFFERSCENEUI_CONTEXTALGO_H
