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


	def testDivisions( self ) :
		# In order to validate the handling of divisions, we could either reproduce some rather complicated
		# code in Python, or we can just hardcode a test case that should exercise all code paths, and has
		# been carefully check visually.  I've opted for the latter.
		#
		# In order to validate everything, the choice of a value for `divisions` is important. There should
		# be at least 3 divisions on all axes ( so that there are at least 2 points on the face interiors,
		# making sure that the internal functions add[XYZ]Face get the order correct ), and value should be
		# different for each axis ( one of the most plausible sources of bugs in this code is using the
		# wrong axis ). The smallest value for `divisions` satisfying both of these is <3,4,5>, which results
		# in a somewhat large amount of reference data, but it's hopefully not unreasonable.

		dimensions = imath.V3f( 6, 8, 10 )

		c = GafferScene.Cube()
		c["dimensions"].setValue( dimensions )
		m = IECoreScene.MeshPrimitive.createBox( imath.Box3f( -0.5 * dimensions, 0.5 * dimensions ) )
		self.assertEqual( c["out"].object( "/cube" ), m )

		c["divisions"].setValue( imath.V3i( 3, 4, 5 ) )

		refVertexIds = [
16, 84, 8, 0, 84, 85, 9, 8, 85, 22, 1, 9, 17, 86, 84, 16, 86, 87, 85, 84, 87, 23, 22, 85, 18, 88, 86, 17, 88, 89, 87, 86, 89, 24, 23, 87, 3, 12, 88, 18, 12, 13, 89, 88, 13, 2, 24, 89, 1, 22, 56, 36, 22, 23, 57, 56, 23, 24, 58, 57, 24, 2, 40, 58, 36, 56, 59, 37, 56, 57, 60, 59, 57, 58, 61, 60, 58, 40, 41, 61, 37, 59, 62, 38, 59, 60, 63, 62, 60, 61, 64, 63, 61, 41, 42, 64, 38, 62, 65, 39, 62, 63, 66, 65, 63, 64, 67, 66, 64, 42, 43, 67, 39, 65, 25, 4, 65, 66, 26, 25, 66, 67, 27, 26, 67, 43, 5, 27, 10, 90, 19, 6, 11, 91, 90, 10, 4, 25, 91, 11, 90, 92, 20, 19, 91, 93, 92, 90, 25, 26, 93, 91, 92, 94, 21, 20, 93, 95, 94, 92, 26, 27, 95, 93, 94, 14, 7, 21, 95, 15, 14, 94, 27, 5, 15, 95, 28, 44, 16, 0, 44, 45, 17, 16, 45, 46, 18, 17, 46, 32, 3, 18, 29, 47, 44, 28, 47, 48, 45, 44, 48, 49, 46, 45, 49, 33, 32, 46, 30, 50, 47, 29, 50, 51, 48, 47, 51, 52, 49, 48, 52, 34, 33, 49, 31, 53, 50, 30, 53, 54, 51, 50, 54, 55, 52, 51, 55, 35, 34, 52, 6, 19, 53, 31, 19, 20, 54, 53, 20, 21, 55, 54, 21, 7, 35, 55, 12, 3, 32, 76, 13, 12, 76, 77, 2, 13, 77, 40, 76, 32, 33, 78, 77, 76, 78, 79, 40, 77, 79, 41, 78, 33, 34, 80, 79, 78, 80, 81, 41, 79, 81, 42, 80, 34, 35, 82, 81, 80, 82, 83, 42, 81, 83, 43, 82, 35, 7, 14, 83, 82, 14, 15, 43, 83, 15, 5, 0, 8, 68, 28, 8, 9, 69, 68, 9, 1, 36, 69, 28, 68, 70, 29, 68, 69, 71, 70, 69, 36, 37, 71, 29, 70, 72, 30, 70, 71, 73, 72, 71, 37, 38, 73, 30, 72, 74, 31, 72, 73, 75, 74, 73, 38, 39, 75, 31, 74, 10, 6, 74, 75, 11, 10, 75, 39, 4, 11
]
		refP = [
-3, -4, -5, 3, -4, -5, 3, 4, -5, -3, 4, -5, 3, -4, 5, 3, 4, 5, -3, -4, 5, -3, 4, 5, -1, -4, -5, 1, -4, -5, -1, -4, 5, 1, -4, 5, -1, 4, -5, 1, 4, -5, -1, 4, 5, 1, 4, 5, -3, -2, -5, -3, 0, -5, -3, 2, -5, -3, -2, 5, -3, 0, 5, -3, 2, 5, 3, -2, -5, 3, 0, -5, 3, 2, -5, 3, -2, 5, 3, 0, 5, 3, 2, 5, -3, -4, -3, -3, -4, -1, -3, -4, 1, -3, -4, 3, -3, 4, -3, -3, 4, -1, -3, 4, 1, -3, 4, 3, 3, -4, -3, 3, -4, -1, 3, -4, 1, 3, -4, 3, 3, 4, -3, 3, 4, -1, 3, 4, 1, 3, 4, 3, -3, -2, -3, -3, 0, -3, -3, 2, -3, -3, -2, -1, -3, 0, -1, -3, 2, -1, -3, -2, 1, -3, 0, 1, -3, 2, 1, -3, -2, 3, -3, 0, 3, -3, 2, 3, 3, -2, -3, 3, 0, -3, 3, 2, -3, 3, -2, -1, 3, 0, -1, 3, 2, -1, 3, -2, 1, 3, 0, 1, 3, 2, 1, 3, -2, 3, 3, 0, 3, 3, 2, 3, -1, -4, -3, 1, -4, -3, -1, -4, -1, 1, -4, -1, -1, -4, 1, 1, -4, 1, -1, -4, 3, 1, -4, 3, -1, 4, -3, 1, 4, -3, -1, 4, -1, 1, 4, -1, -1, 4, 1, 1, 4, 1, -1, 4, 3, 1, 4, 3, -1, -2, -5, 1, -2, -5, -1, 0, -5, 1, 0, -5, -1, 2, -5, 1, 2, -5, -1, -2, 5, 1, -2, 5, -1, 0, 5, 1, 0, 5, -1, 2, 5, 1, 2, 5
		]

		uvA = 0.458333343
		uvB = 0.541666687

		refUVData = [
0.375, 0, uvA, 0, uvB, 0, 0.625, 0, 0.375, 0.0625, uvA, 0.0625, uvB, 0.0625, 0.625, 0.0625, 0.375, 0.125, uvA, 0.125, uvB, 0.125, 0.625, 0.125, 0.375, 0.1875, uvA, 0.1875, uvB, 0.1875, 0.625, 0.1875, 0.375, 0.25, uvA, 0.25, uvB, 0.25, 0.625, 0.25, 0.375, 0.3, uvA, 0.3, uvB, 0.3, 0.625, 0.3, 0.375, 0.35, uvA, 0.35, uvB, 0.35, 0.625, 0.35, 0.375, 0.4, uvA, 0.4, uvB, 0.4, 0.625, 0.4, 0.375, 0.45, uvA, 0.45, uvB, 0.45, 0.625, 0.45, 0.375, 0.5, uvA, 0.5, uvB, 0.5, 0.625, 0.5, 0.375, 0.5625, uvA, 0.5625, uvB, 0.5625, 0.625, 0.5625, 0.375, 0.625, uvA, 0.625, uvB, 0.625, 0.625, 0.625, 0.375, 0.6875, uvA, 0.6875, uvB, 0.6875, 0.625, 0.6875, 0.375, 0.75, uvA, 0.75, uvB, 0.75, 0.625, 0.75, 0.375, 0.8, uvA, 0.8, uvB, 0.8, 0.625, 0.8, 0.375, 0.85, uvA, 0.85, uvB, 0.85, 0.625, 0.85, 0.375, 0.9, uvA, 0.9, uvB, 0.9, 0.625, 0.9, 0.375, 0.95, uvA, 0.95, uvB, 0.95, 0.625, 0.95, 0.375, 1, uvA, 1, uvB, 1, 0.625, 1, 0.325, 0, 0.275, 0, 0.225, 0, 0.175, 0, 0.125, 0, 0.875, 0, 0.825, 0, 0.775, 0, 0.725, 0, 0.675, 0, 0.325, 0.0625, 0.275, 0.0625, 0.225, 0.0625, 0.175, 0.0625, 0.125, 0.0625, 0.875, 0.0625, 0.825, 0.0625, 0.775, 0.0625, 0.725, 0.0625, 0.675, 0.0625, 0.325, 0.125, 0.275, 0.125, 0.225, 0.125, 0.175, 0.125, 0.125, 0.125, 0.875, 0.125, 0.825, 0.125, 0.775, 0.125, 0.725, 0.125, 0.675, 0.125, 0.325, 0.1875, 0.275, 0.1875, 0.225, 0.1875, 0.175, 0.1875, 0.125, 0.1875, 0.875, 0.1875, 0.825, 0.1875, 0.775, 0.1875, 0.725, 0.1875, 0.675, 0.1875, 0.325, 0.25, 0.275, 0.25, 0.225, 0.25, 0.175, 0.25, 0.125, 0.25, 0.875, 0.25, 0.825, 0.25, 0.775, 0.25, 0.725, 0.25, 0.675, 0.25
		]

		refUVIndices = [ 48, 49, 53, 52, 49, 50, 54, 53, 50, 51, 55, 54, 44, 45, 49, 48, 45, 46, 50, 49, 46, 47, 51, 50, 40, 41, 45, 44, 41, 42, 46, 45, 42, 43, 47, 46, 36, 37, 41, 40, 37, 38, 42, 41, 38, 39, 43, 42, 81, 91, 92, 82, 91, 101, 102, 92, 101, 111, 112, 102, 111, 121, 122, 112, 82, 92, 93, 83, 92, 102, 103, 93, 102, 112, 113, 103, 112, 122, 123, 113, 83, 93, 94, 84, 93, 103, 104, 94, 103, 113, 114, 104, 113, 123, 124, 114, 84, 94, 95, 85, 94, 104, 105, 95, 104, 114, 115, 105, 114, 124, 125, 115, 85, 95, 7, 3, 95, 105, 11, 7, 105, 115, 15, 11, 115, 125, 19, 15, 1, 5, 4, 0, 2, 6, 5, 1, 3, 7, 6, 2, 5, 9, 8, 4, 6, 10, 9, 5, 7, 11, 10, 6, 9, 13, 12, 8, 10, 14, 13, 9, 11, 15, 14, 10, 13, 17, 16, 12, 14, 18, 17, 13, 15, 19, 18, 14, 79, 89, 90, 80, 89, 99, 100, 90, 99, 109, 110, 100, 109, 119, 120, 110, 78, 88, 89, 79, 88, 98, 99, 89, 98, 108, 109, 99, 108, 118, 119, 109, 77, 87, 88, 78, 87, 97, 98, 88, 97, 107, 108, 98, 107, 117, 118, 108, 76, 86, 87, 77, 86, 96, 97, 87, 96, 106, 107, 97, 106, 116, 117, 107, 0, 4, 86, 76, 4, 8, 96, 86, 8, 12, 106, 96, 12, 16, 116, 106, 37, 36, 32, 33, 38, 37, 33, 34, 39, 38, 34, 35, 33, 32, 28, 29, 34, 33, 29, 30, 35, 34, 30, 31, 29, 28, 24, 25, 30, 29, 25, 26, 31, 30, 26, 27, 25, 24, 20, 21, 26, 25, 21, 22, 27, 26, 22, 23, 21, 20, 16, 17, 22, 21, 17, 18, 23, 22, 18, 19, 52, 53, 57, 56, 53, 54, 58, 57, 54, 55, 59, 58, 56, 57, 61, 60, 57, 58, 62, 61, 58, 59, 63, 62, 60, 61, 65, 64, 61, 62, 66, 65, 62, 63, 67, 66, 64, 65, 69, 68, 65, 66, 70, 69, 66, 67, 71, 70, 68, 69, 73, 72, 69, 70, 74, 73, 70, 71, 75, 74
		]

		m = IECoreScene.MeshPrimitive(
			IECore.IntVectorData( [ 4 ] * 94 ),
			IECore.IntVectorData( refVertexIds ),
			"linear",
			IECore.V3fVectorData( [ imath.V3f( *refP[i*3 : (i+1)*3] ) for i in range( 96 ) ] )
		)
		m["N"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.FaceVarying,
			IECore.V3fVectorData( [
				imath.V3f( 0, 0, 1 ),
				imath.V3f( 0, 0, -1 ),
				imath.V3f( 0, 1, 0 ),
				imath.V3f( 0, -1, 0 ),
				imath.V3f( 1, 0, 0 ),
				imath.V3f( -1, 0, 0 ),
			], IECore.GeometricData.Interpretation.Normal ),
			IECore.IntVectorData( [1] * 48 + [4] * 80 + [0] * 48 + [5] * 80 + [2] * 60 + [3] * 60 )
		)
		m["uv"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.FaceVarying,
			IECore.V2fVectorData(
				[ imath.V2f( *refUVData[i*2 : (i+1)*2] ) for i in range( 126 ) ],
				IECore.GeometricData.Interpretation.UV
			),
			IECore.IntVectorData( refUVIndices )
		)

		self.assertEqual( c["out"].object( "/cube" ), m )


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
