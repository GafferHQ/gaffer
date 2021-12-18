##########################################################################
#
#  Copyright (c) 2021, Murray Stevenson All rights reserved.
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
import json
import six

import IECore

import Gaffer
import GafferImage
import GafferScene
import GafferTest
import GafferImageTest
import GafferSceneTest

class CryptomatteTest( GafferSceneTest.SceneTestCase ) :

	testImagePath = os.path.join( os.path.dirname( os.path.abspath( __file__ ) ), "images" )
	testImage = os.path.join( testImagePath, "cryptomatte.exr" )

	def testCryptomatteHash( self ) :
		
		manifest = {
			"hello": 6.0705627102400005616e-17,
			"cube": -4.08461912519e+15,
			"sphere": 2.79018604383e+15,
			"plane": 3.66557617593e-11,
			"/GAFFERBOT/C_torso_GRP/C_head_GRP/C_head_CPT/C_head001_REN": -2.5222249091461295e+36,
			"shader:b0d1fe5b982bcae64d6329033cbadc70": 876260905451520.0,
		}

		i = GafferImage.ImageMetadata()
		i["metadata"].addChild( Gaffer.NameValuePlug( "cryptomatte/f834d0a/conversion", "uint32_to_float32" ) )
		i["metadata"].addChild( Gaffer.NameValuePlug( "cryptomatte/f834d0a/hash", "MurmurHash3_32" ) )
		i["metadata"].addChild( Gaffer.NameValuePlug( "cryptomatte/f834d0a/manifest", json.dumps( manifest ) ) )

		c = GafferScene.Cryptomatte()
		c["in"].setInput( i["out"] )
		c["layer"].setValue( "crypto_object" )

		for name in sorted( manifest.keys() ) :
			c["matteNames"].setValue( IECore.StringVectorData( [name] ) )
			self.assertEqual( IECore.FloatData( manifest[name] ), IECore.FloatData( c["__matteValues"].getValue()[0] ) )

	def compareValues( self, c, layers ) :

		cowSampler = GafferImage.ImageSampler()
		cowSampler["image"].setInput( c["out"] )
		cowSampler["pixel"].setValue( imath.V2f( 94, 106 ) )

		cow1Sampler = GafferImage.ImageSampler()
		cow1Sampler["image"].setInput( c["out"] )
		cow1Sampler["pixel"].setValue( imath.V2f( 36, 108 ) )

		if "crypto_object" in layers :
			c["layer"].setValue( "crypto_object" )
			m = c["__manifest"].getValue()

			self.assertTrue( IECore.StringData( "/cow" ) in m.values() )
			self.assertEqual( cowSampler["color"].getValue()[3], 0.0 )
			self.assertEqual( cow1Sampler["color"].getValue()[3], 0.0 )

			c["matteNames"].setValue( IECore.StringVectorData( [ "/cow" ] ) )
			self.assertEqual( cowSampler["color"].getValue()[3], 1.0 )
			self.assertEqual( cow1Sampler["color"].getValue()[3], 0.0 )

			c["matteNames"].setValue( IECore.StringVectorData( [ "/cow1" ] ) )
			self.assertEqual( cowSampler["color"].getValue()[3], 0.0 )
			self.assertEqual( cow1Sampler["color"].getValue()[3], 1.0 )

			c["matteNames"].setValue( IECore.StringVectorData( [ "/cow*" ] ) )
			self.assertEqual( cowSampler["color"].getValue()[3], 1.0 )
			self.assertEqual( cow1Sampler["color"].getValue()[3], 1.0 )

		if "crypto_material" in layers :
			c["layer"].setValue( "crypto_material" )
			m = c["__manifest"].getValue()

			self.assertTrue( IECore.StringData( "shader:db33c6a440a2dcf4a92383d8ae16c33a" ) in m.values() )
			self.assertEqual( cowSampler["color"].getValue()[3], 0.0 )
			self.assertEqual( cow1Sampler["color"].getValue()[3], 0.0 )

			c["matteNames"].setValue( IECore.StringVectorData( [ "shader:db33c6a440a2dcf4a92383d8ae16c33a" ] ) )
			self.assertEqual( cowSampler["color"].getValue()[3], 0.0 )
			self.assertEqual( cow1Sampler["color"].getValue()[3], 1.0 )

			c["matteNames"].setValue( IECore.StringVectorData( [ "shader:b0d1fe5b982bcae64d6329033cbadc70" ] ) )
			self.assertEqual( cowSampler["color"].getValue()[3], 1.0 )
			self.assertEqual( cow1Sampler["color"].getValue()[3], 0.0 )

	def testManifestFromMetadata( self ) :

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.testImage )

		c = GafferScene.Cryptomatte()
		c["in"].setInput( r["out"] )

		self.compareValues( c, ["crypto_object", "crypto_material"] )

		i = GafferImage.ImageMetadata()
		i["in"].setInput( r["out"] )
		i["metadata"].addChild( Gaffer.NameValuePlug( "cryptomatte/f834d0a/manifest", "{broken}" ) )
		
		c["in"].setInput( i["out"] )

		with six.assertRaisesRegex( self, Gaffer.ProcessException, r'Error parsing manifest metadata:' ) as raised :
			self.compareValues( c, ["crypto_object"] )

	def testManifestFromSidecarFile( self ) :

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.testImage )

		c = GafferScene.Cryptomatte()
		c["in"].setInput( r["out"] )
		c["manifestSource"].setValue( GafferScene.Cryptomatte.ManifestSource.Sidecar )
		c["sidecarFile"].setValue( os.path.join( self.testImagePath, "crypto_object.json" ) )
		self.compareValues( c, ["crypto_object"] )

		c["sidecarFile"].setValue( os.path.join( self.testImagePath, "crypto_material.json" ) )
		self.compareValues( c, ["crypto_material"] )

		c["sidecarFile"].setValue( "" )

		with six.assertRaisesRegex( self, Gaffer.ProcessException, r'No manifest file provided.' ) as raised :
			self.compareValues( c, ["crypto_object"] )

		invalidPath = os.path.dirname( self.testImage ) + "/not/a/valid/path.json"
		c["sidecarFile"].setValue( invalidPath )

		with six.assertRaisesRegex( self, Gaffer.ProcessException, r'Manifest file not found: {}'.format( invalidPath ) ) as raised :
			self.compareValues( c, ["crypto_object"] )

	def testManifestFromSidecarMetadata( self ) :

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.testImage )

		# our test image contains both manifest and manif_file metadata entries
		# manifest takes precedence over manif_file, so delete to ensure that
		# we read from the sidecar file specified by manif_file
		d = GafferImage.DeleteImageMetadata()
		d["in"].setInput( r["out"] )
		d["names"].setValue( "cryptomatte/*/manifest" )

		c = GafferScene.Cryptomatte()
		c["in"].setInput( d["out"] )
		c["manifestSource"].setValue( GafferScene.Cryptomatte.ManifestSource.Metadata )
		c["manifestDirectory"].setValue( os.path.dirname( self.testImage ) )

		self.compareValues( c, ["crypto_object", "crypto_material"] )

		c["manifestDirectory"].setValue( "" )

		with six.assertRaisesRegex( self, Gaffer.ProcessException, r'No manifest directory provided.' ) as raised :
			self.compareValues( c, ["crypto_object"] )

		invalidPath = os.path.dirname( self.testImage ) + "/not/a/valid/path"
		c["manifestDirectory"].setValue( invalidPath )

		with six.assertRaisesRegex( self, Gaffer.ProcessException, r'Manifest directory not found: {}'.format( invalidPath ) ) as raised :
			self.compareValues( c, ["crypto_object"] )

		d["names"].setValue( "cryptomatte/bda530a/manifest cryptomatte/bda530a/manif_file" )

		with six.assertRaisesRegex( self, Gaffer.ProcessException, r'Image metadata entry not found. One of the following entries expected: cryptomatte/bda530a/manifest cryptomatte/bda530a/manif_file' ) as raised :
			self.compareValues( c, ["crypto_material"] )
		
	def testPreviewChannels( self ) :

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.testImage )

		c = GafferScene.Cryptomatte()
		c["in"].setInput( r["out"] )
		c["layer"].setValue( "crypto_object" )

		s = GafferImage.ImageSampler()
		s["image"].setInput( c["out"] )
		s["pixel"].setValue( imath.V2f( 32, 108 ) )

		self.assertEqual( s["color"].getValue(), imath.Color4f(-7.18267809e-20, 0.198745549, 0.178857431, 0) )

		c["matteNames"].setValue( IECore.StringVectorData( [ "/cow1" ] ) )

		self.assertEqual( s["color"].getValue(), imath.Color4f(-7.18267809e-20, 0.448745549, 0.928857431, 1) )

	def testWildcardMatch( self ) :
		
		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.testImage )

		c = GafferScene.Cryptomatte()
		c["in"].setInput( r["out"] )
		c["layer"].setValue( "crypto_object" )

		s = GafferImage.ImageSampler()
		s["image"].setInput( c["out"] )
		s["pixel"].setValue( imath.V2f( 32, 108 ) )
		
		s2 = GafferImage.ImageSampler()
		s2["image"].setInput( c["out"] )
		s2["pixel"].setValue( imath.V2f( 106, 78 ) )

		c["matteNames"].setValue( IECore.StringVectorData( [ "/*" ] ) )

		self.assertEqual( s["color"].getValue()[3], 1.0 )
		self.assertEqual( s2["color"].getValue()[3], 1.0 )

		c["matteNames"].setValue( IECore.StringVectorData( [ "/..." ] ) )

		self.assertEqual( s["color"].getValue()[3], 1.0 )
		self.assertEqual( s2["color"].getValue()[3], 1.0 )

		c["matteNames"].setValue( IECore.StringVectorData( [ "/*/?_clawBottom001_REN" ] ) )

		self.assertEqual( s["color"].getValue()[3], 0.0 )
		self.assertEqual( s2["color"].getValue()[3], 0.0 )

		c["matteNames"].setValue( IECore.StringVectorData( [ "/.../?_clawBottom001_REN" ] ) )

		self.assertEqual( s["color"].getValue()[3], 0.0 )
		self.assertEqual( s2["color"].getValue()[3], 1.0 )

	def testAncestorMatch( self ) :

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.testImage )

		c = GafferScene.Cryptomatte()
		c["in"].setInput( r["out"] )
		c["layer"].setValue( "crypto_object" )

		s = GafferImage.ImageSampler()
		s["image"].setInput( c["out"] )
		s["pixel"].setValue( imath.V2f( 32, 108 ) )
		
		s2 = GafferImage.ImageSampler()
		s2["image"].setInput( c["out"] )
		s2["pixel"].setValue( imath.V2f( 106, 78 ) )

		self.assertEqual( s["color"].getValue()[3], 0.0 )
		self.assertEqual( s2["color"].getValue()[3], 0.0 )

		c["matteNames"].setValue( IECore.StringVectorData( [ "/GAFFERBOT" ] ) )

		self.assertEqual( s["color"].getValue()[3], 0.0 )
		self.assertEqual( s2["color"].getValue()[3], 1.0 )

	def testRawValueMatch( self ) :

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.testImage )

		c = GafferScene.Cryptomatte()
		c["in"].setInput( r["out"] )
		c["layer"].setValue( "crypto_object" )

		s = GafferImage.ImageSampler()
		s["image"].setInput( c["out"] )
		s["pixel"].setValue( imath.V2f( 32, 108 ) )
		
		s2 = GafferImage.ImageSampler()
		s2["image"].setInput( c["out"] )
		s2["pixel"].setValue( imath.V2f( 106, 78 ) )

		self.assertEqual( s["color"].getValue()[3], 0.0 )
		self.assertEqual( s2["color"].getValue()[3], 0.0 )

		c["matteNames"].setValue( IECore.StringVectorData( [ "<{}>".format( s["color"].getValue()[0] ) ] ) )

		self.assertEqual( s["color"].getValue()[3], 1.0 )
		self.assertEqual( s2["color"].getValue()[3], 0.0 )

		c["matteNames"].setValue( IECore.StringVectorData( [ "<{}>".format( s2["color"].getValue()[0] ) ] ) )

		self.assertEqual( s["color"].getValue()[3], 0.0 )
		self.assertEqual( s2["color"].getValue()[3], 1.0 )

	def testPassThrough( self ) :

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.testImage )

		c = GafferScene.Cryptomatte()
		c["in"].setInput( r["out"] )

		c["layer"].setValue( "crypto_object" )
		c["matteNames"].setValue( IECore.StringVectorData( [ "/cow" ] ) )

		self.assertEqual( r["out"]["format"].hash(), c["out"]["format"].hash() )
		self.assertEqual( r["out"]["dataWindow"].hash(), c["out"]["dataWindow"].hash() )
		self.assertEqual( r["out"]["metadata"].hash(), c["out"]["metadata"].hash() )

		self.assertEqual( r["out"]["format"].getValue(), c["out"]["format"].getValue() )
		self.assertEqual( r["out"]["dataWindow"].getValue(), c["out"]["dataWindow"].getValue() )
		self.assertEqual( r["out"]["metadata"].getValue(), c["out"]["metadata"].getValue() )
	
	def testKeyedResult( self ) :
		
		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.testImage )

		c = GafferScene.Cryptomatte()
		c["in"].setInput( r["out"] )

		d = GafferImage.DeleteChannels()
		d["in"].setInput( c["out"] )
		d["mode"].setValue( 1 )
		d["channels"].setValue( "A" )

		c["layer"].setValue( "crypto_object" )
		c["matteNames"].setValue( IECore.StringVectorData( [ 	
			"/GAFFERBOT/C_torso_GRP/C_head_GRP/C_head_CPT/L_ear001_REN",
			"/GAFFERBOT/C_torso_GRP/C_torso_CPT/C_torso002_REN",
			"/GAFFERBOT/C_torso_GRP/R_armUpper_GRP/R_armLower_GRP/R_clawBottom_GRP/R_clawBottom_CPT/R_clawBottom001_REN",
			"/GAFFERBOT/C_torso_GRP/R_legUpper_GRP/R_legLower_GRP/R_foot_GRP/R_foot_CPT/R_foot002_REN",
			"/cow1" 
		] )	)

		resultImage = os.path.join( self.testImagePath, "cryptomatteKeyed.exr" )
		r2 = GafferImage.ImageReader()
		r2["fileName"].setValue( resultImage )

		self.assertImagesEqual( d["out"], r2["out"], ignoreMetadata=True )

	def testOutputChannelAffectsChannelNames( self ) :

		c = GafferScene.Cryptomatte()
		cs = GafferTest.CapturingSlot( c.plugDirtiedSignal() )
		c["outputChannel"].setValue( "A2" )

		self.assertTrue( c["out"]["channelNames"] in set( [ x[0] for x in cs ] ) )

	def testOutputChannelName( self ) :
		
		c = GafferScene.Cryptomatte()
		self.assertIn( "A", c["out"]["channelNames"].getValue() )

		c["outputChannel"].setValue( "A2" )
		self.assertIn( "A2", c["out"]["channelNames"].getValue() )
		self.assertNotIn( "A", c["out"]["channelNames"].getValue() )

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testPerformance( self ) :

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.testImage )

		c = GafferScene.Cryptomatte()
		c["in"].setInput( r["out"] )

		c["layer"].setValue( "crypto_object" )
		
		keys = [ "/..." ]
		
		c["matteNames"].setValue( IECore.StringVectorData( keys ) )

		# Pre-compute input to remove cost of file loading from performance test
		GafferImageTest.processTiles( c["in"] )

		with GafferTest.TestRunner.PerformanceScope() :
			GafferImageTest.processTiles( c["out"] )

	def testSceneValid( self ) :

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.testImage )

		c = GafferScene.Cryptomatte()
		c["in"].setInput( r["out"] )

		c["layer"].setValue( "crypto_object" )
		self.assertSceneValid( c["__manifestScene"] )

	def testChildNames( self ) :
		
		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.testImage )

		c = GafferScene.Cryptomatte()
		c["in"].setInput( r["out"] )

		cs = GafferTest.CapturingSlot( c.plugDirtiedSignal() )
		c["layer"].setValue( "crypto_object" )
		self.assertTrue( c["__manifestScene"]["childNames"] in [ x[0] for x in cs ] )

		self.assertEqual( 
			c["__manifestScene"].childNames( "/GAFFERBOT/C_torso_GRP" ), 
			IECore.InternedStringVectorData( [ "C_head_GRP", "C_key_GRP", "C_torso_CPT", "L_armUpper_GRP", "L_legUpper_GRP", "R_armUpper_GRP", "R_legUpper_GRP" ] ) 
		)
		
if __name__ == "__main__":
	unittest.main()