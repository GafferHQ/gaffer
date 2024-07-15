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

import IECore

import Gaffer
import GafferUI

## Abstract base class for toolbars representing nodes, typically
# used in the Viewer. Nodes may have up to four toolbars - one for
# each edge of the frame. See StandardNodeToolbar for a concrete
# implementation suitable for most purposes.
class NodeToolbar( GafferUI.Widget ) :

	def __init__( self, node, topLevelWidget, **kw ) :

		GafferUI.Widget.__init__( self, topLevelWidget, **kw )

		self.__node = node

		scriptNode = self.__node.scriptNode()
		self.__context = GafferUI.PlugValueWidget._PlugValueWidget__defaultContext( node )

	## Returns the node the toolbar represents.
	def node( self ) :

		return self.__node

	## Returns the context in which the toolbar shows its plugs.
	def context( self ) :

		return self.__context

	## Creates a NodeToolbar instance for the specified node and edge.
	# Note that not all nodes have toolbars, so None may be returned.
	@classmethod
	def create( cls, node, edge = GafferUI.Edge.Top ) :

		# Try to create a toolbar using metadata.
		toolbarType = Gaffer.Metadata.value( node, "nodeToolbar:{}:type".format( edge.name.lower() ) )
		if toolbarType is not None :
			if toolbarType == "" :
				return None
			path = toolbarType.split( "." )
			toolbarClass = __import__( path[0] )
			for n in path[1:] :
				toolbarClass = getattr( toolbarClass, n )
			return toolbarClass( node )

		# Fall back to deprecated registry.
		if edge == GafferUI.Edge.Top :
			nodeHierarchy = IECore.RunTimeTyped.baseTypeIds( node.typeId() )
			for typeId in [ node.typeId() ] + nodeHierarchy :
				creator = cls.__creators.get( typeId, None )
				if creator is not None :
					return creator( node )

		return None

	__creators = {}
	## Registers a subclass of NodeToolbar to be used with a specific node type.
	## \deprecated. Use "nodeToolbar:top|bottom|left|right:type" metadata instead.
	@classmethod
	def registerCreator( cls, nodeClassOrTypeId, toolbarCreator ) :

		assert( callable( toolbarCreator ) )

		if isinstance( nodeClassOrTypeId, IECore.TypeId ) :
			nodeTypeId = nodeClassOrTypeId
		else :
			nodeTypeId = nodeClassOrTypeId.staticTypeId()

		cls.__creators[nodeTypeId] = toolbarCreator
