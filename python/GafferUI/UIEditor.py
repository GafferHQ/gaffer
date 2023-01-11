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
import six
import collections
import imath
import inspect
import string

import IECore

import Gaffer
import GafferUI
from . import MetadataWidget

## The UIEditor class allows the user to edit the interfaces for nodes.
class UIEditor( GafferUI.NodeSetEditor ) :

	def __init__( self, scriptNode, **kw ) :

		self.__frame = GafferUI.Frame( borderWidth = 0, borderStyle = GafferUI.Frame.BorderStyle.None_ )

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
			with GafferUI.ListContainer( spacing = 4, borderWidth = 8, parenting = { "label" : "Node" } ) as self.__nodeTab :

				with _Row() :

					_Label( "Name" )

					self.__nodeNameWidget = GafferUI.NameWidget( None )

				with _Row() :

					_Label( "Description", parenting = { "verticalAlignment" : GafferUI.ListContainer.VerticalAlignment.Top } )

					self.__nodeMetadataWidgets.append(
						MetadataWidget.MultiLineStringMetadataWidget( key = "description" )
					)

				with _Row() :

					_Label( "Documentation URL" )

					self.__nodeMetadataWidgets.append(
						MetadataWidget.StringMetadataWidget( key = "documentation:url" )
					)

				with _Row() :

					_Label( "Color" )

					self.__nodeMetadataWidgets.append(
						MetadataWidget.ColorSwatchMetadataWidget( key = "nodeGadget:color", defaultValue = imath.Color3f( 0.4 ) )
					)

				with _Row() as self.__iconRow :

					_Label( "Icon" )

					self.__nodeMetadataWidgets.append(
						MetadataWidget.FileSystemPathMetadataWidget( key = "icon" )
					)

				with _Row() as self.__plugAddButtons :

					_Label( "Plug Creators" )

					for side in ( "Top", "Bottom", "Left", "Right" ) :
						_Label( side )._qtWidget().setFixedWidth( 40 )
						self.__nodeMetadataWidgets.append( MetadataWidget.BoolMetadataWidget(
							key = "noduleLayout:customGadget:addButton%s:visible" % side,
							defaultValue = True
						) )

			# Plugs tab
			with GafferUI.SplitContainer( orientation=GafferUI.SplitContainer.Orientation.Horizontal, borderWidth = 8, parenting = { "label" : "Plugs" } ) as self.__plugTab :

				self.__plugListing = _PlugListing()
				self.__plugListing.selectionChangedSignal().connect( Gaffer.WeakMethod( self.__plugListingSelectionChanged ), scoped = False )

				with GafferUI.TabbedContainer() as self.__plugAndSectionEditorsContainer :

					self.__plugEditor = _PlugEditor()
					self.__sectionEditor = _SectionEditor()
					self.__sectionEditor.nameChangedSignal().connect( Gaffer.WeakMethod( self.__sectionEditorNameChanged ), scoped = False )

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
	def appendNodeContextMenuDefinitions( cls, graphEditor, node, menuDefinition ) :

		menuDefinition.append( "/UIEditorDivider", { "divider" : True } )
		menuDefinition.append(
			"/Set Color...",
			{
				"command" : functools.partial( cls.__setColor, node = node ),
				"active" : not Gaffer.MetadataAlgo.readOnly( node ),
			}
		)

		nodeGadgetTypes = Gaffer.Metadata.value( node, "uiEditor:nodeGadgetTypes" )
		if nodeGadgetTypes :
			nodeGadgetTypes = set( nodeGadgetTypes )
			if nodeGadgetTypes == { "GafferUI::AuxiliaryNodeGadget", "GafferUI::StandardNodeGadget" } :
				nodeGadgetType = Gaffer.Metadata.value( node, "nodeGadget:type" ) or "GafferUI::StandardNodeGadget"
				menuDefinition.append(
					"/Show Name",
					{
						"command" : functools.partial( cls.__setNameVisible, node ),
						"checkBox" : nodeGadgetType == "GafferUI::StandardNodeGadget",
						"active" : not Gaffer.MetadataAlgo.readOnly( node ),
					}
				)
			else :
				# We want to present the options above as a simple "Show Name" checkbox, and haven't yet
				# decided how to present other combinations of allowable gadgets.
				IECore.msg( IECore.Msg.Level.Warning, "UIEditor", 'Unknown combination of "uiEditor:nodeGadgetTypes"' )

	@classmethod
	def appendNodeEditorToolMenuDefinitions( cls, nodeEditor, node, menuDefinition ) :

		menuDefinition.append( "/Edit UI Divider", { "divider" : True } )

		menuDefinition.append(
			"/Edit UI...",
			{
				"command" : functools.partial( GafferUI.UIEditor.acquire, node ),
				"active" : (
					( isinstance( node, Gaffer.Box ) or nodeEditor.nodeUI().plugValueWidget( node["user"] ) is not None ) and
					not Gaffer.MetadataAlgo.readOnly( node )
				)
			}
		)

	## Registers a custom PlugValueWidget type for a plug type, so it can be selected in the UIEditor
	# label: String with the label to be displayed for this widget.
	# plugType: Gaffer.Plug class that can use the widget being registered.
	# metadata: String with associated metadata for the widget. Usually the python identifier for the widget (ex: "GafferUI.BoolPlugValueWidget").
	@classmethod
	def registerPlugValueWidget( cls, label, plugType, metadata ) :

		# simply calls protected _PlugEditor implementation
		_PlugEditor.registerPlugValueWidget( label, plugType, metadata )

	## Register additional metadata for PlugValueWidgets
	# label: string with the label to be displayed for this widget
	# plugValueWidgetType: string with the "plugValueWidget:type" metadata value where this settings applies, or a pattern for it.
	# widgetCreator: callable that receives the plug and returns a MetadataWidget (or another widget) to edit the metadata
	@classmethod
	def registerWidgetSetting( cls, label, plugValueWidgetType, widgetCreator ) :

		# simply calls protected _PlugEditor implementation
		_PlugEditor.registerWidgetSetting( label, plugValueWidgetType, widgetCreator )

	## Utility to quickly register widgets to edit metadata for PlugValueWidgets
	# It uses the defaultValue provided in order to determine the appropriate widget to be used
	# label: string with the label to be displayed for this widget
	# plugValueWidgetType: string with the "plugValueWidget:type" metadata value where this settings applies, or a pattern for it.
	# key: metadata key to be set by the widget
	# defaultValue: default value for the metadata
	@classmethod
	def registerWidgetMetadata( cls, label, plugValueWidgetType, key, defaultValue ) :

		if isinstance( defaultValue, bool ) :

			widgetClass = MetadataWidget.BoolMetadataWidget

		elif isinstance( defaultValue, six.string_types ) :

			widgetClass = MetadataWidget.StringMetadataWidget

		elif isinstance( defaultValue, imath.Color4f ) :

			widgetClass = MetadataWidget.ColorSwatchMetadataWidget

		else :

			raise Exception( "Could not determine the widget to use from defaultValue: {}.".format( repr( defaultValue ) ) )

		cls.registerWidgetSetting(
			label,
			plugValueWidgetType,
			lambda plug : widgetClass( key, target=plug, defaultValue=defaultValue )
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
		self.__plugAddButtons.setVisible( False )

		if self.__node is None :
			self.__plugListing.setPlugParent( None )
			self.__sectionEditor.setPlugParent( None )
		else :
			plugParent = self.__node["user"]
			if isinstance( self.__node, Gaffer.Box ) :
				# For Boxes we want the user to edit the plugs directly
				# parented to the Box, because that is where promoted plugs go,
				# and because we want to leave the "user" plug empty so that it
				# is available for use by the user on Reference nodes once a Box has
				# been exported and referenced.
				plugParent = self.__node
				self.__plugAddButtons.setVisible( True )
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
		elif isinstance( selection, six.string_types ) :
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

		color = Gaffer.Metadata.value( node, "nodeGadget:color" ) or imath.Color3f( 1 )
		dialogue = GafferUI.ColorChooserDialogue( color = color, useDisplayTransform = False )
		color = dialogue.waitForColor( parentWindow = menu.ancestor( GafferUI.Window ) )
		if color is not None :
			with Gaffer.UndoScope( node.ancestor( Gaffer.ScriptNode ) ) :
				Gaffer.Metadata.registerValue( node, "nodeGadget:color", color )

	@staticmethod
	def __setNameVisible( node, nameVisible ) :

		with Gaffer.UndoScope( node.ancestor( Gaffer.ScriptNode ) ) :
			Gaffer.Metadata.registerValue(
				node, "nodeGadget:type",
				"GafferUI::StandardNodeGadget" if nameVisible else "GafferUI::AuxiliaryNodeGadget"
			)

GafferUI.Editor.registerType( "UIEditor", UIEditor )

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
	menuDefinition.append( "/Edit UI...",
		{
			"command" : functools.partial( __editPlugUI, node, plug ),
			"active" : not plugValueWidget.getReadOnly() and not Gaffer.MetadataAlgo.readOnly( plug )
		}
	)

GafferUI.PlugValueWidget.popupMenuSignal().connect( __plugPopupMenu, scoped = False )

##########################################################################
# Simple fixed width label and row classes
##########################################################################

class _Label( GafferUI.Label ) :

	def __init__( self, *args, **kw ) :

		GafferUI.Label.__init__(
			self,
			horizontalAlignment = GafferUI.Label.HorizontalAlignment.Right,
			*args, **kw
		)

		self._qtWidget().setFixedWidth( 110 )

class _Row( GafferUI.ListContainer ) :

	def __init__( self, *args, **kw ) :

		GafferUI.ListContainer.__init__( self, GafferUI.ListContainer.Orientation.Horizontal, spacing = 4, *args, **kw )

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

		def isLeaf( self, canceller = None ) :

			return not isinstance( self.item(), _SectionLayoutItem )

		def isValid( self, canceller = None ) :

			return self.item() is not None

		def _children( self, canceller ) :

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
		GafferUI.Widget.__init__( self, column, **kw )

		# We don't have a way to do this with Widget directly at present, this
		# stops the preset name/value fields being off-screen.
		column._qtWidget().setMinimumWidth( 650 )

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
				self.__deleteButton.clickedSignal().connect( Gaffer.WeakMethod( self.__deleteButtonClicked ), scoped = False )

		self.__parent = None # the parent of the plugs we're listing
		self.__dragItem = None
		self.__selectionChangedSignal = Gaffer.Signals.Signal1()

		self.__pathListing.dragEnterSignal().connect( Gaffer.WeakMethod( self.__dragEnter ), scoped = False )
		self.__pathListing.dragMoveSignal().connect( Gaffer.WeakMethod( self.__dragMove ), scoped = False )
		self.__pathListing.dragEndSignal().connect( Gaffer.WeakMethod( self.__dragEnd ), scoped = False )
		self.__pathListing.selectionChangedSignal().connect( Gaffer.WeakMethod( self.__selectionChanged ), scoped = False )
		self.keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPress ), scoped = False )

	def setPlugParent( self, parent ) :

		assert( isinstance( parent, ( Gaffer.Plug, Gaffer.Node, type( None ) ) ) )

		self.__parent = parent

		self.__childAddedConnection = None
		self.__childRemovedConnection = None
		self.__childNameChangedConnections = {}
		self.__metadataChangedConnections = []

		if self.__parent is not None :

			self.__childAddedConnection = self.__parent.childAddedSignal().connect(
				Gaffer.WeakMethod( self.__childAddedOrRemoved ), scoped = True
			)
			self.__childRemovedConnection = self.__parent.childRemovedSignal().connect(
				Gaffer.WeakMethod( self.__childAddedOrRemoved ), scoped = True
			)

			node = self.__parent if isinstance( self.__parent, Gaffer.Node ) else self.__parent.node()
			self.__metadataChangedConnections = [
				Gaffer.Metadata.nodeValueChangedSignal( node ).connect( Gaffer.WeakMethod( self.__nodeMetadataChanged ), scoped = True ),
				Gaffer.Metadata.plugValueChangedSignal( node ).connect( Gaffer.WeakMethod( self.__plugMetadataChanged ), scoped = True )
			]

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
		elif isinstance( selection, six.string_types ) :
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

		emptySections = Gaffer.Metadata.value( self.getPlugParent(), "uiEditor:emptySections" )
		emptySectionIndices = Gaffer.Metadata.value( self.getPlugParent(), "uiEditor:emptySectionIndices" )
		if emptySections and emptySectionIndices :
			for sectionPath, sectionIndex in zip( emptySections, emptySectionIndices ) :
				parentPath, unused, sectionName = sectionPath.rpartition( "." )
				parentSection = section( layout, parentPath )
				if parentSection.child( sectionName ) is None :
					parentSection.insert( sectionIndex, _SectionLayoutItem( sectionName ) )

		if len( layout ) == 0 and isinstance( self.__parent, Gaffer.Node ) :
			layout.append( _SectionLayoutItem( "Settings" ) )

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
					Gaffer.Metadata.registerValue( childItem.plug, "layout:section", path )
					Gaffer.Metadata.registerValue( childItem.plug, "layout:index", index )
					index += 1
				elif isinstance( childItem, _SectionLayoutItem ) :
					childPath = path + "." + childItem.name() if path else childItem.name()
					if len( childItem ) :
						index = walk( childItem, childPath, index )
					else :
						emptySections.append( childPath )
						emptySectionIndices.append( layoutItem.index( childItem ) )

			return index

		with Gaffer.Signals.BlockedConnection( self.__metadataChangedConnections ) :
			walk( self.__pathListing.getPath().copy().setFromString( "/" ).item() )
			Gaffer.Metadata.registerValue( self.getPlugParent(), "uiEditor:emptySections", emptySections )
			Gaffer.Metadata.registerValue( self.getPlugParent(), "uiEditor:emptySectionIndices", emptySectionIndices )

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
				self.__childNameChangedConnections[child] = child.nameChangedSignal().connect( Gaffer.WeakMethod( self.__childNameChanged ), scoped = True )
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

		with Gaffer.UndoScope( self.__parent.ancestor( Gaffer.ScriptNode ) ) :
			self.__updateMetadata()
		self.__dragItem = None

		return True

	def __selectionChanged( self, pathListing ) :

		self.__deleteButton.setEnabled( bool( pathListing.getSelectedPaths() ) )
		self.__selectionChangedSignal( self )

	def __deleteButtonClicked( self, button ) :

		self.__deleteSelected()

	def __nodeMetadataChanged( self, node, key, reason ) :

		if node != self.__parent :
			return

		if key in ( "uiEditor:emptySections", "uiEditor:emptySectionIndices" ) :
			self.__updatePathLazily()

	def __plugMetadataChanged( self, plug, key, reason ) :

		if ( plug != self.__parent and plug.parent() != self.__parent ) :
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
		m.append( "/Add Plug/ColorDivider", { "divider" : True } )

		for label, plugType in [
			( "Float", Gaffer.FloatVectorDataPlug ),
			( "Int", Gaffer.IntVectorDataPlug ),
			( "NumericDivider", None ),
			( "String", Gaffer.StringVectorDataPlug ),
		] :
			if plugType is not None :
				m.append(
					"/Add Plug/Array/" + label,
					{
						"command" : functools.partial(
							Gaffer.WeakMethod( self.__addPlug ),
							plugCreator = functools.partial( plugType, defaultValue = plugType.ValueType() )
						)
					}
				)
			else :
				m.append( "/Add Plug/Array/" + label, { "divider" : True } )

		m.append( "/Add Plug Divider", { "divider" : True } )

		m.append( "/Add Section", { "command" : Gaffer.WeakMethod( self.__addSection ) } )

		return m

	def __addPlug( self, plugCreator ) :

		plug = plugCreator( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		Gaffer.Metadata.registerValue( plug, "nodule:type", "" )

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

		Gaffer.Metadata.registerValue( plug, "layout:section", parentItem.fullName() )

		with Gaffer.UndoScope( self.__parent.ancestor( Gaffer.ScriptNode ) ) :
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

		with Gaffer.UndoScope( self.__parent.ancestor( Gaffer.ScriptNode ) ) :
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

		with Gaffer.UndoScope( self.__parent.ancestor( Gaffer.ScriptNode ) ) :
			deletePlugsWalk( selectedItem )
			self.__updateMetadata()

##########################################################################
# _PresetsEditor. This provides a ui for editing the presets for a plug.
##########################################################################

class _PresetsEditor( GafferUI.Widget ) :

	def __init__( self, **kw ) :

		row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 8 )
		GafferUI.Widget.__init__( self, row, **kw )

		with row :

			with GafferUI.ListContainer( spacing = 4 ) :

				self.__pathListing = GafferUI.PathListingWidget(
					Gaffer.DictPath( collections.OrderedDict(), "/" ),
					columns = ( GafferUI.PathListingWidget.defaultNameColumn, ),
				)
				self.__pathListing.setDragPointer( "" )
				self.__pathListing.setSortable( False )
				self.__pathListing.setHeaderVisible( False )
				self.__pathListing._qtWidget().setFixedWidth( 200 )
				self.__pathListing._qtWidget().setFixedHeight( 200 )

				self.__pathListing.selectionChangedSignal().connect( Gaffer.WeakMethod( self.__selectionChanged ), scoped = False )
				self.__pathListing.dragEnterSignal().connect( Gaffer.WeakMethod( self.__dragEnter ), scoped = False )
				self.__pathListing.dragMoveSignal().connect( Gaffer.WeakMethod( self.__dragMove ), scoped = False )
				self.__pathListing.dragEndSignal().connect( Gaffer.WeakMethod( self.__dragEnd ), scoped = False )

				with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :

					self.__addButton = GafferUI.Button( image = "plus.png", hasFrame = False )
					self.__addButton.clickedSignal().connect( Gaffer.WeakMethod( self.__addButtonClicked ), scoped = False )

					self.__deleteButton = GafferUI.Button( image = "minus.png", hasFrame = False )
					self.__deleteButton.clickedSignal().connect( Gaffer.WeakMethod( self.__deleteButtonClicked ), scoped = False )

			with GafferUI.ListContainer( spacing = 4 ) as self.__editingColumn :

				GafferUI.Label( "Name" )

				self.__nameWidget = GafferUI.TextWidget()
				self.__nameWidget.editingFinishedSignal().connect( Gaffer.WeakMethod( self.__nameEditingFinished ), scoped = False )

				GafferUI.Spacer( imath.V2i( 4 ), maximumSize = imath.V2i( 4 ) )

				GafferUI.Label( "Value" )

		# We make a UI for editing preset values by copying the plug
		# onto this node and then making a PlugValueWidget for it.
		self.__valueNode = Gaffer.Node( "PresetEditor" )
		self.__valuePlugSetConnection = self.__valueNode.plugSetSignal().connect(
			Gaffer.WeakMethod( self.__valuePlugSet ), scoped = False
		)

	def setPlug( self, plug ) :

		self.__plug = plug

		self.__plugMetadataChangedConnection = None
		del self.__editingColumn[4:]

		plugValueWidget = None
		if self.__plug is not None :
			self.__plugMetadataChangedConnection = Gaffer.Metadata.plugValueChangedSignal( plug.node() ).connect(
				Gaffer.WeakMethod( self.__plugMetadataChanged ),
				scoped = True
			)
			self.__valueNode["presetValue"] = plug.createCounterpart( "presetValue", plug.Direction.In )
			if hasattr( self.__plug, "getValue" ) :
				plugValueWidget = GafferUI.PlugValueWidget.create( self.__valueNode["presetValue"], useTypeOnly = True )

		self.__editingColumn.append( plugValueWidget if plugValueWidget is not None else GafferUI.TextWidget() )

		self.__editingColumn.append( GafferUI.Spacer( imath.V2i( 0 ), parenting = { "expand" : True } ) )

		self.__updatePath()

		self.__addButton.setEnabled( hasattr( self.__plug, "getValue" ) )

	def getPlug( self ) :

		return self.__plug

	def __updatePath( self ) :

		d = self.__pathListing.getPath().dict()
		d.clear()
		if self.__plug is not None :
			for name in Gaffer.Metadata.registeredValues( self.__plug, instanceOnly = True, persistentOnly = True ) :
				if name.startswith( "preset:" ) :
					d[name[7:]] = Gaffer.Metadata.value( self.__plug, name )

		self.__pathListing.getPath().pathChangedSignal()( self.__pathListing.getPath() )

	def __plugMetadataChanged( self, plug, key, reason ) :

		if plug == self.__plug and key.startswith( "preset:" ) :
			self.__updatePath()

	def __selectionChanged( self, listing ) :

		selectedPaths = listing.getSelectedPaths()

		self.__nameWidget.setText( selectedPaths[0][0] if selectedPaths else "" )
		if selectedPaths :
			with Gaffer.Signals.BlockedConnection( self.__valuePlugSetConnection ) :
				self.__valueNode["presetValue"].setValue(
					Gaffer.Metadata.value( self.getPlug(), "preset:" + selectedPaths[0][0] )
				)

		self.__editingColumn.setEnabled( bool( selectedPaths ) )
		self.__deleteButton.setEnabled( bool( selectedPaths ) )

	def __dragEnter( self, listing, event ) :

		if event.sourceWidget is not self.__pathListing :
			return False
		if not isinstance( event.data, IECore.StringVectorData ) :
			return False

		return True

	def __dragMove( self, listing, event ) :

		d = self.__pathListing.getPath().dict()

		srcPath = self.__pathListing.getPath().copy().setFromString( event.data[0] )
		srcIndex = list( d.keys() ).index( srcPath[0] )

		targetPath = self.__pathListing.pathAt( event.line.p0 )
		if targetPath is not None :
			targetIndex = list( d.keys() ).index( targetPath[0] )
		else :
			targetIndex = 0 if event.line.p0.y < 1 else len( d )

		if srcIndex == targetIndex :
			return True

		items = list( d.items() )
		item = items[srcIndex]
		del items[srcIndex]
		items.insert( targetIndex, item )

		d.clear()
		d.update( items )

		self.__pathListing.getPath().pathChangedSignal()( self.__pathListing.getPath() )

		return True

	def __dragEnd( self, listing, event ) :

		d = self.__pathListing.getPath().dict()
		with Gaffer.Signals.BlockedConnection( self.__plugMetadataChangedConnection ) :
			with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
				# reorder by removing everything and reregistering in the order we want
				for item in d.items() :
					Gaffer.Metadata.deregisterValue( self.getPlug(), "preset:" + item[0] )
				for item in d.items() :
					Gaffer.Metadata.registerValue( self.getPlug(), "preset:" + item[0], item[1] )

		self.__updatePath()

		return True

	def __addButtonClicked( self, button ) :

		existingNames = [ p[0] for p in self.__pathListing.getPath().children() ]

		name = "New Preset"
		index = 1
		while name in existingNames :
			name = "New Preset %d" % index
			index += 1

		with Gaffer.UndoScope( self.__plug.ancestor( Gaffer.ScriptNode ) ) :
			Gaffer.Metadata.registerValue( self.__plug, "preset:" + name, self.__plug.getValue() )

		self.__pathListing.setSelectedPaths(
			self.__pathListing.getPath().copy().setFromString( "/" + name )
		)

		self.__nameWidget.grabFocus()
		self.__nameWidget.setSelection( 0, len( name ) )

		return True

	def __deleteButtonClicked( self, button ) :

		paths = self.__pathListing.getPath().children()
		selectedPreset = self.__pathListing.getSelectedPaths()[0][0]
		selectedIndex = [ p[0] for p in paths ].index( selectedPreset )

		with Gaffer.UndoScope( self.__plug.ancestor( Gaffer.ScriptNode ) ) :
			Gaffer.Metadata.deregisterValue( self.__plug, "preset:" + selectedPreset )

		del paths[selectedIndex]
		if len( paths ) :
			self.__pathListing.setSelectedPaths( [ paths[min(selectedIndex,len( paths )-1)] ] )

		return True

	def __nameEditingFinished( self, nameWidget ) :

		selectedPaths = self.__pathListing.getSelectedPaths()
		if not len( selectedPaths ) :
			return True

		oldName = selectedPaths[0][0]
		newName = nameWidget.getText()

		if oldName == newName :
			return True

		if newName == "" :
			# Empty names are not allowed, so revert to previous
			nameWidget.setText( oldName )
			return True

		# Sanitize name. Strictly speaking we should only need to replace '/',
		# but PathListingWidget has a bug handling wildcards in selections, so
		# we replace those too.
		maketrans = str.maketrans if six.PY3 else string.maketrans
		newName = newName.translate( maketrans( "/*?\\[", "_____" ) )

		items = self.__pathListing.getPath().dict().items()
		with Gaffer.Signals.BlockedConnection( self.__plugMetadataChangedConnection ) :
			with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
				# retain order by removing and reregistering everything
				for item in items :
					Gaffer.Metadata.deregisterValue( self.getPlug(), "preset:" + item[0] )
				for item in items :
					Gaffer.Metadata.registerValue( self.getPlug(), "preset:" + (item[0] if item[0] != oldName else newName), item[1] )

		self.__updatePath()
		self.__pathListing.setSelectedPaths( [ self.__pathListing.getPath().copy().setFromString( "/" + newName ) ] )

		return True

	def __valuePlugSet( self, plug ) :

		if not plug.isSame( self.__valueNode["presetValue"] ) :
			return

		selectedPaths = self.__pathListing.getSelectedPaths()
		preset = selectedPaths[0][0]

		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			Gaffer.Metadata.registerValue( self.getPlug(), "preset:" + preset, plug.getValue() )

##########################################################################
# _PlugEditor. This provides a panel for editing a specific plug's name,
# description, etc.
##########################################################################

class _PlugEditor( GafferUI.Widget ) :

	def __init__( self, **kw ) :

		scrolledContainer = GafferUI.ScrolledContainer( horizontalMode = GafferUI.ScrollMode.Never, borderWidth = 8 )
		GafferUI.Widget.__init__( self, scrolledContainer, **kw )

		self.__metadataWidgets = {}

		scrolledContainer.setChild( GafferUI.ListContainer( spacing = 4 ) )
		with scrolledContainer.getChild() :

			with _Row() :

				_Label( "Name" )

				self.__nameWidget = GafferUI.NameWidget( None )

			with _Row() :

				_Label( "Label" )
				self.__metadataWidgets["label"] = MetadataWidget.StringMetadataWidget( key = "label", acceptEmptyString = False )

			with _Row() :

				_Label( "Description", parenting = { "verticalAlignment" : GafferUI.ListContainer.VerticalAlignment.Top } )
				self.__metadataWidgets["description"] = MetadataWidget.MultiLineStringMetadataWidget( key = "description" )
				self.__metadataWidgets["description"].textWidget().setFixedLineHeight( 10 )

			with _Row() :

				_Label( "Widget" )

				self.__widgetMenu = GafferUI.MenuButton(
					menu = GafferUI.Menu( Gaffer.WeakMethod( self.__widgetMenuDefinition ) )
				)

			with GafferUI.Collapsible( "Presets", collapsed = True ) :

				with _Row() :

					_Label( "" )
					self.__presetsEditor = _PresetsEditor()

			with GafferUI.Collapsible( "Widget Settings", collapsed = True ) :

				self.__widgetSettingsContainer = GafferUI.ListContainer( spacing = 4 )

			with GafferUI.Collapsible( "Graph Editor", collapsed = True ) :

				with GafferUI.ListContainer( spacing = 4 ) as self.__graphEditorSection :

					with _Row() :

						_Label( "Gadget" )
						self.__gadgetMenu = GafferUI.MenuButton(
							menu = GafferUI.Menu( Gaffer.WeakMethod( self.__gadgetMenuDefinition ) )
						)

					with _Row() :

						_Label( "Position" )
						self.__metadataWidgets["noduleLayout:section"] = MetadataWidget.MenuMetadataWidget(
							key = "noduleLayout:section",
							labelsAndValues = [
								( "Default", None ),
								( "Top", "top" ),
								( "Bottom", "bottom" ),
								( "Left", "left" ),
								( "Right", "right" ),
							]
						)

					with _Row() :

						_Label( "Color" )
						self.__metadataWidgets["nodule:color"] = MetadataWidget.ColorSwatchMetadataWidget( key = "nodule:color", defaultValue = imath.Color3f( 0.4 ) )

					with _Row() :

						_Label( "Connection Color" )
						self.__metadataWidgets["connectionGadget:color"] = MetadataWidget.ColorSwatchMetadataWidget( key = "connectionGadget:color", defaultValue = imath.Color3f( 0.125 ) )

		self.__plug = None

	def setPlug( self, plug ) :

		self.__plug = plug

		self.__nameWidget.setGraphComponent( self.__plug )
		for widget in self.__metadataWidgets.values() :
			widget.setTarget( self.__plug )

		self.__plugMetadataChangedConnection = None
		if self.__plug is not None :
			self.__plugMetadataChangedConnection = Gaffer.Metadata.plugValueChangedSignal( self.__plug.node() ).connect(
				Gaffer.WeakMethod( self.__plugMetadataChanged ), scoped = True
			)

		self.__updateWidgetMenuText()
		self.__updateWidgetSettings()
		self.__updateGadgetMenuText()
		self.__presetsEditor.setPlug( plug )
		self.__graphEditorSection.setEnabled( self.__plug is not None and self.__plug.parent().isSame( self.__plug.node() ) )

		self.setEnabled( self.__plug is not None )

	def getPlug( self ) :

		return self.__plug

	__plugValueWidgets = {}

	## Registers a custom PlugValueWidget type for a plug type, so it can be selected in the UIEditor
	# label: String with the label to be displayed for this widget.
	# plugType: Gaffer.Plug class that can use the widget being registered.
	# metadata: String with associated metadata for the widget. Usually the python identifier for the widget (ex: "GafferUI.BoolPlugValueWidget").
	@classmethod
	def registerPlugValueWidget( cls, label, plugType, metadata ) :

		if plugType not in cls.__plugValueWidgets :
			cls.__plugValueWidgets[plugType] = {}

		cls.__plugValueWidgets[plugType][label] = metadata

	__widgetSettings = []

	## Register additional metadata for PlugValueWidgets
	# label: string with the label to be displayed for this widget
	# plugValueWidgetType: string with the "plugValueWidget:type" metadata value where this settings applies, or a pattern for it.
	# widgetCreator: callable that receives the plug and returns a MetadataWidget (or another widget) to edit the metadata
	@classmethod
	def registerWidgetSetting( cls, label, plugValueWidgetType, widgetCreator ) :

		cls.__widgetSettings.append( ( label, plugValueWidgetType, widgetCreator ) )

	## Returns a dictionary with the registered PlugValueWidgets for the given plug object or type
	# the dictionary keys will be labels, and the values strings with the widget metadata
	@classmethod
	def __registeredPlugValueWidgets( cls, plugOrPlugType ) :

		result = {}
		plugType = plugOrPlugType
		if not inspect.isclass( plugType ) :
			plugType = type( plugOrPlugType )

		# consider base classes for the plug
		for baseClass in plugType.__bases__ :
			if not issubclass( baseClass, Gaffer.Plug ) :
				continue

			result.update( cls.__registeredPlugValueWidgets( baseClass ) )

		# consider itself
		result.update( cls.__plugValueWidgets.get( plugType, {} ) )

		return result

	def __plugMetadataChanged( self, plug, key, reason ) :

		if plug != self.getPlug() :
			return

		if key == "plugValueWidget:type" :
			self.__updateWidgetMenuText()
			self.__updateWidgetSettings()
		elif key == "nodule:type" :
			self.__updateGadgetMenuText()

	def __updateWidgetMenuText( self ) :

		if self.getPlug() is None :
			self.__widgetMenu.setText( "" )
			return

		metadata = Gaffer.Metadata.value( self.getPlug(), "plugValueWidget:type" )
		registeredWidgets = self.__registeredPlugValueWidgets( self.getPlug() )

		for label, widgetMetadata in registeredWidgets.items() :
			if widgetMetadata == metadata :
				self.__widgetMenu.setText( label )
				return

		self.__widgetMenu.setText( metadata )

	def __updateWidgetSettings( self ) :

		del self.__widgetSettingsContainer[:]

		if self.getPlug() is None :
			return

		widgetType = Gaffer.Metadata.value( self.getPlug(), "plugValueWidget:type" ) or ""

		with self.__widgetSettingsContainer :

			for label, plugValueWidgetType, widgetCreator in self.__widgetSettings :

				if not IECore.StringAlgo.match( widgetType, plugValueWidgetType ) :
					continue

				with _Row() :
					_Label( label )
					widgetCreator( self.getPlug() )

		self.__metadataWidgets["connectionGadget:color"].parent().setEnabled(
			self.getPlug() is not None and self.getPlug().direction() == Gaffer.Plug.Direction.In
		)

	def __widgetMenuDefinition( self ) :

		result = IECore.MenuDefinition()
		if self.getPlug() is None :
			return result

		metadata = Gaffer.Metadata.value( self.getPlug(), "plugValueWidget:type" )
		registeredWidgets = self.__registeredPlugValueWidgets( self.getPlug() )

		labels = list( registeredWidgets.keys() )
		# sort labels so that they are alphabetical, but with "Default" first, and "None" last
		labels.sort()
		labels.sort( key=lambda l: 0 if l == "Default" else 2 if l == "None" else 1 )
		for label in labels :
			result.append(
				"/" + label,
				{
					"command" : functools.partial(
						Gaffer.WeakMethod( self.__registerOrDeregisterMetadata ),
						key = "plugValueWidget:type",
						value = registeredWidgets[label]
					),
					"checkBox" : metadata == registeredWidgets[label],
				}
			)

		return result

	def __updateGadgetMenuText( self ) :

		if self.getPlug() is None :
			self.__gadgetMenu.setText( "" )
			return

		metadata = Gaffer.Metadata.value( self.getPlug(), "nodule:type" )
		metadata = None if metadata == "GafferUI::StandardNodule" else metadata
		for g in self.__gadgetDefinitions :
			if g.metadata == metadata :
				self.__gadgetMenu.setText( g.label )
				return

		self.__gadgetMenu.setText( metadata )

	def __gadgetMenuDefinition( self ) :

		result = IECore.MenuDefinition()
		if self.getPlug() is None :
			return result

		metadata = Gaffer.Metadata.value( self.getPlug(), "nodule:type" )
		for g in self.__gadgetDefinitions :
			if not isinstance( self.getPlug(), g.plugType ) :
				continue

			result.append(
				"/" + g.label,
				{
					"command" : functools.partial( Gaffer.WeakMethod( self.__registerOrDeregisterMetadata ), key = "nodule:type", value = g.metadata ),
					"checkBox" : metadata == g.metadata,
				}
			)

		return result

	def __registerOrDeregisterMetadata( self, unused, key, value ) :

		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			if value is not None :
				Gaffer.Metadata.registerValue( self.getPlug(), key, value )
			else :
				Gaffer.Metadata.deregisterValue( self.getPlug(), key )

	__GadgetDefinition = collections.namedtuple( "GadgetDefinition", ( "label", "plugType", "metadata" ) )
	__gadgetDefinitions = (
		__GadgetDefinition( "Default", Gaffer.Plug, None ),
		__GadgetDefinition( "Array", Gaffer.ArrayPlug, "GafferUI::CompoundNodule" ),
		__GadgetDefinition( "None", Gaffer.Plug, "" ),
	)

##########################################################################
# _SectionEditor. This provides a panel for editing the details of
# a specific section.
##########################################################################

class _SectionEditor( GafferUI.Widget ) :

	def __init__( self, **kw ) :

		column = GafferUI.ListContainer( spacing = 4, borderWidth = 8 )
		GafferUI.Widget.__init__( self, column, **kw )

		with column :

			with _Row() :

				_Label( "Name" )

				self.__nameWidget = GafferUI.TextWidget()
				self.__nameWidget.editingFinishedSignal().connect( Gaffer.WeakMethod( self.__nameWidgetEditingFinished ), scoped = False )

			with _Row() :

				_Label( "Summary", parenting = { "verticalAlignment" : GafferUI.ListContainer.VerticalAlignment.Top } )

				self.__summaryMetadataWidget = MetadataWidget.MultiLineStringMetadataWidget( key = "" )

		self.__section = ""
		self.__plugParent = None
		self.__nameChangedSignal = Gaffer.Signals.Signal3()

	def setPlugParent( self, plugParent ) :

		self.__plugParent = plugParent
		self.__summaryMetadataWidget.setTarget( self.__plugParent )

	def getPlugParent( self ) :

		return self.__plugParent

	def setSection( self, section ) :

		assert( isinstance( section, six.string_types ) )

		self.__section = section
		self.__nameWidget.setText( section.rpartition( "." )[-1] )
		self.__summaryMetadataWidget.setKey( "layout:section:" + self.__section + ":summary" )

	def getSection( self ) :

		return self.__section

	def nameChangedSignal( self ) :

		return self.__nameChangedSignal

	def __nameWidgetEditingFinished( self, nameWidget ) :

		if nameWidget.getText() == "" :
			# Can't rename to the empty string - abandon the edit.
			self.setSection( self.__section )
			return

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

		with Gaffer.UndoScope( self.__plugParent.ancestor( Gaffer.ScriptNode ) ) :

			for plug in self.__plugParent.children( Gaffer.Plug ) :
				s = Gaffer.Metadata.value( plug, "layout:section" )
				if s is not None :
					Gaffer.Metadata.registerValue( plug, "layout:section", newSection( s ) )

			emptySections = Gaffer.Metadata.value( self.getPlugParent(), "uiEditor:emptySections" )
			if emptySections :
				for i in range( 0, len( emptySections ) ) :
					emptySections[i] = newSection( emptySections[i] )
				Gaffer.Metadata.registerValue( self.getPlugParent(), "uiEditor:emptySections", emptySections )

			for name in Gaffer.Metadata.registeredValues( self.getPlugParent(), instanceOnly = True, persistentOnly = True ) :
				m = re.match( "(layout:section:)(.*)(:.*)", name )
				if m :
					if newSection( m.group( 2 ) ) != m.group( 2 ) :
						Gaffer.Metadata.registerValue(
							self.getPlugParent(),
							m.group( 1 ) + newSection( m.group( 2 ) ) + m.group( 3 ),
							Gaffer.Metadata.value( self.getPlugParent(), name )
						)
						Gaffer.Metadata.deregisterValue( self.getPlugParent(), name )

		self.setSection( ".".join( newSectionPath ) )
		self.nameChangedSignal()( self, ".".join( oldSectionPath ), ".".join( newSectionPath ) )


##########################################################################
# Registering custom PlugValueWidgets for the UIEditor
##########################################################################

UIEditor.registerPlugValueWidget( "Default", Gaffer.Plug, None )
UIEditor.registerPlugValueWidget( "None", Gaffer.Plug, "" )

UIEditor.registerPlugValueWidget( "Checkbox", Gaffer.IntPlug, "GafferUI.BoolPlugValueWidget" )
UIEditor.registerPlugValueWidget( "Text Region", Gaffer.StringPlug, "GafferUI.MultiLineStringPlugValueWidget" )
UIEditor.registerPlugValueWidget( "File Chooser", Gaffer.StringPlug, "GafferUI.FileSystemPathPlugValueWidget" )
UIEditor.registerPlugValueWidget( "File Chooser", Gaffer.StringVectorDataPlug, "GafferUI.FileSystemPathVectorDataPlugValueWidget" )
UIEditor.registerPlugValueWidget( "Presets Menu", Gaffer.ValuePlug, "GafferUI.PresetsPlugValueWidget" )
UIEditor.registerPlugValueWidget( "Connection", Gaffer.Plug, "GafferUI.ConnectionPlugValueWidget" )
UIEditor.registerPlugValueWidget( "Button", Gaffer.Plug, "GafferUI.ButtonPlugValueWidget" )

##########################################################################
# Registering standard Widget Settings for the UIEditor
##########################################################################

class _ButtonCodeMetadataWidget( GafferUI.MetadataWidget.MetadataWidget ) :

	def __init__( self, target = None, **kw ) :

		self.__codeWidget = GafferUI.CodeWidget()
		GafferUI.MetadataWidget.MetadataWidget.__init__( self, self.__codeWidget, "buttonPlugValueWidget:clicked", target, defaultValue = "", **kw )

		## \todo Qt 5.6 can't deal with multiline placeholder text. In Qt 5.12
		# we should be able to provide a little more detail here.
		self.__codeWidget._qtWidget().setPlaceholderText(
			"# Access the node graph via `plug`, and the UI via `button`"
		)

		self.__codeWidget.setHighlighter( GafferUI.CodeWidget.PythonHighlighter() )

		self.__codeWidget.editingFinishedSignal().connect(
			Gaffer.WeakMethod( self.__editingFinished ), scoped = False
		)

	def setTarget( self, target ) :

		GafferUI.MetadataWidget.MetadataWidget.setTarget( self, target )

		if target is not None :

			self.__codeWidget.setCompleter(
				GafferUI.CodeWidget.PythonCompleter( {
					"IECore" : IECore,
					"Gaffer" : Gaffer,
					"plug" : target,
					"button" : GafferUI.ButtonPlugValueWidget( target ),
				} )
			)

		else :

			self.__codeWidget.setCompleter( None )

	def _updateFromValue( self, value ) :

		self.__codeWidget.setText( str( value ) )

	def __editingFinished( self, *unused ) :

		self._updateFromWidget( self.__codeWidget.getText() )

UIEditor.registerWidgetMetadata( "File Extensions", "GafferUI.FileSystemPath*PlugValueWidget", "fileSystemPath:extensions", "" )
UIEditor.registerWidgetMetadata( "Bookmarks Category", "GafferUI.FileSystemPath*PlugValueWidget", "path:bookmarks", "" )
UIEditor.registerWidgetMetadata( "File Must Exist", "GafferUI.FileSystemPath*PlugValueWidget", "path:valid", False )
UIEditor.registerWidgetMetadata( "No Directories", "GafferUI.FileSystemPath*PlugValueWidget", "path:leaf", False )
UIEditor.registerWidgetMetadata( "Allow sequences", "GafferUI.FileSystemPath*PlugValueWidget", "fileSystemPath:includeSequences", False )
# Note that includeSequenceFrameRange is primarily used by GafferCortex.
# Think twice before using it elsewhere	as it may not exist in the future.
UIEditor.registerWidgetMetadata( "Sequences include frame range", "GafferUI.FileSystemPath*PlugValueWidget", "fileSystemPath:includeSequenceFrameRange", False )
UIEditor.registerWidgetSetting(
	"Button Click Code",
	"GafferUI.ButtonPlugValueWidget",
	_ButtonCodeMetadataWidget,
)
UIEditor.registerWidgetMetadata( "Inline", "GafferUI.ButtonPlugValueWidget", "layout:accessory", False )
UIEditor.registerWidgetMetadata( "Allow Custom Values", "GafferUI.PresetsPlugValueWidget", "presetsPlugValueWidget:allowCustom", False )
UIEditor.registerWidgetMetadata( "Divider", "*", "divider", False )
