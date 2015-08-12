##########################################################################
#
#  Copyright (c) 2013-2015, Image Engine Design Inc. All rights reserved.
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

import IECore
import Gaffer
import GafferImage
import GafferTest
import os

"""
Tests:

Channel data passes through

Data Window doesn't affect Display Window
Display Window doesn't affect Data Window
Data window intersects
source = Data Window
source = Display Window
source = Custom
"""

class CropTest( unittest.TestCase ) :

	imageFileUndersizeDataWindow = os.path.expandvars( "$GAFFER_ROOT/python/GafferTest/images/blueWithDataWindow.100x100.exr" )
	imageFileOversizeDataWindow = os.path.expandvars( "$GAFFER_ROOT/python/GafferTest/images/checkerWithNegWindows.200x150.exr" )

	def testDefaultState( self ) :

		crop = GafferImage.Crop()

		self.assertEqual( crop["areaSource"].getValue(), GafferImage.Crop.AreaType.DisplayWindow )
		self.assertTrue( crop["area"].getValue().isEmpty() )
		self.assertEqual( crop["affectDataWindow"].getValue(), True )
		self.assertEqual( crop["affectDisplayWindow"].getValue(), False )

	def testPassThrough( self ) :

		i = GafferImage.ImageReader()
		i["fileName"].setValue( self.imageFileUndersizeDataWindow )

		crop = GafferImage.Crop()
		crop["in"].setInput(i["out"])
		crop["areaSource"].setValue( GafferImage.Crop.AreaType.Custom )
		crop["area"].setValue( IECore.Box2i( IECore.V2i( 40 ), IECore.V2i( 50 ) ) )
		crop["affectDataWindow"].setValue( True )
		crop["affectDisplayWindow"].setValue( True )

		self.assertEqual(i['out'].channelDataHash( "R", IECore.V2i( 0 ) ), crop['out'].channelDataHash( "R", IECore.V2i( 0 ) ) )
		self.assertEqual(i['out'].channelDataHash( "G", IECore.V2i( 0 ) ), crop['out'].channelDataHash( "G", IECore.V2i( 0 ) ) )
		self.assertEqual(i['out'].channelDataHash( "B", IECore.V2i( 0 ) ), crop['out'].channelDataHash( "B", IECore.V2i( 0 ) ) )

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

	def testAffectDataWindow( self ) :

		i = GafferImage.ImageReader()
		i["fileName"].setValue( self.imageFileUndersizeDataWindow )

		crop = GafferImage.Crop()
		crop["in"].setInput(i["out"])
		crop["areaSource"].setValue( GafferImage.Crop.AreaType.Custom )
		crop["area"].setValue( IECore.Box2i( IECore.V2i( 40 ), IECore.V2i( 50 ) ) )
		crop["affectDataWindow"].setValue( True )
		crop["affectDisplayWindow"].setValue( False )

		self.assertEqual( crop["out"]["dataWindow"].getValue(), IECore.Box2i( IECore.V2i( 40 ), IECore.V2i( 49 ) ) )
		self.assertEqual( i["out"]["format"].getValue(), crop["out"]["format"].getValue() )

	def testAffectDisplayWindow( self ) :

		i = GafferImage.ImageReader()
		i["fileName"].setValue( self.imageFileUndersizeDataWindow )

		crop = GafferImage.Crop()
		crop["in"].setInput(i["out"])
		crop["areaSource"].setValue( GafferImage.Crop.AreaType.Custom )
		crop["area"].setValue( IECore.Box2i( IECore.V2i( 40 ), IECore.V2i( 50 ) ) )
		crop["affectDataWindow"].setValue( False )
		crop["affectDisplayWindow"].setValue( True )

		self.assertEqual( crop["out"]["format"].getValue().getDisplayWindow(), IECore.Box2i( IECore.V2i( 40 ), IECore.V2i( 49 ) ) )
		self.assertEqual( i["out"]["dataWindow"].getValue(), crop["out"]["dataWindow"].getValue() )

	def testIntersectDataWindow( self ) :

		i = GafferImage.ImageReader()
		i["fileName"].setValue( self.imageFileUndersizeDataWindow )

		crop = GafferImage.Crop()
		crop["in"].setInput(i["out"])
		crop["areaSource"].setValue( GafferImage.Crop.AreaType.Custom )
		crop["area"].setValue( IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( 50 ) ) )
		crop["affectDataWindow"].setValue( True )
		crop["affectDisplayWindow"].setValue( False )

		self.assertEqual( crop["out"]["dataWindow"].getValue(), IECore.Box2i( IECore.V2i( 30 ), IECore.V2i( 49 ) ) )

	def testDataWindowToDisplayWindow( self ) :

		i = GafferImage.ImageReader()
		i["fileName"].setValue( self.imageFileUndersizeDataWindow )

		crop = GafferImage.Crop()
		crop["in"].setInput(i["out"])
		crop["areaSource"].setValue( GafferImage.Crop.AreaType.DataWindow )
		crop["affectDataWindow"].setValue( False )
		crop["affectDisplayWindow"].setValue( True )

		self.assertEqual( i["out"]["dataWindow"].getValue(), crop["out"]["format"].getValue().getDisplayWindow() )
	
	def testDisplayWindowToDataWindow( self ) :

		i = GafferImage.ImageReader()
		i["fileName"].setValue( self.imageFileOversizeDataWindow )

		crop = GafferImage.Crop()
		crop["in"].setInput(i["out"])
		crop["areaSource"].setValue( GafferImage.Crop.AreaType.DisplayWindow )
		crop["affectDataWindow"].setValue( True )
		crop["affectDisplayWindow"].setValue( False )

		self.assertEqual( i["out"]["format"].getValue().getDisplayWindow(), crop["out"]["dataWindow"].getValue() )

	
if __name__ == "__main__":
	unittest.main()
