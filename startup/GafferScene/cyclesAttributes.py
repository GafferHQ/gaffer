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

	"attribute:cycles:visibility:camera" : {

		"defaultValue" : True,
		"description" :
		"""
		Whether or not the object is visible to camera
		rays. To hide an object completely, use the
		`scene:visible` attribute instead.
		""",
		"label" : "Camera",
		"layout:section" : "Visibility",

	},

	"attribute:cycles:visibility:diffuse" : {

		"defaultValue" : True,
		"description" :
		"""
		Whether or not the object is visible to diffuse
		rays.
		""",
		"label" : "Diffuse",
		"layout:section" : "Visibility",

	},

	"attribute:cycles:visibility:glossy" : {

		"defaultValue" : True,
		"description" :
		"""
		Whether or not the object is visible in
		glossy rays.
		""",
		"label" : "Glossy",
		"layout:section" : "Visibility",

	},

	"attribute:cycles:visibility:transmission" : {

		"defaultValue" : True,
		"description" :
		"""
		Whether or not the object is visible in
		transmission.
		""",
		"label" : "Transmission",
		"layout:section" : "Visibility",

	},

	"attribute:cycles:visibility:shadow" : {

		"defaultValue" : True,
		"description" :
		"""
		Whether or not the object is visible to shadow
		rays - whether it casts shadows or not.
		""",
		"label" : "Shadow",
		"layout:section" : "Visibility",

	},

	"attribute:cycles:visibility:scatter" : {

		"defaultValue" : True,
		"description" :
		"""
		Whether or not the object is visible to
		scatter rays.
		""",
		"label" : "Scatter",
		"layout:section" : "Visibility",

	},

	"attribute:cycles:use_holdout" : {

		"defaultValue" : False,
		"description" :
		"""
		Turns the object into a holdout matte.
		This only affects primary (camera) rays.
		""",
		"label" : "Use Holdout",
		"layout:section" : "Rendering",

	},

	"attribute:cycles:is_shadow_catcher" : {

		"defaultValue" : False,
		"description" :
		"""
		Turns the object into a shadow catcher.
		""",
		"label" : "Is Shadow Catcher",
		"layout:section" : "Rendering",

	},

	"attribute:cycles:shadow_terminator_shading_offset" : {

		"defaultValue" : 0.0,
		"description" :
		"""
		Push the shadow terminator towards the light to hide artifacts on low poly geometry.
		""",
		"label" : "Terminator Shading Offset",
		"layout:section" : "Rendering",

	},

	"attribute:cycles:shadow_terminator_geometry_offset" : {

		"defaultValue" : 0.0,
		"description" :
		"""
		Offset rays from the surface to reduce shadow terminator artifact on low poly geometry. Only affects triangles at grazing angles to light.
		""",
		"label" : "Terminator Geometry Offset",
		"layout:section" : "Rendering",

	},

	"attribute:cycles:is_caustics_caster" : {

		"defaultValue" : False,
		"description" :
		"""
		Cast Shadow Caustics.
		""",
		"label" : "Is Caustics Caster",
		"layout:section" : "Rendering",

	},

	"attribute:cycles:is_caustics_receiver" : {

		"defaultValue" : False,
		"description" :
		"""
		Receive Shadow Caustics.
		""",
		"label" : "Is Caustics Receiver",
		"layout:section" : "Rendering",

	},

	"attribute:cycles:max_level" : {

		"defaultValue" : 1,
		"description" :
		"""
		The max level of subdivision that can be
		applied.
		""",
		"label" : "Max Level",
		"layout:section" : "Subdivision",

	},

	"attribute:cycles:dicing_rate" : {

		"defaultValue" : 1.0,
		"description" :
		"""
		Multiplier for scene dicing rate.
		""",
		"label" : "Dicing Scale",
		"layout:section" : "Subdivision",

	},

	"attribute:cycles:adaptive_space" : {

		"defaultValue" : "pixel",
		"description" :
		"""
		How to adaptively subdivide the mesh.

		- Pixel : Subdivide polygons to reach a specified pixel size on screen.
		- Object : Subdivide to reach a specified edge length in object space.
		""",
		"label" : "Adaptive Space",
		"layout:section" : "Subdivision",

		"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",
		"presetNames" : IECore.StringVectorData( [ "Pixel", "Object" ] ),
		"presetValues" : IECore.StringVectorData( [ "pixel", "object" ] ),

	},

	"attribute:cycles:lightgroup" : {

		"defaultValue" : "",
		"description" :
		"""
		Lightgroup membership of lights or objects with emission.
		""",
		"label" : "Lightgroup",
		"layout:section" : "Rendering",

	},

	"attribute:cycles:volume_clipping" : {

		"defaultValue" : 0.001,
		"description" :
		"""
		Value under which voxels are considered empty space to
		optimize rendering.
		""",
		"label" : "Clipping",
		"layout:section" : "Volume",

	},

	"attribute:cycles:volume_step_size" : {

		"defaultValue" : 0.0,
		"description" :
		"""
		Distance between volume samples. When zero it is automatically
		estimated based on the voxel size.
		""",
		"label" : "Step Size",
		"layout:section" : "Volume",

	},

	"attribute:cycles:volume_object_space" : {

		"defaultValue" : False,
		"description" :
		"""
		Specify volume density and step size in object or world space.
		By default object space is used, so that the volume opacity and
		detail remains the same regardless of object scale.
		""",
		"label" : "Object Space",
		"layout:section" : "Volume",

	},

	"attribute:cycles:volume_velocity_scale" : {

		"defaultValue" : 1.0,
		"description" :
		"""
		Scales velocity vectors used in motion blur computation.
		""",
		"label" : "Velocity Scale",
		"layout:section" : "Volume",

	},

	"attribute:cycles:volume_precision" : {

		"defaultValue" : "full",
		"description" :
		"""
		Specifies volume data precision, lower values reduce
		memory consumption at the cost of detail.
		""",
		"label" : "Precision",
		"layout:section" : "Volume",

		"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",
		"presetNames" : IECore.StringVectorData( [ "Full", "Half" ] ),
		"presetValues" : IECore.StringVectorData( [ "full", "half" ] ),

	},

	"attribute:cycles:asset_name" : {

		"defaultValue" : "",
		"description" :
		"""
		Asset name for cryptomatte.
		""",
		"label" : "Asset Name",
		"layout:section" : "Object",

	},

	"attribute:cycles:shader:emission_sampling_method" : {

		"defaultValue" : "auto",
		"description" :
		"""
		Sampling strategy for emissive surfaces.
		""",
		"label" : "Emission Sampling Method",
		"layout:section" : "Shader",

		"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",
		"presetNames" : IECore.StringVectorData( [ "None", "Auto", "Front", "Back", "Front-Back" ] ),
		"presetValues" : IECore.StringVectorData( [ "none", "auto", "front", "back", "front_back" ] ),

	},

	"attribute:cycles:shader:use_transparent_shadow" : {

		"defaultValue" : True,
		"description" :
		"""
		Use transparent shadows for this material if it contains a Transparent BSDF,
		disabling will render faster but not give accurate shadows.
		""",
		"label" : "Transparent Shadow",
		"layout:section" : "Shader",

	},

	"attribute:cycles:shader:volume_sampling_method" : {

		"defaultValue" : "multiple_importance",
		"description" :
		"""
		Sampling method to use for volumes.
		""",
		"label" : "Volume Sampling",
		"layout:section" : "Shader",

		"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",
		"presetNames" : IECore.StringVectorData( [ "Distance", "Equiangular", "Multiple-Importance" ] ),
		"presetValues" : IECore.StringVectorData( [ "distance", "equiangular", "multiple_importance" ] ),

	},

	"attribute:cycles:shader:volume_interpolation_method" : {

		"defaultValue" : "linear",
		"description" :
		"""
		Interpolation method to use for volumes.
		""",
		"label" : "Volume Interpolation",
		"layout:section" : "Shader",

		"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",
		"presetNames" : IECore.StringVectorData( [ "Linear", "Cubic" ] ),
		"presetValues" : IECore.StringVectorData( [ "linear", "cubic" ] ),

	},

	"attribute:cycles:shader:volume_step_rate" : {

		"defaultValue" : 1.0,
		"description" :
		"""
		Scale the distance between volume shader samples when rendering the volume
		(lower values give more accurate and detailed results, but also increased render time).
		""",
		"label" : "Volume Step Rate",
		"layout:section" : "Shader",

	},

	"attribute:cycles:shader:displacement_method" : {

		"defaultValue" : "bump",
		"description" :
		"""
		Method to use for the displacement.
		""",
		"label" : "Displacement Method",
		"layout:section" : "Shader",

		"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",
		"presetNames" : IECore.StringVectorData( [ "Bump", "True", "Both" ] ),
		"presetValues" : IECore.StringVectorData( [ "bump", "true", "both" ] ),

	},

} )

Gaffer.Metadata.registerValue( "attribute:cycles:*", "category", "Cycles" )
