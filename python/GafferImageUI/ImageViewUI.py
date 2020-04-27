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
import math
import imath

import IECore

import Gaffer
import GafferUI
import GafferImage
import GafferImageUI

##########################################################################
# Metadata registration.
##########################################################################

Gaffer.Metadata.registerNode(

	GafferImageUI.ImageView,

	"nodeToolbar:bottom:type", "GafferUI.StandardNodeToolbar.bottom",

	"toolbarLayout:customWidget:LeftSpacer:widgetType", "GafferImageUI.ImageViewUI._Spacer",
	"toolbarLayout:customWidget:LeftSpacer:section", "Top",
	"toolbarLayout:customWidget:LeftSpacer:index", 0,

	"toolbarLayout:customWidget:StateWidget:widgetType", "GafferImageUI.ImageViewUI._StateWidget",
	"toolbarLayout:customWidget:StateWidget:section", "Top",
	"toolbarLayout:customWidget:StateWidget:index", -1,

	"toolbarLayout:customWidget:RightSpacer:widgetType", "GafferImageUI.ImageViewUI._Spacer",
	"toolbarLayout:customWidget:RightSpacer:section", "Top",
	"toolbarLayout:customWidget:RightSpacer:index", -2,

	"toolbarLayout:customWidget:BottomRightSpacer:widgetType", "GafferImageUI.ImageViewUI._Spacer",
	"toolbarLayout:customWidget:BottomRightSpacer:section", "Bottom",
	"toolbarLayout:customWidget:BottomRightSpacer:index", 2,

	plugs = {

		"clipping" : [

			"description",
			"""
			Highlights the regions in which the colour values go above 1 or below 0.
			""",

			"plugValueWidget:type", "GafferImageUI.ImageViewUI._TogglePlugValueWidget",
			"togglePlugValueWidget:imagePrefix", "clipping",
			"togglePlugValueWidget:defaultToggleValue", True,
			"toolbarLayout:divider", True,

		],

		"exposure" : [

			"description",
			"""
			Applies an exposure adjustment to the image.
			""",

			"plugValueWidget:type", "GafferImageUI.ImageViewUI._TogglePlugValueWidget",
			"togglePlugValueWidget:imagePrefix", "exposure",
			"togglePlugValueWidget:defaultToggleValue", 1,

		],

		"gamma" : [

			"description",
			"""
			Applies a gamma correction to the image.
			""",

			"plugValueWidget:type", "GafferImageUI.ImageViewUI._TogglePlugValueWidget",
			"togglePlugValueWidget:imagePrefix", "gamma",
			"togglePlugValueWidget:defaultToggleValue", 2,

		],

		"displayTransform" : [

			"description",
			"""
			Applies colour space transformations for viewing the image correctly.
			""",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
			"label", "",
			"toolbarLayout:width", 100,

			"presetNames", lambda plug : IECore.StringVectorData( GafferImageUI.ImageView.registeredDisplayTransforms() ),
			"presetValues", lambda plug : IECore.StringVectorData( GafferImageUI.ImageView.registeredDisplayTransforms() ),

		],

		"colorInspector" : [

			"plugValueWidget:type", "GafferImageUI.ImageViewUI._ColorInspectorPlugValueWidget",
			"label", "",
			"toolbarLayout:section", "Bottom",
			"toolbarLayout:index", 1,

		],

		"channels" : [

			"description",
			"""
			Chooses an RGBA layer or an auxiliary channel to display.
			""",

			"plugValueWidget:type", "GafferImageUI.RGBAChannelsPlugValueWidget",
			"toolbarLayout:index", 1,
			"toolbarLayout:width", 175,
			"label", "",

		],

		"soloChannel" : [

			"description",
			"""
			Chooses a channel to show in isolation.
			""",

			"plugValueWidget:type", "GafferImageUI.ImageViewUI._SoloChannelPlugValueWidget",
			"toolbarLayout:index", 1,
			"toolbarLayout:divider", True,
			"label", "",

		],

	}

)

##########################################################################
# _TogglePlugValueWidget
##########################################################################

# Toggles between default value and the last non-default value
class _TogglePlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 2 )

		GafferUI.PlugValueWidget.__init__( self, row, plug, **kw )

		self.__imagePrefix = Gaffer.Metadata.value( plug, "togglePlugValueWidget:imagePrefix" )
		with row :

			self.__button = GafferUI.Button( "", self.__imagePrefix + "Off.png", hasFrame=False )
			self.__button.clickedSignal().connect( Gaffer.WeakMethod( self.__clicked ), scoped = False )

			if not isinstance( plug, Gaffer.BoolPlug ) :
				plugValueWidget = GafferUI.PlugValueWidget.create( plug, useTypeOnly=True )
				plugValueWidget.numericWidget().setFixedCharacterWidth( 5 )

		self.__toggleValue = Gaffer.Metadata.value( plug, "togglePlugValueWidget:defaultToggleValue" )
		self._updateFromPlug()

	def hasLabel( self ) :

		return True

	def getToolTip( self ) :

		result = GafferUI.PlugValueWidget.getToolTip( self )

		if result :
			result += "\n"
		result += "## Actions\n\n"
		result += "- Click to toggle to/from default value\n"

		return result

	def _updateFromPlug( self ) :

		with self.getContext() :
			value = self.getPlug().getValue()

		if value != self.getPlug().defaultValue() :
			self.__toggleValue = value
			self.__button.setImage( self.__imagePrefix + "On.png" )
		else :
			self.__button.setImage( self.__imagePrefix + "Off.png" )

		self.setEnabled( self.getPlug().settable() )

	def __clicked( self, button ) :

		with self.getContext() :
			value = self.getPlug().getValue()

		if value == self.getPlug().defaultValue() and self.__toggleValue is not None :
			self.getPlug().setValue( self.__toggleValue )
		else :
			self.getPlug().setToDefault()

##########################################################################
# _ColorInspectorPlugValueWidget
##########################################################################

class _ColorInspectorPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		frame = GafferUI.Frame( borderWidth = 4 )

		GafferUI.PlugValueWidget.__init__( self, frame, plug, **kw )

		# Style selector specificity rules seem to preclude us styling this
		# based on gafferClass.
		frame._qtWidget().setObjectName( "gafferColorInspector" )

		with frame :

			with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :

				GafferUI.Spacer( imath.V2i( 10 ), imath.V2i( 10 ) )

				self.__positionLabel = GafferUI.Label()
				self.__positionLabel._qtWidget().setFixedWidth( 90 )

				self.__swatch = GafferUI.ColorSwatch()
				self.__swatch._qtWidget().setFixedWidth( 12 )
				self.__swatch._qtWidget().setFixedHeight( 12 )

				self.__busyWidget = GafferUI.BusyWidget( size = 12 )

				self.__rgbLabel = GafferUI.Label()

				GafferUI.Spacer( imath.V2i( 20, 10 ), imath.V2i( 20, 10 ) )

				self.__hsvLabel = GafferUI.Label()

				GafferUI.Spacer( imath.V2i( 10 ), imath.V2i( 10 ) )

		self.__pixel = imath.V2f( 0 )

		viewportGadget = plug.parent().viewportGadget()
		viewportGadget.mouseMoveSignal().connect( Gaffer.WeakMethod( self.__mouseMove ), scoped = False )

		imageGadget = viewportGadget.getPrimaryChild()
		imageGadget.buttonPressSignal().connect( Gaffer.WeakMethod( self.__buttonPress ), scoped = False )
		imageGadget.dragBeginSignal().connect( Gaffer.WeakMethod( self.__dragBegin ), scoped = False )
		imageGadget.dragEndSignal().connect( Gaffer.WeakMethod( self.__dragEnd ), scoped = False )

		self.__updateLabels( imath.V2i( 0 ), imath.Color4f( 0, 0, 0, 1 ) )

	def _updateFromPlug( self ) :

		self.__updateLazily()

	@GafferUI.LazyMethod()
	def __updateLazily( self ) :

		with self.getContext() :
			self.__updateInBackground( self.__pixel )

	@GafferUI.BackgroundMethod()
	def __updateInBackground( self, pixel ) :

		image = self.getPlug().node().viewportGadget().getPrimaryChild().getImage()

		with Gaffer.Context( Gaffer.Context.current() ) as c :
			c["colorInspector:pixel"] = pixel
			samplerChannels = self.getPlug()["color"].getInput().node()["channels"].getValue()
			channelNames = image["channelNames"].getValue()
			color = self.getPlug()["color"].getValue()

		if samplerChannels[3] not in channelNames :
			color = imath.Color3f( color[0], color[1], color[2] )

		return pixel, color

	@__updateInBackground.preCall
	def __updateInBackgroundPreCall( self ) :

		self.__busyWidget.setBusy( True )

	@__updateInBackground.postCall
	def __updateInBackgroundPostCall( self, backgroundResult ) :

		if isinstance( backgroundResult, IECore.Cancelled ) :
			# Cancellation. This could be due to any of the
			# following :
			#
			# - This widget being hidden.
			# - A graph edit that will affect the image and will have
			#   triggered a call to _updateFromPlug().
			# - A graph edit that won't trigger a call to _updateFromPlug().
			#
			# LazyMethod takes care of all this for us. If we're hidden,
			# it waits till we're visible. If `updateFromPlug()` has already
			# called `__updateLazily()`, our call will just replace the
			# pending call.
			self.__updateLazily()
			return
		elif isinstance( backgroundResult, Exception ) :
			# Computation error. This will be reported elsewhere
			# in the UI.
			self.__updateLabels( self.__pixel, imath.Color4f( 0 ) )
		else :
			# Success. We have valid infomation to display.
			self.__updateLabels( backgroundResult[0], backgroundResult[1] )

		self.__busyWidget.setBusy( False )

	def __updateLabels( self, pixel, color ) :

		self.__positionLabel.setText( "<b>XY : %d %d</b>" % ( pixel.x, pixel.y ) )
		self.__swatch.setColor( color )

		if isinstance( color, imath.Color4f ) :
			self.__rgbLabel.setText( "<b>RGBA : %.3f %.3f %.3f %.3f</b>" % ( color.r, color.g, color.b, color.a ) )
		else :
			self.__rgbLabel.setText( "<b>RGB : %.3f %.3f %.3f</b>" % ( color.r, color.g, color.b ) )

		hsv = color.rgb2hsv()
		self.__hsvLabel.setText( "<b>HSV : %.3f %.3f %.3f</b>" % ( hsv.r, hsv.g, hsv.b ) )

	def __mouseMove( self, viewportGadget, event ) :

		imageGadget = viewportGadget.getPrimaryChild()
		l = viewportGadget.rasterToGadgetSpace( imath.V2f( event.line.p0.x, event.line.p0.y ), imageGadget )

		try :
			pixel = imageGadget.pixelAt( l )
		except :
			# `pixelAt()` can throw if there is an error
			# computing the image being viewed. We leave
			# the error reporting to other UI components.
			return False

		pixel = imath.V2f( math.floor( pixel.x ), math.floor( pixel.y ) ) # Origin
		pixel = pixel + imath.V2f( 0.5 ) # Center

		if pixel == self.__pixel :
			return False

		self.__pixel = pixel

		self.__updateLazily()

		return True

	def __buttonPress( self, imageGadget, event ) :

		if event.buttons != event.Buttons.Left or event.modifiers :
			return False

		return True # accept press so we get dragBegin()

	def __dragBegin( self, imageGadget, event ) :

		if event.buttons != event.Buttons.Left or event.modifiers :
			return False

		with Gaffer.Context( self.getContext() ) as c :
			c["colorInspector:pixel"] = self.__pixel
			try :
				color = self.getPlug()["color"].getValue()
			except :
				# Error will be reported elsewhere in the UI
				return None

		GafferUI.Pointer.setCurrent( "rgba" )
		return color

	def __dragEnd( self, imageGadget, event ) :

		GafferUI.Pointer.setCurrent( "" )
		return True

##########################################################################
# _SoloChannelPlugValueWidget
##########################################################################

class _SoloChannelPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		self.__button = GafferUI.MenuButton(
			image = "soloChannel-1.png",
			hasFrame = False,
			menu = GafferUI.Menu(
				Gaffer.WeakMethod( self.__menuDefinition ),
				title = "Channel",
			)
		)

		GafferUI.PlugValueWidget.__init__( self, self.__button, plug, **kw )

		self._updateFromPlug()

	def _updateFromPlug( self ) :

		with Gaffer.Context() :

			self.__button.setImage( "soloChannel{0}.png".format( self.getPlug().getValue() ) )

	def __menuDefinition( self ) :

		with self.getContext() :
			soloChannel = self.getPlug().getValue()

		m = IECore.MenuDefinition()
		for name, value in [
			( "All", -1 ),
			( "R", 0 ),
			( "G", 1 ),
			( "B", 2 ),
			( "A", 3 ),
		] :
			m.append(
				"/" + name,
				{
					"command" : functools.partial( Gaffer.WeakMethod( self.__setValue ), value ),
					"checkBox" : soloChannel == value
				}
			)

		return m

	def __setValue( self, value, *unused ) :

		self.getPlug().setValue( value )

##########################################################################
# _StateWidget
##########################################################################

class _Spacer( GafferUI.Spacer ) :

	def __init__( self, imageView, **kw ) :

		GafferUI.Spacer.__init__( self, size = imath.V2i( 0, 25 ) )

## \todo This widget is basically the same as the SceneView and UVView ones. Perhaps the
# View base class should provide standard functionality for pausing and state, and we could
# use one standard widget for everything.
class _StateWidget( GafferUI.Widget ) :

	def __init__( self, imageView, **kw ) :

		row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 )
		GafferUI.Widget.__init__( self, row, **kw )

		with row :

			self.__busyWidget = GafferUI.BusyWidget( size = 20 )
			self.__button = GafferUI.Button( hasFrame = False )

		self.__imageGadget = imageView.viewportGadget().getPrimaryChild()

		self.__button.clickedSignal().connect( Gaffer.WeakMethod( self.__buttonClick ), scoped = False )

		self.__imageGadget.stateChangedSignal().connect( Gaffer.WeakMethod( self.__stateChanged ), scoped = False )

		self.__update()

	def __stateChanged( self, imageGadget ) :

		self.__update()

	def __buttonClick( self, button ) :

		self.__imageGadget.setPaused( not self.__imageGadget.getPaused() )
		self.__update()

	def __update( self ) :

		paused = self.__imageGadget.getPaused()
		self.__button.setImage( "viewPause.png" if not paused else "viewPaused.png" )
		self.__busyWidget.setBusy( self.__imageGadget.state() == self.__imageGadget.State.Running )
		self.__button.setToolTip( "Viewer updates suspended, click to resume" if paused else "Click to suspend viewer updates [esc]" )
