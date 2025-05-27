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

class __OptionsPlugProxy( object ) :

	__renames = {
		"bucketSize" : "ai:bucket_size",
		"bucketScanning" : "ai:bucket_scanning",
		"parallelNodeInit" : "ai:parallel_node_init",
		"threads" : "ai:threads",
		"aaSamples" : "ai:AA_samples",
		"giDiffuseSamples" : "ai:GI_diffuse_samples",
		"giSpecularSamples" : "ai:GI_specular_samples",
		"giTransmissionSamples" : "ai:GI_transmission_samples",
		"giSSSSamples" : "ai:GI_sss_samples",
		"giVolumeSamples" : "ai:GI_volume_samples",
		"lightSamples" : "ai:light_samples",
		"aaSeed" : "ai:AA_seed",
		"aaSampleClamp" : "ai:AA_sample_clamp",
		"aaSampleClampAffectsAOVs" : "ai:AA_sample_clamp_affects_aovs",
		"indirectSampleClamp" : "ai:indirect_sample_clamp",
		"lowLightThreshold" : "ai:low_light_threshold",
		"enableAdaptiveSampling" : "ai:enable_adaptive_sampling",
		"aaSamplesMax" : "ai:AA_samples_max",
		"aaAdaptiveThreshold" : "ai:AA_adaptive_threshold",
		"enableProgressiveRender" : "ai:enable_progressive_render",
		"progressiveMinAASamples" : "ai:progressive_min_AA_samples",
		"giTotalDepth" : "ai:GI_total_depth",
		"giDiffuseDepth" : "ai:GI_diffuse_depth",
		"giSpecularDepth" : "ai:GI_specular_depth",
		"giTransmissionDepth" : "ai:GI_transmission_depth",
		"giVolumeDepth" : "ai:GI_volume_depth",
		"autoTransparencyDepth" : "ai:auto_transparency_depth",
		"maxSubdivisions" : "ai:max_subdivisions",
		"subdivDicingCamera" : "ai:subdiv_dicing_camera",
		"subdivFrustumCulling" : "ai:subdiv_frustum_culling",
		"subdivFrustumPadding" : "ai:subdiv_frustum_padding",
		"textureMaxMemoryMB" : "ai:texture_max_memory_MB",
		"texturePerFileStats" : "ai:texture_per_file_stats",
		"textureMaxSharpen" : "ai:texture_max_sharpen",
		"textureUseExistingTx" : "ai:texture_use_existing_tx",
		"textureAutoGenerateTx" : "ai:texture_auto_generate_tx",
		"textureAutoTxPath" : "ai:texture_auto_tx_path",
		"ignoreTextures" : "ai:ignore_textures",
		"ignoreShaders" : "ai:ignore_shaders",
		"ignoreAtmosphere" : "ai:ignore_atmosphere",
		"ignoreLights" : "ai:ignore_lights",
		"ignoreShadows" : "ai:ignore_shadows",
		"ignoreSubdivision" : "ai:ignore_subdivision",
		"ignoreDisplacement" : "ai:ignore_displacement",
		"ignoreBump" : "ai:ignore_bump",
		"ignoreSSS" : "ai:ignore_sss",
		"ignoreImagers" : "ai:ignore_imagers",
		"textureSearchPath" : "ai:texture_searchpath",
		"proceduralSearchPath" : "ai:procedural_searchpath",
		"pluginSearchPath" : "ai:plugin_searchpath",
		"abortOnError" : "ai:abort_on_error",
		"errorColorBadTexture" : "ai:error_color_bad_texture",
		"errorColorBadPixel" : "ai:error_color_bad_pixel",
		"errorColorBadShader" : "ai:error_color_bad_shader",
		"logFileName" : "ai:log:filename",
		"logMaxWarnings" : "ai:log:max_warnings",
		"logInfo" : "ai:log:info",
		"logWarnings" : "ai:log:warnings",
		"logErrors" : "ai:log:errors",
		"logDebug" : "ai:log:debug",
		"logAssParse" : "ai:log:ass_parse",
		"logPlugins" : "ai:log:plugins",
		"logProgress" : "ai:log:progress",
		"logNAN" : "ai:log:nan",
		"logTimestamp" : "ai:log:timestamp",
		"logStats" : "ai:log:stats",
		"logBacktrace" : "ai:log:backtrace",
		"logMemory" : "ai:log:memory",
		"logColor" : "ai:log:color",
		"consoleInfo" : "ai:console:info",
		"consoleWarnings" : "ai:console:warnings",
		"consoleErrors" : "ai:console:errors",
		"consoleDebug" : "ai:console:debug",
		"consoleAssParse" : "ai:console:ass_parse",
		"consolePlugins" : "ai:console:plugins",
		"consoleProgress" : "ai:console:progress",
		"consoleNAN" : "ai:console:nan",
		"consoleTimestamp" : "ai:console:timestamp",
		"consoleStats" : "ai:console:stats",
		"consoleBacktrace" : "ai:console:backtrace",
		"consoleMemory" : "ai:console:memory",
		"consoleColor" : "ai:console:color",
		"statisticsFileName" : "ai:statisticsFileName",
		"profileFileName" : "ai:profileFileName",
		"reportFileName" : "ai:reportFileName",
		"abortOnLicenseFail" : "ai:abort_on_license_fail",
		"skipLicenseCheck" : "ai:skip_license_check",
		"renderDevice" : "ai:render_device",
		"gpuMaxTextureResolution" : "ai:gpu_max_texture_resolution",
	}

	def __init__( self, optionsPlug ) :

		self.__optionsPlug = optionsPlug

	def __getitem__( self, key ) :

		return self.__optionsPlug[self.__renames.get( key, key )]

def __optionsGetItem( originalGetItem ) :

	def getItem( self, key ) :

		result = originalGetItem( self, key )
		if key == "options" :
			scriptNode = self.ancestor( Gaffer.ScriptNode )
			if scriptNode is not None and scriptNode.isExecuting() :
				return __OptionsPlugProxy( result )

		return result

	return getItem

GafferArnold.ArnoldOptions.__getitem__ = __optionsGetItem( GafferArnold.ArnoldOptions.__getitem__ )
