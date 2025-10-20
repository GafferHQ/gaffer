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

#include "Loader.h"
#include "Transform.h"

using namespace std;
using namespace IECoreRenderMan;

namespace
{

const riley::CoordinateSystemList g_emptyCoordinateSystems = { 0, nullptr };
const IECore::InternedString g_lights( "lights" );
const IECore::InternedString g_shadowedLights( "shadowedLights" );
const RtUString g_defaultShadowGroup( "defaultShadowGroup" );

} // namespace

Object::Object( const std::string &name, const ConstGeometryPrototypePtr &geometryPrototype, const Attributes *attributes, LightLinker *lightLinker, const Session *session )
	:	m_session( session ), m_lightLinker( lightLinker ), m_geometryInstance( riley::GeometryInstanceId::InvalidId() ), m_attributes( attributes ), m_geometryPrototype( geometryPrototype )
{
	m_extraAttributes.SetString( Loader::strings().k_identifier_name, RtUString( name.c_str() ) );
	m_extraAttributes.SetString( Loader::strings().k_grouping_membership, g_defaultShadowGroup );

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
		if( m_linkedLights )
		{
			m_lightLinker->deregisterLightSet( LightLinker::SetType::Light, m_linkedLights );
		}
		if( m_shadowedLights )
		{
			m_lightLinker->deregisterLightSet( LightLinker::SetType::Shadow, m_shadowedLights );
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
	IECoreScenePreview::Renderer::ConstObjectSetPtr *setMemberData;
	LightLinker::SetType setType;
	RtUString attributeName;
	RtUString defaultAttributeValue;

	if( type == g_lights )
	{
		setMemberData = &m_linkedLights;
		setType = LightLinker::SetType::Light;
		attributeName = Loader::strings().k_lighting_subset;
	}
	else if( type == g_shadowedLights )
	{
		setMemberData = &m_shadowedLights;
		setType = LightLinker::SetType::Shadow;
		attributeName = Loader::strings().k_grouping_membership;
		defaultAttributeValue = g_defaultShadowGroup;
	}
	else
	{
		return;
	}

	if( *setMemberData )
	{
		m_lightLinker->deregisterLightSet( setType, *setMemberData );
	}
	*setMemberData = objects;

	RtUString attributeValue = defaultAttributeValue;
	if( objects )
	{
		attributeValue = m_lightLinker->registerLightSet( setType, objects );
	}

	m_extraAttributes.SetString( attributeName, attributeValue );
	attributes( m_attributes.get() );
}

void Object::assignID( uint32_t id )
{
	m_extraAttributes.SetInteger( Loader::strings().k_identifier_id, id );
	attributes( m_attributes.get() );
}

void Object::assignInstanceID( uint32_t id )
{
	// \todo : This will be needed once our RenderMan backend supports encapsulated instancers
}
