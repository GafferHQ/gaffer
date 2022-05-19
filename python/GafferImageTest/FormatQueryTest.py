##########################################################################
#
#  Copyright (c) 2021, Image Engine Design Inc. All rights reserved.
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
import os
import random
import six

import IECore

import Gaffer
import GafferTest
import GafferImage
import GafferImageTest

class FormatQueryTest( GafferImageTest.ImageTestCase ) :

	def test( self ) :

		constantSource = GafferImage.Constant()
		constantSource["color"].setValue( imath.Color4f( 0.1, 0.2, 0.3, 0.4 ) )

		formatQuery = GafferImage.FormatQuery()
		formatQuery["image"].setInput( constantSource["out"] )

		constantDest = GafferImage.Constant()
		constantDest["color"].setValue( imath.Color4f( 0.1, 0.2, 0.3, 0.4 ) )
		constantDest["format"].setInput( formatQuery["format"] )

		random.seed( 42 )
		for f in [
			GafferImage.Format( imath.Box2i( imath.V2i( 0 ), imath.V2i( 511 ) ), 1 ),
			GafferImage.Format( imath.Box2i( imath.V2i( 0 ), imath.V2i( 217, 716) ), 2 ),
			GafferImage.Format( imath.Box2i( imath.V2i( 0 ), imath.V2i( 3840, 2160 ) ), 1 ),
			GafferImage.Format( imath.Box2i( imath.V2i( 0 ), imath.V2i( 32544, 73427 ) ), 0.5 ),
			GafferImage.Format( imath.Box2i( imath.V2i( 10, 20 ), imath.V2i( 80, 90 ) ), 1.5 ),
			GafferImage.Format( imath.Box2i( imath.V2i( -10, -20 ), imath.V2i( 80, 90 ) ), 1 ),
			GafferImage.Format( imath.Box2i( imath.V2i( -1275, -1534 ), imath.V2i( 2422, 5475 ) ), 1 ),
			GafferImage.Format( imath.Box2i( imath.V2i( -12075, -10534 ), imath.V2i( 24202, 50475 ) ), 1 ),
			GafferImage.Format( imath.Box2i( imath.V2i( -120075, -100534 ), imath.V2i( 242002, 500475 ) ), 1 ),
			GafferImage.Format( imath.Box2i( imath.V2i( -1200075, -1000534 ), imath.V2i( 2420002, 5000475 ) ), 1 ),
		] + [
			GafferImage.Format( imath.Box2i( imath.V2i( random.randrange( -500000, 0 ), random.randrange( -500000, 0 ) ), imath.V2i( random.randrange( 0, 500000 ), random.randrange( 0, 500000 ) ) ), 1 ) for i in range( 100 )
		]:
			constantSource["format"].setValue( f )


			self.assertEqual( formatQuery["format"]["displayWindow"].getValue(), f.getDisplayWindow() )
			self.assertEqual( formatQuery["format"]["pixelAspect"].getValue(), f.getPixelAspect() )
			self.assertEqual( formatQuery["format"].getValue(), f )
			self.assertEqual( formatQuery["size"].getValue(), f.getDisplayWindow().size() )
			self.assertEqual( formatQuery["center"].getValue(), imath.V2f( ( imath.V2d( f.getDisplayWindow().min() ) + imath.V2d( f.getDisplayWindow().max() ) ) * 0.5 ) )

			# Driving a Constant using FormatQuery should produce the same image
			# ( but only check if it's not going to be too expensive )
			if f.getDisplayWindow().size()[0] * f.getDisplayWindow().size()[1] < 2000 * 2000:
				self.assertImagesEqual( constantSource["out"], constantDest["out"] )

	def testView( self ) :

		constantSource = GafferImage.Constant()
		constantSource["color"].setValue( imath.Color4f( 0.1, 0.2, 0.3, 0.4 ) )
		constantSource["format"].setValue( GafferImage.Format( imath.Box2i( imath.V2i( 0 ), imath.V2i( 512 ) ), 1 ) )

		reader = GafferImage.ImageReader()
		reader["fileName"].setValue( os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/checkerboard.100x100.exr" ) )

		views = GafferImage.CreateViews()
		views["views"].addChild( Gaffer.NameValuePlug( "left", GafferImage.ImagePlug(), True ) )
		views["views"].addChild( Gaffer.NameValuePlug( "right", GafferImage.ImagePlug(), True ) )
		views["views"][0]["value"].setInput( constantSource["out"] )
		views["views"][1]["value"].setInput( reader["out"] )

		formatQuery = GafferImage.FormatQuery()
		formatQuery["image"].setInput( views["out"] )

		for contextView, queryAndResults in [
			( None, [ ( "", None ), ( "left", imath.V2i( 512 ) ), ( "right", imath.V2i( 100 ) ) ] ),
			( "left", [ ( "", imath.V2i( 512 ) ), ( "left", imath.V2i( 512 ) ), ( "right", imath.V2i( 100 ) ) ] ),
			("right", [ ( "", imath.V2i( 100 ) ), ( "left", imath.V2i( 512 ) ), ( "right", imath.V2i( 100 ) ) ] )

		]:
			for queryView, result in queryAndResults:
				with Gaffer.Context( Gaffer.Context.current() ) as c:
					formatQuery["view"].setValue( queryView )
					if contextView:
						c["image:viewName"] = contextView

					if result is None:
						# The result when contextView and queryView are both not overridden is an error,
						# views has just left and right views, so it's illegal to ask for "default".
						with six.assertRaisesRegex( self, Gaffer.ProcessException, 'View does not exist "default"' ):
							formatQuery["format"]["displayWindow"]["max"].getValue()
					else:
						self.assertEqual( formatQuery["format"]["displayWindow"]["max"].getValue(), result )

		# When reading from an image with a default view, we get the default when requesting a view that
		# doesn't exist
		formatQuery["image"].setInput( reader["out"] )
		formatQuery["view"].setValue( "left" )
		self.assertEqual( formatQuery["format"]["displayWindow"]["max"].getValue(), imath.V2i( 100 ) )
		formatQuery["view"].setValue( "right" )
		self.assertEqual( formatQuery["format"]["displayWindow"]["max"].getValue(), imath.V2i( 100 ) )

	def testCleanContext( self ) :
		# This test checks that formatQuery removes tile origin and channel name from the context before
		# pulling on the input image format.
		# It does this by connecting to a Checkerboard, and computing the tiles, knowing that ContextSanitiser
		# will throw if there is bad variable in the context when pulling on constantSource["format"].
		# Checkerboard should actually be using a global scope for its size parameter anyway, if this is fixed,
		# this test will no longer do anything.  ( I think it's vaguely plausible that in the long run we might
		# end up in a situation where everything that could connect to QueryFormat handles the context pruning
		# itself, and it becomes unnecessary for QueryFormat to prune, but John disagrees )
		constantSource = GafferImage.Constant()
		constantSource["color"].setValue( imath.Color4f( 0.1, 0.2, 0.3, 0.4 ) )

		formatQuery = GafferImage.FormatQuery()
		formatQuery["image"].setInput( constantSource["out"] )

		checkerBoard = GafferImage.Checkerboard()
		checkerBoard["size"].setInput( formatQuery["size"] )

		GafferImage.ImageAlgo.tiles( checkerBoard["out"] )

if __name__ == "__main__":
	unittest.main()
