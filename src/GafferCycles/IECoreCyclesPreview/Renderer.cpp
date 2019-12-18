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
#include "GafferCycles/IECoreCyclesPreview/ParticleAlgo.h"
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
#include "boost/lexical_cast.hpp"
#include "boost/optional.hpp"

#include "tbb/concurrent_hash_map.h"

#include <unordered_map>

// Cycles
#include "bvh/bvh_params.h"
#include "device/device.h"
#include "device/device_task.h"
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

#ifdef WITH_CYCLES_OPENVDB
#include "render/openvdb.h"
#endif

#include "render/osl.h"
#include "render/scene.h"
#include "render/session.h"
#include "subd/subd_dice.h"
#include "util/util_array.h"
#include "util/util_function.h"
#include "util/util_logging.h"
#include "util/util_path.h"
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
typedef std::shared_ptr<ccl::ParticleSystem> SharedCParticleSystemPtr;

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

} // namespace

//////////////////////////////////////////////////////////////////////////
// CyclesOutput
//////////////////////////////////////////////////////////////////////////

namespace
{

ccl::PassType nameToPassType( const std::string &name )
{
#define MAP_PASS(passname, passtype) if(name == passname) return passtype;
#define MAP_PASS_STARTSWITH(startswith, passtype) if(boost::starts_with(name,startswith)) return passtype;
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
#ifdef WITH_CYCLES_ADAPTIVE_SAMPLING
	MAP_PASS( "debug_sample_count", ccl::PASS_SAMPLE_COUNT );
	MAP_PASS( "adaptive_aux_buffer", ccl::PASS_ADAPTIVE_AUX_BUFFER );
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
	MAP_PASS_STARTSWITH( "cryptomatte", ccl::PASS_CRYPTOMATTE );
	MAP_PASS_STARTSWITH( "AOVC",  ccl::PASS_AOV_COLOR );
	MAP_PASS_STARTSWITH( "AOVV", ccl::PASS_AOV_VALUE );
#ifdef WITH_CYCLES_LIGHTGROUPS
	MAP_PASS_STARTSWITH( "lightgroup", ccl::PASS_LIGHTGROUP );
#endif
#undef MAP_PASS
#undef MAP_PASS_STARTSWITH

	return ccl::PASS_NONE;
}

int nameToDenoisePassType( const std::string &name )
{
#define MAP_PASS(passname, offset) if(name == passname) return offset;
	MAP_PASS( "denoise_rgba", ccl::DENOISING_PASS_PREFILTERED_COLOR );
	MAP_PASS( "denoise_normal", ccl::DENOISING_PASS_PREFILTERED_NORMAL );
	MAP_PASS( "denoise_albedo", ccl::DENOISING_PASS_PREFILTERED_ALBEDO );
	MAP_PASS( "denoise_depth", ccl::DENOISING_PASS_PREFILTERED_DEPTH );
	MAP_PASS( "denoise_shadowing", ccl::DENOISING_PASS_PREFILTERED_SHADOWING );
	MAP_PASS( "denoise_variance", ccl::DENOISING_PASS_PREFILTERED_VARIANCE );
	MAP_PASS( "denoise_intensity", ccl::DENOISING_PASS_PREFILTERED_INTENSITY );
	MAP_PASS( "denoise_clean", ccl::DENOISING_PASS_CLEAN );
#undef MAP_PASS

	return -1;
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
#ifdef WITH_CYCLES_ADAPTIVE_SAMPLING
		case ccl::PASS_SAMPLE_COUNT:
			return 1;
		case ccl::PASS_ADAPTIVE_AUX_BUFFER:
			return 4;
#endif
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
		case ccl::PASS_AOV_COLOR:
			return 3;
		case ccl::PASS_AOV_VALUE:
			return 1;
#ifdef WITH_CYCLES_LIGHTGROUPS
		case ccl::PASS_LIGHTGROUP:
			return 3;
#endif
		default:
			return 0;
	}
}

int denoiseComponents( ccl::DenoisingPassOffsets type )
{
	switch( type )
	{
		case ccl::DENOISING_PASS_PREFILTERED_COLOR:
			return 4;
		case ccl::DENOISING_PASS_PREFILTERED_NORMAL:
			return 3;
		case ccl::DENOISING_PASS_PREFILTERED_ALBEDO:
			return 3;
		case ccl::DENOISING_PASS_PREFILTERED_DEPTH:
			return 1;
		case ccl::DENOISING_PASS_PREFILTERED_SHADOWING:
			return 1;
		case ccl::DENOISING_PASS_PREFILTERED_VARIANCE:
			return 3;
		case ccl::DENOISING_PASS_PREFILTERED_INTENSITY:
			return 1;
		case ccl::DENOISING_PASS_CLEAN:
			return 3;
		default:
			return 0;
	}
}

int getNumMultiPassNames( const std::string &dataName, std::string &baseName )
{
	vector<string> split;
	boost::split( split, dataName, boost::is_any_of( "<" ) );
	string numStr = boost::erase_all_copy( split.back(), ">" );
	baseName = split.front();
	try
	{
		int num = boost::lexical_cast<int>( numStr );
		return num;
	}
	catch( const std::exception& e )
	{
		IECore::msg( IECore::Msg::Warning, "CyclesRenderer::output", boost::format( "Cannot determine number of passes for \"%s\". Try using <num_passes> on the end of data." ) % dataName );
		return 0;
	}
}

class CyclesOutput : public IECore::RefCounted
{

	public :

		CyclesOutput( const IECoreScene::Output *output )
		{
			m_name = output->getName();
			m_type = output->getType();
			m_data = output->getData();
			m_passType = nameToPassType( m_data );

#ifdef WITH_CYCLES_LIGHTGROUPS
			if( m_passType == ccl::PASS_LIGHTGROUP )
			{
				int num = getNumMultiPassNames( output->getData(), m_data );
				m_images.resize( num );
			}
			else
#endif
			{
				m_images.resize( 1 );
			}

			m_denoisingPassOffsets = nameToDenoisePassType( m_data );
			if( ( m_passType == ccl::PASS_NONE ) && ( m_denoisingPassOffsets > 0 ) )
			{
				m_components = denoiseComponents( (ccl::DenoisingPassOffsets)m_denoisingPassOffsets );
			}
			else
			{
				m_components = passComponents( m_passType );
			}
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
			for( auto image : m_images )
			{
				if( image.get() )
				{
					image.reset();
				}
			}

			//ccl::DisplayBuffer &display = m_session->display;
			// TODO: Work out if Cycles can do overscan...
			Box2i displayWindow( 
				V2i( 0, 0 ),
				V2i( camera->width - 1, camera->height - 1 )
				);
			Box2i dataWindow(
				V2i( (int)(camera->border.left * (float)camera->width), (int)(camera->border.bottom * (float)camera->height) ),
				V2i( (int)(camera->border.right * (float)camera->width) - 1, (int)(camera->border.top * (float)camera->height - 1 ) )
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

			for( auto image : m_images )
			{
				image = new ImageDisplayDriver( displayWindow, dataWindow, channelNames, m_parameters );
			}
		}

		void writeImage()
		{
			if( m_interactive )
			{
				IECore::msg( IECore::Msg::Debug, "CyclesRenderer::CyclesOutput", boost::format( "Skipping interactive output: \"%s\"." ) % m_name );
				return;
			}
			for( auto image : m_images )
			{
				if( !image )
				{
					IECore::msg( IECore::Msg::Warning, "CyclesRenderer::CyclesOutput", boost::format( "Cannot write output: \"%s\"." ) % m_name );
					return;
				}

				IECoreImage::ImagePrimitivePtr imageCopy = image->image()->copy();
				IECore::WriterPtr writer = IECoreImage::ImageWriter::create( imageCopy, "tmp." + m_type );
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
		}

		std::string m_name;
		std::string m_type;
		std::string m_data;
		ccl::PassType m_passType;
		int m_denoisingPassOffsets;
		ccl::TypeDesc m_quantize;
		std::vector<ImageDisplayDriverPtr> m_images;
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

		RenderCallback( bool interactive )
			: m_session( nullptr ), m_interactive( interactive ), m_displayDriver( nullptr )
		{
		}
		
		~RenderCallback()
		{
			if( m_displayDriver )
			{
				try
				{
					m_displayDriver->imageClose();
				}
				catch( const std::exception &e )
				{
					IECore::msg( IECore::Msg::Error, "DisplayDriver::imageClose", e.what() );
				}
			}
		}

		void updateSession( ccl::Session *session )
		{
			m_session = session;
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
				V2i( (int)(camera->border.left * (float)camera->width), (int)(camera->border.bottom * (float)camera->height) ),
				V2i( (int)(camera->border.right * (float)camera->width) - 1, (int)(camera->border.top * (float)camera->height - 1 ) )
				);

			//CompoundDataPtr parameters = new CompoundData();
			//auto &p = parameters->writable();

			std::vector<std::string> channelNames;

			for( auto &output : m_outputs )
			{
				std::string name = output.second->m_data;
				auto passType = output.second->m_passType;
				int components = passComponents( passType );

#ifdef WITH_CYCLES_LIGHTGROUPS
				if( passType == ccl::PASS_LIGHTGROUP )
				{
					for( int i = 1; i <= output.second->m_images.size(); ++i )
					{
						name = ( boost::format( "%s%02i" ) % output.second->m_data % i ).str();
						if( m_interactive )
							getChannelNames( name, components, channelNames );
					}
				}
				else
#endif
				{
					if( m_interactive )
						getChannelNames( name, components, channelNames );
				}
			}

			if( m_interactive )
			{
				for( auto &output : m_outputs )
				{
					if( output.second->m_type == "ieDisplay" && output.second->m_data == "rgba")
					{
						const auto parameters = output.second->m_parameters;
						const StringData *driverType = parameters->member<StringData>( "driverType", true );
						m_displayDriver = DisplayDriver::create(
							driverType->readable(),
							displayWindow,
							dataWindow,
							channelNames,
							parameters
							);
						break;
					}
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
			// No session, exit out
			if( !m_session )
				return;
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
			const int x = rtile.x;
			const int y = rtile.y;
			const int w = rtile.w;
			const int h = rtile.h;

			const int cam_h = m_session->scene->camera->height;

			Box2i tile( V2i( x, y ), V2i( x + w - 1, y + h - 1 ) );

			ccl::RenderBuffers *buffers = rtile.buffers;
			/* copy data from device */
			if(!buffers->copy_from_device())
				return;

			const float exposure = m_session->scene->film->exposure;

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
				bool read = false;
				if( m_interactive && !output.second->m_interactive )
					continue;
				if( !m_interactive && output.second->m_interactive )
					continue;
				int numChannels = output.second->m_components;

#ifdef WITH_CYCLES_LIGHTGROUPS
				if( output.second->m_passType == ccl::PASS_LIGHTGROUP )
				{
					int i = 0;
					for( auto image : output.second->m_images )
					{
						i += 1;
						read = buffers->get_pass_rect( ( boost::format( "%s%02i" ) % output.second->m_data % i ).str().c_str(), exposure, sample, numChannels, &tileData[0] );
						if( !read )
							memset( &tileData[0], 0, tileData.size()*sizeof(float) );

						if( m_interactive )
							outChannelOffset = interleave( &tileData[0], w, h, numChannels, numOutputChannels, outChannelOffset, &interleavedData[0] );
						else
							image->imageData( tile, &tileData[0], w * h * numChannels );
					}
				}
				else
#else
				if( output.second->m_passType != ccl::PASS_NONE )
#endif
				{
					read = buffers->get_pass_rect( output.second->m_data.c_str(), exposure, sample, numChannels, &tileData[0] );
					if( !read )
						memset( &tileData[0], 0, tileData.size()*sizeof(float) );
					
					if( m_interactive )
						outChannelOffset = interleave( &tileData[0], w, h, numChannels, numOutputChannels, outChannelOffset, &interleavedData[0] );
					else
						output.second->m_images[0]->imageData( tile, &tileData[0], w * h * numChannels );
				}
				else
				{
					if( output.second->m_denoisingPassOffsets >= 0 )
						read = buffers->get_denoising_pass_rect( output.second->m_denoisingPassOffsets, exposure, sample, numChannels, &tileData[0] );

					if( m_interactive )
						outChannelOffset = interleave( &tileData[0], w, h, numChannels, numOutputChannels, outChannelOffset, &interleavedData[0] );
					else
						output.second->m_images[0]->imageData( tile, &tileData[0], w * h * numChannels );
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

		int interleave( float *tileData,
						const int width, const int height,
						const int numChannels,
						const int numOutputChannels,
						const int outChannelOffset,
						float *interleavedData )
		{
			int offset = outChannelOffset;
			for( int c = 0; c < numChannels; c++ )
			{
				// This is taken out of the Arnold output driver. Interleaving.
				float *in = &(tileData[0]) + c;
				float *out = interleavedData + offset;
				for( int j = 0; j < height; j++ )
				{
					for( int i = 0; i < width; i++ )
					{
						*out = *in;
						out += numOutputChannels;
						in += numChannels;
					}
				}
				offset += 1;
			}
			return offset;
		}

		void getChannelNames( const string name, const int components, vector<string> &channelNames )
		{
			if( name == "rgba" )
			{
				channelNames.push_back( "R" );
				channelNames.push_back( "G" );
				channelNames.push_back( "B" );
				channelNames.push_back( "A" );
				return;
			}
			if( components == 1 )
			{
				channelNames.push_back( name );
				return;
			}
			else if( components == 2 )
			{
				channelNames.push_back( name + ".R" );
				channelNames.push_back( name + ".G" );
				return;
			}
			else if( components == 3 )
			{
				channelNames.push_back( name + ".R" );
				channelNames.push_back( name + ".G" );
				channelNames.push_back( name + ".B" );
				return;
			}
			else if( components == 4 )
			{
				channelNames.push_back( name + ".R" );
				channelNames.push_back( name + ".G" );
				channelNames.push_back( name + ".B" );
				channelNames.push_back( name + ".A" );
				return;
			}
		}

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

		ShaderCache( ccl::Scene *scene )
			: m_scene( scene ), m_shaderManager( nullptr )
		{
			#ifdef WITH_OSL
			m_shaderManager = new ccl::OSLShaderManager();
			#endif
			m_defaultSurface = get( nullptr, nullptr );
		}

		~ShaderCache()
		{
			#ifdef WITH_OSL
			delete m_shaderManager;
			#endif
		}

		void update( ccl::Scene *scene )
		{
			m_scene = scene;
			updateShaders();
		}

		// Can be called concurrently with other get() calls.
		SharedCShaderPtr get( const IECoreScene::ShaderNetwork *shader, const IECore::CompoundObject *attributes )
		{
			IECore::MurmurHash h = shader ? shader->Object::hash() : MurmurHash();
			IECore::MurmurHash hSubst;
			if( attributes && shader )
			{
				shader->hashSubstitutions( attributes, hSubst );
				h.append( hSubst );
			}
			Cache::accessor a;
			m_cache.insert( a, h );
			if( !a->second )
			{
				if( shader )
				{
					const std::string namePrefix = "shader:" + a->first.toString() + ":";
					if( hSubst != IECore::MurmurHash() )
					{
						IECoreScene::ShaderNetworkPtr substitutedShader = shader->copy();
						substitutedShader->applySubstitutions( attributes );
						a->second = SharedCShaderPtr( ShaderNetworkAlgo::convert( substitutedShader.get(), m_shaderManager, namePrefix ) );
					}
					else
					{
						a->second = SharedCShaderPtr( ShaderNetworkAlgo::convert( shader, m_shaderManager, namePrefix ) );
					}
				}
				else
				{
					// This creates a camera dot-product shader/facing ratio.
					const std::string name = "defaultSurfaceShader";
					ccl::Shader *cshader = new ccl::Shader();
					ccl::ShaderGraph *cgraph = new ccl::ShaderGraph();
					cshader->name = name.c_str();
					ccl::ShaderNode *outputNode = (ccl::ShaderNode*)cgraph->output();
					ccl::VectorMathNode *vecMath = new ccl::VectorMathNode();
					vecMath->type = ccl::NODE_VECTOR_MATH_DOT_PRODUCT;
					ccl::GeometryNode *geo = new ccl::GeometryNode();
					ccl::ShaderNode *vecMathNode = cgraph->add( (ccl::ShaderNode*)vecMath );
					ccl::ShaderNode *geoNode = cgraph->add( (ccl::ShaderNode*)geo );
					cgraph->connect( IECoreCycles::ShaderNetworkAlgo::output( geoNode, "normal" ), 
									 IECoreCycles::ShaderNetworkAlgo::input( vecMathNode, "vector1" ) );
					cgraph->connect( IECoreCycles::ShaderNetworkAlgo::output( geoNode, "incoming" ), 
									 IECoreCycles::ShaderNetworkAlgo::input( vecMathNode, "vector2" ) );
					cgraph->connect( IECoreCycles::ShaderNetworkAlgo::output( vecMathNode, "value" ), 
									 IECoreCycles::ShaderNetworkAlgo::input( outputNode, "surface" ) );
					cshader->set_graph( cgraph );
					a->second = SharedCShaderPtr( cshader );
				}
				
			}
			return a->second;
		}

		SharedCShaderPtr defaultSurface()
		{
			return m_defaultSurface;
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

		void updateShaders()
		{
			auto &shaders = m_scene->shaders;
			//shaders.clear();
			shaders.resize(4); // 4 built-in shaders, wipe the rest as we manage those
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

		ccl::Scene *m_scene;
		typedef tbb::concurrent_hash_map<IECore::MurmurHash, SharedCShaderPtr> Cache;
		Cache m_cache;
		ccl::ShaderManager *m_shaderManager;
		SharedCShaderPtr m_defaultSurface;

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
// Per-object color
IECore::InternedString g_colorAttributeName( "Cs" );
// Cycles Light
IECore::InternedString g_lightAttributeName( "ccl:light" );
// Particle
std::array<IECore::InternedString, 2> g_particleIndexAttributeNames = { {
	"index",
	"instanceIndex",
} };
IECore::InternedString g_particleAgeAttributeName( "age" );
IECore::InternedString g_particleLifetimeAttributeName( "lifetime" );
std::array<IECore::InternedString, 2> g_particleLocationAttributeNames = { {
	"location",
	"P",
} };
IECore::InternedString g_particleRotationAttributeName( "rotation" );
std::array<IECore::InternedString, 2> g_particleRotationAttributeNames = { {
	"rotation",
	"orientation",
} };
std::array<IECore::InternedString, 2> g_particleSizeAttributeNames = { {
	"size",
	"width",
} };
IECore::InternedString g_particleVelocityAttributeName( "velocity" );
IECore::InternedString g_particleAngularVelocityAttributeName( "angular_velocity" );

// Shader Assignment
IECore::InternedString g_cyclesSurfaceShaderAttributeName( "ccl:surface" );
IECore::InternedString g_oslSurfaceShaderAttributeName( "osl:surface" );
IECore::InternedString g_oslShaderAttributeName( "osl:shader" );
IECore::InternedString g_cyclesDisplacementShaderAttributeName( "ccl:displacement" );
IECore::InternedString g_cyclesVolumeShaderAttributeName( "ccl:volume" );
// Ray visibility
IECore::InternedString g_cameraVisibilityAttributeName( "ccl:visibility:camera" );
IECore::InternedString g_diffuseVisibilityAttributeName( "ccl:visibility:diffuse" );
IECore::InternedString g_glossyVisibilityAttributeName( "ccl:visibility:glossy" );
IECore::InternedString g_transmissionVisibilityAttributeName( "ccl:visibility:transmission" );
IECore::InternedString g_shadowVisibilityAttributeName( "ccl:visibility:shadow" );
IECore::InternedString g_scatterVisibilityAttributeName( "ccl:visibility:scatter" );

IECore::InternedString g_setsAttributeName( "sets" );
IECore::InternedString g_cryptomatteAssetAttributeName( "asset:" );

// Light-group
IECore::InternedString g_lightGroupAttributeName( "ccl:light_group" );

class CyclesAttributes : public IECoreScenePreview::Renderer::AttributesInterface
{

	public :

		CyclesAttributes( const IECore::CompoundObject *attributes, ShaderCache *shaderCache )
			:	m_shaderHash( 0 ), m_visibility( ~0 ), m_useHoldout( false ), m_isShadowCatcher( false ), m_maxLevel( 12 ), m_dicingRate( 1.0f ), m_color( Color3f( 0.0f ) ), m_particle( attributes ), m_lightGroup( -1 )
		{
			updateVisibility( g_cameraVisibilityAttributeName,       (int)ccl::PATH_RAY_CAMERA,         attributes );
			updateVisibility( g_diffuseVisibilityAttributeName,      (int)ccl::PATH_RAY_DIFFUSE,        attributes );
			updateVisibility( g_glossyVisibilityAttributeName,       (int)ccl::PATH_RAY_GLOSSY,         attributes );
			updateVisibility( g_transmissionVisibilityAttributeName, (int)ccl::PATH_RAY_TRANSMIT,       attributes );
			updateVisibility( g_shadowVisibilityAttributeName,       (int)ccl::PATH_RAY_SHADOW,         attributes );
			updateVisibility( g_scatterVisibilityAttributeName,      (int)ccl::PATH_RAY_VOLUME_SCATTER, attributes );

			m_useHoldout = attributeValue<bool>( g_useHoldoutAttributeName, attributes, m_useHoldout );
			m_isShadowCatcher = attributeValue<bool>( g_isShadowCatcherAttributeName, attributes, m_isShadowCatcher );
			m_maxLevel = attributeValue<int>( g_maxLevelAttributeName, attributes, m_maxLevel );
			m_dicingRate = attributeValue<float>( g_dicingRateAttributeName, attributes, m_dicingRate );
			m_color = attributeValue<Color3f>( g_colorAttributeName, attributes, m_color );
			m_lightGroup = attributeValue<int>( g_lightGroupAttributeName, attributes, m_lightGroup );

			m_sets = attribute<IECore::InternedStringVectorData>( g_setsAttributeName, attributes );

			// Surface shader
			const IECoreScene::ShaderNetwork *surfaceShaderAttribute = attribute<IECoreScene::ShaderNetwork>( g_cyclesSurfaceShaderAttributeName, attributes );
			surfaceShaderAttribute = surfaceShaderAttribute ? surfaceShaderAttribute : attribute<IECoreScene::ShaderNetwork>( g_oslSurfaceShaderAttributeName, attributes );
			surfaceShaderAttribute = surfaceShaderAttribute ? surfaceShaderAttribute : attribute<IECoreScene::ShaderNetwork>( g_oslShaderAttributeName, attributes );
			if( surfaceShaderAttribute )
			{
				m_shaderHash = hash_value( surfaceShaderAttribute->getOutput() );

				//const IECoreScene::ShaderNetwork *displacementShaderAttribute = attribute<IECoreScene::ShaderNetwork>( g_cyclesDisplacementShaderAttributeName, attributes );
				//const IECoreScene::ShaderNetwork *volumeShaderAttribute = attribute<IECoreScene::ShaderNetwork>( g_cyclesVolumeShaderAttributeName, attributes );

				m_shader = shaderCache->get( surfaceShaderAttribute, attributes );
			}
			else
			{
				// Volume shader
				const IECoreScene::ShaderNetwork *volumeShaderAttribute = attribute<IECoreScene::ShaderNetwork>( g_cyclesVolumeShaderAttributeName, attributes );
				if( volumeShaderAttribute )
				{
					m_shaderHash = hash_value( volumeShaderAttribute->getOutput() );
					m_shader = shaderCache->get( volumeShaderAttribute, attributes );
				}
				else
				{
					// Revert back to the default surface
					m_shader = shaderCache->defaultSurface();
				}
			}

			// Light attributes
			const IECoreScene::ShaderNetwork *lightShaderAttribute = attribute<IECoreScene::ShaderNetwork>( g_lightAttributeName, attributes );
			if( lightShaderAttribute )
			{
				// This is just to store data that is attached to the lights.
				m_light = CLightPtr( IECoreCycles::ShaderNetworkAlgo::convert( lightShaderAttribute ) );
			}
		}

		bool applyObject( ccl::Object *object, const CyclesAttributes *previousAttributes ) const
		{
			object->visibility = m_visibility;
			object->use_holdout = m_useHoldout;
			object->is_shadow_catcher = m_isShadowCatcher;
			object->color = SocketAlgo::setColor( m_color );

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

			m_particle.apply( object );

			// Cryptomatte asset name
			if( m_sets && m_sets->readable().size() )
			{
				const vector<IECore::InternedString> &v = m_sets->readable();
				for( auto const& name : v )
				{
					if( boost::starts_with( name.string(), g_cryptomatteAssetAttributeName.string() ) )
					{
						object->asset_name = ccl::ustring( name.c_str() + 6 );
						break;
					}
				}
			}

#ifdef WITH_CYCLES_LIGHTGROUPS
			if( ( m_lightGroup > 0 ) && ( m_lightGroup <= 32 ) )
			{
				object->lightgroups = (1 << ( m_lightGroup - 1 ) );
			}
			else
			{
				object->lightgroups = 0;
			}
#endif

			return true;
		}

		bool applyLight( ccl::Light *light, const CyclesAttributes *previousAttributes ) const
		{
			if( ccl::Light *clight = m_light.get() )
			{
				light->type = clight->type;
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
				light->strength = clight->strength;
#ifdef WITH_CYCLES_LIGHTGROUPS
				light->lightgroups = clight->lightgroups;
#endif
			}
			if( m_shader.get() )
			{
				light->shader = m_shader.get();
			}

#ifdef WITH_CYCLES_LIGHTGROUPS
			// Override light-group if there is a ccl:lightGroup assigned
			if( ( m_lightGroup > 0 ) && ( m_lightGroup <= 32 ) )
			{
				light->lightgroups = (1 << ( m_lightGroup - 1 ) );
			}
			else if( m_lightGroup == 0 )
			{
				light->lightgroups = 0;
			}
#endif

			return true;
		}

		// Generates a signature for the work done by applyGeometry.
		void hashGeometry( const IECore::Object *object, IECore::MurmurHash &h ) const
		{
			h.append( m_shaderHash );
			const IECore::TypeId objectType = object->typeId();
			switch( (int)objectType )
			{
				case IECoreScene::MeshPrimitiveTypeId :
					if( static_cast<const IECoreScene::MeshPrimitive *>( object )->interpolation() == "catmullClark" )
					{
						h.append( m_dicingRate );
						h.append( m_maxLevel );
					}
					break;
				case IECoreScene::CurvesPrimitiveTypeId :
					break;
				case IECoreScene::SpherePrimitiveTypeId :
					break;
				case IECoreScene::ExternalProceduralTypeId :
					break;
				//case IECoreVDB::VDBObjectTypeId :
				//	break;
				default :
					// No geometry attributes for this type.
					break;
			}
		}

		// Returns true if the given geometry can be instanced.
		bool canInstanceGeometry( const IECore::Object *object ) const
		{
			if( !IECore::runTimeCast<const IECoreScene::VisibleRenderable>( object ) )
			{
				return false;
			}

			if( const IECoreScene::MeshPrimitive *mesh = IECore::runTimeCast<const IECoreScene::MeshPrimitive>( object ) )
			{
				if( mesh->interpolation() == "catmullClark" )
				{
					// For now we treat all subdiv surfaces as unique because they are all treated as adaptive.
					return false;
				}
				else
				{
					return true;
				}
			}

			if( const IECoreScene::PointsPrimitive *points = IECore::runTimeCast<const IECoreScene::PointsPrimitive>( object ) )
			{
				// Need to revisit this one
				return false;
			}

			return true;
		}

	private :

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

		template<typename T>
		static boost::optional<T> optionalAttribute( const IECore::InternedString &name, const IECore::CompoundObject *attributes )
		{
			typedef IECore::TypedData<T> DataType;
			const DataType *data = attribute<DataType>( name, attributes );
			return data ? data->readable() : boost::optional<T>();
		}

		void updateVisibility( const IECore::InternedString &name, int rayType, const IECore::CompoundObject *attributes )
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

		struct Particle
		{
			Particle( const IECore::CompoundObject *attributes )
			{
				for( const auto &name : g_particleIndexAttributeNames )
				{
					index = optionalAttribute<int>( name, attributes );
					if( index )
						break;
				}
				age = optionalAttribute<float>( g_particleAgeAttributeName, attributes );
				lifetime = optionalAttribute<float>( g_particleLifetimeAttributeName, attributes );
				for( const auto &name : g_particleLocationAttributeNames )
				{
					location = optionalAttribute<V3f>( name, attributes );
					if( location )
						break;
				}
				for( const auto &name : g_particleRotationAttributeNames )
				{
					rotation = optionalAttribute<Quatf>( name, attributes );
					if( rotation )
						break;
				}
				for( const auto &name : g_particleSizeAttributeNames )
				{
					size = optionalAttribute<float>( name, attributes );
					if( size )
						break;
				}
				velocity = optionalAttribute<V3f>( g_particleVelocityAttributeName, attributes );
				angular_velocity = optionalAttribute<V3f>( g_particleAngularVelocityAttributeName, attributes );
			}

			boost::optional<int> index;
			boost::optional<float> age;
			boost::optional<float> lifetime;
			boost::optional<V3f> location;
			boost::optional<Quatf> rotation;
			boost::optional<float> size;
			boost::optional<V3f> velocity;
			boost::optional<V3f> angular_velocity;

			void apply( ccl::Object *object ) const
			{
				if( ccl::ParticleSystem *psys = object->particle_system )
				{
					size_t idx = object->particle_index;
					if( idx < psys->particles.size() )
					{
						if( index )
							psys->particles[idx].index = index.get();
						if( age )
							psys->particles[idx].age = age.get();
						if( lifetime )
							psys->particles[idx].lifetime = lifetime.get();
						if( location )
							psys->particles[idx].location = SocketAlgo::setVector( location.get() );
						if( rotation )
							psys->particles[idx].rotation = SocketAlgo::setQuaternion( rotation.get() );
						if( size )
							psys->particles[idx].size = size.get();
						if( velocity )
							psys->particles[idx].velocity = SocketAlgo::setVector( velocity.get() );
						if( angular_velocity )
							psys->particles[idx].angular_velocity = SocketAlgo::setVector( angular_velocity.get() );
					}
				}
			}
		};

		CLightPtr m_light;
		SharedCShaderPtr m_shader;
		size_t m_shaderHash;
		int m_visibility;
		bool m_useHoldout;
		bool m_isShadowCatcher;
		int m_maxLevel;
		float m_dicingRate;
		IECore::ConstInternedStringVectorDataPtr m_sets;
		Color3f m_color;
		Particle m_particle;
		int m_lightGroup;

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
// ParticleSystemCache
//////////////////////////////////////////////////////////////////////////

namespace
{

class ParticleSystemsCache : public IECore::RefCounted
{

	public :

		ParticleSystemsCache( ccl::Scene *scene ) : m_scene( scene )
		{
		}

		void update( ccl::Scene *scene )
		{
			m_scene = scene;
			updateParticleSystems();
		}

		// Can be called concurrently with other get() calls.
		SharedCParticleSystemPtr get( const IECoreScene::PointsPrimitive *points )
		{
			const IECore::MurmurHash hash = points->Object::hash();

			Cache::accessor a;
			m_cache.insert( a, hash );

			if( !a->second )
			{
				a->second = SharedCParticleSystemPtr( ParticleAlgo::convert( points ) );
			}

			return a->second;
		}

		// For unique attributes on instanced meshes.
		SharedCParticleSystemPtr get( const IECore::MurmurHash hash )
		{
			Cache::accessor a;
			m_cache.insert( a, hash );

			if( !a->second )
			{
				ccl::ParticleSystem *pSys = new ccl::ParticleSystem();
				pSys->particles.push_back_slow( ccl::Particle() );
				a->second = SharedCParticleSystemPtr( pSys );
			}
			else
			{
				a->second->particles.push_back_slow( ccl::Particle() );
			}

			a->second->tag_update( m_scene );

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

		void updateParticleSystems()
		{
			auto &pSystems = m_scene->particle_systems;
			pSystems.clear();

			for( Cache::const_iterator it = m_cache.begin(), eIt = m_cache.end(); it != eIt; ++it )
			{
				if( it->second )
				{
					pSystems.push_back( it->second.get() );
				}
			}

			m_scene->particle_system_manager->tag_update( m_scene );
		}

		ccl::Scene *m_scene;
		typedef tbb::concurrent_hash_map<IECore::MurmurHash, SharedCParticleSystemPtr> Cache;
		Cache m_cache;

};

IE_CORE_DECLAREPTR( ParticleSystemsCache )

} // namespace

//////////////////////////////////////////////////////////////////////////
// InstanceCache
//////////////////////////////////////////////////////////////////////////

namespace
{

class Instance
{

	public :

		Instance( const SharedCObjectPtr object, const SharedCMeshPtr mesh, const SharedCParticleSystemPtr particleSystem = nullptr )
			:	m_object( object ), m_mesh( mesh ), m_particleSystem( particleSystem )
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

		ccl::ParticleSystem *particleSystem()
		{
			return m_particleSystem.get();
		}

	private :

		SharedCObjectPtr m_object;
		SharedCMeshPtr m_mesh;
		SharedCParticleSystemPtr m_particleSystem;

};

class InstanceCache : public IECore::RefCounted
{

	public :

		InstanceCache( ccl::Scene *scene, ParticleSystemsCachePtr particleSystemsCache )
			: m_scene( scene ), m_particleSystemsCache( particleSystemsCache )
		{
		}

		void update( ccl::Scene *scene )
		{
			m_scene = scene;
			updateObjects();
			updateMeshes();
		}

		// Can be called concurrently with other get() calls.
		Instance get( const IECore::Object *object, const IECoreScenePreview::Renderer::AttributesInterface *attributes, const std::string &nodeName )
		{
			const CyclesAttributes *cyclesAttributes = static_cast<const CyclesAttributes *>( attributes );

			ccl::Object *cobject = nullptr;

			if( const IECoreScene::PointsPrimitive *points = IECore::runTimeCast<const IECoreScene::PointsPrimitive>( object ) )
			{
				// Hard-coded sphere for now!
				MeshPrimitivePtr sphere = MeshPrimitive::createSphere( 1.0f, -1.0f, 1.0f, 360.0f, V2i( 12, 24 ) );
				cobject = ObjectAlgo::convert( sphere.get(), nodeName );
				SharedCParticleSystemPtr cpsysPtr = SharedCParticleSystemPtr( m_particleSystemsCache->get( points ) );
				SharedCObjectPtr cobjectPtr = SharedCObjectPtr( cobject );
				SharedCMeshPtr cmeshPtr = SharedCMeshPtr( cobject->mesh );
				cobject->particle_system = cpsysPtr.get();
				// Push-back to vector needs thread locking.
				{
					tbb::spin_mutex::scoped_lock lock( m_objectsMutex );
					m_objects.push_back( cobjectPtr );
					m_uniqueMeshes.push_back( cmeshPtr );
				}
				return Instance( cobjectPtr, cmeshPtr, cpsysPtr );
			}

			if( !cyclesAttributes->canInstanceGeometry( object ) )
			{
				cobject = ObjectAlgo::convert( object, nodeName, m_scene );
				cobject->random_id = (unsigned)IECore::hash_value( object->hash() );
				SharedCObjectPtr cobjectPtr = SharedCObjectPtr( cobject );
				SharedCMeshPtr cmeshPtr = SharedCMeshPtr( cobject->mesh );
				// Push-back to vector needs thread locking.
				{
					tbb::spin_mutex::scoped_lock lock( m_objectsMutex );
					m_objects.push_back( cobjectPtr );
					m_uniqueMeshes.push_back( cmeshPtr );
				}
				return Instance( cobjectPtr, cmeshPtr );
			}

			IECore::MurmurHash hash = object->hash();
			cyclesAttributes->hashGeometry( object, hash );

			Cache::accessor a;
			m_instancedMeshes.insert( a, hash );

			if( !a->second )
			{
				cobject = ObjectAlgo::convert( object, "instance:" + hash.toString(), m_scene );
				cobject->random_id = (unsigned)IECore::hash_value( hash );
				a->second = SharedCMeshPtr( cobject->mesh );
			}
			else
			{
				// For the random_id value
				IECore::MurmurHash instanceHash = hash;
				instanceHash.append( nodeName );
				cobject = new ccl::Object();
				cobject->random_id = (unsigned)IECore::hash_value( instanceHash );
				cobject->mesh = a->second.get();
				string instanceName = "instance:" + hash.toString();
				cobject->name = ccl::ustring( instanceName.c_str() );
			}

			// Set particle system to mesh
			SharedCParticleSystemPtr cparticleSysPtr = SharedCParticleSystemPtr( m_particleSystemsCache->get( hash ) );
			cobject->particle_system = cparticleSysPtr.get();
			cobject->particle_index = cparticleSysPtr.get()->particles.size() - 1;

			SharedCObjectPtr cobjectPtr = SharedCObjectPtr( cobject );
			// Push-back to vector needs thread locking.
			{
				tbb::spin_mutex::scoped_lock lock( m_objectsMutex );
				m_objects.push_back( cobjectPtr );
			}

			return Instance( cobjectPtr, a->second, cparticleSysPtr );
		}

		// Can be called concurrently with other get() calls.
		Instance get( const std::vector<const IECore::Object *> &samples, const std::vector<float> &times, const IECoreScenePreview::Renderer::AttributesInterface *attributes, const std::string &nodeName )
		{
			const CyclesAttributes *cyclesAttributes = static_cast<const CyclesAttributes *>( attributes );

			ccl::Object *cobject = nullptr;

			if( const IECoreScene::PointsPrimitive *points = IECore::runTimeCast<const IECoreScene::PointsPrimitive>( samples.front() ) )
			{
				MeshPrimitivePtr sphere = MeshPrimitive::createSphere( 1.0f, -1.0f, 1.0f, 360.0f, V2i( 12, 24 ) );
				cobject = ObjectAlgo::convert( sphere.get(), nodeName );
				SharedCParticleSystemPtr cpsysPtr = SharedCParticleSystemPtr( m_particleSystemsCache->get( points ) );
				SharedCObjectPtr cobjectPtr = SharedCObjectPtr( cobject );
				SharedCMeshPtr cmeshPtr = SharedCMeshPtr( cobject->mesh );
				cobject->particle_system = cpsysPtr.get();
				// Push-back to vector needs thread locking.
				{
					tbb::spin_mutex::scoped_lock lock( m_objectsMutex );
					m_objects.push_back( cobjectPtr );
					m_uniqueMeshes.push_back( cmeshPtr );
				}
				return Instance( cobjectPtr, cmeshPtr, cpsysPtr );
			}

			if( !cyclesAttributes->canInstanceGeometry( samples.front() ) )
			{
				cobject = ObjectAlgo::convert( samples, nodeName, m_scene );
				cobject->random_id = (unsigned)IECore::hash_value( samples.front()->hash() );
				SharedCObjectPtr cobjectPtr = SharedCObjectPtr( cobject );
				SharedCMeshPtr cmeshPtr = SharedCMeshPtr( cobject->mesh );
				// Push-back to vector needs thread locking.
				{
					tbb::spin_mutex::scoped_lock lock( m_objectsMutex );
					m_objects.push_back( cobjectPtr );
					m_uniqueMeshes.push_back( cmeshPtr );
				}
				return Instance( cobjectPtr, cmeshPtr );
			}

			IECore::MurmurHash hash;
			for( std::vector<const IECore::Object *>::const_iterator it = samples.begin(), eIt = samples.end(); it != eIt; ++it )
			{
				(*it)->hash( hash );
			}
			for( std::vector<float>::const_iterator it = times.begin(), eIt = times.end(); it != eIt; ++it )
			{
				hash.append( *it );
			}
			cyclesAttributes->hashGeometry( samples.front(), hash );

			Cache::accessor a;
			m_instancedMeshes.insert( a, hash );

			if( !a->second )
			{
				cobject = ObjectAlgo::convert( samples, "instance:" + hash.toString(), m_scene );
				cobject->random_id = (unsigned)IECore::hash_value( hash );
				a->second = SharedCMeshPtr( cobject->mesh );
			}
			else
			{
				// For the random_id value
				IECore::MurmurHash instanceHash = hash;
				instanceHash.append( nodeName );
				cobject = new ccl::Object();
				cobject->random_id = (unsigned)IECore::hash_value( instanceHash );
				cobject->mesh = a->second.get();
				string instanceName = "instance:" + hash.toString();
				cobject->name = ccl::ustring( instanceName.c_str() );
			}

			// Set particle system to mesh
			SharedCParticleSystemPtr cparticleSysPtr = SharedCParticleSystemPtr( m_particleSystemsCache->get( hash ) );
			cobject->particle_system = cparticleSysPtr.get();
			cobject->particle_index = cparticleSysPtr.get()->particles.size() - 1;

			SharedCObjectPtr cobjectPtr = SharedCObjectPtr( cobject );
			// Push-back to vector needs thread locking.
			{
				tbb::spin_mutex::scoped_lock lock( m_objectsMutex );
				m_objects.push_back( cobjectPtr );
			}

			return Instance( cobjectPtr, a->second, cparticleSysPtr );
		}

		// Must not be called concurrently with anything.
		void clearUnused()
		{
			// Unique meshes
			vector<SharedCMeshPtr> meshesKeep;
			for( vector<SharedCMeshPtr>::const_iterator it = m_uniqueMeshes.begin(), eIt = m_uniqueMeshes.end(); it != eIt; ++it )
			{
				if( !it->unique() )
				{
					meshesKeep.push_back( *it );
				}
			}

			// Instanced meshes
			vector<IECore::MurmurHash> toErase;
			for( Cache::iterator it = m_instancedMeshes.begin(), eIt = m_instancedMeshes.end(); it != eIt; ++it )
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
				m_instancedMeshes.erase( *it );
			}

			if( toErase.size() || meshesKeep.size() )
			{
				m_uniqueMeshes = meshesKeep;
				updateMeshes();
			}

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

		void updateDicingCamera( ccl::Camera *camera )
		{
			auto &meshes = m_scene->meshes;
			for( ccl::Mesh *mesh : meshes )
			{
				if( mesh->subd_params )
				{
					mesh->subd_params->camera = camera;
				}
			}
			m_scene->mesh_manager->tag_update( m_scene );
		}

		void clearMissingShaders()
		{
			// Make sure there are no nullptrs in used_shaders
			for( ccl::Mesh *mesh : m_scene->meshes )
			{
				for( ccl::Shader *shader : mesh->used_shaders )
				{
					if( shader == nullptr )
					{
						shader = m_scene->default_surface;
					}
				}
			}
		}

	private :

		void updateObjects()
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

		void updateMeshes()
		{
			auto &meshes = m_scene->meshes;
			meshes.clear();

			// Unique meshes
			for( vector<SharedCMeshPtr>::const_iterator it = m_uniqueMeshes.begin(), eIt = m_uniqueMeshes.end(); it != eIt; ++it )
			{
				if( it->get() )
				{
					meshes.push_back( it->get() );
				}
			}

			// Instanced meshes
			for( Cache::const_iterator it = m_instancedMeshes.begin(), eIt = m_instancedMeshes.end(); it != eIt; ++it )
			{
				if( it->second )
				{
					meshes.push_back( it->second.get() );
				}
			}
			clearMissingShaders();
			m_scene->mesh_manager->tag_update( m_scene );
		}

		ccl::Scene *m_scene;
		vector<SharedCObjectPtr> m_objects;
		vector<SharedCMeshPtr> m_uniqueMeshes;
		typedef tbb::concurrent_hash_map<IECore::MurmurHash, SharedCMeshPtr> Cache;
		Cache m_instancedMeshes;
		ParticleSystemsCachePtr m_particleSystemsCache;
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

		~CyclesObject() override
		{
		}

		void link( const IECore::InternedString &type, const IECoreScenePreview::Renderer::ConstObjectSetPtr &objects ) override
		{
		}

		void transform( const Imath::M44f &transform ) override
		{
			ccl::Object *object = m_instance.object();
			if( !object )
				return;
			object->tfm = SocketAlgo::setTransform( transform );
			if( object->mesh->subd_params )
			{
				object->mesh->subd_params->objecttoworld = object->tfm;
			}
		}

		void transform( const std::vector<Imath::M44f> &samples, const std::vector<float> &times ) override
		{
			ccl::Object *object = m_instance.object();
			if( !object )
				return;
			const size_t numSamples = samples.size();
			object->tfm = SocketAlgo::setTransform( samples.front() );
			object->motion = ccl::array<ccl::Transform>( numSamples );
			for( size_t i = 0; i < numSamples; ++i )
				object->motion[i] = SocketAlgo::setTransform( samples[i] );
			if( object->mesh->subd_params )
			{
				object->mesh->subd_params->objecttoworld = object->tfm;
			}
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

		~CyclesLight() override
		{
		}

		void link( const IECore::InternedString &type, const IECoreScenePreview::Renderer::ConstObjectSetPtr &objects ) override
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
			//Imath::Vec3<float> scale = Imath::Vec3<float>( 1.0f );
			//Imath::extractScaling( transform, scale, false );
			//light->sizeu = scale.x;
			//light->sizev = scale.y;
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
			//Imath::Vec3<float> scale = Imath::Vec3<float>( 1.0f );
			//Imath::extractScaling( samples[0], scale, false );
			//light->sizeu = scale.x;
			//light->sizev = scale.y;
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

		~CyclesCamera() override
		{
		}

		void link( const IECore::InternedString &type, const IECoreScenePreview::Renderer::ConstObjectSetPtr &objects ) override
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
// Logging
IECore::InternedString g_logLevelOptionName( "ccl:log_level" );
IECore::InternedString g_progressLevelOptionName( "ccl:progress_level" );
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
IECore::InternedString g_runDenoisingOptionName( "ccl:session:run_denoising" );
IECore::InternedString g_writeDenoisingPassesOptionName( "ccl:session:write_denoising_passes" );
IECore::InternedString g_fullDenoisingOptionName( "ccl:session:full_denoising" );
IECore::InternedString g_cancelTimeoutOptionName( "ccl:session:cancel_timeout" );
IECore::InternedString g_resetTimeoutOptionName( "ccl:session:reset_timeout" );
IECore::InternedString g_textTimeoutOptionName( "ccl:session:text_timeout" );
IECore::InternedString g_progressiveUpdateTimeoutOptionName( "ccl:session:progressive_update_timeout" );
#ifdef WITH_CYCLES_ADAPTIVE_SAMPLING
IECore::InternedString g_adaptiveSamplingOptionName( "ccl:session:adaptive_sampling" );
#endif
// Scene
IECore::InternedString g_bvhTypeOptionName( "ccl:scene:bvh_type" );
IECore::InternedString g_bvhLayoutOptionName( "ccl:scene:bvh_layout" );
IECore::InternedString g_useBvhSpatialSplitOptionName( "ccl:scene:use_bvh_spatial_split" );
IECore::InternedString g_useBvhUnalignedNodesOptionName( "ccl:scene:use_bvh_unaligned_nodes" );
IECore::InternedString g_numBvhTimeStepsOptionName( "ccl:scene:num_bvh_time_steps" );
IECore::InternedString g_persistentDataOptionName( "ccl:scene:persistent_data" );
IECore::InternedString g_textureLimitOptionName( "ccl:scene:texture_limit" );
// Denoise
IECore::InternedString g_denoiseRadiusOptionName( "ccl:denoise:radius" );
IECore::InternedString g_denoiseStrengthOptionName( "ccl:denoise:strength" );
IECore::InternedString g_denoiseFeatureStrengthOptionName( "ccl:denoise:feature_strength" );
IECore::InternedString g_denoiseRelativePcaOptionName( "ccl:denoise:relative_pca" );
IECore::InternedString g_denoiseNeighborFramesOptionName( "ccl:denoise:neighbor_frames" );
IECore::InternedString g_denoiseClampInputOptionName( "ccl:denoise:clampInput" );
// Curves
IECore::InternedString g_curvePrimitiveOptionType( "ccl:curve:primitive" );
IECore::InternedString g_curveShapeOptionType( "ccl:curve:shape" );
IECore::InternedString g_curveLineMethod( "ccl:curve:line_method" );
IECore::InternedString g_curveTriangleMethod( "ccl:curve:triangle_method" );
IECore::InternedString g_curveResolutionOptionType( "ccl:curve:resolution" );
IECore::InternedString g_curveSubdivisionsOptionType( "ccl:curve:subdivisions" );
IECore::InternedString g_useCurvesOptionType( "ccl:curve:use_curves" );
IECore::InternedString g_useEncasingOptionType( "ccl:curve:use_encasing" );
IECore::InternedString g_curveUseBackfacing( "ccl:curve:use_backfacing" );
IECore::InternedString g_useTangentNormalGeoOptionType( "ccl:curve:use_tangent_normal_geometry" );
// Background shader
IECore::InternedString g_backgroundShaderOptionName( "ccl:background:shader" );

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
// Dicing camera
IECore::InternedString g_dicingCameraOptionName( "ccl::dicing_camera" );

// Texture cache
IECore::InternedString g_useTextureCacheOptionName( "ccl:texture:use_texture_cache" );
IECore::InternedString g_textureCacheSizeOptionName( "ccl:texture:cache_size" );
IECore::InternedString g_textureAutoConvertOptionName( "ccl:texture:auto_convert" );
IECore::InternedString g_textureAcceptUnmippedOptionName( "ccl:texture:accept_unmipped" );
IECore::InternedString g_textureAcceptUntiledOptionName( "ccl:texture:accept_untiled" );
IECore::InternedString g_textureAutoTileOptionName( "ccl:texture:auto_tile" );
IECore::InternedString g_textureAutoMipOptionName( "ccl:texture:auto_mip" );
IECore::InternedString g_textureTileSizeOptionName( "ccl:texture:tile_size" );
IECore::InternedString g_textureBlurDiffuseOptionName( "ccl:texture:blur_diffuse" );
IECore::InternedString g_textureBlurGlossyOptionName( "ccl:texture:blur_glossy" );
IECore::InternedString g_textureUseCustomCachePathOptionName( "ccl:texture:use_custom_cache_path" );
IECore::InternedString g_textureCustomCachePathOptionName( "ccl:texture:custom_cache_path" );

IE_CORE_FORWARDDECLARE( CyclesRenderer )

class CyclesRenderer final : public IECoreScenePreview::Renderer
{

	public :

		CyclesRenderer( RenderType renderType, const std::string &fileName )
			:	m_renderType( renderType ),
				m_sessionParams( ccl::SessionParams() ),
				m_sceneParams( ccl::SceneParams() ),
				m_bufferParams( ccl::BufferParams() ),
				m_denoiseParams( ccl::DenoiseParams() ),
				m_textureCacheParams( ccl::TextureCacheParams() ),
				m_deviceName( "CPU" ),
				m_shadingsystemName( "SVM" ),
				m_session( nullptr ),
				m_scene( nullptr ),
				m_renderCallback( nullptr ),
				m_rendering( false ),
				m_deviceDirty( false ),
				m_pause( false ),
				m_progressLevel( IECore::Msg::Info )
		{
			// Set path to find shaders
			#ifdef _WIN32
			string paths = boost::str( boost::format( "%s;%s\\\\cycles;%s" ) % getenv( "GAFFERCYCLES" ) %  getenv( "GAFFER_ROOT" ) % getenv( "GAFFER_EXTENSION_PATHS" ) );
			#else
			string paths = boost::str( boost::format( "%s:%s/cycles:%s" ) % getenv( "GAFFERCYCLES" ) % getenv( "GAFFER_ROOT" ) % getenv( "GAFFER_EXTENSION_PATHS" ) );
			#endif
			const char *kernelFile = "source/kernel/kernel_globals.h";
			SearchPath searchPath( paths );
			boost::filesystem::path path = searchPath.find( kernelFile );
			if( path.empty() )
			{
				IECore::msg( IECore::Msg::Error, "CyclesRenderer", "Cannot find GafferCycles location. Have you set the GAFFERCYCLES environment variable?" );
			}
			else
			{
				string cclPath = path.string();
				cclPath.erase( cclPath.end() - strlen( kernelFile ), cclPath.end() );
				ccl::path_init( cclPath );
			}
			// Define internal device names
			getCyclesDevices();
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
				m_sessionParams.progressive = false;
				m_sessionParams.progressive_refine = false;
				m_sceneParams.bvh_type = ccl::SceneParams::BVH_STATIC;
			}
			else
			{
				m_sessionParams.progressive = true;
				m_sessionParams.progressive_refine = true;
				m_sceneParams.bvh_type = ccl::SceneParams::BVH_DYNAMIC;
			}

			// The interactive renderer also runs in the background. Having
			// this off makes more sense if we were to use Cycles as a
			// viewport alternative to the OpenGL viewer.
			// TODO: Cycles will disable background mode when a GPU device is 
			// used.
			// Unfortunately it means it renders black in preview as it wants
			// to render to a GL buffer and not to CPU.
			m_sessionParams.background = true;
			// We almost-always want persistent data.
			m_sceneParams.persistent_data = true;

			m_sessionParamsDefault = m_sessionParams;
			m_sceneParamsDefault = m_sceneParams;
			m_denoiseParamsDefault = m_denoiseParams;
			m_textureCacheParamsDefault = m_textureCacheParams;

			m_renderCallback = new RenderCallback( ( m_renderType == Interactive ) ? true : false );

#ifdef WITH_CYCLES_OPENVDB
			// OpenVDB
			ccl::openvdb_initialize();
			m_sceneParams.intialized_openvdb = true;
#endif

			init();
			// Maintain our own ImageManager
			m_imageManager = new ccl::ImageManager( m_session->device->info );
			m_imageManagerOld = m_scene->image_manager;
			m_scene->image_manager = m_imageManager;

			// CyclesOptions will set some values to these.
			m_integrator = *(m_scene->integrator);
			m_background = *(m_scene->background);
			m_scene->background->transparent = true;
			m_film = *(m_scene->film);
			m_curveSystemManager = *(m_scene->curve_system_manager);

			m_cameraCache = new CameraCache();
			m_lightCache = new LightCache( m_scene );
			m_shaderCache = new ShaderCache( m_scene );
			m_particleSystemsCache = new ParticleSystemsCache( m_scene );
			m_instanceCache = new InstanceCache( m_scene, m_particleSystemsCache );
			m_attributesCache = new AttributesCache( m_shaderCache );

		}

		~CyclesRenderer() override
		{
			m_session->set_pause( true );
			m_scene->mutex.lock();
			// Reduce the refcount so that it gets cleared.
			m_backgroundShader = nullptr;
			m_cameraCache.reset();
			m_lightCache.reset();
			m_shaderCache.reset();
			m_instanceCache.reset();
			m_attributesCache.reset();
			m_particleSystemsCache.reset();
			// Gaffer has already deleted these, so we can't double-delete
			m_scene->shaders.clear();
			m_scene->meshes.clear();
			m_scene->objects.clear();
			m_scene->lights.clear();
			m_scene->particle_systems.clear();
			// Cycles created the defaultCamera, so we give it back for it to delete.
			m_scene->camera = m_defaultCamera;
			m_scene->mutex.unlock();

			delete m_session;
			delete m_imageManagerOld;
		}

		IECore::InternedString name() const override
		{
			return "Cycles";
		}

		void option( const IECore::InternedString &name, const IECore::Object *value ) override
		{
			#define OPTION_BOOL(CATEGORY, OPTIONNAME, OPTION) if( name == OPTIONNAME ) { \
				if( value == nullptr ) { \
					CATEGORY.OPTION = CATEGORY ## Default.OPTION; \
					return; } \
				if ( const BoolData *data = reportedCast<const BoolData>( value, "option", name ) ) { \
					CATEGORY.OPTION = data->readable(); } \
				return; }
			#define OPTION_FLOAT(CATEGORY, OPTIONNAME, OPTION) if( name == OPTIONNAME ) { \
				if( value == nullptr ) { \
					CATEGORY.OPTION = CATEGORY ## Default.OPTION; \
					return; } \
				if ( const FloatData *data = reportedCast<const FloatData>( value, "option", name ) ) { \
					CATEGORY.OPTION = data->readable(); } \
				return; }
			#define OPTION_INT(CATEGORY, OPTIONNAME, OPTION) if( name == OPTIONNAME ) { \
				if( value == nullptr ) { \
					CATEGORY.OPTION = CATEGORY ## Default.OPTION; \
					return; } \
				if ( const IntData *data = reportedCast<const IntData>( value, "option", name ) ) { \
					CATEGORY.OPTION = data->readable(); } \
				return; }
			#define OPTION_INT_C(CATEGORY, OPTIONNAME, OPTION, CAST) if( name == OPTIONNAME ) { \
				if( value == nullptr ) { \
					CATEGORY.OPTION = CATEGORY ## Default.OPTION; \
					return; } \
				if ( const IntData *data = reportedCast<const IntData>( value, "option", name ) ) { \
					CATEGORY.OPTION = (CAST)data->readable(); } \
				return; }
			#define OPTION_V2I(CATEGORY, OPTIONNAME, OPTION) if( name == OPTIONNAME ) { \
				if( value == nullptr ) { \
					CATEGORY.OPTION = CATEGORY ## Default.OPTION; \
					return; } \
				if ( const V2iData *data = reportedCast<const V2iData>( value, "option", name ) ) { \
					auto d = data->readable(); \
					CATEGORY.OPTION = ccl::make_int2( d.x, d.y ); } \
				return; }
			#define OPTION_STR(CATEGORY, OPTIONNAME, OPTION) if( name == OPTIONNAME ) { \
				if( value == nullptr ) { \
					CATEGORY.OPTION = CATEGORY ## Default.OPTION; \
					return; } \
				if ( const StringData *data = reportedCast<const StringData>( value, "option", name ) ) { \
					CATEGORY.OPTION = data->readable().c_str(); } \
				return; }

			auto *integrator = m_scene->integrator;
			auto *background = m_scene->background;
			auto *film = m_scene->film;
			auto &curveSystemManager = *(m_scene->curve_system_manager);
			auto &curveSystemManagerDefault = m_curveSystemManagerDefault;

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
			else if( name == g_dicingCameraOptionName )
			{
				if( value == nullptr )
				{
					m_dicingCamera = "";
				}
				else if( const StringData *data = reportedCast<const StringData>( value, "option", name ) )
				{
					m_dicingCamera = data->readable();
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
				if( value == nullptr )
				{
					m_deviceName = "CPU";
				}
				else if( const StringData *data = reportedCast<const StringData>( value, "option", name ) )
				{
					auto device_name = data->readable();
					m_deviceName = device_name;
				}
				else
				{
					m_deviceName = "CPU";
					IECore::msg( IECore::Msg::Warning, "CyclesRenderer::option", boost::format( "Unknown value \"%s\" for option \"%s\"." ) % m_deviceName % name.string() );
				}
				m_deviceDirty = true;
				return;
			}
			else if( name == g_threadsOptionName )
			{
				if( value == nullptr )
				{
					m_sessionParams.threads = 0;
				}
				else if ( const IntData *data = reportedCast<const IntData>( value, "option", name ) )
				{
					auto threads = data->readable();
					if( threads < 0 )
						threads = max( ccl::system_cpu_thread_count() + threads, 1);
					
					m_sessionParams.threads = threads;
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
			else if( name == g_logLevelOptionName )
			{
				if( value == nullptr )
				{
					ccl::util_logging_verbosity_set( 0 );
					return;
				}
				else
				{
					if ( const IntData *data = reportedCast<const IntData>( value, "option", name ) )
					{
						ccl::util_logging_verbosity_set( data->readable() );
					}
					return;
				}
			}
			else if( name == g_progressLevelOptionName )
			{
				if( value == nullptr )
				{
					m_progressLevel = IECore::Msg::Info;
					return;
				}
				else
				{
					if ( const IntData *data = reportedCast<const IntData>( value, "option", name ) )
					{
						m_progressLevel = (IECore::Msg::Level)data->readable();
					}
					return;
				}
			}
			else if( boost::starts_with( name.string(), "ccl:session:" ) )
			{
				OPTION_BOOL (m_sessionParams, g_featureSetOptionName,               experimental);
				OPTION_BOOL (m_sessionParams, g_progressiveRefineOptionName,        progressive_refine);
				OPTION_BOOL (m_sessionParams, g_progressiveOptionName,              progressive);
				OPTION_INT  (m_sessionParams, g_samplesOptionName,                  samples);
				OPTION_V2I  (m_sessionParams, g_tileSizeOptionName,                 tile_size);
				OPTION_INT_C(m_sessionParams, g_tileOrderOptionName,                tile_order, ccl::TileOrder);
				OPTION_INT  (m_sessionParams, g_startResolutionOptionName,          start_resolution);
				OPTION_INT  (m_sessionParams, g_pixelSizeOptionName,                pixel_size);
				OPTION_BOOL (m_sessionParams, g_displayBufferLinearOptionName,      display_buffer_linear);
				OPTION_BOOL (m_sessionParams, g_runDenoisingOptionName,             run_denoising);
				OPTION_BOOL (m_sessionParams, g_writeDenoisingPassesOptionName,     write_denoising_passes);
				OPTION_BOOL (m_sessionParams, g_fullDenoisingOptionName,            full_denoising);
				OPTION_FLOAT(m_sessionParams, g_cancelTimeoutOptionName,            cancel_timeout);
				OPTION_FLOAT(m_sessionParams, g_resetTimeoutOptionName,             reset_timeout);
				OPTION_FLOAT(m_sessionParams, g_textTimeoutOptionName,              text_timeout);
				OPTION_FLOAT(m_sessionParams, g_progressiveUpdateTimeoutOptionName, progressive_update_timeout);
#ifdef WITH_CYCLES_ADAPTIVE_SAMPLING
				if( name == g_adaptiveSamplingOptionName )
				{
					if( value == nullptr )
					{
						m_sessionParams.adaptive_sampling = false;
						m_film.use_adaptive_sampling = false;
						return;
					}
					if ( const BoolData *data = reportedCast<const BoolData>( value, "option", name ) )
					{
						m_sessionParams.adaptive_sampling = data->readable();
						m_film.use_adaptive_sampling = data->readable();
						return;
					}
				}
#endif

				IECore::msg( IECore::Msg::Warning, "CyclesRenderer::option", boost::format( "Unknown option \"%s\"." ) % name.string() );
				return;
			}
			else if( boost::starts_with( name.string(), "ccl:scene:" ) )
			{
				OPTION_INT_C(m_sceneParams, g_bvhTypeOptionName,              bvh_type, ccl::SceneParams::BVHType);
				OPTION_INT_C(m_sceneParams, g_bvhLayoutOptionName,            bvh_layout, ccl::BVHLayout);
				OPTION_BOOL (m_sceneParams, g_useBvhSpatialSplitOptionName,   use_bvh_spatial_split);
				OPTION_BOOL (m_sceneParams, g_useBvhUnalignedNodesOptionName, use_bvh_unaligned_nodes);
				OPTION_INT  (m_sceneParams, g_numBvhTimeStepsOptionName,      num_bvh_time_steps);
				OPTION_BOOL (m_sceneParams, g_persistentDataOptionName,       persistent_data);
				OPTION_INT  (m_sceneParams, g_textureLimitOptionName,         texture_limit);

				IECore::msg( IECore::Msg::Warning, "CyclesRenderer::option", boost::format( "Unknown option \"%s\"." ) % name.string() );
				return;
			}
			else if( boost::starts_with( name.string(), "ccl:denoise:" ) )
			{
				OPTION_INT  (m_denoiseParams, g_denoiseRadiusOptionName,          radius);
				OPTION_FLOAT(m_denoiseParams, g_denoiseStrengthOptionName,        strength);
				OPTION_FLOAT(m_denoiseParams, g_denoiseFeatureStrengthOptionName, feature_strength);
				OPTION_BOOL (m_denoiseParams, g_denoiseRelativePcaOptionName,     relative_pca);
				OPTION_INT  (m_denoiseParams, g_denoiseNeighborFramesOptionName,  neighbor_frames);
				OPTION_BOOL (m_denoiseParams, g_denoiseClampInputOptionName,      clamp_input);

				IECore::msg( IECore::Msg::Warning, "CyclesRenderer::option", boost::format( "Unknown option \"%s\"." ) % name.string() );
				return;
			}
			else if( boost::starts_with( name.string(), "ccl:curve:" ) )
			{
				OPTION_INT_C(curveSystemManager, g_curvePrimitiveOptionType,    primitive, ccl::CurvePrimitiveType);
				OPTION_INT_C(curveSystemManager, g_curveShapeOptionType,        curve_shape, ccl::CurveShapeType);
				OPTION_INT_C(curveSystemManager, g_curveLineMethod,             line_method, ccl::CurveLineMethod);
				OPTION_INT_C(curveSystemManager, g_curveTriangleMethod,         triangle_method, ccl::CurveTriangleMethod);
				OPTION_INT  (curveSystemManager, g_curveResolutionOptionType,   resolution);
				OPTION_INT  (curveSystemManager, g_curveSubdivisionsOptionType, subdivisions);

				OPTION_BOOL (curveSystemManager, g_useCurvesOptionType,           use_curves);
				OPTION_BOOL (curveSystemManager, g_useEncasingOptionType,         use_encasing);
				OPTION_BOOL (curveSystemManager, g_curveUseBackfacing,            use_backfacing);
				OPTION_BOOL (curveSystemManager, g_useTangentNormalGeoOptionType, use_tangent_normal_geometry);

				IECore::msg( IECore::Msg::Warning, "CyclesRenderer::option", boost::format( "Unknown option \"%s\"." ) % name.string() );
				return;
			}
			else if( boost::starts_with( name.string(), "ccl:texture:" ) )
			{
#ifdef WITH_CYCLES_TEXTURE_CACHE
				OPTION_BOOL (m_textureCacheParams, g_useTextureCacheOptionName,           use_cache );
				OPTION_INT  (m_textureCacheParams, g_textureCacheSizeOptionName,          cache_size );
				OPTION_BOOL (m_textureCacheParams, g_textureAutoConvertOptionName,        auto_convert );
				OPTION_BOOL (m_textureCacheParams, g_textureAcceptUnmippedOptionName,     accept_unmipped );
				OPTION_BOOL (m_textureCacheParams, g_textureAcceptUntiledOptionName,      accept_untiled );
				OPTION_BOOL (m_textureCacheParams, g_textureAutoTileOptionName,           auto_tile );
				OPTION_BOOL (m_textureCacheParams, g_textureAutoMipOptionName,            auto_mip );
				OPTION_INT  (m_textureCacheParams, g_textureTileSizeOptionName,           tile_size );
				OPTION_FLOAT(m_textureCacheParams, g_textureBlurDiffuseOptionName,        diffuse_blur );
				OPTION_FLOAT(m_textureCacheParams, g_textureBlurGlossyOptionName,         glossy_blur );
				OPTION_BOOL (m_textureCacheParams, g_textureUseCustomCachePathOptionName, use_custom_cache_path );
				OPTION_STR  (m_textureCacheParams, g_textureCustomCachePathOptionName,    custom_cache_path );
#endif

				IECore::msg( IECore::Msg::Warning, "CyclesRenderer::option", boost::format( "Unknown option \"%s\"." ) % name.string() );
				return;
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
							m_backgroundShader = m_shaderCache->get( d, nullptr );
							background->shader = m_backgroundShader.get();
						}
						else
						{
							background->shader = nullptr;
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
			else if( boost::starts_with( name.string(), "ccl:multidevice:" ) )
			{
				string deviceName = name.string().c_str() + 16;
				if( value == nullptr )
				{
					for( ccl::DeviceInfo& device : m_multiDevices )
					{
						if( m_deviceMap[deviceName].id == device.id )
						{
							m_multiDevices.erase( std::remove( m_multiDevices.begin(), m_multiDevices.end(), device ) );
							return;
						}
					}
					return;
				}
				if( const BoolData *data = reportedCast<const BoolData>( value, "option", name ) )
				{
					ccl::vector<ccl::DeviceInfo> devices = ccl::Device::available_devices( ccl::DEVICE_MASK_CPU | ccl::DEVICE_MASK_OPENCL | ccl::DEVICE_MASK_CUDA );
					for( ccl::DeviceInfo& device : devices ) 
					{
						if( m_deviceMap[deviceName].id == device.id ) 
						{
							for( ccl::DeviceInfo& existingDevice : m_multiDevices )
							{
								if( m_deviceMap[deviceName].id == existingDevice.id )
								{
									if( !data->readable() )
									{
										m_multiDevices.erase( std::remove( m_multiDevices.begin(), m_multiDevices.end(), existingDevice ) );
										return;
									}
									else
									{
										return;
									}
								}
							}
							if( data->readable() )
							{
								m_multiDevices.push_back( device );
							}
							return;
						}
					}
				}
				IECore::msg( IECore::Msg::Warning, "CyclesRenderer::option", boost::format( "Unknown device \"%s\"." ) % deviceName );
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
			#undef OPTION_BOOL
			#undef OPTION_FLOAT
			#undef OPTION_INT
			#undef OPTION_INT_C
			#undef OPTION_V2I
			#undef OPTION_STR
		}

		void output( const IECore::InternedString &name, const Output *output ) override
		{
			ccl::Film *film = m_scene->film;

			if( !output )
			{
				// Remove output pass
				const auto coutput = m_outputs.find( name );
				if( coutput != m_outputs.end() )
				{
					auto *o = coutput->second.get();
					auto passType = nameToPassType( o->m_data );
					if( passType == ccl::PASS_CRYPTOMATTE )
					{
						if( o->m_name == "cryptomatte_asset" )
						{
							film->cryptomatte_passes = (ccl::CryptomatteType)(film->cryptomatte_passes & ~(ccl::CRYPT_ASSET) );
						}
						else if( o->m_name == "cryptomatte_object" )
						{
							film->cryptomatte_passes = (ccl::CryptomatteType)(film->cryptomatte_passes & ~(ccl::CRYPT_OBJECT) );
						}
						else if( o->m_name == "cryptomatte_material" )
						{
							film->cryptomatte_passes =  (ccl::CryptomatteType)(film->cryptomatte_passes & ~(ccl::CRYPT_MATERIAL) );
						}
					}
					m_outputs.erase( name );
				}
				else
				{
					return;
				}
			}
			else if( nameToPassType( output->getData() ) == ccl::PASS_NONE )
			{
				// Add denoise output pass
				int denoiseOffset = nameToDenoisePassType( output->getData() );
				if( denoiseOffset > 0 )
				{
					m_outputs[name] = new CyclesOutput( output );
				}
				else
				{
					return;
				}
			}
			else
			{
				auto passType = nameToPassType( output->getData() );
				// Add output pass
				if( passType == ccl::PASS_CRYPTOMATTE )
				{
					const auto coutput = m_outputs.find( name );
					if( coutput == m_outputs.end() )
					{
						m_outputs[name] = new CyclesOutput( output );
					}
				}
				else if( !ccl::Pass::contains( film->passes, passType ) )
				{
					m_outputs[name] = new CyclesOutput( output );
				}
				else
				{
					return;
				}
			}
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

		ObjectInterfacePtr lightFilter( const std::string &name, const IECore::Object *object, const AttributesInterface *attributes ) override
		{
			IECore::msg( IECore::Msg::Warning, "CyclesRenderer", "lightFilter() unimplemented" );
			return nullptr;
		}

		ObjectInterfacePtr object( const std::string &name, const IECore::Object *object, const AttributesInterface *attributes ) override
		{
			if( ( object->typeId() == IECoreScene::Camera::staticTypeId() ) || ( object->typeId() == IECoreScene::PointsPrimitive::staticTypeId() ) ) // temporary for PointsPrimitive
			{
				return nullptr;
			}
			Instance instance = m_instanceCache->get( object, attributes, name );

			ObjectInterfacePtr result = new CyclesObject( instance );
			result->attributes( attributes );
			return result;
		}

		ObjectInterfacePtr object( const std::string &name, const std::vector<const IECore::Object *> &samples, const std::vector<float> &times, const AttributesInterface *attributes ) override
		{
			if( ( samples.front()->typeId() == IECoreScene::Camera::staticTypeId() ) || ( samples.front()->typeId() == IECoreScene::PointsPrimitive::staticTypeId() ) ) // temporary for PointsPrimitive
			{
				return nullptr;
			}
			Instance instance = m_instanceCache->get( samples, times, attributes, name );

			ObjectInterfacePtr result = new CyclesObject( instance );
			result->attributes( attributes );
			return result;
		}

		void render() override
		{
			m_session->set_pause( true );
			updateSceneObjects();
			updateOptions();
			// Clear out any objects which aren't needed in the cache.
			if( m_renderType == Interactive )
			{
				m_scene->mutex.lock();
				m_cameraCache->clearUnused();
				m_instanceCache->clearUnused();
				m_particleSystemsCache->clearUnused();
				m_lightCache->clearUnused();
				m_attributesCache->clearUnused();
				// Clear out any nullptr shaders so we don't crash
				m_instanceCache->clearMissingShaders();
				m_scene->mutex.unlock();
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
			m_pause = !m_pause;
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

			// Fallback
			ccl::DeviceType device_type_fallback = ccl::DEVICE_CPU;
			ccl::DeviceInfo device_fallback;

			ccl::vector<ccl::DeviceInfo> devices = ccl::Device::available_devices( ccl::DEVICE_MASK_CPU | ccl::DEVICE_MASK_OPENCL | ccl::DEVICE_MASK_CUDA 
#ifdef WITH_OPTIX
			| ccl::DEVICE_MASK_OPTIX 
#endif
			);
			bool device_available = false;
			for( ccl::DeviceInfo& device : devices ) 
			{
				if( device_type_fallback == device.type )
				{
					device_fallback = device;
					break;
				}
			}

			if( m_deviceName == "MULTI" )
			{
				if( m_sessionParams.progressive )
				{
					IECore::msg( IECore::Msg::Warning, "CyclesRenderer", "Multi-device is only compatible with Branched Path mode and progressive refine disabled, reverting to CPU." );
					device_available = false;
				}
				else
				{
					ccl::DeviceInfo multidevice = ccl::Device::get_multi_device( m_multiDevices, m_sessionParams.threads, m_sessionParams.background );
					m_sessionParams.device = multidevice;
					device_available = true;
				}
			}
			else
			{
				for( ccl::DeviceInfo& device : devices ) 
				{
					if( m_deviceName ==  device.id ) 
					{
						m_sessionParams.device = device;
						device_available = true;
						break;
					}
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
			m_session->scene = m_scene;

			m_renderCallback->updateSession( m_session );

			// Grab the default camera from cycles.
			m_defaultCamera = m_scene->camera;

			m_scene->camera->need_update = true;
			m_scene->camera->update( m_scene );

			// Set a more sane default than the arbitrary 0.8f
			m_scene->film->exposure = 1.0f;
			m_scene->film->cryptomatte_depth = 2;
			m_scene->film->tag_update( m_scene );

			m_session->reset( m_bufferParams, m_sessionParams.samples );
		}

		void updateSceneObjects()
		{
			m_scene->mutex.lock();
			m_shaderCache->update( m_scene );
			m_lightCache->update( m_scene );
			m_particleSystemsCache->update( m_scene );
			m_instanceCache->update( m_scene );
			m_scene->mutex.unlock();
		}

		void updateOptions()
		{
			m_session->set_samples( m_sessionParams.samples );
			// No checking on denoise settings either
			m_session->params.denoising = m_denoiseParams;
			m_sessionParams.denoising = m_denoiseParams;
			m_sceneParams.texture = m_textureCacheParams;

			ccl::Integrator *integrator = m_scene->integrator;
			if( integrator->modified( m_integrator ) )
			{
				integrator->tag_update( m_scene );
				m_integrator = *integrator;
			}

			ccl::Background *background = m_scene->background;
			if( background->modified( m_background ) )
			{
				background->tag_update( m_scene );
				m_background = *background;
			}

			ccl::Film *film = m_scene->film;
			if( film->modified( m_film ) )
			{
				film->tag_update( m_scene );
				integrator->tag_update( m_scene );
				m_film = *film;
			}

			ccl::CurveSystemManager *curveSystemManager = m_scene->curve_system_manager;
			if( curveSystemManager->modified( m_curveSystemManager ) )
			{
				curveSystemManager->tag_update( m_scene );
				m_curveSystemManager = *curveSystemManager;
			}

			// If anything changes in scene or session, we reset.
			if( m_scene->params.modified( m_sceneParams ) ||
			    m_session->params.modified( m_sessionParams ) ||
				m_deviceDirty )
			{
				m_deviceDirty = false;
				reset();
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

			// Rebuild passes
			m_bufferParamsModified.passes.clear();
			for( auto &coutput : m_outputs )
			{
				if( coutput.second->m_passType == ccl::PASS_COMBINED )
				{
					ccl::Pass::add( coutput.second->m_passType, m_bufferParamsModified.passes, coutput.second->m_data.c_str() );
					break;
				}
			}
			for( auto &coutput : m_outputs )
			{
				if( coutput.second->m_passType == ccl::PASS_COMBINED )
				{
					continue;
				}
				else if( coutput.second->m_passType == ccl::PASS_CRYPTOMATTE )
				{
					string cryptoName( "Crypto" );
					if( coutput.second->m_data == "cryptomatte_asset" )
					{
						cryptoName += "Asset";
						m_scene->film->cryptomatte_passes = (ccl::CryptomatteType)( m_scene->film->cryptomatte_passes | ccl::CRYPT_ASSET );
					}
					else if( coutput.second->m_data == "cryptomatte_object" )
					{
						cryptoName += "Object";
						m_scene->film->cryptomatte_passes = (ccl::CryptomatteType)( m_scene->film->cryptomatte_passes | ccl::CRYPT_OBJECT );
					}
					else if( coutput.second->m_data == "cryptomatte_material" )
					{
						cryptoName += "Material";
						m_scene->film->cryptomatte_passes = (ccl::CryptomatteType)( m_scene->film->cryptomatte_passes | ccl::CRYPT_MATERIAL );
					}
					else
					{
						continue;
					}
					for( int i = 0; i < m_scene->film->cryptomatte_depth; ++i )
					{
						string cryptoFullName = ( boost::format( "%s%02i" ) % cryptoName % i ).str();
						ccl::Pass::add( ccl::PASS_CRYPTOMATTE, m_bufferParamsModified.passes, cryptoFullName.c_str() );
					}
					continue;
				}
				else if(
					( coutput.second->m_passType == ccl::PASS_AOV_COLOR  ) ||
					( coutput.second->m_passType == ccl::PASS_AOV_VALUE  )
				)
				{
					ccl::Pass::add( coutput.second->m_passType, m_bufferParamsModified.passes, coutput.second->m_data.c_str() );
					continue;
				}
#ifdef WITH_CYCLES_LIGHTGROUPS
				else if( coutput.second->m_passType == ccl::PASS_LIGHTGROUP )
				{
					int num = coutput.second->m_images.size();
					for( int i = 1; i <= num; ++i )
					{
						string fullName = ( boost::format( "%s%02i" ) % coutput.second->m_data % i ).str();
						ccl::Pass::add( coutput.second->m_passType, m_bufferParamsModified.passes, fullName.c_str() );
					}
					continue;
				}
#endif
				else
				{
					ccl::Pass::add( coutput.second->m_passType, m_bufferParamsModified.passes, coutput.second->m_data.c_str() );
					continue;
				}
			}

#ifdef WITH_CYCLES_ADAPTIVE_SAMPLING
			// Adaptive
			if( m_sessionParams.adaptive_sampling )
			{
				ccl::Pass::add( ccl::PASS_ADAPTIVE_AUX_BUFFER, m_bufferParamsModified.passes );
				ccl::Pass::add( ccl::PASS_SAMPLE_COUNT, m_bufferParamsModified.passes );
			}
#endif

			if( !m_bufferParams.modified( m_bufferParamsModified ) )
			{
				return;
			}
			else
			{
				m_bufferParams = m_bufferParamsModified;
				m_scene->film->tag_passes_update( m_scene, m_bufferParams.passes );
			}

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
			m_session->set_pause( true );
			m_rendering = false;
			// This is so cycles doesn't delete the objects that Gaffer manages.
			m_scene->objects.clear();
			m_scene->meshes.clear();
			m_scene->shaders.clear();
			m_scene->lights.clear();
			m_scene->particle_systems.clear();
			// Cycles created the defaultCamera, so we give it back for it to delete.
			m_scene->camera = m_defaultCamera;
			// Give back a dummy ImageManager for Cycles to "delete"
			m_scene->image_manager = m_imageManagerOld;

			init();
			// Make sure we are using our ImageManager
			m_imageManagerOld = m_scene->image_manager;
			m_scene->image_manager = m_imageManager;

			// Re-apply the settings for these.
			for( const ccl::SocketType socketType : m_scene->integrator->type->inputs )
			{
				m_scene->integrator->copy_value(socketType, m_integrator, *m_integrator.type->find_input( socketType.name ) );
			}
			for( const ccl::SocketType socketType : m_scene->background->type->inputs )
			{
				m_scene->background->copy_value(socketType, m_background, *m_background.type->find_input( socketType.name ) );
			}
			for( const ccl::SocketType socketType : m_scene->film->type->inputs )
			{
				m_scene->film->copy_value(socketType, m_film, *m_film.type->find_input( socketType.name ) );
			}
			for( ccl::vector<ccl::Pass>::const_iterator it = m_film.passes.begin(), eIt = m_film.passes.end(); it != eIt; ++it )
			{
				m_scene->film->passes.push_back( *it );
			}
			#define CURVES_SET(OPTION) m_scene->curve_system_manager->OPTION = m_curveSystemManager.OPTION;
			CURVES_SET(primitive);
			CURVES_SET(curve_shape);
			CURVES_SET(line_method);
			CURVES_SET(triangle_method);
			CURVES_SET(resolution);
			CURVES_SET(subdivisions);
			CURVES_SET(use_curves);
			CURVES_SET(use_encasing);
			CURVES_SET(use_backfacing);
			CURVES_SET(use_tangent_normal_geometry);
			#undef CURVES_SET
			m_scene->integrator->tag_update( m_scene );
			m_scene->background->tag_update( m_scene );
			m_scene->film->tag_update( m_scene );
			m_scene->curve_system_manager->tag_update( m_scene );
			m_session->reset( m_bufferParams, m_sessionParams.samples );
			
			//m_session->progress.reset();
			//m_scene->reset();
			//m_session->tile_manager.set_tile_order( m_sessionParams.tile_order );
			/* peak memory usage should show current render peak, not peak for all renders
				* made by this render session
				*/
			//m_session->stats.mem_peak = m_session->stats.mem_used;

			// Make sure the instance cache points to the right scene.
			updateSceneObjects();

			//m_session->reset( m_bufferParams, m_sessionParams.samples );
		}

		void updateCamera()
		{
			// Check that the camera we want to use exists,
			// and if not, create a default one.
			{
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

			// Dicing camera update
			{
				const auto cameraIt = m_cameras.find( m_dicingCamera );
				if( cameraIt == m_cameras.end() )
				{
					if( !m_camera.empty() && ( m_dicingCamera != "" ) )
					{
						IECore::msg(
							IECore::Msg::Warning, "CyclesRenderer",
							boost::format( "Dicing camera \"%s\" does not exist" ) % m_dicingCamera
						);
					}
					m_instanceCache->updateDicingCamera( nullptr );
				}
				else
				{
					auto ccamera = m_cameraCache->get( cameraIt->second.get(), cameraIt->first );
					m_instanceCache->updateDicingCamera( ccamera.get() );
				}
			}
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
			m_session->progress.get_status( status, substatus );

			if( substatus != "" )
				status += ": " + substatus;

			/* print status */
			IECore::msg( m_progressLevel, "CyclesRenderer", boost::format( "Progress %05.2f   %s" ) % (double)(progress * 100.0f ) % status );
		}

		void getCyclesDevices()
		{
			DeviceMap retvar;
			ccl::vector<ccl::DeviceInfo> devices = ccl::Device::available_devices( ccl::DEVICE_MASK_CPU | ccl::DEVICE_MASK_OPENCL | ccl::DEVICE_MASK_CUDA
#ifdef WITH_OPTIX
				| ccl::DEVICE_MASK_OPTIX
#endif
			);
			int indexCuda = 0;
			int indexOpenCL = 0;
			int indexOptiX = 0;
			for( const ccl::DeviceInfo &device : devices ) 
			{
				if( device.type == ccl::DEVICE_CPU )
				{
					m_deviceMap["CPU"] = device;
					continue;
				}
				string deviceName = ccl::Device::string_from_type( device.type ).c_str();
				if( device.type == ccl::DEVICE_CUDA )
				{
					auto optionName = boost::format( "%s%02i" ) % deviceName % indexCuda;
					m_deviceMap[optionName.str()] = device;
					++indexCuda;
					continue;
				}
				if( device.type == ccl::DEVICE_OPENCL )
				{
					auto optionName = boost::format( "%s%02i" ) % deviceName % indexOpenCL;
					m_deviceMap[optionName.str()] = device;
					++indexOpenCL;
					continue;
				}
#ifdef WITH_OPTIX
				if( device.type == ccl::DEVICE_OPTIX )
				{
					auto optionName = boost::format( "%s%02i" ) % deviceName % indexOptiX;
					m_deviceMap[optionName.str()] = device;
					++indexOptiX;
					continue;
				}
#endif
			}
		}

		// Cycles core objects.
		ccl::Session *m_session;
		ccl::Scene *m_scene;
		ccl::SessionParams m_sessionParams;
		ccl::SceneParams m_sceneParams;
		ccl::BufferParams m_bufferParams;
		ccl::BufferParams m_bufferParamsModified;
		ccl::DenoiseParams m_denoiseParams;
		ccl::TextureCacheParams m_textureCacheParams;
		ccl::Camera *m_defaultCamera;
		ccl::Integrator m_integrator;
		ccl::Background m_background;
		ccl::Film m_film;
		ccl::CurveSystemManager m_curveSystemManager;
		// Hold onto ImageManager so it doesn't get deleted.
		ccl::ImageManager *m_imageManager;
		// Dummy ImageManager for Cycles
		ccl::ImageManager *m_imageManagerOld;

		// Background shader
		SharedCShaderPtr m_backgroundShader;

		// Defaults
		ccl::SessionParams m_sessionParamsDefault;
		ccl::SceneParams m_sceneParamsDefault;
		ccl::DenoiseParams m_denoiseParamsDefault;
		ccl::CurveSystemManager m_curveSystemManagerDefault;
		ccl::TextureCacheParams m_textureCacheParamsDefault;

		// IECoreScene::Renderer
		string m_deviceName;
		string m_shadingsystemName;
		RenderType m_renderType;
		int m_frame;
		string m_camera;
		bool m_rendering;
		bool m_deviceDirty;
		bool m_pause;
		IECore::Msg::Level m_progressLevel;

		// Caches.
		CameraCachePtr m_cameraCache;
		ShaderCachePtr m_shaderCache;
		LightCachePtr m_lightCache;
		InstanceCachePtr m_instanceCache;
		ParticleSystemsCachePtr m_particleSystemsCache;
		AttributesCachePtr m_attributesCache;

		// Outputs
		OutputMap m_outputs;

		// Multi-Devices
		typedef unordered_map<string, ccl::DeviceInfo> DeviceMap;
		DeviceMap m_deviceMap;
		ccl::vector<ccl::DeviceInfo> m_multiDevices;

		// Cameras (Cycles can only know of one camera at a time)
		typedef unordered_map<string, ConstCameraPtr> CameraMap;
		CameraMap m_cameras;
		tbb::spin_mutex m_camerasMutex;
		string m_dicingCamera;

		// RenderCallback
		RenderCallbackPtr m_renderCallback;

		// Registration with factory
		static Renderer::TypeDescription<CyclesRenderer> g_typeDescription;

};

IECoreScenePreview::Renderer::TypeDescription<CyclesRenderer> CyclesRenderer::g_typeDescription( "Cycles" );

} // namespace
