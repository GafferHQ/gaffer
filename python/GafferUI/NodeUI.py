##########################################################################
#  
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
#  Copyright (c) 2011-2012, Image Engine Design Inc. All rights reserved.
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

from __future__ import with_statement

import re
import fnmatch

import IECore

import Gaffer
import GafferUI

## This class forms the base class for all uis for nodes.
class NodeUI( GafferUI.Widget ) :
	
	## Derived classes may override the default ui by passing
	# their own top level widget - otherwise a standard ui is built
	# using the result of _plugsWidget().
	def __init__( self, node, topLevelWidget=None, **kw ) :
		
		buildUI = False
		if topLevelWidget is None :
			topLevelWidget = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical )
			buildUI = True
			
		GafferUI.Widget.__init__( self, topLevelWidget, **kw )
	
		self.__node = node
		self.__plugsWidget = None
		
		if buildUI :
			topLevelWidget.append( self._plugsWidget() )
			if hasattr( node, "execute" ) :
				executeButton = GafferUI.Button( "Execute" )
				topLevelWidget.append( executeButton )
				self.__executeButtonConnection = executeButton.clickedSignal().connect( Gaffer.WeakMethod( self.__executeClicked ) )
				topLevelWidget.append( GafferUI.Spacer( IECore.V2i( 1 ) ), expand = True )
			
	## Returns the node the ui represents.
	def node( self ) :
	
		return self.__node

	## Returns a Widget representing the plugs for the node.
	def _plugsWidget( self ) :
	
		if self.__plugsWidget is not None :
			return self.__plugsWidget
	
		self.__plugsWidget = GafferUI.ScrolledContainer( horizontalMode=GafferUI.ScrolledContainer.ScrollMode.Never, borderWidth=4 )

		column = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing=4 )
		self.__plugsWidget.setChild( column )
				
		for plug in self.node().children( Gaffer.Plug.staticTypeId() ) :
			if plug.getName().startswith( "__" ) or plug.direction() == Gaffer.Plug.Direction.Out :
				continue
			plugValueWidget = GafferUI.PlugValueWidget.create( plug )
			if plugValueWidget is not None :
				if isinstance( plugValueWidget, GafferUI.PlugValueWidget ) and not plugValueWidget.hasLabel() :
					column.append( GafferUI.PlugWidget( plugValueWidget ) )
				else :
					column.append( plugValueWidget )

		return self.__plugsWidget

	def __executeClicked( self, button ) :
	
		self.node().execute()

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
	def registerNodeUI( cls, nodeTypeId, nodeUIType ) :
	
		assert( issubclass( nodeUIType, NodeUI ) )
	
		cls.__nodeUIs[nodeTypeId] = nodeUIType
		
NodeUI.registerNodeUI( Gaffer.Node.staticTypeId(), NodeUI )
