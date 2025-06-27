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
import GafferArnold

__aliases = {
	"ai:bucket_size" : "bucketSize",
	"ai:bucket_scanning" : "bucketScanning",
	"ai:parallel_node_init" : "parallelNodeInit",
	"ai:threads" : "threads",
	"ai:AA_samples" : "aaSamples",
	"ai:GI_diffuse_samples" : "giDiffuseSamples",
	"ai:GI_specular_samples" : "giSpecularSamples",
	"ai:GI_transmission_samples" : "giTransmissionSamples",
	"ai:GI_sss_samples" : "giSSSSamples",
	"ai:GI_volume_samples" : "giVolumeSamples",
	"ai:light_samples" : "lightSamples",
	"ai:AA_seed" : "aaSeed",
	"ai:AA_sample_clamp" : "aaSampleClamp",
	"ai:AA_sample_clamp_affects_aovs" : "aaSampleClampAffectsAOVs",
	"ai:indirect_sample_clamp" : "indirectSampleClamp",
	"ai:low_light_threshold" : "lowLightThreshold",
	"ai:enable_adaptive_sampling" : "enableAdaptiveSampling",
	"ai:AA_samples_max" : "aaSamplesMax",
	"ai:AA_adaptive_threshold" : "aaAdaptiveThreshold",
	"ai:enable_progressive_render" : "enableProgressiveRender",
	"ai:progressive_min_AA_samples" : "progressiveMinAASamples",
	"ai:GI_total_depth" : "giTotalDepth",
	"ai:GI_diffuse_depth" : "giDiffuseDepth",
	"ai:GI_specular_depth" : "giSpecularDepth",
	"ai:GI_transmission_depth" : "giTransmissionDepth",
	"ai:GI_volume_depth" : "giVolumeDepth",
	"ai:auto_transparency_depth" : "autoTransparencyDepth",
	"ai:max_subdivisions" : "maxSubdivisions",
	"ai:subdiv_dicing_camera" : "subdivDicingCamera",
	"ai:subdiv_frustum_culling" : "subdivFrustumCulling",
	"ai:subdiv_frustum_padding" : "subdivFrustumPadding",
	"ai:texture_max_memory_MB" : "textureMaxMemoryMB",
	"ai:texture_per_file_stats" : "texturePerFileStats",
	"ai:texture_max_sharpen" : "textureMaxSharpen",
	"ai:texture_use_existing_tx" : "textureUseExistingTx",
	"ai:texture_auto_generate_tx" : "textureAutoGenerateTx",
	"ai:texture_auto_tx_path" : "textureAutoTxPath",
	"ai:ignore_textures" : "ignoreTextures",
	"ai:ignore_shaders" : "ignoreShaders",
	"ai:ignore_atmosphere" : "ignoreAtmosphere",
	"ai:ignore_lights" : "ignoreLights",
	"ai:ignore_shadows" : "ignoreShadows",
	"ai:ignore_subdivision" : "ignoreSubdivision",
	"ai:ignore_displacement" : "ignoreDisplacement",
	"ai:ignore_bump" : "ignoreBump",
	"ai:ignore_sss" : "ignoreSSS",
	"ai:ignore_imagers" : "ignoreImagers",
	"ai:texture_searchpath" : "textureSearchPath",
	"ai:procedural_searchpath" : "proceduralSearchPath",
	"ai:plugin_searchpath" : "pluginSearchPath",
	"ai:abort_on_error" : "abortOnError",
	"ai:error_color_bad_texture" : "errorColorBadTexture",
	"ai:error_color_bad_pixel" : "errorColorBadPixel",
	"ai:error_color_bad_shader" : "errorColorBadShader",
	"ai:log:filename" : "logFileName",
	"ai:log:max_warnings" : "logMaxWarnings",
	"ai:log:info" : "logInfo",
	"ai:log:warnings" : "logWarnings",
	"ai:log:errors" : "logErrors",
	"ai:log:debug" : "logDebug",
	"ai:log:ass_parse" : "logAssParse",
	"ai:log:plugins" : "logPlugins",
	"ai:log:progress" : "logProgress",
	"ai:log:nan" : "logNAN",
	"ai:log:timestamp" : "logTimestamp",
	"ai:log:stats" : "logStats",
	"ai:log:backtrace" : "logBacktrace",
	"ai:log:memory" : "logMemory",
	"ai:log:color" : "logColor",
	"ai:console:info" : "consoleInfo",
	"ai:console:warnings" : "consoleWarnings",
	"ai:console:errors" : "consoleErrors",
	"ai:console:debug" : "consoleDebug",
	"ai:console:ass_parse" : "consoleAssParse",
	"ai:console:plugins" : "consolePlugins",
	"ai:console:progress" : "consoleProgress",
	"ai:console:nan" : "consoleNAN",
	"ai:console:timestamp" : "consoleTimestamp",
	"ai:console:stats" : "consoleStats",
	"ai:console:backtrace" : "consoleBacktrace",
	"ai:console:memory" : "consoleMemory",
	"ai:console:color" : "consoleColor",
	"ai:statisticsFileName" : "statisticsFileName",
	"ai:profileFileName" : "profileFileName",
	"ai:reportFileName" : "reportFileName",
	"ai:abort_on_license_fail" : "abortOnLicenseFail",
	"ai:skip_license_check" : "skipLicenseCheck",
	"ai:render_device" : "renderDevice",
	"ai:gpu_max_texture_resolution" : "gpuMaxTextureResolution",
}

# Provide compatibility for ArnoldOptions plugs renamed in Gaffer 1.6
for k, v in __aliases.items() :
	Gaffer.Metadata.registerValue( GafferArnold.ArnoldOptions, "options", f"compatibility:childAlias:{k}", v )
