##########################################################################
#
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
import random

import arnold
import imath

import IECore
import IECoreScene
import IECoreArnold

class PointsAlgoTest( unittest.TestCase ) :

	def testConverterResultType( self ) :

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			p = IECoreScene.PointsPrimitive( IECore.V3fVectorData( [ imath.V3f( i ) for i in range( 0, 10 ) ] ) )
			n = IECoreArnold.NodeAlgo.convert( p, universe, "testPoints" )

			self.assertTrue( type( n ) is type( arnold.AiNode( universe, "points" ) ) )

	def testMode( self ) :

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			p = IECoreScene.PointsPrimitive( IECore.V3fVectorData( [ imath.V3f( i ) for i in range( 0, 10 ) ] ) )

			n = IECoreArnold.NodeAlgo.convert( p, universe, "testPoints" )
			self.assertEqual( arnold.AiNodeGetStr( n, "mode" ), "disk" )

			p["type"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Constant, "particle" )
			n = IECoreArnold.NodeAlgo.convert( p, universe, "testPoints" )
			self.assertEqual( arnold.AiNodeGetStr( n, "mode" ), "disk" )

			p["type"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Constant, "disk" )
			n = IECoreArnold.NodeAlgo.convert( p, universe, "testPoints" )
			self.assertEqual( arnold.AiNodeGetStr( n, "mode" ), "disk" )

			p["type"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Constant, "sphere" )
			n = IECoreArnold.NodeAlgo.convert( p, universe, "testPoints" )
			self.assertEqual( arnold.AiNodeGetStr( n, "mode" ), "sphere" )

			p["type"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Constant, "patch" )
			n = IECoreArnold.NodeAlgo.convert( p, universe, "testPoints" )
			self.assertEqual( arnold.AiNodeGetStr( n, "mode" ), "quad" )

	def testConstantPrimitiveVariable( self ) :

		p = IECoreScene.PointsPrimitive( IECore.V3fVectorData( 10 ) )
		p["myPrimVar"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Constant, IECore.IntData( 10 ) )

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			n = IECoreArnold.NodeAlgo.convert( p, universe, "testPoints" )
			self.assertEqual( arnold.AiNodeGetInt( n, "myPrimVar" ), 10 )

	def testConstantArrayPrimitiveVariable( self ) :

		p = IECoreScene.PointsPrimitive( IECore.V3fVectorData( 10 ) )
		p["myPrimVar"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Constant, IECore.IntVectorData( range( 0, 10 ) ) )

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			n = IECoreArnold.NodeAlgo.convert( p, universe, "testPoints" )
			a = arnold.AiNodeGetArray( n, "myPrimVar" )
			self.assertEqual( arnold.AiArrayGetNumElements( a.contents ), 10 )
			for i in range( 0, 10 ) :
				self.assertEqual( arnold.AiArrayGetInt( a, i ), i )

	def testUniformPrimitiveVariable( self ) :

		p = IECoreScene.PointsPrimitive( IECore.V3fVectorData( 10 ) )
		p["myPrimVar"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Uniform, IECore.IntData( 10 ) )

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			n = IECoreArnold.NodeAlgo.convert( p, universe, "testPoints" )
			self.assertEqual( arnold.AiNodeGetInt( n, "myPrimVar" ), 10 )

	def testVertexPrimitiveVariable( self ) :

		for interpolation in ( "Vertex", "Varying", "FaceVarying" ) :

			p = IECoreScene.PointsPrimitive( IECore.V3fVectorData( 10 ) )
			p["myPrimVar"] = IECoreScene.PrimitiveVariable( getattr( IECoreScene.PrimitiveVariable.Interpolation, interpolation ), IECore.IntVectorData( range( 0, 10 ) ) )

			self.assertTrue( p.arePrimitiveVariablesValid() )

			with IECoreArnold.UniverseBlock( writable = True ) as universe :

				n = IECoreArnold.NodeAlgo.convert( p, universe, "testPoints" )
				a = arnold.AiNodeGetArray( n, "myPrimVar" )
				self.assertEqual( arnold.AiArrayGetNumElements( a.contents ), 10 )
				for i in range( 0, 10 ) :
					self.assertEqual( arnold.AiArrayGetInt( a, i ), i )

	def testBooleanPrimitiveVariable( self ) :

		p = IECoreScene.PointsPrimitive( IECore.V3fVectorData( 10 ) )
		p["truePrimVar"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Constant, IECore.BoolData( True ) )
		p["falsePrimVar"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Constant, IECore.BoolData( False ) )

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			n = IECoreArnold.NodeAlgo.convert( p, universe, "testPoints" )
			self.assertEqual( arnold.AiNodeGetBool( n, "truePrimVar" ), True )
			self.assertEqual( arnold.AiNodeGetBool( n, "falsePrimVar" ), False )

	def testMotion( self ) :

		p1 = IECoreScene.PointsPrimitive( IECore.V3fVectorData( [ imath.V3f( 10 ) ] * 10 ) )
		p1["width"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.FloatVectorData( [ 1 ] * 10 ),
		)

		p2 = IECoreScene.PointsPrimitive( IECore.V3fVectorData( [ imath.V3f( 20 ) ] * 10 ) )
		p2["width"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.FloatVectorData( [ 2 ] * 10 ),
		)

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			n = IECoreArnold.NodeAlgo.convert( [ p1, p2 ], -0.25, 0.25, universe, "testPoints" )

			a = arnold.AiNodeGetArray( n, "points" )
			self.assertEqual( arnold.AiArrayGetNumElements( a.contents ), 10 )
			self.assertEqual( arnold.AiArrayGetNumKeys( a.contents ), 2 )

			r = arnold.AiNodeGetArray( n, "radius" )
			self.assertEqual( arnold.AiArrayGetNumElements( r.contents ), 10 )
			self.assertEqual( arnold.AiArrayGetNumKeys( r.contents ), 2 )

			for i in range( 0, 10 ) :
				self.assertEqual( arnold.AiArrayGetVec( a, i ), arnold.AtVector( 10 ) )
				self.assertEqual( arnold.AiArrayGetFlt( r, i ), 0.5 )
			for i in range( 11, 20 ) :
				self.assertEqual( arnold.AiArrayGetVec( a, i ), arnold.AtVector( 20 ) )
				self.assertEqual( arnold.AiArrayGetFlt( r, i ), 1 )

			self.assertEqual( arnold.AiNodeGetFlt( n, "motion_start" ), -0.25 )
			self.assertEqual( arnold.AiNodeGetFlt( n, "motion_end" ), 0.25 )

if __name__ == "__main__":
	unittest.main()
