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

#include "IECoreScene/Camera.h"
#include "IECoreScene/VisibleRenderable.h"

#include "IECore/CompoundObject.h"
#include "IECore/VectorTypedData.h"

#include "boost/container/flat_map.hpp"

#include <functional>

namespace IECoreScenePreview
{

class Renderer;

} // namespace IECoreScenePreview

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
GAFFERSCENE_API void transformSamples( const ScenePlug *scene, size_t segments, const Imath::V2f &shutter, std::vector<Imath::M44f> &samples, std::set<float> &sampleTimes );

/// Samples the object from the current location in preparation for output to the renderer. Sampling parameters
/// are as for the transformSamples() method. Multiple samples will only be generated for Primitives, since other
/// object types cannot be interpolated anyway.
GAFFERSCENE_API void objectSamples( const ScenePlug *scene, size_t segments, const Imath::V2f &shutter, std::vector<IECoreScene::ConstVisibleRenderablePtr> &samples, std::set<float> &sampleTimes );

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

GAFFERSCENE_API void outputOutputs( const IECore::CompoundObject *globals, IECoreScenePreview::Renderer *renderer );
GAFFERSCENE_API void outputOutputs( const IECore::CompoundObject *globals, const IECore::CompoundObject *previousGlobals, IECoreScenePreview::Renderer *renderer );

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

GAFFERSCENE_API void outputCameras( const ScenePlug *scene, const IECore::CompoundObject *globals, const RenderSets &renderSets, IECoreScenePreview::Renderer *renderer );
GAFFERSCENE_API void outputLights( const ScenePlug *scene, const IECore::CompoundObject *globals, const RenderSets &renderSets, IECoreScenePreview::Renderer *renderer );
GAFFERSCENE_API void outputLightFilters( const ScenePlug *scene, const IECore::CompoundObject *globals, const RenderSets &renderSets, IECoreScenePreview::Renderer *renderer );
GAFFERSCENE_API void outputObjects( const ScenePlug *scene, const IECore::CompoundObject *globals, const RenderSets &renderSets, IECoreScenePreview::Renderer *renderer, const ScenePlug::ScenePath &root = ScenePlug::ScenePath() );

/// Applies the resolution, aspect ratio etc from the globals to the camera.
GAFFERSCENE_API void applyCameraGlobals( IECoreScene::Camera *camera, const IECore::CompoundObject *globals, const ScenePlug *scene );

} // namespace RendererAlgo

} // namespace GafferScene

#endif // GAFFERSCENE_RENDERERALGO_H
