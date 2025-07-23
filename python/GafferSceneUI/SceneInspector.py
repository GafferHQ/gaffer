##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
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

import imath

import IECore

import Gaffer
import GafferScene
import GafferUI
import GafferSceneUI

from GafferUI.PlugValueWidget import sole

from . import _GafferSceneUI

from Qt import QtWidgets

class SceneInspector( GafferSceneUI.SceneEditor ) :

	class Settings( GafferSceneUI.SceneEditor.Settings ) :

		def __init__( self ) :

			GafferSceneUI.SceneEditor.Settings.__init__( self )

			# Public plugs
			# ============

			self["editScope"] = Gaffer.Plug()
			self["location"] = Gaffer.StringPlug()

			self["compare"] = Gaffer.Plug()
			self["compare"]["location"] = Gaffer.OptionalValuePlug( valuePlug = Gaffer.StringPlug() )
			self["compare"]["scene"] = Gaffer.OptionalValuePlug( valuePlug = GafferScene.ScenePlug() )
			self["compare"]["renderPass"] = Gaffer.OptionalValuePlug( valuePlug = Gaffer.StringPlug() )

			# Stop the input scenes claiming that all locations exist when
			# they don't have an input.
			self["in"]["exists"].setValue( False )
			self["compare"]["scene"]["value"]["exists"].setValue( False )

			# Internal network
			# ================

			# The core of our internal network is a switch between two input
			# scenes : `in` and `compare.scene.value`. This is driven by a
			# `__sceneInspector:inputIndex` context variable. By using columns
			# with different values for this context variable we can show
			# side-by-side A/B comparisons of the two scenes in a single
			# PathListingWidget.

			self["__switchedIn"] = GafferScene.ScenePlug()

			self["__switchIndexQuery"] = Gaffer.ContextQuery()
			self["__switchIndexQuery"].addQuery( Gaffer.IntPlug(), "__sceneInspector:inputIndex" )

			self["__deleteContextVariablesA"] = Gaffer.DeleteContextVariables()
			self["__deleteContextVariablesA"].setup( self["in"] )
			self["__deleteContextVariablesA"]["in"].setInput( self["in"] )
			self["__deleteContextVariablesA"]["variables"].setValue( "__sceneInspector:inputIndex" )

			self["__deleteContextVariablesB"] = Gaffer.DeleteContextVariables()
			self["__deleteContextVariablesB"].setup( self["compare"]["scene"]["value"] )
			self["__deleteContextVariablesB"]["in"].setInput( self["compare"]["scene"]["value"] )
			self["__deleteContextVariablesB"]["variables"].setValue( "__sceneInspector:inputIndex" )

			self["__switch"] = Gaffer.Switch()
			self["__switch"].setup( self["in"] )
			self["__switch"]["in"][0].setInput( self["__deleteContextVariablesA"]["out"] )
			self["__switch"]["in"][1].setInput( self["__deleteContextVariablesB"]["out"] )
			self["__switch"]["index"].setInput( self["__switchIndexQuery"]["out"][0]["value"] )
			self["__switch"]["enabled"].setInput( self["compare"]["scene"]["enabled"] )
			self["__switchedIn"].setInput( self["__switch"]["out"] )

			# The `__bScene` always outputs the scene for the B side of the comparison,
			# which we use in widgets for picking locations and render passes to use in
			# the B column.

			self["__bScene"] = Gaffer.ContextVariables()
			self["__bScene"].setup( self["__switch"]["out"] )
			self["__bScene"]["in"].setInput( self["__switch"]["out"] )
			self["__bScene"]["variables"].addChild( Gaffer.NameValuePlug( "__sceneInspector:inputIndex", 1 ) )

	IECore.registerRunTimeTyped( Settings, typeName = "GafferSceneUI::SceneInspector::Settings" )

	def __init__( self, scriptNode, **kw ) :

		mainColumn = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, borderWidth = 4, spacing = 4 )

		GafferSceneUI.SceneEditor.__init__( self, mainColumn, scriptNode, **kw )

		self.settings()["compare"]["scene"]["value"].setInput( self.settings()["in"] )

		self.__standardColumns = [
			GafferUI.StandardPathColumn( "Name", "name" ),
			GafferSceneUI.Private.InspectorColumn( "inspector:inspector", headerData = GafferUI.PathColumn.CellData( value = "Value" ) ),
		]

		self.__diffColumns = [
			GafferUI.StandardPathColumn( "Name", "name" ),
			_GafferSceneUI._SceneInspector.InspectorDiffColumn( _GafferSceneUI._SceneInspector.InspectorDiffColumn.DiffContext.A ),
			_GafferSceneUI._SceneInspector.InspectorDiffColumn( _GafferSceneUI._SceneInspector.InspectorDiffColumn.DiffContext.B ),
		]

		with mainColumn :

			GafferUI.PlugLayout(
				self.settings(),
				orientation = GafferUI.ListContainer.Orientation.Horizontal,
				rootSection = "TopRow",
			)

			GafferUI.PlugLayout(
				self.settings(),
				orientation = GafferUI.ListContainer.Orientation.Horizontal,
				rootSection = "CompareRow",
			)

			with GafferUI.TabbedContainer() :

				with GafferUI.ListContainer( spacing = 4, borderWidth = 4, parenting = { "label" : "Location" } ) :

					self.__locationPathListing = GafferUI.PathListingWidget(
						_GafferSceneUI._SceneInspector.InspectorPath(
							_GafferSceneUI._SceneInspector.InspectorTree(
								self.settings()["__switchedIn"],
								self.__selectionContexts(),
								self.settings()["editScope"]
							),
							"/Location"
						),
						columns = self.__standardColumns,
						selectionMode = GafferUI.PathListingWidget.SelectionMode.Cells,
						displayMode = GafferUI.PathListingWidget.DisplayMode.Tree,
						sortable = False,
					)

				with GafferUI.ListContainer( spacing = 4, borderWidth = 4, parenting = { "label" : "Globals" } ) :

					self.__globalsPathListing = GafferUI.PathListingWidget(
						_GafferSceneUI._SceneInspector.InspectorPath(
							_GafferSceneUI._SceneInspector.InspectorTree(
								self.settings()["__switchedIn"],
								self.__globalsContexts(),
								self.settings()["editScope"],
							),
							"/Globals"
						),
						columns = self.__standardColumns,
						selectionMode = GafferUI.PathListingWidget.SelectionMode.Cells,
						displayMode = GafferUI.PathListingWidget.DisplayMode.Tree,
						sortable = False,
					)

		GafferSceneUI.ScriptNodeAlgo.selectedPathsChangedSignal( scriptNode ).connect(
			Gaffer.WeakMethod( self.__selectedPathsChanged )
		)

		self._updateFromSet()

	def __repr__( self ) :

		return "GafferSceneUI.SceneInspector( scriptNode )"

	def _updateFromContext( self, modifiedItems ) :

		self.__lazyUpdateFromContexts()

	def _updateFromSettings( self, plug ) :

		if plug.getName() == "enabled" and self.settings()["compare"].isAncestorOf( plug ) :
			comparing = any( p["enabled"].getValue() for p in self.settings()["compare"] )
			columns = self.__diffColumns if comparing else self.__standardColumns
			self.__locationPathListing.setColumns( columns )
			self.__globalsPathListing.setColumns( columns )

		if plug in (
			self.settings()["location"],
			self.settings()["compare"]["location"],
			self.settings()["compare"]["renderPass"],
		) :
			self.__lazyUpdateFromContexts()

	@GafferUI.LazyMethod( deferUntilPlaybackStops = True )
	def __lazyUpdateFromContexts( self ) :

		self.__locationPathListing.getPath().tree().setContexts( self.__selectionContexts() )
		self.__globalsPathListing.getPath().tree().setContexts( self.__globalsContexts() )

	def __selectedPathsChanged( self, scriptNode ) :

		self.__locationPathListing.getPath().tree().setContexts( self.__selectionContexts() )

	def __globalsContexts( self ) :

		result = []
		for inputIndex in range( 0, 2 ) :
			context = Gaffer.Context( self.context() )
			context["__sceneInspector:inputIndex"] = inputIndex
			result.append( context )

		if self.settings()["compare"]["renderPass"]["enabled"].getValue() :
			renderPass = self.settings()["compare"]["renderPass"]["value"].getValue()
			if renderPass :
				result[1]["renderPass"] = renderPass
			else :
				del result[1]["renderPass"]

		return result

	def __selectionContexts( self ) :

		result = self.__globalsContexts()

		selectedPath = GafferSceneUI.ScriptNodeAlgo.getLastSelectedPath( self.scriptNode() )
		path = self.settings()["location"].getValue() or selectedPath
		if path :
			result[0]["scene:path"] = GafferScene.ScenePlug.stringToPath( path )

		if self.settings()["compare"]["location"]["enabled"].getValue() :
			path = self.settings()["compare"]["location"]["value"].getValue() or selectedPath

		if path :
			result[1]["scene:path"] = GafferScene.ScenePlug.stringToPath( path )

		return result

GafferUI.Editor.registerType( "SceneInspector", SceneInspector )

# InspectorTree isn't public API. Expose the `registerInspectors()` function on SceneInspector
# itself to make it available to extension authors.
SceneInspector.registerInspectors = _GafferSceneUI._SceneInspector.InspectorTree.registerInspectors

##########################################################################
# Settings metadata
##########################################################################

Gaffer.Metadata.registerNode(

	SceneInspector.Settings,

	"layout:customWidget:compareMenuButton:widgetType", "GafferSceneUI.SceneInspector._CompareMenuButton",
	"layout:customWidget:compareMenuButton:section", "TopRow",
	"layout:customWidget:compareMenuButton:index", 0,

	# Occupies the space left by the `location` plug when we hide it.
	"layout:customWidget:spacer:widgetType", "GafferSceneUI.RenderPassEditor._Spacer",
	"layout:customWidget:spacer:section", "TopRow",
	"layout:customWidget:spacer:index", 1,

	"layout:activator:anyComparisonEnabled", lambda node : any( node["compare"][p]["enabled"].getValue() for p in { "location", "scene", "renderPass" } ),

	plugs = {

		"location" : [

			"description",
			"""
			The scene location to inspect. Defaults to the currently selected location. Use
			the HierarchyView or Viewer to select a location.
			""",

			"plugValueWidget:type", "GafferSceneUI.SceneInspector._LocationPlugValueWidget",
			"layout:section", "TopRow",
			"layout:visibilityActivator", lambda plug : not plug.parent()["compare"]["location"]["enabled"].getValue(),

		],

		"compare" : [

			"plugValueWidget:type", "GafferSceneUI.SceneInspector._ComparePlugValueWidget",
			"layout:visibilityActivator", "anyComparisonEnabled",
			"layout:section", "CompareRow",

		],

		"compare.location.value" : [

			"scenePathPlugValueWidget:scene", "__bScene.out",

		],

		"compare.renderPass.value" : [

			"renderPassPlugValueWidget:scene", "__bScene.out",

		],

		"editScope" : [

			"plugValueWidget:type", "GafferUI.EditScopeUI.EditScopePlugValueWidget",
			"layout:section", "TopRow",
			"layout:width", 130,
			"layout:index", -1,

		],

	}

)

class _CompareMenuButton( GafferUI.PlugValueWidget ) :

	def __init__( self, node, **kw ) :

		self.__button = GafferUI.MenuButton( image = "sceneInspectorCompareOff.png", hasFrame = False )
		GafferUI.PlugValueWidget.__init__( self, self.__button, node["compare"], **kw )

		self.__button.setMenu(
			GafferUI.Menu( title = "Compare", definition = Gaffer.WeakMethod( self.__menuDefinition ) )
		)

		self.setToolTip( "Click to configure A/B comparisons." )

	@staticmethod
	def _valuesForUpdate( plugs, auxiliaryPlugs ) :

		return [
			p["location"]["enabled"].getValue() or p["scene"]["enabled"].getValue() or p["renderPass"]["enabled"].getValue()
			for p in plugs
		]

	def _updateFromValues( self, values, exception ) :

		self.__button.setImage(
			"sceneInspectorCompare{}.png".format( "On" if all( values ) else "Off" )
		)

	@staticmethod
	def __setPlugValues( plugs, *unused, value ) :

		with Gaffer.DirtyPropagationScope() :
			for plug in plugs :
				plug.setValue( value )

	def __menuDefinition( self ) :

		result = IECore.MenuDefinition()

		labels = {
			"location" : "Locations",
			"scene" : "Scenes",
			"renderPass" : "Render Passes",
		}

		enabledValues = []
		for plug in self.getPlug().children() :

			enabled = plug["enabled"].getValue()
			result.append(
				"/{}".format( labels[plug.getName()] ),
				{
					"command" : functools.partial( self.__setPlugValues, [ plug["enabled"] ], value = not enabled ),
					"checkBox" : enabled,
				}
			)

			enabledValues.append( enabled )

		allPlugs = [ p["enabled"] for p in self.getPlug().children() ]
		result.append(
			"/Divider", { "divider" : True }
		)

		result.append(
			"/All",
			{
				"command" : functools.partial( self.__setPlugValues, allPlugs, value = True ),
				"checkBox" : all( enabledValues ),
			}
		)

		result.append(
			"/None",
			{
				"command" : functools.partial( self.__setPlugValues, allPlugs, value = False ),
				"checkBox" : not any( enabledValues ),
			}
		)

		return result

SceneInspector._CompareMenuButton = _CompareMenuButton

# Chooses locations to inspect. Knows that if no location is specified,
# we will fallback to the selection, and shows placeholder text to
# notify the user about that.
class _LocationPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		self.__row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 )

		GafferUI.PlugValueWidget.__init__( self, self.__row, plug, **kw )

		with self.__row :
			self.__pathPlugValueWidget = GafferSceneUI.ScenePathPlugValueWidget( plug )
			self.__pinningButton = GafferUI.Button( image = "locationPinnedOff.png", hasFrame = False, highlightOnOver = True )
			self.__pinningButton.clickedSignal().connect( Gaffer.WeakMethod( self.__pinningButtonClicked ) )

		GafferSceneUI.ScriptNodeAlgo.selectedPathsChangedSignal( self.scriptNode() ).connect(
			Gaffer.WeakMethod( self.__selectedPathsChanged )
		)

		self.__pinned = False
		self.__updatePlaceholderText()

	def hasLabel( self ) :

		return True

	def _updateFromValues( self, values, exception ) :

		self.__pinned = bool( sole( values ) )
		self.__updatePinningButton()

	def __pinningButtonClicked( self, button ) :

		newValue = "" if self.__pinned else GafferSceneUI.ScriptNodeAlgo.getLastSelectedPath( self.scriptNode() )
		with Gaffer.DirtyPropagationScope() :
			for plug in self.getPlugs() :
				plug.setValue( newValue )

	def __selectedPathsChanged( self, scriptNode ) :

		self.__updatePinningButton()
		self.__updatePlaceholderText()

	def __updatePinningButton( self ) :

		self.__pinningButton.setImage( "locationPinned{}.png".format( "On" if self.__pinned else "Off" ) )
		lastSelectedPath = GafferSceneUI.ScriptNodeAlgo.getLastSelectedPath( self.scriptNode() )
		self.__pinningButton.setEnabled( self.__pinned or bool( lastSelectedPath ) )
		self.__pinningButton.setToolTip(
			"Click to unpin" if self.__pinned else f"Click to pin `{lastSelectedPath}`"
		)

	def __updatePlaceholderText( self ) :

		selectedPath = GafferSceneUI.ScriptNodeAlgo.getLastSelectedPath( self.scriptNode() )
		self.__pathPlugValueWidget.pathWidget().setPlaceholderText(
			selectedPath or "Select a location to inspect"
		)

SceneInspector._LocationPlugValueWidget = _LocationPlugValueWidget

# Manages the input connection for `compare.scene`, using the same "Pin" and
# "Follow" concepts as we use for NodeSetEditors. Has huge similarity to
# CompoundEditor's `_PinningWidget` and ImageViewUI's `_CompareImageWidget`,
# with lots of duplication of code.
## \todo Figure out how we can unify the three. It seems like it might make
# sense to do this when we tackle the problem of making the full UI state
# serialisable - since Sets are not serialisable, all three will have a
# common problem to solve.
class _FocusPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		frame = GafferUI.Frame( borderWidth = 0, borderStyle = GafferUI.Frame.BorderStyle.None_ )
		GafferUI.PlugValueWidget.__init__( self, frame, plug, **kw )

		with frame :

			with GafferUI.ListContainer( orientation = GafferUI.ListContainer.Orientation.Horizontal ) :

				self.__bookmarkNumber = GafferUI.Label( horizontalAlignment=GafferUI.Label.HorizontalAlignment.Right )
				self.__bookmarkNumber.buttonPressSignal().connect( Gaffer.WeakMethod( self.__showFocusMenu ) )

				self.__icon = GafferUI.Button( hasFrame=False, highlightOnOver=False )
				self.__icon._qtWidget().setFixedHeight( 13 )
				self.__icon._qtWidget().setFixedWidth( 13 )
				self.__icon.buttonPressSignal().connect( Gaffer.WeakMethod( self.__showFocusMenu ) )

				menuButton = GafferUI.Button( image="menuIndicator.png", hasFrame=False, highlightOnOver=False )
				menuButton._qtWidget().setObjectName( "menuDownArrow" )
				menuButton.buttonPressSignal().connect( Gaffer.WeakMethod( self.__showFocusMenu ) )

		self.__nodeSetChangedSignal = GafferUI.WidgetSignal()

		self.buttonPressSignal().connect( Gaffer.WeakMethod( self.__showFocusMenu ) )

		self.setNodeSet( nodeSet = self.scriptNode().selection() )

	def setNodeSet( self, *unused, nodeSet ) :

		self.__nodeSet = nodeSet
		self.__nodeSetConnections = [
			self.__nodeSet.memberAddedSignal().connect( Gaffer.WeakMethod( self.__updateInput ), scoped = True ),
			self.__nodeSet.memberRemovedSignal().connect( Gaffer.WeakMethod( self.__updateInput ), scoped = True ),
		]
		self.__updateInput()

		# Icon

		if self.__nodeSet.isSame( self.scriptNode().selection() ) :
			icon = "nodeSetNodeSelection.png"
		elif self.__nodeSet.isSame( self.scriptNode().focusSet() ) :
			icon = "nodeSetFocusNode.png"
		else :
			icon = "nodeSet{}.png".format( self.__nodeSet.__class__.__name__ )

		self.__icon.setImage( icon )

		# Bookmark indicator

		if isinstance( self.__nodeSet, Gaffer.NumericBookmarkSet ) :
			self.__bookmarkNumber.setText( "{}".format( self.__nodeSet.getBookmark() ) )
		else :
			self.__bookmarkNumber.setText( "" )

		# Signalling

		self.__nodeSetChangedSignal( self )

	def getNodeSet( self ) :

		return self.__nodeSet

	def nodeSetChangedSignal( self ) :

		return self.__nodeSetChangedSignal

	def __updateInput( self, *unused ) :

		input = None
		if len( self.__nodeSet ) :
			input = next(
				( p for p in self.getPlug().RecursiveOutputRange( self.__nodeSet[-1] ) if not p.getName().startswith( "__" ) ),
				None
			)

		self.getPlug().setInput( input )

	def __followBookmark( self, *unused, bookmark ) :

		self.setNodeSet( nodeSet = Gaffer.NumericBookmarkSet( self.scriptNode(), bookmark ) )

	def __showFocusMenu( self, *unused ) :

		menuDefinition = IECore.MenuDefinition()

		# Add pinning items

		selection = self.scriptNode().selection()
		if len( selection ) == 0 :
			selectionLabel = "Pin To Nothing"
		else :
			selectionLabel = "Pin {}".format( selection[0].getName() )

		menuDefinition.append( "/Pin", {
			"command" : functools.partial( Gaffer.WeakMethod( self.setNodeSet ), nodeSet = Gaffer.StandardSet( selection[:] ) ) ,
				"label" : selectionLabel,
			} )

		# Add following items

		menuDefinition.append( "/Follow Divider", { "divider" : True, "label" : "Follow" } )

		menuDefinition.append( "/Focus Node", {
			"command" : functools.partial( Gaffer.WeakMethod( self.setNodeSet ), nodeSet = self.scriptNode().focusSet() ),
			"checkBox" : self.__nodeSet.isSame( self.scriptNode().focusSet() ),
		} )

		menuDefinition.append( "/Node Selection", {
			"command" : functools.partial( Gaffer.WeakMethod( self.setNodeSet ), nodeSet = selection ),
			"checkBox" : self.__nodeSet.isSame( selection ),
		} )

		# Add bookmarks

		menuDefinition.append( "/NumericBookmarkDivider", { "divider" : True, "label" : "Follow Numeric Bookmark" } )

		for bookmark in range( 1, 10 ) :
			title = f"{bookmark}"
			bookmarkNode = Gaffer.MetadataAlgo.getNumericBookmark( self.scriptNode(), bookmark )
			if bookmarkNode is not None :
				title += " : {}".format( bookmarkNode.getName() )
			menuDefinition.append(
				f"/NumericBookMark{bookmark}",
				{
					"command" : functools.partial( Gaffer.WeakMethod( self.__followBookmark ), bookmark = bookmark ),
					"checkBox" : isinstance( self.__nodeSet, Gaffer.NumericBookmarkSet ) and self.__nodeSet.getBookmark() == bookmark,
					"label" : title,
				}
			)

		# Show menu

		self.__menu = GafferUI.Menu( menuDefinition, title = "Focus" )

		bound = self.bound()
		self.__menu.popup(
			parent = self.ancestor( GafferUI.Window ),
			position = imath.V2i( bound.min().x, bound.max().y )
		)

# Manages a NameLabel showing the input scene, by following the node set
# of either the SceneInspector (A input) or _FocusPlugValueWidget (B input).
class _InputLabelWidget( GafferUI.Widget ) :

	def __init__( self, **kw ) :

		self.__nameLabel = GafferUI.NameLabel( None )
		self.__nameLabel._qtWidget().setFixedHeight( 20 )
		self.__nameLabel._qtWidget().setSizePolicy( QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed )
		GafferUI.Widget.__init__( self, self.__nameLabel, **kw )

	def connectToNodeSetWidget( self, nodeSetWidget ) :

		self.__scriptNode = nodeSetWidget.scriptNode()
		self.__nodeSetChangedConnection = nodeSetWidget.nodeSetChangedSignal().connect(
			Gaffer.WeakMethod( self.__nodeSetChanged ), scoped = True
		)
		self.__nodeSetChanged( nodeSetWidget )
		self.__updateLabel( nodeSetWidget.getNodeSet() )

	def __nodeSetChanged( self, nodeSetWidget ) :

		nodeSet = nodeSetWidget.getNodeSet()
		self.__memberConnections = [
			nodeSet.memberAddedSignal().connect( Gaffer.WeakMethod( self.__nodeSetMembersChanged ), scoped = True ),
			nodeSet.memberRemovedSignal().connect( Gaffer.WeakMethod( self.__nodeSetMembersChanged ), scoped = True ),
		]

		self.__updateLabel( nodeSet )

	def __nodeSetMembersChanged( self, nodeSet, *unused ) :

		self.__updateLabel( nodeSet )

	def __updateLabel( self, nodeSet ) :

		if len( nodeSet ) :
			self.__nameLabel.setGraphComponent( nodeSet[-1] )
		else :
			self.__nameLabel.setGraphComponent( None )
			if nodeSet.isSame( self.__scriptNode.selection() ) :
				text = "Select a node to inspect"
			elif nodeSet.isSame( self.__scriptNode.focusSet() ) :
				text = "Focus a node to inspect"
			elif isinstance( nodeSet, Gaffer.NumericBookmarkSet ) :
				text = "Bookmark a node to inspect"
			else :
				text = ""

			## \todo We should use _StyleSheet.py to match this colour to the
			# placeholder text colour used by QLineEdit etc. But Qt (at least Qt 5)
			# doesn't let us define placeholder text colour in the stylesheet, so
			# here we're just matching it manually.
			self.__nameLabel.setText(
				f"<html><header><style type=text/css> * {{ color:rgb( 156, 156, 156 ) }}></style></head><body>{text}</body></html>"
			)

# Widget for choosing the B scene for comparison.
class _CompareScenePlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 )
		GafferUI.PlugValueWidget.__init__( self, row, plug, **kw )

		with row :
			labelWidget = _InputLabelWidget()
			focusWidget = _FocusPlugValueWidget( plug )
			labelWidget.connectToNodeSetWidget( focusWidget )

# Simple widget that just displays the `renderPass` variable from
# the current context.
class _CurrentRenderPassWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		self.__label = GafferUI.Label()
		GafferUI.PlugValueWidget.__init__( self, self.__label, plug, **kw )

		# Match the size policy of the _RenderPassPlugValueWidget, so they
		# share space equally.
		self.__label._qtWidget().setSizePolicy( QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed )
		self.__label._qtWidget().setFixedHeight( 20 )

	@staticmethod
	def _valuesForUpdate( plugs, auxiliaryPlugs ) :

		return Gaffer.Context.current().get( "renderPass" ) or "None"

	def _updateFromValues( self, value, exception ) :

		self.__label.setText( value )

	def _valuesDependOnContext( self ) :

		return True

# Uber widget that shows all the options for setting up A/B comparisons.
class _ComparePlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal )

		GafferUI.PlugValueWidget.__init__( self, row, plug )

		def createLabel( text, index ) :

			label = GafferUI.Label( text, horizontalAlignment = GafferUI.HorizontalAlignment.Right, parenting = { "index" : index } )
			label._qtWidget().setFixedWidth( 65 ) # So layout doesn't jump when hiding wider labels.
			label._qtWidget().setFixedHeight( 20 ) # To get consistent row heights, regardless of value widget height.
			return label

		with row :

			with GafferUI.Frame( borderStyle = GafferUI.Frame.BorderStyle.None_, borderWidth = 4 ) as aFrame :

				with GafferUI.GridContainer( spacing = 4 ) as self.__aGrid :

					createLabel( "Location", ( 0, 0 ) )
					_LocationPlugValueWidget( plug.parent()["location"], parenting = { "index" : ( 1, 0 ) } )

					createLabel( "Node", ( 0, 1 ) )
					self.__inputLabelWidget = _InputLabelWidget( parenting = { "index" : ( 1, 1 ) } )

					createLabel( "Render Pass", ( 0, 2 ) )
					_CurrentRenderPassWidget( plug["renderPass"]["value"], parenting = { "index" : ( 1, 2 ) } )

				aFrame._qtWidget().setProperty( "gafferDiff", "A" )

			with GafferUI.Frame( borderStyle = GafferUI.Frame.BorderStyle.None_, borderWidth = 4 ) as bFrame :

				with GafferUI.GridContainer( spacing = 4 ) as self.__bGrid :

					createLabel( "Location", ( 0, 0 ) )
					_LocationPlugValueWidget( plug["location"]["value"], parenting = { "index" : ( 1, 0 ) } )

					createLabel( "Node", ( 0, 1 ) )
					_CompareScenePlugValueWidget( plug["scene"]["value"], parenting = { "index" : ( 1, 1 ) } )

					createLabel( "Render Pass", ( 0, 2 ) )
					GafferSceneUI.RenderPassEditor._RenderPassPlugValueWidget( plug["renderPass"]["value"], parenting = { "index" : ( 1, 2 ) } )

				bFrame._qtWidget().setProperty( "gafferDiff", "B" )

		GafferUI.WidgetAlgo.joinEdges( row )

		self.parentChangedSignal().connect( Gaffer.WeakMethod( self.__parentChanged ) )

	def hasLabel( self ) :

		return True

	@staticmethod
	def _valuesForUpdate( plugs, auxiliaryPlugs ) :

		assert( len( plugs ) == 1 )
		return [ p["enabled"].getValue() for p in next( iter( plugs ) ).children() ]

	def _updateFromValues( self, values, exception ) :

		for y, enabled in enumerate( values ) :
			for grid in ( self.__aGrid, self.__bGrid ) :
				for x in range( 0, 2 ) :
					grid[x,y].setVisible( enabled )

	def __parentChanged( self, unused ) :

		# We can't get access to the parent SceneInspector until we get parented,
		# so we have to connect our input label to follow the node set in this
		# awkward delayed fashion.
		self.__inputLabelWidget.connectToNodeSetWidget( self.ancestor( GafferUI.NodeSetEditor ) )

SceneInspector._ComparePlugValueWidget = _ComparePlugValueWidget
