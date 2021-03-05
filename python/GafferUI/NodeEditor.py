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

import IECore

import Gaffer
import GafferUI

from Qt import QtWidgets

class NodeEditor( GafferUI.NodeSetEditor ) :

	def __init__( self, scriptNode, **kw ) :

		self.__column = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical )

		GafferUI.NodeSetEditor.__init__( self, self.__column, scriptNode, **kw )

		with self.__column :

			with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, borderWidth=8, spacing=4 ) as self.__header :

				# NameLabel with a fixed formatter, to be used as a drag source.
				self.__nameLabel = GafferUI.NameLabel( None, formatter = lambda graphComponents : "<h4>Node Name</h4>" )
				# NameWidget to allow editing of the name.
				self.__nameWidget = GafferUI.NameWidget( None )

				with GafferUI.ListContainer(
					GafferUI.ListContainer.Orientation.Horizontal,
					spacing=4,
					parenting = { "horizontalAlignment" : GafferUI.HorizontalAlignment.Right },
				) as self.__infoSection :

					self.__typeLabel = GafferUI.Label()

					infoButton = GafferUI.Button( image = "info.png", hasFrame = False )
					infoButton.clickedSignal().connect( Gaffer.WeakMethod( self.__infoButtonClicked ), scoped = False )

				GafferUI.MenuButton(
					image = "gear.png",
					hasFrame = False,
					menu = GafferUI.Menu( Gaffer.WeakMethod( self.__menuDefinition ) )
				)

			self.__nodeUIFrame = GafferUI.Frame(
				borderStyle = GafferUI.Frame.BorderStyle.None_, borderWidth = 0,
				parenting = { "expand" : True }
			)

		self.__nodeUI = None
		self.__readOnly = False

		self._updateFromSet()

	## Returns the NodeUI being used to represent the current node,
	# or None if there is no current node.
	def nodeUI( self ) :

		self._doPendingUpdate()
		return self.__nodeUI

	## \deprecated
	def setReadOnly( self, readOnly ) :

		if readOnly == self.__readOnly :
			return

		self.__readOnly = readOnly
		if self.__nodeUI is not None :
			self.__nodeUI.setReadOnly( readOnly )
			self.__nameWidget.setEditable( not readOnly )

	## \deprecated
	def getReadOnly( self ) :

		return self.__readOnly

	__toolMenuSignal = Gaffer.Signal3()
	## Returns a signal which is emitted to create the
	# tool menu for a node in the editor. Slots may connect
	# to this signal to edit the menu definition on the fly -
	# the signature for the signal is ( nodeEditor, node, menuDefinition )
	# and the menu definition should just be edited in place.
	@classmethod
	def toolMenuSignal( cls ) :

		return cls.__toolMenuSignal

	def __repr__( self ) :

		return "GafferUI.NodeEditor( scriptNode )"

	def _updateFromSet( self ) :

		GafferUI.NodeSetEditor._updateFromSet( self )

		focusWidget = GafferUI.Widget._owner( QtWidgets.QApplication.focusWidget() )
		if self.__column.isAncestorOf( focusWidget ) :
			# The focus is in our editor, but it belongs to a widget we're about
			# to delete. Transfer the focus up so that we don't lose the focus
			# when we delete the widget.
			## \todo Is there an argument for moving this fix to the ListContainer
			# itself?
			self.__column._qtWidget().setFocus()

		node = self._lastAddedNode()
		if node is None :
			self.__nameLabel.setGraphComponent( None )
			self.__nameWidget.setGraphComponent( None )
			self.__nodeUI = None
			# Spacer is necessary to allow bookmark shortcuts to work in an
			# empty NodeEditor.
			self.__nodeUIFrame.setChild( GafferUI.Spacer( imath.V2i( 0 ) ) )
			self.__header.setVisible( False )
			return

		self.__nameLabel.setGraphComponent( node )
		self.__nameWidget.setGraphComponent( node )
		self.__typeLabel.setText( "<h4>" + node.typeName().rpartition( ":" )[-1] + "</h4>" )

		toolTip = "# " + node.typeName().rpartition( ":" )[2]
		description = Gaffer.Metadata.value( node, "description" )
		if description :
			toolTip += "\n\n" + description
		self.__infoSection.setToolTip( toolTip )

		self.__header.setVisible( True )

		self.__nodeUI = GafferUI.NodeUI.create( node )
		self.__nodeUI.setReadOnly( self.getReadOnly() )
		self.__nodeUIFrame.setChild( self.__nodeUI )

	def _titleFormat( self ) :

		return GafferUI.NodeSetEditor._titleFormat( self, _maxNodes = 1, _reverseNodes = True, _ellipsis = False )

	def __infoButtonClicked( self, *unused ) :

		url = Gaffer.Metadata.value( self.nodeUI().node(), "documentation:url" )
		if url :
			GafferUI.showURL( url )

		return True

	def __menuDefinition( self ) :

		node = self.nodeUI().node()
		result = IECore.MenuDefinition()

		url = Gaffer.Metadata.value( node, "documentation:url" )
		result.append(
			"/Documentation...",
			{
				"active" : bool( url ),
				"command" : functools.partial( GafferUI.showURL, url ),
			}
		)

		nodeCls = type( node )
		GafferUI.Examples.appendExamplesSubmenuDefinition( result, "/Examples", forNode = nodeCls )

		result.append( "/DocumentationDivider", { "divider" : True } )

		result.append(
			"/Revert to Defaults",
			{
				"command" : Gaffer.WeakMethod( self.__revertToDefaults ),
				"active" : not Gaffer.MetadataAlgo.readOnly( self.nodeUI().node() ),
			}
		)

		readOnly = Gaffer.MetadataAlgo.getReadOnly( self.nodeUI().node() )
		result.append(
			"/Unlock" if readOnly else "/Lock",
			{
				"command" : functools.partial( Gaffer.WeakMethod( self.__applyReadOnly ), not readOnly ),
				"active" : not Gaffer.MetadataAlgo.readOnly( self.nodeUI().node().parent() ),
			}
		)

		self.toolMenuSignal()( self, self.nodeUI().node(), result )

		return result

	def __revertToDefaults( self ) :

		def applyDefaults( graphComponent ) :

			if isinstance( graphComponent, Gaffer.Plug ) :

				plug = graphComponent
				if plug.direction() == plug.Direction.Out :
					return
				elif plug.isSame( plug.node()["user"] ) :
					# Not much sense reverting user plugs, since we
					# don't expect the user to have gone to the trouble
					# of giving them defaults.
					return
				elif plug.getName().startswith( "__" ) :
					# Private plugs are none of our business.
					return
				elif Gaffer.MetadataAlgo.readOnly( plug ) :
					return

				if isinstance( plug, Gaffer.ValuePlug ) :
					if plug.settable() :
						plug.setToDefault()
					return

			for c in graphComponent.children( Gaffer.Plug ) :
				applyDefaults( c )

		node = self.nodeUI().node()
		with Gaffer.UndoScope( node.ancestor( Gaffer.ScriptNode ) ) :
			applyDefaults( node )
			Gaffer.NodeAlgo.applyUserDefaults( node )

	def __applyReadOnly( self, readOnly ) :

		node = self.nodeUI().node()
		with Gaffer.UndoScope( node.scriptNode() ) :
			Gaffer.MetadataAlgo.setReadOnly( node, readOnly )

GafferUI.Editor.registerType( "NodeEditor", NodeEditor )
