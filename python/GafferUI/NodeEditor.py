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

import IECore

import Gaffer
import GafferUI

class NodeEditor( GafferUI.NodeSetEditor ) :

	def __init__( self, scriptNode, parenting = None ) :

		self.__column = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical )

		GafferUI.NodeSetEditor.__init__( self, self.__column, scriptNode, parenting = parenting )

		self.__nodeUI = None
		self.__nameWidget = None
		self.__readOnly = False

		self._updateFromSet()

	## Returns the NodeUI being used to represent the current node,
	# or None if there is no current node.
	def nodeUI( self ) :

		self._doPendingUpdate()
		return self.__nodeUI

	def setReadOnly( self, readOnly ) :

		if readOnly == self.__readOnly :
			return

		self.__readOnly = readOnly
		if self.__nodeUI is not None :
			self.__nodeUI.setReadOnly( readOnly )
			self.__nameWidget.setEditable( not readOnly )

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

		del self.__column[:]
		self.__nodeUI = None
		self.__nameWidget = None

		node = self._lastAddedNode()
		if not node :
			return

		with self.__column :
			with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, borderWidth=8, spacing=4 ) :

				GafferUI.Label( "<h4>Node Name</h4>" )
				self.__nameWidget = GafferUI.NameWidget( node )
				self.__nameWidget.setEditable( not self.getReadOnly() )

				with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing=4 ) as infoSection :

					GafferUI.Label( "<h4>" + node.typeName().rpartition( ":" )[-1] + "</h4>" )

					button = GafferUI.Button( image = "info.png", hasFrame = False )
					url = Gaffer.Metadata.nodeValue( node, "documentation:url" )
					if url :
						button.clickedSignal().connect(
							lambda button : GafferUI.showURL( url ),
							scoped = False
						)

				toolTip = "<h3>" + node.typeName().rpartition( ":" )[2] + "</h3>"
				description = Gaffer.Metadata.nodeDescription( node )
				if description :
					toolTip += "\n\n" + description
				infoSection.setToolTip( toolTip )

				GafferUI.MenuButton(
					image = "gear.png",
					hasFrame = False,
					menu = GafferUI.Menu( Gaffer.WeakMethod( self.__menuDefinition ) )
				)

		frame = GafferUI.Frame( borderStyle=GafferUI.Frame.BorderStyle.None, borderWidth=0 )
		self.__column.append( frame, expand=True )
		self.__nodeUI = GafferUI.NodeUI.create( node )
		self.__nodeUI.setReadOnly( self.getReadOnly() )
		frame.setChild( self.__nodeUI )

	def _titleFormat( self ) :

		return GafferUI.NodeSetEditor._titleFormat( self, _maxNodes = 1, _reverseNodes = True, _ellipsis = False )

	def __menuDefinition( self ) :

		result = IECore.MenuDefinition()

		url = Gaffer.Metadata.nodeValue( self.nodeUI().node(), "documentation:url" )
		result.append(
			"/Documentation...",
			{
				"active" : bool( url ),
				"command" : functools.partial( GafferUI.showURL, url ),
			}
		)

		result.append( "/DocumentationDivider", { "divider" : True } )

		result.append(
			"/Revert to Defaults",
			{
				"command" : Gaffer.WeakMethod( self.__revertToDefaults ),
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
				if plug.isSame( plug.node()["user"] ) :
					# Not much sense reverting user plugs, since we
					# don't expect the user to have gone to the trouble
					# of giving them defaults.
					return
				elif plug.getName().startswith( "__" ) :
					# Private plugs are none of our business.
					return

				if isinstance( plug, Gaffer.ValuePlug ) :
					if plug.settable() :
						plug.setToDefault()
					return

			for c in graphComponent.children( Gaffer.Plug ) :
				applyDefaults( c )

		node = self.nodeUI().node()
		with Gaffer.UndoContext( node.ancestor( Gaffer.ScriptNode ) ) :
			applyDefaults( node )
			Gaffer.NodeAlgo.applyUserDefaults( node )

GafferUI.EditorWidget.registerType( "NodeEditor", NodeEditor )
