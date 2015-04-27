##########################################################################
#
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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
import GafferUI
import GafferScene

##########################################################################
# Metadata
##########################################################################

Gaffer.Metadata.registerNode(

	GafferScene.StandardOptions,

	"description",
	"""
	Specifies the standard options (global settings) for the
	scene. These should be respected by all renderers.
	""",

	plugs = {

		# camera plugs

		"options.renderCamera" : [

			"description",
			"""
			The primary camera to be used for rendering. If this
			is not specified, then a default orthographic camera
			positioned at the origin is used.
			""",

		],

		"options.renderResolution" : [

			"description",
			"""
			The resolution of the image to be rendered. Use the
			resolution multiplier as a convenient way to temporarily
			render at multiples of this resolution.
			""",

		],

		"options.pixelAspectRatio" : [

			"description",
			"""
			The aspect ratio (x/y) of the pixels in the rendered image.
			""",

		],

		"options.resolutionMultiplier" : [

			"description",
			"""
			Multiplier applied to the render resolution.
			""",

		],

		"options.renderCropWindow" : [

			"description",
			"""
			Limits the render to a region of the image. The rendered
			image will have the same resolution as usual, but areas
			outside the crop will be rendered black. Coordinates
			range from 0,0 at the top left of the image to 1,1 at the
			bottom right. The crop window tool in the viewer may be
			used to set this interactively.
			""",

		],

		"options.overscan" : [

			"description",
			"""
			Adds extra pixels to the sides of the rendered image.
			This can be useful when camera shake or blur will be
			added as a post process. This plug just enables overscan
			as a whole - use the overscanTop, overscanBottom, overscanLeft
			and overscanRight plugs to specify the amount of overscan
			on each side of the image.
			""",

		],

		"options.overscanTop" : [

			"description",
			"""
			The amount of overscan at the top of the image. Specified
			as a 0-1 proportion of the original image height.
			""",

		],

		"options.overscanBottom" : [

			"description",
			"""
			The amount of overscan at the bottom of the image. Specified
			as a 0-1 proportion of the original image height.
			""",

		],

		"options.overscanLeft" : [

			"description",
			"""
			The amount of overscan at the left of the image. Specified
			as a 0-1 proportion of the original image width.
			""",

		],

		"options.overscanRight" : [

			"description",
			"""
			The amount of overscan at the right of the image. Specified
			as a 0-1 proportion of the original image width.
			""",

		],

		# motion blur plugs

		"options.cameraBlur" : [

			"description",
			"""
			Whether or not camera motion is taken into
			account in the renderered image. To specify the
			number of segments to use for camera motion, use
			a StandardAttributes node filtered for the camera.
			""",

		],

		"options.transformBlur" : [

			"description",
			"""
			Whether or not transform motion is taken into
			account in the renderered image. To specify the
			number of transform segments to use for each
			object in the scene, use a StandardAttributes node
			with appropriate filters.
			""",

		],

		"options.deformationBlur" : [

			"description",
			"""
			Whether or not deformation motion is taken into
			account in the renderered image. To specify the
			number of deformation segments to use for each
			object in the scene, use a StandardAttributes node
			with appropriate filters.
			""",

		],

		"options.shutter" : [

			"description",
			"""
			The interval over which the camera shutter is open.
			Measured in frames, and specified relative to the
			frame being rendered.
			""",

		],

	}

)

##########################################################################
# PlugValueWidgets
##########################################################################

## \todo This is getting used in a few places now - maybe put it in one
# place? Maybe a static method on NumericWidget?
def __floatToString( f ) :

	return ( "%.4f" % f ).rstrip( '0' ).rstrip( '.' )

def __cameraSummary( plug ) :

	info = []
	if plug["renderCamera"]["enabled"].getValue() :
		info.append( plug["renderCamera"]["value"].getValue() )
	if plug["renderResolution"]["enabled"].getValue() :
		resolution = plug["renderResolution"]["value"].getValue()
		info.append( "%dx%d" % ( resolution[0], resolution[1] ) )
	if plug["pixelAspectRatio"]["enabled"].getValue() :
		pixelAspectRatio = plug["pixelAspectRatio"]["value"].getValue()
		info.append( "Aspect %s" % __floatToString( pixelAspectRatio ) )
	if plug["resolutionMultiplier"]["enabled"].getValue() :
		resolutionMultiplier = plug["resolutionMultiplier"]["value"].getValue()
		info.append( "Mult %s" % __floatToString( resolutionMultiplier ) )
	if plug["renderCropWindow"]["enabled"].getValue() :
		crop = plug["renderCropWindow"]["value"].getValue()
		info.append( "Crop %s,%s-%s,%s" % tuple( __floatToString( x ) for x in ( crop.min.x, crop.min.y, crop.max.x, crop.max.y ) ) )
	if plug["overscan"]["enabled"].getValue() :
		info.append( "Overscan %s" % ( "On" if plug["overscan"]["value"].getValue() else "Off" ) )

	return ", ".join( info )

def __motionBlurSummary( plug ) :

	info = []
	if plug["cameraBlur"]["enabled"].getValue() :
		info.append( "Camera " + ( "On" if plug["cameraBlur"]["value"].getValue() else "Off" ) )
	if plug["transformBlur"]["enabled"].getValue() :
		info.append( "Transform " + ( "On" if plug["transformBlur"]["value"].getValue() else "Off" ) )
	if plug["deformationBlur"]["enabled"].getValue() :
		info.append( "Deformation " + ( "On" if plug["deformationBlur"]["value"].getValue() else "Off" ) )
	if plug["shutter"]["enabled"].getValue() :
		info.append( "Shutter " + str( plug["shutter"]["value"].getValue() ) )

	return ", ".join( info )

GafferUI.PlugValueWidget.registerCreator(

	GafferScene.StandardOptions,
	"options",
	GafferUI.SectionedCompoundDataPlugValueWidget,
	sections = (

		{
			"label" : "Camera",
			"summary" : __cameraSummary,
			"namesAndLabels" : (
				( "render:camera", "Camera" ),
				( "render:resolution", "Resolution" ),
				( "render:pixelAspectRatio", "Pixel Aspect Ratio" ),
				( "render:resolutionMultiplier", "Resolution Multiplier" ),
				( "render:cropWindow", "Crop Window" ),
				( "render:overscan", "Overscan" ),
				( "render:overscanTop", "Overscan Top" ),
				( "render:overscanBottom", "Overscan Bottom" ),
				( "render:overscanLeft", "Overscan Left" ),
				( "render:overscanRight", "Overscan Right" ),
			),
		},

		{
			"label" : "Motion Blur",
			"summary" : __motionBlurSummary,
			"namesAndLabels" : (
				( "render:cameraBlur", "Camera" ),
				( "render:transformBlur", "Transform" ),
				( "render:deformationBlur", "Deformation" ),
				( "render:shutter", "Shutter" ),
			),
		},

	),

)

GafferUI.PlugValueWidget.registerCreator(
	GafferScene.StandardOptions,
	"options.renderCamera.value",
	lambda plug : GafferUI.PathPlugValueWidget(
		plug,
		path = GafferScene.ScenePath( plug.node()["in"], plug.node().scriptNode().context(), "/" ),
	),
)
