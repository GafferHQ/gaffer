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

class SequencePath( Gaffer.Path ) :

	def __init__( self, path, root="/", minSequenceSize=1, filter=None ) :
	
		if not isinstance( path, Gaffer.Path ) :
			path = Gaffer.FileSystemPath( path, root )
		
		Gaffer.Path.__init__( self, path[:], path.root(), filter=filter )
				
		# we use the seed for creating base paths whenever we need them
		self.__basePathSeed = path
		self.__minSequenceSize = minSequenceSize
		
	def isValid( self ) :
			
		for p in self.__basePaths() :
			if not p.isValid() :
				return False
			
		return True
	
	def isLeaf( self ) :
	
		for p in self.__basePaths() :
			if not p.isLeaf() :
				return False
			
		return True
	
	def info( self ) :
		
		result = Gaffer.Path.info( self )
		if result is None :
			return None
		
		def average( values ) :
		
			return sum( values ) / len( values )
		
		def mostCommon( values ) :
		
			counter = {}
			for value in values :
				if value in counter :
					counter[value] += 1
				else :
					counter[value] = 1
					
			maxCount = 0
			mostCommonValue = None
			for value, count in counter.items() :
				if count > maxCount :
					mostCommonValue = value
					maxCount = count
					
			return mostCommonValue
			
		combiners = {
			"fileSystem:owner" : mostCommon,
			"fileSystem:group" : mostCommon,
			"fileSystem:modificationTime" : max,
			"fileSystem:accessTime" : max,
			"fileSystem:size" : sum,
		}
		
		infos = [ path.info() for path in self.__basePaths() ]
		if len( infos ) :
			for key, exampleValue in infos[0].items() :
				if key in result :
					continue
				combiner = combiners.get( key, None )
				if combiner is None :
					if isinstance( exampleValue, ( int, float ) ) :
						combiner = average
					elif isinstance( exampleValue, basestring ) :
						combiner = mostCommon
				if combiner is not None :
					values = [ i[key] for i in infos ]
					result[key] = combiner( values )
		
		return result
	
	def _children( self ) :
	
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
		if isinstance( path, basestring ) :
			result.setFromString( path )
		else :
			result.setFromPath( path )
		
		return result

	def __basePaths( self ) :
	
		sequence = None
		with IECore.IgnoredExceptions( Exception ) :
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
