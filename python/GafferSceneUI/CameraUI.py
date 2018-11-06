##########################################################################
#
#  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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

import math
import functools

import imath

import IECoreScene

import Gaffer
import GafferUI
import GafferScene
import GafferSceneUI

filmFitMetadata = [

	"description",
	"""
	Determines how the size of the rendered image relates to the camera aperture. If the aspect
	ratios of the aperture and the output resolution are the same, then this has no effect,
	otherwise it dictates what method is used to preserve the pixel aspect ratio of the rendered
	image.

	Horizontal
	:   The frustum is adjusted so that the rendered image fills the full
		width of the aperture and aspect ratio is preserved.

	Vertical
	:   The frustum is adjusted so that the rendered image fills the full
		height of the aperture and aspect ratio is preserved.

	Fit
	:   Automatically picks Horizontal or Vertical such that all of the aperture is contained
		within the output image. This may result in seeing outside the aperture at the top and
		bottom or left and right.

	Fill
	:   Automatically picks Horizontal or Vertical such that the output image is fully covered by
		the aperture. Part of the aperture may be cropped off at the top and bottom or left and
		right.

	Distort
	:   Distorts the frustum so that the aperture is fitted exactly to the output display window,
		resulting in non-square pixels
	""",

	"preset:Horizontal", IECoreScene.Camera.FilmFit.Horizontal,
	"preset:Vertical", IECoreScene.Camera.FilmFit.Vertical,
	"preset:Fit", IECoreScene.Camera.FilmFit.Fit,
	"preset:Fill", IECoreScene.Camera.FilmFit.Fill,
	"preset:Distort", IECoreScene.Camera.FilmFit.Distort,

	"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
]

##########################################################################
# Metadata
##########################################################################

Gaffer.Metadata.registerNode(

	GafferScene.Camera,

	"description",
	"""
	Produces scenes containing a camera. To choose which camera is
	used for rendering, use a StandardOptions node.
	""",

	"layout:activator:perspective", lambda node : node["projection"].getValue() == "perspective",
	"layout:activator:perspectiveModeFOV", lambda node : node["perspectiveMode"].getValue() == GafferScene.Camera.PerspectiveMode.FieldOfView and node["projection"].getValue() == "perspective",
	"layout:activator:perspectiveModeFocalLength", lambda node : node["perspectiveMode"].getValue() == GafferScene.Camera.PerspectiveMode.ApertureFocalLength and node["projection"].getValue() == "perspective",
	"layout:activator:orthographic", lambda node : node["projection"].getValue() == "orthographic",
	"layout:activator:dof", lambda node : node["fStop"].getValue() != 0,


	plugs = {

		"sets" : [
			"layout:divider", True,
		],

		"projection" : [

			"description",
			"""
			The basic camera type.
			""",

			"preset:Perspective", "perspective",
			"preset:Orthographic", "orthographic",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

			"layout:divider", True,
		],

		"perspectiveMode" : [

			"description",
			"""
			You can control the view of a perspective camera using either a field of view ( which
			is a simple angle ), or as an aperture and focal length ( more natural for people who
			are used to physical cameras ).  In either case, the view will be stored on the camera
			as a focal length and aperture, but you can set or adjust it either way.
			""",

			"preset:Field Of View", GafferScene.Camera.PerspectiveMode.FieldOfView,
			"preset:Aperture and Focal Length", GafferScene.Camera.PerspectiveMode.ApertureFocalLength,

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

			"layout:visibilityActivator", "perspective",

		],

		"fieldOfView" : [

			"description",
			"""
			The horizontal field of view, specified in degrees.  When using a perspective projection
			with "Field Of View" control mode, this will control the focal length.
			""",

			"layout:visibilityActivator", "perspectiveModeFOV",
		],

		"apertureAspectRatio" : [

			"description",
			"""
			When using "Field Of View" control mode, the vertical field of view is controlled by
			maintaining this aspect ratio of the aperture.  The default value of 1 means that the
			horizontal and vertical field of view are the same.

			Note that the final field of view of a render from this camera will depend both on the
			camera settings, but also the resolution and film fit mode in the render settings.
			""",

			"layout:visibilityActivator", "perspectiveModeFOV",
		] ,

		"aperture" : [

			"description",
			"""
			When using "Aperture and Focal Length" control mode, this defines the X and Y dimensions
			of the aperture.

			Note that in CG applications, "Film Back" and aperture are used interchangeably - lenses
			are treated as perfectly symmetric boxes, with the aperture at the front the same size
			as the film back would be in a physical camera.

			Once you have aperture set to match a physical camera, you can use focal length to
			control the field of view, the same as you would with a physical camera.

			The units of aperture do not matter, as long as you use the same units for focal length.
			( By convention, millimeters ).

			A set of presets are provided matching some of the cameras frequently used as references,
			and some common cameras which are currently used, or you can use "Custom" to choose your
			own.

			Note that the final field of view of a render from this camera will depend both on the
			camera settings, but also the resolution and film fit mode in the render settings.
			""",

			"layout:visibilityActivator", "perspectiveModeFocalLength",

			"preset:Academy 35mm   	21.946 x 16.000",			imath.V2f( 21.946, 16 ),
			"preset:Super 35mm   	24.892 x 18.669",			imath.V2f( 24.892, 18.669 ),
			"preset:Micro Four Thirds   	17.30 x 13.00",		imath.V2f( 17.3, 13 ),
			"preset:APS-C   	22.30 x 14.90",					imath.V2f( 22.3, 14.9 ),
			"preset:Full Frame 35mm   	36.00 x 24.00",			imath.V2f( 36, 24 ),
			"preset:Alexa SXT 4:3 2.8k   	23.76 x 17.82",		imath.V2f( 23.76, 17.82 ),
			"preset:Alexa SXT Open Gate 3.4k   	28.25 x 18.17",	imath.V2f( 28.25, 18.17 ),
			"preset:Alexa 65 16:9 5.1k   	42.24 x 23.76",		imath.V2f( 42.24, 23.76 ),
			"preset:Alexa 65 Open Gate 6.5k   	54.12 x 25.58",	imath.V2f( 54.12, 25.58 ),
			"preset:RED EPIC-W 5K S35   	30.72 x 18.00",		imath.V2f( 30.72, 18 ),
			"preset:RED EPIC-W 8K S35   	29.90 x 15.77",		imath.V2f( 29.9, 15.77 ),

			"presetsPlugValueWidget:allowCustom", True,

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
		],

		"focalLength" : [

			"description",
			"""
			When using "Aperture and Focal Length" control mode, this defines the physical focal
			length of the camera.  This allows controlling the field of view using the same units
			used for physical cameras ( as long as your aperture is set appropriately in matching
			units ).
			""",

			"layout:visibilityActivator", "perspectiveModeFocalLength",

		],


		"orthographicAperture" : [

			"description",
			"""
			When using an orthographic projection, this defines the world space extent of the
			camera frustum in X and Y.
			""",

			"layout:visibilityActivator", "orthographic",
			"layout:divider", True,
		],

		"apertureOffset" : [

			"description",
			"""
			Create a skewed camera frustum by offsetting the aperture.  The offset is measured in
			aperture units.  In "Field Of View" control mode, the horizontal field of view is 1
			aperture unit.  In "Aperture and Focal Length" control mode, the aperture units match
			the aperture setting.  For an orthographic camera, aperture units are world space units.

			Only useful in special cases such as emulating a tilt-shift lens, rendering tiles for
			a large panorama, or matching plate images which have been asymmetrically cropped.
			""",
		],

		"fStop" : [

			"description",
			"""
			Setting a non-zero fStop will enable focal blur in renderers that support it.

			fStop specifies ratio of focal length divided by lens aperture.

			A higher fStop reduces the lens aperture, producing less blur.
			""",
			"layout:section", "Depth of Field",
		],

		"focalLengthWorldScale" : [

			"description",
			"""
			To use fStop to compute the lens aperture, we need to know focal length in world units.
			Since we usually store focal length in millimeters to match how we refer to real focal lengths
			and apertures, we need to know how to scale focal length into world units.

			We default to a value of 0.1, which scales from millimeters to centimeters.  This matches
			the default world units of Alembic and USD.  If your world units are decimeters or meters,
			then pick the corresponding option instead.

			If you are controlling the camera using a field of view instead of focal length, then the
			default aperture is just 1.  You should pick "Custom" and then pick a scale that matches
			a realistic aperture size ( ie. 0.036 meters )
			""",

			"preset:No Conversion	   ( 1.0 )", 1.0,
			"preset:Millimeters to Centimeters	   ( 0.1 )", 0.1,
			"preset:Millimeters to Decimeters	   ( 0.01 )", 0.01,
			"preset:Millimeters to Meters	   ( 0.001 )", 0.001,

			"presetsPlugValueWidget:allowCustom", True,

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

			"layout:activator", "dof",
			"layout:section", "Depth of Field",
		],

		"focusDistance" : [

			"description",
			"""
			When rendering with focal blur, focusDistance defines the world distance at which
			objects are in perfect focus.
			""",
			"layout:activator", "dof",
			"layout:section", "Depth of Field",
		],

		"clippingPlanes" : [

			"description",
			"""
			The near and far clipping planes, defining the range over which objects are visible
			to this camera.
			""",

		],

		"renderSettingOverrides" : [

			"description",
			"""
			Render settings specified here will override the global render settings.
			""",
			"layout:section", "Render Overrides",
			"compoundDataPlugValueWidget:editable", False,

		],

		"renderSettingOverrides.filmFit" : [

			"description",
			'Override the "filmFit" render option.  ' + filmFitMetadata[1],

		],

		"renderSettingOverrides.filmFit.value" : filmFitMetadata[2:],

		"renderSettingOverrides.shutter" : [

			"description",
			"""
			Override the "shutter" render option.  The interval over which the camera shutter is
			open.  Measured in frames, and specified relative to the frame being rendered.
			""",

		],

		"renderSettingOverrides.resolution" : [

			"description",
			"""
			Override the "renderResolution" render option.  The resolution of the image to be rendered.
			""",

		],

		"renderSettingOverrides.pixelAspectRatio" : [

			"description",
			"""
			Override the "pixelAspectRatio" render option.  The aspect ratio (x/y) of the pixels in
			the rendered image.
			""",

		],

		"renderSettingOverrides.resolutionMultiplier" : [

			"description",
			"""
			Override the "resolutionMultiplier" render option.  Multiplier applied to the render
			resolution.
			""",

		],

		"renderSettingOverrides.overscan" : [

			"description",
			"""
			Override the "overscan" render option.  Adds extra pixels to the sides of the rendered
			image.  This can be useful when camera shake or blur will be added as a post process.
			This plug just enables overscan as a whole - use the overscanTop, overscanBottom,
			overscanLeft and overscanRight plugs to specify the amount of overscan on each side of
			the image.
			""",

		],

		"renderSettingOverrides.overscanTop" : [

			"description",
			"""
			Override the "overscanTop" render option.  The amount of overscan at the top of the
			image. Specified as a 0-1 proportion of the original image height.
			""",

		],

		"renderSettingOverrides.overscanBottom" : [

			"description",
			"""
			Override the "overscanBottom" render option.  The amount of overscan at the bottom of the
			image. Specified as a 0-1 proportion of the original image height.
			""",

		],

		"renderSettingOverrides.overscanLeft" : [

			"description",
			"""
			Override the "overscanLeft" render option.  The amount of overscan at the left of the
			image. Specified as a 0-1 proportion of the original image height.
			""",

		],

		"renderSettingOverrides.overscanRight" : [

			"description",
			"""
			Override the "overscanRight" render option.  The amount of overscan at the right of the
			image. Specified as a 0-1 proportion of the original image height.
			""",

		],

		"renderSettingOverrides.cropWindow" : [

			"description",
			"""
			Override the "renderCropWindow" render option. Limits the render to a region of the
			image. The rendered image will have the same resolution as usual, but areas outside
			the crop will be rendered black. Coordinates range from 0,0 at the top left of the
			image to 1,1 at the bottom right. The crop window tool in the viewer may be used to
			set this interactively.
			""",

		],

		"renderSettingOverrides.depthOfField" : [

			"description",
			"""
			Override the "depthOfField" render option.  Forces depth of field to always ( or never )
			be rendered.  To get depth of field, you must also set an appropriate f-stop on this
			camera.
			""",

		],


	}

)

##########################################################################
# NodeEditor tool menu
##########################################################################

def __copyCamera( node, transform ) :

	with Gaffer.UndoScope( node.scriptNode() ) :

		s, h, r, t = imath.V3f(), imath.V3f(), imath.V3f(), imath.V3f()
		transform.extractSHRT( s, h, r, t )
		node["transform"]["translate"].setValue( t )
		node["transform"]["rotate"].setValue( r * 180.0 / math.pi )
		node["transform"]["scale"].setValue( s )

def __nodeEditorToolMenu( nodeEditor, node, menuDefinition ) :

	if not isinstance( node, GafferScene.Camera ) :
		return

	layout = nodeEditor.ancestor( GafferUI.CompoundEditor )
	if layout is None :
		return

	viewers = [ v for v in layout.editors( GafferUI.Viewer ) if isinstance( v.view(), GafferSceneUI.SceneView ) ]
	if not viewers :
		return

	for viewer in viewers :

		menuDefinition.append(

			"/Copy From Viewer" + ( "/" + viewer.getTitle() if len( viewers ) > 1 else "" ),
			{
				"command" : functools.partial( __copyCamera, node, viewer.view().viewportGadget().getCameraTransform() ),
				"active" : not Gaffer.MetadataAlgo.readOnly( node["transform"] ),
			}

		)

__nodeEditorToolMenuConnection = GafferUI.NodeEditor.toolMenuSignal().connect( __nodeEditorToolMenu )
