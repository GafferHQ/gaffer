##########################################################################
#
#  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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

import weakref
import functools
import types
import re

import IECore

import Gaffer
import GafferUI

## The UIEditor class allows the user to edit the interfaces for nodes.
class UIEditor( GafferUI.NodeSetEditor ) :

	def __init__( self, scriptNode, **kw ) :

		self.__frame = GafferUI.Frame( borderWidth = 4, borderStyle = GafferUI.Frame.BorderStyle.None )

		GafferUI.NodeSetEditor.__init__( self, self.__frame, scriptNode, **kw )

		# Build the UI. Initially this isn't connected up to any node - we'll
		# perform the connections in _updateFromSet().
		######################################################################

		self.__nodeMetadataWidgets = []
		self.__plugMetadataWidgets = []

		with self.__frame :
			self.__tabbedContainer = GafferUI.TabbedContainer()

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

				self.__nodeMetadataWidgets.append(
					_MultiLineStringMetadataWidget(
						key = "description",
						parenting = { "index" : ( 1, 1 ) }
					)
				)

				GafferUI.Label(
					"Color",
					parenting = {
						"index" : ( 0, 2 ),
						"alignment" : ( GafferUI.HorizontalAlignment.Right, GafferUI.VerticalAlignment.Top )
					}
				)

				self.__nodeMetadataWidgets.append(
					_ColorSwatchMetadataWidget(
						key = "nodeGadget:color",
						parenting = { "index" : ( 1, 2 ) }
					)
				)

			# Plugs tab
			with GafferUI.SplitContainer( orientation=GafferUI.SplitContainer.Orientation.Horizontal, borderWidth = 8, parenting = { "label" : "Plugs" } ) as self.__plugTab :

				self.__plugListing = _PlugListing()
				self.__plugListingSelectionChangedConnection = self.__plugListing.selectionChangedSignal().connect( Gaffer.WeakMethod( self.__plugListingSelectionChanged ) )

				with GafferUI.TabbedContainer() as self.__plugAndSectionEditorsContainer :

					self.__plugEditor = _PlugEditor()
					self.__sectionEditor = _SectionEditor()
					self.__sectionEditorNameChangedConnection = self.__sectionEditor.nameChangedSignal().connect( Gaffer.WeakMethod( self.__sectionEditorNameChanged ) )

				self.__plugAndSectionEditorsContainer.setTabsVisible( False )

			self.__plugTab.setSizes( [ 0.3, 0.7 ] )

		# initialise our selection to nothing

		self.__node = None
		self.__selectedPlug = None

		# call __updateFromSetInternal() to populate our selection and connect
		# the ui to it. we pass lazy==False to avoid the early out if
		# there is no currently selected node.

		self.__updateFromSetInternal( lazy=False )

	# Selection can be None, a Plug, or the name of a section.
	def setSelection( self, selection ) :

		self.__plugListing.setSelection( selection )

	def getSelection( self ) :

		return self.__plugListing.getSelection()

	## Returns the widget layout responsible for editing the node as a whole.
	def nodeEditor( self ) :

		return self.__nodeTab

	## Returns the widget layout responsible for editing individual plugs.
	def plugEditor( self ) :

		return self.__plugTab

	@classmethod
	def appendNodeContextMenuDefinitions( cls, nodeGraph, node, menuDefinition ) :

		menuDefinition.append( "/UIEditorDivider", { "divider" : True } )
		menuDefinition.append( "/Set Color...", { "command" : functools.partial( cls.__setColor, node = node ) } )

	@classmethod
	def appendNodeEditorToolMenuDefinitions( cls, nodeEditor, node, menuDefinition ) :

		menuDefinition.append(
			"/Edit UI...",
			{
				"command" : functools.partial( GafferUI.UIEditor.acquire, node ),
				"active" : nodeEditor.nodeUI().plugValueWidget( node["user"] ) is not None
			}
		)

	def _updateFromSet( self ) :

		GafferUI.NodeSetEditor._updateFromSet( self )

		self.__updateFromSetInternal()

	def __updateFromSetInternal( self, lazy=True ) :

		node = self._lastAddedNode()

		if lazy and node == self.__node :
			return

		self.__node = node
		self.__nodeNameWidget.setGraphComponent( self.__node )
		self.__nodeTab.setEnabled( self.__node is not None )

		if self.__node is None :
			self.__plugListing.setPlugParent( None )
			self.__sectionEditor.setPlugParent( None )
		else :
			plugParent = self.__node["user"]
			if isinstance( self.__node, Gaffer.Box ) and not len( plugParent ) :
				# For Boxes we want the user to edit the plugs directly
				# parented to the Box, because that is where promoted plugs go,
				# and because we want to leave the "user" plug empty so that it
				# is available for use by the user on Reference nodes once a Box has
				# been exported and referenced. We make a small concession to old-skool
				# boxes (where we mistakenly used to promote to the "user" plug) by
				# editing the user plugs instead if any exist.
				plugParent = self.__node
			self.__plugListing.setPlugParent( plugParent )
			self.__sectionEditor.setPlugParent( plugParent )

		for widget in self.__nodeMetadataWidgets :
			widget.setTarget( self.__node )

		self.setSelection( None )

	def __plugListingSelectionChanged( self, listing ) :

		selection = listing.getSelection()
		if selection is None or isinstance( selection, Gaffer.Plug ) :
			self.__plugEditor.setPlug( selection )
			self.__plugAndSectionEditorsContainer.setCurrent( self.__plugEditor )
		elif isinstance( selection, basestring ) :
			self.__plugEditor.setPlug( None )
			self.__sectionEditor.setSection( selection )
			self.__plugAndSectionEditorsContainer.setCurrent( self.__sectionEditor )

	def __sectionEditorNameChanged( self, sectionEditor, oldName, newName ) :

		# When the name changed, our plug listing will have lost its
		# selection. So give it a helping hand.
		self.__plugListing.setSelection( newName )

	def __repr__( self ) :

		return "GafferUI.UIEditor( scriptNode )"

	@classmethod
	def __setColor( cls, menu, node ) :

		color = Gaffer.Metadata.nodeValue( node, "nodeGadget:color" ) or IECore.Color3f( 1 )
		dialogue = GafferUI.ColorChooserDialogue( color = color, useDisplayTransform = False )
		color = dialogue.waitForColor( parentWindow = menu.ancestor( GafferUI.Window ) )
		if color is not None :
			with Gaffer.UndoContext( node.ancestor( Gaffer.ScriptNode ) ) :
				Gaffer.Metadata.registerNodeValue( node, "nodeGadget:color", color )

GafferUI.EditorWidget.registerType( "UIEditor", UIEditor )

##########################################################################
# PlugValueWidget popup menu
##########################################################################

def __editPlugUI( node, plug ) :

	editor = GafferUI.UIEditor.acquire( node )
	editor.setSelection( plug )
	editor.plugEditor().reveal()

def __plugPopupMenu( menuDefinition, plugValueWidget ) :

	plug = plugValueWidget.getPlug()
	node = plug.node()
	if node is None :
		return

	if isinstance( node, Gaffer.Box ) :
		if not plug.parent().isSame( node ) :
			return
	else :
		if not plug.parent().isSame( node["user"] ) :
			return

	menuDefinition.append( "/EditUIDivider", { "divider" : True } )
	menuDefinition.append( "/Edit UI...", { "command" : IECore.curry( __editPlugUI, node, plug ), "active" : not plugValueWidget.getReadOnly() } )

__plugPopupMenuConnection = GafferUI.PlugValueWidget.popupMenuSignal().connect( __plugPopupMenu )

##########################################################################
# Hierarchical representation of a plug layout, suitable for manipulating
# by the _PlugListing.
# \todo Consider sharing this data structure with the PlugLayout itself,
# rather than each using a different internal representation. If we did
# this then the data structure itself should take care of the mapping
# to/from metadata.
##########################################################################

class _LayoutItem( object ) :

	def __init__( self ) :

		self.__parent = None
		self.__children = []

	def parent( self ) :

		if self.__parent is None :
			return None
		else :
			return self.__parent()

	def child( self, name ) :

		for c in self.__children :
			if c.name() == name :
				return c

		return None

	def isAncestorOf( self, item ) :

		while item is not None :
			parent = item.parent()
			if parent is self :
				return True
			item = parent

		return False

	def append( self, child ) :

		self.insert( len( self ), child )

	def insert( self, index, child ) :

		assert( child.parent() is None )
		self.__children.insert( index, child )
		child.__parent = weakref.ref( self )

	def remove( self, child ) :

		assert( child.parent() is self )

		self.__children.remove( child )
		child.__parent = None

	def index( self, child ) :

		return self.__children.index( child )

	def name( self ) :

		raise NotImplementedError

	def fullName( self ) :

		result = ""
		item = self
		while item.parent() is not None :
			if result :
				result = item.name() + "." + result
			else :
				result = item.name()
			item = item.parent()

		return result

	def __len__( self ) :

		return len( self.__children )

	def __getitem__( self, index ) :

		return self.__children[index]

class _SectionLayoutItem( _LayoutItem ) :

	def __init__( self, sectionName ) :

		_LayoutItem.__init__( self )

		self.__sectionName = sectionName

	def name( self ) :

		return self.__sectionName

class _PlugLayoutItem( _LayoutItem ) :

	def __init__( self, plug ) :

		_LayoutItem.__init__( self )

		self.plug = plug
		self.__name = plug.getName()

	def name( self ) :

		return self.__name

##########################################################################
# _PlugListing. This is used to list the plugs in the UIEditor,
# organised into their respective sections.
##########################################################################

class _PlugListing( GafferUI.Widget ) :

	class __LayoutPath( Gaffer.Path ) :

		def __init__( self, rootItem, path, root="/", filter = None ) :

			Gaffer.Path.__init__( self, path, root, filter )

			self.__rootItem = rootItem

		def rootItem( self ) :

			return self.__rootItem

		def item( self ) :

			result = self.__rootItem
			for name in self :
				result = result.child( name )
				if result is None :
					return None

			return result

		def copy( self ) :

			return self.__class__( self.__rootItem, self[:], self.root(), self.getFilter() )

		def isLeaf( self ) :

			return not isinstance( self.item(), _SectionLayoutItem )

		def isValid( self ) :

			return self.item() is not None

		def _children( self ) :

			item = self.item()
			if item is None :
				return []

			result = [
				self.__class__( self.__rootItem, self[:] + [ c.name() ], self.root(), self.getFilter() )
				for c in item
			]

			# Add a placeholder child into empty sections, to be used as a drag target
			# in __dragMove()
			if len( result ) == 0 and isinstance( item, _SectionLayoutItem ) :
				result.append( self.__class__( self.__rootItem, self[:] + [ " " ], self.root(), self.getFilter() ) )

			return result

	def __init__( self, **kw ) :

		column = GafferUI.ListContainer( spacing = 4 )
		GafferUI.Widget.__init__( self, column )

		with column :

			self.__pathListing = GafferUI.PathListingWidget(
				self.__LayoutPath( _SectionLayoutItem( "" ), "/" ),
				# listing displays the plug name and automatically sorts based on plug index
				columns = ( GafferUI.PathListingWidget.defaultNameColumn, ),
				displayMode = GafferUI.PathListingWidget.DisplayMode.Tree,
			)

			self.__pathListing.setDragPointer( "" )
			self.__pathListing.setSortable( False )
			self.__pathListing.setHeaderVisible( False )

			with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :

				GafferUI.MenuButton(
					image = "plus.png",
					hasFrame = False,
					menu = GafferUI.Menu(
						definition = Gaffer.WeakMethod( self.__addMenuDefinition )
					)
				)

				self.__deleteButton = GafferUI.Button( image = "minus.png", hasFrame = False )
				self.__deleteButtonClickedConnection = self.__deleteButton.clickedSignal().connect( Gaffer.WeakMethod( self.__deleteButtonClicked ) )

		self.__parent = None # the parent of the plugs we're listing
		self.__dragItem = None
		self.__selectionChangedSignal = Gaffer.Signal1()

		self.__dragEnterConnection = self.__pathListing.dragEnterSignal().connect( Gaffer.WeakMethod( self.__dragEnter ) )
		self.__dragMoveConnection = self.__pathListing.dragMoveSignal().connect( Gaffer.WeakMethod( self.__dragMove ) )
		self.__dragEndConnection = self.__pathListing.dragEndSignal().connect( Gaffer.WeakMethod( self.__dragEnd ) )
		self.__selectionChangedConnection = self.__pathListing.selectionChangedSignal().connect( Gaffer.WeakMethod( self.__selectionChanged ) )
		self.__keyPressConnection = self.keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPress ) )

		self.__nodeMetadataChangedConnection = Gaffer.Metadata.nodeValueChangedSignal().connect( Gaffer.WeakMethod( self.__nodeMetadataChanged ) )
		self.__plugMetadataChangedConnection = Gaffer.Metadata.plugValueChangedSignal().connect( Gaffer.WeakMethod( self.__plugMetadataChanged ) )

	def setPlugParent( self, parent ) :

		assert( isinstance( parent, ( Gaffer.Plug, Gaffer.Node, types.NoneType ) ) )

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

	# Selection can be None, a Plug, or the name of a section.
	def setSelection( self, selection ) :

		self.__updatePathLazily.flush( self )

		def findPlugPath( path, plug ) :

			item = path.item()
			if isinstance( item, _PlugLayoutItem ) and item.plug.isSame( plug ) :
				return path
			else :
				for child in path.children() :
					r = findPlugPath( child, plug )
					if r is not None :
						return r
				return None

		if isinstance( selection, Gaffer.Plug ) :
			path = findPlugPath( self.__pathListing.getPath(), selection )
			if path is None :
				self.__pathListing.setSelectedPaths( [] )
			else :
				self.__pathListing.setSelectedPaths( [ path ] )
		elif isinstance( selection, basestring ) :
			path = self.__pathListing.getPath().copy()
			path[:] = selection.split( "." )
			self.__pathListing.setSelectedPaths( [ path ] )
		else :
			assert( selection is None )
			self.__pathListing.setSelectedPaths( [] )

	def getSelection( self ) :

		item = self.__selectedItem()
		if item is None :
			return None
		elif isinstance( item, _PlugLayoutItem ) :
			return item.plug
		elif isinstance( item, _SectionLayoutItem ) :
			return item.fullName()
		else :
			return None

	def selectionChangedSignal( self ) :

		return self.__selectionChangedSignal

	# Updates the path we show in the listing by building a layout based
	# on the metadata.
	def __updatePath( self ) :

		if self.__parent is None :
			# we have nothing to show - early out.
			self.__pathListing.setPath( self.__LayoutPath( _SectionLayoutItem( "" ), "/" ) )
			return

		def section( rootLayoutItem, sectionPath ) :

			sectionItem = rootLayoutItem
			if sectionPath != "" :
				for sectionName in sectionPath.split( "." ) :
					childSectionItem = sectionItem.child( sectionName )
					if childSectionItem is None :
						childSectionItem = _SectionLayoutItem( sectionName )
						sectionItem.append( childSectionItem )
					sectionItem = childSectionItem

			return sectionItem

		layout = _SectionLayoutItem( "" )
		for sectionPath in GafferUI.PlugLayout.layoutSections( self.__parent ) :
			if sectionPath == "User" and isinstance( self.__parent, Gaffer.Node ) :
				continue
			sectionItem = section( layout, sectionPath )
			for plug in GafferUI.PlugLayout.layoutOrder( self.__parent, section = sectionPath ) :
				sectionItem.append( _PlugLayoutItem( plug ) )

		emptySections = _metadata( self.getPlugParent(), "uiEditor:emptySections" )
		emptySectionIndices = _metadata( self.getPlugParent(), "uiEditor:emptySectionIndices" )
		if emptySections and emptySectionIndices :
			for sectionPath, sectionIndex in zip( emptySections, emptySectionIndices ) :
				parentPath, unused, sectionName = sectionPath.rpartition( "." )
				parentSection = section( layout, parentPath )
				if parentSection.child( sectionName ) is None :
					parentSection.insert( sectionIndex, _SectionLayoutItem( sectionName ) )

		expandedPaths = self.__pathListing.getExpandedPaths()
		self.__pathListing.setPath( self.__LayoutPath( layout, "/" ) )
		self.__pathListing.setExpandedPaths( expandedPaths )

	@GafferUI.LazyMethod()
	def __updatePathLazily( self ) :

		self.__updatePath()

	# Updates the metadata that controls the plug layout from the layout
	# we show in the listing.
	def __updateMetadata( self ) :

		# Because sections only really exist by virtue of being requested
		# by a plug, we must store empty sections separately for ourselves.

		emptySections = IECore.StringVectorData()
		emptySectionIndices = IECore.IntVectorData()
		def walk( layoutItem, path = "", index = 0 ) :

			for childItem in layoutItem :
				if isinstance( childItem, _PlugLayoutItem ) :
					Gaffer.Metadata.registerPlugValue( childItem.plug, "layout:section", path )
					Gaffer.Metadata.registerPlugValue( childItem.plug, "layout:index", index )
					index += 1
				elif isinstance( childItem, _SectionLayoutItem ) :
					childPath = path + "." + childItem.name() if path else childItem.name()
					if len( childItem ) :
						index = walk( childItem, childPath, index )
					else :
						emptySections.append( childPath )
						emptySectionIndices.append( layoutItem.index( childItem ) )

			return index

		with Gaffer.BlockedConnection( self.__plugMetadataChangedConnection ) :
			walk( self.__pathListing.getPath().copy().setFromString( "/" ).item() )
			_registerMetadata( self.getPlugParent(), "uiEditor:emptySections", emptySections )
			_registerMetadata( self.getPlugParent(), "uiEditor:emptySectionIndices", emptySectionIndices )

	def __childAddedOrRemoved( self, parent, child ) :

		assert( parent.isSame( self.__parent ) )

		self.__updateChildNameChangedConnection( child )
		self.__updatePathLazily()

	def __childNameChanged( self, child ) :

		selection = self.getSelection()
		self.__updatePath()
		if isinstance( selection, Gaffer.Plug ) and child.isSame( selection ) :
			# because the plug's name has changed. the path needed to
			# keep it selected is different too, so we have to manually
			# restore the selection.
			self.setSelection( selection )

	def __updateChildNameChangedConnection( self, child ) :

		if self.__parent.isSame( child.parent() ) :
			if child not in self.__childNameChangedConnections :
				self.__childNameChangedConnections[child] = child.nameChangedSignal().connect( Gaffer.WeakMethod( self.__childNameChanged ) )
		else :
			if child in self.__childNameChangedConnections :
				del self.__childNameChangedConnections[child]

	def __dragEnter( self, listing, event ) :

		# accept the drag if it originates with us,
		# so __dragMove and __drop can implement
		# drag and drop reordering of plugs.
		if event.sourceWidget is not self.__pathListing :
			return False
		if not isinstance( event.data, IECore.StringVectorData ) :
			return False

		dragPath = self.__pathListing.getPath().copy().setFromString( event.data[0] )
		self.__dragItem = dragPath.item()

		# dragging around entire open sections is a bit confusing, so don't
		self.__pathListing.setPathExpanded( dragPath, False )

		return True

	def __dragMove( self, listing, event ) :

		if self.__dragItem is None :
			return False

		# update our layout structure to reflect the drag
		#################################################

		# find newParent and newIndex - variables specifying
		# the new location for the dragged item.
		targetPath = self.__pathListing.pathAt( event.line.p0 )
		if targetPath is not None :
			targetItem = targetPath.item()
			if targetItem is not None :
				if isinstance( targetItem, _SectionLayoutItem ) and self.__pathListing.getPathExpanded( targetPath ) and targetItem.parent() is self.__dragItem.parent() :
					newParent = targetItem
					newIndex = 0
				else :
					newParent = targetItem.parent()
					newIndex = newParent.index( targetItem )
			else :
				# target is a placeholder added into an empty
				# section by __LayoutPath._children().
				newParent = targetPath.copy().truncateUntilValid().item()
				newIndex = 0
		else :
			# drag has gone above or below all listed items
			newParent = self.__pathListing.getPath().rootItem()
			newIndex = 0 if event.line.p0.y < 1 else len( newParent )

		# skip any attempted circular reparenting

		if newParent is self.__dragItem or self.__dragItem.isAncestorOf( newParent ) :
			return True

		# disallow drags that would place a plug below a section

		firstNonPlugIndex = next(
			( x[0] for x in enumerate( newParent ) if not isinstance( x[1], _PlugLayoutItem ) ),
			len( newParent )
		)
		if self.__dragItem.parent() is newParent and newParent.index( self.__dragItem ) < firstNonPlugIndex :
			firstNonPlugIndex -= 1

		if isinstance( self.__dragItem, _PlugLayoutItem ) :
			if newIndex > firstNonPlugIndex :
				return True
		else :
			if newIndex < firstNonPlugIndex :
				newIndex = max( newIndex, firstNonPlugIndex )

		self.__dragItem.parent().remove( self.__dragItem )
		newParent.insert( newIndex, self.__dragItem )

		# let the listing know we've been monkeying behind the scenes.
		# we need to update the selection, because when we reparented
		# the drag item its path will have changed.
		##############################################################

		self.__pathListing.getPath().pathChangedSignal()( self.__pathListing.getPath() )

		selection = self.__pathListing.getPath().copy()
		selection[:] = self.__dragItem.fullName().split( "." )
		self.__pathListing.setSelectedPaths( [ selection ], scrollToFirst = False, expandNonLeaf = False )

		return True

	def __dragEnd( self, listing, event ) :

		if self.__dragItem is None :
			return False

		with Gaffer.UndoContext( self.__parent.ancestor( Gaffer.ScriptNode ) ) :
			self.__updateMetadata()
		self.__dragItem = None

		return True

	def __selectionChanged( self, pathListing ) :

		self.__deleteButton.setEnabled( bool( pathListing.getSelectedPaths() ) )
		self.__selectionChangedSignal( self )

	def __deleteButtonClicked( self, button ) :

		self.__deleteSelected()

	def __nodeMetadataChanged( self, nodeTypeId, key, node ) :

		if self.__parent is None :
			return

		if node is not None and not self.__parent.isSame( node ) :
			return

		if not self.__parent.isInstanceOf( nodeTypeId ) :
			return

		if key in ( "uiEditor:emptySections", "uiEditor:emptySectionIndices" ) :
			self.__updatePathLazily()

	def __plugMetadataChanged( self, nodeTypeId, plugPath, key, plug ) :

		if self.__parent is None :
			return

		if plug is not None and not self.__parent.isSame( plug.parent() ) :
			return

		node = self.__parent.node() if isinstance( self.__parent, Gaffer.Plug ) else self.__parent
		if not node.isInstanceOf( nodeTypeId ) :
			return

		if key in ( "layout:index", "layout:section", "uiEditor:emptySections", "uiEditor:emptySectionIndices" ) :
			self.__updatePathLazily()

	def __keyPress( self, widget, event ) :

		assert( widget is self )

		if event.key == "Backspace" or event.key == "Delete" :
			self.__deleteSelected()

			return True

		return False

	def __addMenuDefinition( self ) :

		m = IECore.MenuDefinition()

		m.append( "/Add Plug/Bool", { "command" : functools.partial( Gaffer.WeakMethod( self.__addPlug ), Gaffer.BoolPlug ) } )
		m.append( "/Add Plug/Float", { "command" : functools.partial( Gaffer.WeakMethod( self.__addPlug ), Gaffer.FloatPlug ) } )
		m.append( "/Add Plug/Int", { "command" : functools.partial( Gaffer.WeakMethod( self.__addPlug ), Gaffer.IntPlug ) } )
		m.append( "/Add Plug/NumericDivider", { "divider" : True } )

		m.append( "/Add Plug/String", { "command" : functools.partial( Gaffer.WeakMethod( self.__addPlug ), Gaffer.StringPlug ) } )
		m.append( "/Add Plug/StringDivider", { "divider" : True } )

		m.append( "/Add Plug/V2i", { "command" : functools.partial( Gaffer.WeakMethod( self.__addPlug ), Gaffer.V2iPlug ) } )
		m.append( "/Add Plug/V3i", { "command" : functools.partial( Gaffer.WeakMethod( self.__addPlug ), Gaffer.V3iPlug ) } )
		m.append( "/Add Plug/V2f", { "command" : functools.partial( Gaffer.WeakMethod( self.__addPlug ), Gaffer.V2fPlug ) } )
		m.append( "/Add Plug/V3f", { "command" : functools.partial( Gaffer.WeakMethod( self.__addPlug ), Gaffer.V3fPlug  ) } )
		m.append( "/Add Plug/VectorDivider", { "divider" : True } )

		m.append( "/Add Plug/Color3f", { "command" : functools.partial( Gaffer.WeakMethod( self.__addPlug ), Gaffer.Color3fPlug ) } )
		m.append( "/Add Plug/Color4f", { "command" : functools.partial( Gaffer.WeakMethod( self.__addPlug ), Gaffer.Color4fPlug ) } )

		m.append( "/Add Plug Divider", { "divider" : True } )

		m.append( "/Add Section", { "command" : Gaffer.WeakMethod( self.__addSection ) } )

		return m

	def __addPlug( self, plugType ) :

		plug = plugType( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		_registerMetadata( plug, "nodule:type", "" )

		parentItem = self.__selectedItem()
		if parentItem is not None :
			while not isinstance( parentItem, _SectionLayoutItem ) :
				parentItem = parentItem.parent()
		else :
			parentItem = self.__pathListing.getPath().rootItem()
			parentItem = next(
				( c for c in parentItem if isinstance( c, _SectionLayoutItem ) ),
				parentItem
			)

		_registerMetadata( plug, "layout:section", parentItem.fullName() )

		with Gaffer.UndoContext( self.__parent.ancestor( Gaffer.ScriptNode ) ) :
			self.getPlugParent().addChild( plug )

		self.__updatePathLazily.flush( self )
		self.setSelection( plug )

	def __addSection( self ) :

		rootItem = self.__pathListing.getPath().rootItem()
		existingSectionNames = set( c.name() for c in rootItem if isinstance( c, _SectionLayoutItem ) )

		name = "New Section"
		index = 1
		while name in existingSectionNames :
			name = "New Section %d" % index
			index += 1

		rootItem.append( _SectionLayoutItem( name ) )

		self.__pathListing.getPath().pathChangedSignal()( self.__pathListing.getPath() )

		with Gaffer.UndoContext( self.__parent.ancestor( Gaffer.ScriptNode ) ) :
			self.__updateMetadata()

		self.__pathListing.setSelectedPaths(
			self.__pathListing.getPath().copy().setFromString( "/" + name )
		)

	def __selectedItem( self ) :

		selectedPaths = self.__pathListing.getSelectedPaths()
		if not len( selectedPaths ) :
			return None

		assert( len( selectedPaths ) == 1 )

		return selectedPaths[0].item()

	def __deleteSelected( self ) :

		selectedItem = self.__selectedItem()
		if selectedItem is None :
			return

		selectedItem.parent().remove( selectedItem )

		def deletePlugsWalk( item ) :

			if isinstance( item, _PlugLayoutItem ) :
				item.plug.parent().removeChild( item.plug )
			else :
				for childItem in item :
					deletePlugsWalk( childItem )

		with Gaffer.UndoContext( self.__parent.ancestor( Gaffer.ScriptNode ) ) :
			deletePlugsWalk( selectedItem )
			self.__updateMetadata()

##########################################################################
# _PlugEditor. This provides a panel for editing a specific plug's name,
# description, etc.
##########################################################################

class _PlugEditor( GafferUI.Widget ) :

	def __init__( self, **kw ) :

		grid = GafferUI.GridContainer( spacing = 4, borderWidth = 8 )
		GafferUI.Widget.__init__( self, grid, **kw )

		self.__metadataWidgets = []

		with grid :

			GafferUI.Label(
				"Name",
				parenting = {
					"index" : ( 0, 0 ),
					"alignment" : ( GafferUI.HorizontalAlignment.Right, GafferUI.VerticalAlignment.Center )
				}
			)

			self.__nameWidget = GafferUI.NameWidget( None, parenting = { "index" : ( 1, 0 ) } )

			GafferUI.Label(
				"Description",
				parenting = {
					"index" : ( 0, 1 ),
					"alignment" : ( GafferUI.HorizontalAlignment.Right, GafferUI.VerticalAlignment.Top )
				}
			)

			self.__metadataWidgets.append(
				_MultiLineStringMetadataWidget(
					key = "description",
					parenting = { "index" : ( 1, 1 ) }
				)
			)

			GafferUI.Label(
				"Divider",
				parenting = {
					"index" : ( 0, 2 ),
					"alignment" : ( GafferUI.HorizontalAlignment.Right, GafferUI.VerticalAlignment.Center )
				}
			)

			self.__metadataWidgets.append(
				_BoolMetadataWidget(
					key = "divider",
					parenting = {
						"index" : ( 1, 2 ),
						"alignment" : ( GafferUI.HorizontalAlignment.Left, GafferUI.VerticalAlignment.Center )
					}
				)
			)

		self.__plug = None

	def setPlug( self, plug ) :

		self.__plug = plug

		self.__nameWidget.setGraphComponent( self.__plug )
		for widget in self.__metadataWidgets :
			widget.setTarget( self.__plug )

		self.setEnabled( self.__plug is not None )

	def getPlug( self ) :

		return self.__plug

##########################################################################
# _SectionEditor. This provides a panel for editing the details of
# a specific section.
##########################################################################

## \todo Add support for specifying section summaries.
class _SectionEditor( GafferUI.Widget ) :

	def __init__( self, **kw ) :

		grid = GafferUI.GridContainer( spacing = 4, borderWidth = 8 )
		GafferUI.Widget.__init__( self, grid, **kw )

		with grid :

			GafferUI.Label(
				"Name",
				parenting = {
					"index" : ( 0, 0 ),
					"alignment" : ( GafferUI.HorizontalAlignment.Right, GafferUI.VerticalAlignment.Center )
				}
			)

			self.__nameWidget = GafferUI.TextWidget( parenting = { "index" : ( 1, 0 ) } )
			self.__nameWidgetEditingFinishedConnection = self.__nameWidget.editingFinishedSignal().connect( Gaffer.WeakMethod( self.__nameWidgetEditingFinished ) )

		self.__section = ""
		self.__plugParent = None
		self.__nameChangedSignal = Gaffer.Signal3()

	def setPlugParent( self, plugParent ) :

		self.__plugParent = plugParent

	def getPlugParent( self ) :

		return self.__plugParent

	def setSection( self, section ) :

		assert( isinstance( section, basestring ) )

		self.__section = section
		self.__nameWidget.setText( section.rpartition( "." )[-1] )

	def getSection( self ) :

		return self.__section

	def nameChangedSignal( self ) :

		return self.__nameChangedSignal

	def __nameWidgetEditingFinished( self, nameWidget ) :

		oldSectionPath = self.__section.split( "." )
		newSectionPath = oldSectionPath[:]
		newSectionPath[-1] = nameWidget.getText().replace( ".", "" )

		if oldSectionPath == newSectionPath :
			return

		def newSection( oldSection ) :

			s = oldSection.split( "." )
			if s[:len(oldSectionPath)] == oldSectionPath :
				s[:len(oldSectionPath)] = newSectionPath
				return ".".join( s )
			else :
				return oldSection

		with Gaffer.UndoContext( self.__plugParent.ancestor( Gaffer.ScriptNode ) ) :
			for plug in self.__plugParent.children( Gaffer.Plug ) :
				s = _metadata( plug, "layout:section" )
				if s is not None :
					_registerMetadata( plug, "layout:section", newSection( s ) )

			emptySections = _metadata( self.getPlugParent(), "uiEditor:emptySections" )
			if emptySections :
				for i in range( 0, len( emptySections ) ) :
					emptySections[i] = newSection( emptySections[i] )
				_registerMetadata( self.getPlugParent(), "uiEditor:emptySections", emptySections )

		self.setSection( ".".join( newSectionPath ) )
		self.nameChangedSignal()( self, ".".join( oldSectionPath ), ".".join( newSectionPath ) )

##########################################################################
# MetadataValueWidgets. These display metadata values, allowing the user
# to edit them.
##########################################################################

class _MetadataWidget( GafferUI.Widget ) :

	def __init__( self, topLevelWidget, key, target = None, **kw ) :

		GafferUI.Widget.__init__( self, topLevelWidget, **kw )

		self.__key = key
		self.__target = None

		self.setTarget( target )

	def setTarget( self, target ) :

		assert( isinstance( target, ( Gaffer.Node, Gaffer.Plug, type( None ) ) ) )

		self.__target = target
		self.setEnabled( self.__target is not None )

		if isinstance( self.__target, Gaffer.Node ) :
			self.__metadataChangedConnection = Gaffer.Metadata.nodeValueChangedSignal().connect(
				Gaffer.WeakMethod( self.__nodeMetadataChanged )
			)
		elif isinstance( self.__target, Gaffer.Plug ) :
			self.__metadataChangedConnection = Gaffer.Metadata.plugValueChangedSignal().connect(
				Gaffer.WeakMethod( self.__plugMetadataChanged )
			)
		else :
			self.__metadataChangedConnection = None

		self.__update()

	def getTarget( self ) :

		return self.__target

	## Must be implemented in derived classes to update
	# the widget from the value.
	def _updateFromValue( self, value ) :

		raise NotImplementedError

	## Must be called by derived classes to update
	# the Metadata value when the widget value changes.
	def _updateFromWidget( self, value ) :

		if self.__target is None :
			return

		with Gaffer.UndoContext( self.__target.ancestor( Gaffer.ScriptNode ) ) :
			_registerMetadata( self.__target, self.__key, value )

	def __update( self ) :

		if isinstance( self.__target, Gaffer.Node ) :
			self._updateFromValue( Gaffer.Metadata.nodeValue( self.__target, self.__key ) )
		elif isinstance( self.__target, Gaffer.Plug ) :
			self._updateFromValue( Gaffer.Metadata.plugValue( self.__target, self.__key ) )
		else :
			self._updateFromValue( None )

	def __nodeMetadataChanged( self, nodeTypeId, key, node ) :

		if self.__key != key :
			return
		if node is not None and not node.isSame( self.__target ) :
			return
		if not self.__target.isInstanceOf( nodeTypeId ) :
			return

		self.__update()

	def __plugMetadataChanged( self, nodeTypeId, plugPath, key, plug ) :

		if self.__key != key :
			return
		if plug is not None and not plug.isSame( self.__target ) :
			return
		if not self.__target.node().isInstanceOf( nodeTypeId ) :
			return
		if not Gaffer.match( self.__target.relativeName( self.__target.node() ), plugPath ) :
			return

		self.__update()

class _BoolMetadataWidget( _MetadataWidget ) :

	def __init__( self, key, target = None, **kw ) :

		self.__boolWidget = GafferUI.BoolWidget()
		_MetadataWidget.__init__( self, self.__boolWidget, key, target, **kw )

		self.__stateChangedConnection = self.__boolWidget.stateChangedSignal().connect(
			Gaffer.WeakMethod( self.__stateChanged )
		)

	def _updateFromValue( self, value ) :

		self.__boolWidget.setState( value if value is not None else False )

	def __stateChanged( self, *unused ) :

		self._updateFromWidget( self.__boolWidget.getState() )

class _MultiLineStringMetadataWidget( _MetadataWidget ) :

	def __init__( self, key, target = None, **kw ) :

		self.__textWidget = GafferUI.MultiLineTextWidget()
		_MetadataWidget.__init__( self, self.__textWidget, key, target, **kw )

		self.__editingFinishedConnection = self.__textWidget.editingFinishedSignal().connect(
			Gaffer.WeakMethod( self.__editingFinished )
		)

	def _updateFromValue( self, value ) :

		self.__textWidget.setText( value if value is not None else "" )

	def __editingFinished( self, *unused ) :

		self._updateFromWidget( self.__textWidget.getText() )

class _ColorSwatchMetadataWidget( _MetadataWidget ) :

	def __init__( self, key, target = None, **kw ) :

		self.__swatch = GafferUI.ColorSwatch( useDisplayTransform = False )

		_MetadataWidget.__init__( self, self.__swatch, key, target, **kw )

		self.__swatch._qtWidget().setMaximumHeight( 20 )
		self.__swatch._qtWidget().setMaximumWidth( 40 )
		self.__value = None

		self.__buttonReleaseConnection = self.__swatch.buttonReleaseSignal().connect( Gaffer.WeakMethod( self.__buttonRelease ) )

	def _updateFromValue( self, value ) :

		if value is not None :
			self.__swatch.setColor( value )
		else :
			self.__swatch.setColor( IECore.Color4f( 0, 0, 0, 0 ) )

		self.__value = value

	def __buttonRelease( self, swatch, event ) :

		if event.button != event.Buttons.Left :
			return False

		color = self.__value if self.__value is not None else IECore.Color3f( 1 )
		dialogue = GafferUI.ColorChooserDialogue( color = color, useDisplayTransform = False )
		color = dialogue.waitForColor( parentWindow = self.ancestor( GafferUI.Window ) )

		if color is not None :
			self._updateFromWidget( color )

# Metadata utility methods.
# \todo We should change the Metadata API to provide overloads
# rather than functions with distinct names, so we don't have to
# do this hoop jumping ourselves.
##########################################################################

def _registerMetadata( target, name, value ) :

	if isinstance( target, Gaffer.Node ) :
		Gaffer.Metadata.registerNodeValue( target, name, value )
	else :
		Gaffer.Metadata.registerPlugValue( target, name, value )

def _metadata( target, name ) :

	if isinstance( target, Gaffer.Node ) :
		return Gaffer.Metadata.nodeValue( target, name )
	else :
		return Gaffer.Metadata.plugValue( target, name )
