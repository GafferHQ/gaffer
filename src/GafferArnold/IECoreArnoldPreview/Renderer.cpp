//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

#include <thread>
#include <memory>

#include "tbb/concurrent_vector.h"
#include "tbb/concurrent_unordered_map.h"
#include "tbb/spin_mutex.h"

#include "boost/format.hpp"
#include "boost/algorithm/string.hpp"
#include "boost/algorithm/string/predicate.hpp"
#include "boost/algorithm/string/join.hpp"
#include "boost/container/flat_map.hpp"
#include "boost/filesystem/operations.hpp"
#include "boost/bind.hpp"
#include "boost/lexical_cast.hpp"

#include "IECore/MessageHandler.h"
#include "IECore/Camera.h"
#include "IECore/Transform.h"
#include "IECore/VectorTypedData.h"
#include "IECore/SimpleTypedData.h"
#include "IECore/ObjectVector.h"
#include "IECore/Shader.h"
#include "IECore/MeshPrimitive.h"
#include "IECore/CurvesPrimitive.h"
#include "IECore/ExternalProcedural.h"

#include "IECoreArnold/ParameterAlgo.h"
#include "IECoreArnold/CameraAlgo.h"
#include "IECoreArnold/NodeAlgo.h"
#include "IECoreArnold/UniverseBlock.h"

#include "Gaffer/StringAlgo.h"

#include "GafferScene/Private/IECoreScenePreview/Renderer.h"
#include "GafferScene/Private/IECoreScenePreview/Procedural.h"

#include "GafferArnold/Private/IECoreArnoldPreview/ShaderAlgo.h"

using namespace std;
using namespace boost::filesystem;
using namespace IECoreArnold;
using namespace IECoreArnoldPreview;

//////////////////////////////////////////////////////////////////////////
//
// Namespacing Utilities
// =====================
//
// In Arnold 4 all nodes are in a global namespace, so there can easily be
// clashes between names generated from different procedurals. We must
// therefore make sure we prefix such names ourselves to keep them unique.
// In Arnold 5, nodes are created with a parent node which provides a
// namespace, so we won't need to prefix them, but we will instead need
// to provide a parent. The utilities below do the namespacing needed for
// Arnold 4, but designed such that when we move to Arnold 5 we'll just be
// able to remove the utilities and replace them with direct calls to
// AiNode/NodeAlgo etc.
//
//////////////////////////////////////////////////////////////////////////

namespace
{

std::string namespacedName( const std::string &nodeName, const AtNode *parentNode )
{
	if( parentNode )
	{
		return AiNodeGetName( parentNode ) + string( ":" ) + nodeName;
	}
	return nodeName;
}

AtNode *namespacedNode( const std::string &nodeType, const std::string &nodeName, const AtNode *parentNode = nullptr )
{
	AtNode *node = AiNode( nodeType.c_str() );
	if( node )
	{
		AiNodeSetStr( node, "name", namespacedName( nodeName, parentNode ).c_str() );
	}
	return node;
}

AtNode *namespacedNodeAlgoConvert( const IECore::Object *object, const std::string &nodeName, const AtNode *parentNode )
{
	AtNode *node = NodeAlgo::convert( object );
	if( node )
	{
		AiNodeSetStr( node, "name", namespacedName( nodeName, parentNode ).c_str() );
	}
	return node;
}

AtNode *namespacedNodeAlgoConvert( const std::vector<const IECore::Object *> &samples, const std::vector<float> &times, const std::string &nodeName, const AtNode *parentNode )
{
	AtNode *node = NodeAlgo::convert( samples, times );
	if( node )
	{
		AiNodeSetStr( node, "name", namespacedName( nodeName, parentNode ).c_str() );
	}
	return node;
}

AtNode *namespacedCameraAlgoConvert( const IECore::Camera *camera, const std::string &name, const AtNode *parentNode )
{
	AtNode *node = CameraAlgo::convert( camera );
	if( node )
	{
		AiNodeSetStr( node, "name", namespacedName( name, parentNode ).c_str() );
	}
	return node;
}

std::vector<AtNode *> namespacedShaderAlgoConvert( const IECore::ObjectVector *shaderNetwork, const std::string &namePrefix, const AtNode *parentNode )
{
	return ShaderAlgo::convert( shaderNetwork, namespacedName( namePrefix, parentNode ) );
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// Utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

typedef std::shared_ptr<AtNode> SharedAtNodePtr;
typedef bool (*NodeDeleter)( AtNode *);

bool nullNodeDeleter( AtNode *node )
{
	return false;
}

NodeDeleter nodeDeleter( IECoreScenePreview::Renderer::RenderType renderType )
{
	if( renderType == IECoreScenePreview::Renderer::Interactive )
	{
		// As interactive edits add/remove objects and shaders, we want to
		// destroy any AtNodes that are no longer needed.
		return AiNodeDestroy;
	}
	else
	{
		// Edits are not possible, so we have no need to delete nodes except
		// when shutting the renderer down. `AiEnd()` (as called by ~UniverseBlock)
		// automatically destroys all nodes and is _much_ faster than destroying
		// them one by one with AiNodeDestroy. So we use a null deleter so that we
		// don't try to destroy the nodes ourselves, and rely entirely on `AiEnd()`.
		return nullNodeDeleter;
	}
}

template<typename T>
T *reportedCast( const IECore::RunTimeTyped *v, const char *type, const IECore::InternedString &name )
{
	T *t = IECore::runTimeCast<T>( v );
	if( t )
	{
		return t;
	}

	IECore::msg( IECore::Msg::Warning, "IECoreArnold::Renderer", boost::format( "Expected %s but got %s for %s \"%s\"." ) % T::staticTypeName() % v->typeName() % type % name.c_str() );
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

std::string formatHeaderParameter( const std::string name, const IECore::Data *data )
{
	if( const IECore::BoolData *boolData = IECore::runTimeCast<const IECore::BoolData>( data ) )
	{
		return boost::str( boost::format( "int '%s' %i" ) % name % int(boolData->readable()) );
	}
	else if( const IECore::FloatData *floatData = IECore::runTimeCast<const IECore::FloatData>( data ) )
	{
		return boost::str( boost::format( "float '%s' %f" ) % name % floatData->readable() );
	}
	else if( const IECore::IntData *intData = IECore::runTimeCast<const IECore::IntData>( data ) )
	{
		return boost::str( boost::format( "int '%s' %i" ) % name % intData->readable() );
	}
	else if( const IECore::StringData *stringData = IECore::runTimeCast<const IECore::StringData>( data ) )
	{
		return boost::str( boost::format( "string '%s' %s" ) % name % stringData->readable() );
	}
	else if( const IECore::V2iData *v2iData = IECore::runTimeCast<const IECore::V2iData>( data ) )
	{
		return boost::str( boost::format( "string '%s' %s" ) % name % v2iData->readable() );
	}
	else if( const IECore::V3iData *v3iData = IECore::runTimeCast<const IECore::V3iData>( data ) )
	{
		return boost::str( boost::format( "string '%s' %s" ) % name % v3iData->readable() );
	}
	else if( const IECore::V2fData *v2fData = IECore::runTimeCast<const IECore::V2fData>( data ) )
	{
		return boost::str( boost::format( "string '%s' %s" ) % name % v2fData->readable() );
	}
	else if( const IECore::V3fData *v3fData = IECore::runTimeCast<const IECore::V3fData>( data ) )
	{
		return boost::str( boost::format( "string '%s' %s" ) % name % v3fData->readable() );
	}
	else if( const IECore::Color3fData *c3fData = IECore::runTimeCast<const IECore::Color3fData>( data ) )
	{
		return boost::str( boost::format( "string '%s' %s" ) % name % c3fData->readable() );
	}
	else if( const IECore::Color4fData *c4fData = IECore::runTimeCast<const IECore::Color4fData>( data ) )
	{
		return boost::str( boost::format( "string '%s' %s" ) % name % c4fData->readable() );
	}
	else
	{
		IECore::msg( IECore::Msg::Warning, "IECoreArnold::Renderer", boost::format( "Cannot convert data \"%s\" of type \"%s\"." ) % name % data->typeName() );
		return "";
	}
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// ArnoldRendererBase forward declaration
//////////////////////////////////////////////////////////////////////////

namespace
{

class ArnoldGlobals;
class Instance;
IE_CORE_FORWARDDECLARE( ShaderCache );
IE_CORE_FORWARDDECLARE( InstanceCache );

/// This class implements the basics of outputting attributes
/// and objects to Arnold, but is not a complete implementation
/// of the renderer interface. It is subclassed to provide concrete
/// implementations suitable for use as the master renderer or
/// for use in procedurals.
class ArnoldRendererBase : public IECoreScenePreview::Renderer
{

	public :

		~ArnoldRendererBase() override;

		Renderer::AttributesInterfacePtr attributes( const IECore::CompoundObject *attributes ) override;

		ObjectInterfacePtr camera( const std::string &name, const IECore::Camera *camera, const AttributesInterface *attributes ) override;
		ObjectInterfacePtr light( const std::string &name, const IECore::Object *object, const AttributesInterface *attributes ) override;
		Renderer::ObjectInterfacePtr object( const std::string &name, const IECore::Object *object, const AttributesInterface *attributes ) override;
		ObjectInterfacePtr object( const std::string &name, const std::vector<const IECore::Object *> &samples, const std::vector<float> &times, const AttributesInterface *attributes ) override;

	protected :

		ArnoldRendererBase( NodeDeleter nodeDeleter, AtNode *parentNode = nullptr );

		NodeDeleter m_nodeDeleter;
		ShaderCachePtr m_shaderCache;
		InstanceCachePtr m_instanceCache;

	private :

		AtNode *m_parentNode;

};

} // namespace

//////////////////////////////////////////////////////////////////////////
// ArnoldOutput
//////////////////////////////////////////////////////////////////////////

namespace
{

class ArnoldOutput : public IECore::RefCounted
{

	public :

		ArnoldOutput( const IECore::InternedString &name, const IECoreScenePreview::Renderer::Output *output, NodeDeleter nodeDeleter )
		{
			// Create a driver node and set its parameters.

			std::string driverNodeType = output->getType();
			if( AiNodeEntryGetType( AiNodeEntryLookUp( driverNodeType.c_str() ) ) != AI_NODE_DRIVER )
			{
				// Automatically map tiff to driver_tiff and so on, to provide a degree of
				// compatibility with existing renderman driver names.
				std::string prefixedType = "driver_" + driverNodeType;
				if( AiNodeEntryLookUp( prefixedType.c_str() ) )
				{
					driverNodeType = prefixedType;
				}
			}

			const std::string driverNodeName = boost::str( boost::format( "ieCoreArnold:display:%s" ) % name.string() );
			m_driver.reset(
				namespacedNode( driverNodeType.c_str(), driverNodeName.c_str() ),
				nodeDeleter
			);
			if( !m_driver )
			{
				throw IECore::Exception( boost::str( boost::format( "Unable to create output driver of type \"%s\"" ) % driverNodeType ) );
			}

			if( const AtParamEntry *fileNameParameter = AiNodeEntryLookUpParameter( AiNodeGetNodeEntry( m_driver.get() ), "filename" ) )
			{
				AiNodeSetStr( m_driver.get(), AiParamGetName( fileNameParameter ), output->getName().c_str() );
			}

			IECore::StringVectorDataPtr customAttributesData;
			// we need to do the const_cast here because there's not const parametersData() in cortex.
			if( const IECore::StringVectorData *d = const_cast<IECoreScenePreview::Renderer::Output*>( output )->parametersData()->member<IECore::StringVectorData>( "custom_attributes") )
			{
				customAttributesData = d->copy();
			}
			else
			{
				customAttributesData = new IECore::StringVectorData();
			}

			std::vector<std::string> &customAttributes = customAttributesData->writable();
			for( IECore::CompoundDataMap::const_iterator it = output->parameters().begin(), eIt = output->parameters().end(); it != eIt; ++it )
			{
				if( boost::starts_with( it->first.string(), "filter" ) )
				{
					continue;
				}

				if( boost::starts_with( it->first.string(), "header:" ) )
				{
					std::string formattedString = formatHeaderParameter( it->first.string().substr( 7 ), it->second.get() );
					if( !formattedString.empty())
					{
						customAttributes.push_back( formattedString );
					}
				}

				ParameterAlgo::setParameter( m_driver.get(), it->first.c_str(), it->second.get() );
			}

			if( AiNodeEntryLookUpParameter( AiNodeGetNodeEntry( m_driver.get() ), "custom_attributes" ) )
			{
				ParameterAlgo::setParameter( m_driver.get(), "custom_attributes", customAttributesData.get() );
			}

			// Create a filter.

			std::string filterNodeType = parameter<std::string>( output->parameters(), "filter", "gaussian" );
			if( AiNodeEntryGetType( AiNodeEntryLookUp( filterNodeType.c_str() ) ) != AI_NODE_FILTER )
			{
				filterNodeType = filterNodeType + "_filter";
			}

			const std::string filterNodeName = boost::str( boost::format( "ieCoreArnold:filter:%s" ) % name.string() );
			m_filter.reset(
				namespacedNode( filterNodeType.c_str(), filterNodeName.c_str() ),
				nodeDeleter
			);
			if( AiNodeEntryGetType( AiNodeGetNodeEntry( m_filter.get() ) ) != AI_NODE_FILTER )
			{
				throw IECore::Exception( boost::str( boost::format( "Unable to create filter of type \"%s\"" ) % filterNodeType ) );
			}

			for( IECore::CompoundDataMap::const_iterator it = output->parameters().begin(), eIt = output->parameters().end(); it != eIt; ++it )
			{
				if( !boost::starts_with( it->first.string(), "filter" ) || it->first == "filter" )
				{
					continue;
				}

				if( it->first == "filterwidth" )
				{
					// Special case to convert RenderMan style `float filterwidth[2]` into
					// Arnold style `float width`.
					if( const IECore::V2fData *v = IECore::runTimeCast<const IECore::V2fData>( it->second.get() ) )
					{
						if( v->readable().x != v->readable().y )
						{
							IECore::msg( IECore::Msg::Warning, "IECoreArnold::Renderer", "Non-square filterwidth not supported" );
						}
						AiNodeSetFlt( m_filter.get(), "width", v->readable().x );
						continue;
					}
				}

				ParameterAlgo::setParameter( m_filter.get(), it->first.c_str() + 6, it->second.get() );
			}

			// Convert the data specification to the form
			// supported by Arnold.

			m_data = output->getData();

			if( m_data=="rgb" )
			{
				m_data = "RGB RGB";
			}
			else if( m_data=="rgba" )
			{
				m_data = "RGBA RGBA";
			}
			else
			{
				vector<std::string> tokens;
				Gaffer::StringAlgo::tokenize( m_data, ' ', tokens );
				if( tokens.size() == 2 && tokens[0] == "color" )
				{
					m_data = tokens[1] + " RGBA";
				}
			}
		}

		std::string string() const
		{
			return boost::str( boost::format( "%s %s %s" ) % m_data % AiNodeGetName( m_filter.get() ) % AiNodeGetName( m_driver.get() ) );
		}

	private :

		SharedAtNodePtr m_driver;
		SharedAtNodePtr m_filter;
		std::string m_data;

};

IE_CORE_DECLAREPTR( ArnoldOutput )

} // namespace

//////////////////////////////////////////////////////////////////////////
// ArnoldShader
//////////////////////////////////////////////////////////////////////////

namespace
{

class ArnoldShader : public IECore::RefCounted
{

	public :

		ArnoldShader( const IECore::ObjectVector *shaderNetwork, NodeDeleter nodeDeleter, const std::string &namePrefix, const AtNode *parentNode )
			:	m_nodeDeleter( nodeDeleter )
		{
			m_nodes = namespacedShaderAlgoConvert( shaderNetwork, namePrefix, parentNode );
		}

		~ArnoldShader() override
		{
			for( std::vector<AtNode *>::const_iterator it = m_nodes.begin(), eIt = m_nodes.end(); it != eIt; ++it )
			{
				m_nodeDeleter( *it );
			}
		}

		AtNode *root()
		{
			return !m_nodes.empty() ? m_nodes.back() : nullptr;
		}

		void nodesCreated( vector<AtNode *> &nodes ) const
		{
			nodes.insert( nodes.end(), m_nodes.begin(), m_nodes.end() );
		}

	private :

		NodeDeleter m_nodeDeleter;
		std::vector<AtNode *> m_nodes;

};

IE_CORE_DECLAREPTR( ArnoldShader )

class ShaderCache : public IECore::RefCounted
{

	public :

		ShaderCache( NodeDeleter nodeDeleter, AtNode *parentNode )
			:	m_nodeDeleter( nodeDeleter ), m_parentNode( parentNode )
		{
		}

		// Can be called concurrently with other get() calls.
		ArnoldShaderPtr get( const IECore::ObjectVector *shader )
		{
			Cache::accessor a;
			m_cache.insert( a, shader->Object::hash() );
			if( !a->second )
			{
				const std::string namePrefix = "shader:" + shader->Object::hash().toString() + ":";
				a->second = new ArnoldShader( shader, m_nodeDeleter, namePrefix, m_parentNode );
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
					// shader.
					toErase.push_back( it->first );
				}
			}
			for( vector<IECore::MurmurHash>::const_iterator it = toErase.begin(), eIt = toErase.end(); it != eIt; ++it )
			{
				m_cache.erase( *it );
			}
		}

		void nodesCreated( vector<AtNode *> &nodes ) const
		{
			for( Cache::const_iterator it = m_cache.begin(), eIt = m_cache.end(); it != eIt; ++it )
			{
				it->second->nodesCreated( nodes );
			}
		}

	private :

		NodeDeleter m_nodeDeleter;
		AtNode *m_parentNode;

		typedef tbb::concurrent_hash_map<IECore::MurmurHash, ArnoldShaderPtr> Cache;
		Cache m_cache;

};

IE_CORE_DECLAREPTR( ShaderCache )

} // namespace

//////////////////////////////////////////////////////////////////////////
// ArnoldAttributes
//////////////////////////////////////////////////////////////////////////

namespace
{

IECore::InternedString g_surfaceShaderAttributeName( "surface" );
IECore::InternedString g_lightShaderAttributeName( "light" );
IECore::InternedString g_doubleSidedAttributeName( "doubleSided" );
IECore::InternedString g_setsAttributeName( "sets" );

IECore::InternedString g_oslSurfaceShaderAttributeName( "osl:surface" );
IECore::InternedString g_oslShaderAttributeName( "osl:shader" );

IECore::InternedString g_cameraVisibilityAttributeName( "ai:visibility:camera" );
IECore::InternedString g_shadowVisibilityAttributeName( "ai:visibility:shadow" );
IECore::InternedString g_diffuseReflectVisibilityAttributeName( "ai:visibility:diffuse_reflect" );
IECore::InternedString g_specularReflectVisibilityAttributeName( "ai:visibility:specular_reflect" );
IECore::InternedString g_diffuseTransmitVisibilityAttributeName( "ai:visibility:diffuse_transmit" );
IECore::InternedString g_specularTransmitVisibilityAttributeName( "ai:visibility:specular_transmit" );
IECore::InternedString g_volumeVisibilityAttributeName( "ai:visibility:volume" );
IECore::InternedString g_subsurfaceVisibilityAttributeName( "ai:visibility:subsurface" );

IECore::InternedString g_arnoldSurfaceShaderAttributeName( "ai:surface" );
IECore::InternedString g_arnoldLightShaderAttributeName( "ai:light" );

IECore::InternedString g_arnoldReceiveShadowsAttributeName( "ai:receive_shadows" );
IECore::InternedString g_arnoldSelfShadowsAttributeName( "ai:self_shadows" );
IECore::InternedString g_arnoldOpaqueAttributeName( "ai:opaque" );
IECore::InternedString g_arnoldMatteAttributeName( "ai:matte" );

IECore::InternedString g_stepSizeAttributeName( "ai:shape:step_size" );

IECore::InternedString g_polyMeshSubdivIterationsAttributeName( "ai:polymesh:subdiv_iterations" );
IECore::InternedString g_polyMeshSubdivAdaptiveErrorAttributeName( "ai:polymesh:subdiv_adaptive_error" );
IECore::InternedString g_polyMeshSubdivAdaptiveMetricAttributeName( "ai:polymesh:subdiv_adaptive_metric" );
IECore::InternedString g_polyMeshSubdivAdaptiveSpaceAttributeName( "ai:polymesh:subdiv_adaptive_space" );
IECore::InternedString g_polyMeshSubdivSmoothDerivsAttributeName( "ai:polymesh:subdiv_smooth_derivs" );
IECore::InternedString g_polyMeshSubdividePolygonsAttributeName( "ai:polymesh:subdivide_polygons" );
IECore::InternedString g_objectSpace( "object" );

IECore::InternedString g_dispMapAttributeName( "ai:disp_map" );
IECore::InternedString g_dispHeightAttributeName( "ai:disp_height" );
IECore::InternedString g_dispPaddingAttributeName( "ai:disp_padding" );
IECore::InternedString g_dispZeroValueAttributeName( "ai:disp_zero_value" );
IECore::InternedString g_dispAutoBumpAttributeName( "ai:disp_autobump" );

IECore::InternedString g_curvesMinPixelWidthAttributeName( "ai:curves:min_pixel_width" );
IECore::InternedString g_curvesModeAttributeName( "ai:curves:mode" );

IECore::InternedString g_linkedLights( "linkedLights" );
IECore::InternedString g_lightFilterPrefix( "ai:lightFilter:" );

const AtString g_nodeArnoldString("node");
const AtString g_ginstanceArnoldString("ginstance");
const AtString g_polymeshArnoldString("polymesh");
const AtString g_curvesArnoldString("curves");
const AtString g_boxArnoldString("box");
const AtString g_volumeArnoldString("volume");
const AtString g_sphereArnoldString("sphere");
const AtString g_subdivTypeArnoldString("subdiv_type");
const AtString g_catclarkArnoldString("catclark");
const AtString g_meshLightArnoldString("mesh_light");

class ArnoldAttributes : public IECoreScenePreview::Renderer::AttributesInterface
{

	public :

		ArnoldAttributes( const IECore::CompoundObject *attributes, ShaderCache *shaderCache )
			:	m_visibility( AI_RAY_ALL ), m_sidedness( AI_RAY_ALL ), m_shadingFlags( Default ), m_stepSize( 0.0f ), m_polyMesh( attributes ), m_displacement( attributes, shaderCache ), m_curves( attributes )
		{
			updateVisibility( g_cameraVisibilityAttributeName, AI_RAY_CAMERA, attributes );
			updateVisibility( g_shadowVisibilityAttributeName, AI_RAY_SHADOW, attributes );
			updateVisibility( g_diffuseReflectVisibilityAttributeName, AI_RAY_DIFFUSE_REFLECT, attributes );
			updateVisibility( g_specularReflectVisibilityAttributeName, AI_RAY_SPECULAR_REFLECT, attributes );
			updateVisibility( g_diffuseTransmitVisibilityAttributeName, AI_RAY_DIFFUSE_TRANSMIT, attributes );
			updateVisibility( g_specularTransmitVisibilityAttributeName, AI_RAY_SPECULAR_TRANSMIT, attributes );
			updateVisibility( g_volumeVisibilityAttributeName, AI_RAY_VOLUME, attributes );
			updateVisibility( g_subsurfaceVisibilityAttributeName, AI_RAY_SUBSURFACE, attributes );

			if( const IECore::BoolData *d = attribute<IECore::BoolData>( g_doubleSidedAttributeName, attributes ) )
			{
				m_sidedness = d->readable() ? AI_RAY_ALL : AI_RAY_UNDEFINED;
			}

			updateShadingFlag( g_arnoldReceiveShadowsAttributeName, ReceiveShadows, attributes );
			updateShadingFlag( g_arnoldSelfShadowsAttributeName, SelfShadows, attributes );
			updateShadingFlag( g_arnoldOpaqueAttributeName, Opaque, attributes );
			updateShadingFlag( g_arnoldMatteAttributeName, Matte, attributes );

			const IECore::ObjectVector *surfaceShaderAttribute = attribute<IECore::ObjectVector>( g_arnoldSurfaceShaderAttributeName, attributes );
			surfaceShaderAttribute = surfaceShaderAttribute ? surfaceShaderAttribute : attribute<IECore::ObjectVector>( g_oslSurfaceShaderAttributeName, attributes );
			surfaceShaderAttribute = surfaceShaderAttribute ? surfaceShaderAttribute : attribute<IECore::ObjectVector>( g_oslShaderAttributeName, attributes );
			surfaceShaderAttribute = surfaceShaderAttribute ? surfaceShaderAttribute : attribute<IECore::ObjectVector>( g_surfaceShaderAttributeName, attributes );
			if( surfaceShaderAttribute )
			{
				m_surfaceShader = shaderCache->get( surfaceShaderAttribute );
			}

			m_lightShader = attribute<IECore::ObjectVector>( g_arnoldLightShaderAttributeName, attributes );
			m_lightShader = m_lightShader ? m_lightShader : attribute<IECore::ObjectVector>( g_lightShaderAttributeName, attributes );

			m_traceSets = attribute<IECore::InternedStringVectorData>( g_setsAttributeName, attributes );
			m_stepSize = attributeValue<float>( g_stepSizeAttributeName, attributes, 0.0f );

			m_linkedLights = attribute<IECore::StringVectorData>( g_linkedLights, attributes );

			for( IECore::CompoundObject::ObjectMap::const_iterator it = attributes->members().begin(), eIt = attributes->members().end(); it != eIt; ++it )
			{
				if( boost::starts_with( it->first.string(), "user:" ) )
				{
					if( const IECore::Data *data = IECore::runTimeCast<const IECore::Data>( it->second.get() ) )
					{
						m_user[it->first] = data;
					}
				}
				if( boost::starts_with( it->first.string(), g_lightFilterPrefix.string() ) )
				{
					ArnoldShaderPtr filter = shaderCache->get( IECore::runTimeCast<const IECore::ObjectVector>( it->second.get() ) );
					m_lightFilterShaders.push_back( filter );
				}
			}
		}

		// Some attributes affect the geometric properties of a node, which means they
		// go on the shape rather than the ginstance. These are problematic because they
		// must be taken into account when determining the hash for instancing, and
		// because they cannot be edited interactively. This method applies those
		// attributes, and is called from InstanceCache during geometry conversion.
		void applyGeometry( const IECore::Object *object, AtNode *node ) const
		{
			if( const IECore::MeshPrimitive *mesh = IECore::runTimeCast<const IECore::MeshPrimitive>( object ) )
			{
				if( m_stepSize == 0.0f )
				{
					m_polyMesh.apply( mesh, node );
					m_displacement.apply( node );
				}
				else
				{
					// Non-zero step sizes will have caused conversion to a box,
					// so we can't apply our mesh attributes at all.
				}
			}
			else if( IECore::runTimeCast<const IECore::CurvesPrimitive>( object ) )
			{
				m_curves.apply( node );
			}

			if( m_stepSize != 0.0f && AiNodeEntryLookUpParameter( AiNodeGetNodeEntry( node ), "step_size" ) )
			{
				// Only apply step_size if it hasn't already been set to a non-zero
				// value by the geometry converter. This allows procedurals to carry
				// their step size as a parameter and have it trump the attribute value.
				// This is important for Gaffer nodes like ArnoldVDB, which carefully
				// calculate the correct step size and provide it via a parameter.
				if( AiNodeGetFlt( node, "step_size" ) == 0.0f )
				{
					AiNodeSetFlt( node, "step_size", m_stepSize );
				}
			}
		}

		// Generates a signature for the work done by applyGeometry.
		void hashGeometry( const IECore::Object *object, IECore::MurmurHash &h ) const
		{
			const IECore::TypeId objectType = object->typeId();
			bool meshInterpolationIsLinear = false;
			bool proceduralIsVolumetric = false;
			if( objectType == IECore::MeshPrimitiveTypeId )
			{
				meshInterpolationIsLinear = static_cast<const IECore::MeshPrimitive *>( object )->interpolation() == "linear";
			}
			else if( objectType == IECore::ExternalProceduralTypeId )
			{
				const IECore::ExternalProcedural *procedural = static_cast<const IECore::ExternalProcedural *>( object );
				if( procedural->getFileName() == "volume" )
				{
					proceduralIsVolumetric = true;
				}
			}
			hashGeometryInternal( objectType, meshInterpolationIsLinear, proceduralIsVolumetric, h );
		}

		// Returns true if the given geometry can be instanced, given the attributes that
		// will be applied in `applyGeometry()`.
		bool canInstanceGeometry( const IECore::Object *object ) const
		{
			if( !IECore::runTimeCast<const IECore::VisibleRenderable>( object ) )
			{
				return false;
			}

			if( const IECore::MeshPrimitive *mesh = IECore::runTimeCast<const IECore::MeshPrimitive>( object ) )
			{
				if( mesh->interpolation() == "linear" )
				{
					return true;
				}
				else
				{
					// We shouldn't instance poly meshes with view dependent subdivision, because the subdivision
					// for the master mesh might be totally inappropriate for the position of the ginstances in frame.
					return m_polyMesh.subdivAdaptiveError == 0.0f || m_polyMesh.subdivAdaptiveSpace == g_objectSpace;
				}
			}
			else if( const IECore::ExternalProcedural *procedural = IECore::runTimeCast<const IECore::ExternalProcedural>( object ) )
			{
				// We don't instance "ass archive" procedurals, because Arnold
				// does automatic instancing of those itself, using its procedural
				// cache.
				return (
					!boost::ends_with( procedural->getFileName(), ".ass" ) &&
					!boost::ends_with( procedural->getFileName(), ".ass.gz" )
				);
			}

			return true;
		}

		// Most attributes (visibility, surface shader etc) are orthogonal to the
		// type of object to which they are applied. These are the good kind, because
		// they can be applied to ginstance nodes, making attribute edits easy. This
		// method applies those attributes, and is called from `Renderer::object()`
		// and `Renderer::attributes()`.
		//
		// The previousAttributes are passed so that we can check that the new
		// geometry attributes are compatible with those which were applied previously
		// (and which cannot be changed now). Returns true if all is well and false
		// if there is a clash (and the edit has therefore failed).
		bool apply( AtNode *node, const ArnoldAttributes *previousAttributes ) const
		{

			// Check that we're not looking at an impossible request
			// to edit geometric attributes.

			if( previousAttributes )
			{
				const AtNode *geometry = node;
				if( AiNodeIs( node, g_ginstanceArnoldString ) )
				{
					geometry = static_cast<const AtNode *>( AiNodeGetPtr( node, g_nodeArnoldString ) );
				}

				IECore::TypeId objectType = IECore::InvalidTypeId;
				bool meshInterpolationIsLinear = false;
				bool proceduralIsVolumetric = false;
				if( AiNodeIs( geometry, g_polymeshArnoldString ) )
				{
					objectType = IECore::MeshPrimitiveTypeId;
					meshInterpolationIsLinear = AiNodeGetStr( geometry, g_subdivTypeArnoldString ) != g_catclarkArnoldString;
				}
				else if( AiNodeIs( geometry, g_curvesArnoldString ) )
				{
					objectType = IECore::CurvesPrimitiveTypeId;
				}
				else if( AiNodeIs( geometry, g_boxArnoldString ) )
				{
					objectType = IECore::MeshPrimitiveTypeId;
				}
				else if( AiNodeIs( geometry, g_volumeArnoldString ) )
				{
					objectType = IECore::ExternalProceduralTypeId;
					proceduralIsVolumetric = true;
				}
				else if( AiNodeIs( geometry, g_sphereArnoldString ) )
				{
					objectType = IECore::SpherePrimitiveTypeId;
				}

				IECore::MurmurHash previousGeometryHash;
				previousAttributes->hashGeometryInternal( objectType, meshInterpolationIsLinear, proceduralIsVolumetric, previousGeometryHash );

				IECore::MurmurHash currentGeometryHash;
				hashGeometryInternal( objectType, meshInterpolationIsLinear, proceduralIsVolumetric, currentGeometryHash );

				if( previousGeometryHash != currentGeometryHash )
				{
					return false;
				}
			}

			// Remove old user parameters we don't want any more.

			AtUserParamIterator *it= AiNodeGetUserParamIterator( node );
			while( !AiUserParamIteratorFinished( it ) )
			{
				const AtUserParamEntry *param = AiUserParamIteratorGetNext( it );
				const char *name = AiUserParamGetName( param );
				if( boost::starts_with( name, "user:" ) )
				{
					if( m_user.find( name ) == m_user.end() )
					{
						AiNodeResetParameter( node, name );
					}
				}
			}
			AiUserParamIteratorDestroy( it );

			// Add user parameters we do want.

			for( ArnoldAttributes::UserAttributes::const_iterator it = m_user.begin(), eIt = m_user.end(); it != eIt; ++it )
			{
				ParameterAlgo::setParameter( node, it->first.c_str(), it->second.get() );
			}

			// Add shape specific parameters.

			if( AiNodeEntryGetType( AiNodeGetNodeEntry( node ) ) == AI_NODE_SHAPE )
			{
				AiNodeSetByte( node, "visibility", m_visibility );
				AiNodeSetByte( node, "sidedness", m_sidedness );

				AiNodeSetBool( node, "receive_shadows", m_shadingFlags & ArnoldAttributes::ReceiveShadows );
				AiNodeSetBool( node, "self_shadows", m_shadingFlags & ArnoldAttributes::SelfShadows );
				AiNodeSetBool( node, "opaque", m_shadingFlags & ArnoldAttributes::Opaque );
				AiNodeSetBool( node, "matte", m_shadingFlags & ArnoldAttributes::Matte );

				if( m_surfaceShader && m_surfaceShader->root() )
				{
					AiNodeSetPtr( node, "shader", m_surfaceShader->root() );
				}
				else
				{
					AiNodeResetParameter( node, "shader" );
				}

				if( m_traceSets && m_traceSets->readable().size() )
				{
					const vector<IECore::InternedString> &v = m_traceSets->readable();
					AtArray *array = AiArrayAllocate( v.size(), 1, AI_TYPE_STRING );
					for( size_t i = 0, e = v.size(); i < e; ++i )
					{
						AiArraySetStr( array, i, v[i].c_str() );
					}
					AiNodeSetArray( node, "trace_sets", array );
				}
				else
				{
					// Arnold very unhelpfully treats `trace_sets == []` as meaning the object
					// is in every trace set. So we instead make `trace_sets == [ "__none__" ]`
					// to get the behaviour people expect.
					AiNodeSetArray( node, "trace_sets", AiArray( 1, 1, AI_TYPE_STRING, "__none__" ) );
				}

				if( m_linkedLights )
				{
					const std::vector<std::string> &lightNames = m_linkedLights->readable();

					std::vector<AtNode*> lightNodesVector;
					for ( IECore::StringVectorData::ValueType::const_iterator it = lightNames.begin(); it != lightNames.end(); ++it )
					{
						std::string lightName = "light:" + *(it);
						AtNode *lightNode = AiNodeLookUpByName( lightName.c_str() );
						if( lightNode )
						{
							lightNodesVector.push_back( lightNode );
						}
					}

					AtArray *linkedLightNodes = AiArrayConvert( lightNodesVector.size(), 1, AI_TYPE_NODE, lightNodesVector.data() );
					AiNodeSetArray( node, "light_group", linkedLightNodes );
					AiNodeSetBool( node, "use_light_group", true );
				}
				else
				{
					AiNodeResetParameter( node, "light_group" );
					AiNodeResetParameter( node, "use_light_group" );
				}
			}

			return true;
		}

		const IECore::ObjectVector *lightShader() const
		{
			return m_lightShader.get();
		}

		const std::vector<ArnoldShaderPtr>& lightFilterShaders() const
		{
			return m_lightFilterShaders;
		}

	private :

		struct PolyMesh
		{

			PolyMesh( const IECore::CompoundObject *attributes )
			{
				subdivIterations = attributeValue<int>( g_polyMeshSubdivIterationsAttributeName, attributes, 1 );
				subdivAdaptiveError = attributeValue<float>( g_polyMeshSubdivAdaptiveErrorAttributeName, attributes, 0.0f );
				subdivAdaptiveMetric = attributeValue<string>( g_polyMeshSubdivAdaptiveMetricAttributeName, attributes, "auto" );
				subdivAdaptiveSpace = attributeValue<string>( g_polyMeshSubdivAdaptiveSpaceAttributeName, attributes, "raster" );
				subdividePolygons = attributeValue<bool>( g_polyMeshSubdividePolygonsAttributeName, attributes, false );
				subdivSmoothDerivs = attributeValue<bool>( g_polyMeshSubdivSmoothDerivsAttributeName, attributes, false );
			}

			int subdivIterations;
			float subdivAdaptiveError;
			IECore::InternedString subdivAdaptiveMetric;
			IECore::InternedString subdivAdaptiveSpace;
			bool subdividePolygons;
			bool subdivSmoothDerivs;

			void hash( bool meshInterpolationIsLinear, IECore::MurmurHash &h ) const
			{
				if( !meshInterpolationIsLinear || subdividePolygons )
				{
					h.append( subdivIterations );
					h.append( subdivAdaptiveError );
					h.append( subdivAdaptiveMetric );
					h.append( subdivAdaptiveSpace );
					h.append( subdivSmoothDerivs );
				}
			}

			void apply( const IECore::MeshPrimitive *mesh, AtNode *node ) const
			{
				if( mesh->interpolation() != "linear" || subdividePolygons )
				{
					AiNodeSetByte( node, "subdiv_iterations", subdivIterations );
					AiNodeSetFlt( node, "subdiv_adaptive_error", subdivAdaptiveError );
					AiNodeSetStr( node, "subdiv_adaptive_metric", subdivAdaptiveMetric.c_str() );
					AiNodeSetStr( node, "subdiv_adaptive_space", subdivAdaptiveSpace.c_str() );
					AiNodeSetBool( node, "subdiv_smooth_derivs", subdivSmoothDerivs );
					if( mesh->interpolation() == "linear" )
					{
						AiNodeSetStr( node, "subdiv_type", "linear" );
					}
				}
			}

		};

		struct Displacement
		{

			Displacement( const IECore::CompoundObject *attributes, ShaderCache *shaderCache )
			{
				if( const IECore::ObjectVector *mapAttribute = attribute<IECore::ObjectVector>( g_dispMapAttributeName, attributes ) )
				{
					map = shaderCache->get( mapAttribute );
				}
				height = attributeValue<float>( g_dispHeightAttributeName, attributes, 1.0f );
				padding = attributeValue<float>( g_dispPaddingAttributeName, attributes, 0.0f );
				zeroValue = attributeValue<float>( g_dispZeroValueAttributeName, attributes, 0.0f );
				autoBump = attributeValue<bool>( g_dispAutoBumpAttributeName, attributes, false );
			}

			ArnoldShaderPtr map;
			float height;
			float padding;
			float zeroValue;
			bool autoBump;

			void hash( IECore::MurmurHash &h ) const
			{
				if( map && map->root() )
				{
					h.append( AiNodeGetName( map->root() ) );
				}
				h.append( height );
				h.append( padding );
				h.append( zeroValue );
				h.append( autoBump );
			}

			void apply( AtNode *node ) const
			{
				if( map && map->root() )
				{
					AiNodeSetPtr( node, "disp_map", map->root() );
				}
				else
				{
					AiNodeResetParameter( node, "disp_map" );
				}

				AiNodeSetFlt( node, "disp_height", height );
				AiNodeSetFlt( node, "disp_padding", padding );
				AiNodeSetFlt( node, "disp_zero_value", zeroValue );
				AiNodeSetBool( node, "disp_autobump", autoBump );
			}

		};

		struct Curves
		{

			Curves( const IECore::CompoundObject *attributes )
			{
				minPixelWidth = attributeValue<float>( g_curvesMinPixelWidthAttributeName, attributes, 0.0f );
				// Arnold actually has three modes - "ribbon", "oriented" and "thick".
				// The Cortex convention (inherited from RenderMan) is that curves without
				// normals ("N" primitive variable) are rendered as camera facing ribbons,
				// and those with normals are rendered as ribbons oriented by "N".
				// IECoreArnold::CurvesAlgo takes care of this part for us automatically, so all that
				// remains for us to do is to override the mode to "thick" if necessary to
				// expose Arnold's remaining functionality.
				//
				// The semantics for our "ai:curves:mode" attribute are therefore as follows :
				//
				//	  "ribbon" : Automatically choose `mode = "ribbon"` or `mode = "oriented"`
				//               according to the existence of "N".
				//    "thick"  : Render with `mode = "thick"`.
				thick = attributeValue<string>( g_curvesModeAttributeName, attributes, "ribbon" ) == "thick";
			}

			float minPixelWidth;
			bool thick;

			void hash( IECore::MurmurHash &h ) const
			{
				h.append( minPixelWidth );
				h.append( thick );
			}

			void apply( AtNode *node ) const
			{
				AiNodeSetFlt( node, "min_pixel_width", minPixelWidth );
				if( thick )
				{
					AiNodeSetStr( node, "mode", "thick" );
				}
			}

		};

		enum ShadingFlags
		{
			ReceiveShadows = 1,
			SelfShadows = 2,
			Opaque = 4,
			Matte = 8,
			Default = ReceiveShadows | SelfShadows | Opaque,
			All = ReceiveShadows | SelfShadows | Opaque | Matte
		};

		template<typename T>
		static const T *attribute( const IECore::InternedString &name, const IECore::CompoundObject *attributes )
		{
			IECore::CompoundObject::ObjectMap::const_iterator it = attributes->members().find( name );
			if( it == attributes->members().end() )
			{
				return nullptr;
			}
			return reportedCast<const T>( it->second.get(), "attribute", name );
		}

		template<typename T>
		static T attributeValue( const IECore::InternedString &name, const IECore::CompoundObject *attributes, const T &defaultValue )
		{
			typedef IECore::TypedData<T> DataType;
			const DataType *data = attribute<DataType>( name, attributes );
			return data ? data->readable() : defaultValue;
		}

		void updateVisibility( const IECore::InternedString &name, unsigned char rayType, const IECore::CompoundObject *attributes )
		{
			if( const IECore::BoolData *d = attribute<IECore::BoolData>( name, attributes ) )
			{
				if( d->readable() )
				{
					m_visibility |= rayType;
				}
				else
				{
					m_visibility = m_visibility & ~rayType;
				}
			}
		}

		void updateShadingFlag( const IECore::InternedString &name, unsigned char flag, const IECore::CompoundObject *attributes )
		{
			if( const IECore::BoolData *d = attribute<IECore::BoolData>( name, attributes ) )
			{
				if( d->readable() )
				{
					m_shadingFlags |= flag;
				}
				else
				{
					m_shadingFlags = m_shadingFlags & ~flag;
				}
			}
		}

		void hashGeometryInternal( IECore::TypeId objectType, bool meshInterpolationIsLinear, bool proceduralIsVolumetric, IECore::MurmurHash &h ) const
		{
			switch( objectType )
			{
				case IECore::MeshPrimitiveTypeId :
					m_polyMesh.hash( meshInterpolationIsLinear, h );
					m_displacement.hash( h );
					h.append( m_stepSize );
					break;
				case IECore::CurvesPrimitiveTypeId :
					m_curves.hash( h );
					break;
				case IECore::SpherePrimitiveTypeId :
					h.append( m_stepSize );
					break;
				case IECore::ExternalProceduralTypeId :
					if( proceduralIsVolumetric )
					{
						h.append( m_stepSize );
					}
					break;
				default :
					// No geometry attributes for this type.
					break;
			}
		}

		unsigned char m_visibility;
		unsigned char m_sidedness;
		unsigned char m_shadingFlags;
		ArnoldShaderPtr m_surfaceShader;
		IECore::ConstObjectVectorPtr m_lightShader;
		std::vector<ArnoldShaderPtr> m_lightFilterShaders;
		IECore::ConstInternedStringVectorDataPtr m_traceSets;
		float m_stepSize;
		PolyMesh m_polyMesh;
		Displacement m_displacement;
		Curves m_curves;
		IECore::ConstStringVectorDataPtr m_linkedLights;

		typedef boost::container::flat_map<IECore::InternedString, IECore::ConstDataPtr> UserAttributes;
		UserAttributes m_user;

};

IE_CORE_DECLAREPTR( ArnoldAttributes )

} // namespace

//////////////////////////////////////////////////////////////////////////
// InstanceCache
//////////////////////////////////////////////////////////////////////////

namespace
{

class Instance
{

	public :

		// Non-instanced
		Instance( const SharedAtNodePtr &node )
			:	m_node( node )
		{
		}

		// Instanced
		Instance( const SharedAtNodePtr &node, NodeDeleter nodeDeleter, const std::string &instanceName, const AtNode *parent )
			:	m_node( node )
		{
			if( node )
			{
				AiNodeSetByte( node.get(), "visibility", 0 );
				m_ginstance = SharedAtNodePtr(
					namespacedNode( "ginstance", instanceName, parent ),
					nodeDeleter
				);
				AiNodeSetPtr( m_ginstance.get(), "node", m_node.get() );
			}
		}

		AtNode *node()
		{
			return m_ginstance.get() ? m_ginstance.get() : m_node.get();
		}

		void nodesCreated( vector<AtNode *> &nodes ) const
		{
			if( m_ginstance )
			{
				nodes.push_back( m_ginstance.get() );
			}
		}

	private :

		SharedAtNodePtr m_node;
		SharedAtNodePtr m_ginstance;

};

// Forward declaration
AtNode *convertProcedural( IECoreScenePreview::ConstProceduralPtr procedural, const std::string &nodeName, const AtNode *parentNode );

class InstanceCache : public IECore::RefCounted
{

	public :

		InstanceCache( NodeDeleter nodeDeleter, AtNode *parentNode )
			:	m_nodeDeleter( nodeDeleter ), m_parentNode( parentNode )
		{
		}

		// Can be called concurrently with other get() calls.
		Instance get( const IECore::Object *object, const IECoreScenePreview::Renderer::AttributesInterface *attributes, const std::string &nodeName )
		{
			const ArnoldAttributes *arnoldAttributes = static_cast<const ArnoldAttributes *>( attributes );

			if( !canInstance( object, arnoldAttributes ) )
			{
				return Instance( convert( object, arnoldAttributes, nodeName ) );
			}

			IECore::MurmurHash h = object->hash();
			arnoldAttributes->hashGeometry( object, h );

			Cache::accessor a;
			m_cache.insert( a, h );
			if( !a->second )
			{
				a->second = convert( object, arnoldAttributes, "instance:" + h.toString() );
			}

			return Instance( a->second, m_nodeDeleter, nodeName, m_parentNode );
		}

		Instance get( const std::vector<const IECore::Object *> &samples, const std::vector<float> &times, const IECoreScenePreview::Renderer::AttributesInterface *attributes, const std::string &nodeName )
		{
			const ArnoldAttributes *arnoldAttributes = static_cast<const ArnoldAttributes *>( attributes );

			if( !canInstance( samples.front(), arnoldAttributes ) )
			{
				return Instance( convert( samples, times, arnoldAttributes, nodeName ) );
			}

			IECore::MurmurHash h;
			for( std::vector<const IECore::Object *>::const_iterator it = samples.begin(), eIt = samples.end(); it != eIt; ++it )
			{
				(*it)->hash( h );
			}
			for( std::vector<float>::const_iterator it = times.begin(), eIt = times.end(); it != eIt; ++it )
			{
				h.append( *it );
			}
			arnoldAttributes->hashGeometry( samples.front(), h );

			Cache::accessor a;
			m_cache.insert( a, h );
			if( !a->second )
			{
				a->second = convert( samples, times, arnoldAttributes, "instance:" + h.toString() );
			}

			return Instance( a->second, m_nodeDeleter, nodeName, m_parentNode );
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
					// node.
					toErase.push_back( it->first );
				}
			}
			for( vector<IECore::MurmurHash>::const_iterator it = toErase.begin(), eIt = toErase.end(); it != eIt; ++it )
			{
				m_cache.erase( *it );
			}
		}

		void nodesCreated( vector<AtNode *> &nodes ) const
		{
			for( Cache::const_iterator it = m_cache.begin(), eIt = m_cache.end(); it != eIt; ++it )
			{
				if( it->second )
				{
					nodes.push_back( it->second.get() );
				}
			}
		}

	private :

		bool canInstance( const IECore::Object *object, const ArnoldAttributes *attributes ) const
		{
			if( IECore::runTimeCast<const IECoreScenePreview::Procedural>( object ) && m_nodeDeleter == AiNodeDestroy )
			{
				// Work around Arnold bug whereby deleting an instanced procedural
				// can lead to crashes. This unfortunately means that we don't get
				// to do instancing of procedurals during interactive renders, but
				// we can at least do it during batch renders.
				/// \todo Remove this workaround once the Arnold bug is fixed.
				return false;
			}
			return attributes->canInstanceGeometry( object );
		}

		SharedAtNodePtr convert( const IECore::Object *object, const ArnoldAttributes *attributes, const std::string &nodeName )
		{
			if( !object )
			{
				return SharedAtNodePtr();
			}

			AtNode *node = nullptr;
			if( const IECoreScenePreview::Procedural *procedural = IECore::runTimeCast<const IECoreScenePreview::Procedural>( object ) )
			{
				node = convertProcedural( procedural, nodeName, m_parentNode );
			}
			else
			{
				node = namespacedNodeAlgoConvert( object, nodeName, m_parentNode );
			}

			if( !node )
			{
				return SharedAtNodePtr();
			}

			attributes->applyGeometry( object, node );

			return SharedAtNodePtr( node, m_nodeDeleter );
		}

		SharedAtNodePtr convert( const std::vector<const IECore::Object *> &samples, const std::vector<float> &times, const ArnoldAttributes *attributes, const std::string &nodeName )
		{
			NodeAlgo::ensureUniformTimeSamples( times );
			AtNode *node = nullptr;
			if( const IECoreScenePreview::Procedural *procedural = IECore::runTimeCast<const IECoreScenePreview::Procedural>( samples.front() ) )
			{
				node = convertProcedural( procedural, nodeName, m_parentNode );
			}
			else
			{
				node = namespacedNodeAlgoConvert( samples, times[0], times[times.size() - 1], nodeName, m_parentNode );
			}

			if( !node )
			{
				return SharedAtNodePtr();
			}

			attributes->applyGeometry( samples.front(), node );

			return SharedAtNodePtr( node, m_nodeDeleter );

		}

		NodeDeleter m_nodeDeleter;
		AtNode *m_parentNode;

		typedef tbb::concurrent_hash_map<IECore::MurmurHash, SharedAtNodePtr> Cache;
		Cache m_cache;

};

IE_CORE_DECLAREPTR( InstanceCache )

} // namespace

//////////////////////////////////////////////////////////////////////////
// ArnoldObject
//////////////////////////////////////////////////////////////////////////

namespace
{

static IECore::InternedString g_surfaceAttributeName( "surface" );
static IECore::InternedString g_aiSurfaceAttributeName( "ai:surface" );

class ArnoldObject : public IECoreScenePreview::Renderer::ObjectInterface
{

	public :

		ArnoldObject( const Instance &instance )
			:	m_instance( instance ), m_attributes( nullptr )
		{
		}

		void transform( const Imath::M44f &transform ) override
		{
			AtNode *node = m_instance.node();
			if( !node )
			{
				return;
			}
			applyTransform( node, transform );
		}

		void transform( const std::vector<Imath::M44f> &samples, const std::vector<float> &times ) override
		{
			AtNode *node = m_instance.node();
			if( !node )
			{
				return;
			}
			applyTransform( node, samples, times );
		}

		bool attributes( const IECoreScenePreview::Renderer::AttributesInterface *attributes ) override
		{
			AtNode *node = m_instance.node();
			if( !node )
			{
				return true;
			}

			const ArnoldAttributes *arnoldAttributes = static_cast<const ArnoldAttributes *>( attributes );
			if( arnoldAttributes->apply( node, m_attributes.get() ) )
			{
				m_attributes = arnoldAttributes;
				return true;
			}
			return false;
		}

		const Instance &instance() const
		{
			return m_instance;
		}

	protected :

		void applyTransform( AtNode *node, const Imath::M44f &transform )
		{
			AiNodeSetMatrix( node, "matrix", reinterpret_cast<const AtMatrix&>( transform.x ) );
		}

		void applyTransform( AtNode *node, const std::vector<Imath::M44f> &samples, const std::vector<float> &times )
		{
			const size_t numSamples = samples.size();
			AtArray *matricesArray = AiArrayAllocate( 1, numSamples, AI_TYPE_MATRIX );
			for( size_t i = 0; i < numSamples; ++i )
			{
				AiArraySetMtx( matricesArray, i, reinterpret_cast<const AtMatrix&>( samples[i].x ) );
			}
			AiNodeSetArray( node, "matrix", matricesArray );

			NodeAlgo::ensureUniformTimeSamples( times );
			AiNodeSetFlt( node, "motion_start", times[0] );
			AiNodeSetFlt( node, "motion_end", times[times.size() - 1] );

		}

		Instance m_instance;
		// We keep a reference to the currently applied attributes
		// for a couple of reasons :
		//
		//  - We need to keep the displacement and surface shaders
		//    alive for as long as they are referenced by m_instance.
		//  - We can use the previously applied attributes to determine
		//    if an incoming attribute edit is impossible because it
		//    would affect the instance itself, and return failure from
		//    `attributes()`.
		ConstArnoldAttributesPtr m_attributes;

};

IE_CORE_FORWARDDECLARE( ArnoldObject )

} // namespace

//////////////////////////////////////////////////////////////////////////
// ArnoldLight
//////////////////////////////////////////////////////////////////////////

namespace
{

class ArnoldLight : public ArnoldObject
{

	public :

		ArnoldLight( const std::string &name, const Instance &instance, NodeDeleter nodeDeleter, const AtNode *parentNode )
			:	ArnoldObject( instance ), m_name( name ), m_nodeDeleter( nodeDeleter ), m_parentNode( parentNode )
		{
		}

		void transform( const Imath::M44f &transform ) override
		{
			ArnoldObject::transform( transform );
			m_transformMatrices.clear();
			m_transformTimes.clear();
			m_transformMatrices.push_back( transform );
			applyLightTransform();
		}

		void transform( const std::vector<Imath::M44f> &samples, const std::vector<float> &times ) override
		{
			ArnoldObject::transform( samples, times );
			m_transformMatrices = samples;
			m_transformTimes = times;
			applyLightTransform();
		}

		bool attributes( const IECoreScenePreview::Renderer::AttributesInterface *attributes ) override
		{
			if( !ArnoldObject::attributes( attributes ) )
			{
				return false;
			}

			const ArnoldAttributes *arnoldAttributes = static_cast<const ArnoldAttributes *>( attributes );

			// Update light shader.

			m_lightShader = nullptr;
			if( !arnoldAttributes->lightShader() )
			{
				return true;
			}

			m_lightShader = new ArnoldShader( arnoldAttributes->lightShader(), m_nodeDeleter, "light:" + m_name + ":", m_parentNode );

			// Simplify name for the root shader, for ease of reading of ass files.
			const std::string name = "light:" + m_name;
			AiNodeSetStr( m_lightShader->root(), "name", name.c_str() );

			// Deal with mesh lights.

			if( AiNodeIs( m_lightShader->root(), g_meshLightArnoldString ) )
			{
				if( m_instance.node() )
				{
					AiNodeSetPtr( m_lightShader->root(), "mesh", m_instance.node() );
				}
				else
				{
					// Don't output mesh lights from locations with no object
					m_lightShader = nullptr;
					return true;
				}
			}

			// Deal with light filters.

			const std::vector<ArnoldShaderPtr> &lightFilterShaders = arnoldAttributes->lightFilterShaders();
			AtArray *linkedFilterNodes = AiArrayAllocate( lightFilterShaders.size(), 1, AI_TYPE_NODE );
			for( unsigned i = 0; i < lightFilterShaders.size(); ++i )
			{
				AiArraySetPtr( linkedFilterNodes, i, lightFilterShaders[i]->root() );
			}

			AiNodeSetArray( m_lightShader->root(), "filters", linkedFilterNodes );

			applyLightTransform();
			return true;
		}

		void nodesCreated( vector<AtNode *> &nodes ) const
		{
			if( m_lightShader )
			{
				m_lightShader->nodesCreated( nodes );
			}
		}

	private :

		void applyLightTransform()
		{
			if( !m_lightShader || m_transformMatrices.empty() )
			{
				return;
			}
			AtNode *root = m_lightShader->root();
			if( m_transformTimes.empty() )
			{
				assert( m_transformMatrices.size() == 1 );
				applyTransform( root, m_transformMatrices[0] );
			}
			else
			{
				applyTransform( root, m_transformMatrices, m_transformTimes );
			}
		}

		// Because the AtNode for the light arrives via attributes(),
		// we need to store the transform and name ourselves so we have
		// them later when we need them.
		std::string m_name;
		vector<Imath::M44f> m_transformMatrices;
		vector<float> m_transformTimes;
		NodeDeleter m_nodeDeleter;
		const AtNode *m_parentNode;
		ArnoldShaderPtr m_lightShader;

};

IE_CORE_DECLAREPTR( ArnoldLight )

} // namespace

//////////////////////////////////////////////////////////////////////////
// Procedurals
//////////////////////////////////////////////////////////////////////////

namespace
{

class ProceduralRenderer final : public ArnoldRendererBase
{

	public :

		// We use a null node deleter because Arnold will automatically
		// destroy all nodes belonging to the procedural when the procedural
		// itself is destroyed.
		/// \todo The base class currently makes a new shader cache
		/// and a new instance cache. Can we share with the parent
		/// renderer instead?
		ProceduralRenderer( AtNode *procedural )
			:	ArnoldRendererBase( nullNodeDeleter, procedural )
		{
		}

		virtual void option( const IECore::InternedString &name, const IECore::Data *value ) override
		{
			IECore::msg( IECore::Msg::Warning, "ArnoldRenderer", "Procedurals can not call option()" );
		}

		virtual void output( const IECore::InternedString &name, const Output *output ) override
		{
			IECore::msg( IECore::Msg::Warning, "ArnoldRenderer", "Procedurals can not call output()" );
		}

		ObjectInterfacePtr camera( const std::string &name, const IECore::Camera *camera, const AttributesInterface *attributes ) override
		{
			IECore::msg( IECore::Msg::Warning, "ArnoldRenderer", "Procedurals can not call camera()" );
			return nullptr;
		}

		ObjectInterfacePtr light( const std::string &name, const IECore::Object *object, const AttributesInterface *attributes ) override
		{
			ArnoldLightPtr result = static_pointer_cast<ArnoldLight>(
				ArnoldRendererBase::light( name, object, attributes )
			);

			NodesCreatedMutex::scoped_lock lock( m_nodesCreatedMutex );
			result->instance().nodesCreated( m_nodesCreated );
			result->nodesCreated( m_nodesCreated );
			return result;
		}

		Renderer::ObjectInterfacePtr object( const std::string &name, const IECore::Object *object, const AttributesInterface *attributes ) override
		{
			ArnoldObjectPtr result = static_pointer_cast<ArnoldObject>(
				ArnoldRendererBase::object( name, object, attributes )
			);

			NodesCreatedMutex::scoped_lock lock( m_nodesCreatedMutex );
			result->instance().nodesCreated( m_nodesCreated );
			return result;
		}

		ObjectInterfacePtr object( const std::string &name, const std::vector<const IECore::Object *> &samples, const std::vector<float> &times, const AttributesInterface *attributes ) override
		{
			ArnoldObjectPtr result = static_pointer_cast<ArnoldObject>(
				ArnoldRendererBase::object( name, samples, times, attributes )
			);

			NodesCreatedMutex::scoped_lock lock( m_nodesCreatedMutex );
			result->instance().nodesCreated( m_nodesCreated );
			return result;
		}

		virtual void render() override
		{
			IECore::msg( IECore::Msg::Warning, "ArnoldRenderer", "Procedurals can not call render()" );
		}

		virtual void pause() override
		{
			IECore::msg( IECore::Msg::Warning, "ArnoldRenderer", "Procedurals can not call pause()" );
		}

		void nodesCreated( vector<AtNode *> &nodes )
		{
			nodes.insert( nodes.begin(), m_nodesCreated.begin(), m_nodesCreated.end() );
			m_instanceCache->nodesCreated( nodes );
			m_shaderCache->nodesCreated( nodes );
		}

	private :

		typedef tbb::spin_mutex NodesCreatedMutex;
		NodesCreatedMutex m_nodesCreatedMutex;
		vector<AtNode *> m_nodesCreated;

};

IE_CORE_DECLAREPTR( ProceduralRenderer )

struct ProceduralData : boost::noncopyable
{
	vector<AtNode *> nodesCreated;
};

int procInit( AtNode *node, void **userPtr )
{
	ProceduralData *data = (ProceduralData *)( AiNodeGetPtr( node, "userptr" ) );
	*userPtr = data;
	return 1;
}

int procCleanup( const AtNode *node, void *userPtr )
{
	const ProceduralData *data = (ProceduralData *)( userPtr );
	delete data;
	return 1;
}

int procNumNodes( const AtNode *node, void *userPtr )
{
	const ProceduralData *data = (ProceduralData *)( userPtr );
	return data->nodesCreated.size();
}

AtNode *procGetNode( const AtNode *node, void *userPtr, int i )
{
	const ProceduralData *data = (ProceduralData *)( userPtr );
	return data->nodesCreated[i];
}

int procFunc( AtProceduralNodeMethods *methods )
{
	methods->Init = procInit;
	methods->Cleanup = procCleanup;
	methods->NumNodes = procNumNodes;
	methods->GetNode = procGetNode;
	return 1;
}

AtNode *convertProcedural( IECoreScenePreview::ConstProceduralPtr procedural, const std::string &nodeName, const AtNode *parentNode )
{
	AtNode *node = namespacedNode( "procedural", nodeName, parentNode );

	AiNodeSetPtr( node, "funcptr", (void *)procFunc );

	ProceduralRendererPtr renderer = new ProceduralRenderer( node );
	procedural->render( renderer.get() );

	ProceduralData *data = new ProceduralData;
	renderer->nodesCreated( data->nodesCreated );
	AiNodeSetPtr( node, "userptr", data );

	return node;
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// InteractiveRenderController
//////////////////////////////////////////////////////////////////////////

namespace
{

class InteractiveRenderController
{

	public :

		InteractiveRenderController()
		{
			m_rendering = false;
		}

		void setRendering( bool rendering )
		{
			if( rendering == m_rendering )
			{
				return;
			}

			m_rendering = rendering;

			if( rendering )
			{
				std::thread thread( boost::bind( &InteractiveRenderController::performInteractiveRender, this ) );
				m_thread.swap( thread );
			}
			else
			{
				if( AiRendering() )
				{
					AiRenderInterrupt();
				}
				m_thread.join();
			}
		}

		bool getRendering() const
		{
			return m_rendering;
		}

	private :

		// Called in a background thread to control a
		// progressive interactive render.
		void performInteractiveRender()
		{
			AtNode *options = AiUniverseGetOptions();
			const int finalAASamples = AiNodeGetInt( options, "AA_samples" );
			const int startAASamples = min( -5, finalAASamples );

			for( int aaSamples = startAASamples; aaSamples <= finalAASamples; ++aaSamples )
			{
				if( aaSamples == 0 || ( aaSamples > 1 && aaSamples != finalAASamples ) )
				{
					// 0 AA_samples is meaningless, and we want to jump straight
					// from 1 AA_sample to the final sampling quality.
					continue;
				}

				AiNodeSetInt( options, "AA_samples", aaSamples );
				if( !m_rendering || AiRender( AI_RENDER_MODE_CAMERA ) != AI_SUCCESS )
				{
					// Render cancelled on main thread.
					break;
				}
			}

			// Restore the setting we've been monkeying with.
			AiNodeSetInt( options, "AA_samples", finalAASamples );
		}

		std::thread m_thread;
		tbb::atomic<bool> m_rendering;

};

} // namespace

//////////////////////////////////////////////////////////////////////////
// Globals
//////////////////////////////////////////////////////////////////////////

namespace
{

/// \todo Should these be defined in the Renderer base class?
/// Or maybe be in a utility header somewhere?
IECore::InternedString g_frameOptionName( "frame" );
IECore::InternedString g_cameraOptionName( "camera" );

IECore::InternedString g_logFileNameOptionName( "ai:log:filename" );
IECore::InternedString g_logMaxWarningsOptionName( "ai:log:max_warnings" );
IECore::InternedString g_pluginSearchPathOptionName( "ai:plugin_searchpath" );
IECore::InternedString g_aaSeedOptionName( "ai:AA_seed" );
IECore::InternedString g_sampleMotionOptionName( "sampleMotion" );

std::string g_logFlagsOptionPrefix( "ai:log:" );
std::string g_consoleFlagsOptionPrefix( "ai:console:" );

const int g_logFlagsDefault = AI_LOG_ALL;
const int g_consoleFlagsDefault = AI_LOG_WARNINGS | AI_LOG_ERRORS | AI_LOG_TIMESTAMP | AI_LOG_BACKTRACE | AI_LOG_MEMORY | AI_LOG_COLOR;

class ArnoldGlobals
{

	public :

		ArnoldGlobals( IECoreScenePreview::Renderer::RenderType renderType, const std::string &fileName )
			:	m_renderType( renderType ),
				m_universeBlock( /* writable = */ true ),
				m_logFileFlags( g_logFlagsDefault ),
				m_consoleFlags( g_consoleFlagsDefault ),
				m_assFileName( fileName )
		{
			AiMsgSetLogFileFlags( m_logFileFlags );
			AiMsgSetConsoleFlags( m_consoleFlags );
			// Get OSL shaders onto the shader searchpath.
			option( g_pluginSearchPathOptionName, new IECore::StringData( "" ) );
		}

		void option( const IECore::InternedString &name, const IECore::Data *value )
		{
			AtNode *options = AiUniverseGetOptions();
			if( name == g_frameOptionName )
			{
				if( value == nullptr )
				{
					m_frame = boost::none;
				}
				else if( const IECore::IntData *d = reportedCast<const IECore::IntData>( value, "option", name ) )
				{
					m_frame = d->readable();
				}
				return;
			}
			else if( name == g_cameraOptionName )
			{
				if( value == nullptr )
				{
					m_cameraName = "";
				}
				else if( const IECore::StringData *d = reportedCast<const IECore::StringData>( value, "option", name ) )
				{
					m_cameraName = d->readable();

				}
				return;
			}
			else if( name == g_logFileNameOptionName )
			{
				if( value == nullptr )
				{
					AiMsgSetLogFileName( "" );
				}
				else if( const IECore::StringData *d = reportedCast<const IECore::StringData>( value, "option", name ) )
				{
					if( !d->readable().empty() )
					{
						try
						{
							boost::filesystem::path path( d->readable() );
							path.remove_filename();
							boost::filesystem::create_directories( path );
						}
						catch( const std::exception &e )
						{
							IECore::msg( IECore::Msg::Error, "ArnoldRenderer::option()", e.what() );
						}
					}
					AiMsgSetLogFileName( d->readable().c_str() );

				}
				return;
			}
			else if( name == g_logMaxWarningsOptionName )
			{
				if( value == nullptr )
				{
					AiMsgSetMaxWarnings( 100 );
				}
				else if( const IECore::IntData *d = reportedCast<const IECore::IntData>( value, "option", name ) )
				{
					AiMsgSetMaxWarnings( d->readable() );
				}
				return;
			}
			else if( boost::starts_with( name.c_str(), g_logFlagsOptionPrefix ) )
			{
				if( updateLogFlags( name.string().substr( g_logFlagsOptionPrefix.size() ), value, /* console = */ false ) )
				{
					return;
				}
			}
			else if( boost::starts_with( name.c_str(), g_consoleFlagsOptionPrefix ) )
			{
				if( updateLogFlags( name.string().substr( g_consoleFlagsOptionPrefix.size() ), value, /* console = */ true ) )
				{
					return;
				}
			}
			else if( name == g_aaSeedOptionName )
			{
				if( value == nullptr )
				{
					m_aaSeed = boost::none;
				}
				else if( const IECore::IntData *d = reportedCast<const IECore::IntData>( value, "option", name ) )
				{
					m_aaSeed = d->readable();
				}
				return;
			}
			else if( name == g_sampleMotionOptionName )
			{
				if( value == nullptr )
				{
					m_sampleMotion = boost::none;
				}
				else if( const IECore::BoolData *d = reportedCast<const IECore::BoolData>( value, "option", name ) )
				{
					m_sampleMotion = d->readable();
				}
				return;
			}
			else if( name == g_pluginSearchPathOptionName )
			{
				// We must include the OSL searchpaths in Arnold's shader
				// searchpaths so that the OSL shaders can be found.
				const char *searchPath = getenv( "OSL_SHADER_PATHS" );
				std::string s( searchPath ? searchPath : "" );
				if( value )
				{
					if( const IECore::StringData *d = reportedCast<const IECore::StringData>( value, "option", name ) )
					{
						s = d->readable() + ":" + s;
					}
				}
				AiNodeSetStr( options, "plugin_searchpath", s.c_str() );
				return;
			}
			else if( boost::starts_with( name.c_str(), "ai:declare:" ) )
			{
				const AtParamEntry *parameter = AiNodeEntryLookUpParameter( AiNodeGetNodeEntry( options ), name.c_str() + 11 );
				if( parameter )
				{
					IECore::msg( IECore::Msg::Warning, "IECoreArnold::Renderer::option", boost::format( "Unable to declare existing option \"%s\"." ) % (name.c_str() + 11) );
				}
				else
				{
					const AtUserParamEntry *userParameter = AiNodeLookUpUserParameter( options, name.c_str() + 11);
					if( userParameter )
					{
						AiNodeResetParameter( options, name.c_str() + 11 );
					}
					if( value )
					{
						ParameterAlgo::setParameter( options, name.c_str() + 11, value );
					}
				}
				return;
			}
			else if( boost::starts_with( name.c_str(), "ai:" ) )
			{
				const AtParamEntry *parameter = AiNodeEntryLookUpParameter( AiNodeGetNodeEntry( options ), name.c_str() + 3 );
				if( parameter )
				{
					if( value )
					{
						ParameterAlgo::setParameter( options, name.c_str() + 3, value );
					}
					else
					{
						AiNodeResetParameter( options, name.c_str() + 3 );
					}
					return;
				}
			}
			else if( boost::starts_with( name.c_str(), "user:" ) )
			{
				if( value )
				{
					ParameterAlgo::setParameter( options, name.c_str(), value );
				}
				else
				{
					AiNodeResetParameter( options, name.c_str() );
				}
				return;
			}
			else if( boost::contains( name.c_str(), ":" ) )
			{
				// Ignore options prefixed for some other renderer.
				return;
			}

			IECore::msg( IECore::Msg::Warning, "IECoreArnold::Renderer::option", boost::format( "Unknown option \"%s\"." ) % name.c_str() );
		}

		void output( const IECore::InternedString &name, const IECoreScenePreview::Renderer::Output *output )
		{
			m_outputs.erase( name );
			if( output )
			{
				try
				{
					m_outputs[name] = new ArnoldOutput( name, output, nodeDeleter( m_renderType ) );
				}
				catch( const std::exception &e )
				{
					IECore::msg( IECore::Msg::Warning, "IECoreArnold::Renderer::output", e.what() );
				}
			}

			IECore::StringVectorDataPtr outputs = new IECore::StringVectorData;
			for( OutputMap::const_iterator it = m_outputs.begin(), eIt = m_outputs.end(); it != eIt; ++it )
			{
				outputs->writable().push_back( it->second->string() );
			}

			IECoreArnold::ParameterAlgo::setParameter( AiUniverseGetOptions(), "outputs", outputs.get() );
		}

		// Some of Arnold's globals come from camera parameters, so the
		// ArnoldRenderer calls this method to notify the ArnoldGlobals
		// of each camera as it is created.
		void camera( const std::string &name, IECore::ConstCameraPtr camera )
		{
			m_cameras[name] = camera;
		}

		void render()
		{
			updateCamera();
			AiNodeSetInt(
				AiUniverseGetOptions(), "AA_seed",
				m_aaSeed.get_value_or( m_frame.get_value_or( 1 ) )
			);

			// Do the appropriate render based on
			// m_renderType.
			switch( m_renderType )
			{
				case IECoreScenePreview::Renderer::Batch :
				{
					const int result = AiRender( AI_RENDER_MODE_CAMERA );
					if( result != AI_SUCCESS )
					{
						throwError( result );
					}
					break;
				}
				case IECoreScenePreview::Renderer::SceneDescription :
					AiASSWrite( m_assFileName.c_str(), AI_NODE_ALL );
					break;
				case IECoreScenePreview::Renderer::Interactive :
					m_interactiveRenderController.setRendering( true );
					break;
			}
		}

		void pause()
		{
			m_interactiveRenderController.setRendering( false );
		}

	private :

		void throwError( int errorCode )
		{
			switch( errorCode )
			{
				case AI_ABORT :
					throw IECore::Exception( "Render aborted" );
				case AI_ERROR_WRONG_OUTPUT :
					throw IECore::Exception( "Can't open output file" );
				case AI_ERROR_NO_CAMERA :
					throw IECore::Exception( "Camera not defined" );
				case AI_ERROR_BAD_CAMERA :
					throw IECore::Exception( "Bad camera" );
				case AI_ERROR_VALIDATION :
					throw IECore::Exception( "Usage not validated" );
				case AI_ERROR_RENDER_REGION :
					throw IECore::Exception( "Invalid render region" );
				case AI_ERROR_OUTPUT_EXISTS :
					throw IECore::Exception( "Output file already exists" );
				case AI_ERROR_OPENING_FILE :
					throw IECore::Exception( "Can't open file" );
				case AI_INTERRUPT :
					throw IECore::Exception( "Render interrupted by user" );
				case AI_ERROR_UNRENDERABLE_SCENEGRAPH :
					throw IECore::Exception( "Unrenderable scenegraph" );
				case AI_ERROR_NO_OUTPUTS :
					throw IECore::Exception( "No outputs" );
				case AI_ERROR :
					throw IECore::Exception( "Generic Arnold error" );
			}
		}

		bool updateLogFlags( const std::string name, const IECore::Data *value, bool console )
		{
			int flagToModify = AI_LOG_NONE;
			if( name == "info" )
			{
				flagToModify = AI_LOG_INFO;
			}
			else if( name == "warnings" )
			{
				flagToModify = AI_LOG_WARNINGS;
			}
			else if( name == "errors" )
			{
				flagToModify = AI_LOG_ERRORS;
			}
			else if( name == "debug" )
			{
				flagToModify = AI_LOG_DEBUG;
			}
			else if( name == "stats" )
			{
				flagToModify = AI_LOG_STATS;
			}
			else if( name == "ass_parse" )
			{
				flagToModify = AI_LOG_ASS_PARSE;
			}
			else if( name == "plugins" )
			{
				flagToModify = AI_LOG_PLUGINS;
			}
			else if( name == "progress" )
			{
				flagToModify = AI_LOG_PROGRESS;
			}
			else if( name == "nan" )
			{
				flagToModify = AI_LOG_NAN;
			}
			else if( name == "timestamp" )
			{
				flagToModify = AI_LOG_TIMESTAMP;
			}
			else if( name == "backtrace" )
			{
				flagToModify = AI_LOG_BACKTRACE;
			}
			else if( name == "memory" )
			{
				flagToModify = AI_LOG_MEMORY;
			}
			else if( name == "color" )
			{
				flagToModify = AI_LOG_COLOR;
			}
			else
			{
				return false;
			}

			bool turnOn = false;
			if( value == nullptr )
			{
				turnOn = flagToModify & ( console == false ? g_logFlagsDefault : g_consoleFlagsDefault );
			}
			else if( const IECore::BoolData *d = reportedCast<const IECore::BoolData>( value, "option", name ) )
			{
				turnOn = d->readable();
			}
			else
			{
				return true;
			}

			int &flags = console ? m_consoleFlags : m_logFileFlags;
			if( turnOn )
			{
				flags |= flagToModify;
			}
			else
			{
				flags = flags & ~flagToModify;
			}

			if( console )
			{
				AiMsgSetConsoleFlags( flags );
			}
			else
			{
				AiMsgSetLogFileFlags( flags );
			}

			return true;
		}

		void updateCamera()
		{
			AtNode *options = AiUniverseGetOptions();

			const IECore::Camera *cortexCamera;
			AtNode *arnoldCamera = AiNodeLookUpByName( m_cameraName.c_str() );
			if( arnoldCamera )
			{
				cortexCamera = m_cameras[m_cameraName].get();
				m_defaultCamera = nullptr;
			}
			else
			{
				if( !m_defaultCamera )
				{
					IECore::CameraPtr defaultCortexCamera = new IECore::Camera();
					defaultCortexCamera->addStandardParameters();
					m_cameras["ieCoreArnold:defaultCamera"] = defaultCortexCamera;
					m_defaultCamera = SharedAtNodePtr(
						namespacedCameraAlgoConvert( defaultCortexCamera.get(), "ieCoreArnold:defaultCamera", nullptr ),
						nodeDeleter( m_renderType )
					);
				}
				cortexCamera = m_cameras["ieCoreArnold:defaultCamera"].get();
				arnoldCamera = m_defaultCamera.get();
			}
			AiNodeSetPtr( options, "camera", arnoldCamera );

			const IECore::V2iData *resolution = cortexCamera->parametersData()->member<IECore::V2iData>( "resolution" );
			AiNodeSetInt( options, "xres", resolution->readable().x );
			AiNodeSetInt( options, "yres", resolution->readable().y );

			const IECore::FloatData *pixelAspectRatio = cortexCamera->parametersData()->member<IECore::FloatData>( "pixelAspectRatio" );
			AiNodeSetFlt( options, "pixel_aspect_ratio", pixelAspectRatio->readable() );

			const IECore::Box2iData *renderRegion = cortexCamera->parametersData()->member<IECore::Box2iData>( "renderRegion" );

			if( renderRegion )
			{
				if( renderRegion->readable().isEmpty() )
				{
					// Arnold does not permit empty render regions.  The user intent of an empty render
					// region is probably to render as little as possible ( it could happen if you
					// built a tool to crop to an object which passed out of frame ).
					// We just pick one pixel in the corner

					AiNodeSetInt( options, "region_min_x", 0 );
					AiNodeSetInt( options, "region_min_y", 0 );
					AiNodeSetInt( options, "region_max_x", 0 );
					AiNodeSetInt( options, "region_max_y", 0 );
				}
				else
				{
					AiNodeSetInt( options, "region_min_x", renderRegion->readable().min.x );
					AiNodeSetInt( options, "region_min_y", renderRegion->readable().min.y );
					AiNodeSetInt( options, "region_max_x", renderRegion->readable().max.x );
					AiNodeSetInt( options, "region_max_y", renderRegion->readable().max.y );
				}
			}
			else
			{
				AiNodeResetParameter( options, "region_min_x" );
				AiNodeResetParameter( options, "region_min_y" );
				AiNodeResetParameter( options, "region_max_x" );
				AiNodeResetParameter( options, "region_max_y" );
			}

			Imath::V2f shutter = cortexCamera->parametersData()->member<IECore::V2fData>( "shutter", true )->readable();
			if( m_sampleMotion.get_value_or( true ) )
			{
				AiNodeSetFlt( arnoldCamera, "shutter_start", shutter[0] );
				AiNodeSetFlt( arnoldCamera, "shutter_end", shutter[1] );
			}
			else
			{
				AiNodeSetFlt( arnoldCamera, "shutter_start", shutter[0] );
				AiNodeSetFlt( arnoldCamera, "shutter_end", shutter[0] );
			}
		}

		// Members used by all render types

		IECoreScenePreview::Renderer::RenderType m_renderType;

		IECoreArnold::UniverseBlock m_universeBlock;

		typedef std::map<IECore::InternedString, ArnoldOutputPtr> OutputMap;
		OutputMap m_outputs;

		std::string m_cameraName;
		typedef tbb::concurrent_unordered_map<std::string, IECore::ConstCameraPtr> CameraMap;
		CameraMap m_cameras;
		SharedAtNodePtr m_defaultCamera;

		int m_logFileFlags;
		int m_consoleFlags;
		boost::optional<int> m_frame;
		boost::optional<int> m_aaSeed;
		boost::optional<bool> m_sampleMotion;

		// Members used by interactive renders

		InteractiveRenderController m_interactiveRenderController;

		// Members used by ass generation "renders"

		std::string m_assFileName;

};

} // namespace

//////////////////////////////////////////////////////////////////////////
// ArnoldRendererBase definition
//////////////////////////////////////////////////////////////////////////

namespace
{

ArnoldRendererBase::ArnoldRendererBase( NodeDeleter nodeDeleter, AtNode *parentNode )
	:	m_nodeDeleter( nodeDeleter ),
		m_shaderCache( new ShaderCache( nodeDeleter, parentNode ) ),
		m_instanceCache( new InstanceCache( nodeDeleter, parentNode ) ),
		m_parentNode( parentNode )
{
}

ArnoldRendererBase::~ArnoldRendererBase()
{
}

ArnoldRendererBase::AttributesInterfacePtr ArnoldRendererBase::attributes( const IECore::CompoundObject *attributes )
{
	return new ArnoldAttributes( attributes, m_shaderCache.get() );
}

ArnoldRendererBase::ObjectInterfacePtr ArnoldRendererBase::camera( const std::string &name, const IECore::Camera *camera, const AttributesInterface *attributes )
{
	IECore::CameraPtr cameraCopy = camera->copy();
	cameraCopy->addStandardParameters();

	Instance instance = m_instanceCache->get( camera, attributes, name );

	ObjectInterfacePtr result = new ArnoldObject( instance );
	result->attributes( attributes );
	return result;
}

ArnoldRendererBase::ObjectInterfacePtr ArnoldRendererBase::light( const std::string &name, const IECore::Object *object, const AttributesInterface *attributes )
{
	Instance instance = m_instanceCache->get( object, attributes, name );
	ObjectInterfacePtr result = new ArnoldLight( name, instance, m_nodeDeleter, m_parentNode );
	result->attributes( attributes );
	return result;
}

ArnoldRendererBase::ObjectInterfacePtr ArnoldRendererBase::object( const std::string &name, const IECore::Object *object, const AttributesInterface *attributes )
{
	Instance instance = m_instanceCache->get( object, attributes, name );
	ObjectInterfacePtr result = new ArnoldObject( instance );
	result->attributes( attributes );
	return result;
}

ArnoldRendererBase::ObjectInterfacePtr ArnoldRendererBase::object( const std::string &name, const std::vector<const IECore::Object *> &samples, const std::vector<float> &times, const AttributesInterface *attributes )
{
	Instance instance = m_instanceCache->get( samples, times, attributes, name );
	ObjectInterfacePtr result = new ArnoldObject( instance );
	result->attributes( attributes );
	return result;
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// ArnoldRenderer
//////////////////////////////////////////////////////////////////////////

namespace
{

/// The full renderer implementation as presented to the outside world.
class ArnoldRenderer final : public ArnoldRendererBase
{

	public :

		ArnoldRenderer( RenderType renderType, const std::string &fileName )
			:	ArnoldRendererBase( nodeDeleter( renderType ) ),
				m_globals( new ArnoldGlobals( renderType, fileName ) )
		{
		}

		~ArnoldRenderer() override
		{
			pause();
		}

		void option( const IECore::InternedString &name, const IECore::Data *value ) override
		{
			m_globals->option( name, value );
		}

		void output( const IECore::InternedString &name, const Output *output ) override
		{
			m_globals->output( name, output );
		}

		ObjectInterfacePtr camera( const std::string &name, const IECore::Camera *camera, const AttributesInterface *attributes ) override
		{
			IECore::CameraPtr cameraCopy = camera->copy();
			cameraCopy->addStandardParameters();
			m_globals->camera( name, cameraCopy.get() );
			return ArnoldRendererBase::camera( name, camera, attributes );
		}

		void render() override
		{
			m_shaderCache->clearUnused();
			m_instanceCache->clearUnused();
			m_globals->render();
		}

		void pause() override
		{
			m_globals->pause();
		}

	private :

		std::unique_ptr<ArnoldGlobals> m_globals;

		// Registration with factory

		static Renderer::TypeDescription<ArnoldRenderer> g_typeDescription;

};

IECoreScenePreview::Renderer::TypeDescription<ArnoldRenderer> ArnoldRenderer::g_typeDescription( "Arnold" );

} // namespace
