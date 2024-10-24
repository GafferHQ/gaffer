##########################################################################
#
#  Copyright (c) 2024, Cinesite VFX Ltd. All rights reserved.
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

import IECore

import Gaffer

Gaffer.Metadata.registerValue( "attribute:cycles:visibility:camera", "label", "Camera" )
Gaffer.Metadata.registerValue( "attribute:cycles:visibility:camera", "defaultValue", IECore.BoolData( True ) )
Gaffer.Metadata.registerValue(
	"attribute:cycles:visibility:camera",
	"description",
	"""
	Whether or not the object is visible to camera
	rays. To hide an object completely, use the
	`scene:visible` attribute instead.
	""",
)

Gaffer.Metadata.registerValue( "attribute:cycles:visibility:diffuse", "label", "Diffuse" )
Gaffer.Metadata.registerValue( "attribute:cycles:visibility:diffuse", "defaultValue", IECore.BoolData( True ) )
Gaffer.Metadata.registerValue(
	"attribute:cycles:visibility:diffuse",
	"description",
	"""
	Whether or not the object is visible to diffuse
	rays.
	""",
)

Gaffer.Metadata.registerValue( "attribute:cycles:visibility:glossy", "label", "Glossy" )
Gaffer.Metadata.registerValue( "attribute:cycles:visibility:glossy", "defaultValue", IECore.BoolData( True ) )
Gaffer.Metadata.registerValue(
	"attribute:cycles:visibility:glossy",
	"description",
	"""
	Whether or not the object is visible in
	glossy rays.
	""",
)

Gaffer.Metadata.registerValue( "attribute:cycles:visibility:transmission", "label", "Transmission" )
Gaffer.Metadata.registerValue( "attribute:cycles:visibility:transmission", "defaultValue", IECore.BoolData( True ) )
Gaffer.Metadata.registerValue(
	"attribute:cycles:visibility:transmission",
	"description",
	"""
	Whether or not the object is visible in
	transmission.
	""",
)

Gaffer.Metadata.registerValue( "attribute:cycles:visibility:shadow", "label", "Shadow" )
Gaffer.Metadata.registerValue( "attribute:cycles:visibility:shadow", "defaultValue", IECore.BoolData( True ) )
Gaffer.Metadata.registerValue(
	"attribute:cycles:visibility:shadow",
	"description",
	"""
	Whether or not the object is visible to shadow
	rays - whether it casts shadows or not.
	""",
)

Gaffer.Metadata.registerValue( "attribute:cycles:visibility:scatter", "label", "Scatter" )
Gaffer.Metadata.registerValue( "attribute:cycles:visibility:scatter", "defaultValue", IECore.BoolData( True ) )
Gaffer.Metadata.registerValue(
	"attribute:cycles:visibility:scatter",
	"description",
	"""
	Whether or not the object is visible to
	scatter rays.
	""",
)

Gaffer.Metadata.registerValue( "attribute:cycles:use_holdout", "label", "Use Holdout" )
Gaffer.Metadata.registerValue( "attribute:cycles:use_holdout", "defaultValue", IECore.BoolData( False ) )
Gaffer.Metadata.registerValue(
	"attribute:cycles:use_holdout",
	"description",
	"""
	Turns the object into a holdout matte.
	This only affects primary (camera) rays.
	""",
)

Gaffer.Metadata.registerValue( "attribute:cycles:is_shadow_catcher", "label", "Is Shadow Catcher" )
Gaffer.Metadata.registerValue( "attribute:cycles:is_shadow_catcher", "defaultValue", IECore.BoolData( False ) )
Gaffer.Metadata.registerValue(
	"attribute:cycles:is_shadow_catcher",
	"description",
	"""
	Turns the object into a shadow catcher.
	""",
)

Gaffer.Metadata.registerValue( "attribute:cycles:shadow_terminator_shading_offset", "label", "Terminator Shading Offset" )
Gaffer.Metadata.registerValue( "attribute:cycles:shadow_terminator_shading_offset", "defaultValue", IECore.FloatData( 0 ) )
Gaffer.Metadata.registerValue(
	"attribute:cycles:shadow_terminator_shading_offset",
	"description",
	"""
	Push the shadow terminator towards the light to hide artifacts on low poly geometry.
	""",
)

Gaffer.Metadata.registerValue( "attribute:cycles:shadow_terminator_geometry_offset", "label", "Terminator Geometry Offset" )
Gaffer.Metadata.registerValue( "attribute:cycles:shadow_terminator_geometry_offset", "defaultValue", IECore.FloatData( 0 ) )
Gaffer.Metadata.registerValue(
	"attribute:cycles:shadow_terminator_geometry_offset",
	"description",
	"""
	Offset rays from the surface to reduce shadow terminator artifact on low poly geometry. Only affects triangles at grazing angles to light.
	""",
)

Gaffer.Metadata.registerValue( "attribute:cycles:lightgroup", "label", "Lightgroup" )
Gaffer.Metadata.registerValue( "attribute:cycles:lightgroup", "defaultValue", IECore.StringData( "" ) )
Gaffer.Metadata.registerValue(
	"attribute:cycles:lightgroup",
	"description",
	"""
	Set the lightgroup of an object with emission.
	""",
)

Gaffer.Metadata.registerValue( "attribute:cycles:is_caustics_caster", "label", "Is Caustics Caster" )
Gaffer.Metadata.registerValue( "attribute:cycles:is_caustics_caster", "defaultValue", IECore.BoolData( False ) )
Gaffer.Metadata.registerValue(
	"attribute:cycles:is_caustics_caster",
	"description",
	"""
	Cast Shadow Caustics.
	""",
)

Gaffer.Metadata.registerValue( "attribute:cycles:is_caustics_receiver", "label", "Is Caustics Receiver" )
Gaffer.Metadata.registerValue( "attribute:cycles:is_caustics_receiver", "defaultValue", IECore.BoolData( False ) )
Gaffer.Metadata.registerValue(
	"attribute:cycles:is_caustics_receiver",
	"description",
	"""
	Receive Shadow Caustics.
	""",
)

Gaffer.Metadata.registerValue( "attribute:cycles:max_level", "label", "Max Level" )
Gaffer.Metadata.registerValue( "attribute:cycles:max_level", "defaultValue", IECore.IntData( 1 ) )
Gaffer.Metadata.registerValue(
	"attribute:cycles:max_level",
	"description",
	"""
	The max level of subdivision that can be
	applied.
	""",
)

Gaffer.Metadata.registerValue( "attribute:cycles:dicing_rate", "label", "Dicing Scale" )
Gaffer.Metadata.registerValue( "attribute:cycles:dicing_rate", "defaultValue", IECore.FloatData( 1 ) )
Gaffer.Metadata.registerValue(
	"attribute:cycles:dicing_rate",
	"description",
	"""
	Multiplier for scene dicing rate.
	""",
)

Gaffer.Metadata.registerValue( "attribute:cycles:volume_clipping", "label", "Clipping" )
Gaffer.Metadata.registerValue( "attribute:cycles:volume_clipping", "defaultValue", IECore.FloatData( 0.001 ) )
Gaffer.Metadata.registerValue(
	"attribute:cycles:volume_clipping",
	"description",
	"""
	Value under which voxels are considered empty space to
	optimize rendering.
	""",
)

Gaffer.Metadata.registerValue( "attribute:cycles:volume_step_size", "label", "Step Size" )
Gaffer.Metadata.registerValue( "attribute:cycles:volume_step_size", "defaultValue", IECore.FloatData( 0 ) )
Gaffer.Metadata.registerValue(
	"attribute:cycles:volume_step_size",
	"description",
	"""
	Distance between volume samples. When zero it is automatically
	estimated based on the voxel size.
	""",
)

Gaffer.Metadata.registerValue( "attribute:cycles:volume_object_space", "label", "Object Space" )
Gaffer.Metadata.registerValue( "attribute:cycles:volume_object_space", "defaultValue", IECore.BoolData( True ) )
Gaffer.Metadata.registerValue(
	"attribute:cycles:volume_object_space",
	"description",
	"""
	Specify volume density and step size in object or world space.
	By default object space is used, so that the volume opacity and
	detail remains the same regardless of object scale.
	""",
)

Gaffer.Metadata.registerValue( "attribute:cycles:asset_name", "label", "Asset Name" )
Gaffer.Metadata.registerValue( "attribute:cycles:asset_name", "defaultValue", IECore.StringData( "" ) )
Gaffer.Metadata.registerValue(
	"attribute:cycles:asset_name",
	"description",
	"""
	Asset name for cryptomatte.
	""",
)

Gaffer.Metadata.registerValue( "attribute:cycles:shader:emission_sampling_method", "label", "Emission Sampling Method" )
Gaffer.Metadata.registerValue( "attribute:cycles:shader:emission_sampling_method", "defaultValue", IECore.StringData( "auto" ) )
Gaffer.Metadata.registerValue(
	"attribute:cycles:shader:emission_sampling_method",
	"description",
	"""
	Sampling strategy for emissive surfaces.
	""",
)
Gaffer.Metadata.registerValue( "attribute:cycles:shader:emission_sampling_method", "plugValueWidget:type", "GafferUI.PresetsPlugValueWidget" )
Gaffer.Metadata.registerValue( "attribute:cycles:shader:emission_sampling_method", "presetNames", IECore.StringVectorData( [ "None", "Auto", "Front", "Back", "Front-Back" ] ) )
Gaffer.Metadata.registerValue( "attribute:cycles:shader:emission_sampling_method", "presetValues", IECore.StringVectorData( [ "none", "auto", "front", "back", "front_back" ] ) )


Gaffer.Metadata.registerValue( "attribute:cycles:shader:use_transparent_shadow", "label", "Transparent Shadow" )
Gaffer.Metadata.registerValue( "attribute:cycles:shader:use_transparent_shadow", "defaultValue", IECore.BoolData( True ) )
Gaffer.Metadata.registerValue(
	"attribute:cycles:shader:use_transparent_shadow",
	"description",
	"""
	Use transparent shadows for this material if it contains a Transparent BSDF,
	disabling will render faster but not give accurate shadows.
	""",
)

Gaffer.Metadata.registerValue( "attribute:cycles:shader:heterogeneous_volume", "label", "Heterogeneous Volume" )
Gaffer.Metadata.registerValue( "attribute:cycles:shader:heterogeneous_volume", "defaultValue", IECore.BoolData( True ) )
Gaffer.Metadata.registerValue(
	"attribute:cycles:shader:heterogeneous_volume",
	"description",
	"""
	Disabling this when using volume rendering, assume volume has the same density
	everywhere (not using any textures), for faster rendering.
	""",
)

Gaffer.Metadata.registerValue( "attribute:cycles:shader:volume_sampling_method", "label", "Volume Sampling" )
Gaffer.Metadata.registerValue( "attribute:cycles:shader:volume_sampling_method", "defaultValue", IECore.StringData( "multiple_importance" ) )
Gaffer.Metadata.registerValue(
	"attribute:cycles:shader:volume_sampling_method",
	"description",
	"""
	Sampling method to use for volumes.
	""",
)
Gaffer.Metadata.registerValue( "attribute:cycles:shader:volume_sampling_method", "plugValueWidget:type", "GafferUI.PresetsPlugValueWidget" )
Gaffer.Metadata.registerValue( "attribute:cycles:shader:volume_sampling_method", "presetNames", IECore.StringVectorData( [ "Distance", "Equiangular", "Multiple-Importance" ] ) )
Gaffer.Metadata.registerValue( "attribute:cycles:shader:volume_sampling_method", "presetValues", IECore.StringVectorData( [ "distance", "equiangular", "multiple_importance" ] ) )

Gaffer.Metadata.registerValue( "attribute:cycles:shader:volume_interpolation_method", "label", "Volume Interpolation" )
Gaffer.Metadata.registerValue( "attribute:cycles:shader:volume_interpolation_method", "defaultValue", IECore.StringData( "linear" ) )
Gaffer.Metadata.registerValue(
	"attribute:cycles:shader:volume_interpolation_method",
	"description",
	"""
	Interpolation method to use for volumes.
	""",
)
Gaffer.Metadata.registerValue( "attribute:cycles:shader:volume_interpolation_method", "plugValueWidget:type", "GafferUI.PresetsPlugValueWidget" )
Gaffer.Metadata.registerValue( "attribute:cycles:shader:volume_interpolation_method", "presetNames", IECore.StringVectorData( [ "Linear", "Cubic" ] ) )
Gaffer.Metadata.registerValue( "attribute:cycles:shader:volume_interpolation_method", "presetValues", IECore.StringVectorData( [ "linear", "cubic" ] ) )

Gaffer.Metadata.registerValue( "attribute:cycles:shader:volume_step_rate", "label", "Volume Step Rate" )
Gaffer.Metadata.registerValue( "attribute:cycles:shader:volume_step_rate", "defaultValue", IECore.FloatData( 1 ) )
Gaffer.Metadata.registerValue(
	"attribute:cycles:shader:volume_step_rate",
	"description",
	"""
	Scale the distance between volume shader samples when rendering the volume
	(lower values give more accurate and detailed results, but also increased render time).
	""",
)

Gaffer.Metadata.registerValue( "attribute:cycles:shader:displacement_method", "label", "Displacement Method" )
Gaffer.Metadata.registerValue( "attribute:cycles:shader:displacement_method", "defaultValue", IECore.StringData( "bump" ) )
Gaffer.Metadata.registerValue(
	"attribute:cycles:shader:displacement_method",
	"description",
	"""
	Method to use for the displacement.
	""",
)
Gaffer.Metadata.registerValue( "attribute:cycles:shader:displacement_method", "plugValueWidget:type", "GafferUI.PresetsPlugValueWidget" )
Gaffer.Metadata.registerValue( "attribute:cycles:shader:displacement_method", "presetNames", IECore.StringVectorData( [ "Bump", "True", "Both" ] ) )
Gaffer.Metadata.registerValue( "attribute:cycles:shader:displacement_method", "presetValues", IECore.StringVectorData( [ "bump", "true", "both" ] ) )
