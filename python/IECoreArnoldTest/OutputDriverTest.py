##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are
#  met:
#
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#
#     * Neither the name of Image Engine Design nor the names of any
#       other contributors to this software may be used to endorse or
#       promote products derived from this software without specific prior
#       written permission.
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

import pathlib
import time
import unittest
import subprocess

import IECoreImage

class OutputDriverTest( unittest.TestCase ) :

	def testMergedDisplays( self ) :

		server = IECoreImage.DisplayDriverServer( 1559 )
		time.sleep( 2 )

		subprocess.check_call( [
			"kick", "-v", "0", "-dw", "-dp",
			pathlib.Path( __file__ ).parent / "assFiles" / "mergedDisplays.ass"
		] )

		image = IECoreImage.ImageDisplayDriver.removeStoredImage( "mergedImage" )
		channelNames = image.keys()

		self.assertEqual( len( channelNames ), 7 )
		self.assertTrue( "R" in channelNames )
		self.assertTrue( "G" in channelNames )
		self.assertTrue( "B" in channelNames )
		self.assertTrue( "A" in channelNames )
		self.assertTrue( "direct_diffuse.R" in channelNames )
		self.assertTrue( "direct_diffuse.G" in channelNames )
		self.assertTrue( "direct_diffuse.B" in channelNames )

	def testVectorAndPointDisplays( self ) :

		server = IECoreImage.DisplayDriverServer( 1559 )
		time.sleep( 2 )

		subprocess.check_call( [
			"kick", "-v", "0", "-dw", "-dp",
			pathlib.Path( __file__ ).parent / "assFiles" / "vectorAndPointDisplays.ass"
		] )

		image = IECoreImage.ImageDisplayDriver.removeStoredImage( "vectorAndPointImage" )
		channelNames = image.keys()

		self.assertEqual( len( channelNames ), 10 )
		self.assertTrue( "R" in channelNames )
		self.assertTrue( "G" in channelNames )
		self.assertTrue( "B" in channelNames )
		self.assertTrue( "A" in channelNames )
		self.assertTrue( "P.R" in channelNames )
		self.assertTrue( "P.G" in channelNames )
		self.assertTrue( "P.B" in channelNames )
		self.assertTrue( "N.R" in channelNames )
		self.assertTrue( "N.G" in channelNames )
		self.assertTrue( "N.B" in channelNames )

	def testLayerName( self ) :

		server = IECoreImage.DisplayDriverServer( 1559 )
		time.sleep( 2 )

		subprocess.check_call( [
			"kick", "-v", "0", "-dw", "-dp",
			pathlib.Path( __file__ ).parent / "assFiles" / "outputWithLayerName.ass"
		] )

		image = IECoreImage.ImageDisplayDriver.removeStoredImage( "layerNameImage" )
		self.assertEqual(
			set( image.keys() ),
			{ "diffuseLayer.{}".format( c ) for c in "RGBA" }
		)

if __name__ == "__main__":
	unittest.main()
