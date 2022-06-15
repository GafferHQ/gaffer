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
import imath

import IECore

import Gaffer
import GafferImage
import GafferTest
import GafferImageTest

class CopyImageMetadataTest( GafferImageTest.ImageTestCase ) :

	checkerFile = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/checker.exr" )

	def test( self ) :

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.checkerFile )
		inMetadata = r["out"]["metadata"].getValue()

		d = GafferImage.DeleteImageMetadata()
		d["in"].setInput( r["out"] )
		d["names"].setValue( "*" )

		m = GafferImage.CopyImageMetadata()
		m["in"].setInput( d["out"] )
		m["copyFrom"].setInput( r["out"] )
		m["names"].setValue( "" )

		# check that the image is passed through

		metadata = m["out"]["metadata"].getValue()
		self.assertEqual( m["out"]["metadata"].getValue(), IECore.CompoundData() )
		self.assertImagesEqual( m["out"], d["out"] )

		# check that we can copy specific metadata

		m["names"].setValue( "screen* compression" )
		metadata = m["out"]["metadata"].getValue()
		expected = set([ "screenWindowWidth", "screenWindowCenter", "compression" ])
		self.assertEqual( set(metadata.keys()), expected )
		for key in metadata.keys() :
			self.assertEqual( metadata[key], inMetadata[key] )

		# check that we can invert the selection

		m["invertNames"].setValue( True )
		metadata = m["out"]["metadata"].getValue()
		expected = set( inMetadata.keys() ) - set( [ "screenWindowWidth", "screenWindowCenter", "compression" ] )
		self.assertEqual( set(metadata.keys()), expected )
		for key in metadata.keys() :
			self.assertEqual( metadata[key], inMetadata[key] )

	def testOverwrite( self ) :

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.checkerFile )
		inMetadata = r["out"]["metadata"].getValue()

		a = GafferImage.ImageMetadata()
		a["metadata"].addChild( Gaffer.NameValuePlug( "compression", IECore.StringData( "extraFancyCompressor" ) ) )

		m = GafferImage.CopyImageMetadata()
		m["in"].setInput( r["out"] )
		m["copyFrom"].setInput( a["out"] )

		# check that the image is passed through

		m["names"].setValue( "" )
		metadata = m["out"]["metadata"].getValue()
		self.assertEqual( metadata["compression"], IECore.StringData( "zips" ) )
		self.assertEqual( m["out"]["metadata"].getValue(), inMetadata )
		self.assertImagesEqual( m["out"], r["out"] )

		# check that we can overwrite certain metadata

		m["names"].setValue( "compression" )
		metadata = m["out"]["metadata"].getValue()
		self.assertTrue( "compression" in metadata.keys() )
		self.assertEqual( metadata["compression"], IECore.StringData( "extraFancyCompressor" ) )

	def testDirtyPropogation( self ) :

		c = GafferImage.Constant()
		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.checkerFile )
		inMetadata = r["out"]["metadata"].getValue()

		m = GafferImage.CopyImageMetadata()
		m["in"].setInput( c["out"] )
		m["copyFrom"].setInput( r["out"] )

		cs = GafferTest.CapturingSlot( m.plugDirtiedSignal() )

		m["copyFrom"].setInput( c["out"] )
		self.assertTrue( m["out"]["metadata"] in set( e[0] for e in cs ) )

		del cs[:]

		m["names"].setValue( "test" )
		self.assertTrue( m["out"]["metadata"] in set( e[0] for e in cs ) )

		del cs[:]

		m["invertNames"].setValue( True )
		self.assertTrue( m["out"]["metadata"] in set( e[0] for e in cs ) )

	def testPassThrough( self ) :

		c = GafferImage.Constant()
		i = GafferImage.ImageReader()
		i["fileName"].setValue( self.checkerFile )

		m = GafferImage.CopyImageMetadata()
		m["in"].setInput( i["out"] )
		m["names"].setValue( "*" )

		self.assertEqual( i["out"]["format"].hash(), m["out"]["format"].hash() )
		self.assertEqual( i["out"]["dataWindow"].hash(), m["out"]["dataWindow"].hash() )
		self.assertEqual( i["out"]["channelNames"].hash(), m["out"]["channelNames"].hash() )

		self.assertEqual( i["out"]["format"].getValue(), m["out"]["format"].getValue() )
		self.assertEqual( i["out"]["dataWindow"].getValue(), m["out"]["dataWindow"].getValue() )
		self.assertEqual( i["out"]["channelNames"].getValue(), m["out"]["channelNames"].getValue() )

		context = Gaffer.Context( Gaffer.Context.current() )
		context["image:tileOrigin"] = imath.V2i( 0 )
		with context :
			for c in [ "G", "B", "A" ] :
				context["image:channelName"] = c
				self.assertEqual( i["out"]["channelData"].hash(), m["out"]["channelData"].hash() )
				self.assertEqual( i["out"]["channelData"].getValue(), m["out"]["channelData"].getValue() )

if __name__ == "__main__":
	unittest.main()
