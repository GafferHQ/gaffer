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
#include "GafferCycles/IECoreCyclesPreview/InstancingConverter.h"
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

typedef std::shared_ptr<ccl::Session*> SharedCSessionPtr;
typedef std::shared_ptr<ccl::Scene*> SharedCScenePtr;
typedef std::shared_ptr<ccl::Object*> SharedCObjectPtr;

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
	SearchPath searchPath( oslShaderPaths ? oslShaderPaths : "", ":" );
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
// DelightHandle
//////////////////////////////////////////////////////////////////////////

namespace
{
} // namespace

//////////////////////////////////////////////////////////////////////////
// DelightOutput
//////////////////////////////////////////////////////////////////////////

namespace
{

class CyclesOutput : public IECore::RefCounted
{

	public :

		CyclesOutput( ccl::Session *session, const std::string &name, const IECoreScenePreview::Renderer::Output *output )
			:	m_session( session )
		{
			// Driver

			session->scene = scene;

			session->progress.set_update_callback(function_bind(&BlenderSession::tag_redraw, this));
			session->progress.set_cancel_callback(function_bind(&BlenderSession::test_cancel, this));
			session->set_pause(session_pause);

			const char *typePtr = output->getType().c_str();
			const char *namePtr = output->getName().c_str();

			ParameterList driverParams( output->parameters() );
			driverParams.add( { "drivername", &typePtr, NSITypeString, 0, 1 } );
			driverParams.add( { "imagefilename", &namePtr, NSITypeString, 0, 1 } );

		}

	private :

		const char *scalarFormat( const IECoreScenePreview::Renderer::Output *output ) const
		{
			// Map old-school "quantize" setting to scalarformat. Maybe
			// we should have a standard more suitable for mapping to modern
			// renderers and display drivers? How would we request half outputs
			// for instance?
			const vector<int> quantize = parameter<vector<int>>( output->parameters(), "quantize", { 0, 0, 0, 0 } );
			if( quantize == vector<int>( { 0, 255, 0, 255 } ) )
			{
				return "uint8";
			}
			else if( quantize == vector<int>( { 0, 65536, 0, 65536 } ) )
			{
				return "uint16";
			}
			else
			{
				return "float";
			}
		}

		ccl::Session m_session;
		DelightHandle m_driverHandle;
		DelightHandle m_layerHandle;

};

IE_CORE_DECLAREPTR( CyclesOutput )

} // namespace

//////////////////////////////////////////////////////////////////////////
// DelightShader
//////////////////////////////////////////////////////////////////////////

namespace
{

class CyclesShader : public IECore::RefCounted
{

	public :

		CyclesShader( NSIContext_t context, const IECore::ObjectVector *shaderNetwork, DelightHandle::Ownership ownership )
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

		std::vector<DelightHandle> m_handles;

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

		ShaderCache( NSIContext_t context, DelightHandle::Ownership ownership )
			:	m_context( context ), m_ownership( ownership )
		{
		}

		// Can be called concurrently with other get() calls.
		DelightShaderPtr get( const IECore::ObjectVector *shader )
		{
			Cache::accessor a;
			m_cache.insert( a, shader ? shader->Object::hash() : MurmurHash() );
			if( !a->second )
			{
				if( shader )
				{
					a->second = new DelightShader( m_context, shader, m_ownership );
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
					a->second = new DelightShader( m_context, defaultSurfaceNetwork.get(), m_ownership );
				}
			}
			return a->second;
		}

		DelightShaderPtr defaultSurface()
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

		NSIContext_t m_context;
		DelightHandle::Ownership m_ownership;

		typedef tbb::concurrent_hash_map<IECore::MurmurHash, DelightShaderPtr> Cache;
		Cache m_cache;

};

IE_CORE_DECLAREPTR( ShaderCache )

} // namespace

//////////////////////////////////////////////////////////////////////////
// CyclesAttributes
//////////////////////////////////////////////////////////////////////////

namespace
{

// List of attributes where we look for an OSL shader, in order of priority.
// Although 3delight only really has surface shaders (lights are just emissive
// surfaces), we support "light" attributes as well for compatibility with
// other renderers and some specific workflows in Gaffer.
std::array<IECore::InternedString, 4> g_shaderAttributeNames = { {
	"osl:light",
	"light",
	"osl:surface",
	"surface",
} };

IECore::InternedString g_setsAttributeName( "sets" );

class CyclesAttributes : public IECoreScenePreview::Renderer::AttributesInterface
{

	public :

		CyclesAttributes( NSIContext_t context, const IECore::CompoundObject *attributes, ShaderCache *shaderCache, DelightHandle::Ownership ownership )
			:	m_handle( context, "attributes:" + attributes->Object::hash().toString(), ownership, "attributes", {} )
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

			ParameterList params;
			for( const auto &m : attributes->members() )
			{
				if( m.first == g_setsAttributeName )
				{
					if( const InternedStringVectorData *d = reportedCast<const InternedStringVectorData>( m.second.get(), "attribute", m.first ) )
					{
						if( d->readable().size() )
						{
							msg( Msg::Warning, "DelightRenderer", "Attribute \"sets\" not supported" );
						}
					}
				}
				else if( boost::starts_with( m.first.string(), "dl:" ) )
				{
					if( const Data *d = reportedCast<const IECore::Data>( m.second.get(), "attribute", m.first ) )
					{
						params.add( m.first.c_str() + 3, d );
					}
				}
				else if( boost::starts_with( m.first.string(), "user:" ) )
				{
					msg( Msg::Warning, "DelightRenderer", boost::format( "User attribute \"%s\" not supported" ) % m.first.string() );
				}
				else if( boost::contains( m.first.string(), ":" ) )
				{
					// Attribute for another renderer - ignore
				}
				else
				{
					msg( Msg::Warning, "DelightRenderer", boost::format( "Attribute \"%s\" not supported" ) % m.first.string() );
				}
			}

			NSISetAttribute( m_handle.context(), m_handle.name(), params.size(), params.data() );

			if( !m_shader )
			{
				m_shader = shaderCache->defaultSurface();
			}

			NSIConnect(
				context,
				m_shader->handle().name(), "",
				m_handle.name(), "surfaceshader",
				0, nullptr
			);
		}

		const DelightHandle &handle() const
		{
			return m_handle;
		}

	private :

		DelightHandle m_handle;
		ConstDelightShaderPtr m_shader;

};

IE_CORE_DECLAREPTR( DelightAttributes )

} // namespace

//////////////////////////////////////////////////////////////////////////
// AttributesCache
//////////////////////////////////////////////////////////////////////////

namespace
{

class AttributesCache : public IECore::RefCounted
{

	public :

		AttributesCache( NSIContext_t context, DelightHandle::Ownership ownership )
			:	m_context( context ), m_ownership( ownership ), m_shaderCache( new ShaderCache( context, ownership ) )
		{
		}

		// Can be called concurrently with other get() calls.
		DelightAttributesPtr get( const IECore::CompoundObject *attributes )
		{
			Cache::accessor a;
			m_cache.insert( a, attributes->Object::hash() );
			if( !a->second )
			{
				a->second = new DelightAttributes( m_context, attributes, m_shaderCache.get(), m_ownership );
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

		NSIContext_t m_context;
		DelightHandle::Ownership m_ownership;

		ShaderCachePtr m_shaderCache;

		typedef tbb::concurrent_hash_map<IECore::MurmurHash, DelightAttributesPtr> Cache;
		Cache m_cache;

};

IE_CORE_DECLAREPTR( AttributesCache )

} // namespace

//////////////////////////////////////////////////////////////////////////
// InstanceCache
//////////////////////////////////////////////////////////////////////////

namespace
{

class InstanceCache : public IECore::RefCounted
{

	public :

		InstanceCache( NSIContext_t context, DelightHandle::Ownership ownership )
			:	m_context( context ), m_ownership( ownership )
		{
		}

		// Can be called concurrently with other get() calls.
		DelightHandleSharedPtr get( const IECore::Object *object )
		{
			const IECore::MurmurHash hash = object->Object::hash();

			Cache::accessor a;
			m_cache.insert( a, hash );
			if( !a->second )
			{
				const std::string &name = "instance:" + hash.toString();
				if( NodeAlgo::convert( object, m_context, name.c_str() ) )
				{
					a->second = make_shared<DelightHandle>( m_context, name, m_ownership );
				}
				else
				{
					a->second = nullptr;
				}
			}

			return a->second;
		}

		// Can be called concurrently with other get() calls.
		DelightHandleSharedPtr get( const std::vector<const IECore::Object *> &samples, const std::vector<float> &times )
		{
			IECore::MurmurHash hash;
			for( std::vector<const IECore::Object *>::const_iterator it = samples.begin(), eIt = samples.end(); it != eIt; ++it )
			{
				(*it)->hash( hash );
			}
			for( std::vector<float>::const_iterator it = times.begin(), eIt = times.end(); it != eIt; ++it )
			{
				hash.append( *it );
			}

			Cache::accessor a;
			m_cache.insert( a, hash );

			if( !a->second )
			{
				const std::string &name = "instance:" + hash.toString();
				if( NodeAlgo::convert( samples, times, m_context, name.c_str() ) )
				{
					a->second = make_shared<DelightHandle>( m_context, name, m_ownership );
				}
				else
				{
					a->second = nullptr;
				}
			}

			return a->second;
		}

		// Must not be called concurrently with anything.
		void clearUnused()
		{
			vector<IECore::MurmurHash> toErase;
			for( Cache::iterator it = m_cache.begin(), eIt = m_cache.end(); it != eIt; ++it )
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
				m_cache.erase( *it );
			}
		}

	private :

		NSIContext_t m_context;
		DelightHandle::Ownership m_ownership;

		typedef tbb::concurrent_hash_map<IECore::MurmurHash, DelightHandleSharedPtr> Cache;
		Cache m_cache;

};

IE_CORE_DECLAREPTR( InstanceCache )

} // namespace

//////////////////////////////////////////////////////////////////////////
// DelightObject
//////////////////////////////////////////////////////////////////////////

namespace
{

class CyclesObject : public IECoreScenePreview::Renderer::ObjectInterface
{

	public :

		CyclesObject( ccl::scene scene, const std::string &name, DelightHandleSharedPtr instance, DelightHandle::Ownership ownership )
			:	m_transformHandle( context, name, ownership, "transform", {} ), m_instance( instance ), m_haveTransform( false )
		{
			NSIConnect(
				m_transformHandle.context(),
				m_instance->name(), "",
				m_transformHandle.name(), "objects",
				0, nullptr
			);

			NSIConnect(
				m_transformHandle.context(),
				m_transformHandle.name(), "",
				NSI_SCENE_ROOT, "objects",
				0, nullptr
			);
		}

		void transform( const Imath::M44f &transform ) override
		{
			if( transform == M44f() && !m_haveTransform )
			{
				return;
			}

			M44d m( transform );
			NSIParam_t param = {
				"transformationmatrix",
				m.getValue(),
				NSITypeDoubleMatrix,
				0, 1, // array length, count
				0 // flags
			};
			NSISetAttribute( m_transformHandle.context(), m_transformHandle.name(), 1, &param );

			m_haveTransform = true;
		}

		void transform( const std::vector<Imath::M44f> &samples, const std::vector<float> &times ) override
		{
			if( m_haveTransform )
			{
				NSIDeleteAttribute( m_transformHandle.context(), m_transformHandle.name(), "transformationmatrix" );
			}

			for( size_t i = 0, e = samples.size(); i < e; ++i )
			{
				M44d m( samples[i] );
				NSIParam_t param = {
					"transformationmatrix",
					m.getValue(),
					NSITypeDoubleMatrix,
					0, 1, // array length, count
					0 // flags
				};
				NSISetAttributeAtTime( m_transformHandle.context(), m_transformHandle.name(), times[i], 1, &param );
			}

			m_haveTransform = true;
		}

		bool attributes( const IECoreScenePreview::Renderer::AttributesInterface *attributes ) override
		{
			if( m_attributes )
			{
				if( attributes == m_attributes )
				{
					return true;
				}

				NSIDisconnect(
					m_transformHandle.context(),
					m_attributes->handle().name(), "",
					m_transformHandle.name(), "geometryattributes"
				);
			}

			m_attributes = static_cast<const DelightAttributes *>( attributes );
			NSIConnect(
				m_transformHandle.context(),
				m_attributes->handle().name(), "",
				m_transformHandle.name(), "geometryattributes",
				0, nullptr

			);
			return true;
		}

	private :

		const DelightHandle m_transformHandle;
		// We keep a reference to the instance and attributes so that they
		// remain alive for at least as long as the object does.
		ConstDelightAttributesPtr m_attributes;
		DelightHandleSharedPtr m_instance;

		bool m_haveTransform;

};

} // namespace

//////////////////////////////////////////////////////////////////////////
// CyclesRenderer
//////////////////////////////////////////////////////////////////////////

namespace
{

IECore::InternedString g_frameOptionName( "frame" );
IECore::InternedString g_cameraOptionName( "camera" );
IECore::InternedString g_sampleMotionOptionName( "sampleMotion" );
IECore::InternedString g_deviceOptionName( "ccl:device" );
IECore::InternedString g_shadingsystemOptionName( "ccl:shadingsystem" );

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

IECore::InternedString g_bvhTypeOptionName( "ccl:scene:bvh_type" );
IECore::InternedString g_bvhLayoutOptionName( "ccl:scene:bvh_layout" );
IECore::InternedString g_useBvhSpatialSplitOptionName( "ccl:scene:use_bvh_spatial_split" );
IECore::InternedString g_useBvhUnalignedNodesOptionName( "ccl:scene:use_bvh_unaligned_nodes" );
IECore::InternedString g_useBvhTimeStepsOptionName( "ccl:scene:use_bvh_time_steps" );
IECore::InternedString g_persistentDataOptionName( "ccl:scene:persistent_data" );
IECore::InternedString g_textureLimitOptionName( "ccl:scene:texture_limit" );

IE_CORE_FORWARDDECLARE( CyclesRenderer )

class CyclesRenderer final : public IECoreScenePreview::Renderer
{

	public :

		CyclesRenderer( RenderType renderType, const std::string &fileName )
			:	m_renderType( renderType ),
				m_session_params( ccl::SessionParams() ),
				m_scene_params( ccl::SceneParams() ),
				m_session_params_dirty( false ),
				m_scene_params_dirty( false ),
				m_device_name( "CPU" ),
				m_shadingsystem_name( "OSL" )
		{
			// Session Defaults
			m_session_params.display_buffer_linear = true;

			if( m_shadingsystem_name == "OSL" )
				m_session_params.shadingsystem = ccl::SHADINGSYSTEM_OSL;
			else if( m_shadingsystem_name == "SVM" )
				m_session_params.shadingsystem = ccl::SHADINGSYSTEM_SVM;

			/*
			ccl::vector<ccl::DeviceType>& device_types = ccl::Device::available_types();
			ccl::foreach(ccl::DeviceType type, device_types) {
				if(device_names != "")
					device_names += ", ";

				device_names += Device::string_from_type(type);
			}
			*/

			ccl::DeviceType device_type = ccl::Device::type_from_string( m_device_name.c_str() );
			ccl::vector<ccl::DeviceInfo>& devices = ccl::Device::available_devices();
			bool device_available = false;
			for(ccl::DeviceInfo& device : devices) {
				if(device_type == device.type) {
					m_session_params.device = device;
					device_available = true;
					break;
				}
			}

			m_session = new ccl::Session( m_session_params );

			m_scene_params.shadingsystem = m_session_params.shadingsystem;
			//m_scene = new ccl::Scene( m_scene_params, m_session_params.device );
			//m_instanceCache = new InstanceCache( m_context, ownership() );
			//m_attributesCache = new AttributesCache( m_context, ownership() );
		}

		~CyclesRenderer() override
		{
			if( m_scene )
			{
				delete m_scene;
				m_scene = nullptr;
			}

			if( m_session )
			{
				delete m_session;
				m_session = nullptr;
			}
			// Delete nodes we own before we destroy context
			//stop();
			//m_attributesCache.reset();
			//m_instanceCache.reset();
			//m_outputs.clear();
			//m_defaultCamera.reset();
			//NSIEnd( m_context );
		}

		void option( const IECore::InternedString &name, const IECore::Object *value ) override
		{
			ccl::SessionParams new_session_params = ccl::SessionParams();
			new_session_params = m_session_params;
			ccl::SessionParams new_scene_params = ccl::SceneParams();
			new_scene_params = m_scene_params;

			if( name == g_frameOptionName )
			{
				m_frame = 1;
				if( value )
				{
					if( const IntData *data = reportedCast<const IntData>( value, "option", name ) )
					{
						m_frame = data->readable();
					}
				}
			}
			else if( name == g_cameraOptionName )
			{
				if( value )
				{
					if( const StringData *data = reportedCast<const StringData>( value, "option", name ) )
					{
						if( m_camera != data->readable() )
						{
							//stop();
							m_camera = data->readable();
						}
					}
					else
					{
						m_camera = "";
					}
				}
				else
				{
					m_camera = "";
				}
			}
			else if( name == g_sampleMotionOptionName )
			{
				ccl::Integrator *integrator = m_scene->integrator;
				ccl::SocketType *input = integrator->node_type->find_input( "motion_blur" );
				if( value && input )
				{
					if( const Data *data = reportedCast<const Data>( value, "option", name ) )
					{
						setSocket( integrator, &input, value );
					}
					else
					{
						integrator->set_default_value( &input );
					}
				}
				else if( input )
				{
					integrator->set_default_value( &input );
				}
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
							if( m_device_name != data->readable() )
							{
								//stop();
								m_device_name = data->readable();
							}
						}
						else
						{
							m_device_name = "CPU";
							IECore::msg( IECore::Msg::Warning, "CyclesRenderer::option", boost::format( "Unknown value \"%s\" for option \"%s\"." ) % m_device_name, name.string() );
						}
					}
					else if( name == g_shadingsystemOptionName )
					{
						if( const StringData *data = reportedCast<const StringData>( value, "option", name ) )
						{
							if( m_shadingsystem_name != data->readable() )
							{
								//stop();
								m_shadingsystem_name = data->readable();
							}
						}
						else
						{
							m_shadingsystem_name = "OSL";
						}
						if( m_shadingsystem_name == "OSL" )
						{
							new_session_params.shadingsystem = ccl::SHADINGSYSTEM_OSL;
							new_scene_params.shadingsystem   = ccl::SHADINGSYSTEM_OSL;
						}
						else if( m_shadingsystem_name == "SVM" )
						{
							new_session_params.shadingsystem = ccl::SHADINGSYSTEM_SVM;
							new_scene_params.shadingsystem   = ccl::SHADINGSYSTEM_SVM;
						}
						else
						{
							IECore::msg( IECore::Msg::Warning, "CyclesRenderer::option", boost::format( "Unknown value \"%s\" for option \"%s\"." ) % m_shadingsystem_name.string(), name.string() );
						}
					}
					if( name == g_backgroundOptionName )
					{
						if ( const BoolData *data = reportedCast<const BoolData>( value, "option", name ) )
							new_session_params.background = data->readable();
					}
					else if( name == g_progressiveRefineOptionName )
					{
						if ( const BoolData *data = reportedCast<const BoolData>( value, "option", name ) )
							new_session_params.progressive_refine = data->readable();
					}
					else if( name == g_progressiveOptionName )
					{
						if ( const BoolData *data = reportedCast<const BoolData>( value, "option", name ) )
							new_session_params.progressive = data->readable();
					}
					else if( name == g_experimentalOptionName )
					{
						if ( const BoolData *data = reportedCast<const BoolData>( value, "option", name ) )
							new_session_params.experimental = data->readable();
					}
					else if( name == g_samplesOptionName )
					{
						if ( const IntData *data = reportedCast<const IntData>( value, "option", name ) )
							new_session_params.samples = data->readable();
					}
					else if( name == g_tileSizeOptionName )
					{
						if ( const V2iData *data = reportedCast<const IntData>( value, "option", name ) )
						{
							auto d = data->readable();
							new_session_params.tile_size = ccl::make_int2( d.x, d.y );
						}
					}
					else if( name == g_tileOrderOptionName )
					{
						if ( const StringData *data = reportedCast<const StringData>( value, "option", name ) )
						{
							const string optionName& = data->readable();
							if( optionName == "center" )
								new_session_params.tile_order = TILE_CENTER;
							else if( optionName == "right_To_left" )
								new_session_params.tile_order = TILE_RIGHT_TO_LEFT;
							else if( optionName == "left_to_right" )
								new_session_params.tile_order = TILE_LEFT_TO_RIGHT;
							else if( optionName == "top_to_bottom" )
								new_session_params.tile_order = TILE_TOP_TO_BOTTOM;
							else if( optionName == "bottom_to_top" )
								new_session_params.tile_order = TILE_BOTTOM_TO_TOP;
							else if( optionName == "hilbert_spiral" )
								new_session_params.tile_order = TILE_HILBERT_SPIRAL;
							else
								IECore::msg( IECore::Msg::Warning, "CyclesRenderer::option", boost::format( "Unknown value \"%s\" for option \"%s\"." ) % optionName.string(), name.string() );
						}
					}
					else if( name == g_startResolutionOptionName )
					{
						if ( const IntData *data = reportedCast<const IntData>( value, "option", name ) )
							new_session_params.start_resolution = data->readable();
					}
					else if( name == g_pixelSizeOptionName )
					{
						if ( const IntData *data = reportedCast<const IntData>( value, "option", name ) )
							new_session_params.pixel_size = data->readable();
					}
					else if( name == g_threadsOptionName )
					{
						if ( const IntData *data = reportedCast<const IntData>( value, "option", name ) )
							new_session_params.threads = data->readable();
					}
					else if( name == g_displayBufferLinearOptionName )
					{
						if ( const BoolData *data = reportedCast<const BoolData>( value, "option", name ) )
							new_session_params.display_buffer_linear = data->readable();
					}
					else if( name == g_useDenoisingOptionName )
					{
						if ( const BoolData *data = reportedCast<const BoolData>( value, "option", name ) )
							new_session_params.use_denoising = data->readable();
					}
					else if( name == g_denoisingRadiusOptionName )
					{
						if ( const IntData *data = reportedCast<const IntData>( value, "option", name ) )
							new_session_params.denoising_radius = data->readable();
					}
					else if( name == g_denoisingStrengthOptionName )
					{
						if ( const FloatData *data = reportedCast<const FloatData>( value, "option", name ) )
							new_session_params.denoising_strength = data->readable();
					}
					else if( name == g_denoisingFeatureStrengthOptionName )
					{
						if ( const FloatData *data = reportedCast<const FloatData>( value, "option", name ) )
							new_session_params.denoising_feature_strength = data->readable();
					}
					else if( name == g_denoisingRelativePcaOptionName )
					{
						if ( const BoolData *data = reportedCast<const BoolData>( value, "option", name ) )
							new_session_params.denoising_relative_pca = data->readable();
					}
					else if( name == g_cancelTimeoutOptionName )
					{
						if ( const FloatData *data = reportedCast<const FloatData>( value, "option", name ) )
							new_session_params.cancel_timeout = (double)data->readable();
					}
					else if( name == g_resetTimeoutOptionName )
					{
						if ( const FloatData *data = reportedCast<const FloatData>( value, "option", name ) )
							new_session_params.reset_timeout = (double)data->readable();
					}
					else if( name == g_textTimeoutOptionName )
					{
						if ( const FloatData *data = reportedCast<const FloatData>( value, "option", name ) )
							new_session_params.text_timeout = (double)data->readable();
					}
					else if( name == g_progressiveUpdateTimeoutOptionName )
					{
						if ( const FloatData *data = reportedCast<const FloatData>( value, "option", name ) )
							new_session_params.progressive_update_timeout = (double)data->readable();
					}
					else
					{
						IECore::msg( IECore::Msg::Warning, "CyclesRenderer::option", boost::format( "Unknown option \"%s\"." ) % name.string() );
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
							new_scene_params.bvh_type = (ccl::SceneParams::BVHType)data->readable();
					}
					else if( name == g_bvhLayoutOptionName )
					{
						if ( const IntData *data = reportedCast<const IntData>( value, "option", name ) )
							new_scene_params.bvh_layout = (ccl::SceneParams::BVHLayout)data->readable();
					}
					else if( name == g_useBvhSpatialSplitOptionName )
					{
						if ( const BoolData *data = reportedCast<const BoolData>( value, "option", name ) )
							new_scene_params.use_bvh_spatial_split = data->readable();
					}
					else if( name == g_useBvhUnalignedNodesOptionName )
					{
						if ( const BoolData *data = reportedCast<const BoolData>( value, "option", name ) )
							new_scene_params.use_bvh_unaligned_nodes = data->readable();
					}
					else if( name == g_useBvhTimeStepsOptionName )
					{
						if ( const IntData *data = reportedCast<const IntData>( value, "option", name ) )
							new_scene_params.use_bvh_time_steps = data->readable();
					}
					else if( name == g_persistentDataOptionName )
					{
						if ( const BoolData *data = reportedCast<const BoolData>( value, "option", name ) )
							new_scene_params.persistent_data = data->readable();
					}
					else if( name == g_textureLimitOptionName )
					{
						if ( const IntData *data = reportedCast<const IntData>( value, "option", name ) )
							new_scene_params.texture_limit = data->readable();
					}
					else
					{
						IECore::msg( IECore::Msg::Warning, "CyclesRenderer::option", boost::format( "Unknown option \"%s\"." ) % name.string() );
					}
				}
			}
			// The last 3 are subclassed internally from ccl::Node so treat their params like Cycles sockets
			else if( boost::starts_with( name.string(), "ccl:background:" ) )
			{
				ccl::Background *background = m_scene->background;
				ccl::SocketType *input = background->node_type->find_input( name.c_str() + 15 );
				if( value && input )
				{
					if( const Data *data = reportedCast<const Data>( value, "option", name ) )
					{
						setSocket( background, &input, value );
					}
					else
					{
						background->set_default_value( &input );
					}
				}
				else if( input )
				{
					background->set_default_value( &input );
				}
			}
			else if( boost::starts_with( name.string(), "ccl:film:" ) )
			{
				ccl::Film *film = m_scene->film;
				ccl::SocketType *input = film->node_type->find_input( name.c_str() + 9 );
				if( value && input )
				{
					if( const Data *data = reportedCast<const Data>( value, "option", name ) )
					{
						setSocket( film, &input, value );
					}
					else
					{
						film->set_default_value( &input );
					}
				}
				else if( input )
				{
					film->set_default_value( &input );
				}
			}
			else if( boost::starts_with( name.string(), "ccl:integrator:" ) )
			{
				ccl::Integrator *integrator = m_scene->integrator;
				ccl::SocketType *input = integrator->node_type->find_input( name.c_str() + 15 );
				if( value && input )
				{
					if( const Data *data = reportedCast<const Data>( value, "option", name ) )
					{
						setSocket( integrator, &input, value );
					}
					else
					{
						integrator->set_default_value( &input );
					}
				}
				else if( input )
				{
					integrator->set_default_value( &input );
				}
			}
			else if( boost::starts_with( name.string(), "ccl:" ) )
			{
				IECore::msg( IECore::Msg::Warning, "CyclesRenderer::option", boost::format( "Unknown option \"%s\"." ) % name.string() );
			}
			else if( boost::starts_with( name.string(), "user:" ) )
			{
				msg( Msg::Warning, "CyclesRenderer::option", boost::format( "User option \"%s\" not supported" ) % name.string() );
			}
			else if( boost::contains( name.c_str(), ":" ) )
			{
				// Ignore options prefixed for some other renderer.
			}
			else
			{
				IECore::msg( IECore::Msg::Warning, "CyclesRenderer::option", boost::format( "Unknown option \"%s\"." ) % name.string() );
			}

			// Actually apply the new params if they've changed
			if( m_session_params->modified( &new_session_params ) )
			{
				m_session_params_dirty = true;
				m_session_params = new_session_params;
			}

			if( m_scene_params->modified( &new_scene_params ) )
			{
				m_scene_params_dirty = true;
				m_scene_params = new_scene_params;
			}
		}

		void output( const IECore::InternedString &name, const Output *output ) override
		{
			// 3Delight crashes if we don't stop the render before
			// modifying the output chain.
			stop();
			m_outputs.erase( name );
			if( !output )
			{
				return;
			}

			m_outputs[name] = new DelightOutput( m_context, name, output, ownership() );
		}

		Renderer::AttributesInterfacePtr attributes( const IECore::CompoundObject *attributes ) override
		{
			return m_attributesCache->get( attributes );
		}

		ObjectInterfacePtr camera( const std::string &name, const IECoreScene::Camera *camera, const AttributesInterface *attributes ) override
		{
			const string objectHandle = "camera:" + name;
			ccl::Camera *ccl_camera = NodeAlgo::convert( camera, objectHandle.c_str() )
			if( !ccl_camera )
			{
				return nullptr;
			}
			else if( m_scene->camera->modified( ccl_camera ) )

			// Because we can't query the contents of an NSI scene, we need to manually
			// keep a track of which cameras are in existence, for use in updateCamera().
			// We do that by storing their names in the m_cameras set.
			{
				tbb::spin_mutex::scoped_lock lock( m_cameraSetMutex );
				m_cameraSet.insert( objectHandle );
			}

			DelightHandleSharedPtr cameraHandle(
				new DelightHandle( m_context, objectHandle.c_str(), ownership() ),
				// 3delight doesn't allow edits to cameras or outputs while the
				// render is running, so we must use a custom deleter to stop
				// the render just before the camera is deleted. This also allows
				// us to remove the camera from the m_cameras set.
				boost::bind( &DelightRenderer::cameraDeleter, DelightRendererPtr( this ), ::_1 )
			);

			ObjectInterfacePtr result = new DelightObject(
				m_context,
				name,
				cameraHandle,
				ownership()
			);
			result->attributes( attributes );
			return result;
		}

		ObjectInterfacePtr light( const std::string &name, const IECore::Object *object, const AttributesInterface *attributes ) override
		{
			return this->object( name, object, attributes );
		}

		Renderer::ObjectInterfacePtr object( const std::string &name, const IECore::Object *object, const AttributesInterface *attributes ) override
		{
			DelightHandleSharedPtr instance = m_instanceCache->get( object );
			if( !instance )
			{
				return nullptr;
			}

			ObjectInterfacePtr result = new DelightObject( m_context, name, instance, ownership() );
			result->attributes( attributes );
			return result;
		}

		ObjectInterfacePtr object( const std::string &name, const std::vector<const IECore::Object *> &samples, const std::vector<float> &times, const AttributesInterface *attributes ) override
		{
			DelightHandleSharedPtr instance = m_instanceCache->get( samples, times );
			if( !instance )
			{
				return nullptr;
			}

			ObjectInterfacePtr result = new DelightObject( m_context, name, instance, ownership() );
			result->attributes( attributes );
			return result;
		}

		void render() override
		{
			m_instanceCache->clearUnused();
			m_attributesCache->clearUnused();

			if( m_rendering )
			{
				const char *synchronize = "synchronize";
				vector<NSIParam_t> params = {
					{ "action", &synchronize, NSITypeString, 0, 1 }
				};
				NSIRenderControl(
					m_context,
					params.size(), params.data()
				);
				return;
			}

			updateCamera();

			const int one = 1;
			const char *start = "start";
			vector<NSIParam_t> params = {
				{ "action", &start, NSITypeString, 0, 1 },
				{ "frame", &m_frame, NSITypeInteger, 0, 1 }
			};

			if( m_renderType == Interactive )
			{
				params.push_back( { "interactive", &one, NSITypeInteger, 0, 1 } );
			}

			NSIRenderControl(
				m_context,
				params.size(), params.data()
			);

			m_rendering = true;

			if( m_renderType == Interactive )
			{
				return;
			}

			const char *wait = "wait";
			params = {
				{ "action", &wait, NSITypeString, 0, 1 }
			};

			NSIRenderControl(
				m_context,
				params.size(), params.data()
			);

			m_rendering = false;
		}

		void pause() override
		{
			// In theory we could use NSIRenderControl "suspend"
			// here, but despite documenting it, 3delight does not
			// support it. Instead we let 3delight waste cpu time
			// while we make our edits.
		}

	private :

		DelightHandle::Ownership ownership() const
		{
			return m_renderType == Interactive ? DelightHandle::Owned : DelightHandle::Unowned;
		}

		void stop()
		{
			if( !m_rendering )
			{
				return;
			}

			const char *stop = "stop";
			ParameterList params = {
				{ "action", &stop, NSITypeString, 0, 1 }
			};

			NSIRenderControl(
				m_context,
				params.size(), params.data()
			);

			m_rendering = false;
		}

		void updateCamera()
		{
			// The NSI handle for the camera that we've been told to use.
			std::string cameraHandle = "camera:" + m_camera;

			// If we're in an interactive render, then disconnect the
			// outputs from any secondary cameras.
			if( m_renderType == Interactive )
			{
				for( auto &camera : m_cameraSet )
				{
					if( camera != cameraHandle )
					{
						for( const auto &output : m_outputs )
						{
							NSIDisconnect(
								m_context,
								output.second->layerHandle().name(), "",
								camera.c_str(), "outputlayers"
							);
						}
					}
				}
			}

			// Check that the camera we want to use exists,
			// and if not, create a default one.

			if( m_cameraSet.find( cameraHandle ) == m_cameraSet.end() )
			{
				if( !m_camera.empty() )
				{
					IECore::msg(
						IECore::Msg::Warning, "DelightRenderer",
						boost::format( "Camera \"%s\" does not exist" ) % m_camera
					);
				}
				cameraHandle = "ieCoreDelight:defaultCamera";
				m_defaultCamera = DelightHandle(
					m_context, cameraHandle, ownership(),
					"orthographiccamera"
				);

				NSIConnect(
					m_context,
					cameraHandle.c_str(), "",
					NSI_SCENE_ROOT, "objects",
					0, nullptr
				);
			}
			else
			{
				m_defaultCamera.reset();
			}

			// Set the oversampling, and connect the outputs up to the camera

			ParameterList cameraParameters = {
				{ "oversampling", &m_oversampling, NSITypeInteger, 0, 1 }
			};
			NSISetAttribute( m_context, cameraHandle.c_str(), cameraParameters.size(), cameraParameters.data() );

			for( const auto &output : m_outputs )
			{
				NSIConnect(
					m_context,
					output.second->layerHandle().name(), "",
					cameraHandle.c_str(), "outputlayers",
					0, nullptr
				);
			}
		}

		SharedCSessionPtr m_session;
		SharedCScenePtr m_scene;
		ccl::SessionParams m_session_params;
		ccl::SceneParams m_scene_params;
		std::string m_device;
		RenderType m_renderType;

		int m_frame;
		string m_camera;
		int m_oversampling;

		bool m_session_params_dirty;
		bool m_scene_params_dirty;

		bool m_rendering = false;

		InstanceCachePtr m_instanceCache;
		AttributesCachePtr m_attributesCache;

		unordered_map<InternedString, ConstDelightOutputPtr> m_outputs;

		typedef set<string> CameraSet;
		CameraSet m_cameraSet;
		tbb::spin_mutex m_cameraSetMutex;

		DelightHandle m_defaultCamera;

		// Registration with factory

		static Renderer::TypeDescription<CyclesRenderer> g_typeDescription;

};

IECoreScenePreview::Renderer::TypeDescription<CyclesRenderer> CyclesRenderer::g_typeDescription( "Cycles" );

} // namespace
