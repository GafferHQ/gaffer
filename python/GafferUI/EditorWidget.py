##########################################################################
#  
#  Copyright (c) 2011, John Haddon. All rights reserved.
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

from Gaffer import ScriptNode
import GafferUI

## The EditorWidget is a base class for all Widgets which somehow display or
# manipulate a ScriptNode or its children.
class EditorWidget( GafferUI.Widget ) :

	def __init__( self, qtWidget, scriptNode=None ) :
	
		GafferUI.Widget.__init__( self, qtWidget )
		
		self.setScriptNode( scriptNode )
	
	def setScriptNode( self, scriptNode ) :
	
		if not ( scriptNode is None or scriptNode.isInstanceOf( ScriptNode.staticTypeId() ) ) :
			raise TypeError( "Editor expects a ScriptNode instance or None.")
		
		self.__scriptNode = scriptNode
		
	def getScriptNode( self ) :
	
		return self.__scriptNode
	
	## This must be implemented by all derived classes as it used for serialisation of layouts.
	# It is not expected that the script being edited is also serialised as part of this operation - 
	# the intention is to create a copy of the layout with no script set yet.
	def __repr__( self ) :
	
		raise NotImplementedError
	
	@classmethod
	def types( cls ) :
	
		return cls.__namesToCreators.keys()
	
	@classmethod
	def create( cls, name, scriptNode ) :
	
		return cls.__namesToCreators[name]( scriptNode = scriptNode )
	
	@classmethod
	def registerType( cls, name, creator ) :
	
		cls.__namesToCreators[name] = creator
		
	__namesToCreators = {}
