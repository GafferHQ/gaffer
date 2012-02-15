##########################################################################
#  
#  Copyright (c) 2011, John Haddon. All rights reserved.
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

import Gaffer
import GafferUI

class PlugValueWidget( GafferUI.Widget ) :

	def __init__( self, topLevelWidget, plug, **kw ) :
	
		GafferUI.Widget.__init__( self, topLevelWidget, **kw )
	
		self.setPlug( plug )
		
	def setPlug( self, plug ) :
	
		self.__plug = plug

		if self.__plug is not None :
			self.__plugSetConnection = plug.node().plugSetSignal().connect( Gaffer.WeakMethod( self.__plugSet ) )
			self.__plugDirtiedConnection = plug.node().plugDirtiedSignal().connect( Gaffer.WeakMethod( self.__plugDirtied ) )
			self.__plugInputChangedConnection = plug.node().plugInputChangedSignal().connect( Gaffer.WeakMethod( self.__plugInputChanged ) )
		else :
			self.__plugSetConnection = None
			self.__plugDirtiedConnection = None
			self.__plugInputChangedConnection = None

		self.updateFromPlug()
		
	def getPlug( self ) :
	
		return self.__plug
	
	## Must be implemented by subclasses so that the widget reflects the current
	# status of the plug.	
	def updateFromPlug( self ) :
	
		raise NotImplementedError
	
	## Returns True if the plug value is editable - that is the plug
	# is an input plug and it has no incoming connection.
	def _editable( self ) :
	
		plug = self.getPlug()
		
		if plug is None :
			return False
		
		if plug.direction()==Gaffer.Plug.Direction.Out :
			return False
		if plug.getInput() :
			return False
		
		return True
			
	@classmethod
	def create( cls, plug ) :

		typeId = plug.typeId()
		if typeId in cls.__typesToCreators :
		
			return cls.__typesToCreators[typeId]( plug )
			
		return None
	
	## Registers a PlugValueWidget type for a specific Plug type. Note
	# that the NodeUI.registerPlugValueWidget function provides the
	# opportunity to further customise the type of Widget used by the NodeUI
	# based on the node type and plug name.
	@classmethod
	def registerType( cls, typeId, creator ) :
	
		cls.__typesToCreators[typeId] = creator
	
	__typesToCreators = {}	
		
	def __plugSet( self, plug ) :
	
		if plug.isSame( self.__plug ) :
		
			self.updateFromPlug()	

	def __plugDirtied( self, plug ) :
	
		if plug.isSame( self.__plug ) :
		
			self.updateFromPlug()	

	def __plugInputChanged( self, plug ) :
	
		if plug.isSame( self.__plug ) :
		
			self.updateFromPlug()	
