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

import six

import IECore

import Gaffer

class IndexedIOPath( Gaffer.Path ) :

	def __init__( self, indexedIO, path, root="/", filter=None ) :

		Gaffer.Path.__init__( self, path, root, filter=filter )

		if isinstance( indexedIO, six.string_types ) :
			self.__indexedIO = IECore.IndexedIO.create( indexedIO, IECore.IndexedIO.OpenMode.Read )
		else :
			self.__indexedIO = indexedIO

	def isValid( self, canceller = None ) :

		try :
			self.__entry()
			return True
		except :
			return False

	def isLeaf( self, canceller = None ) :

		try :
			e = self.__entry()
		except :
			return False

		return e.entryType() == IECore.IndexedIO.EntryType.File

	def propertyNames( self, canceller = None ) :

		return Gaffer.Path.propertyNames( self ) + [
			"indexedIO:entryType", "indexedIO:dataType", "indexedIO:arrayLength"
		]

	def property( self, name, canceller = None ) :

		result = Gaffer.Path.property( self, name )
		if result is not None :
			return result

		e = self.__entry()
		if name == "indexedIO:entryType" :
			return e.entryType()
		elif name == "indexedIO:dataType" :
			return e.dataType() if e.entryType() == IECore.IndexedIO.EntryType.File else None
		elif name == "indexedIO:arrayLength" :
			with IECore.IgnoredExceptions( Exception ) :
				return e.arrayLength()

		return None

	def copy( self ) :

		return IndexedIOPath( self.__indexedIO, self[:], self.root(), self.getFilter() )

	def data( self ) :

		d = self.__indexedIO.directory( self[:-1] )
		return d.read( self[-1] )

	def _children( self, canceller ) :

		try :
			d = self.__indexedIO.directory( self[:] )
		except :
			return []

		entries = d.entryIds()
		result = [ IndexedIOPath( self.__indexedIO, self[:] + [ x.value() ], self.root() ) for x in entries ]

		return result

	def __entry( self ) :

		if len( self ) == 0 :
			return IECore.IndexedIO.Entry( "/", IECore.IndexedIO.EntryType.Directory, IECore.IndexedIO.DataType.Invalid, 0 )

		d = self.__indexedIO.directory( self[:-1], IECore.IndexedIO.MissingBehaviour.ThrowIfMissing )
		return d.entry( self[-1] )

IECore.registerRunTimeTyped( IndexedIOPath, typeName = "GafferCortex::IndexedIOPath" )
