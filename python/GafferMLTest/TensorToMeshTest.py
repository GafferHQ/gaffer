##########################################################################
#
#  Copyright (c) 2024, Lucien Fostier. All rights reserved.
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

import Gaffer
import GafferTest
import GafferScene
import GafferML

class TensorToMeshTest( GafferTest.TestCase ) :
	def testNoInput( self ) :

		node = GafferML.TensorToMesh()
		with self.assertRaisesRegex( Gaffer.ProcessException, "Empty Position tensor" ) :
			node["out"].object("/tensorMesh"),

	def test( self ) :

		points = [ 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 0.0, 2.0 ]
		position = IECore.FloatVectorData( points )
		positionTensor = GafferML.Tensor( position, [ 1, 3, 3 ] )
		vertexIds = IECore.Int64VectorData( [ 0, 1, 2 ]  )
		vertexIdsTensor = GafferML.Tensor( vertexIds, [ 1, 3 ] )
		tensorToMesh = GafferML.TensorToMesh()
		tensorToMesh["position"].setValue( positionTensor )
		tensorToMesh["vertexIds"].setValue( vertexIdsTensor )

		self.assertEqual( tensorToMesh["out"].object( "/" ), IECore.NullObject() )
		self.assertEqual( tensorToMesh["out"].transform( "/" ), imath.M44f() )
		self.assertEqual( tensorToMesh["out"].bound( "/" ), imath.Box3f( imath.V3f( 0 ), imath.V3f( 1, 1, 2 ) ) )
		self.assertEqual( tensorToMesh["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "tensorMesh" ] ) )

		self.assertEqual( tensorToMesh["out"].transform( "/tensorMesh" ), imath.M44f() )
		self.assertEqual( tensorToMesh["out"].bound( "/tensorMesh" ), imath.Box3f( imath.V3f( 0 ), imath.V3f( 1, 1, 2 ) ) )
		self.assertEqual( tensorToMesh["out"].childNames( "/tensorMesh" ), IECore.InternedStringVectorData() )

		mesh = tensorToMesh["out"].object( "/tensorMesh" )
		expectedValue = [component for vec in mesh["P"].data for component in (vec.x, vec.y, vec.z)]

		self.assertEqual( expectedValue, points )
		self.assertEqual( mesh.numFaces(), 1 )
		self.assertEqual( mesh.verticesPerFace, IECore.IntVectorData( [ 3 ] ) )

	def testWrongVertexTensorDimension( self ) :

		points = [ 0.0, 0.0, 0.0 , 1.0, 1.0, 0.0, 1.0, 1.0, 2.0 ]
		position = IECore.FloatVectorData( points )
		positionTensor = GafferML.Tensor( position, [ 3, 3 ] )
		vertexIds = IECore.Int64VectorData( [ 0, 1, 2 ]  )
		vertexIdsTensor = GafferML.Tensor( vertexIds, [ 1, 3 ] )
		tensorToMesh = GafferML.TensorToMesh()
		tensorToMesh["position"].setValue( positionTensor )
		tensorToMesh["vertexIds"].setValue( vertexIdsTensor )

		with self.assertRaisesRegex( Gaffer.ProcessException, "Invalid position tensor number of dimensions" ):
			mesh = tensorToMesh["out"].object( "/tensorMesh" )

	def testWrongVertexDimension( self ) :

		points = [ 0.0, 0.0, 1.0, 1.0, 1.0, 1.0 ]
		position = IECore.FloatVectorData( points )
		positionTensor = GafferML.Tensor( position, [ 1, 3, 2 ] )
		vertexIds = IECore.Int64VectorData( [ 0, 1, 2 ]  )
		vertexIdsTensor = GafferML.Tensor( vertexIds, [ 1, 3 ] )
		tensorToMesh = GafferML.TensorToMesh()
		tensorToMesh["position"].setValue( positionTensor )
		tensorToMesh["vertexIds"].setValue( vertexIdsTensor )

		with self.assertRaisesRegex( Gaffer.ProcessException, "Invalid position dimensions" ):
			mesh = tensorToMesh["out"].object( "/tensorMesh" )

	def testEmptyFaces( self ):
		points = [ 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 0.0, 2.0 ]
		position = IECore.FloatVectorData( points )
		positionTensor = GafferML.Tensor( position, [ 1, 3, 3 ] )
		tensorToMesh = GafferML.TensorToMesh()
		tensorToMesh["position"].setValue( positionTensor )

		with self.assertRaisesRegex( Gaffer.ProcessException, "Empty VertexIds tensor" ):
			mesh = tensorToMesh["out"].object( "/tensorMesh" )

	def testWrongDataTypeVertices( self ):
		points = [ 0, 0, 0, 1, 1, 1, 1, 0, 2 ]
		position = IECore.IntVectorData( points )
		positionTensor = GafferML.Tensor( position, [ 1, 3, 3 ] )
		vertexIds = IECore.Int64VectorData( [ 0, 1, 2 ]  )
		vertexIdsTensor = GafferML.Tensor( vertexIds, [ 1, 3 ] )
		tensorToMesh = GafferML.TensorToMesh()
		tensorToMesh["position"].setValue( positionTensor )
		tensorToMesh["vertexIds"].setValue( vertexIdsTensor )

		with self.assertRaisesRegex( Gaffer.ProcessException, "Invalid data type input for position tensor" ):
			mesh = tensorToMesh["out"].object( "/tensorMesh" )

	def testWrongDataTypeFaces( self ):
		points = [ 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 0.0, 2.0 ]
		position = IECore.FloatVectorData( points )
		positionTensor = GafferML.Tensor( position, [ 1, 3, 3 ] )
		vertexIds = IECore.IntVectorData( [ 0, 1, 2 ]  )
		vertexIdsTensor = GafferML.Tensor( vertexIds, [ 1, 3 ] )
		tensorToMesh = GafferML.TensorToMesh()
		tensorToMesh["position"].setValue( positionTensor )
		tensorToMesh["vertexIds"].setValue( vertexIdsTensor )

		with self.assertRaisesRegex( Gaffer.ProcessException, "Invalid data type input for vertexIds tensor" ):
			mesh = tensorToMesh["out"].object( "/tensorMesh" )

if __name__ == "__main__":
	unittest.main()
