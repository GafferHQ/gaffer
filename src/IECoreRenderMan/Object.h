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

#include "Attributes.h"
#include "GeometryPrototypeCache.h"
#include "Session.h"

#include "GafferScene/Private/IECoreScenePreview/Renderer.h"

namespace IECoreRenderMan
{

class Object : public IECoreScenePreview::Renderer::ObjectInterface
{

	public :

		Object( const ConstGeometryPrototypePtr &geometryPrototype, const Attributes *attributes, const Session *session );
		~Object();

		/// \todo RenderMan volumes seem to reject attempts to transform them
		/// after creation, althought we get lucky and the first one works
		/// despite returning a failure code. Perhaps we need to add transform
		/// arguments to `Renderer::object()` and to be able to return a `bool`
		/// here to request that the object is sent again instead?
		void transform( const Imath::M44f &transform ) override;
		void transform( const std::vector<Imath::M44f> &samples, const std::vector<float> &times ) override;
		bool attributes( const IECoreScenePreview::Renderer::AttributesInterface *attributes ) override;
		void link( const IECore::InternedString &type, const IECoreScenePreview::Renderer::ConstObjectSetPtr &objects ) override;
		void assignID( uint32_t id ) override;

	private :

		const Session *m_session;
		riley::GeometryInstanceId m_geometryInstance;
		/// Used to keep material etc alive as long as we need it.
		ConstAttributesPtr m_attributes;
		/// Used to keep geometry prototype alive as long as we need it.
		ConstGeometryPrototypePtr m_geometryPrototype;

};

} // namespace IECoreRenderMan
