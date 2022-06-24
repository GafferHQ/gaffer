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
import GafferTest
import GafferImage
import GafferImageTest

class ImageMetadataTest( GafferImageTest.ImageTestCase ) :

	checkerFile = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/checker.exr" )

	def test( self ) :

		i = GafferImage.ImageReader()
		i["fileName"].setValue( self.checkerFile )
		inMetadata = i["out"]["metadata"].getValue()

		m = GafferImage.ImageMetadata()
		m["in"].setInput( i["out"] )

		# check that the image is passed through

		self.assertEqual( m["out"]["metadata"].getValue(), inMetadata )
		self.assertImagesEqual( m["out"], i["out"] )

		# check that we can make metadata

		m["metadata"].addChild( Gaffer.NameValuePlug( "comment", IECore.StringData( "my favorite image!" ), "member1", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		m["metadata"].addChild( Gaffer.NameValuePlug( "range", IECore.V2iData( imath.V2i( 5, 10 ) ), True, "member1", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )

		metadata = m["out"]["metadata"].getValue()
		self.assertEqual( len(metadata), len(inMetadata) + 2 )
		self.assertEqual( metadata["comment"], IECore.StringData( "my favorite image!" ) )
		self.assertEqual( metadata["range"], IECore.V2iData( imath.V2i( 5, 10 ) ) )
		del metadata["comment"]
		del metadata["range"]
		self.assertEqual( metadata, inMetadata )

		# check disabling optional metadata

		m["metadata"]["member2"]["enabled"].setValue( False )
		metadata = m["out"]["metadata"].getValue()
		self.assertEqual( len(metadata), len(inMetadata) + 1 )
		self.assertEqual( metadata["comment"], IECore.StringData( "my favorite image!" ) )
		self.assertFalse( "range" in metadata.keys() )
		del metadata["comment"]
		self.assertEqual( metadata, inMetadata )

		# check disabling the node entirely

		m["enabled"].setValue( False )
		self.assertEqual( m["out"]["metadata"].hash(), i["out"]["metadata"].hash() )
		self.assertEqual( m["out"]["metadata"].getValue(), inMetadata )
		self.assertImageHashesEqual( m["out"], i["out"] )
		self.assertImagesEqual( m["out"], i["out"] )

	def testSubstitution( self ) :

		s = Gaffer.ScriptNode()
		s["m"] = GafferImage.ImageMetadata()
		s["m"]["metadata"].addChild( Gaffer.NameValuePlug( "comment", IECore.StringData( "${foo}" ) ) )

		self.assertEqual( s["m"]["out"]["metadata"].getValue()["comment"], IECore.StringData( "" ) )
		h = s["m"]["out"]["metadata"].hash()

		c = Gaffer.Context()
		c["foo"] = "foo"

		with c :
			self.assertNotEqual( s["m"]["out"]["metadata"].hash(), h )
			self.assertEqual( s["m"]["out"]["metadata"].getValue()["comment"], IECore.StringData( "foo" ) )

	def testSerialisation( self ) :

		s = Gaffer.ScriptNode()
		s["m"] = GafferImage.ImageMetadata()
		s["m"]["metadata"].addChild( Gaffer.NameValuePlug( "comment", IECore.StringData( "my favorite image!" ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic  ) )
		s["m"]["metadata"].addChild( Gaffer.NameValuePlug( "range", IECore.V2iData( imath.V2i( 5, 10 ) ), True, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		names = s["m"]["metadata"].keys()

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( s2["m"]["metadata"].keys(), names )
		self.assertTrue( "metadata1" not in s2["m"] )
		self.assertEqual( s2["m"]["metadata"][names[0]]["name"].getValue(), "comment" )
		self.assertEqual( s2["m"]["metadata"][names[0]]["value"].getValue(), "my favorite image!" )
		self.assertEqual( s2["m"]["metadata"][names[1]]["name"].getValue(), "range" )
		self.assertEqual( s2["m"]["metadata"][names[1]]["enabled"].getValue(), True )
		self.assertEqual( s2["m"]["metadata"][names[1]]["value"].getValue(), imath.V2i( 5, 10 ) )

	def testBoxPromotion( self ) :

		s = Gaffer.ScriptNode()
		s["m"] = GafferImage.ImageMetadata()
		s["m"]["metadata"].addChild( Gaffer.NameValuePlug( "comment", IECore.StringData( "my favorite image!" ), "member1", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		s["m"]["metadata"].addChild( Gaffer.NameValuePlug( "range", IECore.V2iData( imath.V2i( 5, 10 ) ), True, "member1", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )

		memberDataAndName = s["m"]["metadata"].memberDataAndName( s["m"]["metadata"]["member1"] )
		memberDataAndName2 = s["m"]["metadata"].memberDataAndName( s["m"]["metadata"]["member2"] )

		Gaffer.Box.create( s, Gaffer.StandardSet( [ s["m"] ] ) )
		Gaffer.PlugAlgo.promote( s["Box"]["m"]["metadata"]["member1"] )
		Gaffer.PlugAlgo.promote( s["Box"]["m"]["metadata"]["member2"] )

		self.assertEqual(
			s["Box"]["m"]["metadata"].memberDataAndName( s["Box"]["m"]["metadata"]["member1"] ),
			memberDataAndName,
		)

		self.assertEqual(
			s["Box"]["m"]["metadata"].memberDataAndName( s["Box"]["m"]["metadata"]["member2"] ),
			memberDataAndName2,
		)

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual(
			s2["Box"]["m"]["metadata"].memberDataAndName( s2["Box"]["m"]["metadata"]["member1"] ),
			memberDataAndName
		)

		self.assertEqual(
			s2["Box"]["m"]["metadata"].memberDataAndName( s2["Box"]["m"]["metadata"]["member2"] ),
			memberDataAndName2,
		)

	def testPassThrough( self ) :

		i = GafferImage.ImageReader()
		i["fileName"].setValue( self.checkerFile )

		m = GafferImage.ImageMetadata()
		m["in"].setInput( i["out"] )
		m["metadata"].addChild( Gaffer.NameValuePlug( "comment", IECore.StringData( "my favorite image!" ) ) )
		m["metadata"].addChild( Gaffer.NameValuePlug( "range", IECore.V2iData( imath.V2i( 5, 10 ) ), True ) )

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

	def testEnabledOnlyAffectsMetadata( self ) :

		m = GafferImage.ImageMetadata()
		cs = GafferTest.CapturingSlot( m.plugDirtiedSignal() )
		m["enabled"].setValue( False )
		self.assertEqual( { x[0] for x in cs }, { m["enabled"], m["out"]["metadata"], m["out"] } )

	def testExtraMetadata( self ) :

		m = GafferImage.ImageMetadata()
		self.assertEqual( m["out"].metadata(), IECore.CompoundData() )

		m["metadata"].addChild( Gaffer.NameValuePlug( "a", "originalA" ) )
		m["metadata"].addChild( Gaffer.NameValuePlug( "b", "originalB" ) )

		m["extraMetadata"].setValue( IECore.CompoundData( {
			"a" : "extraA",
			"c" : "extraC",
		} ) )

		self.assertEqual(
			m["out"].metadata(),
			IECore.CompoundData( {
				"a" : "extraA",
				"b" : "originalB",
				"c" : "extraC",
			} )
		)

if __name__ == "__main__":
	unittest.main()
