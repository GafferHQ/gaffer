##########################################################################
#
#  Copyright (c) 2025, Image Engine Design Inc. All rights reserved.
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

Gaffer.Metadata.registerNode(

	GafferImageUI.ColorInspectorTool,

	"description",
	"""
	Tool for showing color values.
	- Mouse over a pixel to show the color value.
	- Supports dragging color values from a pixel.
	- <kbd>Ctrl</kbd> + click to create a persistent pixel inspector.
	- <kbd>Ctrl</kbd> + drag to create a persistent region inspector.
	""",

	"viewer:shortCut", "I",
	"order", 0,

	"nodeToolbar:bottom:type", "GafferUI.StandardNodeToolbar.bottom",

	plugs = {

		"active" : [

			"boolPlugValueWidget:image", "gafferImageUIColorInspectorTool.png"

		],

		"inspectors" : [
			"plugValueWidget:type", "GafferImageUI.ColorInspectorToolUI._ColorInspectorsPlugValueWidget",
			"label", "",

			"toolbarLayout:section", "Bottom",
		],

		"inspectors.*" : [
			"description", lambda plug :
			{
				GafferImageUI.ColorInspectorTool.ColorInspectorPlug.Mode.Cursor : "Displays the color values of the pixel under the cursor.",
				GafferImageUI.ColorInspectorTool.ColorInspectorPlug.Mode.Pixel : "Displays the color values of pixel inspector {}.".format( plug.getName()[9:] ),
				GafferImageUI.ColorInspectorTool.ColorInspectorPlug.Mode.Area : "Displays the average color values of region inspector {}.".format( plug.getName()[9:] ),
			}[ plug["mode"].getValue() ] + """
			Shows value of each channel, hue/saturation/value, and Exposure Value which is measured in stops relative to 18% grey.
			""",
			"label", "",
			"plugValueWidget:type", "GafferImageUI.ColorInspectorToolUI._ColorInspectorPlugValueWidget",
			"layout:index", lambda plug : 1024-int( "".join( ['0'] + [ i for i in plug.getName() if i.isdigit() ] ) )
		],

	}

)

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

def _v2iFloor( v ):
	return imath.V2i( math.floor( v.x ), math.floor( v.y ) )

def _eventPosition( viewportGadget, event, floor = True ):
	imageGadget = viewportGadget.getPrimaryChild()
	try :
		pixel = imageGadget.pixelAt( viewportGadget.rasterToGadgetSpace( imath.V2f( event.line.p0.x, event.line.p0.y ), imageGadget ) )
	except :
		# `pixelAt()` can throw if there is an error
		# computing the image being viewed. We leave
		# the error reporting to other UI components.
		pixel = imath.V2f( 0 )

	if floor:
		return _v2iFloor( pixel )
	else:
		return imath.V2f( pixel.x, pixel.y )

def _addInspector( inspectorsPlug ):
	suffix = 1
	while "inspector" + str( suffix ) in inspectorsPlug:
		suffix += 1

	inspectorsPlug.addChild( GafferImageUI.ColorInspectorTool.ColorInspectorPlug( "inspector" + str( suffix ) ) )

# Duplicating weird hackery from pixelAspectFromImageGadget in src/GafferImageUI/ImageView.cpp
def _pixelAspectFromImageGadget( imageGadget ) :
	# We want to grab the cached version of imageGadget->format(), but it's not exposed publicly, so we
	# get it from pixelAt.
	# In the future, it would be better if format() was public and we didn't have to worry about it
	# throwing.
	try:
		return 1.0 / imageGadget.pixelAt( IECore.LineSegment3f( imath.V3f( 1, 0, 0 ), imath.V3f( 1, 0, 1 ) ) ).x
	except:
		# Not worried about rendering correctly for images which can't be evaluated properly
		return 1.0

def _transformV2i( v, m, floor = True ) :
	vt = m.multVecMatrix( imath.V3f( v.x + 0.5, v.y + 0.5, 0 ) )

	if floor:
		return imath.V2i( math.floor( vt.x ), math.floor( vt.y ) )
	else:
		return imath.V2f( vt.x, vt.y )

# Returns the source coordinates for both the main image and the compare image, based
# on an input in the coordinate system of the main image.
# The input coordinates can be a Box2i, a V2i, or a V2f ( The cursor may have a fractional
# position in the main image coordinates, allowing the selection of specific comparison pixels
# if the comparison image is scaled differently ).
# The return values is a list of two V2i's or Box2i's ( depending on whether we
# are sampling a single pixel or a region ).
def _toSourceCoordinates( viewportGadget, coordinates ):

	primaryGadget = viewportGadget.getPrimaryChild()
	compareGadget = [
		i for i in viewportGadget.children()
		if isinstance( i, GafferImageUI.ImageGadget )
		and i != primaryGadget
	][0]

	primaryAspect = _pixelAspectFromImageGadget( primaryGadget )
	compareAspect = _pixelAspectFromImageGadget( compareGadget )
	toCompareSpace = imath.M44f()
	toCompareSpace.scale( imath.V3f( primaryAspect, 1.0, 1.0 ) )
	toCompareSpace *= compareGadget.getTransform().inverse()
	toCompareSpace.scale( imath.V3f( 1.0 / compareAspect, 1.0, 1.0 ) )
	toCompareSpace[3][0] /= compareAspect

	if type( coordinates ) == imath.V2f:
		sources = [ _v2iFloor( coordinates ) ] * 2
		if toCompareSpace != imath.M44f():
			sources[1] = _v2iFloor( toCompareSpace.multVecMatrix( imath.V3f( coordinates.x, coordinates.y, 0.0 ) ) )
	elif type( coordinates ) == imath.V2i:
		sources = [ coordinates ] * 2
		if toCompareSpace != imath.M44f():
			sources[1] = _transformV2i( sources[0], toCompareSpace )
	elif type( coordinates ) == imath.Box2i:
		sources = [ coordinates ] * 2
		if toCompareSpace != imath.M44f():
			bMin = _transformV2i( sources[0].min(), toCompareSpace, floor = False )
			bMax = _transformV2i( sources[0].max(), toCompareSpace, floor = False )
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
		raise Exception( "Unsupported data type {}".format( type( coordinates ) ) )

	return sources

def _evaluateColors( colorInspectorTool, sources ):
	colors = [ imath.Color4f( 0, 0, 0, 1 ) ] * 2
	for i in range( 2 ):
		if i == 0:
			c = Gaffer.Context( Gaffer.Context.current() )
		else:
			if colorInspectorTool.view()["compare"]["mode"].getValue() == "":
				# Don't bother computing a color sample for the comparison image if we aren't
				# showing the comparison
				continue

			# We don't want to have to make a separate evaluator plug to evaluate the comparison
			# image, but we do want to use the context created by the __comparisonSelect node.
			# Just grab the context so we can do our own evaluation with it
			c = Gaffer.Context( colorInspectorTool.view()["__comparisonSelect"].inPlugContext() )

		with c :
			if type( sources[i] ) == imath.V2i:
				c["colorInspector:source"] = imath.V2f( sources[i] ) + imath.V2f( 0.5 ) # Center of pixel
				colors[i] = colorInspectorTool["evaluator"]["pixelColor"].getValue()
			elif type( sources[i] ) == imath.Box2i:
				areaEval = colorInspectorTool["evaluator"]["areaColor"]
				c["colorInspector:source"] = GafferImage.BufferAlgo.intersection( sources[i], areaEval.getInput().node()["in"].format().getDisplayWindow() )
				colors[i] = areaEval.getValue()
			else:
				raise Exception( "ColorInspector source must be V2i or Box2i, not " + str( type( sources[i] ) ) )
	return colors


class _ColorInspectorsPlugValueWidget( GafferUI.PlugValueWidget ) :

	__nullObjectForViewportEvents = IECore.NullObject()

	def __init__( self, plug, **kw ) :

		frame = GafferUI.Frame( borderWidth = 4 )
		GafferUI.PlugValueWidget.__init__( self, frame, plug, **kw )

		# Style selector specificity rules seem to preclude us styling this
		# based on gafferClass.
		frame._qtWidget().setObjectName( "gafferColorInspector" )

		with frame :

			GafferUI.LayoutPlugValueWidget( plug )

		self.__createInspectorStartPosition = None

		self.__mouseConnections = []
		viewportGadget = plug.node().view().viewportGadget()

		self.__mouseConnections.append( viewportGadget.buttonPressSignal().connect( Gaffer.WeakMethod( self.__buttonPress ) ) )
		self.__mouseConnections.append( viewportGadget.buttonReleaseSignal().connect( Gaffer.WeakMethod( self.__buttonRelease ) ) )
		self.__mouseConnections.append( viewportGadget.dragBeginSignal().connect( Gaffer.WeakMethod( self.__dragBegin ) ) )
		self.__mouseConnections.append( viewportGadget.dragEnterSignal().connect( Gaffer.WeakMethod( self.__dragEnter ) ) )
		self.__mouseConnections.append( viewportGadget.dragMoveSignal().connect( Gaffer.WeakMethod( self.__dragMove ) ) )
		self.__mouseConnections.append( viewportGadget.dragEndSignal().connect( Gaffer.WeakMethod( self.__dragEnd ) ) )

		plug.node().plugSetSignal().connect( Gaffer.WeakMethod( self.__plugSet ) )

	def __plugSet( self, plug ) :
		if plug == self.getPlug().node()["active"]:
			active = plug.getValue()
			for s in self.__mouseConnections:
				s.setBlocked( not active )

	def __buttonPress( self, viewportGadget, event ) :

		if event.buttons == event.Buttons.Left and not event.modifiers :
			self.__createInspectorStartPosition = None
			return True # accept press so we get dragBegin() for dragging color
		elif event.buttons == event.Buttons.Left and event.modifiers == GafferUI.ModifiableEvent.Modifiers.Control :
			self.__createInspectorStartPosition = _eventPosition( viewportGadget, event )
			_addInspector( self.getPlug() )
			ci = self.getPlug().children()[-1]
			Gaffer.Metadata.registerValue( ci["pixel"], "__hovered", True, persistent = False )
			ci["pixel"].setValue( self.__createInspectorStartPosition )

			return True # creating inspector
		else:
			return False

	def __buttonRelease( self, viewportGadget, event ) :
		if self.__createInspectorStartPosition:
			ci = self.getPlug().children()[-1]
			Gaffer.Metadata.registerValue( ci["pixel"], "__hovered", False, persistent = False )
			Gaffer.Metadata.registerValue( ci["area"], "__hovered", False, persistent = False )

	def __dragBegin( self, viewportGadget, event ) :
		if self.__createInspectorStartPosition:
			# This drag is starting to create a rectangle inspector - just return a special null object
			# to mark this drag.
			return self.__nullObjectForViewportEvents

		# Otherwise, we're going to drag a color value, so we need to compute the color under the current cursor

		cursorPosition = _eventPosition( viewportGadget, event, floor = False )
		sources = _toSourceCoordinates( self.getPlug().node().view().viewportGadget(), cursorPosition )

		inputImagePlug = self.getPlug().node().view()["in"].getInput()
		with inputImagePlug.node().scriptNode().context() :
			colors = _evaluateColors( self.getPlug().node(), sources )

		ig = viewportGadget.getPrimaryChild()
		wipeAngle = ig.getWipeAngle() * math.pi / 180.0
		compareMode = self.getPlug().node().view()["compare"]["mode"].getValue()
		if compareMode == "":
			compositedColor = colors[0]
		elif ig.getWipeEnabled() and ( cursorPosition - ig.getWipePosition() ).dot( imath.V2f( math.cos( wipeAngle ), math.sin( wipeAngle ) ) ) >= 0:
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
			ci = self.getPlug().children()[-1]
			c = imath.Box2i()
			c.extendBy( self.__createInspectorStartPosition )
			c.extendBy( _eventPosition( viewportGadget, event ) )

			# _eventPosition is rounded down, the rectangle should also include the upper end of the
			# pixel containing the cursor
			c.setMax( c.max() + imath.V2i( 1 ) )

			ci["mode"].setValue( GafferImageUI.ColorInspectorTool.ColorInspectorPlug.Mode.Area )
			Gaffer.Metadata.registerValue( ci["pixel"], "__hovered", False, persistent = False )
			Gaffer.Metadata.registerValue( ci["area"], "__hovered", True, persistent = False )
			ci["area"].setValue( c )

		return True

	def __dragEnd( self, viewportGadget, event ) :
		if self.__createInspectorStartPosition:
			ci = self.getPlug().children()[-1]
			Gaffer.Metadata.registerValue( ci["pixel"], "__hovered", False, persistent = False )
			Gaffer.Metadata.registerValue( ci["area"], "__hovered", False, persistent = False )

		GafferUI.Pointer.setCurrent( "" )
		return True

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

		self.__swatch.buttonPressSignal().connect( Gaffer.WeakMethod( self.__buttonPress ) )
		self.__swatch.dragBeginSignal().connect( Gaffer.WeakMethod( self.__dragBegin ) )
		self.__swatch.dragEndSignal().connect( Gaffer.WeakMethod( self.__dragEnd ) )

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

			with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing = 0 ):
				self.__colorValueWidgets = [ _ColorValueWidget( "A" ), _ColorValueWidget( "B" ) ]

			if mode == GafferImageUI.ColorInspectorTool.ColorInspectorPlug.Mode.Cursor:
				m = IECore.MenuDefinition()
				m.append( "/Pixel Inspector",
					{ "command" : functools.partial( Gaffer.WeakMethod( self.__addClick ), GafferImageUI.ColorInspectorTool.ColorInspectorPlug.Mode.Pixel ) }
				)
				m.append( "/Area Inspector",
					{ "command" : functools.partial( Gaffer.WeakMethod( self.__addClick ), GafferImageUI.ColorInspectorTool.ColorInspectorPlug.Mode.Area ) }
				)
				button = GafferUI.MenuButton( "", "plus.png", hasFrame=False, menu = GafferUI.Menu( m, title = "Add Color Inspector" ) )
			else:
				button = GafferUI.Button( "", "delete.png", hasFrame=False )
				button.clickedSignal().connect( Gaffer.WeakMethod( self.__deleteClick ) )


		self.__pixel = imath.V2f( 0 )

		viewportGadget = plug.node().view().viewportGadget()
		viewportGadget.mouseMoveSignal().connect( Gaffer.WeakMethod( self.__mouseMove ) )

		plug.node()["evaluator"]["pixelColor"].getInput().node().plugDirtiedSignal().connect( Gaffer.WeakMethod( self.__updateFromImageNode ) )

		plug.node().view().plugDirtiedSignal().connect( Gaffer.WeakMethod( self.__plugDirtied ) )
		plug.node().plugDirtiedSignal().connect( Gaffer.WeakMethod( self.__plugDirtied ) )

		plug.node().view().contextChangedSignal().connect( Gaffer.WeakMethod( self.__updateFromContext ) )

		Gaffer.Metadata.plugValueChangedSignal( self.getPlug().node() ).connect( Gaffer.WeakMethod( self.__plugMetadataChanged ) )

		self.__updateLabels( [ imath.V2i( 0 ) ] * 2 , [ imath.Color4f( 0, 0, 0, 1 ) ] * 2 )

		# Set initial state of mode icons
		self.__plugDirtied( plug["mode"] )
		self.__plugDirtied( self.getPlug().node().view()["compare"]["mode"] )

	def __addClick( self, mode ):
		_addInspector( self.getPlug().parent() )
		ci = self.getPlug().parent().children()[-1]
		ci["mode"].setValue( mode )
		if mode == GafferImageUI.ColorInspectorTool.ColorInspectorPlug.Mode.Area:
			ci["area"].setValue(
				self.getPlug().node()["evaluator"]["areaColor"].getInput().node()["in"].format().getDisplayWindow()
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
			self.__modeImage._qtWidget().setPixmap( GafferUI.Image._qtPixmapFromFile( [ "sourceCursor.png", "sourcePixel.png", "sourceArea.png" ][ mode ] ) )
		elif childPlug == self.getPlug().node().view()["compare"]["mode"]:
			comparing = self.getPlug().node().view()["compare"]["mode"].getValue() != ""
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

	def __updateFromContext( self, unused ) :

		self.__updateLazily()

	# Returns the source coordinates to sample for this inspector, for both the main image
	# and the compare image, as a list of two V2i's or Box2i's ( depending on whether we
	# are sampling a single pixel or a region )
	def __getSampleSources( self, mode ):

		if mode == GafferImageUI.ColorInspectorTool.ColorInspectorPlug.Mode.Cursor:
			mainCoordinate = self.__pixel
		elif mode == GafferImageUI.ColorInspectorTool.ColorInspectorPlug.Mode.Pixel:
			mainCoordinate = self.getPlug()["pixel"].getValue()
		elif mode == GafferImageUI.ColorInspectorTool.ColorInspectorPlug.Mode.Area:
			mainCoordinate = self.getPlug()["area"].getValue()
		else:
			raise Exception( "ColorInspector mode not recognized <" + mode + ">" )

		return _toSourceCoordinates( self.getPlug().node().view().viewportGadget(), mainCoordinate )


	@GafferUI.LazyMethod()
	def __updateLazily( self ) :

		inputImagePlug = self.getPlug().node().view()["in"].getInput()

		sources = self.__getSampleSources( self.getPlug()["mode"].getValue() )

		if not inputImagePlug:
			# This can happen when the source is deleted - can't get pixel values if there's no input image
			self.__updateLabels( sources, [ imath.Color4f( 0 ) ] * 2 )
			return

		with self.getPlug().node().view().context() :
			self.__updateInBackground( sources )

	@GafferUI.BackgroundMethod()
	def __updateInBackground( self, sources ) :

		colors = _evaluateColors( self.getPlug().node(), sources )

		# TODO : This is a pretty ugly way to find the input node connected to the colorInspector?
		samplerChannels = self.getPlug().node()["evaluator"]["pixelColor"].getInput().node()["channels"].getValue()
		image = self.getPlug().node().view().viewportGadget().getPrimaryChild().getImage()
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
			#   triggered a call to `__plugDirtied()`.
			# - A graph edit that won't trigger a call to `__plugDirtied()`.
			#
			# LazyMethod takes care of all this for us. If we're hidden,
			# it waits till we're visible. If `__plugDirtied()` has already
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
		if mode == GafferImageUI.ColorInspectorTool.ColorInspectorPlug.Mode.Area:
			hovered = Gaffer.Metadata.value( self.getPlug()["area"], "__hovered" )
		if mode == GafferImageUI.ColorInspectorTool.ColorInspectorPlug.Mode.Pixel:
			hovered = Gaffer.Metadata.value( self.getPlug()["pixel"], "__hovered" )

		for i in range( 2 ):
			if i == 1:
				if sources[0] == sources[1] or self.getPlug().node().view()["compare"]["mode"].getValue() == "":
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

			self.__indexLabel.setText( prefix + ( "" if mode == GafferImageUI.ColorInspectorTool.ColorInspectorPlug.Mode.Cursor else "<b>" + self.getPlug().getName()[9:] + "</b>" ) + postfix )
			if type( sources[i] ) == imath.Box2i:
				r = sources[i]
				self.__positionLabels[i].setText( prefix + "<b>%i %i -> %i %i</b>" % ( r.min().x, r.min().y, r.max().x, r.max().y ) + postfix )
			else:
				self.__positionLabels[i].setText( prefix + "<b>XY : %i %i</b>" % ( sources[i].x, sources[i].y ) + postfix )

	def __mouseMove( self, viewportGadget, event ) :

		if not self.getPlug()["mode"].getValue() == GafferImageUI.ColorInspectorTool.ColorInspectorPlug.Mode.Cursor:
			return False

		pixel = _eventPosition( viewportGadget, event, floor = False )

		if pixel == self.__pixel :
			return False

		self.__pixel = pixel

		self.__updateLazily()

		return True
