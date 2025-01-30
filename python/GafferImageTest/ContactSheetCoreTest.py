##########################################################################
#
#  Copyright (c) 2023, John Haddon. All rights reserved.
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

class ContactSheetCoreTest( GafferImageTest.ImageTestCase ) :

	def testSingleTileCoverage( self ) :

		constant = GafferImage.Constant()
		constant["format"].setValue( GafferImage.Format( 300, 200 ) )
		constant["color"].setValue( imath.Color4f( 1, 1, 1, 1 ) )

		contactSheet = GafferImage.ContactSheetCore()
		contactSheet["in"].setInput( constant["out"] )
		contactSheet["format"].setValue( GafferImage.Format( 300, 200 ) )
		contactSheet["tiles"].setValue(
			IECore.Box2fVectorData( [
				imath.Box2f( imath.V2f( 0 ), imath.V2f( 300, 200 ) )
			] )
		)

		self.assertImagesEqual(
			contactSheet["out"], constant["out"], maxDifference = 0.00001
		)

	def testTilesOutsideDisplayWindow( self ) :

		whiteConstant = GafferImage.Constant()
		whiteConstant["color"].setValue( imath.Color4f( 1, 1, 1, 1 ) )

		contactSheet = GafferImage.ContactSheetCore()
		contactSheet["in"].setInput( whiteConstant["out"] )
		contactSheet["format"].setValue( GafferImage.Format( 100, 100 ) )
		contactSheet["tiles"].setValue(
			IECore.Box2fVectorData( [
				imath.Box2f( imath.V2f( 200 ), imath.V2f( 300 ) )
			] )
		)

		blackConstant = GafferImage.Constant()
		blackConstant["color"].setValue( imath.Color4f( 0, 0, 0, 0 ) )
		blackConstant["format"].setInput( contactSheet["format"] )
		self.assertImagesEqual( contactSheet["out"], blackConstant["out"] )

	def testNoInvalidChannelAccesses( self ) :

		checker = GafferImage.Checkerboard()

		shuffledChecker = GafferImage.Shuffle()
		shuffledChecker["shuffles"].addChild(
			Gaffer.ShufflePlug( "R", "Z", deleteSource = True )
		)

		tileIndexQuery = Gaffer.ContextQuery()
		tileIndexQuery.addQuery( Gaffer.IntPlug(), "contactSheet:tileIndex" )

		tileSwitch = Gaffer.Switch()
		tileSwitch.setup( checker["out"] )
		tileSwitch["in"][0].setInput( checker["out"] )
		tileSwitch["in"][1].setInput( shuffledChecker["out"] )
		tileSwitch["index"].setInput( tileIndexQuery["out"][0]["value"] )

		contactSheet = GafferImage.ContactSheetCore()
		contactSheet["in"].setInput( tileSwitch["out"] )
		contactSheet["tiles"].setValue(
			IECore.Box2fVectorData( [
				imath.Box2f( imath.V2f( 0 ), imath.V2f( 10 ) ),
				imath.Box2f( imath.V2f( 10 ), imath.V2f( 20 ) ),
			] )
		)

		# ContactSheet outputs the union of all input channels
		self.assertEqual(
			contactSheet["out"].channelNames(),
			IECore.StringVectorData( "RGBAZ" )
		)

		# And needs to be careful not to pull on channels that
		# are missing in a particular input. This call would throw
		# if it wasn't.
		GafferImage.ImageAlgo.tiles( contactSheet["out"] )

	def testNoInvalidViewAccesses( self ) :

		checker = GafferImage.Checkerboard()
		createViews = GafferImage.CreateViews()
		createViews["views"].resize( 1 )
		createViews["views"][0]["value"].setInput( checker["out"] )
		createViews["views"][0]["name"].setValue( "left" )
		self.assertEqual( createViews["out"].viewNames(), IECore.StringVectorData( [ "left" ] ) )

		contactSheet = GafferImage.ContactSheetCore()
		contactSheet["in"].setInput( createViews["out"] )
		contactSheet["tiles"].setValue(
			IECore.Box2fVectorData( [
				imath.Box2f( imath.V2f( 0 ), imath.V2f( 10 ) ),
			] )
		)

		# The ContactSheet always outputs the `default` view, and only
		# pulls on matching views from the input. So the result should
		# be an empty image.

		self.assertEqual( contactSheet["out"].channelNames(), IECore.StringVectorData() )

		# Now add a second tile, which provides the `default` view.

		tileIndexQuery = Gaffer.ContextQuery()
		tileIndexQuery.addQuery( Gaffer.IntPlug(), "contactSheet:tileIndex" )

		tileSwitch = Gaffer.Switch()
		tileSwitch.setup( createViews["out"] )
		tileSwitch["in"][0].setInput( createViews["out"] )
		tileSwitch["in"][1].setInput( checker["out"] )
		tileSwitch["index"].setInput( tileIndexQuery["out"][0]["value"] )

		contactSheet["in"].setInput( tileSwitch["out"] )
		contactSheet["tiles"].setValue(
			IECore.Box2fVectorData( [
				imath.Box2f( imath.V2f( 0 ), imath.V2f( 10 ) ),
				imath.Box2f( imath.V2f( 20 ), imath.V2f( 30 ) ),
			] )
		)

		# This should give us an image with valid channels, courtesy
		# of the second tile.

		self.assertEqual( contactSheet["out"].channelNames(), checker["out"].channelNames() )

		# But we must still be careful that querying channelData doesn't
		# cause us to access the other tile, which doesn't have a matching view.

		GafferImage.ImageAlgo.tiles( contactSheet["out"] )

	def testOverscanIgnored( self ) :

		# Pure green and pure red checkers

		checker = GafferImage.Checkerboard()
		checker["format"].setValue( GafferImage.Format( 400, 400 ) )
		checker["colorA"].setValue( imath.Color4f( 1, 0, 0, 1 ) )
		checker["colorB"].setValue( imath.Color4f( 0, 1, 0, 1 ) )
		checker["size"].setValue( imath.V2f( 50 ) )

		displayWindowStats = GafferImage.ImageStats()
		displayWindowStats["in"].setInput( checker["out"] )
		displayWindowStats["areaSource"].setValue( displayWindowStats.AreaSource.DisplayWindow )
		self.assertEqual( displayWindowStats["average"].getValue(), imath.Color4f( 0.5, 0.5, 0, 1 ) )

		# Crop display window so that we have a single red checker
		# and then lots of red and green checkers left over in the
		# overscanned data window.

		crop = GafferImage.Crop()
		crop["in"].setInput( checker["out"] )
		crop["area"].setValue( imath.Box2i( imath.V2i( 0 ), imath.V2i( 24 ) ) )
		crop["affectDataWindow"].setValue( False )

		displayWindowStats["in"].setInput( crop["out"] )
		self.assertEqual( displayWindowStats["average"].getValue(), imath.Color4f( 1, 0, 0, 1 ) )

		# ContactSheetCore with a single tile containing that red checker,
		# placed in the centre of the image with plenty of space around it.

		contactSheet = GafferImage.ContactSheetCore()
		contactSheet["in"].setInput( crop["out"] )
		contactSheet["format"].setValue( GafferImage.Format( 1000, 1000 ) )
		contactSheet["tiles"].setValue( IECore.Box2fVectorData( [
			imath.Box2f( imath.V2f( 400 ), imath.V2f( 600 ) )
		] ) )

		# Contact sheets only present the area within the input's display window,
		# so there should be no green in the output, even though there is green
		# in the overscan area.

		displayWindowStats["in"].setInput( contactSheet["out"] )
		self.assertEqual( displayWindowStats["max"]["r"].getValue(), 1 )
		self.assertEqual( displayWindowStats["max"]["g"].getValue(), 0 )

	def testInFormatAffectsResampleMatrix( self ) :

		constant = GafferImage.Constant()
		constant["format"].setValue( GafferImage.Format( 300, 200 ) )
		constant["color"].setValue( imath.Color4f( 1, 1, 1, 1 ) )

		contactSheet = GafferImage.ContactSheetCore()
		contactSheet["in"].setInput( constant["out"] )
		contactSheet["format"].setValue( GafferImage.Format( 300, 200 ) )
		contactSheet["tiles"].setValue(
			IECore.Box2fVectorData( [
				imath.Box2f( imath.V2f( 0 ), imath.V2f( 300, 200 ) )
			] )
		)

		c = Gaffer.Context()
		c["contactSheet:tileIndex"] = IECore.IntData( 0 )
		with c:
			self.assertEqual( contactSheet["__resampleMatrix"].getValue(), imath.M33f((1, 0, 0), (0, 1, 0), (0, 0, 1)) )

			constant["format"].setValue( GafferImage.Format( 150, 100 ) )

			self.assertEqual( contactSheet["__resampleMatrix"].getValue(), imath.M33f((2, 0, 0), (0, 2, 0), (0, 0, 1)) )

	def testModifyFormat( self ) :

		constant = GafferImage.Constant()
		constant["format"].setValue( GafferImage.Format( 300, 200 ) )
		constant["color"].setValue( imath.Color4f( 1, 1, 1, 1 ) )

		contactSheet = GafferImage.ContactSheetCore()
		contactSheet["in"].setInput( constant["out"] )
		contactSheet["format"].setValue( GafferImage.Format( 300, 200 ) )
		contactSheet["tiles"].setValue(
			IECore.Box2fVectorData( [
				imath.Box2f( imath.V2f( 0 ), imath.V2f( 300, 200 ) )
			] )
		)

		# I don't really like that ContactSheetCore introduces a bit of resampling error even when the input
		# and output tile sizes match exactly ... it seems like there could be pretty common usages where
		# you're dealing with exact sizes, and it would be nice if there was a path that just did an Offset
		# in those cases, and didn't slightly change pixel values. Though maybe that's not really possible with
		# this API - since the tiles are specified in float, it might be hard to identify that they are intended
		# to be exact matches. Anyways, not the purpose of this test, at least this doesn't crash any more.
		self.assertImagesEqual( contactSheet["out"], constant["out"], maxDifference = 0.0000003 )

		contactSheet["format"].setValue( GafferImage.Format( 600, 400 ) )

		refBackground = GafferImage.Constant()
		refBackground["format"].setValue( GafferImage.Format( 600, 400 ) )
		refBackground["color"].setValue( imath.Color4f( 0, 0, 0, 0 ) )

		refMerge = GafferImage.Merge()
		refMerge["in"][0].setInput( refBackground["out"] )
		refMerge["in"][1].setInput( constant["out"] )

		self.assertImagesEqual( contactSheet["out"], refMerge["out"], maxDifference = 0.0000003 )

if __name__ == "__main__":
	unittest.main()
