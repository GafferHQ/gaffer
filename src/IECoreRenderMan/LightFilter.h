//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2025, Cinesite VFX Ltd. All rights reserved.
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
#include "LightLinker.h"
#include "Session.h"

#include "Riley.h"

namespace IECoreRenderMan
{

class LightFilter : public IECoreScenePreview::Renderer::ObjectInterface
{

	public :

		LightFilter( const std::string &name, const Attributes *attributes, Session *session, LightLinker *lightLinker );
		~LightFilter();

		// ObjectInterface overrides
		// =========================

		void transform( const Imath::M44f &transform ) override;
		void transform( const std::vector<Imath::M44f> &samples, const std::vector<float> &times ) override;
		bool attributes( const IECoreScenePreview::Renderer::AttributesInterface *attributes ) override;
		void link( const IECore::InternedString &type, const IECoreScenePreview::Renderer::ConstObjectSetPtr &objects ) override;
		void assignID( uint32_t id ) override;

		// Interface used by Light and LightLinker
		// =======================================
		//
		// Light filters aren't first class objects in RenderMan. Instead they
		// are just bits of state on light shaders and light instances. The
		// methods here allow Light and LightLinker to update lights to reflect
		// changes to the filters linked to them.

		riley::CoordinateSystemId coordinateSystem() const { return m_coordinateSystem; }
		const IECoreScene::ShaderNetwork *shader() const { return m_shader.get(); }

		using WeakObjectSetPtr = std::weak_ptr<const IECoreScenePreview::Renderer::ObjectSet>;
		/// \todo Use `unordered_map` (or `concurrent_unordered_map`) when `std::owner_hash()`
		/// becomes available (C++26).
		using SetMemberships = std::set<WeakObjectSetPtr, std::owner_less<WeakObjectSetPtr>>;
		SetMemberships &setMemberships() { return m_setMemberships; }
		const SetMemberships &setMemberships() const { return m_setMemberships; }

	private :

		Session *m_session;

		RtUString m_coordinateSystemName;
		riley::CoordinateSystemId m_coordinateSystem;
		IECore::MurmurHash m_shaderHash;
		IECoreScene::ConstShaderNetworkPtr m_shader;
		LightLinker *m_lightLinker;
		SetMemberships m_setMemberships;

};

} // namespace IECoreRenderMan
