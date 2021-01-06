//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2019, Image Engine Design Inc. All rights reserved.
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

#include "GafferScene/Private/IECoreScenePreview/CapturingRenderer.h"

#include "IECore/MessageHandler.h"
#include "IECore/SimpleTypedData.h"

using namespace std;
using namespace IECore;
using namespace IECoreScenePreview;

//////////////////////////////////////////////////////////////////////////
// CapturingRenderer
//////////////////////////////////////////////////////////////////////////

IECoreScenePreview::Renderer::TypeDescription<CapturingRenderer> CapturingRenderer::g_typeDescription( "Capturing" );

CapturingRenderer::CapturingRenderer( RenderType type, const std::string &fileName, const IECore::MessageHandlerPtr &messageHandler )
	:	m_messageHandler( messageHandler ), m_renderType( type ), m_rendering( false )
{
}

CapturingRenderer::~CapturingRenderer()
{
	for( auto o : m_capturedObjects )
	{
		// Reset soon-to-be-dangling pointer from CapturedObject, in
		// case clients keep the object alive longer than the renderer.
		o.second->m_renderer = nullptr;
		if( m_renderType != Interactive )
		{
			// Remove reference added in `object()`.
			o.second->removeRef();
		}
	}
}

const CapturingRenderer::CapturedObject *CapturingRenderer::capturedObject( const std::string &name ) const
{
	ObjectMap::accessor a;
	if( m_capturedObjects.find( a, name ) )
	{
		return a->second;
	}

	return nullptr;
}

IECore::InternedString CapturingRenderer::name() const
{
	return "Capturing";
}

void CapturingRenderer::option( const IECore::InternedString &name, const IECore::Object *value )
{
	/// \todo Implement
}

void CapturingRenderer::output( const IECore::InternedString &name, const IECoreScene::Output *output )
{
	/// \todo Implement
}

Renderer::AttributesInterfacePtr CapturingRenderer::attributes( const IECore::CompoundObject *attributes )
{
	return new CapturedAttributes( ConstCompoundObjectPtr( attributes ) );
}

Renderer::ObjectInterfacePtr CapturingRenderer::camera( const std::string &name, const IECoreScene::Camera *camera, const AttributesInterface *attributes )
{
	return this->object( name, camera, attributes );
}

Renderer::ObjectInterfacePtr CapturingRenderer::light( const std::string &name, const IECore::Object *object, const AttributesInterface *attributes )
{
	return this->object( name, object, attributes );
}

Renderer::ObjectInterfacePtr CapturingRenderer::lightFilter( const std::string &name, const IECore::Object *object, const AttributesInterface *attributes )
{
	return this->object( name, object, attributes );
}

Renderer::ObjectInterfacePtr CapturingRenderer::object( const std::string &name, const IECore::Object *object, const AttributesInterface *attributes )
{
	return this->object( name, { object }, {}, attributes );
}

Renderer::ObjectInterfacePtr CapturingRenderer::object( const std::string &name, const std::vector<const IECore::Object *> &samples, const std::vector<float> &times, const AttributesInterface *attributes )
{
	IECore::MessageHandler::Scope s( m_messageHandler.get() );

	checkPaused();

	// To facilitate the testing of code that handles the return from the various object methods of
	// a renderer, we return null if the `cr:unrenderable` attribute is set to true.
	if( const auto attr = dynamic_cast<const CapturingRenderer::CapturedAttributes *>( attributes ) )
	{
		const BoolData *attrData = attr->attributes()->member<BoolData>( "cr:unrenderable" );
		if( attrData && attrData->readable() )
		{
			return nullptr;
		}
	}

	ObjectMap::accessor a;
	if( !m_capturedObjects.insert( a, name ) )
	{
		IECore::msg( IECore::Msg::Warning, "CapturingRenderer::object",
			boost::str( boost::format( "Object named \"%s\" already exists" ) % name )
		);
		return nullptr;
	}

	CapturedObjectPtr result = new CapturedObject( this, name, samples, times );
	result->attributes( attributes );
	a->second = result.get();
	if( m_renderType != Interactive )
	{
		// For non-interactive renders, the client code will typically drop
		// their reference to the object immediately, but we still want to
		// capture it for later examination. Add a reference to keep it alive.
		// See ~CapturingRenderer for the associated `removeRef()`.
		a->second->addRef();
	}

	return result;
}

void CapturingRenderer::render()
{
	IECore::MessageHandler::Scope s( m_messageHandler.get() );

	if( m_rendering )
	{
		IECore::msg( IECore::Msg::Warning, "CapturingRenderer::render", "Already rendering" );
	}
	m_rendering = true;
}

void CapturingRenderer::pause()
{
	IECore::MessageHandler::Scope s( m_messageHandler.get() );

	if( m_rendering )
	{
		IECore::msg( IECore::Msg::Warning, "CapturingRenderer::pause", "Not rendering" );
	}
	m_rendering = false;
}

void CapturingRenderer::checkPaused() const
{
	if( m_rendering )
	{
		IECore::msg( IECore::Msg::Warning, "CapturingRenderer", "Edit made while not paused" );
	}
}

//////////////////////////////////////////////////////////////////////////
// CapturedAttributes
//////////////////////////////////////////////////////////////////////////

CapturingRenderer::CapturedAttributes::CapturedAttributes( const IECore::ConstCompoundObjectPtr &attributes )
	:	m_attributes( attributes )
{
}

const IECore::CompoundObject *CapturingRenderer::CapturedAttributes::attributes() const
{
	return m_attributes.get();
}

//////////////////////////////////////////////////////////////////////////
// CapturedObject
//////////////////////////////////////////////////////////////////////////

CapturingRenderer::CapturedObject::CapturedObject( CapturingRenderer *renderer, const std::string &name, const std::vector<const IECore::Object *> &samples, const std::vector<float> &times )
	:	m_renderer( renderer ), m_name( name ), m_capturedSamples( samples.begin(), samples.end() ), m_capturedSampleTimes( times ), m_numAttributeEdits( 0 )
{
}

CapturingRenderer::CapturedObject::~CapturedObject()
{
	if( m_renderer && m_renderer->m_renderType == RenderType::Interactive )
	{
		// If the client of an interactive render drops ownership, that means
		// they want the object to be deleted from the renderer.
		m_renderer->m_capturedObjects.erase( m_name );
	}
}

const std::vector<IECore::ConstObjectPtr> &CapturingRenderer::CapturedObject::capturedSamples() const
{
	return m_capturedSamples;
}

const std::vector<float> &CapturingRenderer::CapturedObject::capturedSampleTimes() const
{
	return m_capturedSampleTimes;
}

const CapturingRenderer::CapturedAttributes *CapturingRenderer::CapturedObject::capturedAttributes() const
{
	return m_capturedAttributes.get();
}

const Renderer::ObjectSet *CapturingRenderer::CapturedObject::capturedLinks( const IECore::InternedString &type ) const
{
	auto it = m_capturedLinks.find( type );
	if( it == m_capturedLinks.end() )
	{
		return nullptr;
	}

	return it->second.first.get();
}

int CapturingRenderer::CapturedObject::numAttributeEdits() const
{
	return m_numAttributeEdits;
}

int CapturingRenderer::CapturedObject::numLinkEdits( const IECore::InternedString &type ) const
{
	auto it = m_capturedLinks.find( type );
	if( it == m_capturedLinks.end() )
	{
		return 0;
	}
	return it->second.second;
}

void CapturingRenderer::CapturedObject::transform( const Imath::M44f &transform )
{
	m_renderer->checkPaused();
	/// \todo Implement
}

void CapturingRenderer::CapturedObject::transform( const std::vector<Imath::M44f> &samples, const std::vector<float> &times )
{
	m_renderer->checkPaused();
	/// \todo Implement
}

bool CapturingRenderer::CapturedObject::attributes( const AttributesInterface *attributes )
{
	m_renderer->checkPaused();
	m_capturedAttributes = static_cast<const CapturedAttributes *>( attributes );
	m_numAttributeEdits++;
	return true;
}

void CapturingRenderer::CapturedObject::link( const IECore::InternedString &type, const ConstObjectSetPtr &objects )
{
	m_renderer->checkPaused();
	auto &p = m_capturedLinks[type];
	p.first = objects;
	p.second++;
}
