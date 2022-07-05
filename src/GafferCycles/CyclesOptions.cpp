//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2018, Alex Fuller. All rights reserved.
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

#include "GafferCycles/CyclesOptions.h"
#include "boost/algorithm/string.hpp"

// Cycles
IECORE_PUSH_DEFAULT_VISIBILITY
#include "device/device.h"
IECORE_POP_DEFAULT_VISIBILITY

using namespace Imath;
using namespace GafferCycles;

IE_CORE_DEFINERUNTIMETYPED( CyclesOptions );

CyclesOptions::CyclesOptions( const std::string &name )
	:	GafferScene::Options( name )
{
	Gaffer::CompoundDataPlug *options = optionsPlug();

	// Log
	options->addChild( new Gaffer::NameValuePlug( "ccl:log_level", new IECore::IntData( 0 ), false, "logLevel" ) );

	// Device
	options->addChild( new Gaffer::NameValuePlug( "ccl:device", new IECore::StringData( "CPU" ), false, "device" ) );

	// Session and scene
	options->addChild( new Gaffer::NameValuePlug( "ccl:shadingsystem", new IECore::StringData( "OSL" ), false, "shadingSystem" ) );

	// Session/Render
	options->addChild( new Gaffer::NameValuePlug( "ccl:session:experimental", new IECore::BoolData( false ), false, "featureSet" ) );
	options->addChild( new Gaffer::NameValuePlug( "ccl:session:samples", new IECore::IntData( 1024 ), false, "samples" ) );
	options->addChild( new Gaffer::NameValuePlug( "ccl:session:pixel_size", new IECore::IntData( 1 ), false, "pixelSize" ) );
	options->addChild( new Gaffer::NameValuePlug( "ccl:session:threads", new IECore::IntData( 0 ), false, "numThreads" ) );
	options->addChild( new Gaffer::NameValuePlug( "ccl:session:time_limit", new IECore::FloatData( 0.0f ), false, "timeLimit" ) );
	options->addChild( new Gaffer::NameValuePlug( "ccl:session:use_profiling", new IECore::BoolData( false ), false, "useProfiling" ) );
	options->addChild( new Gaffer::NameValuePlug( "ccl:session:use_auto_tile", new IECore::BoolData( true ), false, "useAutoTile" ) );
	options->addChild( new Gaffer::NameValuePlug( "ccl:session:tile_size", new IECore::IntData( 2048 ), false, "tileSize" ) );

	// Scene/BVH
	options->addChild( new Gaffer::NameValuePlug( "ccl:scene:bvh_layout", new IECore::StringData( "embree" ), false, "bvhLayout" ) );
	options->addChild( new Gaffer::NameValuePlug( "ccl:scene:use_bvh_spatial_split", new IECore::BoolData( false ), false, "useBvhSpatialSplit" ) );
	options->addChild( new Gaffer::NameValuePlug( "ccl:scene:use_bvh_unaligned_nodes", new IECore::BoolData( true ), false, "useBvhUnalignedNodes" ) );
	options->addChild( new Gaffer::NameValuePlug( "ccl:scene:num_bvh_time_steps", new IECore::IntData( 0 ), false, "numBvhTimeSteps" ) );
	options->addChild( new Gaffer::NameValuePlug( "ccl:scene:hair_subdivisions", new IECore::IntData( 3 ), false, "hairSubdivisions" ) );
	options->addChild( new Gaffer::NameValuePlug( "ccl:scene:hair_shape", new IECore::StringData( "thick" ), false, "hairShape" ) );
	options->addChild( new Gaffer::NameValuePlug( "ccl:scene:texture_limit", new IECore::IntData( 0 ), false, "textureLimit" ) );

	// Integrator
	options->addChild( new Gaffer::NameValuePlug( "ccl:integrator:min_bounce", new IECore::IntData( 0 ), false, "minBounce" ) );
	options->addChild( new Gaffer::NameValuePlug( "ccl:integrator:max_bounce", new IECore::IntData( 7 ), false, "maxBounce" ) );

	options->addChild( new Gaffer::NameValuePlug( "ccl:integrator:max_diffuse_bounce", new IECore::IntData( 7 ), false, "maxDiffuseBounce" ) );
	options->addChild( new Gaffer::NameValuePlug( "ccl:integrator:max_glossy_bounce", new IECore::IntData( 7 ), false, "maxGlossyBounce" ) );
	options->addChild( new Gaffer::NameValuePlug( "ccl:integrator:max_transmission_bounce", new IECore::IntData( 7 ), false, "maxTransmissionBounce" ) );
	options->addChild( new Gaffer::NameValuePlug( "ccl:integrator:max_volume_bounce", new IECore::IntData( 7 ), false, "maxVolumeBounce" ) );

	options->addChild( new Gaffer::NameValuePlug( "ccl:integrator:transparent_min_bounce", new IECore::IntData( 0 ), false, "transparentMinBounce" ) );
	options->addChild( new Gaffer::NameValuePlug( "ccl:integrator:transparent_max_bounce", new IECore::IntData( 7 ), false, "transparentMaxBounce" ) );

	options->addChild( new Gaffer::NameValuePlug( "ccl:integrator:ao_bounces", new IECore::IntData( 0 ), false, "aoBounces" ) );
	options->addChild( new Gaffer::NameValuePlug( "ccl:integrator:ao_factor", new IECore::FloatData( 0.0f ), false, "aoFactor" ) );
	options->addChild( new Gaffer::NameValuePlug( "ccl:integrator:ao_distance", new IECore::FloatData( FLT_MAX ), false, "aoDistance" ) );

	options->addChild( new Gaffer::NameValuePlug( "ccl:integrator:volume_max_steps", new IECore::IntData( 1024 ), false, "volumeMaxSteps" ) );
	options->addChild( new Gaffer::NameValuePlug( "ccl:integrator:volume_step_rate", new IECore::FloatData( 0.1f ), false, "volumeStepRate" ) );

	options->addChild( new Gaffer::NameValuePlug( "ccl:integrator:caustics_reflective", new IECore::BoolData( true ), false, "causticsReflective" ) );
	options->addChild( new Gaffer::NameValuePlug( "ccl:integrator:caustics_refractive", new IECore::BoolData( true ), false, "causticsRefractive" ) );
	options->addChild( new Gaffer::NameValuePlug( "ccl:integrator:filter_glossy", new IECore::FloatData( 0.0f ), false, "filterGlossy" ) );
	options->addChild( new Gaffer::NameValuePlug( "ccl:integrator:use_frame_as_seed", new IECore::BoolData( true ), false, "useFrameAsSeed" ) );
	options->addChild( new Gaffer::NameValuePlug( "ccl:integrator:seed", new IECore::IntData( 0 ), false, "seed" ) );
	options->addChild( new Gaffer::NameValuePlug( "ccl:integrator:sample_clamp_direct", new IECore::FloatData( 0.0f ), false, "sampleClampDirect" ) );
	options->addChild( new Gaffer::NameValuePlug( "ccl:integrator:sample_clamp_indirect", new IECore::FloatData( 0.0f ), false, "sampleClampIndirect" ) );

	options->addChild( new Gaffer::NameValuePlug( "ccl:integrator:start_sample", new IECore::IntData( 0 ), false, "startSample" ) );

	options->addChild( new Gaffer::NameValuePlug( "ccl:integrator:light_sampling_threshold", new IECore::FloatData( 0.05f ), false, "lightSamplingThreshold" ) );

	options->addChild( new Gaffer::NameValuePlug( "ccl:integrator:use_adaptive_sampling", new IECore::BoolData( false ), false, "useAdaptiveSampling" ) );
	options->addChild( new Gaffer::NameValuePlug( "ccl:integrator:adaptive_threshold", new IECore::FloatData( 0.0f ), false, "adaptiveThreshold" ) );
	options->addChild( new Gaffer::NameValuePlug( "ccl:integrator:adaptive_min_samples", new IECore::IntData( 0 ), false, "adaptiveMinSamples" ) );

	options->addChild( new Gaffer::NameValuePlug( "ccl:integrator:sampling_pattern", new IECore::StringData( "sobol" ), false, "samplingPattern" ) );

	options->addChild( new Gaffer::NameValuePlug( "ccl:integrator:denoiser_type", new IECore::StringData( "openimagedenoise" ), false, "denoiserType" ) );
	options->addChild( new Gaffer::NameValuePlug( "ccl:integrator:denoise_start_sample", new IECore::IntData( 0 ), false, "denoiseStartSample" ) );
	options->addChild( new Gaffer::NameValuePlug( "ccl:integrator:use_denoise_pass_albedo", new IECore::BoolData( true ), false, "useDenoisePassAlbedo" ) );
	options->addChild( new Gaffer::NameValuePlug( "ccl:integrator:use_denoise_pass_normal", new IECore::BoolData( true ), false, "useDenoisePassNormal" ) );
	options->addChild( new Gaffer::NameValuePlug( "ccl:integrator:denoiser_prefilter", new IECore::StringData( "accurate" ), false, "denoiserPrefilter" ) );

	// Background
	options->addChild( new Gaffer::NameValuePlug( "ccl:background:use_shader", new IECore::BoolData( true ), false, "bgUseShader" ) );

	options->addChild( new Gaffer::NameValuePlug( "ccl:background:visibility:camera", new IECore::BoolData( true ), false, "bgCameraVisibility" ) );
	options->addChild( new Gaffer::NameValuePlug( "ccl:background:visibility:diffuse", new IECore::BoolData( true ), false, "bgDiffuseVisibility" ) );
	options->addChild( new Gaffer::NameValuePlug( "ccl:background:visibility:glossy", new IECore::BoolData( true ), false, "bgGlossyVisibility" ) );
	options->addChild( new Gaffer::NameValuePlug( "ccl:background:visibility:transmission", new IECore::BoolData( true ), false, "bgTransmissionVisibility" ) );
	options->addChild( new Gaffer::NameValuePlug( "ccl:background:visibility:shadow", new IECore::BoolData( true ), false, "bgShadowVisibility" ) );
	options->addChild( new Gaffer::NameValuePlug( "ccl:background:visibility:scatter", new IECore::BoolData( true ), false, "bgScatterVisibility" ) );

	options->addChild( new Gaffer::NameValuePlug( "ccl:background:transparent", new IECore::BoolData( true ), false, "bgTransparent" ) );
	options->addChild( new Gaffer::NameValuePlug( "ccl:background:transparent_glass", new IECore::BoolData( false ), false, "bgTransparentGlass" ) );
	options->addChild( new Gaffer::NameValuePlug( "ccl:background:transparent_roughness_threshold", new IECore::FloatData( 0.0f ), false, "bgTransparentRoughnessThreshold" ) );

	options->addChild( new Gaffer::NameValuePlug( "ccl:background:volume_step_size", new IECore::FloatData( 0.1f ), false, "volumeStepSize" ) );

	// Film
	options->addChild( new Gaffer::NameValuePlug( "ccl:film:exposure", new IECore::FloatData( 1.0f ), false, "exposure" ) );
	options->addChild( new Gaffer::NameValuePlug( "ccl:film:pass_alpha_threshold", new IECore::FloatData( 0.5f ), false, "passAlphaThreshold" ) );

	options->addChild( new Gaffer::NameValuePlug( "ccl:film:display_pass", new IECore::StringData( "combined" ), false, "displayPass" ) );
	options->addChild( new Gaffer::NameValuePlug( "ccl:film:show_active_pixels", new IECore::BoolData( false ), false, "showActivePixels" ) );

	options->addChild( new Gaffer::NameValuePlug( "ccl:film:filter_type", new IECore::StringData( "box" ), false, "filterType" ) );
	options->addChild( new Gaffer::NameValuePlug( "ccl:film:filter_width", new IECore::FloatData( 1.0f ), false, "filterWidth" ) );

	options->addChild( new Gaffer::NameValuePlug( "ccl:film:mist_start", new IECore::FloatData( 0.0f ), false, "mistStart" ) );
	options->addChild( new Gaffer::NameValuePlug( "ccl:film:mist_depth", new IECore::FloatData( 100.0f ), false, "mistDepth" ) );
	options->addChild( new Gaffer::NameValuePlug( "ccl:film:mist_falloff", new IECore::FloatData( 1.0f ), false, "mistFalloff" ) );

	options->addChild( new Gaffer::NameValuePlug( "ccl:film:cryptomatte_accurate", new IECore::BoolData( false ), false, "cryptomatteAccurate" ) );
	options->addChild( new Gaffer::NameValuePlug( "ccl:film:cryptomatte_depth", new IECore::IntData( 6 ), false, "cryptomatteDepth" ) );

	// Dicing camera
	options->addChild( new Gaffer::NameValuePlug( "ccl:dicing_camera", new IECore::StringData(), false, "dicingCamera" ) );

	// Texture cache
	options->addChild( new Gaffer::NameValuePlug( "ccl:texture:use_texture_cache", new IECore::BoolData( false ), false, "useTextureCache" ) );
	options->addChild( new Gaffer::NameValuePlug( "ccl:texture:cache_size", new IECore::IntData( 1024 ), false, "textureCacheSize" ) );
	options->addChild( new Gaffer::NameValuePlug( "ccl:texture:auto_convert", new IECore::BoolData( true ), false, "textureAutoConvert" ) );
	options->addChild( new Gaffer::NameValuePlug( "ccl:texture:accept_unmipped", new IECore::BoolData( true ), false, "textureAcceptUnmipped" ) );
	options->addChild( new Gaffer::NameValuePlug( "ccl:texture:accept_untiled", new IECore::BoolData( true ), false, "textureAcceptUntiled" ) );
	options->addChild( new Gaffer::NameValuePlug( "ccl:texture:auto_tile", new IECore::BoolData( true ), false, "textureAutoTile" ) );
	options->addChild( new Gaffer::NameValuePlug( "ccl:texture:auto_mip", new IECore::BoolData( true ), false, "textureAutoMip" ) );
	options->addChild( new Gaffer::NameValuePlug( "ccl:texture:tile_size", new IECore::IntData( 64 ), false, "textureTileSize" ) );
	options->addChild( new Gaffer::NameValuePlug( "ccl:texture:blur_diffuse", new IECore::FloatData( 0.0156f ), false, "textureBlurDiffuse" ) );
	options->addChild( new Gaffer::NameValuePlug( "ccl:texture:blur_glossy", new IECore::FloatData( 0.0f ), false, "textureBlurGlossy" ) );
	options->addChild( new Gaffer::NameValuePlug( "ccl:texture:use_custom_cache_path", new IECore::BoolData( false ), false, "useCustomCachePath" ) );
	options->addChild( new Gaffer::NameValuePlug( "ccl:texture:custom_cache_path", new IECore::StringData(), false, "customCachePath" ) );
}

CyclesOptions::~CyclesOptions()
{
}
