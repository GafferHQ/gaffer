##########################################################################
#
#  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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

import os.path

import imath

import IECore

import Gaffer
import GafferTest
import GafferScene
import GafferSceneTest

class ParentTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		s = GafferScene.Sphere()
		c = GafferScene.Cube()

		g = GafferScene.Group()
		g["in"][0].setInput( s["out"] )
		g["in"][1].setInput( c["out"] )

		p = GafferScene.Parent()
		p["in"].setInput( g["out"] )
		p["parent"].setValue( "/group" )
		p["children"][0].setInput( c["out"] )

		self.assertEqual( p["out"].childNames( "/group" ), IECore.InternedStringVectorData( [ "sphere", "cube", "cube1" ] ) )
		self.assertPathsEqual( p["out"], "/group/cube", p["out"], "/group/cube1" )

		self.assertSceneValid( p["out"] )

	def testParentAtRoot( self ) :

		s = GafferScene.Sphere()
		c = GafferScene.Cube()

		g = GafferScene.Group()
		g["in"][0].setInput( s["out"] )
		g["in"][1].setInput( c["out"] )

		p = GafferScene.Parent()
		p["in"].setInput( g["out"] )
		p["parent"].setValue( "/" )
		p["children"][0].setInput( c["out"] )

		self.assertEqual( p["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "group", "cube" ] ) )
		self.assertPathsEqual( p["out"], "/group/cube", p["out"], "/cube" )

		self.assertSceneValid( p["out"] )

	def testUnconnected( self ) :

		p = GafferScene.Parent()

		self.assertEqual( p["out"].childNames( "/" ), IECore.InternedStringVectorData( [] ) )
		self.assertSceneValid( p["out"] )

	def testPassThroughWhenNoChild( self ) :

		c = GafferScene.Cube()

		p = GafferScene.Parent()
		p["parent"].setValue( "/" )
		p["in"].setInput( c["out"] )

		self.assertScenesEqual( p["out"], c["out"] )

	def testNameUniqueification( self ) :

		c = GafferScene.Cube()

		g = GafferScene.Group()
		g["in"][0].setInput( c["out"] )
		g["in"][1].setInput( c["out"] )

		p = GafferScene.Parent()
		p["in"].setInput( g["out"] )
		p["parent"].setValue( "/group" )
		p["children"][0].setInput( c["out"] )

		self.assertEqual( p["out"].childNames( "/group" ), IECore.InternedStringVectorData( [ "cube", "cube1", "cube2" ] ) )
		self.assertSceneValid( p["out"] )

	def testChildSmallerThanExistingChildren( self ) :

		c = GafferScene.Cube()

		cSmall = GafferScene.Cube()
		cSmall["dimensions"].setValue( imath.V3f( 0.1 ) )

		g = GafferScene.Group()
		g["in"][0].setInput( c["out"] )

		p = GafferScene.Parent()
		p["in"].setInput( g["out"] )
		p["parent"].setValue( "/group" )
		p["children"][0].setInput( cSmall["out"] )

		self.assertSceneValid( p["out"] )

	def testChildLargerThanExistingChildren( self ) :

		c = GafferScene.Cube()

		cLarge = GafferScene.Cube()
		cLarge["dimensions"].setValue( imath.V3f( 10 ) )

		g = GafferScene.Group()
		g["in"][0].setInput( c["out"] )

		p = GafferScene.Parent()
		p["in"].setInput( g["out"] )
		p["parent"].setValue( "/group" )
		p["children"][0].setInput( cLarge["out"] )

		self.assertSceneValid( p["out"] )

	def testEmptyParent( self ) :

		c = GafferScene.Cube()

		g = GafferScene.Group()
		g["in"][0].setInput( c["out"] )

		p = GafferScene.Parent()
		p["in"].setInput( g["out"] )
		p["parent"].setValue( "" )
		p["children"][0].setInput( c["out"] )

		self.assertScenesEqual( p["out"], g["out"] )
		self.assertSceneHashesEqual( p["out"], g["out"] )

	def testParentInsideParent( self ) :

		c = GafferScene.Cube()

		p1 = GafferScene.Parent()
		p1["in"].setInput( c["out"] )
		p1["parent"].setValue( "/cube" )
		p1["children"][0].setInput( c["out"] )

		self.assertEqual( p1["out"].childNames( "/cube" ), IECore.InternedStringVectorData( [ "cube" ] ) )

		p2 = GafferScene.Parent()
		p2["in"].setInput( p1["out"] )
		p2["parent"].setValue( "/cube/cube" )
		p2["children"][0].setInput( c["out"] )

		self.assertEqual( p2["out"].childNames( "/cube" ), IECore.InternedStringVectorData( [ "cube" ] ) )
		self.assertEqual( p2["out"].childNames( "/cube/cube" ), IECore.InternedStringVectorData( [ "cube" ] ) )

	def testSets( self ) :

		l1 = GafferSceneTest.TestLight()
		l1["name"].setValue( "light1" )
		l2 = GafferSceneTest.TestLight()
		l2["name"].setValue( "light2" )

		p = GafferScene.Parent()
		p["in"].setInput( l1["out"] )
		p["children"][0].setInput( l2["out"] )
		p["parent"].setValue( "/" )

		self.assertSceneValid( p["out"] )
		self.assertEqual( p["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "light1", "light2" ] ) )

		self.assertEqual( p["out"]["setNames"].getValue(), IECore.InternedStringVectorData( [ "__lights", "defaultLights" ] ) )
		self.assertEqual( set( p["out"].set( "__lights" ).value.paths() ), set( [ "/light1", "/light2" ] ) )

	def testSetsUniqueToChild( self ) :

		c = GafferScene.Cube()
		l = GafferSceneTest.TestLight()

		p = GafferScene.Parent()
		p["in"].setInput( c["out"] )
		p["children"][0].setInput( l["out"] )
		p["parent"].setValue( "/" )

		self.assertSceneValid( p["out"] )
		self.assertEqual( p["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "cube", "light" ] ) )

		self.assertEqual( p["out"]["setNames"].getValue(), IECore.InternedStringVectorData( [ "__lights", "defaultLights" ] ) )
		self.assertEqual( p["out"].set( "__lights" ).value.paths(), [ "/light" ] )

	def testSetsUniqueToParent( self ) :

		l = GafferSceneTest.TestLight()
		c = GafferScene.Cube()

		p = GafferScene.Parent()
		p["in"].setInput( l["out"] )
		p["children"][0].setInput( c["out"] )
		p["parent"].setValue( "/" )

		self.assertSceneValid( p["out"] )
		self.assertEqual( p["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "light", "cube" ] ) )

		self.assertEqual( p["out"]["setNames"].getValue(), IECore.InternedStringVectorData( [ "__lights", "defaultLights" ] ) )
		self.assertEqual( p["out"].set( "__lights" ).value.paths(), [ "/light" ] )

	def testSetsWithNonRootParent( self ) :

		c = GafferScene.Cube()
		l = GafferSceneTest.TestLight()

		p = GafferScene.Parent()
		p["in"].setInput( c["out"] )
		p["children"][0].setInput( l["out"] )
		p["parent"].setValue( "/cube" )

		self.assertSceneValid( p["out"] )
		self.assertEqual( p["out"].childNames( "/cube" ), IECore.InternedStringVectorData( [ "light" ] ) )

		self.assertEqual( p["out"]["setNames"].getValue(), IECore.InternedStringVectorData( [ "__lights", "defaultLights" ] ) )
		self.assertEqual( p["out"].set( "__lights" ).value.paths(), [ "/cube/light" ] )

	def testSetsWithDeepNesting( self ) :

		c = GafferScene.Cube()

		l = GafferSceneTest.TestLight()
		g1 = GafferScene.Group()
		g1["in"][0].setInput( l["out"] )
		g2 = GafferScene.Group()
		g2["in"][0].setInput( g1["out"] )

		p = GafferScene.Parent()
		p["in"].setInput( c["out"] )
		p["children"][0].setInput( g2["out"] )
		p["parent"].setValue( "/cube" )

		self.assertSceneValid( p["out"] )

		self.assertEqual( p["out"]["setNames"].getValue(), IECore.InternedStringVectorData( [ "__lights", "defaultLights" ] ) )
		self.assertEqual( p["out"].set( "__lights" ).value.paths(), [ "/cube/group/group/light" ] )

	def testSetsWithWithRenaming( self ) :

		l1 = GafferSceneTest.TestLight()
		l2 = GafferSceneTest.TestLight()

		p = GafferScene.Parent()
		p["in"].setInput( l1["out"] )
		p["children"][0].setInput( l2["out"] )
		p["parent"].setValue( "/" )

		self.assertSceneValid( p["out"] )
		self.assertEqual( p["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "light", "light1" ] ) )

		self.assertEqual( p["out"]["setNames"].getValue(), IECore.InternedStringVectorData( [ "__lights", "defaultLights" ] ) )
		self.assertEqual( set(  p["out"].set( "__lights" ).value.paths() ), set( [ "/light", "/light1" ] ) )

	def testGlobalsPassThrough( self ) :

		g = GafferScene.Group()
		s = GafferScene.Sphere()

		p = GafferScene.Parent()
		p["in"].setInput( g["out"] )
		p["parent"].setValue( "/group" )
		p["children"][0].setInput( s["out"] )

		self.assertSceneValid( p["out"] )

		self.assertEqual( p["out"]["globals"].hash(), g["out"]["globals"].hash() )
		self.assertTrue( p["out"]["globals"].getValue( _copy = False ).isSame( g["out"]["globals"].getValue( _copy = False ) ) )

	def testChangingInputSet( self ) :

		c1 = GafferScene.Cube()
		c2 = GafferScene.Cube()

		p = GafferScene.Parent()
		p["in"].setInput( c1["out"] )
		p["parent"].setValue( "/" )
		p["children"][0].setInput( c2["out"] )

		h = p["out"].setHash( "test" )
		self.assertEqual( p["out"].set( "test" ).value, IECore.PathMatcher() )

		c1["sets"].setValue( "test" )

		self.assertNotEqual( p["out"].setHash( "test" ), h )
		self.assertEqual( p["out"].set( "test" ).value, IECore.PathMatcher( [ "/cube" ] ) )

	def testFilter( self ) :

		sphere = GafferScene.Sphere()

		group = GafferScene.Group()
		for i in range( 0, 6 ) :
			group["in"][i].setInput( sphere["out"] )

		cube = GafferScene.Cube()
		cube["sets"].setValue( "setA" )

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/group/sphere[1-4]" ] ) )

		parent = GafferScene.Parent()
		parent["in"].setInput( group["out"] )
		parent["children"][0].setInput( cube["out"] )
		parent["filter"].setInput( filter["out"] )

		self.assertSceneValid( parent["out"] )

		self.assertEqual( parent["out"].childNames( "/group/sphere" ), IECore.InternedStringVectorData() )
		for i in range( 1, 5 ) :
			self.assertEqual( parent["out"].childNames( "/group/sphere{0}".format( i ) ), IECore.InternedStringVectorData( [ "cube" ] ) )

		self.assertIn( "setA", parent["out"]["setNames"].getValue() )
		self.assertEqual(
			parent["out"].set( "setA" ).value,
			IECore.PathMatcher( [
				"/group/sphere1/cube",
				"/group/sphere2/cube",
				"/group/sphere3/cube",
				"/group/sphere4/cube",
			] )
		)

	def testMultipleAncestorMatches( self ) :

		innerGroup = GafferScene.Group()
		innerGroup["name"].setValue( "inner" )

		outerGroup = GafferScene.Group()
		outerGroup["in"][0].setInput( innerGroup["out"] )
		outerGroup["name"].setValue( "outer" )

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/outer", "/outer/inner" ] ) )

		cube = GafferScene.Cube()
		cube["sets"].setValue( "setA" )

		parent = GafferScene.Parent()
		parent["in"].setInput( outerGroup["out"] )
		parent["children"][0].setInput( cube["out"] )
		parent["filter"].setInput( filter["out"] )

		self.assertSceneValid( parent["out"] )

		self.assertEqual( parent["out"].childNames( "/outer" ), IECore.InternedStringVectorData( [ "inner", "cube" ] ) )
		self.assertEqual( parent["out"].childNames( "/outer/inner" ), IECore.InternedStringVectorData( [ "cube" ] ) )

	def testFilterConnectionDisablesParentPlug( self ) :

		cube = GafferScene.Cube()

		parent = GafferScene.Parent()
		parent["in"].setInput( cube["out"] )
		parent["children"][0].setInput( cube["out"] )
		parent["parent"].setValue( "/" )

		self.assertEqual( parent["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "cube", "cube1" ] ) )

		filter = GafferScene.PathFilter()
		parent["filter"].setInput( filter["out"] )

		self.assertEqual( parent["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "cube" ] ) )

	def testInvalidParent( self ) :

		cube = GafferScene.Cube()
		cube["sets"].setValue( "setA" )

		parent = GafferScene.Parent()
		parent["in"].setInput( cube["out"] )
		parent["children"][0].setInput( cube["out"] )
		parent["parent"].setValue( "/invalidLocation" )

		self.assertSceneValid( parent["out"] )
		self.assertScenesEqual( parent["out"], cube["out"] )

	def testChildNamesAffectMapping( self ) :

		cube = GafferScene.Cube()
		sphere = GafferScene.Sphere()

		parent = GafferScene.Parent()
		parent["in"].setInput( cube["out"] )
		parent["children"][0].setInput( sphere["out"] )

		cs = GafferTest.CapturingSlot( parent.plugDirtiedSignal() )
		sphere["name"].setValue( "ball" )
		self.assertIn( parent["__mapping"], { x[0] for x in cs } )

	def testChildArray( self ) :

		cube = GafferScene.Cube()
		cube["sets"].setValue( "A B" )

		sphere = GafferScene.Sphere()
		sphere["sets"].setValue( "B C" )

		parent = GafferScene.Parent()
		parent["children"][0].setInput( cube["out"] )
		parent["children"][1].setInput( sphere["out"] )
		parent["children"][2].setInput( sphere["out"] )
		parent["parent"].setValue( "/" )

		self.assertSceneValid( parent["out"] )

		self.assertEqual( parent["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "cube", "sphere", "sphere1" ] ) )
		self.assertEqual( parent["out"].setNames(), IECore.InternedStringVectorData( [ "A", "B", "C" ] ) )
		self.assertEqual( parent["out"].set( "A" ).value, IECore.PathMatcher( [ "/cube" ] ) )
		self.assertEqual( parent["out"].set( "B" ).value, IECore.PathMatcher( [ "/cube", "/sphere", "/sphere1" ] ) )
		self.assertEqual( parent["out"].set( "C" ).value, IECore.PathMatcher( [ "/sphere", "/sphere1" ] ) )

	def testLoadFrom0_54( self ) :

		script = Gaffer.ScriptNode()
		script["fileName"].setValue( os.path.join( os.path.dirname( __file__ ), "scripts", "parent-0.54.1.0.gfr" ) )
		script.load()

		self.assertEqual( script["Parent"]["in"].getInput(), script["Plane"]["out"] )
		self.assertEqual( script["Parent"]["children"][0].getInput(), script["Cube"]["out"] )

		self.assertEqual( script["Box"]["Parent"]["in"].source(), script["Plane"]["out"] )
		self.assertEqual( script["Box"]["Parent"]["children"][0].source(), script["Cube"]["out"] )

		self.assertScenesEqual( script["Parent"]["out"], script["Box"]["out"] )

	def testLoadPromotedChildrenPlug( self ) :

		s = Gaffer.ScriptNode()

		s["b1"] = Gaffer.Box()
		s["b1"]["p"] = GafferScene.Parent()
		Gaffer.PlugAlgo.promote( s["b1"]["p"]["children"] )

		s["b2"] = Gaffer.Box()
		s["b2"]["p"] = GafferScene.Parent()
		s["b2"]["pi"] = Gaffer.BoxIn()
		s["b2"]["pi"].setup( s["b2"]["p"]["children"] )
		s["b2"]["p"]["children"].setInput( s["b2"]["pi"]["out"] )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual(
			s["b1"]["p"]["children"].getInput().fullName(),
			s2["b1"]["p"]["children"].getInput().fullName()
		)

		self.assertEqual(
			s["b2"]["p"]["children"].getInput().fullName(),
			s2["b2"]["p"]["children"].getInput().fullName()
		)

	def testSetPassThroughWhenNoParent( self ) :

		sphere = GafferScene.Sphere()
		sphere["sets"].setValue( "set" )

		cube = GafferScene.Cube()

		parent = GafferScene.Parent()
		parent["in"].setInput( sphere["out"] )
		parent["children"][0].setInput( cube["out"] )

		self.assertEqual( parent["out"].set( "set" ), sphere["out"].set( "set" ) )
		self.assertEqual( parent["out"].setHash( "set" ), sphere["out"].setHash( "set" ) )

	def testContextVariableForParent( self ) :

		sphere = GafferScene.Sphere()
		sphere["sets"].setValue( "set" )

		collect = GafferScene.CollectScenes()
		collect["rootNames"].setValue( IECore.StringVectorData( [ "a", "b" ] ) )

		parent = GafferScene.Parent()
		parent["in"].setInput( collect["out"] )
		parent["children"][0].setInput( sphere["out"] )
		parent["parent"].setValue( "${parent}" )

		with Gaffer.Context() as context :

			context["parent"] = "/a"
			self.assertEqual(
				parent["out"].set( "set" ).value.paths(),
				[ "/a/sphere" ]
			)

			context["parent"] = "/b"
			self.assertEqual(
				parent["out"].set( "set" ).value.paths(),
				[ "/b/sphere" ]
			)

if __name__ == "__main__":
	unittest.main()
