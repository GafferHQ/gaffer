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

import functools
import imath
import weakref

import IECore

import Gaffer
import GafferUI

class GraphEditor( GafferUI.Editor ) :

	def __init__( self, scriptNode, **kw ) :

		self.__gadgetWidget = GafferUI.GadgetWidget(
			bufferOptions = set( [
				GafferUI.GLWidget.BufferOptions.Double,
			] ),
		)

		GafferUI.Editor.__init__( self, self.__gadgetWidget, scriptNode, **kw )

		graphGadget = GafferUI.GraphGadget( self.scriptNode() )
		self.__rootChangedConnection = graphGadget.rootChangedSignal().connect( Gaffer.WeakMethod( self.__rootChanged ) )

		self.__gadgetWidget.getViewportGadget().setPrimaryChild( graphGadget )
		self.__gadgetWidget.getViewportGadget().setDragTracking( GafferUI.ViewportGadget.DragTracking.XDragTracking | GafferUI.ViewportGadget.DragTracking.YDragTracking )
		self.__frame( scriptNode.selection() )

		self.__gadgetWidget.buttonPressSignal().connect( Gaffer.WeakMethod( self.__buttonPress ), scoped = False )
		self.__gadgetWidget.keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPress ), scoped = False )
		self.__gadgetWidget.buttonDoubleClickSignal().connect( Gaffer.WeakMethod( self.__buttonDoubleClick ), scoped = False )
		self.__gadgetWidget.dragEnterSignal().connect( Gaffer.WeakMethod( self.__dragEnter ), scoped = False )
		self.__gadgetWidget.dropSignal().connect( Gaffer.WeakMethod( self.__drop ), scoped = False )
		self.__gadgetWidget.getViewportGadget().preRenderSignal().connect( Gaffer.WeakMethod( self.__preRender ), scoped = False )

		self.__nodeMenu = None

	## Returns the internal GadgetWidget holding the GraphGadget.
	def graphGadgetWidget( self ) :

		return self.__gadgetWidget

	## Returns the internal Gadget used to draw the graph. This may be
	# modified directly to set up appropriate filters etc. This is just
	# a convenience method returning graphGadgetWidget().getViewportGadget().getPrimaryChild().
	def graphGadget( self ) :

		return self.graphGadgetWidget().getViewportGadget().getPrimaryChild()

	## Frames the specified nodes in the viewport. If extend is True
	# then the current framing will be extended to include the specified
	# nodes, if False then the framing will be reset to frame only the
	# nodes specified.
	def frame( self, nodes, extend=False ) :

		self.__frame( nodes, extend )

	def getTitle( self ) :

		title = super( GraphEditor, self ).getTitle()
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
	# ( graphEditor, plug, menuDefinition ) and the menu definition should just be
	# edited in place.
	@classmethod
	def plugContextMenuSignal( cls ) :

		return cls.__plugContextMenuSignal

	__connectionContextMenuSignal = Gaffer.Signal3()
	## Returns a signal which is emitted to create a context menu for a
	# connection in the graph. Slots may connect to this signal to edit the
	# menu definition on the fly - the signature for the signal is
	# ( graphEditor, destinationPlug, menuDefinition ) and the menu definition
	# should just be edited in place.
	@classmethod
	def connectionContextMenuSignal( cls ) :

		return cls.__connectionContextMenuSignal

	@classmethod
	def appendConnectionNavigationMenuDefinitions( cls, graphEditor, destinationPlug, menuDefinition ) :

		def __append( plug, label ) :

			node = plug.node()
			nodeGadget = graphEditor.graphGadget().nodeGadget( node ) if node is not None else None

			menuDefinition.append(
				"/Navigate/Go to " + label,
				{
					"active" : nodeGadget is not None,
					"command" : functools.partial(
						Gaffer.WeakMethod( graphEditor.frame ), [ node ]
					)
				}
			)

			menuDefinition.append(
				"/Navigate/Select " + label,
				{
					"active" : node is not None,
					"command" : functools.partial(
						cls.__select, node
					)
				}
			)

		__append( destinationPlug.getInput(), "Source Node" )
		__append( destinationPlug, "Destination Node" )

	__nodeContextMenuSignal = Gaffer.Signal3()
	## Returns a signal which is emitted to create a context menu for a
	# node in the graph. Slots may connect to this signal to edit the
	# menu definition on the fly - the signature for the signal is
	# ( graphEditor, node, menuDefinition ) and the menu definition should just be
	# edited in place. Typically you would add slots to this signal
	# as part of a startup script.
	@classmethod
	def nodeContextMenuSignal( cls ) :

		return cls.__nodeContextMenuSignal

	## May be used from a slot attached to nodeContextMenuSignal() to install some
	# standard menu items for modifying the connection visibility for a node.
	@classmethod
	def appendConnectionVisibilityMenuDefinitions( cls, graphEditor, node, menuDefinition ) :

		def plugDirectionsWalk( gadget ) :

			result = set()
			if isinstance( gadget, GafferUI.Nodule ) :
				result.add( gadget.plug().direction() )

			for c in gadget.children() :
				result |= plugDirectionsWalk( c )

			return result

		plugDirections = plugDirectionsWalk( graphEditor.graphGadget().nodeGadget( node ) )
		if not plugDirections :
			return

		readOnly = Gaffer.MetadataAlgo.readOnly( node )

		menuDefinition.append( "/ConnectionVisibilityDivider", { "divider" : True } )

		if Gaffer.Plug.Direction.In in plugDirections :
			menuDefinition.append(
				"/Show Input Connections",
				{
					"checkBox" : functools.partial( cls.__getNodeInputConnectionsVisible, graphEditor.graphGadget(), node ),
					"command" : functools.partial( cls.__setNodeInputConnectionsVisible, graphEditor.graphGadget(), node ),
					"active" : not readOnly,
				}
			)

		if Gaffer.Plug.Direction.Out in plugDirections :
			menuDefinition.append(
				"/Show Output Connections",
				{
					"checkBox" : functools.partial( cls.__getNodeOutputConnectionsVisible, graphEditor.graphGadget(), node ),
					"command" : functools.partial( cls.__setNodeOutputConnectionsVisible, graphEditor.graphGadget(), node ),
					"active" : not readOnly
				}
			)

	## May be used from a slot attached to nodeContextMenuSignal() to install a
	# standard menu item for modifying the enabled state of a node.
	@classmethod
	def appendEnabledPlugMenuDefinitions( cls, graphEditor, node, menuDefinition ) :

		enabledPlug = node.enabledPlug() if isinstance( node, Gaffer.DependencyNode ) else None
		if enabledPlug is not None :
			menuDefinition.append( "/EnabledDivider", { "divider" : True } )
			menuDefinition.append(
				"/Enabled",
				{
					"command" : functools.partial( cls.__setEnabled, node ),
					"checkBox" : enabledPlug.getValue(),
					"active" : enabledPlug.settable() and not Gaffer.MetadataAlgo.readOnly( enabledPlug )
				}
			)

			# The plug is hidden as it has no nodule type, rather than via visibility
			plugExposed = bool( Gaffer.Metadata.value( enabledPlug, "nodule:type" ) )
			menuDefinition.append(
				"/Show Enabled Plug",
				{
					# If we weakref enabledPlug, it is dead by the time we come to use it (?)
					"command" : functools.partial( GafferUI.GraphEditor.__exposeEnabledPlug, enabledPlug, not plugExposed ),
					"checkBox" : plugExposed,
					"active" : not Gaffer.MetadataAlgo.readOnly( enabledPlug )
				}
			)

	@staticmethod
	def __exposeEnabledPlug( plug, exposed, _ ) :

		if exposed :
			Gaffer.Metadata.registerValue( plug, "nodule:type", "GafferUI::StandardNodule" )
			Gaffer.Metadata.registerValue( plug, "noduleLayout:section", "right" )
		else :
			Gaffer.Metadata.deregisterValue( plug, "nodule:type" )
			Gaffer.Metadata.deregisterValue( plug, "noduleLayout:section" )

	@classmethod
	def appendContentsMenuDefinitions( cls, graphEditor, node, menuDefinition ) :

		if not GraphEditor.__childrenViewable( node ) :
			return

		menuDefinition.append( "/ContentsDivider", { "divider" : True } )
		menuDefinition.append( "/Show Contents...", { "command" : functools.partial( cls.acquire, node ) } )

	__nodeDoubleClickSignal = GafferUI.WidgetEventSignal()
	## Returns a signal which is emitted whenever a node is double clicked.
	# Slots should have the signature ( graphEditor, node ).
	@classmethod
	def nodeDoubleClickSignal( cls ) :

		return cls.__nodeDoubleClickSignal

	## Ensures that the specified node has a visible GraphEditor viewing
	# it, and returns that editor.
	## \todo Consider how this relates to the todo items in NodeSetEditor.acquire().
	@classmethod
	def acquire( cls, rootNode ) :

		if isinstance( rootNode, Gaffer.ScriptNode ) :
			script = rootNode
		else :
			script = rootNode.scriptNode()

		scriptWindow = GafferUI.ScriptWindow.acquire( script )
		tabbedContainer = None
		for editor in scriptWindow.getLayout().editors( type = GafferUI.GraphEditor ) :
			if rootNode.isSame( editor.graphGadget().getRoot() ) :
				editor.parent().setCurrent( editor )
				return editor

		editor = GraphEditor( script )
		editor.graphGadget().setRoot( rootNode )
		scriptWindow.getLayout().addEditor( editor )

		return editor

	def __repr__( self ) :

		return "GafferUI.GraphEditor( scriptNode )"

	def _nodeMenu( self ) :

		if self.__nodeMenu is None :
			self.__nodeMenu = GafferUI.Menu( GafferUI.NodeMenu.acquire( self.scriptNode().applicationRoot() ).definition(), searchable=True )
			self.__nodeMenu.visibilityChangedSignal().connect( Gaffer.WeakMethod( self.__nodeMenuVisibilityChanged ), scoped = False )

		return self.__nodeMenu

	def __nodeMenuVisibilityChanged( self, widget ) :

		assert( widget is self.__nodeMenu )

		if not self.__nodeMenu.visible() :
			# generally we steal focus on mouse enter (implemented in GadgetWidget),
			# but when the node menu closes we may not get an enter event, so we have to steal
			# the focus back here.
			self.__gadgetWidget._qtWidget().setFocus()

	def __buttonPress( self, widget, event ) :

		if event.buttons & GafferUI.ButtonEvent.Buttons.Right :

			# right click - display either the node creation popup menu
			# or a menu specific to the node/plug/connection under the
			# mouse if possible.

			viewport = self.__gadgetWidget.getViewportGadget()
			gadgets = viewport.gadgetsAt( imath.V2f( event.line.p1.x, event.line.p1.y ) )
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
						nodeGadget = nodeGadget.ancestor( GafferUI.NodeGadget )
					if nodeGadget is not None :
						self.nodeContextMenuSignal()( self, nodeGadget.node(), overrideMenuDefinition )
						overrideMenuTitle = nodeGadget.node().getName()

				if len( overrideMenuDefinition.items() ) :
					menuDefinition = overrideMenuDefinition
					self._m = GafferUI.Menu( menuDefinition, title=overrideMenuTitle )
					self._m.popup( self )
					return True

			if not (
				Gaffer.MetadataAlgo.getChildNodesAreReadOnly( self.graphGadget().getRoot() ) or
				Gaffer.MetadataAlgo.readOnly( self.graphGadget().getRoot() )
			):
				self._nodeMenu().popup( self )
				return True

		return False

	def __nodeGadgetAt( self, position ) :

		viewport = self.__gadgetWidget.getViewportGadget()
		line = viewport.rasterToGadgetSpace( imath.V2f( position.x, position.y ), gadget = self.graphGadget() )
		return self.graphGadget().nodeGadgetAt( line )

	def __keyPress( self, widget, event ) :

		if event.key == "F" and not event.modifiers :
			self.__frame( self.scriptNode().selection() )
			return True
		elif event.key == "Down" :
			selection = self.scriptNode().selection()
			if selection.size() == 1 and selection[0].parent() == self.graphGadget().getRoot() :
				needsModifiers = not GraphEditor.__childrenViewable( selection[0] )
				if (
					( needsModifiers and event.modifiers == event.modifiers.Shift | event.modifiers.Control ) or
					( not needsModifiers and event.modifiers == event.modifiers.None )
				) :
					self.graphGadget().setRoot( selection[0] )
					return True
		elif event.key == "Up" :
			root = self.graphGadget().getRoot()
			if not isinstance( root, Gaffer.ScriptNode ) :
				self.graphGadget().setRoot( root.parent() )
				return True
		elif event.key == "Tab" :
			if not (
				Gaffer.MetadataAlgo.getChildNodesAreReadOnly( self.graphGadget().getRoot() ) or
				Gaffer.MetadataAlgo.readOnly( self.graphGadget().getRoot() )
			):
				self._nodeMenu().popup( self )
				return True

		return False

	def __frame( self, nodes, extend = False ) :

		graphGadget = self.graphGadget()

		# get the bounds of the nodes
		bound = imath.Box3f()
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
			bound = imath.Box3f( imath.V3f( -10, -10, 0 ), imath.V3f( 10, 10, 0 ) )

		# pad it a little bit so
		# it sits nicer in the frame
		bound.setMin( bound.min() - imath.V3f( 1, 1, 0 ) )
		bound.setMax( bound.max() + imath.V3f( 1, 1, 0 ) )

		if extend :
			# we're extending the existing framing, which we assume the
			# user was happy with other than it not showing the nodes in question.
			# so we just take the union of the existing frame and the one for the nodes.
			cb = self.__currentFrame()
			bound.extendBy( imath.Box3f( imath.V3f( cb.min().x, cb.min().y, 0 ), imath.V3f( cb.max().x, cb.max().y, 0 ) ) )
		else :
			# we're reframing from scratch, so the frame for the nodes is all we need.
			# we do however want to make sure that we don't zoom in too far if the node
			# bounds are small, as having a single node filling the screen is of little use -
			# it's better to see some context around it.
			boundSize = bound.size()
			widgetSize = imath.V3f( self._qtWidget().width(), self._qtWidget().height(), 0 )

			pixelsPerUnit = min( widgetSize.x / boundSize.x, widgetSize.y / boundSize.y )
			adjustedPixelsPerUnit = min( pixelsPerUnit, 10 )

			newBoundSize = widgetSize / adjustedPixelsPerUnit
			boundCenter = bound.center()
			bound.setMin( boundCenter - newBoundSize / 2.0 )
			bound.setMax( boundCenter + newBoundSize / 2.0 )

		self.__gadgetWidget.getViewportGadget().frame( bound )

	def __buttonDoubleClick( self, widget, event ) :

		nodeGadget = self.__nodeGadgetAt( event.line.p1 )
		if nodeGadget is not None :
			return self.nodeDoubleClickSignal()( self, nodeGadget.node() )

	def __dragEnter( self, widget, event ) :

		if event.sourceWidget is self.__gadgetWidget :
			return False

		if self.__dropNodes( event.data ) :
			return True

		return False

	def __drop( self, widget, event ) :

		if event.sourceWidget is self.__gadgetWidget :
			return False

		dropNodes = self.__dropNodes( event.data )
		if dropNodes :
			self.__frame( dropNodes )
			return True

		return False

	def __dropNodes( self, dragData ) :

		if isinstance( dragData, Gaffer.Node ) :
			return [ dragData ]
		elif isinstance( dragData, Gaffer.Plug ) :
			return [ dragData.node() ]
		elif isinstance( dragData, Gaffer.Set ) :
			return [ x for x in dragData if isinstance( x, Gaffer.Node ) ]

		return []

	def __currentFrame( self ) :
		viewportGadget = self.graphGadgetWidget().getViewportGadget()

		rasterMin = viewportGadget.rasterToWorldSpace( imath.V2f( 0 ) ).p0
		rasterMax = viewportGadget.rasterToWorldSpace( imath.V2f( viewportGadget.getViewport() ) ).p0

		frame = imath.Box2f()
		frame.extendBy( imath.V2f( rasterMin[0], rasterMin[1] ) )
		frame.extendBy( imath.V2f( rasterMax[0], rasterMax[1] ) )

		return frame

	def __rootChanged( self, graphGadget, previousRoot ) :

		# save/restore the current framing so jumping in
		# and out of Boxes isn't a confusing experience.

		Gaffer.Metadata.registerValue( previousRoot, "ui:graphEditor:framing", self.__currentFrame(), persistent = False )

		frame = Gaffer.Metadata.value( self.graphGadget().getRoot(), "ui:graphEditor:framing" )
		if frame is not None :
			self.graphGadgetWidget().getViewportGadget().frame(
				imath.Box3f( imath.V3f( frame.min().x, frame.min().y, 0 ), imath.V3f( frame.max().x, frame.max().y, 0 ) )
			)
		else :
			self.__frame( self.graphGadget().getRoot().children( Gaffer.Node ) )

		# do what we need to do to keep our title up to date.

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

		# Root has been deleted.
		self.graphGadget().setRoot( self.scriptNode() )

	def __preRender( self, viewportGadget ) :

		# Find all unpositioned nodes.

		graphGadget = self.graphGadget()
		nodes = [ g.node() for g in graphGadget.unpositionedNodeGadgets() ]
		if not nodes :
			return

		nodes = Gaffer.StandardSet( nodes )

		# Lay them out somewhere near the centre of frame.

		gadgetWidget = self.graphGadgetWidget()
		fallbackPosition = gadgetWidget.getViewportGadget().rasterToGadgetSpace(
			imath.V2f( gadgetWidget.size() ) / 2.0,
			gadget = graphGadget
		).p0
		fallbackPosition = imath.V2f( fallbackPosition.x, fallbackPosition.y )

		graphGadget.getLayout().positionNodes( graphGadget, nodes, fallbackPosition )
		graphGadget.getLayout().layoutNodes( graphGadget, nodes )

		# And then extend the frame to include them, in case the
		# layout has gone off screen.

		self.frame( nodes, extend = True )

	@classmethod
	def __getNodeInputConnectionsVisible( cls, graphGadget, node ) :

		return not graphGadget.getNodeInputConnectionsMinimised( node )

	@classmethod
	def __setNodeInputConnectionsVisible( cls, graphGadget, node, value ) :

		with Gaffer.UndoScope( node.ancestor( Gaffer.ScriptNode ) ) :
			graphGadget.setNodeInputConnectionsMinimised( node, not value )

	@classmethod
	def __getNodeOutputConnectionsVisible( cls, graphGadget, node ) :

		return not graphGadget.getNodeOutputConnectionsMinimised( node )

	@classmethod
	def __setNodeOutputConnectionsVisible( cls, graphGadget, node, value ) :

		with Gaffer.UndoScope( node.ancestor( Gaffer.ScriptNode ) ) :
			graphGadget.setNodeOutputConnectionsMinimised( node, not value )

	@classmethod
	def __setEnabled( cls, node, value ) :

		with Gaffer.UndoScope( node.ancestor( Gaffer.ScriptNode ) ) :
			node.enabledPlug().setValue( value )

	@staticmethod
	def __childrenViewable( node ) :

		viewable = Gaffer.Metadata.value( node, "graphEditor:childrenViewable" )
		if viewable is not None :
			return viewable

		## \todo: Remove nodeGraph fallback when all client code has been updated
		return Gaffer.Metadata.value( node, "nodeGraph:childrenViewable" )

	@staticmethod
	def __select( node ) :

		node.scriptNode().selection().clear()
		node.scriptNode().selection().add( node )

GafferUI.Editor.registerType( "GraphEditor", GraphEditor )
