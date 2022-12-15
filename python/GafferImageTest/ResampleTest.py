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
import pathlib
import shutil
import unittest
import subprocess
import time

import imath

import IECore

import Gaffer
import GafferTest
import GafferImage
import GafferImageTest

class ResampleTest( GafferImageTest.ImageTestCase ) :

	def testDataWindow( self ) :

		c = GafferImage.Constant()
		c["format"].setValue( GafferImage.Format( 100, 100 ) )
		c["color"].setValue( imath.Color4f( 1 ) )

		r = GafferImage.Resample()
		r["in"].setInput( c["out"] )
		r["matrix"].setValue(
			imath.M33f().translate( imath.V2f( 10.5, 11.5 ) ).scale( imath.V2f( 0.1 ) )
		)

		self.assertEqual(
			r["out"]["dataWindow"].getValue(),
			imath.Box2i(
				imath.V2i( 10, 11 ),
				imath.V2i( 21, 22 )
			)
		)

	def testExpectedOutput( self ) :

		def __test( fileName, size, filter ) :

			inputFileName = self.imagesPath() / fileName

			reader = GafferImage.ImageReader()
			reader["fileName"].setValue( inputFileName )

			inSize = reader["out"]["format"].getValue().getDisplayWindow().size()
			inSize = imath.V2f( inSize.x, inSize.y )

			resample = GafferImage.Resample()
			resample["in"].setInput( reader["out"] )
			resample["matrix"].setValue(
				imath.M33f().scale( imath.V2f( size.x, size.y ) / inSize )
			)
			resample["filter"].setValue( filter )
			resample["boundingMode"].setValue( GafferImage.Sampler.BoundingMode.Clamp )

			crop = GafferImage.Crop()
			crop["in"].setInput( resample["out"] )
			crop["area"].setValue( imath.Box2i( imath.V2i( 0 ), size ) )

			outputFileName = self.temporaryDirectory() / ( "%s_%dx%d_%s.exr" % ( pathlib.Path( fileName ).with_suffix(""), size.x, size.y, filter ) )
			writer = GafferImage.ImageWriter()
			writer["in"].setInput( crop["out"] )
			writer["channels"].setValue( "[RGB]" )
			writer["fileName"].setValue( outputFileName )
			writer["task"].execute()

			result = GafferImage.ImageReader()
			result["fileName"].setValue( writer["fileName"].getValue() )

			expected = GafferImage.ImageReader()
			expected["fileName"].setValue(
				self.imagesPath() / (
					"%s_%dx%d_%s.exr" % (
						pathlib.Path( fileName ).with_suffix(""),
						size.x,
						size.y,
						filter
					)
				)
			)

			self.assertImagesEqual( result["out"], expected["out"], maxDifference = 0.0005, ignoreMetadata = True )

			# Enable to write out images for visual comparison with OIIO.
			# The images will appear in a "resampleComparison" subdirectory
			# of the current directory.
			if False :

				resampleComparisonDir = pathlib.Path( "resampleComparison" )
				resampleComparisonDir.mkdir( exist_ok=True )

				shutil.copyfile( outputFileName, resampleComparisonDir / ( "gaffer_" + outputFileName.name ) )

				oiioOutputFileName = resampleComparisonDir / ( "oiio_%s_%dx%d_%s.exr" % ( pathlib.Path( fileName ).with_suffix(""), size.x, size.y, filter ) )

				subprocess.check_call(
					"oiiotool --threads 1 %s --ch R,G,B --resize:filter=%s %dx%d  -o %s" %
					(
						inputFileName,
						filter,
						size.x, size.y,
						oiioOutputFileName
					),
					shell = True
				)

		tests = [
			( "resamplePatterns.exr", imath.V2i( 4 ), "lanczos3" ),
			( "resamplePatterns.exr", imath.V2i( 40 ), "box" ),
			( "resamplePatterns.exr", imath.V2i( 101 ), "gaussian" ),
			( "resamplePatterns.exr", imath.V2i( 119 ), "mitchell" ),
		]

		for args in tests :
			__test( *args )

	def testSincUpsize( self ) :

		c = GafferImage.Constant()
		c["format"].setValue( GafferImage.Format( 100, 100 ) )
		c["color"].setValue( imath.Color4f( 1 ) )

		r = GafferImage.Resample()
		r["matrix"].setValue( imath.M33f().scale( imath.V2f( 4 ) ) )
		r["boundingMode"].setValue( GafferImage.Sampler.BoundingMode.Clamp )
		r["filter"].setValue( "sinc" )
		r["in"].setInput( c["out"] )

		i = GafferImage.ImageAlgo.image( r["out"] )
		self.assertEqual( i["R"], IECore.FloatVectorData( [ 1.0 ] * 400 * 400 ) )

	def testExpandDataWindow( self ) :

		d = imath.Box2i( imath.V2i( 5, 6 ), imath.V2i( 101, 304 ) )
		c = GafferImage.Constant()
		c["format"].setValue( GafferImage.Format( d ) )

		r = GafferImage.Resample()
		r["in"].setInput( c["out"] )
		r["filter"].setValue( "box" )
		self.assertEqual( r["out"]["dataWindow"].getValue(), d )

		r["expandDataWindow"].setValue( True )
		self.assertEqual( r["out"]["dataWindow"].getValue(), imath.Box2i( d.min() - imath.V2i( 1 ), d.max() + imath.V2i( 1 ) ) )

		r["filterScale"].setValue( imath.V2f( 10 ) )
		self.assertEqual( r["out"]["dataWindow"].getValue(), imath.Box2i( d.min() - imath.V2i( 5 ), d.max() + imath.V2i( 5 ) ) )

	def testCancellation( self ) :

		c = GafferImage.Constant()

		r = GafferImage.Resample()
		r["in"].setInput( c["out"] )
		r["filterScale"].setValue( imath.V2f( 2000 ) )

		bt = Gaffer.ParallelAlgo.callOnBackgroundThread( r["out"], lambda : GafferImageTest.processTiles( r["out"] ) )
		# Give background tasks time to get into full swing
		time.sleep( 0.1 )

		# Check that we can cancel them in reasonable time
		acceptableCancellationDelay = 4.0 if GafferTest.inCI() else 0.25
		t = time.time()
		bt.cancelAndWait()
		self.assertLess( time.time() - t, acceptableCancellationDelay )

		# Check that we can do the same when using a non-separable filter
		r["filter"].setValue( "disk" )

		bt = Gaffer.ParallelAlgo.callOnBackgroundThread( r["out"], lambda : GafferImageTest.processTiles( r["out"] ) )
		time.sleep( 0.1 )

		t = time.time()
		bt.cancelAndWait()
		self.assertLess( time.time() - t, acceptableCancellationDelay )

	def testNonFlatThrows( self ) :

		resample = GafferImage.Resample()
		resample["matrix"].setValue( imath.M33f().scale( imath.V2f( 0.5 ) ) )

		self.assertRaisesDeepNotSupported( resample )

if __name__ == "__main__":
	unittest.main()
