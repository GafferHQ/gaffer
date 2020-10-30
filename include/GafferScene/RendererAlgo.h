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

#ifndef GAFFERSCENE_RENDERERALGO_H
#define GAFFERSCENE_RENDERERALGO_H

#include "GafferScene/ScenePlug.h"

#include "GafferScene/Private/IECoreScenePreview/Renderer.h"

#include "IECoreScene/Camera.h"
#include "IECoreScene/VisibleRenderable.h"

#include "IECore/CompoundObject.h"
#include "IECore/VectorTypedData.h"

#include "boost/container/flat_map.hpp"

#include "tbb/concurrent_hash_map.h"
#include "tbb/spin_mutex.h"

#include <functional>

namespace GafferScene
{

IE_CORE_FORWARDDECLARE( SceneProcessor )

namespace RendererAlgo
{

/// Creates the directories necessary to receive the outputs defined in globals.
GAFFERSCENE_API void createOutputDirectories( const IECore::CompoundObject *globals );

/// Samples the local transform from the current location in preparation for output to the renderer.
/// If segments is 0, the transform is sampled at the time from the current context. If it is non-zero then
/// the sampling is performed evenly across the shutter interval, which should have been obtained via
/// SceneAlgo::shutter(). If all samples turn out to be identical, they will be collapsed automatically
/// into a single sample. The sampleTimes container is only filled if there is more than one sample.
GAFFERSCENE_API void transformSamples( const ScenePlug *scene, size_t segments, const Imath::V2f &shutter, std::vector<Imath::M44f> &samples, std::vector<float> &sampleTimes );

/// Samples the object from the current location in preparation for output to the renderer. Sampling parameters
/// are as for the transformSamples() method. Multiple samples will only be generated for Primitives, since other
/// object types cannot be interpolated anyway.
GAFFERSCENE_API void objectSamples( const ScenePlug *scene, size_t segments, const Imath::V2f &shutter, std::vector<IECoreScene::ConstVisibleRenderablePtr> &samples, std::vector<float> &sampleTimes );

/// Function to return a SceneProcessor used to adapt the
/// scene for rendering.
typedef std::function<SceneProcessorPtr ()> Adaptor;
/// Registers an adaptor.
GAFFERSCENE_API void registerAdaptor( const std::string &name, Adaptor adaptor );
/// Removes a previously registered adaptor.
GAFFERSCENE_API void deregisterAdaptor( const std::string &name );
/// Returns a SceneProcessor that will apply all the currently
/// registered adaptors.
GAFFERSCENE_API SceneProcessorPtr createAdaptors();

GAFFERSCENE_API void outputOptions( const IECore::CompoundObject *globals, IECoreScenePreview::Renderer *renderer );
GAFFERSCENE_API void outputOptions( const IECore::CompoundObject *globals, const IECore::CompoundObject *previousGlobals, IECoreScenePreview::Renderer *renderer );

GAFFERSCENE_API void outputOutputs( const ScenePlug *scene, const IECore::CompoundObject *globals, IECoreScenePreview::Renderer *renderer );
GAFFERSCENE_API void outputOutputs( const ScenePlug *scene, const IECore::CompoundObject *globals, const IECore::CompoundObject *previousGlobals, IECoreScenePreview::Renderer *renderer );

/// Utility class to handle all the set computations needed for a render.
class GAFFERSCENE_API RenderSets : boost::noncopyable
{

	public :

		RenderSets();
		RenderSets( const ScenePlug *scene );

		enum Changed
		{
			NothingChanged = 0,
			CamerasSetChanged = 1,
			LightsSetChanged = 2,
			LightFiltersSetChanged = 4,
			RenderSetsChanged = 8
		};

		/// Returns a bitmask describing which sets
		/// changed.
		unsigned update( const ScenePlug *scene );
		void clear();

		const IECore::PathMatcher &camerasSet() const;
		const IECore::PathMatcher &lightsSet() const;
		const IECore::PathMatcher &lightFiltersSet() const;

		IECore::ConstInternedStringVectorDataPtr setsAttribute( const std::vector<IECore::InternedString> &path ) const;

	private :

		struct Set
		{
			IECore::InternedString unprefixedName; // With "render:" stripped off
			IECore::MurmurHash hash;
			IECore::PathMatcher set;
		};

		typedef boost::container::flat_map<IECore::InternedString, Set> Sets;

		struct Updater;

		// Stores all the "render:" sets.
		Sets m_sets;
		Set m_camerasSet;
		Set m_lightsSet;
		Set m_lightFiltersSet;

};

/// Utility class to declare light links to a renderer.
class GAFFERSCENE_API LightLinks : boost::noncopyable
{

	public :

		LightLinks();

		/// Registration functions
		/// ======================
		///
		/// These may be called concurrently with one another, and are used to inform the
		/// LightLinks class of all lights and light filters present in a render.

		void addLight( const std::string &path, const IECoreScenePreview::Renderer::ObjectInterfacePtr &light );
		void removeLight( const std::string &path );

		void addLightFilter( const IECoreScenePreview::Renderer::ObjectInterfacePtr &lightFilter, const IECore::CompoundObject *attributes );
		void updateLightFilter( const IECoreScenePreview::Renderer::ObjectInterfacePtr &lightFilter, const IECore::CompoundObject *attributes );
		void removeLightFilter( const IECoreScenePreview::Renderer::ObjectInterfacePtr &lightFilter );

		/// Output functions
		/// ================
		///
		/// These output light links and light filter links, and should be called
		/// once all lights and filters have been declared via the registration
		/// methods above.

		/// Outputs light links for the specified location. May be called concurrently
		/// with respect to itself, but not other methods. The optional `hash` pointer
		/// should be unique to `object`, and will be used to optimise subsequent calls
		/// for the same object.
		/// > Note : `hash` is an awkward implementation detail used to allow
		/// > LightLinks to store some state in RenderController's scene graphs.
		/// > The alternative would be to register all objects with LightLinks,
		/// > but then we would have duplicate storage structures for the entire scene.
		void outputLightLinks( const ScenePlug *scene, const IECore::CompoundObject *attributes, IECoreScenePreview::Renderer::ObjectInterface *object, IECore::MurmurHash *hash = nullptr ) const;
		/// Outputs all light filter links at once.
		void outputLightFilterLinks( const ScenePlug *scene );

		/// Dirty state
		/// ===========
		///
		/// When using LightLinks in an interactive render, it is necessary to
		/// track some state to determine when the output functions need to be
		/// called. These methods take care of that.

		/// Must be called when the scene sets have been dirtied.
		void setsDirtied();
		/// Returns true if calls to `outputLightLinks()` are necessary. Note
		/// that this only considers light registrations and set dirtiness - as
		/// the caller supplies the attributes, it is the caller's responsibility
		/// to track attribute changes per location as necessary.
		bool lightLinksDirty() const;
		/// Returns true if a call to `outputLightFilterLinks()` is necessary.
		bool lightFilterLinksDirty() const;
		/// Must be called once all necessary calls to `outputLightLinks()`
		/// and `outputLightFilterLinks()` have been made.
		void clean();

	private :

		void addFilterLink( const IECoreScenePreview::Renderer::ObjectInterfacePtr &lightFilter, const std::string &filteredLightsExpression );
		void removeFilterLink( const IECoreScenePreview::Renderer::ObjectInterfacePtr &lightFilter, const std::string &filteredLightsExpression );
		std::string filteredLightsExpression( const IECore::CompoundObject *attributes ) const;
		IECoreScenePreview::Renderer::ConstObjectSetPtr linkedLights( const std::string &linkedLightsExpression, const ScenePlug *scene ) const;
		void outputLightFilterLinks( const std::string &lightName, IECoreScenePreview::Renderer::ObjectInterface *light ) const;
		void clearLightLinks();

		/// Storage for lights. This maps from the light name to the light itself.
		using LightMap = tbb::concurrent_hash_map<std::string, IECoreScenePreview::Renderer::ObjectInterfacePtr>;
		LightMap m_lights;

		/// Storage for filters. This maps from filter to `filteredLights` set expression.
		using FilterMap = tbb::concurrent_hash_map<IECoreScenePreview::Renderer::ObjectInterfacePtr, std::string>;
		FilterMap m_filters;

		/// Storage for light link sets
		/// ===========================
		///
		/// This maps from `linkedLights` expressions to ObjectSets containing
		/// the relevant lights.

		using LightLinkMap = tbb::concurrent_hash_map<std::string, IECoreScenePreview::Renderer::ObjectSetPtr>;
		mutable LightLinkMap m_lightLinks;
		tbb::spin_mutex m_lightLinksClearMutex;

		/// Storage for links between lights and light filters
		/// ==================================================
		///
		/// A naive implementation might store an ObjectSet per light, but this
		/// can have huge memory requirements where a large number of filters
		/// are linked to a large number of lights. Instead we group filters
		/// according to their assignments.

		/// Object containing all filters which are linked
		/// to the same set of lights.
		struct FilterLink
		{
			IECore::PathMatcher filteredLights;
			bool filteredLightsDirty;
			IECoreScenePreview::Renderer::ObjectSetPtr lightFilters;
		};

		/// Maps from `filteredLights` set expressions to FilterLinks.
		using FilterLinkMap = tbb::concurrent_hash_map<std::string, FilterLink>;
		FilterLinkMap m_filterLinks;

		/// Dirty state
		std::atomic_bool m_lightLinksDirty;
		std::atomic_bool m_lightFilterLinksDirty;

};

GAFFERSCENE_API void outputCameras( const ScenePlug *scene, const IECore::CompoundObject *globals, const RenderSets &renderSets, IECoreScenePreview::Renderer *renderer );
GAFFERSCENE_API void outputLightFilters( const ScenePlug *scene, const IECore::CompoundObject *globals, const RenderSets &renderSets, LightLinks *lightLinks, IECoreScenePreview::Renderer *renderer );
GAFFERSCENE_API void outputLights( const ScenePlug *scene, const IECore::CompoundObject *globals, const RenderSets &renderSets, LightLinks *lightLinks, IECoreScenePreview::Renderer *renderer );
GAFFERSCENE_API void outputObjects( const ScenePlug *scene, const IECore::CompoundObject *globals, const RenderSets &renderSets, const LightLinks *lightLinks, IECoreScenePreview::Renderer *renderer, const ScenePlug::ScenePath &root = ScenePlug::ScenePath() );

/// Applies the resolution, aspect ratio etc from the globals to the camera.
GAFFERSCENE_API void applyCameraGlobals( IECoreScene::Camera *camera, const IECore::CompoundObject *globals, const ScenePlug *scene );

} // namespace RendererAlgo

} // namespace GafferScene

#endif // GAFFERSCENE_RENDERERALGO_H
