##########################################################################
#
#  Copyright (c) 2014, John Haddon. All rights reserved.
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

import imath

import IECore

import Gaffer
import GafferTest
import GafferScene
import GafferSceneTest

class DuplicateTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		s = GafferScene.Sphere()
		d = GafferScene.Duplicate()
		d["in"].setInput( s["out"] )
		d["target"].setValue( "/sphere" )
		d["transform"]["translate"].setValue( imath.V3f( 1, 0, 0 ) )

		self.assertSceneValid( d["out"] )

		self.assertEqual( d["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "sphere", "sphere1" ] ) )
		self.assertPathHashesEqual( s["out"], "/sphere", d["out"], "/sphere" )
		self.assertPathHashesEqual( d["out"], "/sphere", d["out"], "/sphere1", checks = self.allPathChecks - { "transform" } )
		self.assertEqual( d["out"].transform( "/sphere1" ), imath.M44f().translate( imath.V3f( 1, 0, 0 ) ) )

	def testMultipleCopies( self ) :

		s = GafferScene.Sphere()
		d = GafferScene.Duplicate()
		d["in"].setInput( s["out"] )
		d["target"].setValue( "/sphere" )
		d["transform"]["translate"].setValue( imath.V3f( 1, 0, 0 ) )
		d["copies"].setValue( 10 )

		self.assertSceneValid( d["out"] )

		self.assertEqual(
			d["out"].childNames( "/" ),
			IECore.InternedStringVectorData(
				[ "sphere" ] + [ "sphere%d" % x for x in range( 1, 11 ) ]
			)
		)

		for i in range( 1, 11 ) :
			path = "sphere%d" % i
			self.assertPathHashesEqual( d["out"], "/sphere", d["out"], path, checks = self.allPathChecks - { "transform" } )
			self.assertEqual( d["out"].transform( path ), imath.M44f().translate( imath.V3f( 1, 0, 0 ) * i ) )

	def testHierarchy( self ) :

		s = GafferScene.Sphere()
		g = GafferScene.Group()
		g["in"][0].setInput( s["out"] )

		d = GafferScene.Duplicate()
		d["in"].setInput( g["out"] )
		d["target"].setValue( "/group" )

		self.assertSceneValid( d["out"] )
		self.assertPathsEqual( d["out"], "/group", d["out"], "/group1" )
		self.assertPathHashesEqual( d["out"], "/group", d["out"], "/group1", checks = self.allPathChecks - { "transform" } )
		self.assertPathsEqual( d["out"], "/group/sphere", d["out"], "/group1/sphere" )
		self.assertPathHashesEqual( d["out"], "/group/sphere", d["out"], "/group1/sphere" )

	def testInvalidTarget( self ) :

		s = GafferScene.Sphere()
		d = GafferScene.Duplicate()
		d["in"].setInput( s["out"] )
		d["target"].setValue( "/cube" )

		self.assertSceneValid( d["out"] )
		self.assertScenesEqual( d["out"], d["in"] )

	def testInvalidTargetParent( self ) :

		r = GafferScene.SceneReader()
		r["fileName"].setValue( "${GAFFER_ROOT}/python/GafferSceneTest/alembicFiles/cube.abc" )

		d = GafferScene.Duplicate()
		d["in"].setInput( r["out"] )
		d["target"].setValue( "/notGroup1/pCube1" )

		self.assertScenesEqual( d["in"], d["out"] )

	def testNamePlug( self ) :

		s = GafferScene.Sphere()
		g = GafferScene.Group()
		g["in"][0].setInput( s["out"] )

		d = GafferScene.Duplicate()
		d["in"].setInput( g["out"] )
		d["target"].setValue( "/group/sphere" )

		for target, name, copies, childNames in [

			( "sphere", "", 1, [ "sphere", "sphere1" ] ),
			( "sphere", "", 2, [ "sphere", "sphere1", "sphere2" ] ),
			( "sphere", "copy", 2, [ "sphere", "copy1", "copy2" ] ),
			( "sphere", "copy", 1, [ "sphere", "copy" ] ),
			( "sphere", "sphere", 1, [ "sphere", "sphere1" ] ),
			( "sphere", "sphere", 2, [ "sphere", "sphere1", "sphere2" ] ),
			( "sphere", "copy10", 2, [ "sphere", "copy10", "copy11" ] ),
			( "sphere", "copy10", 1, [ "sphere", "copy10" ] ),
			( "sphere1", "copy10", 1, [ "sphere1", "copy10" ] ),
			( "sphere1", "sphere10", 1, [ "sphere1", "sphere10" ] ),
			( "sphere1", "sphere10", 2, [ "sphere1", "sphere10", "sphere11" ] ),
			( "sphere12", "sphere10", 1, [ "sphere12", "sphere10" ] ),
			( "sphere12", "sphere10", 2, [ "sphere12", "sphere10", "sphere11" ] ),
			( "sphere12", "sphere11", 2, [ "sphere12", "sphere11", "sphere13" ] ),
			( "sphere12", "copy", 1, [ "sphere12", "copy" ] ),
			( "sphere12", "copy2", 1, [ "sphere12", "copy2" ] ),
			( "sphere12", "copy2", 2, [ "sphere12", "copy2", "copy3" ] ),
			( "sphere12", "sphere12", 1, [ "sphere12", "sphere13" ] ),
			( "sphere12", "sphere12", 2, [ "sphere12", "sphere13", "sphere14" ] ),
		] :

			s["name"].setValue( target )
			d["target"].setValue( "/group/" + target )
			d["name"].setValue( name )
			d["copies"].setValue( copies )

			self.assertSceneValid( d["out"] )
			self.assertEqual( d["out"].childNames( "/group" ), IECore.InternedStringVectorData( childNames ) )

	def testNamePlugAffects( self ) :

		d = GafferScene.Duplicate()
		cs = GafferTest.CapturingSlot( d.plugDirtiedSignal() )

		d["name"].setValue( "test" )
		self.assertTrue( d["out"]["childNames"] in [ c[0] for c in cs ] )

	def testSets( self ) :

		s = GafferScene.Sphere()
		s["sets"].setValue( "set" )

		g = GafferScene.Group()
		g["in"][0].setInput( s["out"] )

		d = GafferScene.Duplicate()
		d["in"].setInput( g["out"] )
		d["target"].setValue( "/group" )
		d["copies"].setValue( 5 )

		self.assertEqual(
			set( d["out"].set( "set" ).value.paths() ),
			set(
				[ "/group/sphere" ] +
				[ "/group%d/sphere" % n for n in range( 1, 6 ) ]
			)
		)

		d["target"].setValue( "/group/sphere" )
		d["copies"].setValue( 1500 )

		self.assertEqual(
			set( d["out"].set( "set" ).value.paths() ),
			set(
				[ "/group/sphere" ] +
				[ "/group/sphere%d" % n for n in range( 1, 1501 ) ]
			)
		)

	def testSetNames( self ) :

		s = GafferScene.Sphere()
		s["sets"].setValue( "testSet" )
		d = GafferScene.Duplicate()
		d["in"].setInput( s["out"] )
		d["target"].setValue( "/sphere" )
		d["transform"]["translate"].setValue( imath.V3f( 1, 0, 0 ) )

		with Gaffer.PerformanceMonitor() as m :
			self.assertEqual( s["out"]["setNames"].hash(), d["out"]["setNames"].hash() )
			self.assertTrue( s["out"]["setNames"].getValue( _copy = False ).isSame( d["out"]["setNames"].getValue( _copy = False ) ) )
			self.assertEqual( s["out"]["setNames"].getValue(), IECore.InternedStringVectorData( [ "testSet" ] ) )

		self.assertEqual( m.plugStatistics( d["out"]["setNames"] ).hashCount, 0 )
		self.assertEqual( m.plugStatistics( d["out"]["setNames"] ).computeCount, 0 )

	def testPruneTarget( self ) :

		sphere = GafferScene.Sphere()

		sphereFilter = GafferScene.PathFilter()
		sphereFilter["paths"].setValue( IECore.StringVectorData( [ "/sphere" ] ) )

		prune = GafferScene.Prune()
		prune["in"].setInput( sphere["out"] )

		duplicate = GafferScene.Duplicate()
		duplicate["in"].setInput( prune["out"] )
		duplicate["target"].setValue( "/sphere" )
		self.assertEqual( duplicate["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "sphere", "sphere1" ] ) )

		prune["filter"].setInput( sphereFilter["out"] )
		self.assertEqual( duplicate["out"].childNames( "/" ), IECore.InternedStringVectorData( [] ) )

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testPerformance( self ) :

		sphere = GafferScene.Sphere()
		duplicate = GafferScene.Duplicate()
		duplicate["in"].setInput( sphere["out"] )
		duplicate["target"].setValue( "/sphere" )
		duplicate["transform"]["translate"]["x"].setValue( 2 )
		duplicate["copies"].setValue( 100000 )

		with GafferTest.TestRunner.PerformanceScope() :
			GafferSceneTest.traverseScene( duplicate["out"] )

	def testFilter( self ) :

		cube = GafferScene.Cube()
		cube["sets"].setValue( "boxes" )
		sphere = GafferScene.Sphere()

		group = GafferScene.Group()
		group["in"][0].setInput( cube["out"] )
		group["in"][1].setInput( sphere["out"] )

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/group/*" ] ) )

		duplicate = GafferScene.Duplicate()
		duplicate["in"].setInput( group["out"] )
		duplicate["filter"].setInput( filter["out"] )

		self.assertSceneValid( duplicate["out"] )

		self.assertEqual(
			duplicate["out"].childNames( "/group" ),
			IECore.InternedStringVectorData( [
				"cube", "sphere", "cube1", "sphere1",
			] )
		)

		self.assertPathsEqual( duplicate["out"], "/group/cube", duplicate["in"], "/group/cube" )
		self.assertPathsEqual( duplicate["out"], "/group/sphere", duplicate["in"], "/group/sphere" )
		self.assertPathsEqual( duplicate["out"], "/group/cube1", duplicate["in"], "/group/cube" )
		self.assertPathsEqual( duplicate["out"], "/group/sphere1", duplicate["in"], "/group/sphere" )

		self.assertEqual(
			duplicate["out"].set( "boxes" ).value,
			IECore.PathMatcher( [ "/group/cube", "/group/cube1" ] )
		)

	def testExistingTransform( self ) :

		cube = GafferScene.Cube()
		cube["transform"]["translate"]["x"].setValue( 1 )

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/cube" ] ) )

		duplicate = GafferScene.Duplicate()
		duplicate["in"].setInput( cube["out"] )
		duplicate["filter"].setInput( filter["out"] )
		duplicate["transform"]["translate"]["x"].setValue( 2 )

		self.assertSceneValid( duplicate["out"] )

		self.assertEqual(
			duplicate["out"].transform( "/cube1" ),
			imath.M44f().translate( imath.V3f( 3, 0, 0 ) )
		)

		duplicate["transform"]["translate"]["x"].setValue( 4 )

		self.assertSceneValid( duplicate["out"] )

		self.assertEqual(
			duplicate["out"].transform( "/cube1" ),
			imath.M44f().translate( imath.V3f( 5, 0, 0 ) )
		)

if __name__ == "__main__":
	unittest.main()
