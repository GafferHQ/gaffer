##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

			# at least pull on the attributes, even though we don't have any test cases for that right now
			attributes = scenePlug.attributes( scenePath )

			thisBound = scenePlug.bound( scenePath )

			o = scenePlug.object( scenePath, _copy = False )
			if isinstance( o, IECore.VisibleRenderable ) :
				 if not thisBound.contains( o.bound() ) :
					self.fail( "Bound %s does not contain object %s at %s" % ( thisBound, o.bound(), scenePath ) )

			unionOfTransformedChildBounds = IECore.Box3f()
			childNames = scenePlug.childNames( scenePath, _copy = False )
			for childName in childNames :

				childPath = IECore.InternedStringVectorData( scenePath )
				childPath.append( childName )

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
		walkScene( IECore.InternedStringVectorData() )

		self.assertSetsValid( scenePlug )

	def assertPathExists( self, scenePlug, path ) :

		if isinstance( path, str ) :
			path = path.strip( "/" ).split( "/" )

		for i in range( 0, len( path ) ) :
			self.assertTrue( path[i] in scenePlug.childNames( "/" + "/".join( path[:i] ) ) )

	def assertSetsValid( self, scenePlug ) :

		globals = scenePlug["globals"].getValue()
		if "gaffer:sets" in globals :
			for s in globals["gaffer:sets"].values() :
				for path in s.value.paths() :
					self.assertPathExists( scenePlug, path )

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

		def walkScene( scenePath1, scenePath2 ) :

			if ( not pathsToIgnore ) or ( self.__pathToString( scenePath1 ) not in pathsToIgnore ) :
				self.assertPathsEqual( scenePlug1, scenePath1, scenePlug2, scenePath2, childPlugNames, childPlugNamesToIgnore )
			childNames = scenePlug1.childNames( scenePath1 )
			for childName in childNames :

				childPath1 = IECore.InternedStringVectorData( scenePath1 )
				childPath1.append( childName )

				childPath2 = IECore.InternedStringVectorData( scenePath2 )
				childPath2.append( childName )

				walkScene( childPath1, childPath2 )

		scenePath1 = IECore.InternedStringVectorData()
		scenePath2 = IECore.InternedStringVectorData()
		if scenePlug2PathPrefix :
			scenePath2.extend( IECore.InternedStringVectorData( scenePlug2PathPrefix[1:].split( "/" ) ) )

		walkScene( scenePath1, scenePath2 )

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
				if ( not pathsToIgnore ) or ( self.__pathToString( scenePath ) not in pathsToIgnore ) :
					for childPlugName in childPlugNames :
						self.assertEqual( scenePlug1[childPlugName].hash(), scenePlug2[childPlugName].hash() )
				childNames = scenePlug1["childNames"].getValue()
				for childName in childNames :

					childPath = IECore.InternedStringVectorData( scenePath )
					childPath.append( childName )

					walkScene( childPath )

		walkScene( IECore.InternedStringVectorData() )

	def assertSceneHashesNotEqual( self, scenePlug1, scenePlug2, childPlugNames = None, childPlugNamesToIgnore = (), pathsToIgnore = () ) :

		childPlugNames = self.__childPlugNames( childPlugNames, childPlugNamesToIgnore )

		def walkScene( scenePath ) :

			c = Gaffer.Context()
			c["scene:path"] = scenePath
			with c :
				if ( not pathsToIgnore ) or ( self.__pathToString( scenePath ) not in pathsToIgnore ) :
					for childPlugName in childPlugNames :
						if len( scenePath ) == 0 and childPlugName in [ "attributes", "object", "transform" ]:
							# hashes will automatically be equal for these plugs at the root
							continue
						self.assertNotEqual( scenePlug1[childPlugName].hash(), scenePlug2[childPlugName].hash() )
				childNames = scenePlug1["childNames"].getValue() or []
				for childName in childNames :

					childPath = IECore.InternedStringVectorData( scenePath )
					childPath.append( childName )

					walkScene( childPath )

		walkScene( IECore.InternedStringVectorData() )

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

	__uniqueInts = {}
	@classmethod
	def uniqueInt( cls, key ) :

		value = cls.__uniqueInts.get( key, 0 )
		value += 1
		cls.__uniqueInts[key] = value

		return value

	def __pathToString( self, path ) :

		return "/" + "/".join( [ p.value() for p in path ] )
