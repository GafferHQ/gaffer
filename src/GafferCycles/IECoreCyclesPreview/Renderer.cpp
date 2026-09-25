//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2021, Alex Fuller. All rights reserved.
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
//      * Neither the name of Alex Fuller nor the names of
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

#include "GafferScene/Private/IECoreScenePreview/Renderer.h"

#include "GafferCycles/IECoreCyclesPreview/CameraAlgo.h"
#include "GafferCycles/IECoreCyclesPreview/GeometryAlgo.h"
#include "GafferCycles/IECoreCyclesPreview/IECoreCycles.h"
#include "GafferCycles/IECoreCyclesPreview/ShaderNetworkAlgo.h"
#include "GafferCycles/IECoreCyclesPreview/SocketAlgo.h"

#include "Attributes.h"
#include "IEDisplayOutputDriver.h"
#include "NodeDeleter.h"
#include "OIIOOutputDriver.h"
#include "PointInstancer.h"
#include "SceneAlgo.h"

#include "IECoreScene/Camera.h"
#include "IECoreScene/MeshPrimitive.h"
#include "IECoreScene/Shader.h"

#include "IECore/Interpolator.h"
#include "IECore/MessageHandler.h"
#include "IECore/ObjectVector.h"
#include "IECore/SearchPath.h"
#include "IECore/SimpleTypedData.h"
#include "IECore/StringAlgo.h"
#include "IECore/VectorTypedData.h"

#include "Imath/ImathMatrixAlgo.h"

#include "boost/algorithm/string.hpp"
#include "boost/algorithm/string/predicate.hpp"
#include "boost/container/flat_map.hpp"

#include "tbb/concurrent_unordered_map.h"
#include "tbb/concurrent_hash_map.h"
#include "tbb/concurrent_vector.h"

#include "fmt/format.h"

#include <filesystem>
#include <tuple>
#include <unordered_map>

// Cycles
IECORE_PUSH_DEFAULT_VISIBILITY
#include "bvh/params.h"
#include "device/device.h"
#include "graph/node.h"
#include "graph/node_type.h"
#include "kernel/types.h"
#include "scene/background.h"
#include "session/buffers.h"
#include "scene/curves.h"
#include "scene/film.h"
#include "scene/geometry.h"
#include "scene/shader_graph.h"
#include "scene/hair.h"
#include "scene/integrator.h"
#include "scene/light.h"
#include "scene/mesh.h"
#include "scene/shader_nodes.h"
#include "scene/object.h"
#include "scene/osl.h"
#include "scene/scene.h"
#include "session/session.h"
#include "scene/volume.h"
#include "subd/dice.h"
#include "util/array.h"
#include "util/log.h"
#include "util/murmurhash.h"
#include "util/path.h"
#include "util/time.h"
#include "util/types.h"
#include "util/vector.h"
#include "util/version.h"
IECORE_POP_DEFAULT_VISIBILITY

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace IECoreImage;
using namespace IECoreScene;
using namespace IECoreScenePreview;
using namespace IECoreCycles;

//////////////////////////////////////////////////////////////////////////
// Utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

template<typename T>
T *reportedCast( const IECore::RunTimeTyped *v, const char *type, const IECore::InternedString &name )
{
	T *t = IECore::runTimeCast<T>( v );
	if( t )
	{
		return t;
	}

	IECore::msg( IECore::Msg::Warning, "IECoreCycles::Renderer",
		fmt::format(
			"Expected {} but got {} for {} \"{}\".",
			T::staticTypeName(), v->typeName(), type, name.c_str()
		)
	);
	return nullptr;
}

template<typename T>
T parameter( const IECore::CompoundDataMap &parameters, const IECore::InternedString &name, const T &defaultValue )
{
	IECore::CompoundDataMap::const_iterator it = parameters.find( name );
	if( it == parameters.end() )
	{
		return defaultValue;
	}

	using DataType = IECore::TypedData<T>;
	if( const DataType *d = reportedCast<const DataType>( it->second.get(), "parameter", name ) )
	{
		return d->readable();
	}
	else
	{
		return defaultValue;
	}
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// CyclesOutput
//////////////////////////////////////////////////////////////////////////

namespace
{

void updateCryptomatteMetadata( IECore::CompoundData *metadata, std::string &name, ccl::Scene *scene = nullptr )
{
	std::string identifier = ccl::string_printf( "%08x", ccl::util_murmur_hash3( name.c_str(), name.length(), 0 ) );
	std::string prefix = "cryptomatte/" + identifier.substr( 0, 7 ) + "/";
	metadata->member<IECore::StringData>( prefix + "name", false, true )->writable() = name;
	metadata->member<IECore::StringData>( prefix + "hash", false, true )->writable() = "MurmurHash3_32";
	metadata->member<IECore::StringData>( prefix + "conversion", false, true )->writable() = "uint32_to_float32";

	if( scene )
	{
		if( name == "cryptomatte_object" )
			metadata->member<IECore::StringData>( prefix + "manifest", false, true )->writable() = scene->object_manager->get_cryptomatte_objects( scene );
		else if( name == "cryptomatte_material" )
			metadata->member<IECore::StringData>( prefix + "manifest", false, true )->writable() = scene->shader_manager->get_cryptomatte_materials( scene );
		else if( name == "cryptomatte_asset" )
			metadata->member<IECore::StringData>( prefix + "manifest", false, true )->writable() = scene->object_manager->get_cryptomatte_assets( scene );
	}
}

class CyclesOutput : public IECore::RefCounted
{

	public :

		CyclesOutput( const IECore::InternedString &name, const IECoreScene::Output *output )
			: m_passType( ccl::PASS_NONE ), m_denoise( false ), m_useIEDisplay( output->getType() == "ieDisplay" ), m_lightgroup( false )
		{
			m_parameters = output->parametersData()->copy();
			CompoundDataMap &p = m_parameters->writable();

			p["path"] = new StringData( output->getName() );

			m_denoise = parameter<bool>( output->parameters(), "denoise", false );

			const ccl::NodeEnum &typeEnum = *ccl::Pass::get_type_enum();
			ccl::ustring passType;

			vector<string> tokens;
			IECore::StringAlgo::tokenize( output->getData(), ' ', tokens );
			if( tokens.size() == 1 )
			{
				if( tokens[0] == "rgb" || tokens[0] == "rgba" )
				{
					p["name"] = m_denoise ? new StringData( ccl::string_printf( "%s_denoised", tokens[0].c_str() ) ) : new StringData( tokens[0] );
					p["type"] = new StringData( "combined" );
					passType = "combined";
				}
				else
				{
					p["name"] = m_denoise ? new StringData( ccl::string_printf( "%s_denoised", tokens[0].c_str() ) ) : new StringData( tokens[0] );
					p["type"] = new StringData( tokens[0] );
					passType = tokens[0];
				}
				m_data = tokens[0];
			}
			else if( tokens.size() == 2 )
			{
				if( tokens[0] == "float" && tokens[1] == "Z" )
				{
					m_data = tokens[1];
					p["name"] = new StringData( tokens[1] );
					p["type"] = new StringData( "depth" );
					passType = "depth";
				}
				else if( tokens[0] == "float" && tokens[1] == "id" )
				{
					m_data = tokens[1];
					p["name"] = new StringData( tokens[1] );
					p["type"] = new StringData( "object_id" );
					passType = "object_id";
				}
				else if( tokens[0] == "float" )
				{
					p["name"] = m_denoise ? new StringData( ccl::string_printf( "%s_denoised", tokens[1].c_str() ) ) : new StringData( tokens[1] );
					p["type"] = new StringData( "aov_value" );
					passType = "aov_value";
					m_data = tokens[1];
				}
				else if( tokens[0] == "color" )
				{
					p["name"] = m_denoise ? new StringData( ccl::string_printf( "%s_denoised", tokens[1].c_str() ) ) : new StringData( tokens[1] );
					p["type"] = new StringData( "aov_color" );
					passType = "aov_color";
					m_data = tokens[1];
				}
				else if( tokens[0] == "lg" )
				{
					p["name"] = m_denoise ? new StringData( ccl::string_printf( "%s_denoised", tokens[1].c_str() ) ) : new StringData( tokens[1] );
					p["type"] = new StringData( "lightgroup" );
					passType = "combined";
					m_data = tokens[1];
					m_lightgroup = true;
				}
				else if( tokens[0] == "cryptomatte" )
				{
					m_data = ccl::string_printf( "%s_%s", tokens[0].c_str(), tokens[1].c_str() );
					p["name"] = new StringData( m_data );
					p["type"] = new StringData( tokens[0] );
					passType = tokens[0];
				}
			}

			if( typeEnum.exists( passType ) )
			{
				m_passType = static_cast<ccl::PassType>( typeEnum[passType] );
			}
		}

		CompoundDataPtr m_parameters;
		ccl::PassType m_passType;
		std::string m_data;
		bool m_denoise;
		bool m_useIEDisplay;
		bool m_lightgroup;
};

IE_CORE_DECLAREPTR( CyclesOutput )

using OutputMap = std::map<IECore::InternedString, CyclesOutputPtr>;

} // namespace

//////////////////////////////////////////////////////////////////////////
// AttributesCache
//////////////////////////////////////////////////////////////////////////

namespace
{

class AttributesCache
{

	public :

		AttributesCache( ShaderCache *shaderCache )
			:	m_shaderCache( shaderCache )
		{
		}

		// Can be called concurrently with other get() calls.
		AttributesPtr get( const IECore::CompoundObject *attributes )
		{
			Cache::accessor a;
			m_cache.insert( a, attributes->Object::hash() );
			if( !a->second )
			{
				a->second = new Attributes( attributes, m_shaderCache );
			}
			return a->second;
		}

		// Must not be called concurrently with anything.
		void clearUnused()
		{
			vector<IECore::MurmurHash> toErase;
			for( Cache::iterator it = m_cache.begin(), eIt = m_cache.end(); it != eIt; ++it )
			{
				if( it->second->refCount() == 1 )
				{
					// Only one reference - this is ours, so
					// nothing outside of the cache is using the
					// attributes.
					toErase.push_back( it->first );
				}
			}
			for( vector<IECore::MurmurHash>::const_iterator it = toErase.begin(), eIt = toErase.end(); it != eIt; ++it )
			{
				m_cache.erase( *it );
			}

			m_shaderCache->clearUnused();
		}

	private :

		ShaderCache *m_shaderCache;

		using Cache = tbb::concurrent_hash_map<IECore::MurmurHash, AttributesPtr>;
		Cache m_cache;

};

} // namespace

//////////////////////////////////////////////////////////////////////////
// GeometryCache
//////////////////////////////////////////////////////////////////////////

namespace
{

using SharedGeometryPtr = std::shared_ptr<const ccl::Geometry>;

class GeometryCache
{

	public :

		GeometryCache( ccl::Scene *scene, NodeDeleter *nodeDeleter )
			: m_scene( scene ), m_nodeDeleter( nodeDeleter )
		{
		}

		// Can be called concurrently with other get() calls.
		SharedGeometryPtr get(
			const IECoreScenePreview::Renderer::ObjectSamples &samples,
			const IECoreScenePreview::Renderer::SampleTimes &times,
			const IECoreScenePreview::Renderer::AttributesInterface *attributes,
			const std::string &nodeName
		)
		{
			const Attributes *cyclesAttributes = static_cast<const Attributes *>( attributes );

			if( !cyclesAttributes->canInstanceGeometry( samples.front().get() ) )
			{
				return convert( samples, times, cyclesAttributes, nodeName );
			}

			IECore::MurmurHash h;
			for( const auto &sample : samples )
			{
				sample->hash( h );
			}
			h.append( times.data(), times.size() );
			cyclesAttributes->hashGeometry( samples.front().get(), h );
			cyclesAttributes->hashShader( h );

			Geometry::const_accessor readAccessor;
			if( m_geometry.find( readAccessor, h ) )
			{
				return readAccessor->second;
			}
			else
			{
				Geometry::accessor writeAccessor;
				if( m_geometry.insert( writeAccessor, h ) )
				{
					writeAccessor->second = convert( samples, times, cyclesAttributes, nodeName );
				}
				return writeAccessor->second;
			}
		}

		// Must not be called concurrently with anything.
		void clearUnused()
		{
			vector<IECore::MurmurHash> toErase;
			for( Geometry::iterator it = m_geometry.begin(), eIt = m_geometry.end(); it != eIt; ++it )
			{
				if( it->second.use_count() == 1 )
				{
					// Only one reference - this is ours, so
					// nothing outside of the cache is using the
					// node.
					toErase.push_back( it->first );
				}
			}
			for( vector<IECore::MurmurHash>::const_iterator it = toErase.begin(), eIt = toErase.end(); it != eIt; ++it )
			{
				m_geometry.erase( *it );
			}
		}

	private :

		SharedGeometryPtr convert(
			const IECoreScenePreview::Renderer::ObjectSamples &samples,
			const IECoreScenePreview::Renderer::SampleTimes &times,
			const Attributes *attributes,
			const std::string &nodeName
		)
		{
			std::shared_ptr<ccl::Geometry> geometry( GeometryAlgo::convert( samples, times, m_scene ), NodeDeleter::GeometryDeleter( m_nodeDeleter ) );
			if( geometry )
			{
				geometry->name = ccl::ustring( nodeName.c_str() );
				attributes->applyShader( geometry.get(), m_scene );
				attributes->applyGeometry( geometry.get(), m_scene );
			}

			if( auto vdb = IECore::runTimeCast<const IECoreVDB::VDBObject>( samples.front().get() ) )
			{
				assert( geometry->is_volume() );
				GeometryAlgo::convertVoxelGrids( vdb, static_cast<ccl::Volume*>( geometry.get() ), m_scene, attributes->getVolumePrecision(), attributes->getVolumeClipping() );
			}

			return geometry;
		}

		ccl::Scene *m_scene;
		NodeDeleter *m_nodeDeleter;
		using Geometry = tbb::concurrent_hash_map<IECore::MurmurHash, SharedGeometryPtr>;
		Geometry m_geometry;

};

} // namespace

//////////////////////////////////////////////////////////////////////////
// LightLinker definition
//////////////////////////////////////////////////////////////////////////

namespace
{

class LightLinker
{

	public :

		LightLinker( IECoreScenePreview::Renderer::RenderType renderType );

		enum class SetType
		{
			Light = 0,
			Shadow = 1
		};

		uint32_t registerLightSet( SetType setType, const IECoreScenePreview::Renderer::ConstObjectSetPtr &lights );
		void deregisterLightSet( SetType setType, const IECoreScenePreview::Renderer::ConstObjectSetPtr &lights );

	private :

		const IECoreScenePreview::Renderer::RenderType m_renderType;

		using WeakObjectSetPtr = std::weak_ptr<const IECoreScenePreview::Renderer::ObjectSet>;

		struct LightSet
		{
			size_t useCount = 0;
			uint32_t index;
		};

		struct LightSets
		{
			/// \todo Use `unordered_map` (or `concurrent_unordered_map`) when `std::owner_hash()`
			/// becomes available (in C++26).
			using Map = std::map<WeakObjectSetPtr, LightSet, std::owner_less<WeakObjectSetPtr>>;
			Map map;
			uint64_t usedIndices = 1;
		};

		std::mutex m_mutex;
		LightSets m_lightSets;
		LightSets m_shadowSets;

};

} // namespace

//////////////////////////////////////////////////////////////////////////
// CyclesObject
//////////////////////////////////////////////////////////////////////////

namespace
{

const IECore::InternedString g_lights( "lights" );
const IECore::InternedString g_shadowedLights( "shadowedLights" );

class CyclesObject : public IECoreScenePreview::Renderer::ObjectInterface
{

	public :

		CyclesObject( ccl::Scene *scene, const SharedGeometryPtr &geometry, const std::string &name, LightLinker *lightLinker, NodeDeleter *nodeDeleter )
			:	m_scene( scene ),
				m_object( SceneAlgo::createNodeWithLock<ccl::Object>( scene ), NodeDeleter::ObjectDeleter( nodeDeleter ) ),
				m_geometry( geometry ), m_attributes( nullptr ), m_lightLinker( lightLinker )
		{
			assert( m_geometry );
			m_object->name = ccl::ustring( name.c_str() );
			m_object->set_random_id( std::hash<string>()( name ) );
			{
				// We're not accessing the scene here, but we use the lock to
				// protect against concurrent calls with the same `geometry` on
				// other objects, because `set_geometry()` manipulates the
				// reference count on `geometry` in a non-threadsafe way.
				/// \todo Would the Cycles project accept a patch to make the
				/// reference count atomic?
				std::scoped_lock sceneLock( scene->mutex );
				m_object->set_geometry( const_cast<ccl::Geometry *>( geometry.get() ) );
			}
		}

		~CyclesObject() override
		{
			if( m_linkedLights )
			{
				m_lightLinker->deregisterLightSet( LightLinker::SetType::Light, m_linkedLights );
			}
			if( m_shadowedLights )
			{
				m_lightLinker->deregisterLightSet( LightLinker::SetType::Shadow, m_shadowedLights );
			}
		}

		void link( const IECore::InternedString &type, const IECoreScenePreview::Renderer::ConstObjectSetPtr &objects ) override
		{
			IECoreScenePreview::Renderer::ConstObjectSetPtr *setMemberData;
			LightLinker::SetType setType;
			if( type == g_lights )
			{
				setMemberData = &m_linkedLights;
				setType = LightLinker::SetType::Light;
			}
			else if( type == g_shadowedLights )
			{
				setMemberData = &m_shadowedLights;
				setType = LightLinker::SetType::Shadow;
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

			uint32_t lightSet = 0;
			if( *setMemberData )
			{
				lightSet = m_lightLinker->registerLightSet( setType, *setMemberData );
			}

			if( setType == LightLinker::SetType::Light )
			{
				m_object->set_receiver_light_set( lightSet );
			}
			else
			{
				m_object->set_blocker_shadow_set( lightSet );
			}

			SceneAlgo::tagUpdateWithLock( m_object.get(), m_scene );
		}

		void transform( const IECoreScenePreview::Renderer::TransformSamples &samples, const IECoreScenePreview::Renderer::SampleTimes &times ) override
		{
			const size_t primarySampleIndex = (samples.size() - 1) / 2;
			m_object->set_tfm( SocketAlgo::setTransform( samples[primarySampleIndex] ) );

			ccl::array<ccl::Transform> motion;
			if( samples.size() > 1 )
			{
				motion.resize( samples.size() );
				for( size_t i = 0; i < samples.size(); ++i )
				{
					motion[i] = SocketAlgo::setTransform( samples[i] );
				}
			}
			m_object->set_motion( motion );

			if( m_geometry->is_mesh() )
			{
				auto constMesh = static_cast<const ccl::Mesh *>( m_geometry.get() );
				if( constMesh->get_subdivision_type() != ccl::Mesh::SUBDIVISION_NONE )
				{
					if( constMesh->get_subd_adaptive_space() == ccl::Mesh::SUBDIVISION_ADAPTIVE_SPACE_PIXEL )
					{
						// View-dependent subdivs aren't auto-instanced, so we
						// should be the only one managing `subd_objecttoworld`,
						// making it safe to mutate.
						assert( m_geometry.use_count() == 1 );
						auto mesh = const_cast<ccl::Mesh *>( constMesh );
						mesh->set_subd_objecttoworld( m_object->get_tfm() );
						SceneAlgo::tagUpdateWithLock( mesh, m_scene, /* rebuild = */ true );
					}
					else
					{
						// Non-view-dependent subdivs don't use `subd_objecttoworld`,
						// so we don't need to set it.
					}
				}
			}

			SceneAlgo::tagUpdateWithLock( m_object.get(), m_scene );
		}

		bool attributes( const IECoreScenePreview::Renderer::AttributesInterface *attributes ) override
		{
			const Attributes *cyclesAttributes = static_cast<const Attributes *>( attributes );

			if( m_attributes )
			{
				IECore::MurmurHash currentGeometryHash, newGeometryHash;
				m_attributes->hashGeometry( m_geometry.get(), currentGeometryHash );
				cyclesAttributes->hashGeometry( m_geometry.get(), newGeometryHash );
				if( newGeometryHash != currentGeometryHash )
				{
					// Our geometry might be shared with other instances that
					// don't want the new attributes, so we're not at liberty
					// to make the edit.
					return false;
				}
			}

			cyclesAttributes->applyObject( m_object.get(), m_scene );
			// We only have const access to `m_geometry`, because we may be sharing
			// it with other CyclesObjects. By casting and clobbering the shader, we
			// risk changing the shading on other objects. But currently we prefer that
			// to the alternative of failing the edit and issuing all-new geometry.
			// Ideally Cycles would assign shaders to `ccl::Object` instead.
			cyclesAttributes->applyShader( const_cast<ccl::Geometry *>( m_geometry.get() ), m_scene );
			m_attributes = cyclesAttributes;

			return true;
		}

		void assignID( uint32_t id ) override
		{
			m_object->set_pass_id( id );
		}

		void assignInstanceID( uint32_t id ) override
		{
			// Instance IDs not needed in Cycles, because encapsulated instancers aren't supported.
		}

	private :

		ccl::Scene *m_scene;
		using UniqueObjectPtr = std::unique_ptr<ccl::Object, NodeDeleter::ObjectDeleter>;
		UniqueObjectPtr m_object;
		SharedGeometryPtr m_geometry;
		ConstAttributesPtr m_attributes;
		LightLinker *m_lightLinker;
		IECoreScenePreview::Renderer::ConstObjectSetPtr m_linkedLights;
		IECoreScenePreview::Renderer::ConstObjectSetPtr m_shadowedLights;

};

} // namespace

//////////////////////////////////////////////////////////////////////////
// CyclesLight
//////////////////////////////////////////////////////////////////////////

namespace
{

class CyclesLight : public IECoreScenePreview::Renderer::ObjectInterface
{

	public :

		CyclesLight( ccl::Scene *scene, const std::string &name, NodeDeleter *nodeDeleter )
			:	m_scene( scene ), m_light( SceneAlgo::createNodeWithLock<ccl::Light>( scene ), NodeDeleter::GeometryDeleter( nodeDeleter ) ), m_object( SceneAlgo::createNodeWithLock<ccl::Object>( scene ), NodeDeleter::ObjectDeleter( nodeDeleter ) )
		{
			m_object->set_geometry( m_light.get() );
			m_object->set_random_id( std::hash<string>()( name ) );
			m_object->name = ccl::ustring( name );
			m_light->name = ccl::ustring( name );
			// All lights are always in the first set, which we use for objects
			// which don't have any linking applied. But we only add lights to
			// other sets as they are created by the LightLinker in response to
			// calls to `CyclesObject::link()`.
			m_object->set_light_set_membership( 1 );
			m_object->set_shadow_set_membership( 1 );
		}

		~CyclesLight() override
		{
		}

		void link( const IECore::InternedString &type, const IECoreScenePreview::Renderer::ConstObjectSetPtr &objects ) override
		{
		}

		void transform( const IECoreScenePreview::Renderer::TransformSamples &samples, const IECoreScenePreview::Renderer::SampleTimes &times ) override
		{
			// Set environment map rotation
			/// \todo There are a few problems here :
			///
			/// - We're clobbering the `tex_mapping.rotation` parameter, which is exposed to users
			///   but now has no effect for them. This also prevents us getting the orientation of USD
			///   DomeLights correct - see ShaderNetworkAlgo.
			/// - The light shader was created via `ShaderCache::get()`, and could therefore be shared
			///   between several lights, so we're not at liberty to clobber the shader anyway.
			if( m_light->get_light_type() == ccl::LIGHT_BACKGROUND && m_light->get_used_shaders().size() != 0 )
			{
				ccl::Shader *shader = (ccl::Shader*)m_light->get_used_shaders()[0];
				for( ccl::ShaderNode *node : shader->graph->nodes )
				{
					if( node->type == ccl::EnvironmentTextureNode::get_node_type() )
					{
						ccl::EnvironmentTextureNode *env = (ccl::EnvironmentTextureNode *)node;
						Imath::Eulerf euler( samples[0], Imath::Eulerf::Order::XZY );
						env->tex_mapping.rotation = ccl::make_float3( -euler.x, -euler.y, -euler.z );
						shader->tag_update( m_scene );
						break;
					}
				}
			}

			m_object->set_tfm( SocketAlgo::setTransform( samples[0] ) );
			SceneAlgo::tagUpdateWithLock( m_object.get(), m_scene );
		}

		bool attributes( const IECoreScenePreview::Renderer::AttributesInterface *attributes ) override
		{
			const Attributes *cyclesAttributes = static_cast<const Attributes *>( attributes );
			cyclesAttributes->applyLight( m_light.get(), m_scene );
			cyclesAttributes->applyObject( m_object.get(), m_scene );
			m_attributes = cyclesAttributes;
			return true;
		}

		void assignID( uint32_t id ) override
		{
			/// \todo Implement me
		}

		void assignInstanceID( uint32_t instanceID ) override
		{
		}

		// Used by LightLinker
		// ===================

		uint64_t getLightSetMembership( LightLinker::SetType setType ) const
		{
			return setType == LightLinker::SetType::Light ? m_object->get_light_set_membership() : m_object->get_shadow_set_membership();
		}

		void setLightSetMembership( LightLinker::SetType setType, uint64_t membership )
		{
			if( setType == LightLinker::SetType::Light )
			{
				m_object->set_light_set_membership( membership );
			}
			else
			{
				m_object->set_shadow_set_membership( membership );
			}

			SceneAlgo::tagUpdateWithLock( m_object.get(), m_scene );
		}

	private :

		ccl::Scene *m_scene;
		using UniqueLightPtr = std::unique_ptr<ccl::Light, NodeDeleter::GeometryDeleter>;
		UniqueLightPtr m_light;
		using UniqueObjectPtr = std::unique_ptr<ccl::Object, NodeDeleter::ObjectDeleter>;
		UniqueObjectPtr m_object;
		ConstAttributesPtr m_attributes;

};

IE_CORE_DECLAREPTR( CyclesLight )

} // namespace


//////////////////////////////////////////////////////////////////////////
// LightLinker definition
//////////////////////////////////////////////////////////////////////////

namespace
{

uint64_t indexToMask( int index )
{
	return uint64_t( 1 ) << index;
}

LightLinker::LightLinker( IECoreScenePreview::Renderer::RenderType renderType )
	:	m_renderType( renderType )
{
}

uint32_t LightLinker::registerLightSet( SetType setType, const IECoreScenePreview::Renderer::ConstObjectSetPtr &lights )
{
	std::lock_guard lock( m_mutex );
	LightSets &lightSets = setType == SetType::Light ? m_lightSets : m_shadowSets;

	LightSet &lightSet = lightSets.map[lights];
	lightSet.useCount++;
	if( lightSet.useCount == 1 )
	{
		// First usage of this set. Find an unused index.
		for( int i = 1; i < LIGHT_LINK_SET_MAX; ++i )
		{
			if( ( lightSets.usedIndices & indexToMask( i ) ) == 0 )
			{
				lightSet.index = i;
				lightSets.usedIndices = lightSets.usedIndices | indexToMask( i );
				break;
			}
		}

		if( lightSet.index != 0 )
		{
			// Assign membership to lights. Note that we rely on `lock` here to
			// prevent concurrent modification to the lights from multiple calls
			// to `registerLightSet()`.
			for( const auto &object : *lights )
			{
				auto light = static_cast<CyclesLight *>( object.get() );
				light->setLightSetMembership(
					setType,
					light->getLightSetMembership( setType ) | indexToMask( lightSet.index )
				);
			}
		}
		else
		{
			// We ran out of indices.
			IECore::msg(
				IECore::Msg::Level::Warning, "CyclesRenderer",
				fmt::format(
					"{} linking failed because the maximum number of unique light groups ({}) was exceeded.",
					setType == SetType::Light ? "Light" : "Shadow",
					LIGHT_LINK_SET_MAX
				)
			);
		}
	}
	return lightSet.index;
}

void LightLinker::deregisterLightSet( SetType setType, const IECoreScenePreview::Renderer::ConstObjectSetPtr &lights )
{
	if( m_renderType != IECoreScenePreview::Renderer::RenderType::Interactive )
	{
		// `~CyclesObject` always deregisters links, but in a batch render
		// that doesn't mean they are no longer wanted.
		return;
	}

	std::lock_guard lock( m_mutex );
	LightSets &lightSets = setType == SetType::Light ? m_lightSets : m_shadowSets;

	auto it = lightSets.map.find( lights );
	assert( it != lightSets.map.end() );
	assert( it->second.useCount );
	it->second.useCount--;
	if( it->second.useCount )
	{
		return;
	}

	// Set no longer in use.

	lightSets.usedIndices = lightSets.usedIndices & ~indexToMask( it->second.index );
	for( const auto &object : *lights )
	{
		auto light = static_cast<CyclesLight *>( object.get() );
		light->setLightSetMembership(
			setType,
			light->getLightSetMembership( setType ) & ~indexToMask( it->second.index )
		);
	}

	lightSets.map.erase( it );
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// CyclesCamera
//////////////////////////////////////////////////////////////////////////

namespace
{

class CyclesCamera : public IECoreScenePreview::Renderer::ObjectInterface
{

	public :

		IE_CORE_DECLAREMEMBERPTR( CyclesCamera );

		CyclesCamera( const IECoreScene::ConstCameraPtr &camera )
			:	m_camera( camera )
		{
			transform( { M44f() }, { 0.0f } );
		}

		~CyclesCamera() override
		{
		}

		void link( const IECore::InternedString &type, const IECoreScenePreview::Renderer::ConstObjectSetPtr &objects ) override
		{
		}

		void transform( const IECoreScenePreview::Renderer::TransformSamples &samples, const IECoreScenePreview::Renderer::SampleTimes &times ) override
		{
			m_transformSamples.resize( samples.size() );
			for( size_t i = 0; i < samples.size(); ++i )
			{
				/// \todo Should we really be scaling in Y? It seems we're doing
				/// it to counteract the flipping of the top/bottom view planes
				/// in CameraAlgo, so perhaps we can stop doing that?
				M44f m = samples[i];
				m.scale( Imath::V3f( 1, -1, -1 ) );
				m_transformSamples[i] = SocketAlgo::setTransform( m );
			}
		}

		bool attributes( const IECoreScenePreview::Renderer::AttributesInterface *attributes ) override
		{
			// Attributes don't affect the camera, so the edit always "succeeds".
			return true;
		}

		void assignID( uint32_t id ) override
		{
		}

		void assignInstanceID( uint32_t instanceID ) override
		{
		}

		void apply( ccl::Camera *destination ) const
		{
			CameraAlgo::convert( m_camera.get(), destination );

			const size_t primarySampleIndex = (m_transformSamples.size() - 1) / 2;
			destination->set_matrix( m_transformSamples[primarySampleIndex] );

			ccl::array<ccl::Transform> motion;
			if( m_transformSamples.size() > 1 )
			{
				motion.resize( m_transformSamples.size() );
				for( size_t i = 0; i < m_transformSamples.size(); ++i )
				{
					motion[i] = m_transformSamples[i];
				}
			}
			destination->set_motion( motion );
		}

	private :

		IECoreScene::ConstCameraPtr m_camera;
		ccl::array<ccl::Transform> m_transformSamples;

};

IE_CORE_DECLAREPTR( CyclesCamera )

} // namespace

//////////////////////////////////////////////////////////////////////////
// CyclesRenderer
//////////////////////////////////////////////////////////////////////////

namespace
{

std::array<IECore::InternedString, 2> g_bvhLayoutEnumNames = { {
	"embree",
	"bvh2"
} };

ccl::BVHLayout nameToBvhLayoutEnum( const IECore::InternedString &name )
{
#define MAP_NAME(enumName, enum) if(name == enumName) return enum;
	MAP_NAME(g_bvhLayoutEnumNames[0], ccl::BVHLayout::BVH_LAYOUT_EMBREE);
	MAP_NAME(g_bvhLayoutEnumNames[1], ccl::BVHLayout::BVH_LAYOUT_BVH2);
#undef MAP_NAME

	return ccl::BVHLayout::BVH_LAYOUT_AUTO;
}

std::array<IECore::InternedString, 3> g_curveShapeTypeEnumNames = { {
	"ribbon",
	"thick",
	"thick-linear"
} };

ccl::CurveShapeType nameToCurveShapeTypeEnum( const IECore::InternedString &name )
{
#define MAP_NAME(enumName, enum) if(name == enumName) return enum;
	MAP_NAME(g_curveShapeTypeEnumNames[0], ccl::CurveShapeType::CURVE_RIBBON);
	MAP_NAME(g_curveShapeTypeEnumNames[1], ccl::CurveShapeType::CURVE_THICK);
	MAP_NAME(g_curveShapeTypeEnumNames[2], ccl::CurveShapeType::CURVE_THICK_LINEAR);
#undef MAP_NAME

	return ccl::CurveShapeType::CURVE_THICK;
}

ccl::DeviceInfo firstCPUDevice()
{
	for( const auto &device : ccl::Device::available_devices() )
	{
		if( device.type == ccl::DEVICE_CPU )
		{
			return device;
		}
	}
	assert( false );
	return ccl::DeviceInfo();
}

ccl::DeviceInfo matchingDevices( const std::string &pattern, int threads, bool background, ccl::DenoiserType denoiser = ccl::DenoiserType::DENOISER_NONE )
{
	ccl::vector<ccl::DeviceInfo> devices;
	std::unordered_map<ccl::DeviceType, int> typeIndices;
	for( const auto &device : ccl::Device::available_devices() )
	{
		const string typeString = ccl::Device::string_from_type( device.type );
		const int typeIndex = typeIndices[device.type]++;
		const string name = fmt::format( "{}:{:02}", typeString, typeIndex );
		if(
			// e.g. "CPU" matches the first CPU device.
			( typeIndex == 0 && StringAlgo::matchMultiple( typeString, pattern ) ) ||
			// e.g. "CUDA:*" matches all CUDA devices, or `OPTIX:00` matches the first Optix device.
			StringAlgo::matchMultiple( name, pattern )
		)
		{
			// If a denoiser is specified, only match devices that support it.
			if( denoiser != ccl::DenoiserType::DENOISER_NONE && !( device.denoisers & denoiser ) )
			{
				continue;
			}
			devices.push_back( device );
		}
	}

	if( devices.empty() )
	{
		if( denoiser != ccl::DenoiserType::DENOISER_NONE )
		{
			IECore::msg( IECore::Msg::Warning, "CyclesRenderer", fmt::format( "No compatible {} denoise device matching \"{}\" found, reverting to CPU denoising if available.", ccl::denoiserTypeToHumanReadable( denoiser ), pattern ) );
		}
		else
		{
			IECore::msg( IECore::Msg::Warning, "CyclesRenderer", fmt::format( "No devices matching \"{}\" found, reverting to CPU.", pattern ) );
		}
		devices.push_back( firstCPUDevice() );
	}

	// Note : if there's only one device, `get_multi_device()` just
	// returns it directly, rather than wrapping it.
	return ccl::Device::get_multi_device( devices, threads, background );
}

IECore::CompoundDataPtr sessionParamsAsData( const ccl::SessionParams params )
{
	IECore::CompoundDataPtr result = new IECore::CompoundData;
	result->writable()["device"] = new StringData( params.device.id );
	result->writable()["headless"] = new BoolData( params.headless );
	result->writable()["background"] = new BoolData( params.background );
	result->writable()["samples"] = new BoolData( params.samples );
	result->writable()["threads"] = new IntData( params.threads );
	return result;
}

ccl::SessionParams defaultSessionParams( IECoreScenePreview::Renderer::RenderType renderType )
{
	ccl::SessionParams params;
	params.device = firstCPUDevice();
	params.shadingsystem = ccl::SHADINGSYSTEM_OSL;
	params.use_resolution_divider = false;

	if( renderType == IECoreScenePreview::Renderer::RenderType::Interactive )
	{
		params.headless = false;
		params.background = false;
		params.use_auto_tile = false;
	}
	else
	{
		params.headless = true;
		params.background = true;
		params.temp_dir = std::filesystem::temp_directory_path().string();
	}

	return params;
}

ccl::SceneParams defaultSceneParams( IECoreScenePreview::Renderer::RenderType renderType )
{
	ccl::SceneParams params;
	params.shadingsystem = ccl::SHADINGSYSTEM_OSL;
	params.bvh_layout = ccl::BVH_LAYOUT_AUTO;

	if( renderType == IECoreScenePreview::Renderer::RenderType::Interactive )
	{
		params.bvh_type = ccl::BVH_TYPE_DYNAMIC;
	}
	else
	{
		params.bvh_type = ccl::BVH_TYPE_STATIC;
	}

	return params;
}

// Shading-Systems
IECore::InternedString g_shadingsystemOSL( "OSL" );
IECore::InternedString g_shadingsystemSVM( "SVM" );

ccl::ShadingSystem nameToShadingSystemEnum( const IECore::InternedString &name )
{
#define MAP_NAME(enumName, enum) if(name == enumName) return enum;
	MAP_NAME(g_shadingsystemOSL, ccl::ShadingSystem::SHADINGSYSTEM_OSL);
	MAP_NAME(g_shadingsystemSVM, ccl::ShadingSystem::SHADINGSYSTEM_SVM);
#undef MAP_NAME

	return ccl::ShadingSystem::SHADINGSYSTEM_SVM;
}

// Denoisers
IECore::InternedString g_denoiseOptix( "optix" );
IECore::InternedString g_denoiseOpenImageDenoise( "openimagedenoise" );

ccl::DenoiserType nameToDenoiseTypeEnum( const IECore::InternedString &name )
{
#define MAP_NAME(enumName, enum) if(name == enumName) return enum;
	if( IECoreCycles::optixDenoiseSupported() )
	{
		MAP_NAME(g_denoiseOptix, ccl::DenoiserType::DENOISER_OPTIX);
	}
	if( IECoreCycles::openImageDenoiseSupported() )
	{
		MAP_NAME(g_denoiseOpenImageDenoise, ccl::DenoiserType::DENOISER_OPENIMAGEDENOISE);
	}
#undef MAP_NAME

	return ccl::DenoiserType::DENOISER_NONE;
}

// Core
IECore::InternedString g_frameOptionName( "frame" );
IECore::InternedString g_cameraOptionName( "camera" );
IECore::InternedString g_sampleMotionOptionName( "sampleMotion" );
IECore::InternedString g_deviceOptionName( "cycles:device" );
IECore::InternedString g_denoiseDeviceOptionName( "cycles:denoise_device" );
IECore::InternedString g_shadingsystemOptionName( "cycles:shadingsystem" );
IECore::InternedString g_squareSamplesOptionName( "cycles:square_samples" );
// Logging
IECore::InternedString g_logLevelOptionName( "cycles:log_level" );
IECore::InternedString g_progressLevelOptionName( "cycles:progress_level" );
// Session
IECore::InternedString g_samplesOptionName( "cycles:session:samples" );
IECore::InternedString g_pixelSizeOptionName( "cycles:session:pixel_size" );
IECore::InternedString g_threadsOptionName( "cycles:session:threads" );
IECore::InternedString g_timeLimitOptionName( "cycles:session:time_limit" );
IECore::InternedString g_useProfilingOptionName( "cycles:session:use_profiling" );
IECore::InternedString g_useAutoTileOptionName( "cycles:session:use_auto_tile" );
IECore::InternedString g_tileSizeOptionName( "cycles:session:tile_size" );
// Scene
IECore::InternedString g_bvhTypeOptionName( "cycles:scene:bvh_type" );
IECore::InternedString g_bvhLayoutOptionName( "cycles:scene:bvh_layout" );
IECore::InternedString g_useBvhSpatialSplitOptionName( "cycles:scene:use_bvh_spatial_split" );
IECore::InternedString g_useBvhUnalignedNodesOptionName( "cycles:scene:use_bvh_unaligned_nodes" );
IECore::InternedString g_numBvhTimeStepsOptionName( "cycles:scene:num_bvh_time_steps" );
IECore::InternedString g_hairSubdivisionsOptionName( "cycles:scene:hair_subdivisions" );
IECore::InternedString g_hairShapeOptionName( "cycles:scene:hair_shape" );
IECore::InternedString g_textureLimitOptionName( "cycles:scene:texture_limit" );
// Background shader
IECore::InternedString g_backgroundShaderOptionName( "cycles:background:shader" );
// Integrator
IECore::InternedString g_seedOptionName( "cycles:integrator:seed" );
IECore::InternedString g_denoiserTypeOptionName( "cycles:integrator:denoiser_type" );

const boost::container::flat_map<std::string, ccl::PathRayFlag> g_rayTypes = {
	{ "camera", ccl::PATH_RAY_CAMERA },
	{ "diffuse", ccl::PATH_RAY_DIFFUSE },
	{ "glossy", ccl::PATH_RAY_GLOSSY },
	{ "transmission", ccl::PATH_RAY_TRANSMIT },
	{ "shadow", ccl::PATH_RAY_SHADOW },
	{ "scatter", ccl::PATH_RAY_VOLUME_SCATTER }
};

const boost::container::flat_map<int, ccl::LogLevel> g_logLevels = {
	{ 0, ccl::LOG_LEVEL_ERROR },
	{ 1, ccl::LOG_LEVEL_WARNING },
	{ 2, ccl::LOG_LEVEL_INFO }
};

// Dicing camera
IECore::InternedString g_dicingCameraOptionName( "cycles:dicing_camera" );

// Cryptomatte
IECore::InternedString g_cryptomatteDepthOptionName( "cycles:film:cryptomatte_depth");

IE_CORE_FORWARDDECLARE( CyclesRenderer )

class CyclesRenderer final : public IECoreScenePreview::Renderer
{

	public :

		CyclesRenderer( RenderType renderType, const std::string &fileName, const IECore::MessageHandlerPtr &messageHandler )
			:	m_optionsChanged( true ),
				m_scene( nullptr ),
				m_bufferParams( ccl::BufferParams() ),
				m_renderType( renderType ),
				m_rendering( false ),
				m_outputsChanged( true ),
				m_messageHandler( messageHandler ),
				m_lightLinker( renderType )

		{
			m_cameras["ieCoreCycles:defaultCamera"] =  new CyclesCamera( new IECoreScene::Camera() );
		}

		~CyclesRenderer() override
		{
			// Cancel session before destruction of anything else. `~Session` actually
			// calls `cancel()` internally, but the session can emit progress updates
			// on other threads during cancellation, and our `progress()` method accesses
			// member data that needs to be intact when that happens.
			if( m_session )
			{
				m_session->cancel();
			}
		}

		IECore::InternedString name() const override
		{
			return "Cycles";
		}

		void option( const IECore::InternedString &name, const IECore::Object *value ) override
		{
			// Store for use in `acquireSession()` and `updateOptions()`.
			Option &option = m_options[name];
			if( option.value && value )
			{
				option.modified = value->isNotEqualTo( option.value.get() );
			}
			else
			{
				option.modified = (bool)value != (bool)option.value;
			}
			option.value = value;
			m_optionsChanged = m_optionsChanged || option.modified;
		}

		void output( const IECore::InternedString &name, const Output *output ) override
		{
			const IECore::MessageHandler::Scope s( m_messageHandler.get() );

			if( !output )
			{
				// Remove output pass
				const auto coutput = m_outputs.find( name );
				if( coutput != m_outputs.end() )
				{
					m_outputs.erase( name );
					m_outputsChanged = true;
				}
			}
			else
			{
				const auto coutput = m_outputs.find( name );
				if( coutput == m_outputs.end() )
				{
					m_outputs[name] = new CyclesOutput( name, output );
					m_outputsChanged = true;
				}
			}
		}

		Renderer::AttributesInterfacePtr attributes( const IECore::CompoundObject *attributes ) override
		{
			const IECore::MessageHandler::Scope s( m_messageHandler.get() );
			acquireSession();
			return m_attributesCache->get( attributes );
		}

		ObjectInterfacePtr camera( const std::string &name, const CameraSamples &samples, const SampleTimes &times, const AttributesInterface *attributes ) override
		{
			const IECore::MessageHandler::Scope s( m_messageHandler.get() );
			// No need to acquire session because we don't need it to make a camera.
			// This is important for certain clients (SceneGadget and RenderController)
			// because they make a camera before calling `option()` to set the device.
			CyclesCameraPtr result = new CyclesCamera( samples[0] );
			m_cameras[name] = result;
			if( attributes )
			{
				result->attributes( attributes );
			}
			return result;
		}

		ObjectInterfacePtr light( const std::string &name, const ObjectSamples &samples, const SampleTimes &times, const AttributesInterface *attributes ) override
		{
			const IECore::MessageHandler::Scope s( m_messageHandler.get() );
			acquireSession();

			ObjectInterfacePtr result = new CyclesLight( m_scene, name, m_nodeDeleter.get() );
			result->attributes( attributes );
			return result;
		}

		ObjectInterfacePtr lightFilter( const std::string &name, const ObjectSamples &samples, const SampleTimes &times, const AttributesInterface *attributes ) override
		{
			const IECore::MessageHandler::Scope s( m_messageHandler.get() );
			acquireSession();

			IECore::msg( IECore::Msg::Warning, "CyclesRenderer", "lightFilter() unimplemented" );
			return nullptr;
		}

		ObjectInterfacePtr object( const std::string &name, const ObjectSamples &samples, const SampleTimes &times, const AttributesInterface *attributes ) override
		{
			const IECore::MessageHandler::Scope s( m_messageHandler.get() );
			acquireSession();

			/// \todo Is it actually useful to pass `name` here? It will only be meaningful for the first
			/// CyclesObject that references it, and will be inaccurate for any additional instances.
			SharedGeometryPtr geometry = m_geometryCache->get( samples, times, attributes, name );
			if( !geometry )
			{
				return nullptr;
			}

			ObjectInterfacePtr result = new CyclesObject( m_scene, geometry, name, &m_lightLinker, m_nodeDeleter.get() );
			result->attributes( attributes );
			return result;
		}

		ObjectInterfacePtr pointInstancer( const std::string &name, const PointInstancerSamples &samples, const SampleTimes &times, const std::vector<Prototype> &prototypes, const AttributesInterface *attributes ) override
		{
			const IECore::MessageHandler::Scope s( m_messageHandler.get() );
			acquireSession();

			vector<SharedGeometryPtr> prototypeGeometry;
			prototypeGeometry.reserve( prototypes.size() );
			for( size_t i = 0; i < prototypes.size(); ++i )
			{
				prototypeGeometry.push_back( m_geometryCache->get( prototypes[i].samples, prototypes[i].times, prototypes[i].attributes.get(), fmt::format( "{}_prototype{}", name, i ) ) );
			}

			return new IECoreCycles::PointInstancer( m_scene, m_nodeDeleter.get(), samples, prototypeGeometry );
		}

		void render() override
		{
			const IECore::MessageHandler::Scope s( m_messageHandler.get() );
			acquireSession();

			if( m_rendering && m_renderType == Interactive )
			{
				clearUnused();
			}

			if( m_nodeDeleter )
			{
				m_nodeDeleter->doPendingDeletions();
			}

			updateOptions();
			updateBackground();

			{
				std::lock_guard sceneLock( m_scene->mutex );
				const std::string cameraName = optionValue<string>( g_cameraOptionName, "" );
				updateCamera( cameraName, m_scene->camera );
				updateCamera( optionValue<string>( g_dicingCameraOptionName, cameraName ), m_scene->dicing_camera );
			}

			updateOutputs();
			warnForUnusedOptions();

			if( m_rendering )
			{
				std::lock_guard sceneLock( m_scene->mutex );
				if( m_scene->need_reset() )
				{
					m_session->reset( m_session->params, m_bufferParams );
				}
			}

			if( m_rendering )
			{
				m_session->set_pause( false );
				return;
			}

			m_session->start();

			m_rendering = true;

			if( m_renderType == Interactive )
			{
				return;
			}

			// Free up caches, Cycles now owns the data.
			resetCaches();
			m_session->wait();
			m_rendering = false;
		}

		void pause() override
		{
			const IECore::MessageHandler::Scope s( m_messageHandler.get() );
			if( m_rendering )
			{
				m_session->set_pause( true );
			}
		}

		IECore::DataPtr command( const IECore::InternedString name, const IECore::CompoundDataMap &parameters ) override
		{
			if( name == "cycles:queryIntegrator" )
			{
				acquireSession();
				updateOptions();
				return SocketAlgo::getSockets( m_scene->integrator );
			}
			else if( name == "cycles:queryFilm" )
			{
				acquireSession();
				updateOptions();
				return SocketAlgo::getSockets( m_scene->film );
			}
			else if( name == "cycles:querySession" )
			{
				acquireSession();
				updateOptions();
				return sessionParamsAsData( m_session->params );
			}
			else if( boost::starts_with( name.string(), "cycles:" ) || name.string().find( ":" ) == string::npos )
			{
				IECore::msg( IECore::Msg::Warning, "CyclesRenderer::command", fmt::format( "Unknown command \"{}\"", name.c_str() ) );
			}

			return nullptr;
		}

	private :

		int frame() const
		{
			return optionValue<int>( g_frameOptionName, 1 );
		}

		// Returns the value of an option, falling back to the default provided.
		// If the value was modified since the previous call, sets `*modified = true`.
		template<typename T>
		T optionValue( const IECore::InternedString &name, const T &defaultValue, bool *modified = nullptr ) const
		{
			auto it = m_options.find( name );
			if( it == m_options.end() )
			{
				return defaultValue;
			}
			if( it->second.modified )
			{
				if( modified )
				{
					*modified = true;
				}
				it->second.modified = false;
			}

			if( !it->second.value )
			{
				return defaultValue;
			}
			using DataType = IECore::TypedData<T>;
			const DataType *data = reportedCast<const DataType>( it->second.value.get(), "option", name );
			return data ? data->readable() : defaultValue;
		}

		ccl::SessionParams sessionParamsFromOptions( bool *modified = nullptr )
		{
			ccl::SessionParams params = defaultSessionParams( m_renderType );

			params.samples = optionValue<int>( g_samplesOptionName, params.samples, modified );
			params.pixel_size = optionValue<int>( g_pixelSizeOptionName, params.pixel_size, modified );
			params.time_limit = optionValue<float>( g_timeLimitOptionName, params.time_limit, modified );
			params.use_profiling = optionValue<bool>( g_useProfilingOptionName, params.use_profiling, modified );
			params.use_auto_tile = optionValue<bool>( g_useAutoTileOptionName, params.use_auto_tile, modified );
			params.tile_size = optionValue<int>( g_tileSizeOptionName, params.tile_size, modified );
			params.shadingsystem = nameToShadingSystemEnum( optionValue<string>( g_shadingsystemOptionName, "OSL", modified ) );
			const int threads = optionValue<int>( g_threadsOptionName, 0, modified );
			params.threads = threads > 0 ? threads : std::max( (int)std::thread::hardware_concurrency() + threads, 1 );
			// Device depends on threads, so do that last.
			params.device = matchingDevices( optionValue<string>( g_deviceOptionName, "CPU", modified ), params.threads, params.background );
			// Denoise device depends on the chosen denoiser.
			const ccl::DenoiserType denoiser = nameToDenoiseTypeEnum( optionValue<string>( g_denoiserTypeOptionName, "openimagedenoise", modified ) );
			params.denoise_device = matchingDevices( optionValue<string>( g_denoiseDeviceOptionName, "*", modified ), params.threads, params.background, denoiser );

			return params;
		}

		ccl::SceneParams sceneParamsFromOptions( bool *modified = nullptr )
		{
			ccl::SceneParams params = defaultSceneParams( m_renderType );
			params.bvh_layout = nameToBvhLayoutEnum( optionValue<string>( g_bvhLayoutOptionName, "auto", modified ) );
			params.hair_shape = nameToCurveShapeTypeEnum( optionValue<string>( g_hairShapeOptionName, "ribbon", modified ) );
			params.use_bvh_spatial_split = optionValue<bool>( g_useBvhSpatialSplitOptionName, params.use_bvh_spatial_split, modified );
			params.use_bvh_unaligned_nodes = optionValue<bool>( g_useBvhUnalignedNodesOptionName, params.use_bvh_unaligned_nodes, modified );
			params.num_bvh_time_steps = optionValue<int>( g_numBvhTimeStepsOptionName, params.num_bvh_time_steps, modified );
			params.hair_subdivisions = optionValue<int>( g_hairSubdivisionsOptionName, params.hair_subdivisions, modified );
			params.texture_limit = optionValue<int>( g_textureLimitOptionName, params.texture_limit, modified );
			params.shadingsystem = nameToShadingSystemEnum( optionValue<string>( g_shadingsystemOptionName, "OSL", modified ) );
			return params;
		}

		void acquireSession()
		{
			// Lock is needed because `acquireSession()` can be called from multiple
			// threads. `spin_mutex` is appropriate because after initialisation we
			// are only doing a single check on `m_session`, and we want to return as
			// fast as possible.
			tbb::spin_mutex::scoped_lock lock( m_sessionAcquireMutex );
			if( m_session )
			{
				return;
			}

			ccl::SessionParams sessionParams = sessionParamsFromOptions();
			ccl::SceneParams sceneParams = sceneParamsFromOptions();

			if( sessionParams.shadingsystem == ccl::SHADINGSYSTEM_OSL && !sessionParams.device.has_osl )
			{
				IECore::msg( IECore::Msg::Warning, "CyclesRenderer", "Device doesn't support OSL, reverting to CPU." );
				sessionParams.device = firstCPUDevice();
			}

			m_session = std::make_unique<ccl::Session>( sessionParams, sceneParams );
			m_session->progress.set_update_callback( std::bind( &CyclesRenderer::progress, this ) );
			m_scene = m_session->scene.get();

			/// \todo Determine why this is here, or remove it.
			m_scene->camera->need_flags_update = true;
			m_scene->camera->update( m_scene );

			m_scene->background->set_transparent( true );

			if( m_renderType == RenderType::Interactive )
			{
				m_nodeDeleter = std::make_unique<NodeDeleter>( m_scene );
			}

			m_shaderCache = std::make_unique<ShaderCache>( m_scene );
			m_geometryCache = std::make_unique<GeometryCache>( m_scene, m_nodeDeleter.get() );
			m_attributesCache = std::make_unique<AttributesCache>( m_shaderCache.get() );
		}

		void clearUnused()
		{
			m_geometryCache->clearUnused();
			m_attributesCache->clearUnused();
		}

		void updateOptions()
		{
			if( !m_optionsChanged )
			{
				return;
			}

			std::unique_lock sceneLock( m_scene->mutex );

			// Options that map directly to sockets.

			for( auto &[name, option] : m_options )
			{
				if( boost::starts_with( name.string(), "cycles:film:" ) )
				{
					SocketAlgo::setSocket(
						m_scene->film, name.string().c_str() + 12,
						option.value ? reportedCast<const Data>( option.value.get(), "option", name ) : nullptr
					);
					option.modified = false;
				}
				else if( boost::starts_with( name.string(), "cycles:integrator:" ) )
				{
					SocketAlgo::setSocket(
						m_scene->integrator, name.string().c_str() + 18,
						option.value ? reportedCast<const Data>( option.value.get(), "option", name ) : nullptr
					);
					option.modified = false;
				}
				else if(
					boost::starts_with( name.string(), "cycles:background:" ) &&
					!boost::starts_with( name.string(), "cycles:background:visibility:" ) &&
					name.string() != "cycles:background:shader"
				)
				{
					SocketAlgo::setSocket(
						m_scene->background, name.string().c_str() + 18,
						option.value ? reportedCast<const Data>( option.value.get(), "option", name ) : nullptr
					);
					option.modified = false;
				}
			}

			// Integrator

			ccl::Integrator *integrator = m_scene->integrator;
			integrator->set_seed( optionValue<int>( g_seedOptionName, frame() ) );
			integrator->set_motion_blur( optionValue<bool>( g_sampleMotionOptionName, true ) );
			integrator->set_sampling_pattern( m_session->params.background ? ccl::SAMPLING_PATTERN_BLUE_NOISE_PURE : ccl::SAMPLING_PATTERN_BLUE_NOISE_FIRST );

			if( integrator->is_modified() )
			{
				integrator->tag_update( m_scene, ccl::Integrator::UPDATE_ALL );
			}

			// Background. Here we just deal with _options_ that affect
			// the background. Lights that affect the background are dealt
			// with in `updateBackground()`, which is where the final
			// modification check and `tag_update()` is done.

			ccl::Background *background = m_scene->background;

			auto it = m_options.find( g_backgroundShaderOptionName );
			if( it != m_options.end() && it->second.modified )
			{
				m_backgroundShader = nullptr;
				if( it->second.value )
				{
					if( const IECoreScene::ShaderNetwork *d = reportedCast<const IECoreScene::ShaderNetwork>( it->second.value.get(), "option", g_backgroundShaderOptionName ) )
					{
						// Need to release scene mutex temporarily, so that
						// `ShaderCache::get()` can acquire it.
						sceneLock.unlock();
						m_backgroundShader = m_shaderCache->get( d );
						sceneLock.lock();
					}
				}

				if( m_backgroundShader )
				{
					m_backgroundShader->shader()->tag_used( m_scene );
					background->set_shader( m_backgroundShader->shader() );
				}

				it->second.modified = false;
			}

			uint32_t backgroundVisibility = ccl::PATH_RAY_ALL_VISIBILITY;
			for( const auto &[name, rayType] : g_rayTypes )
			{
				if( !optionValue<bool>( "cycles:background:visibility:" + name, true ) )
				{
					backgroundVisibility = backgroundVisibility & ~rayType;
				}
			}
			background->set_visibility( backgroundVisibility );

			// Session and scene

			bool optionsModified = false;
			const ccl::SessionParams sessionParams = sessionParamsFromOptions( &optionsModified );
			const ccl::SceneParams sceneParams = sceneParamsFromOptions( &optionsModified);
			if( optionsModified && ( sessionParams.modified( m_session->params ) || sceneParams.modified( m_session->scene->params ) ) )
			{
				// Here `modified()` actually means "modified in a way that can't be changed
				// after constructing the session".
				IECore::msg( IECore::Msg::Warning, "CyclesRenderer::option", "Option edit requires a manual render restart" );
			}
			m_session->set_samples( sessionParams.samples );

			// Misc

			ccl::log_level_set( g_logLevels.at( optionValue<int>( g_logLevelOptionName, 0 ) ) );
			optionValue<int>( g_cryptomatteDepthOptionName, 0, &m_outputsChanged );

			m_optionsChanged = false;
		}

		void warnForUnusedOptions()
		{
			for( auto &[name, option] : m_options )
			{
				if( option.modified )
				{
					if( name.string().find( ':' ) == string::npos || boost::starts_with( name.string(), "user:" ) || boost::starts_with( name.string(), "cycles:" ) )
					{
						IECore::msg( IECore::Msg::Warning, "CyclesRenderer::option", fmt::format( "Unknown option \"{}\".", name.string() ) );
					}
					option.modified = false;
				}
			}
		}

		void updateBackground()
		{
			// Note : `updateOptions()` must be called prior to
			// `updateBackground()` so that `m_backgroundShader` is up to date.
			// This function is separate because background lights can be
			// modified without setting `m_optionsChanged`.

			std::lock_guard sceneLock( m_scene->mutex );

			if( !m_backgroundShader )
			{
				/// \todo Figure out how we can avoid repeating this check for
				/// every render. This might be much easier if attribute edits
				/// were performed by a renderer method instead of an ObjectInterface
				/// method. Or can we use `scene->light_manager->need_update()`?
				ccl::Shader *backgroundShader = nullptr;
				ccl::ustring lightgroup( "" );
				/// \todo Avoid iterating over `m_scene->objects` to find the background light.
				for( auto object : m_scene->objects )
				{
					if( !object->get_geometry()->is_light() )
					{
						continue;
					}
					auto light = static_cast<ccl::Light *>( object->get_geometry() );
					if( light->get_light_type() == ccl::LIGHT_BACKGROUND && light->get_used_shaders().size() != 0 )
					{
						backgroundShader = (ccl::Shader*)light->get_used_shaders()[0];
						lightgroup = object->get_lightgroup();
						break;
					}
				}
				m_scene->background->set_shader( backgroundShader ? backgroundShader : m_scene->default_background );
				m_scene->background->set_lightgroup( lightgroup );
			}

			// Note : this is also responsible for tagging any changes
			// made in `updateOptions()`.
			if( m_scene->background->is_modified() )
			{
				m_scene->background->tag_update( m_scene );
			}
		}

		void updateOutputs()
		{
			std::lock_guard sceneLock( m_scene->mutex );

			ccl::Camera *camera = m_scene->camera;
			int width = camera->get_full_width();
			int height = camera->get_full_height();

			ccl::BufferParams updatedBufferParams = m_bufferParams;
			updatedBufferParams.full_width = width;
			updatedBufferParams.full_height = height;
			updatedBufferParams.full_x = (int)(camera->get_border_left() * (float)width);
			updatedBufferParams.full_y = (int)(camera->get_border_bottom() * (float)height);
			updatedBufferParams.width =  (int)(camera->get_border_right() * (float)width) - updatedBufferParams.full_x;
			updatedBufferParams.height = (int)(camera->get_border_top() * (float)height) - updatedBufferParams.full_y;
			updatedBufferParams.window_width = updatedBufferParams.width;
			updatedBufferParams.window_height = updatedBufferParams.height;

			if( m_bufferParams.modified( updatedBufferParams ) )
			{
				// Set `m_outputsChanged` so we call `m_session->reset()` below
				// with the new buffer params, and so we update the display driver
				// with the new resolution.
				m_outputsChanged = true;
				m_bufferParams = updatedBufferParams;
			}

			if( !m_outputsChanged )
				return;

			Box2i displayWindow(
				V2i( 0, 0 ),
				V2i( width - 1, height - 1 )
			);
			Box2i dataWindow(
				V2i(
					(int)(camera->get_border_left()   * (float)width ),
					(int)(camera->get_border_bottom() * (float)height )
				),
				V2i(
					(int)(camera->get_border_right()  * (float)width ) - 1,
					(int)(camera->get_border_top()    * (float)height - 1 )
				)
			);

			ccl::set<ccl::Pass *> passesToDelete;
			for( const auto &p : m_scene->passes )
			{
				passesToDelete.insert( p );
			}
			m_scene->delete_nodes( passesToDelete );

			ccl::CryptomatteType crypto = ccl::CRYPT_NONE;

			CompoundDataPtr layersData = new CompoundData();
			InternedString cryptoAsset;
			InternedString cryptoObject;
			InternedString cryptoMaterial;
			bool hasShadowCatcher = false;
			bool hasDenoise = false;
			const bool useIEDisplay = std::any_of(
				m_outputs.begin(), m_outputs.end(),
				[] ( const auto &output ) { return output.second->m_useIEDisplay; }
			);
			for( auto &coutput : m_outputs )
			{
				if( coutput.second->m_useIEDisplay != useIEDisplay )
				{
					/// \todo Support a mix of IEDisplay and file outputs. To do
					/// this we'd make a single `ccl::OutputDriver` subclass
					/// that could cope with both types.
					IECore::msg(
						IECore::Msg::Warning, "CyclesRenderer",
						fmt::format(
							"Ignoring output \"{}\" because it is not compatible with ieDisplay-based outputs",
							coutput.first.string()
						)
					);
					continue;
				}

				ccl::PassType passType = coutput.second->m_passType;

				// We need to add all lightgroup passes in-order
				if( coutput.second->m_lightgroup )
					continue;

				if( passType == ccl::PASS_CRYPTOMATTE )
				{
					if( coutput.second->m_data == "cryptomatte_asset" )
					{
						crypto = static_cast<ccl::CryptomatteType>( crypto | ccl::CRYPT_ASSET );
						cryptoAsset = coutput.first;
					}
					else if( coutput.second->m_data == "cryptomatte_object" )
					{
						crypto = static_cast<ccl::CryptomatteType>( crypto | ccl::CRYPT_OBJECT );
						cryptoObject = coutput.first;
					}
					else if( coutput.second->m_data == "cryptomatte_material" )
					{
						crypto = static_cast<ccl::CryptomatteType>( crypto | ccl::CRYPT_MATERIAL );
						cryptoMaterial = coutput.first;
					}
					continue;
				}

				if( passType == ccl::PASS_SHADOW_CATCHER )
				{
					hasShadowCatcher = true;
				}

				bool denoise = coutput.second->m_denoise;
				hasDenoise |= denoise;
				std::string name = denoise ? ccl::string_printf( "%s_denoised", coutput.second->m_data.c_str() ) : coutput.second->m_data;
				ccl::Pass *pass = m_scene->create_node<ccl::Pass>();
				pass->set_type( passType );
				pass->set_name( ccl::ustring( name ) );
				pass->set_mode( denoise ? ccl::PassMode::DENOISED : ccl::PassMode::NOISY );

				const IECore::CompoundDataPtr layer = coutput.second->m_parameters->copy();
				layersData->writable()[name] = layer;
			}

			// Adding cryptomattes in-order matters

			ccl::Film *film = m_scene->film;
			if( crypto == ccl::CRYPT_NONE )
			{
				// If there's no crypto, we must set depth to 0 otherwise bugs appear
				film->set_cryptomatte_depth( 0 );
			}
			else
			{
				const int cryptomatteDepth = optionValue( g_cryptomatteDepthOptionName, 0 );
				film->set_cryptomatte_depth(
					// At least have 1 depth if there are crypto passes
					cryptomatteDepth ? ccl::divide_up( std::min( 16, cryptomatteDepth ), 2 ) : 1
				);
			}

			int depth = film->get_cryptomatte_depth();
			if( crypto & ccl::CRYPT_OBJECT )
			{
				std::string name( "cryptomatte_object" );
				IECore::CompoundDataPtr layer = m_outputs[cryptoObject]->m_parameters->copy();
				updateCryptomatteMetadata( layer.get(), name, m_scene );
				for( int i = 0; i < depth; ++i )
				{
					ccl::Pass *pass = m_scene->create_node<ccl::Pass>();
					pass->set_type( ccl::PASS_CRYPTOMATTE );
					pass->set_name( ccl::ustring( ccl::string_printf( "%s%02d", name.c_str(), i ) ) );
					pass->set_mode( ccl::PassMode::NOISY );
					layersData->writable()[pass->get_name().c_str()] = layer;
				}
			}
			if( crypto & ccl::CRYPT_MATERIAL )
			{
				std::string name( "cryptomatte_material" );
				IECore::CompoundDataPtr layer = m_outputs[cryptoMaterial]->m_parameters->copy();
				updateCryptomatteMetadata( layer.get(), name, m_scene );
				for( int i = 0; i < depth; ++i )
				{
					ccl::Pass *pass = m_scene->create_node<ccl::Pass>();
					pass->set_type( ccl::PASS_CRYPTOMATTE );
					pass->set_name( ccl::ustring( ccl::string_printf( "%s%02d", name.c_str(), i ) ) );
					pass->set_mode( ccl::PassMode::NOISY );
					layersData->writable()[pass->get_name().c_str()] = layer;
				}
			}
			if( crypto & ccl::CRYPT_ASSET )
			{
				std::string name( "cryptomatte_asset" );
				IECore::CompoundDataPtr layer = m_outputs[cryptoAsset]->m_parameters->copy();
				updateCryptomatteMetadata( layer.get(), name, m_scene );
				for( int i = 0; i < depth; ++i )
				{
					ccl::Pass *pass = m_scene->create_node<ccl::Pass>();
					pass->set_type( ccl::PASS_CRYPTOMATTE );
					pass->set_name( ccl::ustring( ccl::string_printf( "%s%02d", name.c_str(), i ) ) );
					pass->set_mode( ccl::PassMode::NOISY );
					layersData->writable()[pass->get_name().c_str()] = layer;
				}
			}

			// Add lightgroups on the end
			for( auto &coutput : m_outputs )
			{
				if( coutput.second->m_useIEDisplay != useIEDisplay )
				{
					IECore::msg(
						IECore::Msg::Warning, "CyclesRenderer",
						fmt::format(
							"Ignoring output \"{}\" because it is not compatible with ieDisplay-based outputs",
							coutput.first.string()
						)
					);
					continue;
				}

				ccl::PassType passType = coutput.second->m_passType;

				if( !coutput.second->m_lightgroup )
					continue;

				bool denoise = coutput.second->m_denoise;
				hasDenoise |= denoise;
				std::string name = denoise ? ccl::string_printf( "%s_denoised", coutput.second->m_data.c_str() ) : coutput.second->m_data;
				ccl::Pass *pass = m_scene->create_node<ccl::Pass>();
				pass->set_type( passType );
				pass->set_name( ccl::ustring( name ) );
				pass->set_mode( denoise ? ccl::PassMode::DENOISED : ccl::PassMode::NOISY );
				pass->set_lightgroup( ccl::ustring( coutput.second->m_data ) );

				const IECore::CompoundDataPtr layer = coutput.second->m_parameters->copy();
				layersData->writable()[name] = layer;
			}

			// When we reset the session, it cancels the internal PathTrace and
			// waits for it to finish. We need to do this _before_ calling
			// `set_output_driver()`, because otherwise the rendering threads
			// may try to send data to an output driver that was just destroyed
			// on the main thread.
			/// \todo `Renderer::pause()` really shouldn't return until after
			/// the PathTrace has been cancelled, so we shouldn't need to worry
			/// about that here.
			m_session->reset( m_session->params, m_bufferParams );

			film->set_cryptomatte_passes( crypto );
			film->set_use_approximate_shadow_catcher( !hasShadowCatcher );
			m_scene->integrator->set_use_denoise( hasDenoise );

			if( useIEDisplay )
			{
				m_session->set_output_driver( ccl::make_unique<IEDisplayOutputDriver>( displayWindow, dataWindow, layersData->readable() ) );
			}
			else
			{
				m_session->set_output_driver( ccl::make_unique<OIIOOutputDriver>( displayWindow, dataWindow, layersData->readable() ) );
				// In auto-tiled renders Cycles writes tiles to a temporary EXR in
				// `SessionParams.temp_dir` and invokes this callback once all
				// tiles are complete. The host is then responsible for telling the
				// session to process the buffer and send the completed frame to
				// the output driver via `Session::process_full_buffer_from_disk()`.
				m_session->full_buffer_written_cb = [session = m_session.get()]( ccl::string_view fileName ) {
					session->process_full_buffer_from_disk( fileName );
					// Clean up the temporary EXR as it is not removed by Cycles after processing.
					std::filesystem::remove( std::filesystem::path( fileName.str() ) );
				};
			}

			m_outputsChanged = false;
		}

		void updateCamera( const std::string &sourceName, ccl::Camera *destination )
		{
			auto cameraIt = m_cameras.find( sourceName );
			if( cameraIt == m_cameras.end() )
			{
				if( !sourceName.empty() )
				{
					IECore::msg(
						IECore::Msg::Warning, "CyclesRenderer",
						fmt::format( "Camera \"{}\" does not exist", sourceName )
					);
				}
				cameraIt = m_cameras.find( "ieCoreCycles:defaultCamera" );
			}

			cameraIt->second->apply( destination );
		}

		void progress()
		{
			const IECore::MessageHandler::Scope s( m_messageHandler.get() );

			string status, subStatus, memStatus;
			double totalTime, renderTime;
			float memUsed = (float)m_session->stats.mem_used / 1024.0f / 1024.0f / 1024.0f;
			float memPeak = (float)m_session->stats.mem_peak / 1024.0f / 1024.0f / 1024.0f;

			m_session->progress.get_status( status, subStatus );
			m_session->progress.get_time( totalTime, renderTime );

			if( subStatus != "" )
				status += ": " + subStatus;

			memStatus = ccl::string_printf( "Mem:%.3fG, Peak:%.3fG", (double)memUsed, (double)memPeak );

			double currentTime = ccl::time_dt();
			if( status != m_lastStatus )// || ( m_renderType == Interactive && ( currentTime - m_lastStatusTime ) > 1.0 ) )
			{
				IECore::msg( IECore::MessageHandler::Level::Info, "Cycles", memStatus + " | " + status );
				m_lastStatus = status;
				m_lastStatusTime = currentTime;
			}

			if( m_session->progress.get_error() )
			{
				string error = m_session->progress.get_error_message();
				if (error != m_lastError)
				{
					IECore::msg( IECore::MessageHandler::Level::Error, "Cycles", error );
					m_lastError = error;
				}
			}

			// Not sure what the best way is to inform that an interactive render has stopped other than this.
			// No way that I know of to inform Gaffer that the render has stopped either.
			if( m_lastStatus == "Finished" )
			{
				m_rendering = false;
			}
		}

		void resetCaches()
		{
			m_geometryCache.reset();
			m_shaderCache.reset();
			m_attributesCache.reset();
		}

		// Most `ccl::SessionParams` and `ccl::SceneParams` cannot be modified
		// after construction of the `ccl::Session`. And we are given those params
		// via `option()` after we ourselves have been constructed. So we can't create
		// the session in our constructor. Furthermore, _other_ options pertain to
		// properties of the `ccl::Scene`, and we can't have a scene without constructing a
		// session. Likewise, we can't implement `object()` until we have a scene.
		//
		// We deal with this as follows :
		//
		// 1. Implement `option()` to buffer everything into `m_options`. This is
		//    our "source of truth" for what the options should be.
		// 2. At the first point we _need_ a session (typically in a call to `object()`),
		//    we use `acquireSession()` to construct the session using the SessionParams
		//    defined by the options to date.
		// 3. In `updateOptions()` we apply all other options to their associated Cycles
		//    objects, just prior to rendering.
		// 4. In subsequent `render()` calls, transfer any further option edits to Cycles,
		//    warning if we encounter an edit that can't be applied to the SessionParams.
		//
		// This relies on clients to send all initial options before creating an object,
		// which fortunately is the case.
		struct Option { IECore::ConstObjectPtr value = nullptr; mutable bool modified = false; };
		std::unordered_map<IECore::InternedString, Option> m_options;
		bool m_optionsChanged;

		// Session.
		tbb::spin_mutex m_sessionAcquireMutex;
		std::unique_ptr<ccl::Session> m_session;
		ccl::Scene *m_scene;
		ccl::BufferParams m_bufferParams;
		std::unique_ptr<NodeDeleter> m_nodeDeleter;

		// Background shader
		IECoreCycles::ShaderPtr m_backgroundShader;

		// IECoreScene::Renderer
		RenderType m_renderType;
		bool m_rendering;
		bool m_outputsChanged;

		// Logging
		IECore::MessageHandlerPtr m_messageHandler;
		string m_lastError;
		string m_lastStatus;
		double m_lastStatusTime;

		// Caches
		std::unique_ptr<ShaderCache> m_shaderCache;
		std::unique_ptr<GeometryCache> m_geometryCache;
		std::unique_ptr<AttributesCache> m_attributesCache;
		LightLinker m_lightLinker;

		// Outputs
		OutputMap m_outputs;

		// Cameras. We store these in Cortex form, and apply them to the scene's
		// camera in `updateCamera()`.
		using CameraMap = tbb::concurrent_unordered_map<std::string, ConstCyclesCameraPtr>;
		CameraMap m_cameras;

		// Registration with factory
		static Renderer::TypeDescription<CyclesRenderer> g_typeDescription;

};

IECoreScenePreview::Renderer::TypeDescription<CyclesRenderer> CyclesRenderer::g_typeDescription( "Cycles" );

} // namespace
