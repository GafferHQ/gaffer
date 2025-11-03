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

	plugs = {

		"view" : {

			"description" :
			"""
			Chooses view to display from a multi-view image.  The "default" view is used for normal images
			that don't have specific views.
			""",

			"plugValueWidget:type" : "GafferImageUI.ImageViewUI._ImageView_ViewPlugValueWidget",
			"toolbarLayout:width" : 125,
			"label" : "",
			"toolbarLayout:divider" : True,

		},

		"compare" : {
			"plugValueWidget:type" : "GafferImageUI.ImageViewUI._CompareParentPlugValueWidget",
			"toolbarLayout:divider" : True,
			"label" : "",
		},

		"compare.mode" : {

			"description" :
			"""
			Enables a comparison mode to view two images at once - they can be composited under or over, or
			subtracted for a difference view.  Or replace mode just shows the front image, which is useful
			in combination with the Wipe tool.
			""",

			"plugValueWidget:type" : "GafferImageUI.ImageViewUI._CompareModePlugValueWidget",

		},

		"compare.matchDisplayWindows" : {
			# matchDisplayWindows is also handled by _CompareModePlugValueWidget
			"plugValueWidget:type" : "",
		},

		"compare.wipe" : {

			"description" :
			"""
			Enables a wipe tool to hide part of the image, for comparing with the background image.
			Hotkey W.
			""",

			"plugValueWidget:type" : "GafferImageUI.ImageViewUI._CompareWipePlugValueWidget",

		},

		"compare.image" : {

			"description" :
			"""
			The image to compare with.
			""",

			"plugValueWidget:type" : "GafferImageUI.ImageViewUI._CompareImageWidget",

		},

		"compare.catalogueOutput" : {
			# catalogueOutput is also handled by _CompareImageWidget
			"plugValueWidget:type" : "",

			"preset:1" : "output:1",
			"preset:2" : "output:2",
			"preset:3" : "output:3",
			"preset:4" : "output:4",
		},


		"channels" : {

			"description" :
			"""
			Chooses an RGBA layer or an auxiliary channel to display.
			""",

			"plugValueWidget:type" : "GafferImageUI.ImageViewUI._ChannelsPlugValueWidget",
			"toolbarLayout:width" : 175,
			"label" : "",

		},


	}

)

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
			Gaffer.WeakMethod( self.__keyPress )
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
			Gaffer.WeakMethod( self.__keyPress )
		)

	def _image( self ):

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

		firstValue = next( iter( self._rgbaChannels().values() ), None )
		result.append(
			"/First",
			{
				"command" : functools.partial( Gaffer.WeakMethod( self.__setValue ), value = firstValue ),
				"shortCut" : "Ctrl+PgUp",
				"active" : firstValue is not None and firstValue != currentValue,
			}
		)

		return result

	def __keyPress( self, gadget, event ) :

		if event.key in ( "PageUp", "PageDown" ) :
			if event.key == "PageDown" :
				value = self.__incrementedValue( 1 )
			elif event.modifiers == event.Modifiers.Control :
				value = next( iter( self._rgbaChannels().values() ), None )
			else :
				value = self.__incrementedValue( -1 )
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

		self.__button.clickedSignal().connect( Gaffer.WeakMethod( self.__buttonClick ) )

		# We use the paused state of the primary ImageGadget to drive our UI
		self.__imageGadgets[0].stateChangedSignal().connect( Gaffer.WeakMethod( self.__stateChanged ) )

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
		self.dragEnterSignal().connectFront( Gaffer.WeakMethod( self.__dragEnter ) )
		self.dragLeaveSignal().connectFront( Gaffer.WeakMethod( self.__dragLeave ) )
		self.dropSignal().connectFront( Gaffer.WeakMethod( self.__drop ) )

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
			"add" : "compareModeAdd.png",
			"difference" : "compareModeDifference.png",
			"sideBySide" : "compareModeSideBySide.png",
			"replace" : "compareModeReplace.png",
		}

		plug.node().viewportGadget().keyPressSignal().connect(
			Gaffer.WeakMethod( self.__keyPress )
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
			return Gaffer.Metadata.value( self.getPlug(), "imageViewer:lastCompareMode" ) or "replace"
		else:
			return ""

	def __keyPress( self, gadget, event ) :

		if event.key == "K" and not event.modifiers :
			self.__setValue( self.__hotkeyTarget() )
			return True

		return False

	def __menuDefinition( self ) :

		with self.context() :
			compareMode = self.getPlug().getValue()

		hotkeyTarget = self.__hotkeyTarget()

		m = IECore.MenuDefinition()
		for name, value in [
			( "None", "" ),
			( "Over", "over" ),
			( "Under", "under" ),
			( "Add", "add" ),
			( "Difference", "difference" ),
			( "Replace", "replace" ),
		] :
			m.append(
				"/" + name,
				{
					"command" : functools.partial( Gaffer.WeakMethod( self.__setValue ), value ),
					"icon" : self.__iconDict[value],
					"checkBox" : value == compareMode,
					"shortCut" : "K" if value == hotkeyTarget else None,
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

		self.__button.clickedSignal().connect( Gaffer.WeakMethod( self.__toggle ) )
		plug.node().viewportGadget().keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPress ) )

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
			self.__bookmarkNumber.buttonPressSignal().connect( Gaffer.WeakMethod( self.__showEditorFocusMenu ) )

			self.__icon = GafferUI.Button( hasFrame=False, highlightOnOver=False )
			self.__icon._qtWidget().setFixedHeight( 13 )
			self.__icon._qtWidget().setFixedWidth( 13 )
			self.__icon.buttonPressSignal().connect( Gaffer.WeakMethod( self.__showEditorFocusMenu ) )

			self.__menuButton = GafferUI.Button( image="menuIndicator.png", hasFrame=False, highlightOnOver=False )
			self.__menuButton._qtWidget().setObjectName( "menuDownArrow" )
			self.__menuButton.buttonPressSignal().connect( Gaffer.WeakMethod( self.__showEditorFocusMenu ) )

		self.addChild( row )

		self.buttonPressSignal().connect( Gaffer.WeakMethod( self.__showEditorFocusMenu ) )

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
