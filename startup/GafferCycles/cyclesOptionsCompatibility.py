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
	"cycles:log_level" : "logLevel",
	"cycles:device" : "device",
	"cycles:shadingsystem" : "shadingSystem",
	"cycles:session:samples" : "samples",
	"cycles:session:pixel_size" : "pixelSize",
	"cycles:session:threads" : "numThreads",
	"cycles:session:time_limit" : "timeLimit",
	"cycles:session:use_profiling" : "useProfiling",
	"cycles:session:use_auto_tile" : "useAutoTile",
	"cycles:session:tile_size" : "tileSize",
	"cycles:scene:bvh_layout" : "bvhLayout",
	"cycles:scene:use_bvh_spatial_split" : "useBvhSpatialSplit",
	"cycles:scene:use_bvh_unaligned_nodes" : "useBvhUnalignedNodes",
	"cycles:scene:num_bvh_time_steps" : "numBvhTimeSteps",
	"cycles:scene:hair_subdivisions" : "hairSubdivisions",
	"cycles:scene:hair_shape" : "hairShape",
	"cycles:scene:texture_limit" : "textureLimit",
	"cycles:integrator:min_bounce" : "minBounce",
	"cycles:integrator:max_bounce" : "maxBounce",
	"cycles:integrator:max_diffuse_bounce" : "maxDiffuseBounce",
	"cycles:integrator:max_glossy_bounce" : "maxGlossyBounce",
	"cycles:integrator:max_transmission_bounce" : "maxTransmissionBounce",
	"cycles:integrator:max_volume_bounce" : "maxVolumeBounce",
	"cycles:integrator:transparent_min_bounce" : "transparentMinBounce",
	"cycles:integrator:transparent_max_bounce" : "transparentMaxBounce",
	"cycles:integrator:ao_bounces" : "aoBounces",
	"cycles:integrator:ao_factor" : "aoFactor",
	"cycles:integrator:ao_distance" : "aoDistance",
	"cycles:integrator:volume_max_steps" : "volumeMaxSteps",
	"cycles:integrator:volume_step_rate" : "volumeStepRate",
	"cycles:integrator:caustics_reflective" : "causticsReflective",
	"cycles:integrator:caustics_refractive" : "causticsRefractive",
	"cycles:integrator:filter_glossy" : "filterGlossy",
	"cycles:integrator:seed" : "seed",
	"cycles:integrator:sample_clamp_direct" : "sampleClampDirect",
	"cycles:integrator:sample_clamp_indirect" : "sampleClampIndirect",
	"cycles:integrator:start_sample" : "startSample",
	"cycles:integrator:use_light_tree" : "useLightTree",
	"cycles:integrator:light_sampling_threshold" : "lightSamplingThreshold",
	"cycles:integrator:use_adaptive_sampling" : "useAdaptiveSampling",
	"cycles:integrator:adaptive_threshold" : "adaptiveThreshold",
	"cycles:integrator:adaptive_min_samples" : "adaptiveMinSamples",
	"cycles:integrator:denoiser_type" : "denoiserType",
	"cycles:denoise_device" : "denoiseDevice",
	"cycles:integrator:denoise_start_sample" : "denoiseStartSample",
	"cycles:integrator:use_denoise_pass_albedo" : "useDenoisePassAlbedo",
	"cycles:integrator:use_denoise_pass_normal" : "useDenoisePassNormal",
	"cycles:integrator:denoiser_prefilter" : "denoiserPrefilter",
	"cycles:integrator:use_guiding" : "useGuiding",
	"cycles:integrator:use_surface_guiding" : "useSurfaceGuiding",
	"cycles:integrator:use_volume_guiding" : "useVolumeGuiding",
	"cycles:integrator:guiding_training_samples" : "guidingTrainingSamples",
	"cycles:background:use_shader" : "bgUseShader",
	"cycles:background:visibility:camera" : "bgCameraVisibility",
	"cycles:background:visibility:diffuse" : "bgDiffuseVisibility",
	"cycles:background:visibility:glossy" : "bgGlossyVisibility",
	"cycles:background:visibility:transmission" : "bgTransmissionVisibility",
	"cycles:background:visibility:shadow" : "bgShadowVisibility",
	"cycles:background:visibility:scatter" : "bgScatterVisibility",
	"cycles:background:transparent" : "bgTransparent",
	"cycles:background:transparent_glass" : "bgTransparentGlass",
	"cycles:background:transparent_roughness_threshold" : "bgTransparentRoughnessThreshold",
	"cycles:background:volume_step_size" : "volumeStepSize",
	"cycles:film:exposure" : "exposure",
	"cycles:film:pass_alpha_threshold" : "passAlphaThreshold",
	"cycles:film:display_pass" : "displayPass",
	"cycles:film:show_active_pixels" : "showActivePixels",
	"cycles:film:filter_type" : "filterType",
	"cycles:film:filter_width" : "filterWidth",
	"cycles:film:mist_start" : "mistStart",
	"cycles:film:mist_depth" : "mistDepth",
	"cycles:film:mist_falloff" : "mistFalloff",
	"cycles:film:cryptomatte_depth" : "cryptomatteDepth",
	"cycles:dicing_camera" : "dicingCamera",
}

# Provide compatibility for CyclesOptions plugs renamed in Gaffer 1.6
for k, v in __aliases.items() :
	Gaffer.Metadata.registerValue( GafferCycles.CyclesOptions, "options", f"compatibility:childAlias:{k}", v )
