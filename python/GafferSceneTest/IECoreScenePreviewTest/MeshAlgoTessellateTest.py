##########################################################################
#
#  Copyright (c) 2024, Image Engine Design Inc. All rights reserved.
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
import pathlib

import IECore
import IECoreScene

import Gaffer
import GafferTest

import GafferScene.Private.IECoreScenePreview.MeshAlgo as MeshAlgo

class MeshAlgoTessellateTest( GafferTest.TestCase ) :
	usdFileDir = pathlib.Path( __file__ ).parent.parent / "usdFiles"

	# We begin with a bunch of machinery to support assertMeshesPracticallyEqual.
	# This is a bit overkill for what's actually needed here, but it does seem quite useful in general to be
	# able to compare meshes that have floating point precision differences, or have different vertex or face
	# orders, but are still effectively the same mesh. We haven't decided on a central place for this to live,
	# hopefully we remember it exists next time we need it.
	def reindexPrimvar( self, var, reindex ):
		if var.indices:
			return IECoreScene.PrimitiveVariable( var.interpolation, var.data, IECore.IntVectorData( [ var.indices[i] for i in reindex ] ) )
		else:
			data = type( var.data )( [ var.data[i] for i in reindex ] )
			IECore.setGeometricInterpretation( data, IECore.getGeometricInterpretation( var.data ) )
			return IECoreScene.PrimitiveVariable( var.interpolation, data )

	def reorderVertsToMatch( self, m, ref ):
		tree = IECore.V3fTree( ref["P"].data )

		numVerts = m.variableSize( IECoreScene.PrimitiveVariable.Interpolation.Vertex )

		sortIndices = sorted( range( numVerts ), key = lambda i : tree.nearestNeighbour( m["P"].data[i] ) )

		reverseSort = [-1] * numVerts
		for i in range( len( sortIndices ) ):
			reverseSort[ sortIndices[i] ] = i

		result = IECoreScene.MeshPrimitive( m.verticesPerFace, IECore.IntVectorData( [ reverseSort[i] for i in m.vertexIds ] ), m.interpolation )

		for k in m.keys():
			if m[k].interpolation == IECoreScene.PrimitiveVariable.Interpolation.Vertex:
				result[k] = self.reindexPrimvar( m[k], sortIndices )
			else:
				result[k] = m[k]
		return result

	def canonicalizeFaceOrders( self, m ):
		offset = 0
		vertices = []
		for n in m.verticesPerFace:
			origIndices = range( offset, offset+n )
			ids = [ m.vertexIds[i] for i in origIndices ]
			rotate = ids.index( min( ids ) )
			vertices.append( list( origIndices )[rotate:] + list( origIndices )[:rotate] )
			offset += n

		faceReorder = sorted( range( m.numFaces() ), key = lambda i : [ m.vertexIds[ j ] for j in vertices[i] ] )

		faceVertexReorder = sum( [ vertices[i] for i in faceReorder ], [] )

		result = IECoreScene.MeshPrimitive( IECore.IntVectorData( m.verticesPerFace[i] for i in faceReorder ), IECore.IntVectorData( [ m.vertexIds[i] for i in faceVertexReorder ] ), m.interpolation )

		for k in m.keys():
			if m[k].interpolation == IECoreScene.PrimitiveVariable.Interpolation.FaceVarying:
				result[k] = self.reindexPrimvar( m[k], faceVertexReorder )
			elif m[k].interpolation == IECoreScene.PrimitiveVariable.Interpolation.Uniform:
				result[k] = self.reindexPrimvar( m[k], faceReorder )
			else:
				result[k] = m[k]
		return result

	def betterAssertAlmostEqual( self, a, b, tolerance = 0, msg = "" ):
		if hasattr( a, "min" ):
			# Assume it's a box
			self.betterAssertAlmostEqual( a.min(), b.min(), tolerance, msg )
			self.betterAssertAlmostEqual( a.max(), b.max(), tolerance, msg )
			return
		elif hasattr( a, "v" ):
			# Assume it's a quat
			self.betterAssertAlmostEqual( a.r(), b.r(), tolerance, msg )
			self.betterAssertAlmostEqual( a.v(), b.v(), tolerance, msg )
			return
		elif type( a ) == imath.Color4f:
			# Annoying that imath doesn't have equalWithAbsError on Color4f
			self.betterAssertAlmostEqual( a.r, b.r, tolerance, msg )
			self.betterAssertAlmostEqual( a.g, b.g, tolerance, msg )
			self.betterAssertAlmostEqual( a.b, b.b, tolerance, msg )
			self.betterAssertAlmostEqual( a.a, b.a, tolerance, msg )
			return

		if type( a ) == str:
			match = a == b
		elif hasattr( a, "equalWithAbsError" ):
			match = a.equalWithAbsError( b, tolerance )
		else:
			match = abs( a - b ) <= tolerance

		if not match:
			raise AssertionError( ( msg + " : " if msg else "" ) + "%s != %s" % ( repr( a ), repr( b ) ) )

	def assertPrimvarsPracticallyEqual( self, a, b, name, tolerance = 0 ):
		self.assertEqual( a.interpolation, b.interpolation )
		expandedVarA = a.expandedData()
		expandedVarB = b.expandedData()

		if not hasattr( expandedVarA, "size" ):
			self.betterAssertAlmostEqual( expandedVarA.value, expandedVarB.value, tolerance, "Primvar %s" % name )
			return

		self.assertEqual( len( expandedVarA ), len( expandedVarB ) )

		hasAbsError = hasattr( expandedVarA[0], "equalWithAbsError" )
		for i in range( len( expandedVarA ) ):
			self.betterAssertAlmostEqual(
				expandedVarA[i], expandedVarB[i], tolerance, 'Primvar "%s" element %i' % ( name, i )
			)

	def assertMeshesPracticallyEqual( self, a, b, tolerance = 0 ):
		compareA = self.canonicalizeFaceOrders( a )
		compareB = self.canonicalizeFaceOrders( self.reorderVertsToMatch( b, a ) )

		self.assertPrimvarsPracticallyEqual( compareA["P"], compareB["P"], "P", tolerance )
		self.assertEqual( compareA.verticesPerFace, compareB.verticesPerFace )
		self.assertEqual( compareA.vertexIds, compareB.vertexIds )
		self.assertEqual( compareA.interpolation, compareB.interpolation )

		self.assertEqual( compareA.keys(), compareB.keys() )

		for k in compareA.keys():
			self.assertPrimvarsPracticallyEqual( compareA[k], compareB[k], k, tolerance )

	# Create some test data - this test data is pretty boring - just a grid. But this has the advantage
	# that tessellations of it should end up identical to turning the tessellation rate to this function.
	# We rely on testGeneralMesh which uses a mesh stored in USD to exercise more interesting actual shapes.
	# This is good for testing basic functionality, and weird primvar data types.
	def createTestData( self, tessellationRate, interpolation = "catmullClark", triangular = False ):
		Interp = IECoreScene.PrimitiveVariable.Interpolation

		m = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ), imath.V2i( tessellationRate ) )
		del m["N"]

		if triangular:
			m = IECoreScene.MeshAlgo.triangulate( m )

		m.setInterpolation( interpolation )

		# Create a faceVarying primvar
		faceVarying = IECoreScene.PrimitiveVariable( m["uv"] )
		IECoreScene.MeshAlgo.resamplePrimitiveVariable( m, faceVarying, Interp.FaceVarying )

		m["faceVarying"] = faceVarying

		# Create a uniform variable that just separates the 4 quadrants of the mesh ( this will yield consistent
		# results for any even tessellation rate
		uniformSource = IECoreScene.PrimitiveVariable( m["uv"] )
		IECoreScene.MeshAlgo.resamplePrimitiveVariable( m, uniformSource, Interp.Uniform )
		m["uniform"] = IECoreScene.PrimitiveVariable( Interp.Uniform, IECore.IntVectorData( [ (i[0] > 0.5 ) + 2 * ( i[1] > 0.5 ) for i in uniformSource.data ] ) )

		# Create a bunch of vertex variables to make sure we exercise a lot of data types

		m["color4f"] = IECoreScene.PrimitiveVariable( Interp.Vertex, IECore.Color4fVectorData(
			[ imath.Color4f( uv[0], uv[1], 0.7 * uv[0], 0.7 * uv[1] ) for uv in m["uv"].data ]
		) )

		m["quatd"] = IECoreScene.PrimitiveVariable( Interp.Vertex, IECore.QuatdVectorData(
			[ imath.Quatd( uv[0], uv[1], 0.7 * uv[0], 0.7 * uv[1] ) for uv in m["uv"].data ]
		) )

		m["box3f"] = IECoreScene.PrimitiveVariable( Interp.Vertex, IECore.Box3fVectorData(
			[ imath.Box3f( imath.V3f( uv[0] ), imath.V3f( uv[1] ) ) for uv in m["uv"].data ]
		) )

		m["m33f"] = IECoreScene.PrimitiveVariable( Interp.Vertex, IECore.M33fVectorData(
			[ imath.M33f( *[ (i//3) * uv[0] + (i%3) * 0.7 * uv[1] for i in range( 9 ) ] ) for uv in m["uv"].data ]
		) )

		m["m44f"] = IECoreScene.PrimitiveVariable( Interp.Vertex, IECore.M44fVectorData(
			[ imath.M44f( *[ (i//4) * uv[0] + (i%4) * 0.7 * uv[1] for i in range( 16 ) ] ) for uv in m["uv"].data ]
		) )

		# Interpolating ints is a bit weird, but we should be able to give result rounded to about as correct
		# as we can get.
		m["int"] = IECoreScene.PrimitiveVariable( Interp.Vertex, IECore.IntVectorData(
			[ round( uv[0] * 1000 + uv[1] * 1000000 ) for uv in m["uv"].data ]
		) )

		if triangular:

			uniformSource = IECoreScene.PrimitiveVariable( m["uv"] )
			IECoreScene.MeshAlgo.resamplePrimitiveVariable( m, uniformSource, Interp.Uniform )
			toDelete = IECoreScene.PrimitiveVariable( Interp.Uniform, IECore.IntVectorData( [ i[0] < i[1] for i in uniformSource.data ] ) )
			m = IECoreScene.MeshAlgo.deleteFaces( m, toDelete )

		return m

	def test( self ) :

		# Check that I've fixed a crash on empty meshes
		emptyMesh = IECoreScene.MeshPrimitive( IECore.IntVectorData(), IECore.IntVectorData(), "catmullClark", IECore.V3fVectorData() )
		self.assertEqual( MeshAlgo.tessellateMesh( emptyMesh, 1 ), emptyMesh )


		# Test some basic tessellations
		self.assertMeshesPracticallyEqual(
			MeshAlgo.tessellateMesh( self.createTestData( 2 ), 1 ),
			self.createTestData( 4, "linear" ),
			0.000002
		)

		self.assertMeshesPracticallyEqual(
			MeshAlgo.tessellateMesh( self.createTestData( 2 ), 3 ),
			self.createTestData( 8, "linear" ),
			0.000002
		)

		# Test calculateNormals
		self.assertPrimvarsPracticallyEqual(
			MeshAlgo.tessellateMesh( self.createTestData( 2 ), 1, calculateNormals = True )["N"],
			IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, IECore.V3fVectorData( [ imath.V3f( 0,0,1 ) ] * 25 ) ),
			"N", 0.000001
		)

		# We can also just interpolate the normals from upstream
		sourceWithNormal = self.createTestData( 2 )
		sourceWithNormal["N"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, IECore.V3fVectorData( [ imath.V3f( 1,0,0 ) ] * 9 ) )
		self.assertPrimvarsPracticallyEqual(
			MeshAlgo.tessellateMesh( sourceWithNormal, 1 )["N"],
			IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, IECore.V3fVectorData( [ imath.V3f( 1,0,0 ) ] * 25 ) ),
			"N", 0.000001
		)
		# But setting calculateNormals will still override them
		self.assertPrimvarsPracticallyEqual(
			MeshAlgo.tessellateMesh( sourceWithNormal, 1, calculateNormals = True )["N"],
			IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, IECore.V3fVectorData( [ imath.V3f( 0,0,1 ) ] * 25 ) ),
			"N", 0.000001
		)

		# Test some invalid primitive variables

		sourceWithInvalid = self.createTestData( 2 )
		sourceWithInvalid["string"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, IECore.StringVectorData( [ "hello" ] * 9 ) )
		# Interpolating strings doesn't make sense - we currently just output empty strings
		self.assertEqual( MeshAlgo.tessellateMesh( sourceWithInvalid, 1 )["string"].data, IECore.StringVectorData( [ "" ] * 25 ) )
		sourceWithInvalid["invalid"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, IECore.FloatVectorData( [ 5 ] * 7 ) )
		with self.assertRaisesRegex( RuntimeError, 'Cannot tessellate invalid primvar: "invalid"' ):
			MeshAlgo.tessellateMesh( sourceWithInvalid, 1 )

		sourceWithInvalid["invalid"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, IECore.FloatData( 5 ) )
		with self.assertRaisesRegex( RuntimeError, 'Cannot tessellate invalid primvar: "invalid"' ):
			MeshAlgo.tessellateMesh( sourceWithInvalid, 1 )
		del sourceWithInvalid["invalid"]
		del sourceWithInvalid["P"]
		with self.assertRaisesRegex( RuntimeError, 'Mesh must have V3f P primvar.' ):
			MeshAlgo.tessellateMesh( sourceWithInvalid, 1 )
		sourceWithInvalid["P"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, IECore.FloatVectorData( [ 5 ] * 9 ) )
		with self.assertRaisesRegex( RuntimeError, 'Mesh must have V3f P primvar.' ):
			MeshAlgo.tessellateMesh( sourceWithInvalid, 1 )
		sourceWithInvalid["P"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, IECore.V3fVectorData( [ imath.V3f() ] * 7 ) )
		with self.assertRaisesRegex( RuntimeError, 'P primvar is invalid.' ):
			MeshAlgo.tessellateMesh( sourceWithInvalid, 1 )

		# Test that we output correct vertex counts when OpenSubdiv outputs degenerate "quads" with one vertex
		# set to -1 ( happens on odd tessellations of irregular faces )
		self.assertEqual(
			list( MeshAlgo.tessellateMesh( self.createTestData( 2, triangular = True ), 2 ).verticesPerFace ),
			[ 4, 4, 4, 4, 4, 4, 3 ] * 4
		)

		# Test meshes with linear interpolation
		self.assertMeshesPracticallyEqual(
			MeshAlgo.tessellateMesh( self.createTestData( 2, "linear" ), 1 ),
			self.createTestData( 4, "linear" ),
			0.000002
		)

		# Basic tests for Loop subdivision

		with self.assertRaisesRegex( RuntimeError, "Loop subdivision can only be applied to triangle meshes" ):
			MeshAlgo.tessellateMesh( self.createTestData( 2, "linear" ), 1, scheme = MeshAlgo.SubdivisionScheme.Loop ),

		self.assertMeshesPracticallyEqual(
			MeshAlgo.tessellateMesh( self.createTestData( 2, "catmullClark", triangular = True ), 1, scheme = MeshAlgo.SubdivisionScheme.Loop ),
			self.createTestData( 4, "linear", triangular = True ),
			0.000002
		)

		# We can also use Loop subdivision by specifying it as the interpolation on the mesh, though we don't
		# currently provide a way to author this
		self.assertMeshesPracticallyEqual(
			MeshAlgo.tessellateMesh( self.createTestData( 2, "loop", triangular = True ), 1 ),
			self.createTestData( 4, "linear", triangular = True ),
			0.000002
		)

	def testGeneralMesh( self ) :

		# Test with a sample mesh that actually exercises some interesting shapes, and irregular faces.

		file = IECoreScene.SceneInterface.create(
			str( self.usdFileDir / "generalTestMesh.usd" ), IECore.IndexedIO.OpenMode.Read
		)
		source = file.child( "object" ).readObject( 0.0 )

		referenceFile = IECoreScene.SceneInterface.create(
			str( self.usdFileDir / "generalTestMeshTessellated.usd" ), IECore.IndexedIO.OpenMode.Read
		)
		reference = referenceFile.child( "object" ).readObject( 0.0 )

		catmarkRate2 = MeshAlgo.tessellateMesh( source, 1, calculateNormals = True )
		self.assertEqual( catmarkRate2, reference )
		self.assertEqual( catmarkRate2.verticesPerFace, IECore.IntVectorData( [ 4 ] * 804  ) )

		# For this fairly general mesh, it's hard to test a lot of specifics about high tessellation rates without
		# storing a lot of reference data, but we can at least check that the primitive variables are valid,
		# and the number of triangles is 48 for odd tessellation rates ( 1 for each triangular face in the
		# original mesh, plus N for each N-gon ), and 0 for even tessellation rates.

		catmarkRate3 = MeshAlgo.tessellateMesh( source, 2, calculateNormals = True )
		self.assertTrue( catmarkRate3.arePrimitiveVariablesValid() )
		self.assertEqual( sorted( list(	catmarkRate3.verticesPerFace ) ), [ 3 ] * 48 + [ 4 ] * 1779  )

		catmarkRate6 = MeshAlgo.tessellateMesh( source, 5, calculateNormals = True )
		self.assertTrue( catmarkRate6.arePrimitiveVariablesValid() )
		self.assertEqual( catmarkRate6.verticesPerFace, IECore.IntVectorData( [ 4 ] * 7236  ) )

		catmarkRate9 = MeshAlgo.tessellateMesh( source, 8, calculateNormals = True )
		self.assertTrue( catmarkRate9.arePrimitiveVariablesValid() )
		self.assertEqual( sorted( list( catmarkRate9.verticesPerFace ) ), [ 3 ] * 48 + [ 4 ] * 16251  )

		# We can also validate that if we use a linear scheme, then a high tessellation rate can be matched
		# by repeated tessellation at lower rates ( as long as the first tessllation is at an even rate,
		# odd tessellation rates introduce triangles that don't end up in exactly the same place during
		# subsequent retessellations )

		linearRate6 = MeshAlgo.tessellateMesh( source, 5, scheme = MeshAlgo.SubdivisionScheme.Bilinear, calculateNormals = True )

		self.assertNotEqual( linearRate6, catmarkRate6 )

		linearRate2 = MeshAlgo.tessellateMesh( source, 1, scheme = MeshAlgo.SubdivisionScheme.Bilinear, calculateNormals = True )
		linearRate2x3 = MeshAlgo.tessellateMesh( linearRate2, 2, scheme = MeshAlgo.SubdivisionScheme.Bilinear, calculateNormals = True )

		self.assertMeshesPracticallyEqual( linearRate6, linearRate2x3, 0.00001 )

		# Check that we can also use a linear scheme by setting the mesh type

		source.setInterpolation( "linear" )
		self.assertEqual( MeshAlgo.tessellateMesh( source, 5, calculateNormals = True ), linearRate6 )

		# And test that we can override the scheme to CatmullClark
		self.assertEqual( MeshAlgo.tessellateMesh( source, 5, scheme = MeshAlgo.SubdivisionScheme.CatmullClark, calculateNormals = True ), catmarkRate6 )

	# Turn a mesh into a doubled up mesh, with copies of all vertices and faces shifted in P
	def duplicateMesh( self, m ) :
		numVerts = len( m["P"].data )
		result = IECoreScene.MeshPrimitive(
			IECore.IntVectorData( list( m.verticesPerFace ) * 2 ),
			IECore.IntVectorData( list( m.vertexIds ) + [ i + numVerts for i in m.vertexIds ] ),
			m.interpolation,
			IECore.V3fVectorData( list( m["P"].data ) + [ i + imath.V3f( 10 ) for i in m["P"].data ] )
		)

		result.setCreases(
			IECore.IntVectorData( list( m.creaseLengths() ) * 2 ),
			IECore.IntVectorData( list( m.creaseIds() ) + [ i + numVerts for i in m.creaseIds() ] ),
			IECore.FloatVectorData( list( m.creaseSharpnesses() ) * 2 )
		)
		result.setCorners(
			IECore.IntVectorData( list( m.cornerIds() ) + [ i + numVerts for i in m.cornerIds() ] ),
			IECore.FloatVectorData( list( m.cornerSharpnesses() ) * 2 )
		)

		for k in m.keys():
			if k == "P":
				continue
			if m[k].interpolation == IECoreScene.PrimitiveVariable.Interpolation.Constant:
				result[k] = m[k]
			elif m[k].indices:
				result[k] = IECoreScene.PrimitiveVariable(
					m[k].interpolation, m[k].data, IECore.IntVectorData( list( m[k].indices ) * 2 )
				)
			else:
				result[k] = IECoreScene.PrimitiveVariable(
					m[k].interpolation, type( m[k].data )( list( m[k].data ) * 2 )
				)

		return result

	# Test facevarying variables with indices reused across completely unrelated vertices
	def testSharedFacevarying( self ) :

		# We can get this kind of troublesome sharing by duplicating our whole test mesh,
		# reusing the facevarying indices ( so the copy will have the same indices as the original )

		file = IECoreScene.SceneInterface.create(
			str( self.usdFileDir / "generalTestMesh.usd" ), IECore.IndexedIO.OpenMode.Read
		)
		source = file.child( "object" ).readObject( 0.0 )

		sourceDuped = self.duplicateMesh( source )

		tessellated = MeshAlgo.tessellateMesh( source, 2, calculateNormals = True )
		dupedTessellated = MeshAlgo.tessellateMesh( sourceDuped, 2, calculateNormals = True )

		# The copy should be tessellated with results that are identical to the original
		self.assertMeshesPracticallyEqual( dupedTessellated, self.duplicateMesh( tessellated ), 0.001 )

		# assertMeshesPraticallyEqual confirms our values all end up correct, but doesn't check how the
		# indices are shared - we can check this manually by confirming that uv indices for the
		# tessellated copy end up the same as the indices for the tessellated original, just all shifted
		# by a constant offset, ensuring they end up indepedent.
		uvSize = len( tessellated["uv"].data )
		self.assertEqual(
			list( dupedTessellated["uv"].indices ),
			list( tessellated["uv"].indices ) + [ i + uvSize for i in tessellated["uv"].indices ]
		)

	def testNonManifold( self ) :
		# We don't care too much about results on non-manifold meshes, but we can make sure that a bunch
		# of weird cases do something reasonable and don't crash.

		nonManifoldFile = IECoreScene.SceneInterface.create(
			str( self.usdFileDir / "nonManifold.usd" ), IECore.IndexedIO.OpenMode.Read
		)
		nonManifold = nonManifoldFile.child( "object" ).readObject( 0.0 )

		referenceFile = IECoreScene.SceneInterface.create(
			str( self.usdFileDir / "nonManifoldTessellated.usd" ), IECore.IndexedIO.OpenMode.Read
		)
		reference = referenceFile.child( "object" ).readObject( 0.0 )
		self.assertEqual( MeshAlgo.tessellateMesh( nonManifold, 2, calculateNormals = True ), reference )

		# Hard to define correct results on this weird data without using reference data, but we can
		# at least run a couple higher tessellations to make sure we don't crash or something.
		MeshAlgo.tessellateMesh( nonManifold, 3, calculateNormals = True )
		MeshAlgo.tessellateMesh( nonManifold, 4 )

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testSmallSourcePerf( self ):

		sphere = IECoreScene.MeshPrimitive.createSphere(
			1, divisions = imath.V2i( 100 )
		)

		sphere.setInterpolation( "catmullClark" )
		del sphere["N"]

		with GafferTest.TestRunner.PerformanceScope() :
			MeshAlgo.tessellateMesh( sphere, 7 )

	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 1)
	def testBigSourcePerfIrregular( self ):

		sphere = IECoreScene.MeshPrimitive.createSphere(
			1, divisions = imath.V2i( 300 )
		)

		sphere.setInterpolation( "catmullClark" )
		del sphere["N"]

		with GafferTest.TestRunner.PerformanceScope() :
			MeshAlgo.tessellateMesh( sphere, 1 )

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testBigSourcePerfRegular( self ):

		# OpenSubdiv really doesn't like the poles on our sphere primitive. Clipping them off
		# results in much faster times.
		sphere = IECoreScene.MeshPrimitive.createSphere(
			1, divisions = imath.V2i( 300 ), zMin = -0.9999999, zMax = 0.9999999
		)

		sphere.setInterpolation( "catmullClark" )
		del sphere["N"]

		with GafferTest.TestRunner.PerformanceScope() :
			MeshAlgo.tessellateMesh( sphere, 1 )

if __name__ == "__main__":
	unittest.main()
