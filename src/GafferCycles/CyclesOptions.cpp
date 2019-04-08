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

using namespace Imath;
using namespace GafferCycles;

IE_CORE_DEFINERUNTIMETYPED( CyclesOptions );

CyclesOptions::CyclesOptions( const std::string &name )
	:	GafferScene::Options( name )
{
	Gaffer::CompoundDataPlug *options = optionsPlug();

	// Device

	options->addOptionalMember( "ccl:device", new IECore::StringData( "CPU" ), "device", Gaffer::Plug::Default, false );

	// Session and scene
	options->addOptionalMember( "ccl:shadingsystem", new IECore::StringData( "SVM" ), "shadingSystem", Gaffer::Plug::Default, false );

	// Session/Render

	options->addOptionalMember( "ccl:session:experimental", new IECore::BoolData( false ), "featureSet", Gaffer::Plug::Default, false );

	options->addOptionalMember( "ccl:session:progressive_refine", new IECore::BoolData( false ), "progressiveRefine", Gaffer::Plug::Default, false );
	//options->addOptionalMember( "ccl:session:progressive", new IECore::BoolData( false ), "progressive", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:session:samples", new IECore::IntData( 8 ), "samples", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:session:tile_size", new IECore::V2iData( Imath::V2i( 64, 64 ) ), "tileSize", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:session:tile_order", new IECore::IntData( 0 ), "tileOrder", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:session:start_resolution", new IECore::IntData( 64 ), "startResolution", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:session:pixel_size", new IECore::IntData( 64 ), "pixelSize", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:session:threads", new IECore::IntData( 0 ), "numThreads", Gaffer::Plug::Default, false );
	//options->addOptionalMember( "ccl:session:display_buffer_linear", new IECore::BoolData( true ), "displayBufferLinear", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:session:run_denoising", new IECore::BoolData( false ), "runDenoising", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:session:write_denoising_passes", new IECore::BoolData( false ), "writeDenoisingPasses", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:session:full_denoising", new IECore::BoolData( false ), "fullDenoising", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:session:cancel_timeout", new IECore::FloatData( 0.1f ), "cancelTimeout", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:session:reset_timeout", new IECore::FloatData( 0.1f ), "resetTimeout", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:session:text_timeout", new IECore::FloatData( 1.0f ), "textTimeout", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:session:progressive_update_timeout", new IECore::FloatData( 1.0f ), "progressiveUpdateTimeout", Gaffer::Plug::Default, false );

	// Denoising
	options->addOptionalMember( "ccl:denoise:radius", new IECore::IntData( 8 ), "denoiseRadius", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:denoise:strength", new IECore::FloatData( 0.5f ), "denoiseStrength", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:denoise:feature_strength", new IECore::FloatData( 0.5f ), "denoiseFeatureStrength", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:denoise:relative_pca", new IECore::BoolData( false ), "denoiseRelativePca", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:denoise:neighbor_frames", new IECore::IntData( 2 ), "denoiseNeighborFrames", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:denoise:clamp_input", new IECore::BoolData( true ), "denoiseClampInput", Gaffer::Plug::Default, false );

	options->addOptionalMember( "ccl:denoising_diffuse_direct",        new IECore::BoolData( true ), "denoisingDiffuseDirect",       Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:denoising_diffuse_indirect",      new IECore::BoolData( true ), "denoisingDiffuseIndirect",      Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:denoising_glossy_direct",         new IECore::BoolData( true ), "denoisingGlossyDirect",        Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:denoising_glossy_indirect",       new IECore::BoolData( true ), "denoisingGlossyIndirect",      Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:denoising_transmission_direct",   new IECore::BoolData( true ), "denoisingTransmissionDirect",  Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:denoising_transmission_indirect", new IECore::BoolData( true ), "denoisingTransmissionIndirect", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:denoising_subsurface_direct",     new IECore::BoolData( true ), "denoisingSubsurfaceDirect",    Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:denoising_subsurface_indirect",   new IECore::BoolData( true ), "denoisingSubsurfaceIndirect",  Gaffer::Plug::Default, false );

	// Scene/BVH

	//options->addOptionalMember( "ccl:scene:dicing_camera", new IECore::StringData( "dicingCamera" ), "", Gaffer::Plug::Default, false );

	//options->addOptionalMember( "ccl:scene:bvh_type", new IECore::IntData( 0 ), "bvhType", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:scene:bvh_layout", new IECore::IntData( 0 | 1 << 1 ), "bvhLayout", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:scene:use_bvh_spatial_split", new IECore::BoolData( false ), "useBvhSpatialSplit", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:scene:use_bvh_unaligned_nodes", new IECore::BoolData( true ), "useBvhUnalignedNodes", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:scene:num_bvh_time_steps", new IECore::IntData( 0 ), "numBvhTimeSteps", Gaffer::Plug::Default, false );

	//options->addOptionalMember( "ccl:scene:persistent_data", new IECore::BoolData( true ), "persistentData", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:scene:texture_limit", new IECore::IntData( 0 ), "textureLimit", Gaffer::Plug::Default, false );

	// Integrator

	options->addOptionalMember( "ccl:integrator:max_bounce", new IECore::IntData( 7 ), "maxBounce", Gaffer::Plug::Default, false );

	options->addOptionalMember( "ccl:integrator:max_diffuse_bounce", new IECore::IntData( 7 ), "maxDiffuseBounce", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:integrator:max_glossy_bounce", new IECore::IntData( 7 ), "maxGlossyBounce", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:integrator:max_transmission_bounce", new IECore::IntData( 7 ), "maxTransmissionBounce", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:integrator:max_volume_bounce", new IECore::IntData( 7 ), "maxVolumeBounce", Gaffer::Plug::Default, false );

	options->addOptionalMember( "ccl:integrator:transparent_max_bounce", new IECore::IntData( 7 ), "transparentMaxBounce", Gaffer::Plug::Default, false );

	options->addOptionalMember( "ccl:integrator:ao_bounces", new IECore::IntData( 0 ), "aoBounces", Gaffer::Plug::Default, false );

	options->addOptionalMember( "ccl:integrator:volume_max_steps", new IECore::IntData( 1024 ), "volumeMaxSteps", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:integrator:volume_step_size", new IECore::FloatData( 0.1f ), "volumeStepSize", Gaffer::Plug::Default, false );

	options->addOptionalMember( "ccl:integrator:caustics_reflective", new IECore::BoolData( true ), "causticsReflective", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:integrator:caustics_refractive", new IECore::BoolData( true ), "causticsRefractive", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:integrator:filter_glossy", new IECore::FloatData( 0.0f ), "filterGlossy", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:integrator:seed", new IECore::IntData( 0 ), "seed", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:integrator:sample_clamp_direct", new IECore::FloatData( 0.0f ), "sampleClampDirect", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:integrator:sample_clamp_indirect", new IECore::FloatData( 0.0f ), "sampleClampIndirect", Gaffer::Plug::Default, false );

	options->addOptionalMember( "ccl:integrator:aa_samples", new IECore::IntData( 0 ), "aaSamples", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:integrator:diffuse_samples", new IECore::IntData( 1 ), "diffuseSamples", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:integrator:glossy_samples", new IECore::IntData( 1 ), "glossySamples", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:integrator:transmission_samples", new IECore::IntData( 1 ), "transmissionSamples", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:integrator:ao_samples", new IECore::IntData( 1 ), "aoSamples", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:integrator:mesh_light_samples", new IECore::IntData( 1 ), "meshlightSamples", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:integrator:subsurface_samples", new IECore::IntData( 1 ), "subsurfaceSamples", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:integrator:volume_samples", new IECore::IntData( 1 ), "volumeSamples", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:integrator:start_sample", new IECore::IntData( 0 ), "startSample", Gaffer::Plug::Default, false );

	options->addOptionalMember( "ccl:integrator:sample_all_lights_direct", new IECore::BoolData( true ), "sampleAllLightsDirect", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:integrator:sample_all_lights_indirect", new IECore::BoolData( true ), "sampleAllLightsIndirect", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:integrator:light_sampling_threshold", new IECore::FloatData( 0.05f ), "lightSamplingThreshold", Gaffer::Plug::Default, false );

	options->addOptionalMember( "ccl:integrator:method", new IECore::IntData( 0 ), "method", Gaffer::Plug::Default, false );

	options->addOptionalMember( "ccl:integrator:sampling_pattern", new IECore::IntData( 0 ), "samplingPattern", Gaffer::Plug::Default, false );

	// Curves
	options->addOptionalMember( "ccl:curve:use_curves", new IECore::BoolData( false ), "useCurves", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:curve:minimum_width", new IECore::FloatData( 0.0f ), "curveMinimumWidth", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:curve:maximum_width", new IECore::FloatData( 0.10f ), "curveMaximumWidth", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:curve:primitive", new IECore::IntData( 0 ), "curvePrimitive", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:curve:shape", new IECore::IntData( 0 ), "curveShape", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:curve:resolution", new IECore::IntData( 0 ), "curveResolution", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:curve:subdivisions", new IECore::IntData( 0 ), "curveSubdivisions", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:curve:cull_backfacing", new IECore::BoolData( false ), "curveCullBackfacing", Gaffer::Plug::Default, false );

	// Background
	options->addOptionalMember( "ccl:background:ao_factor", new IECore::FloatData( 0.0f ), "aoFactor", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:background:ao_distance", new IECore::FloatData( FLT_MAX ), "aoDistance", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:background:use_shader", new IECore::BoolData( true ), "bgUseShader", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:background:use_ao", new IECore::BoolData( false ), "useAO", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:background:transparent", new IECore::BoolData( true ), "bgTransparent", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:background:transparent_glass", new IECore::BoolData( false ), "bgTransparentGlass", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:background:transparent_roughness_threshold", new IECore::FloatData( 0.0f ), "bgTransparentRoughnessThreshold", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:background:visibility:camera", new IECore::BoolData( true ), "bgCameraVisibility", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:background:visibility:diffuse", new IECore::BoolData( true ), "bgDiffuseVisibility", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:background:visibility:glossy", new IECore::BoolData( true ), "bgGlossyVisibility", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:background:visibility:transmission", new IECore::BoolData( true ), "bgTransmissionVisibility", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:background:visibility:shadow", new IECore::BoolData( true ), "bgShadowVisibility", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:background:visibility:scatter", new IECore::BoolData( true ), "bgScatterVisibility", Gaffer::Plug::Default, false );

	// Film
	options->addOptionalMember( "ccl:film:exposure", new IECore::FloatData( 0.5f ), "exposure", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:film:pass_alpha_threshold", new IECore::FloatData( 0.5f ), "passAlphaThreshold", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:film:filter_type", new IECore::IntData( 0 ), "filterType", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:film:filter_width", new IECore::FloatData( 1.0f ), "filterWidth", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:film:mist_start", new IECore::FloatData( 0.0f ), "mistStart", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:film:mist_depth", new IECore::FloatData( 100.0f ), "mistDepth", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:film:mist_falloff", new IECore::FloatData( 1.0f ), "mistFalloff", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:film:use_sample_clamp", new IECore::BoolData( false ), "useSampleClamp", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:film:denoising_data_pass", new IECore::BoolData( false ), "denoisingDataPass", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ccl:film:denoising_clean_pass", new IECore::BoolData( false ), "denoisingCleanPass", Gaffer::Plug::Default, false );
}

CyclesOptions::~CyclesOptions()
{
}
