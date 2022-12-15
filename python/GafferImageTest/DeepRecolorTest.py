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

class DeepRecolorTest( GafferImageTest.ImageTestCase ) :

	representativeImagePath = GafferImageTest.ImageTestCase.imagesPath() / "representativeDeepImage.exr"
	flatImagePath = GafferImageTest.ImageTestCase.imagesPath() / "rgb.100x100.exr"

	def testBasics( self ):
		representativeImage = GafferImage.ImageReader()
		representativeImage["fileName"].setValue( self.representativeImagePath )

		flatImage = GafferImage.ImageReader()
		flatImage["fileName"].setValue( self.flatImagePath )

		rc = GafferImage.DeepRecolor()
		rc["in"].setInput( representativeImage["out"] )
		rc["colorSource"].setInput( flatImage["out"] )

		representativeSampleCounts = GafferImage.DeepSampleCounts()
		representativeSampleCounts["in"].setInput( representativeImage["out"] )

		rcSampleCounts = GafferImage.DeepSampleCounts()
		rcSampleCounts["in"].setInput( rc["out"] )

		# Make sure we keep all the deep samples
		self.assertImagesEqual( representativeSampleCounts["out"], rcSampleCounts["out"] )

		rcFlat = GafferImage.DeepToFlat()
		rcFlat["in"].setInput( rc["out"] )

		representativeFlat = GafferImage.DeepToFlat()
		representativeFlat["in"].setInput( representativeImage["out"] )

		unpremult = GafferImage.Unpremultiply()
		unpremult["in"].setInput( flatImage["out"] )

		flatCombine = GafferImage.CopyChannels()
		flatCombine["in"][0].setInput( representativeFlat["out"] )
		flatCombine["in"][1].setInput( unpremult["out"] )
		flatCombine["channels"].setValue( "[RGB]" )

		premult = GafferImage.Premultiply()
		premult["in"].setInput( flatCombine["out"] )

		# Make sure that the default recolor matches the flat value of premulting by the deep alpha
		self.assertImagesEqual( rcFlat["out"], premult["out"], maxDifference = 1e-6 )

		compare = GafferImage.Merge()
		compare["in"][0].setInput( rcFlat["out"] )
		compare["in"][1].setInput( premult["out"] )
		compare["operation"].setValue( GafferImage.Merge.Operation.Difference )

		compareStats = GafferImage.ImageStats()
		compareStats["in"].setInput( compare["out"] )
		compareStats["area"].setValue( imath.Box2i( imath.V2i( 0, 0 ), imath.V2i( 150, 100 ) ) )

		m = compareStats["max"].getValue()
		a = compareStats["average"].getValue()
		for i in range( 4 ):
			self.assertLessEqual( m[i], 1e-6 )
			self.assertLessEqual( a[i], 1e-8 )

		rc["useColorSourceAlpha"].setValue( True )

		m = compareStats["max"].getValue()
		a = compareStats["average"].getValue()
		for i in range( 3 ):
			self.assertGreater( m[i], 0.4 )
			self.assertGreater( a[i], 0.0001 )

		# Make sure that using useColorSourceAlpha basically matches the original color source after
		# flattening.  ( It's not exact because of a few pixels with zero samples in the deep which
		# we can't do anything with )
		compare["in"][1].setInput( flatImage["out"] )

		m = compareStats["max"].getValue()
		a = compareStats["average"].getValue()
		for i in range( 4 ):
			self.assertLessEqual( m[i], 0.5 )
			self.assertLessEqual( a[i], 0.0003 )


if __name__ == "__main__":
	unittest.main()
