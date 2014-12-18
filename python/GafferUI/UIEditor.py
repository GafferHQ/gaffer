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

					self.__plugMetadataWidgets.append(
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

					self.__plugMetadataWidgets.append(
						_BoolMetadataWidget(
							key = "divider",
							parenting = {
								"index" : ( 1, 2 ),
								"alignment" : ( GafferUI.HorizontalAlignment.Left, GafferUI.VerticalAlignment.Center )
							}
						)
					)

			self.__plugTab.setSizes( [ 0.3, 0.7 ] )

		# initialise our selection to nothing

		self.__node = None
		self.__selectedPlug = None

		# call __updateFromSetInternal() to populate our selection and connect
		# the ui to it. we pass lazy==False to avoid the early out if
		# there is no currently selected node.

		self.__updateFromSetInternal( lazy=False )

	def setSelectedPlug( self, plug ) :

		self.__setSelectedPlugInternal( plug )

	def getSelectedPlug( self ) :

		return self.__selectedPlug

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

	def _updateFromSet( self ) :

		GafferUI.NodeSetEditor._updateFromSet( self )

		self.__updateFromSetInternal()

	def __setSelectedPlugInternal( self, plug, lazy=True ) :

		assert( plug is None or self.__node["user"].isAncestorOf( plug ) )

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

		for widget in self.__plugMetadataWidgets :
			widget.setTarget( self.__selectedPlug )

	def __updateFromSetInternal( self, lazy=True ) :

		node = self._lastAddedNode()
		if isinstance( node, Gaffer.Reference ) :
			# ui is defined before exporting,
			# so we don't want to edit it after
			# referencing.
			node = None

		if lazy and node == self.__node :
			return

		self.__node = node
		self.__nodeNameWidget.setGraphComponent( self.__node )
		self.__nodeTab.setEnabled( self.__node is not None )

		self.__plugListing.setPlugParent( self.__node["user"] if self.__node is not None else None )

		if self.__node is None or not len( self.__node["user"] ) :
			self.__setSelectedPlugInternal( None, lazy )
		else :
			self.__setSelectedPlugInternal( self.__node["user"][0], lazy )

		for widget in self.__nodeMetadataWidgets :
			widget.setTarget( self.__node )

	def __plugListingSelectionChanged( self, listing ) :

		paths = listing.getSelectedPaths()
		if not paths :
			# the path might have been deselected automatically because the plug name
			# changed. in this case we want to restore the old selection.
			previousSelection = self.getSelectedPlug()
			if (
				previousSelection is not None and
				self.__node is not None and
				previousSelection.parent() is not None and
				previousSelection.parent().isSame( self.__node["user"] )
			) :
				listing.setSelectedPaths(
					listing.getPath().copy().setFromString( "/" + previousSelection.getName() )
				)
			else :
				self.setSelectedPlug( None )
		else :
			self.setSelectedPlug( paths[0].info()["dict:value"].plug )

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

# PlugValueWidget popup menu
##########################################################################

def __editPlugUI( node, plug ) :

	editor = GafferUI.UIEditor.acquire( node )
	editor.setSelectedPlug( plug )
	editor.plugEditor().reveal()

def __plugPopupMenu( menuDefinition, plugValueWidget ) :

	plug = plugValueWidget.getPlug()
	node = plug.node()
	if node is None or isinstance( node, Gaffer.Reference ):
		return

	if not plug.parent().isSame( node["user"] ) :
		return

	menuDefinition.append( "/EditUIDivider", { "divider" : True } )
	menuDefinition.append( "/Edit UI...", { "command" : IECore.curry( __editPlugUI, node, plug ), "active" : not plugValueWidget.getReadOnly() } )

__plugPopupMenuConnection = GafferUI.PlugValueWidget.popupMenuSignal().connect( __plugPopupMenu )

# _PlugListing. This is used to list the plugs in the UIEditor.
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
		self.__dragEndConnection = self.dragEndSignal().connect( Gaffer.WeakMethod( self.__dragEnd ) )
		self.__keyPressConnection = self.keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPress ) )

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

		plugs = self.__parent.children( Gaffer.Plug )
		plugs = GafferUI.PlugLayout.layoutOrder( plugs )

		d = {}
		for index, plug in enumerate( plugs ) :
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

	def __dragEnd( self, listing, event ) :

		if not self.__dragValid( event ) :
			return False

		# flush the changed indices into the metadata for the node,
		# so that they actual PlugLayout will be updated to reflect
		# the new ordering.

		with Gaffer.UndoContext( self.getPlugParent().ancestor( Gaffer.ScriptNode ) ) :
			for entry in self.getPath().dict().values() :
				Gaffer.Metadata.registerPlugValue( entry.plug, "layout:index", entry.index )

		return True

	def __plugMetadataChanged( self, nodeTypeId, plugPath, key ) :

		if self.__parent is None :
			return

		if not self.__parent.node().isInstanceOf( nodeTypeId ) :
			return

		if key == "layout:index" :
			self.__updatePath()

	def __keyPress( self, widget, event ) :

		assert( widget is self )

		if event.key == "Backspace" or event.key == "Delete" :

			selectedPaths = self.getSelectedPaths()
			if len( selectedPaths ) :
				with Gaffer.UndoContext( self.__parent.ancestor( Gaffer.ScriptNode ) ) :
					for path in selectedPaths :
						plug = path.info()["dict:value"].plug
						self.__parent.removeChild( plug )

			return True

		return False

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
			if isinstance( self.__target, Gaffer.Plug ) :
				Gaffer.Metadata.registerPlugValue( self.__target, self.__key, value )
			else :
				Gaffer.Metadata.registerNodeValue( self.__target, self.__key, value )

	def __update( self ) :

		if isinstance( self.__target, Gaffer.Node ) :
			self._updateFromValue( Gaffer.Metadata.nodeValue( self.__target, self.__key ) )
		elif isinstance( self.__target, Gaffer.Plug ) :
			self._updateFromValue( Gaffer.Metadata.plugValue( self.__target, self.__key ) )
		else :
			self._updateFromValue( None )

	def __nodeMetadataChanged( self, nodeTypeId, key ) :

		if self.__key != key :
			return
		if not self.__target.isInstanceOf( nodeTypeId ) :
			return

		self.__update()

	def __plugMetadataChanged( self, nodeTypeId, plugPath, key ) :

		if self.__key != key :
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
