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

import os
import unittest
import inspect
import imath

import IECore

import Gaffer
import GafferTest
import GafferImage
import GafferImageTest

class CollectImagesTest( GafferImageTest.ImageTestCase ) :

	layersPath = GafferImageTest.ImageTestCase.imagesPath() / "layers.10x10.exr"

	# Test against an image which has a different positioned box in each image layer, and a datawindow
	# that has been enlarged to hold all layers
	def testSimpleLayers( self ) :

		expected = GafferImage.ImageReader()
		expected["fileName"].setValue( self.layersPath )

		constant = GafferImage.Constant()
		constant["format"].setValue( GafferImage.Format( 10, 10, 1.000 ) )
		constant["color"].setValue( imath.Color4f( 1, 0, 0, 1 ) )

		crop = GafferImage.Crop()
		crop["affectDisplayWindow"].setValue( False )
		crop["in"].setInput( constant["out"] )

		delete = GafferImage.DeleteChannels()
		delete["channels"].setValue( "A" )
		delete["in"].setInput( crop["out"] )

		collect = GafferImage.CollectImages()
		collect["rootLayers"].setValue( IECore.StringVectorData( [ '0', '1', '2' ] ) )
		collect["in"].setInput( delete["out"] )


		e = Gaffer.Expression()
		crop.addChild( e )
		e.setExpression( inspect.cleandoc( """
		layer = context.get( "collect:layerName", None )

		if layer:
			o = imath.V2i(2, 2 ) * ( 1 + int( layer ) )
			area = imath.Box2i( o, imath.V2i( 1, 1 ) + o )
		else:
			area = imath.Box2i( imath.V2i( 3, 1 ), imath.V2i( 4, 2 ) )

		parent["area"] = area
		""" ), "python" )

		copyChannels = GafferImage.CopyChannels()
		copyChannels["channels"].setValue( "*" )
		copyChannels["in"][0].setInput( crop["out"] )
		copyChannels["in"][1].setInput( collect["out"] )

		self.assertImagesEqual( copyChannels["out"], expected["out"], ignoreMetadata = True )

	def testLayerMapping( self ) :

		constant1 = GafferImage.Constant()
		constant1['color'].setValue( imath.Color4f( 0.1, 0.2, 0.3, 0.4 ) )
		constant1["format"].setValue( GafferImage.Format( 10, 10, 1.000 ) )

		metadata1 = GafferImage.ImageMetadata()
		metadata1["in"].setInput( constant1["out"] )
		metadata1["metadata"].addChild( Gaffer.NameValuePlug( "test", 1 ) )

		constant2 = GafferImage.Constant()
		constant2['color'].setValue( imath.Color4f( 0.2, 0.4, 0.6, 0.8 ) )
		constant2["format"].setValue( GafferImage.Format( 20, 20, 1.000 ) )

		metadata2 = GafferImage.ImageMetadata()
		metadata2["in"].setInput( constant2["out"] )
		metadata2["metadata"].addChild( Gaffer.NameValuePlug( "test", 2 ) )

		switch = Gaffer.Switch()
		switch.setup( GafferImage.ImagePlug() )
		switch["in"][0].setInput( metadata1["out"] )
		switch["in"][1].setInput( metadata2["out"] )

		e = Gaffer.Expression()
		switch.addChild( e )
		e.setExpression( 'parent["index"] = context["collect:layerName"] != "A"', "python" )

		collect = GafferImage.CollectImages()
		collect["in"].setInput( switch["out"] )

		# Metadata and format are driven by the first layer

		collect["rootLayers"].setValue( IECore.StringVectorData( [ 'A', 'B' ] ) )
		self.assertEqual( collect["out"]["format"].getValue(), GafferImage.Format( 10, 10, 1) )
		self.assertEqual( collect["out"]["metadata"].getValue(), IECore.CompoundData( { "test" : 1 } ) )

		collect["rootLayers"].setValue( IECore.StringVectorData( [ 'B', 'A' ] ) )
		self.assertEqual( collect["out"]["format"].getValue(), GafferImage.Format( 20, 20, 1) )
		self.assertEqual( collect["out"]["metadata"].getValue(), IECore.CompoundData( { "test" : 2 } ) )

		collect["rootLayers"].setValue( IECore.StringVectorData( [] ) )
		self.assertEqual( collect["out"]["format"].getValue(), constant1["format"].getDefaultFormat( Gaffer.Context.current() ) )
		self.assertEqual( collect["out"]["metadata"].getValue(), IECore.CompoundData() )

		sampler = GafferImage.ImageSampler( "ImageSampler" )
		sampler["pixel"].setValue( imath.V2f( 1, 1 ) )
		sampler["channels"].setValue( IECore.StringVectorData( [ "A.R", "A.G","A.B","A.A" ] ) )
		sampler["image"].setInput( collect["out"] )

		collect["rootLayers"].setValue( IECore.StringVectorData( [ 'A' ] ) )


		self.assertEqual( list(collect["out"]["channelNames"].getValue()), [ "A.R", "A.G", "A.B", "A.A" ] )
		self.assertEqual( sampler["color"].getValue(), imath.Color4f( 0.1, 0.2, 0.3, 0.4 ) )

		# Test simple duplicate
		collect["rootLayers"].setValue( IECore.StringVectorData( [ 'A', 'A' ] ) )

		self.assertEqual( list(collect["out"]["channelNames"].getValue()), [ "A.R", "A.G", "A.B", "A.A" ] )
		self.assertEqual( sampler["color"].getValue(), imath.Color4f( 0.1, 0.2, 0.3, 0.4 ) )

		collect["rootLayers"].setValue( IECore.StringVectorData( [ 'A', 'B' ] ) )
		self.assertEqual( list(collect["out"]["channelNames"].getValue()), [
			"A.R", "A.G", "A.B", "A.A",
			"B.R", "B.G", "B.B", "B.A" ] )
		self.assertEqual( sampler["color"].getValue(), imath.Color4f( 0.1, 0.2, 0.3, 0.4 ) )
		sampler["channels"].setValue( IECore.StringVectorData( [ "B.R", "B.G","B.B","B.A" ] ) )
		self.assertEqual( sampler["color"].getValue(), imath.Color4f( 0.2, 0.4, 0.6, 0.8 ) )

		# Test overlapping names take the first layer
		constant1["layer"].setValue( "B" )
		collect["rootLayers"].setValue( IECore.StringVectorData( [ 'A', 'A.B' ] ) )
		sampler["channels"].setValue( IECore.StringVectorData( [ "A.B.R", "A.B.G","A.B.B","A.B.A" ] ) )
		self.assertEqual( list(collect["out"]["channelNames"].getValue()), [ "A.B.R", "A.B.G", "A.B.B", "A.B.A" ] )
		self.assertEqual( sampler["color"].getValue(), imath.Color4f( 0.1, 0.2, 0.3, 0.4 ) )
		collect["rootLayers"].setValue( IECore.StringVectorData( [ 'A.B', 'A' ] ) )
		self.assertEqual( list(collect["out"]["channelNames"].getValue()), [ "A.B.R", "A.B.G", "A.B.B", "A.B.A" ] )
		self.assertEqual( sampler["color"].getValue(), imath.Color4f( 0.2, 0.4, 0.6, 0.8 ) )

	def testDeep( self ) :

		constantA = GafferImage.Constant()
		constantA["color"].setValue( imath.Color4f( 0.1, 0.2, 0.3, 0.4 ) )
		constantB = GafferImage.Constant()
		constantB["color"].setValue( imath.Color4f( 0.01, 0.02, 0.03, 0.04 ) )
		constantC = GafferImage.Constant()
		constantC["color"].setValue( imath.Color4f( 0.001, 0.002, 0.003, 0.004 ) )
		constantD = GafferImage.Constant()
		constantD["color"].setValue( imath.Color4f( 0.0001, 0.0002, 0.0003, 0.0004 ) )

		deepMergeAB = GafferImage.DeepMerge()
		deepMergeAB["in"][0].setInput( constantA["out"] )
		deepMergeAB["in"][1].setInput( constantB["out"] )

		deepMergeCD = GafferImage.DeepMerge()
		deepMergeCD["in"][0].setInput( constantC["out"] )
		deepMergeCD["in"][1].setInput( constantD["out"] )

		switch = Gaffer.Switch()
		switch.setup( GafferImage.ImagePlug( "in", ) )
		switch["in"][0].setInput( deepMergeAB["out"] )
		switch["in"][1].setInput( deepMergeCD["out"] )

		switchExpr = Gaffer.Expression()
		switch.addChild( switchExpr )
		switchExpr.setExpression( 'parent["index"] = context["collect:layerName"] == "CD"' )

		collect = GafferImage.CollectImages()
		collect["in"].setInput( switch["out"] )
		collect["rootLayers"].setValue( IECore.StringVectorData( [ 'AB', 'CD' ] ) )

		o = imath.V2i( 0 )
		self.assertEqual( collect["out"].channelData( "AB.R", o ), deepMergeAB["out"].channelData( "R", o ) )
		self.assertEqual( collect["out"].channelData( "AB.G", o ), deepMergeAB["out"].channelData( "G", o ) )
		self.assertEqual( collect["out"].channelData( "AB.B", o ), deepMergeAB["out"].channelData( "B", o ) )
		self.assertEqual( collect["out"].channelData( "AB.A", o ), deepMergeAB["out"].channelData( "A", o ) )
		self.assertEqual( collect["out"].channelData( "CD.R", o ), deepMergeCD["out"].channelData( "R", o ) )
		self.assertEqual( collect["out"].channelData( "CD.G", o ), deepMergeCD["out"].channelData( "G", o ) )
		self.assertEqual( collect["out"].channelData( "CD.B", o ), deepMergeCD["out"].channelData( "B", o ) )
		self.assertEqual( collect["out"].channelData( "CD.A", o ), deepMergeCD["out"].channelData( "A", o ) )
		self.assertEqual( collect["out"].sampleOffsets( o ), deepMergeAB["out"].sampleOffsets( o ) )
		self.assertEqual( collect["out"].dataWindow(), deepMergeAB["out"].dataWindow() )
		self.assertEqual( collect["out"].deep(), True )
		self.assertEqual( collect["out"].channelNames(), IECore.StringVectorData( [ 'AB.R', 'AB.G', 'AB.B', 'AB.A', 'CD.R', 'CD.G', 'CD.B', 'CD.A' ] ) )

		deepMergeAB["enabled"].setValue( False )
		with self.assertRaisesRegex( Gaffer.ProcessException, r'Input to CollectImages must be consistent, but it is sometimes deep.*' ) as raised:
			collect["out"].deep()

		deepMergeAB["enabled"].setValue( True )

		deepMergeAB["in"][2].setInput( constantB["out"] )

		with self.assertRaisesRegex( Gaffer.ProcessException, r'SampleOffsets on input to CollectImages must match. Pixel 0,0 received both 3 and 2 samples' ) as raised:
			collect["out"].sampleOffsets( o )

		offset = GafferImage.Offset()
		offset["in"].setInput( constantB["out"] )
		offset["offset"].setValue( imath.V2i( -5, -13 ) )

		deepMergeAB["in"][2].setInput( offset["out"] )
		with self.assertRaisesRegex( Gaffer.ProcessException, r'DataWindows on deep input to CollectImages must match. Received both -5,-13 -> 1920,1080 and 0,0 -> 1920,1080' ) as raised:
			collect["out"].dataWindow()

	def testMergeMetadata( self ) :
		imageMetadata = GafferImage.ImageMetadata()
		imageMetadata["expression"] = Gaffer.Expression()
		imageMetadata["expression"].setExpression( inspect.cleandoc(
			"""
			n = int( context.get( "collect:layerName" ) )
			parent["extraMetadata"] = IECore.CompoundData( { str(i) : IECore.IntData( n ) for i in range( n ) } )
			"""
		) )
		collectImages = GafferImage.CollectImages()
		collectImages["in"].setInput( imageMetadata["out"] )
		collectImages["rootLayers"].setValue( IECore.StringVectorData( [ '4', '3', '2', '1' ] ) )
		self.assertEqual(
			collectImages["out"].metadata(),
			IECore.CompoundData( { str(i) : IECore.IntData(4) for i in range( 4 ) } )
		)
		collectImages["mergeMetadata"].setValue( True )
		self.assertEqual(
			collectImages["out"].metadata(),
			IECore.CompoundData( { str(i) : IECore.IntData(i+1) for i in range( 4 ) } )
		)

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testHighLayerCountPerformance( self ) :

		constant = GafferImage.Constant()

		collect = GafferImage.CollectImages()
		collect["in"].setInput( constant["out"] )
		collect["rootLayers"].setValue( IECore.StringVectorData( [ "layer{}".format( i ) for i in range( 0, 1000 ) ] ) )

		with GafferTest.TestRunner.PerformanceScope() :
			GafferImageTest.processTiles( collect["out"] )

if __name__ == "__main__":
	unittest.main()
