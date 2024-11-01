##########################################################################
#
#  Copyright (c) 2019, Cinesite VFX Ltd. All rights reserved.
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
from collections import deque
from collections import OrderedDict

import imath

import IECore

import Gaffer
import GafferUI

from GafferUI._StyleSheet import _styleColors
from Qt import QtGui
from Qt import QtWidgets

Gaffer.Metadata.registerNode(

	Gaffer.EditScope,

	"description",
	"""
	A container that interactive tools may make nodes in
	as necessary.
	""",

	"icon", "editScopeNode.png",

	"graphEditor:childrenViewable", True,

	# Add + buttons for setting up via the GraphEditor

	"noduleLayout:customGadget:setupButtonTop:gadgetType", "GafferUI.EditScopeUI.PlugAdder",
	"noduleLayout:customGadget:setupButtonTop:section", "top",

	"noduleLayout:customGadget:setupButtonBottom:gadgetType", "GafferUI.EditScopeUI.PlugAdder",
	"noduleLayout:customGadget:setupButtonBottom:section", "bottom",

	# Hide the Box + buttons until the node has been set up. Two sets of buttons at
	# the same time is way too confusing.

	"noduleLayout:customGadget:addButtonTop:visible", lambda node : "in" in node,
	"noduleLayout:customGadget:addButtonBottom:visible", lambda node : "in" in node,
	"noduleLayout:customGadget:addButtonLeft:visible", lambda node : "in" in node,
	"noduleLayout:customGadget:addButtonRight:visible", lambda node : "in" in node,

	# Add a custom widget for showing a summary of the processors within.

	"layout:customWidget:processors:widgetType", "GafferUI.EditScopeUI.__ProcessorsWidget",
	"layout:customWidget:processors:section", "Edits",

	plugs = {

		"in" : [

			"renameable", False,
			"deletable", False,

		],

		"out" : [

			"renameable", False,
			"deletable", False,

		],

	},

)

# Disable editing of `EditScope.BoxIn` and `EditScope.BoxOut`

Gaffer.Metadata.registerValue( Gaffer.EditScope, "BoxIn.name", "readOnly", True )
Gaffer.Metadata.registerValue( Gaffer.EditScope, "BoxIn.name", "layout:visibilityActivator", False )
Gaffer.Metadata.registerValue( Gaffer.EditScope, "BoxOut.name", "readOnly", True )
Gaffer.Metadata.registerValue( Gaffer.EditScope, "BoxOut.name", "layout:visibilityActivator", False )
Gaffer.Metadata.registerValue( Gaffer.BoxIn, "renameable", lambda node : not isinstance( node.parent(), Gaffer.EditScope ) or node.getName() != "BoxIn" )
Gaffer.Metadata.registerValue( Gaffer.BoxOut, "renameable", lambda node : not isinstance( node.parent(), Gaffer.EditScope ) or node.getName() != "BoxOut" )

# EditScopePlugValueWidget
# ========================

class EditScopePlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		self.__frame = GafferUI.Frame( borderWidth = 0 )
		GafferUI.PlugValueWidget.__init__( self, self.__frame, plug, **kw )

		with self.__frame :
			with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :
				GafferUI.Spacer( imath.V2i( 4, 1 ), imath.V2i( 4, 1 ) )
				GafferUI.Label( "Edit Scope" )
				self.__busyWidget = GafferUI.BusyWidget( size = 18 )
				self.__busyWidget.setVisible( False )
				self.__menuButton = GafferUI.MenuButton(
					"",
					menu = GafferUI.Menu( Gaffer.WeakMethod( self.__menuDefinition ) ),
					highlightOnOver = False
				)
				# Ignore the width in X so MenuButton width is limited by the overall width of the widget
				self.__menuButton._qtWidget().setSizePolicy( QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Fixed )
				GafferUI.Spacer( imath.V2i( 4, 1 ), imath.V2i( 4, 1 ) )

		self.buttonPressSignal().connect( Gaffer.WeakMethod( self.__buttonPress ) )
		self.dragBeginSignal().connect( Gaffer.WeakMethod( self.__dragBegin ) )
		self.dragEndSignal().connect( Gaffer.WeakMethod( self.__dragEnd ) )
		self.dragEnterSignal().connect( Gaffer.WeakMethod( self.__dragEnter ) )
		self.dragLeaveSignal().connect( Gaffer.WeakMethod( self.__dragLeave ) )
		# We connect to the front, and unconditionally return True to ensure that we never
		# run the default dropSignal handler from PlugValueWidget.
		self.dropSignal().connectFront( Gaffer.WeakMethod( self.__drop ) )

		self.__updatePlugInputChangedConnection()
		self.__acquireContextTracker()

	def hasLabel( self ) :

		return True

	def setPlugs( self, plugs ) :

		GafferUI.PlugValueWidget.setPlugs( self, plugs )
		self.__updatePlugInputChangedConnection()
		self.__acquireContextTracker()

	def getToolTip( self ) :

		editScope = self.__editScope()
		if editScope is None :
			return "Edits will be made using the last relevant node found outside of an edit scope.\n\nTo make an edit in an edit scope, choose it from the menu."

		unusableReason = self.__unusableReason( editScope )
		if unusableReason :
			return unusableReason
		else :
			return "Edits will be made in {}.".format( editScope.getName() )

	# We don't actually display values, but this is also called whenever the
	# input changes, which is when we need to update.
	def _updateFromValues( self, values, exception ) :

		editScope = self.__editScope()
		editScopeActive = editScope is not None
		self.__updateMenuButton()
		if editScopeActive :
			self.__editScopeNameChangedConnection = editScope.nameChangedSignal().connect(
				Gaffer.WeakMethod( self.__editScopeNameChanged ), scoped = True
			)
			self.__editScopeMetadataChangedConnection = Gaffer.Metadata.nodeValueChangedSignal( editScope ).connect(
				Gaffer.WeakMethod( self.__editScopeMetadataChanged ), scoped = True
			)
		else :
			self.__editScopeNameChangedConnection = None
			self.__editScopeMetadataChangedConnection = None

		if self._qtWidget().property( "editScopeActive" ) != editScopeActive :
			self._qtWidget().setProperty( "editScopeActive", GafferUI._Variant.toVariant( editScopeActive ) )
			self._repolish()

	def __updatePlugInputChangedConnection( self ) :

		self.__plugInputChangedConnection = self.getPlug().node().plugInputChangedSignal().connect(
			Gaffer.WeakMethod( self.__plugInputChanged ), scoped = True
		)

	def __plugInputChanged( self, plug ) :

		if plug.getName() == "in" and plug.parent() == self.getPlug().node() :
			# The result of `__inputNode()` will have changed.
			self.__acquireContextTracker()

	def __acquireContextTracker( self ) :

		self.__contextTracker = GafferUI.ContextTracker.acquire( self.__inputNode() )
		self.__contextTrackerChangedConnection = self.__contextTracker.changedSignal().connect(
			Gaffer.WeakMethod( self.__contextTrackerChanged ), scoped = True
		)

		if not self.__contextTracker.updatePending() :
			self.__updateMenuButton()
		else :
			# We'll update later in `__contextTrackerChanged()`.
			pass

	def __updateMenuButton( self ) :

		editScope = self.__editScope()
		self.__menuButton.setText( editScope.getName() if editScope is not None else "None" )

		if editScope is not None :
			self.__menuButton.setImage(
				self.__editScopeSwatch( editScope ) if not self.__unusableReason( editScope ) else "warningSmall.png"
			)
		else :
			self.__menuButton.setImage( None )

	def __editScopeNameChanged( self, editScope, oldName ) :

		self.__updateMenuButton()

	def __editScopeMetadataChanged( self, editScope, key, reason ) :

		if key == "nodeGadget:color" :
			self.__updateMenuButton()

	def __contextTrackerChanged( self, contextTracker ) :

		self.__updateMenuButton()
		self.__busyWidget.setVisible( False )

	def __editScope( self ) :

		input = self.getPlug().getInput()
		return input.ancestor( Gaffer.EditScope ) if input is not None else None

	def __editScopePredicate( self, node ) :

		if not isinstance( node, Gaffer.EditScope ) :
			return False

		if "out" not in node or not self.getPlug().acceptsInput( node["out"] ) :
			return False

		return True

	def __connectEditScope( self, editScope, *ignored ) :

		self.getPlug().setInput( editScope["out"] )

	def __inputNode( self ) :

		node = self.getPlug().node()
		# We assume that our plug is on a node dedicated to holding settings for the
		# UI, and that it has an `in` plug that is connected to the node in the graph
		# that is being viewed. We start our node graph traversal at the viewed node
		# (we can't start at _this_ node, as then we will visit our own input connection
		# which may no longer be upstream of the viewed node).
		if node["in"].getInput() is None :
			return None

		inputNode = node["in"].getInput().node()
		if not isinstance( inputNode, Gaffer.EditScope ) and isinstance( inputNode, Gaffer.SubGraph ) :
			# If we're starting from a SubGraph then attempt to begin the search from the
			# first input of the node's output so we can find any Edit Scopes within.
			output = node["in"].getInput().getInput()
			if output is not None and inputNode.isAncestorOf( output ) :
				return output.node()

		return inputNode

	def __activeEditScopes( self ) :

		node = self.__inputNode()
		if node is None :
			return []

		result = Gaffer.NodeAlgo.findAllUpstream( node, self.__editScopePredicate )
		if self.__editScopePredicate( node ) :
			result.insert( 0, node )

		result = [ n for n in result if self.__contextTracker.isTracked( n ) ]

		return result

	def __buildMenu( self, path, currentEditScope ) :

		result = IECore.MenuDefinition()

		for childPath in path.children() :
			itemName = childPath[-1]

			if childPath.isLeaf() :
				editScope = childPath.property( "dict:value" )
			else :
				singlesStack = deque( [ childPath ] )
				while singlesStack :
					childPath = singlesStack.popleft()
					children = childPath.children()
					if len( children ) == 1 :
						itemName += "." + children[0][-1]
						if children[0].isLeaf() :
							childPath = children[0]
							editScope = children[0].property( "dict:value" )
						else :
							singlesStack.extend( [ children[0] ] )

			if currentEditScope is not None :
				node = currentEditScope.scriptNode().descendant( ".".join( childPath[:] ) )
				icon = "menuBreadCrumb.png" if node.isAncestorOf( currentEditScope ) else None
			else :
				icon = None

			if childPath.isLeaf() :
				result.append(
					itemName,
					{
						"command" : functools.partial( Gaffer.WeakMethod( self.__connectEditScope ), editScope ),
						"label" : itemName,
						"checkBox" : editScope == currentEditScope,
						"icon" : self.__editScopeSwatch( editScope ),
						"active" : not self.__unusableReason( editScope ),
						"description" : self.__unusableReason( editScope ),
					}
				)
			else :
				result.append(
					itemName,
					{
						"subMenu" : functools.partial( Gaffer.WeakMethod( self.__buildMenu ), childPath, currentEditScope ),
						"icon" : icon
					}
				)

		return result

	def __menuDefinition( self ) :

		currentEditScope = None
		if self.getPlug().getInput() is not None :
			currentEditScope = self.getPlug().getInput().parent()

		activeEditScopes = self.__activeEditScopes()

		# Build a menu hierarchy to match the node hierarchy.
		# This will be simplified where possible in `__buildMenu()`.

		menuHierarchy = OrderedDict()
		for editScope in reversed( activeEditScopes ) :

			ancestorNodes = []
			currentNode = editScope
			while currentNode.parent() != editScope.scriptNode() :
				currentNode = currentNode.parent()
				ancestorNodes.append( currentNode )

			ancestorNodes.reverse()

			currentMenu = menuHierarchy
			for n in ancestorNodes :
				currentMenu = currentMenu.setdefault( n.getName(), {} )
			currentMenu[editScope.getName()] = editScope

		result = self.__buildMenu( Gaffer.DictPath( menuHierarchy, "/" ), currentEditScope )

		if self.__contextTracker.updatePending() :
			result.append( "/__RefreshDivider__", { "divider" : True } )
			result.append( "/Refresh", { "command" : Gaffer.WeakMethod( self.__refreshMenu ) } )

		result.append( "/__NoneDivider__", { "divider" : True } )
		result.append(
			"/None", { "command" : functools.partial( self.getPlug().setInput, None ) },
		)

		if currentEditScope is not None :
			result.append( "/__ActionsDivider__", { "divider" : True, "label" : "Actions" } )
			nodes = currentEditScope.processors()
			nodes.extend( self.__userNodes( currentEditScope ) )

			if nodes :
				for node in nodes :
					path = node.relativeName( currentEditScope ).replace( ".", "/" )
					result.append(
						"/Show Edits/" + path,
						{
							"command" : functools.partial( GafferUI.NodeEditor.acquire, node )
						}
					)
			else :
				result.append(
					"/Show Edits/EditScope is Empty",
					{ "active" : False },
				)

		return result

	def __refreshMenu( self ) :

		if self.__contextTracker.updatePending() :
			# An update will already be in progress so we just show our busy
			# widget until it is done.
			self.__busyWidget.setVisible( True )

	def __editScopeSwatch( self, editScope ) :

		return GafferUI.Image.createSwatch(
			Gaffer.Metadata.value( editScope, "nodeGadget:color" ) or imath.Color3f( 1 )
		)

	@staticmethod
	def __userNodes( editScope ) :

		nodes = Gaffer.Metadata.nodesWithMetadata( editScope, "editScope:includeInNavigationMenu" )
		return [ n for n in nodes if n.ancestor( Gaffer.EditScope ).isSame( editScope ) ]

	def __dropNode( self,  event ) :

		if isinstance( event.data, Gaffer.EditScope ) :
			return event.data
		elif (
			isinstance( event.data, Gaffer.Set ) and event.data.size() == 1 and
			isinstance( event.data[0], Gaffer.EditScope )
		) :
			return event.data[0]
		else:
			return None

	def __buttonPress( self, widget, event ) :

		return event.buttons & ( event.Buttons.Left | event.Buttons.Middle ) and self.__editScope() is not None

	def __dragBegin( self, widget, event ) :

		if not event.buttons & ( event.Buttons.Left | event.Buttons.Middle ) :
			return None

		data = self.__editScope()
		if data is None :
			return None

		GafferUI.Pointer.setCurrent( "nodes" )
		return data

	def __dragEnd( self, widget, event ) :

		GafferUI.Pointer.setCurrent( "" )

		return True

	def __dragEnter( self, widget, event ) :

		if event.sourceWidget is self :
			return False

		if self.__dropNode( event ) :
			self.__frame.setHighlighted( True )

		return True

	def __dragLeave( self, widget, event ) :

		self.__frame.setHighlighted( False )

		return True

	def __drop( self, widget, event ) :

		dropNode = self.__dropNode( event )
		if dropNode is not None :

			reason = self.__unusableReason( dropNode )
			if reason is None :
				self.__connectEditScope( dropNode )
			else :
				with GafferUI.PopupWindow() as self.__popup :
					with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :
						GafferUI.Image( "warningSmall.png" )
						GafferUI.Label( f"<h4>{reason}</h4>" )
				self.__popup.popup( parent = self )

		self.__frame.setHighlighted( False )

		return True

	def __unusableReason( self, editScope ) :

		name = editScope.relativeName( editScope.scriptNode() )
		inputNode = self.__inputNode()
		if inputNode is None :
			return f"{name} cannot be used while nothing is viewed."
		elif not self.__contextTracker.isTracked( editScope ) :
			inputNodeName = inputNode.relativeName( inputNode.scriptNode() )
			return f"{name} cannot be used as it is not upstream of {inputNodeName}."
		elif not self.__contextTracker.isEnabled( editScope ) :
			return f"{name} cannot be used as it is disabled."
		else :
			return None

# ProcessorWidget
# ===============

class ProcessorWidget( GafferUI.Widget ) :

	def __init__( self, topLevelWidget, processor, **kw ) :

		GafferUI.Widget.__init__( self, topLevelWidget, **kw )

		self.__processor = processor

	def processor( self ) :

		return self.__processor

	__widgetTypes = {}
	@staticmethod
	def registerProcessorWidget( processorType, widgetCreator ) :

		ProcessorWidget.__widgetTypes[processorType] = widgetCreator

	@staticmethod
	def create( processor ) :

		processorType = Gaffer.Metadata.value( processor, "editScope:processorType" )
		creator = ProcessorWidget.__widgetTypes.get( processorType )
		if creator is None :
			for name, candidate in ProcessorWidget.__widgetTypes.items() :
				if IECore.StringAlgo.matchMultiple( processorType, name ) :
					creator = candidate
					break

		if creator is not None :
			return creator( processor )

		return None

# SimpleProcessorWidget
# =====================

## Base class for creating simple summaries of Processors, including links
class SimpleProcessorWidget( ProcessorWidget ) :

	def __init__( self, processor, **kw ) :

		self.__column = GafferUI.ListContainer( spacing = 4 )
		ProcessorWidget.__init__( self, self.__column, processor, **kw )

		with self.__column :
			with GafferUI.ListContainer( orientation = GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :
				label = GafferUI.NameLabel( processor )
				label.setFormatter( lambda g : "<h4>{}</h4".format( GafferUI.NameLabel.defaultFormatter( g ) ) )
				GafferUI.Spacer( size = imath.V2i( 1 ) )
				GafferUI.LabelPlugValueWidget( processor["enabled"] )
				GafferUI.BoolPlugValueWidget( processor["enabled"] )
			with GafferUI.ListContainer( orientation = GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :
				_acquireSummaryWidgetClass( self._summary )( processor["out"] )
				textColor = QtGui.QColor( *_styleColors["foregroundInfo"] ).name()
				showLabel = GafferUI.Label( f"<a href=gaffer://show><font color={textColor}>Show</font></a>" )
				showLabel.linkActivatedSignal().connect( Gaffer.WeakMethod( self.__show ) )
			GafferUI.Divider()

	## Called to retrieve the text for the summary label, so must be overridden
	# by derived classes. Use `linkCreator( text, data )` to create an HTML link
	# to include in the summary. When the link is clicked, `_linkActivated( data )`
	# will be called.
	#
	# > Note : This is called on a background thread to avoid locking
	# > the UI, so it is static to avoid the possibility of unsafe
	# > access to UI elements.
	@staticmethod
	def _summary( processor, linkCreator ) :

		raise NotImplementedError

	## Called when a link within the summary is clicked.
	def _linkActivated( self, linkData ) :

		raise NotImplementedError

	def __show( self, *unused ) :

		GafferUI.NodeEditor.acquire( self.processor() )

## Helper class for associating arbitrary data with HTML links.
class _LinkCreator :

	def __init__( self ) :

		self.__linkData = []

	def __call__( self, text, data ) :

		index = len( self.__linkData )
		self.__linkData.append( data )
		textColor = QtGui.QColor( *_styleColors["foregroundInfo"] ).name()

		return f"<a href=gaffer://{index}><font color={textColor}>{text}</font></a>"

	def linkData( self, link ) :

		index = int( link.rpartition( "/" )[2] )
		return self.__linkData[index]

# Factory for PlugValueWidget subclasses for showing the summary. We want to use PlugValueWidget
# for this because it handles all the details of background updates for us. But we need to make
# a unique subclass for each `summaryFunction` because `PlugValueWidget._valuesForUpdate()` is
# static.
__summaryWidgetClasses = {}
def _acquireSummaryWidgetClass( summaryFunction ) :

	global __summaryWidgetClasses
	if summaryFunction in __summaryWidgetClasses :
		return __summaryWidgetClasses[summaryFunction]

	class _SummaryPlugValueWidget( GafferUI.PlugValueWidget ) :

		def __init__( self, plug, **kw ) :

			row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 )
			GafferUI.PlugValueWidget.__init__( self, row, { plug }, **kw )

			with row :
				self.__errorImage = GafferUI.Image( "errorSmall.png" )
				self.__label = GafferUI.Label()
				self.__label.linkActivatedSignal().connect( Gaffer.WeakMethod( self.__linkActivated ) )
				GafferUI.Spacer( size = imath.V2i( 1, 20 ) )
				self.__busyWidget = GafferUI.BusyWidget( size = 20 )

		@staticmethod
		def _valuesForUpdate( plugs, auxiliaryPlugs ) :

			assert( len( plugs ) == 1 )

			links = _LinkCreator()
			summary = summaryFunction( next( iter( plugs ) ).node(), links )

			return [ { "summary" : summary, "links" : links } ]

		def _updateFromValues( self, values, exception ) :

			self.__busyWidget.setVisible( not values and exception is None )

			self.__errorImage.setVisible( exception is not None )
			self.__errorImage.setToolTip( str( exception ) if exception is not None else "" )

			if values :
				self.__label.setText(
					"<font color={textColor}>{summary}</font>".format(
						textColor = QtGui.QColor( *_styleColors["foreground"] ).name(),
						summary = values[0]["summary"] if len( values ) else ""
					)
				)
				self.__links = values[0]["links"]

		def __linkActivated( self, label, link ) :

			self.ancestor( SimpleProcessorWidget )._linkActivated( self.__links.linkData( link ) )

	__summaryWidgetClasses[summaryFunction] = _SummaryPlugValueWidget
	return _SummaryPlugValueWidget

# __ProcessorsWidget
# ==================

class __ProcessorsWidget( GafferUI.Widget ) :

	def __init__( self, editScope, **kw ) :

		self.__column = GafferUI.ListContainer( spacing = 4 )
		GafferUI.Widget.__init__( self, self.__column, **kw )

		self.__editScope = editScope
		self.__processorWidgets = {}

		editScope.childAddedSignal().connect( Gaffer.WeakMethod( self.__editScopeChildAdded ) )
		editScope.childRemovedSignal().connect( Gaffer.WeakMethod( self.__editScopeChildRemoved ) )

		self.__update()

	def __editScopeChildAdded( self, editScope, child ) :

		if Gaffer.Metadata.value( child, "editScope:processorType" ) :
			self.__update()

	def __editScopeChildRemoved( self, editScope, child ) :

		if Gaffer.Metadata.value( child, "editScope:processorType" ) :
			self.__update()

	@GafferUI.LazyMethod()
	def __update( self ) :

		# Get rid of any widgets we don't need

		processors = set( self.__editScope.processors() )
		self.__processorWidgets = {
			p : w for p, w in self.__processorWidgets.items()
			if p in processors
		}

		# Make sure we have a widget for all processors

		for processor in processors :
			if processor in self.__processorWidgets :
				continue
			widget = ProcessorWidget.create( processor )
			self.__processorWidgets[processor] = widget

		# Update the layout

		widgets = [ w for w in self.__processorWidgets.values() if w is not None ]
		widgets = sorted( widgets, key = lambda w : w.processor().getName() )

		if not widgets :
			textColor = QtGui.QColor( *_styleColors["foregroundFaded"] ).name()
			with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) as row :
				GafferUI.Image( "infoSmall.png" )
				GafferUI.Label( f"<font color={textColor}>No edits created yet</font>" )
			widgets.append( row )

		self.__column[:] = widgets
