##########################################################################
#
#  Copyright (c) 2013-2015, John Haddon. All rights reserved.
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
import imath

import IECore

import Gaffer
import GafferTest
import GafferImage
import GafferImageTest
import GafferOSL
import GafferOSLTest

class OSLImageTest( GafferOSLTest.OSLTestCase ) :

	def test( self ) :

		getRed = GafferOSL.OSLShader()
		getRed.loadShader( "ImageProcessing/InChannel" )
		getRed["parameters"]["channelName"].setValue( "R" )

		getGreen = GafferOSL.OSLShader()
		getGreen.loadShader( "ImageProcessing/InChannel" )
		getGreen["parameters"]["channelName"].setValue( "G" )

		getBlue = GafferOSL.OSLShader()
		getBlue.loadShader( "ImageProcessing/InChannel" )
		getBlue["parameters"]["channelName"].setValue( "B" )

		floatToColor = GafferOSL.OSLShader()
		floatToColor.loadShader( "Conversion/FloatToColor" )
		floatToColor["parameters"]["r"].setInput( getBlue["out"]["channelValue"] )
		floatToColor["parameters"]["g"].setInput( getGreen["out"]["channelValue"] )
		floatToColor["parameters"]["b"].setInput( getRed["out"]["channelValue"] )

		outRGB = GafferOSL.OSLShader()
		outRGB.loadShader( "ImageProcessing/OutLayer" )
		outRGB["parameters"]["layerColor"].setInput( floatToColor["out"]["c"] )

		imageShader = GafferOSL.OSLShader()
		imageShader.loadShader( "ImageProcessing/OutImage" )
		imageShader["parameters"]["in0"].setInput( outRGB["out"]["layer"] )

		reader = GafferImage.ImageReader()
		reader["fileName"].setValue( os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/rgb.100x100.exr" ) )

		image = GafferOSL.OSLImage()
		image["in"].setInput( reader["out"] )

		# we haven't connected the shader yet, so the node should act as a pass through

		self.assertEqual( image["out"].image(), reader["out"].image() )
		self.assertEqual( image["out"].imageHash(), reader["out"].imageHash() )

		# that should all change when we hook up a shader

		cs = GafferTest.CapturingSlot( image.plugDirtiedSignal() )
		image["shader"].setInput( imageShader["out"] )

		self.assertEqual( len( cs ), 5 )
		self.assertTrue( cs[0][0].isSame( image["shader"] ) )
		self.assertTrue( cs[1][0].isSame( image["__shading"] ) )
		self.assertTrue( cs[2][0].isSame( image["out"]["channelNames"] ) )
		self.assertTrue( cs[3][0].isSame( image["out"]["channelData"] ) )
		self.assertTrue( cs[4][0].isSame( image["out"] ) )

		inputImage = reader["out"].image()
		outputImage = image["out"].image()

		self.assertNotEqual( inputImage, outputImage )
		self.assertEqual( outputImage["R"], inputImage["B"] )
		self.assertEqual( outputImage["G"], inputImage["G"] )
		self.assertEqual( outputImage["B"], inputImage["R"] )

		# changes in the shader network should signal more dirtiness

		del cs[:]

		getGreen["parameters"]["channelName"].setValue( "R" )

		self.assertEqual( len( cs ), 5 )
		self.assertTrue( cs[0][0].isSame( image["shader"] ) )
		self.assertTrue( cs[1][0].isSame( image["__shading"] ) )
		self.assertTrue( cs[2][0].isSame( image["out"]["channelNames"] ) )
		self.assertTrue( cs[3][0].isSame( image["out"]["channelData"] ) )
		self.assertTrue( cs[4][0].isSame( image["out"] ) )

		del cs[:]

		floatToColor["parameters"]["r"].setInput( getRed["out"]["channelValue"] )

		self.assertEqual( len( cs ), 5 )
		self.assertTrue( cs[0][0].isSame( image["shader"] ) )
		self.assertTrue( cs[1][0].isSame( image["__shading"] ) )
		self.assertTrue( cs[2][0].isSame( image["out"]["channelNames"] ) )
		self.assertTrue( cs[3][0].isSame( image["out"]["channelData"] ) )
		self.assertTrue( cs[4][0].isSame( image["out"] ) )

		inputImage = reader["out"].image()
		outputImage = image["out"].image()

		self.assertEqual( outputImage["R"], inputImage["R"] )
		self.assertEqual( outputImage["G"], inputImage["R"] )
		self.assertEqual( outputImage["B"], inputImage["R"] )

	def testOnlyAcceptsSurfaceShaders( self ) :

		image = GafferOSL.OSLImage()
		shader = GafferOSL.OSLShader()

		shader.loadShader( "ObjectProcessing/OutPoint" )
		self.assertFalse( image["shader"].acceptsInput( shader["out"] ) )

		shader.loadShader( "ImageProcessing/OutImage" )
		self.assertTrue( image["shader"].acceptsInput( shader["out"] ) )

	def testAcceptsNone( self ) :

		image = GafferOSL.OSLImage()
		self.assertTrue( image["shader"].acceptsInput( None ) )

	def testAcceptsShaderSwitch( self ) :

		script = Gaffer.ScriptNode()
		script["image"] = GafferOSL.OSLImage()
		script["switch"] = Gaffer.Switch()
		script["switch"].setup( Gaffer.Plug() )

		# We're testing a backwards compatibility special case that is
		# only enabled when loading a script, hence the use of `execute()`.
		script.execute( """script["image"]["shader"].setInput( script["switch"]["out"] )""" )
		self.assertTrue( script["image"]["shader"].getInput().isSame( script["switch"]["out"] ) )

	def testAcceptsDot( self ) :

		script = Gaffer.ScriptNode()
		script["image"] = GafferOSL.OSLImage()
		script["switch"] = Gaffer.Switch()
		script["switch"].setup( Gaffer.Plug() )
		script["dot"] = Gaffer.Dot()
		script["dot"].setup( script["switch"]["out"] )

		# We're testing a backwards compatibility special case that is
		# only enabled when loading a script, hence the use of `execute()`.
		script.execute( """script["image"]["shader"].setInput( script["dot"]["out"] )""" )
		self.assertTrue( script["image"]["shader"].getInput().isSame( script["dot"]["out"] ) )

	def testChannelWithZeroValue( self ) :

		outR = GafferOSL.OSLShader()
		outR.loadShader( "ImageProcessing/OutChannel" )
		outR["parameters"]["channelName"].setValue( "R" )
		outR["parameters"]["channelValue"].setValue( 0 )

		imageShader = GafferOSL.OSLShader()
		imageShader.loadShader( "ImageProcessing/OutImage" )
		imageShader["parameters"]["in0"].setInput( outR["out"]["channel"] )

		reader = GafferImage.ImageReader()
		reader["fileName"].setValue( os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/rgb.100x100.exr" ) )

		image = GafferOSL.OSLImage()
		image["in"].setInput( reader["out"] )
		image["shader"].setInput( imageShader["out"] )

		inputImage = reader["out"].image()
		outputImage = image["out"].image()

		self.assertEqual( outputImage["R"], IECore.FloatVectorData( [ 0 ] * inputImage["R"].size() ) )
		self.assertEqual( outputImage["G"], inputImage["G"] )
		self.assertEqual( outputImage["B"], inputImage["B"] )

	def testPassThrough( self ) :

		outR = GafferOSL.OSLShader()
		outR.loadShader( "ImageProcessing/OutChannel" )
		outR["parameters"]["channelName"].setValue( "R" )
		outR["parameters"]["channelValue"].setValue( 0 )

		imageShader = GafferOSL.OSLShader()
		imageShader.loadShader( "ImageProcessing/OutImage" )
		imageShader["parameters"]["in0"].setInput( outR["out"]["channel"] )

		reader = GafferImage.ImageReader()
		reader["fileName"].setValue( os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/rgb.100x100.exr" ) )

		image = GafferOSL.OSLImage()
		image["in"].setInput( reader["out"] )
		image["shader"].setInput( imageShader["out"] )

		self.assertEqual( image["out"]["format"].hash(), reader["out"]["format"].hash() )
		self.assertEqual( image["out"]["dataWindow"].hash(), reader["out"]["dataWindow"].hash() )
		self.assertEqual( image["out"]["metadata"].hash(), reader["out"]["metadata"].hash() )

		self.assertEqual( image["out"]["format"].getValue(), reader["out"]["format"].getValue() )
		self.assertEqual( image["out"]["dataWindow"].getValue(), reader["out"]["dataWindow"].getValue() )
		self.assertEqual( image["out"]["metadata"].getValue(), reader["out"]["metadata"].getValue() )

	def testReferencePromotedPlug( self ) :

		s = Gaffer.ScriptNode()

		s["b"] = Gaffer.Box()
		s["b"]["i"] = GafferOSL.OSLImage()
		p = Gaffer.PlugAlgo.promote( s["b"]["i"]["shader"] )
		p.setName( "p" )

		s["b"].exportForReference( self.temporaryDirectory() + "/test.grf" )

		s["r"] = Gaffer.Reference()
		s["r"].load( self.temporaryDirectory() + "/test.grf" )

		s["s"] = GafferOSL.OSLShader()
		s["s"].loadShader( "ImageProcessing/OutImage" )

		s["r"]["p"].setInput( s["s"]["out"] )

	def testDirtyPropagation( self ) :

		c = GafferImage.Constant()
		o = GafferOSL.OSLImage()
		o["in"].setInput( c["out"] )

		cs = GafferTest.CapturingSlot( o.plugDirtiedSignal() )

		c["color"]["r"].setValue( 1 )
		self.assertTrue( o["out"]["channelData"] in set( x[0] for x in cs ) )

	def testNegativeTileCoordinates( self ) :

		constant = GafferImage.Constant()
		constant["format"].setValue( GafferImage.Format( imath.Box2i( imath.V2i( -128 ), imath.V2i( 128 ) ) ) )

		outR = GafferOSL.OSLShader()
		outR.loadShader( "ImageProcessing/OutChannel" )
		outR["parameters"]["channelName"].setValue( "R" )
		outR["parameters"]["channelValue"].setValue( 1 )

		imageShader = GafferOSL.OSLShader()
		imageShader.loadShader( "ImageProcessing/OutImage" )
		imageShader["parameters"]["in0"].setInput( outR["out"]["channel"] )

		image = GafferOSL.OSLImage()
		image["in"].setInput( constant["out"] )
		image["shader"].setInput( imageShader["out"] )

		sampler = GafferImage.Sampler( image["out"], "R", image["out"]["dataWindow"].getValue() )
		for y in range( -128, 128 ) :
			for x in range( -128, 128 ) :
				self.assertEqual( sampler.sample( x, y ), 1, "Pixel {},{}".format( x, y ) )

	def testGlobals( self ) :

		constant = GafferImage.Constant()
		constant["format"].setValue( GafferImage.Format( imath.Box2i( imath.V2i( -10 ), imath.V2i( 10 ) ) ) )

		globals = GafferOSL.OSLShader()
		globals.loadShader( "Utility/Globals" )

		outP = GafferOSL.OSLShader()
		outP.loadShader( "ImageProcessing/OutLayer" )
		outP["parameters"]["layerColor"].setInput( globals["out"]["globalP"] )

		outU = GafferOSL.OSLShader()
		outU.loadShader( "ImageProcessing/OutChannel" )
		outU["parameters"]["channelName"].setValue( "u" )
		outU["parameters"]["channelValue"].setInput( globals["out"]["globalU"] )

		outV = GafferOSL.OSLShader()
		outV.loadShader( "ImageProcessing/OutChannel" )
		outV["parameters"]["channelName"].setValue( "v" )
		outV["parameters"]["channelValue"].setInput( globals["out"]["globalV"] )

		imageShader = GafferOSL.OSLShader()
		imageShader.loadShader( "ImageProcessing/OutImage" )
		imageShader["parameters"]["in0"].setInput( outP["out"]["layer"] )
		imageShader["parameters"]["in1"].setInput( outU["out"]["channel"] )
		imageShader["parameters"]["in2"].setInput( outV["out"]["channel"] )

		image = GafferOSL.OSLImage()
		image["in"].setInput( constant["out"] )
		image["shader"].setInput( imageShader["out"] )

		displayWindow = image["out"]["format"].getValue().getDisplayWindow()

		samplerR = GafferImage.Sampler( image["out"], "R", displayWindow )
		samplerG = GafferImage.Sampler( image["out"], "G", displayWindow )
		samplerB = GafferImage.Sampler( image["out"], "B", displayWindow )
		samplerU = GafferImage.Sampler( image["out"], "u", displayWindow )
		samplerV = GafferImage.Sampler( image["out"], "v", displayWindow )

		size = imath.V2f( displayWindow.size() )
		uvStep = imath.V2f( 1.0 ) / size
		uvMin = 0.5 * uvStep

		for y in range( displayWindow.min().y, displayWindow.max().y ) :
			for x in range( displayWindow.min().x, displayWindow.max().x ) :

				self.assertEqual( samplerR.sample( x, y ), x + 0.5, "Pixel {},{}".format( x, y ) )
				self.assertEqual( samplerG.sample( x, y ), y + 0.5, "Pixel {},{}".format( x, y ) )
				self.assertEqual( samplerB.sample( x, y ), 0, "Pixel {},{}".format( x, y ) )

				uv = uvMin + uvStep * imath.V2f( imath.V2i( x, y ) - displayWindow.min() )
				self.assertAlmostEqual( samplerU.sample( x, y ), uv.x, delta = 0.0000001, msg = "Pixel {},{}".format( x, y ) )
				self.assertAlmostEqual( samplerV.sample( x, y ), uv.y, delta = 0.0000001, msg = "Pixel {},{}".format( x, y ) )

	def testTextureOrientation( self ) :

		constant = GafferImage.Constant()
		constant["format"].setValue( GafferImage.Format( 32, 32 ) )

		textureFileName = os.path.dirname( __file__ ) + "/images/vRamp.tx"

		outLayer = GafferOSL.OSLCode()
		outLayer["out"]["layer"] = GafferOSL.ClosurePlug(
			direction = Gaffer.Plug.Direction.Out,
			flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic
		)
		outLayer["code"].setValue( 'layer = outLayer( "", texture( "{}", u, v ) )'.format( textureFileName ) )

		outImage = GafferOSL.OSLShader()
		outImage.loadShader( "ImageProcessing/OutImage" )
		outImage["parameters"]["in0"].setInput( outLayer["out"]["layer"] )

		oslImage = GafferOSL.OSLImage()
		oslImage["in"].setInput( constant["out"] )
		oslImage["shader"].setInput( outImage["out"] )

		sampler = GafferImage.Sampler( oslImage["out"], "R", oslImage["out"]["dataWindow"].getValue() )
		for y in range( 0, 31 ) :
			self.assertAlmostEqual( sampler.sample( 5, y ), (y + 0.5) / 32.0, delta = 0.02 )

	def testPullsMinimalSetOfInputChannels( self ) :

		constant = GafferImage.Constant()
		constant["color"].setValue( imath.Color4f( 0.1101, 0.1224, 0.1353, 0.135 ) )

		outLayer = GafferOSL.OSLShader()
		outLayer.loadShader( "ImageProcessing/OutLayer" )

		outImage = GafferOSL.OSLShader()
		outImage.loadShader( "ImageProcessing/OutImage" )
		outImage["parameters"][0].setInput( outLayer["out"]["layer"] )

		oslImage = GafferOSL.OSLImage()
		oslImage["in"].setInput( constant["out"] )
		oslImage["shader"].setInput( outImage["out"] )

		with Gaffer.PerformanceMonitor() as pm :
			oslImage["out"].image()

		# Because the shader doesn't use any input channels,
		# the OSLImage node shouldn't have needed to pull on
		# any of the RGB channels. Because the shader doesn't
		# write to alpha, it does need to pull on alpha to pass
		# it through. Hence we expect a single computation for
		# the Constant's channelData.

		s = pm.plugStatistics( constant["out"]["channelData"] )
		self.assertEqual( s.computeCount, 1 )

	def testShaderNetworkGeneratedInGlobalContext( self ) :

		constant = GafferImage.Constant()

		outLayer = GafferOSL.OSLCode()
		outLayer["out"]["layer"] = GafferOSL.ClosurePlug(
			direction = Gaffer.Plug.Direction.Out,
			flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic
		)
		outLayer["code"].setValue( 'layer = outLayer( "", color( 0, 1, 0) )' )

		outImage = GafferOSL.OSLShader()
		outImage.loadShader( "ImageProcessing/OutImage" )
		outImage["parameters"]["in0"].setInput( outLayer["out"]["layer"] )

		oslImage = GafferOSL.OSLImage()
		oslImage["in"].setInput( constant["out"] )
		oslImage["shader"].setInput( outImage["out"] )

		with Gaffer.ContextMonitor( outImage) as cm :
			GafferImageTest.processTiles( oslImage["out"] )

		cs = cm.combinedStatistics()
		self.assertEqual( cs.numUniqueContexts(), 1 )
		self.assertNotIn( "image:tileOrigin", cs.variableNames() )
		self.assertNotIn( "image:channelName", cs.variableNames() )

if __name__ == "__main__":
	unittest.main()
