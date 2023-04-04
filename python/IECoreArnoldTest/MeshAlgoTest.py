##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
#  Copyright (c) 2012, Image Engine Design Inc. All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are
#  met:
#
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#
#     * Neither the name of Image Engine Design nor the names of any
#       other contributors to this software may be used to endorse or
#       promote products derived from this software without specific prior
#       written permission.
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

import arnold
import imath

import IECore
import IECoreScene
import IECoreImage
import IECoreArnold

class MeshAlgoTest( unittest.TestCase ) :

	def testUVs( self ) :

		m = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) )
		m["uv"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.FaceVarying, m["uv"].expandedData() )
		uvData = m["uv"].data

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			n = IECoreArnold.NodeAlgo.convert( m, universe, "testMesh" )

			uvs = arnold.AiNodeGetArray( n, "uvlist" )
			self.assertEqual( arnold.AiArrayGetNumElements( uvs.contents ), 4 )

			uvIndices = arnold.AiNodeGetArray( n, "uvidxs" )
			self.assertEqual( arnold.AiArrayGetNumElements( uvIndices.contents ), 4 )

			for i in range( 0, 4 ) :
				p = arnold.AiArrayGetVec2( uvs, i )
				self.assertEqual( arnold.AiArrayGetVec2( uvs, i ), arnold.AtVector2( uvData[i][0], uvData[i][1] ) )
				self.assertEqual( arnold.AiArrayGetInt( uvIndices, i ), i )

	def testIndexedUVs( self ) :

		m = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) )
		uvData = m["uv"].data
		uvIds = m["uv"].indices

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			n = IECoreArnold.NodeAlgo.convert( m, universe, "testMesh" )

			uvs = arnold.AiNodeGetArray( n, "uvlist" )
			self.assertEqual( arnold.AiArrayGetNumElements( uvs.contents ), 4 )

			uvIndices = arnold.AiNodeGetArray( n, "uvidxs" )
			self.assertEqual( arnold.AiArrayGetNumElements( uvIndices.contents ), 4 )

			for i in range( 0, 4 ) :
				aiUv = arnold.AiArrayGetVec2( uvs, i )
				aiUVId = arnold.AiArrayGetInt( uvIndices, i )
				aiIndexedUV = arnold.AiArrayGetVec2( uvs, aiUVId )
				self.assertEqual( aiUVId, uvIds[i] )
				self.assertEqual( aiUv, arnold.AtVector2( uvData[i][0], uvData[i][1] ) )
				self.assertEqual( aiIndexedUV, arnold.AtVector2( uvData[uvIds[i]][0], uvData[uvIds[i]][1] ) )

	def testAdditionalUVs( self ) :

		m = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) )
		m["myMap"] = m["uv"]
		uvData = m["myMap"].data
		indicesData = m["myMap"].indices

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			n = IECoreArnold.NodeAlgo.convert( m, universe, "testMesh" )

			uvs = arnold.AiNodeGetArray( n, "myMap" )
			self.assertEqual( arnold.AiArrayGetNumElements( uvs.contents ), 4 )

			uvIndices = arnold.AiNodeGetArray( n, "myMapidxs" )
			self.assertEqual( arnold.AiArrayGetNumElements( uvIndices.contents ), 4 )

			for i in range( 0, 4 ) :
				p = arnold.AiArrayGetVec2( uvs, i )
				self.assertEqual( arnold.AiArrayGetVec2( uvs, i ), arnold.AtVector2( uvData[i][0], uvData[i][1] ) )
				self.assertEqual( arnold.AiArrayGetInt( uvIndices, i ), indicesData[i] )

	def testNormals( self ) :

		m = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -0.9 ), imath.V2f( 0.9 ) ) )
		m["N"] = IECoreScene.PrimitiveVariable(
				IECoreScene.PrimitiveVariable.Interpolation.Vertex,
				IECore.V3fVectorData( [ imath.V3f( 1, 0, 0 ), imath.V3f( 1, 0, 0 ), imath.V3f( 1, 0, 0 ), imath.V3f( 1, 0, 0 ) ] )
		)

		mFaceVaryingIndexed = IECoreScene.MeshPrimitive.createBox( imath.Box3f( imath.V3f( -0.9 ), imath.V3f( 0.9 ) ) )

		mVertexIndexed = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -0.9 ), imath.V2f( 0.9 ) ), imath.V2i( 3 ) )
		mVertexIndexed["N"] = IECoreScene.PrimitiveVariable(
				IECoreScene.PrimitiveVariable.Interpolation.Vertex,
				IECore.V3fVectorData( [ imath.V3f( 1, 0, 0 ), imath.V3f( -1, 0, 0 ) ] ), IECore.IntVectorData( [0]* 8 + [1]* 8 )
		)

		mNoNormals = m.copy()
		del mNoNormals["N"]

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			n = IECoreArnold.NodeAlgo.convert( m, universe, "testMesh" )
			self.assertTrue( arnold.AiNodeGetBool( n, "smoothing" ) )

			normals = arnold.AiNodeGetArray( n, "nlist" )
			self.assertEqual( arnold.AiArrayGetNumElements( normals.contents ), 4 )

			for i in range( 0, 4 ) :
				self.assertEqual( arnold.AiArrayGetVec( normals, i ), arnold.AtVector( 1, 0, 0 ) )

			n = IECoreArnold.NodeAlgo.convert( mFaceVaryingIndexed, universe, "testMesh2" )
			self.assertTrue( arnold.AiNodeGetBool( n, "smoothing" ) )
			normals = arnold.AiNodeGetArray( n, "nlist" )
			normalIndices = arnold.AiNodeGetArray( n, "nidxs" )

			refNormals = [(0,0,-1), (1,0,0), (0,0,1), (-1,0,0), (0,1,0), (0,-1,0)]
			for i in range( 0, 24 ) :
				self.assertEqual( arnold.AiArrayGetVec( normals, arnold.AiArrayGetInt( normalIndices, i ) ),
					arnold.AtVector( *refNormals[i//4] ) )

			n = IECoreArnold.NodeAlgo.convert( mVertexIndexed, universe, "testMesh3" )
			self.assertTrue( arnold.AiNodeGetBool( n, "smoothing" ) )
			normals = arnold.AiNodeGetArray( n, "nlist" )
			normalIndices = arnold.AiNodeGetArray( n, "nidxs" )
			for i in range( 0, 36 ) :
				s = [0, (i // 2)%2, 1][i // 12]
				self.assertEqual( arnold.AiArrayGetVec( normals, arnold.AiArrayGetInt( normalIndices, i ) ),
					arnold.AtVector( -1 if s else 1, 0, 0 ) )

			n = IECoreArnold.NodeAlgo.convert( mNoNormals, universe, "testMesh4" )
			self.assertFalse( arnold.AiNodeGetBool( n, "smoothing" ) )

	def testVertexPrimitiveVariables( self ) :

		m = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) )
		m["myPrimVar"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.FloatVectorData( [ 0, 1, 2, 3 ] )
		)
		m["myV3fPrimVar"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.V3fVectorData( [ imath.V3f( v ) for v in range( 0, 4 ) ] )
		)

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			n = IECoreArnold.NodeAlgo.convert( m, universe, "testMesh" )
			a = arnold.AiNodeGetArray( n, "myPrimVar" )
			v = arnold.AiNodeGetArray( n, "myV3fPrimVar" )
			self.assertEqual( arnold.AiArrayGetNumElements( a.contents ), 4 )
			for i in range( 0, 4 ) :
				self.assertEqual( arnold.AiArrayGetFlt( a, i ), i )
				self.assertEqual( arnold.AiArrayGetVec( v, i ), i )

	def testFaceVaryingPrimitiveVariables( self ) :

		m = IECoreScene.MeshPrimitive.createPlane(
			imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ),
			imath.V2i( 2 ),
		)
		self.assertEqual( m.variableSize( IECoreScene.PrimitiveVariable.Interpolation.FaceVarying ), 16 )

		m["myPrimVar"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.FaceVarying,
			IECore.FloatVectorData( range( 0, 16 ) )
		)

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			n = IECoreArnold.NodeAlgo.convert( m, universe, "testMesh" )
			a = arnold.AiNodeGetArray( n, "myPrimVar" )
			ia = arnold.AiNodeGetArray( n, "myPrimVaridxs" )
			self.assertEqual( arnold.AiArrayGetNumElements( a.contents ), 16 )
			self.assertEqual( arnold.AiArrayGetNumElements( ia.contents ), 16 )
			for i in range( 0, 16 ) :
				self.assertEqual( arnold.AiArrayGetFlt( a, i ), i )
				self.assertEqual( arnold.AiArrayGetUInt( ia, i ), i )

	def testIndexedFaceVaryingPrimitiveVariables( self ) :

		m = IECoreScene.MeshPrimitive.createPlane(
			imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ),
			imath.V2i( 2, 1 ),
		)
		self.assertEqual( m.variableSize( IECoreScene.PrimitiveVariable.Interpolation.FaceVarying ), 8 )

		m["myPrimVar"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.FaceVarying,
			IECore.FloatVectorData( [ 5, 10 ] ),
			IECore.IntVectorData( [ 0, 0, 0, 0, 1, 1, 1, 1 ] )
		)

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			n = IECoreArnold.NodeAlgo.convert( m, universe, "testMesh" )
			a = arnold.AiNodeGetArray( n, "myPrimVar" )
			ia = arnold.AiNodeGetArray( n, "myPrimVaridxs" )
			self.assertEqual( arnold.AiArrayGetNumElements( a.contents ), 2 )
			self.assertEqual( arnold.AiArrayGetNumElements( ia.contents ), 8 )

			for i in range( 0, len( m["myPrimVar"].data ) ) :
				self.assertEqual( arnold.AiArrayGetFlt( a, i ), m["myPrimVar"].data[i] )

			for i in range( 0, len( m["myPrimVar"].indices ) ) :
				self.assertEqual( arnold.AiArrayGetUInt( ia, i ), m["myPrimVar"].indices[i] )

	def testIndexedUniformPrimitiveVariables( self ) :

		# We expect uniform indexed variables to be expanded out fully
		# when converting to Arnold, because Arnold only supports indexing
		# for FaceVarying variables.

		m = IECoreScene.MeshPrimitive.createPlane(
			imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ),
			imath.V2i( 4, 1 ),
		)
		self.assertEqual( m.variableSize( IECoreScene.PrimitiveVariable.Interpolation.Uniform ), 4 )

		m["myPrimVar"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Uniform,
			IECore.FloatVectorData( [ 5, 10 ] ),
			IECore.IntVectorData( [ 0, 1, 0, 1 ] )
		)

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			n = IECoreArnold.NodeAlgo.convert( m, universe, "testMesh" )

			self.assertEqual( arnold.AiNodeLookUpUserParameter( n, "myPrimVaridxs" ), None )

			a = arnold.AiNodeGetArray( n, "myPrimVar" )
			self.assertEqual( arnold.AiArrayGetNumElements( a.contents ), 4 )

			for i in range( 0, 4 ) :
				self.assertEqual(
					arnold.AiArrayGetFlt( a, i ),
					m["myPrimVar"].data[m["myPrimVar"].indices[i]]
				)

	def testMotion( self ) :

		m1 = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) )
		IECoreScene.MeshNormalsOp()( input = m1, copyInput = False )

		m2 = m1.copy()
		m2["P"].data[0] -= imath.V3f( 0, 0, 1 )
		m2["P"].data[1] -= imath.V3f( 0, 0, 1 )
		IECoreScene.MeshNormalsOp()( input = m2, copyInput = False )

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			node = IECoreArnold.NodeAlgo.convert( [ m1, m2 ], -0.25, 0.25, universe, "testMesh" )

			vList = arnold.AiNodeGetArray( node, "vlist" )
			self.assertEqual( arnold.AiArrayGetNumElements( vList.contents ), 4 )
			self.assertEqual( arnold.AiArrayGetNumKeys( vList.contents ), 2 )

			nList = arnold.AiNodeGetArray( node, "nlist" )
			self.assertEqual( arnold.AiArrayGetNumElements( nList.contents ), 4 )
			self.assertEqual( arnold.AiArrayGetNumKeys( nList.contents ), 2 )

			for i in range( 0, 4 ) :
				p = arnold.AiArrayGetVec( vList, i )
				self.assertEqual( imath.V3f( p.x, p.y, p.z ), m1["P"].data[i] )
				n = arnold.AiArrayGetVec( nList, i )
				self.assertEqual( imath.V3f( n.x, n.y, n.z ), m1["N"].data[i] )

			for i in range( 4, 8 ) :
				p = arnold.AiArrayGetVec( vList, i )
				self.assertEqual( imath.V3f( p.x, p.y, p.z ), m2["P"].data[i-4] )
				n = arnold.AiArrayGetVec( nList, i )
				self.assertEqual( imath.V3f( n.x, n.y, n.z ), m2["N"].data[i-4] )

			self.assertEqual( arnold.AiNodeGetFlt( node, "motion_start" ), -0.25 )
			self.assertEqual( arnold.AiNodeGetFlt( node, "motion_end" ), 0.25 )

	def testClashingPrimitiveVariables( self ) :
		# make sure that names of arnold built-in's can't be used as names for primitive variables
		m = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) )

		m["name"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Uniform,
			IECore.StringData( "CannotRenameMe" )
		)

		expectedMsg = 'Primitive variable "name" will be ignored because it clashes with Arnold\'s built-in parameters'

		with IECoreArnold.UniverseBlock( writable = True ) as universe :
			msg = IECore.CapturingMessageHandler()
			with msg :
				IECoreArnold.NodeAlgo.convert( m, universe, "testMesh" )

			self.assertEqual( len(msg.messages), 1 )
			self.assertEqual( msg.messages[-1].message, expectedMsg )
			self.assertEqual( msg.messages[-1].level, IECore.Msg.Level.Warning )

	def testPointTypePrimitiveVariables( self ) :
		# make sure that we can add prim vars of both vector and point type, and differentiate between the two.
		m = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) )

		points = IECore.V3fVectorData( [] )
		IECore.setGeometricInterpretation( points, IECore.GeometricData.Interpretation.Point )
		m["points"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, points )

		vectors = IECore.V3fVectorData( [] )
		IECore.setGeometricInterpretation( vectors, IECore.GeometricData.Interpretation.Vector )
		m["vectors"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, vectors )

		with IECoreArnold.UniverseBlock( writable = True ) as universe :
			node = IECoreArnold.NodeAlgo.convert( m, universe, "testMesh" )
			p = arnold.AiNodeGetArray( node, "points" )
			self.assertEqual( arnold.AiArrayGetType( p.contents ), arnold.AI_TYPE_VECTOR )

			v = arnold.AiNodeGetArray( node, "vectors" )
			self.assertEqual( arnold.AiArrayGetType( v.contents ), arnold.AI_TYPE_VECTOR )

	def testBoolVectorPrimitiveVariables( self ) :

		m = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) )
		m["myBoolPrimVar"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.BoolVectorData( [ True, False, True, False ] )
		)

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			n = IECoreArnold.NodeAlgo.convert( m, universe, "testMesh" )
			a = arnold.AiNodeGetArray( n, "myBoolPrimVar" )

			self.assertEqual( arnold.AiArrayGetNumElements( a.contents ), 4 )
			self.assertEqual( arnold.AiArrayGetBool( a, 0 ), True )
			self.assertEqual( arnold.AiArrayGetBool( a, 1 ), False )
			self.assertEqual( arnold.AiArrayGetBool( a, 2 ), True )
			self.assertEqual( arnold.AiArrayGetBool( a, 3 ), False )

	def testColor4fVectorDataPrimimitiveVariable( self ) :

		m = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) )
		m["myColor"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.Color4fVectorData( [
				imath.Color4f( 1, 0, 0, 1 ),
				imath.Color4f( 0, 2, 0, 0 ),
				imath.Color4f( 0, 0, 3, 0.25 ),
				imath.Color4f( 4, 0, 0, 1 ),
			] )
		)

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			n = IECoreArnold.NodeAlgo.convert( m, universe, "testMesh" )
			a = arnold.AiNodeGetArray( n, "myColor" )

			self.assertEqual( arnold.AiArrayGetType( a.contents ), arnold.AI_TYPE_RGBA )
			self.assertEqual( arnold.AiArrayGetNumElements( a.contents ), 4 )

			self.assertEqual( arnold.AiArrayGetRGBA( a, 0 ), arnold.AtRGBA( 1, 0, 0, 1 ) )
			self.assertEqual( arnold.AiArrayGetRGBA( a, 1 ), arnold.AtRGBA( 0, 2, 0, 0 ) )
			self.assertEqual( arnold.AiArrayGetRGBA( a, 2 ), arnold.AtRGBA( 0, 0, 3, 0.25 ) )
			self.assertEqual( arnold.AiArrayGetRGBA( a, 3 ), arnold.AtRGBA( 4, 0, 0, 1 ) )

	def testExpandVertexIndexedUVs( self ):

		vertsPerFace = IECore.IntVectorData( [4, 4] )
		vertexIds = IECore.IntVectorData( [0, 1, 4, 3, 1, 2, 5, 4] )
		positions = IECore.V3fVectorData( [ imath.V3f(0,0,0), imath.V3f(1,0,0), imath.V3f(2,0,0), imath.V3f(0,1,0), imath.V3f(1,1,0), imath.V3f(2,1,0)] )

		m = IECoreScene.MeshPrimitive( vertsPerFace, vertexIds, "linear", positions)
		m["uv"] = IECoreScene.PrimitiveVariable(IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.V2fVectorData( [imath.V2f( 0, 0 ), imath.V2f( 1, 0 ), imath.V2f( 0, 1 ), imath.V2f( 1, 1 )], IECore.GeometricData.Interpretation.UV ),
			IECore.IntVectorData( [0, 1, 1, 2, 3, 3] ) )

		self.assertTrue( m.arePrimitiveVariablesValid() )

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			n = IECoreArnold.NodeAlgo.convert( m, universe, "testMesh" )

			uvArray = arnold.AiNodeGetArray( n, "uvlist" )
			self.assertEqual( arnold.AiArrayGetNumElements( uvArray.contents ), 4 )

			self.assertEqual( arnold.AiArrayGetVec2( uvArray, 0 ), arnold.AtVector2( 0, 0 ) )
			self.assertEqual( arnold.AiArrayGetVec2( uvArray, 1 ), arnold.AtVector2( 1, 0 ) )
			self.assertEqual( arnold.AiArrayGetVec2( uvArray, 2 ), arnold.AtVector2( 0, 1 ) )
			self.assertEqual( arnold.AiArrayGetVec2( uvArray, 3 ), arnold.AtVector2( 1, 1 ) )

			uvIndicesArray = arnold.AiNodeGetArray( n, "uvidxs" )
			self.assertEqual( arnold.AiArrayGetNumElements( uvIndicesArray.contents ), 8 )

			self.assertEqual( arnold.AiArrayGetInt( uvIndicesArray, 0 ), 0 )
			self.assertEqual( arnold.AiArrayGetInt( uvIndicesArray, 1 ), 1 )
			self.assertEqual( arnold.AiArrayGetInt( uvIndicesArray, 2 ), 3 )
			self.assertEqual( arnold.AiArrayGetInt( uvIndicesArray, 3 ), 2 )

			self.assertEqual( arnold.AiArrayGetInt( uvIndicesArray, 4 ), 1 )
			self.assertEqual( arnold.AiArrayGetInt( uvIndicesArray, 5 ), 1 )
			self.assertEqual( arnold.AiArrayGetInt( uvIndicesArray, 6 ), 3 )
			self.assertEqual( arnold.AiArrayGetInt( uvIndicesArray, 7 ), 3 )

	def testCornersAndCreases( self ) :

		m = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) )
		m.setInterpolation( "catmullClark" )
		m.setCorners( IECore.IntVectorData( [ 3 ] ), IECore.FloatVectorData( [ 5 ] ) )
		m.setCreases( IECore.IntVectorData( [ 3 ] ), IECore.IntVectorData( [ 0, 1, 2 ] ), IECore.FloatVectorData( [ 6 ] ) )

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			n = IECoreArnold.NodeAlgo.convert( m, universe, "testMesh" )

			idxArray = arnold.AiNodeGetArray( n, "crease_idxs" )
			for i, v in enumerate( [ 0, 1, 1, 2, 3, 3 ] ) :
				self.assertEqual( arnold.AiArrayGetUInt( idxArray, i ), v )

			sharpnessArray = arnold.AiNodeGetArray( n, "crease_sharpness" )
			for i, v in enumerate( [ 6, 6, 5 ] ) :
				self.assertEqual( arnold.AiArrayGetFlt( sharpnessArray, i ), v )

if __name__ == "__main__":
	unittest.main()
