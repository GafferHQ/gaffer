##########################################################################
#  
#  Copyright (c) 2012, John Haddon. All rights reserved.
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

## \todo We need to emit the changed signal when children are added
# and removed. It would be easiest to do this by having a descendantAddedSignal
# on GraphComponent (otherwise we have to make connections to every child everywhere).
class GraphComponentPath( Gaffer.Path ) :

	def __init__( self, rootComponent, path, root="/", filter=None ) :
		
		Gaffer.Path.__init__( self, path, root, filter=filter )
	
		assert( isinstance( rootComponent, Gaffer.GraphComponent ) )
	
		self.__rootComponent = rootComponent
	
	def isValid( self ) :
	
		try :
			self.__graphComponent()
			return True
		except :
			return False
	
	def isLeaf( self ) :
	
		return False
			
	def info( self ) :
	
		result = Gaffer.Path.info( self )
		if result is None :
			return None
					
		gc = None
		with IECore.IgnoredExceptions( Exception ) :
			gc = self.__dictEntry()
	
		if gc is not None :
			result["graphComponent:type"] = gc.typeName()
	
		return result
		
	def copy( self ) :
	
		return GraphComponentPath( self.__rootComponent, self[:], self.root(), self.getFilter() )
	
	def _children( self ) :
	
		try :
			e = self.__graphComponent()
			return [ GraphComponentPath( self.__rootComponent, self[:] + [ x ], self.root() ) for x in e.keys() ]
		except :
			return []
			
		return []

	def __graphComponent( self ) :
		
		e = self.__rootComponent
		for p in self :
			e = e[p]
		
		return e
