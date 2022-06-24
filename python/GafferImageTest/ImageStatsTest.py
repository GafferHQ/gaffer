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

import os
import unittest
import imath
import six

import IECore

import Gaffer
import GafferTest
import GafferImage
import GafferImageTest

class ImageStatsTest( GafferImageTest.ImageTestCase ) :

	__rgbFilePath = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/rgb.100x100.exr" )
	__file300PxPath = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/dotGrid.warped.exr" )

	# Test that the outputs change when different channels are selected.
	def testChannels( self ) :

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.__rgbFilePath )

		s = GafferImage.ImageStats()
		s["in"].setInput( r["out"] )
		s["area"].setValue( r["out"]["format"].getValue().getDisplayWindow() )

		s["channels"].setValue( IECore.StringVectorData( [ "", "G", "B" ] ) )
		self.__assertColour( s["average"].getValue(), imath.Color4f( 0., 0.0744, 0.1250, 0. ) )
		self.__assertColour( s["min"].getValue(), imath.Color4f( 0, 0, 0, 0. ) )
		self.__assertColour( s["max"].getValue(), imath.Color4f( 0, 0.5, 0.5, 0. ) )

		s["channels"].setValue( IECore.StringVectorData( [ "R", "", "B" ] ) )
		self.__assertColour( s["average"].getValue(), imath.Color4f( 0.0544, 0, 0.1250, 0. ) )
		self.__assertColour( s["min"].getValue(), imath.Color4f( 0, 0, 0, 0. ) )
		self.__assertColour( s["max"].getValue(), imath.Color4f( 0.5, 0, 0.5, 0. ) )

	def testDisconnectedDirty( self ) :

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.__rgbFilePath )
		s = GafferImage.ImageStats()
		s["in"].setInput( r["out"] )
		s["in"].setInput( None )

		cs = GafferTest.CapturingSlot( s.plugDirtiedSignal() )
		s["in"].setInput( r["out"] )

		dirtiedPlugs = set( [ x[0].relativeName( x[0].node() ) for x in cs ] )

		expectedPlugs = [
			'min',
			'min.r',
			'min.g',
			'min.b',
			'min.a',
			'max',
			'max.r',
			'max.g',
			'max.b',
			'max.a',
			'average',
			'average.r',
			'average.g',
			'average.b',
			'average.a',
			'in',
			'in.dataWindow',
			'in.channelNames',
			'in.format',
			'in.channelData'
		]

		for plug in expectedPlugs :
			self.assertTrue( plug in dirtiedPlugs )

	def testDisconnectHash( self ) :

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.__rgbFilePath )

		s = GafferImage.ImageStats()
		s["area"].setValue( r["out"]["format"].getValue().getDisplayWindow() )

		# Get the hashes of the outputs when there is no input.
		minHash = s["min"].hash()
		maxHash = s["max"].hash()
		averageHash = s["average"].hash()

		# Check that they are not equal to the hashes when we have an input.
		s["in"].setInput( r["out"] )
		self.assertNotEqual( minHash, s["min"].hash() )
		self.assertNotEqual( maxHash, s["max"].hash() )
		self.assertNotEqual( averageHash, s["average"].hash() )

	def testStats( self ) :

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.__rgbFilePath )

		s = GafferImage.ImageStats()
		s["in"].setInput( r["out"] )
		s["channels"].setValue( IECore.StringVectorData( [ "R", "G", "B", "A" ] ) )

		s["area"].setValue( r["out"]["format"].getValue().getDisplayWindow() )
		self.__assertColour( s["average"].getValue(), imath.Color4f( 0.0544, 0.0744, 0.1250, 0.2537 ) )
		self.__assertColour( s["min"].getValue(), imath.Color4f( 0, 0, 0, 0 ) )
		self.__assertColour( s["max"].getValue(), imath.Color4f( 0.5, 0.5, 0.5, 0.875 ) )

	# Test that we can change the ROI and the outputs are correct.
	def testROI( self ) :

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.__rgbFilePath )

		s = GafferImage.ImageStats()
		s["in"].setInput( r["out"] )
		s["channels"].setValue( IECore.StringVectorData( [ "R", "G", "B", "A" ] ) )

		s["area"].setValue( imath.Box2i( imath.V2i( 20, 20 ), imath.V2i( 25, 25 ) ) )
		self.__assertColour( s["average"].getValue(), imath.Color4f( 0.5, 0, 0, 0.5 ) )
		self.__assertColour( s["max"].getValue(), imath.Color4f( 0.5, 0, 0, 0.5 ) )
		self.__assertColour( s["min"].getValue(), imath.Color4f( 0.5, 0, 0, 0.5 ) )

		s["area"].setValue( imath.Box2i( imath.V2i( 20, 20 ), imath.V2i( 41, 30 ) ) )
		self.__assertColour( s["average"].getValue(), imath.Color4f( 0.4048, 0.1905, 0, 0.5952 ) )
		self.__assertColour( s["min"].getValue(), imath.Color4f( 0.25, 0, 0, 0.5 ) )
		self.__assertColour( s["max"].getValue(), imath.Color4f( 0.5, 0.5, 0, 0.75 ) )

	# Test only tiles which intersect a changed boundary have modified hashes
	def testROIHash( self ) :

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.__file300PxPath )

		s = GafferImage.ImageStats()
		s["in"].setInput( r["out"] )
		s["channels"].setValue( IECore.StringVectorData( [ "R", "G", "B", "A" ] ) )

		allHashes = []
		stats = []
		for a in [
			imath.Box2i( imath.V2i( 0, 0 ), imath.V2i( 300, 300 ) ),
			imath.Box2i( imath.V2i( 3, 5 ), imath.V2i( 300, 300 ) )
		]:
			s["area"].setValue( a )

			hashes = {}
			c = Gaffer.Context( Gaffer.Context.current() )
			for x in range( 0, 300, 64 ):
				for y in range( 0, 300, 64 ):
					c["image:channelName"] = "R"
					c["image:tileOrigin"] = imath.V2i( x, y )
					with c:
						hashes[ (x,y) ] = s["__tileStats"].hash()
			allHashes.append( hashes )

			stats.append( [ s["min"].getValue(), s["max"].getValue(), s["average"].getValue() ] )

		self.__assertColour( stats[0][0], imath.Color4f( 0, 0, 0, 0 ) )
		self.__assertColour( stats[0][1], imath.Color4f( 0.8027, 1, 1, 0 ) )
		self.__assertColour( stats[0][2], imath.Color4f( 0.0031, 0.0499, 0.1956, 0 ) )

		self.__assertColour( stats[1][0], imath.Color4f( 0, 0, 0, 0 ) )
		self.__assertColour( stats[1][1], imath.Color4f( 0.8027, 1, 1, 0 ) )
		self.__assertColour( stats[1][2], imath.Color4f( 0.0031, 0.0503, 0.1973, 0 ) )

		numDiff = 0
		numSame = 0
		for k, v in allHashes[0].items():
			if v == allHashes[1][k]:
				numSame += 1
			else:
				numDiff += 1

		# Check that interior hashes stay the same
		self.assertEqual( numSame, 16 )

		# Check that border hashes change
		self.assertEqual( numDiff, 9 )

	def testMin( self ) :

		c = GafferImage.Constant()
		s = GafferImage.ImageStats()
		s["in"].setInput( c["out"] )
		s["area"].setValue( c["out"]["format"].getValue().getDisplayWindow() )

		self.assertEqual( s["max"]["r"].getValue(), 0 )

	def testFormatAndMetadataAffectNothing( self ) :

		s = GafferImage.ImageStats()

		self.assertEqual( s.affects( s["in"]["format"] ), [] )
		self.assertEqual( s.affects( s["in"]["metadata"] ), [] )

	def testRepeatedChannels( self ) :

		c = GafferImage.Constant()
		s = GafferImage.ImageStats()
		s["in"].setInput( c["out"] )
		s["area"].setValue( c["out"]["format"].getValue().getDisplayWindow() )
		s["channels"].setValue( IECore.StringVectorData( [ "A", "A", "A", "A" ] ) )

		self.assertEqual( s["min"].getValue(), imath.Color4f( 1 ) )
		self.assertEqual( s["max"].getValue(), imath.Color4f( 1 ) )

	def testView( self ) :

		constantSource = GafferImage.Constant()
		constantSource["color"].setValue( imath.Color4f( 0.1, 0.2, 0.3, 0.4 ) )

		reader = GafferImage.ImageReader()
		reader["fileName"].setValue( self.__rgbFilePath )

		views = GafferImage.CreateViews()
		views["views"].addChild( Gaffer.NameValuePlug( "left", GafferImage.ImagePlug(), True ) )
		views["views"].addChild( Gaffer.NameValuePlug( "right", GafferImage.ImagePlug(), True ) )
		views["views"][0]["value"].setInput( constantSource["out"] )
		views["views"][1]["value"].setInput( reader["out"] )

		s = GafferImage.ImageStats()
		s["in"].setInput( views["out"] )
		s["area"].setValue( reader["out"]["format"].getValue().getDisplayWindow() )

		for contextView, queryAndResults in [
			( None, [ ( "", None ), ( "left", imath.Color4f( 0.1, 0.2, 0.3, 0.4 ) ), ( "right", imath.Color4f( 0.5, 0.5, 0.5, 0.875 ) ) ] ),
			( "left", [ ( "", imath.Color4f( 0.1, 0.2, 0.3, 0.4 ) ), ( "left", imath.Color4f( 0.1, 0.2, 0.3, 0.4 ) ), ( "right", imath.Color4f( 0.5, 0.5, 0.5, 0.875 ) ) ] ),
			("right", [ ( "", imath.Color4f( 0.5, 0.5, 0.5, 0.875 ) ), ( "left", imath.Color4f( 0.1, 0.2, 0.3, 0.4 ) ), ( "right", imath.Color4f( 0.5, 0.5, 0.5, 0.875 ) ) ] )

		]:
			for queryView, result in queryAndResults:
				with Gaffer.Context( Gaffer.Context.current() ) as c:
					s["view"].setValue( queryView )
					if contextView:
						c["image:viewName"] = contextView
					if result is None:
						# The result when contextView and queryView are both not overridden is an error,
						# views has just left and right views, so it's illegal to ask for "default".
						with six.assertRaisesRegex( self, Gaffer.ProcessException, 'View does not exist "default"' ):
							self.assertEqual( s["max"].getValue(), result )
					else:
						self.assertEqual( s["max"].getValue(), result )

		# When reading from an image with a default view, we get the default when requesting a view that
		# doesn't exist
		s["in"].setInput( reader["out"] )
		s["view"].setValue( "left" )
		self.assertEqual( s["max"].getValue(), imath.Color4f( 0.5, 0.5, 0.5, 0.875 ) )
		s["view"].setValue( "right" )
		self.assertEqual( s["max"].getValue(), imath.Color4f( 0.5, 0.5, 0.5, 0.875 ) )

	def __assertColour( self, colour1, colour2 ) :
		for i in range( 0, 4 ):
			self.assertEqual( "%.4f" % colour2[i], "%.4f" % colour1[i] )

if __name__ == "__main__":
	unittest.main()
