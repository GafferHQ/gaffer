//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2026, Cinesite VFX Ltd. All rights reserved.
//
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//
//     * Redistributions of source code must retain the above copyright
//       notice, this list of conditions and the following disclaimer.
//
//     * Redistributions in binary form must reproduce the above copyright
//       notice, this list of conditions and the following disclaimer in the
//       documentation and/or other materials provided with the distribution.
//
//     * Neither the name of Image Engine Design nor the names of any
//       other contributors to this software may be used to endorse or
//       promote products derived from this software without specific prior
//       written permission.
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

#include "IECoreScene/ShaderNetwork.h"
#include "IECoreScene/ShaderNetworkAlgo.h"

IECORE_PUSH_DEFAULT_VISIBILITY
#include "scene/object.h"
#include "scene/scene.h"
IECORE_POP_DEFAULT_VISIBILITY

#include "tbb/concurrent_hash_map.h"

namespace IECoreCycles
{

/// \todo This could probably go in its own header.
class Shader : public IECore::RefCounted
{

	public :

		~Shader() override;

		void hash( IECore::MurmurHash &h ) const;
		ccl::Shader *shader() const;

	private :

		friend class ShaderCache;

		/// Private constructor so only ShaderCache can create shaders. This
		/// gives us guarantees that the hash matches.
		Shader( ccl::Shader *shader, const IECore::MurmurHash &h );

		/// Note : `ccl::Scene::delete_nodes()` doesn't actually delete shader
		/// nodes, and `ShaderCache::clearUnused()` is a no-op, so we don't
		/// bother managing them via a NodeDeleter.
		ccl::Shader *m_shader;
		const IECore::MurmurHash m_hash;

};

IE_CORE_DECLAREPTR( Shader )

/// \todo This could probably go in its own header.
class ShaderCache
{

	public :

		ShaderCache( ccl::Scene *scene );

		ShaderPtr get( const IECoreScene::ShaderNetwork *surfaceShader );

		// Can be called concurrently with other get() calls.
		ShaderPtr get(
			const IECoreScene::ShaderNetwork *surfaceShader,
			const IECoreScene::ShaderNetwork *displacementShader,
			const IECoreScene::ShaderNetwork *volumeShader,
			const IECore::CompoundObject *attributes
		);

		// Must not be called concurrently with anything.
		void clearUnused();

	private :

		ccl::Scene *m_scene;
		using Cache = tbb::concurrent_hash_map<IECore::MurmurHash, ShaderPtr>;
		Cache m_cache;

};

class Attributes : public IECoreScenePreview::Renderer::AttributesInterface
{

	public :

		Attributes( const IECore::CompoundObject *attributes, ShaderCache *shaderCache );

		// Applies all relevant attributes to `object`.
		// > Note : Does not modify the geometry at `object->get_geometry()`.
		void applyObject( ccl::Object *object, ccl::Scene *scene ) const;

		// Geometry Attributes
		// ===================
		//
		// Some attributes apply to `ccl::Geometry`. These need careful handling
		// because they interact with automatic instancing.

		// Returns true if the given geometry can be instanced.
		bool canInstanceGeometry( const IECore::Object *object ) const;
		// Generates a signature for the work done by `applyGeometry()`.
		void hashGeometry( const IECore::Object *object, IECore::MurmurHash &h ) const;
		void hashGeometry( const ccl::Geometry *geometry, IECore::MurmurHash &h ) const;
		// Applies attributes relevant to `geometry`.
		void applyGeometry( ccl::Geometry *geometry, ccl::Scene *scene ) const;

		// Applies the shader to the geometry.
		void applyShader( ccl::Geometry *geometry, ccl::Scene *scene ) const;

		// Applies attributes relevant to `light`. Instancing is not an
		// issue here because we never instance lights.
		void applyLight( ccl::Light *light, ccl::Scene *scene ) const;

		int getVolumePrecision() const;
		float getVolumeClipping() const;

	private :

		void updateVisibility( const IECore::InternedString &name, int rayType, const IECore::CompoundObject *attributes );
		void hashSubdivision( IECore::MurmurHash &h ) const;

		struct Volume
		{
			Volume( const IECore::CompoundObject *attributes );

			std::optional<float> clipping;
			std::optional<float> stepSize;
			std::optional<bool> objectSpace;
			std::optional<float> velocityScale;
			std::optional<std::string> precision;

			void hash( IECore::MurmurHash &h ) const;
			void apply( ccl::Volume *volume ) const;

		};

		IECoreScene::ConstShaderNetworkPtr m_lightAttribute;
		ShaderPtr m_lightShader;
		ShaderPtr m_shader;
		int m_visibility;
		bool m_useHoldout;
		bool m_isShadowCatcher;
		float m_shadowTerminatorShadingOffset;
		float m_shadowTerminatorGeometryOffset;
		int m_maxLevel;
		float m_dicingRate;
		std::string m_adaptiveSpace;
		Imath::Color3f m_color;
		Volume m_volume;
		IECore::InternedString m_assetName;
		IECore::InternedString m_lightGroup;
		bool m_isCausticsCaster;
		bool m_isCausticsReceiver;
		bool m_muteLight;
		bool m_automaticInstancing;

		using CustomAttributes = ccl::vector<ccl::ParamValue>;
		CustomAttributes m_custom;

};

IE_CORE_DECLAREPTR( Attributes )

} // namespace IECoreCycles
