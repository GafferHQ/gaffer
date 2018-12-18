//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2018, Alex Fuller, John Haddon. All rights reserved.
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

#include "GafferScene/Private/IECoreScenePreview/Renderer.h"

#include "GafferCycles/IECoreCyclesPreview/AttributeAlgo.h"
#include "GafferCycles/IECoreCyclesPreview/CameraAlgo.h"
#include "GafferCycles/IECoreCyclesPreview/CurvesAlgo.h"
#include "GafferCycles/IECoreCyclesPreview/MeshAlgo.h"
#include "GafferCycles/IECoreCyclesPreview/ObjectAlgo.h"
#include "GafferCycles/IECoreCyclesPreview/SocketAlgo.h"

#include "IECoreScene/Camera.h"
#include "IECoreScene/CurvesPrimitive.h"
#include "IECoreScene/MeshPrimitive.h"
#include "IECoreScene/Shader.h"
#include "IECoreScene/SpherePrimitive.h"
#include "IECoreScene/Transform.h"

#include "IECore/LRUCache.h"
#include "IECore/MessageHandler.h"
#include "IECore/ObjectVector.h"
#include "IECore/SearchPath.h"
#include "IECore/SimpleTypedData.h"
#include "IECore/StringAlgo.h"
#include "IECore/VectorTypedData.h"

#include "boost/algorithm/string.hpp"
#include "boost/algorithm/string/predicate.hpp"

#include "tbb/concurrent_hash_map.h"

#include <unordered_map>

// Cycles
#include "device/device.h"
#include "graph/node.h"
#include "graph/node_type.h"
#include "render/buffers.h"
#include "render/osl.h"
#include "render/scene.h"
#include "render/session.h"
#include "util/util_function.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace IECoreCycles;

//////////////////////////////////////////////////////////////////////////
// Utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

typedef std::unique_ptr<ccl::Camera*> CCameraPtr;
typedef std::shared_ptr<ccl::Object*> SharedCObjectPtr;
typedef std::shared_ptr<ccl::Light*> SharedCLightPtr;
typedef std::shared_ptr<ccl::Mesh*> SharedCMeshPtr;
typedef std::shared_ptr<ccl::Shader*> SharedCShaderPtr;

template<typename T>
T *reportedCast( const IECore::RunTimeTyped *v, const char *type, const IECore::InternedString &name )
{
	T *t = IECore::runTimeCast<T>( v );
	if( t )
	{
		return t;
	}

	IECore::msg( IECore::Msg::Warning, "IECoreCycles::Renderer", boost::format( "Expected %s but got %s for %s \"%s\"." ) % T::staticTypeName() % v->typeName() % type % name.c_str() );
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

	typedef IECore::TypedData<T> DataType;
	if( const DataType *d = reportedCast<const DataType>( it->second.get(), "parameter", name ) )
	{
		return d->readable();
	}
	else
	{
		return defaultValue;
	}
}

template<typename T>
inline const T *dataCast( const char *name, const IECore::Data *data )
{
	const T *result = runTimeCast<const T>( data );
	if( result )
	{
		return result;
	}
	msg( Msg::Warning, "setParameter", boost::format( "Unsupported value type \"%s\" for parameter \"%s\" (expected %s)." ) % data->typeName() % name % T::staticTypeName() );
	return nullptr;
}

std::string shaderCacheGetter( const std::string &shaderName, size_t &cost )
{
	cost = 1;
	const char *oslShaderPaths = getenv( "OSL_SHADER_PATHS" );
	SearchPath searchPath( oslShaderPaths ? oslShaderPaths : "" );
	boost::filesystem::path path = searchPath.find( shaderName + ".oso" );
	if( path.empty() )
	{
		return shaderName;
	}
	else
	{
		return path.string();
	}
}

typedef IECore::LRUCache<std::string, std::string> ShaderSearchPathCache;
ShaderSearchPathCache g_shaderSearchPathCache( shaderCacheGetter, 10000 );

//const ccl::ustring g_( "" );

} // namespace

//////////////////////////////////////////////////////////////////////////
// RenderCallback
//////////////////////////////////////////////////////////////////////////

namespace
{

class RenderCallback : public IECore:RefCounted
{

	public :

		RenderCallback( )
		{
		}

		bool writeRender( const uchar *pixels, int width, int height, int channels )
		{
		}

}

class RenderTileCallback : public IECore:RefCounted
{

	public :

		RenderTileCallback( ccl::Session *session )
			: m_session( session )
		{
			ccl::Camera &camera = m_session->scene->camera;
			//ccl::DisplayBuffer &display = m_session->display;
			// TODO: Work out if Cycles can do overscan...
			displayDriver = IECoreImage::DisplayDriver::create( "ieDisplay",
				Box2i(V2i(0, 0)
				      V2i(camera.width - 1, camera.height - 1)), 
				Box2i(V2i(0, 0)
				      V2i(camera.width - 1, camera.height - 1)), 
				
				);
		}

		void updateRenderTile( ccl::RenderTile& rtile, bool highlight)
		{
			int x = rtile.x - m_session->tile_manager.params.full_x;
			int y = rtile.y - m_session->tile_manager.params.full_y;
			int w = rtile.w;
			int h = rtile.h;

		}

	private :

		ccl::Session *m_session;
		DisplayDriverPtr displayDriver;
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// CyclesOutput
//////////////////////////////////////////////////////////////////////////

namespace
{

ccl::PassType nameToPassType( const std::string &name )
{
#define MAP_PASS(passname, passtype) if(name == passname) return passtype;
	MAP_PASS( "rgba", ccl::PASS_COMBINED );
	MAP_PASS( "depth", ccl::PASS_DEPTH );
	MAP_PASS( "normal", ccl::PASS_NORMAL );
	MAP_PASS( "uv", ccl::PASS_UV );
	MAP_PASS( "object_id", ccl::PASS_OBJECT_ID );
	MAP_PASS( "material_id", ccl::PASS_MATERIAL_ID );
	MAP_PASS( "motion", ccl::PASS_MOTION );
	MAP_PASS( "motion_weight", ccl::PASS_MOTION_WEIGHT );
	MAP_PASS( "render_time", ccl::PASS_RENDER_TIME );
	MAP_PASS( "cryptomatte", ccl::PASS_CRYPTOMATTE );
	MAP_PASS( "mist", ccl::PASS_MIST );
	MAP_PASS( "emission", ccl::PASS_EMISSION );
	MAP_PASS( "background", ccl::PASS_BACKGROUND );
	MAP_PASS( "ao", ccl::PASS_AO );
	MAP_PASS( "shadow", ccl::PASS_SHADOW );
	MAP_PASS( "diffuse_direct", ccl::PASS_DIFFUSE_DIRECT );
	MAP_PASS( "diffuse_indirect", ccl::PASS_DIFFUSE_INDIRECT );
	MAP_PASS( "diffuse_color", ccl::PASS_DIFFUSE_COLOR );
	MAP_PASS( "glossy_direct", ccl::PASS_GLOSSY_DIRECT );
	MAP_PASS( "glossy_indirect", ccl::PASS_GLOSSY_INDIRECT );
	MAP_PASS( "glossy_color", ccl::PASS_GLOSSY_COLOR );
	MAP_PASS( "transmission_direct", ccl::PASS_TRANSMISSION_DIRECT );
	MAP_PASS( "transmission_indirect", ccl::PASS_TRANSMISSION_INDIRECT );
	MAP_PASS( "transmission_color", ccl::PASS_TRANSMISSION_COLOR );
	MAP_PASS( "subsurface_direct", ccl::PASS_SUBSURFACE_DIRECT );
	MAP_PASS( "subsurface_indirect", ccl::PASS_SUBSURFACE_INDIRECT );
	MAP_PASS( "subsurface_color", ccl::PASS_SUBSURFACE_COLOR );
	MAP_PASS( "volume_direct", ccl::PASS_VOLUME_DIRECT );
	MAP_PASS( "volume_indirect", ccl::PASS_VOLUME_INDIRECT );
#undef MAP_PASS

	return ccl::PASS_NONE );
}

class CyclesOutput : public IECore::RefCounted
{

	public :

		CyclesOutput( const IECoreScene::Output *output )
		{
			type = output->getType();
			data = output->getData();
			passType = nameToPassType( data );

			for( auto &params : output->parameters() )
			{
				if( params.first == "quantize" )
				{
					const vector<int> quantize = parameter<vector<int>>( params.second, "quantize", { 0, 0, 0, 0 } );
					if( quantize == vector<int>( { 0, 255, 0, 255 } ) )
					{
						quantize = ccl::TypeDesc::UINT8;
					}
					else if( quantize == vector<int>( { 0, 65536, 0, 65536 } ) )
					{
						quantize = ccl::TypeDesc::UINT16;
					}
					else
					{
						quantize = ccl::TypeDesc::FLOAT;
					}
				}
			}
		}

		std::string type;
		std::string data;
		ccl::PassType passType;
		ccl::TypeDesc quantize;
};

IE_CORE_DECLAREPTR( CyclesOutput )

} // namespace

//////////////////////////////////////////////////////////////////////////
// CyclesShader
//////////////////////////////////////////////////////////////////////////

namespace
{

class CyclesShader : public IECore::RefCounted
{

	public :

		CyclesShader( ccl::Scene* scene, const IECore::ObjectVector *shaderNetwork, DelightHandle::Ownership ownership )
		{
			const string name = "shader:" + shaderNetwork->Object::hash().toString();

			for( const ObjectPtr &object : shaderNetwork->members() )
			{
				const Shader *shader = runTimeCast<const Shader>( object.get() );
				if( !shader )
				{
					continue;
				}

				const string shaderHandle = parameter<string>( shader->parameters(), "__handle", "" );
				const string nodeName = shaderHandle.size() ? name + ":" + shaderHandle : name;

				NSICreate(
					context,
					nodeName.c_str(),
					"shader",
					0, nullptr
				);

				ParameterList parameterList;
				std::string shaderFileName = g_shaderSearchPathCache.get( shader->getName() );
				parameterList.add( "shaderfilename", shaderFileName );

				for( const auto &parameter : shader->parameters() )
				{
					if( parameter.first == "__handle" )
					{
						continue;
					}
					// Deal with connections, which are specified awkwardly as
					// string parameters prefixed with "link:".
					if( auto stringData = runTimeCast<const StringData>( parameter.second ) )
					{
						const string &value = stringData->readable();
						if( boost::starts_with( value, "link:" ) )
						{
							const size_t i = value.find_first_of( "." );

							string fromHandle( value.begin() + 5, value.begin() + i );
							fromHandle = name + ":" + fromHandle;
							const char *fromAttr = value.c_str() + i + 1;

							NSIConnect(
								context,
								fromHandle.c_str(),
								fromAttr,
								nodeName.c_str(),
								parameter.first.c_str(),
								0, nullptr
							);
							continue;
						}
					}
					// Standard parameter with values
					parameterList.add( parameter.first.c_str(), parameter.second.get() );
				}

				NSISetAttribute(
					context,
					nodeName.c_str(),
					parameterList.size(),
					parameterList.data()
				);

				m_handles.emplace_back( context, nodeName, ownership );
			}
		}

		const DelightHandle &handle() const
		{
			return m_handles.back();
		}

	private :

		std::vector<CyclesHandle> m_handles;

};

IE_CORE_DECLAREPTR( CyclesShader )

} // namespace

//////////////////////////////////////////////////////////////////////////
// ShaderCache
//////////////////////////////////////////////////////////////////////////

namespace
{

class ShaderCache : public IECore::RefCounted
{

	public :

		ShaderCache( ccl::Scene* scene, DelightHandle::Ownership ownership )
			:	m_scene( scene ), m_ownership( ownership )
		{
		}

		// Can be called concurrently with other get() calls.
		CyclesShaderPtr get( const IECore::ObjectVector *shader )
		{
			Cache::accessor a;
			m_cache.insert( a, shader ? shader->Object::hash() : MurmurHash() );
			if( !a->second )
			{
				if( shader )
				{
					a->second = new CyclesShader( m_context, shader, m_ownership );
				}
				else
				{
					ObjectVectorPtr defaultSurfaceNetwork = new ObjectVector;
					/// \todo Use a shader that comes with 3delight, and provide
					/// the expected "defaultsurface" facing ratio shading. The
					/// closest available at present is the samplerInfo shader, but
					/// that spews errors about a missing "mayaCamera" coordinate
					/// system.
					ShaderPtr defaultSurfaceShader = new Shader( "Surface/Constant", "surface" );
					defaultSurfaceNetwork->members().push_back( defaultSurfaceShader );
					a->second = new CyclesShader( m_context, defaultSurfaceNetwork.get(), m_ownership );
				}
			}
			return a->second;
		}

		CyclesShaderPtr defaultSurface()
		{
			return get( nullptr );
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
					// shader.
					toErase.push_back( it->first );
				}
			}
			for( vector<IECore::MurmurHash>::const_iterator it = toErase.begin(), eIt = toErase.end(); it != eIt; ++it )
			{
				m_cache.erase( *it );
			}
		}

	private :

		ccl::Scene* m_scene;
		DelightHandle::Ownership m_ownership;

		typedef tbb::concurrent_hash_map<IECore::MurmurHash, CyclesShaderPtr> Cache;
		Cache m_cache;

};

IE_CORE_DECLAREPTR( ShaderCache )

} // namespace

//////////////////////////////////////////////////////////////////////////
// CyclesAttributes
//////////////////////////////////////////////////////////////////////////

namespace
{

IECore::InternedString g_useHoldoutAttributeName( "ccl:use_holdout" );
IECore::InternedString g_isShadowCatcherAttributeName( "ccl:is_shadow_catcher" );
IECore::InternedString g_useAdaptiveSubdivisionAttributeName( "ccl:max_level" );
IECore::InternedString g_dicingRateAttributeName( "ccl:dicing_rate" );

std::array<IECore::InternedString, 4> g_shaderAttributeNames = { {
	"osl:light",
	"light",
	"osl:surface",
	"surface",
} };

ccl::RayType nameToRayType( const std::string &name )
{
#define MAP_RAY(rayname, raytype) if(name == rayname) return raytype;
	MAP_RAY( "camera", ccl::PATH_RAY_CAMERA );
	MAP_RAY( "diffuse", ccl::PATH_RAY_DIFFUSE );
	MAP_RAY( "glossy", ccl::PATH_RAY_GLOSSY );
	MAP_RAY( "transmission", ccl::PATH_RAY_TRANSMIT );
	MAP_RAY( "shadow", ccl::PATH_RAY_SHADOW );
	MAP_RAY( "scatter", ccl::PATH_RAY_VOLUME_SCATTER );
#undef MAP_RAY

	return 0;
}

IECore::InternedString g_setsAttributeName( "sets" );

class CyclesAttributes : public IECoreScenePreview::Renderer::AttributesInterface
{

	public :

		CyclesAttributes( const IECore::CompoundObject *attributes, ShaderCache *shaderCache )
			:	m_visibility( ~0 ), m_useHoldout( false ), m_isShadowCatcher( false ), m_maxLevel( 12 ), m_dicingRate( 1.0f )
		{
			for( const auto &name : g_shaderAttributeNames )
			{
				if( const Object *o = attributes->member<const Object>( name ) )
				{
					if( const ObjectVector *shader = reportedCast<const ObjectVector>( o, "attribute", name ) )
					{
						m_shader = shaderCache->get( shader );
					}
					break;
				}
			}

			for( const auto &m : attributes->members() )
			{
				if( m.first == g_setsAttributeName )
				{
					if( const InternedStringVectorData *d = reportedCast<const InternedStringVectorData>( m.second.get(), "attribute", m.first ) )
					{
						if( d->readable().size() )
						{
							msg( Msg::Warning, "CyclesRenderer", "Attribute \"sets\" not supported" );
						}
					}
				}
				else if( boost::starts_with( m.first.string(), "ccl:visibility:" ) )
				{
					if( const Data *d = reportedCast<const IECore::Data>( m.second.get(), "attribute", m.first ) )
					{
						if( const BoolData &data = static_cast<const BoolData *>( d ) )
						{
							auto &vis = data->readable();
							auto ray = nameToRayType( m.first.string() + 15 );
							m_visibility |= vis ? ray : m_visibility & ~ray;
						}
					}
				}
				else if( boost::starts_with( m.first.string(), "ccl:" ) )
				{
					if( const Data *d = reportedCast<const IECore::Data>( m.second.get(), "attribute", m.first ) )
					{
						if( m.first == g_useHoldoutAttributeName )
						{
							if ( const BoolData *data = static_cast<const BoolData *>( d ) )
								m_useHoldout = data->readable();
						}
						else if( m.first == g_isShadowCatcherAttributeName )
						{
							if ( const BoolData *data = static_cast<const BoolData *>( d ) )
								m_isShadowCatcher = data->readable();
						}
						else if( m.first == g_maxLevelAttributeName )
						{
							if ( const BoolData *data = static_cast<const BoolData *>( d ) )
								m_maxLevel = data->readable();
						}
						else if( m.first == g_dicingRateAttributeName )
						{
							if ( const FloatData *data = static_cast<const FloatData *>( d ) )
								m_dicingRate = data->readable();
						}
						//setSocket( node, m.first.string() + 15, value );
						//m_attributes[m.first.string() + 15] = value;
					}
				}
				else if( boost::starts_with( m.first.string(), "user:" ) )
				{
					msg( Msg::Warning, "CyclesRenderer", boost::format( "User attribute \"%s\" not supported" ) % m.first.string() );
				}
				else if( boost::contains( m.first.string(), ":" ) )
				{
					// Attribute for another renderer - ignore
				}
				else
				{
					msg( Msg::Warning, "CyclesRenderer", boost::format( "Attribute \"%s\" not supported" ) % m.first.string() );
				}
			}

			//setSocket( node, "visibility", value );

			if( !m_shader )
			{
				m_shader = shaderCache->defaultSurface();
			}

		}

		bool apply( ccl::Node *node, const CyclesAttributes *previousAttributes ) const
		{
			SocketAlgo::setSocket( node, "visibility", m_visibility );
			SocketAlgo::setSocket( node, g_useHoldoutAttributeName + 4, m_useHoldout );
			SocketAlgo::setSocket( node, g_isShadowCatcherAttributeName + 4, m_isShadowCatcher );
			if( node->find_input("Mesh") )
			{
				ccl::Object *object = (ccl::Object*)node;
				if( object->mesh->subd_params )
				{
					object->mesh->subd_params.max_level = m_max_level;
					object->mesh->subd_params.dicing_rate = m_dicing_rate;
				}
			}
			return true;
		}

		//const DelightHandle &handle() const
		//{
		//	return m_handle;
		//}

	private :

		struct Curves
		{
			Curves( const IECore::CompoundObject *attributes )
			{
				
			}
		}

		ConstCyclesShaderPtr m_shader;
		unsigned m_visibility;
		bool m_useHoldout;
		bool m_isShadowCatcher;
		bool m_useAdaptiveSubdivision;
		float m_dicingRate;

};

IE_CORE_DECLAREPTR( CyclesAttributes )

} // namespace

//////////////////////////////////////////////////////////////////////////
// AttributesCache
//////////////////////////////////////////////////////////////////////////

namespace
{

class AttributesCache : public IECore::RefCounted
{

	public :

		AttributesCache( ShaderCachePtr *shaderCache )
			:	m_shaderCache( shaderCache )
		{
		}

		// Can be called concurrently with other get() calls.
		CyclesAttributesPtr get( const IECore::CompoundObject *attributes )
		{
			Cache::accessor a;
			m_cache.insert( a, attributes->Object::hash() );
			if( !a->second )
			{
				a->second = new CyclesAttributes( attributes, m_shaderCache.get() );
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

		ShaderCachePtr m_shaderCache;

		typedef tbb::concurrent_hash_map<IECore::MurmurHash, CyclesAttributesPtr> Cache;
		Cache m_cache;

};

IE_CORE_DECLAREPTR( AttributesCache )

} // namespace

//////////////////////////////////////////////////////////////////////////
// InstanceCache
//////////////////////////////////////////////////////////////////////////

namespace
{

class Instance
{

	public :

		Instance( const SharedCObjectPtr object, const SharedCMeshPtr mesh )
			:	m_object( object ), m_mesh( mesh )
		{
		}

		ccl::Object *object()
		{
			return m_object.get();
		}

		ccl::Mesh *mesh()
		{
			return m_mesh.get();
		}

	private :

		SharedCObjectPtr m_object;
		SharedCMeshPtr m_mesh;

}

class InstanceCache : public IECore::RefCounted
{

	public :

		InstanceCache( ccl::Scene *scene )
			: m_scene( scene )
		{
		}

		void update( ccl::Scene *scene )
		{
			m_scene = scene;
			updateObjects();
			updateMeshes();
		}

		// Can be called concurrently with other get() calls.
		Instance get( const IECore::Object *object, const std::string &nodeName )
		{
			ccl::Object *cobject = nullptr;

			const IECore::MurmurHash hash = object->Object::hash();

			MeshCache::accessor a;
			m_meshes.insert( a, hash );

			if( !a->second )
			{
				cobject = convert( object, "instance:" + hash.toString() );
				a->second = SharedCMeshPtr( cobject->mesh );
			}
			else
			{
				cobject = new ccl::Object();
				cobject->mesh = a->second.get();
				cobject->name = ccl::ustring( nodeName.c_str() );
			}

			auto cobjectPtr = SharedCObjectPtr( cobject );
			// Push-back to vector needs thread locking.
			{
				tbb::spin_mutex::scoped_lock lock( m_objectsMutex );
				m_objects.push_back( cobjectPtr );
			}

			return Instance( cobjectPtr, a->second );
		}

		// Can be called concurrently with other get() calls.
		Instance get( const std::vector<const IECore::Object *> &samples, const std::vector<float> &times, const std::string &nodeName )
		{
			ccl::Object *cobject = nullptr;

			IECore::MurmurHash hash;
			for( std::vector<const IECore::Object *>::const_iterator it = samples.begin(), eIt = samples.end(); it != eIt; ++it )
			{
				(*it)->hash( hash );
			}
			for( std::vector<float>::const_iterator it = times.begin(), eIt = times.end(); it != eIt; ++it )
			{
				hash.append( *it );
			}

			MeshCache::accessor a;
			m_meshCache.insert( a, hash );

			if( !a->second )
			{
				cobject = convert( samples, "instance:" + hash.toString() );
				a->second = SharedCMeshPtr( cobject->mesh );
			}
			else
			{
				cobject = new ccl::Object();
				cobject->mesh = a->second.get();
				cobject->name = ccl::ustring( nodeName.c_str() );
			}

			auto cobjectPtr = SharedCObjectPtr( cobject );
			// Push-back to vector needs thread locking.
			{
				tbb::spin_mutex::scoped_lock lock( m_objectsMutex );
				m_objects.push_back( cobjectPtr );
			}

			return Instance( cobjectPtr, a->second );
		}

		// Must not be called concurrently with anything.
		void clearUnused()
		{
			// Meshes
			vector<IECore::MurmurHash> toErase;
			for( MeshCache::iterator it = m_meshes.begin(), eIt = m_meshes.end(); it != eIt; ++it )
			{
				if( it->second.unique() )
				{
					// Only one reference - this is ours, so
					// nothing outside of the cache is using the
					// instance.
					toErase.push_back( it->first );
				}
			}
			for( vector<IECore::MurmurHash>::const_iterator it = toErase.begin(), eIt = toErase.end(); it != eIt; ++it )
			{
				m_meshes.erase( *it );
			}

			if( toErase.size() )
				updateMeshes();

			// Objects
			vector<SharedCObjectPtr> toErase;
			for( set<SharedCObjectPtr>::iterator it = m_objects.begin(), eIt = m_meshes.end(); it != eIt; ++it )
			{
				if( it->unique() )
				{
					// Only one reference - this is ours, so
					// nothing outside of the cache is using the
					// instance.
					toErase.push_back( *it );
				}
			}
			for( set<SharedCObjectPtr>::const_iterator it = toErase.begin(), eIt = toErase.end(); it != eIt; ++it )
			{
				m_objects.erase( *it );
			}

			if( toErase.size() )
				updateObjects();
		}

	private :

		void updateObjects() const
		{
			auto &objects = m_scene->objects;
			objects.clear();
			for( vector<SharedCObjectPtr>::const_iterator it = m_objects.begin(), eIt = m_objects.end(); it != eIt; ++it )
			{
				if( it->second )
				{
					objects.push_back( it->second.get() );
				}
			}
		}

		void updateMeshes() const
		{
			auto &meshes = m_scene->meshes;
			meshes.clear();
			for( Cache::const_iterator it = m_cache.begin(), eIt = m_cache.end(); it != eIt; ++it )
			{
				if( it->second )
				{
					meshes.push_back( it->second.get() );
				}
			}
		}

		ccl::Scene *m_scene;
		vector<SharedCObjectPtr> m_objects;
		typedef tbb::concurrent_hash_map<IECore::MurmurHash, SharedCMeshPtr> MeshCache;
		MeshCache m_meshes;
		tbb::spin_mutex m_objectsMutex;

};

IE_CORE_DECLAREPTR( InstanceCache )

} // namespace

//////////////////////////////////////////////////////////////////////////
// LightCache
//////////////////////////////////////////////////////////////////////////

namespace
{

class LightCache : public IECore::RefCounted
{

	public :

		LightCache( ccl::Scene *scene )
			: m_scene( scene )
		{
		}

		void update( ccl::Scene *scene )
		{
			m_scene = scene;
			updateLights();
		}

		// Can be called concurrently with other get() calls.
		SharedCLightPtr get( const IECore::Object *object, const std::string &nodeName )
		{
			auto clight = SharedCLightPtr( new ccl::Light() );
			clight.get().name = nodeName.c_str();
			// Push-back to vector needs thread locking.
			{
				tbb::spin_mutex::scoped_lock lock( m_lightsMutex );
				m_lights.push_back( clight );
			}
			return clight;
		}

		// Must not be called concurrently with anything.
		void clearUnused()
		{
			vector<SharedCLightPtr> toErase;
			for( vector<SharedCLightPtr>::iterator it = m_objects.begin(), eIt = m_meshes.end(); it != eIt; ++it )
			{
				if( it->unique() )
				{
					// Only one reference - this is ours, so
					// nothing outside of the cache is using the
					// instance.
					toErase.push_back( *it );
				}
			}
			for( set<SharedCLightPtr>::const_iterator it = toErase.begin(), eIt = toErase.end(); it != eIt; ++it )
			{
				m_objects.erase( *it );
			}

			if( toErase.size() )
				updateLights();
		}

	private :

		void updateLights() const
		{
			auto &lights = m_scene->lights;
			lights.clear();
			for( vector<SharedCLightPtr>::const_iterator it = m_lights.begin(), eIt = m_lights.end(); it != eIt; ++it )
			{
				if( it->second )
				{
					lights.push_back( it->second.get() );
				}
			}
		}

		ccl::Scene *m_scene;
		ccl::vector<SharedCLightPtr> m_lights;
		tbb::spin_mutex m_lightsMutex;

};

IE_CORE_DECLAREPTR( LightCache )

} // namespace

//////////////////////////////////////////////////////////////////////////
// CyclesObject
//////////////////////////////////////////////////////////////////////////

namespace
{

class CyclesObject : public IECoreScenePreview::Renderer::ObjectInterface
{

	public :

		CyclesObject( const Instance &instance )
			:	m_instance( instance ), m_attributes( nullptr )
		{
		}

		void transform( const Imath::M44f &transform ) override
		{
			ccl::Object *object = m_instance.object();
			if( !object )
				return;
			object->tfm = SocketAlgo::setTransform( transform );
		}

		void transform( const std::vector<Imath::M44f> &samples, const std::vector<float> &times ) override
		{
			ccl::Object *object = m_instance.object();
			if( !object )
				return;
			const size_t numSamples = samples.size();
			object->motion = ccl::array( numSamples );
			for( size_t i = 0; i < numSamples; ++i )
				object->motion[i] = SocketAlgo::setTransform( samples[i] );
		}

		bool attributes( const IECoreScenePreview::Renderer::AttributesInterface *attributes ) override
		{
			ccl::Object *object = m_instance.object();
			if( !object )
			{
				return true;
			}

			const CyclesAttributes *cyclesAttributes = static_cast<const CyclesAttributes *>( attributes );
			if( cyclesAttributes->apply( object, m_attributes.get() ) )
			{
				m_attributes = cyclesAttributes;
				return true;
			}
			return false;
		}

	private :

		Instance m_instance;
		ConstCyclesAttributesPtr m_attributes;

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

		CyclesLight( const ccl::Light &light )
			:	m_light( light ), m_attributes( nullptr )
		{
		}

		void transform( const Imath::M44f &transform ) override
		{
			ccl::Light *light = m_light.get();
			if( !light )
				return;
			light->tfm = SocketAlgo::setTransform( transform );
		}

		void transform( const std::vector<Imath::M44f> &samples, const std::vector<float> &times ) override
		{
			ccl::Light *light = m_instance.get();
			if( !light )
				return;
			const size_t numSamples = samples.size();
			light->motion = ccl::array( numSamples );
			for( size_t i = 0; i < numSamples; ++i )
				light->motion[i] = SocketAlgo::setTransform( samples[i] );
		}

		bool attributes( const IECoreScenePreview::Renderer::AttributesInterface *attributes ) override
		{
			ccl::Light *light = m_light.get();
			if( !light )
				return true;

			const CyclesAttributes *cyclesAttributes = static_cast<const CyclesAttributes *>( attributes );
			if( cyclesAttributes->apply( light, m_attributes.get() ) )
			{
				m_attributes = cyclesAttributes;
				return true;
			}
			return false;
		}

	private :

		SharedCLightPtr m_light;
		ConstCyclesAttributesPtr m_attributes;

};

IE_CORE_DECLAREPTR( CyclesLight )

} // namespace

//////////////////////////////////////////////////////////////////////////
// CyclesCamera
//////////////////////////////////////////////////////////////////////////

namespace
{

class CyclesCamera : public IECoreScenePreview::Renderer::ObjectInterface
{

	public :

		CyclesCamera( const ccl::Camera &camera )
			:	m_camera( camera ), m_attributes( nullptr )
		{
		}

		void transform( const Imath::M44f &transform ) override
		{
			ccl::Camera *camera = m_camera.get();
			if( !camera )
				return;
			camera->matrix = SocketAlgo::setTransform( transform );
		}

		void transform( const std::vector<Imath::M44f> &samples, const std::vector<float> &times ) override
		{
			ccl::Camera *camera = m_instance.get();
			if( !camera )
				return;
			const size_t numSamples = samples.size();
			camera->motion = ccl::array( numSamples );
			for( size_t i = 0; i < numSamples; ++i )
				camera->motion[i] = SocketAlgo::setTransform( samples[i] );
		}

	private :

		CCameraPtr m_camera;
		ConstCyclesAttributesPtr m_attributes;

};

IE_CORE_DECLAREPTR( CyclesCamera )

} // namespace

//////////////////////////////////////////////////////////////////////////
// CyclesRenderer
//////////////////////////////////////////////////////////////////////////

namespace
{

// Core
IECore::InternedString g_frameOptionName( "frame" );
IECore::InternedString g_cameraOptionName( "camera" );
IECore::InternedString g_sampleMotionOptionName( "sampleMotion" );
IECore::InternedString g_deviceOptionName( "ccl:device" );
IECore::InternedString g_shadingsystemOptionName( "ccl:shadingsystem" );
// Session
IECore::InternedString g_backgroundOptionName( "ccl:session:background" );
IECore::InternedString g_progressiveRefineOptionName( "ccl:session:progressive_refine" );
IECore::InternedString g_progressiveOptionName( "ccl:session:progressive" );
IECore::InternedString g_experimentalOptionName( "ccl:session:experimental" );
IECore::InternedString g_samplesOptionName( "ccl:session:samples" );
IECore::InternedString g_tileSizeOptionName( "ccl:session:tile_size" );
IECore::InternedString g_tileOrderOptionName( "ccl:session:tile_order" );
IECore::InternedString g_startResolutionOptionName( "ccl:session:start_resolution" );
IECore::InternedString g_pixelSizeOptionName( "ccl:session:pixel_size" );
IECore::InternedString g_threadsOptionName( "ccl:session:threads" );
IECore::InternedString g_displayBufferLinearOptionName( "ccl:session:display_buffer_linear" );
IECore::InternedString g_useDenoisingOptionName( "ccl:session:use_denoising" );
IECore::InternedString g_denoisingRadiusOptionName( "ccl:session:denoising_radius" );
IECore::InternedString g_denoisingStrengthOptionName( "ccl:session:denoising_strength" );
IECore::InternedString g_denoisingFeatureStrengthOptionName( "ccl:session:denoising_feature_strength" );
IECore::InternedString g_denoisingRelativePcaOptionName( "ccl:session:denoising_relative_pca" );
IECore::InternedString g_cancelTimeoutOptionName( "ccl:session:cancel_timeout" );
IECore::InternedString g_resetTimeoutOptionName( "ccl:session:reset_timeout" );
IECore::InternedString g_textTimeoutOptionName( "ccl:session:text_timeout" );
IECore::InternedString g_progressiveUpdateTimeoutOptionName( "ccl:session:progressive_update_timeout" );
// Scene
IECore::InternedString g_bvhTypeOptionName( "ccl:scene:bvh_type" );
IECore::InternedString g_bvhLayoutOptionName( "ccl:scene:bvh_layout" );
IECore::InternedString g_useBvhSpatialSplitOptionName( "ccl:scene:use_bvh_spatial_split" );
IECore::InternedString g_useBvhUnalignedNodesOptionName( "ccl:scene:use_bvh_unaligned_nodes" );
IECore::InternedString g_useBvhTimeStepsOptionName( "ccl:scene:use_bvh_time_steps" );
IECore::InternedString g_persistentDataOptionName( "ccl:scene:persistent_data" );
IECore::InternedString g_textureLimitOptionName( "ccl:scene:texture_limit" );
// Curves
IECore::InternedString g_useCurvesOptionType( "ccl:curve:use_curves" );
IECore::InternedString g_curveMinimumWidthOptionType( "ccl:curve:minimum_width" );
IECore::InternedString g_curveMaximumWidthOptionType( "ccl:curve:maximum_width" );
IECore::InternedString g_curvePrimitiveOptionType( "ccl:curve:primitive" );
IECore::InternedString g_curveShapeOptionType( "ccl:curve:shape" );
IECore::InternedString g_curveResolutionOptionType( "ccl:curve:resolution" );
IECore::InternedString g_curveSubdivisionsOptionType( "ccl:curve:subdivisions" );
IECore::InternedString g_curveCullBackfacing( "ccl:curve:cull_backfacing" );

IE_CORE_FORWARDDECLARE( CyclesRenderer )

class CyclesRenderer final : public IECoreScenePreview::Renderer
{

	public :

		CyclesRenderer( RenderType renderType, const std::string &fileName )
			:	m_renderType( renderType ),
				m_session_params( ccl::SessionParams() ),
				m_scene_params( ccl::SceneParams() ),
				m_device_name( "CPU" ),
				m_shadingsystem_name( "OSL" )
		{
			/*
			ccl::vector<ccl::DeviceType>& device_types = ccl::Device::available_types();
			ccl::foreach(ccl::DeviceType type, device_types) {
				if(device_names != "")
					device_names += ", ";

				device_names += Device::string_from_type(type);
			}
			*/

			// TODO: See if it makes sense for Gaffer to manage image stuff or just use Cycles built-in.
			/*
			m_scene->image_manager->builtin_image_info_cb = 
				ccl::function_bind( &builtinImageInfo, this, ccl::_1, ccl::_2, ccl::_3 );
			m_scene->image_manager->builtin_image_pixels_cb = 
				ccl::function_bind( &builtinImagePixels, this, ccl::_1, ccl::_2, ccl::_3, ccl::_4, ccl::_5 );
			m_scene->image_manager->builtin_image_float_pixels_cb = 
				ccl::function_bind( &builtinImageFloatPixels, this, ccl::_1, ccl::_2, ccl::_3, ccl::_4, ccl::_5 );
			*/

			init();

			m_lightCache = new LightCache( m_scene );
			//m_shaderCache = new ShaderCache( m_scene );
			m_instanceCache = new InstanceCache( m_scene );
			m_attributesCache = new AttributesCache();

			// m_scene already has these, but we keep a copy that we can freely modify and later memcpy
			// into m_scene.
			m_integrator = new ccl::Integrator();
			m_background = new ccl::Background();
			m_film = new ccl::Film();
		}

		~CyclesRenderer() override
		{
			m_attributesCache.reset();
			m_instanceCache.reset();
			m_lightCache.reset();
			m_outputs.clear();
			m_defaultCamera.reset();
			delete m_integrator;
			delete m_background;
			delete m_film;

			// The rest should be cleaned up by Cycles.
			delete m_session;
		}

		IECore::InternedString name() const override
		{
			return "Cycles";
		}

		void option( const IECore::InternedString &name, const IECore::Object *value ) override
		{
			if( name == g_frameOptionName )
			{
				if( value == nullptr )
				{
					m_frame = boost::none;
				}
				else if( const IntData *data = reportedCast<const IntData>( value, "option", name ) )
				{
					m_frame = data->readable();
				}
				return;
			}
			else if( name == g_cameraOptionName )
			{
				if( value == nullptr )
				{
					m_camera = "";
				}
				else if( const StringData *data = reportedCast<const StringData>( value, "option", name ) )
				{
					m_camera = data->readable();
				}
				return;
			}
			else if( name == g_sampleMotionOptionName )
			{
				ccl::SocketType *input = m_integrator->node_type->find_input( "motion_blur" );
				if( value && input )
				{
					if( const BoolData *data = reportedCast<const BoolData>( value, "option", name ) )
					{
						SocketAlgo::setSocket( m_integrator, &input, data->readable() );
					}
					else
					{
						m_integrator->set_default_value( &input );
						//IECore::msg( IECore::Msg::Warning, "CyclesRenderer::option", boost::format( "Unknown value \"%s\" for option \"%s\"." ) % m_device_name, name.string() );
					}
				}
				else if( input )
				{
					m_integrator->set_default_value( &input );
				}
				return;
			}
			else if( boost::starts_with( name.string(), "ccl:session:" ) )
			{
				//std::string param = name.c_str() + 12;
				if( value )
				{
					if( name == g_deviceOptionName )
					{
						if( const StringData *data = reportedCast<const StringData>( value, "option", name ) )
						{
							auto device_name = data->readable();
							m_device_name = device_name;
						}
						else
						{
							m_device_name = "CPU";
							IECore::msg( IECore::Msg::Warning, "CyclesRenderer::option", boost::format( "Unknown value \"%s\" for option \"%s\"." ) % m_device_name, name.string() );
						}
						return;
					}
					else if( name == g_shadingsystemOptionName )
					{
						if( const StringData *data = reportedCast<const StringData>( value, "option", name ) )
						{
							auto shadingsystem_name = data->readable();
							if( shadingsystem_name == "OSL" )
							{
								m_shadingsystem_name = shadingsystem_name;
								m_session_params.shadingsystem = ccl::SHADINGSYSTEM_OSL;
								m_scene_params.shadingsystem   = ccl::SHADINGSYSTEM_OSL;
							}
							else if( shadingsystem_name == "SVM" )
							{
								m_shadingsystem_name = shadingsystem_name;
								m_session_params.shadingsystem = ccl::SHADINGSYSTEM_SVM;
								m_scene_params.shadingsystem   = ccl::SHADINGSYSTEM_SVM;
							}
							else
							{
								m_shadingsystem_name = "OSL";
								IECore::msg( IECore::Msg::Warning, "CyclesRenderer::option", boost::format( "Unknown value \"%s\" for option \"%s\"." ) % shadingsystem_name, name.string() );
							}
						}
						else
						{
							IECore::msg( IECore::Msg::Warning, "CyclesRenderer::option", boost::format( "Unknown value for option \"%s\"." ) % name.string() );
						}
						return;
					}
					else if( name == g_backgroundOptionName )
					{
						if ( const BoolData *data = reportedCast<const BoolData>( value, "option", name ) )
							m_session_params.background = data->readable();
						return;
					}
					else if( name == g_progressiveRefineOptionName )
					{
						if ( const BoolData *data = reportedCast<const BoolData>( value, "option", name ) )
							m_session_params.progressive_refine = data->readable();
						return;
					}
					else if( name == g_progressiveOptionName )
					{
						if ( const BoolData *data = reportedCast<const BoolData>( value, "option", name ) )
							m_session_params.progressive = data->readable();
						return;
					}
					else if( name == g_experimentalOptionName )
					{
						if ( const BoolData *data = reportedCast<const BoolData>( value, "option", name ) )
							m_session_params.experimental = data->readable();
						return;
					}
					else if( name == g_samplesOptionName )
					{
						if ( const IntData *data = reportedCast<const IntData>( value, "option", name ) )
							m_session_params.samples = data->readable();
						return;
					}
					else if( name == g_tileSizeOptionName )
					{
						if ( const V2iData *data = reportedCast<const IntData>( value, "option", name ) )
						{
							auto d = data->readable();
							m_session_params.tile_size = ccl::make_int2( d.x, d.y );
						}
						return;
					}
					else if( name == g_tileOrderOptionName )
					{
						if ( const IntData *data = reportedCast<const IntData>( value, "option", name ) )
							m_session_params.tile_order = (ccl::TileOrder)data->readable();
						return;
					}
					else if( name == g_startResolutionOptionName )
					{
						if ( const IntData *data = reportedCast<const IntData>( value, "option", name ) )
							m_session_params.start_resolution = data->readable();
						return;
					}
					else if( name == g_pixelSizeOptionName )
					{
						if ( const IntData *data = reportedCast<const IntData>( value, "option", name ) )
							m_session_params.pixel_size = data->readable();
						return;
					}
					else if( name == g_threadsOptionName )
					{
						if ( const IntData *data = reportedCast<const IntData>( value, "option", name ) )
							m_session_params.threads = data->readable();
						return;
					}
					else if( name == g_displayBufferLinearOptionName )
					{
						if ( const BoolData *data = reportedCast<const BoolData>( value, "option", name ) )
							m_session_params.display_buffer_linear = data->readable();
						return;
					}
					else if( name == g_useDenoisingOptionName )
					{
						if ( const BoolData *data = reportedCast<const BoolData>( value, "option", name ) )
							m_session_params.use_denoising = data->readable();
						return;
					}
					else if( name == g_denoisingRadiusOptionName )
					{
						if ( const IntData *data = reportedCast<const IntData>( value, "option", name ) )
							m_session_params.denoising_radius = data->readable();
						return;
					}
					else if( name == g_denoisingStrengthOptionName )
					{
						if ( const FloatData *data = reportedCast<const FloatData>( value, "option", name ) )
							m_session_params.denoising_strength = data->readable();
						return;
					}
					else if( name == g_denoisingFeatureStrengthOptionName )
					{
						if ( const FloatData *data = reportedCast<const FloatData>( value, "option", name ) )
							m_session_params.denoising_feature_strength = data->readable();
						return;
					}
					else if( name == g_denoisingRelativePcaOptionName )
					{
						if ( const BoolData *data = reportedCast<const BoolData>( value, "option", name ) )
							m_session_params.denoising_relative_pca = data->readable();
						return;
					}
					else if( name == g_cancelTimeoutOptionName )
					{
						if ( const FloatData *data = reportedCast<const FloatData>( value, "option", name ) )
							m_session_params.cancel_timeout = (double)data->readable();
						return;
					}
					else if( name == g_resetTimeoutOptionName )
					{
						if ( const FloatData *data = reportedCast<const FloatData>( value, "option", name ) )
							m_session_params.reset_timeout = (double)data->readable();
						return;
					}
					else if( name == g_textTimeoutOptionName )
					{
						if ( const FloatData *data = reportedCast<const FloatData>( value, "option", name ) )
							m_session_params.text_timeout = (double)data->readable();
						return;
					}
					else if( name == g_progressiveUpdateTimeoutOptionName )
					{
						if ( const FloatData *data = reportedCast<const FloatData>( value, "option", name ) )
							m_session_params.progressive_update_timeout = (double)data->readable();
						return;
					}
					else
					{
						IECore::msg( IECore::Msg::Warning, "CyclesRenderer::option", boost::format( "Unknown option \"%s\"." ) % name.string() );
						return;
					}
				}
			}
			else if( boost::starts_with( name.string(), "ccl:scene:" ) )
			{
				if( value )
				{
					if( name == g_bvhTypeOptionName )
					{
						if ( const IntData *data = reportedCast<const IntData>( value, "option", name ) )
							m_scene_params.bvh_type = (ccl::SceneParams::BVHType)data->readable();
						return;
					}
					else if( name == g_bvhLayoutOptionName )
					{
						if ( const IntData *data = reportedCast<const IntData>( value, "option", name ) )
							m_scene_params.bvh_layout = (ccl::SceneParams::BVHLayout)data->readable();
						return;
					}
					else if( name == g_useBvhSpatialSplitOptionName )
					{
						if ( const BoolData *data = reportedCast<const BoolData>( value, "option", name ) )
							m_scene_params.use_bvh_spatial_split = data->readable();
						return;
					}
					else if( name == g_useBvhUnalignedNodesOptionName )
					{
						if ( const BoolData *data = reportedCast<const BoolData>( value, "option", name ) )
							m_scene_params.use_bvh_unaligned_nodes = data->readable();
						return;
					}
					else if( name == g_useBvhTimeStepsOptionName )
					{
						if ( const IntData *data = reportedCast<const IntData>( value, "option", name ) )
							m_scene_params.use_bvh_time_steps = data->readable();
						return;
					}
					else if( name == g_persistentDataOptionName )
					{
						if ( const BoolData *data = reportedCast<const BoolData>( value, "option", name ) )
							m_scene_params.persistent_data = data->readable();
						return;
					}
					else if( name == g_textureLimitOptionName )
					{
						if ( const IntData *data = reportedCast<const IntData>( value, "option", name ) )
							m_scene_params.texture_limit = data->readable();
						return;
					}
					else
					{
						IECore::msg( IECore::Msg::Warning, "CyclesRenderer::option", boost::format( "Unknown option \"%s\"." ) % name.string() );
						return;
					}
				}
			}
			else if( boost::starts_with( name.string(), "ccl:curves:" ) )
			{
				if( value )
				{
					if( name == g_useCurvesOptionType )
					{
						if ( const BoolData *data = reportedCast<const BoolData>( value, "option", name ) )
							m_curve_params.use_curves = data->readable();
						return;
					}
					else if( name == g_curveMinimumWidthOptionType )
					{
						if ( const FloatData *data = reportedCast<const FloatData>( value, "option", name ) )
							m_curve_params.minimum_width = data->readable();
						return;
					}
					else if( name == g_curveMaximumWidthOptionType )
					{
						if ( const FloatData *data = reportedCast<const FloatData>( value, "option", name ) )
							m_curve_params.maximum_width = data->readable();
						return;
					}
					else if( name == g_curvePrimitiveOptionType )
					{
						if ( const IntData *data = reportedCast<const IntData>( value, "option", name ) )
							m_curve_params.primitive = (ccl::CurvePrimitiveType)data->readable();
						return;
					}
					else if( name == g_curveShapeOptionType )
					{
						if ( const IntData *data = reportedCast<const IntData>( value, "option", name ) )
							m_curve_params.curve_shape = (ccl::CurveShapeType)data->readable();
						return;
					}
					else if( name == g_curveResolutionOptionType )
					{
						if ( const IntData *data = reportedCast<const IntData>( value, "option", name ) )
							m_curve_params.resolution = data->readable();
						return;
					}
					else if( name == g_curveSubdivisionsOptionType )
					{
						if ( const IntData *data = reportedCast<const IntData>( value, "option", name ) )
							m_curve_params.subdivisions = data->readable();
						return;
					}
					else if( name == g_curveCullBackfacing )
					{
						if ( const BoolData *data = reportedCast<const BoolData>( value, "option", name ) )
							m_curve_params.use_backfacing = data->readable();
						return;
					}
				}
			}
			// The last 3 are subclassed internally from ccl::Node so treat their params like Cycles sockets
			else if( boost::starts_with( name.string(), "ccl:background:" ) )
			{
				ccl::SocketType *input = m_background->node_type->find_input( name.c_str() + 15 );
				if( value && input )
				{
					if( const Data *data = reportedCast<const Data>( value, "option", name ) )
					{
						SocketAlgo::setSocket( m_background, input, value );
					}
					else
					{
						m_background->set_default_value( *input );
					}
				}
				else if( input )
				{
					m_background->set_default_value( *input );
				}
				return;
			}
			else if( boost::starts_with( name.string(), "ccl:film:" ) )
			{
				ccl::SocketType *input = m_film->node_type->find_input( name.c_str() + 9 );
				if( value && input )
				{
					if( const Data *data = reportedCast<const Data>( value, "option", name ) )
					{
						SocketAlgo::setSocket( m_film, input, value );
					}
					else
					{
						m_film->set_default_value( *input );
					}
				}
				else if( input )
				{
					m_film->set_default_value( *input );
				}
				return;
			}
			else if( boost::starts_with( name.string(), "ccl:integrator:" ) )
			{
				ccl::SocketType *input = m_integrator->node_type->find_input( name.c_str() + 15 );
				if( value && input )
				{
					if( const Data *data = reportedCast<const Data>( value, "option", name ) )
					{
						SocketAlgo::setSocket( m_integrator, input, value );
					}
					else
					{
						m_integrator->set_default_value( *input );
					}
				}
				else if( input )
				{
					m_integrator->set_default_value( *input );
				}
				return;
			}
			else if( boost::starts_with( name.string(), "ccl:" ) )
			{
				IECore::msg( IECore::Msg::Warning, "CyclesRenderer::option", boost::format( "Unknown option \"%s\"." ) % name.string() );
				return;
			}
			else if( boost::starts_with( name.string(), "user:" ) )
			{
				IECore::msg( Msg::Warning, "CyclesRenderer::option", boost::format( "User option \"%s\" not supported" ) % name.string() );
				return;
			}
			else if( boost::contains( name.c_str(), ":" ) )
			{
				// Ignore options prefixed for some other renderer.
				return;
			}
			else
			{
				IECore::msg( IECore::Msg::Warning, "CyclesRenderer::option", boost::format( "Unknown option \"%s\"." ) % name.string() );
				return;
			}
		}

		void output( const IECore::InternedString &name, const Output *output ) override
		{
			auto passType = nameToPassType( output->getData() );
			if( passType == ccl::PASS_NONE )
				return;

			ccl::array<Pass> passes;
			// Beauty
			ccl::Pass::add( ccl::PASS_COMBINED, passes );

			ccl::Film *film = m_scene->film;

			if( !output && ccl::Pass::contains( film->passes, passType ) )
			{
				// Just remove and rebuild
				m_outputs.erase( name );
			}
			else if( !ccl::Pass::contains(film->passes, passType ) )
			{
				m_outputs[name] = new CyclesOutput( output );
			}
			else
				return;

			for( auto &output : m_outputs )
			{
				if( output.second.passType == ccl::PASS_COMBINED )
				{
					continue;
				}
				ccl::Pass::add( output.second.passType, passes );
			}

			ccl::BufferParams bufferParams;
			bufferParams.passes = passes;

			film->tag_update( m_scene );
		}

		Renderer::AttributesInterfacePtr attributes( const IECore::CompoundObject *attributes ) override
		{
			return m_attributesCache->get( attributes );
		}

		ObjectInterfacePtr camera( const std::string &name, const IECoreScene::Camera *camera, const AttributesInterface *attributes ) override
		{
			if( ccl::Camera *ccamera = CameraAlgo::convert( camera, name ) )
			{
				return nullptr;
			}

			// Store the camera for later use in updateCamera().
			{
				tbb::spin_mutex::scoped_lock lock( m_camerasMutex );
				m_cameras[name] = camera;
			}

			ObjectInterfacePtr result = new CyclesCamera( ccamera );
			result->attributes( attributes );
			return result;
		}

		ObjectInterfacePtr light( const std::string &name, const IECore::Object *object, const AttributesInterface *attributes ) override
		{
			SharedCLightPtr clight = m_lightCache->get( object, name );
			if( !clight )
			{
				return nullptr;
			}

			ObjectInterfacePtr result = new CyclesLight( clight );
			result->attributes( attributes );
			return result;
		}

		ObjectInterfacePtr object( const std::string &name, const IECore::Object *object, const AttributesInterface *attributes ) override
		{
			Instance instance = m_instanceCache->get( object, name );
			if( !instance )
			{
				return nullptr;
			}

			ObjectInterfacePtr result = new CyclesObject( instance );
			result->attributes( attributes );
			return result;
		}

		ObjectInterfacePtr object( const std::string &name, const std::vector<const IECore::Object *> &samples, const std::vector<float> &times, const AttributesInterface *attributes ) override
		{
			Instance instance = m_instanceCache->get( object, name );
			if( !instance )
			{
				return nullptr;
			}

			ObjectInterfacePtr result = new CyclesObject( instance );
			result->attributes( attributes );
			return result;
		}

		void render() override
		{
			updateOptions();
			// Clear out any objects which aren't needed in the cache.
			m_lightCache->clearUnused();
			m_instanceCache->clearUnused();
			m_attributesCache->clearUnused();

			if( m_rendering )
			{
			}

			updateCamera();

			if( m_renderType == Interactive )
			{
				m_session->write_render_tile_cb = ccl::function_bind(&RenderTileCallback::writeRenderTile, this, _1);
				m_session->update_render_tile_cb = ccl::function_bind(&RenderTileCallback::updateRenderTile, this, _1, _2);
			}

			m_rendering = true;

			if( m_renderType == Interactive )
			{
				return;
			}

			m_rendering = false;
		}

		void pause() override
		{
			m_session->set_pause( true );
		}

	private :

		void init()
		{
			// Clear scene & session if they exist.
			if( m_session )
				delete m_session;

			// Session Defaults
			m_session_params.display_buffer_linear = true;

			if( m_shadingsystem_name == "OSL" )
				m_session_params.shadingsystem = ccl::SHADINGSYSTEM_OSL;
			else if( m_shadingsystem_name == "SVM" )
				m_session_params.shadingsystem = ccl::SHADINGSYSTEM_SVM;

			// Fallback
			ccl::DeviceType device_type_fallback = ccl::Device::type_from_string( "CPU" );
			ccl::DeviceInfo device_fallback;

			ccl::DeviceType device_type = ccl::Device::type_from_string( m_device_name.c_str() );

			ccl::vector<ccl::DeviceInfo>& devices = ccl::Device::available_devices();
			bool device_available = false;
			for( ccl::DeviceInfo& device : devices ) 
			{
				if( device_type_fallback == device.type )
				{
					device_fallback = device;
					break;
				}
			}
			for( ccl::DeviceInfo& device : devices ) 
			{
				if( device_type == device.type ) 
				{
					m_session_params.device = device;
					device_available = true;
					break;
				}
			}
			if( !device_available )
			{
				IECore::msg( IECore::Msg::Warning, "CyclesRenderer", boost::format( "Cannot find the device \"%s\" requested, reverting to CPU." ) % m_device_name );
				m_session_params.device = device_fallback;
			}

			m_session = new ccl::Session( m_session_params );
			m_session->set_pause( true );

			m_scene_params.shadingsystem = m_session_params.shadingsystem;
			m_scene = new ccl::Scene( m_scene_params, m_session->device );

			session->scene = m_scene;
		}

		void stop()
		{
			if( !m_rendering )
			{
				return;
			}

			m_session->wait();

			m_rendering = false;
		}

		void updateSceneObjects()
		{
			m_shaderCache.update( m_scene );
			m_lightCache.update( m_scene );
			m_instanceCache.update( m_scene );
		}

		void updateOptions()
		{

			// If anything changes in scene or session, we reset.
			if( m_scene->params.modified( m_scene_params ) ||
			    m_session->params.modified( m_session_params )
			{
				reset();
			}

			if( m_integrator->modified( m_scene->integrator ) )
			{
				memcpy( m_scene.integrator, m_integrator, sizeof( ccl::Integrator ) );
				m_scene->integrator->tag_update( m_scene );
			}

			if( m_background->modified( m_scene->background ) )
			{
				memcpy( m_scene.background, m_background, sizeof( ccl::Background ) );
				m_scene->background->tag_update( m_scene );
			}

			if( m_film->modified( m_scene->film ) )
			{
				memcpy( m_scene.film, m_film, sizeof( ccl::Film ) );
				m_scene->film->tag_update( m_scene );
			}
		}

		void reset()
		{
			// This is so cycles doesn't delete the objects that Gaffer manages.
			m_scene->objects.clear();
			m_scene->meshes.clear();
			m_scene->shaders.clear();
			m_scene->lights.clear();
			m_scene->particle_systems.clear();
			init();
			// Make sure the instance cache points to the right scene.
			updateSceneObjects();
		}

		void updateCamera()
		{
			// Check that the camera we want to use exists,
			// and if not, create a default one.
			const auto cameraIt = m_cameras.find( m_camera );
			if( cameraIt == m_cameras.end() )
			{
				if( !m_camera.empty() )
				{
					IECore::msg(
						IECore::Msg::Warning, "CyclesRenderer",
						boost::format( "Camera \"%s\" does not exist" ) % m_camera
					);
				}
				m_defaultCamera = new ccl::Camera;
				m_defaultCamera.get()->name = "ieCoreCamera:defaultCamera";

				m_scene->camera = m_defaultCamera.get();
			}
			else
			{
				m_scene->camera = cameraIt->second.get();
				m_defaultCamera.reset();
			}
			scene->camera->update( m_scene );
		}

		// Callback in Cycles for builtin image info
		void builtinImageInfo( const string &builtin_name, void *builtin_data, ccl::ImageMetaData& metadata  )
		{

		}

		// Callback in Cycles for builtin image pixels.
		bool builtinImagePixels( const string &builtin_name,
								 void *builtin_data,
								 unsigned char *pixels,
								 const size_t pixels_size,
								 const bool free_cache )
		{
			return true;
		}

		// Same as above, but for floats.
		bool BlenderSession::builtin_image_float_pixels( const string &builtin_name,
														 void *builtin_data,
														 float *pixels,
														 const size_t pixels_size,
														 const bool free_cache )
		{
			return true;
		}

		// Callback in Cycles to render to a display
		void writeRenderTile( ccl::RenderTile& rtile )
		{
			int x = rtile.x - m_session->tile_manager.params.full_x;
			int y = rtile.y - m_session->tile_manager.params.full_y;
			int w = rtile.w;
			int h = rtile.h;

		}

		void updateRenderTile( ccl::RenderTile& rtile, bool highlight)
		{

		}

		// Cycles core objects.
		ccl::Session *m_session;
		ccl::Scene *m_scene;
		ccl::SessionParams m_session_params;
		ccl::SceneParams m_scene_params;
		ccl::Integrator *m_integrator;
		ccl::Background *m_background;
		ccl::Film *m_film;

		// IECoreScene::Renderer
		std::string m_device;
		RenderType m_renderType;
		int m_frame;
		string m_camera;
		int m_oversampling;
		bool m_rendering = false;

		// Caches.
		ShaderCachePtr m_shaderCache;
		LightCachePtr m_lightCache;
		InstanceCachePtr m_instanceCache;
		AttributesCachePtr m_attributesCache;

		// Outputs
		typedef std::map<IECore::InternedString, ConstCyclesOutputPtr> OutputMap;
		OutputMap m_outputs;

		// Cameras (Cycles can only know of one camera at a time)
		typedef unordered_map<string, ConstCameraPtr> CameraMap;
		CameraMap m_cameras;
		tbb::spin_mutex m_camerasMutex;
		ConstCameraPtr m_defaultCamera;

		// Registration with factory
		static Renderer::TypeDescription<CyclesRenderer> g_typeDescription;

};

IECoreScenePreview::Renderer::TypeDescription<CyclesRenderer> CyclesRenderer::g_typeDescription( "Cycles" );

} // namespace
