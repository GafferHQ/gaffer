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

class DictPath( Gaffer.Path ) :

	def __init__( self, dict, path, root="/", filter=None, dictTypes = ( dict, IECore.CompoundData, IECore.CompoundObject ) ) :

		Gaffer.Path.__init__( self, path, root, filter=filter )

		assert( isinstance( dict, dictTypes ) )

		self.__dictTypes = dictTypes
		self.__dict = dict

	## Returns the dictionary that this path represents. If this
	# is modified, then it is the responsibility of the modifying
	# code to emit pathChangedSignal().
	def dict( self ) :

		return self.__dict

	def isValid( self, canceller = None ) :

		try :
			self.__dictEntry()
			return True
		except :
			return False

	def isLeaf( self, canceller = None ) :

		try :
			e = self.__dictEntry()
			return not isinstance( e, self.__dictTypes )
		except :
			return False

	def propertyNames( self, canceller = None ) :

		return Gaffer.Path.propertyNames( self ) + [ "dict:value" ]

	def property( self, name, canceller = None ) :

		if name == "dict:value" :
			with IECore.IgnoredExceptions( Exception ) :
				e = self.__dictEntry()
				if not isinstance( e, self.__dictTypes ) :
					return e

		return Gaffer.Path.property( self, name )

	def copy( self ) :

		return DictPath( self.__dict, self[:], self.root(), self.getFilter(), self.__dictTypes )

	def _children( self, canceller ) :

		try :
			e = self.__dictEntry()
			if isinstance( e, self.__dictTypes ) :
				return [ DictPath( self.__dict, self[:] + [ x ], self.root(), dictTypes=self.__dictTypes ) for x in e.keys() ]
		except :
			return []

		return []

	def __dictEntry( self ) :

		e = self.__dict
		for p in self :
			e = e[p]

		return e

IECore.registerRunTimeTyped( DictPath, typeName = "Gaffer::DictPath" )
