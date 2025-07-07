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
import GafferDelight

__aliases = {
	"dl:bucketorder" : "bucketOrder",
	"dl:numberofthreads" : "numberOfThreads",
	"dl:renderatlowpriority" : "renderAtLowPriority",
	"dl:oversampling" : "oversampling",
	"dl:quality_shadingsamples" : "shadingSamples",
	"dl:quality_volumesamples" : "volumeSamples",
	"dl:clampindirect" : "clampIndirect",
	"dl:importancesamplefilter" : "importanceSampleFilter",
	"dl:show_displacement" : "showDisplacement",
	"dl:show_osl_subsurface" : "showSubsurface",
	"dl:show_atmosphere" : "showAtmosphere",
	"dl:show_multiplescattering" : "showMultipleScattering",
	"dl:statistics_progress" : "showProgress",
	"dl:statistics_filename" : "statisticsFileName",
	"dl:maximumraydepth_diffuse" : "maximumRayDepthDiffuse",
	"dl:maximumraydepth_hair" : "maximumRayDepthHair",
	"dl:maximumraydepth_reflection" : "maximumRayDepthReflection",
	"dl:maximumraydepth_refraction" : "maximumRayDepthRefraction",
	"dl:maximumraydepth_volume" : "maximumRayDepthVolume",
	"dl:maximumraylength_diffuse" : "maximumRayLengthDiffuse",
	"dl:maximumraylength_hair" : "maximumRayLengthHair",
	"dl:maximumraylength_reflection" : "maximumRayLengthReflection",
	"dl:maximumraylength_refraction" : "maximumRayLengthRefraction",
	"dl:maximumraylength_specular" : "maximumRayLengthSpecular",
	"dl:maximumraylength_volume" : "maximumRayLengthVolume",
	"dl:texturememory" : "textureMemory",
	"dl:networkcache_size" : "networkCacheSize",
	"dl:networkcache_directory" : "networkCacheDirectory",
	"dl:license_server" : "licenseServer",
	"dl:license_wait" : "licenseWait",
}

# Provide compatibility for DelightOptions plugs renamed in Gaffer 1.6
for k, v in __aliases.items() :
	Gaffer.Metadata.registerValue( GafferDelight.DelightOptions, "options", f"compatibility:childAlias:{k}", v )
