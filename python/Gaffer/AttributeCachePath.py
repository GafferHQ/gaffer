##########################################################################
#
#  Copyright (c) 2012-2013, Image Engine Design Inc. All rights reserved.
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

class AttributeCachePath( Gaffer.Path ) :

	def __init__( self, attributeCache, path, root="/", filter=None ) :

		Gaffer.Path.__init__( self, path, root, filter=filter )

		if isinstance( attributeCache, basestring ) :
			self.__attributeCache = IECore.AttributeCache( attributeCache, IECore.IndexedIO.OpenMode.Read )
		else :
			self.__attributeCache = attributeCache

	def isValid( self ) :

		if len( self ) == 0 :
			return True
		elif len( self ) == 1 :
			return self[0] in ( "header", "objects" )
		elif len( self ) == 2 :
			if self[0] == "header" :
				return self[1] in self.__attributeCache.headers()
			elif self[0] == "objects" :
				return self.__attributeCache.contains( self[1] )
		elif len( self ) == 3 :
			if self[0] != "objects" :
				return False
			return self.__attributeCache.contains( self[1], self[2] )

		return False

	def isLeaf( self ) :

		if len( self ) == 2 and self[0] == "header" :
			return True
		elif len( self ) == 3 and self[0] == "objects" :
			return True

		return False

	def info( self ) :

		result = Gaffer.Path.info( self )
		if result is None :
			return None

		return result

	def copy( self ) :

		return AttributeCachePath( self.__attributeCache, self[:], self.root(), self.getFilter() )

	def data( self ) :

		if self[0] == "header" :
			return self.__attributeCache.readHeader( self[1] )
		else :
			return self.__attributeCache.read( self[1], self[2] )

		return None

	def _children( self ) :

		paths = []
		if len( self ) == 0 :
			paths.append( [ "header" ] )
			paths.append( [ "objects" ] )
		elif len( self ) == 1 :
			if self[0] == "header" :
				paths += [ [ "header", h ] for h in self.__attributeCache.headers() ]
			elif self[0] == "objects" :
				paths += [ [ "objects", o ] for o in self.__attributeCache.objects() ]
		elif len( self ) == 2 :
			if self[0] == "objects" :
				paths += [ self[:] + [ a ] for a in self.__attributeCache.attributes( self[1] ) ]

		return [ AttributeCachePath( self.__attributeCache, path, self.root(), self.getFilter() ) for path in paths ]
