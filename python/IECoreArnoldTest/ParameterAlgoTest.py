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

import unittest

import arnold
import imath

import IECore
import IECoreArnold

class ParameterAlgoTest( unittest.TestCase ) :

	def testTypeErrors( self ) :

		self.assertRaisesRegex(
			TypeError,
			"Expected an AtNode",
			IECoreArnold.ParameterAlgo.setParameter, None, "test", IECore.IntData( 10 )
		)

	def testSetParameter( self ) :

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			n = arnold.AiNode( universe, "standard_surface" )

			IECoreArnold.ParameterAlgo.setParameter( n, "base", IECore.FloatData( 0.25 ) )
			IECoreArnold.ParameterAlgo.setParameter( n, "customString", IECore.StringData( "test" ) )

			self.assertEqual( arnold.AiNodeGetFlt( n, "base" ), 0.25 )
			self.assertEqual( arnold.AiNodeGetStr( n, "customString" ), "test" )

	def testGetParameter( self ) :

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			n = arnold.AiNode( universe, "standard_surface" )

			self.assertEqual(
				IECoreArnold.ParameterAlgo.getParameter( n, "base" ),
				IECore.FloatData( arnold.AiNodeGetFlt( n, "base" ) )
			)

			arnold.AiNodeSetStr( n, "name", "testString" )
			self.assertEqual(
				IECoreArnold.ParameterAlgo.getParameter( n, "name" ),
				IECore.StringData( "testString" ),
			)

	def testIntData( self ) :

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			n = arnold.AiNode( universe, "standard_surface" )
			IECoreArnold.ParameterAlgo.setParameter( n, "customInt", IECore.IntData( 42 ) )
			IECoreArnold.ParameterAlgo.setParameter( n, "customUInt", IECore.UIntData( 43 ) )
			IECoreArnold.ParameterAlgo.setParameter( n, "customIntVectorData", IECore.IntVectorData( [ 5, 6, 7 ] ) )
			IECoreArnold.ParameterAlgo.setParameter( n, "customUIntVectorData", IECore.UIntVectorData( [ 12, 2147483649 ] ) )

			self.assertEqual( arnold.AiNodeGetInt( n, "customInt" ), 42 )
			self.assertEqual( arnold.AiNodeGetUInt( n, "customUInt" ), 43 )
			a = arnold.AiNodeGetArray( n, "customIntVectorData" )
			self.assertEqual( arnold.AiArrayGetNumElements( a.contents ), 3 )
			self.assertEqual( arnold.AiArrayGetInt( a, 0 ), 5 )
			self.assertEqual( arnold.AiArrayGetInt( a, 1 ), 6 )
			self.assertEqual( arnold.AiArrayGetInt( a, 2 ), 7 )
			a = arnold.AiNodeGetArray( n, "customUIntVectorData" )
			self.assertEqual( arnold.AiArrayGetNumElements( a.contents ), 2 )
			self.assertEqual( arnold.AiArrayGetUInt( a, 0 ), 12 )
			self.assertEqual( arnold.AiArrayGetUInt( a, 1 ), 2147483649 )

	def testDoubleData( self ) :

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			n = arnold.AiNode( universe, "standard_surface" )

			IECoreArnold.ParameterAlgo.setParameter( n, "base", IECore.DoubleData( 0.25 ) )
			self.assertEqual( arnold.AiNodeGetFlt( n, "base" ), 0.25 )

			IECoreArnold.ParameterAlgo.setParameter( n, "customFloat", IECore.DoubleData( 0.25 ) )
			self.assertEqual( arnold.AiNodeGetFlt( n, "customFloat" ), 0.25 )

			IECoreArnold.ParameterAlgo.setParameter( n, "customMatrix", IECore.M44dData( imath.M44d( 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16 ) ) )
			m = arnold.AiNodeGetMatrix( n, "customMatrix" )
			self.assertEqual(
				[ list( i ) for i in m.data ],
				[ [1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, 16] ],
			)

	def testStringArray( self ) :

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			n = arnold.AiNode( universe, "polymesh" )
			IECoreArnold.ParameterAlgo.setParameter( n, "trace_sets", IECore.StringVectorData( [ "a", "b" ] ) )

			a = arnold.AiNodeGetArray( n, "trace_sets" )
			self.assertEqual( arnold.AiArrayGetNumElements( a.contents ), 2 )
			self.assertEqual( arnold.AiArrayGetStr( a, 0 ), "a" )
			self.assertEqual( arnold.AiArrayGetStr( a, 1 ), "b" )

	def testVectorIntData( self ) :

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			n = arnold.AiNode( universe, "standard_surface" )

			IECoreArnold.ParameterAlgo.setParameter( n, "customV2i", IECore.V2iData( imath.V2i( 3, 4 ) ) )
			self.assertEqual( arnold.AiNodeGetVec2( n, "customV2i" ), arnold.AtVector2( 3, 4 ) )

			IECoreArnold.ParameterAlgo.setParameter( n, "customV3i", IECore.V3iData( imath.V3i( 3, 4, 5 ) ) )
			self.assertEqual( arnold.AiNodeGetVec( n, "customV3i" ), arnold.AtVector( 3, 4, 5 ) )

if __name__ == "__main__":
	unittest.main()
