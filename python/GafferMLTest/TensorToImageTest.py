##########################################################################
#
#  Copyright (c) 2024, Cinesite VFX Ltd. All rights reserved.
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

import Gaffer
import GafferTest
import GafferImage
import GafferImageTest
import GafferML

class TensorToImageTest( GafferImageTest.ImageTestCase ) :

	def testNoInput( self ) :

		node = GafferML.TensorToImage()
		with self.assertRaisesRegex( Gaffer.ProcessException, "Empty tensor" ) :
			node["out"].dataWindow()

	def testNonMatchingChannels( self ) :

		tensor = GafferML.Tensor(
			IECore.Color3fVectorData( [ imath.Color3f( 1, 2, 3 ) ] ),
			[ 1, 1, 3 ]
		)

		tensorToImage = GafferML.TensorToImage()
		tensorToImage["tensor"].setValue( tensor )
		tensorToImage["interleavedChannels"].setValue( True )
		self.assertEqual( tensorToImage["out"].dataWindow(), imath.Box2i( imath.V2i( 0 ), imath.V2i( 1 ) ) )

		# Only two channels specified.

		tensorToImage["channels"].setValue( IECore.StringVectorData( [ "R", "G" ] ) )
		self.assertEqual( tensorToImage["out"].channelNames(), IECore.StringVectorData( [ "R", "G" ] ) )
		self.assertEqual( tensorToImage["out"].channelData( "R", imath.V2i( 0 ) )[0], 1 )
		self.assertEqual( tensorToImage["out"].channelData( "G", imath.V2i( 0 ) )[0], 2 )

		with self.assertRaisesRegex( RuntimeError, 'Invalid channel "B"' ) :
			tensorToImage["out"].channelData( "B", imath.V2i( 0 ) )

		# Duplicate channels specified. We just take the first.

		tensorToImage["channels"].setValue( IECore.StringVectorData( [ "R", "R", "B" ] ) )
		self.assertEqual( tensorToImage["out"].channelNames(), IECore.StringVectorData( [ "R", "B" ] ) )
		self.assertEqual( tensorToImage["out"].channelData( "R", imath.V2i( 0 ) )[0], 1 )
		self.assertEqual( tensorToImage["out"].channelData( "B", imath.V2i( 0 ) )[0], 3 )

		with self.assertRaisesRegex( RuntimeError, 'Invalid channel "G' ) :
			tensorToImage["out"].channelData( "G", imath.V2i( 0 ) )

		# Too many channels specified. We error if the extra channel is accessed.

		tensorToImage["channels"].setValue( IECore.StringVectorData( [ "R", "G", "B", "A" ] ) )
		self.assertEqual( tensorToImage["out"].channelNames(), IECore.StringVectorData( [ "R", "G", "B", "A" ] ) )
		self.assertEqual( tensorToImage["out"].channelData( "R", imath.V2i( 0 ) )[0], 1 )
		self.assertEqual( tensorToImage["out"].channelData( "G", imath.V2i( 0 ) )[0], 2 )
		self.assertEqual( tensorToImage["out"].channelData( "B", imath.V2i( 0 ) )[0], 3 )

		with self.assertRaisesRegex( RuntimeError, 'Channel "A" out of range' ) :
			tensorToImage["out"].channelData( "A", imath.V2i( 0 ) )

		# Channels skipped by entering empty strings.

		tensorToImage["channels"].setValue( IECore.StringVectorData( [ "R", "", "B" ] ) )
		self.assertEqual( tensorToImage["out"].channelNames(), IECore.StringVectorData( [ "R", "B" ] ) )
		self.assertEqual( tensorToImage["out"].channelData( "R", imath.V2i( 0 ) )[0], 1 )
		self.assertEqual( tensorToImage["out"].channelData( "B", imath.V2i( 0 ) )[0], 3 )

		with self.assertRaisesRegex( RuntimeError, 'Invalid channel "G' ) :
			tensorToImage["out"].channelData( "G", imath.V2i( 0 ) )

	def testRoundTripWithImageToTensor( self ) :

		image = GafferImage.Checkerboard()

		imageToTensor = GafferML.ImageToTensor()
		imageToTensor["image"].setInput( image["out"] )
		imageToTensor["channels"].setInput( image["out"]["channelNames"])

		tensorToImage = GafferML.TensorToImage()
		tensorToImage["tensor"].setInput( imageToTensor["tensor"] )
		tensorToImage["channels"].setInput( image["out"]["channelNames"])

		self.assertImagesEqual( tensorToImage["out"], image["out"] )

		imageToTensor["interleaveChannels"].setValue( True )
		tensorToImage["interleavedChannels"].setValue( True )

		self.assertImagesEqual( tensorToImage["out"], image["out"] )

	def testNonFloatTensor( self ) :

		tensor = GafferML.Tensor(
			IECore.IntVectorData( [ 1, 2, 3 ] ),
			[ 1, 1, 3 ]
		)

		tensorToImage = GafferML.TensorToImage()
		tensorToImage["tensor"].setValue( tensor )
		tensorToImage["interleavedChannels"].setValue( True )

		with self.assertRaisesRegex( RuntimeError, "Unsupported tensor data type" ) :
			tensorToImage["out"].channelData( "R", imath.V2i( 0 ) )

if __name__ == "__main__":
	unittest.main()
