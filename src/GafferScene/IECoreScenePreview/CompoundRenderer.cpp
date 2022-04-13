//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2022, Cinesite VFX Ltd. All rights reserved.
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

#include "GafferScene/Private/IECoreScenePreview/CompoundRenderer.h"

#include "IECoreScene/Output.h"

#include "IECore/VectorTypedData.h"

#include "boost/algorithm/string/predicate.hpp"

using namespace std;
using namespace IECoreScenePreview;

//////////////////////////////////////////////////////////////////////////
// Internal object types
//////////////////////////////////////////////////////////////////////////

namespace
{

struct CompoundAttributesInterface : public IECoreScenePreview::Renderer::AttributesInterface
{

	CompoundAttributesInterface( CompoundRenderer::Renderers &renderers, const IECore::CompoundObject *a )
	{
		for( size_t i = 0; i < renderers.size(); ++i )
		{
			attributes[i] = renderers[i]->attributes( a );
		}
	}

	std::array<Renderer::AttributesInterfacePtr, 2> attributes;

};

struct CompoundObjectInterface : public IECoreScenePreview::Renderer::ObjectInterface
{

	void transform( const Imath::M44f &transform ) override
	{
		for( auto &o : objects )
		{
			if( o )
			{
				o->transform( transform );
			}
		}
	}

	void transform( const std::vector<Imath::M44f> &samples, const std::vector<float> &times ) override
	{
		for( auto &o : objects )
		{
			if( o )
			{
				o->transform( samples, times );
			}
		}
	}

	bool attributes( const IECoreScenePreview::Renderer::AttributesInterface *attributes ) override
	{
		auto *compoundAttributes = static_cast<const CompoundAttributesInterface *>( attributes );
		for( size_t i = 0; i < objects.size(); ++i )
		{
			if( objects[i] && !objects[i]->attributes( compoundAttributes->attributes[i].get() ) )
			{
				return false;
			}
		}
		return true;
	}

	void link( const IECore::InternedString &type, const IECoreScenePreview::Renderer::ConstObjectSetPtr &compoundObjectSet ) override
	{
		for( size_t i = 0; i < objects.size(); ++i )
		{
			if( !objects[i] )
			{
				continue;
			}
			else if( !compoundObjectSet )
			{
				objects[i]->link( type, nullptr );
			}
			else
			{
				auto objectSet = std::make_shared<Renderer::ObjectSet>();
				for( auto &o : *compoundObjectSet )
				{
					objectSet->insert( static_cast<CompoundObjectInterface *>( o.get() )->objects[i] );
				}
				objects[i]->link( type, objectSet );
			}
		}
	}

	std::array<IECoreScenePreview::Renderer::ObjectInterfacePtr, 2> objects;

};

IE_CORE_DECLAREPTR( CompoundObjectInterface )

} // namespace

//////////////////////////////////////////////////////////////////////////
// Renderer implementation
//////////////////////////////////////////////////////////////////////////

CompoundRenderer::CompoundRenderer( const Renderers &renderers )
	:	Renderer(), m_renderers( renderers )
{
}

CompoundRenderer::~CompoundRenderer()
{
}

IECore::InternedString CompoundRenderer::name() const
{
	return "Compound";
}

void CompoundRenderer::option( const IECore::InternedString &name, const IECore::Object *value )
{
	for( auto &r : m_renderers )
	{
		r->option( name, value );
	}
}

void CompoundRenderer::output( const IECore::InternedString &name, const IECoreScene::Output *output )
{
	for( auto &r : m_renderers )
	{
		r->output( name, output );
	}
}

Renderer::AttributesInterfacePtr CompoundRenderer::attributes( const IECore::CompoundObject *attributes )
{
	return new CompoundAttributesInterface( m_renderers, attributes );
}

Renderer::ObjectInterfacePtr CompoundRenderer::camera( const std::string &name, const IECoreScene::Camera *camera, const AttributesInterface *attributes )
{
	auto compoundAttributes = static_cast<const CompoundAttributesInterface *>( attributes );
	CompoundObjectInterfacePtr result = new CompoundObjectInterface;
	for( size_t i = 0; i < m_renderers.size(); ++i )
	{
		result->objects[i] = m_renderers[i]->camera( name, camera, compoundAttributes->attributes[i].get() );
	}
	return result;
}

Renderer::ObjectInterfacePtr CompoundRenderer::light( const std::string &name, const IECore::Object *object, const AttributesInterface *attributes )
{
	auto compoundAttributes = static_cast<const CompoundAttributesInterface *>( attributes );
	CompoundObjectInterfacePtr result = new CompoundObjectInterface;
	for( size_t i = 0; i < m_renderers.size(); ++i )
	{
		result->objects[i] = m_renderers[i]->light( name, object, compoundAttributes->attributes[i].get() );
	}
	return result;
}

Renderer::ObjectInterfacePtr CompoundRenderer::lightFilter( const std::string &name, const IECore::Object *object, const AttributesInterface *attributes )
{
	auto compoundAttributes = static_cast<const CompoundAttributesInterface *>( attributes );
	CompoundObjectInterfacePtr result = new CompoundObjectInterface;
	for( size_t i = 0; i < m_renderers.size(); ++i )
	{
		result->objects[i] = m_renderers[i]->lightFilter( name, object, compoundAttributes->attributes[i].get() );
	}
	return result;
}

Renderer::ObjectInterfacePtr CompoundRenderer::object( const std::string &name, const IECore::Object *object, const AttributesInterface *attributes )
{
	auto compoundAttributes = static_cast<const CompoundAttributesInterface *>( attributes );
	CompoundObjectInterfacePtr result = new CompoundObjectInterface;
	for( size_t i = 0; i < m_renderers.size(); ++i )
	{
		result->objects[i] = m_renderers[i]->object( name, object, compoundAttributes->attributes[i].get() );
	}
	return result;
}

Renderer::ObjectInterfacePtr CompoundRenderer::object( const std::string &name, const std::vector<const IECore::Object *> &samples, const std::vector<float> &times, const AttributesInterface *attributes )
{
	auto compoundAttributes = static_cast<const CompoundAttributesInterface *>( attributes );
	CompoundObjectInterfacePtr result = new CompoundObjectInterface;
	for( size_t i = 0; i < m_renderers.size(); ++i )
	{
		result->objects[i] = m_renderers[i]->object( name, samples, times, compoundAttributes->attributes[i].get() );
	}
	return result;
}

void CompoundRenderer::render()
{
	for( auto &r : m_renderers )
	{
		r->render();
	}
}

void CompoundRenderer::pause()
{
	for( auto &r : m_renderers )
	{
		r->pause();
	}
}

IECore::DataPtr CompoundRenderer::command( const IECore::InternedString name, const IECore::CompoundDataMap &parameters )
{
	for( auto &r : m_renderers )
	{
		if( IECore::DataPtr d = r->command( name, parameters ) )
		{
			// Return result from the first renderer to handle the
			// command. This works reasonably for now, where all
			// commands are renderer-specific and unlikely to be needed
			// by the next renderer.
			return d;
		}
	}
	return nullptr;
}
