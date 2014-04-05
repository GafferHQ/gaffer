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

import IECore

import Gaffer
import GafferUI

class NodeEditor( GafferUI.NodeSetEditor ) :

	def __init__( self, scriptNode, **kw ) :
	
		self.__column = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical )
		
		GafferUI.NodeSetEditor.__init__( self, self.__column, scriptNode, **kw )
		
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
					GafferUI.Image( "info.png" )
				toolTip = "<h3>" + node.typeName().rpartition( ":" )[2] + "</h3>"
				description = Gaffer.Metadata.nodeDescription( node )
				if description :
					toolTip += "\n\n" + description
				infoSection.setToolTip( toolTip )
					
		frame = GafferUI.Frame( borderStyle=GafferUI.Frame.BorderStyle.None, borderWidth=0 )
		self.__column.append( frame, expand=True )
		self.__nodeUI = GafferUI.NodeUI.create( node )
		self.__nodeUI.setReadOnly( self.getReadOnly() )
		frame.setChild( self.__nodeUI )

	def _titleFormat( self ) :
	
		return GafferUI.NodeSetEditor._titleFormat( self, _maxNodes = 1, _reverseNodes = True, _ellipsis = False )
				
GafferUI.EditorWidget.registerType( "NodeEditor", NodeEditor )
