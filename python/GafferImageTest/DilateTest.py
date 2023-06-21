##########################################################################
#
#  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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
import imath

import IECore

import Gaffer
import GafferTest
import GafferImage
import GafferImageTest

class DilateTest( GafferImageTest.ImageTestCase ) :

	def testPassThrough( self ) :

		c = GafferImage.Constant()

		m = GafferImage.Dilate()
		m["in"].setInput( c["out"] )
		m["radius"].setValue( imath.V2i( 0 ) )

		self.assertEqual( GafferImage.ImageAlgo.imageHash( c["out"] ), GafferImage.ImageAlgo.imageHash( m["out"] ) )
		self.assertImagesEqual( c["out"], m["out"] )

	def testExpandDataWindow( self ) :

		c = GafferImage.Constant()

		m = GafferImage.Dilate()
		m["in"].setInput( c["out"] )
		m["radius"].setValue( imath.V2i( 1 ) )

		self.assertEqual( m["out"]["dataWindow"].getValue(), c["out"]["dataWindow"].getValue() )

		m["expandDataWindow"].setValue( True )

		self.assertEqual( m["out"]["dataWindow"].getValue().min(), c["out"]["dataWindow"].getValue().min() - imath.V2i( 1 ) )
		self.assertEqual( m["out"]["dataWindow"].getValue().max(), c["out"]["dataWindow"].getValue().max() + imath.V2i( 1 ) )

	def testFilter( self ) :

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.imagesPath() / "radial.exr" )

		m = GafferImage.Dilate()
		m["in"].setInput( r["out"] )
		self.assertImagesEqual( m["out"], r["out"] )

		m["radius"].setValue( imath.V2i( 12 ) )
		m["boundingMode"].setValue( GafferImage.Sampler.BoundingMode.Clamp )

		dataWindow = m["out"]["dataWindow"].getValue()
		s = GafferImage.Sampler( m["out"], "R", dataWindow )

		self.assertEqual( s.sample( 112, 112 ), 1.0 )

	def testShape( self ):
		constant1 = GafferImage.Constant( "constant1" )
		constant1["color"].setValue( imath.Color4f( 1, 1, 1, 1 ) )
		crop1 = GafferImage.Crop( "crop1" )
		crop1["in"].setInput( constant1["out"] )
		crop1["area"].setValue( imath.Box2i( imath.V2i( 3, 7 ), imath.V2i( 4, 8 ) ) )
		crop1["affectDisplayWindow"].setValue( False )

		constant2 = GafferImage.Constant( "constant2" )
		constant2["color"].setValue( imath.Color4f( 2, 2, 2, 1 ) )
		crop2 = GafferImage.Crop( "crop2" )
		crop2["in"].setInput( constant2["out"] )
		crop2["area"].setValue( imath.Box2i( imath.V2i( 6, 4 ), imath.V2i( 7, 5 ) ) )
		crop2["affectDisplayWindow"].setValue( False )

		merge = GafferImage.Merge( "merge" )
		merge["in"][0].setInput( crop1["out"] )
		merge["in"][1].setInput( crop2["out"] )
		merge["operation"].setValue( 8 )

		dilate = GafferImage.Dilate( "dilate" )
		dilate["in"].setInput( merge["out"] )
		dilate["expandDataWindow"].setValue( True )

		expectedResultsText = """
0000000000 0000000000 0000000000
0000000000 0000000000 0000000000
0000000000 0000000000 0000222220
0000000000 0000022200 0000222220
0000002000 0000022200 0000222220
0000000000 0000022200 0111222220
0000000000 0011100000 0111222220
0001000000 0011100000 0111110000
0000000000 0011100000 0111110000
0000000000 0000000000 0111110000
"""
		expectedResults = expectedResultsText.splitlines()[1:]

		for r in [ 0, 1, 2 ]:
			dilate["radius"].setValue( imath.V2i( r ) )

			s = GafferImage.Sampler( dilate['out'], "R", imath.Box2i( imath.V2i( 0 ), imath.V2i( 10 ) ) )
			for y in range( 10 ):
				for x in range( 10 ):
					self.assertEqual( s.sample( x, y ), int( expectedResults[ y ][ x + r * 11 ] ) )

	def testDriverChannel( self ) :

		rRaw = GafferImage.ImageReader()
		rRaw["fileName"].setValue( self.imagesPath() / "circles.exr" )

		r = GafferImage.Grade()
		r["in"].setInput( rRaw["out"] )
		# Trim off the noise in the blacks so that areas with no visible color are actually flat
		r["blackPoint"].setValue( imath.Color4f( 0.03 ) )


		masterDilate = GafferImage.Dilate()
		masterDilate["in"].setInput( r["out"] )
		masterDilate["radius"].setValue( imath.V2i( 2 ) )

		masterDilate["masterChannel"].setValue( "G" )

		expected = GafferImage.ImageReader()
		expected["fileName"].setValue( self.imagesPath() / "circlesGreenDilate.exr" )

		# Note that in this expected image, the green channel is nicely medianed, and red and blue are completely
		# unchanged in areas where there is no green.  In areas where red and blue overlap with a noisy green,
		# they get a bit scrambled.  This is why in practice, you would use something like luminance, rather
		# than just the green channel
		self.assertImagesEqual( masterDilate["out"], expected["out"], ignoreMetadata = True, maxDifference=0.0005 )


		defaultDilate = GafferImage.Dilate()
		defaultDilate["in"].setInput( r["out"] )
		defaultDilate["radius"].setValue( imath.V2i( 2 ) )

		masterDilateSingleChannel = GafferImage.DeleteChannels()
		masterDilateSingleChannel["in"].setInput( masterDilate["out"] )
		masterDilateSingleChannel["mode"].setValue( GafferImage.DeleteChannels.Mode.Keep )

		defaultDilateSingleChannel = GafferImage.DeleteChannels()
		defaultDilateSingleChannel["in"].setInput( defaultDilate["out"] )
		defaultDilateSingleChannel["mode"].setValue( GafferImage.DeleteChannels.Mode.Keep )

		for c in [ "R", "G", "B" ]:
			masterDilate["masterChannel"].setValue( c )
			masterDilateSingleChannel["channels"].setValue( c )
			defaultDilateSingleChannel["channels"].setValue( c )

			# When we look at just the channel being used as the master, it matches a default median not using
			# a master
			self.assertImagesEqual( masterDilateSingleChannel["out"], defaultDilateSingleChannel["out"] )

	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 1 )
	def testPerf( self ) :

		imageReader = GafferImage.ImageReader()
		imageReader["fileName"].setValue( self.imagesPath() / 'deepMergeReference.exr' )

		GafferImageTest.processTiles( imageReader["out"] )

		dilate = GafferImage.Dilate()
		dilate["in"].setInput( imageReader["out"] )
		dilate["radius"].setValue( imath.V2i( 128 ) )

		with GafferTest.TestRunner.PerformanceScope() :
			GafferImageTest.processTiles( dilate["out"] )

if __name__ == "__main__":
	unittest.main()
