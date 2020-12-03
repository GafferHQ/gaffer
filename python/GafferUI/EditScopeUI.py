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

import imath

import IECore

import Gaffer
import GafferUI

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
Gaffer.Metadata.registerValue( Gaffer.EditScope, "BoxOut.name", "readOnly", True )
Gaffer.Metadata.registerValue( Gaffer.BoxIn, "renameable", lambda node : not isinstance( node.parent(), Gaffer.EditScope ) or node.getName() != "BoxIn" )
Gaffer.Metadata.registerValue( Gaffer.BoxOut, "renameable", lambda node : not isinstance( node.parent(), Gaffer.EditScope ) or node.getName() != "BoxOut" )

# EditScopePlugValueWidget
# ========================

class EditScopePlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		frame = GafferUI.Frame( borderWidth = 0 )
		GafferUI.PlugValueWidget.__init__( self, frame, plug, **kw )

		with frame :
			with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :
				GafferUI.Spacer( imath.V2i( 4, 1 ), imath.V2i( 4, 1 ) )
				GafferUI.Label( "Edit Scope" )
				self.__menuButton = GafferUI.MenuButton(
					"",
					menu = GafferUI.Menu( Gaffer.WeakMethod( self.__menuDefinition ) )
				)
				self.__menuButton._qtWidget().setFixedWidth( 100 )
				self.__navigationMenuButton = GafferUI.MenuButton(
					image = "navigationArrow.png",
					hasFrame = False,
					menu = GafferUI.Menu( Gaffer.WeakMethod( self.__navigationMenuDefinition ) )
				)
				GafferUI.Spacer( imath.V2i( 4, 1 ), imath.V2i( 4, 1 ) )

		self._updateFromPlug()

	def hasLabel( self ) :

		return True

	def _updateFromPlug( self ) :

		editScope = self.__editScope()
		editScopeActive = editScope is not None
		self.__updateMenuButton( editScope )
		self.__navigationMenuButton.setEnabled( editScopeActive )
		if editScopeActive :
			self.__editScopeNameChangedConnection = editScope.nameChangedSignal().connect(
				Gaffer.WeakMethod( self.__editScopeNameChanged ), scoped = True
			)
		else :
			self.__editScopeNameChangedConnection = None

		if self._qtWidget().property( "editScopeActive" ) != editScopeActive :
			self._qtWidget().setProperty( "editScopeActive", GafferUI._Variant.toVariant( editScopeActive ) )
			self._repolish()

	def __updateMenuButton( self, editScope ) :

		self.__menuButton.setText( editScope.getName() if editScope is not None else "None" )

	def __editScopeNameChanged( self, editScope ) :

		self.__updateMenuButton( editScope )

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

	def __menuDefinition( self ) :

		result = IECore.MenuDefinition()

		node = self.getPlug().node()
		if isinstance( node, GafferUI.View ) and self.getPlug() == node["editScope"] :
			if node["in"].getInput() is None :
				return
			else :
				node = node["in"].getInput().node()

		currentEditScope = None
		if self.getPlug().getInput() is not None :
			currentEditScope = self.getPlug().getInput().parent()

		def addItem( editScope, enabled = True ) :

			result.append(
				# The underscore suffix prevents collisions with a node and
				# it's submenu if it has nested edit scopes.
				"/%s_" % editScope.relativeName( editScope.scriptNode() ).replace( ".", "/" ),
				{
					"command" : functools.partial( Gaffer.WeakMethod( self.__connectEditScope ), editScope ),
					"active" : enabled,
					"label" : editScope.getName(),
					"checkBox" : editScope == currentEditScope,
				}
			)

		upstream = Gaffer.NodeAlgo.findAllUpstream( node, self.__editScopePredicate )
		if self.__editScopePredicate( node ) :
			upstream.insert( 0, node )

		result.append( "/__UpstreamDivider__", { "divider" : True, "label" : "Upstream" } )
		if upstream :
			for editScope in reversed( upstream ) :
				addItem( editScope )
		else :
			result.append( "/None Available", { "active" : False } )

		downstream = Gaffer.NodeAlgo.findAllDownstream( node, self.__editScopePredicate )
		if downstream :
			result.append( "/__DownstreamDivider__", { "divider" : True, "label" : "Downstream" } )
			for editScope in downstream :
				addItem( editScope, enabled = False )

		result.append( "/__NoneDivider__", { "divider" : True } )
		result.append(
			"/None", { "command" : functools.partial( self.getPlug().setInput, None ) },
		)

		return result

	def __navigationMenuDefinition( self ) :

		result = IECore.MenuDefinition()

		editScope = self.__editScope()
		if editScope is None :
			result.append(
				"/No EditScope Selected",
				{ "active" : False },
			)
			return result

		nodes = editScope.processors()
		nodes.extend( self.__userNodes( editScope ) )

		if nodes :
			for node in nodes :
				path = node.relativeName( editScope ).replace( ".", "/" )
				result.append(
					"/" + path,
					{
						"command" : functools.partial( GafferUI.NodeEditor.acquire, node )
					}
				)
		else :
			result.append(
				"/EditScope is Empty",
				{ "active" : False },
			)

		return result

	@staticmethod
	def __userNodes( editScope ) :

		nodes = Gaffer.Metadata.nodesWithMetadata( editScope, "editScope:includeInNavigationMenu" )
		return [ n for n in nodes if n.ancestor( Gaffer.EditScope ).isSame( editScope ) ]
