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

import Gaffer

## The CompoundPathFilter class simply combines a number of other
# PathFilters, applying them in sequence.
class CompoundPathFilter( Gaffer.PathFilter ) :

	def __init__( self, filters=[], userData={} ) :

		Gaffer.PathFilter.__init__( self, userData )

		self.__filters = None
		self.__changedConnections = []
		self.setFilters( filters )

	def addFilter( self, filter ) :

		assert( filter not in self.__filters )

		self.__filters.append( filter )
		self.__changedConnections.append( filter.changedSignal().connect( Gaffer.WeakMethod( self.__filterChanged ) ) )
		if self.getEnabled() :
			self.changedSignal()( self )

	def removeFilter( self, filter ) :

		index = self.__filters.index( filter )
		del self.__filters[index]
		del self.__changedConnections[index]

		if self.getEnabled() :
			self.changedSignal()( self )

	def setFilters( self, filters ) :

		assert( type( filters ) is list )

		if filters == self.__filters :
			return

		# copy list so it can't be changed behind our back
		self.__filters = list( filters )

		# update changed connections
		self.__changedConnections = [ f.changedSignal().connect( Gaffer.WeakMethod( self.__filterChanged ) ) for f in self.__filters ]

		if self.getEnabled() :
			self.changedSignal()( self )

	def getFilters( self ) :

		# return a copy so the list can't be changed behind our back
		return list( self.__filters )

	def _filter( self, paths ) :

		for f in self.__filters :
			paths = f.filter( paths )

		return paths

	def __filterChanged( self, childFilter ) :

		assert( childFilter in self.__filters )

		if self.getEnabled() :
			self.changedSignal()( self )
