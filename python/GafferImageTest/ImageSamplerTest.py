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
import os

import IECore
import IECoreImage

import Gaffer
import GafferTest
import GafferImage
import GafferImageTest

class ImageSamplerTest( GafferImageTest.ImageTestCase ) :

	def test( self ) :

		xRamp = GafferImage.Ramp()
		xRamp["format"].setValue( GafferImage.Format( 75, 75, 1.000 ) )
		xRamp["endPosition"].setValue( imath.V2f( 75, 0 ) )
		xRamp["ramp"]["p1"]["y"].setValue( imath.Color4f( 75, 0, 0, 0 ) )
		yRamp = GafferImage.Ramp()
		yRamp["format"].setValue( GafferImage.Format( 75, 75, 1.000 ) )
		yRamp["endPosition"].setValue( imath.V2f( 0, 75 ) )
		yRamp["ramp"]["p1"]["y"].setValue( imath.Color4f( 0, 75, 0, 0 ) )

		rampMerge = GafferImage.Merge()
		rampMerge["operation"].setValue( GafferImage.Merge.Operation.Add )
		rampMerge["in"]["in0"].setInput( xRamp["out"] )
		rampMerge["in"]["in1"].setInput( yRamp["out"] )

		sampler = GafferImage.ImageSampler()
		sampler["image"].setInput( rampMerge["out"] )

		hashes = set()
		for x in range( 0, 75 ) :
			for y in range( 0, 75 ) :
				sampler["pixel"].setValue( imath.V2f( x + 0.5, y + 0.5 ) )

				c = sampler["color"].getValue()
				for i in range( 4 ):
					self.assertAlmostEqual( c[i], [ x + 0.5, y + 0.5, 0, 0 ][i], places = 4 )
				hashes.add( str( sampler["color"].hash() ) )

		self.assertEqual( len( hashes ), 75 * 75 )

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
		reader["fileName"].setValue( os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/blueWithDataWindow.100x100.exr" ) )

		views = GafferImage.CreateViews()
		views["views"].addChild( Gaffer.NameValuePlug( "left", GafferImage.ImagePlug(), True ) )
		views["views"].addChild( Gaffer.NameValuePlug( "right", GafferImage.ImagePlug(), True ) )
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

if __name__ == "__main__":
	unittest.main()
