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

class ClassLoaderPath( Gaffer.Path ) :

	def __init__( self, classLoader, path, root="/", filter=None ) :

		Gaffer.Path.__init__( self, path, root, filter )

		self.__classLoader = classLoader

	def isValid( self, canceller = None ) :

		if not len( self ) :
			# root is always valid
			return True

		p = str( self )[1:] # remove leading slash

		if p in self.__classLoader.classNames() :
			return True
		elif self.__classLoader.classNames( p + "/*" ) :
			return True

		return False

	def isLeaf( self, canceller = None ) :

		return str( self )[1:] in self.__classLoader.classNames()

	def propertyNames( self, canceller = None ) :

		return Gaffer.Path.propertyNames( self ) + [ "classLoader:versions" ]

	def property( self, name, canceller = None ) :

		if name == "classLoader:versions" :
			if not self.isLeaf() :
				return None
			return IECore.IntVectorData( self.__classLoader.versions( str( self )[1:] ) )

		return Gaffer.Path.property( self, name )

	def copy( self ) :

		return ClassLoaderPath( self.__classLoader, self[:], self.root(), self.getFilter() )

	def classLoader( self ) :

		return self.__classLoader

	def load( self, version=None ) :

		return self.__classLoader.load( str( self )[1:], version )

	def _children( self, canceller ) :

		result = []
		added = set()
		matcher = "/".join( self[:] ) + "/*" if len( self ) else "*"
		for n in self.__classLoader.classNames( matcher) :
			child = ClassLoaderPath( self.__classLoader, self.root() + n, filter=self.getFilter() )
			while len( child ) > len( self ) + 1 :
				del child[-1]
			if str( child ) not in added :
				result.append( child )
				added.add( str( child ) )

		return result

IECore.registerRunTimeTyped( ClassLoaderPath, typeName = "GafferCortex::ClassLoaderPath" )
