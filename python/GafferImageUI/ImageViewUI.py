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

from GafferUI.PlugValueWidget import sole

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

			"preset:1", "output:1",
			"preset:2", "output:2",
			"preset:3", "output:3",
			"preset:4", "output:4",
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

	def hasLabel( self ) :

		return True

	def getToolTip( self ) :

		result = GafferUI.PlugValueWidget.getToolTip( self )

		if result :
			result += "\n"
		result += "## Actions\n\n"
		result += "- Click to toggle to/from default value\n"

		return result

	def _updateFromValues( self, values, exception ) :

		value = sole( values )
		if value != self.getPlug().defaultValue() :
			self.__toggleValue = value
			self.__button.setImage( self.__imagePrefix + "On.png" )
		else :
			self.__button.setImage( self.__imagePrefix + "Off.png" )

	def _updateFromEditable( self ) :

		self.__button.setEnabled( self._editable() )

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

class _ColorValueWidget( GafferUI.Widget ) :

	def __init__( self, label, **kw ) :

		l = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 )
		GafferUI.Widget.__init__( self, l, **kw )

		with l:
			self.__idLabel = GafferUI.Label()
			self.__idLabel.setText( "<b>" + label + "</b>" )

			self.__swatch = GafferUI.ColorSwatch()
			self.__swatch._qtWidget().setFixedWidth( 12 )
			self.__swatch._qtWidget().setFixedHeight( 12 )

			self.__busyWidget = GafferUI.BusyWidget( size = 12 )

			self.__rgbLabel = GafferUI.Label()
			labelFont = QtGui.QFont( self.__rgbLabel._qtWidget().font() )
			labelFont.setBold( True )
			labelFont.setPixelSize( 10 )
			labelFontMetrics = QtGui.QFontMetrics( labelFont )
			self.__rgbLabel._qtWidget().setMinimumWidth( labelFontMetrics.boundingRect( "RGBA : 99999 99999 99999 99999" ).width() )

			self.__hsvLabel = GafferUI.Label()
			self.__hsvLabel._qtWidget().setMinimumWidth( labelFontMetrics.boundingRect( "HSV : 99999 99999 99999" ).width() )

			self.__exposureLabel = GafferUI.Label()
			self.__exposureLabel._qtWidget().setMinimumWidth( labelFontMetrics.boundingRect( "EV : 19.9" ).width() )

			# All the characters we're using in these text boxes have no descenders, so cropping off the bottom
			# yields better centered characters
			self.__idLabel._qtWidget().setMaximumHeight( 11 )
			self.__rgbLabel._qtWidget().setMaximumHeight( 11 )
			self.__hsvLabel._qtWidget().setMaximumHeight( 11 )
			self.__exposureLabel._qtWidget().setMaximumHeight( 11 )

			GafferUI.Spacer( size = imath.V2i( 0 ) )

		self.__swatch.buttonPressSignal().connect( Gaffer.WeakMethod( self.__buttonPress ), scoped = False )
		self.__swatch.dragBeginSignal().connect( Gaffer.WeakMethod( self.__dragBegin ), scoped = False )
		self.__swatch.dragEndSignal().connect( Gaffer.WeakMethod( self.__dragEnd ), scoped = False )

		self.setColor( imath.Color4f( 0, 0, 0, 1 ) )

	def setLabelVisible( self, visible ):
		self.__idLabel.setVisible( visible )

	def setBusy( self, busy ):
		self.__busyWidget.setBusy( busy )

	def setColor( self, color ):
		self.__color = color
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

	def __buttonPress( self, imageGadget, event ) :

		if event.buttons == event.Buttons.Left and not event.modifiers :
			return True # accept press so we get dragBegin() for dragging color
		return False

	def __dragBegin( self, imageGadget, event ) :
		GafferUI.Pointer.setCurrent( "rgba" )
		return self.__color

	def __dragEnd( self, imageGadget, event ) :
		GafferUI.Pointer.setCurrent( "" )
		return True

class _ColorInspectorPlugValueWidget( GafferUI.PlugValueWidget ) :

	__nullObjectForViewportEvents = IECore.NullObject()

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

			with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing = 0 ):
				self.__positionLabels = [ GafferUI.Label(), GafferUI.Label() ]
				for i in self.__positionLabels:
					i._qtWidget().setMinimumWidth( labelFontMetrics.boundingRect( "9999 9999 -> 9999 9999" ).width() )
					# All the characters we're using in these text boxes have no descenders, so cropping off
					# the bottom yields better centered characters
					i._qtWidget().setMaximumHeight( 11 )

			with  GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing = 0 ):
				self.__colorValueWidgets = [ _ColorValueWidget( "A" ), _ColorValueWidget( "B" ) ]

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


		self.__pixel = imath.V2f( 0 )
		self.__createInspectorStartPosition = None

		if plug.getName() == "ColorInspectorPlug":
			viewportGadget = plug.node().viewportGadget()

			viewportGadget.mouseMoveSignal().connect( Gaffer.WeakMethod( self.__mouseMove ), scoped = False )
			viewportGadget.buttonPressSignal().connect( Gaffer.WeakMethod( self.__buttonPress ), scoped = False )
			viewportGadget.buttonReleaseSignal().connect( Gaffer.WeakMethod( self.__buttonRelease ), scoped = False )
			viewportGadget.dragBeginSignal().connect( Gaffer.WeakMethod( self.__dragBegin ), scoped = False )
			viewportGadget.dragEnterSignal().connect( Gaffer.WeakMethod( self.__dragEnter ), scoped = False )
			viewportGadget.dragMoveSignal().connect( Gaffer.WeakMethod( self.__dragMove ), scoped = False )
			viewportGadget.dragEndSignal().connect( Gaffer.WeakMethod( self.__dragEnd ), scoped = False )

		plug.node()["colorInspector"]["evaluator"]["pixelColor"].getInput().node().plugDirtiedSignal().connect( Gaffer.WeakMethod( self.__updateFromImageNode ), scoped = False )

		plug.node().plugDirtiedSignal().connect( Gaffer.WeakMethod( self.__plugDirtied ), scoped = False )
		plug.node()["in"].getInput().node().scriptNode().context().changedSignal().connect( Gaffer.WeakMethod( self.__updateFromContext ), scoped = False )
		Gaffer.Metadata.plugValueChangedSignal( self.getPlug().node() ).connect( Gaffer.WeakMethod( self.__plugMetadataChanged ), scoped = False )

		self.__updateLabels( [ imath.V2i( 0 ) ] * 2 , [ imath.Color4f( 0, 0, 0, 1 ) ] * 2 )

		# Set initial state of mode icons
		self.__plugDirtied( plug["mode"] )
		self.__plugDirtied( self.getPlug().node()["compare"]["mode"] )

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

	# We don't fit neatly into PlugValueWidget's `_updateFromValues()` scheme,
	# because we have a lot of custom logic in `__getSampleSources` and also depend
	# on plug's that other than `self.getPlug()`. So we implement our own updates
	# manually via `__plugDirtied`.
	def __plugDirtied( self, childPlug ):

		if self.getPlug().node() is None :
			# If the plug has been unparented, we're going to be deleted, and we
			# no longer need to worry about updating anything.
			return

		if childPlug == self.getPlug()["mode"]:
			mode = self.getPlug()["mode"].getValue()
			## \todo - should GafferUI.Image have a setImage?
			self.__modeImage._qtWidget().setPixmap( GafferUI.Image._qtPixmapFromFile( [ "sourceCursor.png", "sourcePixel.png", "sourceArea.png" ][ mode ]  ) )
		elif childPlug == self.getPlug().node()["compare"]["mode"]:
			comparing = self.getPlug().node()["compare"]["mode"].getValue() != ""
			for c in self.__colorValueWidgets:
				c.setLabelVisible( comparing )
			self.__colorValueWidgets[1].setVisible( comparing )
			self.__updateLazily()
		elif childPlug == self.getPlug() :
			self.__updateLazily()

	def __plugMetadataChanged( self, plug, key, reason ):
		if key == "__hovered" and ( plug == self.getPlug()["area"] or plug == self.getPlug()["pixel"] ):
			# We could avoid the extra compute of the color at the cost of a little extra complexity if
			# we stored the last evaluated color so we could directly call _updateLabels
			self.__updateLazily()

	def __updateFromContext( self, context, name ) :

		self.__updateLazily()

	@staticmethod
	# Duplicating weird hackery from pixelAspectFromImageGadget in src/GafferImageUI/ImageView.cpp
	def __pixelAspectFromImageGadget( imageGadget ) :
		# We want to grab the cached version of imageGadget->format(), but it's not exposed publicly, so we
		# get it from pixelAt.
		# In the future, it would be better if format() was public and we didn't have to worry about it
		# throwing.
		try:
			return 1.0 / imageGadget.pixelAt( IECore.LineSegment3f( imath.V3f( 1, 0, 0 ), imath.V3f( 1, 0, 1 ) ) ).x
		except:
			# Not worried about rendering correctly for images which can't be evaluated properly
			return 1.0

	@staticmethod
	def __transformV2i( v, m, floor = True ) :
		vt = m.multVecMatrix( imath.V3f( v.x + 0.5, v.y + 0.5, 0 ) )

		if floor:
			return imath.V2i( math.floor( vt.x ), math.floor( vt.y ) )
		else:
			return imath.V2f( vt.x, vt.y )

	# Returns the source coordinates to sample for this inspector, for both the main image
	# and the compare image, as a list of two V2i's or Box2i's ( depending on whether we
	# are sampling a single pixel or a region )
	def __getSampleSources( self, mode ):

		primaryGadget = self.getPlug().node().viewportGadget().getPrimaryChild()
		compareGadget = [
			i for i in self.getPlug().node().viewportGadget().children()
			if isinstance( i, GafferImageUI.ImageGadget )
			and i != primaryGadget
		][0]

		primaryAspect = self.__pixelAspectFromImageGadget( primaryGadget )
		compareAspect = self.__pixelAspectFromImageGadget( compareGadget )
		toCompareSpace = imath.M44f()
		toCompareSpace.scale( imath.V3f( primaryAspect, 1.0, 1.0 ) )
		toCompareSpace *= compareGadget.getTransform().inverse()
		toCompareSpace.scale( imath.V3f( 1.0 / compareAspect, 1.0, 1.0 ) )
		toCompareSpace[3][0] /= compareAspect

		if mode == GafferImageUI.ImageView.ColorInspectorPlug.Mode.Cursor:
			sources = [ self.__V2iFloor( self.__pixel ) ] * 2
			if toCompareSpace != imath.M44f():
				sources[1] = self.__V2iFloor( toCompareSpace.multVecMatrix( imath.V3f( self.__pixel.x, self.__pixel.y, 0.0 ) ) )
		elif mode == GafferImageUI.ImageView.ColorInspectorPlug.Mode.Pixel:
			sources = [ self.getPlug()["pixel"].getValue() ] * 2
			if toCompareSpace != imath.M44f():
				sources[1] = self.__transformV2i( sources[0], toCompareSpace )
		elif mode == GafferImageUI.ImageView.ColorInspectorPlug.Mode.Area:
			sources = [ self.getPlug()["area"].getValue() ] * 2
			if toCompareSpace != imath.M44f():
				bMin = self.__transformV2i( sources[0].min(), toCompareSpace, floor = False )
				bMax = self.__transformV2i( sources[0].max(), toCompareSpace, floor = False )
				ibMin = imath.V2i( round( bMin.x ), round( bMin.y ) )
				ibMax = imath.V2i( round( bMax.x ), round( bMax.y ) )
				if ibMin.x == ibMax.x:
					ibMin.x = math.floor( bMin.x )
					ibMax.x = math.ceil( bMax.x )
				if ibMin.y == ibMax.y:
					ibMin.y = math.floor( bMin.y )
					ibMax.y = math.ceil( bMax.y )
				sources[1] = imath.Box2i( ibMin, ibMax )
		else:
			raise Exception( "ColorInspector mode not recognized <" + mode + ">" )

		return sources

	@GafferUI.LazyMethod()
	def __updateLazily( self ) :

		inputImagePlug = self.getPlug().node()["in"].getInput()

		sources = self.__getSampleSources( self.getPlug()["mode"].getValue() )

		if not inputImagePlug:
			# This can happen when the source is deleted - can't get pixel values if there's no input image
			self.__updateLabels( sources, [ imath.Color4f( 0 ) ] * 2 )
			return

		with inputImagePlug.node().scriptNode().context() :
			self.__updateInBackground( sources )

	def __evaluateColors( self, sources ):
		colors = [ imath.Color4f( 0, 0, 0, 1 ) ] * 2
		for i in range( 2 ):
			if i == 0:
				c = Gaffer.Context( Gaffer.Context.current() )
			else:
				if self.getPlug().node()["compare"]["mode"].getValue() == "":
					# Don't bother computing a color sample for the comparison image if we aren't
					# showing the comparison
					continue

				# We don't want to have to make a separate evaluator plug to evaluate the comparison
				# image, but we do want to use the context created by the __comparisonSelect node.
				# Just grab the context so we can do our own evaluation with it
				c = Gaffer.Context( self.getPlug().node()["__comparisonSelect"].inPlugContext() )

			with c :
				if type( sources[i] ) == imath.V2i:
					c["colorInspector:source"] = imath.V2f( sources[i] ) + imath.V2f( 0.5 ) # Center of pixel
					colors[i] = self.getPlug().node()["colorInspector"]["evaluator"]["pixelColor"].getValue()
				elif type( sources[i] ) == imath.Box2i:
					areaEval = self.getPlug().node()["colorInspector"]["evaluator"]["areaColor"]
					c["colorInspector:source"] = GafferImage.BufferAlgo.intersection( sources[i], areaEval.getInput().node()["in"].format().getDisplayWindow() )
					colors[i] = areaEval.getValue()
				else:
					raise Exception( "ColorInspector source must be V2i or Box2i, not " + str( type( sources[i] ) ) )
		return colors

	@GafferUI.BackgroundMethod()
	def __updateInBackground( self, sources ) :

		colors = self.__evaluateColors( sources )

		# TODO : This is a pretty ugly way to find the input node connected to the colorInspector?
		samplerChannels = self.getPlug().node()["colorInspector"]["evaluator"]["pixelColor"].getInput().node()["channels"].getValue()
		image = self.getPlug().node().viewportGadget().getPrimaryChild().getImage()
		channelNames = image["channelNames"].getValue()

		if samplerChannels[3] not in channelNames :
			colors = [ imath.Color3f( color[0], color[1], color[2] ) for color in colors ]

		return sources, colors

	@__updateInBackground.preCall
	def __updateInBackgroundPreCall( self ) :

		for c in self.__colorValueWidgets:
			c.setBusy( True )

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
			self.__updateLabels( [ self.__pixel ] * 2, [ imath.Color4f( 0 ) ] * 2 )
		else :
			# Success. We have valid infomation to display.
			self.__updateLabels( backgroundResult[0], backgroundResult[1] )

			for c in self.__colorValueWidgets:
				c.setBusy( False )

	def __updateLabels( self, sources, colors ) :

		self.__colorValueWidgets[0].setColor( colors[0] )
		self.__colorValueWidgets[1].setColor( colors[1] )

		mode = self.getPlug()["mode"].getValue()

		hovered = False
		if mode == GafferImageUI.ImageView.ColorInspectorPlug.Mode.Area:
			hovered = Gaffer.Metadata.value( self.getPlug()["area"], "__hovered" )
		if mode == GafferImageUI.ImageView.ColorInspectorPlug.Mode.Pixel:
			hovered = Gaffer.Metadata.value( self.getPlug()["pixel"], "__hovered" )

		for i in range( 2 ):
			if i == 1:
				if sources[0] == sources[1] or self.getPlug().node()["compare"]["mode"].getValue() == "":
					self.__positionLabels[1].setVisible( False )
					continue
				else:
					self.__positionLabels[1].setVisible( True )

			prefix = ""
			postfix = ""
			if i == 0 and hovered:
				# Chosen to match brightColor in python/GafferUI/_Stylesheet.py
				prefix = '<font color="#779cbd">'
				postfix = '</font>'

			self.__indexLabel.setText( prefix + ( "" if mode == GafferImageUI.ImageView.ColorInspectorPlug.Mode.Cursor else "<b>" + self.getPlug().getName()[1:] + "</b>" ) + postfix )
			if type( sources[i] ) == imath.Box2i:
				r = sources[i]
				self.__positionLabels[i].setText( prefix + "<b>%i %i -> %i %i</b>" % ( r.min().x, r.min().y, r.max().x, r.max().y ) + postfix )
			else:
				self.__positionLabels[i].setText( prefix + "<b>XY : %i %i</b>" % ( sources[i].x, sources[i].y ) + postfix )

	@staticmethod
	def __V2iFloor( v ):
		return imath.V2i( math.floor( v.x ), math.floor( v.y ) )

	def __eventPosition( self, viewportGadget, event, floor = True ):
		imageGadget = viewportGadget.getPrimaryChild()
		try :
			pixel = imageGadget.pixelAt( viewportGadget.rasterToGadgetSpace( imath.V2f( event.line.p0.x, event.line.p0.y ), imageGadget ) )
		except :
			# `pixelAt()` can throw if there is an error
			# computing the image being viewed. We leave
			# the error reporting to other UI components.
			pixel = imath.V2f( 0 )

		if floor:
			return self.__V2iFloor( pixel )
		else:
			return imath.V2f( pixel.x, pixel.y )

	def __mouseMove( self, viewportGadget, event ) :
		pixel = self.__eventPosition( viewportGadget, event, floor = False )

		if pixel == self.__pixel :
			return False

		self.__pixel = pixel

		self.__updateLazily()

		return True

	def __buttonPress( self, viewportGadget, event ) :
		if event.buttons == event.Buttons.Left and not event.modifiers :
			self.__createInspectorStartPosition = None
			return True # accept press so we get dragBegin() for dragging color
		elif event.buttons == event.Buttons.Left and event.modifiers == GafferUI.ModifiableEvent.Modifiers.Control :
			self.__createInspectorStartPosition = self.__eventPosition( viewportGadget, event )
			self.__addInspector()
			ci = self.getPlug().parent().children()[-1]
			Gaffer.Metadata.registerValue( ci["pixel"], "__hovered", True, persistent = False )
			ci["pixel"].setValue( self.__createInspectorStartPosition )

			return True # creating inspector
		else:
			return False

	def __buttonRelease( self, viewportGadget, event ) :
		if self.__createInspectorStartPosition:
			ci = self.getPlug().parent().children()[-1]
			Gaffer.Metadata.registerValue( ci["pixel"], "__hovered", False, persistent = False )
			Gaffer.Metadata.registerValue( ci["area"], "__hovered", False, persistent = False )

	def __dragBegin( self, viewportGadget, event ) :
		if self.__createInspectorStartPosition:
			return self.__nullObjectForViewportEvents


		sources = self.__getSampleSources( GafferImageUI.ImageView.ColorInspectorPlug.Mode.Cursor )

		inputImagePlug = self.getPlug().node()["in"].getInput()
		with inputImagePlug.node().scriptNode().context() :
			colors = self.__evaluateColors( sources )

		ig = viewportGadget.getPrimaryChild()
		wipeAngle = ig.getWipeAngle() * math.pi / 180.0
		compareMode = self.getPlug().node()["compare"]["mode"].getValue()
		if compareMode == "":
			compositedColor = colors[0]
		elif ig.getWipeEnabled() and ( self.__pixel - ig.getWipePosition() ).dot( imath.V2f( math.cos( wipeAngle ), math.sin( wipeAngle ) ) ) >= 0:
			compositedColor = colors[1]
		else:
			if compareMode == "replace":
				compositedColor = colors[0]
			elif compareMode == "over":
				compositedColor = colors[0] + colors[1] * ( 1.0 - colors[0].a )
			elif compareMode == "under":
				compositedColor = colors[1] + colors[0] * ( 1.0 - colors[1].a )
			elif compareMode == "difference":
				diff = colors[1] - colors[0]
				compositedColor = imath.Color4f( abs( diff.r ), abs( diff.g ), abs( diff.b ), abs( diff.a ) )

		GafferUI.Pointer.setCurrent( "rgba" )
		return compositedColor

	def __dragEnter( self, viewportGadget, event ) :
		if not event.data.isSame( self.__nullObjectForViewportEvents ):
			return False

		return True

	def __dragMove( self, viewportGadget, event ) :
		if self.__createInspectorStartPosition:
			ci = self.getPlug().parent().children()[-1]
			c = imath.Box2i()
			c.extendBy( self.__createInspectorStartPosition )
			c.extendBy( self.__eventPosition( viewportGadget, event ) )

			# __eventPosition is rounded down, the rectangle should also include the upper end of the
			# pixel containing the cursor
			c.setMax( c.max() + imath.V2i( 1 ) )

			ci["mode"].setValue( GafferImageUI.ImageView.ColorInspectorPlug.Mode.Area )
			Gaffer.Metadata.registerValue( ci["pixel"], "__hovered", False, persistent = False )
			Gaffer.Metadata.registerValue( ci["area"], "__hovered", True, persistent = False )
			ci["area"].setValue( c )

		return True

	def __dragEnd( self, viewportGadget, event ) :
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

	def _updateFromValues( self, values, exception ) :

		self.__button.setImage( "soloChannel{0}.png".format( sole( values ) ) )

	def _updateFromEditable( self ) :

		self.__button.setEnabled( self._editable() )

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

		# We connect to the front, and unconditionally return True from all these methods, to
		# ensure that we never run any of the default signal handlers from PlugValueWidget
		self.dragEnterSignal().connectFront( Gaffer.WeakMethod( self.__dragEnter ), scoped = False )
		self.dragLeaveSignal().connectFront( Gaffer.WeakMethod( self.__dragLeave ), scoped = False )
		self.dropSignal().connectFront( Gaffer.WeakMethod( self.__drop ), scoped = False )

	@staticmethod
	def _valuesForUpdate( plugs, auxiliaryPlugs ) :

		return [ p["mode"].getValue() for p in plugs ]

	def _updateFromValues( self, values, exception ) :

		m = sole( values )
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
			self.__row[-1]._setState( Gaffer.StandardSet( [ node ] ), "" )

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

	def _updateFromValues( self, values, exception ) :

		v = sole( values )
		if v :
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

	def _updateFromValues( self, values, exception ) :

		self.__button.setImage(
			"wipeEnabled.png" if sole( values ) else "wipeDisabled.png"
		)

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
		self.__catalogueOutput = ""

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

		self._setState( self.__defaultNodeSet, Gaffer.NodeAlgo.presets( self.__node["compare"]["catalogueOutput"] )[0] )

	def _setState( self, nodeSet, catalogueOutputPreset ):

		assert( isinstance( catalogueOutputPreset, str ) )

		self.__nodeSet = nodeSet
		self.__catalogueOutput = catalogueOutputPreset
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
		if self.__catalogueOutput != "":
			Gaffer.NodeAlgo.applyPreset( self.__node["compare"]["catalogueOutput"], self.__catalogueOutput )
		else:
			self.__node["compare"]["catalogueOutput"].setValue( "" )

		# Icon

		if self.__catalogueOutput != "":
			try:
				icon = "catalogueOutput%s.png" % self.__catalogueOutput
				# Try loading icon just to check for validity ( taking advantage of the icon cache )
				GafferUI.Image._qtPixmapFromFile( icon )
			except:
				# Icon doesn't exist, use a default
				icon = "catalogueOutputHeader.png"
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
		if self.__catalogueOutput != "":
			toolTipElements.append( "" )
			toolTipElements.append( "Comparing to Catalogue output " + self.__catalogueOutput )
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
		self._setState( Gaffer.StandardSet( list( self.__scriptNode.selection() ) ), "" )

	def __followNodeSelection( self, *unused ) :
		self._setState( self.__scriptNode.selection(), "" )

	def __followFocusNode( self, *unused ) :
		self._setState( self.__scriptNode.focusSet(), "" )

	def __followCatalogueOutput( self, i, *unused ) :
		self._setState( self.__defaultNodeSet, i )

	def __followBookmark( self, i, *unused ) :
		self._setState( Gaffer.NumericBookmarkSet( self.__scriptNode, i ), "" )


	def __showEditorFocusMenu( self, *unused ) :

		m = IECore.MenuDefinition()

		m.append( "/Catalogue Divider", { "divider" : True, "label" : "Follow Catalogue Output" } )
		for i in Gaffer.NodeAlgo.presets( self.__node["compare"]["catalogueOutput"] ):
			m.append( "/CatalogueOutput{}".format( i ), {
				"command" : functools.partial( Gaffer.WeakMethod( self.__followCatalogueOutput ), i ),
				"checkBox" : self.__catalogueOutput == i,
				"label" : i,
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
			m.append( "/NumericBookMark{}".format( i ), {
				"command" : functools.partial( Gaffer.WeakMethod( self.__followBookmark ), i ),
				"checkBox" : isCurrent,
				"label" : title,
			} )

		self.__pinningMenu = GafferUI.Menu( m, title = "Comparison Image" )

		buttonBound = self.__icon.bound()
		self.__pinningMenu.popup(
			parent = self.ancestor( GafferUI.Window ),
			position = imath.V2i( buttonBound.min().x, buttonBound.max().y )
		)

		return True
