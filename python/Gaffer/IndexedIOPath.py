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

class IndexedIOPath( Gaffer.Path ) :

	def __init__( self, indexedIO, path, root="/", filter=None ) :

		Gaffer.Path.__init__( self, path, root, filter=filter )

		if isinstance( indexedIO, basestring ) :
			self.__indexedIO = IECore.IndexedIO.create( indexedIO, IECore.IndexedIO.OpenMode.Read )
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

		return e.entryType() == IECore.IndexedIO.EntryType.File

	def info( self ) :

		result = Gaffer.Path.info( self )
		if result is None :
			return None

		e = self.__entry()

		result["indexedIO:entryType"] = e.entryType()
		if e.entryType() == IECore.IndexedIO.EntryType.File :
			result["indexedIO:dataType"] = e.dataType()
			with IECore.IgnoredExceptions( Exception ) :
				result["indexedIO:arrayLength"] = e.arrayLength()

		return result

	def copy( self ) :

		return IndexedIOPath( self.__indexedIO, self[:], self.root(), self.getFilter() )

	def data( self ) :

		d = self.__indexedIO.directory( self[:-1] )
		return d.read( self[-1] )

	def _children( self ) :

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
