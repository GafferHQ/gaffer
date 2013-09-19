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

import unittest

import IECore
import Gaffer
import GafferTest
import GafferImage
import os

class RemoveChannelsTest( unittest.TestCase ) :

	checkerFile = os.path.expandvars( "$GAFFER_ROOT/python/GafferTest/images/checker.exr" )

	def testDirtyPropagation( self ) :
		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.checkerFile )		

		c = GafferImage.RemoveChannels()
		c["in"].setInput( r["out"] )

		cs = GafferTest.CapturingSlot( c.plugDirtiedSignal() )

		self.assertEqual( c["mode"].getValue(), GafferImage.RemoveChannels.RemoveChannelsMode.Remove )
		c["mode"].setValue( GafferImage.RemoveChannels.RemoveChannelsMode.Keep )

		dirtiedPlugs = set( [ x[0].relativeName( x[0].node() ) for x in cs ] )

		self.assertEqual( len(dirtiedPlugs), 3 )
		self.assertTrue( "mode" in dirtiedPlugs )
		self.assertTrue( "out" in dirtiedPlugs )
		self.assertTrue( "out.channelNames" in dirtiedPlugs )

		cs = GafferTest.CapturingSlot( c.plugDirtiedSignal() )

		c["channels"].setValue( IECore.StringVectorData( ["R"] ) )

		dirtiedPlugs = set( [ x[0].relativeName( x[0].node() ) for x in cs ] )
		self.assertEqual( len(dirtiedPlugs), 3 )
		self.assertTrue( "channels" in dirtiedPlugs )
		self.assertTrue( "out" in dirtiedPlugs )
		self.assertTrue( "out.channelNames" in dirtiedPlugs )

	def testRemoveChannels( self ) :

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.checkerFile )

		c = GafferImage.RemoveChannels()
		c["in"].setInput( r["out"] )
		c["mode"].setValue( GafferImage.RemoveChannels.RemoveChannelsMode.Remove ) # Remove selected channels
		c["channels"].setValue( IECore.StringVectorData( [ "G", "A" ] ) )
		
		self.assertEqual( c["out"]["channelNames"].getValue(), IECore.StringVectorData( [ "R", "B" ] ) )

	def testKeepChannels( self ) :

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.checkerFile )

		c = GafferImage.RemoveChannels()
		c["in"].setInput( r["out"] )
		c["mode"].setValue( GafferImage.RemoveChannels.RemoveChannelsMode.Keep ) # Keep selected channels
		c["channels"].setValue( IECore.StringVectorData( [ "G", "A" ] ) )

		self.assertEqual( c["out"]["channelNames"].getValue(), IECore.StringVectorData( [ "G", "A" ] ) )

	# The channel data should not change even if it is removed. This is because we don't modify it but just "hide" it.
	def testChannelDataHash( self ) :

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.checkerFile )
		h1 = r["out"].channelData( "R", IECore.V2i( 0 ) ).hash()

		c = GafferImage.RemoveChannels()
		c["in"].setInput( r["out"] )
		c["mode"].setValue( GafferImage.RemoveChannels.RemoveChannelsMode.Remove ) # Remove selected channels
		c["channels"].setValue( r["out"]["channelNames"].getValue() )
		h2 = c["out"].channelData( "R", IECore.V2i( 0 ) ).hash()

		self.assertEqual( h1, h2 )

		c["channels"].setValue( IECore.StringVectorData( [ "R" ] ) )
		h2 = c["out"].channelData( "R", IECore.V2i( 0 ) ).hash()
		self.assertEqual( h1, h2 )

		c["channels"].setValue( IECore.StringVectorData( [ "G" ] ) )
		h2 = c["out"].channelData( "R", IECore.V2i( 0 ) ).hash()
		self.assertEqual( h1, h2 )

	def testHashChanged( self ) :

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.checkerFile )

		c = GafferImage.RemoveChannels()
		c["in"].setInput( r["out"] )
		c["mode"].setValue( GafferImage.RemoveChannels.RemoveChannelsMode.Keep ) # Keep selected channels
		c["channels"].setValue( r["out"]["channelNames"].getValue() )
		h = c["out"]["channelNames"].hash()

		c["channels"].setValue( IECore.StringVectorData( [ "R", "B" ] ) )
		h2 = c["out"]["channelNames"].hash()
		self.assertNotEqual( h, h2 )

