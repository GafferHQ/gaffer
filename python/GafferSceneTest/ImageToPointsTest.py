##########################################################################
#
#  Copyright (c) 2023, Cinesite VFX Ltd. All rights reserved.
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
import IECoreScene

import Gaffer
import GafferImage
import GafferScene
import GafferSceneTest

class ImageToPointsTest( GafferSceneTest.SceneTestCase ) :

	def testPixelPositions( self ) :

		image = GafferImage.Constant()
		image["format"].setValue( GafferImage.Format( 2, 3 ) )

		imageToPoints = GafferScene.ImageToPoints()
		imageToPoints["image"].setInput( image["out"] )

		points = imageToPoints["out"].object( "/points" )
		self.assertEqual( points.numPoints, 6 )
		self.assertTrue( points.arePrimitiveVariablesValid() )

		# Positions should match the pixel centres, output in
		# image buffer order, bottom to top.

		self.assertEqual(
			points["P"].data,
			IECore.V3fVectorData( [
				imath.V3f( 0.5, 0.5, 0 ), imath.V3f( 1.5, 0.5, 0 ),
				imath.V3f( 0.5, 1.5, 0 ), imath.V3f( 1.5, 1.5, 0 ),
				imath.V3f( 0.5, 2.5, 0 ), imath.V3f( 1.5, 2.5, 0 ),
			] )
		)

		# And should take pixel aspect into account.

		image["format"].setValue( GafferImage.Format( 2, 3, 2 ) )
		points = imageToPoints["out"].object( "/points" )
		self.assertEqual(
			points["P"].data,
			IECore.V3fVectorData( [
				imath.V3f( 1, 0.5, 0 ), imath.V3f( 3, 0.5, 0 ),
				imath.V3f( 1, 1.5, 0 ), imath.V3f( 3, 1.5, 0 ),
				imath.V3f( 1, 2.5, 0 ), imath.V3f( 3, 2.5, 0 ),
			] )
		)

	def testCustomPositions( self ) :

		ramp = GafferImage.Ramp()
		ramp["format"].setValue( GafferImage.Format( 2, 3 ) )
		ramp["startPosition"].setValue( imath.V2f( 0, 0.5 ) )
		ramp["endPosition"].setValue( imath.V2f( 0, 2.5 ) )

		imageToPoints = GafferScene.ImageToPoints()
		imageToPoints["image"].setInput( ramp["out"] )
		imageToPoints["position"].setValue( IECore.StringVectorData( [ "R", "G", "B" ] ) )

		# Positions should come from ramp values. We need to allow a small delta in
		# the comparisons to account for imprecision in the Ramp output.

		points = imageToPoints["out"].object( "/points" )
		self.assertEqual( points.numPoints, 6 )
		self.assertTrue( points.arePrimitiveVariablesValid() )

		for p in points["P"].data[0:2] :
			self.assertTrue( p.equalWithAbsError( imath.V3f( 0 ), 0.000001 ) )
		for p in points["P"].data[2:4] :
			self.assertTrue( p.equalWithAbsError( imath.V3f( 0.5 ), 0.000001 ) )
		for p in points["P"].data[4:6] :
			self.assertTrue( p.equalWithAbsError( imath.V3f( 1 ), 0.000001 ) )

		# Output should not be affected by pixel aspect

		pointsHash = imageToPoints["out"].objectHash( "/points" )
		ramp["format"].setValue( GafferImage.Format( 2, 3, 2 ) )
		self.assertEqual( imageToPoints["out"].objectHash( "/points" ), pointsHash )
		self.assertEqual( imageToPoints["out"].object( "/points" ), points )

	def testMissingPositions( self ) :

		imageToPoints = GafferScene.ImageToPoints()
		imageToPoints["position"].setValue( IECore.StringVectorData( [ "R", "G", "B" ] ) )

		with self.assertRaisesRegex( Gaffer.ProcessException, "Position channels are missing from the input image" ) :
			imageToPoints["out"].object( "points" )

	def testPrimitiveVariables( self ) :

		ramp = GafferImage.Ramp()
		ramp["format"].setValue( GafferImage.Format( 1, 2 ) )
		ramp["startPosition"].setValue( imath.V2f( 0, 0.5 ) )
		ramp["endPosition"].setValue( imath.V2f( 0, 1.5 ) )

		rampStart = imath.Color4f( 1, 0.5, 0, 1 )
		rampEnd =  imath.Color4f( 0, 0.5, 1, 1 )
		ramp["ramp"].setValue(
			Gaffer.SplineDefinitionfColor4f(
				(
					( 0, rampStart ),
					( 1, rampEnd ),
				), Gaffer.SplineDefinitionInterpolation.Constant
			)
		)

		shuffle = GafferImage.Shuffle()
		shuffle["in"].setInput( ramp["out"] )
		shuffle["channels"].addChild( shuffle.ChannelPlug( "diffuse.R", "B" ) )
		shuffle["channels"].addChild( shuffle.ChannelPlug( "diffuse.G", "G" ) )
		shuffle["channels"].addChild( shuffle.ChannelPlug( "diffuse.B", "R" ) )
		shuffle["channels"].addChild( shuffle.ChannelPlug( "depth", "R" ) )
		shuffle["channels"].addChild( shuffle.ChannelPlug( "layer.specialChannel", "B" ) )

		imageToPoints = GafferScene.ImageToPoints()
		imageToPoints["image"].setInput( shuffle["out"] )

		# RGB from the default layer is mapped to `Cs`.

		points = imageToPoints["out"].object( "/points" )
		self.assertTrue( points.arePrimitiveVariablesValid() )
		self.assertEqual( set( points.keys() ), { "P", "Cs", "width" } )
		self.assertEqual( points["Cs"].data, IECore.Color3fVectorData( [
			imath.Color3f( rampStart.r, rampStart.g, rampStart.b ),
			imath.Color3f( rampEnd.r, rampEnd.g, rampEnd.b ),
		] ) )

		# RGB from other layers are mapped to a Color3f primitive variable with the same name.

		imageToPoints["primitiveVariables"].setValue( "diffuse.*" )
		points = imageToPoints["out"].object( "/points" )
		self.assertTrue( points.arePrimitiveVariablesValid() )
		self.assertEqual( set( points.keys() ), { "P", "diffuse", "width" } )
		self.assertEqual( points["diffuse"].data, IECore.Color3fVectorData( [
			imath.Color3f( rampStart.b, rampStart.g, rampStart.r ),
			imath.Color3f( rampEnd.b, rampEnd.g, rampEnd.r ),
		] ) )

		# Everything else is mapped to individual float primitive variables.

		imageToPoints["primitiveVariables"].setValue( "depth A layer.specialChannel" )
		points = imageToPoints["out"].object( "/points" )
		self.assertTrue( points.arePrimitiveVariablesValid() )
		self.assertEqual( set( points.keys() ), { "P", "depth", "A", "layer.specialChannel", "width" } )
		self.assertEqual( points["depth"].data, IECore.FloatVectorData( [ rampStart.r, rampEnd.r ] ) )
		self.assertEqual( points["A"].data, IECore.FloatVectorData( [ rampStart.a, rampEnd.a ] ) )
		self.assertEqual( points["layer.specialChannel"].data, IECore.FloatVectorData( [ rampStart.b, rampEnd.b ] ) )

	def testWidth( self ) :

		constant = GafferImage.Constant()
		constant["format"].setValue( GafferImage.Format( 1, 1 ) )
		constant["color"].setValue( imath.Color4f( 1, 0.5, 0, 1 ) )

		imageToPoints = GafferScene.ImageToPoints()
		imageToPoints["image"].setInput( constant["out"] )

		# If no width channel is specified, we get a constant width
		# from the width plug.

		self.assertEqual(
			imageToPoints["out"].object( "/points" )["width"],
			IECoreScene.PrimitiveVariable(
				IECoreScene.PrimitiveVariable.Interpolation.Constant,
				IECore.FloatData( 1 )
			)
		)

		imageToPoints["width"].setValue( 0.5 )
		self.assertEqual(
			imageToPoints["out"].object( "/points" )["width"],
			IECoreScene.PrimitiveVariable(
				IECoreScene.PrimitiveVariable.Interpolation.Constant,
				IECore.FloatData( 0.5 )
			)
		)

		# If a width channel is specified, then that should be multiplied
		# with the width from the plug.

		imageToPoints["widthChannel"].setValue( "G" )
		self.assertEqual(
			imageToPoints["out"].object( "/points" )["width"],
			IECoreScene.PrimitiveVariable(
				IECoreScene.PrimitiveVariable.Interpolation.Vertex,
				IECore.FloatVectorData( [ 0.5 * 0.5 ] )
			)
		)

	def testAlpha( self ) :

		ramp = GafferImage.Ramp()
		ramp["format"].setValue( GafferImage.Format( 1, 2 ) )
		ramp["startPosition"].setValue( imath.V2f( 0, 0.5 ) )
		ramp["endPosition"].setValue( imath.V2f( 0, 1.5 ) )

		rampStart = imath.Color4f( 1, 0.5, 0, 0 )
		rampEnd =  imath.Color4f( 0, 0.5, 1, 1 )
		ramp["ramp"].setValue(
			Gaffer.SplineDefinitionfColor4f(
				(
					( 0, rampStart ),
					( 1, rampEnd ),
				), Gaffer.SplineDefinitionInterpolation.Constant
			)
		)

		imageToPoints = GafferScene.ImageToPoints()
		imageToPoints["image"].setInput( ramp["out"] )

		points = imageToPoints["out"].object( "/points" )
		self.assertTrue( points.arePrimitiveVariablesValid() )
		self.assertEqual( points.numPoints, 2 )
		self.assertEqual( points["Cs"].data, IECore.Color3fVectorData( [
			imath.Color3f( rampStart.r, rampStart.g, rampStart.b ),
			imath.Color3f( rampEnd.r, rampEnd.g, rampEnd.b ),
		] ) )

		imageToPoints["ignoreTransparent"].setValue( True )
		points = imageToPoints["out"].object( "/points" )
		self.assertTrue( points.arePrimitiveVariablesValid() )
		self.assertEqual( points.numPoints, 1 )
		self.assertEqual( points["Cs"].data, IECore.Color3fVectorData( [
			imath.Color3f( rampEnd.r, rampEnd.g, rampEnd.b ),
		] ) )

	def testSmallerDataWindow( self ) :

		constant = GafferImage.Constant()
		constant["format"].setValue( GafferImage.Format( 2, 2 ) )

		crop = GafferImage.Crop()
		crop["in"].setInput( constant["out"] )
		crop["area"].setValue( imath.Box2i( imath.V2i( 0 ), imath.V2i( 1 ) ) )
		crop["affectDisplayWindow"].setValue( False )
		self.assertNotEqual( crop["out"].dataWindow(), crop["out"].format().getDisplayWindow() )

		imageToPoints = GafferScene.ImageToPoints()
		imageToPoints["image"].setInput( crop["out"] )

		points = imageToPoints["out"].object( "/points" )
		self.assertTrue( points.arePrimitiveVariablesValid() )
		self.assertEqual( points.numPoints, 4 ) # Number of pixels in _display_ window
		self.assertEqual(
			points["P"].data,
			IECore.V3fVectorData( [
				imath.V3f( 0.5, 0.5, 0 ), imath.V3f( 1.5, 0.5, 0 ),
				imath.V3f( 0.5, 1.5, 0 ), imath.V3f( 1.5, 1.5, 0 ),
			] )
		)

if __name__ == "__main__":
	unittest.main()
