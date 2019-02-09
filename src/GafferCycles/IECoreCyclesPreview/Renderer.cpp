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
#include "GafferCycles/IECoreCyclesPreview/ShaderNetworkAlgo.h"
#include "GafferCycles/IECoreCyclesPreview/SocketAlgo.h"

#include "IECoreImage/DisplayDriver.h"
#include "IECoreImage/ImageDisplayDriver.h"
#include "IECoreImage/ImagePrimitive.h"
#include "IECoreImage/ImageWriter.h"

#include "IECoreScene/Camera.h"
#include "IECoreScene/CurvesPrimitive.h"
#include "IECoreScene/MeshPrimitive.h"
#include "IECoreScene/Shader.h"
#include "IECoreScene/SpherePrimitive.h"
#include "IECoreScene/Transform.h"

#include "IECore/CompoundParameter.h"
#include "IECore/LRUCache.h"
#include "IECore/FileNameParameter.h"
#include "IECore/MessageHandler.h"
#include "IECore/ObjectVector.h"
#include "IECore/SearchPath.h"
#include "IECore/SimpleTypedData.h"
#include "IECore/StringAlgo.h"
#include "IECore/VectorTypedData.h"
#include "IECore/Writer.h"

#include "OpenEXR/ImathMatrixAlgo.h"

#include "boost/algorithm/string.hpp"
#include "boost/algorithm/string/predicate.hpp"

#include "tbb/concurrent_hash_map.h"

#include <unordered_map>

// Cycles
#include "bvh/bvh_params.h"
#include "device/device.h"
#include "graph/node.h"
#include "graph/node_type.h"
#include "kernel/kernel_types.h"
#include "render/background.h"
#include "render/buffers.h"
#include "render/curves.h"
#include "render/film.h"
#include "render/graph.h"
#include "render/integrator.h"
#include "render/light.h"
#include "render/mesh.h"
#include "render/nodes.h"
#include "render/object.h"
#include "render/osl.h"
#include "render/scene.h"
#include "render/session.h"
#include "subd/subd_dice.h"
#include "util/util_array.h"
#include "util/util_function.h"
#include "util/util_vector.h"

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

//typedef std::unique_ptr<ccl::Camera> CCameraPtr;
typedef std::unique_ptr<ccl::Integrator> CIntegratorPtr;
typedef std::unique_ptr<ccl::Background> CBackgroundPtr;
typedef std::unique_ptr<ccl::Film> CFilmPtr;
typedef std::unique_ptr<ccl::CurveSystemManager> CCurveSystemManagerPtr;
typedef std::unique_ptr<ccl::Light> CLightPtr;
typedef std::shared_ptr<ccl::Camera> SharedCCameraPtr;
typedef std::shared_ptr<ccl::Object> SharedCObjectPtr;
typedef std::shared_ptr<ccl::Light> SharedCLightPtr;
typedef std::shared_ptr<ccl::Mesh> SharedCMeshPtr;
typedef std::shared_ptr<ccl::Shader> SharedCShaderPtr;

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

/*
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
*/

//typedef IECore::LRUCache<std::string, std::string> ShaderSearchPathCache;
//ShaderSearchPathCache g_shaderSearchPathCache( shaderCacheGetter, 10000 );

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
	MAP_PASS( "mist", ccl::PASS_MIST );
	MAP_PASS( "emission", ccl::PASS_EMISSION );
	MAP_PASS( "background", ccl::PASS_BACKGROUND );
	MAP_PASS( "ao", ccl::PASS_AO );
	MAP_PASS( "shadow", ccl::PASS_SHADOW );
#ifdef WITH_CYCLES_DEBUG
	MAP_PASS( "bvh_traversed_nodes", ccl::PASS_BVH_TRAVERSED_NODES );
	MAP_PASS( "bvh_traversed_instances", ccl::PASS_BVH_TRAVERSED_INSTANCES );
	MAP_PASS( "bvh_intersections", ccl::PASS_BVH_INTERSECTIONS );
	MAP_PASS( "ray_bounces", ccl::PASS_RAY_BOUNCES );
#endif
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
	MAP_PASS( "cryptomatte_asset", ccl::PASS_CRYPTOMATTE );
	MAP_PASS( "cryptomatte_object", ccl::PASS_CRYPTOMATTE );
	MAP_PASS( "cryptomatte_material", ccl::PASS_CRYPTOMATTE );
#undef MAP_PASS

	return ccl::PASS_NONE;
}

int passComponents( ccl::PassType type )
{
	switch( type )
	{
		case ccl::PASS_NONE:
			return 0;
		case ccl::PASS_COMBINED:
			return 4;
		case ccl::PASS_DEPTH:
			return 1;
		case ccl::PASS_MIST:
			return 1;
		case ccl::PASS_NORMAL:
			return 3;
		case ccl::PASS_UV:
			return 3;
		case ccl::PASS_MOTION:
			return 4;
		case ccl::PASS_MOTION_WEIGHT:
			return 1;
		case ccl::PASS_OBJECT_ID:
		case ccl::PASS_MATERIAL_ID:
			return 1;
		case ccl::PASS_EMISSION:
		case ccl::PASS_BACKGROUND:
		case ccl::PASS_AO:
		case ccl::PASS_SHADOW:
			return 3;
		case ccl::PASS_LIGHT:
			return 0;
#ifdef WITH_CYCLES_DEBUG
		case ccl::PASS_BVH_TRAVERSED_NODES:
		case ccl::PASS_BVH_TRAVERSED_INSTANCES:
		case ccl::PASS_BVH_INTERSECTIONS:
		case ccl::PASS_RAY_BOUNCES:
			return 1;
#endif
		case ccl::PASS_RENDER_TIME:
			return 0;
		case ccl::PASS_DIFFUSE_COLOR:
		case ccl::PASS_GLOSSY_COLOR:
		case ccl::PASS_TRANSMISSION_COLOR:
		case ccl::PASS_SUBSURFACE_COLOR:
		case ccl::PASS_DIFFUSE_DIRECT:
		case ccl::PASS_DIFFUSE_INDIRECT:
		case ccl::PASS_GLOSSY_DIRECT:
		case ccl::PASS_GLOSSY_INDIRECT:
		case ccl::PASS_TRANSMISSION_DIRECT:
		case ccl::PASS_TRANSMISSION_INDIRECT:
		case ccl::PASS_SUBSURFACE_DIRECT:
		case ccl::PASS_SUBSURFACE_INDIRECT:
		case ccl::PASS_VOLUME_DIRECT:
		case ccl::PASS_VOLUME_INDIRECT:
			return 3;
		case ccl::PASS_CRYPTOMATTE:
			return 4;
		default:
			return 0;
	}
}

class CyclesOutput : public IECore::RefCounted
{

	public :

		CyclesOutput( const IECoreScene::Output *output )
			: m_image( nullptr )
		{
			m_name = output->getName();
			m_type = output->getType();
			m_data = output->getData();
			m_passType = nameToPassType( m_data );
			m_components = passComponents( m_passType );
			m_parameters = output->parametersData()->copy();
			if( m_type == "ieDisplay" )
				m_interactive = true;
			else
				m_interactive = false;

			const vector<int> quantize = parameter<vector<int>>( output->parameters(), "quantize", { 0, 0, 0, 0 } );
			if( quantize == vector<int>( { 0, 255, 0, 255 } ) )
			{
				m_quantize = ccl::TypeDesc::UINT8;
			}
			else if( quantize == vector<int>( { 0, 65536, 0, 65536 } ) )
			{
				m_quantize = ccl::TypeDesc::UINT16;
			}
			else
			{
				m_quantize = ccl::TypeDesc::FLOAT;
			}
		}

		void createImage( ccl::Camera *camera )
		{
			if( m_image.get() )
			{
				m_image.reset();
			}
			//ccl::DisplayBuffer &display = m_session->display;
			// TODO: Work out if Cycles can do overscan...
			Box2i displayWindow( 
				V2i( 0, 0 ),
				V2i( camera->width - 1, camera->height - 1 )
				);
			Box2i dataWindow(
				V2i( 0, 0 ),
				V2i( camera->width - 1, camera->height - 1 )
				);

			vector<string> channelNames;

			if( m_components == 1 )
			{
				channelNames.push_back( "A" );
			}
			else if( m_components == 2 )
			{
				channelNames.push_back( "R" );
				channelNames.push_back( "G" );
			}
			else if( m_components == 3 )
			{
				channelNames.push_back( "R" );
				channelNames.push_back( "G" );
				channelNames.push_back( "B" );
			}
			else if( m_components == 4 )
			{
				channelNames.push_back( "R" );
				channelNames.push_back( "G" );
				channelNames.push_back( "B" );
				channelNames.push_back( "A" );
			}

			m_parameters->writable()["handle"] = new StringData();

			m_image = new ImageDisplayDriver( displayWindow, dataWindow, channelNames, m_parameters );
		}

		void writeImage()
		{
			if( !m_image )
			{
				IECore::msg( IECore::Msg::Warning, "CyclesRenderer::CyclesOutput", boost::format( "Cannot write output: \"%s\"." ) % m_name );
				return;
			}
			IECoreImage::ImagePrimitivePtr image = m_image->image()->copy();
			IECore::WriterPtr writer = IECoreImage::ImageWriter::create( image, "tmp." + m_type );
			if( !writer )
			{
				IECore::msg( IECore::Msg::Warning, "CyclesRenderer::CyclesOutput", boost::format( "Unsupported display type \"%s\"." ) % m_type );
				return;
			}

			writer->parameters()->parameter<IECore::FileNameParameter>( "fileName" )->setTypedValue( m_name );
			//if( m_quantize == ccl::TypeDesc::UINT16 )
			//	writer->parameters()->parameter<IECore::StringParameter>( "openexr.dataType" )->setTypedValue( 'half' );
			//else if( m_quantize == ccl::TypeDesc::UINT16 )
			//	writer->parameters()->parameter<IECore::StringParameter>( "openexr.dataType" )->setTypedValue( 'float' );
			writer->write();
		}

		std::string m_name;
		std::string m_type;
		std::string m_data;
		ccl::PassType m_passType;
		ccl::TypeDesc m_quantize;
		ImageDisplayDriverPtr m_image;
		CompoundDataPtr m_parameters;
		int m_components;
		bool m_interactive;
};

IE_CORE_DECLAREPTR( CyclesOutput )

typedef unordered_map<IECore::InternedString, CyclesOutputPtr> OutputMap;

} // namespace


//////////////////////////////////////////////////////////////////////////
// RenderCallback
//////////////////////////////////////////////////////////////////////////

namespace
{

class RenderCallback : public IECore::RefCounted
{

	public :

		RenderCallback( ccl::Session *session, bool interactive )
			: m_session( session ), m_interactive( interactive ), m_displayDriver( nullptr )
		{
		}

		void updateOutputs( OutputMap &outputs )
		{
			m_outputs = outputs;

			ccl::Camera *camera = m_session->scene->camera;
			//ccl::DisplayBuffer &display = m_session->display;
			// TODO: Work out if Cycles can do overscan...
			Box2i displayWindow( 
				V2i( 0, 0 ),
				V2i( camera->width - 1, camera->height - 1 )
				);
			Box2i dataWindow(
				V2i( 0, 0 ),
				V2i( camera->width - 1, camera->height - 1 )
				);

			//CompoundDataPtr parameters = new CompoundData();
			//auto &p = parameters->writable();

			std::vector<std::string> channelNames;

			for( auto &output : m_outputs )
			{
				std::string name = output.second->m_data;
				auto passType = output.second->m_passType;
				int components = passComponents( passType );

				if( m_interactive )
				{
					if( name == "rgba" )
					{
						channelNames.push_back( "R" );
						channelNames.push_back( "G" );
						channelNames.push_back( "B" );
						channelNames.push_back( "A" );
						continue;
					}
					if( components == 1 )
					{
						channelNames.push_back( name );
						continue;
					}
					else if( components == 2 )
					{
						channelNames.push_back( name + ".R" );
						channelNames.push_back( name + ".G" );
						continue;
					}
					else if( components == 3 )
					{
						channelNames.push_back( name + ".R" );
						channelNames.push_back( name + ".G" );
						channelNames.push_back( name + ".B" );
						continue;
					}
					else if( components == 4 )
					{
						channelNames.push_back( name + ".R" );
						channelNames.push_back( name + ".G" );
						channelNames.push_back( name + ".B" );
						channelNames.push_back( name + ".A" );
						continue;
					}
				}
			}

			if( m_interactive )
			{
				const auto bIt = m_outputs.find( "Interactive/Beauty" );
				if( bIt != m_outputs.end() )
				{
					const auto parameters = bIt->second->m_parameters;
					const StringData *driverType = parameters->member<StringData>( "driverType", true );
					m_displayDriver = DisplayDriver::create(
						driverType->readable(),
						displayWindow, 
						dataWindow, 
						channelNames,
						parameters
						);
				}
			}
		}
/*
		int builtin_image_frame(const string &builtin_name)
		{

		}

		void builtin_image_info(const string &builtin_name,
								void *builtin_data,
								ImageMetaData& metadata)
		{

		}

		bool builtin_image_pixels( const string &builtin_name,
									void *builtin_data,
									unsigned char *pixels,
									const size_t pixels_size,
									const bool free_cache )
		{

		}

		bool builtin_image_float_pixels(const string &builtin_name,
										void *builtin_data,
										float *pixels,
										const size_t pixels_size,
										const bool free_cache)
		{
			
		}
*/
		void writeRenderTile( ccl::RenderTile& rtile )
		{
			// Early-out if there's no output passes
			if( m_outputs.empty() )
			{
				IECore::msg( IECore::Msg::Warning, "CyclesRenderer::CyclesOutput", "No outputs to render to." );
				return;
			}
			// Early-out if there's no interactive render passes
			if( m_interactive && !m_displayDriver )
			{
				IECore::msg( IECore::Msg::Warning, "CyclesRenderer::CyclesOutput", "No interactive outputs to render to." );
				return;
			}
			const int x = rtile.x - m_session->tile_manager.params.full_x;
			const int y = rtile.y - m_session->tile_manager.params.full_y;
			const int w = rtile.w;
			const int h = rtile.h;

			const int cam_h = m_session->scene->camera->height;

			Box2i tile( V2i( x, y ), V2i( x + w - 1, y + h - 1 ) );

			ccl::RenderBuffers *buffers = rtile.buffers;
			/* copy data from device */
			if(!buffers->copy_from_device())
				return;

			//float exposure = m_session->scene->film->exposure;

			const int numOutputChannels = m_interactive ? m_displayDriver->channelNames().size() : 1;

			// Pixels we will use to get from cycles.
			vector<float> tileData( w * h * 4 );
			// Multiple channels get outputted to one display driver in interactive mode.
			vector<float> interleavedData;
			if( m_interactive )
				interleavedData.resize( w * h * numOutputChannels );

			/* Adjust absolute sample number to the range. */
			int sample = rtile.sample;
			const int range_start_sample = m_session->tile_manager.range_start_sample;
			if( range_start_sample != -1 )
			{
				sample -= range_start_sample;
			}

			int outChannelOffset = 0;
			for( auto &output : m_outputs )
			{
				if( m_interactive && !output.second->m_interactive )
					continue;
				if( !m_interactive && output.second->m_interactive )
					continue;
				int numChannels = output.second->m_components;
				buffers->get_pass_rect( output.second->m_passType, 0.5f, sample, numChannels, &tileData[0], output.second->m_data.c_str() );
				if( m_interactive )
				{
					for( int c = 0; c < numChannels; c++ )
					{
						// This is taken out of the Arnold output driver. Interleaving.
						float *in = &(tileData[0]) + c;
						float *out = &(interleavedData[0]) + outChannelOffset;
						for( int j = 0; j < h; j++ )
						{
							for( int i = 0; i < w; i++ )
							{
								*out = *in;
								out += numOutputChannels;
								in += numChannels;
							}
						}
						outChannelOffset += 1;
					}
				}
				else
				{
					output.second->m_image->imageData( tile, &tileData[0], w * h * numChannels );
				}
			}
			if( m_interactive )
			{
				m_displayDriver->imageData( tile, &interleavedData[0], w * h * numOutputChannels );
			}
		}

		void updateRenderTile( ccl::RenderTile& rtile, bool highlight)
		{
			writeRenderTile( rtile );
		}

	private :

		ccl::Session *m_session;
		DisplayDriverPtr m_displayDriver;
		OutputMap m_outputs;
		bool m_interactive;

};

IE_CORE_DECLAREPTR( RenderCallback )

} // namespace

//////////////////////////////////////////////////////////////////////////
// ShaderCache
//////////////////////////////////////////////////////////////////////////

namespace
{

class ShaderCache : public IECore::RefCounted
{

	public :

		ShaderCache( ccl::Scene* scene )
			: m_scene( scene )
		{
		}

		void update( ccl::Scene *scene )
		{
			m_scene = scene;
			updateShaders();
		}

		// Can be called concurrently with other get() calls.
		SharedCShaderPtr get( const IECoreScene::ShaderNetwork *shader )
		{
			Cache::accessor a;
			m_cache.insert( a, shader ? shader->Object::hash() : MurmurHash() );
			if( !a->second )
			{
				if( shader )
				{
					const std::string namePrefix = "shader:" + a->first.toString() + ":";
					a->second = SharedCShaderPtr( ShaderNetworkAlgo::convert( shader, m_scene, namePrefix ) );
				}
				else
				{
					// This creates a camera dot-product shader/facing ratio.
					const std::string name = "defaultSurfaceShader";
					ccl::Shader *cshader = new ccl::Shader();
					cshader->name = name.c_str();
					cshader->graph = new ccl::ShaderGraph();
					ccl::ShaderNode *outputNode = (ccl::ShaderNode*)cshader->graph->output();
					ccl::VectorMathNode *vecMath = new ccl::VectorMathNode();
					vecMath->type = ccl::NODE_VECTOR_MATH_DOT_PRODUCT;
					ccl::GeometryNode *geo = new ccl::GeometryNode();
					ccl::MathNode *math = new ccl::MathNode();
					math->type = ccl::NODE_MATH_MULTIPLY;
					math->value2 = 2.0f;
					ccl::ShaderNode *vecMathNode = cshader->graph->add( (ccl::ShaderNode*)vecMath );
					ccl::ShaderNode *geoNode = cshader->graph->add( (ccl::ShaderNode*)geo );
					ccl::ShaderNode *mathNode = cshader->graph->add( (ccl::ShaderNode*)math );
					cshader->graph->connect( IECoreCycles::ShaderNetworkAlgo::output( geoNode, "normal" ), 
											 IECoreCycles::ShaderNetworkAlgo::input( vecMathNode, "vector1" ) );
					cshader->graph->connect( IECoreCycles::ShaderNetworkAlgo::output( geoNode, "incoming" ), 
											 IECoreCycles::ShaderNetworkAlgo::input( vecMathNode, "vector2" ) );
					cshader->graph->connect( IECoreCycles::ShaderNetworkAlgo::output( vecMathNode, "value" ), 
											 IECoreCycles::ShaderNetworkAlgo::input( mathNode, "value1" ) );
					cshader->graph->connect( IECoreCycles::ShaderNetworkAlgo::output( mathNode, "value" ), 
											 IECoreCycles::ShaderNetworkAlgo::input( outputNode, "surface" ) );
					a->second = SharedCShaderPtr( cshader );
				}
				
			}
			return a->second;
		}

		SharedCShaderPtr defaultSurface()
		{
			return get( nullptr );
		}

		// To apply a default color+strength to the lights without shaders assigned.
		SharedCShaderPtr getEmission( const IECoreScene::Shader *shader, const V3f &color, const float strength )
		{
			Cache::accessor a;
			m_cache.insert( a, shader->Object::hash() );
			if( !a->second )
			{
				const std::string name = "shader:" + a->first.toString() + ":emission";
				ccl::Shader *cshader = new ccl::Shader();
				cshader->name = name.c_str();
				cshader->graph = new ccl::ShaderGraph();
				ccl::ShaderNode *outputNode = (ccl::ShaderNode*)cshader->graph->output();
				ccl::EmissionNode *emission = new ccl::EmissionNode();
				emission->color = SocketAlgo::setColor( color );
				emission->strength = strength;
				ccl::ShaderNode *shaderNode = cshader->graph->add( (ccl::ShaderNode*)emission );
				cshader->graph->connect( shaderNode->output( "Emission" ), outputNode->input( "Surface" ) );
				a->second = SharedCShaderPtr( cshader );
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
					// shader.
					toErase.push_back( it->first );
				}
			}
			for( vector<IECore::MurmurHash>::const_iterator it = toErase.begin(), eIt = toErase.end(); it != eIt; ++it )
			{
				m_cache.erase( *it );
			}

			if( toErase.size() )
				updateShaders();
		}

	private :

		void updateShaders() const
		{
			auto &shaders = m_scene->shaders;
			shaders.clear();
			for( Cache::const_iterator it = m_cache.begin(), eIt = m_cache.end(); it != eIt; ++it )
			{
				if( it->second )
				{
					ccl::Shader *cshader = it->second.get();
					shaders.push_back( cshader );
					cshader->tag_update( m_scene );
				}
			}
		}

		ccl::Scene* m_scene;
		typedef tbb::concurrent_hash_map<IECore::MurmurHash, SharedCShaderPtr> Cache;
		Cache m_cache;

};

IE_CORE_DECLAREPTR( ShaderCache )

} // namespace

//////////////////////////////////////////////////////////////////////////
// CyclesAttributes
//////////////////////////////////////////////////////////////////////////

namespace
{

// Standard Attributes
IECore::InternedString g_visibilityAttributeName( "visibility" );
IECore::InternedString g_doubleSidedAttributeName( "doubleSided" );
IECore::InternedString g_transformBlurAttributeName( "transformBlur" );
IECore::InternedString g_transformBlurSegmentsAttributeName( "transformBlurSegments" );
IECore::InternedString g_deformationBlurAttributeName( "deformationBlur" );
IECore::InternedString g_deformationBlurSegmentsAttributeName( "deformationBlurSegments" );
// Cycles Attributes
IECore::InternedString g_cclVisibilityAttributeName( "ccl:visibility" );
IECore::InternedString g_useHoldoutAttributeName( "ccl:use_holdout" );
IECore::InternedString g_isShadowCatcherAttributeName( "ccl:is_shadow_catcher" );
IECore::InternedString g_maxLevelAttributeName( "ccl:max_level" );
IECore::InternedString g_dicingRateAttributeName( "ccl:dicing_rate" );
// Cycles Light
IECore::InternedString g_lightAttributeName( "ccl:light" );

// Shader Assignment
std::array<IECore::InternedString, 2> g_shaderAttributeNames = { {
	"surface",
	"osl:surface",
} };

ccl::PathRayFlag nameToRayType( const std::string &name )
{
#define MAP_RAY(rayname, raytype) if(name == rayname) return raytype;
	MAP_RAY( "camera", ccl::PATH_RAY_CAMERA );
	MAP_RAY( "diffuse", ccl::PATH_RAY_DIFFUSE );
	MAP_RAY( "glossy", ccl::PATH_RAY_GLOSSY );
	MAP_RAY( "transmission", ccl::PATH_RAY_TRANSMIT );
	MAP_RAY( "shadow", ccl::PATH_RAY_SHADOW );
	MAP_RAY( "scatter", ccl::PATH_RAY_VOLUME_SCATTER );
#undef MAP_RAY

	return (ccl::PathRayFlag)0;
}

IECore::InternedString g_setsAttributeName( "sets" );

class CyclesAttributes : public IECoreScenePreview::Renderer::AttributesInterface
{

	public :

		CyclesAttributes( const IECore::CompoundObject *attributes, ShaderCache *shaderCache )
			:	m_cclVisibility( ~0 ), m_useHoldout( false ), m_isShadowCatcher( false ), m_maxLevel( 12 ), m_dicingRate( 1.0f )
		{
			for( const auto &name : g_shaderAttributeNames )
			{
				if( const Object *o = attributes->member<const Object>( name ) )
				{
					if( const ShaderNetwork *shader = reportedCast<const ShaderNetwork>( o, "attribute", name ) )
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
						if( const IntData *data = static_cast<const IntData *>( d ) )
						{
							auto &vis = data->readable();
							auto ray = nameToRayType( m.first.string().c_str() + 15 );
							m_cclVisibility = vis ? m_cclVisibility |= ray : m_cclVisibility & ~ray;
						}
					}
				}
				else if( boost::starts_with( m.first.string(), "ccl:" ) )
				{
					if( const ShaderNetwork *shaderNetwork = reportedCast<const ShaderNetwork>( m.second.get(), "attribute", m.first ) )
					{
						if( m.first == g_lightAttributeName )
						{
							const IECoreScene::Shader *shader = shaderNetwork->getShader( shaderNetwork->getOutput().shader );
							// This is just to store some data.
							m_light = CLightPtr( new ccl::Light() );
							ccl::Light *clight = m_light.get();
							float strength = 1.0f;
							auto color = Imath::V3f( 1.0f );
							for( const auto &namedParameter : shader->parameters() )
							{
								string paramName = namedParameter.first.string();
								if( paramName == "color" )
								{
									if( const Color3fData *data = static_cast<const Color3fData *>( namedParameter.second.get() ) )
										color = data->readable();
									continue;
								}
								else if ( paramName == "strength" )
								{
									if( const FloatData *data = static_cast<const FloatData *>( namedParameter.second.get() ) )
										strength = data->readable();
									continue;
								}
								SocketAlgo::setSocket( clight, paramName, namedParameter.second.get() );
							}

							m_shader = shaderCache->getEmission( shader, color, strength );
						}
						else
						{
							m_shader = shaderCache->get( shaderNetwork );
						}
					}
					else if( const Data *d = reportedCast<const IECore::Data>( m.second.get(), "attribute", m.first ) )
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

			if( !m_shader )
			{
				m_shader = shaderCache->defaultSurface();
			}
		}

		bool applyObject( ccl::Object *object, const CyclesAttributes *previousAttributes ) const
		{
			//const ccl::NodeType *nodeType = node->type;
			object->visibility = m_cclVisibility;
			object->use_holdout = m_useHoldout;
			object->is_shadow_catcher = m_isShadowCatcher;

			if( object->mesh )
			{
				ccl::Mesh *mesh = object->mesh;
				if( mesh->subd_params )
				{
					mesh->subd_params->max_level = m_maxLevel;
					mesh->subd_params->dicing_rate = m_dicingRate;
				}
				// Assign shader. Clearing used_shaders will use the default shader.
				mesh->used_shaders.clear();
				if( m_shader )
				{
					mesh->used_shaders.push_back( m_shader.get() );
				}
			}

			return true;
		}

		bool applyLight( ccl::Light *light, const CyclesAttributes *previousAttributes ) const
		{
			if( ccl::Light *clight = m_light.get() )
			{
				light->size = clight->size;
				light->map_resolution = clight->map_resolution;
				light->spot_angle = clight->spot_angle;
				light->spot_smooth = clight->spot_smooth;
				light->cast_shadow = clight->cast_shadow;
				light->use_mis = clight->use_mis;
				light->use_diffuse = clight->use_diffuse;
				light->use_glossy = clight->use_glossy;
				light->use_transmission = clight->use_transmission;
				light->use_scatter = clight->use_scatter;
				light->samples = clight->samples;
				light->max_bounces = clight->max_bounces;
				light->is_portal = clight->is_portal;
				light->is_enabled = clight->is_enabled;
			}
			if( m_shader.get() )
			{
				light->shader = m_shader.get();
			}
			return true;
		}

	private :

		CLightPtr m_light;
		SharedCShaderPtr m_shader;
		unsigned m_cclVisibility;
		bool m_useHoldout;
		bool m_isShadowCatcher;
		bool m_maxLevel;
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

		AttributesCache( ShaderCachePtr shaderCache )
			: m_shaderCache( shaderCache )
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

};

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
				cobject = ObjectAlgo::convert( object, "instance:" + hash.toString() );
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
			m_meshes.insert( a, hash );

			if( !a->second )
			{
				cobject = ObjectAlgo::convert( samples, "instance:" + hash.toString() );
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
			vector<SharedCObjectPtr> objectsKeep;
			for( vector<SharedCObjectPtr>::const_iterator it = m_objects.begin(), eIt = m_objects.end(); it != eIt; ++it )
			{
				if( !it->unique() )
				{
					objectsKeep.push_back( *it );
				}
			}

			if( objectsKeep.size() )
			{
				m_objects = objectsKeep;
				updateObjects();
			}
		}

	private :

		void updateObjects() const
		{
			auto &objects = m_scene->objects;
			objects.clear();
			for( vector<SharedCObjectPtr>::const_iterator it = m_objects.begin(), eIt = m_objects.end(); it != eIt; ++it )
			{
				if( it->get() )
				{
					objects.push_back( it->get() );
				}
			}
			m_scene->object_manager->tag_update( m_scene );
		}

		void updateMeshes() const
		{
			auto &meshes = m_scene->meshes;
			meshes.clear();
			for( MeshCache::const_iterator it = m_meshes.begin(), eIt = m_meshes.end(); it != eIt; ++it )
			{
				if( it->second )
				{
					meshes.push_back( it->second.get() );
				}
			}
			m_scene->mesh_manager->tag_update( m_scene );
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
		SharedCLightPtr get( const std::string &nodeName )
		{
			auto clight = SharedCLightPtr( new ccl::Light() );
			clight.get()->name = nodeName.c_str();
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
			vector<SharedCLightPtr> lightsKeep;
			for( vector<SharedCLightPtr>::const_iterator it = m_lights.begin(), eIt = m_lights.end(); it != eIt; ++it )
			{
				if( !it->unique() )
				{
					lightsKeep.push_back( *it );
				}
			}

			if( lightsKeep.size() )
			{
				m_lights = lightsKeep;
				updateLights();
			}
		}

	private :

		void updateLights() const
		{
			auto &lights = m_scene->lights;
			lights.clear();
			for( vector<SharedCLightPtr>::const_iterator it = m_lights.begin(), eIt = m_lights.end(); it != eIt; ++it )
			{
				if( it->get() )
				{
					lights.push_back( it->get() );
				}
			}
			m_scene->light_manager->tag_update( m_scene );
		}

		ccl::Scene *m_scene;
		vector<SharedCLightPtr> m_lights;
		tbb::spin_mutex m_lightsMutex;

};

IE_CORE_DECLAREPTR( LightCache )

} // namespace

//////////////////////////////////////////////////////////////////////////
// CameraCache
//////////////////////////////////////////////////////////////////////////

namespace
{

class CameraCache : public IECore::RefCounted
{

	public :

		CameraCache()
		{
		}

		// Can be called concurrently with other get() calls.
		SharedCCameraPtr get( const IECoreScene::Camera *camera, const std::string &name )
		{
			const IECore::MurmurHash hash = camera->Object::hash();

			Cache::accessor a;
			m_cache.insert( a, hash );

			if( !a->second )
			{
				a->second = SharedCCameraPtr( CameraAlgo::convert( camera, name ) );
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
					// camera.
					toErase.push_back( it->first );
				}
			}
			for( vector<IECore::MurmurHash>::const_iterator it = toErase.begin(), eIt = toErase.end(); it != eIt; ++it )
			{
				m_cache.erase( *it );
			}
		}

	private :

		typedef tbb::concurrent_hash_map<IECore::MurmurHash, SharedCCameraPtr> Cache;
		Cache m_cache;

};

IE_CORE_DECLAREPTR( CameraCache )

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
			object->motion = ccl::array<ccl::Transform>( numSamples );
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
			if( cyclesAttributes->applyObject( object, m_attributes.get() ) )
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

		CyclesLight( SharedCLightPtr &light )
			: m_light( light ), m_attributes( nullptr )
		{
		}

		void transform( const Imath::M44f &transform ) override
		{
			ccl::Light *light = m_light.get();
			if( !light )
				return;
			ccl::Transform tfm = SocketAlgo::setTransform( transform );
			light->tfm = tfm;
			// To feed into area lights
			light->axisu = ccl::transform_get_column(&tfm, 0);
			light->axisv = ccl::transform_get_column(&tfm, 1);
			Imath::Vec3<float> scale = Imath::Vec3<float>( 1.0f );
			Imath::extractScaling( transform, scale, false );
			light->sizeu = scale.x;
			light->sizev = scale.y;
			light->co = ccl::transform_get_column(&tfm, 3);
			light->dir = -ccl::transform_get_column(&tfm, 2);
		}

		void transform( const std::vector<Imath::M44f> &samples, const std::vector<float> &times ) override
		{
			ccl::Light *light = m_light.get();
			if( !light )
				return;
			// Cycles doesn't support motion samples on lights (yet)
			ccl::Transform tfm = SocketAlgo::setTransform( samples[0] );
			light->tfm = tfm;
			// To feed into area lights
			light->axisu = ccl::transform_get_column(&tfm, 0);
			light->axisv = ccl::transform_get_column(&tfm, 1);
			Imath::Vec3<float> scale = Imath::Vec3<float>( 1.0f );
			Imath::extractScaling( samples[0], scale, false );
			light->sizeu = scale.x;
			light->sizev = scale.y;
			light->co = ccl::transform_get_column(&tfm, 3);
			light->dir = -ccl::transform_get_column(&tfm, 2);
		}

		bool attributes( const IECoreScenePreview::Renderer::AttributesInterface *attributes ) override
		{
			ccl::Light *light = m_light.get();
			if( !light )
				return true;

			const CyclesAttributes *cyclesAttributes = static_cast<const CyclesAttributes *>( attributes );
			if( cyclesAttributes->applyLight( light, m_attributes.get() ) )
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

		CyclesCamera( SharedCCameraPtr camera )
			: m_camera( camera )//, m_attributes( nullptr )
		{
		}

		void transform( const Imath::M44f &transform ) override
		{
			ccl::Camera *camera = m_camera.get();
			if( !camera )
				return;
			Imath::M44f ctransform = transform;
			ctransform.scale( Imath::V3f( 1.0f, -1.0f, -1.0f ) );
			camera->matrix = SocketAlgo::setTransform( ctransform );
		}

		void transform( const std::vector<Imath::M44f> &samples, const std::vector<float> &times ) override
		{
			ccl::Camera *camera = m_camera.get();
			if( !camera )
				return;
			const size_t numSamples = samples.size();
			camera->motion = ccl::array<ccl::Transform>( numSamples );
			const Imath::V3f scale = Imath::V3f( 1.0f, -1.0f, -1.0f );
			for( size_t i = 0; i < numSamples; ++i )
			{
				Imath::M44f ctransform = samples[i];
				ctransform.scale( scale );
				camera->motion[i] = SocketAlgo::setTransform( ctransform );
			}
		}

		bool attributes( const IECoreScenePreview::Renderer::AttributesInterface *attributes ) override
		{
			return false;
		}

	private :

		SharedCCameraPtr m_camera;
		//ConstCyclesAttributesPtr m_attributes;

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
IECore::InternedString g_featureSetOptionName( "ccl:session:experimental" );
IECore::InternedString g_progressiveRefineOptionName( "ccl:session:progressive_refine" );
IECore::InternedString g_progressiveOptionName( "ccl:session:progressive" );
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
IECore::InternedString g_numBvhTimeStepsOptionName( "ccl:scene:num_bvh_time_steps" );
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
// Background shader
IECore::InternedString g_backgroundShaderOptionName( "ccl:background:shader" );
// Square samples
std::array<IECore::InternedString, 8> g_squareSamplesOptionNames = { {
	"ccl:integrator:aa_samples",
	"ccl:integrator:diffuse_samples",
	"ccl:integrator:glossy_samples",
	"ccl:integrator:transmission_samples",
	"ccl:integrator:ao_samples",
	"ccl:integrator:mesh_light_samples",
	"ccl:integrator:subsurface_samples",
	"ccl:integrator:volume_samples",
} };

IE_CORE_FORWARDDECLARE( CyclesRenderer )

class CyclesRenderer final : public IECoreScenePreview::Renderer
{

	public :

		CyclesRenderer( RenderType renderType, const std::string &fileName )
			:	m_renderType( renderType ),
				m_sessionParams( ccl::SessionParams() ),
				m_sceneParams( ccl::SceneParams() ),
				m_bufferParams( ccl::BufferParams() ),
				m_deviceName( "CPU" ),
				m_shadingsystemName( "SVM" ),
				m_session( nullptr ),
				m_scene( nullptr ),
				m_renderCallback( nullptr ),
				m_integratorCache( new ccl::Integrator() ),
				m_backgroundCache( new ccl::Background() ),
				m_filmCache( new ccl::Film() ),
				m_curveSystemManagerCache( new ccl::CurveSystemManager() ),
				m_curveSystemManagerDefault( new ccl::CurveSystemManager() ), // To restore default values
				m_rendering( false )
		{
			// Session Defaults
			m_sessionParams.display_buffer_linear = true;
			m_bufferParamsModified = m_bufferParams;

			m_sessionParams.shadingsystem = ccl::SHADINGSYSTEM_SVM;
			m_sceneParams.shadingsystem = m_sessionParams.shadingsystem;

			if( m_renderType != Interactive )
			{
				// Sane defaults, not INT_MAX
				m_sessionParams.samples = 128;
				m_sessionParams.start_resolution = 64;
			}

			// The interactive renderer also runs in the background. Having
			// this off makes more sense if we were to use Cycles as a
			// viewport alternative to the OpenGL viewer.
			m_sessionParams.background = true;
			// We almost-always want persistent data.
			m_sceneParams.persistent_data = true;

			m_sessionParamsDefault = m_sessionParams;
			m_sceneParamsDefault = m_sceneParams;

			init();

			m_cameraCache = new CameraCache();
			m_lightCache = new LightCache( m_scene );
			m_shaderCache = new ShaderCache( m_scene );
			m_instanceCache = new InstanceCache( m_scene );
			m_attributesCache = new AttributesCache( m_shaderCache );

		}

		~CyclesRenderer() override
		{
			pause();

			// Cycles created the defaultCamera, so we give it back for it to delete.
			m_scene->camera = m_defaultCamera;

			m_attributesCache.reset();
			m_instanceCache.reset();
			m_shaderCache.reset();
			m_lightCache.reset();
			m_cameraCache.reset();
			m_outputs.clear();

			// Gaffer has already deleted these, so we can't double-delete
			m_scene->shaders.clear();
			m_scene->meshes.clear();
			m_scene->objects.clear();
			m_scene->lights.clear();
			m_scene->particle_systems.clear();

			// The rest should be cleaned up by Cycles.
			delete m_session;
		}

		IECore::InternedString name() const override
		{
			return "Cycles";
		}

		void option( const IECore::InternedString &name, const IECore::Object *value ) override
		{
			auto *integrator = m_integratorCache.get();
			auto *background = m_backgroundCache.get();
			auto *film = m_filmCache.get();
			auto *curveSystemManager = m_curveSystemManagerCache.get();

			if( name == g_frameOptionName )
			{
				if( value == nullptr )
				{
					m_frame = 0;
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
				const ccl::SocketType *input = integrator->node_type->find_input( ccl::ustring( "motion_blur" ) );
				if( value && input )
				{
					if( const Data *data = reportedCast<const Data>( value, "option", name ) )
					{
						SocketAlgo::setSocket( (ccl::Node*)integrator, input, data );
					}
					else
					{
						integrator->set_default_value( *input );
						//IECore::msg( IECore::Msg::Warning, "CyclesRenderer::option", boost::format( "Unknown value \"%s\" for option \"%s\"." ) % m_deviceName, name.string() );
					}
				}
				else if( input )
				{
					integrator->set_default_value( *input );
				}
				return;
			}
			else if( name == g_deviceOptionName )
			{
				if( const StringData *data = reportedCast<const StringData>( value, "option", name ) )
				{
					auto device_name = data->readable();
					m_deviceName = device_name;
				}
				else if( value == nullptr )
				{
					m_deviceName = "CPU";
				}
				else
				{
					m_deviceName = "CPU";
					IECore::msg( IECore::Msg::Warning, "CyclesRenderer::option", boost::format( "Unknown value \"%s\" for option \"%s\"." ) % m_deviceName % name.string() );
				}
				return;
			}
			else if( name == g_shadingsystemOptionName )
			{
				if( value == nullptr )
				{
					m_shadingsystemName = "SVM";
					m_sessionParams.shadingsystem = ccl::SHADINGSYSTEM_SVM;
					m_sceneParams.shadingsystem   = ccl::SHADINGSYSTEM_SVM;
				}
				else if( const StringData *data = reportedCast<const StringData>( value, "option", name ) )
				{
					auto shadingsystemName = data->readable();
					if( shadingsystemName == "OSL" )
					{
						m_shadingsystemName = shadingsystemName;
						m_sessionParams.shadingsystem = ccl::SHADINGSYSTEM_OSL;
						m_sceneParams.shadingsystem   = ccl::SHADINGSYSTEM_OSL;
					}
					else if( shadingsystemName == "SVM" )
					{
						m_shadingsystemName = shadingsystemName;
						m_sessionParams.shadingsystem = ccl::SHADINGSYSTEM_SVM;
						m_sceneParams.shadingsystem   = ccl::SHADINGSYSTEM_SVM;
					}
					else
					{
						m_shadingsystemName = "SVM";
						m_sessionParams.shadingsystem = ccl::SHADINGSYSTEM_SVM;
						m_sceneParams.shadingsystem   = ccl::SHADINGSYSTEM_SVM;
						IECore::msg( IECore::Msg::Warning, "CyclesRenderer::option", boost::format( "Unknown value \"%s\" for option \"%s\"." ) % shadingsystemName % name.string() );
					}
				}
				else
				{
					IECore::msg( IECore::Msg::Warning, "CyclesRenderer::option", boost::format( "Unknown value for option \"%s\"." ) % name.string() );
				}
				return;
			}
			else if( boost::starts_with( name.string(), "ccl:session:" ) )
			{
				if( name == g_featureSetOptionName )
				{
					if( value == nullptr )
					{
						m_sessionParams.experimental = m_sessionParamsDefault.experimental;
						return;
					}
					if ( const BoolData *data = reportedCast<const BoolData>( value, "option", name ) )
						m_sessionParams.experimental = data->readable();
					return;
				}
				else if( name == g_progressiveRefineOptionName )
				{
					if( value == nullptr )
					{
						m_sessionParams.progressive_refine = m_sessionParamsDefault.progressive_refine;
						return;
					}
					if ( const BoolData *data = reportedCast<const BoolData>( value, "option", name ) )
						m_sessionParams.progressive_refine = data->readable();
					return;
				}
				else if( name == g_progressiveOptionName )
				{
					if( value == nullptr )
					{
						m_sessionParams.progressive = m_sessionParamsDefault.progressive;
						return;
					}
					if ( const BoolData *data = reportedCast<const BoolData>( value, "option", name ) )
						m_sessionParams.progressive = data->readable();
					return;
				}
				else if( name == g_samplesOptionName )
				{
					if( value == nullptr )
					{
						m_sessionParams.samples = m_sessionParamsDefault.samples;
						return;
					}
					if ( const IntData *data = reportedCast<const IntData>( value, "option", name ) )
						m_sessionParams.samples = data->readable();
					return;
				}
				else if( name == g_tileSizeOptionName )
				{
					if( value == nullptr )
					{
						m_sessionParams.tile_size = m_sessionParamsDefault.tile_size;
						return;
					}
					if ( const V2iData *data = reportedCast<const V2iData>( value, "option", name ) )
					{
						auto d = data->readable();
						m_sessionParams.tile_size = ccl::make_int2( d.x, d.y );
					}
					return;
				}
				else if( name == g_tileOrderOptionName )
				{
					if( value == nullptr )
					{
						m_sessionParams.tile_order = m_sessionParamsDefault.tile_order;
						return;
					}
					if ( const IntData *data = reportedCast<const IntData>( value, "option", name ) )
						m_sessionParams.tile_order = (ccl::TileOrder)data->readable();
					return;
				}
				else if( name == g_startResolutionOptionName )
				{
					if( value == nullptr )
					{
						m_sessionParams.start_resolution = m_sessionParamsDefault.start_resolution;
						return;
					}
					if ( const IntData *data = reportedCast<const IntData>( value, "option", name ) )
						m_sessionParams.start_resolution = data->readable();
					return;
				}
				else if( name == g_pixelSizeOptionName )
				{
					if( value == nullptr )
					{
						m_sessionParams.pixel_size = m_sessionParamsDefault.pixel_size;
						return;
					}
					if ( const IntData *data = reportedCast<const IntData>( value, "option", name ) )
						m_sessionParams.pixel_size = data->readable();
					return;
				}
				else if( name == g_threadsOptionName )
				{
					if( value == nullptr )
					{
						m_sessionParams.threads = m_sessionParamsDefault.threads;
						return;
					}
					if ( const IntData *data = reportedCast<const IntData>( value, "option", name ) )
						m_sessionParams.threads = data->readable();
					return;
				}
				else if( name == g_displayBufferLinearOptionName )
				{
					if( value == nullptr )
					{
						m_sessionParams.display_buffer_linear = m_sessionParamsDefault.display_buffer_linear;
						return;
					}
					if ( const BoolData *data = reportedCast<const BoolData>( value, "option", name ) )
						m_sessionParams.display_buffer_linear = data->readable();
					return;
				}
				else if( name == g_useDenoisingOptionName )
				{
					if( value == nullptr )
					{
						m_sessionParams.use_denoising = m_sessionParamsDefault.use_denoising;
						return;
					}
					if ( const BoolData *data = reportedCast<const BoolData>( value, "option", name ) )
						m_sessionParams.use_denoising = data->readable();
					return;
				}
				else if( name == g_denoisingRadiusOptionName )
				{
					if( value == nullptr )
					{
						m_sessionParams.denoising_radius = m_sessionParamsDefault.denoising_radius;
						return;
					}
					if ( const IntData *data = reportedCast<const IntData>( value, "option", name ) )
						m_sessionParams.denoising_radius = data->readable();
					return;
				}
				else if( name == g_denoisingStrengthOptionName )
				{
					if( value == nullptr )
					{
						m_sessionParams.denoising_strength = m_sessionParamsDefault.denoising_strength;
						return;
					}
					if ( const FloatData *data = reportedCast<const FloatData>( value, "option", name ) )
						m_sessionParams.denoising_strength = data->readable();
					return;
				}
				else if( name == g_denoisingFeatureStrengthOptionName )
				{
					if( value == nullptr )
					{
						m_sessionParams.denoising_feature_strength = m_sessionParamsDefault.denoising_feature_strength;
						return;
					}
					if ( const FloatData *data = reportedCast<const FloatData>( value, "option", name ) )
						m_sessionParams.denoising_feature_strength = data->readable();
					return;
				}
				else if( name == g_denoisingRelativePcaOptionName )
				{
					if( value == nullptr )
					{
						m_sessionParams.denoising_relative_pca = m_sessionParamsDefault.denoising_relative_pca;
						return;
					}
					if ( const BoolData *data = reportedCast<const BoolData>( value, "option", name ) )
						m_sessionParams.denoising_relative_pca = data->readable();
					return;
				}
				else if( name == g_cancelTimeoutOptionName )
				{
					if( value == nullptr )
					{
						m_sessionParams.cancel_timeout = m_sessionParamsDefault.cancel_timeout;
						return;
					}
					if ( const FloatData *data = reportedCast<const FloatData>( value, "option", name ) )
						m_sessionParams.cancel_timeout = (double)data->readable();
					return;
				}
				else if( name == g_resetTimeoutOptionName )
				{
					if( value == nullptr )
					{
						m_sessionParams.reset_timeout = m_sessionParamsDefault.reset_timeout;
						return;
					}
					if ( const FloatData *data = reportedCast<const FloatData>( value, "option", name ) )
						m_sessionParams.reset_timeout = (double)data->readable();
					return;
				}
				else if( name == g_textTimeoutOptionName )
				{
					if( value == nullptr )
					{
						m_sessionParams.text_timeout = m_sessionParamsDefault.text_timeout;
						return;
					}
					if ( const FloatData *data = reportedCast<const FloatData>( value, "option", name ) )
						m_sessionParams.text_timeout = (double)data->readable();
				}
				else if( name == g_progressiveUpdateTimeoutOptionName )
				{
					if( value == nullptr )
					{
						m_sessionParams.progressive_update_timeout = m_sessionParamsDefault.progressive_update_timeout;
						return;
					}
					if ( const FloatData *data = reportedCast<const FloatData>( value, "option", name ) )
						m_sessionParams.progressive_update_timeout = (double)data->readable();
				}
				else
				{
					IECore::msg( IECore::Msg::Warning, "CyclesRenderer::option", boost::format( "Unknown option \"%s\"." ) % name.string() );
					return;
				}
			}
			else if( boost::starts_with( name.string(), "ccl:scene:" ) )
			{
				if( name == g_bvhTypeOptionName )
				{
					if( value == nullptr )
					{
						m_sceneParams.bvh_type = m_sceneParamsDefault.bvh_type;
						return;
					}
					if ( const IntData *data = reportedCast<const IntData>( value, "option", name ) )
						m_sceneParams.bvh_type = (ccl::SceneParams::BVHType)data->readable();
					return;
				}
				else if( name == g_bvhLayoutOptionName )
				{
					if( value == nullptr )
					{
						m_sceneParams.bvh_layout = m_sceneParamsDefault.bvh_layout;
						return;
					}
					if ( const IntData *data = reportedCast<const IntData>( value, "option", name ) )
						m_sceneParams.bvh_layout = (ccl::BVHLayout)data->readable();
					return;
				}
				else if( name == g_useBvhSpatialSplitOptionName )
				{
					if( value == nullptr )
					{
						m_sceneParams.use_bvh_spatial_split = m_sceneParamsDefault.use_bvh_spatial_split;
						return;
					}
					if ( const BoolData *data = reportedCast<const BoolData>( value, "option", name ) )
						m_sceneParams.use_bvh_spatial_split = data->readable();
					return;
				}
				else if( name == g_useBvhUnalignedNodesOptionName )
				{
					if( value == nullptr )
					{
						m_sceneParams.use_bvh_unaligned_nodes = m_sceneParamsDefault.use_bvh_unaligned_nodes;
						return;
					}
					if ( const BoolData *data = reportedCast<const BoolData>( value, "option", name ) )
						m_sceneParams.use_bvh_unaligned_nodes = data->readable();
					return;
				}
				else if( name == g_numBvhTimeStepsOptionName )
				{
					if( value == nullptr )
					{
						m_sceneParams.num_bvh_time_steps = m_sceneParamsDefault.num_bvh_time_steps;
						return;
					}
					if ( const IntData *data = reportedCast<const IntData>( value, "option", name ) )
						m_sceneParams.num_bvh_time_steps = data->readable();
					return;
				}
				else if( name == g_persistentDataOptionName )
				{
					if( value == nullptr )
					{
						m_sceneParams.persistent_data = m_sceneParamsDefault.persistent_data;
						return;
					}
					if ( const BoolData *data = reportedCast<const BoolData>( value, "option", name ) )
						m_sceneParams.persistent_data = data->readable();
					return;
				}
				else if( name == g_textureLimitOptionName )
				{
					if( value == nullptr )
					{
						m_sceneParams.texture_limit = m_sceneParamsDefault.texture_limit;
						return;
					}
					if ( const IntData *data = reportedCast<const IntData>( value, "option", name ) )
						m_sceneParams.texture_limit = data->readable();
					return;
				}
				else
				{
					IECore::msg( IECore::Msg::Warning, "CyclesRenderer::option", boost::format( "Unknown option \"%s\"." ) % name.string() );
					return;
				}
			}
			else if( boost::starts_with( name.string(), "ccl:curves:" ) )
			{
				if( name == g_useCurvesOptionType )
				{
					if( value == nullptr )
					{
						curveSystemManager->use_curves = m_curveSystemManagerDefault->use_curves;
						return;
					}
					if ( const BoolData *data = reportedCast<const BoolData>( value, "option", name ) )
						curveSystemManager->use_curves = data->readable();
					return;
				}
				else if( name == g_curveMinimumWidthOptionType )
				{
					if( value == nullptr )
					{
						curveSystemManager->minimum_width = m_curveSystemManagerDefault->minimum_width;
						return;
					}
					if ( const FloatData *data = reportedCast<const FloatData>( value, "option", name ) )
						curveSystemManager->minimum_width = data->readable();
					return;
				}
				else if( name == g_curveMaximumWidthOptionType )
				{
					if( value == nullptr )
					{
						curveSystemManager->maximum_width = m_curveSystemManagerDefault->maximum_width;
						return;
					}
					if ( const FloatData *data = reportedCast<const FloatData>( value, "option", name ) )
						curveSystemManager->maximum_width = data->readable();
					return;
				}
				else if( name == g_curvePrimitiveOptionType )
				{
					if( value == nullptr )
					{
						curveSystemManager->primitive = m_curveSystemManagerDefault->primitive;
						return;
					}
					if ( const IntData *data = reportedCast<const IntData>( value, "option", name ) )
						curveSystemManager->primitive = (ccl::CurvePrimitiveType)data->readable();
					return;
				}
				else if( name == g_curveShapeOptionType )
				{
					if( value == nullptr )
					{
						curveSystemManager->curve_shape = m_curveSystemManagerDefault->curve_shape;
						return;
					}
					if ( const IntData *data = reportedCast<const IntData>( value, "option", name ) )
						curveSystemManager->curve_shape = (ccl::CurveShapeType)data->readable();
					return;
				}
				else if( name == g_curveResolutionOptionType )
				{
					if( value == nullptr )
					{
						curveSystemManager->resolution = m_curveSystemManagerDefault->resolution;
						return;
					}
					if ( const IntData *data = reportedCast<const IntData>( value, "option", name ) )
						curveSystemManager->resolution = data->readable();
					return;
				}
				else if( name == g_curveSubdivisionsOptionType )
				{
					if( value == nullptr )
					{
						curveSystemManager->subdivisions = m_curveSystemManagerDefault->subdivisions;
						return;
					}
					if ( const IntData *data = reportedCast<const IntData>( value, "option", name ) )
						curveSystemManager->subdivisions = data->readable();
					return;
				}
				else if( name == g_curveCullBackfacing )
				{
					if( value == nullptr )
					{
						curveSystemManager->use_backfacing = m_curveSystemManagerDefault->use_backfacing;
						return;
					}
					if ( const BoolData *data = reportedCast<const BoolData>( value, "option", name ) )
						curveSystemManager->use_backfacing = data->readable();
					return;
				}
			}
			// The last 3 are subclassed internally from ccl::Node so treat their params like Cycles sockets
			else if( boost::starts_with( name.string(), "ccl:background:" ) )
			{
				const ccl::SocketType *input = background->node_type->find_input( ccl::ustring( name.string().c_str() + 15 ) );
				if( value && input )
				{
					if( boost::starts_with( name.string(), "ccl:background:visibility:" ) )
					{
						if( const Data *d = reportedCast<const IECore::Data>( value, "option", name ) )
						{
							if( const IntData *data = static_cast<const IntData *>( d ) )
							{
								auto &vis = data->readable();
								auto ray = nameToRayType( name.string().c_str() + 26 );
								background->visibility = vis ? background->visibility |= ray : background->visibility & ~ray;
							}
						}
					}
					else if( name == g_backgroundShaderOptionName )
					{
						m_backgroundShader = nullptr;
						if( const IECoreScene::ShaderNetwork *d = reportedCast<const IECoreScene::ShaderNetwork>( value, "option", name ) )
						{
							m_backgroundShader = m_shaderCache->get( d );
							background->shader = m_backgroundShader.get();
						}
						else
						{
							background->shader = m_scene->default_background;
						}
					}
					else if( const Data *data = reportedCast<const Data>( value, "option", name ) )
					{
						SocketAlgo::setSocket( (ccl::Node*)background, input, data );
					}
					else
					{
						background->set_default_value( *input );
					}
				}
				else if( input )
				{
					background->set_default_value( *input );
				}
				return;
			}
			else if( boost::starts_with( name.string(), "ccl:film:" ) )
			{
				const ccl::SocketType *input = film->node_type->find_input( ccl::ustring( name.string().c_str() + 9 ) );
				if( value && input )
				{
					if( const Data *data = reportedCast<const Data>( value, "option", name ) )
					{
						SocketAlgo::setSocket( (ccl::Node*)film, input, data );
					}
					else
					{
						film->set_default_value( *input );
					}
				}
				else if( input )
				{
					film->set_default_value( *input );
				}
				return;
			}
			else if( boost::starts_with( name.string(), "ccl:integrator:" ) )
			{
				const ccl::SocketType *input = integrator->node_type->find_input( ccl::ustring( name.string().c_str() + 15 ) );
				if( value && input )
				{
					for( const auto &sampleName : g_squareSamplesOptionNames )
					{
						if( name == sampleName )
						{
							if( const IntData *data = reportedCast<const IntData>( value, "option", name ) )
							{
								// Square the values
								integrator->set( *input, data->readable() * data->readable() );
							}
							else
							{
								integrator->set_default_value( *input );
							}
							return;
						}
					}
					if( const Data *data = reportedCast<const Data>( value, "option", name ) )
					{
						SocketAlgo::setSocket( (ccl::Node*)integrator, input, data );
					}
					else
					{
						integrator->set_default_value( *input );
					}
				}
				else if( input )
				{
					integrator->set_default_value( *input );
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
			auto *film = m_filmCache.get();

			if( !output )
			{
				const auto coutput = m_outputs.find( name );
				if( coutput != m_outputs.end() )
				{
					auto *o = coutput->second.get();
					auto passType = nameToPassType( o->m_data );
					if( passType == ccl::PASS_CRYPTOMATTE )
					{
						if( o->m_name == "cryptomatte_asset" )
						{
							film->cryptomatte_passes = (ccl::CryptomatteType)( film->cryptomatte_passes ^ ccl::CRYPT_ASSET );
						}
						else if( o->m_name == "cryptomatte_object" )
						{
							film->cryptomatte_passes = (ccl::CryptomatteType)( film->cryptomatte_passes ^ ccl::CRYPT_OBJECT );
						}
						else if( o->m_name == "cryptomatte_material" )
						{
							film->cryptomatte_passes = (ccl::CryptomatteType)( film->cryptomatte_passes ^ ccl::CRYPT_MATERIAL );
						}
					}
					m_outputs.erase( name );
				}
				return;
			}

			auto passType = nameToPassType( output->getData() );
			if( passType == ccl::PASS_NONE )
				return;

			ccl::vector<ccl::Pass> passes;
			// Beauty
			ccl::Pass::add( ccl::PASS_COMBINED, passes );

			if( !ccl::Pass::contains( m_filmCache->passes, passType ) )
			{
				m_outputs[name] = new CyclesOutput( output );
			}
			else if ( output->getData() == "rgba" )
			{
				m_outputs[name] = new CyclesOutput( output );
			}
			else
				return;

			for( auto &coutput : m_outputs )
			{
				if( coutput.second->m_passType == ccl::PASS_COMBINED )
				{
					continue;
				}
				else if( coutput.second->m_passType == ccl::PASS_CRYPTOMATTE )
				{
					string cryptoName( "Crypto" );
					if( output->getName() == "cryptomatte_asset" )
					{
						cryptoName += "Asset";
						film->cryptomatte_passes = (ccl::CryptomatteType)( film->cryptomatte_passes | ccl::CRYPT_ASSET );
					}
					else if( output->getName() == "cryptomatte_object" )
					{
						cryptoName += "Object";
						film->cryptomatte_passes = (ccl::CryptomatteType)( film->cryptomatte_passes | ccl::CRYPT_OBJECT );
					}
					else if( output->getName() == "cryptomatte_material" )
					{
						cryptoName += "Material";
						film->cryptomatte_passes = (ccl::CryptomatteType)( film->cryptomatte_passes | ccl::CRYPT_MATERIAL );
					}
					else
					{
						continue;
					}
					for( int i = 0; i < film->cryptomatte_depth; ++i )
					{
						string cryptoFullName = ( boost::format( "%s%02i" ) % cryptoName % i ).str();
						ccl::Pass::add( ccl::PASS_CRYPTOMATTE, passes, cryptoFullName.c_str() );
					}
				}
				else
					ccl::Pass::add( coutput.second->m_passType, passes );
			}

			m_bufferParamsModified.passes = passes;
		}

		Renderer::AttributesInterfacePtr attributes( const IECore::CompoundObject *attributes ) override
		{
			return m_attributesCache->get( attributes );
		}

		ObjectInterfacePtr camera( const std::string &name, const IECoreScene::Camera *camera, const AttributesInterface *attributes ) override
		{
			SharedCCameraPtr ccamera = m_cameraCache->get( camera, name );
			if( !ccamera )
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
			SharedCLightPtr clight = m_lightCache->get( name );
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

			ObjectInterfacePtr result = new CyclesObject( instance );
			result->attributes( attributes );
			return result;
		}

		ObjectInterfacePtr object( const std::string &name, const std::vector<const IECore::Object *> &samples, const std::vector<float> &times, const AttributesInterface *attributes ) override
		{
			Instance instance = m_instanceCache->get( samples, times, name );

			ObjectInterfacePtr result = new CyclesObject( instance );
			result->attributes( attributes );
			return result;
		}

		void render() override
		{
			pause();
			updateSceneObjects();
			updateOptions();
			// Clear out any objects which aren't needed in the cache.
			if( m_renderType == Interactive )
			{
				m_cameraCache->clearUnused();
				m_lightCache->clearUnused();
				m_shaderCache->clearUnused();
				m_instanceCache->clearUnused();
				m_attributesCache->clearUnused();
			}

			updateCamera();
			updateOutputs();

			if( m_rendering )
			{
				m_scene->reset();
				//m_session->update_scene();
                m_session->reset( m_bufferParams, m_sessionParams.samples );
				m_session->set_pause( false );
				return;
			}

			m_rendering = true;

			m_session->start();

			if( m_renderType == Interactive )
			{
				return;
			}

			m_session->wait();

			writeImages();

			m_rendering = false;
		}

		void pause() override
		{
			m_session->set_pause( true );
		}

		void writeRenderTile( ccl::RenderTile& rtile )
		{
			m_renderCallback->writeRenderTile( rtile );
		}

		void updateRenderTile( ccl::RenderTile& rtile, bool highlight )
		{
			m_renderCallback->updateRenderTile( rtile, highlight );
		}

	private :

		void init()
		{
			// Clear scene & session if they exist.
			if( m_session )
				delete m_session;
			
			m_renderCallback.reset();

			// Fallback
			ccl::DeviceType device_type_fallback = ccl::DEVICE_CPU;
			ccl::DeviceInfo device_fallback;

			ccl::DeviceType device_type = ccl::Device::type_from_string( m_deviceName.c_str() );
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
					m_sessionParams.device = device;
					device_available = true;
					break;
				}
			}
			if( !device_available )
			{
				IECore::msg( IECore::Msg::Warning, "CyclesRenderer", boost::format( "Cannot find the device \"%s\" requested, reverting to CPU." ) % m_deviceName );
				m_sessionParams.device = device_fallback;
			}

			m_session = new ccl::Session( m_sessionParams );

			m_session->write_render_tile_cb = function_bind( &CyclesRenderer::writeRenderTile, this, ccl::_1 );
			m_session->update_render_tile_cb = function_bind( &CyclesRenderer::updateRenderTile, this, ccl::_1, ccl::_2 );
			m_session->progress.set_update_callback( function_bind( &CyclesRenderer::progress, this ) );

			m_session->set_pause( true );

			m_scene = new ccl::Scene( m_sceneParams, m_session->device );
			m_scene->params = m_sceneParams;

			m_renderCallback = new RenderCallback( m_session, ( m_renderType == Interactive ) ? true : false );

			// Grab the default camera from cycles.
			m_defaultCamera = m_scene->camera;
			// CyclesOptions will set some values to these.
			m_integrator = m_scene->integrator;
			m_background = m_scene->background;
			m_background->transparent = true;
			m_film = m_scene->film;
			m_curveSystemManager = m_scene->curve_system_manager;

			m_session->scene = m_scene;

			m_scene->camera->need_update = true;
			m_scene->camera->update( m_scene );

			m_session->reset( m_bufferParams, m_sessionParams.samples );
		}

		void updateSceneObjects()
		{
			m_shaderCache->update( m_scene );
			m_lightCache->update( m_scene );
			m_instanceCache->update( m_scene );
		}

		void updateOptions()
		{
			// This doesn't get checked, so we set it just in-case.
			m_session->params.samples = m_sessionParams.samples;
			// If anything changes in scene or session, we reset.
			if( m_sceneParams.modified( m_sceneParams ) ||
			    m_session->params.modified( m_sessionParams ) )
			{
				m_scene->params = m_sceneParams;
				m_session->params = m_sessionParams;
				reset();
			}

			const auto *integrator = m_integratorCache.get();
			if( m_integrator->modified( *integrator ) )
			{
				memcpy( m_integrator, integrator, sizeof( ccl::Integrator ) );
				m_integrator->tag_update( m_scene );
			}

			const auto *background = m_backgroundCache.get();
			if( m_background->modified( *background ) )
			{
				memcpy( m_background, background, sizeof( ccl::Background ) );
				m_background->tag_update( m_scene );
			}

			const auto *film = m_filmCache.get();
			if( m_film->modified( *film ) )
			{
				memcpy( m_film, film, sizeof( ccl::Film ) );
				m_film->tag_update( m_scene );
			}

			const auto *curveSystemManager = m_curveSystemManagerCache.get();
			if( m_curveSystemManager->modified( *curveSystemManager ) )
			{
				memcpy( m_curveSystemManager, curveSystemManager, sizeof( ccl::CurveSystemManager ) );
				m_curveSystemManager->tag_update( m_scene );
			}
		}

		void updateOutputs()
		{
			// Update m_bufferParams from the current camera.
			auto *cam = m_scene->camera;
			const int width = cam->width;
			const int height = cam->height;
			m_bufferParamsModified.full_width = cam->full_width;
			m_bufferParamsModified.full_height = cam->full_height;
			ccl::BoundBox2D border = cam->border.clamp();
			m_bufferParamsModified.full_x = (int)(border.left * (float)width);
			m_bufferParamsModified.full_y = (int)(border.bottom * (float)height);
			m_bufferParamsModified.width =  (int)(border.right * (float)width) - m_bufferParamsModified.full_x;
			m_bufferParamsModified.height = (int)(border.top * (float)height) - m_bufferParamsModified.full_y;

			if( !m_bufferParams.modified( m_bufferParamsModified ) )
				return;
			else
				m_bufferParams = m_bufferParamsModified;

			m_session->reset( m_bufferParams, m_sessionParams.samples );
			m_renderCallback->updateOutputs( m_outputs );
			if( m_renderType != Interactive )
			{
				for( auto &output : m_outputs )
				{
					CyclesOutput *co = output.second.get();
					co->createImage( cam );
				}
			}
		}

		void reset()
		{
			pause();
			m_rendering = false;
			// This is so cycles doesn't delete the objects that Gaffer manages.
			m_scene->objects.clear();
			m_scene->meshes.clear();
			m_scene->shaders.clear();
			m_scene->lights.clear();
			m_scene->particle_systems.clear();
			// Cycles created the defaultCamera, so we give it back for it to delete.
			m_scene->camera = m_defaultCamera;
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
				m_scene->camera = m_defaultCamera;
			}
			else
			{
				auto ccamera = m_cameraCache->get( cameraIt->second.get(), cameraIt->first );
				if( m_scene->camera != ccamera.get() )
				{
					m_scene->camera = ccamera.get();
				}
			}
			m_scene->camera->need_update = true;
			m_scene->camera->update( m_scene );
		}

		void writeImages()
		{
			if( m_renderType != Interactive )
			{
				for( auto &output : m_outputs )
				{
					CyclesOutput *co = output.second.get();
					co->writeImage();
				}
			}
		}

		void progress()
		{
			string status, substatus;

			/* get status */
			float progress = m_session->progress.get_progress();
			m_session->progress.get_status(status, substatus);

			if(substatus != "")
				status += ": " + substatus;

			/* print status */
			IECore::msg( IECore::Msg::Info, "CyclesRenderer", boost::format( "Progress %05.2f   %s" ) % (double)(progress * 100.0f ) % status );
		}

		// Cycles core objects.
		ccl::Session *m_session;
		ccl::Scene *m_scene;
		ccl::SessionParams m_sessionParams;
		ccl::SceneParams m_sceneParams;
		ccl::BufferParams m_bufferParams;
		ccl::BufferParams m_bufferParamsModified;
		ccl::Camera *m_defaultCamera;
		ccl::Integrator *m_integrator;
		ccl::Background *m_background;
		ccl::Film *m_film;
		ccl::CurveSystemManager *m_curveSystemManager;

		// Background shader
		SharedCShaderPtr m_backgroundShader;

		// Defaults
		ccl::SessionParams m_sessionParamsDefault;
		ccl::SceneParams m_sceneParamsDefault;
		CCurveSystemManagerPtr m_curveSystemManagerDefault;

		// IECoreScene::Renderer
		string m_deviceName;
		string m_shadingsystemName;
		RenderType m_renderType;
		int m_frame;
		string m_camera;
		bool m_rendering;

		// Caches.
		CameraCachePtr m_cameraCache;
		ShaderCachePtr m_shaderCache;
		LightCachePtr m_lightCache;
		InstanceCachePtr m_instanceCache;
		//ParticleSystemPtr m_particleSystemCache;
		AttributesCachePtr m_attributesCache;

		// Store these to restore.
		CIntegratorPtr m_integratorCache;
		CBackgroundPtr m_backgroundCache;
		CFilmPtr m_filmCache;
		CCurveSystemManagerPtr m_curveSystemManagerCache;

		// Outputs
		OutputMap m_outputs;

		// Cameras (Cycles can only know of one camera at a time)
		typedef unordered_map<string, ConstCameraPtr> CameraMap;
		CameraMap m_cameras;
		tbb::spin_mutex m_camerasMutex;

		// RenderCallback
		RenderCallbackPtr m_renderCallback;

		// Registration with factory
		static Renderer::TypeDescription<CyclesRenderer> g_typeDescription;

};

IECoreScenePreview::Renderer::TypeDescription<CyclesRenderer> CyclesRenderer::g_typeDescription( "Cycles" );

} // namespace
