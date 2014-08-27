##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
#  Copyright (c) 2012, Image Engine Design Inc. All rights reserved.
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
import GafferTest
import GafferImage

class OpenColorIOTest( unittest.TestCase ) :

	fileName = os.path.expandvars( "$GAFFER_ROOT/python/GafferTest/images/checker.exr" )

	def test( self ) :

		n = GafferImage.ImageReader()
		n["fileName"].setValue( self.fileName )

		o = GafferImage.OpenColorIO()
		o["in"].setInput( n["out"] )

		self.assertEqual( n["out"].image(), o["out"].image() )

		o["inputSpace"].setValue( "linear" )
		o["outputSpace"].setValue( "sRGB" )

		self.assertNotEqual( n["out"].image(), o["out"].image() )

	def testHashPassThrough( self ) :

		n = GafferImage.ImageReader()
		n["fileName"].setValue( self.fileName )

		o = GafferImage.OpenColorIO()
		o["in"].setInput( n["out"] )

		self.assertEqual( n["out"].image(), o["out"].image() )

		o["inputSpace"].setValue( "linear" )
		o["outputSpace"].setValue( "sRGB" )

		self.assertNotEqual( n["out"].image(), o["out"].image() )

		o["enabled"].setValue( False )

		self.assertEqual( n["out"].image(), o["out"].image() )
		self.assertEqual( n["out"]['format'].hash(), o["out"]['format'].hash() )
		self.assertEqual( n["out"]['dataWindow'].hash(), o["out"]['dataWindow'].hash() )
		self.assertEqual( n["out"]['channelNames'].hash(), o["out"]['channelNames'].hash() )

		o["enabled"].setValue( True )

		o["inputSpace"].setValue( "linear" )
		o["outputSpace"].setValue( "linear" )
		self.assertEqual( n["out"].image(), o["out"].image() )
		self.assertEqual( n["out"]['format'].hash(), o["out"]['format'].hash() )
		self.assertEqual( n["out"]['dataWindow'].hash(), o["out"]['dataWindow'].hash() )
		self.assertEqual( n["out"]['channelNames'].hash(), o["out"]['channelNames'].hash() )

	def testImageHashPassThrough( self ) :

		i = GafferImage.ImageReader()
		i["fileName"].setValue( self.fileName )

		o = GafferImage.OpenColorIO()
		o["in"].setInput( i["out"] )

		self.assertEqual( i["out"].imageHash(), o["out"].imageHash() )

		o["inputSpace"].setValue( "linear" )
		o["outputSpace"].setValue( "sRGB" )

		self.assertNotEqual( i["out"].imageHash(), o["out"].imageHash() )

	def testChannelsAreSeparate( self ) :

		i = GafferImage.ImageReader()
		i["fileName"].setValue( os.path.expandvars( "$GAFFER_ROOT/python/GafferTest/images/circles.exr" ) )

		o = GafferImage.OpenColorIO()
		o["in"].setInput( i["out"] )

		o["inputSpace"].setValue( "linear" )
		o["outputSpace"].setValue( "sRGB" )

		self.assertNotEqual(
			o["out"].channelDataHash( "R", IECore.V2i( 0 ) ),
			o["out"].channelDataHash( "G", IECore.V2i( 0 ) )
		)

		self.assertNotEqual(
			o["out"].channelData( "R", IECore.V2i( 0 ) ),
			o["out"].channelData( "G", IECore.V2i( 0 ) )
		)

if __name__ == "__main__":
	unittest.main()
