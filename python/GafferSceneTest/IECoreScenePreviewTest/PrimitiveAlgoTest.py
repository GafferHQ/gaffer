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
import itertools
import math
import pathlib
import random
import threading
import time

import IECore
import IECoreScene

import Gaffer
import GafferTest

# Because we haven't yet figured out where else assertMeshesPraticallyEqual should live
import GafferSceneTest.IECoreScenePreviewTest.MeshAlgoTessellateTest

import GafferScene.Private.IECoreScenePreview.PrimitiveAlgo as PrimitiveAlgo
Interpolation = IECoreScene.PrimitiveVariable.Interpolation

class PrimitiveAlgoTest( GafferTest.TestCase ) :
	usdFileDir = pathlib.Path( __file__ ).parent.parent / "usdFiles"

	def resamplePrimVars( self, prim, primVars, interp ):
		for pv in primVars:
			resampled = prim[pv]
			if type( prim ) == IECoreScene.MeshPrimitive:
				IECoreScene.MeshAlgo.resamplePrimitiveVariable( prim, resampled, interp )
			elif type( prim ) == IECoreScene.CurvesPrimitive:
				IECoreScene.CurvesAlgo.resamplePrimitiveVariable( prim, resampled, interp )
				self.assertTrue( prim.isPrimitiveVariableValid( resampled ) )
			elif type( prim ) == IECoreScene.PointsPrimitive:
				IECoreScene.PointsAlgo.resamplePrimitiveVariable( prim, resampled, interp )
			prim[pv] = resampled

	def interpolationMatches( self, prim, a, b ):
		if a == b:
			return True

		# Some interpolations are effectively the same, depending on the primitive type
		if type( prim ) == IECoreScene.MeshPrimitive:
			isVertex = { Interpolation.Vertex, Interpolation.Varying }
			return a in isVertex and b in isVertex
		elif type( prim ) == IECoreScene.CurvesPrimitive:
			isVarying = { Interpolation.Varying, Interpolation.FaceVarying }
			return a in isVarying and b in isVarying
		elif type( prim ) == IECoreScene.PointsPrimitive:
			isVertex = { Interpolation.Vertex, Interpolation.Varying, Interpolation.FaceVarying }
			return a in isVertex and b in isVertex

	def testTransformPrimitive( self ):
		prim = IECoreScene.MeshPrimitive.createBox( imath.Box3f( imath.V3f( -1 ), imath.V3f( 1 ) ) )
		vectorData = prim["P"].data.copy()
		vectorData.setInterpretation( IECore.GeometricData.Interpretation.Vector )
		prim["vectorTest"] = IECoreScene.PrimitiveVariable( Interpolation.Vertex, vectorData )
		numericData = prim["P"].data.copy()
		numericData.setInterpretation( IECore.GeometricData.Interpretation.None_ )
		prim["numericTest"] = IECoreScene.PrimitiveVariable( Interpolation.Vertex, numericData )
		prim["constantVectorTest"] = IECoreScene.PrimitiveVariable(
			Interpolation.Constant, IECore.V3fData( imath.V3f( 1, 0, 0 ), IECore.GeometricData.Interpretation.Point )
		)

		m = imath.M44f()
		m.translate( imath.V3f( 10, 1, 0 ) )
		m.scale( imath.V3f( 0.5, 1, 1 ) )
		m.rotate( imath.V3f( 0, math.radians( 45 ), 0 ) )

		result = prim.copy()
		PrimitiveAlgo.transformPrimitive( result, m )

		sq = math.sqrt( 2.0 )
		rotated = [ imath.V3f( *i ) for i in [ ( -sq, -1, 0 ), ( 0, -1, -sq ), ( 0, 1, -sq ), ( -sq, 1, 0 ), ( sq, -1, 0 ), ( sq, 1, 0 ), ( 0, -1, sq ), ( 0, 1, sq ) ] ]
		squashed = [ imath.V3f( 0.5, 1, 1 ) * i for i in rotated ]
		self.assertEqual(
			result["P"],
			IECoreScene.PrimitiveVariable(
				Interpolation.Vertex,
				IECore.V3fVectorData( [ imath.V3f( 10,1,0 ) + i for i in squashed ], IECore.GeometricData.Interpretation.Point )
			)
		)
		self.assertEqual(
			result["vectorTest"],
			IECoreScene.PrimitiveVariable(
				Interpolation.Vertex,
				IECore.V3fVectorData( squashed, IECore.GeometricData.Interpretation.Vector )
			)
		)
		normals = [ imath.V3f( *i ) for i in [ ( sq, 0, sq/2 ), ( -sq, 0, -sq/2 ), ( 0, 1, 0 ), ( 0, -1, 0 ), ( sq, 0, -sq/2 ), ( -sq, 0, sq/2 ) ] ]
		GafferSceneTest.IECoreScenePreviewTest.MeshAlgoTessellateTest().betterAssertAlmostEqual(
			result["N"],
			IECoreScene.PrimitiveVariable(
				Interpolation.FaceVarying,
				IECore.V3fVectorData( normals, IECore.GeometricData.Interpretation.Normal ),
				IECore.IntVectorData( sum( [[i,i,i,i] for i in [1, 4, 0, 5, 2, 3]], [] ) )
			),
			tolerance = 0.0000002
		)
		self.assertEqual( result["numericTest"], prim["numericTest"] )

		self.assertEqual(
			result["constantVectorTest"],
			IECoreScene.PrimitiveVariable(
				Interpolation.Constant,
				IECore.V3fData( imath.V3f( 10 + sq/4, 1, -sq/2 ), IECore.GeometricData.Interpretation.Point )
			)
		)

	def testTransformPrimitiveCancellation( self ):

		# Test cancellation
		# ( This function is so fast that we actually need some pretty enormous data to show cancellation doing
		# something )
		bigPlane = IECoreScene.MeshPrimitive.createPlane(
			imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ),
			divisions = imath.V2i( 2000, 2000 )
		)

		m = imath.M44f()
		m.translate( imath.V3f( 10, 1, 0 ) )

		canceller = IECore.Canceller()

		def slowTransform():
			try:
				PrimitiveAlgo.transformPrimitive( bigPlane, m, canceller )
			except IECore.Cancelled:
				pass

		t = time.time()
		thread = threading.Thread( target = slowTransform )
		thread.start()

		# Delay so that the computation actually starts, rather
		# than being avoided entirely.
		time.sleep( 0.01 )

		acceptableCancellationDelay = 0.01 if GafferTest.inCI() else 0.001

		canceller.cancel()
		thread.join()
		self.assertLess( time.time() - t, 0.01 + acceptableCancellationDelay )

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testTransformPrimitivePerf( self ) :

		mesh = IECoreScene.MeshPrimitive.createPlane(
			imath.Box2f( imath.V2f( -2 ), imath.V2f( 2 ) ),
			divisions = imath.V2i( 4000, 4000 )
		)

		m = imath.M44f()
		m.setTranslation( imath.V3f( 0, 1, 0 ) )

		with GafferTest.TestRunner.PerformanceScope() :
			# It's too expensive to allocate a mesh big enough to really make this slow,
			# so run it 10 times to give a less noisy timing result
			for i in range( 10 ):
				PrimitiveAlgo.transformPrimitive( mesh, m )


	def testMergePrimitivesSimpleMeshes( self ) :

		mesh1 = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -2 ), imath.V2f( 2 ) ) )

		with self.assertRaisesRegex( RuntimeError, "mergePrimitives requires at least one primitive" ) :
			self.assertEqual( PrimitiveAlgo.mergePrimitives( [] ), None )

		self.assertEqual( PrimitiveAlgo.mergePrimitives( [( mesh1, imath.M44f() )] ), mesh1 )

		with self.assertRaisesRegex( RuntimeError, "Cannot merge null Primitive" ) :
			PrimitiveAlgo.mergePrimitives( [( mesh1, imath.M44f() ), ( None, imath.M44f() )] )

		mesh2 = IECoreScene.MeshPrimitive(
			IECore.IntVectorData( [ 3 ] ), IECore.IntVectorData( range( 3 ) ),
			"linear", IECore.V3fVectorData( [ imath.V3f( i ) for i in [ (1,0,0),(0,1,0),(0,0,1) ] ] )
		)
		mesh2["constV3fPrimVar"] = IECoreScene.PrimitiveVariable( Interpolation.Constant,
			IECore.V3fData( imath.V3f( 0.1, 0.2, 0.3 ), IECore.GeometricData.Interpretation.Point )
		)

		with IECore.CapturingMessageHandler() as mh:
			mergedWithMissingN = PrimitiveAlgo.mergePrimitives( [( mesh1, imath.M44f() ), ( mesh2, imath.M44f() ) ] )
		self.assertEqual( len( mh.messages ), 1 )
		self.assertEqual( mh.messages[0].context, "mergePrimitives" )
		self.assertEqual( mh.messages[0].message, 'Primitive variable N missing on some input primitives, defaulting to zero length normals.' )

		# The effect of not specifying a normal is the same as a Constant, zero normal
		mesh2["N"] = IECoreScene.PrimitiveVariable( Interpolation.Constant,
			IECore.V3fData( imath.V3f( 0 ), IECore.GeometricData.Interpretation.Normal )
		)

		merged = PrimitiveAlgo.mergePrimitives( [( mesh1, imath.M44f() ), ( mesh2, imath.M44f() ) ] )
		self.assertEqual( merged["N"], mergedWithMissingN["N"] )
		self.assertEqual( merged, mergedWithMissingN )

		self.assertTrue( merged.arePrimitiveVariablesValid() )
		self.assertEqual( merged.interpolation, "linear" )
		self.assertEqual( merged.verticesPerFace, IECore.IntVectorData( [ 4, 3 ] ) )
		self.assertEqual( merged.vertexIds, IECore.IntVectorData( [ 0, 1, 3, 2,   4, 5, 6 ] ) )
		self.assertEqual( merged["P"], IECoreScene.PrimitiveVariable( Interpolation.Vertex, IECore.V3fVectorData( [ imath.V3f( i ) for i in [
			(-2, -2, 0), (2, -2, 0), (-2, 2, 0), (2, 2, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1) ]
		], IECore.GeometricData.Interpretation.Point ) ) )

		m = imath.M44f()
		m.translate( imath.V3f( 30, 0, 0 ) )
		mergedTranslated = PrimitiveAlgo.mergePrimitives( [( mesh1, imath.M44f() ), ( mesh2, m ) ] )
		self.assertEqual( mergedTranslated["P"].data, IECore.V3fVectorData( [ imath.V3f( i ) for i in [
			(-2, -2, 0), (2, -2, 0), (-2, 2, 0), (2, 2, 0), (31, 0, 0), (30, 1, 0), (30, 0, 1) ]
		], IECore.GeometricData.Interpretation.Point ) )
		self.assertEqual(
			mergedTranslated["constV3fPrimVar"].data,
			IECore.V3fVectorData( [ imath.V3f( 0 ), imath.V3f( 30.1, 0.2, 0.3 ) ],
				IECore.GeometricData.Interpretation.Point )
		)

	def testMergePrimitivesSimpleCurves( self ) :

		mesh1 = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -2 ), imath.V2f( 2 ) ) )

		curveVerts1 = [ imath.V3f( i ) for i in [ (0,0,0),(0,1,0),(1,1,0),(1,0,0) ] ]
		curves1 = IECoreScene.CurvesPrimitive( IECore.IntVectorData( [ 4 ] ), IECore.CubicBasisf.linear(), False,
			IECore.V3fVectorData( curveVerts1 )
		)

		with self.assertRaisesRegex( RuntimeError, "Primitive type mismatch: Cannot merge CurvesPrimitive with MeshPrimitive" ) :
			PrimitiveAlgo.mergePrimitives( [( mesh1, imath.M44f() ), ( curves1, imath.M44f() ) ] )

		curveVerts2	= [ imath.V3f( i, 2, 0 ) for i in range( 7 ) ]
		curves2 = IECoreScene.CurvesPrimitive( IECore.IntVectorData( [ 7 ] ), IECore.CubicBasisf.linear(), False,
			IECore.V3fVectorData( curveVerts2 )
		)

		merged = PrimitiveAlgo.mergePrimitives( [( curves1, imath.M44f() ), ( curves2, imath.M44f() ) ] )
		self.assertTrue( merged.arePrimitiveVariablesValid() )
		self.assertEqual( merged.verticesPerCurve(), IECore.IntVectorData( [ 4, 7 ] ) )
		self.assertEqual( merged["P"], IECoreScene.PrimitiveVariable( Interpolation.Vertex, IECore.V3fVectorData( curveVerts1 + curveVerts2, IECore.GeometricData.Interpretation.Point ) ) )

		curves1.setTopology( curves1.verticesPerCurve(), curves1.basis(), True )
		with self.assertRaisesRegex( RuntimeError, "Cannot merge periodic and non-periodic curves" ) :
			PrimitiveAlgo.mergePrimitives( [( curves1, imath.M44f() ), ( curves2, imath.M44f() ) ] )

		curves2.setTopology( curves2.verticesPerCurve(), curves2.basis(), True )
		mergedNew = PrimitiveAlgo.mergePrimitives( [( curves1, imath.M44f() ), ( curves2, imath.M44f() ) ] )
		merged.setTopology( merged.verticesPerCurve(), merged.basis(), True )
		self.assertEqual( mergedNew, merged )

		curves1.setTopology( curves1.verticesPerCurve(), IECore.CubicBasisf.bezier(), True )
		with IECore.CapturingMessageHandler() as mh:
			mergedNew = PrimitiveAlgo.mergePrimitives( [( curves1, imath.M44f() ), ( curves2, imath.M44f() ) ] )
		self.assertEqual( len( mh.messages ), 1 )
		self.assertEqual( mh.messages[0].message, 'Ignoring mismatch in curve basis and defaulting to linear' )

		self.assertEqual( mergedNew, merged )

		curves2.setTopology( curves2.verticesPerCurve(), IECore.CubicBasisf.bezier(), True )
		mergedNew = PrimitiveAlgo.mergePrimitives( [( curves1, imath.M44f() ), ( curves2, imath.M44f() ) ] )
		merged.setTopology( merged.verticesPerCurve(), IECore.CubicBasisf.bezier(), True )

		self.assertEqual( mergedNew, merged )

	def testMergePrimitivesSimplePoints( self ) :

		mesh1 = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -2 ), imath.V2f( 2 ) ) )

		pointVerts1 = [ imath.V3f( i ) for i in range( 9 ) ]
		points1 = IECoreScene.PointsPrimitive( IECore.V3fVectorData( pointVerts1 ) )

		with self.assertRaisesRegex( RuntimeError, "Primitive type mismatch: Cannot merge PointsPrimitive with MeshPrimitive" ) :
			PrimitiveAlgo.mergePrimitives( [( mesh1, imath.M44f() ), ( points1, imath.M44f() ) ] )

		pointVerts2 = [ imath.V3f( i, 0, 0 ) for i in range( 11 ) ]
		points2 = IECoreScene.PointsPrimitive( IECore.V3fVectorData( pointVerts2 ) )

		merged = PrimitiveAlgo.mergePrimitives( [( points1, imath.M44f() ), ( points2, imath.M44f() ) ] )
		self.assertTrue( merged.arePrimitiveVariablesValid() )
		self.assertEqual( merged["P"], IECoreScene.PrimitiveVariable( Interpolation.Vertex, IECore.V3fVectorData( pointVerts1 + pointVerts2, IECore.GeometricData.Interpretation.Point ) ) )
		self.assertEqual( merged.keys(), [ "P" ] )

		points1["type"] = IECoreScene.PrimitiveVariable( Interpolation.Constant, IECore.StringData( "sphere" ) )

		with IECore.CapturingMessageHandler() as mh:
			merged = PrimitiveAlgo.mergePrimitives( [( points1, imath.M44f() ), ( points2, imath.M44f() ) ] )
		self.assertEqual( len( mh.messages ), 1 )
		self.assertEqual( mh.messages[0].message, 'Ignoring mismatch in point type between sphere and particle and defaulting to particle' )

		self.assertEqual( merged["type"], IECoreScene.PrimitiveVariable( Interpolation.Constant, IECore.StringData( "particle" ) ) )

		points2["type"] = IECoreScene.PrimitiveVariable( Interpolation.Constant, IECore.StringData( "sphere" ) )

		merged = PrimitiveAlgo.mergePrimitives( [( points1, imath.M44f() ), ( points2, imath.M44f() ) ] )

		self.assertEqual( merged["type"], IECoreScene.PrimitiveVariable( Interpolation.Constant, IECore.StringData( "sphere" ) ) )


	def testMergePrimitiveMeshInterpolate( self ) :

		mesh1 = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -2 ), imath.V2f( 2 ) ) )
		mesh2 = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -2 ), imath.V2f( 3 ) ) )

		ref = PrimitiveAlgo.mergePrimitives( [( mesh1, imath.M44f() ), ( mesh2, imath.M44f() ) ] )

		mesh1.setInterpolation( "catmullClark" )

		with IECore.CapturingMessageHandler() as mh:
			merged = PrimitiveAlgo.mergePrimitives( [( mesh1, imath.M44f() ), ( mesh2, imath.M44f() ) ] )
		self.assertEqual( len( mh.messages ), 1 )
		self.assertEqual( mh.messages[0].message, 'Ignoring mismatch between mesh interpolations catmullClark and linear and defaulting to linear' )
		self.assertEqual( merged, ref )

		mesh2.setInterpolation( "catmullClark" )
		merged = PrimitiveAlgo.mergePrimitives( [( mesh1, imath.M44f() ), ( mesh2, imath.M44f() ) ] )
		ref.setInterpolation( "catmullClark" )
		self.assertEqual( merged, ref )

		mesh2.setInterpolateBoundary( "edgeOnly" )
		with IECore.CapturingMessageHandler() as mh:
			merged = PrimitiveAlgo.mergePrimitives( [( mesh1, imath.M44f() ), ( mesh2, imath.M44f() ) ] )
		self.assertEqual( len( mh.messages ), 1 )
		self.assertEqual( mh.messages[0].message, 'Ignoring mismatch between mesh interpolate bound edgeAndCorner and edgeOnly and defaulting to edgeAndCorner' )
		self.assertEqual( merged, ref )

		mesh1.setInterpolateBoundary( "edgeOnly" )
		merged = PrimitiveAlgo.mergePrimitives( [( mesh1, imath.M44f() ), ( mesh2, imath.M44f() ) ] )
		ref.setInterpolateBoundary( "edgeOnly" )
		self.assertEqual( merged, ref )

		mesh2.setFaceVaryingLinearInterpolation( "cornersPlus2" )
		with IECore.CapturingMessageHandler() as mh:
			merged = PrimitiveAlgo.mergePrimitives( [( mesh1, imath.M44f() ), ( mesh2, imath.M44f() ) ] )
		self.assertEqual( len( mh.messages ), 1 )
		self.assertEqual( mh.messages[0].message, 'Ignoring mismatch between mesh face varying linear interpolation cornersPlus1 and cornersPlus2 and defaulting to cornersPlus1' )
		self.assertEqual( merged, ref )

		mesh1.setFaceVaryingLinearInterpolation( "cornersPlus2" )
		merged = PrimitiveAlgo.mergePrimitives( [( mesh1, imath.M44f() ), ( mesh2, imath.M44f() ) ] )
		ref.setFaceVaryingLinearInterpolation( "cornersPlus2" )
		self.assertEqual( merged, ref )

		mesh2.setTriangleSubdivisionRule( "smooth" )
		with IECore.CapturingMessageHandler() as mh:
			merged = PrimitiveAlgo.mergePrimitives( [( mesh1, imath.M44f() ), ( mesh2, imath.M44f() ) ] )
		self.assertEqual( len( mh.messages ), 1 )
		self.assertEqual( mh.messages[0].message, 'Ignoring mismatch between mesh triangle subdivision rule catmullClark and smooth and defaulting to catmullClark' )
		self.assertEqual( merged, ref )

		mesh1.setTriangleSubdivisionRule( "smooth" )
		merged = PrimitiveAlgo.mergePrimitives( [( mesh1, imath.M44f() ), ( mesh2, imath.M44f() ) ] )
		ref.setTriangleSubdivisionRule( "smooth" )
		self.assertEqual( merged, ref )


	def runTestMismatchedInterpolation( self, source ) :
		# A lot of the complexity comes from handling every possible combination for mismatched interpolations,
		# so make sure we test it thoroughly

		isMesh = type( source ) == IECoreScene.MeshPrimitive
		isCurves = type( source ) == IECoreScene.CurvesPrimitive
		isPoints = not isMesh and not isCurves

		# Create a source with one primvar of each interpolation, and a random P

		def randomC():
			return imath.Color3f( random.random(), random.random(), random.random() )

		source["P"] = IECoreScene.PrimitiveVariable( Interpolation.Vertex,
			IECore.V3fVectorData(
				[ imath.V3f( randomC() ) for i in range( source.variableSize( Interpolation.Vertex ) ) ]
			)
		)
		allInterps = source.copy()
		allInterps["A"] = IECoreScene.PrimitiveVariable( Interpolation.Constant, IECore.Color3fData( randomC() ) )
		for name, interp in [
			( "B", Interpolation.Vertex ), ( "C", Interpolation.Uniform ),
			( "D", Interpolation.Varying ), ( "E", Interpolation.FaceVarying )
		]:
			allInterps[name] = IECoreScene.PrimitiveVariable(
				interp, IECore.Color3fVectorData( [ randomC() for i in range( source.variableSize( interp ) ) ] )
			)
		allInterps["labelSource"] = IECoreScene.PrimitiveVariable( Interpolation.Constant, IECore.IntData( 0 ) )

		for interp, indexed in itertools.product( [
				Interpolation.Constant, Interpolation.Vertex, Interpolation.Uniform,
				Interpolation.Varying, Interpolation.FaceVarying
			], [ False, True ] ):

			# Create a source with all primvars set to the current interpolation, optionally indexed
			oneInterp = source.copy()
			for name in [ "A", "B", "C", "D", "E" ]:
				varSize = source.variableSize( interp )

				if interp == Interpolation.Constant:
					oneInterp[name] = IECoreScene.PrimitiveVariable( interp, IECore.Color3fData( randomC() ) )
				elif indexed:
					oneInterp[name] = IECoreScene.PrimitiveVariable(
						interp,
						IECore.Color3fVectorData( [ randomC() for i in range( 10 ) ] ),
						IECore.IntVectorData( [ random.randint( 0, 9 ) for i in range( varSize ) ] )
					)
				else:
					oneInterp[name] = IECoreScene.PrimitiveVariable(
						interp,
						IECore.Color3fVectorData( [ randomC() for i in range( varSize ) ] )
					)
			oneInterp["labelSource"] = IECoreScene.PrimitiveVariable( Interpolation.Constant, IECore.IntData( 1 ) )

			with IECore.CapturingMessageHandler() as mh:
				merged = PrimitiveAlgo.mergePrimitives( [( allInterps, imath.M44f() ), ( oneInterp, imath.M44f() )] )
			self.assertTrue( merged.arePrimitiveVariablesValid() )

			allInterpsRef = allInterps.copy()
			oneInterpRef = oneInterp.copy()

			numDiscarded = 0
			if isCurves:
				# We don't support merging varying/vertex on curves ( the resampling required is more complicated,
				# and can't be done losslessly )
				messageTexts = [ i.message for i in mh.messages ]
				for k in allInterps.keys():
					mixedInterps = set( [ allInterpsRef[k].interpolation, oneInterpRef[k].interpolation ] )
					if Interpolation.Vertex in mixedInterps and (
							Interpolation.Varying in mixedInterps or Interpolation.FaceVarying in mixedInterps ):
						del allInterpsRef[k]
						del oneInterpRef[k]
						numDiscarded += 1
						self.assertIn(
							'Discarding variable "%s" - Cannot mix Vertex and Varying curve variables.' % k,
							messageTexts
						)
			self.assertEqual( len( mh.messages ), numDiscarded )

			for k in allInterpsRef.keys():

				kInterp = allInterps[k].interpolation

				if isPoints:
					expectedInterp = Interpolation.Vertex
				elif k == "P":
					expectedInterp = Interpolation.Vertex
				elif k == "labelSource":
					expectedInterp = Interpolation.Uniform
				elif self.interpolationMatches( source, kInterp, interp ):
					expectedInterp = interp
				elif kInterp == Interpolation.Constant or ( not isMesh and kInterp == Interpolation.Uniform ):
					expectedInterp = interp
				elif interp == Interpolation.Constant or ( not isMesh and interp == Interpolation.Uniform ):
					expectedInterp = kInterp
				elif isMesh:
					expectedInterp = Interpolation.FaceVarying
				else:
					# All cases are covered by previous branches
					raise IECore.Exception( "%s %s" % ( kInterp, interp ) )

				if expectedInterp == Interpolation.Constant:
					expectedInterp = Interpolation.Uniform

				if isMesh:
					if expectedInterp == Interpolation.Varying:
						expectedInterp = Interpolation.Vertex
				elif isCurves:
					if expectedInterp == Interpolation.FaceVarying:
						expectedInterp = Interpolation.Varying
				else:
					if expectedInterp == Interpolation.FaceVarying or expectedInterp == Interpolation.Varying:
						expectedInterp = Interpolation.Vertex

				self.resamplePrimVars( allInterpsRef, [ k ], expectedInterp )
				self.resamplePrimVars( oneInterpRef, [ k ], expectedInterp )


			with self.subTest( mergeWithInterp = interp, indexed = indexed ):

				self.assertTrue( allInterpsRef.arePrimitiveVariablesValid() )
				self.assertTrue( oneInterpRef.arePrimitiveVariablesValid() )

				if type( merged ) == IECoreScene.MeshPrimitive:
					splitter = IECoreScene.MeshAlgo.MeshSplitter( merged, merged["labelSource"] )

					GafferSceneTest.IECoreScenePreviewTest.MeshAlgoTessellateTest().assertMeshesPracticallyEqual( splitter.mesh( 0 ), allInterpsRef )
					GafferSceneTest.IECoreScenePreviewTest.MeshAlgoTessellateTest().assertMeshesPracticallyEqual( splitter.mesh( 1 ), oneInterpRef )

				for k in allInterpsRef.keys():
					with self.subTest( interpolationA = allInterps[k].interpolation, interpolationB = interp, primVar = k ):
						expectedInterp = allInterpsRef[k].interpolation
						needIndices = (
							oneInterp[k].indices != None or
							#indexed or
							not self.interpolationMatches( source, allInterps[k].interpolation, expectedInterp ) or
							not self.interpolationMatches( source, oneInterp[k].interpolation, expectedInterp )
						)

						self.assertEqual( merged[k].indices != None, needIndices )
						self.assertEqual( merged[k].interpolation, expectedInterp )

						self.assertEqual(
							list( merged[k].expandedData() ),
							list( allInterpsRef[k].expandedData() ) + list( oneInterpRef[k].expandedData() )
						)

	def testMismatchedInterpolationMesh( self ):

		file = IECoreScene.SceneInterface.create(
			str( self.usdFileDir / "generalTestMesh.usd" ), IECore.IndexedIO.OpenMode.Read
		)
		meshSource = file.child( "object" ).readObject( 0.0 )
		for k in meshSource.keys():
			del meshSource[k]

		self.runTestMismatchedInterpolation( meshSource )

	def testMismatchedInterpolationCurvesLinear( self ):

		source = IECoreScene.CurvesPrimitive(
			IECore.IntVectorData( [ 4, 5, 6, 5, 4] ), IECore.CubicBasisf.linear(), False
		)
		self.runTestMismatchedInterpolation( source )

	def testMismatchedInterpolationCurvesCubic( self ):
		source = IECoreScene.CurvesPrimitive(
			IECore.IntVectorData( [ 4, 5, 6, 5, 4] ), IECore.CubicBasisf.bSpline(), False
		)
		self.runTestMismatchedInterpolation( source )

	def testMismatchedInterpolationCurvesPeriodicLinear( self ):
		source = IECoreScene.CurvesPrimitive(
			IECore.IntVectorData( [ 4, 5, 6, 5, 4] ), IECore.CubicBasisf.linear(), True
		)
		self.runTestMismatchedInterpolation( source )

	def testMismatchedInterpolationCurvesPeriodicCubic( self ):
		source = IECoreScene.CurvesPrimitive(
			IECore.IntVectorData( [ 4, 5, 6, 5, 4] ), IECore.CubicBasisf.bSpline(), True
		)
		self.runTestMismatchedInterpolation( source )

	def testMismatchedInterpolationPoints( self ):
		source = IECoreScene.PointsPrimitive( 20 )
		self.runTestMismatchedInterpolation( source )

	def testMergeMeshes( self ) :

		# Test with a more complex mesh that has creases

		file = IECoreScene.SceneInterface.create(
			str( self.usdFileDir / "generalTestMesh.usd" ), IECore.IndexedIO.OpenMode.Read
		)
		source = file.child( "object" ).readObject( 0.0 )

		with IECore.CapturingMessageHandler() as mh:
			bogusIndexed = PrimitiveAlgo.mergePrimitives( [( source, imath.M44f() ), ( source, imath.M44f() )] )
		self.assertEqual( bogusIndexed.keys(), [ 'P', 'altUv', 'indexedUniform', 'indexedVertex', 'stringConstant', 'unindexedFaceVarying', 'unindexedUniform', 'uv' ] )
		self.assertEqual( len( mh.messages ), 1 )
		self.assertEqual( mh.messages[0].context, "mergePrimitives" )
		self.assertEqual( mh.messages[0].message, 'Discarding variable "indexedConstant" - Cannot promote Constant primitive variable of type "Color3fVectorData".' )

		del source["indexedConstant"]


		m = imath.M44f()
		m.translate( imath.V3f( 30, 0, 0 ) )
		sourceShifted = source.copy()
		PrimitiveAlgo.transformPrimitive( sourceShifted, m )

		self.assertEqual(
			PrimitiveAlgo.mergePrimitives( [( source, imath.M44f() ), ( source, m )] ),
			PrimitiveAlgo.mergePrimitives( [( source, imath.M44f() ), ( sourceShifted, imath.M44f() )] )
		)

		sourceShifted["labelSource"] = IECoreScene.PrimitiveVariable( Interpolation.Constant, IECore.IntData( 1 ) )

		referenceSource = source.copy()
		referenceSource["labelSource"] = IECoreScene.PrimitiveVariable( Interpolation.Constant, IECore.IntData( 0 ) )
		self.resamplePrimVars( referenceSource, [ "labelSource", "stringConstant" ], Interpolation.Uniform )

		referenceShifted = sourceShifted.copy()
		self.resamplePrimVars( referenceShifted, [ "labelSource", "stringConstant" ], Interpolation.Uniform )


		# Try merging two complex meshes, and then splitting them back apart to make sure they match.
		# We need to use assertMeshesPracticallyEqual here instead of assertEqual because MeshSplitter
		# does not preserve vertex order.
		merged = PrimitiveAlgo.mergePrimitives( [( source, imath.M44f() ), ( sourceShifted, imath.M44f() )] )

		splitter = IECoreScene.MeshAlgo.MeshSplitter( merged, merged["labelSource"] )
		GafferSceneTest.IECoreScenePreviewTest.MeshAlgoTessellateTest().assertMeshesPracticallyEqual( splitter.mesh( 0 ), referenceSource )
		GafferSceneTest.IECoreScenePreviewTest.MeshAlgoTessellateTest().assertMeshesPracticallyEqual( splitter.mesh( 1 ), referenceShifted )

		# assertMeshesPracticallyEqual ignores whether variables are indexed. We want to make sure that any
		# variables that aren't already indexed, and having match interpolations between the meshes, and
		# don't need to be promoted from Constant to Uniform, don't need to be indexed.
		self.assertEqual(
			{ i for i in merged.keys() if merged[i].indices },
			{'labelSource', 'uv', 'indexedVertex', 'stringConstant', 'altUv', 'indexedUniform'}
		)

		# Now try merging a plane that has different primvars
		sourcePlane = IECoreScene.MeshPrimitive.createPlane(
			imath.Box2f( imath.V2f( -2 ), imath.V2f( 2 ) ),
			divisions = imath.V2i( 4, 4 )
		)
		sourcePlane["labelSource"] = IECoreScene.PrimitiveVariable( Interpolation.Constant, IECore.IntData( 2 ) )
		sourcePlane.setInterpolation( "catmullClark" )

		referencePlane = sourcePlane.copy()
		referencePlane["altUv"] = IECoreScene.PrimitiveVariable( Interpolation.Constant, IECore.V2fData( imath.V2f( 0 ) ) )
		referencePlane["indexedUniform"] = IECoreScene.PrimitiveVariable( Interpolation.Constant, IECore.IntData( 0 ) )
		referencePlane["indexedVertex"] = IECoreScene.PrimitiveVariable( Interpolation.Constant, IECore.V3fData( imath.V3f(0) ) )
		referencePlane["stringConstant"] = IECoreScene.PrimitiveVariable( Interpolation.Constant, IECore.StringData( "" ) )
		referencePlane["unindexedFaceVarying"] = IECoreScene.PrimitiveVariable( Interpolation.Constant, IECore.V3fData( imath.V3f( 0 ) ) )
		referencePlane["unindexedUniform"] = IECoreScene.PrimitiveVariable( Interpolation.Constant, IECore.IntData( 0 ) )
		self.resamplePrimVars( referencePlane, [ "labelSource", "stringConstant", "indexedUniform", "unindexedUniform" ], Interpolation.Uniform )
		self.resamplePrimVars( referencePlane, [ "indexedVertex" ], Interpolation.Vertex )
		self.resamplePrimVars( referencePlane, [ "altUv", "unindexedFaceVarying" ], Interpolation.FaceVarying )

		# Merge 3 meshes - complex mesh, shifted complex mesh, and a plane

		with IECore.CapturingMessageHandler() as mh:
			merged = PrimitiveAlgo.mergePrimitives(
				[( source, imath.M44f() ), ( sourcePlane, imath.M44f() ), ( sourceShifted, imath.M44f() )]
			)
		self.assertEqual( len( mh.messages ), 1 )
		self.assertEqual( mh.messages[0].message, 'Primitive variable N missing on some input primitives, defaulting to zero length normals.' )

		referenceSource["N"] = IECoreScene.PrimitiveVariable( Interpolation.Vertex, IECore.V3fVectorData( [imath.V3f( 0 ) ] * referenceSource.variableSize( Interpolation.Vertex ) ) )
		referenceShifted["N"] = IECoreScene.PrimitiveVariable( Interpolation.Vertex, IECore.V3fVectorData( [imath.V3f( 0 ) ] * referenceSource.variableSize( Interpolation.Vertex ) ) )

		splitter = IECoreScene.MeshAlgo.MeshSplitter( merged, merged["labelSource"] )
		GafferSceneTest.IECoreScenePreviewTest.MeshAlgoTessellateTest().assertMeshesPracticallyEqual( splitter.mesh( 0 ), referenceSource )
		GafferSceneTest.IECoreScenePreviewTest.MeshAlgoTessellateTest().assertMeshesPracticallyEqual( splitter.mesh( 1 ), referenceShifted )
		GafferSceneTest.IECoreScenePreviewTest.MeshAlgoTessellateTest().assertMeshesPracticallyEqual( splitter.mesh( 2 ), referencePlane )

		# Just about everything needs to be indexed now, since the variables that are missing from one prim get
		# indexed
		self.assertEqual(
			{ i for i in merged.keys() if merged[i].indices },
			{'labelSource', 'uv', 'indexedVertex', 'stringConstant', 'altUv', 'indexedUniform', 'N', 'unindexedUniform', 'unindexedFaceVarying'}
		)

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testMergeManyPerf( self ) :

		mesh = IECoreScene.MeshPrimitive.createPlane(
			imath.Box2f( imath.V2f( -2 ), imath.V2f( 2 ) ),
			divisions = imath.V2i( 100, 100 )
		)

		meshes = []
		for i in range( 1000 ):
			m = imath.M44f()
			m.setTranslation( imath.V3f( 0, i, 0 ) )

			meshes.append( ( mesh, m ) )

		with GafferTest.TestRunner.PerformanceScope() :
			PrimitiveAlgo.mergePrimitives( meshes )

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testMergeFewPerf( self ) :

		mesh = IECoreScene.MeshPrimitive.createPlane(
			imath.Box2f( imath.V2f( -2 ), imath.V2f( 2 ) ),
			divisions = imath.V2i( 2000, 2000 )
		)

		m = imath.M44f()
		m.setTranslation( imath.V3f( 0, 1, 0 ) )

		meshes = [ ( mesh, imath.M44f() ), ( mesh, m ) ]

		with GafferTest.TestRunner.PerformanceScope() :
			PrimitiveAlgo.mergePrimitives( meshes )


if __name__ == "__main__":
	unittest.main()
