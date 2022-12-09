##########################################################################
#
#  Copyright (c) 2015, John Haddon. All rights reserved.
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
import pathlib

import IECore

import Gaffer
import GafferImage
import GafferImageTest
import os

class BlurTest( GafferImageTest.ImageTestCase ) :

	def testPassThrough( self ) :

		c = GafferImage.Constant()

		b = GafferImage.Blur()
		b["in"].setInput( c["out"] )
		b["radius"].setValue( imath.V2f( 0 ) )

		self.assertImageHashesEqual( c["out"], b["out"] )
		self.assertImagesEqual( c["out"], b["out"] )

	def testNonFlatThrows( self ) :

		blur = GafferImage.Blur()
		blur["radius"].setValue( imath.V2f( 1 ) )

		self.assertRaisesDeepNotSupported( blur )

	def testExpandDataWindow( self ) :

		c = GafferImage.Constant()

		b = GafferImage.Blur()
		b["in"].setInput( c["out"] )
		b["radius"].setValue( imath.V2f( 1 ) )

		self.assertEqual( b["out"]["dataWindow"].getValue(), c["out"]["dataWindow"].getValue() )

		b["expandDataWindow"].setValue( True )

		self.assertEqual( b["out"]["dataWindow"].getValue().min(), c["out"]["dataWindow"].getValue().min() - imath.V2i( 2 ) )
		self.assertEqual( b["out"]["dataWindow"].getValue().max(), c["out"]["dataWindow"].getValue().max() + imath.V2i( 2 ) )

	def testOnePixelBlur( self ) :

		constant = GafferImage.Constant()
		constant["color"].setValue( imath.Color4f( 1 ) )

		crop = GafferImage.Crop()
		crop["in"].setInput( constant["out"] )
		crop["area"].setValue( imath.Box2i( imath.V2i( 10 ), imath.V2i( 11 ) ) )
		crop["affectDisplayWindow"].setValue( False )

		blur = GafferImage.Blur()
		blur["in"].setInput( crop["out"] )
		blur["radius"].setValue( imath.V2f( 1 ) )
		blur["expandDataWindow"].setValue( True )

		sampler = GafferImage.Sampler( blur["out"], "R", imath.Box2i( imath.V2i( 0 ), imath.V2i( 20 ) ) )

		# Centre is brightest
		self.assertGreater( sampler.sample( 10, 10 ), sampler.sample( 11, 10 ) )

		# Corners are least bright
		self.assertGreater( sampler.sample( 11, 10 ), sampler.sample( 11, 11 ) )
		self.assertGreater( sampler.sample( 11, 11 ), 0 )

		# Shape is symmetrical
		self.assertEqual( sampler.sample( 11, 10 ), sampler.sample( 9, 10 ) )
		self.assertEqual( sampler.sample( 10, 11 ), sampler.sample( 10, 9 ) )
		self.assertEqual( sampler.sample( 10, 11 ), sampler.sample( 10, 9 ) )

		self.assertEqual( sampler.sample( 9, 9 ), sampler.sample( 11, 9 ) )
		self.assertEqual( sampler.sample( 9, 9 ), sampler.sample( 11, 11 ) )
		self.assertEqual( sampler.sample( 9, 9 ), sampler.sample( 9, 11 ) )

	def testEnergyPreservation( self ) :

		constant = GafferImage.Constant()
		constant["color"].setValue( imath.Color4f( 1 ) )

		crop = GafferImage.Crop()
		crop["in"].setInput( constant["out"] )
		crop["area"].setValue( imath.Box2i( imath.V2i( 10 ), imath.V2i( 11 ) ) )
		crop["affectDisplayWindow"].setValue( False )

		blur = GafferImage.Blur()
		blur["in"].setInput( crop["out"] )
		blur["expandDataWindow"].setValue( True )

		stats = GafferImage.ImageStats()
		stats["in"].setInput( blur["out"] )
		stats["area"].setValue( imath.Box2i( imath.V2i( 5 ), imath.V2i( 15 ) ) )

		for i in range( 0, 10 ) :

			blur["radius"].setValue( imath.V2f( i * 0.5 ) )
			self.assertAlmostEqual( stats["average"]["r"].getValue(), 1 / 100., delta = 0.0001 )

	def testBlurRange( self ):

		constant = GafferImage.Constant()
		constant["format"].setValue( GafferImage.Format( 5, 5, 1.000 ) )
		constant["color"].setValue( imath.Color4f( 1, 1, 1, 1 ) )



		cropDot = GafferImage.Crop()
		cropDot["area"].setValue( imath.Box2i( imath.V2i( 2, 2 ), imath.V2i( 3, 3 ) ) )
		cropDot["affectDisplayWindow"].setValue( False )
		cropDot["in"].setInput( constant["out"] )

		blur = GafferImage.Blur()
		blur["expandDataWindow"].setValue( True )
		blur["in"].setInput( cropDot["out"] )
		blur["radius"]["y"].setInput( blur["radius"]["x"] )

		expression = Gaffer.Expression()
		blur.addChild( expression )
		expression.setExpression( 'parent["radius"]["x"] = context[ "loop:index" ] * 0.2', "python" )

		loopInit = GafferImage.Constant()
		loopInit["format"].setValue( GafferImage.Format( 5, 5, 1.000 ) )

		imageLoop = Gaffer.Loop()
		imageLoop.setup( GafferImage.ImagePlug() )
		imageLoop["in"].setInput( loopInit["out"] )

		merge = GafferImage.Merge()
		merge["in"].addChild( GafferImage.ImagePlug( "in2", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ) )
		merge["in"]["in0"].setInput( blur["out"] )
		merge["in"]["in1"].setInput( imageLoop["previous"] )

		offset = GafferImage.Offset()
		offset["offset"].setValue( imath.V2i( -5, 0 ) )
		offset["in"].setInput( merge["out"] )

		imageLoop["next"].setInput( offset["out"] )

		deleteChannels = GafferImage.DeleteChannels()
		deleteChannels["mode"].setValue( GafferImage.DeleteChannels.Mode.Keep )
		deleteChannels["channels"].setValue( IECore.StringVectorData( [ 'R' ] ) )
		deleteChannels["in"].setInput( imageLoop["out"] )

		finalCrop = GafferImage.Crop()
		finalCrop["areaSource"].setValue( 1 )
		finalCrop["in"].setInput( deleteChannels["out"] )

		# Enable to write out images for visual comparison
		if False:
			testWriter = GafferImage.ImageWriter()
			testWriter["in"].setInput( finalCrop["out"] )
			testWriter["fileName"].setValue( "/tmp/blurRange.exr" )
			testWriter["openexr"]["dataType"].setValue( 'float' )
			testWriter["task"].execute()

		expectedReader = GafferImage.ImageReader()
		expectedReader["fileName"].setValue( pathlib.Path( __file__ ).parent / "images" / "blurRange.exr" )

		self.assertImagesEqual( finalCrop["out"], expectedReader["out"], maxDifference = 0.00001, ignoreMetadata = True )

if __name__ == "__main__":
	unittest.main()
