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

import functools

import IECore
import IECoreScene

import Gaffer
import GafferUI
import GafferScene

from GafferUI.PlugValueWidget import sole

##########################################################################
# Metadata
##########################################################################

def __cameraSummary( plug ) :

	info = []
	if plug["renderCamera"]["enabled"].getValue() :
		info.append( plug["renderCamera"]["value"].getValue() )
	if plug["filmFit"]["enabled"].getValue() :
		info.append( "Fit Mode %s" %
			IECoreScene.Camera.FilmFit.values[ plug["filmFit"]["value"].getValue() ].name
		)
	if plug["renderResolution"]["enabled"].getValue() :
		resolution = plug["renderResolution"]["value"].getValue()
		info.append( "%dx%d" % ( resolution[0], resolution[1] ) )
	if plug["pixelAspectRatio"]["enabled"].getValue() :
		pixelAspectRatio = plug["pixelAspectRatio"]["value"].getValue()
		info.append( "Aspect %s" % GafferUI.NumericWidget.valueToString( pixelAspectRatio ) )
	if plug["resolutionMultiplier"]["enabled"].getValue() :
		resolutionMultiplier = plug["resolutionMultiplier"]["value"].getValue()
		info.append( "Mult %s" % GafferUI.NumericWidget.valueToString( resolutionMultiplier ) )
	if plug["renderCropWindow"]["enabled"].getValue() :
		crop = plug["renderCropWindow"]["value"].getValue()
		info.append( "Crop %s,%s-%s,%s" % tuple( GafferUI.NumericWidget.valueToString( x ) for x in ( crop.min().x, crop.min().y, crop.max().x, crop.max().y ) ) )
	if plug["overscan"]["enabled"].getValue() :
		info.append( "Overscan %s" % ( "On" if plug["overscan"]["value"].getValue() else "Off" ) )
	if plug["depthOfField"]["enabled"].getValue() :
		info.append( "DOF " + ( "On" if plug["depthOfField"]["value"].getValue() else "Off" ) )

	return ", ".join( info )

def __renderSetSummary( plug ) :

	info = []
	if plug["includedPurposes"]["enabled"].getValue() :
		purposes = plug["includedPurposes"]["value"].getValue()
		info.append( "Purposes {}".format( " / ".join( [ p.capitalize() for p in purposes ] ) if purposes else "None" ) )
	if plug["inclusions"]["enabled"].getValue() :
		info.append( "Inclusions {}".format( plug["inclusions"]["value"].getValue() ) )
	if plug["exclusions"]["enabled"].getValue() :
		info.append( "Exclusions {}".format( plug["exclusions"]["value"].getValue() ) )
	if plug["additionalLights"]["enabled"].getValue() :
		info.append( "Lights {}".format( plug["additionalLights"]["value"].getValue() ) )

	return ", ".join( info )

def __motionBlurSummary( plug ) :

	info = []
	if plug["transformBlur"]["enabled"].getValue() :
		info.append( "Transform " + ( "On" if plug["transformBlur"]["value"].getValue() else "Off" ) )
	if plug["deformationBlur"]["enabled"].getValue() :
		info.append( "Deformation " + ( "On" if plug["deformationBlur"]["value"].getValue() else "Off" ) )
	if plug["shutter"]["enabled"].getValue() :
		info.append( "Shutter " + str( plug["shutter"]["value"].getValue() ) )

	return ", ".join( info )

def __statisticsSummary( plug ) :

	info = []
	if plug["performanceMonitor"]["enabled"].getValue() :
		info.append( "Performance Monitor " + ( "On" if plug["performanceMonitor"]["value"].getValue() else "Off" ) )

	return ", ".join( info )

## This dictionary is shared with certain nodes that have options- and
# camera-related plugs. We assume that the first metadata element for
# each user-facing plug is the string `"description"`, so take care to
# maintain this when updating these entries or adding new ones.
plugsMetadata = {

	# Section summaries

	"options" : [

		"layout:section:Camera:summary", __cameraSummary,
		"layout:section:Render Set:summary", __renderSetSummary,
		"layout:section:Motion Blur:summary", __motionBlurSummary,
		"layout:section:Statistics:summary", __statisticsSummary,

	],

	# Camera plugs

	"options.renderCamera" : [

		"description",
		"""
		The primary camera to be used for rendering. If this
		is not specified, then a default orthographic camera
		positioned at the origin is used.
		""",

		"layout:section", "Camera",
		"label", "Camera",

	],

	"options.renderCamera.value" : [

		"plugValueWidget:type", "GafferSceneUI.ScenePathPlugValueWidget",
		"path:valid", True,
		"scenePathPlugValueWidget:setNames", IECore.StringVectorData( [ "__cameras" ] ),
		"scenePathPlugValueWidget:setsLabel", "Show only cameras",

	],

	"options.filmFit" : [

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
		"layout:section", "Camera",
		"label", "Film Fit",

	],

	"options.filmFit.value" : [

		"preset:Horizontal", IECoreScene.Camera.FilmFit.Horizontal,
		"preset:Vertical", IECoreScene.Camera.FilmFit.Vertical,
		"preset:Fit", IECoreScene.Camera.FilmFit.Fit,
		"preset:Fill", IECoreScene.Camera.FilmFit.Fill,
		"preset:Distort", IECoreScene.Camera.FilmFit.Distort,

		"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

	],

	"options.renderResolution" : [

		"description",
		"""
		The resolution of the image to be rendered.
		""",

		"layout:section", "Camera",
		"label", "Resolution",

	],

	"options.pixelAspectRatio" : [

		"description",
		"""
		The `width / height` aspect ratio of the individual pixels in
		the rendered image.
		""",

		"layout:section", "Camera",

	],

	"options.resolutionMultiplier" : [

		"description",
		"""
		Multiplies the resolution of the render by this amount.
		""",

		"layout:section", "Camera",

	],

	"options.renderCropWindow" : [

		"description",
		"""
		Limits the render to a region of the image. The rendered image
		will have the same resolution as usual, but areas outside the
		crop will be rendered black. Coordinates range from (0,0) at
		the top-left of the image to (1,1) at the bottom-right. The
		crop window tool in the viewer may be used to set this
		interactively.
		""",

		"layout:section", "Camera",
		"label", "Crop Window",

	],

	"options.overscan" : [

		"description",
		"""
		Whether to enable overscan, which adds extra pixels to the
		sides of the rendered image.

		Overscan can be useful when camera shake or blur will be added
		as a post-process. This plug just enables overscan as a whole –
		use the _Overscan Top_, _Overscan Bottom_, _Overscan Left_ and
		_Overscan Right_ plugs to specify the amount of overscan on
		each side of the image.
		""",

		"layout:section", "Camera",

	],

	"options.overscanTop" : [

		"description",
		"""
		The amount of overscan at the top of the image. Specified as a
		0-1 proportion of the original image height.
		""",

		"layout:section", "Camera",

	],

	"options.overscanBottom" : [

		"description",
		"""
		The amount of overscan at the bottom of the image. Specified as
		a 0-1 proportion of the original image height.
		""",

		"layout:section", "Camera",

	],

	"options.overscanLeft" : [

		"description",
		"""
		The amount of overscan at the left of the image. Specified as a
		0-1 proportion of the original image width.
		""",

		"layout:section", "Camera",

	],

	"options.overscanRight" : [

		"description",
		"""
		The amount of overscan at the right of the image. Specified as
		a 0-1 proportion of the original image width.
		""",

		"layout:section", "Camera",

	],

	"options.depthOfField" : [

		"description",
		"""
		Whether to render with depth of field. To ensure the effect is
		visible, you must also set an f-stop value greater than 0 on
		this camera.
		""",

		"layout:section", "Camera",
	],

	# Purpose

	"options.includedPurposes" : [

		"description",
		"""
		Limits the objects included in the render according to the values of their `usd:purpose`
		attribute. The "Default" purpose includes all objects which have no `usd:purpose` attribute;
		other than for debugging, there is probably no good reason to omit it.

		> Tip : Use the USDAttributes node to assign the `usd:purpose` attribute.
		""",

		"layout:section", "Render Set",

	],

	"options.includedPurposes.value" : [

		"plugValueWidget:type", "GafferSceneUI.StandardOptionsUI._IncludedPurposesPlugValueWidget",

	],

	"options.inclusions" : [

		"description",
		"""
		A set expression that limits the objects included in the render to only those matched
		and their descendants. Objects not matched by the set expression will be pruned from
		the scene.

		> Tip : Cameras are included by default and do not need to be specified here.
		""",

		"layout:section", "Render Set",

	],

	"options.exclusions" : [

		"description",
		"""
		A set expression that excludes the matched objects from the render. Exclusions
		affect both `inclusions` and `additionalLights` and cause the matching objects and
		their descendants to be pruned from the scene.
		""",

		"layout:section", "Render Set",

	],

	"options.additionalLights" : [

		"description",
		"""
		A set expression that specifies additional lights to be included in the render.
		This differs from `inclusions` in that only lights will be matched by this set
		expression.
		""",

		"layout:section", "Render Set",

	],

	# Motion blur plugs

	"options.transformBlur" : [

		"description",
		"""
		Whether or not transform motion is taken into
		account in the renderered image. To specify the
		number of transform segments to use for each
		object in the scene, use a StandardAttributes node
		with appropriate filters.
		""",

		"layout:section", "Motion Blur",
		"label", "Transform",

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

		"layout:section", "Motion Blur",
		"label", "Deformation",

	],

	"options.shutter" : [

		"description",
		"""
		The interval over which the camera shutter is open. Measured
		in frames, and specified relative to the frame being rendered.
		""",

		"layout:section", "Motion Blur",

	],

	"options.sampleMotion" : [

		"description",
		"""
		Whether to actually render motion blur.  Disabling this
		setting while motion blur is set up produces a render where
		there is no blur, but there is accurate motion information.
		Useful for rendering motion vector passes.
		""",

		"layout:section", "Motion Blur",

	],

	# Statistics plugs

	"options.performanceMonitor" : [

		"description",
		"""
		Enables a performance monitor and uses it to output
		statistics about scene generation performance.
		""",

		"layout:section", "Statistics",

	],

}

Gaffer.Metadata.registerNode(

	GafferScene.StandardOptions,

	"description",
	"""
	Specifies the standard options (global settings) for the
	scene. These should be respected by all renderers.
	""",

	plugs = plugsMetadata

)

class _IncludedPurposesPlugValueWidget( GafferUI.PlugValueWidget ) :

	__allPurposes = [ "default", "render", "proxy", "guide" ]

	def __init__( self, plugs, **kw ) :

		self.__menuButton = GafferUI.MenuButton( "", menu = GafferUI.Menu( Gaffer.WeakMethod( self.__menuDefinition ) ) )
		GafferUI.PlugValueWidget.__init__( self, self.__menuButton, plugs, **kw )

		self._addPopupMenu( self.__menuButton )

		self.__currentValue = None

	def _updateFromValues( self, values, exception ) :

		self.__currentValue = sole( values )
		if self.__currentValue :
			self.__menuButton.setText( ", ".join( [ p.capitalize() for p in self.__currentValue ] ) )
		else :
			# A value of `None` means we have multiple different values (from different plugs),
			# and a value of `[]` means the user has disabled all purposes.
			self.__menuButton.setText( "---" if self.__currentValue is None else "None" )
		self.__menuButton.setErrored( exception is not None )

	def _updateFromEditable( self ) :

		self.__menuButton.setEnabled( self._editable() )

	def __menuDefinition( self ) :

		result = IECore.MenuDefinition()

		currentValue = self.__currentValue or []
		for purpose in self.__allPurposes :

			result.append(
				"/{}".format( purpose.capitalize() ),
				{
					"checkBox" : purpose in currentValue,
					"command" : functools.partial( Gaffer.WeakMethod( self.__togglePurpose ), purpose = purpose )
				}
			)


		return result

	def __togglePurpose( self, checked, purpose ) :

		with self.getContext() :
			with Gaffer.UndoScope( next( iter( self.getPlugs() ) ).ancestor( Gaffer.ScriptNode ) ) :
				for plug in self.getPlugs() :
					value = plug.getValue()
					# Conform value so that only valid purposes are present, and they are
					# always presented in the same order.
					value = [
						p for p in self.__allPurposes
						if
						( p != purpose and p in value ) or ( p == purpose and checked )
					]
					plug.setValue( IECore.StringVectorData( value ) )
