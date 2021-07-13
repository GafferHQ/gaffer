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
	"toolbarLayout:customWidget:BottomRightSpacer:index", 2,

	"layout:activator:gpuAvailable", lambda node : ImageViewUI.createDisplayTransform( node["displayTransform"].getValue() ).isinstance( GafferImage.OpenColorIOTransform ),

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
			"toolbarLayout:index", 4,

		],

		"exposure" : [

			"description",
			"""
			Applies an exposure adjustment to the image.
			""",

			"plugValueWidget:type", "GafferImageUI.ImageViewUI._TogglePlugValueWidget",
			"togglePlugValueWidget:imagePrefix", "exposure",
			"togglePlugValueWidget:defaultToggleValue", 1,
			"toolbarLayout:index", 5,

		],

		"gamma" : [

			"description",
			"""
			Applies a gamma correction to the image.
			""",

			"plugValueWidget:type", "GafferImageUI.ImageViewUI._TogglePlugValueWidget",
			"togglePlugValueWidget:imagePrefix", "gamma",
			"togglePlugValueWidget:defaultToggleValue", 2,
			"toolbarLayout:index", 6,

		],

		"displayTransform" : [

			"description",
			"""
			Applies colour space transformations for viewing the image correctly.
			""",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
			"label", "",
			"toolbarLayout:width", 100,
			"toolbarLayout:index", 7,

			"presetNames", lambda plug : IECore.StringVectorData( GafferImageUI.ImageView.registeredDisplayTransforms() ),
			"presetValues", lambda plug : IECore.StringVectorData( GafferImageUI.ImageView.registeredDisplayTransforms() ),

		],

		"lutGPU" : [
			"description",
			"""
			Controls whether to use the fast GPU path for applying exposure, gamma, and displayTransform.
			Much faster, but may suffer loss of accuracy in some corner cases.
			""",

			"plugValueWidget:type", "GafferImageUI.ImageViewUI._LutGPUPlugValueWidget",
			"toolbarLayout:index", 8,
			"label", "",
			"layout:activator", "gpuAvailable",
		],


		"colorInspector" : [
			"plugValueWidget:type", "GafferUI.LayoutPlugValueWidget",
			"toolbarLayout:section", "Bottom",
			"toolbarLayout:index", 1,
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

		"channels" : [

			"description",
			"""
			Chooses an RGBA layer or an auxiliary channel to display.
			""",

			"plugValueWidget:type", "GafferImageUI.RGBAChannelsPlugValueWidget",
			"toolbarLayout:index", 2,
			"toolbarLayout:width", 175,
			"label", "",

		],

		"soloChannel" : [

			"description",
			"""
			Chooses a channel to show in isolation.
			""",

			"plugValueWidget:type", "GafferImageUI.ImageViewUI._SoloChannelPlugValueWidget",
			"toolbarLayout:index", 3,
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
			self.__indexLabel._qtWidget().setMinimumWidth( labelFontMetrics.width( "99" ) )

			self.__modeImage = GafferUI.Image( "sourceCursor.png" )

			self.__positionLabel = GafferUI.Label()
			self.__positionLabel._qtWidget().setMinimumWidth( labelFontMetrics.width( "9999 9999 -> 9999 9999" ) )

			self.__swatch = GafferUI.ColorSwatch()
			self.__swatch._qtWidget().setFixedWidth( 12 )
			self.__swatch._qtWidget().setFixedHeight( 12 )

			self.__busyWidget = GafferUI.BusyWidget( size = 12 )

			self.__rgbLabel = GafferUI.Label()
			self.__rgbLabel._qtWidget().setMinimumWidth( labelFontMetrics.width( "RGBA : 99999 99999 99999 99999" ) )

			self.__hsvLabel = GafferUI.Label()
			self.__hsvLabel._qtWidget().setMinimumWidth( labelFontMetrics.width( "HSV : 99999 99999 99999" ) )

			self.__exposureLabel = GafferUI.Label()
			self.__exposureLabel._qtWidget().setMinimumWidth( labelFontMetrics.width( "EV : 19.9" ) )

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

		m.append( "/LuminanceDivider", { "divider" : True, })

		m.append(
				"/Luminance",
				{
					"command" : functools.partial( Gaffer.WeakMethod( self.__setValue ), -2 ),
					"checkBox" : soloChannel == -2
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
				text += "Running LUT on GPU ( fast mode )."
			else:
				text += "Running LUT on CPU ( slow but accurate mode )."
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
			( "GPU (fast)", True ),
			( "CPU (accurate)", False )
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

		self.__imageGadget = imageView.viewportGadget().getPrimaryChild()

		self.__button.clickedSignal().connect( Gaffer.WeakMethod( self.__buttonClick ), scoped = False )

		self.__imageGadget.stateChangedSignal().connect( Gaffer.WeakMethod( self.__stateChanged ), scoped = False )

		self.__update()

	def __stateChanged( self, imageGadget ) :

		self.__update()

	def __buttonClick( self, button ) :

		self.__imageGadget.setPaused( not self.__imageGadget.getPaused() )

	def __update( self ) :

		paused = self.__imageGadget.getPaused()
		self.__button.setImage( "viewPause.png" if not paused else "viewPaused.png" )
		self.__busyWidget.setBusy( self.__imageGadget.state() == self.__imageGadget.State.Running )
		self.__button.setToolTip( "Viewer updates suspended, click to resume" if paused else "Click to suspend viewer updates [esc]" )
