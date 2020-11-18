##########################################################################
#
#  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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

import inspect
import unittest
import os
import subprocess

import IECore

import Gaffer
import GafferScene
import GafferSceneTest

class EncapsulateTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		# - groupA
		#    - groupB
		#       - sphere
		#       - cube
		#    - sphere

		sphere = GafferScene.Sphere()
		sphere["sets"].setValue( "sphereSet" )

		cube = GafferScene.Cube()
		cube["sets"].setValue( "cubeSet" )

		groupB = GafferScene.Group()
		groupB["in"][0].setInput( sphere["out"] )
		groupB["in"][1].setInput( cube["out"] )
		groupB["name"].setValue( "groupB" )

		groupA = GafferScene.Group()
		groupA["in"][0].setInput( groupB["out"] )
		groupA["in"][1].setInput( sphere["out"] )
		groupA["name"].setValue( "groupA" )

		# When there is no filter attached, the node
		# should be an exact pass-through.

		encapsulate = GafferScene.Encapsulate()
		encapsulate["in"].setInput( groupA["out"] )

		self.assertSceneHashesEqual( encapsulate["out"], groupA["out"], checks = self.allSceneChecks - { "sets" } )
		self.assertScenesEqual( encapsulate["out"], groupA["out"] )

		# The same goes if there is a filter but it
		# doesn't match anything.

		pathFilter = GafferScene.PathFilter()
		encapsulate["filter"].setInput( pathFilter["out"] )

		self.assertSceneHashesEqual( encapsulate["out"], groupA["out"], checks = self.allSceneChecks - { "sets" } )
		self.assertScenesEqual( encapsulate["out"], groupA["out"] )

		# Even when the filter does match something, the
		# unmatched paths should be unaffected, and the
		# globals and set names should be unchanged.

		pathFilter["paths"].setValue( IECore.StringVectorData( [ "/groupA/groupB" ] ) )

		for path in [ "/", "/groupA", "/groupA/sphere" ] :
			self.assertPathHashesEqual( groupA["out"], path, encapsulate["out"], path )
			self.assertPathsEqual( groupA["out"], path, encapsulate["out"], path )

		for plugName in [ "globals", "setNames" ] :
			self.assertEqual( groupA["out"][plugName].hash(), encapsulate["out"][plugName].hash() )
			self.assertEqual( groupA["out"][plugName].getValue(), encapsulate["out"][plugName].getValue() )

		# And even for matched paths, the attributes, transform
		# and bound should be passed through unchanged.

		self.assertEqual( groupA["out"].attributesHash( "/groupA/groupB" ), encapsulate["out"].attributesHash( "/groupA/groupB" ) )
		self.assertEqual( groupA["out"].attributes( "/groupA/groupB" ), encapsulate["out"].attributes( "/groupA/groupB" ) )

		self.assertEqual( groupA["out"].transformHash( "/groupA/groupB" ), encapsulate["out"].transformHash( "/groupA/groupB" ) )
		self.assertEqual( groupA["out"].transform( "/groupA/groupB" ), encapsulate["out"].transform( "/groupA/groupB" ) )

		self.assertEqual( groupA["out"].boundHash( "/groupA/groupB" ), encapsulate["out"].boundHash( "/groupA/groupB" ) )
		self.assertEqual( groupA["out"].bound( "/groupA/groupB" ), encapsulate["out"].bound( "/groupA/groupB" ) )

		# But the children should all have been pruned away
		# and replaced by an appropriate Capsule.

		self.assertEqual( encapsulate["out"].childNames( "/groupA/groupB" ), IECore.InternedStringVectorData() )
		capsule = encapsulate["out"].object( "/groupA/groupB" )
		self.assertIsInstance( capsule, GafferScene.Capsule )
		self.assertEqual( capsule.scene(), groupA["out"] )
		self.assertEqual( capsule.root(), "/groupA/groupB" )
		self.assertEqual( capsule.bound(), groupA["out"].bound( "/groupA/groupB" ) )

		# And the sets should also have been pruned so they
		# don't include the objects beneath the capsule.

		self.assertEqual( encapsulate["out"].set( "sphereSet" ).value.paths(), [ "/groupA/sphere" ] )
		self.assertEqual( encapsulate["out"].set( "cubeSet" ).value.paths(), [] )

		# As a double check, test that this setup works properly with Unencapsulate
		unencapsulateFilter = GafferScene.PathFilter()

		unencapsulate = GafferScene.Unencapsulate()
		unencapsulate["in"].setInput( encapsulate["out"] )
		unencapsulate["filter"].setInput( unencapsulateFilter["out"] )

		# We can reverse the encapsulate by unencapsulating everything
		unencapsulateFilter["paths"].setValue( IECore.StringVectorData( [ "..." ] ) )
		self.assertScenesEqual( encapsulate["in"], unencapsulate["out"] )

		# Or by targetting just the path that was encapsulated
		unencapsulateFilter["paths"].setValue( IECore.StringVectorData( [ "/groupA/groupB" ] ) )
		self.assertScenesEqual( encapsulate["in"], unencapsulate["out"] )

		# But if we don't target that path, the scene stays encapsulated
		unencapsulateFilter["paths"].setValue( IECore.StringVectorData( [ "/groupA/" ] ) )
		self.assertScenesEqual( encapsulate["out"], unencapsulate["out"] )

	def testCapsuleHash( self ) :

		sphere = GafferScene.Sphere()
		group1 = GafferScene.Group()
		group1["in"][0].setInput( sphere["out"] )
		group2 = GafferScene.Group()
		group2["in"][0].setInput( group1["out"] )

		pathFilter = GafferScene.PathFilter()
		pathFilter["paths"].setValue( IECore.StringVectorData( [ "/group/group" ] ) )

		encapsulate = GafferScene.Encapsulate()
		encapsulate["in"].setInput( group2["out"] )
		encapsulate["filter"].setInput( pathFilter["out"] )

		objectHashes = set()
		capsuleHashes = set()

		def assertHashesUnique( path ) :

			objectHash = encapsulate["out"].objectHash( path )
			capsule = encapsulate["out"].object( path )
			self.assertIsInstance( capsule, GafferScene.Capsule )
			capsuleHash = capsule.hash()

			self.assertNotIn( objectHash, objectHashes )
			self.assertNotIn( capsuleHash, capsuleHashes )

			objectHashes.add( objectHash )
			capsuleHashes.add( capsuleHash )

		assertHashesUnique( "/group/group" )

		sphere["radius"].setValue( 2 )
		assertHashesUnique( "/group/group" )

		sphere["name"].setValue( "bigSphere" )
		assertHashesUnique( "/group/group" )

		sphere["transform"]["translate"]["x"].setValue( 1 )
		assertHashesUnique( "/group/group" )

		pathFilter["paths"].setValue( IECore.StringVectorData( [ "/group" ] ) )
		assertHashesUnique( "/group" )

		encapsulate["in"].setInput( group1["out"] )
		assertHashesUnique( "/group" )

	def testSetMemberAtRoot( self ) :

		sphere = GafferScene.Sphere()
		sphere["sets"].setValue( "A" )

		group = GafferScene.Group()
		group["in"][0].setInput( sphere["out"] )

		self.assertEqual( group["out"].set( "A" ).value.paths(), [ "/group/sphere" ] )

		pathFilter = GafferScene.PathFilter()
		pathFilter["paths"].setValue( IECore.StringVectorData( [ "/group/sphere" ] ) )

		encapsulate = GafferScene.Encapsulate()
		encapsulate["in"].setInput( group["out"] )
		encapsulate["filter"].setInput( pathFilter["out"] )

		self.assertEqual( encapsulate["out"].set( "A" ).value.paths(), [ "/group/sphere" ] )

	def testSignalThreadSafety( self ) :

		script = Gaffer.ScriptNode()

		script["random"] = Gaffer.Random()
		script["random"]["contextEntry"].setValue( "collect:rootName" )

		script["sphere"] = GafferScene.Sphere()
		script["sphere"]["radius"].setInput( script["random"]["outFloat"] )

		script["filter"] = GafferScene.PathFilter()
		script["filter"]["paths"].setValue( IECore.StringVectorData( [ "/sphere" ] ) )

		script["encapsulate"] = GafferScene.Encapsulate()
		script["encapsulate"]["in"].setInput( script["sphere"]["out"] )
		script["encapsulate"]["filter"].setInput( script["filter"]["out"] )

		script["collect"] = GafferScene.CollectScenes()
		script["collect"]["in"].setInput( script["encapsulate"]["out"] )
		script["collect"]["rootNames"].setValue( IECore.StringVectorData( [ str( x ) for x in range( 0, 100 ) ] ) )

		script["fileName"].setValue( os.path.join( self.temporaryDirectory(), "test.gfr" ) )
		script.save()

		# This exposed a crash caused by non-threadsafe access to signals from Capsules. It
		# will throw if the subprocess crashes.
		subprocess.check_output( [ "gaffer", "stats", script["fileName"].getValue(), "-scene", "collect" ] )

if __name__ == "__main__":
	unittest.main()
