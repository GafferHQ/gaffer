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
import inspect

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
		for useClosure in [ False, True ]:

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

			reader = GafferImage.ImageReader()
			reader["fileName"].setValue( os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/rgb.100x100.exr" ) )

			shuffle = GafferImage.Shuffle()
			shuffle["in"].setInput( reader["out"] )
			shuffle["channels"].addChild( GafferImage.Shuffle.ChannelPlug( "channel" ) )
			shuffle["channels"]["channel"]["out"].setValue( 'unchangedR' )
			shuffle["channels"]["channel"]["in"].setValue( 'R' )

			image = GafferOSL.OSLImage()
			image["in"].setInput( shuffle["out"] )

			# we haven't connected the shader yet, so the node should act as a pass through

			self.assertEqual( GafferImage.ImageAlgo.image( image["out"] ), GafferImage.ImageAlgo.image( shuffle["out"] ) )

			# that should all change when we hook up a shader

			if useClosure:

				outRGB = GafferOSL.OSLShader()
				outRGB.loadShader( "ImageProcessing/OutLayer" )
				outRGB["parameters"]["layerColor"].setInput( floatToColor["out"]["c"] )

				imageShader = GafferOSL.OSLShader()
				imageShader.loadShader( "ImageProcessing/OutImage" )
				imageShader["parameters"]["in0"].setInput( outRGB["out"]["layer"] )

				image["channels"].addChild( Gaffer.NameValuePlug( "", GafferOSL.ClosurePlug(), "testClosure" ) )

			else:

				image["channels"].addChild( Gaffer.NameValuePlug( "", imath.Color3f(), "testColor" ) )

			cs = GafferTest.CapturingSlot( image.plugDirtiedSignal() )

			def checkDirtiness( expected):
				self.assertEqual( [ i[0].fullName() for i in cs ], [ "OSLImage." + i for i in expected ] )
				del cs[:]

			if useClosure:
				image["channels"]["testClosure"]["value"].setInput( imageShader["out"]["out"] )
				channelsDirtied = ["channels.testClosure.value", "channels.testClosure"]
			else:
				image["channels"]["testColor"]["value"].setInput( floatToColor["out"]["c"] )
				channelsDirtied = [
					"channels.testColor.value.r", "channels.testColor.value.g", "channels.testColor.value.b",
					"channels.testColor.value", "channels.testColor"
				]

			checkDirtiness( channelsDirtied + [
					"channels", "__shader", "__shading",
					"__affectedChannels", "out.channelNames", "out.channelData", "out"
			] )

			inputImage = GafferImage.ImageAlgo.image( shuffle["out"] )

			with Gaffer.ContextMonitor( image["__shading"] ) as monitor :
				self.assertEqual( image["out"].channelNames(), IECore.StringVectorData( [ "A", "B", "G", "R", "unchangedR" ] ) )
				# Evaluating channel names only requires evaluating the shading plug if we have a closure
				self.assertEqual( monitor.combinedStatistics().numUniqueContexts(), 1 if useClosure else 0 )

				# Channels we don't touch should be passed through unaltered
				for channel, changed in [('B',True), ('G',True), ('R',True), ('A',False), ('unchangedR',False) ]:
					self.assertEqual(
						image["out"].channelDataHash( channel, imath.V2i( 0, 0 ) ) ==
						shuffle["out"].channelDataHash( channel, imath.V2i( 0, 0 ) ),
						not changed
					)
					image["out"].channelData( channel, imath.V2i( 0, 0 ) )

			# Should only need one shading evaluate for all channels
			self.assertEqual( monitor.combinedStatistics().numUniqueContexts(), 1 )

			outputImage = GafferImage.ImageAlgo.image( image["out"] )

			self.assertNotEqual( inputImage, outputImage )
			self.assertEqual( outputImage["R"], inputImage["B"] )
			self.assertEqual( outputImage["G"], inputImage["G"] )
			self.assertEqual( outputImage["B"], inputImage["R"] )

			# changes in the shader network should signal more dirtiness

			getGreen["parameters"]["channelName"].setValue( "R" )
			checkDirtiness( channelsDirtied + [
					"channels", "__shader", "__shading",
					"__affectedChannels", "out.channelNames", "out.channelData", "out"
			] )

			floatToColor["parameters"]["r"].setInput( getRed["out"]["channelValue"] )
			checkDirtiness( channelsDirtied + [
					"channels", "__shader", "__shading",
					"__affectedChannels", "out.channelNames", "out.channelData", "out"
			] )


			inputImage = GafferImage.ImageAlgo.image( shuffle["out"] )
			outputImage = GafferImage.ImageAlgo.image( image["out"] )

			self.assertEqual( outputImage["R"], inputImage["R"] )
			self.assertEqual( outputImage["G"], inputImage["R"] )
			self.assertEqual( outputImage["B"], inputImage["R"] )
			self.assertEqual( outputImage["A"], inputImage["A"] )
			self.assertEqual( outputImage["unchangedR"], inputImage["unchangedR"] )

			image["in"].setInput( None )
			checkDirtiness( [
					'in.viewNames', 'in.format', 'in.dataWindow', 'in.metadata', 'in.deep', 'in.sampleOffsets', 'in.channelNames', 'in.channelData', 'in',
					'out.viewNames', '__shading', '__affectedChannels',
					'out.channelNames', 'out.channelData', 'out.format', 'out.dataWindow', 'out.metadata', 'out.deep', 'out.sampleOffsets', 'out'
			] )

			image["defaultFormat"]["displayWindow"]["max"]["x"].setValue( 200 )
			checkDirtiness( [
					'defaultFormat.displayWindow.max.x', 'defaultFormat.displayWindow.max', 'defaultFormat.displayWindow', 'defaultFormat',
					'__defaultIn.format', '__defaultIn.dataWindow', '__defaultIn', '__shading', '__affectedChannels',
					'out.channelNames', 'out.channelData', 'out.format', 'out.dataWindow', 'out'
			] )

			constant = GafferImage.Constant()
			image["in"].setInput( constant["out"] )

			checkDirtiness( [
					'in.viewNames', 'in.format', 'in.dataWindow', 'in.metadata', 'in.deep', 'in.sampleOffsets', 'in.channelNames', 'in.channelData', 'in',
					'out.viewNames', '__shading', '__affectedChannels',
					'out.channelNames', 'out.channelData', 'out.format', 'out.dataWindow', 'out.metadata', 'out.deep', 'out.sampleOffsets', 'out'
			] )

			image["in"].setInput( shuffle["out"] )
			if useClosure:
				outRGB["parameters"]["layerName"].setValue( "newLayer" )
			else:
				image["channels"][0]["name"].setValue( "newLayer" )

			self.assertEqual( image["out"].channelNames(), IECore.StringVectorData(
				[ "A", "B", "G", "R", "newLayer.B", "newLayer.G", "newLayer.R", "unchangedR" ]
			) )

			for channel in ['B', 'G', 'R', 'A', 'unchangedR' ]:
				self.assertEqual(
					image["out"].channelDataHash( channel, imath.V2i( 0, 0 ) ),
					shuffle["out"].channelDataHash( channel, imath.V2i( 0, 0 ) )
				)
				self.assertEqual(
					image["out"].channelData( channel, imath.V2i( 0, 0 ) ),
					shuffle["out"].channelData( channel, imath.V2i( 0, 0 ) )
				)

			crop = GafferImage.Crop()
			crop["area"].setValue( imath.Box2i( imath.V2i( 0, 0 ), imath.V2i( 0, 0 ) ) )
			crop["in"].setInput( shuffle["out"] )

			image["in"].setInput( crop["out"] )

			if useClosure:
				# When using closures, we can't find out about the new channels being added if the datawindow is
				# empty
				self.assertEqual( image["out"].channelNames(), IECore.StringVectorData(
					[ "A", "B", "G", "R", "unchangedR" ]
				) )
			else:
				self.assertEqual( image["out"].channelNames(), IECore.StringVectorData(
					[ "A", "B", "G", "R", "newLayer.B", "newLayer.G", "newLayer.R", "unchangedR" ]
				) )



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
		constant["format"].setValue(
			GafferImage.Format( GafferImage.ImagePlug.tileSize(), GafferImage.ImagePlug.tileSize() )
		)

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

	# Extreme example of doing something very expensive in OSLImage
	def mandelbrotNode( self ):
		mandelbrotCode = GafferOSL.OSLCode()
		mandelbrotCode["parameters"].addChild( Gaffer.IntPlug( "iterations", defaultValue = 0, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ) )
		mandelbrotCode["out"].addChild( Gaffer.FloatPlug( "outFloat", direction = Gaffer.Plug.Direction.Out ) )
		mandelbrotCode["code"].setValue( inspect.cleandoc(
			"""
			// Basic mandelbrot adapted from surface shader here:
			// https://github.com/AcademySoftwareFoundation/OpenShadingLanguage/blob/master/src/shaders/mandelbrot.osl
			point center = point (0,0,0);
			float scale = 2;
			point cent = center;
			point c = scale * point(2*(u-0.5), 2*((1-v)-0.5), 0) + cent;
			point z = c;
			int i;
			for (i = 1; i < iterations && dot(z,z) < 4.0; ++i) {
			float x = z[0], y = z[1];
			z = point (x*x - y*y, 2*x*y, 0) + c;
			}
			if (i < iterations) {
				float f = pow(float(i)/iterations, 1/log10(float(iterations)));
				outFloat = f;
			} else {
				outFloat = 0;
			}
			"""
		) )
		return mandelbrotCode

	def testBadCachePolicyHang( self ):

		# Using the legacy cache policy for OSLImage.shadingPlug creates a hang due to tbb task stealing,
		# though it's a bit hard to actually demonstrate

		constant = GafferImage.Constant()
		constant["format"].setValue( GafferImage.Format( 128, 128, 1.000 ) )

		# Need a slow to compute OSL code in order to trigger hang
		mandelbrotCode = self.mandelbrotNode()

		# In order to trigger the hang, we need to mix threads which are stuck waiting for an expression which
		# uses the Standard policy with threads that are actually finishing, so that tbb tries to start up new
		# threads while we're waiting for the expression result.  To do this, we use the "var" context variable
		# to create two versions of this OSLCode
		mandelbrotCode["varExpression"] = Gaffer.Expression()
		mandelbrotCode["varExpression"].setExpression( 'parent.parameters.iterations = 100000 + context( "var", 0 );', "OSL" )


		oslImage = GafferOSL.OSLImage()
		oslImage["channels"].addChild( Gaffer.NameValuePlug( "", Gaffer.Color3fPlug( "value", defaultValue = imath.Color3f( 1, 1, 1 ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ), True, "channel", Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		oslImage["in"].setInput( constant["out"] )
		oslImage["channels"]["channel"]["value"][0].setInput( mandelbrotCode["out"]["outFloat"] )
		oslImage["channels"]["channel"]["value"][1].setInput( mandelbrotCode["out"]["outFloat"] )
		oslImage["channels"]["channel"]["value"][2].setInput( mandelbrotCode["out"]["outFloat"] )

		# This imageStats is use to create non-blocking slow calculations
		imageStats = GafferImage.ImageStats()
		imageStats["in"].setInput( oslImage["out"] )
		imageStats["area"].setValue( imath.Box2i( imath.V2i( 0, 0 ), imath.V2i( 64, 64 ) ) )


		# This box does the non-blocking slow calculation, followed by a blocking slow calculation.
		# This ensures that tasks which do just the non-block calculation will start finishing while
		# the blocking slow calculation is still running, allowing tbb to try running more threads
		# on the blocking calcluation, realizing they can't run, and stealing tasks onto those threads
		# which can hit the Standard policy lock on the expression upstream and deadlock, unless the
		# OSLImage isolates its threads correctly
		expressionBox = Gaffer.Box()
		expressionBox.addChild( Gaffer.FloatVectorDataPlug( "inChannelData", defaultValue = IECore.FloatVectorData( [ ] ) ) )
		expressionBox.addChild( Gaffer.FloatPlug( "inStat" ) )
		expressionBox.addChild( Gaffer.FloatPlug( "out", direction = Gaffer.Plug.Direction.Out ) )
		expressionBox["inChannelData"].setInput( oslImage["out"]["channelData"] )
		expressionBox["inStat"].setInput( imageStats["average"]["r"] )

		expressionBox["contextVariables"] = Gaffer.ContextVariables()
		expressionBox["contextVariables"].setup( Gaffer.FloatVectorDataPlug( "in", defaultValue = IECore.FloatVectorData( [ ] ) ) )
		expressionBox["contextVariables"]["variables"].addChild( Gaffer.NameValuePlug( "image:tileOrigin", Gaffer.V2iPlug( "value" ), True, "member1" ) )
		expressionBox["contextVariables"]["variables"].addChild( Gaffer.NameValuePlug( "image:channelName", Gaffer.StringPlug( "value", defaultValue = 'R' ), True, "member2" ) )
		expressionBox["contextVariables"]["variables"].addChild( Gaffer.NameValuePlug( "var", Gaffer.IntPlug( "value", defaultValue = 1 ), True, "member3" ) )
		expressionBox["contextVariables"]["in"].setInput( expressionBox["inChannelData"] )

		expressionBox["expression"] = Gaffer.Expression()
		expressionBox["expression"].setExpression( inspect.cleandoc(
			"""
			d = parent["contextVariables"]["out"]
			parent["out"] = d[0] + parent["inStat"]
			"""
		) )

		# Create a switch to mix which tasks perform the non-blocking or blocking calculation - we need a mixture
		# to trigger the hang
		switch = Gaffer.Switch()
		switch.setup( Gaffer.IntPlug( "in", defaultValue = 0, ) )
		switch["in"][0].setInput( expressionBox["out"] )
		switch["in"][1].setInput( imageStats["average"]["r"] )

		switch["switchExpression"] = Gaffer.Expression()
		switch["switchExpression"].setExpression( 'parent.index = ( stoi( context( "testContext", "0" ) ) % 10 ) > 5;', "OSL" )

		# In order to evaluate this expression a bunch of times at once with different values of "testContext",
		# we set up a simple scene that can be evaluated with GafferSceneTest.traversScene.
		# In theory, we could use a simple function that used a parallel_for to evaluate switch["out"], but for
		# some reason we don't entirely understand, this does not trigger the hang
		import GafferSceneTest
		import GafferScene

		sphere = GafferScene.Sphere()

		pathFilter = GafferScene.PathFilter()
		pathFilter["paths"].setValue( IECore.StringVectorData( [ '/sphere' ] ) )

		customAttributes = GafferScene.CustomAttributes()
		customAttributes["attributes"].addChild( Gaffer.NameValuePlug( "foo", Gaffer.FloatPlug( "value" ), True, "member1" ) )
		customAttributes["attributes"]["member1"]["value"].setInput( switch["out"] )
		customAttributes["in"].setInput( sphere["out"] )
		customAttributes["filter"].setInput( pathFilter["out"] )

		collectScenes = GafferScene.CollectScenes()
		collectScenes["in"].setInput( customAttributes["out"] )
		collectScenes["rootNames"].setValue( IECore.StringVectorData( [ str(i) for i in range(1000) ] ) )
		collectScenes["rootNameVariable"].setValue( 'testContext' )

		# When OSLImage.shadingPlug is not correctly isolated, and grain size on ShadingEngine is smaller than the
		# image tile size, this fails about 50% of the time.  Running it 5 times makes the failure pretty consistent.
		for i in range( 5 ):
			Gaffer.ValuePlug.clearCache()
			Gaffer.ValuePlug.clearHashCache()
			GafferSceneTest.traverseScene( collectScenes["out"] )

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testMinimalPerf( self ) :

		constant = GafferImage.Constant()
		constant["format"].setValue( GafferImage.Format( 4096, 4096 ) )

		floatToColor = GafferOSL.OSLShader()
		floatToColor.loadShader( "Conversion/FloatToColor" )

		oslImage = GafferOSL.OSLImage()
		oslImage["in"].setInput( constant["out"] )
		oslImage["channels"].addChild( Gaffer.NameValuePlug( "", Gaffer.Color3fPlug( "value" ), True, "channel" ) )
		oslImage["channels"]["channel"]["value"].setInput( floatToColor["out"]["c"] )

		GafferImage.ImageAlgo.image( constant["out"] )

		# Run the fastest possible OSLImage on lots of tiles, to highlight any constant overhead
		with GafferTest.TestRunner.PerformanceScope() :
			GafferImage.ImageAlgo.image( oslImage["out"] )

	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 1)
	def testCollaboratePerf( self ) :
		# Test an expensive OSLImage, with many output tiles depending on the same input tiles,
		# which should give TaskCollaborate a chance to show some benefit

		constant = GafferImage.Constant()
		constant["format"].setValue( GafferImage.Format( 128, 128 ) )

		deleteChannels = GafferImage.DeleteChannels( "DeleteChannels" )
		deleteChannels["in"].setInput( constant["out"] )
		deleteChannels["mode"].setValue( GafferImage.DeleteChannels.Mode.Keep )
		deleteChannels["channels"].setValue( 'R' )

		mandelbrotCode = self.mandelbrotNode()
		mandelbrotCode["parameters"]["iterations"].setValue( 500000 )

		oslImage = GafferOSL.OSLImage()
		oslImage["in"].setInput( deleteChannels["out"] )
		oslImage["channels"].addChild( Gaffer.NameValuePlug( "R", Gaffer.FloatPlug( "value" ), True, "channel" ) )
		oslImage["channels"]["channel"]["value"].setInput( mandelbrotCode["out"]["outFloat"] )

		resize = GafferImage.Resize()
		resize["in"].setInput( oslImage["out"] )
		resize["format"].setValue( GafferImage.Format( imath.Box2i( imath.V2i( 0 ), imath.V2i( 2048 ) ), 1 ) )
		# We use a resize because it pulls the input tiles repeatedly, we don't want to spend time on resizing
		# pixels, so use a fast filter
		resize["filter"].setValue( 'box' )

		with GafferTest.TestRunner.PerformanceScope() :
			GafferImage.ImageAlgo.image( resize["out"] )

	def testOSLSplineMatch( self ):

		g = GafferOSL.OSLShader()
		g.loadShader( "Utility/Globals" )
		colorSpline = GafferOSL.OSLShader()
		colorSpline.loadShader( "Pattern/ColorSpline" )
		colorSpline["parameters"]["x"].setInput( g["out"]["globalU"] )

		# Values chosen to trigger a precision issue with OSL's splineinverse on a constant basis
		# if it is not avoided.  The values have also been selected a little to avoid showing
		# issues we don't want to deal with:
		#  * The X values are non-decreasing when evaluated as catmullRom ( non-monotonic X values
		#    are a weird special case that can't be handled well, and OSL and Cortex deal with it
		#    differently badly
		#  * The values are chosen so that the discontinuities in "constant" mode don't lie
		#    directly on a pixel center - if they did, it's comes down solely to floating point
		#    precision which side we lie on.
		colorSpline["parameters"]["spline"].setValue(
			Gaffer.SplineDefinitionfColor3f(
				(
					( 0.1580, imath.Color3f( 0.71, 0.21, 0.39 ) ),
					( 0.2249, imath.Color3f( 0, 0.30, 0 ) ),
					( 0.2631, imath.Color3f( 0, 0.46, 0 ) ),
					( 0.3609, imath.Color3f( 0.71, 0.39, 0.054 ) ),
					( 0.3826, imath.Color3f( 0, 0, 0 ) ),
					( 0.4116, imath.Color3f( 0.87, 0.31, 1 ) ),
					( 0.4300, imath.Color3f( 0, 0, 0 ) ),
					( 0.4607, imath.Color3f( 0.71, 0.21, 0.39 ) ),
					( 0.5996, imath.Color3f( 0, 1, 1 ) ),
					( 0.9235, imath.Color3f( 1, 0.25, 0.25 ) )
				), Gaffer.SplineDefinitionInterpolation.Constant
			)
		)

		oslImage = GafferOSL.OSLImage( "OSLImage" )
		oslImage["channels"].addChild( Gaffer.NameValuePlug( "", Gaffer.Color3fPlug( "value" ), True, "channel" ) )
		oslImage["channels"]["channel"]["value"].setInput( colorSpline["out"]["c"] )
		oslImage["defaultFormat"].setValue( GafferImage.Format( 3000, 64, 1.000 ) )

		for i in Gaffer.SplineDefinitionInterpolation.names.values():
			colorSpline["parameters"]["spline"]["interpolation"].setValue( i )
			cortexSpline = colorSpline["parameters"]["spline"].getValue().spline()
			samplers = [
				GafferImage.Sampler( oslImage["out"], c, imath.Box2i( imath.V2i( 0 ), imath.V2i( 3000, 1 ) ) )
				for c in [ "R", "G", "B" ]
			]
			for x in range( 3000 ):
				result = cortexSpline( ( x + 0.5 ) / 3000.0 )
				for c in range(3):
					self.assertAlmostEqual( samplers[c].sample( x, 0 ), result[c], places = 3 )

if __name__ == "__main__":
	unittest.main()
