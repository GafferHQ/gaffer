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

import unittest

import IECore

import GafferScene
import GafferSceneTest

class SceneAlgoTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		sphere = GafferScene.Sphere()
		plane = GafferScene.Plane()
		group = GafferScene.Group()
		group["in"][0].setInput( sphere["out"] )
		group["in"][1].setInput( plane["out"] )

		plane2 = GafferScene.Plane()
		plane2["divisions"].setValue( IECore.V2i( 99, 99 ) ) # 10000 instances

		instancer = GafferScene.Instancer()
		instancer["in"].setInput( plane2["out"] )
		instancer["parent"].setValue( "/plane" )
		instancer["instance"].setInput( group["out"] )

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/plane/instances/*1/group/plane" ] ) )

		matchingPaths = GafferScene.PathMatcher()
		GafferScene.matchingPaths( filter, instancer["out"], matchingPaths )

		self.assertEqual( len( matchingPaths.paths() ), 1000 )
		self.assertEqual( matchingPaths.match( "/plane/instances/1/group/plane" ), GafferScene.Filter.Result.ExactMatch )
		self.assertEqual( matchingPaths.match( "/plane/instances/1121/group/plane" ), GafferScene.Filter.Result.ExactMatch )
		self.assertEqual( matchingPaths.match( "/plane/instances/1121/group/sphere" ), GafferScene.Filter.Result.NoMatch )

	def testExists( self ) :

		sphere = GafferScene.Sphere()
		plane = GafferScene.Plane()
		group = GafferScene.Group()
		group["in"][0].setInput( sphere["out"] )
		group["in"][1].setInput( plane["out"] )

		self.assertTrue( GafferScene.exists( group["out"], "/" ) )
		self.assertTrue( GafferScene.exists( group["out"], "/group" ) )
		self.assertTrue( GafferScene.exists( group["out"], "/group/sphere" ) )
		self.assertTrue( GafferScene.exists( group["out"], "/group/plane" ) )

		self.assertFalse( GafferScene.exists( group["out"], "/a" ) )
		self.assertFalse( GafferScene.exists( group["out"], "/group2" ) )
		self.assertFalse( GafferScene.exists( group["out"], "/group/sphere2" ) )
		self.assertFalse( GafferScene.exists( group["out"], "/group/plane/child" ) )

	def testVisible( self ) :

		sphere = GafferScene.Sphere()
		group = GafferScene.Group()
		group["in"][0].setInput( sphere["out"] )
		group2 = GafferScene.Group()
		group2["in"][0].setInput( group["out"] )

		visibleFilter = GafferScene.PathFilter()

		attributes1 = GafferScene.StandardAttributes()
		attributes1["attributes"]["visibility"]["enabled"].setValue( True )
		attributes1["attributes"]["visibility"]["value"].setValue( True )
		attributes1["in"].setInput( group2["out"] )
		attributes1["filter"].setInput( visibleFilter["out"] )

		invisibleFilter = GafferScene.PathFilter()

		attributes2 = GafferScene.StandardAttributes()
		attributes2["attributes"]["visibility"]["enabled"].setValue( True )
		attributes2["attributes"]["visibility"]["value"].setValue( False )
		attributes2["in"].setInput( attributes1["out"] )
		attributes2["filter"].setInput( invisibleFilter["out"] )

		self.assertTrue( GafferScene.visible( attributes2["out"], "/group/group/sphere" ) )
		self.assertTrue( GafferScene.visible( attributes2["out"], "/group/group" ) )
		self.assertTrue( GafferScene.visible( attributes2["out"], "/group" ) )
		self.assertTrue( GafferScene.visible( attributes2["out"], "/" ) )

		visibleFilter["paths"].setValue( IECore.StringVectorData( [ "/group" ] ) )

		self.assertTrue( GafferScene.visible( attributes2["out"], "/group/group/sphere" ) )
		self.assertTrue( GafferScene.visible( attributes2["out"], "/group/group" ) )
		self.assertTrue( GafferScene.visible( attributes2["out"], "/group" ) )
		self.assertTrue( GafferScene.visible( attributes2["out"], "/" ) )

		invisibleFilter["paths"].setValue( IECore.StringVectorData( [ "/group/group" ] ) )

		self.assertFalse( GafferScene.visible( attributes2["out"], "/group/group/sphere" ) )
		self.assertFalse( GafferScene.visible( attributes2["out"], "/group/group" ) )
		self.assertTrue( GafferScene.visible( attributes2["out"], "/group" ) )
		self.assertTrue( GafferScene.visible( attributes2["out"], "/" ) )

		visibleFilter["paths"].setValue( IECore.StringVectorData( [ "/group/group/sphere" ] ) )

		self.assertFalse( GafferScene.visible( attributes2["out"], "/group/group/sphere" ) )
		self.assertFalse( GafferScene.visible( attributes2["out"], "/group/group" ) )
		self.assertTrue( GafferScene.visible( attributes2["out"], "/group" ) )
		self.assertTrue( GafferScene.visible( attributes2["out"], "/" ) )

	def testSetExists( self ) :

		plane = GafferScene.Plane()
		plane["sets"].setValue( "A B" )

		self.assertTrue( GafferScene.setExists( plane["out"], "A" ) )
		self.assertTrue( GafferScene.setExists( plane["out"], "B" ) )
		self.assertFalse( GafferScene.setExists( plane["out"], " " ) )
		self.assertFalse( GafferScene.setExists( plane["out"], "" ) )
		self.assertFalse( GafferScene.setExists( plane["out"], "C" ) )

	def testSets( self ) :

		light = GafferSceneTest.TestLight()
		light["sets"].setValue( "A B C" )

		sets = GafferScene.sets( light["out"] )
		self.assertEqual( set( sets.keys() ), { "__lights", "A", "B", "C" } )
		for n in sets.keys() :
			self.assertEqual( sets[n], light["out"].set( n ) )
			self.assertFalse( sets[n].isSame( light["out"].set( n, _copy = False ) ) )

		sets = GafferScene.sets( light["out"], _copy = False )
		self.assertEqual( set( sets.keys() ), { "__lights", "A", "B", "C" } )
		for n in sets.keys() :
			self.assertTrue( sets[n].isSame( light["out"].set( n, _copy = False ) ) )

	def testMatchingPathsWithPathMatcher( self ) :

		s = GafferScene.Sphere()
		g = GafferScene.Group()
		g["in"][0].setInput( s["out"] )
		g["in"][1].setInput( s["out"] )
		g["in"][2].setInput( s["out"] )

		f = GafferScene.PathMatcher( [ "/group/s*" ] )
		m = GafferScene.PathMatcher()
		GafferScene.matchingPaths( f, g["out"], m )

		self.assertEqual( set( m.paths() ), { "/group/sphere", "/group/sphere1", "/group/sphere2" } )

	def testDefaultCamera( self ) :

		o = GafferScene.StandardOptions()
		c1 = GafferScene.camera( o["out"] )
		self.assertTrue( isinstance( c1, IECore.Camera ) )

		o["options"]["renderCamera"]["enabled"].setValue( True )
		c2 = GafferScene.camera( o["out"] )
		self.assertEqual( c1, c2 )

if __name__ == "__main__":
	unittest.main()
