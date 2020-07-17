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
import imath

import IECore
import IECoreScene

import Gaffer
import GafferTest
import GafferScene
import GafferSceneTest

class CubeTest( GafferSceneTest.SceneTestCase ) :

	def testConstruct( self ) :

		c = GafferScene.Cube()
		self.assertEqual( c.getName(), "Cube" )

	def testCompute( self ) :

		c = GafferScene.Cube()

		self.assertEqual( c["out"].object( "/" ), IECore.NullObject() )
		self.assertEqual( c["out"].transform( "/" ), imath.M44f() )
		self.assertEqual( c["out"].bound( "/" ), imath.Box3f( imath.V3f( -0.5, -0.5, -0.5 ), imath.V3f( 0.5, 0.5, 0.5 ) ) )
		self.assertEqual( c["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "cube" ] ) )

		self.assertEqual( c["out"].object( "/cube" ), IECoreScene.MeshPrimitive.createBox( imath.Box3f( imath.V3f( -0.5 ), imath.V3f( 0.5 ) ) ) )
		self.assertEqual( c["out"].transform( "/cube" ), imath.M44f() )
		self.assertEqual( c["out"].bound( "/cube" ), imath.Box3f( imath.V3f( -0.5, -0.5, -0.5 ), imath.V3f( 0.5, 0.5, 0.5 ) ) )
		self.assertEqual( c["out"].childNames( "/cube" ), IECore.InternedStringVectorData() )

	def testPlugs( self ) :

		c = GafferScene.Cube()
		m = IECoreScene.MeshPrimitive.createBox( imath.Box3f( imath.V3f( -0.5 ), imath.V3f( 0.5 ) ) )
		self.assertEqual( c["out"].object( "/cube" ), m )
		h = c["out"].objectHash( "/cube" )

		c["dimensions"].setValue( imath.V3f( 2.5, 5, 6 ) )
		m = IECoreScene.MeshPrimitive.createBox( imath.Box3f( imath.V3f( -1.25, -2.5, -3 ), imath.V3f( 1.25, 2.5, 3 ) ) )
		self.assertEqual( c["out"].object( "/cube" ), m )
		self.assertNotEqual( c["out"].objectHash( "/cube" ), h )

	def testAffects( self ) :

		c = GafferScene.Cube()

		s = GafferTest.CapturingSlot( c.plugDirtiedSignal() )

		c["name"].setValue( "box" )
		self.assertEqual(
			{ x[0] for x in s if not x[0].getName().startswith( "__" ) },
			{ c["name"], c["out"]["childNames"], c["out"]["childBounds"], c["out"]["exists"], c["out"]["set"], c["out"] }
		)

		del s[:]

		c["dimensions"]["x"].setValue( 10 )
		found = False
		for ss in s :
			if ss[0].isSame( c["out"] ) :
				found = True
		self.assertTrue( found )

	def testTransform( self ) :

		c = GafferScene.Cube()
		c["transform"]["translate"].setValue( imath.V3f( 1, 0, 0 ) )

		self.assertEqual( c["out"].transform( "/" ), imath.M44f() )
		self.assertEqual( c["out"].transform( "/cube" ), imath.M44f().translate( imath.V3f( 1, 0, 0 ) ) )

		self.assertEqual( c["out"].bound( "/" ), imath.Box3f( imath.V3f( 0.5, -0.5, -0.5 ), imath.V3f( 1.5, 0.5, 0.5 ) ) )
		self.assertEqual( c["out"].bound( "/cube" ), imath.Box3f( imath.V3f( -0.5, -0.5, -0.5 ), imath.V3f( 0.5, 0.5, 0.5 ) ) )

	def testEnabled( self ) :

		c = GafferScene.Cube()
		c["enabled"].setValue( False )

		self.assertSceneValid( c["out"] )
		self.assertTrue( c["out"].bound( "/" ).isEmpty() )
		self.assertEqual( c["out"].childNames( "/" ), IECore.InternedStringVectorData() )

		c["enabled"].setValue( True )
		self.assertSceneValid( c["out"] )
		self.assertEqual( c["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "cube" ] ) )

	def testSerialise( self ) :

		s = Gaffer.ScriptNode()
		s["c"] = GafferScene.Cube()

		ss = s.serialise()

if __name__ == "__main__":
	unittest.main()
