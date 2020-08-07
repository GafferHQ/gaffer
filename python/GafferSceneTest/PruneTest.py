##########################################################################
#
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
import IECoreScene

import Gaffer
import GafferScene
import GafferSceneTest

class PruneTest( GafferSceneTest.SceneTestCase ) :

	def testPassThrough( self ) :

		sphere = IECoreScene.SpherePrimitive()
		input = GafferSceneTest.CompoundObjectSource()
		input["in"].setValue(
			IECore.CompoundObject( {
				"bound" : IECore.Box3fData( sphere.bound() ),
				"children" : {
					"groupA" : {
						"bound" : IECore.Box3fData( sphere.bound() ),
						"children" : {
							"sphereAA" : {
								"bound" : IECore.Box3fData( sphere.bound() ),
								"object" : sphere,
							},
							"sphereAB" : {
								"bound" : IECore.Box3fData( sphere.bound() ),
								"object" : sphere,
							},
						},
					},
					"groupB" : {
						"bound" : IECore.Box3fData( sphere.bound() ),
						"children" : {
							"sphereBA" : {
								"bound" : IECore.Box3fData( sphere.bound() ),
								"object" : sphere,
							},
							"sphereBB" : {
								"bound" : IECore.Box3fData( sphere.bound() ),
								"object" : sphere,
							},
						},
					},
				},
			} ),
		)

		prune = GafferScene.Prune()
		prune["in"].setInput( input["out"] )

		self.assertSceneValid( input["out"] )
		self.assertSceneValid( prune["out"] )

		# with no filter applied, nothing should be pruned so we should have a perfect pass through

		self.assertScenesEqual( input["out"], prune["out"] )
		self.assertSceneHashesEqual( input["out"], prune["out"] )
		self.assertTrue( input["out"].object( "/groupA/sphereAA", _copy = False ).isSame( prune["out"].object( "/groupA/sphereAA", _copy = False ) ) )

		# and even with a filter applied, we should have a perfect pass through if the node is disabled.

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/*" ] ) )
		prune["filter"].setInput( filter["out"] )

		prune["enabled"].setValue( False )

		self.assertScenesEqual( input["out"], prune["out"] )
		self.assertSceneHashesEqual( input["out"], prune["out"] )
		self.assertTrue( input["out"].object( "/groupA/sphereAA", _copy = False ).isSame( prune["out"].object( "/groupA/sphereAA", _copy = False ) ) )

		# The pass through should also apply to the `childBounds` plug, which is automatically
		# computed by SceneNode/SceneProcessor.

		for path in [
			"/",
			"/groupA",
			"/groupB",
			"/groupA/sphereAA",
			"/groupA/sphereAB",
			"/groupB/sphereBA",
			"/groupB/sphereBB",
		] :

			self.assertEqual(
				prune["out"].childBoundsHash( path ),
				prune["in"].childBoundsHash( path ),
			)

			self.assertEqual(
				prune["out"].childBounds( path ),
				prune["in"].childBounds( path ),
			)

	def testPruning( self ) :

		sphere = IECoreScene.SpherePrimitive()
		input = GafferSceneTest.CompoundObjectSource()
		input["in"].setValue(
			IECore.CompoundObject( {
				"bound" : IECore.Box3fData( sphere.bound() ),
				"children" : {
					"groupA" : {
						"bound" : IECore.Box3fData( sphere.bound() ),
						"children" : {
							"sphereAA" : {
								"bound" : IECore.Box3fData( sphere.bound() ),
								"object" : sphere,
							},
							"sphereAB" : {
								"bound" : IECore.Box3fData( sphere.bound() ),
								"object" : sphere,
							},
						},
					},
					"groupB" : {
						"bound" : IECore.Box3fData( sphere.bound() ),
						"children" : {
							"sphereBA" : {
								"bound" : IECore.Box3fData( sphere.bound() ),
								"object" : sphere,
							},
							"sphereBB" : {
								"bound" : IECore.Box3fData( sphere.bound() ),
								"object" : sphere,
							},
						},
					},
				},
			} ),
		)

		prune = GafferScene.Prune()
		prune["in"].setInput( input["out"] )

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/groupA/sphereAB" ] ) )
		prune["filter"].setInput( filter["out"] )

		self.assertNotEqual( prune["out"].childNamesHash( "/groupA" ), input["out"].childNamesHash( "/groupA" ) )
		self.assertEqual( prune["out"].childNames( "/groupA" ), IECore.InternedStringVectorData( [ "sphereAA" ] ) )

		filter["paths"].setValue( IECore.StringVectorData( [ "/groupA/sphereAA" ] ) )
		self.assertEqual( prune["out"].childNames( "/groupA" ), IECore.InternedStringVectorData( [ "sphereAB" ] ) )

	def testAdjustBounds( self ) :

		sphere1 = IECoreScene.SpherePrimitive()
		sphere2 = IECoreScene.SpherePrimitive( 2 )
		input = GafferSceneTest.CompoundObjectSource()
		input["in"].setValue(
			IECore.CompoundObject( {
				"bound" : IECore.Box3fData( sphere2.bound() ),
				"children" : {
					"group" : {
						"bound" : IECore.Box3fData( sphere2.bound() ),
						"children" : {
							"sphere1" : {
								"bound" : IECore.Box3fData( sphere1.bound() ),
								"object" : sphere1,
							},
							"sphere2" : {
								"bound" : IECore.Box3fData( sphere2.bound() ),
								"object" : sphere2,
							},
						},
					},
				},
			} ),
		)

		prune = GafferScene.Prune()
		prune["in"].setInput( input["out"] )

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/group/sphere2" ] ) )
		prune["filter"].setInput( filter["out"] )

		self.assertEqual( prune["out"].bound( "/" ), sphere2.bound() )
		self.assertEqual( prune["out"].bound( "/group" ), sphere2.bound() )
		self.assertEqual( prune["out"].bound( "/group/sphere1" ), sphere1.bound() )

		prune["adjustBounds"].setValue( True )

		self.assertEqual( prune["out"].bound( "/" ), sphere1.bound() )
		self.assertEqual( prune["out"].bound( "/group" ), sphere1.bound() )
		self.assertEqual( prune["out"].bound( "/group/sphere1" ), sphere1.bound() )

	def testLightSets( self ) :

		light1 = GafferSceneTest.TestLight()
		light2 = GafferSceneTest.TestLight()

		group = GafferScene.Group()
		group["in"][0].setInput( light1["out"] )
		group["in"][1].setInput( light2["out"] )

		lightSet = group["out"].set( "__lights" )
		self.assertEqual( set( lightSet.value.paths() ), set( [ "/group/light", "/group/light1" ] ) )

		prune = GafferScene.Prune()
		prune["in"].setInput( group["out"] )

		lightSet = prune["out"].set( "__lights" )
		self.assertEqual( set( lightSet.value.paths() ), set( [ "/group/light", "/group/light1" ] ) )

		filter = GafferScene.PathFilter()
		prune["filter"].setInput( filter["out"] )

		lightSet = prune["out"].set( "__lights" )
		self.assertEqual( set( lightSet.value.paths() ), set( [ "/group/light", "/group/light1" ] ) )

		filter["paths"].setValue( IECore.StringVectorData( [ "/group/light" ] ) )
		lightSet = prune["out"].set( "__lights" )
		self.assertEqual( set( lightSet.value.paths() ), set( [ "/group/light1" ] ) )

		filter["paths"].setValue( IECore.StringVectorData( [ "/group/light*" ] ) )
		lightSet = prune["out"].set( "__lights" )
		self.assertEqual( lightSet.value.paths(), [] )

	def testSetsWhenAncestorPruned( self ) :

		light1 = GafferSceneTest.TestLight()
		light2 = GafferSceneTest.TestLight()

		group1 = GafferScene.Group()
		group2 = GafferScene.Group()

		group1["in"][0].setInput( light1["out"] )
		group2["in"][0].setInput( light1["out"] )

		topGroup = GafferScene.Group()
		topGroup["in"][0].setInput( group1["out"] )
		topGroup["in"][1].setInput( group2["out"] )

		lightSet = topGroup["out"].set( "__lights" )
		self.assertEqual( set( lightSet.value.paths() ), set( [ "/group/group/light", "/group/group1/light" ] ) )

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/group/group" ] ) )

		prune = GafferScene.Prune()
		prune["in"].setInput( topGroup["out"] )
		prune["filter"].setInput( filter["out"] )

		lightSet = prune["out"].set( "__lights" )
		self.assertEqual( set( lightSet.value.paths() ), set( [ "/group/group1/light" ] ) )

	def testPruneRoot( self ) :

		sphere = GafferScene.Sphere()
		sphere["sets"].setValue("sphereSet")

		p = GafferScene.Prune()
		p["in"].setInput( sphere["out"] )
		pathFilter = GafferScene.PathFilter()
		p["filter"].setInput( pathFilter["out"] )

		self.assertEqual( p["out"].childNames("/"), IECore.InternedStringVectorData( [ "sphere" ] ) )
		self.assertEqual( p["out"].set( "sphereSet" ).value.paths(), ["/sphere"] )
		pathFilter["paths"].setValue( IECore.StringVectorData( ["/"] ) )
		self.assertEqual( p["out"].set( "sphereSet" ).value.paths(), [] )
		self.assertEqual( p["out"].childNames("/"), IECore.InternedStringVectorData() )

	def testFilterPromotion( self ) :

		b = Gaffer.Box()
		b["n"] = GafferScene.Prune()

		self.assertTrue( Gaffer.PlugAlgo.canPromote( b["n"]["filter"] ) )
		Gaffer.PlugAlgo.promote( b["n"]["filter"] )
		self.assertTrue( Gaffer.PlugAlgo.isPromoted( b["n"]["filter"] ) )

	def testSets( self ) :

		setPaths = [
			[
				"/a",
				"/a/b/c/d/e",
				"/a/b/c",
				"/b/c",
			],
			[
				"/f/g/h/i",
			],
		]

		filterPaths = [
			[],
			[
				"/*",
			],
			[
				"/a",
			],
			[
				"/a/b",
			],
			[
				"/f/g/h/...",
			],
		]

		for s in setPaths :
			for p in filterPaths :

				pathFilter = GafferScene.PathFilter()
				pathFilter["paths"].setValue( IECore.StringVectorData( p ) )

				setNode = GafferScene.Set()
				setNode["paths"].setValue( IECore.StringVectorData( s ) )

				prune = GafferScene.Prune()
				prune["in"].setInput( setNode["out"] )
				prune["filter"].setInput( pathFilter["out"] )

				outputSet = set( prune["out"].set( "set" ).value.paths() )
				filterMatcher = IECore.PathMatcher( p )
				for inputSetPath in s :
					if filterMatcher.match( inputSetPath ) & ( IECore.PathMatcher.Result.ExactMatch | IECore.PathMatcher.Result.AncestorMatch ) :
						self.assertTrue( inputSetPath not in outputSet )
					else :
						self.assertTrue( inputSetPath in outputSet )

if __name__ == "__main__":
	unittest.main()
