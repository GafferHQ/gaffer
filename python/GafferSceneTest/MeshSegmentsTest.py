##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
#  Copyright (c) 2012-2013, Image Engine Design Inc. All rights reserved.
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

import os
import unittest
import six

import imath

import IECore
import IECoreScene

import Gaffer
import GafferTest
import GafferScene
import GafferSceneTest

class MeshSegmentsTest( GafferSceneTest.SceneTestCase ) :

	def testSampleFile( self ) :

		r = GafferScene.SceneReader()
		r["fileName"].setValue( os.path.join( os.path.dirname( __file__ ), "usdFiles", "segmentTestMesh.usd" ) )

		f = GafferScene.PathFilter()
		f["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		d = GafferScene.DeleteFaces()
		d["in"].setInput( r["out"] )
		d["filter"].setInput( f["out"] )
		d["faces"].setValue( "spiral" )

		s = GafferScene.MeshSegments()
		s["in"].setInput( d["out"] )
		s["filter"].setInput( f["out"] )

		def formatUniform( q, width ):
			return "".join( [ ( ( "%x" % q[i] ) if q[i] >= 0 else " " ) + ( "\n" if i % width == width - 1 else "" ) for i in range( len( q ) ) ] )

		# Expected segmentations for either deleting faces based on the "spiral" primvar and using vertex
		# topology, or using the UVs which have been offset within the spiral.  Note that the UV offset
		# was intentionally chosen so that the corners touch, and segment zero has a small coverage on
		# both corners when segmenting by UVs
		expected = """
00111000000111110000011110011	  000      11111     2222  33	00111222222333334444455556677
01110001111111111110000111001	 000   111111111111    222  3	01112223333333333334444555667
11000011110000001111100011100	00    1111      11111   222  	11222233334444443333344455566
10001111000000000001110001100	0   1111           111   22  	12223333444444444443334445566
00011100001111110000111000110	   111    444444    111   22 	22233344448888884444333444556
00111000111111111110001100111	  111   44444444444   11  222	22333444888888888884443344555
01110011110000001111000110011	 111  4444      4444   11  22	23334488884444448888444334455
01100111000000000011100110001	 11  444          444  11   2	23344888444444444488844334445
11000110001111110001110011001	11   44   111111   444  11  2	33444884443333334448884433445
11001100011111111100110011001	11  44   111111111  44  11  2	33448844433333333344884433445
10011000110000001110011001101	1  44   11      111  44  11 2	34488444334444443334488443345
10011001100001000110011001100	1  44  11    4   11  44  11  	34488443344448444334488443344
10011001100111110110011001100	1  44  11  44444 11  44  11  	34488443344888884334488443344
00110011001100110010011001100	  44  11  44  44  1  44  11  	44884433448844884434488443344
00110011001100000110011001100	  44  11  44     11  44  11  	44884433448844444334488443344
00110011001001100110011001100	  44  11  4  11  11  44  11  	44884433448443344334488443344
00110011001101111100110011001	  44  11  44 11111  44  11  4	44884433448843333344884433448
00110011001100010000110011001	  44  11  44   1    44  11  4	44884433448844434444884433448
10110011001110000001100011001	5 44  11  444      44   11  4	94884433448884444448844433448
10011001100111111111000110011	5  44  11  444444444   11  44	94488443344888888888444334488
10011001110001111110001100011	5  44  111   444444   11   44	94488443334448888884443344488
10001100111000000000011100110	5   44  111          111  44 	9444884433344444444443334488a
11001100011110000001111001110	55  44   1111      1111  444 	9944884443333444444333344888a
11100110001111111111100011100	555  44   11111111111   444  	999448844433333333333444888aa
01100011100001111110000111000	 55   444    111111    444   	b9944488844443333334444888aaa
00110001110000000000011110001	  55   444           4444   6	bb99444888444444444448888aaac
00111000111110000001111000011	  555   44444      4444    66	bb999444888884444448888aaaacc
10011100001111111111110001110	7  555    444444444444   666 	0bb9994444888888888888aaacccd
11001111000001111100000011100	77  5555     44444      666  	00bb99994444488888aaaaaacccdd
"""

		# Test segmenting based on vertex connectivity
		segment = s["out"].object( "/plane" )["segment"].data
		spiral = r["out"].object( "/plane" )["spiral"].expandedData()

		# Format the segment data back onto the original grid, so we can see visually that it is correct
		i = 0
		segmentAsGrid = []
		for j in range( len( spiral ) ):
			if not spiral[j]:
				segmentAsGrid.append( segment[i] )
				i += 1
			else:
				segmentAsGrid.append( -1 )

		self.assertEqual( formatUniform( segmentAsGrid, 29 ).splitlines(), [ i[30:59] for i in expected.splitlines()[1:] ] )

		# Instead of using the name of a vertex primvar, we get the same result by passing no prim var
		s["connectivity"].setValue( "" )
		self.assertEqual( s["out"].object( "/plane" )["segment"].data, segment )


		# Test segmenting based on a face-varying primVar
		s["in"].setInput( r["out"] )
		s["connectivity"].setValue( "uv" )

		segment = s["out"].object( "/plane" )["segment"].data
		self.assertEqual( formatUniform( segment, 29 ).splitlines(), [ i[60:] for i in expected.splitlines()[1:] ] )

		# Test segmenting based on a uniform prim var ( this just uses the prim var's indices as the segments )
		s["connectivity"].setValue( "spiral" )
		segment = s["out"].object( "/plane" )["segment"].data
		self.assertEqual( formatUniform( segment, 29 ).splitlines(), [ i[:29] for i in expected.splitlines()[1:] ] )

	def testInvalid( self ) :

		# Test with a weird and bad mesh to hit a bunch of corner cases

		mesh = IECoreScene.MeshPrimitive( IECore.IntVectorData( [3,3] ), IECore.IntVectorData( [ 0, 1, 2, 3, 4, 5 ] ) )
		mesh["P"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.V3fVectorData(
				[ imath.V3f( 0 ), imath.V3f( 1 ) ],
				IECore.GeometricData.Interpretation.Point
			),
			IECore.IntVectorData( [ 0, 1, 0, 1, 0, 1 ] )
		)
		mesh["uv"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.FaceVarying,
			IECore.V2fVectorData( [ imath.V2f( 0 ) ] * 6 )
		)
		mesh["unindexedUniform"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Uniform,
			IECore.StringVectorData( [ "foo", "foo" ] )
		)
		mesh["const"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Constant,
			IECore.StringVectorData( [ "foo" ] )
		)
		self.assertTrue( mesh.arePrimitiveVariablesValid() )

		o = GafferScene.ObjectToScene()
		o["object"].setValue( mesh )

		f = GafferScene.PathFilter()
		f["paths"].setValue( IECore.StringVectorData( [ "/object" ] ) )

		s = GafferScene.MeshSegments()
		s["in"].setInput( o["out"] )
		s["filter"].setInput( f["out"] )

		with six.assertRaisesRegex( self, RuntimeError, "Vertex primitive variable P has indices.  Indices are not supported on vertex primitive variables." ) :
			s["out"].object( "/object" )

		s["connectivity"].setValue( "doesNotExist" )
		with six.assertRaisesRegex( self, RuntimeError, 'No primitive variable named "doesNotExist"' ) :
			s["out"].object( "/object" )

		s["connectivity"].setValue( "uv" )
		with six.assertRaisesRegex( self, RuntimeError, "FaceVarying primitive variable uv must be indexed in order to use as connectivity." ) :
			s["out"].object( "/object" )

		s["connectivity"].setValue( "unindexedUniform" )
		with six.assertRaisesRegex( self, RuntimeError, "Uniform primitive variable unindexedUniform must be indexed in order to use as connectivity." ) :
			s["out"].object( "/object" )

		# We can segment even this bad mesh by its vertex connectivity specifying no primvar
		s["connectivity"].setValue( "" )
		self.assertEqual( s["out"].object( "/object" )["segment"].data, IECore.IntVectorData( [0, 1] ) )

		# And segmenting by a const primvar always puts everything in one segment
		s["connectivity"].setValue( "const" )
		self.assertEqual( s["out"].object( "/object" )["segment"].data, IECore.IntVectorData( [0, 0] ) )

if __name__ == "__main__":
	unittest.main()
