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
import os
import unittest

import IECore

import Gaffer
import GafferScene
import GafferSceneTest

class CollectScenesTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		# Make a few input scenes

		script = Gaffer.ScriptNode()

		script["sphere"] = GafferScene.Sphere()
		script["sphere"]["sets"].setValue( "spheres" )

		script["cube"] = GafferScene.Cube()
		script["cube"]["sets"].setValue( "cubes" )

		script["group"] = GafferScene.Group()
		script["group"]["in"][0].setInput( script["sphere"]["out"] )
		script["group"]["in"][1].setInput( script["cube"]["out"] )

		script["switch"] = Gaffer.Switch()
		script["switch"].setup( GafferScene.ScenePlug() )

		script["switch"]["in"][0].setInput( script["sphere"]["out"] )
		script["switch"]["in"][1].setInput( script["cube"]["out"] )
		script["switch"]["in"][2].setInput( script["group"]["out"] )

		# Make an empty CollectScenes

		script["collect"] = GafferScene.CollectScenes()
		script["collect"]["in"].setInput( script["switch"]["out"] )

		self.assertSceneValid( script["collect"]["out"] )
		self.assertEqual( script["collect"]["out"].childNames( "/" ), IECore.InternedStringVectorData() )

		# Configure it to collect the input scenes

		script["collect"]["rootNames"].setValue( IECore.StringVectorData( [ "sphere", "cube", "group" ] ) )

		script["expression"] = Gaffer.Expression()
		script["expression"].setExpression( inspect.cleandoc(
			"""
			scenes = parent["collect"]["rootNames"]
			parent["switch"]["index"] = scenes.index( context.get( "collect:rootName", "sphere" ) )
			"""
		) )

		# Check we get what we expect

		self.assertEqual( script["collect"]["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "sphere", "cube", "group" ] ) )
		self.assertSceneValid( script["collect"]["out"] )

		script["subTree"] = GafferScene.SubTree()
		script["subTree"]["in"].setInput( script["collect"]["out"] )

		script["subTree"]["root"].setValue( "/sphere" )
		self.assertScenesEqual( script["subTree"]["out"], script["sphere"]["out"], checks = self.allSceneChecks - { "sets" } )

		script["subTree"]["root"].setValue( "/cube" )
		self.assertScenesEqual( script["subTree"]["out"], script["cube"]["out"], checks = self.allSceneChecks - { "sets" } )

		script["subTree"]["root"].setValue( "/group" )
		self.assertScenesEqual( script["subTree"]["out"], script["group"]["out"] )

		# Check the sets too

		self.assertEqual( script["collect"]["out"]["setNames"].getValue(), IECore.InternedStringVectorData( [ "spheres", "cubes" ] ) )

		self.assertEqual(
			script["collect"]["out"].set( "spheres" ).value,
			IECore.PathMatcher(
				[ "/sphere/sphere", "/group/group/sphere" ]
			)
		)

		self.assertEqual(
			script["collect"]["out"].set( "cubes" ).value,
			IECore.PathMatcher(
				[ "/cube/cube", "/group/group/cube" ]
			)
		)

	def testGlobals( self ) :

		options = GafferScene.CustomOptions()
		options["options"].addChild( Gaffer.NameValuePlug( "user:test", "${collect:rootName}" ) )
		self.assertTrue( "option:user:test" in options["out"]["globals"].getValue() )

		collect = GafferScene.CollectScenes()
		collect["in"].setInput( options["out"] )
		collect["rootNames"].setValue( IECore.StringVectorData( [ "a", "b" ] ) )

		self.assertEqual( collect["out"]["globals"].getValue()["option:user:test"], IECore.StringData( "a" ) )

	def testSubstitutions( self ) :

		sphere = GafferScene.Sphere()

		primitiveVariables = GafferScene.PrimitiveVariables()
		primitiveVariables["in"].setInput( sphere["out"] )
		primitiveVariables["primitiveVariables"].addChild( Gaffer.NameValuePlug( "color", "${collect:rootName}" ) )

		collect = GafferScene.CollectScenes()
		collect["in"].setInput( primitiveVariables["out"] )
		collect["rootNames"].setValue( IECore.StringVectorData( [ "red", "green", "blue" ] ) )

		for c in ( "red", "green", "blue" ) :
			self.assertEqual( collect["out"].object( "/{}/sphere".format( c ) )["color"].data.value, c )

	def testCacheReuse( self ) :

		sphere = GafferScene.Sphere()

		collect = GafferScene.CollectScenes()
		collect["in"].setInput( sphere["out"] )
		collect["rootNames"].setValue( IECore.StringVectorData( [ "test" ] ) )

		self.assertPathHashesEqual( sphere["out"], "/sphere", collect["out"], "/test/sphere" )
		self.assertTrue(
			sphere["out"].object( "/sphere", _copy = False ).isSame(
				collect["out"].object( "/test/sphere", _copy = False )
			)
		)

	def testCollectObject( self ) :

		sphere = GafferScene.Sphere()
		sphere["sets"].setValue( "sphereSet" )

		collect = GafferScene.CollectScenes()
		collect["in"].setInput( sphere["out"] )
		collect["rootNames"].setValue( IECore.StringVectorData( [ "test" ] ) )
		collect["sourceRoot"].setValue( "sphere" )

		self.assertPathHashesEqual( sphere["out"], "/sphere", collect["out"], "/test" )
		self.assertEqual( sphere["out"].object( "/sphere" ), collect["out"].object( "/test" ) )

		self.assertEqual( collect["out"].set( "sphereSet" ).value.paths(), [ "/test" ] )

	def testRoot( self ) :

		script = Gaffer.ScriptNode()

		script["sphere"] = GafferScene.Sphere()
		script["sphere"]["sets"].setValue( "sphereSet" )

		script["group"] = GafferScene.Group()
		script["group"]["in"][0].setInput( script["sphere"]["out"] )

		script["cube"] = GafferScene.Cube()
		script["cube"]["sets"].setValue( "cubeSet" )

		script["switch"] = Gaffer.Switch()
		script["switch"].setup( GafferScene.ScenePlug() )

		script["switch"]["in"][0].setInput( script["group"]["out"] )
		script["switch"]["in"][1].setInput( script["cube"]["out"] )

		script["collect"] = GafferScene.CollectScenes()
		script["collect"]["in"].setInput( script["switch"]["out"] )
		script["collect"]["rootNames"].setValue( IECore.StringVectorData( [ "0", "1", "2", "3" ] ) )

		script["expression"] = Gaffer.Expression()
		script["expression"].setExpression( inspect.cleandoc(
			"""
			root = context.get( "collect:rootName", "0" )
			parent["switch"]["index"] = int( root ) > 1
			parent["collect"]["sourceRoot"] = {
				"0" : "",
				"1" : "/group",
				"2" : "/",
				"3" : "/cube"
			}[root]
			"""
		) )

		self.assertEqual( script["collect"]["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "0", "1", "2", "3" ] ) )

		self.assertEqual( script["collect"]["out"].childNames( "/0" ), IECore.InternedStringVectorData( [ "group" ] ) )
		self.assertEqual( script["collect"]["out"].childNames( "/1" ), IECore.InternedStringVectorData( [ "sphere" ] ) )
		self.assertEqual( script["collect"]["out"].childNames( "/2" ), IECore.InternedStringVectorData( [ "cube" ] ) )
		self.assertEqual( script["collect"]["out"].childNames( "/3" ), IECore.InternedStringVectorData() )

		self.assertEqual( script["collect"]["out"].object( "/0" ), IECore.NullObject() )
		self.assertEqual( script["collect"]["out"].object( "/1" ), IECore.NullObject() )
		self.assertEqual( script["collect"]["out"].object( "/2" ), IECore.NullObject() )
		self.assertEqual( script["collect"]["out"].object( "/3" ), script["cube"]["out"].object( "/cube" ) )

		self.assertEqual( script["collect"]["out"].childNames( "/0/group" ), IECore.InternedStringVectorData( [ "sphere" ] ) )
		self.assertEqual( script["collect"]["out"].childNames( "/1/sphere" ), IECore.InternedStringVectorData() )
		self.assertEqual( script["collect"]["out"].childNames( "/2/cube" ), IECore.InternedStringVectorData() )

		self.assertEqual( script["collect"]["out"].object( "/0/group" ), IECore.NullObject() )
		self.assertEqual( script["collect"]["out"].object( "/1/sphere" ), script["sphere"]["out"].object( "/sphere" ) )
		self.assertEqual( script["collect"]["out"].object( "/2/cube" ), script["cube"]["out"].object( "/cube" ) )

		self.assertEqual( script["collect"]["out"].childNames( "/0/group/sphere" ), IECore.InternedStringVectorData() )
		self.assertEqual( script["collect"]["out"].object( "/0/group/sphere" ), script["sphere"]["out"].object( "/sphere" ) )

		self.assertEqual( script["collect"]["out"]["setNames"].getValue(), IECore.InternedStringVectorData( [ "sphereSet", "cubeSet" ] ) )

		self.assertEqual(
			set( script["collect"]["out"].set( "sphereSet" ).value.paths() ),
			{
				"/0/group/sphere",
				"/1/sphere",
			}
		)

		self.assertEqual(
			set( script["collect"]["out"].set( "cubeSet" ).value.paths() ),
			{
				"/2/cube",
				"/3",
			}
		)

	def testInPlug( self ) :

		c = GafferScene.CollectScenes()
		self.assertIsInstance( c["in"], GafferScene.ScenePlug )

	def testLoadFromVersion0_48( self ) :

		s = Gaffer.ScriptNode()
		s["fileName"].setValue( os.path.dirname( __file__ ) + "/scripts/collectScenes-0.48.0.0.gfr" )
		s.load()

		self.assertTrue( s["CollectScenes"]["in"].getInput(), s["Sphere"]["out"] )

	def testCollectInvalidLocation( self ) :

		sphere = GafferScene.Sphere()
		sphere["sets"].setValue( "set1" )

		group = GafferScene.Group()
		group["in"][0].setInput( sphere["out"] )

		collect = GafferScene.CollectScenes()
		collect["rootNames"].setValue( IECore.StringVectorData( [ "A" ] ) )
		collect["in"].setInput( group["out"] )

		self.assertSceneValid( collect["out"] )
		self.assertEqual( collect["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "A" ] ) )
		self.assertEqual( collect["out"].childNames( "/A" ), IECore.InternedStringVectorData( [ "group" ] ) )
		self.assertEqual( collect["out"].childNames( "/A/group" ), IECore.InternedStringVectorData( [ "sphere" ] ) )
		self.assertEqual( collect["out"].childNames( "/A/group/sphere" ), IECore.InternedStringVectorData() )

		collect["sourceRoot"].setValue( "iDontExist" )

		self.assertSceneValid( collect["out"] )
		self.assertEqual( collect["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "A" ] ) )
		self.assertEqual( collect["out"].childNames( "/A" ), IECore.InternedStringVectorData() )

if __name__ == "__main__":
	unittest.main()
