##########################################################################
#
#  Copyright (c) 2026, Cinesite VFX Ltd. All rights reserved.
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
#      * Neither the name of  Image Engine Design Inc nor the names of
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

import math

import imath

import IECore
import IECoreScene

import GafferScene
import GafferSceneTest

class QuantizePrimitiveVariablesTest( GafferSceneTest.SceneTestCase ) :

	def testNumericTypes( self ) :

		points = IECoreScene.PointsPrimitive( 0 )
		points["float"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Constant, IECore.FloatData( 0.1 )
		)
		points["int"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Constant, IECore.IntData( 5 )
		)
		points["v2i"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Constant, IECore.V2iData( imath.V2i( 20, 35 ) )
		)
		points["v3i"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Constant, IECore.V3iData( imath.V3i( -10, 101, 5 ) )
		)
		points["v2f"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Constant, IECore.V2fData( imath.V2f( 20.2, 350.1 ) )
		)
		points["v3f"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Constant, IECore.V3fData( imath.V3f( -10.5, 101.2, 50 ) )
		)
		points["color3f"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Constant, IECore.Color3fData( imath.Color3f( 99, 1, 505 ) )
		)
		points["floatArray"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Constant, IECore.FloatVectorData( [ 0.1, 0.4, 5.1 ] )
		)
		points["intArray"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Constant, IECore.IntVectorData( [ 3, 4, 5 ] )
		)
		points["v2iArray"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Constant, IECore.V2iVectorData( [ imath.V2i( 1, 2 ), imath.V2i( 4, 5 ) ] )
		)
		points["v3iArray"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Constant, IECore.V3iVectorData( [ imath.V3i( 1, 2, 3 ), imath.V3i( 4, 5, 6 ) ] )
		)
		points["v2fArray"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Constant, IECore.V2fVectorData( [ imath.V2f( 111, 112 ), imath.V2f( 114, 115 ) ] )
		)
		points["v3fArray"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Constant, IECore.V3fVectorData( [ imath.V3f( 1, 2, 3 ), imath.V3f( 4, 5, 6 ) ] )
		)
		points["color3fArray"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Constant, IECore.Color3fVectorData( [ imath.Color3f( -1, -2, -3 ), imath.Color3f( -4, -5, -6 ) ] )
		)

		objectToScene = GafferScene.ObjectToScene()
		objectToScene["object"].setValue( points )

		objectFilter = GafferScene.PathFilter()
		objectFilter["paths"].setValue( IECore.StringVectorData( [ "/object" ] ) )

		quantize = GafferScene.QuantizePrimitiveVariables()
		quantize["in"].setInput( objectToScene["out"] )
		quantize["filter"].setInput( objectFilter["out"] )
		quantize["names"].setValue( "*" )
		quantize["quantization"].setValue( 4 )

		points = quantize["out"].object( "/object" )
		self.assertEqual( points["float"].data, IECore.FloatData( 0 ) )
		self.assertEqual( points["int"].data, IECore.IntData( 4 ) )
		self.assertEqual( points["v2i"].data, IECore.V2iData( imath.V2i( 20, 36 ) ) )
		self.assertEqual( points["v3i"].data, IECore.V3iData( imath.V3i( -8, 100, 4 ) ) )
		self.assertEqual( points["v2f"].data, IECore.V2fData( imath.V2f( 20, 352 ) ) )
		self.assertEqual( points["v3f"].data, IECore.V3fData( imath.V3f( -12, 100, 52 ) ) )
		self.assertEqual( points["color3f"].data, IECore.Color3fData( imath.Color3f( 100, 0, 504 ) ) )
		self.assertEqual( points["floatArray"].data, IECore.FloatVectorData( [ 0, 0, 4 ] ) )
		self.assertEqual( points["intArray"].data, IECore.IntVectorData( [ 4, 4, 4 ] ) )
		self.assertEqual( points["v2iArray"].data, IECore.V2iVectorData( [ imath.V2i( 0, 4 ), imath.V2i( 4, 4 ) ] ) )
		self.assertEqual( points["v3iArray"].data, IECore.V3iVectorData( [ imath.V3i( 0, 4, 4 ), imath.V3i( 4, 4, 8 ) ] ) )
		self.assertEqual( points["v2fArray"].data, IECore.V2fVectorData( [ imath.V2f( 112, 112 ), imath.V2f( 116, 116 ) ] ) )
		self.assertEqual( points["v3fArray"].data, IECore.V3fVectorData( [ imath.V3f( 0, 4, 4 ), imath.V3f( 4, 4, 8 ) ] ) )
		self.assertEqual( points["color3fArray"].data, IECore.Color3fVectorData( [ imath.Color3f( 0, -4, -4 ), imath.Color3f( -4, -4, -8 ) ] ) )

	def testNonNumericTypesPassThrough( self ) :

		points = IECoreScene.PointsPrimitive( 0 )
		points["string"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Constant, IECore.StringData( "Hello" )
		)
		points["stringArray"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Constant, IECore.StringVectorData( [ "Hello" ] )
		)

		objectToScene = GafferScene.ObjectToScene()
		objectToScene["object"].setValue( points )

		objectFilter = GafferScene.PathFilter()
		objectFilter["paths"].setValue( IECore.StringVectorData( [ "/object" ] ) )

		quantize = GafferScene.QuantizePrimitiveVariables()
		quantize["in"].setInput( objectToScene["out"] )
		quantize["filter"].setInput( objectFilter["out"] )
		quantize["names"].setValue( "string*" )
		quantize["quantization"].setValue( 4 )

		self.assertEqual( quantize["out"].object( "/object" ), quantize["in"].object( "/object" ) )

	def testNegativeZero( self ) :

		points = IECoreScene.PointsPrimitive( 0 )
		points["float"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Constant, IECore.FloatData( -0.1 )
		)

		objectToScene = GafferScene.ObjectToScene()
		objectToScene["object"].setValue( points )

		objectFilter = GafferScene.PathFilter()
		objectFilter["paths"].setValue( IECore.StringVectorData( [ "/object" ] ) )

		quantize = GafferScene.QuantizePrimitiveVariables()
		quantize["in"].setInput( objectToScene["out"] )
		quantize["filter"].setInput( objectFilter["out"] )
		quantize["names"].setValue( "*" )
		quantize["quantization"].setValue( 0.5 )

		points = quantize["out"].object( "/object" )
		self.assertEqual( points["float"].data.value, 0.0 )
		self.assertEqual( math.copysign( 1,  points["float"].data.value ), 1 )

	def testPassThroughForZeroQuantization( self ) :

		points = IECoreScene.PointsPrimitive( 0 )
		points["float"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Constant, IECore.FloatData( -0.1 )
		)

		objectToScene = GafferScene.ObjectToScene()
		objectToScene["object"].setValue( points )

		objectFilter = GafferScene.PathFilter()
		objectFilter["paths"].setValue( IECore.StringVectorData( [ "/object" ] ) )

		quantize = GafferScene.QuantizePrimitiveVariables()
		quantize["in"].setInput( objectToScene["out"] )
		quantize["filter"].setInput( objectFilter["out"] )
		quantize["names"].setValue( "*" )
		self.assertEqual( quantize["quantization"].getValue(), 0 )

		self.assertScenesEqual( quantize["out"], quantize["in"] )
		self.assertSceneHashesEqual( quantize["out"], quantize["in"] )
