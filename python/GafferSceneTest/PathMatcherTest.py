##########################################################################
#  
#  Copyright (c) 2012, John Haddon. All rights reserved.
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

import unittest
import random

import IECore

import Gaffer
import GafferScene

class PathMatcherTest( unittest.TestCase ) :

	@staticmethod
	def generatePaths( seed, depthRange, numChildrenRange ) :
	
		nouns = [
			"Ball", "Building", "Car", "Tree", "Rampart", "Head", "Arm", 
			"Window", "Door", "Trailer", "Light", "FlockOfBirds", "Herd", "Sheep", 
			"Cow", "Wing", "Engine", "Mast", "Rock", "Road", "Sign", 
		]
		
		adjectives = [
			"big", "red", "metallic", "left", "right", "top", "bottom", "wooden",
			"front", "back", "lower", "upper", "magnificent", "hiRes", "loRes",
		]
		
		paths = []
		def buildWalk( parent="", depth=1 ) :
			
			if depth > random.randint( *depthRange ) :
				return
				
			for i in range( 0, random.randint( *numChildrenRange ) ) :
				path = parent + "/" + random.choice( adjectives ) + random.choice( nouns ) + str( i )
				paths.append( path )
				buildWalk( path, depth + 1 )
						
		random.seed( seed )
		buildWalk()
	
		return paths
	
	def testMatch( self ) :
	
		m = GafferScene.PathMatcher( [ "/a", "/red", "/b/c/d" ] )
	
		for path, result in [
			( "/a", GafferScene.Filter.Result.Match ),
			( "/red", GafferScene.Filter.Result.Match ),
			( "/re", GafferScene.Filter.Result.NoMatch ),
			( "/redThing", GafferScene.Filter.Result.NoMatch ),
			( "/b/c/d", GafferScene.Filter.Result.Match ),
			( "/c", GafferScene.Filter.Result.NoMatch ),
			( "/a/b", GafferScene.Filter.Result.NoMatch ),
			( "/blue", GafferScene.Filter.Result.NoMatch ),
			( "/b/c", GafferScene.Filter.Result.DescendantMatch ),
		] :
			self.assertEqual( m.match( path ), result )

	def testBuildScaling( self ) :
	
		# this test provides a useful means of measuring performance when
		# working on the PatchMatcher construction algorithm. it just
		# constructs a matcher for each of two different hierarchies :
		#
		#    * a deep hierarchy with relatively few children at each branch point
		#	 * a shallow hierarchy with large numbers of children at each branch point
		#
		# uncomment the timers to get useful information printed out.
	
		# deep hierarchy
		paths = IECore.StringVectorData( self.generatePaths( seed = 10, depthRange = ( 3, 14 ), numChildrenRange = ( 2, 6 ) ) )
 		t = IECore.Timer()
 		GafferScene.PathMatcher( paths )
 		#print t.stop()
 		
		# shallow hierarchy
		paths = IECore.StringVectorData( self.generatePaths( seed = 10, depthRange = ( 2, 2 ), numChildrenRange = ( 500, 1000 ) ) )
		t = IECore.Timer()
		GafferScene.PathMatcher( paths )
		#print t.stop()
	
	def testLookupScaling( self ) :
	
		# as above, except this time measuring lookup performance.
		
 		match = GafferScene.Filter.Result.Match

		# deep hierarchy
		paths = self.generatePaths( seed = 10, depthRange = ( 3, 14 ), numChildrenRange = ( 2, 6 ) )
 		matcher = GafferScene.PathMatcher( paths )
 		 		
 		t = IECore.Timer()
		for path in paths :
			self.assertEqual( matcher.match( path ), match )
		#print t.stop()
		
		# shallow hierarchy
		paths = self.generatePaths( seed = 10, depthRange = ( 2, 2 ), numChildrenRange = ( 500, 1000 ) )
 		matcher = GafferScene.PathMatcher( paths )
 		 		
 		t = IECore.Timer()
		for path in paths :
			self.assertEqual( matcher.match( path ), match )
		#print t.stop()
			
	def testDefaultConstructor( self ) :
	
		m = GafferScene.PathMatcher()
		self.assertEqual( m.match( "/" ), GafferScene.Filter.Result.NoMatch )
		
if __name__ == "__main__":
	unittest.main()
