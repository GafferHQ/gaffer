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

#include "Attributes.h"
#include "GeometryPrototypeCache.h"
#include "LightLinker.h"
#include "MaterialCache.h"
#include "Session.h"

#include "Riley.h"

namespace IECoreRenderMan
{

class Light : public IECoreScenePreview::Renderer::ObjectInterface
{

	public :

		Light( const ConstGeometryPrototypePtr &geometryPrototype, const Attributes *attributes, MaterialCache *materialCache, LightLinker *lightLinker, Session *session );
		~Light() override;

		// ObjectInterface overrides
		// =========================

		void transform( const Imath::M44f &transform ) override;
		void transform( const std::vector<Imath::M44f> &samples, const std::vector<float> &times ) override;
		bool attributes( const IECoreScenePreview::Renderer::AttributesInterface *attributes ) override;
		void link( const IECore::InternedString &type, const IECoreScenePreview::Renderer::ConstObjectSetPtr &objects ) override;
		void assignID( uint32_t id ) override;
		void assignInstanceID( uint32_t id ) override;

		// Interface used by LightLinker
		// =============================

		void updateLightFilterShader( const IECoreScene::ConstShaderNetworkPtr &lightFilterShader );
		void updateLinking( RtUString memberships, RtUString shadowSubset );

	private :

		ConstLightShaderPtr acquireLightShader( const Attributes *attributes ) const;

		MaterialCache *m_materialCache;
		Session *m_session;
		LightLinker *m_lightLinker;
		ConstLightShaderPtr m_lightShader;
		riley::LightInstanceId m_lightInstance;
		Imath::M44f m_preTransform;
		/// Used to keep material etc alive as long as we need it.
		ConstAttributesPtr m_attributes;
		/// Used to keep geometry prototype alive as long as we need it.
		ConstGeometryPrototypePtr m_geometryPrototype;
		/// Combination of `m_attributes->instanceAttributes()` and
		/// "grouping:membership" attribute used to implement light linking.
		RtParamList m_allAttributes;
		IECoreScene::ConstShaderNetworkPtr m_lightFilterShader;
		IECoreScenePreview::Renderer::ConstObjectSetPtr m_linkedFilters;
		RtUString m_shadowSubset;

};

} // namespace IECoreRenderMan
