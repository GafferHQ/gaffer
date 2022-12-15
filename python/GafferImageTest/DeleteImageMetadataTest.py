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

import IECore

import Gaffer
import GafferTest
import GafferImage
import GafferImageTest

class DeleteImageMetadataTest( GafferImageTest.ImageTestCase ) :

	checkerFile = Gaffer.rootPath() / "python" / "GafferImageTest" / "images" / "checker.exr"

	def test( self ) :

		i = GafferImage.ImageReader()
		i["fileName"].setValue( self.checkerFile )
		inMetadata = i["out"]["metadata"].getValue()

		m = GafferImage.DeleteImageMetadata()
		m["in"].setInput( i["out"] )

		# check that the image is passed through

		metadata = m["out"]["metadata"].getValue()
		self.assertEqual( m["out"]["metadata"].getValue(), inMetadata )
		self.assertImagesEqual( m["out"], i["out"] )
		self.assertTrue( "screenWindowWidth" in metadata )
		self.assertTrue( "screenWindowCenter" in metadata )
		self.assertTrue( "compression" in metadata )

		# check that we can delete metadata

		m["names"].setValue( "screen* compression" )
		metadata = m["out"]["metadata"].getValue()
		self.assertFalse( "screenWindowWidth" in metadata )
		self.assertFalse( "screenWindowCenter" in metadata )
		self.assertFalse( "compression" in metadata )
		for key in metadata.keys() :
			self.assertEqual( metadata[key], inMetadata[key] )

		# check that we can invert the deletion

		m["invertNames"].setValue( True )
		metadata = m["out"]["metadata"].getValue()
		expected = set([ "screenWindowWidth", "screenWindowCenter", "compression" ])
		self.assertEqual( set(metadata.keys()), expected )
		for key in metadata.keys() :
			self.assertEqual( metadata[key], inMetadata[key] )

		# test dirty propagation

		cs = GafferTest.CapturingSlot( m.plugDirtiedSignal() )

		m["names"].setValue( "" )
		self.assertTrue( m["out"]["metadata"] in set( e[0] for e in cs ) )

		del cs[:]

		m["invertNames"].setValue( False )
		self.assertTrue( m["out"]["metadata"] in set( e[0] for e in cs ) )

if __name__ == "__main__":
	unittest.main()
