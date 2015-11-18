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

class ImageProcessorTest( GafferImageTest.ImageTestCase ) :

	def testDerivingInPython( self ) :

		# We allow deriving in Python for use as a "shell" node containing
		# an internal node network which provides the implementation. But
		# we don't allow the overriding of the compute*() and hash*() methods
		# because the performance would be abysmal.

		class DeleteAlpha( GafferImage.ImageProcessor ) :

			def __init__( self, name = "DeleteAlpha" ) :

				GafferImage.ImageProcessor.__init__( self, name )

				self["__deleteChannels"] = GafferImage.DeleteChannels()
				self["__deleteChannels"]["in"].setInput( self["in"] )
				self["__deleteChannels"]["enabled"].setInput( self["enabled"] )
				self["__deleteChannels"]["channels"].setValue( IECore.StringVectorData( [ "A" ] ) )

				self["out"].setInput( self["__deleteChannels"]["out"] )

		IECore.registerRunTimeTyped( DeleteAlpha )

		Gaffer.Metadata.registerNode(

			DeleteAlpha,

			"description",
			"""
			Deletes the alpha channel.
			""",

		)

		c = GafferImage.Constant()
		self.assertTrue( "A" in c["out"]["channelNames"].getValue() )

		n = DeleteAlpha()
		n["in"].setInput( c["out"] )
		self.assertFalse( "A" in n["out"]["channelNames"].getValue() )

		n["enabled"].setValue( False )
		self.assertTrue( "A" in n["out"]["channelNames"].getValue() )

		self.assertEqual(
			Gaffer.Metadata.nodeValue( n, "description" ),
			"Deletes the alpha channel.",
		)

	def testNumberOfInputs( self ) :

		n = GafferImage.ImageProcessor()
		self.assertTrue( isinstance( n["in"], GafferImage.ImagePlug ) )

		n = GafferImage.ImageProcessor( minInputs = 2, maxInputs = 2 )
		self.assertTrue( isinstance( n["in"], Gaffer.ArrayPlug ) )
		self.assertEqual( len( n["in"] ), 2 )
		self.assertTrue( isinstance( n["in"][0], GafferImage.ImagePlug ) )
		self.assertTrue( isinstance( n["in"][1], GafferImage.ImagePlug ) )
		self.assertEqual( n["in"].minSize(), 2 )
		self.assertEqual( n["in"].maxSize(), 2 )

		n = GafferImage.ImageProcessor( minInputs = 2, maxInputs = 1000 )
		self.assertTrue( isinstance( n["in"], Gaffer.ArrayPlug ) )
		self.assertTrue( isinstance( n["in"][0], GafferImage.ImagePlug ) )
		self.assertTrue( isinstance( n["in"][1], GafferImage.ImagePlug ) )
		self.assertEqual( len( n["in"] ), 2 )
		self.assertEqual( n["in"].minSize(), 2 )
		self.assertEqual( n["in"].maxSize(), 1000 )

		n = GafferImage.ImageProcessor( minInputs = 2 )
		self.assertTrue( isinstance( n["in"], Gaffer.ArrayPlug ) )
		self.assertTrue( isinstance( n["in"][0], GafferImage.ImagePlug ) )
		self.assertTrue( isinstance( n["in"][1], GafferImage.ImagePlug ) )
		self.assertEqual( len( n["in"] ), 2 )
		self.assertEqual( n["in"].minSize(), 2 )
		self.assertEqual( n["in"].maxSize(), Gaffer.ArrayPlug().maxSize() )

if __name__ == "__main__":
	unittest.main()
