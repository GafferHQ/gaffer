##########################################################################
#  
#  Copyright (c) 2013-2014, Image Engine Design Inc. All rights reserved.
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

import re
import os
import weakref

import IECore

import Gaffer
import GafferUI

## A command suitable for use with NodeMenu.append(), to add a menu
# item for the creation of a Box from the current selection. We don't
# actually append it automatically, but instead let the startup files
# for particular applications append it if it suits their purposes.
def nodeMenuCreateCommand( menu ) :

	nodeGraph = menu.ancestor( GafferUI.NodeGraph )
	assert( nodeGraph is not None )
	
	script = nodeGraph.scriptNode()
	graphGadget = nodeGraph.graphGadgetWidget().getViewportGadget().getChild()
	
	return Gaffer.Box.create( graphGadget.getRoot(), script.selection() )

## A callback suitable for use with NodeGraph.nodeContextMenuSignal - it provides
# menu options specific to Boxes. We don't actually register it automatically,
# but instead let the startup files for particular applications register
# it if it suits their purposes.
def appendNodeContextMenuDefinitions( nodeGraph, node, menuDefinition ) :
	
	if not isinstance( node, Gaffer.Box ) :
		return
			
	menuDefinition.append( "/BoxDivider", { "divider" : True } )
	menuDefinition.append( "/Show Contents...", { "command" : IECore.curry( __showContents, nodeGraph, node ) } )

def __showContents( nodeGraph, box ) :

	GafferUI.NodeGraph.acquire( box )

# NodeUI
##########################################################################

class BoxNodeUI( GafferUI.StandardNodeUI ) :

	def __init__( self, node, displayMode = None, **kw ) :
	
		GafferUI.StandardNodeUI.__init__( self, node, displayMode, **kw )
		
		## \todo Maybe this should become a customisable part of the StandardNodeUI - if so then
		# perhaps we need to integrate it with the existing presets menu in ParameterisedHolderNodeUI.
		toolButton = GafferUI.MenuButton( image = "gear.png", hasFrame=False )
		toolButton.setMenu( GafferUI.Menu( Gaffer.WeakMethod( self._toolMenuDefinition ) ) )

		self._tabbedContainer().setCornerWidget( toolButton )
	
		self.__uiEditor = None
	
	def _toolMenuDefinition( self ) :
	
		result = IECore.MenuDefinition()
		result.append( "/Edit UI...", { "command" : Gaffer.WeakMethod( self.__showUIEditor ) } )
		result.append( "/Export Divider", { "divider" : True } )
		result.append( "/Export for referencing...", { "command" : Gaffer.WeakMethod( self.__exportForReferencing ) } )
		
		return result
		
	def __exportForReferencing( self ) :
	
		bookmarks = GafferUI.Bookmarks.acquire( self.node().ancestor( Gaffer.ApplicationRoot.staticTypeId() ), category="reference" )

		path = Gaffer.FileSystemPath( bookmarks.getDefault( self ) )
		path.setFilter( Gaffer.FileSystemPath.createStandardFilter( [ "grf" ] ) )

		dialogue = GafferUI.PathChooserDialogue( path, title="Export for referencing", confirmLabel="Export", leaf=True, bookmarks=bookmarks )
		path = dialogue.waitForPath( parentWindow = self.ancestor( GafferUI.Window ) )

		if not path :
			return

		path = str( path )
		if not path.endswith( ".grf" ) :
			path += ".grf"

		self.node().exportForReference( path )
		
	def __showUIEditor( self ) :
	
		if self.__uiEditor is None :
			## \todo Close when deleted, only one per node, title matching node name etc, etc. 
			# Maybe we need an EditorWindow class? or a CompoundEditor.acquire() method??
			#	- I think maybe the latter.
			with GafferUI.Window( "Box Editor", borderWidth = 4 ) as self.__uiEditor :
				editor = BoxEditor( self.node().scriptNode() )
				editor.setNodeSet( Gaffer.StandardSet( [ self.node() ] ) )
				
			self.ancestor( GafferUI.Window ).addChildWindow( self.__uiEditor )
		
		self.__uiEditor.setVisible( True )
	
GafferUI.NodeUI.registerNodeUI( Gaffer.Box.staticTypeId(), BoxNodeUI )

# PlugValueWidget registrations
##########################################################################

GafferUI.PlugValueWidget.registerCreator( Gaffer.Box.staticTypeId(), re.compile( "in[0-9]*" ), None )
GafferUI.PlugValueWidget.registerCreator( Gaffer.Box.staticTypeId(), re.compile( "out[0-9]*" ), None )

def __plugValueWidgetCreator( plug ) :

	# when a plug has been promoted, we get the widget that would
	# have been used to represent the internal plug, and then 
	# call setPlug() with the external plug. this allows us to
	# transfer custom uis from inside the box to outside the box.	
	box = plug.node()
	for output in plug.outputs() :
		if box.plugIsPromoted( output ) :
			widget = GafferUI.PlugValueWidget.create( output )
			if widget is not None :
				widget.setPlug( plug )
			return widget
			
	return GafferUI.PlugValueWidget.create( plug, useTypeOnly=True )
		
GafferUI.PlugValueWidget.registerCreator( Gaffer.Box.staticTypeId(), "user.*" , __plugValueWidgetCreator )

# Plug menu
##########################################################################

def __promoteToBox( box, plug ) :

	with Gaffer.UndoContext( box.ancestor( Gaffer.ScriptNode.staticTypeId() ) ) :
		box.promotePlug( plug )

def __unpromoteFromBox( box, plug ) :

	with Gaffer.UndoContext( box.ancestor( Gaffer.ScriptNode.staticTypeId() ) ) :
		box.unpromotePlug( plug )

def __plugPopupMenu( menuDefinition, plugValueWidget ) :
	
	plug = plugValueWidget.getPlug()
	node = plug.node()
	if node is None :
		return

	box = node.ancestor( Gaffer.Box.staticTypeId() )
	if box is None :
		return

	if box.canPromotePlug( plug ) :
		
		menuDefinition.append( "/BoxDivider", { "divider" : True } )
		menuDefinition.append( "/Promote to %s" % box.getName(), {
			"command" : IECore.curry( __promoteToBox, box, plug ),
			"active" : not plugValueWidget.getReadOnly(),
		} )

	elif box.plugIsPromoted( plug ) :
	
		# Add a menu item to unpromote the plug, replacing the "Remove input" menu item if it exists
		
		with IECore.IgnoredExceptions( Exception ) :
			menuDefinition.remove( "/Remove input" )
			
		menuDefinition.append( "/BoxDivider", { "divider" : True } )
		menuDefinition.append( "/Unpromote from %s" % box.getName(), {
			"command" : IECore.curry( __unpromoteFromBox, box, plug ),
			"active" : not plugValueWidget.getReadOnly(),
		} )
			
__plugPopupMenuConnection = GafferUI.PlugValueWidget.popupMenuSignal().connect( __plugPopupMenu )

# BoxEditor. This allows Box UIs to be customised.
##########################################################################

class BoxEditor( GafferUI.NodeSetEditor ) :

	def __init__( self, scriptNode, **kw ) :
	
		self.__tabbedContainer = GafferUI.TabbedContainer()
	
		GafferUI.NodeSetEditor.__init__( self, self.__tabbedContainer, scriptNode, **kw )
		
		# Build the UI. Initially this isn't connected up to any node - we'll
		# perform the connections in _updateFromSet().
		######################################################################
		
		self.__nodeMetadataConnections = []
		self.__plugMetadataConnections = []
		
		with self.__tabbedContainer :
		
			# Node tab
			with GafferUI.GridContainer( spacing = 4, borderWidth = 8, parenting = { "label" : "Node" } ) as self.__nodeTab :
				
				GafferUI.Label(
					"Name",
					parenting = {
						"index" : ( 0, 0 ),
						"alignment" : ( GafferUI.HorizontalAlignment.Right, GafferUI.VerticalAlignment.Center )
					}
				)
				
				self.__nodeNameWidget = GafferUI.NameWidget( None, parenting = { "index" : ( 1, 0 ) } )
			
				GafferUI.Label(
					"Description",
					parenting = {
						"index" : ( 0, 1 ),
						"alignment" : ( GafferUI.HorizontalAlignment.Right, GafferUI.VerticalAlignment.Top )
					}
				)
				
				description = GafferUI.MultiLineTextWidget( parenting = { "index" : ( 1, 1 ) } )
				self.__nodeMetadataConnections.append( _MetadataConnection( description, None, "description" ) )
			
			# Plugs tab
			with GafferUI.SplitContainer( orientation=GafferUI.SplitContainer.Orientation.Horizontal, borderWidth = 8, parenting = { "label" : "Plugs" } ) :
				
				self.__plugListing = _PlugListing()
				self.__plugListingSelectionChangedConnection = self.__plugListing.selectionChangedSignal().connect( Gaffer.WeakMethod( self.__plugListingSelectionChanged ) )
				
				with GafferUI.GridContainer( spacing = 4, borderWidth = 8 ) as self.__plugEditor :
				
					GafferUI.Label(
						"Name",
						parenting = {
							"index" : ( 0, 0 ), 
							"alignment" : ( GafferUI.HorizontalAlignment.Right, GafferUI.VerticalAlignment.Center )
						}
					)
			
					self.__plugNameWidget = GafferUI.NameWidget( None, parenting = { "index" : ( 1, 0 ) } )

					GafferUI.Label(
						"Description",
						parenting = {
							"index" : ( 0, 1 ), 
							"alignment" : ( GafferUI.HorizontalAlignment.Right, GafferUI.VerticalAlignment.Top )
						}
					)

					description = GafferUI.MultiLineTextWidget( parenting = { "index" : ( 1, 1 ) } )
					self.__plugMetadataConnections.append( _MetadataConnection( description, None, "description" ) )
			
					GafferUI.Label(
						"Divider",
						parenting = {
							"index" : ( 0, 2 ), 
							"alignment" : ( GafferUI.HorizontalAlignment.Right, GafferUI.VerticalAlignment.Center )
						}
					)
			
					divider = GafferUI.BoolWidget(
						parenting = {
							"index" : ( 1, 2 ), 
							"alignment" : ( GafferUI.HorizontalAlignment.Left, GafferUI.VerticalAlignment.Center )
						}
					)
					self.__plugMetadataConnections.append( _MetadataConnection( divider, None, "divider" ) )

		# initialise our selection to nothing
				
		self.__box = None
		self.__selectedPlug = None
	
		# call __updateFromSetInternal() to populate our selection and connect
		# the ui to it. we pass lazy==False to avoid the early out if
		# there is no currently selected box.

		self.__updateFromSetInternal( lazy=False )
		
	def setSelectedPlug( self, plug ) :
	
		self.__setSelectedPlugInternal( plug )		
		
	def getSelectedPlug( self ) :
	
		return self.__selectedPlug	
		
	def _updateFromSet( self ) :
	
		self.__updateFromSetInternal()
	
	def __setSelectedPlugInternal( self, plug, lazy=True ) :
	
		assert( plug is None or self.__box["user"].isAncestorOf( plug ) )
		
		if lazy and plug == self.__selectedPlug :
			return
		
		self.__selectedPlug = plug
		self.__plugNameWidget.setGraphComponent( self.__selectedPlug )
		self.__plugEditor.setEnabled( self.__selectedPlug is not None )
		
		if self.__selectedPlug is not None :
			self.__plugListing.setSelectedPaths(
				self.__plugListing.getPath().copy().setFromString( "/" + plug.getName() )
			)
		else :
			self.__plugListing.setSelectedPaths( [] )
		
		for connection in self.__plugMetadataConnections :
			connection.setTarget( self.__selectedPlug )
			
	def __updateFromSetInternal( self, lazy=True ) :
		
		boxes = [ node for node in self.getNodeSet() if isinstance( node, Gaffer.Box ) ]
		box = boxes[-1] if len( boxes ) else None 

		if lazy and box == self.__box :
			return
			
		self.__box = box
		self.__nodeNameWidget.setGraphComponent( self.__box )
		self.__nodeTab.setEnabled( self.__box is not None )
				
		self.__plugListing.setPlugParent( self.__box["user"] if self.__box is not None else None )

		if self.__box is None or not len( self.__box["user"] ) :
			self.__setSelectedPlugInternal( None, lazy )
		else :
			self.__setSelectedPlugInternal( self.__box["user"][0], lazy )
			
		for connection in self.__nodeMetadataConnections :
			connection.setTarget( self.__box )
					
	def __plugListingSelectionChanged( self, listing ) :
		
		paths = listing.getSelectedPaths()
		if not paths :
			# the path might have been deselected automatically because the plug name
			# changed. in this case we want to restore the old selection.
			previousSelection = self.getSelectedPlug()
			if (
				previousSelection is not None and
				self.__box is not None and
				previousSelection.parent().isSame( self.__box["user"] )
			) :
				listing.setSelectedPaths(
					listing.getPath().copy().setFromString( "/" + previousSelection.getName() )
				)
			else :
				self.setSelectedPlug( None )
		else :
			self.setSelectedPlug( paths[0].info()["dict:value"].plug )
	
GafferUI.EditorWidget.registerType( "BoxEditor", BoxEditor )

# _PlugListing. This is used to list the plugs in the BoxEditor.
##########################################################################

class _PlugListing( GafferUI.PathListingWidget ) :

	# Class used to represent a plug and its index within the listing.
	class Entry( object ) :
	
		__slots__ = ( "plug", "index" )
		
		def __init__( self, plug, index ) :
		
			self.plug = plug
			self.index = index

	def __init__( self ) :
			
		GafferUI.PathListingWidget.__init__(
			self,
			Gaffer.DictPath( {}, "/" ),
			# listing displays the plug name and automatically sorts based on plug index
			columns = ( GafferUI.PathListingWidget.Column( "dict:value", "Name", lambda x : x.plug.getName(), lambda x : x.index ), ),
			displayMode = GafferUI.PathListingWidget.DisplayMode.Tree,
		)
		
		self.__parent = None # the parent of the plugs we're listing

		self.setDragPointer( "" )

		self.setHeaderVisible( False )
		self.__dragEnterConnection = self.dragEnterSignal().connect( Gaffer.WeakMethod( self.__dragEnter ) )
		self.__dragMoveConnection = self.dragMoveSignal().connect( Gaffer.WeakMethod( self.__dragMove ) )
		self.__dropConnection = self.dropSignal().connect( Gaffer.WeakMethod( self.__drop ) )
		
		self.__metadataPlugValueChangedConnection = Gaffer.Metadata.plugValueChangedSignal().connect( Gaffer.WeakMethod( self.__plugMetadataChanged ) )
		
	def setPlugParent( self, parent ) :
	
		self.__parent = parent
		
		self.__childAddedConnection = None
		self.__childRemovedConnection = None
		self.__childNameChangedConnections = {}

		if self.__parent is not None :			
			self.__childAddedConnection = self.__parent.childAddedSignal().connect( Gaffer.WeakMethod( self.__childAddedOrRemoved ) )
			self.__childRemovedConnection = self.__parent.childRemovedSignal().connect( Gaffer.WeakMethod( self.__childAddedOrRemoved ) )
			for child in self.__parent.children() :
				self.__updateChildNameChangedConnection( child )
		
		self.__updatePath()
		
	def getPlugParent( self ) :
	
		return self.__parent

	def __updatePath( self ) :
	
		if self.__parent is None :
			# we have nothing to show - early out.
			self.setPath( Gaffer.DictPath( {}, "/" ) )
			return
	
		# build a DictPath to represent our child plugs.
	
		plugsAndIndices = [ list( x ) for x in enumerate( self.__parent.children() ) ]
		for plugAndIndex in plugsAndIndices :
			index = Gaffer.Metadata.plugValue( plugAndIndex[1], "layout:index" )
			if index is not None :
				plugAndIndex[0] = index
		
		d = {}
		for index, plug in plugsAndIndices :
			d[plug.getName()] = self.Entry( plug, index )
			
		self.setPath( Gaffer.DictPath( d, "/" ) )

	def __childAddedOrRemoved( self, parent, child ) :
	
		assert( parent.isSame( self.__parent ) )
		
		self.__updatePath()
		self.__updateChildNameChangedConnection( child ) 
	
	def __childNameChanged( self, child ) :
	
		self.__updatePath()
		
	def __updateChildNameChangedConnection( self, child ) :
       
		if self.__parent.isSame( child.parent() ) :
			if child not in self.__childNameChangedConnections :
				self.__childNameChangedConnections[child] = child.nameChangedSignal().connect( Gaffer.WeakMethod( self.__childNameChanged ) )
		else :
			if child in self.__childNameChangedConnections :
				del self.__childNameChangedConnections[child]

	def __dragValid( self, event ) :
	
		if event.sourceWidget is not self :
			return False
		if not isinstance( event.data, IECore.StringVectorData ) :
			return False
				
		return True

	def __dragEnter( self, listing, event ) :
	
		# accept the drag if it originates with us,
		# so __dragMove and __drop can implement
		# drag and drop reordering of plugs.
		if not self.__dragValid( event ) :
			return False
		
		return True

	def __dragMove( self, listing, event ) :
	
		if not self.__dragValid( event ) :
			return False
		
		# figure out which index we're moving,
		# and to where.
		
		d = self.getPath().dict()
		
		oldIndex = d[event.data[0][1:]].index
		targetPath = self.pathAt( event.line.p0 )
		if targetPath is not None :
			newIndex = d[targetPath[0]].index
		else :
			if event.line.p0.y < 1 :
				newIndex = 0
			else :
				newIndex = len( d ) - 1
		
		if newIndex == oldIndex :
			return True
		
		# edit our plug dictionary in place to apply the
		# new ordering.
		
		for entry in self.getPath().dict().values() :
			if entry.index > oldIndex and entry.index <= newIndex :
				entry.index -= 1
			elif entry.index == oldIndex :
				entry.index = newIndex
			elif entry.index >= newIndex and entry.index < oldIndex :
				entry.index += 1
		
		# let the listing know we've been monkeying behind the scenes.
		
		self.getPath().pathChangedSignal()( self.getPath() )
				
		return True
		
	def __drop( self, listing, event ) :
	
		if not self.__dragValid( event ) :
			return False
		
		# flush the changed indices into the metadata for the node,
		# so that they actual PlugLayout will be updated to reflect
		# the new ordering.
		
		for entry in self.getPath().dict().values() :
			self.__parent.node().setPlugMetadata( entry.plug, "layout:index", entry.index )
		
		return True

	def __plugMetadataChanged( self, nodeTypeId, plugPath, key ) :
	
		if self.__parent is None :
			return
			
		if not self.__parent.node().isInstanceOf( nodeTypeId ) :
			return
		
		if key == "layout:index" :
			self.__updatePath()

# _MetadataConnection. This maintains connections between a widget and
# a metadata value, to allow users to edit metadata.
##########################################################################

class _MetadataConnection() :

	__instances = []

	def __init__( self, widget, target, key ) :
	
		if isinstance( widget, ( GafferUI.TextWidget, GafferUI.MultiLineTextWidget ) ) :
			self.__widgetChangedConnection = widget.editingFinishedSignal().connect(
				Gaffer.WeakMethod( self.__widgetChanged )
			)
		elif isinstance( widget, GafferUI.BoolWidget ) :
			self.__widgetChangedConnection = widget.stateChangedSignal().connect(
				Gaffer.WeakMethod( self.__widgetChanged )
			)
		else :
			raise TypeError(  "Unsupported widget type" )
				
		self.__widget = widget
		self.__key = key
		self.__target = None
		
		self.setTarget( target )
		
		_MetadataConnection.__instances.append( weakref.ref( self ) )
		
	def setTarget( self, target ) :
		
		assert( isinstance( target, ( Gaffer.Box, Gaffer.Plug, type( None ) ) ) )
		if isinstance( target, Gaffer.Plug ) :
			assert( isinstance( target.node(), Gaffer.Box ) )

		self.__target = target
		self.__widget.setEnabled( self.__target is not None )
		
		self.__updateWidgetValue()
		
	def getTarget( self ) :
	
		return self.__target
		
	def __widgetChanged( self, widget ) :
	
		assert( widget is self.__widget )
		
		if self.__target is None :
			return
		
		# get the value from the widget
		
		if isinstance( widget, ( GafferUI.TextWidget, GafferUI.MultiLineTextWidget ) ) :
			value = widget.getText()
		elif isinstance( widget, GafferUI.BoolWidget ) :
			value = widget.getState()
		
		# transfer it to the metadata
		
		if isinstance( self.__target, Gaffer.Plug ) :
			self.__target.node().setPlugMetadata( self.__target, self.__key, value )
		else :
			self.__target.setNodeMetadata( self.__key, value )

	def __updateWidgetValue( self ) :

		# get the value from metadata
		
		if isinstance( self.__target, Gaffer.Plug ) :
			value = Gaffer.Metadata.plugValue( self.__target, self.__key )
		elif isinstance( self.__target, Gaffer.Box ) :
			value = Gaffer.Metadata.nodeValue( self.__target, self.__key )
		else :
			value = None
			
		# transfer it to the widget
				
		if isinstance( self.__widget, ( GafferUI.TextWidget, GafferUI.MultiLineTextWidget ) ) :
			self.__widget.setText( value if value is not None else "" )
		elif isinstance( self.__widget, GafferUI.BoolWidget ) :
			self.__widget.setState( value if value is not None else False )

	@classmethod
	def _nodeMetadataChanged( cls, nodeTypeId, key ) :
	
		for i in cls.__instances :
			instance = i()
			if instance is None or instance.getTarget() is None :
				continue
			if instance.__key != key :
				continue
			if not instance.getTarget().isInstanceOf( nodeTypeId ) :
				continue
				
			instance.__updateWidgetValue()
			
	@classmethod
	def _plugMetadataChanged( cls, nodeTypeId, plugPath, key ) :
	
		for i in cls.__instances :
			instance = i()
			if instance is None or instance.getTarget() is None :
				continue
			if instance.__key != key :
				continue
			if not isinstance( instance.getTarget(), Gaffer.Plug ) :
				continue
			if not instance.getTarget().node().isInstanceOf( nodeTypeId ) :
				continue
			if not Gaffer.match( instance.getTarget().relativeName( instance.getTarget().node() ), plugPath ) :
				continue
				
			instance.__updateWidgetValue()		
			
__nodeMetadataChangedConnection = Gaffer.Metadata.nodeValueChangedSignal().connect( _MetadataConnection._nodeMetadataChanged )
__plugMetadataChangedConnection = Gaffer.Metadata.plugValueChangedSignal().connect( _MetadataConnection._plugMetadataChanged )
