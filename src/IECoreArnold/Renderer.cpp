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

#include "GafferScene/Private/IECoreScenePreview/Renderer.h"
#include "GafferScene/Private/IECoreScenePreview/Procedural.h"

#include "IECoreArnold/CameraAlgo.h"
#include "IECoreArnold/NodeAlgo.h"
#include "IECoreArnold/ParameterAlgo.h"
#include "IECoreArnold/ShaderNetworkAlgo.h"
#include "IECoreArnold/UniverseBlock.h"

#include "IECoreScene/Camera.h"
#include "IECoreScene/CurvesPrimitive.h"
#include "IECoreScene/ExternalProcedural.h"
#include "IECoreScene/MeshPrimitive.h"
#include "IECoreScene/Shader.h"
#include "IECoreScene/SpherePrimitive.h"
#include "IECoreScene/Transform.h"

#include "IECoreVDB/VDBObject.h"
#include "IECoreVDB/TypeIds.h"

#include "IECore/MessageHandler.h"
#include "IECore/SimpleTypedData.h"
#include "IECore/StringAlgo.h"
#include "IECore/VectorTypedData.h"
#include "IECore/Version.h"

#include "boost/algorithm/string.hpp"
#include "boost/algorithm/string/join.hpp"
#include "boost/algorithm/string/predicate.hpp"
#include "boost/container/flat_map.hpp"
#include "boost/date_time/posix_time/posix_time.hpp"
#include "boost/filesystem/operations.hpp"
#include "boost/format.hpp"
#include "boost/lexical_cast.hpp"

#include "ai_array.h"
#include "ai_msg.h"
#include "ai_procedural.h"
#include "ai_ray.h"
#include "ai_render.h"
#include "ai_scene.h"
#include "ai_stats.h"

#include "tbb/concurrent_unordered_map.h"
#include "tbb/concurrent_vector.h"
#include "tbb/partitioner.h"
#include "tbb/spin_mutex.h"

#include <condition_variable>
#include <functional>
#include <memory>
#include <sstream>
#include <thread>
#include <unordered_set>

using namespace std;
using namespace boost::filesystem;
using namespace IECoreArnold;

//////////////////////////////////////////////////////////////////////////
// Utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

using SharedAtNodePtr = std::shared_ptr<AtNode>;
using NodeDeleter = bool (*)( AtNode * );

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

void substituteShaderIfNecessary( IECoreScene::ConstShaderNetworkPtr &shaderNetwork, const IECore::CompoundObject *attributes )
{
	if( !shaderNetwork )
	{
		return;
	}

	IECore::MurmurHash h;
	shaderNetwork->hashSubstitutions( attributes, h );
	if( h != IECore::MurmurHash() )
	{
		IECoreScene::ShaderNetworkPtr substituted = shaderNetwork->copy();
		substituted->applySubstitutions( attributes );
		shaderNetwork = substituted;
	}
}

void hashShaderOutputParameter( const IECoreScene::ShaderNetwork *network, const IECoreScene::ShaderNetwork::Parameter &parameter, IECore::MurmurHash &h )
{

	h.append( parameter.name );

	network->getShader( parameter.shader )->hash( h );

	for( const auto &i : network->inputConnections( parameter.shader ) )
	{
		h.append( i.destination.name );
		hashShaderOutputParameter( network, i.source, h );
	}
}

// Arnold does not support non-uniform sampling. It just takes a start and end
// time, and assumes the samples are distributed evenly between them. Throw an
// exception if given data we can't render.
void ensureUniformTimeSamples( const std::vector<float> &times )
{
	if( times.size() == 0 )
	{
		throw IECore::Exception( "Motion block times must not be empty" );
	}

	float motionStart = times[0];
	float motionEnd = times[ times.size() - 1 ];

	for( unsigned int i = 0; i < times.size(); i++ )
	{
		// Use a really coarse epsilon to check if the values are uniform - if someone is sloppy with
		// floating point precision when computing their sample times, we don't want to stop them from rendering.
		// But we should warn someone if they are actually trying to use a feature Arnold doesn't support.
		const float uniformity_epsilon = 0.01;
		float expectedTime = motionStart + ( motionEnd - motionStart ) / ( times.size() - 1 ) * i;
		if( times[i] < expectedTime - uniformity_epsilon || times[i] > expectedTime + uniformity_epsilon )
		{
			std::stringstream text;
			text << "Arnold does not support non-uniform motion blocks.\n";
			text << "Invalid motion block: [ " << times[0];
			for( unsigned int j = 1; j < times.size(); j++ )
			{
				text << ", " << times[j];
			}
			text << " ]\n";
			text << "( sample " << i << ", with value " << times[i] << " does not match " << expectedTime << ")\n";
			throw IECore::Exception( text.str() );
		}
	}
}

const AtString g_aaSamplesArnoldString( "AA_samples" );
const AtString g_aaSeedArnoldString( "AA_seed" );
const AtString g_aovShadersArnoldString( "aov_shaders" );
const AtString g_autoArnoldString( "auto" );
const AtString g_atmosphereArnoldString( "atmosphere" );
const AtString g_backgroundArnoldString( "background" );
const AtString g_boxArnoldString("box");
const AtString g_cameraArnoldString( "camera" );
const AtString g_catclarkArnoldString("catclark");
const AtString g_colorManagerArnoldString( "color_manager" );
const AtString g_cortexIDArnoldString( "cortex:id" );
const AtString g_customAttributesArnoldString( "custom_attributes" );
const AtString g_curvesArnoldString("curves");
const AtString g_dispMapArnoldString( "disp_map" );
const AtString g_dispHeightArnoldString( "disp_height" );
const AtString g_dispPaddingArnoldString( "disp_padding" );
const AtString g_dispZeroValueArnoldString( "disp_zero_value" );
const AtString g_dispAutoBumpArnoldString( "disp_autobump" );
const AtString g_enableProgressiveRenderString( "enable_progressive_render" );
const AtString g_fileNameArnoldString( "filename" );
const AtString g_filtersArnoldString( "filters" );
const AtString g_funcPtrArnoldString( "funcptr" );
const AtString g_ginstanceArnoldString( "ginstance" );
const AtString g_ignoreMotionBlurArnoldString( "ignore_motion_blur" );
const AtString g_inputArnoldString( "input" );
const AtString g_lightGroupArnoldString( "light_group" );
const AtString g_shadowGroupArnoldString( "shadow_group" );
const AtString g_linearArnoldString( "linear" );
const AtString g_matrixArnoldString( "matrix" );
const AtString g_geometryMatrixArnoldString( "geometry_matrix" );
const AtString g_matteArnoldString( "matte" );
const AtString g_meshArnoldString( "mesh" );
const AtString g_modeArnoldString( "mode" );
const AtString g_minPixelWidthArnoldString( "min_pixel_width" );
const AtString g_meshLightArnoldString("mesh_light");
const AtString g_motionStartArnoldString( "motion_start" );
const AtString g_motionEndArnoldString( "motion_end" );
const AtString g_nameArnoldString( "name" );
const AtString g_nodeArnoldString("node");
const AtString g_objectArnoldString( "object" );
const AtString g_opaqueArnoldString( "opaque" );
const AtString g_proceduralArnoldString( "procedural" );
const AtString g_pinCornersArnoldString( "pin_corners" );
const AtString g_pixelAspectRatioArnoldString( "pixel_aspect_ratio" );
const AtString g_pluginSearchPathArnoldString( "plugin_searchpath" );
const AtString g_polymeshArnoldString("polymesh");
const AtString g_rasterArnoldString( "raster" );
const AtString g_receiveShadowsArnoldString( "receive_shadows" );
const AtString g_referenceTimeString( "reference_time" );
const AtString g_regionMinXArnoldString( "region_min_x" );
const AtString g_regionMaxXArnoldString( "region_max_x" );
const AtString g_regionMinYArnoldString( "region_min_y" );
const AtString g_regionMaxYArnoldString( "region_max_y" );
const AtString g_renderSessionArnoldString( "render_session" );
const AtString g_selfShadowsArnoldString( "self_shadows" );
const AtString g_shaderArnoldString( "shader" );
const AtString g_shutterStartArnoldString( "shutter_start" );
const AtString g_shutterEndArnoldString( "shutter_end" );
const AtString g_sidednessArnoldString( "sidedness" );
const AtString g_sphereArnoldString("sphere");
const AtString g_sssSetNameArnoldString( "sss_setname" );
const AtString g_stepSizeArnoldString( "step_size" );
const AtString g_stepScaleArnoldString( "step_scale" );
const AtString g_subdivDicingCameraString( "subdiv_dicing_camera" );
const AtString g_subdivIterationsArnoldString( "subdiv_iterations" );
const AtString g_subdivAdaptiveErrorArnoldString( "subdiv_adaptive_error" );
const AtString g_subdivAdaptiveMetricArnoldString( "subdiv_adaptive_metric" );
const AtString g_subdivAdaptiveSpaceArnoldString( "subdiv_adaptive_space" );
const AtString g_subdivFrustumIgnoreArnoldString( "subdiv_frustum_ignore" );
const AtString g_subdivSmoothDerivsArnoldString( "subdiv_smooth_derivs" );
const AtString g_subdivTypeArnoldString( "subdiv_type" );
const AtString g_subdivUVSmoothingArnoldString( "subdiv_uv_smoothing" );
const AtString g_toonIdArnoldString( "toon_id" );
const AtString g_traceSetsArnoldString( "trace_sets" );
const AtString g_transformTypeArnoldString( "transform_type" );
const AtString g_thickArnoldString( "thick" );
const AtString g_useLightGroupArnoldString( "use_light_group" );
const AtString g_useShadowGroupArnoldString( "use_shadow_group" );
const AtString g_userPtrArnoldString( "userptr" );
const AtString g_visibilityArnoldString( "visibility" );
const AtString g_autobumpVisibilityArnoldString( "autobump_visibility" );
const AtString g_volumeArnoldString("volume");
const AtString g_volumePaddingArnoldString( "volume_padding" );
const AtString g_volumeGridsArnoldString( "grids" );
const AtString g_velocityGridsArnoldString( "velocity_grids" );
const AtString g_velocityScaleArnoldString( "velocity_scale" );
const AtString g_velocityFPSArnoldString( "velocity_fps" );
const AtString g_velocityOutlierThresholdArnoldString( "velocity_outlier_threshold" );
const AtString g_widthArnoldString( "width" );
const AtString g_xresArnoldString( "xres" );
const AtString g_yresArnoldString( "yres" );
const AtString g_filterMapArnoldString( "filtermap" );
const AtString g_universeArnoldString( "universe" );
const AtString g_uvRemapArnoldString( "uv_remap" );

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
IE_CORE_FORWARDDECLARE( ArnoldObject );

/// This class implements the basics of outputting attributes
/// and objects to Arnold, but is not a complete implementation
/// of the renderer interface. It is subclassed to provide concrete
/// implementations suitable for use as the master renderer or
/// for use in procedurals.
class ArnoldRendererBase : public IECoreScenePreview::Renderer
{

	public :

		~ArnoldRendererBase() override;

		IECore::InternedString name() const override;

		Renderer::AttributesInterfacePtr attributes( const IECore::CompoundObject *attributes ) override;

		ObjectInterfacePtr camera( const std::string &name, const IECoreScene::Camera *camera, const AttributesInterface *attributes ) override;
		ObjectInterfacePtr camera( const std::string &name, const std::vector<const IECoreScene::Camera *> &samples, const std::vector<float> &times, const AttributesInterface *attributes ) override;
		ObjectInterfacePtr light( const std::string &name, const IECore::Object *object, const AttributesInterface *attributes ) override;
		ObjectInterfacePtr lightFilter( const std::string &name, const IECore::Object *object, const AttributesInterface *attributes ) override;
		Renderer::ObjectInterfacePtr object( const std::string &name, const IECore::Object *object, const AttributesInterface *attributes ) override;
		ObjectInterfacePtr object( const std::string &name, const std::vector<const IECore::Object *> &samples, const std::vector<float> &times, const AttributesInterface *attributes ) override;

	protected :

		ArnoldRendererBase( NodeDeleter nodeDeleter, AtUniverse *universe, AtNode *parentNode = nullptr, const IECore::MessageHandlerPtr &messageHandler = IECore::MessageHandlerPtr() );

		NodeDeleter m_nodeDeleter;
		AtUniverse *m_universe;
		ShaderCachePtr m_shaderCache;
		InstanceCachePtr m_instanceCache;

		IECore::MessageHandlerPtr m_messageHandler;

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

		ArnoldOutput( AtUniverse *universe, const IECore::InternedString &name, const IECoreScene::Output *output, NodeDeleter nodeDeleter )
		{
			// Create a driver node and set its parameters.

			AtString driverNodeType( output->getType().c_str() );
			if( AiNodeEntryGetType( AiNodeEntryLookUp( driverNodeType ) ) != AI_NODE_DRIVER )
			{
				// Automatically map tiff to driver_tiff and so on, to provide a degree of
				// compatibility with existing renderman driver names.
				AtString prefixedType( ( std::string("driver_") + driverNodeType.c_str() ).c_str() );
				if( AiNodeEntryLookUp( prefixedType ) )
				{
					driverNodeType = prefixedType;
				}
			}

			const std::string driverNodeName = boost::str( boost::format( "ieCoreArnold:display:%s" ) % name.string() );
			m_driver.reset(
				AiNode( universe, driverNodeType, AtString( driverNodeName.c_str() ) ),
				nodeDeleter
			);
			if( !m_driver )
			{
				throw IECore::Exception( boost::str( boost::format( "Unable to create output driver of type \"%s\"" ) % driverNodeType.c_str() ) );
			}

			if( const AtParamEntry *fileNameParameter = AiNodeEntryLookUpParameter( AiNodeGetNodeEntry( m_driver.get() ), g_fileNameArnoldString ) )
			{
				AiNodeSetStr( m_driver.get(), AiParamGetName( fileNameParameter ), AtString( output->getName().c_str() ) );
			}

			IECore::StringVectorDataPtr customAttributesData;
			if( const IECore::StringVectorData *d = output->parametersData()->member<IECore::StringVectorData>( "custom_attributes") )
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

				if( it->first.string() == "camera" )
				{
					if( const IECore::StringData *d = IECore::runTimeCast<const IECore::StringData>( it->second.get() ) )
					{
						m_cameraOverride = d->readable();
						continue;
					}
				}

				ParameterAlgo::setParameter( m_driver.get(), it->first.c_str(), it->second.get() );
			}

			if( AiNodeEntryLookUpParameter( AiNodeGetNodeEntry( m_driver.get() ), g_customAttributesArnoldString ) )
			{
				ParameterAlgo::setParameter( m_driver.get(), "custom_attributes", customAttributesData.get() );
			}

			// Create a filter.

			std::string filterNodeType = parameter<std::string>( output->parameters(), "filter", "gaussian" );
			if( AiNodeEntryGetType( AiNodeEntryLookUp( AtString( filterNodeType.c_str() ) ) ) != AI_NODE_FILTER )
			{
				filterNodeType = filterNodeType + "_filter";
			}

			const std::string filterNodeName = boost::str( boost::format( "ieCoreArnold:filter:%s" ) % name.string() );
			m_filter.reset(
				AiNode( universe, AtString( filterNodeType.c_str() ), AtString( filterNodeName.c_str() ) ),
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
						AiNodeSetFlt( m_filter.get(), g_widthArnoldString, v->readable().x );
						continue;
					}
				}

				ParameterAlgo::setParameter( m_filter.get(), it->first.c_str() + 6, it->second.get() );
			}

			// Convert the data specification to the form
			// supported by Arnold.

			if( output->getData()=="rgb" )
			{
				m_data = "RGB";
				m_type = "RGB";
			}
			else if( output->getData()=="rgba" )
			{
				m_data = "RGBA";
				m_type = "RGBA";
			}
			else
			{
				std::string colorType = "RGB";
				if( parameter<bool>( output->parameters(), "includeAlpha", false ) )
				{
					colorType = "RGBA";
				}

				vector<std::string> tokens;
				IECore::StringAlgo::tokenize( output->getData(), ' ', tokens );

				if( tokens.size() == 2 )
				{
					if( tokens[0] == "color" )
					{
						m_data = tokens[1];
						m_type = colorType;
					}
					else if( tokens[0] == "lpe" )
					{
						m_lpeName = "ieCoreArnold:lpe:" + name.string();
						m_lpeValue = tokens[1];
						m_data = m_lpeName;
						m_type = colorType;
					}
					else if( tokens[0] == "float" || tokens[0] == "int" || tokens[0] == "uint" )
					{
						// Cortex convention is `<type> <name>`. Arnold
						// convention is `<name> <TYPE>`.
						m_data = tokens[1];
						m_type = boost::to_upper_copy( tokens[0] );
					}
					else
					{
						/// \todo Omit this output completely. We currently give it to Arnold
						/// verbatim, to provide backward compatibility for old scenes that passed
						/// an Arnold-formatted data string directly. In future, we want all outputs
						/// to use the standard Cortex formatting instead.
						IECore::msg(
							IECore::Msg::Warning, "ArnoldRenderer",
							boost::format( "Unknown data type \"%1%\" for output \"%2%\"" ) % tokens[0] % name
						);
						m_data = tokens[0];
						m_type = tokens[1];
					}
				}
				else
				{
					/// \todo See above.
					IECore::msg(
						IECore::Msg::Warning, "ArnoldRenderer",
						boost::format( "Unknown data specification \"%1%\" for output \"%2%\"" ) % output->getData() % name
					);
					m_data = output->getData();
					m_type = "";
				}
			}

			// Decide if this render should be updated at interactive rates or
			// not. We update all beauty outputs interactively by default, and
			// allow others to be overridden using a parameter.
			m_updateInteractively = parameter<bool>(
				output->parameters(), "updateInteractively",
				m_data == "RGBA" || m_data == "RGB"
			);
		}

		void updateImager( AtNode *imager )
		{
			AiNodeSetPtr( m_driver.get(), g_inputArnoldString, imager );
		}

		void append( std::vector<std::string> &outputs, std::vector<std::string> &lightPathExpressions ) const
		{
			outputs.push_back( boost::str( boost::format( "%s %s %s %s" ) % m_data % m_type % AiNodeGetName( m_filter.get() ) % AiNodeGetName( m_driver.get() ) ) );
			if( m_lpeValue.size() )
			{
				lightPathExpressions.push_back( m_lpeName + " " + m_lpeValue );
			}
		}

		const std::string &cameraOverride()
		{
			return m_cameraOverride;
		}

		bool updateInteractively() const
		{
			return m_updateInteractively;
		}

		bool requiresIDAOV() const
		{
			return m_data == "id";
		}

	private :

		SharedAtNodePtr m_driver;
		SharedAtNodePtr m_filter;
		std::string m_data;
		std::string m_type;
		std::string m_lpeName;
		std::string m_lpeValue;
		std::string m_cameraOverride;
		bool m_updateInteractively;

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

		ArnoldShader( const IECoreScene::ShaderNetwork *shaderNetwork, NodeDeleter nodeDeleter, AtUniverse *universe, const std::string &name, const AtNode *parentNode )
			:	m_nodeDeleter( nodeDeleter ), m_hash( shaderNetwork->Object::hash() )
		{
			m_nodes = ShaderNetworkAlgo::convert( shaderNetwork, universe, name, parentNode );
		}

		~ArnoldShader() override
		{
			for( std::vector<AtNode *>::const_iterator it = m_nodes.begin(), eIt = m_nodes.end(); it != eIt; ++it )
			{
				m_nodeDeleter( *it );
			}
		}

		bool update( const IECoreScene::ShaderNetwork *shaderNetwork )
		{
			// `ShaderNetworkAlgo::update()` will destroy unwanted nodes, so we can
			// only call it if we're responsible for deleting them in the first place.
			assert( m_nodeDeleter == AiNodeDestroy );
			return ShaderNetworkAlgo::update( m_nodes, shaderNetwork );
		}

		AtNode *root() const
		{
			return !m_nodes.empty() ? m_nodes.back() : nullptr;
		}

		void nodesCreated( vector<AtNode *> &nodes ) const
		{
			nodes.insert( nodes.end(), m_nodes.begin(), m_nodes.end() );
		}

		void hash( IECore::MurmurHash &h ) const
		{
			h.append( m_hash );
		}

	private :

		NodeDeleter m_nodeDeleter;
		std::vector<AtNode *> m_nodes;
		const IECore::MurmurHash m_hash;

};

IE_CORE_DECLAREPTR( ArnoldShader )

class ShaderCache : public IECore::RefCounted
{

	public :

		ShaderCache( NodeDeleter nodeDeleter, AtUniverse *universe, AtNode *parentNode )
			:	m_nodeDeleter( nodeDeleter ), m_universe( universe ), m_parentNode( parentNode )
		{
		}

		// Can be called concurrently with other get() calls.
		ArnoldShaderPtr get( const IECoreScene::ShaderNetwork *shader, const IECore::CompoundObject *attributes )
		{
			IECore::MurmurHash h = shader->Object::hash();
			IECore::MurmurHash hSubst;
			if( attributes )
			{
				shader->hashSubstitutions( attributes, hSubst );
				h.append( hSubst );
			}

			Cache::const_accessor readAccessor;
			if( m_cache.find( readAccessor, h ) )
			{
				return readAccessor->second;
			}

			Cache::accessor writeAccessor;
			if( m_cache.insert( writeAccessor, h ) )
			{
				const std::string namePrefix = "shader:" + writeAccessor->first.toString();
				if( hSubst != IECore::MurmurHash() )
				{
					IECoreScene::ShaderNetworkPtr substitutedShader = shader->copy();
					substitutedShader->applySubstitutions( attributes );
					writeAccessor->second = new ArnoldShader( substitutedShader.get(), m_nodeDeleter, m_universe, namePrefix, m_parentNode );
				}
				else
				{
					writeAccessor->second = new ArnoldShader( shader, m_nodeDeleter, m_universe, namePrefix, m_parentNode );
				}
			}
			return writeAccessor->second;
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
		AtUniverse *m_universe;
		AtNode *m_parentNode;

		using Cache = tbb::concurrent_hash_map<IECore::MurmurHash, ArnoldShaderPtr>;
		Cache m_cache;
};

IE_CORE_DECLAREPTR( ShaderCache )

} // namespace

//////////////////////////////////////////////////////////////////////////
// ArnoldAttributes
//////////////////////////////////////////////////////////////////////////

namespace
{

// Forward declaration
bool isConvertedProcedural( const AtNode *node );

IECore::InternedString g_surfaceShaderAttributeName( "surface" );
IECore::InternedString g_lightShaderAttributeName( "light" );
IECore::InternedString g_doubleSidedAttributeName( "doubleSided" );
IECore::InternedString g_setsAttributeName( "sets" );

IECore::InternedString g_oslSurfaceShaderAttributeName( "osl:surface" );
IECore::InternedString g_oslShaderAttributeName( "osl:shader" );

IECore::InternedString g_cameraVisibilityAttributeName( "ai:visibility:camera" );
IECore::InternedString g_shadowVisibilityAttributeName( "ai:visibility:shadow" );
IECore::InternedString g_shadowGroup( "ai:visibility:shadow_group" );
IECore::InternedString g_diffuseReflectVisibilityAttributeName( "ai:visibility:diffuse_reflect" );
IECore::InternedString g_specularReflectVisibilityAttributeName( "ai:visibility:specular_reflect" );
IECore::InternedString g_diffuseTransmitVisibilityAttributeName( "ai:visibility:diffuse_transmit" );
IECore::InternedString g_specularTransmitVisibilityAttributeName( "ai:visibility:specular_transmit" );
IECore::InternedString g_volumeVisibilityAttributeName( "ai:visibility:volume" );
IECore::InternedString g_subsurfaceVisibilityAttributeName( "ai:visibility:subsurface" );

IECore::InternedString g_cameraVisibilityAutoBumpAttributeName( "ai:autobump_visibility:camera" );
IECore::InternedString g_diffuseReflectVisibilityAutoBumpAttributeName( "ai:autobump_visibility:diffuse_reflect" );
IECore::InternedString g_specularReflectVisibilityAutoBumpAttributeName( "ai:autobump_visibility:specular_reflect" );
IECore::InternedString g_diffuseTransmitVisibilityAutoBumpAttributeName( "ai:autobump_visibility:diffuse_transmit" );
IECore::InternedString g_specularTransmitVisibilityAutoBumpAttributeName( "ai:autobump_visibility:specular_transmit" );
IECore::InternedString g_volumeVisibilityAutoBumpAttributeName( "ai:autobump_visibility:volume" );
IECore::InternedString g_subsurfaceVisibilityAutoBumpAttributeName( "ai:autobump_visibility:subsurface" );

IECore::InternedString g_arnoldSurfaceShaderAttributeName( "ai:surface" );
IECore::InternedString g_arnoldLightShaderAttributeName( "ai:light" );
IECore::InternedString g_arnoldFilterMapAttributeName( "ai:filtermap" );
IECore::InternedString g_arnoldUVRemapAttributeName( "ai:uv_remap" );
IECore::InternedString g_arnoldLightFilterShaderAttributeName( "ai:lightFilter:filter" );

IECore::InternedString g_arnoldReceiveShadowsAttributeName( "ai:receive_shadows" );
IECore::InternedString g_arnoldSelfShadowsAttributeName( "ai:self_shadows" );
IECore::InternedString g_arnoldOpaqueAttributeName( "ai:opaque" );
IECore::InternedString g_arnoldMatteAttributeName( "ai:matte" );

IECore::InternedString g_volumeStepSizeAttributeName( "ai:volume:step_size" );
IECore::InternedString g_volumeStepScaleAttributeName( "ai:volume:step_scale" );
IECore::InternedString g_shapeVolumeStepScaleAttributeName( "ai:shape:step_scale" );
IECore::InternedString g_shapeVolumeStepSizeAttributeName( "ai:shape:step_size" );
IECore::InternedString g_shapeVolumePaddingAttributeName( "ai:shape:volume_padding" );
IECore::InternedString g_volumeGridsAttributeName( "ai:volume:grids" );
IECore::InternedString g_velocityGridsAttributeName( "ai:volume:velocity_grids" );
IECore::InternedString g_velocityScaleAttributeName( "ai:volume:velocity_scale" );
IECore::InternedString g_velocityFPSAttributeName( "ai:volume:velocity_fps" );
IECore::InternedString g_velocityOutlierThresholdAttributeName( "ai:volume:velocity_outlier_threshold" );

IECore::InternedString g_transformTypeAttributeName( "ai:transform_type" );

IECore::InternedString g_polyMeshSubdivIterationsAttributeName( "ai:polymesh:subdiv_iterations" );
IECore::InternedString g_polyMeshSubdivAdaptiveErrorAttributeName( "ai:polymesh:subdiv_adaptive_error" );
IECore::InternedString g_polyMeshSubdivAdaptiveMetricAttributeName( "ai:polymesh:subdiv_adaptive_metric" );
IECore::InternedString g_polyMeshSubdivAdaptiveSpaceAttributeName( "ai:polymesh:subdiv_adaptive_space" );
IECore::InternedString g_polyMeshSubdivSmoothDerivsAttributeName( "ai:polymesh:subdiv_smooth_derivs" );
IECore::InternedString g_polyMeshSubdivFrustumIgnoreAttributeName( "ai:polymesh:subdiv_frustum_ignore" );
IECore::InternedString g_polyMeshSubdividePolygonsAttributeName( "ai:polymesh:subdivide_polygons" );
IECore::InternedString g_polyMeshSubdivUVSmoothingAttributeName( "ai:polymesh:subdiv_uv_smoothing" );

IECore::InternedString g_dispMapAttributeName( "ai:disp_map" );
IECore::InternedString g_dispHeightAttributeName( "ai:disp_height" );
IECore::InternedString g_dispPaddingAttributeName( "ai:disp_padding" );
IECore::InternedString g_dispZeroValueAttributeName( "ai:disp_zero_value" );
IECore::InternedString g_dispAutoBumpAttributeName( "ai:disp_autobump" );

IECore::InternedString g_curvesMinPixelWidthAttributeName( "ai:curves:min_pixel_width" );
IECore::InternedString g_curvesModeAttributeName( "ai:curves:mode" );
IECore::InternedString g_sssSetNameName( "ai:sss_setname" );
IECore::InternedString g_toonIdName( "ai:toon_id" );

IECore::InternedString g_lightFilterPrefix( "ai:lightFilter:" );

IECore::InternedString g_filteredLights( "filteredLights" );

const char *customAttributeName( const std::string &attributeName, bool *hasPrecedence = nullptr )
{
	if( boost::starts_with( attributeName, "user:" ) )
	{
		if( hasPrecedence )
		{
			*hasPrecedence = false;
		}
		return attributeName.c_str();
	}
	else if( boost::starts_with( attributeName, "render:" ) )
	{
		if( hasPrecedence )
		{
			*hasPrecedence = true;
		}
		return attributeName.c_str() + 7;
	}

	// Not a custom attribute
	return nullptr;
}

class ArnoldAttributes : public IECoreScenePreview::Renderer::AttributesInterface
{

	public :

		ArnoldAttributes( const IECore::CompoundObject *attributes, ShaderCache *shaderCache )
			:	m_visibility( AI_RAY_ALL ), m_sidedness( AI_RAY_ALL ), m_shadingFlags( Default ), m_stepSize( 0.0f ), m_stepScale( 1.0f ), m_volumePadding( 0.0f ), m_polyMesh( attributes ), m_displacement( attributes, shaderCache ), m_curves( attributes ), m_volume( attributes ), m_allAttributes( attributes )
		{
			updateVisibility( m_visibility, g_cameraVisibilityAttributeName, AI_RAY_CAMERA, attributes );
			updateVisibility( m_visibility, g_shadowVisibilityAttributeName, AI_RAY_SHADOW, attributes );
			updateVisibility( m_visibility, g_diffuseReflectVisibilityAttributeName, AI_RAY_DIFFUSE_REFLECT, attributes );
			updateVisibility( m_visibility, g_specularReflectVisibilityAttributeName, AI_RAY_SPECULAR_REFLECT, attributes );
			updateVisibility( m_visibility, g_diffuseTransmitVisibilityAttributeName, AI_RAY_DIFFUSE_TRANSMIT, attributes );
			updateVisibility( m_visibility, g_specularTransmitVisibilityAttributeName, AI_RAY_SPECULAR_TRANSMIT, attributes );
			updateVisibility( m_visibility, g_volumeVisibilityAttributeName, AI_RAY_VOLUME, attributes );
			updateVisibility( m_visibility, g_subsurfaceVisibilityAttributeName, AI_RAY_SUBSURFACE, attributes );

			if( const IECore::BoolData *d = attribute<IECore::BoolData>( g_doubleSidedAttributeName, attributes ) )
			{
				m_sidedness = d->readable() ? AI_RAY_ALL : AI_RAY_UNDEFINED;
			}

			updateShadingFlag( g_arnoldReceiveShadowsAttributeName, ReceiveShadows, attributes );
			updateShadingFlag( g_arnoldSelfShadowsAttributeName, SelfShadows, attributes );
			updateShadingFlag( g_arnoldOpaqueAttributeName, Opaque, attributes );
			updateShadingFlag( g_arnoldMatteAttributeName, Matte, attributes );

			const IECoreScene::ShaderNetwork *surfaceShaderAttribute = attribute<IECoreScene::ShaderNetwork>( g_arnoldSurfaceShaderAttributeName, attributes );
			surfaceShaderAttribute = surfaceShaderAttribute ? surfaceShaderAttribute : attribute<IECoreScene::ShaderNetwork>( g_oslSurfaceShaderAttributeName, attributes );
			/// \todo Remove support for interpreting "osl:shader" as a surface shader assignment.
			surfaceShaderAttribute = surfaceShaderAttribute ? surfaceShaderAttribute : attribute<IECoreScene::ShaderNetwork>( g_oslShaderAttributeName, attributes );
			surfaceShaderAttribute = surfaceShaderAttribute ? surfaceShaderAttribute : attribute<IECoreScene::ShaderNetwork>( g_surfaceShaderAttributeName, attributes );
			if( surfaceShaderAttribute )
			{
				m_surfaceShader = shaderCache->get( surfaceShaderAttribute, attributes );
			}

			if( auto filterMapAttribute = attribute<IECoreScene::ShaderNetwork>( g_arnoldFilterMapAttributeName, attributes ) )
			{
				m_filterMap = shaderCache->get( filterMapAttribute, attributes );
			}
			if( auto uvRemapAttribute = attribute<IECoreScene::ShaderNetwork>( g_arnoldUVRemapAttributeName, attributes ) )
			{
				m_uvRemap = shaderCache->get( uvRemapAttribute, attributes );
			}

			m_lightShader = attribute<IECoreScene::ShaderNetwork>( g_arnoldLightShaderAttributeName, attributes );
			m_lightShader = m_lightShader ? m_lightShader : attribute<IECoreScene::ShaderNetwork>( g_lightShaderAttributeName, attributes );
			substituteShaderIfNecessary( m_lightShader, attributes );

			m_lightFilterShader = attribute<IECoreScene::ShaderNetwork>( g_arnoldLightFilterShaderAttributeName, attributes );
			substituteShaderIfNecessary( m_lightFilterShader, attributes );

			m_traceSets = attribute<IECore::InternedStringVectorData>( g_setsAttributeName, attributes );
			m_transformType = attribute<IECore::StringData>( g_transformTypeAttributeName, attributes );
			m_stepSize = attributeValue<float>( g_shapeVolumeStepSizeAttributeName, attributes, 0.0f );
			m_stepScale = attributeValue<float>( g_shapeVolumeStepScaleAttributeName, attributes, 1.0f );
			m_volumePadding = attributeValue<float>( g_shapeVolumePaddingAttributeName, attributes, 0.0f );

			m_sssSetName = attribute<IECore::StringData>( g_sssSetNameName, attributes );
			m_toonId = attribute<IECore::StringData>( g_toonIdName, attributes );

			for( IECore::CompoundObject::ObjectMap::const_iterator it = attributes->members().begin(), eIt = attributes->members().end(); it != eIt; ++it )
			{
				bool hasPrecedence;
				if( const char *name = customAttributeName( it->first.string(), &hasPrecedence ) )
				{
					if( const IECore::Data *data = IECore::runTimeCast<const IECore::Data>( it->second.get() ) )
					{
						auto inserted = m_custom.insert( CustomAttributes::value_type( name, nullptr ) );
						if( hasPrecedence || inserted.second )
						{
							inserted.first->second = data;
						}
					}
				}

				if( it->first == g_arnoldLightFilterShaderAttributeName )
				{
					continue;
				}
				else if( boost::starts_with( it->first.string(), g_lightFilterPrefix.string() ) )
				{
					ArnoldShaderPtr filter = shaderCache->get( IECore::runTimeCast<const IECoreScene::ShaderNetwork>( it->second.get() ), attributes );
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
			if( const IECoreScene::MeshPrimitive *mesh = IECore::runTimeCast<const IECoreScene::MeshPrimitive>( object ) )
			{
				m_polyMesh.apply( mesh, node );
				m_displacement.apply( node );
			}
			else if( IECore::runTimeCast<const IECoreScene::CurvesPrimitive>( object ) )
			{
				m_curves.apply( node );
			}
			else if( IECore::runTimeCast<const IECoreVDB::VDBObject>( object ) )
			{
				m_volume.apply( node );
			}
			else if( const IECoreScene::ExternalProcedural *procedural = IECore::runTimeCast<const IECoreScene::ExternalProcedural>( object ) )
			{
				if( procedural->getFileName() == "volume" )
				{
					m_volume.apply( node );
				}
			}

			float actualStepSize = m_stepSize * m_stepScale;

			if( actualStepSize != 0.0f && AiNodeEntryLookUpParameter( AiNodeGetNodeEntry( node ), g_stepSizeArnoldString ) )
			{
				// Only apply step_size if it hasn't already been set to a non-zero
				// value by the geometry converter. This allows procedurals to carry
				// their step size as a parameter and have it trump the attribute value.
				// This is important for Gaffer nodes like ArnoldVDB, which carefully
				// calculate the correct step size and provide it via a parameter.
				if( AiNodeGetFlt( node, g_stepSizeArnoldString ) == 0.0f )
				{
					AiNodeSetFlt( node, g_stepSizeArnoldString, actualStepSize );
				}
			}

			if( m_volumePadding != 0.0f && AiNodeEntryLookUpParameter( AiNodeGetNodeEntry( node ), g_volumePaddingArnoldString ) )
			{
				AiNodeSetFlt( node, g_volumePaddingArnoldString, m_volumePadding );
			}

		}

		// Generates a signature for the work done by applyGeometry.
		void hashGeometry( const IECore::Object *object, IECore::MurmurHash &h ) const
		{
			const IECore::TypeId objectType = object->typeId();
			bool meshInterpolationIsLinear = false;
			bool proceduralIsVolumetric = false;
			if( objectType == IECoreScene::MeshPrimitive::staticTypeId() )
			{
				meshInterpolationIsLinear = static_cast<const IECoreScene::MeshPrimitive *>( object )->interpolation() == "linear";
			}
			else if( objectType == IECoreScene::ExternalProcedural::staticTypeId() )
			{
				const IECoreScene::ExternalProcedural *procedural = static_cast<const IECoreScene::ExternalProcedural *>( object );
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
			if( !IECore::runTimeCast<const IECoreScene::VisibleRenderable>( object ) )
			{
				return false;
			}

			if( const IECoreScene::MeshPrimitive *mesh = IECore::runTimeCast<const IECoreScene::MeshPrimitive>( object ) )
			{
				if( mesh->interpolation() == "linear" && !m_polyMesh.subdividePolygons )
				{
					return true;
				}
				else
				{
					// We shouldn't instance poly meshes with view dependent subdivision, because the subdivision
					// for the master mesh might be totally inappropriate for the position of the ginstances in frame.
					return m_polyMesh.subdivAdaptiveError == 0.0f || m_polyMesh.subdivAdaptiveSpace == g_objectArnoldString;
				}
			}
			else if( IECore::runTimeCast<const IECoreScene::CurvesPrimitive>( object ) )
			{
				// Min pixel width is a screen-space metric, and hence not compatible with instancing.
				return m_curves.minPixelWidth == 0.0f;
			}
			else if( const IECoreScene::ExternalProcedural *procedural = IECore::runTimeCast<const IECoreScene::ExternalProcedural>( object ) )
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

			const AtNode *geometry = node;
			if( AiNodeIs( node, g_ginstanceArnoldString ) )
			{
				geometry = static_cast<const AtNode *>( AiNodeGetPtr( node, g_nodeArnoldString ) );
			}

			if( previousAttributes )
			{
				IECore::TypeId objectType = IECore::InvalidTypeId;
				bool meshInterpolationIsLinear = false;
				bool proceduralIsVolumetric = false;
				if( AiNodeIs( geometry, g_polymeshArnoldString ) )
				{
					objectType = IECoreScene::MeshPrimitive::staticTypeId();
					meshInterpolationIsLinear = AiNodeGetStr( geometry, g_subdivTypeArnoldString ) != g_catclarkArnoldString;
				}
				else if( AiNodeIs( geometry, g_curvesArnoldString ) )
				{
					objectType = IECoreScene::CurvesPrimitive::staticTypeId();
				}
				else if( AiNodeIs( geometry, g_boxArnoldString ) )
				{
					objectType = IECoreScene::MeshPrimitive::staticTypeId();
				}
				else if( AiNodeIs( geometry, g_volumeArnoldString ) )
				{
					objectType = IECoreScene::ExternalProcedural::staticTypeId();
					proceduralIsVolumetric = true;
				}
				else if( AiNodeIs( geometry, g_sphereArnoldString ) )
				{
					objectType = IECoreScene::SpherePrimitive::staticTypeId();
				}
				else if( isConvertedProcedural( geometry ) )
				{
					objectType = IECoreScenePreview::Procedural::staticTypeId();
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

			// Remove old custom parameters.

			const AtNodeEntry *nodeEntry = AiNodeGetNodeEntry( node );
			if( previousAttributes )
			{
				for( const auto &attr : previousAttributes->m_custom )
				{
					if( AiNodeEntryLookUpParameter( nodeEntry, attr.first ) )
					{
						// Be careful not to reset a parameter we wouldn't
						// have set in the first place.
						continue;
					}
					AiNodeResetParameter( node, attr.first );
				}
			}

			// Add new custom parameters.

			for( const auto &attr : m_custom )
			{
				if( AiNodeEntryLookUpParameter( nodeEntry, attr.first ) )
				{
					IECore::msg(
						IECore::Msg::Warning,
						"Renderer::attributes",
						boost::format( "Custom attribute \"%s\" will be ignored because it clashes with Arnold's built-in parameters" ) % attr.first.c_str()
					);
					continue;
				}

				ParameterAlgo::setParameter( node, attr.first, attr.second.get() );
			}

			// Early out for IECoreScene::Procedurals. Arnold's inheritance rules for procedurals are back
			// to front, with any explicitly set parameters on the procedural node overriding parameters of child
			// nodes completely. We emulate the inheritance we want in ArnoldProceduralRenderer.

			if( isConvertedProcedural( geometry ) )
			{
				// Arnold neither inherits nor overrides visibility parameters. Instead
				// it does a bitwise `&` between the procedural and its children. The
				// `procedural` node itself will have `visibility == 0` applied by the
				// `Instance` constructor, so it can be instanced without the original
				// being seen. Override that by applying full visibility to the `ginstance`
				// so that the children of the procedural have full control of their final
				// visibility.
				AiNodeSetByte( node, g_visibilityArnoldString, AI_RAY_ALL );
				return true;
			}

			// Add shape specific parameters.

			if( AiNodeEntryGetType( AiNodeGetNodeEntry( node ) ) == AI_NODE_SHAPE )
			{
				AiNodeSetByte( node, g_visibilityArnoldString, m_visibility );
				AiNodeSetByte( node, g_sidednessArnoldString, m_sidedness );

				if( m_transformType )
				{
					// \todo : Arnold quite explicitly discourages constructing AtStrings repeatedly,
					// but given the need to pass m_transformType around as a string for consistency
					// reasons, it seems like there's not much else we can do here.
					// If we start reusing ArnoldAttributes for multiple locations with identical attributes,
					// it could be worth caching this, or possibly in the future we could come up with
					// some way of cleanly exposing enum values as something other than strings.
					AiNodeSetStr( node, g_transformTypeArnoldString, AtString( m_transformType->readable().c_str() ) );
				}

				AiNodeSetBool( node, g_receiveShadowsArnoldString, m_shadingFlags & ArnoldAttributes::ReceiveShadows );
				AiNodeSetBool( node, g_selfShadowsArnoldString, m_shadingFlags & ArnoldAttributes::SelfShadows );
				AiNodeSetBool( node, g_opaqueArnoldString, m_shadingFlags & ArnoldAttributes::Opaque );
				AiNodeSetBool( node, g_matteArnoldString, m_shadingFlags & ArnoldAttributes::Matte );

				if( m_surfaceShader && m_surfaceShader->root() )
				{
					AiNodeSetPtr( node, g_shaderArnoldString, m_surfaceShader->root() );
				}
				else
				{
					AiNodeResetParameter( node, g_shaderArnoldString );
				}

				if( m_traceSets && m_traceSets->readable().size() )
				{
					const vector<IECore::InternedString> &v = m_traceSets->readable();
					AtArray *array = AiArrayAllocate( v.size(), 1, AI_TYPE_STRING );
					for( size_t i = 0, e = v.size(); i < e; ++i )
					{
						AiArraySetStr( array, i, v[i].c_str() );
					}
					AiNodeSetArray( node, g_traceSetsArnoldString, array );
				}
				else
				{
					// Arnold very unhelpfully treats `trace_sets == []` as meaning the object
					// is in every trace set. So we instead make `trace_sets == [ "__none__" ]`
					// to get the behaviour people expect.
					AiNodeSetArray( node, g_traceSetsArnoldString, AiArray( 1, 1, AI_TYPE_STRING, "__none__" ) );
				}

				if( m_sssSetName )
				{
					ParameterAlgo::setParameter( node, g_sssSetNameArnoldString, m_sssSetName.get() );
				}
				else
				{
					AiNodeResetParameter( node, g_sssSetNameArnoldString );
				}

				if( m_toonId )
				{
					ParameterAlgo::setParameter( node, g_toonIdArnoldString, m_toonId.get() );
				}
				else
				{
					AiNodeResetParameter( node, g_toonIdArnoldString );
				}
			}

			// Add camera specific parameters.

			if( AiNodeEntryGetType( AiNodeGetNodeEntry( node ) ) == AI_NODE_CAMERA )
			{
				if( AiNodeEntryLookUpParameter( AiNodeGetNodeEntry( node ), g_filterMapArnoldString ) )
				{
					if( m_filterMap && m_filterMap->root() )
					{
						AiNodeSetPtr( node, g_filterMapArnoldString, m_filterMap->root() );
					}
					else
					{
						AiNodeResetParameter( node, g_filterMapArnoldString );
					}
				}

				if( AiNodeEntryLookUpParameter( AiNodeGetNodeEntry( node ), g_uvRemapArnoldString ) )
				{
					if( m_uvRemap && m_uvRemap->root() )
					{
						AiNodeLinkOutput( m_uvRemap->root(), "", node, g_uvRemapArnoldString );
					}
					else
					{
						AiNodeResetParameter( node, g_uvRemapArnoldString );
					}
				}
			}

			return true;

		}

		const IECoreScene::ShaderNetwork *lightShader() const
		{
			return m_lightShader.get();
		}

		/// Return the shader assigned to a world space light filter
		const IECoreScene::ShaderNetwork *lightFilterShader() const
		{
			return m_lightFilterShader.get();
		}

		/// Return the shaders for filters directly assigned to a light
		const std::vector<ArnoldShaderPtr>& lightFilterShaders() const
		{
			return m_lightFilterShaders;
		}

		const IECore::CompoundObject *allAttributes() const
		{
			return m_allAttributes.get();
		}

	private :

		struct PolyMesh
		{

			PolyMesh( const IECore::CompoundObject *attributes )
			{
				subdivIterations = attributeValue<int>( g_polyMeshSubdivIterationsAttributeName, attributes, 1 );
				subdivAdaptiveError = attributeValue<float>( g_polyMeshSubdivAdaptiveErrorAttributeName, attributes, 0.0f );

				const IECore::StringData *subdivAdaptiveMetricData = attribute<IECore::StringData>( g_polyMeshSubdivAdaptiveMetricAttributeName, attributes );
				if( subdivAdaptiveMetricData )
				{
					subdivAdaptiveMetric = AtString( subdivAdaptiveMetricData->readable().c_str() );
				}
				else
				{
					subdivAdaptiveMetric = g_autoArnoldString;
				}

				const IECore::StringData *subdivAdaptiveSpaceData = attribute<IECore::StringData>( g_polyMeshSubdivAdaptiveSpaceAttributeName, attributes );
				if( subdivAdaptiveSpaceData )
				{
					subdivAdaptiveSpace = AtString( subdivAdaptiveSpaceData->readable().c_str() );
				}
				else
				{
					subdivAdaptiveSpace = g_rasterArnoldString;
				}

				if( auto a = attribute<IECore::StringData>( g_polyMeshSubdivUVSmoothingAttributeName, attributes ) )
				{
					subdivUVSmoothing = AtString( a->readable().c_str() );
				}
				else
				{
					subdivUVSmoothing = g_pinCornersArnoldString;
				}

				subdividePolygons = attributeValue<bool>( g_polyMeshSubdividePolygonsAttributeName, attributes, false );
				subdivSmoothDerivs = attributeValue<bool>( g_polyMeshSubdivSmoothDerivsAttributeName, attributes, false );
				subdivFrustumIgnore = attributeValue<bool>( g_polyMeshSubdivFrustumIgnoreAttributeName, attributes, false );
			}

			int subdivIterations;
			float subdivAdaptiveError;
			AtString subdivAdaptiveMetric;
			AtString subdivAdaptiveSpace;
			AtString subdivUVSmoothing;
			bool subdividePolygons;
			bool subdivSmoothDerivs;
			bool subdivFrustumIgnore;

			void hash( bool meshInterpolationIsLinear, IECore::MurmurHash &h ) const
			{
				if( !meshInterpolationIsLinear || subdividePolygons )
				{
					h.append( subdivIterations );
					h.append( subdivAdaptiveError );
					h.append( subdivAdaptiveMetric.c_str() );
					h.append( subdivAdaptiveSpace.c_str() );
					h.append( subdivUVSmoothing.c_str() );
					h.append( subdivSmoothDerivs );
					h.append( subdivFrustumIgnore );
				}
			}

			void apply( const IECoreScene::MeshPrimitive *mesh, AtNode *node ) const
			{
				if( mesh->interpolation() != "linear" || subdividePolygons )
				{
					AiNodeSetByte( node, g_subdivIterationsArnoldString, subdivIterations );
					AiNodeSetFlt( node, g_subdivAdaptiveErrorArnoldString, subdivAdaptiveError );
					AiNodeSetStr( node, g_subdivAdaptiveMetricArnoldString, subdivAdaptiveMetric );
					AiNodeSetStr( node, g_subdivAdaptiveSpaceArnoldString, subdivAdaptiveSpace );
					AiNodeSetStr( node, g_subdivUVSmoothingArnoldString, subdivUVSmoothing );
					AiNodeSetBool( node, g_subdivSmoothDerivsArnoldString, subdivSmoothDerivs );
					AiNodeSetBool( node, g_subdivFrustumIgnoreArnoldString, subdivFrustumIgnore );
					if( mesh->interpolation() == "linear" )
					{
						AiNodeSetStr( node, g_subdivTypeArnoldString, g_linearArnoldString );
					}
				}
			}

		};

		struct Displacement
		{

			Displacement( const IECore::CompoundObject *attributes, ShaderCache *shaderCache )
			{
				if( const IECoreScene::ShaderNetwork *mapAttribute = attribute<IECoreScene::ShaderNetwork>( g_dispMapAttributeName, attributes ) )
				{
					map = shaderCache->get( mapAttribute, attributes );
				}
				height = attributeValue<float>( g_dispHeightAttributeName, attributes, 1.0f );
				padding = attributeValue<float>( g_dispPaddingAttributeName, attributes, 0.0f );
				zeroValue = attributeValue<float>( g_dispZeroValueAttributeName, attributes, 0.0f );
				autoBump = attributeValue<bool>( g_dispAutoBumpAttributeName, attributes, false );
				autoBumpVisibility = AI_RAY_CAMERA;
				updateVisibility( autoBumpVisibility, g_cameraVisibilityAutoBumpAttributeName, AI_RAY_CAMERA, attributes );
				updateVisibility( autoBumpVisibility, g_diffuseReflectVisibilityAutoBumpAttributeName, AI_RAY_DIFFUSE_REFLECT, attributes );
				updateVisibility( autoBumpVisibility, g_specularReflectVisibilityAutoBumpAttributeName, AI_RAY_SPECULAR_REFLECT, attributes );
				updateVisibility( autoBumpVisibility, g_diffuseTransmitVisibilityAutoBumpAttributeName, AI_RAY_DIFFUSE_TRANSMIT, attributes );
				updateVisibility( autoBumpVisibility, g_specularTransmitVisibilityAutoBumpAttributeName, AI_RAY_SPECULAR_TRANSMIT, attributes );
				updateVisibility( autoBumpVisibility, g_volumeVisibilityAutoBumpAttributeName, AI_RAY_VOLUME, attributes );
				updateVisibility( autoBumpVisibility, g_subsurfaceVisibilityAutoBumpAttributeName, AI_RAY_SUBSURFACE, attributes );
			}

			ArnoldShaderPtr map;
			float height;
			float padding;
			float zeroValue;
			bool autoBump;
			unsigned char autoBumpVisibility;

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
				h.append( autoBumpVisibility );
			}

			void apply( AtNode *node ) const
			{
				if( map && map->root() )
				{
					AiNodeSetPtr( node, g_dispMapArnoldString, map->root() );
				}
				else
				{
					AiNodeResetParameter( node, g_dispMapArnoldString );
				}

				AiNodeSetFlt( node, g_dispHeightArnoldString, height );
				AiNodeSetFlt( node, g_dispPaddingArnoldString, padding );
				AiNodeSetFlt( node, g_dispZeroValueArnoldString, zeroValue );
				AiNodeSetBool( node, g_dispAutoBumpArnoldString, autoBump );
				AiNodeSetByte( node, g_autobumpVisibilityArnoldString, autoBumpVisibility );
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
				AiNodeSetFlt( node, g_minPixelWidthArnoldString, minPixelWidth );
				if( thick )
				{
					AiNodeSetStr( node, g_modeArnoldString, g_thickArnoldString );
				}
			}

		};

		struct Volume
		{
			Volume( const IECore::CompoundObject *attributes )
			{
				volumeGrids = attribute<IECore::StringVectorData>( g_volumeGridsAttributeName, attributes );
				velocityGrids = attribute<IECore::StringVectorData>( g_velocityGridsAttributeName, attributes );
				velocityScale = optionalAttribute<float>( g_velocityScaleAttributeName, attributes );
				velocityFPS = optionalAttribute<float>( g_velocityFPSAttributeName, attributes );
				velocityOutlierThreshold = optionalAttribute<float>( g_velocityOutlierThresholdAttributeName, attributes );
				stepSize = optionalAttribute<float> ( g_volumeStepSizeAttributeName, attributes );
				stepScale = optionalAttribute<float>( g_volumeStepScaleAttributeName, attributes );
			}

			IECore::ConstStringVectorDataPtr volumeGrids;
			IECore::ConstStringVectorDataPtr velocityGrids;
			std::optional<float> velocityScale;
			std::optional<float> velocityFPS;
			std::optional<float> velocityOutlierThreshold;
			std::optional<float> stepSize;
			std::optional<float> stepScale;

			void hash( IECore::MurmurHash &h ) const
			{
				if( volumeGrids )
				{
					volumeGrids->hash( h );
				}

				if( velocityGrids )
				{
					velocityGrids->hash( h );
				}

				h.append( velocityScale.value_or( 1.0f ) );
				h.append( velocityFPS.value_or( 24.0f ) );
				h.append( velocityOutlierThreshold.value_or( 0.001f ) );
				h.append( stepSize.value_or( 0.0f ) );
				h.append( stepScale.value_or( 1.0f ) );
			}

			void apply( AtNode *node ) const
			{
				if( volumeGrids && volumeGrids->readable().size() )
				{
					AtArray *array = ParameterAlgo::dataToArray( volumeGrids.get(), AI_TYPE_STRING );
					AiNodeSetArray( node, g_volumeGridsArnoldString, array );
				}

				if( velocityGrids && velocityGrids->readable().size() )
				{
					AtArray *array = ParameterAlgo::dataToArray( velocityGrids.get(), AI_TYPE_STRING );
					AiNodeSetArray( node, g_velocityGridsArnoldString, array );
				}

				if( !velocityScale || velocityScale.value() > 0 )
				{
					AtNode *options = AiUniverseGetOptions( AiNodeGetUniverse( node ) );
					const AtNode *arnoldCamera = static_cast<const AtNode *>( AiNodeGetPtr( options, g_cameraArnoldString ) );

					if( arnoldCamera )
					{
						float shutterStart = AiNodeGetFlt( arnoldCamera, g_shutterStartArnoldString );
						float shutterEnd = AiNodeGetFlt( arnoldCamera, g_shutterEndArnoldString );

						// We're getting very lucky here:
						//  - Arnold has automatically set options.camera the first time we made a camera
						//  - All cameras output by Gaffer at present will have the same shutter,
						//    so it doesn't matter if we get it from the final render camera or not.
						AiNodeSetFlt( node, g_motionStartArnoldString, shutterStart );
						AiNodeSetFlt( node, g_motionEndArnoldString, shutterEnd );
					}
				}

				if( velocityScale )
				{
					AiNodeSetFlt( node, g_velocityScaleArnoldString, velocityScale.value() );
				}

				if( velocityFPS )
				{
					AiNodeSetFlt( node, g_velocityFPSArnoldString, velocityFPS.value() );
				}

				if( velocityOutlierThreshold )
				{
					AiNodeSetFlt( node, g_velocityOutlierThresholdArnoldString, velocityOutlierThreshold.value() );
				}

				if ( stepSize )
				{
					AiNodeSetFlt( node, g_stepSizeArnoldString, stepSize.value() * stepScale.value_or( 1.0f ) );
				}
				else if ( stepScale )
				{
					AiNodeSetFlt( node, g_stepScaleArnoldString, stepScale.value() );
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
			using DataType = IECore::TypedData<T>;
			const DataType *data = attribute<DataType>( name, attributes );
			return data ? data->readable() : defaultValue;
		}

		template<typename T>
		static std::optional<T> optionalAttribute( const IECore::InternedString &name, const IECore::CompoundObject *attributes )
		{
			using DataType = IECore::TypedData<T>;
			const DataType *data = attribute<DataType>( name, attributes );
			return data ? data->readable() : std::optional<T>();
		}

		static void updateVisibility( unsigned char &visibility, const IECore::InternedString &name, unsigned char rayType, const IECore::CompoundObject *attributes )
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
			switch( (int)objectType )
			{
				case IECoreScene::MeshPrimitiveTypeId :
					m_polyMesh.hash( meshInterpolationIsLinear, h );
					m_displacement.hash( h );
					h.append( m_stepSize );
					h.append( m_stepScale );
					h.append( m_volumePadding );
					break;
				case IECoreScene::CurvesPrimitiveTypeId :
					m_curves.hash( h );
					break;
				case IECoreScene::SpherePrimitiveTypeId :
					h.append( m_stepSize );
					h.append( m_stepScale );
					h.append( m_volumePadding );
					break;
				case IECoreScene::ExternalProceduralTypeId :
					if( proceduralIsVolumetric )
					{
						h.append( m_stepSize );
						h.append( m_stepScale );
						h.append( m_volumePadding );

						m_volume.hash( h );
					}
					break;
				case IECoreVDB::VDBObjectTypeId :
					h.append( m_volumePadding );
					m_volume.hash( h );
					break;
				default :
					if(
						objectType == (IECore::TypeId)GafferScene::PreviewProceduralTypeId ||
						IECore::RunTimeTyped::inheritsFrom( objectType, (IECore::TypeId)GafferScene::PreviewProceduralTypeId )
					)
					{
						hashProceduralGeometry( h );
					}
					// No geometry attributes for this type.
					break;
			}
		}

		template<typename T>
		void hashOptional( const T *t, IECore::MurmurHash &h ) const
		{
			if( t )
			{
				t->hash( h );
			}
			else
			{
				h.append( 0 );
			}
		}

		void hashProceduralGeometry( IECore::MurmurHash &h ) const
		{
			// Everything except custom attributes affects procedurals,
			// because we have to manually inherit attributes by
			// applying them to the child nodes of the procedural.
			h.append( m_visibility );
			h.append( m_sidedness );
			h.append( m_shadingFlags );
			hashOptional( m_surfaceShader.get(), h );
			hashOptional( m_filterMap.get(), h );
			hashOptional( m_uvRemap.get(), h );
			hashOptional( m_lightShader.get(), h );
			hashOptional( m_lightFilterShader.get(), h );
			for( const auto &s : m_lightFilterShaders )
			{
				s->hash( h );
			}
			hashOptional( m_traceSets.get(), h );
			hashOptional( m_transformType.get(), h );
			h.append( m_stepSize );
			h.append( m_stepScale );
			h.append( m_volumePadding );
			m_polyMesh.hash( true, h );
			m_polyMesh.hash( false, h );
			m_displacement.hash( h );
			m_curves.hash( h );
			m_volume.hash( h );
			hashOptional( m_toonId.get(), h );
			hashOptional( m_sssSetName.get(), h );
		}

		unsigned char m_visibility;
		unsigned char m_sidedness;
		unsigned char m_shadingFlags;
		ArnoldShaderPtr m_surfaceShader;
		ArnoldShaderPtr m_filterMap;
		ArnoldShaderPtr m_uvRemap;
		IECoreScene::ConstShaderNetworkPtr m_lightShader;
		IECoreScene::ConstShaderNetworkPtr m_lightFilterShader;
		std::vector<ArnoldShaderPtr> m_lightFilterShaders;
		IECore::ConstInternedStringVectorDataPtr m_traceSets;
		IECore::ConstStringDataPtr m_transformType;
		float m_stepSize;
		float m_stepScale;
		float m_volumePadding;
		PolyMesh m_polyMesh;
		Displacement m_displacement;
		Curves m_curves;
		Volume m_volume;
		IECore::ConstStringDataPtr m_toonId;
		IECore::ConstStringDataPtr m_sssSetName;
		// When adding fields, please update `hashProceduralGeometry()`!

		// AtString defines implicit cast to a (uniquefied) `const char *`,
		// and that is sufficient for the default `std::less<AtString>`
		// comparison.
		using CustomAttributes = boost::container::flat_map<AtString, IECore::ConstDataPtr>;
		CustomAttributes m_custom;

		// The original attributes we were contructed from. We stash
		// these so that they can be inherited manually when expanding
		// procedurals.
		/// \todo Instead of storing this, can be instead copy/update
		/// the fields above directly when emulating inheritance? We are
		/// avoiding that for now because it would mean child nodes of the
		/// procedural referencing shaders etc generated outside of the
		/// procedural. We saw crashes in Arnold when attempting that in the
		/// past, but have been told by the developers since that it should
		/// be supported.
		IECore::ConstCompoundObjectPtr m_allAttributes;

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
			else
			{
				// Technically the node was created in `InstanceCache.get()`
				// rather than by us directly, but we are the sole owner and
				// this is the most natural place to report the creation.
				nodes.push_back( m_node.get() );
			}
		}

	private :

		// Constructors are private as they are only intended for use in
		// `InstanceCache::get()`. See comment in `nodesCreated()`.
		friend class InstanceCache;

		// Non-instanced
		Instance( const SharedAtNodePtr &node )
			:	m_node( node )
		{
		}

		// Instanced
		Instance( const SharedAtNodePtr &node, NodeDeleter nodeDeleter, AtUniverse *universe, const std::string &instanceName, const AtNode *parent )
			:	m_node( node )
		{
			if( node )
			{
				AiNodeSetByte( node.get(), g_visibilityArnoldString, 0 );
				m_ginstance = SharedAtNodePtr(
					AiNode( universe, g_ginstanceArnoldString, AtString( instanceName.c_str() ), parent ),
					nodeDeleter
				);
				AiNodeSetPtr( m_ginstance.get(), g_nodeArnoldString, m_node.get() );
			}
		}

		SharedAtNodePtr m_node;
		SharedAtNodePtr m_ginstance;

};

// Forward declaration
AtNode *convertProcedural( IECoreScenePreview::ConstProceduralPtr procedural, const ArnoldAttributes *attributes, AtUniverse *universe, const std::string &nodeName, AtNode *parentNode );

class InstanceCache : public IECore::RefCounted
{

	public :

		InstanceCache( NodeDeleter nodeDeleter, AtUniverse *universe, AtNode *parentNode )
			:	m_nodeDeleter( nodeDeleter ), m_universe( universe ), m_parentNode( parentNode )
		{
		}

		// Can be called concurrently with other get() calls.
		Instance get( const IECore::Object *object, const IECoreScenePreview::Renderer::AttributesInterface *attributes, const std::string &nodeName )
		{
			const ArnoldAttributes *arnoldAttributes = static_cast<const ArnoldAttributes *>( attributes );

			if( !arnoldAttributes->canInstanceGeometry( object ) )
			{
				return Instance( convert( object, arnoldAttributes, nodeName ) );
			}

			IECore::MurmurHash h = object->hash();
			arnoldAttributes->hashGeometry( object, h );

			SharedAtNodePtr node;
			Cache::const_accessor readAccessor;
			if( m_cache.find( readAccessor, h ) )
			{
				node = readAccessor->second;
				readAccessor.release();
			}
			else
			{
				Cache::accessor writeAccessor;
				if( m_cache.insert( writeAccessor, h ) )
				{
					writeAccessor->second = convert( object, arnoldAttributes, "instance:" + h.toString() );
				}
				node = writeAccessor->second;
				writeAccessor.release();
			}

			return Instance( node, m_nodeDeleter, m_universe, nodeName, m_parentNode );
		}

		Instance get( const std::vector<const IECore::Object *> &samples, const std::vector<float> &times, const IECoreScenePreview::Renderer::AttributesInterface *attributes, const std::string &nodeName )
		{
			const ArnoldAttributes *arnoldAttributes = static_cast<const ArnoldAttributes *>( attributes );

			if( !arnoldAttributes->canInstanceGeometry( samples.front() ) )
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

			SharedAtNodePtr node;
			Cache::const_accessor readAccessor;
			if( m_cache.find( readAccessor, h ) )
			{
				node = readAccessor->second;
				readAccessor.release();
			}
			else
			{
				Cache::accessor writeAccessor;
				if( m_cache.insert( writeAccessor, h ) )
				{
					writeAccessor->second = convert( samples, times, arnoldAttributes, "instance:" + h.toString() );
				}
				node = writeAccessor->second;
				writeAccessor.release();
			}

			return Instance( node, m_nodeDeleter, m_universe, nodeName, m_parentNode );
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

		SharedAtNodePtr convert( const IECore::Object *object, const ArnoldAttributes *attributes, const std::string &nodeName )
		{
			if( !object )
			{
				return SharedAtNodePtr();
			}

			AtNode *node = nullptr;
			if( const IECoreScenePreview::Procedural *procedural = IECore::runTimeCast<const IECoreScenePreview::Procedural>( object ) )
			{
				node = convertProcedural( procedural, attributes, m_universe, nodeName, m_parentNode );
			}
			else
			{
				node = NodeAlgo::convert( object, m_universe, nodeName, m_parentNode );
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
			ensureUniformTimeSamples( times );
			AtNode *node = nullptr;
			if( const IECoreScenePreview::Procedural *procedural = IECore::runTimeCast<const IECoreScenePreview::Procedural>( samples.front() ) )
			{
				node = convertProcedural( procedural, attributes, m_universe, nodeName, m_parentNode );
			}
			else
			{
				node = NodeAlgo::convert( samples, times[0], times[times.size() - 1], m_universe, nodeName, m_parentNode );
			}

			if( !node )
			{
				return SharedAtNodePtr();
			}

			attributes->applyGeometry( samples.front(), node );

			return SharedAtNodePtr( node, m_nodeDeleter );

		}

		NodeDeleter m_nodeDeleter;
		AtUniverse *m_universe;
		AtNode *m_parentNode;

		using Cache = tbb::concurrent_hash_map<IECore::MurmurHash, SharedAtNodePtr>;
		Cache m_cache;

};

IE_CORE_DECLAREPTR( InstanceCache )

} // namespace

//////////////////////////////////////////////////////////////////////////
// ArnoldObject
//////////////////////////////////////////////////////////////////////////

namespace
{

IECore::InternedString g_surfaceAttributeName( "surface" );
IECore::InternedString g_aiSurfaceAttributeName( "ai:surface" );

IE_CORE_FORWARDDECLARE( ArnoldLight )

class ArnoldObjectBase : public IECoreScenePreview::Renderer::ObjectInterface
{

	public :

		ArnoldObjectBase( const Instance &instance )
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
			const ArnoldAttributes *arnoldAttributes = static_cast<const ArnoldAttributes *>( attributes );

			AtNode *node = m_instance.node();
			if( !node || arnoldAttributes->apply( node, m_attributes.get() ) )
			{
				m_attributes = arnoldAttributes;
				return true;
			}

			return false;
		}

		void link( const IECore::InternedString &type, const IECoreScenePreview::Renderer::ConstObjectSetPtr &objects ) override
		{
		}

		void assignID( uint32_t id ) override
		{
			if( AtNode *node = m_instance.node() )
			{
				/// \todo Ideally we might use the built-in `id` parameter here, rather
				/// than make our own. But Arnold's `user_data_int` shader can't query
				/// it for some reason.
				if( AiNodeDeclare( node, g_cortexIDArnoldString, "constant UINT" ) )
				{
					AiNodeSetUInt( node, g_cortexIDArnoldString, id );
				}
			}
		}

		const Instance &instance() const
		{
			return m_instance;
		}

	protected :

		void applyTransform( AtNode *node, const Imath::M44f &transform, const AtString matrixParameterName = g_matrixArnoldString )
		{
			AiNodeSetMatrix( node, matrixParameterName, reinterpret_cast<const AtMatrix&>( transform.x ) );
		}

		void applyTransform( AtNode *node, const std::vector<Imath::M44f> &samples, const std::vector<float> &times, const AtString matrixParameterName = g_matrixArnoldString )
		{
			const AtParamEntry *parameter = AiNodeEntryLookUpParameter( AiNodeGetNodeEntry( node ), matrixParameterName );
			if( AiParamGetType( parameter ) != AI_TYPE_ARRAY )
			{
				// Parameter doesn't support motion blur
				applyTransform( node, samples[0], matrixParameterName );
				return;
			}

			const size_t numSamples = samples.size();
			AtArray *matricesArray = AiArrayAllocate( 1, numSamples, AI_TYPE_MATRIX );
			for( size_t i = 0; i < numSamples; ++i )
			{
				AiArraySetMtx( matricesArray, i, reinterpret_cast<const AtMatrix&>( samples[i].x ) );
			}
			AiNodeSetArray( node, matrixParameterName, matricesArray );

			ensureUniformTimeSamples( times );
			AiNodeSetFlt( node, g_motionStartArnoldString, times[0] );
			AiNodeSetFlt( node, g_motionEndArnoldString, times[times.size() - 1] );

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
// ArnoldLightFilter
//////////////////////////////////////////////////////////////////////////

namespace
{

class ArnoldLightFilter : public ArnoldObjectBase
{

	public :

		ArnoldLightFilter( const std::string &name, const Instance &instance, NodeDeleter nodeDeleter, AtUniverse *universe, const AtNode *parentNode )
			:	ArnoldObjectBase( instance ), m_name( name ), m_nodeDeleter( nodeDeleter ), m_universe( universe ), m_parentNode( parentNode )
		{
		}

		~ArnoldLightFilter() override
		{
		}

		void transform( const Imath::M44f &transform ) override
		{
			ArnoldObjectBase::transform( transform );
			m_transformMatrices.clear();
			m_transformTimes.clear();
			m_transformMatrices.push_back( transform );
			applyLightFilterTransform();
		}

		void transform( const std::vector<Imath::M44f> &samples, const std::vector<float> &times ) override
		{
			ArnoldObjectBase::transform( samples, times );
			m_transformMatrices = samples;
			m_transformTimes = times;
			applyLightFilterTransform();
		}

		bool attributes( const IECoreScenePreview::Renderer::AttributesInterface *attributes ) override
		{
			if( !ArnoldObjectBase::attributes( attributes ) )
			{
				return false;
			}

			// Update light filter shader.

			if( m_attributes->lightFilterShader() )
			{
				if( !m_lightFilterShader )
				{
					m_lightFilterShader = new ArnoldShader( m_attributes->lightFilterShader(), m_nodeDeleter, m_universe, "lightFilter:" + m_name, m_parentNode );
					applyLightFilterTransform();
				}
				else
				{
					bool keptRootShader = m_lightFilterShader->update( m_attributes->lightFilterShader() );
					if( !keptRootShader )
					{
						// Couldn't update existing shader in place because the shader type
						// was changed. This will leave dangling pointers in any `filters` lists
						// held by lights. Return false to force the client to rebuild from
						// scratch.
						return false;
					}
				}
			}
			else
			{
				if( m_lightFilterShader )
				{
					// Removing `m_lightFilterShader` would create dangling pointers,
					// so we can not make the edit.
					return false;
				}
			}

			return true;
		}

		void nodesCreated( vector<AtNode *> &nodes ) const
		{
			if( m_lightFilterShader )
			{
				m_lightFilterShader->nodesCreated( nodes );
			}
		}

		ArnoldShader *lightFilterShader() const
		{
			return m_lightFilterShader.get();
		}

	private :

		void applyLightFilterTransform()
		{
			if( !m_lightFilterShader || m_transformMatrices.empty() )
			{
				return;
			}
			AtNode *root = m_lightFilterShader->root();
			if( m_transformTimes.empty() )
			{
				assert( m_transformMatrices.size() == 1 );
				applyTransform( root, m_transformMatrices[0], g_geometryMatrixArnoldString );
			}
			else
			{
				applyTransform( root, m_transformMatrices, m_transformTimes, g_geometryMatrixArnoldString );
			}
		}

		std::string m_name;
		vector<Imath::M44f> m_transformMatrices;
		vector<float> m_transformTimes;
		NodeDeleter m_nodeDeleter;
		AtUniverse *m_universe;
		const AtNode *m_parentNode;
		ArnoldShaderPtr m_lightFilterShader;

};

IE_CORE_DECLAREPTR( ArnoldLightFilter )

} // namespace

//////////////////////////////////////////////////////////////////////////
// ArnoldLight
//////////////////////////////////////////////////////////////////////////

namespace
{

IECore::InternedString g_lightFilters( "lightFilters" );

class ArnoldLight : public ArnoldObjectBase
{

	public :

		ArnoldLight( const std::string &name, const Instance &instance, NodeDeleter nodeDeleter, AtUniverse *universe, const AtNode *parentNode )
			:	ArnoldObjectBase( instance ), m_name( name ), m_nodeDeleter( nodeDeleter ), m_universe( universe ), m_parentNode( parentNode )
		{
		}

		~ArnoldLight() override
		{
		}

		void transform( const Imath::M44f &transform ) override
		{
			ArnoldObjectBase::transform( transform );
			m_transformMatrices.clear();
			m_transformTimes.clear();
			m_transformMatrices.push_back( transform );
			applyLightTransform();
		}

		void transform( const std::vector<Imath::M44f> &samples, const std::vector<float> &times ) override
		{
			ArnoldObjectBase::transform( samples, times );
			m_transformMatrices = samples;
			m_transformTimes = times;
			applyLightTransform();
		}

		bool attributes( const IECoreScenePreview::Renderer::AttributesInterface *attributes ) override
		{
			ConstArnoldAttributesPtr oldAttributes = m_attributes;
			if( !ArnoldObjectBase::attributes( attributes ) )
			{
				return false;
			}

			// Update light shader.

			if( m_attributes->lightShader() )
			{
				if( !m_lightShader )
				{
					m_lightShader = new ArnoldShader( m_attributes->lightShader(), m_nodeDeleter, m_universe, "light:" + m_name, m_parentNode );

					applyLightTransform();

					// Link mesh lights to the geometry held by ArnoldObjectBase.

					if( AiNodeIs( m_lightShader->root(), g_meshLightArnoldString ) )
					{
						if( m_instance.node() )
						{
							AiNodeSetPtr( m_lightShader->root(), g_meshArnoldString, m_instance.node() );
						}
						else
						{
							// Don't output mesh lights from locations with no object
							IECore::msg( IECore::Msg::Warning, "Arnold Render", "Mesh light without object at location: " + m_name );
							m_lightShader = nullptr;
						}
					}
				}
				else
				{
					const IECoreScene::Shader* lightOutput = m_attributes->lightShader()->outputShader();
					if( lightOutput && lightOutput->getName() == "quad_light" )
					{
						IECoreScene::ShaderNetwork::Parameter newColorParameter = m_attributes->lightShader()->getOutput();
						newColorParameter.name = "color";
						IECoreScene::ShaderNetwork::Parameter newColorInput = m_attributes->lightShader()->input( newColorParameter );

						IECoreScene::ShaderNetwork::Parameter oldColorParameter = oldAttributes->lightShader()->getOutput();
						oldColorParameter.name = "color";
						IECoreScene::ShaderNetwork::Parameter oldColorInput = oldAttributes->lightShader()->input( oldColorParameter );

						if( newColorInput && oldColorInput )
						{
							IECore::MurmurHash newColorHash, oldColorHash;
							hashShaderOutputParameter( m_attributes->lightShader(), newColorInput, newColorHash );
							hashShaderOutputParameter( oldAttributes->lightShader(), oldColorInput, oldColorHash );
							if( newColorHash != oldColorHash )
							{
								// Arnold currently fails to update quad light shaders during interactive renders
								// correctly.  ( At least when there is an edit to the color parameter, and it's
								// driven by a network which contains a texture. )
								// Until they fix this, we can just throw out and rebuild quad lights whenever
								// there's a change to a network driving color
								return false;
							}
						}
					}

					bool keptRootShader = m_lightShader->update( m_attributes->lightShader() );
					if( !keptRootShader )
					{
						// Couldn't update existing shader in place because the shader type
						// was changed. This will leave dangling pointers in any `light_group`
						// lists held by objects. Return false to force the client to rebuild from
						// scratch.
						return false;
					}
				}
			}
			else
			{
				if( m_lightShader )
				{
					// Removing `m_lightShader` would create dangling light linking pointers,
					// so we can not make the edit - the client must rebuild instead.
					return false;
				}
				else
				{
					// We're outputting a light that is invalid, output a warning about that
					IECore::msg( IECore::Msg::Warning, "Arnold Render", "Light without shader at location: " + m_name );
				}
			}

			// Update filter links if needed.

			if(
				( oldAttributes && oldAttributes->lightFilterShaders() != m_attributes->lightFilterShaders() ) ||
				( !oldAttributes && m_attributes->lightFilterShaders().size() )
			)
			{
				updateLightFilterLinks();
			}

			return true;
		}

		void link( const IECore::InternedString &type, const IECoreScenePreview::Renderer::ConstObjectSetPtr &lightFilters ) override
		{
			if( type != g_lightFilters || lightFilters == m_linkedLightFilters )
			{
				return;
			}

			m_linkedLightFilters = lightFilters;
			updateLightFilterLinks();
		}

		const ArnoldShader *lightShader() const
		{
			return m_lightShader.get();
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

		void updateLightFilterLinks()
		{
			if( !m_lightShader )
			{
				return;
			}

			auto &attributesLightFilters = m_attributes->lightFilterShaders();
			vector<AtNode *> lightFilterNodes;
			lightFilterNodes.reserve(
				( m_linkedLightFilters ? m_linkedLightFilters->size() : 0 ) + attributesLightFilters.size()
			);

			if( m_linkedLightFilters )
			{
				for( const auto &filter : *m_linkedLightFilters )
				{
					const ArnoldLightFilter *arnoldFilter = static_cast<const ArnoldLightFilter *>( filter.get() );
					if( arnoldFilter->lightFilterShader() )
					{
						lightFilterNodes.push_back( arnoldFilter->lightFilterShader()->root() );
					}
				}
			}

			for( const auto &filterShader : attributesLightFilters )
			{
				lightFilterNodes.push_back( filterShader->root() );
			}

			AiNodeSetArray(
				m_lightShader->root(), g_filtersArnoldString,
				AiArrayConvert( lightFilterNodes.size(), 1, AI_TYPE_NODE, lightFilterNodes.data() )
			);
		}

		// Because the AtNode for the light arrives via attributes(),
		// we need to store the transform and name ourselves so we have
		// them later when we need them.
		std::string m_name;
		vector<Imath::M44f> m_transformMatrices;
		vector<float> m_transformTimes;
		NodeDeleter m_nodeDeleter;
		AtUniverse *m_universe;
		const AtNode *m_parentNode;
		ArnoldShaderPtr m_lightShader;
		IECoreScenePreview::Renderer::ConstObjectSetPtr m_linkedLightFilters;

};

IE_CORE_DECLAREPTR( ArnoldLight )

} // namespace

//////////////////////////////////////////////////////////////////////////
// ArnoldObject
//////////////////////////////////////////////////////////////////////////

namespace
{

IECore::InternedString g_lights( "lights" );

class ArnoldObject : public ArnoldObjectBase
{

	public :

		ArnoldObject( const Instance &instance )
			:	ArnoldObjectBase( instance )
		{
		}

		~ArnoldObject() override
		{
		}

		void link( const IECore::InternedString &type, const IECoreScenePreview::Renderer::ConstObjectSetPtr &objects ) override
		{
			AtNode *node = m_instance.node();
			if( !node )
			{
				return;
			}

			AtString groupParameterName;
			AtString useParameterName;
			if( type == g_lights )
			{
				groupParameterName = g_lightGroupArnoldString;
				useParameterName = g_useLightGroupArnoldString;
			}
			else if( type == g_shadowGroup )
			{
				groupParameterName = g_shadowGroupArnoldString;
				useParameterName = g_useShadowGroupArnoldString;
			}
			else
			{
				return;
			}

			if( objects )
			{
				vector<AtNode *> lightNodes; lightNodes.reserve( objects->size() );
				for( const auto &o : *objects )
				{
					auto arnoldLight = dynamic_cast<const ArnoldLight *>( o.get() );
					if( arnoldLight && arnoldLight->lightShader() )
					{
						lightNodes.push_back( arnoldLight->lightShader()->root() );
					}
					else
					{
						if( !arnoldLight )
						{
							// Not aware of any way this could happen
							IECore::msg( IECore::Msg::Warning, "ArnoldObject::link()", "Attempt to link nonexistent light" );
						}
						else
						{
							// We have an ArnoldLight, but with an invalid lightShader.
							// It is the responsibility of ArnoldLight to output a warning when constructing in
							// an invalid state, so we don't need to warn here
						}
					}
				}

				AiNodeSetArray( node, groupParameterName, AiArrayConvert( lightNodes.size(), 1, AI_TYPE_NODE, lightNodes.data() ) );
				AiNodeSetBool( node, useParameterName, true );
			}
			else
			{
				AiNodeResetParameter( node, groupParameterName );
				AiNodeResetParameter( node, useParameterName );
			}
		}

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
		/// \todo Pass through the parent message hander so we can redirect
		/// IECore::msg message handlers here.
		ProceduralRenderer( AtNode *procedural, IECore::ConstCompoundObjectPtr attributesToInherit )
			:	ArnoldRendererBase( nullNodeDeleter, AiNodeGetUniverse( procedural ), procedural ),
				m_attributesToInherit( attributesToInherit )
		{
		}

		void option( const IECore::InternedString &name, const IECore::Object *value ) override
		{
			IECore::msg( IECore::Msg::Warning, "ArnoldRenderer", "Procedurals can not call option()" );
		}

		void output( const IECore::InternedString &name, const IECoreScene::Output *output ) override
		{
			IECore::msg( IECore::Msg::Warning, "ArnoldRenderer", "Procedurals can not call output()" );
		}

		ArnoldRendererBase::AttributesInterfacePtr attributes( const IECore::CompoundObject *attributes ) override
		{
			// Emulate attribute inheritance.
			IECore::CompoundObjectPtr fullAttributes = new IECore::CompoundObject;
			for( const auto &a : m_attributesToInherit->members() )
			{
				if( !customAttributeName( a.first.string() ) )
				{
					// We ignore custom attributes because they follow normal inheritance
					// in Arnold anyway. They will be written onto the `ginstance` node
					// referring to the procedural instead.
					fullAttributes->members()[a.first] = a.second;
				}
			}
			for( const auto &a : attributes->members() )
			{
				fullAttributes->members()[a.first] = a.second;
			}
			return ArnoldRendererBase::attributes( fullAttributes.get() );
		}

		ObjectInterfacePtr camera( const std::string &name, const IECoreScene::Camera *camera, const AttributesInterface *attributes ) override
		{
			IECore::msg( IECore::Msg::Warning, "ArnoldRenderer", "Procedurals can not call camera()" );
			return nullptr;
		}

		ObjectInterfacePtr camera( const std::string &name, const std::vector<const IECoreScene::Camera *> &samples, const std::vector<float> &times, const AttributesInterface *attributes ) override
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

		ObjectInterfacePtr lightFilter( const std::string &name, const IECore::Object *object, const AttributesInterface *attributes ) override
		{
			ArnoldLightFilterPtr result = static_pointer_cast<ArnoldLightFilter>(
				ArnoldRendererBase::lightFilter( name, object, attributes )
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

		void render() override
		{
			IECore::msg( IECore::Msg::Warning, "ArnoldRenderer", "Procedurals can not call render()" );
		}

		void pause() override
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

		IECore::ConstCompoundObjectPtr m_attributesToInherit;

		using NodesCreatedMutex = tbb::spin_mutex;
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
	ProceduralData *data = (ProceduralData *)( AiNodeGetPtr( node, g_userPtrArnoldString ) );
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

AtNode *convertProcedural( IECoreScenePreview::ConstProceduralPtr procedural, const ArnoldAttributes *attributes, AtUniverse *universe, const std::string &nodeName, AtNode *parentNode )
{
	AtNode *node = AiNode( universe, g_proceduralArnoldString, AtString( nodeName.c_str() ), parentNode );

	AiNodeSetPtr( node, g_funcPtrArnoldString, (void *)procFunc );

	ProceduralRendererPtr renderer = new ProceduralRenderer( node, attributes->allAttributes() );
	tbb::this_task_arena::isolate(
		// Isolate in case procedural spawns TBB tasks, because
		// `convertProcedural()` is called behind a lock in
		// `InstanceCache.get()`.
		[&]() {
			procedural->render( renderer.get() );
		}
	);

	ProceduralData *data = new ProceduralData;
	renderer->nodesCreated( data->nodesCreated );
	AiNodeSetPtr( node, g_userPtrArnoldString, data );

	return node;
}

bool isConvertedProcedural( const AtNode *node )
{
	return AiNodeIs( node, g_proceduralArnoldString ) && AiNodeGetPtr( node, g_funcPtrArnoldString ) == procFunc;
}

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
IECore::InternedString g_statisticsFileNameOptionName( "ai:statisticsFileName" );
IECore::InternedString g_profileFileNameOptionName( "ai:profileFileName" );
IECore::InternedString g_pluginSearchPathOptionName( "ai:plugin_searchpath" );
IECore::InternedString g_aaSeedOptionName( "ai:AA_seed" );
IECore::InternedString g_enableProgressiveRenderOptionName( "ai:enable_progressive_render" );
IECore::InternedString g_progressiveMinAASamplesOptionName( "ai:progressive_min_AA_samples" );
IECore::InternedString g_sampleMotionOptionName( "sampleMotion" );
IECore::InternedString g_atmosphereOptionName( "ai:atmosphere" );
IECore::InternedString g_backgroundOptionName( "ai:background" );
IECore::InternedString g_colorManagerOptionName( "ai:color_manager" );
IECore::InternedString g_subdivDicingCameraOptionName( "ai:subdiv_dicing_camera" );
IECore::InternedString g_imagerOptionName( "ai:imager" );
IECore::InternedString g_idAOVShaderOptionName( "ai:aov_shader:__cortexID" );

std::string g_logFlagsOptionPrefix( "ai:log:" );
std::string g_consoleFlagsOptionPrefix( "ai:console:" );

const int g_logFlagsDefault = AI_LOG_ALL;
const int g_consoleFlagsDefault = AI_LOG_WARNINGS | AI_LOG_ERRORS | AI_LOG_TIMESTAMP | AI_LOG_BACKTRACE | AI_LOG_MEMORY | AI_LOG_COLOR;

void throwError( int errorCode )
{
	switch( errorCode )
	{
		case AI_ABORT :
			throw IECore::Exception( "Render aborted" );
		case AI_ERROR_NO_CAMERA :
			throw IECore::Exception( "Camera not defined" );
		case AI_ERROR_BAD_CAMERA :
			throw IECore::Exception( "Bad camera" );
		case AI_ERROR_VALIDATION :
			throw IECore::Exception( "Usage not validated" );
		case AI_ERROR_RENDER_REGION :
			throw IECore::Exception( "Invalid render region" );
		case AI_INTERRUPT :
			throw IECore::Exception( "Render interrupted by user" );
		case AI_ERROR_NO_OUTPUTS :
			throw IECore::Exception( "No outputs" );
		case AI_ERROR :
			throw IECore::Exception( "Generic Arnold error" );
	}
}

class ArnoldGlobals
{

	public :

		ArnoldGlobals( IECoreScenePreview::Renderer::RenderType renderType, const std::string &fileName, const IECore::MessageHandlerPtr &messageHandler )
			:	m_renderType( renderType ),
				m_universeBlock( new IECoreArnold::UniverseBlock( /* writable = */ true ) ),
				m_renderSession(
					AiRenderSession(
						m_universeBlock->universe(),
						renderType == IECoreScenePreview::Renderer::RenderType::Interactive ? AI_SESSION_INTERACTIVE : AI_SESSION_BATCH
					),
					&AiRenderSessionDestroy
				),
				m_messageHandler( messageHandler ),
				m_logFileFlags( g_logFlagsDefault ),
				m_consoleFlags( g_consoleFlagsDefault ),
				m_enableProgressiveRender( true ),
				m_shaderCache( new ShaderCache( nodeDeleter( renderType ), m_universeBlock->universe(), /* parentNode = */ nullptr ) ),
				m_renderBegun( false ),
				m_fileName( fileName )
		{
			// If we've been given a MessageHandler then we output to that and
			// turn off Arnold's console logging.
			if( m_messageHandler )
			{
				m_messageCallbackId = AiMsgRegisterCallback( &messageCallback, m_consoleFlags, this );
				AiMsgSetConsoleFlags( m_universeBlock->universe(), AI_LOG_NONE );
			}
			else
			{
				AiMsgSetConsoleFlags( m_universeBlock->universe(), m_consoleFlags );
			}

			AiMsgSetLogFileFlags( m_universeBlock->universe(), m_logFileFlags );
			// Get OSL shaders onto the shader searchpath.
			option( g_pluginSearchPathOptionName, new IECore::StringData( "" ) );
		}

		~ArnoldGlobals()
		{
			if( m_renderBegun )
			{
				AiRenderInterrupt( m_renderSession.get(), AI_BLOCKING );
				AiRenderEnd( m_renderSession.get() );
			}

			// Delete nodes we own before universe is destroyed.
			m_shaderCache.reset();
			m_outputs.clear();
			m_aovShaders.clear();
			m_colorManager.reset();
			m_atmosphere.reset();
			m_background.reset();
			m_imager.reset();
			m_defaultCamera.reset();
			// Destroy the universe while our message callback is
			// still active, so we catch any Arnold shutdown messages.
			m_renderSession.reset( nullptr );
			m_universeBlock.reset( nullptr );

			if( m_messageCallbackId )
			{
				AiMsgDeregisterCallback( *m_messageCallbackId );
			}
		}

		AtUniverse *universe() { return m_universeBlock->universe(); }

		void option( const IECore::InternedString &name, const IECore::Object *value )
		{
			AtNode *options = AiUniverseGetOptions( m_universeBlock->universe() );
			if( name == g_frameOptionName )
			{
				if( value == nullptr )
				{
					m_frame = std::nullopt;
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
			else if( name == g_subdivDicingCameraOptionName )
			{
				if( value == nullptr )
				{
					m_subdivDicingCameraName = "";
				}
				else if( const IECore::StringData *d = reportedCast<const IECore::StringData>( value, "option", name ) )
				{
					m_subdivDicingCameraName = d->readable();

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
					/// \todo Arnold only has one global log file, but we want
					/// one per renderer.
					AiMsgSetLogFileName( d->readable().c_str() );
				}
				return;
			}
			else if( name == g_statisticsFileNameOptionName )
			{
				AiStatsSetMode( AI_STATS_MODE_OVERWRITE );

				if( value == nullptr )
				{
					AiStatsSetFileName( "" );
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
					AiStatsSetFileName( d->readable().c_str() );

				}
				return;
			}
			else if( name == g_profileFileNameOptionName )
			{
				if( value == nullptr )
				{
					AiProfileSetFileName( "" );
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

					AiProfileSetFileName( d->readable().c_str() );
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
				if( updateLogFlags( name.string().substr( g_logFlagsOptionPrefix.size() ), IECore::runTimeCast<const IECore::Data>( value ), /* console = */ false ) )
				{
					return;
				}
			}
			else if( boost::starts_with( name.c_str(), g_consoleFlagsOptionPrefix ) )
			{
				if( updateLogFlags( name.string().substr( g_consoleFlagsOptionPrefix.size() ), IECore::runTimeCast<const IECore::Data>( value ), /* console = */ true ) )
				{
					return;
				}
			}
			else if( name == g_enableProgressiveRenderOptionName )
			{
				if( value == nullptr )
				{
					m_enableProgressiveRender = true;
				}
				else if( auto d = reportedCast<const IECore::BoolData>( value, "option", name ) )
				{
					m_enableProgressiveRender = d->readable();
				}
				return;
			}
			else if( name == g_progressiveMinAASamplesOptionName )
			{
				if( value == nullptr )
				{
					m_progressiveMinAASamples = std::nullopt;
				}
				else if( const IECore::IntData *d = reportedCast<const IECore::IntData>( value, "option", name ) )
				{
					m_progressiveMinAASamples = d->readable();
				}
				return;
			}
			else if( name == g_aaSeedOptionName )
			{
				if( value == nullptr )
				{
					m_aaSeed = std::nullopt;
				}
				else if( const IECore::IntData *d = reportedCast<const IECore::IntData>( value, "option", name ) )
				{
					m_aaSeed = d->readable();
				}
				return;
			}
			else if( name == g_sampleMotionOptionName )
			{
				bool sampleMotion = true;
				if( value )
				{
					if( const IECore::BoolData *d = reportedCast<const IECore::BoolData>( value, "option", name ) )
					{
						sampleMotion = d->readable();
					}
				}
				AiNodeSetBool( options, g_ignoreMotionBlurArnoldString, !sampleMotion );
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
				AiNodeSetStr( options, g_pluginSearchPathArnoldString, AtString( s.c_str() ) );
				return;
			}
			else if( name == g_colorManagerOptionName )
			{
				m_colorManager = nullptr;
				if( value )
				{
					if( const IECoreScene::ShaderNetwork *d = reportedCast<const IECoreScene::ShaderNetwork>( value, "option", name ) )
					{
						m_colorManager = m_shaderCache->get( d, nullptr );
					}
				}
				AiNodeSetPtr( options, g_colorManagerArnoldString, m_colorManager ? m_colorManager->root() : nullptr );
				return;
			}
			else if( name == g_atmosphereOptionName )
			{
				m_atmosphere = nullptr;
				if( value )
				{
					if( const IECoreScene::ShaderNetwork *d = reportedCast<const IECoreScene::ShaderNetwork>( value, "option", name ) )
					{
						m_atmosphere = m_shaderCache->get( d, nullptr );
					}
				}
				AiNodeSetPtr( options, g_atmosphereArnoldString, m_atmosphere ? m_atmosphere->root() : nullptr );
				return;
			}
			else if( name == g_backgroundOptionName )
			{
				m_background = nullptr;
				if( value )
				{
					if( const IECoreScene::ShaderNetwork *d = reportedCast<const IECoreScene::ShaderNetwork>( value, "option", name ) )
					{
						m_background = m_shaderCache->get( d, nullptr );
					}
				}
				AiNodeSetPtr( options, g_backgroundArnoldString, m_background ? m_background->root() : nullptr );
				return;
			}
			else if( name == g_imagerOptionName )
			{
				m_imager = nullptr;
				if( value )
				{
					if( const IECoreScene::ShaderNetwork *d = reportedCast<const IECoreScene::ShaderNetwork>( value, "option", name ) )
					{
						m_imager = m_shaderCache->get( d, nullptr );
					}
				}
				for( const auto &output : m_outputs )
				{
					output.second->updateImager( m_imager ? m_imager->root() : nullptr );
				}
				return;
			}
			else if( boost::starts_with( name.c_str(), "ai:aov_shader:" ) )
			{
				m_aovShaders.erase( name );
				if( value )
				{
					if( const IECoreScene::ShaderNetwork *d = reportedCast<const IECoreScene::ShaderNetwork>( value, "option", name ) )
					{
						m_aovShaders[name] = m_shaderCache->get( d, nullptr );
					}
				}

				AtArray *array = AiArrayAllocate( m_aovShaders.size(), 1, AI_TYPE_NODE );
				int i = 0;
				for( AOVShaderMap::const_iterator it = m_aovShaders.begin(); it != m_aovShaders.end(); ++it )
				{
					AiArraySetPtr( array, i++, it->second->root() );
				}
				AiNodeSetArray( options, g_aovShadersArnoldString, array );
				return;
			}
			else if( boost::starts_with( name.c_str(), "ai:declare:" ) )
			{
				AtString arnoldName( name.c_str() + 11 );
				const AtParamEntry *parameter = AiNodeEntryLookUpParameter( AiNodeGetNodeEntry( options ), arnoldName );
				if( parameter )
				{
					IECore::msg( IECore::Msg::Warning, "IECoreArnold::Renderer::option", boost::format( "Unable to declare existing option \"%s\"." ) % arnoldName.c_str() );
				}
				else
				{
					const AtUserParamEntry *userParameter = AiNodeLookUpUserParameter( options, arnoldName );
					if( userParameter )
					{
						AiNodeResetParameter( options, arnoldName );
					}
					const IECore::Data *dataValue = IECore::runTimeCast<const IECore::Data>( value );
					if( dataValue )
					{
						ParameterAlgo::setParameter( options, arnoldName, dataValue );
					}
				}
				return;
			}
			else if( boost::starts_with( name.c_str(), "ai:" ) )
			{
				if( name == "ai:ignore_motion_blur" )
				{
					IECore::msg( IECore::Msg::Warning, "IECoreArnold::Renderer::option", boost::format( "ai:ignore_motion_blur is not supported directly - set generic Gaffer option sampleMotion to False to control this option." ) );
					return;
				}
				AtString arnoldName( name.c_str() + 3 );
				const AtParamEntry *parameter = AiNodeEntryLookUpParameter( AiNodeGetNodeEntry( options ), arnoldName );
				if( parameter )
				{
					const IECore::Data *dataValue = IECore::runTimeCast<const IECore::Data>( value );
					if( dataValue )
					{
						ParameterAlgo::setParameter( options, arnoldName, dataValue );
					}
					else
					{
						AiNodeResetParameter( options, arnoldName );
					}
					return;
				}
			}
			else if( boost::starts_with( name.c_str(), "user:" ) )
			{
				AtString arnoldName( name.c_str() );
				const IECore::Data *dataValue = IECore::runTimeCast<const IECore::Data>( value );
				if( dataValue )
				{
					ParameterAlgo::setParameter( options, arnoldName, dataValue );
				}
				else
				{
					AiNodeResetParameter( options, arnoldName );
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

		void output( const IECore::InternedString &name, const IECoreScene::Output *output )
		{
			m_outputs.erase( name );
			if( output )
			{
				try
				{
					ArnoldOutputPtr o = new ArnoldOutput( m_universeBlock->universe(), name, output, nodeDeleter( m_renderType ) );
					o->updateImager( m_imager ? m_imager->root() : nullptr );
					m_outputs[name] = o;
				}
				catch( const std::exception &e )
				{
					IECore::msg( IECore::Msg::Warning, "IECoreArnold::Renderer::output", e.what() );
				}
			}

		}

		// Some of Arnold's globals come from camera parameters, so the
		// ArnoldRenderer calls this method to notify the ArnoldGlobals
		// of each camera as it is created.
		void camera( const std::string &name, IECoreScene::ConstCameraPtr camera )
		{
			m_cameras[name] = camera;
		}

		void render()
		{
			updateIDAOV();
			updateCameraMeshes();

			AtNode *options = AiUniverseGetOptions( m_universeBlock->universe() );

			AiNodeSetInt(
				options, g_aaSeedArnoldString,
				m_aaSeed.value_or( m_frame.value_or( 1 ) )
			);

			// Set the reference time, so that volume motion will use the correct reference
			AiNodeSetFlt(
				options, g_referenceTimeString,
				m_frame.value_or( 1 )
			);

			AtNode *dicingCamera = nullptr;
			if( m_subdivDicingCameraName.size() )
			{
				dicingCamera = AiNodeLookUpByName( m_universeBlock->universe(), AtString( m_subdivDicingCameraName.c_str() ) );
				if( !dicingCamera )
				{
					IECore::msg( IECore::Msg::Warning, "IECoreArnold::Renderer", "Could not find dicing camera named: " + m_subdivDicingCameraName );
				}
			}

			if( dicingCamera )
			{
				AiNodeSetPtr( options, g_subdivDicingCameraString, dicingCamera );
			}
			else
			{
				AiNodeResetParameter( options, g_subdivDicingCameraString );
			}

			m_shaderCache->clearUnused();

			// Do the appropriate render based on
			// m_renderType.
			switch( m_renderType )
			{
				case IECoreScenePreview::Renderer::Batch :
				{
					// Loop through all cameras referenced by any current outputs,
					// and do a render for each
					std::set<std::string> cameraOverrides;
					for( const auto &it : m_outputs )
					{
						cameraOverrides.insert( it.second->cameraOverride() );
					}

					for( const auto &cameraOverride : cameraOverrides )
					{
						updateCamera( cameraOverride.size() ? cameraOverride : m_cameraName );
						throwError( AiRender( m_renderSession.get() ) );
					}
					break;
				}
				case IECoreScenePreview::Renderer::SceneDescription : {
					// A scene file can only contain options to render from one camera,
					// so just use the default camera.
					updateCamera( m_cameraName );
					unique_ptr<AtParamValueMap, decltype(&AiParamValueMapDestroy)> params(
						AiParamValueMap(), AiParamValueMapDestroy
					);
					AiSceneWrite( m_universeBlock->universe(), m_fileName.c_str(), params.get() );
					break;
				}
				case IECoreScenePreview::Renderer::Interactive :
					// If we want to use Arnold's progressive refinement, we can't be constantly switching
					// the camera around, so just use the default camera
					if( m_renderBegun )
					{
						AiRenderInterrupt( m_renderSession.get(), AI_BLOCKING );
					}
					updateCamera( m_cameraName );

					// Set progressive options. This is a bit of a mess. There are two different
					// "progressive" modes in Arnold :
					//
					// 1. A series of throwaway low-sampling renders of increasing resolution.
					//    This is controlled by two render hints : `progressive` and
					//    `progressive_min_AA_samples`.
					// 2. Progressive sample-by-sample rendering of the final high quality image.
					//    This is controlled by `options.enable_progressive_render`, although
					//    SolidAngle don't recommend it be used for batch rendering.
					//
					// Technically these are orthogonal and could be used independently, but that
					// makes for a confusing array of options and the necessity of explaining the
					// two different versions of "progressive". Instead we enable #1 only when #2
					// is enabled.

					const int minAASamples = m_progressiveMinAASamples.value_or( -4 );
					// Must never set `progressive_min_AA_samples > -1`, as it'll get stuck and
					// Arnold will never let us set it back.
					AiRenderSetHintInt( m_renderSession.get(), AtString( "progressive_min_AA_samples" ), std::min( minAASamples, -1 ) );
					// It seems important to set `progressive` after `progressive_min_AA_samples`,
					// otherwise Arnold may ignore changes to the latter. Disable entirely for
					// `minAASamples == 0` to account for the workaround above.
					AiRenderSetHintBool( m_renderSession.get(), AtString( "progressive" ), m_enableProgressiveRender && minAASamples < 0 );
					AiNodeSetBool( AiUniverseGetOptions( m_universeBlock->universe() ), g_enableProgressiveRenderString, m_enableProgressiveRender );

					if( !m_renderBegun )
					{
						AiRenderBegin( m_renderSession.get(), AI_RENDER_MODE_CAMERA );

						// Arnold's AiRenderGetStatus is not particularly reliable - renders start up on a separate thread,
						// and the currently reported status may not include recent changes.  So instead, we track a basic
						// status flag for whether we are already rendering ourselves
						m_renderBegun = true;
					}
					else
					{
						AiRenderRestart( m_renderSession.get() );
					}
					break;
			}
		}

		void pause()
		{
			// We need to block here because pause() is used to make sure that the render isn't running
			// before performing IPR edits.
			AiRenderInterrupt( m_renderSession.get(), AI_BLOCKING );
		}

	private :

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
				if( m_messageCallbackId )
				{
					AiMsgSetCallbackMask( *m_messageCallbackId, flags );
				}
				else
				{
					AiMsgSetConsoleFlags( m_universeBlock->universe(), flags );
				}
			}
			else
			{
				AiMsgSetLogFileFlags( m_universeBlock->universe(), flags );
			}

			return true;
		}

		void updateCamera( const std::string &cameraName )
		{
			AtNode *options = AiUniverseGetOptions( m_universeBlock->universe() );

			// Set the global output list in the options to all outputs matching the current camera
			IECore::StringVectorDataPtr outputs = new IECore::StringVectorData;
			IECore::StringVectorDataPtr lpes = new IECore::StringVectorData;
			vector<int> interactiveIndices;
			for( OutputMap::const_iterator it = m_outputs.begin(), eIt = m_outputs.end(); it != eIt; ++it )
			{
				std::string outputCamera = it->second->cameraOverride();
				if( outputCamera == "" )
				{
					outputCamera = m_cameraName;
				}

				if( outputCamera == cameraName )
				{
					if( it->second->updateInteractively() )
					{
						interactiveIndices.push_back( outputs->writable().size() );
					}
					it->second->append( outputs->writable(), lpes->writable() );
				}
			}

			AiRenderRemoveAllInteractiveOutputs( m_renderSession.get() );

			IECoreArnold::ParameterAlgo::setParameter( options, "outputs", outputs.get() );
			IECoreArnold::ParameterAlgo::setParameter( options, "light_path_expressions", lpes.get() );

			for( auto i : interactiveIndices )
			{
				AiRenderAddInteractiveOutput( m_renderSession.get(), i );
			}

			const IECoreScene::Camera *cortexCamera;
			AtNode *arnoldCamera = AiNodeLookUpByName( m_universeBlock->universe(), AtString( cameraName.c_str() ) );
			if( arnoldCamera )
			{
				cortexCamera = m_cameras[cameraName].get();
				m_defaultCamera = nullptr;
			}
			else
			{
				if( !m_defaultCamera )
				{
					IECoreScene::ConstCameraPtr defaultCortexCamera = new IECoreScene::Camera();
					m_cameras["ieCoreArnold:defaultCamera"] = defaultCortexCamera;
					m_defaultCamera = SharedAtNodePtr(
						NodeAlgo::convert( defaultCortexCamera.get(), m_universeBlock->universe(), "ieCoreArnold:defaultCamera", nullptr ),
						nodeDeleter( m_renderType )
					);
				}
				cortexCamera = m_cameras["ieCoreArnold:defaultCamera"].get();
				arnoldCamera = m_defaultCamera.get();
			}
			AiNodeSetPtr( options, g_cameraArnoldString, arnoldCamera );

			Imath::V2i resolution = cortexCamera->renderResolution();
			Imath::Box2i renderRegion = cortexCamera->renderRegion();

			AiNodeSetInt( options, g_xresArnoldString, resolution.x );
			AiNodeSetInt( options, g_yresArnoldString, resolution.y );

			AiNodeSetFlt( options, g_pixelAspectRatioArnoldString, cortexCamera->getPixelAspectRatio() );

			if(
				renderRegion.min.x >= renderRegion.max.x ||
				renderRegion.min.y >= renderRegion.max.y
			)
			{
				// Arnold does not permit empty render regions.  The user intent of an empty render
				// region is probably to render as little as possible ( it could happen if you
				// built a tool to crop to an object which passed out of frame ).
				// We just pick one pixel in the corner
				renderRegion = Imath::Box2i( Imath::V2i( 0 ), Imath::V2i( 1 ) );
			}

			// Note that we have to flip Y and subtract 1 from the max value, because
			// renderRegion is stored in Gaffer image format ( +Y up and an exclusive upper bound )
			AiNodeSetInt( options, g_regionMinXArnoldString, renderRegion.min.x );
			AiNodeSetInt( options, g_regionMinYArnoldString, resolution.y - renderRegion.max.y );
			AiNodeSetInt( options, g_regionMaxXArnoldString, renderRegion.max.x - 1 );
			AiNodeSetInt( options, g_regionMaxYArnoldString, resolution.y - renderRegion.min.y - 1 );

			Imath::V2f shutter = cortexCamera->getShutter();
			AiNodeSetFlt( arnoldCamera, g_shutterStartArnoldString, shutter[0] );
			AiNodeSetFlt( arnoldCamera, g_shutterEndArnoldString, shutter[1] );
		}

		void updateCameraMeshes()
		{
			for( const auto &it : m_cameras )
			{
				IECoreScene::ConstCameraPtr cortexCamera = it.second;

				std::string meshPath = parameter( cortexCamera->parameters(), "mesh", std::string("") );
				if( !meshPath.size() )
				{
					continue;
				}

				AtNode *arnoldCamera = AiNodeLookUpByName( m_universeBlock->universe(), AtString( it.first.c_str() ) );
				if( !arnoldCamera )
				{
					continue;
				}

				AtNode *meshNode = AiNodeLookUpByName(  m_universeBlock->universe(), AtString( meshPath.c_str() ) );
				if( meshNode )
				{
					AtString meshType = AiNodeEntryGetNameAtString( AiNodeGetNodeEntry( meshNode ) );
					if( meshType == g_ginstanceArnoldString )
					{
						AiNodeSetPtr( arnoldCamera, g_meshArnoldString, AiNodeGetPtr( meshNode, g_nodeArnoldString ) );
						AiNodeSetMatrix( arnoldCamera, g_matrixArnoldString, AiNodeGetMatrix( meshNode, g_matrixArnoldString ) );
						continue;
					}
					else if( meshType == g_polymeshArnoldString )
					{
						AiNodeSetPtr( arnoldCamera, g_meshArnoldString, meshNode );
						AiNodeSetMatrix( arnoldCamera, g_matrixArnoldString, AiM4Identity() );
						continue;
					}
				}

				throw IECore::Exception( boost::str( boost::format( "While outputting camera \"%s\", could not find target mesh at \"%s\"" ) % it.first % meshPath ) );
			}
		}

		void updateIDAOV()
		{
			// Arnold actually declares a built in `ID` AOV, but it doesn't seem to
			// do anything. So we have to emulate one using an AOV shader of our own.
			// See related comments in `ArnoldObject::assignID().

			bool needAOV = false;
			for( const auto &output : m_outputs )
			{
				if( output.second->requiresIDAOV() )
				{
					needAOV = true;
					break;
				}
			}

			const bool haveAOV = m_aovShaders.find( g_idAOVShaderOptionName ) != m_aovShaders.end();
			if( needAOV && !haveAOV )
			{
				IECoreScene::ShaderNetworkPtr network = new IECoreScene::ShaderNetwork;
				network->addShader(
					"userData",
					new IECoreScene::Shader( "user_data_int", "ai:shader", { { "attribute", new IECore::StringData( "cortex:id" ) } } )
				);
				network->addShader(
					"aovWrite",
					new IECoreScene::Shader( "aov_write_int", "ai:shader", { { "aov_name", new IECore::StringData( "id" ) } })
				);
				network->addConnection( { { "userData", "" }, { "aovWrite", "aov_input" } } );
				network->setOutput( { "aovWrite", "" } );

				option( g_idAOVShaderOptionName, network.get() );
			}
			else if( !needAOV && haveAOV )
			{
				option( g_idAOVShaderOptionName, nullptr );
			}
		}

		static void messageCallback( int mask, int severity, const char *message, AtParamValueMap *metadata, void *userPtr )
		{
			const ArnoldGlobals *that = static_cast<ArnoldGlobals *>( userPtr );

			// We get given messages from all render sessions, but can filter them based on the `universe` metadata.
			void *universe = nullptr;
			if( AiParamValueMapGetPtr( metadata, g_universeArnoldString, &universe ) )
			{
				if( universe != that->m_universeBlock->universe() )
				{
					return;
				}
			}

			const IECore::Msg::Level level = \
				( mask == AI_LOG_DEBUG ) ? IECore::Msg::Level::Debug : g_ieMsgLevels[ min( severity, 3 ) ];

			std::stringstream msg;

			if( that->m_consoleFlags & AI_LOG_TIMESTAMP )
			{
				const boost::posix_time::time_duration elapsed = boost::posix_time::millisec( AiMsgUtilGetElapsedTime() );
				msg << std::setfill( '0' );
				msg << std::setw( 2 ) << elapsed.hours() << ":";
				msg << std::setw( 2 ) << elapsed.minutes() << ":";
				msg << std::setw( 2 ) << elapsed.seconds() << " ";
			}
			if( that->m_consoleFlags & AI_LOG_MEMORY )
			{
				const size_t mb = AiMsgUtilGetUsedMemory() / 1024 / 1024;
				msg << std::setfill( ' ' ) << std::setw( 4 );
				if( mb < 1024 )
				{
					msg << mb << "MB  ";
				}
				else
				{
					msg.setf( std::ios::fixed, std::ios::floatfield );
					msg << setprecision( 1 ) << ( float( mb ) / 1024.0f ) << "GB ";
				}
			}

			msg << message;

			that->m_messageHandler->handle( level, "Arnold", msg.str() );
		}

		static const std::vector<IECore::MessageHandler::Level> g_ieMsgLevels;

		// Members used by all render types

		IECoreScenePreview::Renderer::RenderType m_renderType;

		std::unique_ptr<UniverseBlock> m_universeBlock;
		std::unique_ptr<AtRenderSession, decltype(&AiRenderSessionDestroy)> m_renderSession;
		IECore::MessageHandlerPtr m_messageHandler;
		std::optional<unsigned> m_messageCallbackId;

		using OutputMap = std::map<std::string, ArnoldOutputPtr>;
		OutputMap m_outputs;

		using AOVShaderMap = std::map<IECore::InternedString, ArnoldShaderPtr>;
		AOVShaderMap m_aovShaders;

		ArnoldShaderPtr m_colorManager;
		ArnoldShaderPtr m_atmosphere;
		ArnoldShaderPtr m_background;
		ArnoldShaderPtr m_imager;

		std::string m_cameraName;
		using CameraMap = tbb::concurrent_unordered_map<std::string, IECoreScene::ConstCameraPtr>;
		CameraMap m_cameras;
		SharedAtNodePtr m_defaultCamera;
		std::string m_subdivDicingCameraName;

		int m_logFileFlags;
		int m_consoleFlags;
		std::optional<int> m_frame;
		std::optional<int> m_aaSeed;
		bool m_enableProgressiveRender;
		std::optional<int> m_progressiveMinAASamples;
		ShaderCachePtr m_shaderCache;

		bool m_renderBegun;

		// Members used by SceneDescription "renders"

		std::string m_fileName;

};

const std::vector<IECore::MessageHandler::Level> ArnoldGlobals::g_ieMsgLevels = {
	IECore::MessageHandler::Level::Info,
	IECore::MessageHandler::Level::Warning,
	IECore::MessageHandler::Level::Error,
	IECore::MessageHandler::Level::Error
};

} // namespace

//////////////////////////////////////////////////////////////////////////
// ArnoldRendererBase definition
//////////////////////////////////////////////////////////////////////////

namespace
{

ArnoldRendererBase::ArnoldRendererBase( NodeDeleter nodeDeleter, AtUniverse *universe, AtNode *parentNode, const IECore::MessageHandlerPtr &messageHandler )
	:	m_nodeDeleter( nodeDeleter ),
		m_universe( universe ),
		m_shaderCache( new ShaderCache( nodeDeleter, universe, parentNode ) ),
		m_instanceCache( new InstanceCache( nodeDeleter, universe, parentNode ) ),
		m_messageHandler( messageHandler ),
		m_parentNode( parentNode )
{
}

ArnoldRendererBase::~ArnoldRendererBase()
{
}

IECore::InternedString ArnoldRendererBase::name() const
{
	return "Arnold";
}

ArnoldRendererBase::AttributesInterfacePtr ArnoldRendererBase::attributes( const IECore::CompoundObject *attributes )
{
	const IECore::MessageHandler::Scope s( m_messageHandler.get() );

	return new ArnoldAttributes( attributes, m_shaderCache.get() );
}

ArnoldRendererBase::ObjectInterfacePtr ArnoldRendererBase::camera( const std::string &name, const IECoreScene::Camera *camera, const AttributesInterface *attributes )
{
	const IECore::MessageHandler::Scope s( m_messageHandler.get() );

	Instance instance = m_instanceCache->get( camera, attributes, name );

	ObjectInterfacePtr result = new ArnoldObject( instance );
	result->attributes( attributes );
	return result;
}

ArnoldRendererBase::ObjectInterfacePtr ArnoldRendererBase::camera( const std::string &name, const std::vector<const IECoreScene::Camera *> &samples, const std::vector<float> &times, const AttributesInterface *attributes )
{
	const IECore::MessageHandler::Scope s( m_messageHandler.get() );

	Instance instance = m_instanceCache->get( vector<const IECore::Object *>( samples.begin(), samples.end() ), times, attributes, name );

	ObjectInterfacePtr result = new ArnoldObject( instance );
	result->attributes( attributes );
	return result;
}

ArnoldRendererBase::ObjectInterfacePtr ArnoldRendererBase::light( const std::string &name, const IECore::Object *object, const AttributesInterface *attributes )
{
	const IECore::MessageHandler::Scope s( m_messageHandler.get() );

	Instance instance = m_instanceCache->get( object, attributes, name );
	ObjectInterfacePtr result = new ArnoldLight( name, instance, m_nodeDeleter, m_universe, m_parentNode );
	result->attributes( attributes );
	return result;
}

ArnoldRendererBase::ObjectInterfacePtr ArnoldRendererBase::lightFilter( const std::string &name, const IECore::Object *object, const AttributesInterface *attributes )
{
	const IECore::MessageHandler::Scope s( m_messageHandler.get() );

	Instance instance = m_instanceCache->get( object, attributes, name );
	ObjectInterfacePtr result = new ArnoldLightFilter( name, instance, m_nodeDeleter, m_universe, m_parentNode );
	result->attributes( attributes );

	return result;
}

ArnoldRendererBase::ObjectInterfacePtr ArnoldRendererBase::object( const std::string &name, const IECore::Object *object, const AttributesInterface *attributes )
{
	const IECore::MessageHandler::Scope s( m_messageHandler.get() );

	Instance instance = m_instanceCache->get( object, attributes, name );
	ObjectInterfacePtr result = new ArnoldObject( instance );
	result->attributes( attributes );
	return result;
}

ArnoldRendererBase::ObjectInterfacePtr ArnoldRendererBase::object( const std::string &name, const std::vector<const IECore::Object *> &samples, const std::vector<float> &times, const AttributesInterface *attributes )
{
	const IECore::MessageHandler::Scope s( m_messageHandler.get() );

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

		// Public constructor makes ArnoldGlobals and delegates to a private internal
		// constructor. This allows us to pass the universe from the globals to the
		// ArnoldRendererBase constructor.
		ArnoldRenderer( RenderType renderType, const std::string &fileName, const IECore::MessageHandlerPtr &messageHandler )
			:	ArnoldRenderer(
					nodeDeleter( renderType ),
					std::make_unique<ArnoldGlobals>( renderType, fileName, messageHandler ),
					messageHandler
				)
		{
		}

		~ArnoldRenderer() override
		{
			pause();
			// Delete cached nodes before universe is destroyed.
			m_instanceCache.reset( nullptr );
			m_shaderCache.reset( nullptr );
		}

		void option( const IECore::InternedString &name, const IECore::Object *value ) override
		{
			const IECore::MessageHandler::Scope s( m_messageHandler.get() );
			m_globals->option( name, value );
		}

		void output( const IECore::InternedString &name, const IECoreScene::Output *output ) override
		{
			const IECore::MessageHandler::Scope s( m_messageHandler.get() );
			m_globals->output( name, output );
		}

		ObjectInterfacePtr camera( const std::string &name, const IECoreScene::Camera *camera, const AttributesInterface *attributes ) override
		{
			const IECore::MessageHandler::Scope s( m_messageHandler.get() );

			m_globals->camera( name, camera );
			return ArnoldRendererBase::camera( name, camera, attributes );
		}

		ObjectInterfacePtr camera( const std::string &name, const std::vector<const IECoreScene::Camera *> &samples, const std::vector<float> &times, const AttributesInterface *attributes ) override
		{
			const IECore::MessageHandler::Scope s( m_messageHandler.get() );
			m_globals->camera( name, samples[0] );
			return ArnoldRendererBase::camera( name, samples, times, attributes );
		}

		void render() override
		{
			const IECore::MessageHandler::Scope s( m_messageHandler.get() );

			m_shaderCache->clearUnused();
			m_instanceCache->clearUnused();
			m_globals->render();
		}

		void pause() override
		{
			const IECore::MessageHandler::Scope s( m_messageHandler.get() );
			m_globals->pause();
		}

		IECore::DataPtr command( const IECore::InternedString name, const IECore::CompoundDataMap &parameters ) override
		{
			if( name == "ai:queryUniverse" )
			{
				// Provide access to the underlying `AtUniverse`, for debugging
				// and testing.
				return new IECore::UInt64Data( (uint64_t)m_universe );
			}
			else if( name == "ai:cacheFlush" )
			{
				const int flags = parameter<int>( parameters, "flags", AI_CACHE_ALL );
				AiUniverseCacheFlush( m_universe, flags );
				return nullptr;
			}
			else if( boost::starts_with( name.string(), "ai:" ) || name.string().find( ":" ) == string::npos )
			{
				IECore::msg( IECore::Msg::Warning, "IECoreArnold::Renderer::command", boost::format( "Unknown command \"%s\"." ) % name.c_str() );
			}

			return nullptr;
		}

	private :

		ArnoldRenderer( NodeDeleter nodeDeleter, std::unique_ptr<ArnoldGlobals> globals, const IECore::MessageHandlerPtr &messageHandler )
			:	ArnoldRendererBase( nodeDeleter, globals->universe(), /* parentNode = */ nullptr, messageHandler ),
				m_globals( std::move( globals ) )
		{
		}

		std::unique_ptr<ArnoldGlobals> m_globals;

		// Registration with factory

		static Renderer::TypeDescription<ArnoldRenderer> g_typeDescription;

};

IECoreScenePreview::Renderer::TypeDescription<ArnoldRenderer> ArnoldRenderer::g_typeDescription( "Arnold" );

} // namespace
