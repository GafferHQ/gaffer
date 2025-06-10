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

import IECore
import IECoreScene

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
		"layout:section", "Camera",

		"plugValueWidget:type", "GafferSceneUI.ScenePathPlugValueWidget",
		"path:valid", True,
		"scenePathPlugValueWidget:setNames", IECore.StringVectorData( [ "__cameras" ] ),
		"scenePathPlugValueWidget:setsLabel", "Show only cameras",

	],

	"option:render:filmFit" : [

		"defaultValue", 0,
		"description",
		"""
		How the aperture gate (the frame defined by the aperture) will
		fit into the resolution gate (the framed defined by the data
		window). Fitting is applied only if the respective aspect
		ratios of the aperture and the resolution are different. The
		following fitting modes are available:

		- _Horizontal:_ The aperture gate will fit horizontally between
		the left/right edges of the resolution gate, while preserving
		its aspect ratio. If the aperture's aspect ratio is larger than
		the resolution's, the top/bottom edges of the aperture will be
		cropped. If it's smaller, then the top/bottom edges will
		capture extra vertical scene content.
		- _Vertical:_ The aperture gate will fit vertically between the
		top/bottom edges of the resolution gate, while preserving its
		aspect ratio. If the aperture's aspect ratio is larger than the
		resolution's, the left/right edges of the aperture will be
		cropped. If it's smaller, then the left/right edges will
		capture more horizontal scene content.
		- _Fit_: The aperture gate will fit horizontally (like
		_Horizontal_ mode) or vertically (like _Vertical_ mode) inside
		the resolution gate to avoid cropping the aperture, while
		preserving its aspect ratio. If the two gates' aspect ratios
		differ, the aperture will capture extra horizontal or vertical
		scene content.
		- _Fill:_ The aperture gate will fill the resolution gate such
		that none of the aperture captures extra scene content, while
		preserving its aspect ratio. In other words, it will make the
		opposite choice of the _Fit_ mode. If the two gates' aspect
		ratios differ, the aperture will be horizontally or vertically
		cropped.
		- _Distort:_ The aperture gate will match the size of the
		resolution gate. If their aspect ratios differ, the resulting
		image will appear vertically or horizontally stretched or
		squeezed.
		""",
		"label", "Film Fit",
		"layout:section", "Camera",

		"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
		"presetNames", IECore.StringVectorData( [ "Horizontal", "Vertical", "Fit", "Fill", "Distort" ] ),
		"presetValues", IECore.IntVectorData( [ IECoreScene.Camera.FilmFit.Horizontal, IECoreScene.Camera.FilmFit.Vertical, IECoreScene.Camera.FilmFit.Fit, IECoreScene.Camera.FilmFit.Fill, IECoreScene.Camera.FilmFit.Distort ] ),

	],

	"option:render:resolution" : [

		"defaultValue", imath.V2i( 1024, 778 ),
		"description",
		"""
		The resolution of the image to be rendered.
		""",
		"label", "Resolution",
		"layout:section", "Camera",

	],

	"option:render:pixelAspectRatio" : [

		"defaultValue", 1.0,
		"description",
		"""
		The `width / height` aspect ratio of the individual pixels in
		the rendered image.
		""",
		"label", "Pixel Aspect Ratio",
		"layout:section", "Camera",

	],

	"option:render:resolutionMultiplier" : [

		"defaultValue", 1.0,
		"description",
		"""
		Multiplies the resolution of the render by this amount.
		""",
		"label", "Resolution Multiplier",
		"layout:section", "Camera",

	],

	"option:render:cropWindow" : [

		"defaultValue", imath.Box2f( imath.V2f( 0, 0 ), imath.V2f( 1, 1 ) ),
		"minValue", imath.V2f( 0, 0 ),
		"maxValue", imath.V2f( 1, 1 ),
		"description",
		"""
		Limits the render to a region of the image. The rendered image
		will have the same resolution as usual, but areas outside the
		crop will be rendered black. Coordinates range from (0,0) at
		the top-left of the image to (1,1) at the bottom-right. The
		crop window tool in the viewer may be used to set this
		interactively.
		""",
		"label", "Crop Window",
		"layout:section", "Camera",

	],

	"option:render:overscan" : [

		"defaultValue", False,
		"description",
		"""
		Whether to enable overscan, which adds extra pixels to the
		sides of the rendered image.

		Overscan can be useful when camera shake or blur will be added
		as a post-process. This plug just enables overscan as a whole –
		use the `render:overscanTop`, `render:overscanBottom`, `render:overscanLeft` and
		`render:overscanRight` options to specify the amount of overscan on
		each side of the image.
		""",
		"label", "Overscan",
		"layout:section", "Camera",

	],

	"option:render:overscanTop" : [

		"defaultValue", 0.0,
		"minValue", 0.0,
		"maxValue", 1.0,
		"description",
		"""
		The amount of overscan at the top of the image. Specified as a
		0-1 proportion of the original image height.
		""",
		"label", "Overscan Top",
		"layout:section", "Camera",

	],

	"option:render:overscanBottom" : [

		"defaultValue", 0.0,
		"minValue", 0.0,
		"maxValue", 1.0,
		"description",
		"""
		The amount of overscan at the bottom of the image. Specified as
		a 0-1 proportion of the original image height.
		""",
		"label", "Overscan Bottom",
		"layout:section", "Camera",

	],

	"option:render:overscanLeft" : [

		"defaultValue", 0.0,
		"minValue", 0.0,
		"maxValue", 1.0,
		"description",
		"""
		The amount of overscan at the left of the image. Specified as a
		0-1 proportion of the original image width.
		""",
		"label", "Overscan Left",
		"layout:section", "Camera",

	],

	"option:render:overscanRight" : [

		"defaultValue", 0.0,
		"minValue", 0.0,
		"maxValue", 1.0,
		"description",
		"""
		The amount of overscan at the right of the image. Specified as
		a 0-1 proportion of the original image width.
		""",
		"label", "Overscan Right",
		"layout:section", "Camera",

	],

	"option:render:depthOfField" : [

		"defaultValue", False,
		"description",
		"""
		Whether to render with depth of field. To ensure the effect is
		visible, you must also set an f-stop value greater than 0 on
		this camera.
		""",
		"label", "Depth Of Field",
		"layout:section", "Camera",

	],

	"option:render:defaultRenderer" : [

		"defaultValue", "",
		"description",
		"""
		Specifies the default renderer to be used by the Render and
		InteractiveRender nodes.
		""",
		"label", "Default Renderer",
		"layout:section", "Renderer",

	],

	"option:render:includedPurposes" : [

		"defaultValue", IECore.StringVectorData( [ "default", "render" ] ),
		"description",
		"""
		Limits the objects included in the render according to the values of their `usd:purpose`
		attribute. The "Default" purpose includes all objects which have no `usd:purpose` attribute;
		other than for debugging, there is probably no good reason to omit it.

		> Tip : Use the USDAttributes node to assign the `usd:purpose` attribute.
		""",
		"label", "Included Purposes",
		"layout:section", "Render Set",

		"plugValueWidget:type", "GafferSceneUI.StandardOptionsUI._IncludedPurposesPlugValueWidget",

	],

	"option:render:inclusions" : [

		"defaultValue", "/",
		"description",
		"""
		A set expression that limits the objects included in the render to only those matched
		and their descendants. Objects not matched by the set expression will be pruned from
		the scene.

		> Tip : Cameras are included by default and do not need to be specified here.
		""",
		"label", "Inclusions",
		"layout:section", "Render Set",

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
		"layout:section", "Render Set",

	],

	"option:render:additionalLights" : [

		"defaultValue", "",
		"description",
		"""
		A set expression that specifies additional lights to be included in the render.
		This differs from `inclusions` in that only lights and light filters will be
		matched by this set expression.
		""",
		"label", "Additional Lights",
		"layout:section", "Render Set",

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
		## \todo: The full version of this label would be "Camera Inclusions / Catchers" but it
		# is slightly too long for the standard Node Editor label width on some combinations of
		# OS & desktop environment, such that some users see the whole label, while it is truncated
		# for others. We should look into whether shipping a standard font with Gaffer would reduce
		# this ambiguity.
		"label", "Camera Inclusions",
		"layout:section", "Visibility Set",

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
		"label", "Camera Exclusions",
		"layout:section", "Visibility Set",

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
		"layout:section", "Visibility Set",

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
		"layout:section", "Visibility Set",

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
		"label", "Transform",
		"layout:section", "Motion Blur",

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
		"label", "Deformation",
		"layout:section", "Motion Blur",

	],

	"option:render:shutter" : [

		"defaultValue", imath.V2f( -0.25, 0.25 ),
		"description",
		"""
		The interval over which the camera shutter is open. Measured
		in frames, and specified relative to the frame being rendered.
		""",
		"label", "Shutter",
		"layout:section", "Motion Blur",

	],

	"option:sampleMotion" : [

		"defaultValue", True,
		"description",
		"""
		Whether to actually render motion blur. Disabling this
		setting while motion blur is set up produces a render where
		there is no blur, but there is accurate motion information.
		Useful for rendering motion vector passes.
		""",
		"label", "Sample Motion",
		"layout:section", "Motion Blur",

	],

	"option:render:renderManifestFilePath" : [

		"defaultValue", "",
		"description",
		"""
		Specifies a file to write a matching ID manifest to, when
		rendering an ID aov in a batch render. This is needed to use
		the Image Selection Tool with batch renders (interactive
		renders just need an ID aov).
		""",
		"label", "File Path",
		"layout:section", "Render Manifest",

	],

	"option:render:performanceMonitor" : [

		"defaultValue", False,
		"description",
		"""
		Enables a performance monitor and uses it to output
		statistics about scene generation performance.
		""",
		"label", "Performance Monitor",
		"layout:section", "Statistics",

	],

} )
