##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
#  Copyright (c) 2013-2014, Image Engine Design Inc. All rights reserved.
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
import threading

import IECore

import Gaffer
import GafferTest
import GafferScene
import GafferSceneTest

class SeedsTest( GafferSceneTest.SceneTestCase ) :

	def testChildNames( self ) :

		p = GafferScene.Plane()
		s = GafferScene.Seeds()
		s["in"].setInput( p["out"] )
		s["parent"].setValue( "/plane" )
		s["name"].setValue( "seeds" )

		self.assertEqual( s["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "plane" ] ) )
		self.assertEqual( s["out"].childNames( "/plane" ), IECore.InternedStringVectorData( [ "seeds" ] ) )
		self.assertEqual( s["out"].childNames( "/plane/seeds" ), IECore.InternedStringVectorData() )

		s["name"].setValue( "points" )

		self.assertEqual( s["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "plane" ] ) )
		self.assertEqual( s["out"].childNames( "/plane" ), IECore.InternedStringVectorData( [ "points" ] ) )
		self.assertEqual( s["out"].childNames( "/plane/points" ), IECore.InternedStringVectorData() )

	def testObject( self ) :

		p = GafferScene.Plane()
		s = GafferScene.Seeds()
		s["in"].setInput( p["out"] )
		s["parent"].setValue( "/plane" )
		s["name"].setValue( "seeds" )

		self.assertEqual( s["out"].objectHash( "/plane" ), p["out"].objectHash( "/plane" ) )
		self.assertEqual( s["out"].object( "/plane" ), p["out"].object( "/plane" ) )

		self.failUnless( isinstance( s["out"].object( "/plane/seeds" ), IECore.PointsPrimitive ) )
		numPoints = s["out"].object( "/plane/seeds" ).numPoints

		s["density"].setValue( 10 )
		self.failUnless( s["out"].object( "/plane/seeds" ).numPoints > numPoints )

		h = s["out"].objectHash( "/plane/seeds" )
		m = s["out"].object( "/plane/seeds" )
		s["name"].setValue( "notSeeds" )
		self.assertEqual( h, s["out"].objectHash( "/plane/notSeeds" ) )
		self.assertEqual( m, s["out"].object( "/plane/notSeeds" ) )

	def testSceneValidity( self ) :

		p = GafferScene.Plane()
		s = GafferScene.Seeds()
		s["in"].setInput( p["out"] )
		s["parent"].setValue( "/plane" )
		s["name"].setValue( "seeds" )

		self.assertSceneValid( s["out"] )

	def testDisabled( self ) :

		p = GafferScene.Plane()
		s = GafferScene.Seeds()
		s["in"].setInput( p["out"] )
		s["parent"].setValue( "/plane" )
		s["name"].setValue( "seeds" )

		self.assertEqual( s["out"].childNames( "/plane" ), IECore.InternedStringVectorData( [ "seeds" ] ) )

		s["enabled"].setValue( False )

		self.assertEqual( s["out"].childNames( "/plane" ), IECore.InternedStringVectorData() )
		self.assertScenesEqual( s["out"], p["out"] )

	def testNamePlugDefaultValue( self ) :

		s = GafferScene.Seeds()
		self.assertEqual( s["name"].defaultValue(), "seeds" )
		self.assertEqual( s["name"].getValue(), "seeds" )

	def testDirtyPropagation( self ) :

		p = GafferScene.Plane()

		s = GafferScene.Seeds()
		s["in"].setInput( p["out"] )
		s["parent"].setValue( "/plane" )
		s["name"].setValue( "seeds" )

		s2 = GafferScene.Seeds()
		s2["in"].setInput( s["out"] )
		s2["parent"].setValue( "/plane" )
		s2["name"].setValue( "seeds" )
		s2["density"].setValue( 10 )

		dirtied = GafferTest.CapturingSlot( s2.plugDirtiedSignal() )
		s2["name"].setValue( "blah" )
		self.failUnless( s2["__mapping"] in [ p[0] for p in dirtied ] )
		self.failUnless( s2["out"]["childNames"] in [ p[0] for p in dirtied ] )

		dirtied = GafferTest.CapturingSlot( s2.plugDirtiedSignal() )
		s["name"].setValue( "blah" )
		self.failUnless( s2["__mapping"] in [ p[0] for p in dirtied ] )
		self.failUnless( s2["out"]["childNames"] in [ p[0] for p in dirtied ] )

	def testMultipleChildren( self ) :

		p = GafferScene.Plane()

		s = GafferScene.Seeds()
		s["in"].setInput( p["out"] )
		s["parent"].setValue( "/plane" )
		s["name"].setValue( "seeds" )

		s2 = GafferScene.Seeds()
		s2["in"].setInput( s["out"] )
		s2["parent"].setValue( "/plane" )
		s2["name"].setValue( "seeds" )
		s2["density"].setValue( 10 )

		self.assertEqual( s2["out"].childNames( "/plane" ), IECore.InternedStringVectorData( [ "seeds", "seeds1" ] ) )
		self.assertTrue( len( s2["out"].object( "/plane/seeds" )["P"].data ) < len( s2["out"].object( "/plane/seeds1" )["P"].data ) )

		self.assertSceneValid( s["out"] )
		self.assertSceneValid( s2["out"] )

		s["name"].setValue( "seeds1" )
		self.assertEqual( s2["out"].childNames( "/plane" ), IECore.InternedStringVectorData( [ "seeds1", "seeds" ] ) )
		self.assertTrue( len( s2["out"].object( "/plane/seeds1" )["P"].data ) < len( s2["out"].object( "/plane/seeds" )["P"].data ) )

		self.assertEqual( s2["out"].objectHash( "/plane/seeds1" ), s["out"].objectHash( "/plane/seeds1" ) )

		self.assertSceneValid( s["out"] )
		self.assertSceneValid( s2["out"] )

	def testEmptyName( self ) :

		p = GafferScene.Plane()

		s = GafferScene.Seeds()
		s["in"].setInput( p["out"] )
		s["parent"].setValue( "/plane" )
		s["name"].setValue( "" )

		self.assertScenesEqual( s["out"], p["out"] )
		self.assertSceneHashesEqual( s["out"], p["out"] )

	def testEmptyParent( self ) :

		p = GafferScene.Plane()
		s = GafferScene.Seeds()

		s["in"].setInput( p["out"] )
		s["parent"].setValue( "" )

		self.assertScenesEqual( s["out"], p["out"] )
		self.assertSceneHashesEqual( s["out"], p["out"] )

	def testGlobalsPassThrough( self ) :

		p = GafferScene.Plane()
		l = GafferSceneTest.TestLight()

		g = GafferScene.Group()
		g["in"].setInput( p["out"] )
		g["in1"].setInput( l["out"] )

		s = GafferScene.Seeds()
		s["in"].setInput( g["out"] )
		s["parent"].setValue( "/group/plane" )

		self.assertEqual( s["in"]["globals"].hash(), s["out"]["globals"].hash() )
		self.assertEqual( s["in"]["globals"].getValue(), s["out"]["globals"].getValue() )

if __name__ == "__main__":
	unittest.main()
