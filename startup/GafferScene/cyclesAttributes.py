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


Gaffer.Metadata.registerValues( {

	"attribute:cycles:visibility:camera" : [

		"defaultValue", True,
		"description",
		"""
		Whether or not the object is visible to camera
		rays. To hide an object completely, use the
		`scene:visible` attribute instead.
		""",
		"label", "Camera",

	],

	"attribute:cycles:visibility:diffuse" : [

		"defaultValue", True,
		"description",
		"""
		Whether or not the object is visible to diffuse
		rays.
		""",
		"label", "Diffuse",

	],

	"attribute:cycles:visibility:glossy" : [

		"defaultValue", True,
		"description",
		"""
		Whether or not the object is visible in
		glossy rays.
		""",
		"label", "Glossy",

	],

	"attribute:cycles:visibility:transmission" : [

		"defaultValue", True,
		"description",
		"""
		Whether or not the object is visible in
		transmission.
		""",
		"label", "Transmission",

	],

	"attribute:cycles:visibility:shadow" : [

		"defaultValue", True,
		"description",
		"""
		Whether or not the object is visible to shadow
		rays - whether it casts shadows or not.
		""",
		"label", "Shadow",

	],

	"attribute:cycles:visibility:scatter" : [

		"defaultValue", True,
		"description",
		"""
		Whether or not the object is visible to
		scatter rays.
		""",
		"label", "Scatter",

	],

	"attribute:cycles:use_holdout" : [

		"defaultValue", False,
		"description",
		"""
		Turns the object into a holdout matte.
		This only affects primary (camera) rays.
		""",
		"label", "Use Holdout",

	],

	"attribute:cycles:is_shadow_catcher" : [

		"defaultValue", False,
		"description",
		"""
		Turns the object into a shadow catcher.
		""",
		"label", "Is Shadow Catcher",

	],

	"attribute:cycles:shadow_terminator_shading_offset" : [

		"defaultValue", 0.0,
		"description",
		"""
		Push the shadow terminator towards the light to hide artifacts on low poly geometry.
		""",
		"label", "Terminator Shading Offset",

	],

	"attribute:cycles:shadow_terminator_geometry_offset" : [

		"defaultValue", 0.0,
		"description",
		"""
		Offset rays from the surface to reduce shadow terminator artifact on low poly geometry. Only affects triangles at grazing angles to light.
		""",
		"label", "Terminator Geometry Offset",

	],

	"attribute:cycles:lightgroup" : [

		"defaultValue", "",
		"description",
		"""
		Set the lightgroup of an object with emission.
		""",
		"label", "Lightgroup",

	],

	"attribute:cycles:is_caustics_caster" : [

		"defaultValue", False,
		"description",
		"""
		Cast Shadow Caustics.
		""",
		"label", "Is Caustics Caster",

	],

	"attribute:cycles:is_caustics_receiver" : [

		"defaultValue", False,
		"description",
		"""
		Receive Shadow Caustics.
		""",
		"label", "Is Caustics Receiver",

	],

	"attribute:cycles:max_level" : [

		"defaultValue", 1,
		"description",
		"""
		The max level of subdivision that can be
		applied.
		""",
		"label", "Max Level",

	],

	"attribute:cycles:dicing_rate" : [

		"defaultValue", 1.0,
		"description",
		"""
		Multiplier for scene dicing rate.
		""",
		"label", "Dicing Scale",

	],

	"attribute:cycles:volume_clipping" : [

		"defaultValue", 0.001,
		"description",
		"""
		Value under which voxels are considered empty space to
		optimize rendering.
		""",
		"label", "Clipping",

	],

	"attribute:cycles:volume_step_size" : [

		"defaultValue", 0.0,
		"description",
		"""
		Distance between volume samples. When zero it is automatically
		estimated based on the voxel size.
		""",
		"label", "Step Size",

	],

	"attribute:cycles:volume_object_space" : [

		"defaultValue", True,
		"description",
		"""
		Specify volume density and step size in object or world space.
		By default object space is used, so that the volume opacity and
		detail remains the same regardless of object scale.
		""",
		"label", "Object Space",

	],

	"attribute:cycles:asset_name" : [

		"defaultValue", "",
		"description",
		"""
		Asset name for cryptomatte.
		""",
		"label", "Asset Name",

	],

	"attribute:cycles:shader:emission_sampling_method" : [

		"defaultValue", "auto",
		"description",
		"""
		Sampling strategy for emissive surfaces.
		""",
		"label", "Emission Sampling Method",
		"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
		"presetNames", IECore.StringVectorData( [ "None", "Auto", "Front", "Back", "Front-Back" ] ),
		"presetValues", IECore.StringVectorData( [ "none", "auto", "front", "back", "front_back" ] ),

	],

	"attribute:cycles:shader:use_transparent_shadow" : [

		"defaultValue", True,
		"description",
		"""
		Use transparent shadows for this material if it contains a Transparent BSDF,
		disabling will render faster but not give accurate shadows.
		""",
		"label", "Transparent Shadow",

	],

	"attribute:cycles:shader:heterogeneous_volume" : [

		"defaultValue", True,
		"description",
		"""
		Disabling this when using volume rendering, assume volume has the same density
		everywhere (not using any textures), for faster rendering.
		""",
		"label", "Heterogeneous Volume",

	],

	"attribute:cycles:shader:volume_sampling_method" : [

		"defaultValue", "multiple_importance",
		"description",
		"""
		Sampling method to use for volumes.
		""",
		"label", "Volume Sampling",
		"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
		"presetNames", IECore.StringVectorData( [ "Distance", "Equiangular", "Multiple-Importance" ] ),
		"presetValues", IECore.StringVectorData( [ "distance", "equiangular", "multiple_importance" ] ),

	],

	"attribute:cycles:shader:volume_interpolation_method" : [

		"defaultValue", "linear",
		"description",
		"""
		Interpolation method to use for volumes.
		""",
		"label", "Volume Interpolation",
		"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
		"presetNames", IECore.StringVectorData( [ "Linear", "Cubic" ] ),
		"presetValues", IECore.StringVectorData( [ "linear", "cubic" ] ),

	],

	"attribute:cycles:shader:volume_step_rate" : [

		"defaultValue", 1.0,
		"description",
		"""
		Scale the distance between volume shader samples when rendering the volume
		(lower values give more accurate and detailed results, but also increased render time).
		""",
		"label", "Volume Step Rate",

	],

	"attribute:cycles:shader:displacement_method" : [

		"defaultValue", "bump",
		"description",
		"""
		Method to use for the displacement.
		""",
		"label", "Displacement Method",
		"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
		"presetNames", IECore.StringVectorData( [ "Bump", "True", "Both" ] ),
		"presetValues", IECore.StringVectorData( [ "bump", "true", "both" ] ),

	],

} )
