##########################################################################
#  
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
#  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
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

from __future__ import with_statement

import IECore

import Gaffer
import GafferUI

QtCore = GafferUI._qtImport( "QtCore" )

class NodeGraph( GafferUI.EditorWidget ) :

	def __init__( self, scriptNode, **kw ) :
				
		self.__gadgetWidget = GafferUI.GadgetWidget(
			bufferOptions = set( [
				GafferUI.GLWidget.BufferOptions.Double,
			] ),
		)
		
		GafferUI.EditorWidget.__init__( self, self.__gadgetWidget, scriptNode, **kw )
		
		graphGadget = GafferUI.GraphGadget( self.scriptNode() )
		self.__rootChangedConnection = graphGadget.rootChangedSignal().connect( Gaffer.WeakMethod( self.__rootChanged ) )
		
		self.__gadgetWidget.getViewportGadget().setChild( graphGadget )
		self.__gadgetWidget.getViewportGadget().setDragTracking( True )
		self.__frame( scriptNode.selection() )		

		self.__buttonPressConnection = self.buttonPressSignal().connect( Gaffer.WeakMethod( self.__buttonPress ) )
		self.__keyPressConnection = self.keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPress ) )
		self.__buttonDoubleClickConnection = self.buttonDoubleClickSignal().connect( Gaffer.WeakMethod( self.__buttonDoubleClick ) )
		
		self.__gadgetWidget._qtWidget().installEventFilter( _eventFilter )
		
		self.__nodeMenu = None
		
	## Returns the internal GadgetWidget holding the GraphGadget.	
	def graphGadgetWidget( self ) :
	
		return self.__gadgetWidget

	## Returns the internal Gadget used to draw the graph. This may be
	# modified directly to set up appropriate filters etc. This is just
	# a convenience method returning graphGadgetWidget().getViewportGadget().getChild().
	def graphGadget( self ) :
	
		return self.graphGadgetWidget().getViewportGadget().getChild()

	## Frames the specified nodes in the viewport.
	def frame( self, nodes ) :
	
		self.__frame( nodes )
	
	def getTitle( self ) :
		
		title = super( NodeGraph, self ).getTitle()
		if title:
			return title
		
		result = IECore.CamelCase.toSpaced( self.__class__.__name__ )
	
		root = self.graphGadget().getRoot()
		if not root.isSame( self.scriptNode() ) :
			result += " : " + root.relativeName( self.scriptNode() ).replace( ".", " / " )
		
		return result
	
	__plugContextMenuSignal = Gaffer.Signal3()
	## Returns a signal which is emitted to create a context menu for a 
	# plug in the graph. Slots may connect to this signal to edit the
	# menu definition on the fly - the signature for the signal is
	# ( nodeGraph, plug, menuDefinition ) and the menu definition should just be
	# edited in place.
	@classmethod
	def plugContextMenuSignal( cls ) :
	
		return cls.__plugContextMenuSignal
	
	__connectionContextMenuSignal = Gaffer.Signal3()
	## Returns a signal which is emitted to create a context menu for a 
	# connection in the graph. Slots may connect to this signal to edit the
	# menu definition on the fly - the signature for the signal is
	# ( nodeGraph, destinationPlug, menuDefinition ) and the menu definition
	# should just be edited in place.
	@classmethod
	def connectionContextMenuSignal( cls ) :
	
		return cls.__connectionContextMenuSignal
		
	__nodeContextMenuSignal = Gaffer.Signal3()
	## Returns a signal which is emitted to create a context menu for a
	# node in the graph. Slots may connect to this signal to edit the
	# menu definition on the fly - the signature for the signal is
	# ( nodeGraph, node, menuDefinition ) and the menu definition should just be
	# edited in place. Typically you would add slots to this signal
	# as part of a startup script.
	@classmethod
	def nodeContextMenuSignal( cls ) :
	
		return cls.__nodeContextMenuSignal
	
	## May be used from a slot attached to nodeContextMenuSignal() to install some
	# standard menu items for modifying the connection visibility for a node.
	@classmethod
	def appendConnectionVisibilityMenuDefinitions( cls, nodeGraph, node, menuDefinition ) :
	
		menuDefinition.append( "/ConnectionVisibilityDivider", { "divider" : True } )
		menuDefinition.append(
			"/Show Input Connections",
			{
				"checkBox" : IECore.curry( cls.__getNodeInputConnectionsVisible, nodeGraph.graphGadget(), node ),
				"command" : IECore.curry( cls.__setNodeInputConnectionsVisible, nodeGraph.graphGadget(), node )
			}
		)
		menuDefinition.append(
			"/Show Output Connections",
			{
				"checkBox" : IECore.curry( cls.__getNodeOutputConnectionsVisible, nodeGraph.graphGadget(), node ),
				"command" : IECore.curry( cls.__setNodeOutputConnectionsVisible, nodeGraph.graphGadget(), node )
			}
		)

	## May be used from a slot attached to nodeContextMenuSignal() to install a
	# standard menu item for modifying the enabled state of a node.
	@classmethod
	def appendEnabledPlugMenuDefinitions( cls, nodeGraph, node, menuDefinition ) :
		
		enabledPlug = node.enabledPlug() if isinstance( node, Gaffer.DependencyNode ) else None
		if enabledPlug is not None :
			menuDefinition.append( "/EnabledDivider", { "divider" : True } )
			menuDefinition.append(
				"/Enabled",
				{
					"command" : IECore.curry( cls.__setEnabled, node ),
					"checkBox" : enabledPlug.getValue(),
					"active" : enabledPlug.settable()
				}
			)
	
	__nodeDoubleClickSignal = Gaffer.Signal2()
	## Returns a signal which is emitted whenever a node is double clicked.
	# Slots should have the signature ( nodeGraph, node ).
	@classmethod
	def nodeDoubleClickSignal( cls ) :
	
		return cls.__nodeDoubleClickSignal
	
	## Ensures that the specified node has a visible NodeGraph viewing
	# it, and returns that editor.
	## \todo Consider how this relates to the todo items in NodeEditor.acquire().
	@classmethod
	def acquire( cls, rootNode ) :
	
		if isinstance( rootNode, Gaffer.ScriptNode ) :
			script = rootNode
		else :
			script = rootNode.scriptNode()
			
		scriptWindow = GafferUI.ScriptWindow.acquire( script )
		tabbedContainer = None
		for editor in scriptWindow.getLayout().editors( type = GafferUI.NodeGraph ) :
			if rootNode.isSame( editor.graphGadget().getRoot() ) :
				editor.parent().setCurrent( editor )
				return editor
					
		editor = NodeGraph( script )
		editor.graphGadget().setRoot( rootNode )
		scriptWindow.getLayout().addEditor( editor )
		
		return editor
		
	def __repr__( self ) :

		return "GafferUI.NodeGraph( scriptNode )"	

	def _nodeMenu( self ) :
	
		if self.__nodeMenu is None :
			self.__nodeMenu = GafferUI.Menu( GafferUI.NodeMenu.acquire( self.scriptNode().applicationRoot() ).definition(), searchable=True )
	
		return self.__nodeMenu
	
	def __buttonPress( self, widget, event ) :
				
		if event.buttons & GafferUI.ButtonEvent.Buttons.Right :
						
			# right click - display either the node creation popup menu
			# or a menu specific to the node/plug/connection under the
			# mouse if possible.
			
			viewport = self.__gadgetWidget.getViewportGadget()
			gadgets = viewport.gadgetsAt( IECore.V2f( event.line.p1.x, event.line.p1.y ) )
			if len( gadgets ) :
			
				overrideMenuDefinition = IECore.MenuDefinition()
				overrideMenuTitle = None
				
				if isinstance( gadgets[0], GafferUI.Nodule ) :
					self.plugContextMenuSignal()( self, gadgets[0].plug(), overrideMenuDefinition )
					overrideMenuTitle = gadgets[0].plug().relativeName( self.graphGadget().getRoot() )
				elif isinstance( gadgets[0], GafferUI.ConnectionGadget ) :
					self.connectionContextMenuSignal()( self, gadgets[0].dstNodule().plug(), overrideMenuDefinition )
					overrideMenuTitle = "-> " + gadgets[0].dstNodule().plug().relativeName( self.graphGadget().getRoot() )					
				else :
					nodeGadget = gadgets[0]
					if not isinstance( nodeGadget, GafferUI.NodeGadget ) :
						nodeGadget = nodeGadget.ancestor( GafferUI.NodeGadget.staticTypeId() )
					if nodeGadget is not None :
						self.nodeContextMenuSignal()( self, nodeGadget.node(), overrideMenuDefinition )
						overrideMenuTitle = nodeGadget.node().getName()
			
				if len( overrideMenuDefinition.items() ) :
					menuDefinition = overrideMenuDefinition
					self._m = GafferUI.Menu( menuDefinition, title=overrideMenuTitle )
					self._m.popup( self )
					return True
			
			self._nodeMenu().popup( self )
			
			return True
	
		return False
	
	def __nodeGadgetAt( self, position ) :
	
		viewport = self.__gadgetWidget.getViewportGadget()
		line = viewport.rasterToGadgetSpace( IECore.V2f( position.x, position.y ) )
		return self.graphGadget().nodeGadgetAt( line )
	
	def __keyPress( self, widget, event ) :
		
		if event.key == "F" :
			self.__frame( self.scriptNode().selection() )
			return True
		## \todo This cursor key navigation might not make sense for all applications,
		# so we should move it into BoxUI and load it in a config file that the gui app uses.
		# I think this implies that every Widget.*Signal() method should have a
		# Widget.static*Signal() method to allow global handlers to be registered by widget type.
		# We already have a mix of static/nonstatic signals for menus, so that might make a nice
		# generalisation.
		elif event.key == "Down" :
			selection = self.scriptNode().selection()
			if selection.size() and isinstance( selection[0], Gaffer.Box ) :
				self.graphGadget().setRoot( selection[0] )
				self.__frame( self.graphGadget().getRoot().children( Gaffer.Node.staticTypeId() ) )
				return True
		elif event.key == "Up" :
			root = self.graphGadget().getRoot()
			if isinstance( root, Gaffer.Box ) :
				self.graphGadget().setRoot( root.parent() )
				return True
				
		return False
		
	def __frame( self, nodes ) :
	
		graphGadget = self.graphGadget()
		
		# get the bounds of the nodes
		bound = IECore.Box3f()
		for node in nodes :
			nodeGadget = graphGadget.nodeGadget( node )
			if nodeGadget :
				bound.extendBy( nodeGadget.transformedBound( graphGadget ) )
		
		# if there were no nodes then use the bound of the whole
		# graph.		
		if bound.isEmpty() :
			bound = graphGadget.bound()
			
		# if there's still nothing then an arbitrary area in the centre of the world
		if bound.isEmpty() :
			bound = IECore.Box3f( IECore.V3f( -10, -10, 0 ), IECore.V3f( 10, 10, 0 ) )
			
		# pad it a little bit so
		# it sits nicer in the frame
		bound.min -= IECore.V3f( 5, 5, 0 )
		bound.max += IECore.V3f( 5, 5, 0 )
				
		# now adjust the bounds so that we don't zoom in further than we want to
		boundSize = bound.size()
		widgetSize = IECore.V3f( self._qtWidget().width(), self._qtWidget().height(), 0 )
		pixelsPerUnit = widgetSize / boundSize
		adjustedPixelsPerUnit = min( pixelsPerUnit.x, pixelsPerUnit.y, 10 )
		newBoundSize = widgetSize / adjustedPixelsPerUnit
		boundCenter = bound.center()
		bound.min = boundCenter - newBoundSize / 2.0
		bound.max = boundCenter + newBoundSize / 2.0
			
		self.__gadgetWidget.getViewportGadget().frame( bound )
	
	def __buttonDoubleClick( self, widget, event ) :
	
		nodeGadget = self.__nodeGadgetAt( event.line.p1 )				
		if nodeGadget is not None :
			return self.nodeDoubleClickSignal()( self, nodeGadget.node() )
	
	def __rootChanged( self, graphGadget ) :
	
		if graphGadget.getRoot().isSame( self.scriptNode() ) :
			self.__rootNameChangedConnection = None
			self.__rootParentChangedConnection = None
		else :
			self.__rootNameChangedConnection = graphGadget.getRoot().nameChangedSignal().connect( Gaffer.WeakMethod( self.__rootNameChanged ) )
			self.__rootParentChangedConnection = graphGadget.getRoot().parentChangedSignal().connect( Gaffer.WeakMethod( self.__rootParentChanged ) )
			
		self.titleChangedSignal()( self )
		
	def __rootNameChanged( self, root ) :
	
		self.titleChangedSignal()( self )
		
	def __rootParentChanged( self, root, oldParent ) :
	
		# root has been deleted
		## \todo I'm not sure if we should be responsible for removing ourselves or not.
		# Perhaps we should just signal that we're not valid in some way and the CompoundEditor should
		# remove us? Consider how this relates to NodeEditor.__deleteWindow() too.
		self.parent().removeChild( self )

	@classmethod
	def __getNodeInputConnectionsVisible( cls, graphGadget, node ) :

		return not graphGadget.getNodeInputConnectionsMinimised( node )

	@classmethod
	def __setNodeInputConnectionsVisible( cls, graphGadget, node, value ) :

		with Gaffer.UndoContext( node.ancestor( Gaffer.ScriptNode.staticTypeId() ) ) :
			graphGadget.setNodeInputConnectionsMinimised( node, not value )

	@classmethod
	def __getNodeOutputConnectionsVisible( cls, graphGadget, node ) :

		return not graphGadget.getNodeOutputConnectionsMinimised( node )

	@classmethod
	def __setNodeOutputConnectionsVisible( cls, graphGadget, node, value ) :

		with Gaffer.UndoContext( node.ancestor( Gaffer.ScriptNode.staticTypeId() ) ) :
			graphGadget.setNodeOutputConnectionsMinimised( node, not value )

	@classmethod
	def __setEnabled( cls, node, value ) :

		with Gaffer.UndoContext( node.ancestor( Gaffer.ScriptNode.staticTypeId() ) ) :
			node.enabledPlug().setValue( value )

## Used to capture TAB input since it doesn't make it through to the keyPressSignal
## \todo: investigate this further. TextWidget does receive TAB in keyPressSignal
class _EventFilter( QtCore.QObject ) :
	
	def eventFilter( self, qObject, qEvent ) :
		
		if qEvent.type() == QtCore.QEvent.KeyPress and qEvent.key() == QtCore.Qt.Key_Tab :
			
			nodeGraph = GafferUI.Widget._owner( qObject ).ancestor( NodeGraph )
			if nodeGraph :
				nodeGraph._nodeMenu().popup( nodeGraph )
				return True
		
		return False

# this single instance is used by all widgets
_eventFilter = _EventFilter()

GafferUI.EditorWidget.registerType( "NodeGraph", NodeGraph )
