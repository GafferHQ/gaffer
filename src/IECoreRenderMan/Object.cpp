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

#include "Object.h"

#include "Transform.h"

#include "RixPredefinedStrings.hpp"

using namespace std;
using namespace IECoreRenderMan;

namespace
{

const riley::CoordinateSystemList g_emptyCoordinateSystems = { 0, nullptr };

} // namespace

Object::Object( const std::string &name, const ConstGeometryPrototypePtr &geometryPrototype, const Attributes *attributes, const Session *session )
	:	m_session( session ), m_geometryInstance( riley::GeometryInstanceId::InvalidId() ), m_attributes( attributes ), m_geometryPrototype( geometryPrototype )
{
	m_extraAttributes.SetString( Rix::k_identifier_name, RtUString( name.c_str() ) );

	RtParamList allAttributes = m_attributes->instanceAttributes();
	allAttributes.Update( m_extraAttributes );

	m_geometryInstance = m_session->riley->CreateGeometryInstance(
		riley::UserId(),
		/* group = */ riley::GeometryPrototypeId::InvalidId(),
		m_geometryPrototype->id(),
		m_attributes->surfaceMaterial()->id(),
		g_emptyCoordinateSystems,
		IdentityTransform(),
		allAttributes
	);
}

Object::~Object()
{
	if( m_session->renderType == IECoreScenePreview::Renderer::Interactive )
	{
		if( m_geometryInstance != riley::GeometryInstanceId::InvalidId() )
		{
			m_session->riley->DeleteGeometryInstance( riley::GeometryPrototypeId::InvalidId(), m_geometryInstance );
		}
	}
}

void Object::transform( const Imath::M44f &transform )
{
	StaticTransform staticTransform( transform );
	const riley::GeometryInstanceResult result = m_session->riley->ModifyGeometryInstance(
		/* group = */ riley::GeometryPrototypeId::InvalidId(),
		m_geometryInstance,
		/* material = */ nullptr,
		/* coordsys = */ nullptr,
		&staticTransform,
		/* attributes = */ nullptr
	);

	if( result != riley::GeometryInstanceResult::k_Success )
	{
		IECore::msg( IECore::Msg::Warning, "RenderManObject::transform", "Unexpected edit failure" );
	}
}

void Object::transform( const std::vector<Imath::M44f> &samples, const std::vector<float> &times )
{
	AnimatedTransform animatedTransform( samples, times );
	const riley::GeometryInstanceResult result = m_session->riley->ModifyGeometryInstance(
		/* group = */ riley::GeometryPrototypeId::InvalidId(),
		m_geometryInstance,
		/* material = */ nullptr,
		/* coordsys = */ nullptr,
		&animatedTransform,
		/* attributes = */ nullptr
	);

	if( result != riley::GeometryInstanceResult::k_Success )
	{
		IECore::msg( IECore::Msg::Warning, "RenderManObject::transform", "Unexpected edit failure" );
	}
}

bool Object::attributes( const IECoreScenePreview::Renderer::AttributesInterface *attributes )
{
	const Attributes *typedAttributes = static_cast<const Attributes *>( attributes );
	if( typedAttributes->prototypeHash() != m_attributes->prototypeHash() )
	{
		return false;
	}

	RtParamList allAttributes = typedAttributes->instanceAttributes();
	allAttributes.Update( m_extraAttributes );

	const riley::GeometryInstanceResult result = m_session->riley->ModifyGeometryInstance(
		/* group = */ riley::GeometryPrototypeId::InvalidId(),
		m_geometryInstance,
		&typedAttributes->surfaceMaterial()->id(),
		/* coordsys = */ nullptr,
		/* xform = */ nullptr,
		&allAttributes
	);
	m_attributes = typedAttributes;

	if( result != riley::GeometryInstanceResult::k_Success )
	{
		IECore::msg( IECore::Msg::Warning, "RenderManObject::attributes", "Unexpected edit failure" );
	}
	return true;
}

void Object::link( const IECore::InternedString &type, const IECoreScenePreview::Renderer::ConstObjectSetPtr &objects )
{
}

void Object::assignID( uint32_t id )
{
}
