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

import IECore

import Gaffer
import GafferTest
import GafferScene

class SceneTestCase( GafferTest.TestCase ) :

	def assertSceneValid( self, scenePlug ) :
	
		def walkScene( scenePath ) :

			thisBound = scenePlug.bound( scenePath )
			
			o = scenePlug.object( scenePath )
			if isinstance( o, IECore.VisibleRenderable ) :
				 if not thisBound.contains( o.bound() ) :
					self.fail( "Bound %s does not contain object %s at %s" % ( thisBound, o.bound(), scenePath ) )
	
			unionOfTransformedChildBounds = IECore.Box3f()
			childNames = scenePlug.childNames( scenePath )
			for childName in childNames :
				
				if scenePath == "/" :
					childPath = scenePath + childName
				else :
					childPath = scenePath + "/" + childName
				
				childBound = scenePlug.bound( childPath )
				childTransform = scenePlug.transform( childPath )
				childBound = childBound.transform( childTransform )
				
				unionOfTransformedChildBounds.extendBy( childBound )
				
				walkScene( childPath )
			
			if not thisBound.contains( unionOfTransformedChildBounds ) :
				self.fail( "Bound ( %s ) does not contain children ( %s ) at %s" % ( thisBound, unionOfTransformedChildBounds, scenePath ) )

		# check that the root doesn't have any properties it shouldn't
		self.assertEqual( scenePlug.attributes( "/" ), IECore.CompoundObject() )
		self.assertEqual( scenePlug.transform( "/" ), IECore.M44f() )
		self.assertEqual( scenePlug.object( "/" ), IECore.NullObject() )
		
		# then walk the scene to check the bounds
		walkScene( "/" )

	def __childPlugNames( self, childPlugNames, childPlugNamesToIgnore ) :
	
		if childPlugNames is None :
			childPlugNames = ( "bound", "transform", "attributes", "object", "childNames" )
		childPlugNames = set( childPlugNames )	
		childPlugNames -= set( childPlugNamesToIgnore )
		
		return childPlugNames

	def assertPathsEqual( self, scenePlug1, scenePath1, scenePlug2, scenePath2, childPlugNames = None, childPlugNamesToIgnore = () ) :
	
		childPlugNames = self.__childPlugNames( childPlugNames, childPlugNamesToIgnore )
		for childPlugName in childPlugNames :
			getFn1 = getattr( scenePlug1, childPlugName )
			getFn2 = getattr( scenePlug2, childPlugName )
			self.assertEqual( getFn1( scenePath1 ), getFn2( scenePath2 ) )

	def assertScenesEqual( self, scenePlug1, scenePlug2, scenePlug2PathPrefix = "", childPlugNames = None, childPlugNamesToIgnore = (), pathsToIgnore = () ) :
			
		def walkScene( scenePath ) :

			if scenePath not in pathsToIgnore :
				self.assertPathsEqual( scenePlug1, scenePath, scenePlug2, scenePlug2PathPrefix + scenePath, childPlugNames, childPlugNamesToIgnore )
			childNames = scenePlug1.childNames( scenePath )
			for childName in childNames :
				if scenePath == "/" :
					childPath = scenePath + childName
				else :
					childPath = scenePath + "/" + childName
		
				walkScene( childPath )
	
		walkScene( "/" )

	def assertPathHashesEqual( self, scenePlug1, scenePath1, scenePlug2, scenePath2, childPlugNames = None, childPlugNamesToIgnore = () ) :
	
		childPlugNames = self.__childPlugNames( childPlugNames, childPlugNamesToIgnore )
		for childPlugName in childPlugNames :
			hashFn1 = getattr( scenePlug1, childPlugName + "Hash" )
			hashFn2 = getattr( scenePlug2, childPlugName + "Hash" )
			self.assertEqual( hashFn1( scenePath1 ), hashFn2( scenePath2 ) )

	def assertPathHashesNotEqual( self, scenePlug1, scenePath1, scenePlug2, scenePath2, childPlugNames = None, childPlugNamesToIgnore = () ) :
	
		childPlugNames = self.__childPlugNames( childPlugNames, childPlugNamesToIgnore )
		for childPlugName in childPlugNames :
			hashFn1 = getattr( scenePlug1, childPlugName + "Hash" )
			hashFn2 = getattr( scenePlug2, childPlugName + "Hash" )
			self.assertNotEqual( hashFn1( scenePath1 ), hashFn2( scenePath2 ) )
		
	def assertSceneHashesEqual( self, scenePlug1, scenePlug2, childPlugNames = None, childPlugNamesToIgnore = (), pathsToIgnore = () ) :
	
		childPlugNames = self.__childPlugNames( childPlugNames, childPlugNamesToIgnore )
		
		def walkScene( scenePath ) :

			c = Gaffer.Context()
			c["scene:path"] = scenePath
			with c :
				if scenePath not in pathsToIgnore :
					for childPlugName in childPlugNames :
						self.assertEqual( scenePlug1[childPlugName].hash(), scenePlug2[childPlugName].hash() )
				childNames = scenePlug1["childNames"].getValue() or []
				for childName in childNames :
					if scenePath == "/" :
						childPath = scenePath + childName
					else :
						childPath = scenePath + "/" + childName
			
					walkScene( childPath )
		
		walkScene( "/" )
		
	def assertSceneHashesNotEqual( self, scenePlug1, scenePlug2, childPlugNames = None, childPlugNamesToIgnore = (), pathsToIgnore = () ) :
	
		childPlugNames = self.__childPlugNames( childPlugNames, childPlugNamesToIgnore )
		
		def walkScene( scenePath ) :

			c = Gaffer.Context()
			c["scene:path"] = scenePath
			with c :
				if scenePath not in pathsToIgnore :
					for childPlugName in childPlugNames :
						self.assertNotEqual( scenePlug1[childPlugName].hash(), scenePlug2[childPlugName].hash() )
				childNames = scenePlug1["childNames"].getValue() or []
				for childName in childNames :
					if scenePath == "/" :
						childPath = scenePath + childName
					else :
						childPath = scenePath + "/" + childName
			
					walkScene( childPath )
		
		walkScene( "/" )
		
	def assertBoxesEqual( self, box1, box2 ) :
	
		for n in "min", "max" :
			v1 = getattr( box1, n )
			v2 = getattr( box1, n )
			for i in range( 0, 3 ) :
				self.assertEqual( v1[i], v2[i] )
				
	def assertBoxesAlmostEqual( self, box1, box2, places ) :
	
		for n in "min", "max" :
			v1 = getattr( box1, n )
			v2 = getattr( box1, n )
			for i in range( 0, 3 ) :
				self.assertAlmostEqual( v1[i], v2[i], places )			
		