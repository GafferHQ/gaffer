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
import inspect

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
		c["sets"].setValue( "A" )

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

	def testParentContextVariable( self ) :

		# Parent a sphere at `/a` and a grid at `/b`.

		sphere = GafferScene.Sphere()
		sphere["transform"]["translate"]["x"].setValue( 1 )
		sphere["sets"].setValue( "set1" )

		grid = GafferScene.Grid()
		grid["transform"]["translate"]["x"].setValue( 2 )

		switch = Gaffer.NameSwitch()
		switch.setup( sphere["out"] )
		switch["selector"].setValue( "${parent}" )
		switch["in"].resize( 3 )
		switch["in"][1]["name"].setValue( "/a" )
		switch["in"][1]["value"].setInput( sphere["out"] )
		switch["in"][2]["name"].setValue( "/b" )
		switch["in"][2]["value"].setInput( grid["out"] )

		collect = GafferScene.CollectScenes()
		collect["rootNames"].setValue( IECore.StringVectorData( [ "a", "b" ] ) )

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/a", "/b" ] ) )

		parent = GafferScene.Parent()
		parent["in"].setInput( collect["out"] )
		parent["children"][0].setInput( switch["out"]["value"] )
		parent["filter"].setInput( filter["out"] )
		parent["parentVariable"].setValue( "parent" )

		# Check the scene is as we expect

		self.assertSceneValid( parent["out"] )

		self.assertEqual( parent["out"].childNames( "/a" ), IECore.InternedStringVectorData( [ "sphere" ] ) )
		self.assertEqual( parent["out"].childNames( "/a/sphere" ), IECore.InternedStringVectorData() )
		self.assertEqual( parent["out"].childNames( "/b" ), IECore.InternedStringVectorData( [ "grid" ] ) )
		self.assertEqual( parent["out"].childNames( "/b/grid" ), IECore.InternedStringVectorData( [ "gridLines", "centerLines", "borderLines" ] ) )

		self.assertScenesEqual(
			sphere["out"],
			parent["out"],
			scenePlug2PathPrefix = "/a"
		)

		self.assertPathHashesEqual(
			sphere["out"], "/sphere",
			parent["out"], "/a/sphere",
		)

		self.assertScenesEqual(
			grid["out"],
			parent["out"],
			scenePlug2PathPrefix = "/b",
			# Don't want to check sets, because the grid has no sets.
			checks = self.allSceneChecks - { "sets" }
		)

		for path in [ "/grid", "/grid/centerLines", "/grid/gridLines", "/grid/borderLines" ] :
			self.assertPathHashesEqual(
				grid["out"], path,
				parent["out"], "/b" + path,
			)

		# Rename the parent variable. This should dirty all the output plugs and make the NameSwitch
		# output an empty scene.

		cs = GafferTest.CapturingSlot( parent.plugDirtiedSignal() )
		parent["parentVariable"].setValue( "x" )

		self.assertLessEqual( # Equivalent to `assertTrue( a.issubset( b ) )`, but with more informative errors
			{ parent["out"][n] for n in [ "bound", "transform", "attributes", "object", "childNames", "set" ] },
			{ x[0] for x in cs }
		)

		self.assertSceneValid( parent["out"] )
		self.assertEqual( parent["out"].childNames( "/a" ), IECore.InternedStringVectorData() )
		self.assertEqual( parent["out"].childNames( "/b" ), IECore.InternedStringVectorData() )

	def testDifferentSetsPerParent( self ) :

		sphere = GafferScene.Sphere()
		sphere["sets"].setValue( "roundThings" )

		cube = GafferScene.Cube()
		cube["sets"].setValue( "squareThings" )

		switch = Gaffer.NameSwitch()
		switch.setup( sphere["out"] )
		switch["selector"].setValue( "${parent}" )
		switch["in"].resize( 3 )
		switch["in"][1]["name"].setValue( "/a" )
		switch["in"][1]["value"].setInput( sphere["out"] )
		switch["in"][2]["name"].setValue( "/b" )
		switch["in"][2]["value"].setInput( cube["out"] )

		collect = GafferScene.CollectScenes()
		collect["rootNames"].setValue( IECore.StringVectorData( [ "a", "b" ] ) )

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/a", "/b" ] ) )

		parent = GafferScene.Parent()
		parent["in"].setInput( collect["out"] )
		parent["children"][0].setInput( switch["out"]["value"] )
		parent["filter"].setInput( filter["out"] )
		parent["parentVariable"].setValue( "parent" )

		self.assertEqual( set( str( x ) for x in parent["out"].setNames() ), { "roundThings", "squareThings" } )
		self.assertEqual( parent["out"].set( "roundThings" ).value, IECore.PathMatcher( [ "/a/sphere" ] ) )
		self.assertEqual( parent["out"].set( "squareThings" ).value, IECore.PathMatcher( [ "/b/cube" ] ) )

		cube["name"].setValue( "box" )
		self.assertEqual( set( str( x ) for x in parent["out"].setNames() ), { "roundThings", "squareThings" } )
		self.assertEqual( parent["out"].set( "roundThings" ).value, IECore.PathMatcher( [ "/a/sphere" ] ) )
		self.assertEqual( parent["out"].set( "squareThings" ).value, IECore.PathMatcher( [ "/b/box" ] ) )

		sphere["sets"].setValue( "balls" )
		self.assertEqual( set( str( x ) for x in parent["out"].setNames() ), { "balls", "squareThings" } )
		self.assertEqual( parent["out"].set( "balls" ).value, IECore.PathMatcher( [ "/a/sphere" ] ) )
		self.assertEqual( parent["out"].set( "squareThings" ).value, IECore.PathMatcher( [ "/b/box" ] ) )

	def testDestination( self ) :

		# /group
		#    /sphere1
		#	 /sphere2

		script = Gaffer.ScriptNode()

		script["sphere1"] = GafferScene.Sphere()
		script["sphere1"]["name"].setValue( "sphere1" )
		script["sphere1"]["transform"]["translate"]["x"].setValue( 1 )

		script["sphere2"] = GafferScene.Sphere()
		script["sphere2"]["name"].setValue( "sphere2" )
		script["sphere2"]["transform"]["translate"]["x"].setValue( 2 )

		script["group"] = GafferScene.Group()
		script["group"]["in"][0].setInput( script["sphere1"]["out"] )
		script["group"]["in"][1].setInput( script["sphere2"]["out"] )

		# "Parenting" a cube to each sphere, but putting the results at
		# the root of the scene. Using an expression to vary the dimensions
		# and sets of each cube.

		script["spheresFilter"] = GafferScene.PathFilter()
		script["spheresFilter"]["paths"].setValue( IECore.StringVectorData( [ "/group/sphere*" ] ) )

		script["cube"] = GafferScene.Cube()

		script["expression"] = Gaffer.Expression()
		script["expression"].setExpression( inspect.cleandoc(
			"""
			first = context.get( "parent", "" ) == "/group/sphere1"
			parent["cube"]["sets"] = "set1" if first else "set2"
			parent["cube"]["dimensions"]["x"] = 1 if first else 2
			"""
		) )

		script["parent"] = GafferScene.Parent()
		script["parent"]["in"].setInput( script["group"]["out"] )
		script["parent"]["children"][0].setInput( script["cube"]["out"] )
		script["parent"]["filter"].setInput( script["spheresFilter"]["out"] )
		script["parent"]["parentVariable"].setValue( "parent" )
		script["parent"]["destination"].setValue( "${scene:path}/../.." )

		self.assertSceneValid( script["parent"]["out"] )

		# Because two cubes are being added below one location, the second will
		# have a numeric suffix to keep it unique from the other. It's ambiguous
		# as to which one should be the second, so we define it by sorting them
		# based on their original parent.

		self.assertEqual( script["parent"]["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "group", "cube", "cube1" ] ) )
		self.assertEqual( script["parent"]["out"].object( "/cube" ).bound().size().x, 1 )
		self.assertEqual( script["parent"]["out"].object( "/cube1" ).bound().size().x, 2 )
		self.assertEqual( script["parent"]["out"].childNames( "/group" ), IECore.InternedStringVectorData( [ "sphere1", "sphere2" ] ) )
		self.assertEqual( script["parent"]["out"].childNames( "/cube" ), IECore.InternedStringVectorData() )
		self.assertEqual( script["parent"]["out"].childNames( "/cube1" ), IECore.InternedStringVectorData() )

		# The contents of the sets should reflect the same sorting and uniquefying.

		self.assertEqual( script["parent"]["out"].setNames(), IECore.InternedStringVectorData( [ "set1", "set2" ] ) )

		self.assertEqual(
			script["parent"]["out"].set( "set1" ).value,
			IECore.PathMatcher( [ "/cube" ] )
		)
		self.assertEqual(
			script["parent"]["out"].set( "set2" ).value,
			IECore.PathMatcher( [ "/cube1" ] )
		)

		# We want the cubes to be positioned as if they were parented below the spheres.

		self.assertEqual( script["parent"]["out"].fullTransform( "/cube" ), script["parent"]["in"].fullTransform( "/group/sphere1" ) )
		self.assertEqual( script["parent"]["out"].fullTransform( "/cube1" ), script["parent"]["in"].fullTransform( "/group/sphere2" ) )

		# And if we move the cubes to a different location, we want all that to apply still.

		script["parent"]["destination"].setValue( "/group" )

		self.assertSceneValid( script["parent"]["out"] )

		self.assertEqual( script["parent"]["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "group" ] ) )
		self.assertEqual( script["parent"]["out"].childNames( "/group" ), IECore.InternedStringVectorData( [ "sphere1", "sphere2", "cube", "cube1" ] ) )
		self.assertEqual( script["parent"]["out"].object( "/group/cube" ).bound().size().x, 1 )
		self.assertEqual( script["parent"]["out"].object( "/group/cube1" ).bound().size().x, 2 )
		self.assertEqual( script["parent"]["out"].childNames( "/group/cube" ), IECore.InternedStringVectorData() )
		self.assertEqual( script["parent"]["out"].childNames( "/group/cube1" ), IECore.InternedStringVectorData() )

		self.assertEqual( script["parent"]["out"].setNames(), IECore.InternedStringVectorData( [ "set1", "set2" ] ) )
		self.assertEqual(
			script["parent"]["out"].set( "set1" ).value,
			IECore.PathMatcher( [ "/group/cube" ] )
		)
		self.assertEqual(
			script["parent"]["out"].set( "set2" ).value,
			IECore.PathMatcher( [ "/group/cube1" ] )
		)

		self.assertEqual( script["parent"]["out"].fullTransform( "/group/cube" ), script["parent"]["in"].fullTransform( "/group/sphere1" ) )
		self.assertEqual( script["parent"]["out"].fullTransform( "/group/cube1" ), script["parent"]["in"].fullTransform( "/group/sphere2" ) )

	def testCreateNewDestination( self ) :

		sphere = GafferScene.Sphere()
		sphere["sets"].setValue( "A" )
		sphere["transform"]["translate"]["x"].setValue( 1 )

		group = GafferScene.Group()
		group["in"][0].setInput( sphere["out" ])
		group["transform"]["translate"]["y"].setValue( 2 )

		cube = GafferScene.Cube()
		cube["sets"].setValue( "A" )

		parent = GafferScene.Parent()
		parent["in"].setInput( group["out"] )
		parent["children"][0].setInput( cube["out"] )
		parent["parent"].setValue( "/group/sphere" )
		parent["destination"].setValue( "/group/parented/things" )

		self.assertSceneValid( parent["out"] )

		self.assertEqual( parent["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "group" ] ) )
		self.assertEqual( parent["out"].childNames( "/group" ), IECore.InternedStringVectorData( [ "sphere", "parented" ] ) )
		self.assertEqual( parent["out"].childNames( "/group/sphere" ), IECore.InternedStringVectorData() )
		self.assertEqual( parent["out"].childNames( "/group/parented" ), IECore.InternedStringVectorData( [ "things" ] ) )
		self.assertEqual( parent["out"].childNames( "/group/parented/things" ), IECore.InternedStringVectorData( [ "cube" ] ) )
		self.assertEqual( parent["out"].childNames( "/group/parented/things/cube" ), IECore.InternedStringVectorData() )

		self.assertPathHashesEqual( parent["out"], "/group", parent["in"], "/group", checks = self.allPathChecks - { "bound", "childNames" } )

		self.assertPathsEqual(
			parent["out"], "/group/parented/things/cube", cube["out"], "/cube",
			checks = self.allPathChecks - { "transform" }
		)
		self.assertEqual(
			parent["out"].fullTransform( "/group/parented/things/cube" ),
			parent["out"].fullTransform( "/group/sphere" )
		)

		self.assertEqual( parent["out"].set( "A" ).value, IECore.PathMatcher( [ "/group/sphere", "/group/parented/things/cube" ] ) )

	def testNonPreExistingNestedDestination( self ) :

		sphere = GafferScene.Sphere()
		cube = GafferScene.Cube()
		group = GafferScene.Group()
		group["in"][0].setInput( sphere["out"] )
		group["in"][1].setInput( cube["out"] )

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/group/*" ] ) )

		plane = GafferScene.Plane()

		parent = GafferScene.Parent()
		parent["in"].setInput( group["out"] )
		parent["children"][0].setInput( plane["out"] )
		parent["filter"].setInput( filter["out"] )

		spreadsheet = Gaffer.Spreadsheet()
		spreadsheet["selector"].setValue( "${scene:path}" )
		spreadsheet["rows"].addColumn( parent["destination"] )
		parent["destination"].setInput( spreadsheet["out"]["destination" ] )
		spreadsheet["rows"].addRows( 2 )
		spreadsheet["rows"][1]["name"].setValue( "/group/sphere" )
		spreadsheet["rows"][1]["cells"]["destination"]["value"].setValue( "/newOuterGroup" )
		spreadsheet["rows"][2]["name"].setValue( "/group/cube" )
		spreadsheet["rows"][2]["cells"]["destination"]["value"].setValue( "/newOuterGroup/newInnerGroup" )

		with self.assertRaisesRegex( Gaffer.ProcessException, 'Destination "/newOuterGroup" contains a nested destination' ) :
			parent["out"].childNames( "/newOuterGroup" )

		# Swap order, so they are likely visited the other way round when building the branches tree.
		spreadsheet["rows"][1]["cells"]["destination"]["value"].setValue( "/newOuterGroup/newInnerGroup" )
		spreadsheet["rows"][2]["cells"]["destination"]["value"].setValue( "/newOuterGroup" )

		with self.assertRaisesRegex( Gaffer.ProcessException, 'Destination "/newOuterGroup" contains a nested destination' ) :
			parent["out"].childNames( "/newOuterGroup" )

	def testMultipleNewDestinationsBelowOneParent( self ) :

		script = Gaffer.ScriptNode()

		script["cube"] = GafferScene.Cube()
		script["sphere"] = GafferScene.Sphere()
		script["group"] = GafferScene.Group()
		script["group"]["in"][0].setInput( script["sphere"]["out"] )
		script["group"]["in"][1].setInput( script["cube"]["out"] )

		script["filter"] = GafferScene.PathFilter()
		script["filter"]["paths"].setValue( IECore.StringVectorData( [ "/group/cube", "/group/sphere" ] ) )

		script["plane"] = GafferScene.Plane()

		script["parent"] = GafferScene.Parent()
		script["parent"]["in"].setInput( script["group"]["out"] )
		script["parent"]["filter"].setInput( script["filter"]["out"] )
		script["parent"]["children"][0].setInput( script["plane"]["out"] )

		script["expression"] = Gaffer.Expression()
		script["expression"].setExpression( inspect.cleandoc(
			"""
			path = context["scene:path"]
			if path[-1] == "sphere" :
				parent["parent"]["destination"] = "/group/childrenOfRoundThings"
			else :
				parent["parent"]["destination"] = "/group/childrenOfSquareThings"
			"""
		) )

		self.assertSceneValid( script["parent"]["out"] )

		# We expect alphabetical ordering for the new names.
		self.assertEqual(
			script["parent"]["out"].childNames( "/group" ),
			IECore.InternedStringVectorData( [ "sphere", "cube", "childrenOfRoundThings", "childrenOfSquareThings" ] )
		)

	def testNoUnwantedBoundEvaluations( self ) :

		reader = GafferScene.SceneReader()
		reader["fileName"].setValue( "${GAFFER_ROOT}/resources/gafferBot/caches/gafferBot.scc" )

		group = GafferScene.Group()

		parent = GafferScene.Parent()
		parent["in"].setInput( reader["out"] )
		parent["children"][0].setInput( group["out"] )
		parent["parent"].setValue( "/" )
		parent["destination"].setValue( "/children" )

		# Computing the root bound should not require more than the bounds
		# of `/` and `/GAFFERBOT` to be queried from the input scene.

		with Gaffer.ContextMonitor( reader["out"]["bound"] ) as contextMonitor :
			parent["out"].bound( "/" )

		self.assertEqual( contextMonitor.combinedStatistics().numUniqueContexts(), 2 )

		# If we parent to `/GAFFERBOT/children` then computing the bound of `/GAFFERBOT`
		# should only query `/GAFFERBOT` and `/GAFFERBOT/C_torso_GRP` from the input.

		Gaffer.ValuePlug.clearCache()
		Gaffer.ValuePlug.clearHashCache()

		parent["destination"].setValue( "/GAFFERBOT/children" )
		with Gaffer.ContextMonitor( reader["out"]["bound"] ) as contextMonitor :
			parent["out"].bound( "/GAFFERBOT" )

		self.assertEqual( contextMonitor.combinedStatistics().numUniqueContexts(), 2 )

		# The bounds for children of `/GAFFERBOT` should be perfect pass throughs.

		self.assertEqual(
			parent["out"].boundHash( "/GAFFERBOT/C_torso_GRP" ),
			parent["in"].boundHash( "/GAFFERBOT/C_torso_GRP" )
		)

	def testChainedNodesWithIdenticalBranches( self ) :

		# Trick to make a large scene without needing a cache file
		# and without using a BranchCreator. This scene is infinite
		# but very cheap to compute.

		infiniteScene = GafferScene.ScenePlug()
		infiniteScene["childNames"].setValue( IECore.InternedStringVectorData( [ "one", "two" ] ) )

		# Filter that will search the scene to a fixed depth, but
		# never find anything.

		pathFilter = GafferScene.PathFilter()
		pathFilter["paths"].setValue( IECore.StringVectorData( [ "/*/*/*/*/*/*/*/*/*/*/*/thisDoesntExist" ] ) )

		# Two Parent nodes one after another, using the same filter.
		# These will generate the same (empty) set of branches.

		parent1 = GafferScene.Parent()
		parent1["in"].setInput( infiniteScene )
		parent1["filter"].setInput( pathFilter["out"] )

		parent2 = GafferScene.Parent()
		parent2["in"].setInput( parent1["out"] )
		parent2["filter"].setInput( pathFilter["out"] )

		# Simulate the effects of a previous computation being evicted
		# from the cache.

		parent2["__branches"].getValue()
		Gaffer.ValuePlug.clearCache()

		# We are now a situation where the hash for `parent2.__branches` is
		# cached, but the value isn't. This is significant, because it means
		# that in the next step, the downstream compute for `parent2.__branches`
		# starts _before_ the upstream one for `parent1.__branches`. If the hash
		# wasn't cached, then the hash for `parent2` would trigger
		# an upstream compute for `parent1.__branches` first.

		# Trigger scene generation. We can't use `traverseScene()` because the
		# scene is infinite, so we use `matchingPaths()` to generate up to a fixed
		# depth. The key effect here is that lots of threads are indirectly pulling on
		# `parent2.__branches`, triggering task collaboration.

		with Gaffer.PerformanceMonitor() as monitor :
			paths = IECore.PathMatcher()
			GafferScene.SceneAlgo.matchingPaths( IECore.PathMatcher( [ "/*/*/*/*/*/*/*/*/*/*/*/*" ] ), parent2["out"], paths )

		# We only expect to see a single hash/compute for `__branches` on each
		# node. A previous bug meant that this was not the case, and thousands
		# of unnecessary evaluations of `parent1.__branches` could occur.

		self.assertEqual( monitor.plugStatistics( parent1["__branches"] ).computeCount, 1 )
		self.assertEqual( monitor.plugStatistics( parent2["__branches"] ).computeCount, 1 )

if __name__ == "__main__":
	unittest.main()
