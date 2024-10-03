##########################################################################
#
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

import imath
import math

import IECore
import IECoreImage

import Gaffer
import GafferTest
import GafferImage
import GafferImageTest

class ImageSamplerTest( GafferImageTest.ImageTestCase ) :

	def test( self ) :

		window = imath.Box2i( imath.V2i( -75 ), imath.V2i( 300 ) )

		xRamp = GafferImage.Ramp()
		xRamp["format"].setValue( GafferImage.Format( window ) )
		xRamp["startPosition"].setValue( imath.V2f( window.min().x, 0 ) )
		xRamp["endPosition"].setValue( imath.V2f( window.max().x, 0 ) )
		xRamp["ramp"]["p0"]["y"].setValue( imath.Color4f( window.min().x, 0, 0, 0 ) )
		xRamp["ramp"]["p1"]["y"].setValue( imath.Color4f( window.max().x, 0, 0, 0 ) )
		yRamp = GafferImage.Ramp()
		yRamp["format"].setValue( GafferImage.Format( window ) )
		yRamp["startPosition"].setValue( imath.V2f( 0, window.min().y ) )
		yRamp["endPosition"].setValue( imath.V2f( 0, window.max().y ) )
		yRamp["ramp"]["p0"]["y"].setValue( imath.Color4f( 0, window.min().y, 0, 0 ) )
		yRamp["ramp"]["p1"]["y"].setValue( imath.Color4f( 0, window.max().y, 0, 0 ) )

		rampMerge = GafferImage.Merge()
		rampMerge["operation"].setValue( GafferImage.Merge.Operation.Add )
		rampMerge["in"]["in0"].setInput( xRamp["out"] )
		rampMerge["in"]["in1"].setInput( yRamp["out"] )

		sampler = GafferImage.ImageSampler()
		sampler["image"].setInput( rampMerge["out"] )

		hashes = set()
		count = 0
		for px in list( range( -10, 10 ) ) + list( range( -75, -10, 7 ) ) + list( range( 10, 300, 17 ) ):
			for py in list( range( -10, 10 ) ) + list( range( -75, -10, 7 ) ) + list( range( 10, 300, 17 ) ):
				sampler["interpolate"].setValue( True )
				for ox in [ 0, 0.25, 0.5, 0.75 ]:
					for oy in [ 0, 0.25, 0.5, 0.75 ]:
						x = px + ox
						y = py + oy

						if x < -74.5 or y < -74.5 or x > 299.5 or y > 299.5:
							# Border pixels blend to zero, and don't match the linear gradient
							continue

						sampler["pixel"].setValue( imath.V2f( x, y ) )

						c = sampler["color"].getValue()
						for i in range( 4 ):
							self.assertAlmostEqual( c[i], [ x, y, 0, 0 ][i], places = 3 )
						hashes.add( str( sampler["color"].hash() ) )
						count += 1

				sampler["pixel"].setValue( imath.V2f( px + 0.5, py + 0.5 ) )
				centerColor = sampler["color"].getValue()

				sampler["interpolate"].setValue( False )

				for ox in [ 0, 0.25, 0.5, 0.75 ]:
					for oy in [ 0, 0.25, 0.5, 0.75 ]:
						x = px + ox
						y = py + oy

						sampler["pixel"].setValue( imath.V2f( x, y ) )
						self.assertEqual( centerColor, sampler["color"].getValue() )

		self.assertEqual( len( hashes ), count )

	def testChannelsPlug( self ) :

		constant = GafferImage.Constant()
		constant["layer"].setValue( "diffuse" )
		constant["color"].setValue( imath.Color4f( 1, 0.5, 0.25, 1 ) )

		sampler = GafferImage.ImageSampler()
		sampler["image"].setInput( constant["out"] )
		sampler["pixel"].setValue( imath.V2f( 10.5 ) )
		self.assertEqual( sampler["color"].getValue(), imath.Color4f( 0, 0, 0, 0 ) )

		sampler["channels"].setValue( IECore.StringVectorData( [ "diffuse.R", "diffuse.G", "diffuse.B", "diffuse.A" ] ) )
		self.assertEqual( sampler["color"].getValue(), imath.Color4f( 1, 0.5, 0.25, 1 ) )

	def testView( self ) :

		constantSource = GafferImage.Constant()
		constantSource["color"].setValue( imath.Color4f( 0.1, 0.2, 0.3, 0.4 ) )

		reader = GafferImage.ImageReader()
		reader["fileName"].setValue( self.imagesPath() / "blueWithDataWindow.100x100.exr" )

		views = GafferImage.CreateViews()
		views["views"].resize( 2 )
		views["views"][0]["name"].setValue( "left" )
		views["views"][1]["name"].setValue( "right" )
		views["views"][0]["value"].setInput( constantSource["out"] )
		views["views"][1]["value"].setInput( reader["out"] )

		sampler = GafferImage.ImageSampler()
		sampler["image"].setInput( views["out"] )
		sampler["pixel"].setValue( imath.V2f( 50.5 ) )

		for contextView, queryAndResults in [
			( None, [ ( "", None ), ( "left", imath.Color4f( 0.1, 0.2, 0.3, 0.4 ) ), ( "right", imath.Color4f( 0, 0, 0.5, 0.5 ) ) ] ),
			( "left", [ ( "", imath.Color4f( 0.1, 0.2, 0.3, 0.4 ) ), ( "left", imath.Color4f( 0.1, 0.2, 0.3, 0.4 ) ), ( "right", imath.Color4f( 0, 0, 0.5, 0.5 ) ) ] ),
			("right", [ ( "", imath.Color4f( 0, 0, 0.5, 0.5 ) ), ( "left", imath.Color4f( 0.1, 0.2, 0.3, 0.4 ) ), ( "right", imath.Color4f( 0, 0, 0.5, 0.5 ) ) ] )

		]:
			for queryView, result in queryAndResults:
				with Gaffer.Context( Gaffer.Context.current() ) as c:
					sampler["view"].setValue( queryView )
					if contextView:
						c["image:viewName"] = contextView

					if result is None:
						# The result when contextView and queryView are both not overridden is an error,
						# views has just left and right views, so it's illegal to ask for "default".
						with self.assertRaisesRegex( Gaffer.ProcessException, 'View does not exist "default"' ):
							sampler["color"].getValue()
					else:
						self.assertEqual( sampler["color"].getValue(), result )

		# When reading from an image with a default view, we get the default when requesting a view that
		# doesn't exist
		sampler["image"].setInput( reader["out"] )
		sampler["view"].setValue( "left" )
		self.assertEqual( sampler["color"].getValue(), imath.Color4f( 0, 0, 0.5, 0.5 ) )
		sampler["view"].setValue( "right" )
		self.assertEqual( sampler["color"].getValue(), imath.Color4f( 0, 0, 0.5, 0.5 ) )

	def testExceptionalValues( self ) :

		c = GafferImage.Constant()
		c["color"].setValue( imath.Color4f( 1 ) )

		inf = GafferImage.Grade()
		inf["in"].setInput( c["out"] )
		inf["multiply"].setValue( imath.Color4f( float( "inf" ) ) )
		inf["offset"].setValue( imath.Color4f( float( "inf" ) ) )
		inf["blackClamp"].setValue( False )

		sampler = GafferImage.ImageSampler()
		sampler["image"].setInput( inf["out"] )
		sampler["pixel"].setValue( imath.V2f( 0 ) )

		self.assertEqual( sampler["color"].getValue()[0], float( "inf" ) )

		inf["multiply"].setValue( imath.Color4f( -float( "inf" ) ) )
		inf["offset"].setValue( imath.Color4f( -float( "inf" ) ) )
		self.assertEqual( sampler["color"].getValue()[0], -float( "inf" ) )

		inf["multiply"].setValue( imath.Color4f( float( "nan" ) ) )
		self.assertTrue( math.isnan( sampler["color"].getValue()[0] ) )


if __name__ == "__main__":
	unittest.main()
