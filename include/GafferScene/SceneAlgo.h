//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFERSCENE_SCENEALGO_H
#define GAFFERSCENE_SCENEALGO_H

#include "OpenEXR/ImathVec.h"

#include "Gaffer/NumericPlug.h"
#include "GafferScene/ScenePlug.h"

namespace IECore
{

IE_CORE_FORWARDDECLARE( Transform )
IE_CORE_FORWARDDECLARE( Camera )
IE_CORE_FORWARDDECLARE( CompoundData )

} // namespace IECore

namespace GafferScene
{

class Filter;
class PathMatcher;

namespace SceneAlgo
{

/// Returns true if the specified location exists within the scene, and false otherwise.
/// This operates by traversing the path from the root, ensuring that each location includes
/// the next path element within its child names.
bool exists( const ScenePlug *scene, const ScenePlug::ScenePath &path );

/// Returns true if the specified location is visible, and false otherwise.
/// This operates by traversing the path from the root, terminating if
/// the "scene:visible" attribute is false.
bool visible( const ScenePlug *scene, const ScenePlug::ScenePath &path );

/// Finds all the paths in the scene that are matched by the filter, and adds them into the PathMatcher.
void matchingPaths( const Filter *filter, const ScenePlug *scene, PathMatcher &paths );
/// As above, but specifying the filter as a plug - typically Filter::outPlug() or
/// FilteredSceneProcessor::filterPlug() would be passed.
void matchingPaths( const Gaffer::IntPlug *filterPlug, const ScenePlug *scene, PathMatcher &paths );
/// As above, but specifying the filter as a PathMatcher.
void matchingPaths( const PathMatcher &filter, const ScenePlug *scene, PathMatcher &paths );

/// Calls a functor on all paths in the scene
/// The functor must take ( const ScenePlug*, const ScenePlug::ScenePath& ), and can return false to prune traversal
template <class ThreadableFunctor>
void parallelTraverse( const ScenePlug *scene, ThreadableFunctor &f );

/// Calls a functor on all paths in the scene that are matched by the filter.
/// The functor must take ( const ScenePlug*, const ScenePlug::ScenePath& ), and can return false to prune traversal
template <class ThreadableFunctor>
void filteredParallelTraverse( const ScenePlug *scene, const GafferScene::Filter *filter, ThreadableFunctor &f );
/// As above, but specifying the filter as a plug - typically Filter::outPlug() or
/// FilteredSceneProcessor::filterPlug() would be passed.
template <class ThreadableFunctor>
void filteredParallelTraverse( const ScenePlug *scene, const Gaffer::IntPlug *filterPlug, ThreadableFunctor &f );
/// As above, but using a PathMatcher as a filter.
template <class ThreadableFunctor>
void filteredParallelTraverse( const ScenePlug *scene, const PathMatcher &filter, ThreadableFunctor &f );

/// Returns just the global attributes from the globals (everything prefixed with "attribute:").
IECore::ConstCompoundObjectPtr globalAttributes( const IECore::CompoundObject *globals );

/// Calculates the shutter specified by the globals.
Imath::V2f shutter( const IECore::CompoundObject *globals );

/// Calculates the full transform for the specified location in the scene, sampling motion according to the attributes at that
/// location if motionBlur is true.
IECore::TransformPtr transform( const ScenePlug *scene, const ScenePlug::ScenePath &path, const Imath::V2f &shutter, bool motionBlur );

/// Returns the primary render camera, with all globals settings such as
/// crop, resolution, overscan etc applied as they would be for rendering.
/// The globals may be passed if they are available, if not they will be computed.
IECore::CameraPtr camera( const ScenePlug *scene, const IECore::CompoundObject *globals = NULL );
/// As above, but choosing a specific camera rather than the primary one.
IECore::CameraPtr camera( const ScenePlug *scene, const ScenePlug::ScenePath &cameraPath, const IECore::CompoundObject *globals = NULL );
/// Applies the resolution, aspect ratio etc from the globals to the camera.
void applyCameraGlobals( IECore::Camera *camera, const IECore::CompoundObject *globals );

/// Returns true if the specified set exists within the scene, and false otherwise.
/// This simply searches for the set name in the result of scene->setNamesPlug()->getValue().
bool setExists( const ScenePlug *scene, const IECore::InternedString &setName );

/// Returns all the sets in the scene, indexed by name. Performs individual set
/// computations in parallel for improved performance.
IECore::ConstCompoundDataPtr sets( const ScenePlug *scene );
/// As above, but returning only the requested sets.
IECore::ConstCompoundDataPtr sets( const ScenePlug *scene, const std::vector<IECore::InternedString> &setNames );

/// Returns a bounding box for the specified object. Typically
/// this is provided by the VisibleRenderable::bound() method, but
/// for other object types we must return a synthetic bound.
Imath::Box3f bound( const IECore::Object *object );

} // namespace SceneAlgo

/// \todo Remove this temporary backwards compatibility.
using namespace SceneAlgo;

} // namespace GafferScene

#include "GafferScene/SceneAlgo.inl"

#endif // GAFFERSCENE_SCENEALGO_H
