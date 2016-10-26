##########################################################################
#
#  Copyright (c) 2013-2015, Image Engine Design Inc. All rights reserved.
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

import IECore

import Gaffer
import GafferImage
import GafferImageTest

class ObjectToImageTest( GafferImageTest.ImageTestCase ) :

	fileName = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/checker.exr" )
	negFileName = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/checkerWithNegativeDataWindow.200x150.exr" )

	def test( self ) :

		i = IECore.Reader.create( self.fileName ).read()

		n = GafferImage.ObjectToImage()
		n["object"].setValue( i )

		self.assertEqual( n["out"].image(), i )

	def testDeepPlugs( self ) :

		ts = GafferImage.ImagePlug.tileSize()

		i = IECore.Reader.create( self.fileName ).read()

		n = GafferImage.ObjectToImage()
		n["object"].setValue( i )

		self.assertEqual( n["out"]["deepState"].getValue(), GafferImage.ImagePlug.DeepState.Flat )
		self.assertEqual( n["out"].sampleOffsets( IECore.V2i( 0 ) ), GafferImage.ImagePlug.flatTileSampleOffsets() )

	def testImageWithANegativeDataWindow( self ) :

		i = IECore.Reader.create( self.negFileName ).read()

		n = GafferImage.ObjectToImage()
		n["object"].setValue( i )

		self.assertEqual( n["out"].image(), i )

	def testHashVariesPerTileAndChannel( self ) :

		n = GafferImage.ObjectToImage()
		n["object"].setValue( IECore.Reader.create( self.fileName ).read() )

		self.assertNotEqual(
			n["out"].channelDataHash( "R", IECore.V2i( 0 ) ),
			n["out"].channelDataHash( "G", IECore.V2i( 0 ) )
		)

		self.assertNotEqual(
			n["out"].channelDataHash( "R", IECore.V2i( 0 ) ),
			n["out"].channelDataHash( "R", IECore.V2i( GafferImage.ImagePlug.tileSize() ) )
		)

if __name__ == "__main__":
	unittest.main()
