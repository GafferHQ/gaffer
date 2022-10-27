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

from Qt import QtGui
from Qt import QtWidgets
from Qt import QtCore

##########################################################################
# Metadata registration.
##########################################################################

Gaffer.Metadata.registerNode(

	GafferImageUI.ImageView,

	"nodeToolbar:bottom:type", "GafferUI.StandardNodeToolbar.bottom",

	"toolbarLayout:customWidget:StateWidget:widgetType", "GafferImageUI.ImageViewUI._StateWidget",
	"toolbarLayout:customWidget:StateWidget:section", "Top",
	"toolbarLayout:customWidget:StateWidget:index", 0,

	"toolbarLayout:customWidget:LeftCenterSpacer:widgetType", "GafferImageUI.ImageViewUI._Spacer",
	"toolbarLayout:customWidget:LeftCenterSpacer:section", "Top",
	"toolbarLayout:customWidget:LeftCenterSpacer:index", 1,

	"toolbarLayout:customWidget:RightCenterSpacer:widgetType", "GafferImageUI.ImageViewUI._Spacer",
	"toolbarLayout:customWidget:RightCenterSpacer:section", "Top",
	"toolbarLayout:customWidget:RightCenterSpacer:index", -2,

	"toolbarLayout:customWidget:StateWidgetBalancingSpacer:widgetType", "GafferImageUI.ImageViewUI._StateWidgetBalancingSpacer",
	"toolbarLayout:customWidget:StateWidgetBalancingSpacer:section", "Top",
	"toolbarLayout:customWidget:StateWidgetBalancingSpacer:index", -1,

	"toolbarLayout:customWidget:BottomRightSpacer:widgetType", "GafferImageUI.ImageViewUI._ExpandingSpacer",
	"toolbarLayout:customWidget:BottomRightSpacer:section", "Bottom",
	"toolbarLayout:customWidget:BottomRightSpacer:index", -1,

	"toolbarLayout:activator:gpuAvailable", lambda node : isinstance( GafferImageUI.ImageView.createDisplayTransform( node["displayTransform"].getValue() ), GafferImage.OpenColorIOTransform ),

	plugs = {

		"view" : [

			"description",
			"""
			Chooses view to display from a multi-view image.  The "default" view is used for normal images
			that don't have specific views.
			""",

			"plugValueWidget:type", "GafferImageUI.ImageViewUI._ImageView_ViewPlugValueWidget",
			"toolbarLayout:width", 125,
			"label", "",
			"toolbarLayout:divider", True,

		],

		"compare" : [
			"plugValueWidget:type", "GafferImageUI.ImageViewUI._CompareParentPlugValueWidget",
			"toolbarLayout:divider", True,
			"label", "",
		],

		"compare.mode" : [

			"description",
			"""
			Enables a comparison mode to view two images at once - they can be composited under or over, or
			subtracted for a difference view.  Or replace mode just shows the front image, which is useful
			in combination with the Wipe tool.
			""",

			"plugValueWidget:type", "GafferImageUI.ImageViewUI._CompareModePlugValueWidget",

		],

		"compare.matchDisplayWindows" : [
			# matchDisplayWindows is also handled by _CompareModePlugValueWidget
			"plugValueWidget:type", "",
		],

		"compare.wipe" : [

			"description",
			"""
			Enables a wipe tool to hide part of the image, for comparing with the background image.
			Hotkey W.
			""",

			"plugValueWidget:type", "GafferImageUI.ImageViewUI._CompareWipePlugValueWidget",

		],

		"compare.image" : [

			"description",
			"""
			The image to compare with.
			""",

			"plugValueWidget:type", "GafferImageUI.ImageViewUI._CompareImageWidget",

		],

		"compare.catalogueOutput" : [
			# catalogueOutput is also handled by _CompareImageWidget
			"plugValueWidget:type", "",
		],


		"channels" : [

			"description",
			"""
			Chooses an RGBA layer or an auxiliary channel to display.
			""",

			"plugValueWidget:type", "GafferImageUI.ImageViewUI._ChannelsPlugValueWidget",
			"toolbarLayout:width", 175,
			"label", "",

		],

		"soloChannel" : [

			"description",
			"""
			Chooses a channel to show in isolation.
			""",

			"plugValueWidget:type", "GafferImageUI.ImageViewUI._SoloChannelPlugValueWidget",
			"toolbarLayout:divider", True,
			"label", "",

		],

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

		"lutGPU" : [
			"description",
			"""
			Controls whether to use the fast GPU path for applying exposure, gamma, and displayTransform.
			""",

			"plugValueWidget:type", "GafferImageUI.ImageViewUI._LutGPUPlugValueWidget",
			"label", "",
			"toolbarLayout:activator", "gpuAvailable",

			# Turning off GPU mode means we can't properly support efficient wipes.  Since we no longer
			# have feature parity, we're deprecating CPU mode, and expecting everyone to use the GPU path.
			# With new OCIO, the GPU path now gives high quality on any even vaguely recent GPU.
			# The only use case I can think of for the CPU path is checking that the GPU path is working correctly.
			# If you need to do that, set this metadata to True, and then create a new Viewer to force a refresh.
			"toolbarLayout:visibilityActivator", False,
		],

		"colorInspector" : [
			"plugValueWidget:type", "GafferUI.LayoutPlugValueWidget",
			"toolbarLayout:section", "Bottom",
		],

		"colorInspector.evaluator" : [
			"plugValueWidget:type", "",
		],

		"colorInspector.inspectors" : [
			"plugValueWidget:type", "GafferImageUI.ImageViewUI._ColorInspectorsPlugValueWidget",
			"label", "",
		],

		"colorInspector.inspectors.*" : [
			"description",
			"""
			Display the value of the pixel under the cursor.  Ctrl-click to add an inspector to a pixel, or
			Ctrl-drag to create an area inspector.  Display shows value of each channel, hue/saturation/value, and Exposure Value which is measured in stops relative to 18% grey.
			""",
			"label", "",
			"plugValueWidget:type", "GafferImageUI.ImageViewUI._ColorInspectorPlugValueWidget",
			"layout:index", lambda plug : 1024-int( "".join( ['0'] + [ i for i in plug.getName() if i.isdigit() ] ) )
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

def _inspectFormat( f ) :
	r = "%.3f" % f
	if '.' in r and len( r ) > 5:
		r = r[ 0 : max( 5, r.find('.') ) ]
	return r.rstrip('.')

def _hsvString( color ) :

	if any( math.isinf( x ) or math.isnan( x ) for x in color ) :
		# The conventional thing to do would be to call `color.rgb2hsv()`
		# and catch the exception that PyImath throws. But PyImath's
		# exception handling involves a signal handler for SIGFPE. And
		# Arnold likes to install its own handler for that, somehow
		# breaking everything so that the entire application terminates.
		return "- - -"
	else :
		hsv = color.rgb2hsv()
		return "%s %s %s" % ( _inspectFormat( hsv.r ), _inspectFormat( hsv.g ), _inspectFormat( hsv.b ) )

class _ColorInspectorsPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		frame = GafferUI.Frame( borderWidth = 4 )
		GafferUI.PlugValueWidget.__init__( self, frame, plug, **kw )

		# Style selector specificity rules seem to preclude us styling this
		# based on gafferClass.
		frame._qtWidget().setObjectName( "gafferColorInspector" )

		with frame :

			GafferUI.LayoutPlugValueWidget( plug )


class _ColorInspectorPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		l = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 )
		GafferUI.PlugValueWidget.__init__( self, l, plug, **kw )

		mode = plug["mode"].getValue()
		with l:
			self.__indexLabel = GafferUI.Label()
			labelFont = QtGui.QFont( self.__indexLabel._qtWidget().font() )
			labelFont.setBold( True )
			labelFont.setPixelSize( 10 )
			labelFontMetrics = QtGui.QFontMetrics( labelFont )
			self.__indexLabel._qtWidget().setMinimumWidth( labelFontMetrics.boundingRect( "99" ).width() )

			self.__modeImage = GafferUI.Image( "sourceCursor.png" )

			self.__positionLabel = GafferUI.Label()
			self.__positionLabel._qtWidget().setMinimumWidth( labelFontMetrics.boundingRect( "9999 9999 -> 9999 9999" ).width() )

			self.__swatch = GafferUI.ColorSwatch()
			self.__swatch._qtWidget().setFixedWidth( 12 )
			self.__swatch._qtWidget().setFixedHeight( 12 )

			self.__busyWidget = GafferUI.BusyWidget( size = 12 )

			self.__rgbLabel = GafferUI.Label()
			self.__rgbLabel._qtWidget().setMinimumWidth( labelFontMetrics.boundingRect( "RGBA : 99999 99999 99999 99999" ).width() )

			self.__hsvLabel = GafferUI.Label()
			self.__hsvLabel._qtWidget().setMinimumWidth( labelFontMetrics.boundingRect( "HSV : 99999 99999 99999" ).width() )

			self.__exposureLabel = GafferUI.Label()
			self.__exposureLabel._qtWidget().setMinimumWidth( labelFontMetrics.boundingRect( "EV : 19.9" ).width() )

			l.addChild( GafferUI.Spacer( size = imath.V2i( 0 ) ) )

			if mode == GafferImageUI.ImageView.ColorInspectorPlug.Mode.Cursor:
				m = IECore.MenuDefinition()
				m.append( "/Pixel Inspector",
					{ "command" : functools.partial( Gaffer.WeakMethod( self.__addClick ), GafferImageUI.ImageView.ColorInspectorPlug.Mode.Pixel ) }
				)
				m.append( "/Area Inspector",
					{ "command" : functools.partial( Gaffer.WeakMethod( self.__addClick ), GafferImageUI.ImageView.ColorInspectorPlug.Mode.Area ) }
				)
				button = GafferUI.MenuButton( "", "plus.png", hasFrame=False, menu = GafferUI.Menu( m, title = "Add Color Inspector" ) )
			else:
				button = GafferUI.Button( "", "delete.png", hasFrame=False )
				button.clickedSignal().connect( Gaffer.WeakMethod( self.__deleteClick ), scoped = False )


		self.__pixel = imath.V2i( 0 )
		self.__createInspectorStartPosition = None

		if plug.getName() == "ColorInspectorPlug":
			viewportGadget = plug.node().viewportGadget()

			imageGadget = viewportGadget.getPrimaryChild()
			imageGadget.mouseMoveSignal().connect( Gaffer.WeakMethod( self.__mouseMove ), scoped = False )
			imageGadget.buttonPressSignal().connect( Gaffer.WeakMethod( self.__buttonPress ), scoped = False )
			imageGadget.buttonReleaseSignal().connect( Gaffer.WeakMethod( self.__buttonRelease ), scoped = False )
			imageGadget.dragBeginSignal().connect( Gaffer.WeakMethod( self.__dragBegin ), scoped = False )
			imageGadget.dragEnterSignal().connect( Gaffer.WeakMethod( self.__dragEnter ), scoped = False )
			imageGadget.dragMoveSignal().connect( Gaffer.WeakMethod( self.__dragMove ), scoped = False )
			imageGadget.dragEndSignal().connect( Gaffer.WeakMethod( self.__dragEnd ), scoped = False )

		self.__swatch.buttonPressSignal().connect( Gaffer.WeakMethod( self.__buttonPress ), scoped = False )
		self.__swatch.dragBeginSignal().connect( Gaffer.WeakMethod( self.__dragBegin ), scoped = False )
		self.__swatch.dragEndSignal().connect( Gaffer.WeakMethod( self.__dragEnd ), scoped = False )

		plug.node()["colorInspector"]["evaluator"]["pixelColor"].getInput().node().plugDirtiedSignal().connect( Gaffer.WeakMethod( self.__updateFromImageNode ), scoped = False )

		plug.node().plugDirtiedSignal().connect( Gaffer.WeakMethod( self._plugDirtied ), scoped = False )
		plug.node()["in"].getInput().node().scriptNode().context().changedSignal().connect( Gaffer.WeakMethod( self.__updateFromContext ), scoped = False )
		Gaffer.Metadata.plugValueChangedSignal( self.getPlug().node() ).connect( Gaffer.WeakMethod( self.__plugMetadataChanged ), scoped = False )

		self.__updateLabels( imath.V2i( 0 ), imath.Color4f( 0, 0, 0, 1 ) )

		# Set initial state of mode icon
		self._plugDirtied( plug["mode"] )

	def __addInspector( self ):
		parent = self.getPlug().parent()
		suffix = 1
		while "c" + str( suffix ) in parent:
			suffix += 1

		parent.addChild( GafferImageUI.ImageView.ColorInspectorPlug( "c" + str( suffix ) ) )

	def __addClick( self, mode ):
		self.__addInspector()
		ci = self.getPlug().parent().children()[-1]
		ci["mode"].setValue( mode )
		if mode == GafferImageUI.ImageView.ColorInspectorPlug.Mode.Area:
			ci["area"].setValue(
				self.getPlug().node()["colorInspector"]["evaluator"]["areaColor"].getInput().node()["in"].format().getDisplayWindow()
			)

	def __deleteClick( self, button ):
		self.getPlug().parent().removeChild( self.getPlug() )

	def __updateFromImageNode( self, unused ):

		self.__updateLazily()

	def _plugDirtied( self, childPlug ):
		if childPlug == self.getPlug()["mode"]:
			mode = self.getPlug()["mode"].getValue()

			# TODO - should GafferUI.Image have a setImage?
			self.__modeImage._qtWidget().setPixmap( GafferUI.Image._qtPixmapFromFile( [ "sourceCursor.png", "sourcePixel.png", "sourceArea.png" ][ mode ]  ) )
			self.__updateLazily()

	def __plugMetadataChanged( self, plug, key, reason ):
		if key == "__hovered" and ( plug == self.getPlug()["area"] or plug == self.getPlug()["pixel"] ):
			# We could avoid the extra compute of the color at the cost of a little extra complexity if
			# we stored the last evaluated color so we could directly call _updateLabels
			self.__updateLazily()

	def _updateFromPlug( self ) :

		self.__updateLazily()

	def __updateFromContext( self, context, name ) :

		self.__updateLazily()

	@GafferUI.LazyMethod()
	def __updateLazily( self ) :
		mode = self.getPlug()["mode"].getValue()
		inputImagePlug = self.getPlug().node()["in"].getInput()
		if not inputImagePlug:
			# This can happen when the source is deleted - can't get pixel values if there's no input image
			self.__updateLabels( self.__pixel, imath.Color4f( 0 ) )
			return

		with inputImagePlug.node().scriptNode().context() :
			if mode == GafferImageUI.ImageView.ColorInspectorPlug.Mode.Cursor:
				self.__updateInBackground( self.__pixel )
			elif mode == GafferImageUI.ImageView.ColorInspectorPlug.Mode.Area:
				self.__updateInBackground( self.getPlug()["area"].getValue() )
			elif mode == GafferImageUI.ImageView.ColorInspectorPlug.Mode.Pixel:
				self.__updateInBackground( self.getPlug()["pixel"].getValue() )

	@GafferUI.BackgroundMethod()
	def __updateInBackground( self, source ) :

		with Gaffer.Context( Gaffer.Context.current() ) as c :
			if type( source ) == imath.V2i:
				c["colorInspector:source"] = imath.V2f( source ) + imath.V2f( 0.5 ) # Center of pixel
				color = self.getPlug().node()["colorInspector"]["evaluator"]["pixelColor"].getValue()
			elif type( source ) == imath.Box2i:
				areaEval = self.getPlug().node()["colorInspector"]["evaluator"]["areaColor"]
				c["colorInspector:source"] = GafferImage.BufferAlgo.intersection( source, areaEval.getInput().node()["in"].format().getDisplayWindow() )
				color = areaEval.getValue()
			else:
				raise Exception( "ColorInspector source must be V2i or Box2i, not " + str( type( source ) ) )

		# TODO : This is a pretty ugly way to find the input node connected to the colorInspector?
		samplerChannels = self.getPlug().node()["colorInspector"]["evaluator"]["pixelColor"].getInput().node()["channels"].getValue()
		image = self.getPlug().node().viewportGadget().getPrimaryChild().getImage()
		channelNames = image["channelNames"].getValue()

		if samplerChannels[3] not in channelNames :
			color = imath.Color3f( color[0], color[1], color[2] )

		return source, color

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
		mode = self.getPlug()["mode"].getValue()

		hovered = False
		if mode == GafferImageUI.ImageView.ColorInspectorPlug.Mode.Area:
			hovered = Gaffer.Metadata.value( self.getPlug()["area"], "__hovered" )
		if mode == GafferImageUI.ImageView.ColorInspectorPlug.Mode.Pixel:
			hovered = Gaffer.Metadata.value( self.getPlug()["pixel"], "__hovered" )
		prefix = ""
		postfix = ""
		if hovered:
			# Chosen to match brightColor in python/GafferUI/_Stylesheet.py
			prefix = '<font color="#779cbd">'
			postfix = '</font>'
		self.__indexLabel.setText( prefix + ( "" if mode == GafferImageUI.ImageView.ColorInspectorPlug.Mode.Cursor else "<b>" + self.getPlug().getName()[1:] + "</b>" ) + postfix )
		if mode == GafferImageUI.ImageView.ColorInspectorPlug.Mode.Area:
			r = self.getPlug()["area"].getValue()
			self.__positionLabel.setText( prefix + "<b>%i %i -> %i %i</b>" % ( r.min().x, r.min().y, r.max().x, r.max().y ) + postfix )
		elif mode == GafferImageUI.ImageView.ColorInspectorPlug.Mode.Cursor:
			self.__positionLabel.setText( prefix + "<b>XY : %i %i</b>" % ( pixel.x, pixel.y ) + postfix )
		else:
			p = self.getPlug()["pixel"].getValue()
			self.__positionLabel.setText( prefix + "<b>XY : %i %i</b>" % ( p.x, p.y ) + postfix )

		self.__swatch.setColor( color )

		if isinstance( color, imath.Color4f ) :
			self.__rgbLabel.setText( "<b>RGBA : %s %s %s %s</b>" % ( _inspectFormat(color.r), _inspectFormat(color.g), _inspectFormat(color.b), _inspectFormat(color.a) ) )
		else :
			self.__rgbLabel.setText( "<b>RGB : %s %s %s</b>" % ( _inspectFormat(color.r), _inspectFormat(color.g), _inspectFormat(color.b) ) )

		self.__hsvLabel.setText( "<b>HSV : %s</b>" % _hsvString( color ) )

		luminance = color.r * 0.2126 + color.g * 0.7152 + color.b * 0.0722
		if luminance == 0:
			exposure = "-inf"
		elif luminance < 0:
			exposure = "NaN"
		else:
			exposure = "%.1f" % ( math.log( luminance / 0.18 ) / math.log( 2 ) )
			if exposure == "-0.0":
				exposure = "0.0"
		self.__exposureLabel.setText( "<b>EV : %s</b>" % exposure )

	def __eventPosition( self, imageGadget, event ):
		try :
			pixel = imageGadget.pixelAt( event.line )
		except :
			# `pixelAt()` can throw if there is an error
			# computing the image being viewed. We leave
			# the error reporting to other UI components.
			return imath.V2i( 0 )
		return imath.V2i( math.floor( pixel.x ), math.floor( pixel.y ) )

	def __mouseMove( self, imageGadget, event ) :

		pixel = self.__eventPosition( imageGadget, event )

		if pixel == self.__pixel :
			return False

		self.__pixel = pixel

		self.__updateLazily()

		return True

	def __buttonPress( self, imageGadget, event ) :

		if event.buttons == event.Buttons.Left and not event.modifiers :
			self.__createInspectorStartPosition = None
			return True # accept press so we get dragBegin() for dragging color
		elif event.buttons == event.Buttons.Left and event.modifiers == GafferUI.ModifiableEvent.Modifiers.Control :
			self.__createInspectorStartPosition = self.__eventPosition( imageGadget, event )
			self.__addInspector()
			ci = self.getPlug().parent().children()[-1]
			Gaffer.Metadata.registerValue( ci["pixel"], "__hovered", True, persistent = False )
			ci["pixel"].setValue( self.__createInspectorStartPosition )

			return True # creating inspector
		else:
			return False

	def __buttonRelease( self, imageGadget, event ) :
		if self.__createInspectorStartPosition:
			ci = self.getPlug().parent().children()[-1]
			Gaffer.Metadata.registerValue( ci["pixel"], "__hovered", False, persistent = False )
			Gaffer.Metadata.registerValue( ci["area"], "__hovered", False, persistent = False )

	def __dragBegin( self, imageGadget, event ) :

		if self.__createInspectorStartPosition:
			return IECore.NullObject.defaultNullObject()

		with Gaffer.Context( self.getPlug().node()["in"].getInput().node().scriptNode().context() ) as c :

			try :
				source = self.__pixel
				if self.getPlug()["mode"].getValue() == GafferImageUI.ImageView.ColorInspectorPlug.Mode.Pixel:
					source = self.getPlug()["pixel"].getValue()
				elif self.getPlug()["mode"].getValue() == GafferImageUI.ImageView.ColorInspectorPlug.Mode.Area:
					source = self.getPlug()["area"].getValue()

				if type( source ) == imath.V2i:
					c["colorInspector:source"] = imath.V2f( source ) + imath.V2f( 0.5 ) # Center of pixel
					color = self.getPlug().node()["colorInspector"]["evaluator"]["pixelColor"].getValue()
				else:
					c["colorInspector:source"] = source
					color = self.getPlug().node()["colorInspector"]["evaluator"]["areaColor"].getValue()

			except :
				# Error will be reported elsewhere in the UI
				return None

		GafferUI.Pointer.setCurrent( "rgba" )
		return color

	def __dragEnter( self, imageGadget, event ) :
		viewportGadget = self.getPlug().node().viewportGadget()
		imageGadget = viewportGadget.getPrimaryChild()
		if event.sourceGadget != imageGadget:
			return False

		return True

	def __dragMove( self, imageGadget, event ) :
		if self.__createInspectorStartPosition:
			ci = self.getPlug().parent().children()[-1]
			c = imath.Box2i()
			c.extendBy( self.__createInspectorStartPosition )
			c.extendBy( self.__eventPosition( imageGadget, event ) )

			# __eventPosition is rounded down, the rectangle should also include the upper end of the
			# pixel containing the cursor
			c.setMax( c.max() + imath.V2i( 1 ) )

			ci["mode"].setValue( GafferImageUI.ImageView.ColorInspectorPlug.Mode.Area )
			Gaffer.Metadata.registerValue( ci["pixel"], "__hovered", False, persistent = False )
			Gaffer.Metadata.registerValue( ci["area"], "__hovered", True, persistent = False )
			ci["area"].setValue( c )

		return True

	def __dragEnd( self, imageGadget, event ) :
		if self.__createInspectorStartPosition:
			ci = self.getPlug().parent().children()[-1]
			Gaffer.Metadata.registerValue( ci["pixel"], "__hovered", False, persistent = False )
			Gaffer.Metadata.registerValue( ci["area"], "__hovered", False, persistent = False )

		GafferUI.Pointer.setCurrent( "" )
		return True

##########################################################################
# _ViewPlugValueWidget
##########################################################################

# Note the weird prefix - a natural name for this would be _ViewPlugValueWidget, but Python appears
# to have an undocumented feature where because GafferImageUI.ViewPlugValueWidget and
# GafferImageUI.ImageViewUI._ViewPlugValueWidget vary only in the namespace and the leading underscore,
# this is similar enough that Python suddenly starts allowing subclasses to override private superclass
# functions.
class _ImageView_ViewPlugValueWidget( GafferImageUI.ViewPlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		GafferImageUI.ViewPlugValueWidget.__init__( self, plug, **kw )

		plug.node().viewportGadget().keyPressSignal().connect(
			Gaffer.WeakMethod( self.__keyPress ),
			scoped = False
		)

		self.__ctrlModifier = Gaffer.Metadata.value( plug, "imageViewViewPlugWidget:ctrlModifier" ) or False

	def _menuDefinition( self ) :

		result = GafferImageUI.ViewPlugValueWidget._menuDefinition( self )

		result.append( "/__PreviousNextDivider__", { "divider" : True } )

		try :
			currentValue = self.getPlug().getValue()
		except Gaffer.ProcessException :
			currentValue = None

		previousValue = self.__incrementedValue( -1 )
		result.append(
			"/Previous",
			{
				"command" : functools.partial( Gaffer.WeakMethod( self.__setValue ), value = previousValue ),
				"shortCut" : "Ctrl+[" if self.__ctrlModifier else "[",
				"active" : previousValue is not None and previousValue != currentValue,
			}
		)

		nextValue = self.__incrementedValue( 1 )
		result.append(
			"/Next",
			{
				"command" : functools.partial( Gaffer.WeakMethod( self.__setValue ), value = nextValue ),
				"shortCut" : "Ctrl+]" if self.__ctrlModifier else "]",
				"active" : nextValue is not None and nextValue != currentValue,
			}
		)

		return result

	def __keyPress( self, gadget, event ) :

		if event.key in ( "BracketLeft", "BracketRight" ) and (
			bool( event.modifiers & event.modifiers.Control ) == self.__ctrlModifier
		):
			value = self.__incrementedValue( -1 if event.key == "BracketLeft" else 1 )
			if value is not None :
				self.__setValue( value )
			return True

		return False

	def __setValue( self, value ) :

		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			self.getPlug().setValue( value )

	def __incrementedValue( self, increment ) :

		try :
			currentValue = self.getPlug().getValue()
		except Gaffer.ProcessException :
			return None

		values = self._views()
		if not values :
			return currentValue

		try :
			index = values.index( currentValue ) + increment
		except ValueError :
			return values[0]

		index = max( 0, min( index, len( values ) - 1 ) )
		return values[index]

##########################################################################
# _ChannelsPlugValueWidget
##########################################################################

class _ChannelsPlugValueWidget( GafferImageUI.RGBAChannelsPlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		GafferImageUI.RGBAChannelsPlugValueWidget.__init__( self, plug, **kw )

		plug.node().viewportGadget().keyPressSignal().connect(
			Gaffer.WeakMethod( self.__keyPress ),
			scoped = False
		)

	def _image( self ):
		# \todo Assuming that we can find an image plug in this specific location
		# may need updating when we add wipes
		return self.getPlug().node()._getPreprocessor()["_selectView"]["out"]

	def _menuDefinition( self ) :

		result = GafferImageUI.RGBAChannelsPlugValueWidget._menuDefinition( self )

		result.append( "/__PreviousNextDivider__", { "divider" : True } )

		try :
			currentValue = self.getPlug().getValue()
		except Gaffer.ProcessException :
			currentValue = None

		previousValue = self.__incrementedValue( -1 )
		result.append(
			"/Previous",
			{
				"command" : functools.partial( Gaffer.WeakMethod( self.__setValue ), value = previousValue ),
				"shortCut" : "PgUp",
				"active" : previousValue is not None and previousValue != currentValue,
			}
		)

		nextValue = self.__incrementedValue( 1 )
		result.append(
			"/Next",
			{
				"command" : functools.partial( Gaffer.WeakMethod( self.__setValue ), value = nextValue ),
				"shortCut" : "PgDown",
				"active" : nextValue is not None and nextValue != currentValue,
			}
		)

		return result

	def __keyPress( self, gadget, event ) :

		if event.key in ( "PageUp", "PageDown" ) :
			value = self.__incrementedValue( -1 if event.key == "PageUp" else 1 )
			if value is not None :
				self.__setValue( value )
			return True

		return False

	def __setValue( self, value ) :

		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			self.getPlug().setValue( value )

	def __incrementedValue( self, increment ) :

		try :
			currentValue = self.getPlug().getValue()
		except Gaffer.ProcessException :
			return None

		values = list( self._rgbaChannels().values() )
		if not values :
			return currentValue

		try :
			index = values.index( currentValue ) + increment
		except ValueError :
			return values[0]

		index = max( 0, min( index, len( values ) - 1 ) )
		return values[index]


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
		m.append(
			"/All",
			{
				"command" : functools.partial( Gaffer.WeakMethod( self.__setValue ), -1 ),
				"checkBox" : soloChannel == -1
			}
		)
		for name, value in [
			( "R", 0 ),
			( "G", 1 ),
			( "B", 2 ),
			( "A", 3 ),
		] :
			m.append(
				"/" + name,
				{
					"command" : functools.partial( Gaffer.WeakMethod( self.__setValue ), value ),
					"checkBox" : soloChannel == value,
					"shortCut" : name
				}
			)

		m.append( "/LuminanceDivider", { "divider" : True, })

		m.append(
				"/Luminance",
				{
					"command" : functools.partial( Gaffer.WeakMethod( self.__setValue ), -2 ),
					"checkBox" : soloChannel == -2,
					"shortCut" : "L"
				}
			)

		return m

	def __setValue( self, value, *unused ) :

		self.getPlug().setValue( value )

##########################################################################
# _LutGPUPlugValueWidget
##########################################################################

class _LutGPUPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		self.__button = GafferUI.MenuButton(
			image = "lutGPU.png",
			hasFrame = False,
			menu = GafferUI.Menu(
				Gaffer.WeakMethod( self.__menuDefinition ),
				title = "LUT Mode",
			)
		)

		GafferUI.PlugValueWidget.__init__( self, self.__button, plug, **kw )

		plug.node().plugSetSignal().connect( Gaffer.WeakMethod( self.__plugSet ), scoped = False )

		self._updateFromPlug()

	def getToolTip( self ) :
		text = "# LUT Mode\n\n"
		if self.__button.getEnabled():
			if self.getPlug().getValue():
				text += "Running LUT on GPU."
			else:
				text += "Running LUT on CPU."
			text += "\n\nAlt+G to toggle"
		else:
			text += "GPU not supported by current DisplayTransform"
		return text

	def __plugSet( self, plug ) :
		n = plug.node()
		if plug == n["displayTransform"] :
			self._updateFromPlug()

	def _updateFromPlug( self ) :

		with self.getContext() :
			gpuSupported = isinstance(
				GafferImageUI.ImageView.createDisplayTransform( self.getPlug().node()["displayTransform"].getValue() ),
				GafferImage.OpenColorIOTransform
			)

			gpuOn = gpuSupported and self.getPlug().getValue()
			self.__button.setImage( "lutGPU.png" if gpuOn else "lutCPU.png" )
			self.__button.setEnabled( gpuSupported )

	def __menuDefinition( self ) :

		with self.getContext() :
			lutGPU = self.getPlug().getValue()

		n = self.getPlug().node()["displayTransform"].getValue()
		gpuSupported = isinstance( GafferImageUI.ImageView.createDisplayTransform( n ), GafferImage.OpenColorIOTransform )
		m = IECore.MenuDefinition()
		for name, value in [
			( "GPU", True ),
			( "CPU", False )
		] :
			m.append(
				"/" + name,
				{
					"command" : functools.partial( Gaffer.WeakMethod( self.__setValue ), value ),
					"checkBox" : lutGPU == value,
					"active" : gpuSupported
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

class _ExpandingSpacer( GafferUI.Spacer ):
	def __init__( self, imageView, **kw ) :

		GafferUI.Widget.__init__( self, QtWidgets.QWidget(), **kw )

		layout = QtWidgets.QHBoxLayout()
		layout.setContentsMargins( 0, 0, 0, 0 )
		self._qtWidget().setLayout( layout )
		layout.addStretch( 1 )

class _StateWidgetBalancingSpacer( GafferUI.Spacer ) :

	def __init__( self, imageView, **kw ) :

		width = 25 + 4 + 20
		GafferUI.Spacer.__init__(
			self,
			imath.V2i( 0 ), # Minimum
			preferredSize = imath.V2i( width, 1 ),
			maximumSize = imath.V2i( width, 1 )
		)


## \todo This widget is basically the same as the SceneView and UVView ones. Perhaps the
# View base class should provide standard functionality for pausing and state, and we could
# use one standard widget for everything.
class _StateWidget( GafferUI.Widget ) :

	def __init__( self, imageView, **kw ) :

		row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 )
		GafferUI.Widget.__init__( self, row, **kw )

		with row :

			self.__button = GafferUI.Button( hasFrame = False )
			self.__busyWidget = GafferUI.BusyWidget( size = 20 )

		# Find all ImageGadgets
		self.__imageGadgets = [ i for i in imageView.viewportGadget().children() if isinstance( i, GafferImageUI.ImageGadget ) ]
		# Put the primary ImageGadget first in the list
		self.__imageGadgets.sort( key = lambda i :  i != imageView.viewportGadget().getPrimaryChild() )

		self.__button.clickedSignal().connect( Gaffer.WeakMethod( self.__buttonClick ), scoped = False )

		# We use the paused state of the primary ImageGadget to drive our UI
		self.__imageGadgets[0].stateChangedSignal().connect( Gaffer.WeakMethod( self.__stateChanged ), scoped = False )

		self.__update()

	def __stateChanged( self, imageGadget ) :

		self.__update()

	def __buttonClick( self, button ) :

		newPaused = not self.__imageGadgets[0].getPaused()
		for i in self.__imageGadgets:
			i.setPaused( newPaused )

	def __update( self ) :

		paused = self.__imageGadgets[0].getPaused()
		self.__button.setImage( "viewPause.png" if not paused else "viewPaused.png" )
		self.__busyWidget.setBusy( self.__imageGadgets[0].state() == GafferImageUI.ImageGadget.State.Running )
		self.__button.setToolTip( "Viewer updates suspended, click to resume" if paused else "Click to suspend viewer updates [esc]" )



##########################################################################
# Compare Widgets
##########################################################################

def _firstValidImagePlug( node ):
	for plug in GafferImage.ImagePlug.RecursiveOutputRange( node ) :
		if not plug.getName().startswith( "__" ):
			return plug
	return None

class _CompareParentPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :
		self.__row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 0 )

		GafferUI.PlugValueWidget.__init__( self, self.__row, plug, **kw )

		widgets = [ GafferUI.PlugValueWidget.create( p ) for p in plug.children( Gaffer.Plug ) ]

		# Omit null widgets ( ie. for catalogueOutput which is handled by _CompareImageWidget )
		widgets = [ w for w in widgets if w ]

		widgets[0]._qtWidget().setFixedWidth( 25 ) # Mode selector is just an icon
		widgets[0]._qtWidget().layout().setSizeConstraint( QtWidgets.QLayout.SetDefaultConstraint )

		self.__row[:] = widgets

		GafferUI.WidgetAlgo.joinEdges( self.__row[:], GafferUI.ListContainer.Orientation.Horizontal )

		self._updateFromPlug()

		# We connect to the front, and unconditionally return True from all these methods, to
		# ensure that we never run any of the default signal handlers from PlugValueWidget
		self.dragEnterSignal().connectFront( Gaffer.WeakMethod( self.__dragEnter ), scoped = False )
		self.dragLeaveSignal().connectFront( Gaffer.WeakMethod( self.__dragLeave ), scoped = False )
		self.dropSignal().connectFront( Gaffer.WeakMethod( self.__drop ), scoped = False )

	def _updateFromPlug( self ) :

		with Gaffer.Context() :
			m = self.getPlug()["mode"].getValue()

		# Disable all but mode plug if mode is "" ( comparison disabled )
		for i in self.__row[1:]:
			i.setEnabled( m != "" )

	def __dropNode( self,  event ) :
		if isinstance( event.data, Gaffer.Node ) :
			return event.data
		elif isinstance( event.data, Gaffer.Set ) :
			for node in reversed( event.data ):
				if isinstance( node, Gaffer.Node ) and _firstValidImagePlug( node ):
					return node
		else:
			return None

	def __dragEnter( self, tabbedContainer, event ) :

		if self.__dropNode( event ) :
			self.__row[-1].setHighlighted( True )

		return True

	def __dragLeave( self, tabbedContainer, event ) :

		self.__row[-1].setHighlighted( False )

		return True

	def __drop( self, widget, event ) :

		node = self.__dropNode( event )

		if node:
			self.__row[-1]._setState( Gaffer.StandardSet( [ node ] ), 0 )

			if not self.getPlug()["mode"].getValue():
				self.getPlug()["mode"].setValue( self.__row[0]._CompareModePlugValueWidget__hotkeyTarget() )

		self.__row[-1].setHighlighted( False )

		return True

class _CompareModePlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		self.__button = GafferUI.MenuButton(
			image = "compareModeNone.png",
			menu = GafferUI.Menu(
				Gaffer.WeakMethod( self.__menuDefinition ),
				title = "Compare Mode",
			)
		)
		self.__button._qtWidget().setMaximumWidth( 25 )

		GafferUI.PlugValueWidget.__init__( self, self.__button, plug, **kw )

		self.__iconDict = {
			"" : "compareModeNone.png",
			"over" : "compareModeOver.png",
			"under" : "compareModeUnder.png",
			"difference" : "compareModeDifference.png",
			"sideBySide" : "compareModeSideBySide.png",
			"replace" : "compareModeReplace.png",
		}

		plug.node().viewportGadget().keyPressSignal().connect(
			Gaffer.WeakMethod( self.__keyPress ),
			scoped = False
		)

		self._updateFromPlug()

	def _updateFromPlug( self ) :

		with Gaffer.Context() :
			v = self.getPlug().getValue()

		if v != "":
			Gaffer.Metadata.registerValue( self.getPlug(), "imageViewer:lastCompareMode", v )

		icon = self.__iconDict[v] if v in self.__iconDict else "compareModeNone.png"
		self.__button.setImage( icon )

	def __hotkeyTarget( self ):
		with Gaffer.Context() :
			v = self.getPlug().getValue()

		if v == "":
			return Gaffer.Metadata.value( self.getPlug(), "imageViewer:lastCompareMode" ) or "over"
		else:
			return ""

	def __keyPress( self, gadget, event ) :

		if event.key == "Q" and not event.modifiers :
			self.__setValue( self.__hotkeyTarget() )
			return True

		return False

	def __menuDefinition( self ) :

		with self.getContext() :
			compareMode = self.getPlug().getValue()

		hotkeyTarget = self.__hotkeyTarget()

		m = IECore.MenuDefinition()
		for name, value in [
			( "None", "" ),
			( "Over", "over" ),
			( "Under", "under" ),
			( "Difference", "difference" ),
			( "Replace", "replace" ),
		] :
			m.append(
				"/" + name,
				{
					"command" : functools.partial( Gaffer.WeakMethod( self.__setValue ), value ),
					"icon" : self.__iconDict[value] if value != compareMode else None,
					"checkBox" : value == compareMode,
					"shortCut" : "Q" if value == hotkeyTarget else None,
				}
			)

		m.append( "/MatchDisplayWindowsDivider", { "divider" : True } )
		m.append(
			"/Match Display Windows",
			{
				"command" : functools.partial( Gaffer.WeakMethod( self.__toggleMatchDisplayWindows ), value ),
				"checkBox" : self.getPlug().parent()["matchDisplayWindows"].getValue()
			}
		)

		return m

	def __setValue( self, value, *unused ) :

		self.getPlug().setValue( value )

	def __toggleMatchDisplayWindows( self, *unused ) :

		matchPlug = self.getPlug().parent()["matchDisplayWindows"]
		matchPlug.setValue( not matchPlug.getValue() )

class _CompareWipePlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		self.__button = GafferUI.Button(
			image = "wipeEnabled.png"
		)
		self.__button._qtWidget().setMaximumWidth( 25 )
		self.__button._qtWidget().setProperty( "gafferThinButton", True )

		GafferUI.PlugValueWidget.__init__( self, self.__button, plug, **kw )

		self.__button.clickedSignal().connect( Gaffer.WeakMethod( self.__toggle  ), scoped = False)
		plug.node().viewportGadget().keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPress ), scoped = False )

		self._updateFromPlug()

	def _updateFromPlug( self ) :

		with Gaffer.Context() :
			v = self.getPlug().getValue()

		icon = "wipeEnabled.png" if v else "wipeDisabled.png"
		self.__button.setImage( icon )

	def __keyPress( self, gadget, event ) :

		if event.key == "W" and not event.modifiers :
			self.__toggle()
			return True

		return False

	def __toggle( self, *args ):
		with Gaffer.Context() :
			mode = self.getPlug().parent()["mode"].getValue()
			if mode == "":
				# Can't toggle wipe when comparison is disabled
				return
			v = self.getPlug().getValue()

		self.getPlug().setValue( not v )

class _CompareImageWidget( GafferUI.Frame ) :

	def __init__( self, plug ) :

		GafferUI.Frame.__init__( self, borderWidth = 0, borderStyle = GafferUI.Frame.BorderStyle.None_ )

		self._qtWidget().setFixedHeight( 15 )
		self.__node = plug.node()
		self.__scriptNode = plug.node()["in"].getInput().node().scriptNode()
		self.__defaultNodeSet = Gaffer.StandardSet( [] )
		self.__nodeSet = self.__defaultNodeSet
		self.__catalogueOutput = 0

		row = GafferUI.ListContainer( orientation = GafferUI.ListContainer.Orientation.Horizontal )
		with row :

			self.__bookmarkNumber = GafferUI.Label( horizontalAlignment=GafferUI.Label.HorizontalAlignment.Right )
			self.__bookmarkNumber.buttonPressSignal().connect( Gaffer.WeakMethod( self.__showEditorFocusMenu ), scoped=False )

			self.__icon = GafferUI.Button( hasFrame=False, highlightOnOver=False )
			self.__icon._qtWidget().setFixedHeight( 13 )
			self.__icon._qtWidget().setFixedWidth( 13 )
			self.__icon.buttonPressSignal().connect( Gaffer.WeakMethod( self.__showEditorFocusMenu ), scoped=False )

			self.__menuButton = GafferUI.Button( image="menuIndicator.png", hasFrame=False, highlightOnOver=False )
			self.__menuButton._qtWidget().setObjectName( "menuDownArrow" )
			self.__menuButton.buttonPressSignal().connect( Gaffer.WeakMethod( self.__showEditorFocusMenu ), scoped=False )

		self.addChild( row )

		self.buttonPressSignal().connect( Gaffer.WeakMethod( self.__showEditorFocusMenu ), scoped=False )

		self._setState( self.__defaultNodeSet, 1 )

	def _setState( self, nodeSet, outputIndex ):
		self.__nodeSet = nodeSet
		self.__catalogueOutput = outputIndex
		self.__memberAddedConnection = self.__nodeSet.memberAddedSignal().connect(
			Gaffer.WeakMethod( self._update ), scoped = True
		)
		self.__memberRemovedConnection = self.__nodeSet.memberRemovedSignal().connect(
			Gaffer.WeakMethod( self._update ), scoped = True
		)
		self._update()

	def _update( self, *unused ) :
		compareImage = None

		if self.__nodeSet is self.__defaultNodeSet:
			compareImage = self.__node["__preprocessor"]["_comparisonSwitch"]["in"][0]["value"]
		elif len( self.__nodeSet ):
			compareImage = _firstValidImagePlug( self.__nodeSet[-1] )

		self.__node["compare"]["image"].setInput( compareImage )
		self.__node["compare"]["catalogueOutput"].setValue( "output:%i" % self.__catalogueOutput if self.__catalogueOutput > 0 else "" )

		# Icon

		if self.__catalogueOutput > 0:
			icon = "catalogueOutput%i.png" % self.__catalogueOutput
		elif self.__nodeSet.isSame( self.__scriptNode.selection() ) :
			icon = "nodeSetNodeSelection.png"
		elif self.__nodeSet.isSame( self.__scriptNode.focusSet() ) :
			icon = "nodeSetFocusNode.png"
		else :
			icon = "nodeSet%s.png"  % self.__nodeSet.__class__.__name__

		self.__icon.setImage( icon )

		# Bookmark set numeric indicator

		if isinstance( self.__nodeSet, Gaffer.NumericBookmarkSet ) :
			self.__bookmarkNumber.setText( "%d" % self.__nodeSet.getBookmark() )
			self.__bookmarkNumber.setVisible( True )
		else :
			self.__bookmarkNumber.setVisible( False )
			self.__bookmarkNumber.setText( "" )

		self._repolish()

	def getToolTip( self ) :

		toolTipElements = []
		if self.__catalogueOutput > 0:
			toolTipElements.append( "" )
			toolTipElements.append( "Comparing to Catalogue output %i." % self.__catalogueOutput )
		elif self.__nodeSet == self.__scriptNode.selection() :
			toolTipElements.append( "" )
			toolTipElements.append( "Comparing to the node selection." )
		elif self.__nodeSet == self.__scriptNode.focusSet() :
			toolTipElements.append( "" )
			toolTipElements.append( "Comparing to the Focus Node." )
		elif isinstance( self.__nodeSet, Gaffer.NumericBookmarkSet ) :
			toolTipElements.append( "" )
			toolTipElements.append( "Comparing to Numeric Bookmark %d." % self.__nodeSet.getBookmark() )
		elif isinstance( self.__nodeSet, Gaffer.StandardSet ) :
			toolTipElements.append( "" )
			n = len(self.__nodeSet)
			if n == 0 :
				s = "Comparing to nothing."
			else :
				s = "Comparing to pinned node: " + self.__nodeSet[-1].relativeName( self.__nodeSet[-1].scriptNode() )
			toolTipElements.append( s )

		toolTipElements.append( "Drag an image node here to pin a comparison node." )

		return "\n".join( toolTipElements )

	def __pinToNodeSelection( self, *unused ) :
		self._setState( Gaffer.StandardSet( list( self.__scriptNode.selection() ) ), 0 )

	def __followNodeSelection( self, *unused ) :
		self._setState( self.__scriptNode.selection(), 0 )

	def __followFocusNode( self, *unused ) :
		self._setState( self.__scriptNode.focusSet(), 0 )

	def __followCatalogueOutput( self, i, *unused ) :
		self._setState( self.__defaultNodeSet, i )

	def __followBookmark( self, i, *unused ) :
		self._setState( Gaffer.NumericBookmarkSet( self.__scriptNode, i ), 0 )


	def __showEditorFocusMenu( self, *unused ) :

		m = IECore.MenuDefinition()

		m.append( "/Catalogue Divider", { "divider" : True, "label" : "Follow Catalogue Output" } )
		for i in range( 1, 5 ):
			m.append( "/%i"%i, {
				"command" : functools.partial( Gaffer.WeakMethod( self.__followCatalogueOutput ), i ),
				"checkBox" : self.__catalogueOutput == i
				#"shortCut" : "`"
			} )
		m.append( "/Pin Divider", { "divider" : True, "label" : "Pin" } )

		selection = self.__scriptNode.selection()

		if len(selection) == 0 :
			label = "Pin To Nothing"
		elif len(selection) == 1 :
			label = "Pin %s" % selection[0].getName()
		else :
			label = "Pin %d Selected Nodes" % len(selection)

		m.append( "/Pin Node Selection", {
			"command" : Gaffer.WeakMethod( self.__pinToNodeSelection ),
			"label" : label,
			"shortCut" : "p"
		} )

		m.append( "/Follow Divider", { "divider" : True, "label" : "Follow" } )

		m.append( "/Focus Node", {
			"command" : Gaffer.WeakMethod( self.__followFocusNode ),
			"checkBox" : self.__nodeSet.isSame( self.__scriptNode.focusSet() ),
			"shortCut" : "`"
		} )

		m.append( "/Node Selection", {
			"command" : Gaffer.WeakMethod( self.__followNodeSelection ),
			"checkBox" : self.__nodeSet.isSame( selection ),
			"shortCut" : "n"
		} )

		m.append( "/NumericBookmarkDivider", { "divider" : True, "label" : "Follow Numeric Bookmark" } )

		for i in range( 1, 10 ) :
			bookmarkNode = Gaffer.MetadataAlgo.getNumericBookmark( self.__scriptNode, i )
			title = "%d" % i
			if bookmarkNode is not None :
				title += " : %s" % bookmarkNode.getName()
			isCurrent = isinstance( self.__nodeSet, Gaffer.NumericBookmarkSet ) and self.__nodeSet.getBookmark() == i
			m.append( "%s" % title, {
				"command" : functools.partial( Gaffer.WeakMethod( self.__followBookmark ), i ),
				"checkBox" : isCurrent,
			} )

		self.__pinningMenu = GafferUI.Menu( m, title = "Comparison Image" )

		buttonBound = self.__icon.bound()
		self.__pinningMenu.popup(
			parent = self.ancestor( GafferUI.Window ),
			position = imath.V2i( buttonBound.min().x, buttonBound.max().y )
		)

		return True
