##########################################################################
#
#  Copyright (c) 2019, Image Engine Design Inc. All rights reserved.
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

import random
import unittest
import imath
import os

import IECore

import GafferTest
import GafferImage
import GafferImageTest

class DeepHoldoutTest( GafferImageTest.ImageTestCase ) :

	representativeImagePath = GafferImageTest.ImageTestCase.imagesPath() / "representativeDeepImage.exr"

	def testBasics( self ):
		representativeImage = GafferImage.ImageReader()
		representativeImage["fileName"].setValue( self.representativeImagePath )

		offset = GafferImage.Offset()
		offset["in"].setInput( representativeImage["out"] )

		holdout = GafferImage.DeepHoldout()
		holdout["in"].setInput( representativeImage["out"] )
		holdout["holdout"].setInput( offset["out"] )

		flat = GafferImage.DeepToFlat()
		flat["in"].setInput( representativeImage["out"] )

		# For the case of holding out an image by itself, we can find an analytic solution for the
		# held out alpha.  For a composited alpha value A, the held out alpha will be ( 1 - ( 1 - A )^2 ) / 2
		# Check that this relationship holds

		alphaOnlyHoldout = GafferImage.DeleteChannels()
		alphaOnlyHoldout["in"].setInput( holdout["out"] )
		alphaOnlyHoldout["mode"].setValue( GafferImage.DeleteChannels.Mode.Keep )
		alphaOnlyHoldout["channels"].setValue( '[A]' )

		complementAndSquare = GafferImage.Grade()
		complementAndSquare["in"].setInput( flat["out"] )
		complementAndSquare["channels"].setValue( '[A]' )
		complementAndSquare["multiply"].setValue( imath.Color4f( 1, 1, 1, -1 ) )
		complementAndSquare["offset"].setValue( imath.Color4f( 0, 0, 0, 1 ) )
		complementAndSquare["gamma"].setValue( imath.Color4f( 1, 1, 1, 0.5 ) )

		complementAndHalve = GafferImage.Grade()
		complementAndHalve["in"].setInput( complementAndSquare["out"] )
		complementAndHalve["channels"].setValue( '[A]' )
		complementAndHalve["multiply"].setValue( imath.Color4f( 1, 1, 1, -0.5 ) )
		complementAndHalve["offset"].setValue( imath.Color4f( 0, 0, 0, 0.5 ) )

		alphaOnlyReference = GafferImage.DeleteChannels()
		alphaOnlyReference["in"].setInput( complementAndHalve["out"] )
		alphaOnlyReference["mode"].setValue( GafferImage.DeleteChannels.Mode.Keep )
		alphaOnlyReference["channels"].setValue( '[A]' )

		self.assertImagesEqual( alphaOnlyHoldout["out"], alphaOnlyReference["out"], maxDifference = 1e-6 )

		# For a more complex holdout, we can create a comparison manually using shuffles and a DeepMerge
		preShuffle = GafferImage.Shuffle()
		preShuffle["in"].setInput( representativeImage["out"] )
		preShuffle["channels"].addChild( preShuffle.ChannelPlug( "holdoutR", "R" ) )
		preShuffle["channels"].addChild( preShuffle.ChannelPlug( "holdoutG", "G" ) )
		preShuffle["channels"].addChild( preShuffle.ChannelPlug( "holdoutB", "B" ) )
		preShuffle["channels"].addChild( preShuffle.ChannelPlug( "holdoutA", "A" ) )

		manualHoldoutMerge = GafferImage.DeepMerge()
		manualHoldoutMerge["in"][0].setInput( preShuffle["out"] )
		manualHoldoutMerge["in"][1].setInput( offset["out"] )

		manualHoldoutFlatten = GafferImage.DeepToFlat()
		manualHoldoutFlatten["in"].setInput( manualHoldoutMerge["out"] )

		postShuffle = GafferImage.Shuffle()
		postShuffle["in"].setInput( manualHoldoutFlatten["out"] )
		postShuffle["channels"].addChild( postShuffle.ChannelPlug( "R", "holdoutR" ) )
		postShuffle["channels"].addChild( postShuffle.ChannelPlug( "G", "holdoutG" ) )
		postShuffle["channels"].addChild( postShuffle.ChannelPlug( "B", "holdoutB" ) )
		postShuffle["channels"].addChild( postShuffle.ChannelPlug( "A", "holdoutA" ) )

		channelCleanup = GafferImage.DeleteChannels()
		channelCleanup["in"].setInput( postShuffle["out"] )
		channelCleanup["mode"].setValue( GafferImage.DeleteChannels.Mode.Keep )
		channelCleanup["channels"].setValue( '[RGBAZ]' )

		cropCleanup = GafferImage.Crop()
		cropCleanup["in"].setInput( channelCleanup["out"] )
		cropCleanup["area"].setValue( imath.Box2i( imath.V2i( 0, 0 ), imath.V2i( 150, 100 ) ) )

		self.assertImagesEqual( holdout["out"], cropCleanup["out"], maxDifference = 1e-5 )


		# The way we handle Z is a bit arbitrary, but everything else we should be able to match with
		# this network with arbitrary inputs
		holdoutNoZ = GafferImage.DeleteChannels()
		holdoutNoZ["in"].setInput( holdout["out"] )
		holdoutNoZ["channels"].setValue( 'Z' )

		channelCleanup["channels"].setValue( '[RGBA]' )

		offset["offset"].setValue( imath.V2i( 13, 31 ) )
		self.assertImagesEqual( holdoutNoZ["out"], cropCleanup["out"], maxDifference = 1e-5 )

		offset["offset"].setValue( imath.V2i( -13, -51 ) )
		self.assertImagesEqual( holdoutNoZ["out"], cropCleanup["out"], maxDifference = 1e-5 )

		offset["offset"].setValue( imath.V2i( 103, -27 ) )
		self.assertImagesEqual( holdoutNoZ["out"], cropCleanup["out"], maxDifference = 1e-5 )

	def testDirtyPropagation( self ):
		a = GafferImage.Constant()
		b = GafferImage.Constant()
		aShuffle = GafferImage.Shuffle()
		aShuffle["in"].setInput( a["out"] )
		bShuffle = GafferImage.Shuffle()
		bShuffle["in"].setInput( b["out"] )
		holdout = GafferImage.DeepHoldout()
		holdout["in"].setInput( aShuffle["out"] )
		holdout["holdout"].setInput( bShuffle["out"] )

		cs = GafferTest.CapturingSlot( holdout.plugDirtiedSignal() )

		a["color"]["r"].setValue( 0.5 )
		dirtiedPlugs = { x[0].relativeName( holdout ) for x in cs }
		self.assertIn( "__intermediateIn.channelData", dirtiedPlugs )
		self.assertIn( "__flattened.channelData", dirtiedPlugs )
		self.assertIn( "out.channelData", dirtiedPlugs )
		del cs[:]

		b["color"]["a"].setValue( 0.5 )
		dirtiedPlugs = { x[0].relativeName( holdout ) for x in cs }
		self.assertIn( "__flattened.channelData", dirtiedPlugs )
		self.assertIn( "out.channelData", dirtiedPlugs )
		del cs[:]

		aShuffle["channels"].addChild( bShuffle.ChannelPlug( "Z", "__white" ) )
		dirtiedPlugs = { x[0].relativeName( holdout ) for x in cs }
		self.assertIn( "__intermediateIn.channelData", dirtiedPlugs )
		self.assertIn( "__flattened.channelData", dirtiedPlugs )
		self.assertIn( "out.channelData", dirtiedPlugs )
		self.assertIn( "__intermediateIn.channelNames", dirtiedPlugs )
		self.assertIn( "__flattened.channelNames", dirtiedPlugs )
		self.assertIn( "out.channelNames", dirtiedPlugs )
		del cs[:]

		bShuffle["channels"].addChild( bShuffle.ChannelPlug( "Z", "__white" ) )
		dirtiedPlugs = { x[0].relativeName( holdout ) for x in cs }
		self.assertIn( "__flattened.channelData", dirtiedPlugs )
		self.assertIn( "out.channelData", dirtiedPlugs )
		self.assertIn( "__flattened.channelNames", dirtiedPlugs )
		del cs[:]

if __name__ == "__main__":
	unittest.main()
