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

#include "GafferScene/Private/IECoreScenePreview/Renderer.h"

#include "Riley.h"

#include "boost/multi_index/member.hpp"
#include "boost/multi_index/ordered_index.hpp"
#include "boost/multi_index_container.hpp"

#include "tbb/concurrent_hash_map.h"
#include "tbb/concurrent_unordered_map.h"

#include <mutex>

namespace IECoreRenderMan
{

/// Owns a Riley instance and tracks shared state to facilitate communication
/// between the various Renderer subcomponents. Riley is essentially a "write only"
/// API, so if we want access to any state we need to track it ourselves.
struct Session
{

	/// Options must be provided at construction time, as Riley requires them to
	/// be set before any other operations can take place (and indeed, will crash
	/// if the Riley instance is destroyed without `SetOptions()` being called).
	Session( IECoreScenePreview::Renderer::RenderType renderType, const RtParamList &options, const IECore::MessageHandlerPtr &messageHandler );
	~Session();

	riley::Riley *riley;
	const IECoreScenePreview::Renderer::RenderType renderType;

	/// Riley API Wrappers
	/// ==================
	///
	/// These functions all wrap the equivalent Riley methods directly, allowing
	/// the Session to track state that Riley does not provide queries for. This
	/// is necessary for handling some of the more awkward mappings from the
	/// `IECoreScene::Renderer` API to the Riley API.
	///
	/// > Note : Where a wrapper exists, you _must_ use it in preference to calling
	/// > Riley directly. Where no wrapper exists for a Riley method, then that method
	/// > may be called directly.

	/// Cameras
	/// -------

	/// > Note : The `options` argument is not for `Riley::CreateCamera()`, but is
	/// > a session-specific argument used to pass resolution etc from the camera to
	/// > the session's options.
	riley::CameraId createCamera( RtUString name, const riley::ShadingNode &projection, const riley::Transform &transform, const RtParamList &properties, const RtParamList &options );
	void deleteCamera( riley::CameraId cameraId );

	/// Lights
	/// ------

	riley::LightShaderId createLightShader( const riley::ShadingNetwork &light, const riley::ShadingNetwork &lightFilter );
	void deleteLightShader( riley::LightShaderId lightShaderId );

	riley::LightInstanceId createLightInstance( riley::GeometryPrototypeId geometry, riley::MaterialId materialId, riley::LightShaderId lightShaderId, const riley::CoordinateSystemList &coordinateSystems, const riley::Transform &transform, const RtParamList &attributes );
	riley::LightInstanceResult modifyLightInstance(
		riley::LightInstanceId lightInstanceId, const riley::MaterialId *materialId, const riley::LightShaderId *lightShaderId, const riley::CoordinateSystemList *coordinateSystems, const riley::Transform *transform,
		const RtParamList *attributes
	);
	void deleteLightInstance( riley::LightInstanceId lightInstanceId );

	/// Camera Queries
	/// ==============

	struct CameraInfo
	{
		std::string name;
		riley::CameraId id;
		RtParamList options;
	};

	/// Returns information about the camera with the specified name.
	CameraInfo cameraInfo( const std::string &name ) const;

	/// Light Synchronisation
	/// =====================

	/// Should be called before rendering to update the links between
	/// portal lights and the associated dome light.
	void updatePortals();

	private :

		struct ExceptionHandler;
		std::unique_ptr<ExceptionHandler> m_exceptionHandler;

		// Map for tracking cameras. We need to index this with both CameraId and name,
		// so use `multi_index_container`. We don't anticipate many cameras being created
		// concurrently so are content to use a mutex to provide thread safety.
		mutable std::mutex m_camerasMutex;
		using CameraMap = boost::multi_index::multi_index_container<
			CameraInfo,
			boost::multi_index::indexed_by<
				boost::multi_index::ordered_unique<
					boost::multi_index::member<CameraInfo, riley::CameraId, &CameraInfo::id>
				>,
				boost::multi_index::ordered_unique<
					boost::multi_index::member<CameraInfo, std::string, &CameraInfo::name>
				>
			>
		>;
		CameraMap m_cameras;

		struct LightShaderInfo
		{
			std::vector<riley::ShadingNode> shaders;
			std::vector<riley::ShadingNode> lightFilterShaders;
		};

		// Keys are `riley::LightShaderId`. The `concurrent_unordered_map` gives
		// us thread-safety for the map data structure itself, but not for the
		// values within. This is exactly what we need, as we may be editing shaders
		// from many threads, but any particular shader will only be modified by
		// a single thread at a time.
		using LightShaderMap = tbb::concurrent_unordered_map<uint32_t, LightShaderInfo>;
		LightShaderMap m_domeAndPortalShaders;

		struct LightInfo
		{
			riley::LightShaderId lightShader;
			RtMatrix4x4 transform;
			RtParamList attributes;
		};
		// Keys are `riley::LightInstanceId`.
		using LightInstanceMap = tbb::concurrent_unordered_map<uint32_t, LightInfo>;
		LightInstanceMap m_domeAndPortalLights;
		std::atomic_bool m_portalsDirty;

};

IE_CORE_DECLAREPTR( Session );

} // namespace IECoreRenderMan
