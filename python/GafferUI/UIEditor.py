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
import collections
import imath

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
			with GafferUI.ListContainer( spacing = 4, borderWidth = 8, parenting = { "label" : "Node" } ) as self.__nodeTab :

				with _Row() :

					_Label( "Name" )

					self.__nodeNameWidget = GafferUI.NameWidget( None )

				with _Row() :

					_Label( "Description", parenting = { "verticalAlignment" : GafferUI.ListContainer.VerticalAlignment.Top } )

					self.__nodeMetadataWidgets.append(
						_MultiLineStringMetadataWidget( key = "description" )
					)

				with _Row() :

					_Label( "Documentation URL" )

					self.__nodeMetadataWidgets.append(
						_StringMetadataWidget( key = "documentation:url" )
					)

				with _Row() :

					_Label( "Color" )

					self.__nodeMetadataWidgets.append(
						_ColorSwatchMetadataWidget( key = "nodeGadget:color" )
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
	def appendNodeContextMenuDefinitions( cls, graphEditor, node, menuDefinition ) :

		menuDefinition.append( "/UIEditorDivider", { "divider" : True } )
		menuDefinition.append(
			"/Set Color...",
			{
				"command" : functools.partial( cls.__setColor, node = node ),
				"active" : not Gaffer.MetadataAlgo.readOnly( node ),
			}
		)

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
			if isinstance( self.__node, Gaffer.Box ) :
				# For Boxes we want the user to edit the plugs directly
				# parented to the Box, because that is where promoted plugs go,
				# and because we want to leave the "user" plug empty so that it
				# is available for use by the user on Reference nodes once a Box has
				# been exported and referenced.
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

		color = Gaffer.Metadata.value( node, "nodeGadget:color" ) or imath.Color3f( 1 )
		dialogue = GafferUI.ColorChooserDialogue( color = color, useDisplayTransform = False )
		color = dialogue.waitForColor( parentWindow = menu.ancestor( GafferUI.Window ) )
		if color is not None :
			with Gaffer.UndoScope( node.ancestor( Gaffer.ScriptNode ) ) :
				Gaffer.Metadata.registerValue( node, "nodeGadget:color", color )

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

__plugPopupMenuConnection = GafferUI.PlugValueWidget.popupMenuSignal().connect( __plugPopupMenu )

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

	def setKey( self, key ) :

		if key == self.__key :
			return

		self.__key = key
		self.__update()

	def getKey( self, key ) :

		return self.__key

	## Must be implemented in derived classes to update
	# the widget from the value.
	def _updateFromValue( self, value ) :

		raise NotImplementedError

	## Must be called by derived classes to update
	# the Metadata value when the widget value changes.
	def _updateFromWidget( self, value ) :

		if self.__target is None :
			return

		with Gaffer.UndoScope( self.__target.ancestor( Gaffer.ScriptNode ) ) :
			Gaffer.Metadata.registerValue( self.__target, self.__key, value )

	## May be called by derived classes to deregister the
	# metadata value.
	def _deregisterValue( self ) :

		if self.__target is None :
			return

		with Gaffer.UndoScope( self.__target.ancestor( Gaffer.ScriptNode ) ) :
			Gaffer.Metadata.deregisterValue( self.__target, self.__key )

	def __update( self ) :

		if self.__target is None :
			self._updateFromValue( None )
			return

		v = Gaffer.Metadata.value( self.__target, self.__key )
		if v is None :
			k = self.__fallbackKey( self.__key )
			if k is not None :
				v = Gaffer.Metadata.value( self.__target, k )

		self._updateFromValue( v )

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

		if Gaffer.MetadataAlgo.affectedByChange( self.__target, nodeTypeId, plugPath, plug ) :
			self.__update()

	@staticmethod
	def __fallbackKey( k ) :

		for oldPrefix, newPrefix in [
			( "pathPlugValueWidget:", "path:" ),
			( "fileSystemPathPlugValueWidget:", "fileSystemPath:" ),
		] :
			if k.startswith( newPrefix ) :
				return k.replace( newPrefix, oldPrefix )

		return None

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

class _StringMetadataWidget( _MetadataWidget ) :

	def __init__( self, key, target = None, acceptEmptyString = True, **kw ) :

		self.__textWidget = GafferUI.TextWidget()
		_MetadataWidget.__init__( self, self.__textWidget, key, target, **kw )

		self.__acceptEmptyString = acceptEmptyString

		self.__editingFinishedConnection = self.__textWidget.editingFinishedSignal().connect(
			Gaffer.WeakMethod( self.__editingFinished )
		)

	def textWidget( self ) :

		return self.__textWidget

	def _updateFromValue( self, value ) :

		self.__textWidget.setText( str( value ) if value is not None else "" )

	def __editingFinished( self, *unused ) :

		text = self.__textWidget.getText()
		if text or self.__acceptEmptyString :
			self._updateFromWidget( text )
		else :
			self._deregisterValue()

class _MultiLineStringMetadataWidget( _MetadataWidget ) :

	def __init__( self, key, target = None, role = GafferUI.MultiLineTextWidget.Role.Text, **kw ) :

		self.__textWidget = GafferUI.MultiLineTextWidget( role = role )
		_MetadataWidget.__init__( self, self.__textWidget, key, target, **kw )

		self.__editingFinishedConnection = self.__textWidget.editingFinishedSignal().connect(
			Gaffer.WeakMethod( self.__editingFinished )
		)

	def textWidget( self ) :

		return self.__textWidget

	def _updateFromValue( self, value ) :

		self.__textWidget.setText( value if value is not None else "" )

	def __editingFinished( self, *unused ) :

		self._updateFromWidget( self.__textWidget.getText() )

class _ColorSwatchMetadataWidget( _MetadataWidget ) :

	def __init__( self, key, target = None, **kw ) :

		self.__swatch = GafferUI.ColorSwatch( useDisplayTransform = False )

		_MetadataWidget.__init__( self, self.__swatch, key, target, **kw )

		self.__swatch._qtWidget().setFixedHeight( 18 )
		self.__swatch._qtWidget().setMaximumWidth( 40 )
		self.__value = None

		self.__buttonReleaseConnection = self.__swatch.buttonReleaseSignal().connect( Gaffer.WeakMethod( self.__buttonRelease ) )

	def _updateFromValue( self, value ) :

		if value is not None :
			self.__swatch.setColor( value )
		else :
			self.__swatch.setColor( imath.Color4f( 0, 0, 0, 0 ) )

		self.__value = value

	def __buttonRelease( self, swatch, event ) :

		if event.button != event.Buttons.Left :
			return False

		color = self.__value if self.__value is not None else imath.Color3f( 1 )
		dialogue = GafferUI.ColorChooserDialogue( color = color, useDisplayTransform = False )
		color = dialogue.waitForColor( parentWindow = self.ancestor( GafferUI.Window ) )

		if color is not None :
			self._updateFromWidget( color )

class _MenuMetadataWidget( _MetadataWidget ) :

	def __init__( self, key, labelsAndValues, target = None, **kw ) :

		self.__menuButton = GafferUI.MenuButton(
			menu = GafferUI.Menu( Gaffer.WeakMethod( self.__menuDefinition ) )
		)

		self.__labelsAndValues = labelsAndValues
		self.__currentValue = None

		_MetadataWidget.__init__( self, self.__menuButton, key, target, **kw )

	def _updateFromValue( self, value ) :

		self.__currentValue = value

		buttonText = str( value )
		for label, value in self.__labelsAndValues :
			if value == self.__currentValue :
				buttonText = label
				break

		self.__menuButton.setText( buttonText )

	def __menuDefinition( self ) :

		result = IECore.MenuDefinition()
		for label, value in self.__labelsAndValues :
			result.append(
				"/" + label,
				{
					"command" : functools.partial( Gaffer.WeakMethod( self.__setValue ), value = value ),
					"checkBox" : value == self.__currentValue
				}
			)

		return result

	def __setValue( self, unused, value ) :

		self._updateFromWidget( value )

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
		GafferUI.Widget.__init__( self, column, **kw )

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

		with Gaffer.BlockedConnection( self.__plugMetadataChangedConnection ) :
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

		with Gaffer.UndoScope( self.__parent.ancestor( Gaffer.ScriptNode ) ) :
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

		parentAffected = isinstance( self.__parent, Gaffer.Plug ) and Gaffer.MetadataAlgo.affectedByChange( self.__parent, nodeTypeId, plugPath, plug )
		childAffected = Gaffer.MetadataAlgo.childAffectedByChange( self.__parent, nodeTypeId, plugPath, plug )
		if not parentAffected and not childAffected :
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

				self.__pathListingSelectionChangedConnection = self.__pathListing.selectionChangedSignal().connect( Gaffer.WeakMethod( self.__selectionChanged ) )
				self.__dragEnterConnection = self.__pathListing.dragEnterSignal().connect( Gaffer.WeakMethod( self.__dragEnter ) )
				self.__dragMoveConnection = self.__pathListing.dragMoveSignal().connect( Gaffer.WeakMethod( self.__dragMove ) )
				self.__dragEndConnection = self.__pathListing.dragEndSignal().connect( Gaffer.WeakMethod( self.__dragEnd ) )

				with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :

					self.__addButton = GafferUI.Button( image = "plus.png", hasFrame = False )
					self.__addButtonClickedConnection = self.__addButton.clickedSignal().connect( Gaffer.WeakMethod( self.__addButtonClicked ) )

					self.__deleteButton = GafferUI.Button( image = "minus.png", hasFrame = False )
					self.__deleteButtonClickedConnection = self.__deleteButton.clickedSignal().connect( Gaffer.WeakMethod( self.__deleteButtonClicked ) )

			with GafferUI.ListContainer( spacing = 4 ) as self.__editingColumn :

				GafferUI.Label( "Name" )

				self.__nameWidget = GafferUI.TextWidget()
				self.__nameEditingFinishedConnection = self.__nameWidget.editingFinishedSignal().connect( Gaffer.WeakMethod( self.__nameEditingFinished ) )

				GafferUI.Spacer( imath.V2i( 4 ), maximumSize = imath.V2i( 4 ) )

				GafferUI.Label( "Value" )

		# We make a UI for editing preset values by copying the plug
		# onto this node and then making a PlugValueWidget for it.
		self.__valueNode = Gaffer.Node( "PresetEditor" )
		self.__valuePlugSetConnection = self.__valueNode.plugSetSignal().connect( Gaffer.WeakMethod( self.__valuePlugSet ) )

	def setPlug( self, plug ) :

		self.__plug = plug

		self.__plugMetadataChangedConnection = None
		del self.__editingColumn[4:]

		plugValueWidget = None
		if self.__plug is not None :
			self.__plugMetadataChangedConnection = Gaffer.Metadata.plugValueChangedSignal().connect( Gaffer.WeakMethod( self.__plugMetadataChanged ) )
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

	def __plugMetadataChanged( self, nodeTypeId, plugPath, key, plug ) :

		if self.__plug is None or not Gaffer.MetadataAlgo.affectedByChange( self.__plug, nodeTypeId, plugPath, plug ) :
			return

		if key.startswith( "preset:" ) :
			self.__updatePath()

	def __selectionChanged( self, listing ) :

		selectedPaths = listing.getSelectedPaths()

		self.__nameWidget.setText( selectedPaths[0][0] if selectedPaths else "" )
		if selectedPaths :
			with Gaffer.BlockedConnection( self.__valuePlugSetConnection ) :
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
		srcIndex = d.keys().index( srcPath[0] )

		targetPath = self.__pathListing.pathAt( event.line.p0 )
		if targetPath is not None :
			targetIndex = d.keys().index( targetPath[0] )
		else :
			targetIndex = 0 if event.line.p0.y < 1 else len( d )

		if srcIndex == targetIndex :
			return True

		items = d.items()
		item = items[srcIndex]
		del items[srcIndex]
		items.insert( targetIndex, item )

		d.clear()
		d.update( items )

		self.__pathListing.getPath().pathChangedSignal()( self.__pathListing.getPath() )

		return True

	def __dragEnd( self, listing, event ) :

		d = self.__pathListing.getPath().dict()
		with Gaffer.BlockedConnection( self.__plugMetadataChangedConnection ) :
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

		# Sanitize name
		newName = newName.replace( "/", "_")

		items = self.__pathListing.getPath().dict().items()
		with Gaffer.BlockedConnection( self.__plugMetadataChangedConnection ) :
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
				self.__metadataWidgets["label"] = _StringMetadataWidget( key = "label", acceptEmptyString = False )

			with _Row() :

				_Label( "Description", parenting = { "verticalAlignment" : GafferUI.ListContainer.VerticalAlignment.Top } )
				self.__metadataWidgets["description"] = _MultiLineStringMetadataWidget( key = "description" )
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

				with GafferUI.ListContainer( spacing = 4 ) :

					for m in self.__metadataDefinitions :

						with _Row() :
							_Label( m.label )
							self.__metadataWidgets[m.key] = m.metadataWidgetType( key = m.key )

			with GafferUI.Collapsible( "Graph Editor", collapsed = True ) :

				with GafferUI.ListContainer( spacing = 4 ) as self.__graphEditorSection :

					with _Row() :

						_Label( "Gadget" )
						self.__gadgetMenu = GafferUI.MenuButton(
							menu = GafferUI.Menu( Gaffer.WeakMethod( self.__gadgetMenuDefinition ) )
						)

					with _Row() :

						_Label( "Position" )
						self.__metadataWidgets["noduleLayout:section"] = _MenuMetadataWidget(
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
						self.__metadataWidgets["nodule:color"] = _ColorSwatchMetadataWidget( key = "nodule:color" )

					with _Row() :

						_Label( "Connection Color" )
						self.__metadataWidgets["connectionGadget:color"] = _ColorSwatchMetadataWidget( key = "connectionGadget:color" )

			GafferUI.Spacer( imath.V2i( 0 ), parenting = { "expand" : True } )

		self.__plugMetadataChangedConnection = Gaffer.Metadata.plugValueChangedSignal().connect( Gaffer.WeakMethod( self.__plugMetadataChanged ) )

		self.__plug = None

	def setPlug( self, plug ) :

		self.__plug = plug

		self.__nameWidget.setGraphComponent( self.__plug )
		for widget in self.__metadataWidgets.values() :
			widget.setTarget( self.__plug )

		self.__updateWidgetMenuText()
		self.__updateWidgetSettings()
		self.__updateGadgetMenuText()
		self.__presetsEditor.setPlug( plug )
		self.__graphEditorSection.setEnabled( self.__plug is not None and self.__plug.parent().isSame( self.__plug.node() ) )

		self.setEnabled( self.__plug is not None )

	def getPlug( self ) :

		return self.__plug

	def __plugMetadataChanged( self, nodeTypeId, plugPath, key, plug ) :

		if self.getPlug() is None :
			return

		if not Gaffer.MetadataAlgo.affectedByChange( self.getPlug(), nodeTypeId, plugPath, plug ) :
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
		for w in self.__widgetDefinitions :
			if w.metadata == metadata :
				self.__widgetMenu.setText( w.label )
				return

		self.__widgetMenu.setText( metadata )

	def __updateWidgetSettings( self ) :

		widgetType = ""
		if self.getPlug() is not None :
			widgetType = Gaffer.Metadata.value( self.getPlug(), "plugValueWidget:type" ) or ""

		for m in self.__metadataDefinitions :
			widget = self.__metadataWidgets[m.key]
			widget.parent().setVisible( IECore.StringAlgo.match( widgetType, m.plugValueWidgetType ) )

		self.__metadataWidgets["connectionGadget:color"].parent().setEnabled(
			self.getPlug() is not None and self.getPlug().direction() == Gaffer.Plug.Direction.In
		)

	def __widgetMenuDefinition( self ) :

		result = IECore.MenuDefinition()
		if self.getPlug() is None :
			return result

		metadata = Gaffer.Metadata.value( self.getPlug(), "plugValueWidget:type" )
		for w in self.__widgetDefinitions :
			if not isinstance( self.getPlug(), w.plugType ) :
				continue

			result.append(
				"/" + w.label,
				{
					"command" : functools.partial( Gaffer.WeakMethod( self.__registerOrDeregisterMetadata ), key = "plugValueWidget:type", value = w.metadata ),
					"checkBox" : metadata == w.metadata,
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

	__WidgetDefinition = collections.namedtuple( "WidgetDefinition", ( "label", "plugType", "metadata" ) )
	__widgetDefinitions = (
		__WidgetDefinition( "Default", Gaffer.Plug, None ),
		__WidgetDefinition( "Checkbox", Gaffer.IntPlug, "GafferUI.BoolPlugValueWidget" ),
		__WidgetDefinition( "Text Region", Gaffer.StringPlug, "GafferUI.MultiLineStringPlugValueWidget" ),
		__WidgetDefinition( "File Chooser", Gaffer.StringPlug, "GafferUI.FileSystemPathPlugValueWidget" ),
		__WidgetDefinition( "File Chooser", Gaffer.StringVectorDataPlug, "GafferUI.FileSystemPathVectorDataPlugValueWidget" ),
		__WidgetDefinition( "Presets Menu", Gaffer.ValuePlug, "GafferUI.PresetsPlugValueWidget" ),
		__WidgetDefinition( "Connection", Gaffer.Plug, "GafferUI.ConnectionPlugValueWidget" ),
		__WidgetDefinition( "Button", Gaffer.Plug, "GafferUI.ButtonPlugValueWidget" ),
		__WidgetDefinition( "None", Gaffer.Plug, "" ),
	)

	__MetadataDefinition = collections.namedtuple( "MetadataDefinition", ( "key", "label", "metadataWidgetType", "plugValueWidgetType" ) )
	__metadataDefinitions = (
		__MetadataDefinition( "fileSystemPath:extensions", "File Extensions", _StringMetadataWidget, "GafferUI.FileSystemPath*PlugValueWidget" ),
		__MetadataDefinition( "path:bookmarks", "Bookmarks Category", _StringMetadataWidget, "GafferUI.FileSystemPath*PlugValueWidget" ),
		__MetadataDefinition( "path:valid", "File Must Exist", _BoolMetadataWidget, "GafferUI.FileSystemPath*PlugValueWidget" ),
		__MetadataDefinition( "path:leaf", "No Directories", _BoolMetadataWidget, "GafferUI.FileSystemPath*PlugValueWidget" ),
		__MetadataDefinition( "fileSystemPath:includeSequences", "Allow sequences", _BoolMetadataWidget, "GafferUI.FileSystemPath*PlugValueWidget" ),
		# Note that includeSequenceFrameRange is primarily used by GafferCortex.
		# Think twice before using it elsewhere	as it may not exist in the future.
		__MetadataDefinition( "fileSystemPath:includeSequenceFrameRange", "Sequences include frame range", _BoolMetadataWidget, "GafferUI.FileSystemPath*PlugValueWidget" ),
		__MetadataDefinition(
			"buttonPlugValueWidget:clicked",
			"Button Click Code",
			lambda key : _MultiLineStringMetadataWidget( key, role = GafferUI.MultiLineTextWidget.Role.Code ),
			"GafferUI.ButtonPlugValueWidget"
		),
		__MetadataDefinition( "layout:accessory", "Inline", _BoolMetadataWidget,  "GafferUI.ButtonPlugValueWidget" ),
		__MetadataDefinition( "divider", "Divider", _BoolMetadataWidget,  "*" ),

	)

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
				self.__nameWidgetEditingFinishedConnection = self.__nameWidget.editingFinishedSignal().connect( Gaffer.WeakMethod( self.__nameWidgetEditingFinished ) )

			with _Row() :

				_Label( "Summary", parenting = { "verticalAlignment" : GafferUI.ListContainer.VerticalAlignment.Top } )

				self.__summaryMetadataWidget = _MultiLineStringMetadataWidget( key = "" )

		self.__section = ""
		self.__plugParent = None
		self.__nameChangedSignal = Gaffer.Signal3()

	def setPlugParent( self, plugParent ) :

		self.__plugParent = plugParent
		self.__summaryMetadataWidget.setTarget( self.__plugParent )

	def getPlugParent( self ) :

		return self.__plugParent

	def setSection( self, section ) :

		assert( isinstance( section, basestring ) )

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
