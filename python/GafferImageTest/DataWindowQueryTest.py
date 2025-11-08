##########################################################################
#
#  Copyright (c) 2025, Cinesite VFX Ltd. All rights reserved.
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
#      * Neither the name of Image Engine Design Inc nor the names of
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

import imath
import random
import unittest

import GafferImage
import GafferImageTest

class DataWindowQueryTest( GafferImageTest.ImageTestCase ) :

	def test( self ) :

		constant = GafferImage.Constant()
		constant["format"].setValue( GafferImage.Format( imath.Box2i( imath.V2i( 0 ), imath.V2i( 1024 ) ), 1 ) )

		crop = GafferImage.Crop()
		crop["in"].setInput( constant["out"] )
		crop["areaSource"].setValue( GafferImage.Crop.AreaSource.Area )
		crop["affectDataWindow"].setValue( True )
		crop["affectDisplayWindow"].setValue( False )

		dataWindowQuery = GafferImage.DataWindowQuery()
		dataWindowQuery["in"].setInput( crop["out"] )

		random.seed( 42 )
		for dataWindow in [
			imath.Box2i(
				imath.V2i( random.randrange( 0, 512 ), random.randrange( 0, 512) ),
				imath.V2i( random.randrange( 512, 1024 ), random.randrange( 512, 1024 ) )
			) for i in range( 0, 10 )
		] :
			crop["area"].setValue( dataWindow )
			self.assertEqual( dataWindowQuery["dataWindow"].getValue(), dataWindow )
			self.assertEqual( dataWindowQuery["center"].getValue(), imath.Box2f( imath.V2f( dataWindow.min() ), imath.V2f( dataWindow.max() ) ).center() )
			self.assertEqual( dataWindowQuery["size"].getValue(), dataWindow.size() )

		oddWindow = imath.Box2i( imath.V2i( 1 ), imath.V2i( 4 ) )
		crop["area"].setValue( oddWindow )
		self.assertEqual( dataWindowQuery["dataWindow"].getValue(), oddWindow )
		self.assertEqual( dataWindowQuery["center"].getValue(), imath.V2f( 2.5 ) )
		self.assertEqual( dataWindowQuery["size"].getValue(), imath.V2i( 3 ) )

	def testView( self ) :

		constant1 = GafferImage.Constant()
		smallBox = imath.Box2i( imath.V2i( 0 ), imath.V2i( 511 ) )
		smallBoxFloat = imath.Box2f( imath.V2f( smallBox.min() ), imath.V2f( smallBox.max() ) )
		constant1["format"].setValue( GafferImage.Format( smallBox, 1 ) )

		constant2 = GafferImage.Constant()
		bigBox = imath.Box2i( imath.V2i( 0 ), imath.V2i( 1023 ) )
		bigBoxFloat = imath.Box2f( imath.V2f( bigBox.min() ), imath.V2f( bigBox.max() ) )
		constant2["format"].setValue( GafferImage.Format( bigBox, 1 ) )

		createViews = GafferImage.CreateViews()
		createViews["views"].resize( 2 )
		createViews["views"][0]["name"].setValue( "viewA" )
		createViews["views"][1]["name"].setValue( "viewB" )
		createViews["views"]["view0"]["value"].setInput( constant1["out"] )
		createViews["views"]["view1"]["value"].setInput( constant2["out"] )

		dataWindowQuery = GafferImage.DataWindowQuery()
		dataWindowQuery["in"].setInput( createViews["out"] )

		dataWindowQuery["view"].setValue( "viewA" )
		self.assertEqual( dataWindowQuery["dataWindow"].getValue(), smallBox )
		self.assertEqual( dataWindowQuery["center"].getValue(), smallBoxFloat.center() )
		self.assertEqual( dataWindowQuery["size"].getValue(), smallBox.size() )

		dataWindowQuery["view"].setValue( "viewB" )
		self.assertEqual( dataWindowQuery["dataWindow"].getValue(), bigBox )
		self.assertEqual( dataWindowQuery["center"].getValue(), bigBoxFloat.center() )
		self.assertEqual( dataWindowQuery["size"].getValue(), bigBox.size() )

		createViews["views"][0]["name"].setValue( "viewB" )
		createViews["views"][1]["name"].setValue( "viewA" )
		self.assertEqual( dataWindowQuery["dataWindow"].getValue(), smallBox )
		self.assertEqual( dataWindowQuery["center"].getValue(), smallBoxFloat.center() )
		self.assertEqual( dataWindowQuery["size"].getValue(), smallBox.size() )

if __name__ == "__main__" :
	unittest.main()