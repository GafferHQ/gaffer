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

import collections
import contextlib

import IECore

import Gaffer

## \deprecated: Use FileSystemPath and FileSequencePathFilter instead.
class SequencePath( Gaffer.Path ) :

	def __init__( self, path, root="/", minSequenceSize=1, filter=None ) :

		if not isinstance( path, Gaffer.Path ) :
			if isinstance( path, str ) :
				path = Gaffer.FileSystemPath( path )
			else :
				path = Gaffer.FileSystemPath( path, root )

		Gaffer.Path.__init__( self, path[:], path.root(), filter=filter )

		# we use the seed for creating base paths whenever we need them
		self.__basePathSeed = path
		self.__minSequenceSize = minSequenceSize

	def isValid( self, canceller = None ) :

		for p in self.__basePaths() :
			if not p.isValid() :
				return False

		return True

	def isLeaf( self, canceller = None ) :

		for p in self.__basePaths() :
			if not p.isLeaf() :
				return False

		return True

	def propertyNames( self, canceller = None ) :

		return self.__basePathSeed.propertyNames()

	def property( self, name, canceller = None ) :

		result = Gaffer.Path.property( self, name )
		if result is not None :
			return result

		def average( values ) :

			return sum( values ) / len( values )

		def mostCommon( values ) :

			return collections.Counter( values ).most_common( 1 )[0][0]

		combiners = {
			"fileSystem:owner" : mostCommon,
			"fileSystem:group" : mostCommon,
			"fileSystem:modificationTime" : max,
			"fileSystem:accessTime" : max,
			"fileSystem:size" : sum,
		}

		values = [ path.property( name ) for path in self.__basePaths() ]

		combiner = combiners.get( name, None )
		if combiner is None :
			if isinstance( values[0], ( int, float ) ) :
				combiner = average
			elif isinstance( values[0], str ) :
				combiner = mostCommon

		if combiner is not None :
			return combiner( values )

		return None

	def _children( self, canceller ) :

		p = self.__basePath( self )

		children = p.children()

		nonLeafPaths = []
		leafPathStrings = []
		for child in children :
			if child.isLeaf() :
				leafPathStrings.append( str( child ) )
			else :
				nonLeafPaths.append( child )

		sequences = IECore.findSequences( leafPathStrings, self.__minSequenceSize )

		result = []
		for path in sequences + nonLeafPaths :
			result.append( SequencePath( self.__basePath( str( path ) ), minSequenceSize=self.__minSequenceSize, filter = self.getFilter() ) )

		return result

	def copy( self ) :

		result = SequencePath( self.__basePathSeed, minSequenceSize = self.__minSequenceSize, filter = self.getFilter() )
		result.setFromPath( self )
		return result

	def __basePath( self, path ) :

		result = self.__basePathSeed.copy()
		if isinstance( path, str ) :
			result.setFromString( path )
		else :
			result.setFromPath( path )

		return result

	def __basePaths( self ) :

		sequence = None
		with contextlib.suppress( Exception ) :
			sequence = IECore.FileSequence( str( self ) )

		result = []
		if sequence :
			for f in sequence.fileNames() :
				result.append( self.__basePath( f ) )
		else :
			result.append( self.__basePath( self ) )

		return result

	def __isSequence( self ) :

		s = str( self )
		if IECore.FileSequence.fileNameValidator().match( s ) :
			return True

		return False

IECore.registerRunTimeTyped( SequencePath, typeName = "Gaffer::SequencePath" )
