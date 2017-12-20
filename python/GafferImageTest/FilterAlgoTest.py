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
#      * Neither the name of Image Engine Design nor the names of
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
import IECoreImage

import Gaffer
import GafferImage
import GafferImageTest
import math

class FilterAlgoTest( GafferImageTest.ImageTestCase ) :

	derivativesReferenceParallelFileName = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/filterDerivativesTest.parallel.exr" )
	derivativesReferenceBoxFileName = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/filterDerivativesTest.box.exr" )

	# Artificial test of several filters passing in different derivatives, including a bunch of 15 degree rotations
	def testFilterDerivatives( self ):
		# Size of one grid cell
		subSize = 35

		# Each grid cell gets a dot in the middle
		redDot = GafferImage.Constant()
		redDot["format"].setValue( GafferImage.Format( 1, 1, 1.000 ) )
		redDot["color"].setValue( imath.Color4f( 10, 0, 0, 1 ) )
		redDotCentered = GafferImage.Crop( "Crop" )
		redDotCentered["in"].setInput( redDot["out"] )
		redDotCentered["area"].setValue( imath.Box2i( imath.V2i( -(subSize-1)/2 ), imath.V2i( (subSize-1)/2 + 1 ) ) )

		borderForFilterWidth = 40
		sampleRegion = redDotCentered["out"]["dataWindow"].getValue()
		sampleRegion.setMin( sampleRegion.min() - imath.V2i( borderForFilterWidth ) )
		sampleRegion.setMax( sampleRegion.max() + imath.V2i( borderForFilterWidth ) )

		s = GafferImage.Sampler( redDotCentered["out"], "R", sampleRegion, GafferImage.Sampler.BoundingMode.Black )

		filters = GafferImage.FilterAlgo.filterNames()
		dirs = [
			(imath.V2f(1,0), imath.V2f(0,1)),
			(imath.V2f(5,0), imath.V2f(0,1)),
			(imath.V2f(1,0), imath.V2f(0,5)),
			(imath.V2f(5,0), imath.V2f(0,5)) ]

		for angle in range( 0, 91, 15 ):
			sa = math.sin( angle / 180.0 * math.pi )
			ca = math.cos( angle / 180.0 * math.pi )
			dirs.append( ( imath.V2f(ca * 5, sa * 5 ), imath.V2f(-sa * 3, ca * 3 ) ) )

		size = subSize * imath.V2i( len( dirs ), len( filters ) )
		w = imath.Box2i( imath.V2i( 0 ), size - imath.V2i( 1 ) )
		parallelogramImage = IECoreImage.ImagePrimitive( w, w )
		boxImage = IECoreImage.ImagePrimitive( w, w )

		parallelogramR = IECore.FloatVectorData( size[0] * size[1] )
		boxR = IECore.FloatVectorData( size[0] * size[1] )

		for x_sub, d in enumerate( dirs ):
			for y_sub, f in enumerate( filters ):
				for y in range( subSize ):
					for x in range( subSize ):
						p = imath.V2f( x + 0.5, y + 0.5 )
						inputDerivatives = GafferImage.FilterAlgo.derivativesToAxisAligned( p, d[0], d[1] )


						boxR[ ( y_sub * subSize + y ) * size[0] + x_sub * subSize + x ] = GafferImage.FilterAlgo.sampleBox(
							s, p, inputDerivatives[0], inputDerivatives[1], f )
						parallelogramR[ ( y_sub * subSize + y ) * size[0] + x_sub * subSize + x ] = GafferImage.FilterAlgo.sampleParallelogram(
							s, p, d[0], d[1], f )

		parallelogramImage["R"] = parallelogramR
		boxImage["R"] = boxR

		# Enable to write out images for visual comparison
		if False:
			IECore.Writer.create( parallelogramImage, "/tmp/filterDerivativesTestResult.parallelogram.exr" ).write()
			IECore.Writer.create( boxImage, "/tmp/filterDerivativesTestResult.box.exr" ).write()

		imageNode = GafferImage.ObjectToImage()
		imageNode["object"].setValue( parallelogramImage )

		expectedImage = GafferImage.ImageReader()
		expectedImage["fileName"].setValue( self.derivativesReferenceParallelFileName )

		self.assertImagesEqual( imageNode["out"], expectedImage["out"], ignoreMetadata = True, maxDifference = 0.000005 )

		imageNode["object"].setValue( boxImage )
		expectedImage["fileName"].setValue( self.derivativesReferenceBoxFileName )

		self.assertImagesEqual( imageNode["out"], expectedImage["out"], ignoreMetadata = True, maxDifference = 0.000005 )

	def testMatchesResample( self ):
		def __test( fileName, size, filter ) :

			inputFileName = os.path.dirname( __file__ ) + "/images/" + fileName

			reader = GafferImage.ImageReader()
			reader["fileName"].setValue( inputFileName )

			inSize = reader["out"]["format"].getValue().getDisplayWindow().size()
			inSize = imath.V2f( inSize.x, inSize.y )

			deleteChannels = GafferImage.DeleteChannels()
			deleteChannels["mode"].setValue( 1 )
			deleteChannels["channels"].setValue( IECore.StringVectorData( [ 'R' ] ) )
			deleteChannels["in"].setInput( reader["out"] )


			scale = imath.V2f( size.x, size.y ) / inSize

			resample = GafferImage.Resample()
			resample["in"].setInput( deleteChannels["out"] )
			resample["matrix"].setValue(
				imath.M33f().scale( scale )
			)
			resample["filter"].setValue( filter )
			resample["boundingMode"].setValue( GafferImage.Sampler.BoundingMode.Clamp )

			crop = GafferImage.Crop()
			crop["in"].setInput( resample["out"] )
			crop["area"].setValue( imath.Box2i( imath.V2i( 0 ), size ) )

			borderForFilterWidth = 60
			sampleRegion = reader["out"]["dataWindow"].getValue()
			sampleRegion.setMin( sampleRegion.min() - imath.V2i( borderForFilterWidth ) )
			sampleRegion.setMax( sampleRegion.max() + imath.V2i( borderForFilterWidth ) )

			s = GafferImage.Sampler( reader["out"], "R", sampleRegion, GafferImage.Sampler.BoundingMode.Clamp )

			w = imath.Box2i( imath.V2i( 0 ), size - imath.V2i( 1 ) )
			boxImage = IECoreImage.ImagePrimitive( w, w )
			parallelImage = IECoreImage.ImagePrimitive( w, w )

			boxR = IECore.FloatVectorData( size.x * size.y )
			parallelR = IECore.FloatVectorData( size.x * size.y )

			for y in range( size.y ):
				for x in range( size.x ):
						boxR[ ( size.y - 1 - y ) * size.x + x ] = GafferImage.FilterAlgo.sampleBox(
							s,
							imath.V2f( x + 0.5, y + 0.5 ) / scale,
							max( 1.0 / scale[0], 1.0 ),
							max( 1.0 / scale[1], 1.0 ),
							filter )
						parallelR[ ( size.y - 1 - y ) * size.x + x ] = GafferImage.FilterAlgo.sampleParallelogram(
							s,
							imath.V2f( x + 0.5, y + 0.5 ) / scale,
							imath.V2f( 1.0 / scale[0], 0),
							imath.V2f( 0, 1.0 / scale[1]),
							filter )

			boxImage["R"] = boxR
			parallelImage["R"] = parallelR

			# Enable to write out images for visual comparison
			if False:
				tempDirectory = "/tmp"
				expectedFileName = tempDirectory + "/%s_%dx%d_%s_expected.exr" % ( os.path.splitext( fileName )[0], size.x, size.y, filter )
				expectedWriter = GafferImage.ImageWriter()
				expectedWriter["in"].setInput( crop["out"] )
				expectedWriter["fileName"].setValue( expectedFileName )
				expectedWriter["task"].execute()

				outputFileName = tempDirectory + "/%s_%dx%d_%s.box.exr" % ( os.path.splitext( fileName )[0], size.x, size.y, filter )
				IECore.Writer.create( boxImage, outputFileName ).write()
				outputFileName = tempDirectory + "/%s_%dx%d_%s.parallel.exr" % ( os.path.splitext( fileName )[0], size.x, size.y, filter )
				IECore.Writer.create( parallelImage, outputFileName ).write()

			imageNode = GafferImage.ObjectToImage()
			imageNode["object"].setValue( boxImage )
			self.assertImagesEqual( crop["out"], imageNode["out"], maxDifference = 0.000011, ignoreMetadata = True )

			imageNode["object"].setValue( parallelImage )
			self.assertImagesEqual( crop["out"], imageNode["out"], maxDifference = 0.000011, ignoreMetadata = True )

		tests = [
			( "resamplePatterns.exr", imath.V2i( 4 ), "lanczos3" ),
			( "resamplePatterns.exr", imath.V2i( 40 ), "box" ),
			( "resamplePatterns.exr", imath.V2i( 101 ), "gaussian" ),
			( "resamplePatterns.exr", imath.V2i( 119 ), "mitchell" ),
			( "resamplePatterns.exr", imath.V2i( 300 ), "sinc" ),
		]

		for args in tests :
			__test( *args )



if __name__ == "__main__":
	unittest.main()
