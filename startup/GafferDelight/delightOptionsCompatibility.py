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
	"bucketOrder" : "dl:bucketorder",
	"numberOfThreads" : "dl:numberofthreads",
	"renderAtLowPriority" : "dl:renderatlowpriority",
	"oversampling" : "dl:oversampling",
	"shadingSamples" : "dl:quality_shadingsamples",
	"volumeSamples" : "dl:quality_volumesamples",
	"clampIndirect" : "dl:clampindirect",
	"importanceSampleFilter" : "dl:importancesamplefilter",
	"showDisplacement" : "dl:show_displacement",
	"showSubsurface" : "dl:show_osl_subsurface",
	"showAtmosphere" : "dl:show_atmosphere",
	"showMultipleScattering" : "dl:show_multiplescattering",
	"showProgress" : "dl:statistics_progress",
	"statisticsFileName" : "dl:statistics_filename",
	"maximumRayDepthDiffuse" : "dl:maximumraydepth_diffuse",
	"maximumRayDepthHair" : "dl:maximumraydepth_hair",
	"maximumRayDepthReflection" : "dl:maximumraydepth_reflection",
	"maximumRayDepthRefraction" : "dl:maximumraydepth_refraction",
	"maximumRayDepthVolume" : "dl:maximumraydepth_volume",
	"maximumRayLengthDiffuse" : "dl:maximumraylength_diffuse",
	"maximumRayLengthHair" : "dl:maximumraylength_hair",
	"maximumRayLengthReflection" : "dl:maximumraylength_reflection",
	"maximumRayLengthRefraction" : "dl:maximumraylength_refraction",
	"maximumRayLengthSpecular" : "dl:maximumraylength_specular",
	"maximumRayLengthVolume" : "dl:maximumraylength_volume",
	"textureMemory" : "dl:texturememory",
	"networkCacheSize" : "dl:networkcache_size",
	"networkCacheDirectory" : "dl:networkcache_directory",
	"licenseServer" : "dl:license_server",
	"licenseWait" : "dl:license_wait",
}

for k, v in __aliases.items() :
	Gaffer.Metadata.registerValue( GafferDelight.DelightOptions, "options", f"compatibility:childAlias:{k}", v )
