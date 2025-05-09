##########################################################################
#
#  Copyright (c) 2025, Image Engine Design Inc. All rights reserved.
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
import pathlib
import time

import IECore

import Gaffer
import GafferTest
import GafferScene
import GafferSceneTest
import GafferImage

class RenderManifestTest( GafferSceneTest.SceneTestCase ) :

	testImagePath = pathlib.Path( __file__ ).parent / "images"
	testImage = testImagePath / "cryptomatte.exr"

	def test( self ) :

		r = GafferScene.RenderManifest()

		# acquireID can either insert new ids in incremental order, or retrieve existing ids
		self.assertEqual( r.acquireID( "/a" ), 1 )
		self.assertEqual( r.acquireID( "/b" ), 2 )
		self.assertEqual( r.acquireID( "/c" ), 3 )
		self.assertEqual( r.acquireID( "/long/path/with/many/elements" ), 4 )
		self.assertEqual( r.acquireID( "/long/path/with/many/elements" ), 4 )
		self.assertEqual( r.acquireID( "/c" ), 3 )
		self.assertEqual( r.acquireID( "/b" ), 2 )
		self.assertEqual( r.acquireID( "/a" ), 1 )


		# idForPath can only retrieve existing ids
		self.assertEqual( r.idForPath( "/a" ), 1 )
		self.assertEqual( r.idForPath( "/c" ), 3 )

		# Returns 0 for unknown path
		self.assertEqual( r.idForPath( "/x" ), 0 )


		self.assertEqual( r.pathForID( 1 ), "/a" )
		self.assertEqual( r.pathForID( 3 ), "/c" )
		self.assertEqual( r.pathForID( 4 ), "/long/path/with/many/elements" )

		# Returns None for unknown path
		self.assertEqual( r.pathForID( 42 ), None )

		# There are also batch forms that operate on id lists and path matchers
		self.assertEqual( r.acquireIDs( IECore.PathMatcher( [ "x", "y", "z" ] ) ), [ 5, 6, 7] )

		self.assertEqual( r.pathsForIDs( [ 5, 6, 7] ), IECore.PathMatcher( [ "x", "y", "z" ] ) )


		self.assertEqual( r.size(), 7 )
		r.clear()
		self.assertEqual( r.size(), 0 )


	def testReadCryptomatte( self ):

		imageReader = GafferImage.ImageReader()
		imageReader["fileName"].setValue( self.testImage )

		# Delete in the in-place manifest, so we know it works to read from the sidecar file
		m = imageReader["out"].metadata()
		del m["cryptomatte/f834d0a/manifest"]
		r = GafferScene.RenderManifest.loadFromImageMetadata( m, "crypto_object" )

		self.assertEqual( r.size(), 92 )
		self.assertEqual( r.idForPath( "/GAFFERBOT/C_torso_GRP/C_head_GRP/C_head_CPT/C_head001_REN" ), 4226998693 )
		self.assertEqual( r.pathForID( 4226998693 ), "/GAFFERBOT/C_torso_GRP/C_head_GRP/C_head_CPT/C_head001_REN" )

		# Delete the manif_file, so we know it works to read from the in-place manifest
		m = imageReader["out"].metadata()
		del m["cryptomatte/f834d0a/manif_file"]
		r = GafferScene.RenderManifest.loadFromImageMetadata( m, "crypto_object" )

		self.assertEqual( r.size(), 92 )
		self.assertEqual( r.idForPath( "/GAFFERBOT/C_torso_GRP/C_head_GRP/C_head_CPT/C_head001_REN" ), 4226998693 )
		self.assertEqual( r.pathForID( 4226998693 ), "/GAFFERBOT/C_torso_GRP/C_head_GRP/C_head_CPT/C_head001_REN" )

		# We can also load the material cryptomattes
		r = GafferScene.RenderManifest.loadFromImageMetadata( m, "crypto_material" )
		self.assertEqual( r.size(), 14 )
		self.assertEqual( r.idForPath( "shader:ba1b35e0886c8e92a5c5daea71484b84" ), 1650131652 )
		self.assertEqual( r.pathForID( 1650131652 ), "/shader:ba1b35e0886c8e92a5c5daea71484b84" )

		# If we delete both sources of metadata, we get an exception
		m = imageReader["out"].metadata()
		del m["cryptomatte/f834d0a/manif_file"]
		del m["cryptomatte/f834d0a/manifest"]
		with self.assertRaisesRegex( IECore.Exception, "No gaffer:renderManifestFilePath metadata or cryptomatte metadata found" ):
			GafferScene.RenderManifest.loadFromImageMetadata( m, "crypto_object" )

	def testReadWriteEXR( self ):
		r = GafferScene.RenderManifest()
		r.acquireID( "/a" )
		r.acquireID( "/b" )
		r.acquireID( "/c" )
		r.acquireID( "/long/path/with/many/elements" )

		filePath = self.temporaryDirectory() / "testManifest.exr"

		r.writeEXRManifest( filePath )

		# Try reading back this manifest

		r2 = GafferScene.RenderManifest.loadFromImageMetadata( IECore.CompoundData( { "gaffer:renderManifestFilePath" : str( filePath ) } ), "" )
		self.assertEqual( r2.size(), 4 )
		self.assertEqual( r2.idForPath( "b" ), 2 )
		self.assertEqual( r2.pathForID( 2 ), "/b" )

		# Update the manifest on disk
		r.acquireID( "x" )

		# This is such a small manifest that the time to write it could less than the file system's timer
		# precision, resulting in sporadic failures if both writes get the same mod time, and RenderManifest
		# thinks it doesn't need to reload because the time stamp hasn't changed. A delay of 0.001s seems
		# adequate to avoid this - delay by 0.01s to be safe.
		time.sleep( 0.01 )
		r.writeEXRManifest( filePath )

		# Make sure we get the update
		r2 = GafferScene.RenderManifest.loadFromImageMetadata( IECore.CompoundData( { "gaffer:renderManifestFilePath" : str( filePath ) } ), "" )
		self.assertEqual( r2.size(), 5 )
		self.assertEqual( r2.idForPath( "x" ), 5 )
		self.assertEqual( r2.pathForID( 5 ), "/x" )

if __name__ == "__main__":
	unittest.main()
