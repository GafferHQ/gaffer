##########################################################################
#
#  Copyright (c) 2023, Cinesite VFX Ltd. All rights reserved.
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

import imath

import Gaffer

Gaffer.Metadata.registerValues( {

	"option:render:camera" : [

		"defaultValue", "",
		"description",
		"""
		The primary camera to be used for rendering. If this
		is not specified, then a default orthographic camera
		positioned at the origin is used.
		""",
		"label", "Camera",

	],

	"option:render:resolution" : [

		"defaultValue", imath.V2i( 1024, 778 ),
		"description",
		"""
		The resolution of the image to be rendered.
		""",
		"label", "Resolution",

	],

	"option:render:resolutionMultiplier" : [

		"defaultValue", 1.0,
		"description",
		"""
		Multiplies the resolution of the render by this amount.
		""",
		"label", "Resolution Multiplier",

	],

	"option:render:deformationBlur" : [

		"defaultValue", False,
		"description",
		"""
		Whether or not deformation motion is taken into
		account in the rendered image. To specify the
		number of deformation segments to use for each
		object in the scene, use a StandardAttributes
		node with appropriate filters.
		""",
		"label", "Deformation Blur",

	],

	"option:render:transformBlur" : [

		"defaultValue", False,
		"description",
		"""
		Whether or not transform motion is taken into
		account in the rendered image. To specify the
		number of transform segments to use for each
		object in the scene, use a StandardAttributes
		node with appropriate filters.
		""",
		"label", "Transform Blur",

	],

	"option:render:shutter" : [

		"defaultValue", imath.V2f( -0.25, 0.25 ),
		"description",
		"""
		The interval over which the camera shutter is open. Measured
		in frames, and specified relative to the frame being rendered.
		""",
		"label", "Shutter",

	],

	"option:render:defaultRenderer" : [

		"defaultValue", "",
		"description",
		"""
		Specifies the default renderer to be used by the Render and
		InteractiveRender nodes.
		""",
		"label", "Renderer",

	],

	"option:render:inclusions" : [

		"defaultValue", "/",
		"description",
		"""
		A set expression that limits the objects included in the render to only those matched
		and their descendants. Objects not matched by the set expression will be pruned from
		the scene. Cameras are included by default and do not need to be specified here.
		""",
		"label", "Inclusions",

	],

	"option:render:exclusions" : [

		"defaultValue", "",
		"description",
		"""
		A set expression that excludes the matched objects from the render. Exclusions
		affect both `inclusions` and `additionalLights` and cause the matching objects and
		their descendants to be pruned from the scene.
		""",
		"label", "Exclusions",

	],

	"option:render:additionalLights" : [

		"defaultValue", "",
		"description",
		"""
		A set expression that specifies additional lights to be included in the render.
		This differs from `inclusions` as only lights and light filters will be matched
		by this set expression.
		""",
		"label", "Additional Lights",

	],

	"option:render:cameraInclusions" : [

		"defaultValue", "/",
		"description",
		"""
		A set expression that limits the objects visible to camera rays to only those matched
		and their descendants. Camera visibility attributes authored in the scene take
		precedence over this option.

		For shadow, reflection and reflectionAlpha pass types, this specifies objects that
		catch shadows or reflections.
		""",
		"label", "Camera Inclusions / Catchers",

	],

	"option:render:cameraExclusions" : [

		"defaultValue", "",
		"description",
		"""
		A set expression that excludes the matched objects and their descendants from camera
		ray visibility. Camera visibility attributes authored in the scene take precedence
		over this option.

		Typically, this is used to exclude descendants of locations in `cameraInclusions`,
		as locations not specified in `cameraInclusions` already default to being excluded
		from camera ray visibility.

		For shadow, reflection and reflectionAlpha pass types, this specifies objects that
		cast shadows or reflections. Shadow or reflection visibility attributes authored
		in the scene take precedence over this option.
		""",
		"label", "Camera Exclusions / Casters",

	],

	"option:render:matteInclusions" : [

		"defaultValue", "",
		"description",
		"""
		A set expression that specifies objects that should be treated as matte (holdout)
		objects along with their descendants. Matte attributes authored in the scene take
		precedence over this option.
		""",
		"label", "Matte Inclusions",

	],

	"option:render:matteExclusions" : [

		"defaultValue", "",
		"description",
		"""
		A set expression that excludes the matched objects and their descendants from being
		treated as matte (holdout) objects. Matte attributes authored in the scene take
		precedence over this option.

		Typically, this is used to exclude descendants of locations in `matteInclusions`,
		as locations not specified in `matteInclusions` already default to not being
		treated as matte objects.
		""",
		"label", "Matte Exclusions",

	],

} )
