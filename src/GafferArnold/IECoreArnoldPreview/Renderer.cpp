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

#include "tbb/compat/thread"
#include "tbb/concurrent_vector.h"
#include "tbb/concurrent_unordered_map.h"

#include "boost/make_shared.hpp"
#include "boost/format.hpp"
#include "boost/algorithm/string/predicate.hpp"
#include "boost/algorithm/string/join.hpp"
#include "boost/container/flat_map.hpp"
#include "boost/filesystem/operations.hpp"

#include "IECore/MessageHandler.h"
#include "IECore/Camera.h"
#include "IECore/Transform.h"
#include "IECore/VectorTypedData.h"
#include "IECore/SimpleTypedData.h"
#include "IECore/ObjectVector.h"
#include "IECore/Shader.h"
#include "IECore/MeshPrimitive.h"
#include "IECore/CurvesPrimitive.h"

#include "IECoreArnold/ParameterAlgo.h"
#include "IECoreArnold/CameraAlgo.h"
#include "IECoreArnold/NodeAlgo.h"
#include "IECoreArnold/UniverseBlock.h"

#include "Gaffer/StringAlgo.h"

#include "GafferScene/Private/IECoreScenePreview/Renderer.h"

#include "GafferArnold/Private/IECoreArnoldPreview/ShaderAlgo.h"

using namespace std;
using namespace boost::filesystem;
using namespace IECoreArnold;
using namespace IECoreArnoldPreview;

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

	IECore::msg( IECore::Msg::Warning, "IECoreArnold::Renderer", boost::format( "Expected %s but got %s for %s \"%s\"." ) % T::staticTypeName() % v->typeName() % type % name.c_str() );
	return NULL;
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

} // namespace

//////////////////////////////////////////////////////////////////////////
// ArnoldOutput
//////////////////////////////////////////////////////////////////////////

namespace
{

class ArnoldOutput : public IECore::RefCounted
{

	public :

		ArnoldOutput( const IECore::InternedString &name, const IECoreScenePreview::Renderer::Output *output )
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

			m_driver.reset( AiNode( driverNodeType.c_str() ), AiNodeDestroy );
			if( !m_driver )
			{
				throw IECore::Exception( boost::str( boost::format( "Unable to create output driver of type \"%s\"" ) % driverNodeType ) );
			}

			const std::string driverNodeName = boost::str( boost::format( "ieCoreArnold:display:%s" ) % name.string() );
			AiNodeSetStr( m_driver.get(), "name", driverNodeName.c_str() );

			if( const AtParamEntry *fileNameParameter = AiNodeEntryLookUpParameter( AiNodeGetNodeEntry( m_driver.get() ), "filename" ) )
			{
				AiNodeSetStr( m_driver.get(), AiParamGetName( fileNameParameter ), output->getName().c_str() );
			}

			for( IECore::CompoundDataMap::const_iterator it = output->parameters().begin(), eIt = output->parameters().end(); it != eIt; ++it )
			{
				if( boost::starts_with( it->first.string(), "filter" ) )
				{
					continue;
				}
				ParameterAlgo::setParameter( m_driver.get(), it->first.c_str(), it->second.get() );
			}

			// Create a filter.

			std::string filterNodeType = parameter<std::string>( output->parameters(), "filter", "gaussian" );
			if( AiNodeEntryGetType( AiNodeEntryLookUp( filterNodeType.c_str() ) ) != AI_NODE_FILTER )
			{
				filterNodeType = filterNodeType + "_filter";
			}

			m_filter.reset( AiNode( filterNodeType.c_str() ), AiNodeDestroy );
			if( AiNodeEntryGetType( AiNodeGetNodeEntry( m_filter.get() ) ) != AI_NODE_FILTER )
			{
				throw IECore::Exception( boost::str( boost::format( "Unable to create filter of type \"%s\"" ) % filterNodeType ) );
			}

			const std::string filterNodeName = boost::str( boost::format( "ieCoreArnold:filter:%s" ) % name.string() );
			AiNodeSetStr( m_filter.get(), "name", filterNodeName.c_str() );

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
				Gaffer::tokenize( m_data, ' ', tokens );
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

		boost::shared_ptr<AtNode> m_driver;
		boost::shared_ptr<AtNode> m_filter;
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

		ArnoldShader( const IECore::ObjectVector *shaderNetwork, const std::string &namePrefix = "" )
		{
			m_nodes = ShaderAlgo::convert( shaderNetwork, namePrefix );
		}

		virtual ~ArnoldShader()
		{
			for( std::vector<AtNode *>::const_iterator it = m_nodes.begin(), eIt = m_nodes.end(); it != eIt; ++it )
			{
				AiNodeDestroy( *it );
			}
		}

		AtNode *root()
		{
			return !m_nodes.empty() ? m_nodes.back() : NULL;
		}

	private :

		std::vector<AtNode *> m_nodes;

};

IE_CORE_DECLAREPTR( ArnoldShader )

class ShaderCache : public IECore::RefCounted
{

	public :

		// Can be called concurrently with other get() calls.
		ArnoldShaderPtr get( const IECore::ObjectVector *shader )
		{
			Cache::accessor a;
			m_cache.insert( a, shader->Object::hash() );
			if( !a->second )
			{
				a->second = new ArnoldShader( shader, "shader:" + shader->Object::hash().toString() + ":" );
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

	private :

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
IECore::InternedString g_reflectedVisibilityAttributeName( "ai:visibility:reflected" );
IECore::InternedString g_refractedVisibilityAttributeName( "ai:visibility:refracted" );
IECore::InternedString g_diffuseVisibilityAttributeName( "ai:visibility:diffuse" );
IECore::InternedString g_glossyVisibilityAttributeName( "ai:visibility:glossy" );

IECore::InternedString g_arnoldSurfaceShaderAttributeName( "ai:surface" );
IECore::InternedString g_arnoldLightShaderAttributeName( "ai:light" );

IECore::InternedString g_arnoldReceiveShadowsAttributeName( "ai:receive_shadows" );
IECore::InternedString g_arnoldSelfShadowsAttributeName( "ai:self_shadows" );
IECore::InternedString g_arnoldOpaqueAttributeName( "ai:opaque" );
IECore::InternedString g_arnoldMatteAttributeName( "ai:matte" );

IECore::InternedString g_polyMeshSubdivIterationsAttributeName( "ai:polymesh:subdiv_iterations" );
IECore::InternedString g_polyMeshSubdivAdaptiveErrorAttributeName( "ai:polymesh:subdiv_adaptive_error" );
IECore::InternedString g_polyMeshSubdivAdaptiveMetricAttributeName( "ai:polymesh:subdiv_adaptive_metric" );
IECore::InternedString g_polyMeshSubdivAdaptiveSpaceAttributeName( "ai:polymesh:subdiv_adaptive_space" );
IECore::InternedString g_polyMeshSubdividePolygonsAttributeName( "ai:polymesh:subdividePolygons" );
IECore::InternedString g_objectSpace( "object" );

IECore::InternedString g_dispMapAttributeName( "ai:disp_map" );
IECore::InternedString g_dispHeightAttributeName( "ai:disp_height" );
IECore::InternedString g_dispPaddingAttributeName( "ai:disp_padding" );
IECore::InternedString g_dispZeroValueAttributeName( "ai:disp_zero_value" );
IECore::InternedString g_dispAutoBumpAttributeName( "ai:disp_autobump" );

IECore::InternedString g_curvesMinPixelWidthAttributeName( "ai:curves:min_pixel_width" );
IECore::InternedString g_curvesModeAttributeName( "ai:curves:mode" );

class ArnoldAttributes : public IECoreScenePreview::Renderer::AttributesInterface
{

	public :

		struct PolyMesh
		{

			PolyMesh( const IECore::CompoundObject *attributes )
			{
				subdivIterations = attributeValue<int>( g_polyMeshSubdivIterationsAttributeName, attributes, 1 );
				subdivAdaptiveError = attributeValue<float>( g_polyMeshSubdivAdaptiveErrorAttributeName, attributes, 0.0f );
				subdivAdaptiveMetric = attributeValue<string>( g_polyMeshSubdivAdaptiveMetricAttributeName, attributes, "auto" );
				subdivAdaptiveSpace = attributeValue<string>( g_polyMeshSubdivAdaptiveSpaceAttributeName, attributes, "raster" );
				subdividePolygons = attributeValue<bool>( g_polyMeshSubdividePolygonsAttributeName, attributes, false );
			}

			int subdivIterations;
			float subdivAdaptiveError;
			IECore::InternedString subdivAdaptiveMetric;
			IECore::InternedString subdivAdaptiveSpace;
			bool subdividePolygons;

			void hash( const IECore::MeshPrimitive *mesh, IECore::MurmurHash &h ) const
			{
				if( mesh->interpolation() != "linear" || subdividePolygons )
				{
					h.append( subdivIterations );
					h.append( subdivAdaptiveError );
					h.append( subdivAdaptiveMetric );
					h.append( subdivAdaptiveSpace );
					h.append( subdividePolygons );
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

		ArnoldAttributes( const IECore::CompoundObject *attributes, ShaderCache *shaderCache )
			:	visibility( AI_RAY_ALL ), sidedness( AI_RAY_ALL ), shadingFlags( Default ), polyMesh( attributes ), displacement( attributes, shaderCache ), curves( attributes )
		{
			updateVisibility( g_cameraVisibilityAttributeName, AI_RAY_CAMERA, attributes );
			updateVisibility( g_shadowVisibilityAttributeName, AI_RAY_SHADOW, attributes );
			updateVisibility( g_reflectedVisibilityAttributeName, AI_RAY_REFLECTED, attributes );
			updateVisibility( g_refractedVisibilityAttributeName, AI_RAY_REFRACTED, attributes );
			updateVisibility( g_diffuseVisibilityAttributeName, AI_RAY_DIFFUSE, attributes );
			updateVisibility( g_glossyVisibilityAttributeName, AI_RAY_GLOSSY, attributes );

			if( const IECore::BoolData *d = attribute<IECore::BoolData>( g_doubleSidedAttributeName, attributes ) )
			{
				sidedness = d->readable() ? AI_RAY_ALL : AI_RAY_UNDEFINED;
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
				surfaceShader = shaderCache->get( surfaceShaderAttribute );
			}

			lightShader = attribute<IECore::ObjectVector>( g_arnoldLightShaderAttributeName, attributes );
			lightShader = lightShader ? lightShader : attribute<IECore::ObjectVector>( g_lightShaderAttributeName, attributes );

			traceSets = attribute<IECore::InternedStringVectorData>( g_setsAttributeName, attributes );

			for( IECore::CompoundObject::ObjectMap::const_iterator it = attributes->members().begin(), eIt = attributes->members().end(); it != eIt; ++it )
			{
				if( !boost::starts_with( it->first.string(), "user:" ) )
				{
					continue;
				}
				if( const IECore::Data *data = IECore::runTimeCast<const IECore::Data>( it->second.get() ) )
				{
					user[it->first] = data;
				}
			}
		}

		enum ShadingFlags
		{
			ReceiveShadows = 1,
			SelfShadows = 2,
			Opaque = 4,
			Matte = 8,
			Default = ReceiveShadows | SelfShadows | Opaque,
			All = ReceiveShadows | SelfShadows | Opaque | Matte
		};

		unsigned char visibility;
		unsigned char sidedness;
		unsigned char shadingFlags;
		ArnoldShaderPtr surfaceShader;
		IECore::ConstObjectVectorPtr lightShader;
		IECore::ConstInternedStringVectorDataPtr traceSets;
		PolyMesh polyMesh;
		Displacement displacement;
		Curves curves;

		typedef boost::container::flat_map<IECore::InternedString, IECore::ConstDataPtr> UserAttributes;
		UserAttributes user;

	private :

		template<typename T>
		static const T *attribute( const IECore::InternedString &name, const IECore::CompoundObject *attributes )
		{
			IECore::CompoundObject::ObjectMap::const_iterator it = attributes->members().find( name );
			if( it == attributes->members().end() )
			{
				return NULL;
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
					visibility |= rayType;
				}
				else
				{
					visibility = visibility & ~rayType;
				}
			}
		}

		void updateShadingFlag( const IECore::InternedString &name, unsigned char flag, const IECore::CompoundObject *attributes )
		{
			if( const IECore::BoolData *d = attribute<IECore::BoolData>( name, attributes ) )
			{
				if( d->readable() )
				{
					shadingFlags |= flag;
				}
				else
				{
					shadingFlags = shadingFlags & ~flag;
				}
			}
		}

};

} // namespace

//////////////////////////////////////////////////////////////////////////
// InstanceCache
//////////////////////////////////////////////////////////////////////////

class Instance
{

	public :

		Instance( boost::shared_ptr<AtNode> node, bool instanced, ArnoldShaderPtr displacementShader )
			:	m_node( node ), m_displacementShader( displacementShader )
		{
			if( instanced && node )
			{
				AiNodeSetByte( node.get(), "visibility", 0 );
				m_ginstance = boost::shared_ptr<AtNode>( AiNode( "ginstance" ), AiNodeDestroy );
				AiNodeSetPtr( m_ginstance.get(), "node", m_node.get() );
			}
		}

		AtNode *node()
		{
			return m_ginstance.get() ? m_ginstance.get() : m_node.get();
		}

	private :

		boost::shared_ptr<AtNode> m_node;
		boost::shared_ptr<AtNode> m_ginstance;
		// The displacement shader is effectively part of the geometry
		// in Arnold, so the Instance must keep it alive in tandem with
		// m_node.
		ArnoldShaderPtr m_displacementShader;

};

class InstanceCache : public IECore::RefCounted
{

	public :

		// Can be called concurrently with other get() calls.
		Instance get( const IECore::Object *object, const IECoreScenePreview::Renderer::AttributesInterface *attributes )
		{
			const ArnoldAttributes *arnoldAttributes = static_cast<const ArnoldAttributes *>( attributes );

			if( !canInstance( object, arnoldAttributes ) )
			{
				return Instance( convert( object, arnoldAttributes ), /* instanced = */ false, arnoldAttributes->displacement.map );
			}

			IECore::MurmurHash h = object->hash();
			hashAttributes( object, arnoldAttributes, h );

			Cache::accessor a;
			m_cache.insert( a, h );
			if( !a->second )
			{
				a->second = convert( object, arnoldAttributes );
				if( a->second )
				{
					std::string name = "instance:" + h.toString();
					AiNodeSetStr( a->second.get(), "name", name.c_str() );
				}
			}

			return Instance( a->second, /* instanced = */ true, arnoldAttributes->displacement.map );
		}

		Instance get( const std::vector<const IECore::Object *> &samples, const std::vector<float> &times, const IECoreScenePreview::Renderer::AttributesInterface *attributes )
		{
			const ArnoldAttributes *arnoldAttributes = static_cast<const ArnoldAttributes *>( attributes );

			if( !canInstance( samples.front(), arnoldAttributes ) )
			{
				return Instance( convert( samples, times, arnoldAttributes ), /* instanced = */ false, arnoldAttributes->displacement.map );
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
			hashAttributes( samples.front(), arnoldAttributes, h );

			Cache::accessor a;
			m_cache.insert( a, h );
			if( !a->second )
			{
				a->second = convert( samples, times, arnoldAttributes );
				if( a->second )
				{
					std::string name = "instance:" + h.toString();
					AiNodeSetStr( a->second.get(), "name", name.c_str() );
				}
			}

			return Instance( a->second, /* instanced = */ true, arnoldAttributes->displacement.map );
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

	private :

		bool canInstance( const IECore::Object *object, const ArnoldAttributes *attributes )
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
					return attributes->polyMesh.subdivAdaptiveError == 0.0f || attributes->polyMesh.subdivAdaptiveSpace == g_objectSpace;
				}
			}

			return true;
		}

		void hashAttributes( const IECore::Object *object, const ArnoldAttributes *attributes, IECore::MurmurHash &h )
		{
			// Take account of the fact that in `convert()` we will apply shape specific
			// attributes to the resulting node (via `applyAttributes()`).
			if( const IECore::MeshPrimitive *mesh = IECore::runTimeCast<const IECore::MeshPrimitive>( object ) )
			{
				attributes->polyMesh.hash( mesh, h );
				attributes->displacement.hash( h );
			}
			else if( IECore::runTimeCast<const IECore::CurvesPrimitive>( object ) )
			{
				attributes->curves.hash( h );
			}
		}

		void applyAttributes( const IECore::Object *object, const ArnoldAttributes *attributes, AtNode *node )
		{
			if( const IECore::MeshPrimitive *mesh = IECore::runTimeCast<const IECore::MeshPrimitive>( object ) )
			{
				attributes->polyMesh.apply( mesh, node );
				attributes->displacement.apply( node );
			}
			else if( IECore::runTimeCast<const IECore::CurvesPrimitive>( object ) )
			{
				attributes->curves.apply( node );
			}
		}

		boost::shared_ptr<AtNode> convert( const IECore::Object *object, const ArnoldAttributes *attributes )
		{
			if( !object )
			{
				return boost::shared_ptr<AtNode>();
			}

			AtNode *node = NodeAlgo::convert( object );
			if( !node )
			{
				return boost::shared_ptr<AtNode>();
			}

			applyAttributes( object, attributes, node );

			return boost::shared_ptr<AtNode>( node, AiNodeDestroy );
		}

		boost::shared_ptr<AtNode> convert( const std::vector<const IECore::Object *> &samples, const std::vector<float> &times, const ArnoldAttributes *attributes )
		{
			AtNode *node = NodeAlgo::convert( samples, times );
			if( !node )
			{
				return boost::shared_ptr<AtNode>();
			}

			applyAttributes( samples.front(), attributes, node );

			return boost::shared_ptr<AtNode>( node, AiNodeDestroy );

		}

		typedef tbb::concurrent_hash_map<IECore::MurmurHash, boost::shared_ptr<AtNode> > Cache;
		Cache m_cache;

};

IE_CORE_DECLAREPTR( InstanceCache )

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
			:	m_instance( instance )
		{
		}

		virtual void transform( const Imath::M44f &transform )
		{
			AtNode *node = m_instance.node();
			if( !node )
			{
				return;
			}
			applyTransform( node, transform );
		}

		virtual void transform( const std::vector<Imath::M44f> &samples, const std::vector<float> &times )
		{
			AtNode *node = m_instance.node();
			if( !node )
			{
				return;
			}
			applyTransform( node, samples, times );
		}

		virtual void attributes( const IECoreScenePreview::Renderer::AttributesInterface *attributes )
		{
			AtNode *node = m_instance.node();
			if( !node )
			{
				return;
			}

			const ArnoldAttributes *arnoldAttributes = static_cast<const ArnoldAttributes *>( attributes );

			// Remove old user parameters we don't want any more.

			AtUserParamIterator *it= AiNodeGetUserParamIterator( node );
			while( !AiUserParamIteratorFinished( it ) )
			{
				const AtUserParamEntry *param = AiUserParamIteratorGetNext( it );
				const char *name = AiUserParamGetName( param );
				if( boost::starts_with( name, "user:" ) )
				{
					if( arnoldAttributes->user.find( name ) == arnoldAttributes->user.end() )
					{
						AiNodeResetParameter( node, name );
					}
				}
			}
			AiUserParamIteratorDestroy( it );

			// Add user parameters we do want.

			for( ArnoldAttributes::UserAttributes::const_iterator it = arnoldAttributes->user.begin(), eIt = arnoldAttributes->user.end(); it != eIt; ++it )
			{
				ParameterAlgo::setParameter( node, it->first.c_str(), it->second.get() );
			}

			// Add shape specific parameters.

			if( AiNodeEntryGetType( AiNodeGetNodeEntry( node ) ) == AI_NODE_SHAPE )
			{
				AiNodeSetByte( node, "visibility", arnoldAttributes->visibility );
				AiNodeSetByte( node, "sidedness", arnoldAttributes->sidedness );

				AiNodeSetBool( node, "receive_shadows", arnoldAttributes->shadingFlags & ArnoldAttributes::ReceiveShadows );
				AiNodeSetBool( node, "self_shadows", arnoldAttributes->shadingFlags & ArnoldAttributes::SelfShadows );
				AiNodeSetBool( node, "opaque", arnoldAttributes->shadingFlags & ArnoldAttributes::Opaque );
				AiNodeSetBool( node, "matte", arnoldAttributes->shadingFlags & ArnoldAttributes::Matte );

				m_shader = arnoldAttributes->surfaceShader; // Keep shader alive as long as we are alive
				if( m_shader && m_shader->root() )
				{
					AiNodeSetPtr( node, "shader", m_shader->root() );
				}
				else
				{
					AiNodeResetParameter( node, "shader" );
				}

				if( arnoldAttributes->traceSets && arnoldAttributes->traceSets->readable().size() )
				{
					const vector<IECore::InternedString> &v = arnoldAttributes->traceSets->readable();
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
			}

		}

	protected :

		void applyTransform( AtNode *node, const Imath::M44f &transform )
		{
			AiNodeSetMatrix( node, "matrix", const_cast<float (*)[4]>( transform.x ) );
		}

		void applyTransform( AtNode *node, const std::vector<Imath::M44f> &samples, const std::vector<float> &times )
		{
			const size_t numSamples = samples.size();
			AtArray *timesArray = AiArrayAllocate( samples.size(), 1, AI_TYPE_FLOAT );
			AtArray *matricesArray = AiArrayAllocate( 1, numSamples, AI_TYPE_MATRIX );
			for( size_t i = 0; i < numSamples; ++i )
			{
				AiArraySetFlt( timesArray, i, times[i] );
				AiArraySetMtx( matricesArray, i, const_cast<float (*)[4]>( samples[i].x ) );
			}
			AiNodeSetArray( node, "matrix", matricesArray );
			if( AiNodeEntryLookUpParameter( AiNodeGetNodeEntry( node ), "transform_time_samples" ) )
			{
				AiNodeSetArray( node, "transform_time_samples", timesArray );
			}
			else
			{
				AiNodeSetArray( node, "time_samples", timesArray );
			}
		}

		Instance m_instance;
		ArnoldShaderPtr m_shader;

};

} // namespace

//////////////////////////////////////////////////////////////////////////
// ArnoldLight
//////////////////////////////////////////////////////////////////////////

namespace
{

class ArnoldLight : public ArnoldObject
{

	public :

		ArnoldLight( const std::string &name, const Instance &instance )
			:	ArnoldObject( instance ), m_name( name )
		{
		}

		virtual void transform( const Imath::M44f &transform )
		{
			ArnoldObject::transform( transform );
			m_transformMatrices.clear();
			m_transformTimes.clear();
			m_transformMatrices.push_back( transform );
			applyLightTransform();
		}

		virtual void transform( const std::vector<Imath::M44f> &samples, const std::vector<float> &times )
		{
			ArnoldObject::transform( samples, times );
			m_transformMatrices = samples;
			m_transformTimes = times;
			applyLightTransform();
		}

		virtual void attributes( const IECoreScenePreview::Renderer::AttributesInterface *attributes )
		{
			ArnoldObject::attributes( attributes );
			const ArnoldAttributes *arnoldAttributes = static_cast<const ArnoldAttributes *>( attributes );

			// Update light shader.

			m_lightShader = NULL;
			if( !arnoldAttributes->lightShader )
			{
				return;
			}

			m_lightShader = new ArnoldShader( arnoldAttributes->lightShader.get(), "light:" + m_name + ":" );

			// Simplify name for the root shader, for ease of reading of ass files.
			const std::string name = "light:" + m_name;
			AiNodeSetStr( m_lightShader->root(), "name", name.c_str() );

			// Deal with mesh_lights.

			if( AiNodeIs( m_lightShader->root(), "mesh_light" ) )
			{
				if( m_instance.node() )
				{
					AiNodeSetPtr( m_lightShader->root(), "mesh", m_instance.node() );
				}
				else
				{
					// Don't output mesh_lights from locations with no object
					m_lightShader = NULL;
					return;
				}
			}

			applyLightTransform();
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
		ArnoldShaderPtr m_lightShader;

};

} // namespace

//////////////////////////////////////////////////////////////////////////
// ArnoldRenderer
//////////////////////////////////////////////////////////////////////////

namespace
{

/// \todo Should these be defined in the Renderer base class?
/// Or maybe be in a utility header somewhere?
IECore::InternedString g_cameraOptionName( "camera" );
IECore::InternedString g_logFileNameOptionName( "ai:log:filename" );
IECore::InternedString g_shaderSearchPathOptionName( "ai:shader_searchpath" );

class ArnoldRenderer : public IECoreScenePreview::Renderer
{

	public :

		ArnoldRenderer( RenderType renderType, const std::string &fileName )
			:	m_renderType( renderType ),
				m_universeBlock( boost::make_shared<UniverseBlock>(  /* writable = */ true ) ),
				m_shaderCache( new ShaderCache ),
				m_instanceCache( new InstanceCache ),
				m_assFileName( fileName )
		{
			loadOSLShaders();
			/// \todo Control with an option.
			AiMsgSetConsoleFlags( AI_LOG_ALL );
		}

		virtual ~ArnoldRenderer()
		{
			pause();
		}

		virtual void option( const IECore::InternedString &name, const IECore::Data *value )
		{
			AtNode *options = AiUniverseGetOptions();
			if( name == g_cameraOptionName )
			{
				if( value == NULL )
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
				if( value == NULL )
				{
					AiMsgSetLogFileName( "" );
				}
				else if( const IECore::StringData *d = reportedCast<const IECore::StringData>( value, "option", name ) )
				{
					AiMsgSetLogFileName( d->readable().c_str() );

				}
				return;
			}
			else if( name == g_shaderSearchPathOptionName )
			{
				// When generating an ASS file, we must manually insert
				// the paths used by loadOSLShaders() into the shader_searchpath
				// option, otherwise standalone rendering via `kick` will fail
				// to find the shaders.
				string s = m_oslShaderDirectories;
				if( value )
				{
					if( const IECore::StringData *d = reportedCast<const IECore::StringData>( value, "option", name ) )
					{
						s = d->readable() + ":" + s;
					}
				}
				AiNodeSetStr( options, "shader_searchpath", s.c_str() );
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

		virtual void output( const IECore::InternedString &name, const Output *output )
		{
			m_outputs.erase( name );
			if( output )
			{
				try
				{
					m_outputs[name] = new ArnoldOutput( name, output );
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

		virtual Renderer::AttributesInterfacePtr attributes( const IECore::CompoundObject *attributes )
		{
			return new ArnoldAttributes( attributes, m_shaderCache.get() );
		}

		virtual ObjectInterfacePtr camera( const std::string &name, const IECore::Camera *camera, const AttributesInterface *attributes )
		{
			IECore::CameraPtr cameraCopy = camera->copy();
			cameraCopy->addStandardParameters();
			m_cameras[name] = cameraCopy;

			Instance instance = m_instanceCache->get( camera, attributes );
			if( AtNode *node = instance.node() )
			{
				AiNodeSetStr( node, "name", name.c_str() );
			}

			ObjectInterfacePtr result = store( new ArnoldObject( instance ) );
			result->attributes( attributes );
			return result;
		}

		virtual ObjectInterfacePtr light( const std::string &name, const IECore::Object *object, const AttributesInterface *attributes )
		{
			Instance instance = m_instanceCache->get( object, attributes );
			if( AtNode *node = instance.node() )
			{
				AiNodeSetStr( node, "name", name.c_str() );
			}

			ObjectInterfacePtr result = store( new ArnoldLight( name, instance ) );
			result->attributes( attributes );
			return result;
		}

		virtual Renderer::ObjectInterfacePtr object( const std::string &name, const IECore::Object *object, const AttributesInterface *attributes )
		{
			Instance instance = m_instanceCache->get( object, attributes );
			if( AtNode *node = instance.node() )
			{
				AiNodeSetStr( node, "name", name.c_str() );
			}

			ObjectInterfacePtr result = store( new ArnoldObject( instance ) );
			result->attributes( attributes );
			return result;
		}

		virtual ObjectInterfacePtr object( const std::string &name, const std::vector<const IECore::Object *> &samples, const std::vector<float> &times, const AttributesInterface *attributes )
		{
			Instance instance = m_instanceCache->get( samples, times, attributes );
			if( AtNode *node = instance.node() )
			{
				AiNodeSetStr( node, "name", name.c_str() );
			}

			ObjectInterfacePtr result = store( new ArnoldObject( instance ) );
			result->attributes( attributes );
			return result;
		}

		virtual void render()
		{
			updateCamera();
			m_shaderCache->clearUnused();
			m_instanceCache->clearUnused();

			// Do the appropriate render based on
			// m_renderType.
			switch( m_renderType )
			{
				case Batch :
					AiRender( AI_RENDER_MODE_CAMERA );
					break;
				case SceneDescription :
					AiASSWrite( m_assFileName.c_str(), AI_NODE_ALL );
					break;
				case Interactive :
					std::thread thread( performInteractiveRender );
					m_interactiveRenderThread.swap( thread );
					break;
			}
		}

		virtual void pause()
		{
			if( AiRendering() )
			{
				AiRenderInterrupt();
			}
			if( m_interactiveRenderThread.joinable() )
			{
				m_interactiveRenderThread.join();
			}
		}

	private :

		// Arnold supports OSL shaders out of the box if they are
		// placed on the ARNOLD_PLUGIN_PATH. But we want to support
		// any OSL shaders found on the OSL_SHADER_PATHS as well, to
		// be compatible with other OSL hosts within Gaffer. We also
		// want to support shader libraries with shaders in subdirectories,
		// so here we search for such shaders and load them explicitly.
		void loadOSLShaders()
		{
			const char *searchPath = getenv( "OSL_SHADER_PATHS" );
			if( !searchPath )
			{
				return;
			}

			vector<string> paths;
			Gaffer::tokenize( searchPath, ':', paths );

			vector<string> directories;
			for( vector<string>::const_iterator pIt = paths.begin(), peIt = paths.end(); pIt != peIt; ++pIt )
			{
				if( !is_directory( *pIt ) )
				{
					continue;
				}

				AiLoadPlugins( pIt->c_str() );
				directories.push_back( *pIt );

				try
				{
					for( recursive_directory_iterator dIt( *pIt ), deIt; dIt != deIt; ++dIt )
					{
						if( is_directory( *dIt ) )
						{
							AiLoadPlugins( dIt->path().c_str() );
							directories.push_back( dIt->path().string() );
						}
					}
				}
				catch( const filesystem_error & )
				{
				}
			}

			// Make sure SceneDescription mode includes the necessary paths in the
			// ass file.
			m_oslShaderDirectories = boost::algorithm::join( directories, ":" );
			option( g_shaderSearchPathOptionName, NULL );
		}

		ObjectInterfacePtr store( ObjectInterface *objectInterface )
		{
			if( m_renderType != Interactive )
			{
				// Our ObjectInterface class owns the AtNodes it
				// represents. In Interactive mode the client is
				// responsible for keeping it alive as long as the
				// object should exist, but in non-interactive modes
				// we are responsible for ensuring the object doesn't
				// die. Storing it is the simplest approach.
				//
				// \todo We might want to save memory by not storing
				// ObjectInterfaces, but instead giving them the notion
				// of whether or not they own the AtNodes they created.
				m_objects.push_back( objectInterface );
			}
			return objectInterface;
		}

		void updateCamera()
		{
			AtNode *options = AiUniverseGetOptions();

			const IECore::Camera *cortexCamera = m_cameras[m_cameraName].get();
			if( cortexCamera )
			{
				AiNodeSetPtr( options, "camera", AiNodeLookUpByName( m_cameraName.c_str() ) );
				m_defaultCamera = NULL;
			}
			else
			{
				if( !m_defaultCamera )
				{
					IECore::CameraPtr defaultCortexCamera = new IECore::Camera();
					defaultCortexCamera->addStandardParameters();
					IECore::CompoundObjectPtr defaultCortexAttributes = new IECore::CompoundObject();
					AttributesInterfacePtr defaultAttributes = this->attributes( defaultCortexAttributes.get() );
					m_defaultCamera = camera( "ieCoreArnold:defaultCamera", defaultCortexCamera.get(), defaultAttributes.get() );
				}
				cortexCamera = m_cameras["ieCoreArnold:defaultCamera"].get();
				AiNodeSetPtr( options, "camera", AiNodeLookUpByName( "ieCoreArnold:defaultCamera" ) );
			}

			const IECore::V2iData *resolution = cortexCamera->parametersData()->member<IECore::V2iData>( "resolution" );
			AiNodeSetInt( options, "xres", resolution->readable().x );
			AiNodeSetInt( options, "yres", resolution->readable().y );

			const IECore::FloatData *pixelAspectRatio = cortexCamera->parametersData()->member<IECore::FloatData>( "pixelAspectRatio" );
			AiNodeSetFlt( options, "aspect_ratio", 1.0f / pixelAspectRatio->readable() ); // arnold is y/x, we're x/y

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
		}

		// Called in a background thread to control a
		// progressive interactive render.
		static void performInteractiveRender()
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
				if( AiRender( AI_RENDER_MODE_CAMERA ) != AI_SUCCESS )
				{
					// Render cancelled on main thread.
					break;
				}
			}

			// Restore the setting we've been monkeying with.
			AiNodeSetInt( options, "AA_samples", finalAASamples );
		}

		// Members used by all render types.

		RenderType m_renderType;

		boost::shared_ptr<IECoreArnold::UniverseBlock> m_universeBlock;

		std::string m_oslShaderDirectories;

		typedef std::map<IECore::InternedString, ArnoldOutputPtr> OutputMap;
		OutputMap m_outputs;

		std::string m_cameraName;
		typedef tbb::concurrent_unordered_map<std::string, IECore::ConstCameraPtr> CameraMap;
		CameraMap m_cameras;
		ObjectInterfacePtr m_defaultCamera;

		ShaderCachePtr m_shaderCache;
		InstanceCachePtr m_instanceCache;

		// Members used by batch renders

		tbb::concurrent_vector<ObjectInterfacePtr> m_objects;

		// Members used by interactive renders

		std::thread m_interactiveRenderThread;

		// Members used by ass generation "renders"

		std::string m_assFileName;

		// Registration with factory

		static Renderer::TypeDescription<ArnoldRenderer> g_typeDescription;

};

IECoreScenePreview::Renderer::TypeDescription<ArnoldRenderer> ArnoldRenderer::g_typeDescription( "IECoreArnold::Renderer" );

} // namespace
