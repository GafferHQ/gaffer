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
#include "boost/container/flat_map.hpp"
#include "boost/container/static_vector.hpp"

#include <mutex>
#include <array>

using namespace std;
using namespace IECoreScenePreview;

//////////////////////////////////////////////////////////////////////////
// ObjectSets class declaration
//////////////////////////////////////////////////////////////////////////

namespace
{

// Manages the decomposition of ObjectSets of CompoundObjectInterfaces into
// regular ObjectSets of ObjectInterfaces for each renderer.
struct ObjectSets
{

	using WeakObjectSetPtr = std::weak_ptr<const IECoreScenePreview::Renderer::ObjectSet>;

	// Array of ObjectSets, one per renderer.
	using ObjectSetArray = std::array<IECoreScenePreview::Renderer::ConstObjectSetPtr, 2>;

	ObjectSetArray registerObjectSet( const IECoreScenePreview::Renderer::ConstObjectSetPtr &objectSet );
	void deregisterObjectSet( const WeakObjectSetPtr &objectSet );

	// Everyone can share the same static instance, because lifetimes
	// of the internal data are governed entirely by ObjectInterface
	// lifetimes (via `deregisterObjectSet()`). This avoids the Renderer
	// needing to own an instance and passing the pointer to every single
	// CompoundObjectInterface.
	static ObjectSets &instance();

	private :

		struct ObjectSetData
		{
			size_t useCount = 0;
			ObjectSetArray objectSetArray;
		};

		/// \todo Use `unordered_map` (or `concurrent_unordered_map`) when `std::owner_hash()`
		/// becomes available (in C++26).
		using ObjectSetDataMap = std::map<WeakObjectSetPtr, ObjectSetData, std::owner_less<WeakObjectSetPtr>>;
		std::mutex m_mutex;
		ObjectSetDataMap m_objectSetData;

};

} // namespace

//////////////////////////////////////////////////////////////////////////
// Internal object types
//////////////////////////////////////////////////////////////////////////

namespace
{

struct CompoundAttributesInterface : public IECoreScenePreview::Renderer::AttributesInterface
{

	CompoundAttributesInterface( const CompoundRenderer::Renderers &renderers, const IECore::CompoundObject *a )
	{
		for( size_t i = 0; i < renderers.size(); ++i )
		{
			attributes[i] = renderers[i]->attributes( a );
		}
	}

	/// Using `std::array` of fixed length since we currently only need two
	/// renderers, and it minimises the size of internal data structures. We
	/// check the number of renderers matches in the CompoundRenderer
	/// constructor.
	std::array<Renderer::AttributesInterfacePtr, 2> attributes;

};

struct CompoundObjectInterface : public IECoreScenePreview::Renderer::ObjectInterface
{

	~CompoundObjectInterface()
	{
		if( m_links.empty() )
		{
			return;
		}

		ObjectSets &objectSets = ObjectSets::instance();
		for( const auto &[type, s] : m_links )
		{
			if( s )
			{
				objectSets.deregisterObjectSet( s );
			}
		}
	}

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

	void link( const IECore::InternedString &type, const IECoreScenePreview::Renderer::ConstObjectSetPtr &objectSet ) override
	{
		Renderer::ConstObjectSetPtr &current = m_links[type];
		if( current == objectSet )
		{
			return;
		}

		ObjectSets &objectSets = ObjectSets::instance();
		if( current )
		{
			objectSets.deregisterObjectSet( current );
		}

		current = objectSet;

		ObjectSets::ObjectSetArray array;
		if( current )
		{
			array = objectSets.registerObjectSet( objectSet );
		}

		for( size_t i = 0; i < objects.size(); ++i )
		{
			if( objects[i] )
			{
				objects[i]->link( type, array[i] );
			}
		}
	}

	void assignID( uint32_t id ) override
	{
		for( auto &o : objects )
		{
			if( o )
			{
				o->assignID( id );
			}
		}
	}

	/// See comment for CompoundAttributesInterface::attributes.
	std::array<IECoreScenePreview::Renderer::ObjectInterfacePtr, 2> objects;

	private :

		// We don't anticipate more than a couple of link types per object, so use
		// a sorted static vector to store links without the overhead of allocations.
		using LinkMap = boost::container::flat_map<
			IECore::InternedString, Renderer::ConstObjectSetPtr, std::less<IECore::InternedString>,
			boost::container::static_vector<std::pair<IECore::InternedString, Renderer::ConstObjectSetPtr>, 3>
		>;

		LinkMap m_links;

};

IE_CORE_DECLAREPTR( CompoundObjectInterface )

} // namespace

//////////////////////////////////////////////////////////////////////////
// ObjectSets implementation
//////////////////////////////////////////////////////////////////////////

namespace
{

ObjectSets::ObjectSetArray ObjectSets::registerObjectSet( const Renderer::ConstObjectSetPtr &objectSet )
{
	std::lock_guard guard( m_mutex );
	ObjectSetData &data = m_objectSetData[objectSet];
	data.useCount++;
	if( data.useCount == 1 )
	{
		// First usage of this set. Initialise an array of sets for each
		// renderer.
		std::array<Renderer::ObjectSetPtr, 2> mutableSets;
		for( auto &o : mutableSets )
		{
			o = std::make_shared<Renderer::ObjectSet>();
		}

		for( const auto &object : *objectSet )
		{
			auto compoundObject = static_cast<const CompoundObjectInterface *>( object.get() );
			for( size_t i = 0; i < compoundObject->objects.size(); ++i )
			{
				if( compoundObject->objects[i] )
				{
					mutableSets[i]->insert( compoundObject->objects[i] );
				}
			}

		}
		// Transfer into immutable sets for storage.
		std::copy( mutableSets.begin(), mutableSets.end(), data.objectSetArray.begin() );
	}

	return data.objectSetArray;
}

void ObjectSets::deregisterObjectSet( const ObjectSets::WeakObjectSetPtr &objectSet )
{
	std::lock_guard guard( m_mutex );
	auto it = m_objectSetData.find( objectSet );
	assert( it != m_objectSetData.end() );
	assert( it->second.useCount );
	it->second.useCount--;
	if( !it->second.useCount )
	{
		m_objectSetData.erase( it );
	}
}

ObjectSets &ObjectSets::instance()
{
	static ObjectSets g_instance;
	return g_instance;
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// Renderer implementation
//////////////////////////////////////////////////////////////////////////

CompoundRenderer::CompoundRenderer( const Renderers &renderers )
	:	m_renderers( renderers )
{
	if( m_renderers.size() != 2 )
	{
		throw IECore::Exception( "Expected 2 renderers" );
	}
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
		result->objects[i] = m_renderers[i]->camera( name, camera, compoundAttributes ? compoundAttributes->attributes[i].get() : nullptr );
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
