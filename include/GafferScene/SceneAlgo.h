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

#include "GafferScene/Filter.h"
#include "GafferScene/ScenePlug.h"

#include "GafferImage/ImagePlug.h"

#include "Gaffer/NumericPlug.h"

#include "IECore/Export.h"

IECORE_PUSH_DEFAULT_VISIBILITY
#include "OpenEXR/ImathVec.h"
IECORE_POP_DEFAULT_VISIBILITY

#include <unordered_set>

namespace IECore
{

IE_CORE_FORWARDDECLARE( CompoundData )

} // namespace IECore

namespace GafferScene
{

class SceneProcessor;
class FilteredSceneProcessor;
class ShaderTweaks;

namespace SceneAlgo
{

/// Filter queries
/// ==============

/// Returns all the nodes which are filtered by the specified filter,
/// whether directly or indirectly via an intermediate filter.
GAFFERSCENE_API std::unordered_set<FilteredSceneProcessor *> filteredNodes( Filter *filter );

/// Finds all the paths in the scene that are matched by the filter, and adds them into the PathMatcher.
GAFFERSCENE_API void matchingPaths( const Filter *filter, const ScenePlug *scene, IECore::PathMatcher &paths );
/// As above, but specifying the filter as a plug - typically Filter::outPlug() or
/// FilteredSceneProcessor::filterPlug() would be passed.
GAFFERSCENE_API void matchingPaths( const FilterPlug *filterPlug, const ScenePlug *scene, IECore::PathMatcher &paths );
/// As above, but specifying the filter as a PathMatcher.
GAFFERSCENE_API void matchingPaths( const IECore::PathMatcher &filter, const ScenePlug *scene, IECore::PathMatcher &paths );

/// Matching above, but doing a fast hash of the matching paths instead of storing all paths
GAFFERSCENE_API IECore::MurmurHash matchingPathsHash( const Filter *filter, const ScenePlug *scene );
GAFFERSCENE_API IECore::MurmurHash matchingPathsHash( const GafferScene::FilterPlug *filterPlug, const ScenePlug *scene );
GAFFERSCENE_API IECore::MurmurHash matchingPathsHash( const IECore::PathMatcher &filter, const ScenePlug *scene );

/// Parallel scene traversal
/// ========================

/// Invokes the ThreadableFunctor at every location in the scene,
/// visiting parent locations before their children, but
/// otherwise processing locations in parallel as much
/// as possible.
///
/// Functor should be of the following form.
///
/// ```
/// struct ThreadableFunctor
/// {
///
///	    /// Called to construct a new functor to be used at
///     /// each child location. This allows state to be
///     /// accumulated as the scene is traversed, with each
///     /// parent passing its state to its children.
///     ThreadableFunctor( const ThreadableFunctor &parent );
///
///     /// Called to process a specific location. May return
///     /// false to prune the traversal, or true to continue
///     /// to the children.
///     bool operator()( const ScenePlug *scene, const ScenePlug::ScenePath &path );
///
/// };
/// ```
template <class ThreadableFunctor>
void parallelProcessLocations( const GafferScene::ScenePlug *scene, ThreadableFunctor &f );
/// As above, but starting the traversal at the specified root.
template <class ThreadableFunctor>
void parallelProcessLocations( const GafferScene::ScenePlug *scene, ThreadableFunctor &f, const ScenePlug::ScenePath &root );

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
void filteredParallelTraverse( const ScenePlug *scene, const FilterPlug *filterPlug, ThreadableFunctor &f );
/// As above, but using a PathMatcher as a filter.
template <class ThreadableFunctor>
void filteredParallelTraverse( const ScenePlug *scene, const IECore::PathMatcher &filter, ThreadableFunctor &f );

/// Globals
/// =======

/// Returns just the global attributes from the globals (everything prefixed with "attribute:").
GAFFERSCENE_API IECore::ConstCompoundObjectPtr globalAttributes( const IECore::CompoundObject *globals );

/// Calculates the shutter specified by the globals ( potentially overridden by a camera )
GAFFERSCENE_API Imath::V2f shutter( const IECore::CompoundObject *globals, const ScenePlug *scene );

/// Sets
/// ====

/// Returns true if the specified set exists within the scene, and false otherwise.
/// This simply searches for the set name in the result of scene->setNamesPlug()->getValue().
GAFFERSCENE_API bool setExists( const ScenePlug *scene, const IECore::InternedString &setName );

/// Returns all the sets in the scene, indexed by name. Performs individual set
/// computations in parallel for improved performance.
GAFFERSCENE_API IECore::ConstCompoundDataPtr sets( const ScenePlug *scene );
/// As above, but returning only the requested sets.
GAFFERSCENE_API IECore::ConstCompoundDataPtr sets( const ScenePlug *scene, const std::vector<IECore::InternedString> &setNames );

/// History
/// =======
///
/// Methods to query the tree of upstream computations involved in computing
/// a property of the scene.

struct History : public IECore::RefCounted
{
	IE_CORE_DECLAREMEMBERPTR( History )
	typedef std::vector<Ptr> Predecessors;

	History() = default;
	History( const ScenePlugPtr &scene, const Gaffer::ContextPtr &context ) : scene( scene ), context( context ) {}

	ScenePlugPtr scene;
	Gaffer::ContextPtr context;
	Predecessors predecessors;
};

GAFFERSCENE_API History::Ptr history( const Gaffer::ValuePlug *scenePlugChild, const ScenePlug::ScenePath &path );

/// Extends History to provide information on the history of a specific attribute.
/// Attributes may be renamed by ShuffleAttributes nodes and this is reflected
/// in the `attributeName` field.
struct AttributeHistory : public History
{
	IE_CORE_DECLAREMEMBERPTR( AttributeHistory )
	AttributeHistory(
		const ScenePlugPtr &scene, const Gaffer::ContextPtr &context,
		const IECore::InternedString &attributeName, const IECore::ConstObjectPtr &attributeValue
	) :	History( scene, context ), attributeName( attributeName ), attributeValue( attributeValue ) {}
	IECore::InternedString attributeName;
	IECore::ConstObjectPtr attributeValue;
};

/// Filters `attributesHistory` and returns a history for the specific `attribute`.
/// `attributesHistory` should have been obtained from a previous call to
/// `history( scene->attributesPlug(), path )`. If the attribute doesn't exist then
/// null is returned.
GAFFERSCENE_API AttributeHistory::Ptr attributeHistory( const History *attributesHistory, const IECore::InternedString &attribute );

/// Returns the upstream scene originally responsible for generating the specified location.
GAFFERSCENE_API ScenePlug *source( const ScenePlug *scene, const ScenePlug::ScenePath &path );

/// Returns the last tweaks node to edit the specified object.
/// > Note : Currently only CameraTweaks are recognised, but as other tweaks nodes are added
/// > we should support them here (for instance, we might introduce an ExternalProceduralTweaks
/// > node to replace the old Parameters node).
GAFFERSCENE_API SceneProcessor *objectTweaks( const ScenePlug *scene, const ScenePlug::ScenePath &path );

/// Returns the last ShaderTweaks node to edit the specified attribute.
GAFFERSCENE_API ShaderTweaks *shaderTweaks( const ScenePlug *scene, const ScenePlug::ScenePath &path, const IECore::InternedString &attributeName );

/// Returns the name of a context variable in which the history methods store a unique value
/// to disable the effects of the hash cache, so that the full upstream process can be examined.
/// May be removed from a context to reenable the cache for expensive hash operations that are
/// known to be irrelevant to the history.
GAFFERSCENE_API IECore::InternedString historyIDContextName();

/// Render Metadata
/// ===============
///
/// Methods to determine information about the scene that produced an image.
/// Gaffer's output code adds the name of the source ScenePlug into the image
/// headers for renders, this metadata (or equivalent) must be present for
/// these methods to function.
/// NOTE: No attempts are made to track renaming or re-connections, so if the
/// graph topology has changed since the image was rendered, results may vary.

/// Returns the script-relative name of the source ScenePlug referenced by the
/// supplied image. Note: this is the exact plug that was rendered so may
/// include internal processing nodes not visible in the user-land node graph.
/// If no metadata is present, and empty string is returned.
GAFFERSCENE_API std::string sourceSceneName( const GafferImage::ImagePlug *image );

/// Returns the source ScenePlug for the supplied image as per
/// SceneAlgo::sourceSceneName or a nullptr if no metadata exists or the plug
/// can't be found.
GAFFERSCENE_API ScenePlug *sourceScene( GafferImage::ImagePlug *image );

/// Light linking queries
/// =====================

/// Returns the paths to locations which are linked to the specified light.
GAFFERSCENE_API IECore::PathMatcher linkedObjects( const ScenePlug *scene, const ScenePlug::ScenePath &light );
/// Returns the paths to locations which are linked to at least one of the specified lights.
GAFFERSCENE_API IECore::PathMatcher linkedObjects( const ScenePlug *scene, const IECore::PathMatcher &lights );

/// Returns the paths to all lights which are linked to the specified object.
GAFFERSCENE_API IECore::PathMatcher linkedLights( const ScenePlug *scene, const ScenePlug::ScenePath &object );
/// Returns the paths to all lights which are linked to at least one of the specified objects.
GAFFERSCENE_API IECore::PathMatcher linkedLights( const ScenePlug *scene, const IECore::PathMatcher &objects );

/// Miscellaneous
/// =============

/// \deprecated Use `ScenePlug::exists()` instead.
GAFFERSCENE_API bool exists( const ScenePlug *scene, const ScenePlug::ScenePath &path );

/// Returns true if the specified location is visible, and false otherwise.
/// This operates by traversing the path from the root, terminating if
/// the "scene:visible" attribute is false.
GAFFERSCENE_API bool visible( const ScenePlug *scene, const ScenePlug::ScenePath &path );

/// Returns a bounding box for the specified object. Typically
/// this is provided by the VisibleRenderable::bound() method, but
/// for other object types we must return a synthetic bound.
GAFFERSCENE_API Imath::Box3f bound( const IECore::Object *object );

} // namespace SceneAlgo

} // namespace GafferScene

#include "GafferScene/SceneAlgo.inl"

#endif // GAFFERSCENE_SCENEALGO_H
