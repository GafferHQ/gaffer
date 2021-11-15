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
import IECoreScene
import IECoreArnold

class SphereAlgoTest( unittest.TestCase ) :

	def testConvert( self ) :

		s = IECoreScene.SpherePrimitive( 0.25 )
		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			n = IECoreArnold.NodeAlgo.convert( s, universe, "testSphere" )
			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( n ) ), "sphere" )
			self.assertEqual( arnold.AiNodeGetFlt( n, "radius" ), 0.25 )

	def testConvertWithMotion( self ) :

		s = [ IECoreScene.SpherePrimitive( 0.25 ), IECoreScene.SpherePrimitive( 0.5 ) ]

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			n = IECoreArnold.NodeAlgo.convert( s, 0, 1, universe, "testSphere" )
			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( n ) ), "sphere" )

			a = arnold.AiNodeGetArray( n, "radius" )
			self.assertEqual( arnold.AiArrayGetFlt( a, 0 ), 0.25 )
			self.assertEqual( arnold.AiArrayGetFlt( a, 1 ), 0.5 )

			self.assertEqual( arnold.AiNodeGetFlt( n, "motion_start" ), 0 )
			self.assertEqual( arnold.AiNodeGetFlt( n, "motion_end" ), 1 )

	def testPrimitiveVariables( self ) :

		s = IECoreScene.SpherePrimitive()
		s["v"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Constant, imath.V3f( 1, 2, 3 ) )
		s["c"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Constant, imath.Color3f( 1, 2, 3 ) )
		s["s"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Constant, "test" )
		s["i"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Constant, 11 )
		s["b"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Constant, True )
		s["f"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Constant, 2.5 )
		s["m"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Constant, imath.M44f( 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16) )

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			n = IECoreArnold.NodeAlgo.convert( s, universe, "testSphere" )
			self.assertEqual( arnold.AiNodeGetVec( n, "v" ), arnold.AtVector( 1, 2, 3 ) )
			self.assertEqual( arnold.AiNodeGetRGB( n, "c" ), arnold.AtRGB( 1, 2, 3 ) )
			self.assertEqual( arnold.AiNodeGetStr( n, "s" ), "test" )
			self.assertEqual( arnold.AiNodeGetInt( n, "i" ), 11 )
			self.assertEqual( arnold.AiNodeGetBool( n, "b" ), True )
			self.assertEqual( arnold.AiNodeGetFlt( n, "f" ), 2.5 )

			m = arnold.AiNodeGetMatrix( n, "m" )
			self.assertEqual(
				[ list( i ) for i in m.data ],
				[ [1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, 16] ],
			)


if __name__ == "__main__":
	unittest.main()
