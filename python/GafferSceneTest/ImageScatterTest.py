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

class ImageScatterTest( GafferSceneTest.SceneTestCase ) :

	def testDensity( self ) :

		constant = GafferImage.Constant()

		scatter = GafferScene.ImageScatter()
		scatter["image"].setInput( constant["out"] )

		for width in ( 100, 200, 400 ) :
			for height in ( 100, 200, 400 ) :
				for pixelAspect in ( 0.5, 1.0, 2.0 ) :
					for value in ( 0, 0.1, 0.5, 1.0 ) :
						for density in ( 0, 0.1, 0.5, 1.0, 2.0 ) :
							with self.subTest( width = width, height = height, value = value, density = density, pixelAspect = pixelAspect ) :
								constant["format"].setValue( GafferImage.Format( width, height, pixelAspect ) )
								constant["color"]["r"].setValue( value )
								scatter["density"].setValue( density )
								points = scatter["out"].object( "/points" )
								expected = width * pixelAspect * height * density * value
								self.assertAlmostEqual(
									points.numPoints, expected,
									delta = expected * 0.07
								)

	def testMissingChannels( self ) :

		constant = GafferImage.Constant()
		scatter = GafferScene.ImageScatter()
		scatter["image"].setInput( constant["out"] )

		scatter["densityChannel"].setValue( "doesNotExist" )

		with self.assertRaisesRegex( Gaffer.ProcessException, 'Density channel "doesNotExist" does not exist' ) :
			scatter["out"].object( "/points" )

		scatter["densityChannel"].setValue( "R" )
		scatter["widthChannel"].setValue( "doesNotExist" )

		with self.assertRaisesRegex( Gaffer.ProcessException, 'Width channel "doesNotExist" does not exist' ) :
			scatter["out"].object( "/points" )

	def testPrimitiveVariables( self ) :

		ramp = GafferImage.Ramp()
		ramp["format"].setValue( GafferImage.Format( 2, 3 ) )
		ramp["startPosition"].setValue( imath.V2f( 0, 0.5 ) )
		ramp["endPosition"].setValue( imath.V2f( 0, 2.5 ) )
		ramp["ramp"]["p0"]["y"]["a"].setValue( 1 ) # Solid alpha
		ramp["ramp"]["interpolation"].setValue( Gaffer.SplineDefinitionInterpolation.Linear )

		scatter = GafferScene.ImageScatter()
		scatter["image"].setInput( ramp["out"] )
		scatter["density"].setValue( 10 )
		scatter["densityChannel"].setValue( "A" )
		scatter["width"].setValue( 2.0 )
		scatter["widthChannel"].setValue( "R" )

		points = scatter["out"].object( "/points" )
		self.assertEqual( set( points.keys() ), { "P", "width" } )

		scatter["primitiveVariables"].setValue( "[RGBA]" )
		points = scatter["out"].object( "/points" )
		self.assertEqual( set( points.keys() ), { "P", "width", "Cs", "A" } )
		self.assertIsInstance( points["Cs"].data, IECore.Color3fVectorData )
		self.assertEqual( len( points["Cs"].data ), len( points["P"].data ) )
		self.assertIsInstance( points["width"].data, IECore.FloatVectorData )
		self.assertEqual( len( points["width"].data ), len( points["P"].data ) )

		for i, c in enumerate( points["Cs"].data ) :
			# Expected spline value
			y = points["P"].data[i].y
			y = (y - 0.5) / 2.0
			y = max( 0, min( y, 1 ) )
			# Should match what we sampled for `Cs`
			self.assertAlmostEqual( c[0], y, delta = 0.000001 )
			self.assertAlmostEqual( c[1], y, delta = 0.000001 )
			self.assertAlmostEqual( c[2], y, delta = 0.000001 )
			# And width should be double that
			self.assertAlmostEqual( points["width"].data[i], y * 2, delta = 0.000001 )

		self.assertEqual(
			points["A"].data,
			IECore.FloatVectorData( [ 1.0 ] * len( points["P"].data ) )
		)

	def testWidth( self ) :

		constant = GafferImage.Constant()
		constant["format"].setValue( GafferImage.Format( 1, 1 ) )
		constant["color"].setValue( imath.Color4f( 1, 0.5, 0, 1 ) )

		scatter = GafferScene.ImageScatter()
		scatter["image"].setInput( constant["out"] )

		# If no width channel is specified, we get a constant width
		# from the width plug.

		self.assertEqual(
			scatter["out"].object( "/points" )["width"],
			IECoreScene.PrimitiveVariable(
				IECoreScene.PrimitiveVariable.Interpolation.Constant,
				IECore.FloatData( 1 )
			)
		)

		scatter["width"].setValue( 0.5 )
		self.assertEqual(
			scatter["out"].object( "/points" )["width"],
			IECoreScene.PrimitiveVariable(
				IECoreScene.PrimitiveVariable.Interpolation.Constant,
				IECore.FloatData( 0.5 )
			)
		)

		# If a width channel is specified, then that should be multiplied
		# with the width from the plug.

		scatter["widthChannel"].setValue( "G" )
		points = scatter["out"].object( "/points" )
		self.assertEqual(
			points["width"],
			IECoreScene.PrimitiveVariable(
				IECoreScene.PrimitiveVariable.Interpolation.Vertex,
				IECore.FloatVectorData( [ 0.5 * 0.5 ] * points.numPoints )
			)
		)

if __name__ == "__main__":
	unittest.main()
