##########################################################################
#
#  Copyright (c) 2025, Cinesite VFX Ltd. All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are
#  met:
#
#      * Redistributions of source code must retain the above
#        copyright notice, this list of conditions and the following
#        disclaimer.
#
#      * Redistributions in binary form must reproduce the above
#        copyright notice, this list of conditions and the following
#        disclaimer in the documentation and/or other materials provided with
#        the distribution.
#
#      * Neither the name of John Haddon nor the names of
#        any other contributors to this software may be used to endorse or
#        promote products derived from this software without specific prior
#        written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
#  IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
#  THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
#  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
#  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
#  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
#  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
##########################################################################

import Gaffer
import GafferCycles

__aliases = {
	"logLevel" : "cycles:log_level",
	"device" : "cycles:device",
	"shadingSystem" : "cycles:shadingsystem",
	"samples" : "cycles:session:samples",
	"pixelSize" : "cycles:session:pixel_size",
	"numThreads" : "cycles:session:threads",
	"timeLimit" : "cycles:session:time_limit",
	"useProfiling" : "cycles:session:use_profiling",
	"useAutoTile" : "cycles:session:use_auto_tile",
	"tileSize" : "cycles:session:tile_size",
	"bvhLayout" : "cycles:scene:bvh_layout",
	"useBvhSpatialSplit" : "cycles:scene:use_bvh_spatial_split",
	"useBvhUnalignedNodes" : "cycles:scene:use_bvh_unaligned_nodes",
	"numBvhTimeSteps" : "cycles:scene:num_bvh_time_steps",
	"hairSubdivisions" : "cycles:scene:hair_subdivisions",
	"hairShape" : "cycles:scene:hair_shape",
	"textureLimit" : "cycles:scene:texture_limit",
	"minBounce" : "cycles:integrator:min_bounce",
	"maxBounce" : "cycles:integrator:max_bounce",
	"maxDiffuseBounce" : "cycles:integrator:max_diffuse_bounce",
	"maxGlossyBounce" : "cycles:integrator:max_glossy_bounce",
	"maxTransmissionBounce" : "cycles:integrator:max_transmission_bounce",
	"maxVolumeBounce" : "cycles:integrator:max_volume_bounce",
	"transparentMinBounce" : "cycles:integrator:transparent_min_bounce",
	"transparentMaxBounce" : "cycles:integrator:transparent_max_bounce",
	"aoBounces" : "cycles:integrator:ao_bounces",
	"aoFactor" : "cycles:integrator:ao_factor",
	"aoDistance" : "cycles:integrator:ao_distance",
	"volumeMaxSteps" : "cycles:integrator:volume_max_steps",
	"volumeStepRate" : "cycles:integrator:volume_step_rate",
	"causticsReflective" : "cycles:integrator:caustics_reflective",
	"causticsRefractive" : "cycles:integrator:caustics_refractive",
	"filterGlossy" : "cycles:integrator:filter_glossy",
	"seed" : "cycles:integrator:seed",
	"sampleClampDirect" : "cycles:integrator:sample_clamp_direct",
	"sampleClampIndirect" : "cycles:integrator:sample_clamp_indirect",
	"startSample" : "cycles:integrator:start_sample",
	"useLightTree" : "cycles:integrator:use_light_tree",
	"lightSamplingThreshold" : "cycles:integrator:light_sampling_threshold",
	"useAdaptiveSampling" : "cycles:integrator:use_adaptive_sampling",
	"adaptiveThreshold" : "cycles:integrator:adaptive_threshold",
	"adaptiveMinSamples" : "cycles:integrator:adaptive_min_samples",
	"denoiserType" : "cycles:integrator:denoiser_type",
	"denoiseDevice" : "cycles:denoise_device",
	"denoiseStartSample" : "cycles:integrator:denoise_start_sample",
	"useDenoisePassAlbedo" : "cycles:integrator:use_denoise_pass_albedo",
	"useDenoisePassNormal" : "cycles:integrator:use_denoise_pass_normal",
	"denoiserPrefilter" : "cycles:integrator:denoiser_prefilter",
	"useGuiding" : "cycles:integrator:use_guiding",
	"useSurfaceGuiding" : "cycles:integrator:use_surface_guiding",
	"useVolumeGuiding" : "cycles:integrator:use_volume_guiding",
	"guidingTrainingSamples" : "cycles:integrator:guiding_training_samples",
	"bgUseShader" : "cycles:background:use_shader",
	"bgCameraVisibility" : "cycles:background:visibility:camera",
	"bgDiffuseVisibility" : "cycles:background:visibility:diffuse",
	"bgGlossyVisibility" : "cycles:background:visibility:glossy",
	"bgTransmissionVisibility" : "cycles:background:visibility:transmission",
	"bgShadowVisibility" : "cycles:background:visibility:shadow",
	"bgScatterVisibility" : "cycles:background:visibility:scatter",
	"bgTransparent" : "cycles:background:transparent",
	"bgTransparentGlass" : "cycles:background:transparent_glass",
	"bgTransparentRoughnessThreshold" : "cycles:background:transparent_roughness_threshold",
	"volumeStepSize" : "cycles:background:volume_step_size",
	"exposure" : "cycles:film:exposure",
	"passAlphaThreshold" : "cycles:film:pass_alpha_threshold",
	"displayPass" : "cycles:film:display_pass",
	"showActivePixels" : "cycles:film:show_active_pixels",
	"filterType" : "cycles:film:filter_type",
	"filterWidth" : "cycles:film:filter_width",
	"mistStart" : "cycles:film:mist_start",
	"mistDepth" : "cycles:film:mist_depth",
	"mistFalloff" : "cycles:film:mist_falloff",
	"cryptomatteDepth" : "cycles:film:cryptomatte_depth",
	"dicingCamera" : "cycles:dicing_camera",
}

for k, v in __aliases.items() :
	Gaffer.Metadata.registerValue( GafferCycles.CyclesOptions, "options", f"compatibility:childAlias:{k}", v )
