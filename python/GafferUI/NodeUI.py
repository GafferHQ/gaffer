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

import os.path
import functools

import IECore

import Gaffer
import GafferUI

def __documentationURL( node ) :

	fileName = "$GAFFER_ROOT/doc/gaffer/html/Reference/NodeReference/" + node.typeName().replace( "::", "/" ) + ".html"
	fileName = os.path.expandvars( fileName )
	return "file://" + fileName if os.path.isfile( fileName ) else ""

Gaffer.Metadata.registerNode(

	Gaffer.Node,

	"description",
	"""
	A container for plugs.
	""",

	"documentation:url", __documentationURL,
	"renameable", True,

	plugs = {

		"user" : {

			"description" :
			"""
			Container for user-defined plugs. Nodes
			should never make their own plugs here,
			so users are free to do as they wish.
			""",

			"layout:index" : -1, # Last
			"layout:section" : "User",
			"nodule:type" : "",
			"plugValueWidget:type" : "GafferUI.LayoutPlugValueWidget",

			"layout:customWidget:addButton:widgetType" : "GafferUI.UserPlugs.plugCreationWidget",
			"layout:customWidget:addButton:index" : -1, # Last

		},

		"user.*" : {

			"deletable" : True,
			"renameable" : True,

		},

		"*" : {

			"layout:section" : "Settings"

		},

		"..." : {

			# Just because a plug is renameable and/or deletable on one node
			# does not mean it should still be when promoted to another.
			"renameable:promotable" : False,
			"deletable:promotable" : False,

		},

	}

)

##########################################################################
# NodeUI
##########################################################################

## This class forms the base class for all uis for nodes.
class NodeUI( GafferUI.Widget ) :

	def __init__( self, node, topLevelWidget, **kw ) :

		GafferUI.Widget.__init__( self, topLevelWidget, **kw )

		self.__node = node

	## Returns the node the ui represents.
	def node( self ) :

		return self.__node

	## Should be implemented by derived classes to return
	# the PlugValueWidget they are using to represent the
	# specified plug. Returns `None` if there is no such
	# widget.
	def plugValueWidget( self, plug ) :

		return None

	## Creates a NodeUI instance for the specified node.
	@classmethod
	def create( cls, node ) :

		nodeHierarchy = IECore.RunTimeTyped.baseTypeIds( node.typeId() )
		for typeId in [ node.typeId() ] + nodeHierarchy :
			nodeUI = cls.__nodeUIs.get( typeId, None )
			if nodeUI is not None :
				return nodeUI( node )

		assert( 0 )

	__nodeUIs = {}
	## Registers a subclass of NodeUI to be used with a specific node type.
	@classmethod
	def registerNodeUI( cls, nodeClassOrTypeId, nodeUICreator ) :

		assert( callable( nodeUICreator ) )

		if isinstance( nodeClassOrTypeId, IECore.TypeId ) :
			nodeTypeId = nodeClassOrTypeId
		else :
			nodeTypeId = nodeClassOrTypeId.staticTypeId()

		cls.__nodeUIs[nodeTypeId] = nodeUICreator

	@staticmethod
	def appendPlugDeletionMenuDefinitions( plugOrPlugValueWidget, menuDefinition ) :

		if isinstance( plugOrPlugValueWidget, GafferUI.PlugValueWidget ) :
			plug = plugOrPlugValueWidget.getPlug()
		else :
			plug = plugOrPlugValueWidget

		while plug is not None :
			if Gaffer.Metadata.value( plug, "deletable" ) :
				break
			plug = plug.parent() if isinstance( plug.parent(), Gaffer.Plug ) else None

		if plug is None :
			return

		if len( menuDefinition.items() ) :
			menuDefinition.append( "/DeleteDivider", { "divider" : True } )

		menuDefinition.append( "/Delete", { "command" : functools.partial( NodeUI.__deletePlug, plug ), "active" : not Gaffer.MetadataAlgo.readOnly( plug ) } )

	@staticmethod
	def __deletePlug( plug ) :

		with Gaffer.UndoScope( plug.ancestor( Gaffer.ScriptNode ) ) :
			plug.parent().removeChild( plug )
