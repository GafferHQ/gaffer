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

import contextlib

import IECore

import Gaffer

class ParameterPath( Gaffer.Path ) :

	def __init__( self, rootParameter, path, root="/", filter=None, forcedLeafTypes = () ) :

		Gaffer.Path.__init__( self, path, root, filter=filter )

		assert( isinstance( rootParameter, IECore.Parameter ) )

		self.__forcedLeafTypes = forcedLeafTypes
		self.__rootParameter = rootParameter

	def isValid( self, canceller = None ) :

		try :
			self.__parameter()
			return True
		except :
			return False

	def isLeaf( self, canceller = None ) :

		try :
			p = self.__parameter()
		except :
			return False

		return isinstance( p, self.__forcedLeafTypes ) or not isinstance( p, IECore.CompoundParameter )

	def propertyNames( self, canceller = None ) :

		return Gaffer.Path.propertyNames( self ) + [ "parameter:parameter" ]

	def property( self, name, canceller = None ) :

		if name == "parameter:parameter" :
			with contextlib.suppress( Exception ) :
				return self.__parameter()
			return None

		return Gaffer.Path.property( self, name )

	def copy( self ) :

		return ParameterPath( self.__rootParameter, self[:], self.root(), self.getFilter(), self.__forcedLeafTypes )

	def _children( self, canceller ) :

		try :
			p = self.__parameter()
		except :
			return []

		if isinstance( p, IECore.CompoundParameter ) and not isinstance( p, self.__forcedLeafTypes ) :
			return [ ParameterPath( self.__rootParameter, self[:] + [ x ], self.root(), self.getFilter(), forcedLeafTypes=self.__forcedLeafTypes ) for x in p.keys() ]

		return []

	def __parameter( self ) :

		result = self.__rootParameter
		for p in self :
			result = result[p]

		return result

IECore.registerRunTimeTyped( ParameterPath, typeName = "GafferCortex::ParameterPath" )
