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

class OSLImageTest( GafferImageTest.ImageTestCase ) :
	representativeDeepImagePath = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/representativeDeepImage.exr" )

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

		self.assertEqual( GafferImage.ImageAlgo.image( image["out"] ), GafferImage.ImageAlgo.image( reader["out"] ) )

		# that should all change when we hook up a shader

		image["channels"].addChild( Gaffer.NameValuePlug( "", GafferOSL.ClosurePlug(), "testClosure" ) )
		cs = GafferTest.CapturingSlot( image.plugDirtiedSignal() )

		def checkDirtiness( expected):
			self.assertEqual( [ i[0].fullName() for i in cs ], [ "OSLImage." + i for i in expected ] )
			del cs[:]

		image["channels"]["testClosure"]["value"].setInput( imageShader["out"]["out"] )

		checkDirtiness( [
				"channels.testClosure.value", "channels.testClosure", "channels", "__shader", "__shading",
				"out.channelNames", "out.channelData", "out"
		] )

		inputImage = GafferImage.ImageAlgo.image( reader["out"] )
		outputImage = GafferImage.ImageAlgo.image( image["out"] )

		self.assertNotEqual( inputImage, outputImage )
		self.assertEqual( outputImage["R"], inputImage["B"] )
		self.assertEqual( outputImage["G"], inputImage["G"] )
		self.assertEqual( outputImage["B"], inputImage["R"] )

		# changes in the shader network should signal more dirtiness

		getGreen["parameters"]["channelName"].setValue( "R" )
		checkDirtiness( [
				"channels.testClosure.value", "channels.testClosure", "channels", "__shader", "__shading",
				"out.channelNames", "out.channelData", "out"
		] )

		floatToColor["parameters"]["r"].setInput( getRed["out"]["channelValue"] )
		checkDirtiness( [
				"channels.testClosure.value", "channels.testClosure", "channels", "__shader", "__shading",
				"out.channelNames", "out.channelData", "out"
		] )

		inputImage = GafferImage.ImageAlgo.image( reader["out"] )
		outputImage = GafferImage.ImageAlgo.image( image["out"] )

		self.assertEqual( outputImage["R"], inputImage["R"] )
		self.assertEqual( outputImage["G"], inputImage["R"] )
		self.assertEqual( outputImage["B"], inputImage["R"] )

		image["in"].setInput( None )
		checkDirtiness( [
				'in.format', 'in.dataWindow', 'in.metadata', 'in.deep', 'in.sampleOffsets', 'in.channelNames', 'in.channelData', 'in',
				'__shading',
				'out.channelNames', 'out.channelData', 'out.format', 'out.dataWindow', 'out.metadata', 'out.deep', 'out.sampleOffsets', 'out'
		] )

		image["defaultFormat"]["displayWindow"]["max"]["x"].setValue( 200 )
		checkDirtiness( [
				'defaultFormat.displayWindow.max.x', 'defaultFormat.displayWindow.max', 'defaultFormat.displayWindow', 'defaultFormat',
				'__defaultIn.format', '__defaultIn.dataWindow', '__defaultIn', '__shading',
				'out.channelNames', 'out.channelData', 'out.format', 'out.dataWindow', 'out'
		] )

		constant = GafferImage.Constant()
		image["in"].setInput( constant["out"] )

		checkDirtiness( [
				'in.format', 'in.dataWindow', 'in.metadata', 'in.deep', 'in.sampleOffsets', 'in.channelNames', 'in.channelData', 'in',
				'__shading',
				'out.channelNames', 'out.channelData', 'out.format', 'out.dataWindow', 'out.metadata', 'out.deep', 'out.sampleOffsets', 'out'
		] )


	def testAcceptsShaderSwitch( self ) :

		script = Gaffer.ScriptNode()
		script["image"] = GafferOSL.OSLImage()
		script["switch"] = Gaffer.Switch()
		script["switch"].setup( Gaffer.Plug() )

		# We're testing a backwards compatibility special case that is
		# only enabled when loading a script, hence the use of `execute()`.
		script.execute( """script["image"]["shader"].setInput( script["switch"]["out"] )""" )
		self.assertTrue( script["image"]["channels"]["legacyClosure"]["value"].getInput().isSame( script["switch"]["out"] ) )

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
		self.assertTrue( script["image"]["channels"]["legacyClosure"]["value"].getInput().isSame( script["dot"]["out"] ) )

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
		image["shader"].setInput( imageShader["out"]["out"] )

		inputImage = GafferImage.ImageAlgo.image( reader["out"] )
		outputImage = GafferImage.ImageAlgo.image( image["out"] )

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
		image["shader"].setInput( imageShader["out"]["out"] )

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
		s["b"]["i"]["channels"].addChild( Gaffer.NameValuePlug( "", GafferOSL.ClosurePlug(), "testClosure", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		p = Gaffer.PlugAlgo.promote( s["b"]["i"]["channels"]["testClosure"]["value"] )
		p.setName( "p" )

		s["b"].exportForReference( self.temporaryDirectory() + "/test.grf" )

		s["r"] = Gaffer.Reference()
		s["r"].load( self.temporaryDirectory() + "/test.grf" )

		s["s"] = GafferOSL.OSLShader()
		s["s"].loadShader( "ImageProcessing/OutImage" )

		s["r"]["p"].setInput( s["s"]["out"]["out"] )

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
		image["shader"].setInput( imageShader["out"]["out"] )

		sampler = GafferImage.Sampler( image["out"], "R", image["out"]["dataWindow"].getValue() )
		for y in range( -128, 128 ) :
			for x in range( -128, 128 ) :
				self.assertEqual( sampler.sample( x, y ), 1, "Pixel {},{}".format( x, y ) )

	def testDeep( self ) :
		# Simple network to swap channels
		inLayer = GafferOSL.OSLShader()
		inLayer.loadShader( "ImageProcessing/InLayer" )

		colorToFloat = GafferOSL.OSLShader()
		colorToFloat.loadShader( "Conversion/ColorToFloat" )
		colorToFloat["parameters"]["c"].setInput( inLayer["out"]["layerColor"] )

		floatToColor = GafferOSL.OSLShader()
		floatToColor.loadShader( "Conversion/FloatToColor" )
		floatToColor["parameters"]["r"].setInput( colorToFloat["out"]["b"] )
		floatToColor["parameters"]["g"].setInput( colorToFloat["out"]["r"] )
		floatToColor["parameters"]["b"].setInput( colorToFloat["out"]["g"] )

		# Read in a deep image
		imageReader = GafferImage.ImageReader()
		imageReader["fileName"].setValue( self.representativeDeepImagePath )

		# Try running OSLImage on deep image, then flattening
		oslImageDeep = GafferOSL.OSLImage()
		oslImageDeep["channels"].addChild( Gaffer.NameValuePlug( "", Gaffer.Color3fPlug( "value", defaultValue = imath.Color3f( 1, 1, 1 ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ), True, "channel", Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		oslImageDeep["in"].setInput( imageReader["out"] )
		oslImageDeep["channels"]["channel"]["value"].setInput( floatToColor["out"]["c"] )

		postFlatten = GafferImage.DeepToFlat()
		postFlatten["in"].setInput( oslImageDeep["out"] )

		# Try running OSLImage on already flattened image
		preFlatten = GafferImage.DeepToFlat()
		preFlatten["in"].setInput( imageReader["out"] )

		oslImageFlat = GafferOSL.OSLImage()
		oslImageFlat["channels"].addChild( Gaffer.NameValuePlug( "", Gaffer.Color3fPlug( "value", defaultValue = imath.Color3f( 1, 1, 1 ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ), True, "channel", Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		oslImageFlat["in"].setInput( preFlatten["out"] )
		oslImageFlat["channels"]["channel"]["value"].setInput( floatToColor["out"]["c"] )

		# Results should match
		self.assertImagesEqual( postFlatten["out"], oslImageFlat["out"] )

		# Also test reading from UV
		shaderGlobals = GafferOSL.OSLShader( "Globals" )
		shaderGlobals.loadShader( "Utility/Globals" )

		uvToColor = GafferOSL.OSLShader()
		uvToColor.loadShader( "Conversion/FloatToColor" )
		uvToColor["parameters"]["r"].setInput( shaderGlobals["out"]["globalU"] )
		uvToColor["parameters"]["g"].setInput( shaderGlobals["out"]["globalV"] )

		inAlpha = GafferOSL.OSLShader()
		inAlpha.loadShader( "ImageProcessing/InChannel" )
		inAlpha["parameters"]["channelName"].setValue( 'A' )

		multiplyAlpha = GafferOSL.OSLShader()
		multiplyAlpha.loadShader( "Maths/MultiplyColor" )
		multiplyAlpha["parameters"]["a"].setInput( uvToColor["out"]["c"] )
		multiplyAlpha["parameters"]["b"]["r"].setInput( inAlpha["out"]["channelValue"] )
		multiplyAlpha["parameters"]["b"]["g"].setInput( inAlpha["out"]["channelValue"] )
		multiplyAlpha["parameters"]["b"]["b"].setInput( inAlpha["out"]["channelValue"] )

		oslImageDeep["channels"]["channel"]["value"].setInput( multiplyAlpha["out"]["out"] )

		outImage = GafferImage.ImageAlgo.image( postFlatten["out"] )
		size = outImage.dataWindow.size() + imath.V2i( 1 )
		i = 0
		for y in range( size.y ):
			for x in range( size.x ):
				self.assertAlmostEqual( outImage["R"][i], (x + 0.5) / size.x * outImage["A"][i], places = 5 )
				self.assertAlmostEqual( outImage["G"][i], (size.y - y - 0.5) / size.y * outImage["A"][i], places = 5 )
				i += 1

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
		image["shader"].setInput( imageShader["out"]["out"] )

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
		oslImage["shader"].setInput( outImage["out"]["out"] )

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
		oslImage["shader"].setInput( outImage["out"]["out"] )

		with Gaffer.PerformanceMonitor() as pm :
			GafferImage.ImageAlgo.image( oslImage["out"] )

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
		oslImage["shader"].setInput( outImage["out"]["out"] )

		with Gaffer.ContextMonitor( oslImage["__oslCode"] ) as cm :
			GafferImageTest.processTiles( oslImage["out"] )

		cs = cm.combinedStatistics()
		self.assertEqual( cs.numUniqueContexts(), 1 )
		self.assertNotIn( "image:tileOrigin", cs.variableNames() )
		self.assertNotIn( "image:channelName", cs.variableNames() )

	def testAllTypes( self ) :

		i = GafferOSL.OSLImage()
		i["defaultFormat"].setValue( GafferImage.Format( imath.Box2i( imath.V2i(0), imath.V2i( 5 ) ) ) )

		i["channels"].addChild( Gaffer.NameValuePlug( "", imath.Color3f(1,3,5) ) )
		i["channels"].addChild( Gaffer.NameValuePlug( "testFloat", 42.42 ) )
		i["channels"].addChild( Gaffer.NameValuePlug( "testColor", imath.Color3f(12,13,14) ) )

		image = GafferImage.ImageAlgo.image( i['out'] )

		self.assertEqual( image["R"], IECore.FloatVectorData( [1]*25 ) )
		self.assertEqual( image["G"], IECore.FloatVectorData( [3]*25 ) )
		self.assertEqual( image["B"], IECore.FloatVectorData( [5]*25 ) )
		self.assertEqual( image["testFloat"], IECore.FloatVectorData( [42.42]*25 ) )
		self.assertEqual( image["testColor.R"], IECore.FloatVectorData( [12]*25 ) )
		self.assertEqual( image["testColor.G"], IECore.FloatVectorData( [13]*25 ) )
		self.assertEqual( image["testColor.B"], IECore.FloatVectorData( [14]*25 ) )

	def testClosure( self ) :

		i = GafferOSL.OSLImage()
		i["defaultFormat"].setValue( GafferImage.Format( imath.Box2i( imath.V2i(0), imath.V2i( 5 ) ) ) )
		i["channels"].addChild( Gaffer.NameValuePlug( "testClosure", GafferOSL.ClosurePlug() ) )

		code = GafferOSL.OSLCode( "OSLCode" )
		code["out"].addChild( GafferOSL.ClosurePlug( "output1", direction = Gaffer.Plug.Direction.Out ) )
		code["code"].setValue( 'output1 = outLayer( "blah", color( 0.1, 0.2, 0.3 ) ) + outChannel( "foo", 0.5 );' )

		i["channels"][0]["value"].setInput( code["out"]["output1"] )

		image = GafferImage.ImageAlgo.image( i['out'] )
		self.assertEqual( image["blah.R"], IECore.FloatVectorData( [0.1]*25 ) )
		self.assertEqual( image["blah.G"], IECore.FloatVectorData( [0.2]*25 ) )
		self.assertEqual( image["blah.B"], IECore.FloatVectorData( [0.3]*25 ) )
		self.assertEqual( image["foo"], IECore.FloatVectorData( [0.5]*25 ) )

	def testUndo( self ) :

		s = Gaffer.ScriptNode()

		i = GafferOSL.OSLImage()
		s.addChild( i )

		self.assertFalse( s.undoAvailable() )

		self.assertEqual( len( i["__oslCode"]["parameters"].children() ), 0 )

		with Gaffer.UndoScope( s ) :
			i["channels"].addChild( Gaffer.NameValuePlug( "testColor", imath.Color3f( 42 ) ) )
			i["channels"].addChild( Gaffer.NameValuePlug( "testFloat", 42.42 ) )

		self.assertTrue( s.undoAvailable() )
		self.assertEqual( len( i["__oslCode"]["parameters"].children() ), 4 )

		with Gaffer.UndoScope( s ) :
			del i["channels"][0]
			del i["channels"][0]

		self.assertEqual( len( i["__oslCode"]["parameters"].children() ), 0 )

		# Test that the internal connections are recreated correctly when undoing adding and removing channels
		s.undo()

		self.assertEqual( len( i["__oslCode"]["parameters"].children() ), 4 )

		s.undo()

		self.assertEqual( len( i["__oslCode"]["parameters"].children() ), 0 )

	def testDefaultFormat( self ):
		constant = GafferImage.Constant()

		oslImage = GafferOSL.OSLImage()
		oslImage["channels"].addChild( Gaffer.NameValuePlug( "", imath.Color3f( 0.5, 0.6, 0.7 )  ) )

		self.assertEqual( oslImage["out"]["dataWindow"].getValue(), imath.Box2i( imath.V2i( 0 ), imath.V2i( 1920, 1080 ) ) )
		self.assertEqual( oslImage["out"]["format"].getValue().getDisplayWindow(), imath.Box2i( imath.V2i( 0 ), imath.V2i( 1920, 1080 ) ) )

		oslImage["defaultFormat"].setValue( GafferImage.Format( imath.Box2i( imath.V2i(0), imath.V2i( 5 ) ) ) )

		self.assertEqual( oslImage["out"]["dataWindow"].getValue(), imath.Box2i( imath.V2i( 0 ), imath.V2i( 5, 5 ) ) )
		self.assertEqual( oslImage["out"]["format"].getValue().getDisplayWindow(), imath.Box2i( imath.V2i( 0 ), imath.V2i( 5, 5 ) ) )
		self.assertEqual( GafferImage.ImageAlgo.image( oslImage["out"] )["G"], IECore.FloatVectorData( [0.6] * 25 ) )

		oslImage["in"].setInput( constant["out"] )

		self.assertEqual( oslImage["out"]["dataWindow"].getValue(), imath.Box2i( imath.V2i( 0 ), imath.V2i( 1920, 1080 ) ) )
		self.assertEqual( oslImage["out"]["format"].getValue().getDisplayWindow(), imath.Box2i( imath.V2i( 0 ), imath.V2i( 1920, 1080 ) ) )

		constant["format"].setValue( GafferImage.Format( imath.Box2i( imath.V2i(0), imath.V2i( 4 ) ) ) )
		self.assertEqual( oslImage["out"]["dataWindow"].getValue(), imath.Box2i( imath.V2i( 0 ), imath.V2i( 4, 4 ) ) )
		self.assertEqual( oslImage["out"]["format"].getValue().getDisplayWindow(), imath.Box2i( imath.V2i( 0 ), imath.V2i( 4, 4 ) ) )
		self.assertEqual( GafferImage.ImageAlgo.image( oslImage["out"] )["G"], IECore.FloatVectorData( [0.6] * 16 ) )

if __name__ == "__main__":
	unittest.main()
