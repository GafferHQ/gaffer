##########################################################################
#  
#  Copyright (c) 2012, Image Engine Design Inc. All rights reserved.
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

class IndexedIOPath( Gaffer.Path ) :

	def __init__( self, indexedIO, path, filter=None ) :
		
		Gaffer.Path.__init__( self, path, filter )
	
		if isinstance( indexedIO, basestring ) :
			self.__indexedIO = IECore.IndexedIOInterface.create( indexedIO, "/", IECore.IndexedIOOpenMode.Read )
		else :
			self.__indexedIO = indexedIO
	
	def isValid( self ) :
	
		try :
			self.__entry()
			return True
		except :
			return False
	
	def isLeaf( self ) :
	
		try :
			e = self.__entry()
		except :
			return False
			
		return e.entryType() == IECore.IndexedIOEntryType.File
		
	def info( self ) :
	
		result = Gaffer.Path.info( self )
		if result is None :
			return None
		
		e = None
		with IECore.IgnoredExceptions( Exception ) :
			e = self.__entry()
		
		if e is None :
			return result
			
		result["indexedIO:entryType"] = e.entryType()
		if e.entryType() == IECore.IndexedIOEntryType.File :
			result["indexedIO:dataType"] = e.dataType()
			with IECore.IgnoredExceptions( Exception ) :
				result["indexedIO:arrayLength"] = e.arrayLength()
		
		return result
		
	def copy( self ) :
	
		return IndexedIOPath( self.__indexedIO, self[:], self.getFilter() )
	
	def data( self ) :
	
		return self.__indexedIO.read( str( self ) )
	
	def _children( self ) :
	
		e = None
		try :
			e = self.__entry()
		except :
			return []
		
		if e is None or e.entryType() == IECore.IndexedIOEntryType.File :
			return []
			
		self.__indexedIO.chdir( str( self ) )
		entries = self.__indexedIO.ls()
		result = [ IndexedIOPath( self.__indexedIO, self[:] + [ x.id() ] ) for x in entries ]
		self.__indexedIO.chdir( "/" )
		
		return result

	def __entry( self ) :
		
		return self.__indexedIO.ls( str( self ) )