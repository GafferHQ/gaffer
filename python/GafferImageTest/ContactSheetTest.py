##########################################################################
#
#  Copyright (c) 2024, John Haddon. All rights reserved.
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

import IECore

import Gaffer
import GafferImage
import GafferImageTest

class ContactSheetTest( GafferImageTest.ImageTestCase ) :

	def testNumTiles( self ) :

		constant = GafferImage.Constant()

		contactSheet = GafferImage.ContactSheet()
		contactSheet["in"][0].setInput( constant["out"] )
		contactSheet["mode"].setValue( 1 ) # Sequence
		contactSheet["frames"].setValue( "1-10" )

		# We should generate one tile per frame in Automatic mode.
		self.assertEqual( len( contactSheet["ContactSheetCore"]["tiles"].getValue() ), 10 )

		# In Custom mode, we should never generate more than either
		# the number of tiles requested or the number of frames.
		contactSheet["divisionsMode"].setValue( 1 ) # Custom
		self.assertEqual( len( contactSheet["ContactSheetCore"]["tiles"].getValue() ), 9 )
		contactSheet["divisions"].setValue( imath.V2i( 100, 100 ) )
		self.assertEqual( len( contactSheet["ContactSheetCore"]["tiles"].getValue() ), 10 )

	def testAutomaticDivisionsWithOneTile( self ) :

		constant = GafferImage.Constant()
		contactSheet = GafferImage.ContactSheet()
		contactSheet["in"][0].setInput( constant["out"] )

		for margins in [ 0, 50 ] :
			with self.subTest( margins = margins ) :
				for side in [ "Left", "Right", "Top", "Bottom" ] :
					contactSheet[f"margin{side}"].setValue( margins )
				self.assertEqual( len( contactSheet["ContactSheetCore"]["tiles"].getValue() ), 1 )
				self.assertEqual(
					contactSheet["ContactSheetCore"]["tiles"].getValue()[0].center(),
					imath.V2f( contactSheet["out"].format().getDisplayWindow().center() )
				)

	def testInitialNumInputs( self ) :

		# We want just a single input by default, with more appearing
		# when the user connects additional plugs. This can get messed up
		# if there is a connection to the box in ContactSheet.gfr at the
		# point it is exported.
		contactSheet = GafferImage.ContactSheet()
		self.assertEqual( len( contactSheet["in"] ), 1 )

	def testUpstreamContext( self ) :

		# Check that none of the ContactSheet's internal context variables
		# leak out into the upstream graph.

		constant = GafferImage.Constant()

		contactSheet = GafferImage.ContactSheet()
		contactSheet["in"][0].setInput( constant["out"] )

		with Gaffer.ContextMonitor( constant["out"] ) as monitor :
			GafferImage.ImageAlgo.tiles( contactSheet["out"] )

		self.assertEqual(
			set( monitor.combinedStatistics().variableNames() ),
			{
				"image:channelName", "image:viewName", "image:tileOrigin", "frame", "framesPerSecond"
			}
		)

	def testNoInputs( self ) :

		# Here we're just testing that the internal expression don't
		# error if `numTiles == 0`. It's quite easy to get into division
		# by zero problems in this case.
		contactSheet = GafferImage.ContactSheet()
		GafferImage.ImageAlgo.tiles( contactSheet["out"] )

	def testTallTiles( self ) :

		constant = GafferImage.Constant()
		constant["format"].setValue( GafferImage.Format( 10, 100 ) )

		contactSheet = GafferImage.ContactSheet()
		contactSheet["in"][0].setInput( constant["out"] )
		contactSheet["format"].setValue( GafferImage.Format( 100, 100 ) )
		contactSheet["mode"].setValue( 1 ) # Sequence

		# Up to 20 tiles, our best fit is to put them all on one row.
		# At 10 tiles we perfectly fill the output image, and then up to
		# 20 we need vertical padding, but still less than we'd have if
		# we created a second row.

		for numTiles in range( 1, 21 ) :
			with self.subTest( numTiles = numTiles ) :
				contactSheet["frames"].setValue( f"1-{numTiles}" )
				self.assertEqual( contactSheet["outDivisions"].getValue(), imath.V2i( numTiles, 1 ) )
				tiles = contactSheet["ContactSheetCore"]["tiles"].getValue()
				self.assertEqual( len( tiles ), numTiles )
				self.assertEqual(
					len( { t.min().y for t in tiles } ), 1
				)

		# Between 20 and 40 tiles, we need two rows, culminating in a perfect.
		# fit at 40.

		for numTiles in range( 21, 41 ) :
			with self.subTest( numTiles = numTiles ) :
				contactSheet["frames"].setValue( f"1-{numTiles}" )
				self.assertEqual( contactSheet["outDivisions"].getValue(), imath.V2i( 20, 2 ) )
				tiles = contactSheet["ContactSheetCore"]["tiles"].getValue()
				self.assertEqual( len( tiles ), numTiles )
				self.assertEqual(
					len( { t.min().y for t in tiles } ), 2
				)
				self.assertEqual(
					sum( [ t.size().x * t.size().y for t in tiles ] ),
					numTiles * 5 * 50
				)

if __name__ == "__main__":
	unittest.main()
