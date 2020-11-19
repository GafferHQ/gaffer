# -*- coding: utf-8 -*-

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

##########################################################################
# Metadata
##########################################################################

plugsMetadata = {

	"sets" : [

		"layout:divider", True,

	],

	"projection" : [

		"description",
		"""
		The base camera type.

		Supports two standard projections: orthographic and
		perspective. For less standard projections that require
		renderer-specific implementations, such as spherical, you
		will need to use a downstream CameraTweaks node to adjust
		this camera's parameters.
		""",

		"preset:Perspective", "perspective",
		"preset:Orthographic", "orthographic",

		"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		"layout:divider", True,

	],

	"perspectiveMode" : [

		"description",
		"""
		The input values to use in defining the perspective
		projection. They can be either a horizontal field of view
		(`fieldOfView`), or a film back/sensor (`aperture`) and
		focal length (`focalLength`). The latter two can take the
		exact measurements from a real camera and lens setup. With
		either perspective mode, perspective is stored as
		`aperture` and `focalLength` parameters on the camera.
		""",

		"preset:Field Of View", GafferScene.Camera.PerspectiveMode.FieldOfView,
		"preset:Aperture and Focal Length", GafferScene.Camera.PerspectiveMode.ApertureFocalLength,

		"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		"layout:visibilityActivator", "perspective",

	],

	"fieldOfView" : [

		"description",
		"""
		The horizontal field of view, in degrees.

		In the camera's parameters, projection is always stored as
		`aperture` and `focalLength`. When using the _Field of
		View_ perspective mode, the aperture has the fixed
		dimensions of `1, 1`, and this plug drives the
		`focalLength` parameter.
		""",

		"layout:visibilityActivator", "perspectiveModeFOV",

	],

	"apertureAspectRatio" : [

		"description",
		"""
		The vertical field of view, according to the ratio
		`(horizontal FOV) / (vertical FOV)`. A value of 1 would
		result in a square aperture, while a value of 1.778 would
		result in a 16:9 aperture.

		"Aperture" in this sense is equivalent to film back/sensor.

		The final projection of a render using this camera will
		depend on these settings in combination with the
		`resolution` and `filmFit` render settings.
		""",

		"layout:visibilityActivator", "perspectiveModeFOV",

	] ,

	"aperture" : [

		"description",
		"""
		The width and height of the aperture when using the
		_Aperture and Focal Length_ perspective mode. Use this in
		conjunction with a focal length to define the camera's
		equivalent field of view.

		"Aperture" here is equivalent to the film back/sensor on a
		real camera. A handful of default camera presets are
		provided, including Full Frame 35mm and several popular
		Alexa and RED bodies. Once the aperture is set, the focal
		length can then be adjusted on its own to control the field
		of view, just like on a real camera.

		When setting the aperture manually, the `x` and `y`
		dimensions can be measured in any unit of length, so long
		as they use the same unit as the focal length. You can
		safely follow convention and use millimeters for both.

		The final field of view of a render will depend on these
		settings in combination with the `resolution` and `filmFit`
		render options.
		""",

		"layout:visibilityActivator", "perspectiveModeFocalLength",

		"preset:Academy 35mm   	21.946 × 16.000",			imath.V2f( 21.946, 16 ),
		"preset:Super 35mm   	24.892 × 18.669",			imath.V2f( 24.892, 18.669 ),
		"preset:Micro Four Thirds   	17.30 × 13.00",		imath.V2f( 17.3, 13 ),
		"preset:APS-C   	22.30 × 14.90",					imath.V2f( 22.3, 14.9 ),
		"preset:Full Frame 35mm   	36.00 × 24.00",			imath.V2f( 36, 24 ),
		"preset:Alexa SXT 4:3 2.8k   	23.76 × 17.82",		imath.V2f( 23.76, 17.82 ),
		"preset:Alexa SXT Open Gate 3.4k   	28.25 × 18.17",	imath.V2f( 28.25, 18.17 ),
		"preset:Alexa 65 16:9 5.1k   	42.24 × 23.76",		imath.V2f( 42.24, 23.76 ),
		"preset:Alexa 65 Open Gate 6.5k   	54.12 × 25.58",	imath.V2f( 54.12, 25.58 ),
		"preset:RED EPIC-W 5K S35   	30.72 × 18.00",		imath.V2f( 30.72, 18 ),
		"preset:RED EPIC-W 8K S35   	29.90 × 15.77",		imath.V2f( 29.9, 15.77 ),

		"presetsPlugValueWidget:allowCustom", True,

		"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

	],

	"focalLength" : [

		"description",
		"""
		The focal length portion of the _Aperture and Focal Length_
		perspective mode. This is equivalent to the lens's focal
		length in a real camera setup. Use this in conjunction with
		the aperture to set the camera's equivalent field of view.
		Like on a real camera, the aperture is typically constant,
		and the focal length is then adjusted to control the field
		of view.

		This can be a distance in any unit of length, as long as
		you use the same unit for the aperture. You can safely
		follow convention and use millimeters for both.

		The final field of view of a render using this camera will
		depend on these settings in combination with the
		`resolution` and `filmFit` render options.
		""",

		"layout:visibilityActivator", "perspectiveModeFocalLength",

	],


	"orthographicAperture" : [

		"description",
		"""
		The width and height of the orthographic camera's aperture,
		in world space units.
		""",

		"layout:visibilityActivator", "orthographic",
		"layout:divider", True,

	],

	"apertureOffset" : [

		"description",
		"""
		Offsets the aperture parallel to the image plane, to
		achieve a skewed viewing frustum. The scale of the offset
		depends on the projection and perspective mode:

		- Perspective projection:
			- _Field Of View_ mode: 1 offset = 1 horizontal field
			of view.
			- _Aperture and Focal Length_ mode: 1 offset = 1
			aperture unit of measure (for example, 1mm).
		- Orthographic projection: 1 offset = 1 world space unit.

		For use in special cases, such as simulating a tilt-shift
		lens, rendering tiles for a large panorama, or matching a
		plate that has been asymmetrically cropped.
		""",

	],

	"fStop" : [

		"description",
		"""
		The setting equivalent to the f-number on a camera, which ultimately determines the strength of the depth of field blur. A lower value produces more blur. As in a real camera, `fStop` is defined as `focalLength / lens aperture`.

		To enable depth of field blur (if your renderer supports it), give this plug a value greater than 0, and, on a downstream StandardOptions node, enable the _Depth Of Field_ plug and turn it on.

		""",
		"layout:section", "Depth of Field",

	],

	"focalLengthWorldScale" : [

		"description",
		"""
		The scale to convert from focal length units to world space
		units. Combined with f-stop to calculate the lens aperture.
		Set this to scale the lens units into scene units, to
		ensure the depth of field blur correctly scales to the
		scene. Once this plug is set, the `fStop` plug can be
		adjusted to match a real-world lens setting.

		For example, given a lens with a focal length in mm, and a
		scene that uses decimeters for its world space units, the
		_Millimeters to Decimeters_ preset would provide the proper
		conversion.

		The default value of 0.1 scales millimeter (default focal
		length unit) to centimeter (default world space unit of
		Alembic and USD scene formats). Other default presets for
		scaling to decimeter or meter are also available.

		If using _Field Of View_ projection mode, you won't have a
		focal length plug to work with, and the aperture size will
		be (1,1). To compensate, select _Custom_ and then input a
		value that scales the scene unit of measure to a realistic
		aperture size. For example, `3.5` would convert 1
		centimeter (Alembic/USD default) to 35mm, which would
		simulate a 35mm lens.
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
		The distance from the camera at which objects are in
		perfect focus, in world space units.
		""",
		"layout:activator", "dof",
		"layout:section", "Depth of Field",
	],

	"clippingPlanes" : [

		"description",
		"""
		The near and far clipping planes, defining a region of
		forward depth within which objects are visible to this
		camera.
		""",

	],

	"renderSettingOverrides" : [

		"description",
		"""
		Render settings specified here will override their
		corresponding global render options.
		""",
		"layout:section", "Render Overrides",
		"compoundDataPlugValueWidget:editable", False,

	],

	"visualiserAttributes" : [

			"description",
			"""
			Attributes that affect the visualisation of this camera in the Viewer.
			""",

			"layout:section", "Visualisation",

	],

	"visualiserAttributes.scale" : [

			"description",
			"""
			Scales non-geometric visualisations in the viewport to make them
			easier to work with.
			""",

	],

	"visualiserAttributes.frustum" : [

			"description",
			"""
			Controls whether the camera draws a visualisation of its frustum.
			"""

	],

	"visualiserAttributes.frustum.value" : [

			"preset:Off", "off",
			"preset:When Selected", "whenSelected",
			"preset:On", "on",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget"
	]

}

__sourceMetadata = GafferSceneUI.StandardOptionsUI.plugsMetadata

## Start with a special entry: the filmFit option presets are reused
# without modification
__overrideMetadata = {
	"renderSettingOverrides.filmFit.value": __sourceMetadata["options.filmFit.value"]
}

## The plug names from StandardOptionsUI that the Camera node actually
# overrides; not all of their names match, so we need to provide
# the replacement names too
__plugsToOverride = {
	"options.filmFit": "renderSettingOverrides.filmFit",
	"options.shutter": "renderSettingOverrides.shutter",
	"options.renderResolution": "renderSettingOverrides.resolution",
	"options.pixelAspectRatio": "renderSettingOverrides.pixelAspectRatio",
	"options.resolutionMultiplier": "renderSettingOverrides.resolutionMultiplier",
	"options.overscan": "renderSettingOverrides.overscan",
	"options.overscanLeft": "renderSettingOverrides.overscanLeft",
	"options.overscanRight": "renderSettingOverrides.overscanRight",
	"options.overscanTop": "renderSettingOverrides.overscanTop",
	"options.overscanBottom": "renderSettingOverrides.overscanBottom",
	"options.renderCropWindow": "renderSettingOverrides.cropWindow",
	"options.depthOfField": "renderSettingOverrides.depthOfField",
}

## Use the key names from the override dict, but reuse the plug
# description text from the source dict
for sourcePlug, overridePlug in __plugsToOverride.items() :

	plugMetadata = __sourceMetadata[ sourcePlug ]

	__overrideMetadata[ overridePlug ] = [
		plugMetadata[0],
		"Overrides the `{option}` render option:\n\n{description}".format(
			option = sourcePlug.replace( "options.", ""),
			# We assume the second element is the plug description
			description = plugMetadata[1]
		)
	]

plugsMetadata.update( __overrideMetadata )

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

	plugs = plugsMetadata

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
