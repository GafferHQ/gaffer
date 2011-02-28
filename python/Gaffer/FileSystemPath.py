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

import os
import pwd
import grp

import Gaffer

class FileSystemPath( Gaffer.Path ) :

	def __init__( self, path ) :
	
		if isinstance( path, basestring ) :
			if len( path ) and path[0] != "/" :
				path = os.path.join( os.getcwd(), path )
	
		Gaffer.Path.__init__( self, path )
									
	def isValid( self ) :
	
		return os.path.exists( str( self ) )
	
	def isLeaf( self ) :
	
		return self.isValid() and not os.path.isdir( str( self ) )
	
	def info( self ) :
	
		result = Gaffer.Path.info( self )
		if result is None :
			return None
					
		s = os.stat( str( self ) )
		try :
			p = pwd.getpwuid( s.st_uid )
		except :
			p = None
		try :
			g = grp.getgrgid( s.st_gid )
		except :
			g = None
				
		result["fileSystem:owner"] = p.pw_name if p is not None else ""
		result["fileSystem:group"] = g.gr_name if g is not None else ""
		result["fileSystem:modificationTime"] = s.st_mtime
		result["fileSystem:accessTime"] = s.st_atime
		
		return result
	
	def _children( self ) :
	
		try :
			c = os.listdir( str( self ) )
		except :
			return []
			
		return [ FileSystemPath( self[:] + [ x ] ) for x in c ]

