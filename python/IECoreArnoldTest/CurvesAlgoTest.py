##########################################################################
#
#  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

import math
import unittest

import arnold
import imath

import IECore
import IECoreScene
import IECoreArnold

class CurvesAlgoTest( unittest.TestCase ) :

	def testMotion( self ) :

		c1 = IECoreScene.CurvesPrimitive( IECore.IntVectorData( [ 4 ] ) )
		c2 = IECoreScene.CurvesPrimitive( IECore.IntVectorData( [ 4 ] ) )

		c1["P"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.V3fVectorData( [ imath.V3f( 1 ) ] * 4 ),
		)

		c2["P"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.V3fVectorData( [ imath.V3f( 2 ) ] * 4 ),
		)

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			n = IECoreArnold.NodeAlgo.convert( [ c1, c2 ], -0.25, 0.25, universe, "testCurve" )

			a = arnold.AiNodeGetArray( n, "points" )
			self.assertEqual( arnold.AiArrayGetNumElements( a.contents ), 4 )
			self.assertEqual( arnold.AiArrayGetNumKeys( a.contents ), 2 )

			for i in range( 0, 4 ) :
				self.assertEqual( arnold.AiArrayGetVec( a, i ), arnold.AtVector( 1 ) )
			for i in range( 4, 8 ) :
				self.assertEqual( arnold.AiArrayGetVec( a, i ), arnold.AtVector( 2 ) )

			self.assertEqual( arnold.AiNodeGetFlt( n, "motion_start" ), -0.25 )
			self.assertEqual( arnold.AiNodeGetFlt( n, "motion_end" ), 0.25 )

	def testNPrimitiveVariable( self ) :

		c = IECoreScene.CurvesPrimitive( IECore.IntVectorData( [ 4 ] ), IECore.CubicBasisf.catmullRom() )
		c["P"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.V3fVectorData( [ imath.V3f( x, 0, 0 ) for x in range( 0, 4 ) ] )
		)

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			# No N - should be a ribbon

			n = IECoreArnold.NodeAlgo.convert( c, universe, "testCurve" )
			self.assertEqual( arnold.AiNodeGetStr( n, "mode" ), "ribbon" )
			self.assertEqual( arnold.AiArrayGetNumElements( arnold.AiNodeGetArray( n, "orientations" ).contents ), 0 )

			# N - should be oriented

			c["N"] = IECoreScene.PrimitiveVariable(
				IECoreScene.PrimitiveVariable.Interpolation.Vertex,
				IECore.V3fVectorData( [ imath.V3f( 0, math.sin( x ), math.cos( x ) ) for x in range( 0, 4 ) ] )
			)

			n = IECoreArnold.NodeAlgo.convert( c, universe, "testCurve" )
			self.assertEqual( arnold.AiNodeGetStr( n, "mode" ), "oriented" )
			orientations = arnold.AiNodeGetArray( n, "orientations" )
			self.assertEqual( arnold.AiArrayGetNumElements( orientations.contents ), 4 )

			for i in range( 0, 4 ) :
				self.assertEqual( arnold.AiArrayGetVec( orientations, i ), arnold.AtVector( 0, math.sin( i ), math.cos( i ) ) )

			# Motion blurred N - should be oriented and deforming

			c2 = c.copy()
			c2["N"] = IECoreScene.PrimitiveVariable(
				IECoreScene.PrimitiveVariable.Interpolation.Vertex,
				IECore.V3fVectorData( [ imath.V3f( 0, math.sin( x + 0.2 ), math.cos( x + 0.2 ) ) for x in range( 0, 4 ) ] )
			)

			n = IECoreArnold.NodeAlgo.convert( [ c, c2 ], 0.0, 1.0, universe, "testCurve" )
			self.assertEqual( arnold.AiNodeGetStr( n, "mode" ), "oriented" )

			orientations = arnold.AiNodeGetArray( n, "orientations" )
			self.assertEqual( arnold.AiArrayGetNumElements( orientations.contents ), 4 )
			self.assertEqual( arnold.AiArrayGetNumKeys( orientations.contents ), 2 )

			for i in range( 0, 4 ) :
				self.assertEqual( arnold.AiArrayGetVec( orientations, i ), arnold.AtVector( 0, math.sin( i ), math.cos( i ) ) )
				self.assertEqual( arnold.AiArrayGetVec( orientations, i + 4 ), arnold.AtVector( 0, math.sin( i + 0.2 ), math.cos( i + 0.2 ) ) )

	def testUniformUVs( self ) :

		c = IECoreScene.CurvesPrimitive( IECore.IntVectorData( [ 2, 2 ] ), IECore.CubicBasisf.linear() )
		c["P"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.V3fVectorData( [ imath.V3f( x, 0, 0 ) for x in range( 0, 4 ) ] )
		)
		c["uv"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Uniform,
			IECore.V2fVectorData(
				[
					imath.V2f( 1, 2 ),
					imath.V2f( 3, 4 ),
				],
				IECore.GeometricData.Interpretation.UV
			)
		)

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			n = IECoreArnold.NodeAlgo.convert( c, universe, "testCurve" )

			uvs = arnold.AiNodeGetArray( n, "uvs" ).contents
			self.assertEqual( arnold.AiArrayGetNumElements( uvs ), 2 )

			self.assertEqual( arnold.AiArrayGetVec2( uvs, 0 ), arnold.AtVector2( 1, 2 ) )
			self.assertEqual( arnold.AiArrayGetVec2( uvs, 1 ), arnold.AtVector2( 3, 4 ) )

	def testVertexUVs( self ) :

		c = IECoreScene.CurvesPrimitive( IECore.IntVectorData( [ 2, 2 ] ), IECore.CubicBasisf.linear() )
		c["P"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.V3fVectorData( [ imath.V3f( x, 0, 0 ) for x in range( 0, 4 ) ] )
		)
		c["uv"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.V2fVectorData(
				[
					imath.V2f( 1, 2 ),
					imath.V2f( 3, 4 ),
					imath.V2f( 5, 6 ),
					imath.V2f( 7, 8 ),
				],
				IECore.GeometricData.Interpretation.UV
			)
		)

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			n = IECoreArnold.NodeAlgo.convert( c, universe, "testCurve" )

			uvs = arnold.AiNodeGetArray( n, "uvs" ).contents
			self.assertEqual( arnold.AiArrayGetNumElements( uvs ), 4 )

			self.assertEqual( arnold.AiArrayGetVec2( uvs, 0 ), arnold.AtVector2( 1, 2 ) )
			self.assertEqual( arnold.AiArrayGetVec2( uvs, 1 ), arnold.AtVector2( 3, 4 ) )
			self.assertEqual( arnold.AiArrayGetVec2( uvs, 2 ), arnold.AtVector2( 5, 6 ) )
			self.assertEqual( arnold.AiArrayGetVec2( uvs, 3 ), arnold.AtVector2( 7, 8 ) )

	def testVertexToVaryingConversion( self ) :

		c = IECoreScene.CurvesPrimitive( IECore.IntVectorData( [ 2, 2 ] ), IECore.CubicBasisf.linear() )
		c["P"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.V3fVectorData( [ imath.V3f( x, 0, 0 ) for x in range( 0, 4 ) ] )
		)
		c["width"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.FloatVectorData( [ 1 ] * 4 ),
		)
		c["foo"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.FloatVectorData( [ 1.5 ] * 4 )
		)
		c["orient"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.QuatfVectorData( [ imath.Quatf() ] * 4 )
		)
		self.assertTrue( c.arePrimitiveVariablesValid() )

		c2 = c.copy()
		c2["width"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.FloatVectorData( [ 2 ] * 4 ),
		)
		self.assertTrue( c2.arePrimitiveVariablesValid() )

		c3 = IECoreScene.CurvesPrimitive( IECore.IntVectorData( [ 8, 8 ] ), IECore.CubicBasisf.bSpline() )
		c3["P"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.V3fVectorData( [
					imath.V3f( 0, 0, 0 ),
					imath.V3f( 0, 0, 0 ),
					imath.V3f( 0, 0, 0 ),
					imath.V3f( 0, 0.75, 0 ),
					imath.V3f( 0.25, 1, 0 ),
					imath.V3f( 1, 1, 0 ),
					imath.V3f( 1, 1, 0 ),
					imath.V3f( 1, 1, 0 ),
					imath.V3f( 0, 0, 1 ),
					imath.V3f( 0, 0, 1 ),
					imath.V3f( 0, 0, 1 ),
					imath.V3f( 0, 0.75, 1 ),
					imath.V3f( 0.25, 1, 1 ),
					imath.V3f( 1, 1, 1 ),
					imath.V3f( 1, 1, 1 ),
					imath.V3f( 1, 1, 1 )
			] ),
		)
		c3["width"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.FloatVectorData( [ 1 ] * 16 ),
		)
		c3["foo"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.FloatVectorData( [ 1.5 ] * 16 )
		)
		c3["orient"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.QuatfVectorData( [ imath.Quatf() ] * 16 )
		)
		self.assertTrue( c3.arePrimitiveVariablesValid() )

		c4 = c3.copy()
		c4["width"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.FloatVectorData( [ 2 ] * 16 ),
		)
		self.assertTrue( c4.arePrimitiveVariablesValid() )

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			n = IECoreArnold.NodeAlgo.convert( c, universe, "testLinearCurve" )
			r = arnold.AiNodeGetArray( n, "radius" )
			self.assertEqual( arnold.AiArrayGetNumElements( r.contents ), 4 )
			self.assertEqual( arnold.AiArrayGetNumKeys( r.contents ), 1 )
			foo = arnold.AiNodeGetArray( n, "foo" )
			self.assertEqual( arnold.AiArrayGetNumElements( foo.contents ), 4 )
			self.assertEqual( arnold.AiArrayGetNumKeys( foo.contents ), 1 )
			self.assertIsNone( arnold.AiNodeGetArray( n, "orient" ) )
			for i in range( 0, 4 ) :
				self.assertEqual( arnold.AiArrayGetFlt( r, i ), 0.5 )
				self.assertEqual( arnold.AiArrayGetFlt( foo, i ), 1.5 )

			n2 = IECoreArnold.NodeAlgo.convert( [ c, c2 ], -0.25, 0.25, universe, "testLinearCurves" )
			r2 = arnold.AiNodeGetArray( n2, "radius" )
			self.assertEqual( arnold.AiArrayGetNumElements( r2.contents ), 4 )
			self.assertEqual( arnold.AiArrayGetNumKeys( r2.contents ), 2 )
			foo2 = arnold.AiNodeGetArray( n2, "foo" )
			self.assertEqual( arnold.AiArrayGetNumElements( foo2.contents ), 4 )
			# arbitrary userdata is not sampled
			self.assertEqual( arnold.AiArrayGetNumKeys( foo2.contents ), 1 )
			for i in range( 0, 4 ) :
				self.assertEqual( arnold.AiArrayGetFlt( r2, i ), 0.5 )
				self.assertEqual( arnold.AiArrayGetFlt( foo2, i ), 1.5 )
			for i in range( 4, 8 ) :
				self.assertEqual( arnold.AiArrayGetFlt( r2, i ), 1 )

			# for cubic curves, radius will have been converted to Varying, so it will have fewer elements

			n3 = IECoreArnold.NodeAlgo.convert( c3, universe, "testBSplineCurve" )
			r3 = arnold.AiNodeGetArray( n3, "radius" )
			self.assertEqual( arnold.AiArrayGetNumElements( r3.contents ), 12 )
			self.assertEqual( arnold.AiArrayGetNumKeys( r3.contents ), 1 )
			foo3 = arnold.AiNodeGetArray( n3, "foo" )
			self.assertEqual( arnold.AiArrayGetNumElements( foo3.contents ), 12 )
			self.assertEqual( arnold.AiArrayGetNumKeys( foo3.contents ), 1 )
			self.assertIsNone( arnold.AiNodeGetArray( n3, "orient" ) )
			for i in range( 0, 12 ) :
				self.assertEqual( arnold.AiArrayGetFlt( r3, i ), 0.5 )
				self.assertEqual( arnold.AiArrayGetFlt( foo3, i ), 1.5 )

			n4 = IECoreArnold.NodeAlgo.convert( [ c3, c4 ], -0.25, 0.25, universe, "testBSplineCurves" )
			r4 = arnold.AiNodeGetArray( n4, "radius" )
			self.assertEqual( arnold.AiArrayGetNumElements( r4.contents ), 12 )
			self.assertEqual( arnold.AiArrayGetNumKeys( r4.contents ), 2 )
			foo4 = arnold.AiNodeGetArray( n4, "foo" )
			self.assertEqual( arnold.AiArrayGetNumElements( foo4.contents ), 12 )
			# arbitrary userdata is not sampled
			self.assertEqual( arnold.AiArrayGetNumKeys( foo4.contents ), 1 )
			for i in range( 0, 12 ) :
				self.assertEqual( arnold.AiArrayGetFlt( r4, i ), 0.5 )
				self.assertEqual( arnold.AiArrayGetFlt( foo4, i ), 1.5 )
			for i in range( 12, 24 ) :
				self.assertEqual( arnold.AiArrayGetFlt( r4, i ), 1 )

if __name__ == "__main__":
	unittest.main()
