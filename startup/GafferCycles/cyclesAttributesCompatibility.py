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
	"cameraVisibility" : "cycles:visibility:camera",
	"diffuseVisibility" : "cycles:visibility:diffuse",
	"glossyVisibility" : "cycles:visibility:glossy",
	"transmissionVisibility" : "cycles:visibility:transmission",
	"shadowVisibility" : "cycles:visibility:shadow",
	"scatterVisibility" : "cycles:visibility:scatter",
	"useHoldout" : "cycles:use_holdout",
	"isShadowCatcher" : "cycles:is_shadow_catcher",
	"shadowTerminatorShadingOffset" : "cycles:shadow_terminator_shading_offset",
	"shadowTerminatorGeometryOffset" : "cycles:shadow_terminator_geometry_offset",
	"isCausticsCaster" : "cycles:is_caustics_caster",
	"isCausticsReceiver" : "cycles:is_caustics_receiver",
	"maxLevel" : "cycles:max_level",
	"dicingScale" : "cycles:dicing_rate",
	"lightGroup" : "cycles:lightgroup",
	"volumeClipping" : "cycles:volume_clipping",
	"volumeStepSize" : "cycles:volume_step_size",
	"volumeObjectSpace" : "cycles:volume_object_space",
	"volumeVelocityScale" : "cycles:volume_velocity_scale",
	"volumePrecision" : "cycles:volume_precision",
	"assetName" : "cycles:asset_name",
	"emissionSamplingMethod" : "cycles:shader:emission_sampling_method",
	"useTransparentShadow" : "cycles:shader:use_transparent_shadow",
	"volumeSamplingMethod" : "cycles:shader:volume_sampling_method",
	"volumeInterpolationMethod" : "cycles:shader:volume_interpolation_method",
	"volumeStepRate" : "cycles:shader:volume_step_rate",
	"displacementMethod" : "cycles:shader:displacement_method",
}

for k, v in __aliases.items() :
	Gaffer.Metadata.registerValue( GafferCycles.CyclesAttributes, "attributes", f"compatibility:childAlias:{k}", v )
