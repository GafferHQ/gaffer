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

import GafferScene
import GafferScene.Private.IECoreScenePreview.MeshAlgo as MeshAlgo
import GafferSceneTest

class MeshTessellateTest( GafferSceneTest.SceneTestCase ) :

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

	def canonicizeFaceOrders( self, m ):
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
		compareA = self.canonicizeFaceOrders( a )
		compareB = self.canonicizeFaceOrders( self.reorderVertsToMatch( b, a ) )

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

		objectToScene = GafferScene.ObjectToScene()

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ '/object' ] ) )

		tessellate = GafferScene.MeshTessellate()
		tessellate["in"].setInput( objectToScene["out"] )
		tessellate["filter"].setInput( filter["out"] )

		# Check that I've fixed a crash on empty meshes
		emptyMesh = IECoreScene.MeshPrimitive( IECore.IntVectorData(), IECore.IntVectorData(), "catmullClark", IECore.V3fVectorData() )
		objectToScene["object"].setValue( emptyMesh )
		self.assertEqual( tessellate["out"].object( "object" ), emptyMesh )


		# Test some basic tessellations
		objectToScene["object"].setValue( self.createTestData( 2 ) )
		tessellate["divisions"].setValue( 1 )
		self.assertMeshesPracticallyEqual( tessellate["out"].object( "object" ), self.createTestData( 4, "linear" ), 0.000002 )

		tessellate["divisions"].setValue( 3 )
		self.assertMeshesPracticallyEqual( tessellate["out"].object( "object" ), self.createTestData( 8, "linear" ), 0.000002 )

		tessellate["divisions"].setValue( 1 )

		# Test calculateNormals
		tessellate["calculateNormals"].setValue( True )
		self.assertPrimvarsPracticallyEqual(
			tessellate["out"].object( "object" )["N"],
			IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, IECore.V3fVectorData( [ imath.V3f( 0,0,1 ) ] * 25 ) ),
			"N", 0.000001
		)

		# We can also just interpolate the normals from upstream
		tessellate["calculateNormals"].setValue( False )
		sourceWithNormal = self.createTestData( 2 )
		sourceWithNormal["N"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, IECore.V3fVectorData( [ imath.V3f( 1,0,0 ) ] * 9 ) )
		objectToScene["object"].setValue( sourceWithNormal )
		self.assertPrimvarsPracticallyEqual(
			tessellate["out"].object( "object" )["N"],
			IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, IECore.V3fVectorData( [ imath.V3f( 1,0,0 ) ] * 25 ) ),
			"N", 0.000001
		)
		# But setting calculateNormals will still override them
		tessellate["calculateNormals"].setValue( True )
		self.assertPrimvarsPracticallyEqual(
			tessellate["out"].object( "object" )["N"],
			IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, IECore.V3fVectorData( [ imath.V3f( 0,0,1 ) ] * 25 ) ),
			"N", 0.000001
		)
		tessellate["calculateNormals"].setValue( False )

		# Test some invalid primitive variables

		sourceWithInvalid = self.createTestData( 2 )
		sourceWithInvalid["string"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, IECore.StringVectorData( [ "hello" ] * 9 ) )
		objectToScene["object"].setValue( sourceWithInvalid )
		# Interpolating strings doesn't make sense - we currently just output empty strings
		self.assertEqual( tessellate["out"].object( "object" )["string"].data, IECore.StringVectorData( [ "" ] * 25 ) )
		sourceWithInvalid["invalid"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, IECore.FloatVectorData( [ 5 ] * 7 ) )
		objectToScene["object"].setValue( sourceWithInvalid )
		with self.assertRaisesRegex( RuntimeError, 'Cannot tessellate invalid primvar: "invalid"' ):
			tessellate["out"].object( "object" )
		sourceWithInvalid["invalid"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, IECore.FloatData( 5 ) )
		objectToScene["object"].setValue( sourceWithInvalid )
		with self.assertRaisesRegex( RuntimeError, 'Cannot tessellate invalid primvar: "invalid"' ):
			tessellate["out"].object( "object" )
		del sourceWithInvalid["invalid"]
		del sourceWithInvalid["P"]
		objectToScene["object"].setValue( sourceWithInvalid )
		with self.assertRaisesRegex( RuntimeError, 'Mesh must have V3f P primvar.' ):
			tessellate["out"].object( "object" )
		sourceWithInvalid["P"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, IECore.FloatVectorData( [ 5 ] * 9 ) )
		objectToScene["object"].setValue( sourceWithInvalid )
		with self.assertRaisesRegex( RuntimeError, 'Mesh must have V3f P primvar.' ):
			tessellate["out"].object( "object" )
		sourceWithInvalid["P"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, IECore.V3fVectorData( [ imath.V3f() ] * 7 ) )
		objectToScene["object"].setValue( sourceWithInvalid )
		with self.assertRaisesRegex( RuntimeError, 'P primvar is invalid.' ):
			print( tessellate["out"].object( "object" )["P"] )

		# Test meshes with linear interpolation
		objectToScene["object"].setValue( self.createTestData( 2, "linear" ) )
		# By default, we don't tessellate them
		self.assertEqual( tessellate["out"].object( "object" ), self.createTestData( 2, "linear" ) )
		# But we can force it by setting tessellatePolygons
		tessellate["tessellatePolygons"].setValue( True )
		self.assertMeshesPracticallyEqual( tessellate["out"].object( "object" ), self.createTestData( 4, "linear" ), 0.000002 )

		# Basic tests for Loop subdivision

		objectToScene["object"].setValue( self.createTestData( 2 ) )

		tessellate["scheme"].setValue( MeshAlgo.SubdivisionScheme.Loop )

		with self.assertRaisesRegex( RuntimeError, "Loop subdivision can only be applied to triangle meshes" ):
			tessellate["out"].object( "object" )

		objectToScene["object"].setValue( self.createTestData( 2, "catmullClark", triangular = True ) )
		self.assertMeshesPracticallyEqual( tessellate["out"].object( "object" ), self.createTestData( 4, "linear", triangular = True ), 0.000002 )

		# We can also use Loop subdivision by specifying it as the interpolation on the mesh, though we don't
		# currently provide a way to author this
		tessellate["scheme"].setValue( MeshAlgo.SubdivisionScheme.Default )
		objectToScene["object"].setValue( self.createTestData( 2, "loop", triangular = True ) )
		self.assertMeshesPracticallyEqual( tessellate["out"].object( "object" ), self.createTestData( 4, "linear", triangular = True ), 0.000002 )

	def testGeneralMesh( self ) :

		# Test with a sample mesh that actually exercises some interesting shapes, and irregular faces.

		testReader = GafferScene.SceneReader()
		testReader["fileName"].setValue( pathlib.Path( __file__ ).parent / "usdFiles" / "generalTestMesh.usd" )

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ '/object' ] ) )

		tessellate = GafferScene.MeshTessellate()
		tessellate["in"].setInput( testReader["out"] )
		tessellate["filter"].setInput( filter["out"] )
		tessellate["calculateNormals"].setValue( True )
		tessellate["divisions"].setValue( 1 )

		referenceReader = GafferScene.SceneReader()
		referenceReader["fileName"].setValue( pathlib.Path( __file__ ).parent / "usdFiles" / "generalTestMeshTessellated.usd" )
		self.assertScenesEqual( tessellate["out"], referenceReader["out"] )

		self.assertMeshesPracticallyEqual( tessellate["out"].object( "object" ), referenceReader["out"].object( "object" ) )
		self.assertEqual( tessellate["out"].object( "object" ).verticesPerFace, IECore.IntVectorData( [ 4 ] * 804  ) )

		# For this fairly general mesh, it's hard to test a lot of specifics about high tessellation rates without
		# storing a lot of reference data, but we can at least check that the primitive variables are valid,
		# and the number of triangles is 48 for odd tessellation rates ( 1 for each triangular face in the
		# original mesh, plus N for each N-gon ), and 0 for even tessellation rates.

		tessellate["divisions"].setValue( 2 )
		catmarkRate3 = tessellate["out"].object( "object" )
		self.assertTrue( catmarkRate3.arePrimitiveVariablesValid() )
		self.assertEqual( sorted( list(	catmarkRate3.verticesPerFace ) ), [ 3 ] * 48 + [ 4 ] * 1779  )

		tessellate["divisions"].setValue( 5 )
		catmarkRate6 = tessellate["out"].object( "object" )
		self.assertTrue( catmarkRate6.arePrimitiveVariablesValid() )
		self.assertEqual( catmarkRate6.verticesPerFace, IECore.IntVectorData( [ 4 ] * 7236  ) )

		tessellate["divisions"].setValue( 8 )
		catmarkRate9 = tessellate["out"].object( "object" )
		self.assertTrue( catmarkRate9.arePrimitiveVariablesValid() )
		self.assertEqual( sorted( list( catmarkRate9.verticesPerFace ) ), [ 3 ] * 48 + [ 4 ] * 16251  )

		# We can also validate that if we use a linear scheme, then a high tessellation rate can be matched
		# by repeated tessellation at lower rates ( as long as the first tessllation is at an even rate,
		# odd tessellation rates introduce triangles that don't end up in exactly the same place during
		# subsequent retessellations )

		tessellate["scheme"].setValue( MeshAlgo.SubdivisionScheme.Bilinear )
		tessellate["divisions"].setValue( 5 )
		linearRate6 = tessellate["out"].object( "object" )

		self.assertNotEqual( linearRate6, catmarkRate6 )

		tessellate["divisions"].setValue( 1 )

		retessellate = GafferScene.MeshTessellate()
		retessellate["in"].setInput( tessellate["out"] )
		retessellate["filter"].setInput( filter["out"] )
		retessellate["tessellatePolygons"].setValue( True )
		retessellate["calculateNormals"].setValue( True )
		retessellate["scheme"].setValue( MeshAlgo.SubdivisionScheme.Bilinear )
		retessellate["divisions"].setValue( 2 )

		retessellate2x3 = retessellate["out"].object( "object" )

		self.assertMeshesPracticallyEqual( linearRate6, retessellate2x3, 0.00001 )

		# Check that we can also use a linear scheme by setting the mesh type

		meshType = GafferScene.MeshType()
		meshType["in"].setInput( testReader["out"] )
		meshType["filter"].setInput( filter["out"] )
		meshType["meshType"].setValue( "linear" )

		tessellate["in"].setInput( meshType["out"] )
		tessellate["scheme"].setValue( MeshAlgo.SubdivisionScheme.Default )
		tessellate["tessellatePolygons"].setValue( True )
		tessellate["divisions"].setValue( 5 )
		self.assertEqual( tessellate["out"].object( "object" ), linearRate6 )

		# And test that we can override the scheme to CatmullClark
		tessellate["scheme"].setValue( MeshAlgo.SubdivisionScheme.CatmullClark )
		self.assertEqual( tessellate["out"].object( "object" ), catmarkRate6 )

	def testNonManifold( self ) :
		# We don't care too much about results on non-manifold meshes, but we can make sure that a bunch
		# of weird cases do something reasonable and don't crash.

		testReader = GafferScene.SceneReader()
		testReader["fileName"].setValue( pathlib.Path( __file__ ).parent / "usdFiles" / "nonManifold.usd" )

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ '/object' ] ) )

		tessellate = GafferScene.MeshTessellate()
		tessellate["in"].setInput( testReader["out"] )
		tessellate["filter"].setInput( filter["out"] )
		tessellate["calculateNormals"].setValue( True )
		tessellate["divisions"].setValue( 2 )

		referenceReader = GafferScene.SceneReader()
		referenceReader["fileName"].setValue( pathlib.Path( __file__ ).parent / "usdFiles" / "nonManifoldTessellated.usd" )
		self.assertScenesEqual( tessellate["out"], referenceReader["out"] )

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testSmallSourcePerf( self ):

		sphere = GafferScene.Sphere()
		sphere["divisions"].setValue( imath.V2i( 100, 100 ) )

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ '/sphere' ] ) )

		meshType = GafferScene.MeshType()
		meshType["in"].setInput( sphere["out"] )
		meshType["filter"].setInput( filter["out"] )
		meshType["meshType"].setValue( 'catmullClark' )

		tessellate = GafferScene.MeshTessellate()
		tessellate["in"].setInput( meshType["out"] )
		tessellate["filter"].setInput( filter["out"] )
		tessellate["tessellatePolygons"].setValue( True )
		tessellate["divisions"].setValue( 7 )

		tessellate["in"].object( "/sphere" )

		with GafferTest.TestRunner.PerformanceScope() :
			tessellate["out"].object( "/sphere" )

	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 1)
	def testBigSourcePerfIrregular( self ):

		sphere = GafferScene.Sphere()
		sphere["divisions"].setValue( imath.V2i( 300, 300 ) )

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ '/sphere' ] ) )

		meshType = GafferScene.MeshType()
		meshType["in"].setInput( sphere["out"] )
		meshType["filter"].setInput( filter["out"] )
		meshType["meshType"].setValue( 'catmullClark' )

		tessellate = GafferScene.MeshTessellate()
		tessellate["in"].setInput( meshType["out"] )
		tessellate["filter"].setInput( filter["out"] )
		tessellate["tessellatePolygons"].setValue( True )
		tessellate["divisions"].setValue( 1 )

		tessellate["in"].object( "/sphere" )

		with GafferTest.TestRunner.PerformanceScope() :
			tessellate["out"].object( "/sphere" )

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testBigSourcePerfRegular( self ):

		# OpenSubdiv really doesn't like the poles on our sphere primitive. Clipping them off
		# results in much faster times.

		sphere = GafferScene.Sphere()
		sphere["divisions"].setValue( imath.V2i( 300, 300 ) )
		sphere["zMin"].setValue( -0.9999999 )
		sphere["zMax"].setValue( 0.9999999 )

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ '/sphere' ] ) )

		meshType = GafferScene.MeshType()
		meshType["in"].setInput( sphere["out"] )
		meshType["filter"].setInput( filter["out"] )
		meshType["meshType"].setValue( 'catmullClark' )

		tessellate = GafferScene.MeshTessellate()
		tessellate["in"].setInput( meshType["out"] )
		tessellate["filter"].setInput( filter["out"] )
		tessellate["tessellatePolygons"].setValue( True )
		tessellate["divisions"].setValue( 1 )

		tessellate["in"].object( "/sphere" )

		with GafferTest.TestRunner.PerformanceScope() :
			tessellate["out"].object( "/sphere" )

if __name__ == "__main__":
	unittest.main()
