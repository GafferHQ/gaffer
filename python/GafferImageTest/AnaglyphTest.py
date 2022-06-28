##########################################################################
#
#  Copyright (c) 2022, Image Engine Design Inc. All rights reserved.
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
import inspect
import unittest
import imath

import IECore

import Gaffer
import GafferImage
import GafferImageTest

class AnaglyphTest( GafferImageTest.ImageTestCase ) :

	file = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/multipart.exr" )

	def test( self ) :

		reader = GafferImage.ImageReader()
		reader["fileName"].setValue( self.file )

		left = GafferImage.Shuffle()
		left["in"].setInput( reader["out"] )
		left["channels"].addChild( GafferImage.Shuffle.ChannelPlug( "R", "customRgba.R" ) )
		left["channels"].addChild( GafferImage.Shuffle.ChannelPlug( "G", "customRgba.G" ) )
		left["channels"].addChild( GafferImage.Shuffle.ChannelPlug( "B", "customRgba.B" ) )
		left["channels"].addChild( GafferImage.Shuffle.ChannelPlug( "A", "customRgba.A" ) )

		right = GafferImage.ImageTransform()
		right["in"].setInput( left["out"] )
		right['transform']['translate'].setValue( imath.V2f( 10, 0 ) )

		createViews = GafferImage.CreateViews()
		createViews["views"].addChild( Gaffer.NameValuePlug( "left", GafferImage.ImagePlug(), True, "view0", Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		createViews["views"].addChild( Gaffer.NameValuePlug( "right", GafferImage.ImagePlug(), True, "view1", Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		createViews["views"][0]["value"].setInput( left["out"] )
		createViews["views"][1]["value"].setInput( right["out"] )

		anaglyph = GafferImage.Anaglyph()
		anaglyph["in"].setInput( createViews["out"] )

		leftChannels = [ "R", "customRgb.R", "customRgba.R" ]
		rightChannels = [ "G", "B", "customRgb.G", "customRgb.B", "customRgba.G", "customRgba.B" ]
		maxChannels = [ "A", "customRgba.A", "customDepth.Z" ]

		self.assertEqual( anaglyph["out"].viewNames(), IECore.StringVectorData( [ "default" ] ) )
		self.assertEqual( set( anaglyph["out"].channelNames() ), set( left["out"].channelNames() ) )
		self.assertEqual( set( anaglyph["out"].channelNames() ), set( leftChannels + rightChannels + maxChannels ) )

		compareA = GafferImage.DeleteChannels()
		compareA["in"].setInput( anaglyph["out"] )
		compareA["mode"].setValue( GafferImage.DeleteChannels.Mode.Keep )

		compareB = GafferImage.DeleteChannels()
		compareB["in"].setInput( left["out"] )
		compareB["mode"].setValue( GafferImage.DeleteChannels.Mode.Keep )
		compareB["channels"].setInput( compareA["channels"] )

		compareA["channels"].setValue( " ".join( leftChannels ) )
		self.assertImagesEqual( compareA["out"], compareB["out"], ignoreDataWindow = True )

		compareB["in"].setInput( right["out"] )
		compareA["channels"].setValue( " ".join( rightChannels ) )
		self.assertImagesEqual( compareA["out"], compareB["out"], ignoreDataWindow = True )

		# For channels which aren't colors, we take the max of the two views.  Doesn't always make sense,
		# but need to do something, and it's kinda reasonable for alpha
		maxm = GafferImage.Merge()
		maxm["in"][0].setInput( left["out"] )
		maxm["in"][1].setInput( right["out"] )
		maxm["operation"].setValue( GafferImage.Merge.Operation.Max )

		compareB["in"].setInput( maxm["out"] )
		compareA["channels"].setValue( " ".join( maxChannels ) )
		self.assertImagesEqual( compareA["out"], compareB["out"] )


		anaglyph["enabled"].setValue( False )
		self.assertImagesEqual( anaglyph["out"], createViews["out"] )
