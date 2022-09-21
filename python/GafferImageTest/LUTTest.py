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

import os
import unittest
import imath

import PyOpenColorIO

import IECore

import Gaffer
import GafferTest
import GafferImage
import GafferImageTest

class LUTTest( GafferImageTest.ImageTestCase ) :

	imageFile = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/checker.exr" )
	lut = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/openColorIO/luts/slog10.spi1d" )

	def test( self ) :

		n = GafferImage.ImageReader()
		n["fileName"].setValue( self.imageFile )

		o = GafferImage.LUT()
		o["in"].setInput( n["out"] )

		self.assertImagesEqual( n["out"], o["out"] )

		o["fileName"].setValue( self.lut )
		o["interpolation"].setValue( GafferImage.LUT.Interpolation.Linear )

		forward = GafferImage.ImageAlgo.image( o["out"] )
		self.assertNotEqual( GafferImage.ImageAlgo.image( n["out"] ), forward )

		o["direction"].setValue( GafferImage.OpenColorIOTransform.Direction.Inverse )
		inverse = GafferImage.ImageAlgo.image( o["out"] )
		self.assertNotEqual( GafferImage.ImageAlgo.image( n["out"] ), inverse )
		self.assertNotEqual( forward, inverse )

	def testBadFileName( self ) :

		n = GafferImage.ImageReader()
		n["fileName"].setValue( self.imageFile )

		o = GafferImage.LUT()
		o["in"].setInput( n["out"] )
		o["fileName"].setValue( "/not/a/real.cube" )
		self.assertRaises( RuntimeError, GafferImage.ImageAlgo.image, o["out"] )

	def testBadInterpolation( self ) :

		n = GafferImage.ImageReader()
		n["fileName"].setValue( self.imageFile )

		o = GafferImage.LUT()
		o["in"].setInput( n["out"] )
		o["fileName"].setValue( self.lut )

		image = GafferImage.ImageAlgo.image( o["out"] )

		log = []
		def loggingFunction( message ) :
			log.append( message )

		try :
			PyOpenColorIO.SetLoggingFunction( loggingFunction )
			o["interpolation"].setValue( GafferImage.LUT.Interpolation.Tetrahedral )
			# Bad interpolations fall back to the default interpolation, but
			# also emit a warning message.
			self.assertEqual( GafferImage.ImageAlgo.image( o["out"] ), image )
		finally :
			PyOpenColorIO.ResetToDefaultLoggingFunction()

		## \todo Perhaps libGafferImage should permanently install a logging function that
		# forwards messages to `IECore::MessageHandler`?
		self.assertEqual( len( log ), 1 )
		self.assertIn(
			"Interpolation specified by FileTransform 'tetrahedral' is not allowed with the given file",
			log[0]
		)

	def testHashPassThrough( self ) :

		n = GafferImage.ImageReader()
		n["fileName"].setValue( self.imageFile )

		o = GafferImage.LUT()
		o["in"].setInput( n["out"] )

		self.assertImageHashesEqual( n["out"], o["out"] )
		self.assertImagesEqual( n["out"], o["out"] )

		o["fileName"].setValue( self.lut )

		self.assertNotEqual( GafferImage.ImageAlgo.image( n["out"] ), GafferImage.ImageAlgo.image( o["out"] ) )

		o["enabled"].setValue( False )

		self.assertImageHashesEqual( n["out"], o["out"] )
		self.assertImagesEqual( n["out"], o["out"] )
		self.assertEqual( n["out"]['format'].hash(), o["out"]['format'].hash() )
		self.assertEqual( n["out"]['dataWindow'].hash(), o["out"]['dataWindow'].hash() )
		self.assertEqual( n["out"]["metadata"].getValue(), o["out"]["metadata"].getValue() )
		self.assertEqual( n["out"]['channelNames'].hash(), o["out"]['channelNames'].hash() )

		o["enabled"].setValue( True )

		o["fileName"].setValue( "" )
		self.assertImageHashesEqual( n["out"], o["out"] )
		self.assertImagesEqual( n["out"], o["out"] )
		self.assertEqual( n["out"]['format'].hash(), o["out"]['format'].hash() )
		self.assertEqual( n["out"]['dataWindow'].hash(), o["out"]['dataWindow'].hash() )
		self.assertEqual( n["out"]["metadata"].getValue(), o["out"]["metadata"].getValue() )
		self.assertEqual( n["out"]['channelNames'].hash(), o["out"]['channelNames'].hash() )

	def testImageHashPassThrough( self ) :

		i = GafferImage.ImageReader()
		i["fileName"].setValue( self.imageFile )

		o = GafferImage.LUT()
		o["in"].setInput( i["out"] )

		self.assertEqual( GafferImage.ImageAlgo.imageHash( i["out"] ), GafferImage.ImageAlgo.imageHash( o["out"] ) )

		o["fileName"].setValue( self.lut )

		self.assertNotEqual( GafferImage.ImageAlgo.imageHash( i["out"] ), GafferImage.ImageAlgo.imageHash( o["out"] ) )

	def testChannelsAreSeparate( self ) :

		i = GafferImage.ImageReader()
		i["fileName"].setValue( os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/circles.exr" ) )

		o = GafferImage.LUT()
		o["in"].setInput( i["out"] )

		o["fileName"].setValue( self.lut )

		self.assertNotEqual(
			o["out"].channelDataHash( "R", imath.V2i( 0 ) ),
			o["out"].channelDataHash( "G", imath.V2i( 0 ) )
		)

		self.assertNotEqual(
			o["out"].channelData( "R", imath.V2i( 0 ) ),
			o["out"].channelData( "G", imath.V2i( 0 ) )
		)

	def testPassThrough( self ) :

		i = GafferImage.ImageReader()
		i["fileName"].setValue( self.imageFile )

		o = GafferImage.LUT()
		o["in"].setInput( i["out"] )
		o["fileName"].setValue( self.lut )

		self.assertEqual( i["out"]["format"].hash(), o["out"]["format"].hash() )
		self.assertEqual( i["out"]["dataWindow"].hash(), o["out"]["dataWindow"].hash() )
		self.assertEqual( i["out"]["metadata"].getValue(), o["out"]["metadata"].getValue() )
		self.assertEqual( i["out"]["channelNames"].hash(), o["out"]["channelNames"].hash() )

		self.assertEqual( i["out"]["format"].getValue(), o["out"]["format"].getValue() )
		self.assertEqual( i["out"]["dataWindow"].getValue(), o["out"]["dataWindow"].getValue() )
		self.assertEqual( i["out"]["metadata"].getValue(), o["out"]["metadata"].getValue() )
		self.assertEqual( i["out"]["channelNames"].getValue(), o["out"]["channelNames"].getValue() )

if __name__ == "__main__":
	unittest.main()
