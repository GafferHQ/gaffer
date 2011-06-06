##########################################################################
#  
#  Copyright (c) 2011, John Haddon. All rights reserved.
#  Copyright (c) 2011, Image Engine Design Inc. All rights reserved.
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

import Gaffer
import GafferUI

QtCore = GafferUI._qtImport( "QtCore" )

## The NodeSetEditor is a base class for all Editors which focus their
# editing on a subset of nodes beneath a ScriptNode. This set defaults
# to the ScriptNode.selection() but can be modified to be any Set of nodes.
class NodeSetEditor( GafferUI.EditorWidget ) :

	def __init__( self, topLevelWidget, scriptNode ) :
	
		GafferUI.EditorWidget.__init__( self, topLevelWidget, scriptNode )
		
		self.__updateScheduled = False
			
	def setScriptNode( self, scriptNode ) :
	
		GafferUI.EditorWidget.setScriptNode( self, scriptNode )
		
		if scriptNode :
			self.setNodeSet( scriptNode.selection() )
		else :
			self.setNodeSet( Gaffer.Set() )
			
	def setNodeSet( self, nodeSet ) :
	
		self.__nodeSet = nodeSet
		self.__memberAddedConnection = self.__nodeSet.memberAddedSignal().connect( Gaffer.WeakMethod( self.__membersChanged ) )
		self.__memberRemovedConnection = self.__nodeSet.memberRemovedSignal().connect( Gaffer.WeakMethod( self.__membersChanged ) )
		self._updateFromSet()
		
	def getNodeSet( self ) :
	
		return self.__nodeSet
		
	def _updateFromSet( self ) :
	
		raise NotImplementedError

	def __membersChanged( self, set, member ) :
		
		if self.__updateScheduled :
			return
		
		QtCore.QTimer.singleShot( 0, self.__updateTimeout )
		self.__updateScheduled = True
	
	def __updateTimeout( self ) :
		
		self.__updateScheduled = False
		self._updateFromSet()
