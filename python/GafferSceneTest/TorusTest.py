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

import unittest

import IECore

import Gaffer
import GafferTest
import GafferScene
import GafferSceneTest

class TorusTest( GafferSceneTest.SceneTestCase ) :

	def testConstruct( self ) :

		s = GafferScene.Torus()
		self.assertEqual( s.getName(), "Torus" )

	def testCompute( self ) :

		s = GafferScene.Torus()

		self.assertEqual( s["out"].object( "/" ), IECore.NullObject() )
		self.assertEqual( s["out"].transform( "/" ), IECore.M44f() )
		self.assertEqual( s["out"].bound( "/" ), IECore.Box3f( IECore.V3f( -1, -0.4, -1 ), IECore.V3f( 1, 0.4, 1 ) ) )
		self.assertEqual( s["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "torus" ] ) )

		self.assertEqual( s["out"].object( "/torus" ), IECore.MeshPrimitive.createTorus( 0.6, 0.4, IECore.V2i( 40, 20 ) ) )
		self.assertEqual( s["out"].transform( "/torus" ), IECore.M44f() )
		self.assertEqual( s["out"].bound( "/torus" ), IECore.Box3f( IECore.V3f( -1, -0.4, -1 ), IECore.V3f( 1, 0.4, 1 ) ) )
		self.assertEqual( s["out"].childNames( "/torus" ), IECore.InternedStringVectorData() )

	def testMesh( self ) :

		s = GafferScene.Torus()
		m = IECore.MeshPrimitive.createTorus( 0.6, 0.4 )
		self.assertEqual( s["out"].object( "/torus" ), m )
		c = Gaffer.Context()
		h = s["out"].objectHash( "/torus" )

		s["innerRadius"].setValue( 3 )
		s["outerRadius"].setValue( 1 )
		m = IECore.MeshPrimitive.createTorus( 3, 1 )
		self.assertEqual( s["out"].object( "/torus" ), m )
		self.assertNotEqual( s["out"].objectHash( "/torus" ), h )
		h = s["out"].objectHash( "/torus" )

		s["divisions"].setValue( IECore.V2i( 6, 10 ) )
		m = IECore.MeshPrimitive.createTorus( 3, 1, IECore.V2i( 6, 10 ) )
		self.assertEqual( s["out"].object( "/torus" ), m )
		self.assertNotEqual( s["out"].objectHash( "/torus" ), h )

	def testAffects( self ) :

		t = GafferScene.Torus()

		tt = GafferTest.CapturingSlot( t.plugDirtiedSignal() )

		t["name"].setValue( "donut" )
		self.assertEqual( len( tt ), 4 )
		self.failUnless( tt[0][0].isSame( t["name"] ) )
		self.failUnless( tt[1][0].isSame( t["out"]["childNames"] ) )
		self.failUnless( tt[2][0].isSame( t["out"]["set"] ) )
		self.failUnless( tt[3][0].isSame( t["out"] ) )

		del tt[:]

		t["divisions"]["x"].setValue( 10 )
		found = False
		for ttt in tt :
			if ttt[0].isSame( t["out"] ) :
				found = True
		self.failUnless( found )

	def testTransform( self ) :

		t = GafferScene.Torus()
		t["transform"]["translate"].setValue( IECore.V3f( 1, 0, 0 ) )

		self.assertEqual( t["out"].transform( "/" ), IECore.M44f() )
		self.assertEqual( t["out"].transform( "/torus" ), IECore.M44f.createTranslated( IECore.V3f( 1, 0, 0 ) ) )

		self.assertEqual( t["out"].bound( "/" ), IECore.Box3f( IECore.V3f( 0, -0.4, -1 ), IECore.V3f( 2, 0.4, 1 ) ) )
		self.assertEqual( t["out"].bound( "/torus" ), IECore.Box3f( IECore.V3f( -1, -0.4, -1 ), IECore.V3f( 1, 0.4, 1 ) ) )

	def testEnabled( self ) :

		t = GafferScene.Torus()
		t["enabled"].setValue( False )

		self.assertSceneValid( t["out"] )
		self.assertTrue( t["out"].bound( "/" ).isEmpty() )
		self.assertEqual( t["out"].childNames( "/" ), IECore.InternedStringVectorData() )

		t["enabled"].setValue( True )
		self.assertSceneValid( t["out"] )
		self.assertEqual( t["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "torus" ] ) )

	def testSerialise( self ) :

		t = Gaffer.ScriptNode()
		t["t"] = GafferScene.Torus()

		tt = t.serialise()

	def testChildNamesHash( self ) :

		t1 = GafferScene.Torus()
		t1["name"].setValue( "torus1" )

		t2 = GafferScene.Torus()
		t2["name"].setValue( "torus2" )

		self.assertNotEqual( t1["out"].childNamesHash( "/" ), t2["out"].childNamesHash( "/" ) )
		self.assertEqual( t1["out"].childNamesHash( "/torus1" ), t2["out"].childNamesHash( "/torus2" ) )

		self.assertNotEqual( t1["out"].childNames( "/" ), t2["out"].childNames( "/" ) )
		self.assertTrue( t1["out"].childNames( "/torus1", _copy=False ).isSame( t2["out"].childNames( "torus2", _copy=False ) ) )

if __name__ == "__main__":
	unittest.main()
