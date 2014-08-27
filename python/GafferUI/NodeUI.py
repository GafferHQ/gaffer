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

import re
import fnmatch

import IECore

import Gaffer
import GafferUI

## This class forms the base class for all uis for nodes.
class NodeUI( GafferUI.Widget ) :

	def __init__( self, node, topLevelWidget, **kw ) :

		GafferUI.Widget.__init__( self, topLevelWidget, **kw )

		self.__node = node
		self.__readOnly = False

	## Returns the node the ui represents.
	def node( self ) :

		return self.__node

	## Should be implemented by derived classes to return
	# a PlugValueWidget they are using to represent the
	# specified plug. Since many UIs are built lazily on
	# demand, this may return None unless lazy=False is
	# passed to force creation of parts of the UI that
	# otherwise are not yet visible to the user.
	def plugValueWidget( self, plug, lazy=True ) :

		return None

	## Can be called to make the UI read only - must
	# be implemented appropriately by derived classes.
	def setReadOnly( self, readOnly ) :

		assert( isinstance( readOnly, bool ) )
		self.__readOnly = readOnly

	def getReadOnly( self ) :

		return self.__readOnly

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

GafferUI.Nodule.registerNodule( Gaffer.Node, "user", lambda plug : None )

Gaffer.Metadata.registerPlugValue( Gaffer.Node, "user", "nodeUI:section", "User" )
