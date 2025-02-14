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

#include "MaterialCache.h"

namespace IECoreRenderMan
{

class Attributes : public IECoreScenePreview::Renderer::AttributesInterface
{

	public :

		Attributes( const IECore::CompoundObject *attributes, MaterialCache *materialCache );
		~Attributes();

		/// Returns a hash of everything in `prototypeParamList()`, to be
		/// used by GeometryPrototypeCache when automaticaly deduplicating
		/// objects. Returns `std::nullopt` if automatic instancing is
		/// turned off.
		/// \todo Should we have different hashes for different object types,
		/// so attributes for curves (for example) don't mess with instancing
		/// of meshes?
		const std::optional<IECore::MurmurHash> &prototypeHash() const;
		/// Attributes to be applied when creating GeometryPrototypes.
		const RtParamList &prototypeAttributes() const;
		/// Attributes to be applied to GeometryInstances.
		const RtParamList &instanceAttributes() const;

		const Material *surfaceMaterial() const;
		const Displacement *displacement() const { return m_displacement.get(); }

		const IECoreScene::ShaderNetwork *lightShader() const;
		/// Material to be assigned to lights. RenderMan uses this to
		/// shade ray hits on mesh lights, while using `lightShader()` for
		/// light emission. Returns `nullptr` for all non-mesh lights.
		const Material *lightMaterial() const;

	private :

		std::optional<IECore::MurmurHash> m_prototypeHash;
		RtParamList m_prototypeAttributes;
		RtParamList m_instanceAttributes;
		ConstMaterialPtr m_surfaceMaterial;
		ConstDisplacementPtr m_displacement;
		/// \todo Could we use the material cache for these too?
		IECoreScene::ConstShaderNetworkPtr m_lightShader;
		ConstMaterialPtr m_lightMaterial;

};

IE_CORE_DECLAREPTR( Attributes )

} // namespace IECoreRenderMan
