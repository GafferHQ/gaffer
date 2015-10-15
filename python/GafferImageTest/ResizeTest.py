##########################################################################
#
#  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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

import IECore

import Gaffer
import GafferTest
import GafferImage
import GafferImageTest

class ResizeTest( GafferImageTest.ImageTestCase ) :

	def testDefaultFormat( self ) :

		r = GafferImage.Resize()
		self.assertTrue( r["format"].getValue().getDisplayWindow().isEmpty() )

		f1 = GafferImage.Format( IECore.Box2i( IECore.V2i( 1, 2 ), IECore.V2i( 11, 12 ) ), 1 )
		f2 = GafferImage.Format( IECore.Box2i( IECore.V2i( 100, 200 ), IECore.V2i( 1100, 1200 ) ), 1 )

		c1 = Gaffer.Context()
		c2 = Gaffer.Context()

		GafferImage.FormatPlug.setDefaultFormat( c1, f1 )
		GafferImage.FormatPlug.setDefaultFormat( c2, f2 )

		with c1 :
			self.assertEqual( r["out"]["format"].getValue(), f1 )

		with c2 :
			self.assertEqual( r["out"]["format"].getValue(), f2 )

	def testChannelDataPassThrough( self ) :

		# Resize to the same size as the input image.
		c = GafferImage.Constant()
		c["format"].setValue( GafferImage.Format( IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( 512 ) ), 1 ) )
		c["color"].setValue( IECore.Color4f( 0.25, 0.5, 0.75, 1 ) )

		r = GafferImage.Resize()
		r["in"].setInput( c["out"] )
		r["format"].setValue( GafferImage.Format( IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( 512 ) ), 1 ) )

		# Assert that the pixel data is passed clean through.
		for channel in [ "R", "G", "B", "A" ] :
			self.assertEqual(
				c["out"].channelDataHash( channel, IECore.V2i( 0 ) ),
				r["out"].channelDataHash( channel, IECore.V2i( 0 ) ),
			)
			self.assertTrue(
				c["out"].channelData( channel, IECore.V2i( 0 ), _copy = False ).isSame(
					r["out"].channelData( channel, IECore.V2i( 0 ), _copy = False )
				)
			)

	# Tests that hashes pass through when the input data is not Flat
	def testNonFlatHashPassThrough( self ) :

		resize = GafferImage.Resize()
		resize["format"].setValue( GafferImage.Format( IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( 1024 ) ), 1 ) )

		self._testNonFlatHashPassThrough( resize )


	def testFit( self ) :

		c = GafferImage.Constant()
		c["format"].setValue( GafferImage.Format( IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( 256, 128 ) ), 1 ) )
		c["color"].setValue( IECore.Color4f( 0.25, 0.5, 0.75, 1 ) )

		r = GafferImage.Resize()
		r["in"].setInput( c["out"] )
		r["format"].setValue( GafferImage.Format( IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( 1024, 256 ) ), 1 ) )

		self.assertEqual( r["fitMode"].getValue(), r.FitMode.Horizontal )

		horizontalDataWindow = r["out"]["dataWindow"].getValue()
		displayWindow = r["format"].getValue().getDisplayWindow()

		self.assertEqual( horizontalDataWindow.min.x, displayWindow.min.x )
		self.assertEqual( horizontalDataWindow.max.x, displayWindow.max.x )
		self.assertTrue( horizontalDataWindow.min.y < displayWindow.min.y )
		self.assertTrue( horizontalDataWindow.max.y > displayWindow.max.y )

		r["fitMode"].setValue( r.FitMode.Vertical )
		verticalDataWindow = r["out"]["dataWindow"].getValue()

		self.assertTrue( verticalDataWindow.min.x > displayWindow.min.x )
		self.assertTrue( verticalDataWindow.max.x < displayWindow.max.x )
		self.assertEqual( verticalDataWindow.min.y, displayWindow.min.y )
		self.assertEqual( verticalDataWindow.max.y, displayWindow.max.y )

		r["fitMode"].setValue( r.FitMode.Fit )
		self.assertEqual( r["out"]["dataWindow"].getValue(), verticalDataWindow )

		r["fitMode"].setValue( r.FitMode.Fill )
		self.assertEqual( r["out"]["dataWindow"].getValue(), horizontalDataWindow )

		r["fitMode"].setValue( r.FitMode.Distort )
		self.assertEqual( r["out"]["dataWindow"].getValue(), displayWindow )

	def testMismatchedDataWindow( self ) :

		constant = GafferImage.Constant()
		constant["format"].setValue( GafferImage.Format( IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( 256, 256 ) ), 1 ) )

		crop = GafferImage.Crop()
		crop["in"].setInput( constant["out"] )
		crop["areaSource"].setValue( crop.AreaSource.Area )
		crop["area"].setValue( IECore.Box2i( IECore.V2i( 64 ), IECore.V2i( 128 ) ) )
		crop["affectDisplayWindow"].setValue( False )
		crop["affectDataWindow"].setValue( True )

		resize = GafferImage.Resize()
		resize["in"].setInput( crop["out"] )
		resize["format"].setValue( GafferImage.Format( IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( 512, 512 ) ), 1 ) )

		self.assertEqual(
			resize["out"]["dataWindow"].getValue(),
			IECore.Box2i( IECore.V2i( 128 ), IECore.V2i( 256 ) )
		)

	def testDataWindowRounding( self ) :

		constant = GafferImage.Constant()
		constant["format"].setValue( GafferImage.Format( IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( 200, 150 ) ), 1 ) )

		resize = GafferImage.Resize()
		resize["in"].setInput( constant["out"] )

		for width in range( 1, 2000 ) :
			resize["format"].setValue( GafferImage.Format( width, 150, 1 ) )
			dataWindow = resize["out"]["dataWindow"].getValue()
			self.assertEqual( dataWindow.min.x, 0 )
			self.assertEqual( dataWindow.max.x, width )

		resize["fitMode"].setValue( resize.FitMode.Vertical )
		for height in range( 1, 2000 ) :
			resize["format"].setValue( GafferImage.Format( 200, height, 1 ) )
			dataWindow = resize["out"]["dataWindow"].getValue()
			self.assertEqual( dataWindow.min.y, 0 )
			self.assertEqual( dataWindow.max.y, height )

	def testFilterAffectsChannelData( self ) :

		 r = GafferImage.Resize()
		 cs = GafferTest.CapturingSlot( r.plugDirtiedSignal() )
		 r["filter"].setValue( "gaussian" )

		 self.assertTrue( r["out"]["channelData"] in set( c[0] for c in cs ) )

	def testSamplerBoundsViolationCrash( self ) :

		c = GafferImage.Constant()
		c["format"].setValue( GafferImage.Format( 3792, 3160 ) )

		r = GafferImage.Resize()
		r["in"].setInput( c["out"] )
		r["format"].setValue( GafferImage.Format( 1920, 1080 ) )
		r["fitMode"].setValue( r.FitMode.Vertical )

		r["out"].image()

	def testDownsizingSamplerBounds( self ) :

		c = GafferImage.Constant()
		c["format"].setValue( GafferImage.Format( 50, 53 ) )

		r = GafferImage.Resize()
		r["in"].setInput( c["out"] )
		r["fitMode"].setValue( r.FitMode.Distort )

		# Downsize to every single size smaller than the input,
		# to check for sampler bounds violations similar to those
		# which motivated the test above.
		for width in range( 1, 50 ) :
			for height in range( 1, 53 ) :
				r["format"].setValue( GafferImage.Format( width, height ) )
				r["out"].image()

	def testFormatDependencies( self ) :

		r = GafferImage.Resize()
		cs = GafferTest.CapturingSlot( r.plugDirtiedSignal() )

		r["format"].setValue( GafferImage.Format( 100, 200, 2 ) )
		dirtiedPlugs = set( c[0] for c in cs )

		self.assertTrue( r["out"]["format"] in dirtiedPlugs )
		self.assertTrue( r["out"]["dataWindow"] in dirtiedPlugs )

	def testDisable( self ) :

		c = GafferImage.Constant()
		c["format"].setValue( GafferImage.Format( 100, 100 ) )

		r = GafferImage.Resize()
		r["in"].setInput( c["out"] )
		r["format"].setValue( GafferImage.Format( 200, 200 ) )

		self.assertEqual( r["out"]["format"].getValue(), GafferImage.Format( 200, 200 ) )
		self.assertEqual( r["out"]["dataWindow"].getValue(), IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( 200 ) ) )

		r["enabled"].setValue( False )
		self.assertEqual( r["out"]["format"].getValue(), GafferImage.Format( 100, 100 ) )
		self.assertEqual( r["out"]["dataWindow"].getValue(), IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( 100 ) ) )

	def testEmptyDataWindow( self ) :

		e = self.emptyImage()

		r = GafferImage.Resize()
		r["in"].setInput( e["out"] )
		r["format"].setValue( GafferImage.Format( 2121, 1012 ) )

		self.assertEqual( r["out"]["dataWindow"].getValue(), IECore.Box2i() )

if __name__ == "__main__":
	unittest.main()
