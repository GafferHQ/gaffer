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
import IECoreAlembic

import Gaffer

class AlembicPath( Gaffer.Path ) :

	def __init__( self, fileNameOrAlembicInput, path, root="/", filter=None ) :
	
		Gaffer.Path.__init__( self, path, root, filter=filter )
				
		if isinstance( fileNameOrAlembicInput, basestring ) :
			self.__rootInput = IECoreAlembic( fileNameOrAlembicInput )
		else :
			assert( isinstance( fileNameOrAlembicInput, IECoreAlembic.AlembicInput ) )
			self.__rootInput = fileNameOrAlembicInput

	def isValid( self ) :
	
		try :
			self.__input()
			return True
		except :
			return False
	
	def isLeaf( self ) :
	
		# any alembic object may have children.
		return False
		
	def info( self ) :
	
		return Gaffer.Path.info( self )
				
	def _children( self ) :
	
		childNames = self.__input().childNames()
		return [ AlembicPath( self.__rootInput, self[:] + [ x ], self.root() ) for x in childNames ]
			
	def copy( self ) :
	
		return AlembicPath( self.__rootInput, self[:], self.root(), self.getFilter() )
		
	def __input( self ) :
	
		result = self.__rootInput
		for p in self :
			result = result.child( p )
			
		return result
