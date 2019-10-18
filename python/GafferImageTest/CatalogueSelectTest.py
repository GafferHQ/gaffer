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
import IECore

import GafferImage
import GafferImageTest


class CatalogueSelectTest( GafferImageTest.ImageTestCase ) :

	def testSelection( self ):

		# Set up Catalogue with images that we can select

		images = []
		readers = []
		fileNames = [ "checker.exr", "blurRange.exr", "noisyRamp.exr", "resamplePatterns.exr" ]
		for fileName in fileNames :
			images.append( GafferImage.Catalogue.Image.load( "${GAFFER_ROOT}/python/GafferImageTest/images/" + fileName ) )
			readers.append( GafferImage.ImageReader() )
			readers[-1]["fileName"].setValue( images[-1]["fileName"].getValue() )

		c = GafferImage.Catalogue()

		for image in images :
			c["images"].addChild( image )

		# Pulling out images by name

		for i, fileName in enumerate( fileNames ) :
			catalogueSelect = GafferImage.CatalogueSelect()
			catalogueSelect["in"].setInput( c["out"] )
			catalogueSelect["imageName"].setValue( fileName.split( "." )[0] )

			self.assertImagesEqual( catalogueSelect["out"], readers[i]["out"], ignoreMetadata = True )

		# Pulling out image that is selected in the Catalogue UI

		catalogueSelect = GafferImage.CatalogueSelect()
		catalogueSelect["in"].setInput( c["out"] )
		catalogueSelect["imageName"].setValue( "" )

		self.assertImagesEqual( catalogueSelect["out"], c["out"] )

		# Pulling out invalid image

		catalogueSelect["imageName"].setValue("nope")
		with self.assertRaises( Exception ) as cm:
			GafferImage.ImageAlgo.image( catalogueSelect["out"] )

		self.assertEqual( str( cm.exception ), "CatalogueSelect.__context.out.format : Unknown image name." )
