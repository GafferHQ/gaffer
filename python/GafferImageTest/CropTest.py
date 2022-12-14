##########################################################################
#
#  Copyright (c) 2013-2015, Image Engine Design Inc. All rights reserved.
#  Copyright (c) 2015, Nvizible Ltd. All rights reserved.
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
import os
import imath

import IECore

import Gaffer
import GafferTest
import GafferImage
import GafferImageTest

class CropTest( GafferImageTest.ImageTestCase ) :

	imageFileUndersizeDataWindow = Gaffer.rootPath() / "python" / "GafferImageTest" / "images" / "blueWithDataWindow.100x100.exr"
	imageFileOversizeDataWindow = Gaffer.rootPath() / "python"/ "GafferImageTest" / "images" / "checkerWithNegWindows.200x150.exr"
	representativeDeepImagePath = Gaffer.rootPath() / "python"/ "GafferImageTest"/ "images" /"representativeDeepImage.exr"

	def testDefaultState( self ) :

		crop = GafferImage.Crop()

		self.assertEqual( crop["areaSource"].getValue(), GafferImage.Crop.AreaSource.Area )
		self.assertTrue( crop["area"].getValue().isEmpty() )
		self.assertEqual( crop["affectDataWindow"].getValue(), True )
		self.assertEqual( crop["affectDisplayWindow"].getValue(), True )

	def testPassThrough( self ) :

		i = GafferImage.ImageReader()
		i["fileName"].setValue( self.imageFileUndersizeDataWindow )

		crop = GafferImage.Crop()
		crop["in"].setInput(i["out"])
		crop["areaSource"].setValue( GafferImage.Crop.AreaSource.Area )
		crop["area"].setValue( imath.Box2i( imath.V2i( 40 ), imath.V2i( 50 ) ) )
		crop["affectDataWindow"].setValue( True )
		crop["affectDisplayWindow"].setValue( True )
		crop["resetOrigin"].setValue( False )

		self.assertEqual(i['out'].channelDataHash( "R", imath.V2i( 0 ) ), crop['out'].channelDataHash( "R", imath.V2i( 0 ) ) )
		self.assertEqual(i['out'].channelDataHash( "G", imath.V2i( 0 ) ), crop['out'].channelDataHash( "G", imath.V2i( 0 ) ) )
		self.assertEqual(i['out'].channelDataHash( "B", imath.V2i( 0 ) ), crop['out'].channelDataHash( "B", imath.V2i( 0 ) ) )

		self.assertEqual( i["out"]["metadata"].hash(), crop["out"]["metadata"].hash() )
		self.assertEqual( i["out"]["channelNames"].hash(), crop["out"]["channelNames"].hash() )
		self.assertNotEqual( i["out"]["format"].hash(), crop["out"]["format"].hash() )
		self.assertNotEqual( i["out"]["dataWindow"].hash(), crop["out"]["dataWindow"].hash() )

		self.assertEqual( i["out"]["metadata"].getValue(), crop["out"]["metadata"].getValue() )
		self.assertEqual( i["out"]["channelNames"].getValue(), crop["out"]["channelNames"].getValue() )
		self.assertNotEqual( i["out"]["format"].getValue(), crop["out"]["format"].getValue() )
		self.assertNotEqual( i["out"]["dataWindow"].getValue(), crop["out"]["dataWindow"].getValue() )

	def testEnableBehaviour( self ) :

		crop = GafferImage.Crop()

		self.assertTrue( crop.enabledPlug().isSame( crop["enabled"] ) )
		self.assertTrue( crop.correspondingInput( crop["out"] ).isSame( crop["in"] ) )
		self.assertEqual( crop.correspondingInput( crop["in"] ), None )
		self.assertEqual( crop.correspondingInput( crop["enabled"] ), None )

	def testAreaFormat( self ) :

		constant = GafferImage.Constant()
		constant['format'].setValue( GafferImage.Format( 1024, 576 ) )

		crop1 = GafferImage.Crop()
		crop1['in'].setInput( constant['out'] )
		crop1['areaSource'].setValue( GafferImage.Crop.AreaSource.Format )
		crop1['format'].setValue( GafferImage.Format( 2048, 1152 ) )

		crop2 = GafferImage.Crop()
		crop2['in'].setInput( constant['out'] )
		crop2['areaSource'].setValue( GafferImage.Crop.AreaSource.Area )
		crop2['area'].setValue( imath.Box2i( imath.V2i( 0, 0 ), imath.V2i( 2048, 1152 ) ) )

		self.assertEqual( crop1['out']['dataWindow'].getValue(), crop2['out']['dataWindow'].getValue() )

		crop1['formatCenter'].setValue( True )
		crop2['area'].setValue( imath.Box2i( imath.V2i( -512, -288 ), imath.V2i( 1536, 864 ) ) )
		crop2['resetOrigin'].setValue( True )

		self.assertEqual( crop1['out']['dataWindow'].getValue(), crop2['out']['dataWindow'].getValue() )

	def testAffectDataWindow( self ) :

		i = GafferImage.ImageReader()
		i["fileName"].setValue( self.imageFileUndersizeDataWindow )

		crop = GafferImage.Crop()
		crop["in"].setInput(i["out"])
		crop["areaSource"].setValue( GafferImage.Crop.AreaSource.Area )
		crop["area"].setValue( imath.Box2i( imath.V2i( 40 ), imath.V2i( 50 ) ) )
		crop["affectDataWindow"].setValue( True )
		crop["affectDisplayWindow"].setValue( False )

		self.assertEqual( crop["out"]["dataWindow"].getValue(), imath.Box2i( imath.V2i( 40 ), imath.V2i( 50 ) ) )
		self.assertEqual( i["out"]["format"].getValue(), crop["out"]["format"].getValue() )

	def testAffectDisplayWindow( self ) :

		i = GafferImage.ImageReader()
		i["fileName"].setValue( self.imageFileUndersizeDataWindow )

		crop = GafferImage.Crop()
		crop["in"].setInput(i["out"])
		crop["areaSource"].setValue( GafferImage.Crop.AreaSource.Area )
		crop["area"].setValue( imath.Box2i( imath.V2i( 40 ), imath.V2i( 50 ) ) )
		crop["affectDataWindow"].setValue( False )
		crop["affectDisplayWindow"].setValue( True )
		crop["resetOrigin"].setValue( False )

		self.assertEqual( crop["out"]["format"].getValue().getDisplayWindow(), imath.Box2i( imath.V2i( 40 ), imath.V2i( 50 ) ) )
		self.assertEqual( i["out"]["dataWindow"].getValue(), crop["out"]["dataWindow"].getValue() )

		crop["resetOrigin"].setValue( True )

		self.assertEqual( crop["out"]["format"].getValue().getDisplayWindow(), imath.Box2i( imath.V2i( 0 ), imath.V2i( 10 ) ) )
		self.assertEqual( crop["out"]["dataWindow"].getValue(), imath.Box2i( imath.V2i( -10 ), imath.V2i( 40 ) ) )

	def testIntersectDataWindow( self ) :

		i = GafferImage.ImageReader()
		i["fileName"].setValue( self.imageFileUndersizeDataWindow )

		crop = GafferImage.Crop()
		crop["in"].setInput(i["out"])
		crop["areaSource"].setValue( GafferImage.Crop.AreaSource.Area )
		crop["area"].setValue( imath.Box2i( imath.V2i( 0 ), imath.V2i( 50 ) ) )
		crop["affectDataWindow"].setValue( True )
		crop["affectDisplayWindow"].setValue( False )

		self.assertEqual( crop["out"]["dataWindow"].getValue(), imath.Box2i( imath.V2i( 30 ), imath.V2i( 50 ) ) )

	def testDataWindowToDisplayWindow( self ) :

		i = GafferImage.ImageReader()
		i["fileName"].setValue( self.imageFileUndersizeDataWindow )

		crop = GafferImage.Crop()
		crop["in"].setInput(i["out"])
		crop["areaSource"].setValue( GafferImage.Crop.AreaSource.DataWindow )
		crop["affectDataWindow"].setValue( False )
		crop["affectDisplayWindow"].setValue( True )
		crop["resetOrigin"].setValue( False )

		self.assertEqual( i["out"]["dataWindow"].getValue(), crop["out"]["format"].getValue().getDisplayWindow() )
		self.assertEqual( crop["out"]["dataWindow"].getValue(), i["out"]["dataWindow"].getValue() )

		crop["resetOrigin"].setValue( True )

		self.assertEqual( crop["out"]["format"].getValue().getDisplayWindow(), imath.Box2i( imath.V2i( 0 ), imath.V2i( 50 ) ) )
		self.assertEqual( crop["out"]["dataWindow"].getValue(), imath.Box2i( imath.V2i( 0 ), imath.V2i( 50 ) ) )

	def testDisplayWindowToDataWindow( self ) :

		i = GafferImage.ImageReader()
		i["fileName"].setValue( self.imageFileOversizeDataWindow )

		crop = GafferImage.Crop()
		crop["in"].setInput(i["out"])
		crop["areaSource"].setValue( GafferImage.Crop.AreaSource.DisplayWindow )
		crop["affectDataWindow"].setValue( True )
		crop["affectDisplayWindow"].setValue( False )

		self.assertEqual( i["out"]["format"].getValue().getDisplayWindow(), crop["out"]["dataWindow"].getValue() )

	def testAffects( self ) :

		c = GafferImage.Crop()

		self.assertEqual(
			set( c.affects( c["affectDisplayWindow"] ) ),
			{ c["out"]["format"], c["__offset"]["x"], c["__offset"]["y"] }
		)

		self.assertEqual(
			set( c.affects( c["affectDataWindow"] ) ),
			{ c["__cropDataWindow"] }
		)

		self.assertTrue( c["__cropDataWindow"] in set( c.affects( c["in"]["dataWindow"] ) ) )
		self.assertTrue( c["out"]["format"] in set( c.affects( c["in"]["format"] ) ) )

	def testResetOrigin( self ) :

		constant = GafferImage.Constant()
		constant["format"].setValue( GafferImage.Format( 100, 200, 1 ) )

		crop = GafferImage.Crop()
		crop["in"].setInput( constant["out"] )
		self.assertEqual( crop["affectDisplayWindow"].getValue(), True )
		self.assertEqual( crop["affectDataWindow"].getValue(), True )
		self.assertEqual( crop["resetOrigin"].getValue(), True )

		area = imath.Box2i( imath.V2i( 50 ), imath.V2i( 100, 190 ) )
		crop["area"].setValue( area )

		self.assertEqual( crop["out"]["format"].getValue().getDisplayWindow(), imath.Box2i( imath.V2i( 0 ), area.size() ) )
		self.assertEqual( crop["out"]["dataWindow"].getValue(), imath.Box2i( imath.V2i( 0 ), area.size() ) )

		crop["resetOrigin"].setValue( False )

		self.assertEqual( crop["out"]["format"].getValue().getDisplayWindow(), area )
		self.assertEqual( crop["out"]["dataWindow"].getValue(), area )

		# If we're not affecting the display window, then the reset origin flag
		# should be ignored.
		crop["resetOrigin"].setValue( True )
		crop["affectDisplayWindow"].setValue( False )

		self.assertEqual( crop["out"]["format"].getValue(), crop["in"]["format"].getValue() )
		self.assertEqual( crop["out"]["dataWindow"].getValue(), area )

		# But if we are affecting the display window, and we are resetting the origin,
		# the data window should be offset even if affectDataWindow is off.

		crop["affectDisplayWindow"].setValue( True )
		crop["affectDataWindow"].setValue( False )

		self.assertEqual( crop["out"]["format"].getValue().getDisplayWindow(), imath.Box2i( imath.V2i( 0 ), area.size() ) )
		self.assertEqual( crop["out"]["dataWindow"].getValue(), imath.Box2i( imath.V2i( -50 ), imath.V2i( 50, 150 ) ) )

	def testEmptyInput( self ) :

		crop = GafferImage.Crop()

		crop["area"]["min"].setValue( imath.V2i( 20 ) )
		self.assertTrue( GafferImage.BufferAlgo.empty( crop["out"]["dataWindow"].getValue() ) )

	def testDeep( self ) :
		representativeDeep = GafferImage.ImageReader()
		representativeDeep["fileName"].setValue( self.representativeDeepImagePath )

		deepCrop = GafferImage.Crop()
		deepCrop["in"].setInput( representativeDeep["out"] )

		postFlatten = GafferImage.DeepToFlat()
		postFlatten["in"].setInput( deepCrop["out"] )

		preFlatten = GafferImage.DeepToFlat()
		preFlatten["in"].setInput( representativeDeep["out"] )

		flatCrop = GafferImage.Crop()
		flatCrop["in"].setInput( preFlatten["out"] )

		dataWindow = representativeDeep["out"].dataWindow()

		for affectDisplay in [ True, False ]:
			for area in [
				imath.Box2i( imath.V2i( 0, 0 ), imath.V2i( 150, 100 ) ),
				imath.Box2i( imath.V2i( -10, -13 ), imath.V2i( 157, 103 ) ),
				imath.Box2i( imath.V2i( 10, 13 ), imath.V2i( 143, 77 ) ),
				imath.Box2i( imath.V2i( 37, 65 ), imath.V2i( 101, 67 ) ),
				imath.Box2i( imath.V2i( 0, 0 ), imath.V2i( 149, 99 ) )
			] :
				deepCrop["area"].setValue( area )
				flatCrop["area"].setValue( area )

				self.assertImagesEqual( postFlatten["out"], flatCrop["out"] )

	def testFormatAffectsOutput( self ) :

		crop = GafferImage.Crop()
		cs = GafferTest.CapturingSlot( crop.plugDirtiedSignal() )
		crop["format"].setValue( GafferImage.Format( 100, 200 ) )
		self.assertIn( crop["out"]["dataWindow"], { x[0] for x in cs } )

if __name__ == "__main__":
	unittest.main()
