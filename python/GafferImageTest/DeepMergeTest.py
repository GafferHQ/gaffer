##########################################################################
#
#  Copyright (c) 2019, Image Engine Design Inc. All rights reserved.
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

import random
import unittest
import imath

import IECore

import GafferTest
import GafferImage
import GafferImageTest

class DeepMergeTest( GafferImageTest.ImageTestCase ) :

	# Match the current state of GafferImage.Merge, with an expectedFailure
	# because it does not currently actually detect the case where there
	# is one input, and do a hash pass-through
	@unittest.expectedFailure
	def testHashPassThrough( self ) :

		constant1 = GafferImage.Constant()
		constant2 = GafferImage.Constant()

		##########################################
		# Test to see if the input is always passed
		# through if only the first input is connected.
		##########################################

		merge = GafferImage.DeepMerge()

		merge["in"][0].setInput( constant1["out"] )

		for plug in [ "format", "dataWindow", "metadata", "channelNames", "sampleOffsets", "deep" ] :
			self.assertEqual( constant1["out"][plug].hash(), merge["out"][plug].hash() )

		##########################################
		# Test that if we add a second input and disable
		# the node the hash still gets passed through.
		##########################################

		merge["in"][1].setInput( constant2["out"] )
		merge["enabled"].setValue(False)

		for plug in [ "format", "dataWindow", "metadata", "channelNames", "sampleOffsets", "deep" ] :
			self.assertEqual( constant1["out"][plug].hash(), merge["out"][plug].hash() )

	# As with testHashPassThrough, passthroughs for a single input haven't been implemented
	@unittest.expectedFailure
	def testOutputDeep( self ) :

		# Test default deep state when no inputs connected
		merge1 = GafferImage.DeepMerge()
		self.assertEqual( merge1["out"]["deep"].getValue(), merge1["out"]["deep"].defaultValue() )

		# Test that deep state passes through Flat value when one input connected
		constant1 = GafferImage.Constant()
		merge1["in"][0].setInput( constant1["out"] )
		self.assertEqual( merge1["out"]["deep"].getValue(), constant1["out"]["deep"].getValue() )

		# Test that deep state is Deep when two inputs connected
		constant2 = GafferImage.Constant()
		merge1["in"][1].setInput( constant2["out"] )
		self.assertEqual( merge1["out"]["deep"].getValue(), GafferImage.ImagePlug.Deep.Deep )

		# Test that deep state passes through Deep value when one input connected
		merge2 = GafferImage.DeepMerge()
		merge2["in"][0].setInput( merge1["out"] )
		self.assertEqual( merge2["out"]["deep"].getValue(), merge1["out"]["deep"].getValue() )


	def testSampleOffsets( self ) :

		ts = GafferImage.ImagePlug.tileSize()

		constant1 = GafferImage.Constant()
		constant2 = GafferImage.Constant()

		constant1["format"].setValue( GafferImage.Format( imath.Box2i( imath.V2i( 0 ), imath.V2i( 512 ) ), 1 ) )
		constant2["format"].setValue( GafferImage.Format( imath.Box2i( imath.V2i( 0 ), imath.V2i( 512 ) ), 1 ) )

		merge = GafferImage.DeepMerge()
		merge["in"][0].setInput( constant1["out"] )
		merge["in"][1].setInput( constant2["out"] )

		expectedSampleOffsets = IECore.IntVectorData( range(2, ts * ts * 2 + 1, 2) )
		actualSampleOffsets = merge["out"].sampleOffsets( imath.V2i( 0 ) )

		self.assertEqual( actualSampleOffsets, expectedSampleOffsets )


	def testChannelData( self ) :

		ts = GafferImage.ImagePlug.tileSize()

		constant1 = GafferImage.Constant()
		constant1["format"].setValue( GafferImage.Format( imath.Box2i( imath.V2i( 0 ), imath.V2i( 512 ) ), 1 ) )
		constant1["color"].setValue( imath.Color4f( 0.25, 0.5, 1.0, 0.5 ) )

		addDepth1 = GafferImage.FlatToDeep()
		addDepth1["in"].setInput( constant1["out"] )
		addDepth1["depth"].setValue( 10.0 )

		constant2 = GafferImage.Constant()
		constant2["format"].setValue( GafferImage.Format( imath.Box2i( imath.V2i( 0 ), imath.V2i( 512 ) ), 1 ) )
		constant2["color"].setValue( imath.Color4f( 2.0, 3.0, 4.0, 1.0 ) )

		addDepth2 = GafferImage.FlatToDeep()
		addDepth2["in"].setInput( constant2["out"] )
		addDepth2["depth"].setValue( 20.0 )

		merge = GafferImage.DeepMerge()
		merge["in"][0].setInput( addDepth1["out"] )
		merge["in"][1].setInput( addDepth2["out"] )

		expectedChannelData = {}
		expectedChannelData["R"] = IECore.FloatVectorData( [ 0.25, 2.0 ] * ts * ts )
		expectedChannelData["G"] = IECore.FloatVectorData( [ 0.5, 3.0 ] * ts * ts )
		expectedChannelData["B"] = IECore.FloatVectorData( [ 1.0, 4.0 ] * ts * ts )
		expectedChannelData["A"] = IECore.FloatVectorData( [ 0.5, 1.0 ] * ts * ts )
		expectedChannelData["Z"] = IECore.FloatVectorData( [ 10.0, 20.0 ] * ts * ts )

		for channelName in expectedChannelData :
			actualChannelData = merge["out"].channelData( channelName, imath.V2i( 0 ) )
			self.assertEqual( actualChannelData, expectedChannelData[channelName] )

		addDepth1["zBackMode"].setValue( GafferImage.FlatToDeep.ZBackMode.Thickness )
		addDepth1["thickness"].setValue( 2.0 )

		expectedChannelData["ZBack"] = IECore.FloatVectorData( [ 12.0, 20.0 ] * ts * ts )

		for channelName in expectedChannelData :
			actualChannelData = merge["out"].channelData( channelName, imath.V2i( 0 ) )
			self.assertEqual( actualChannelData, expectedChannelData[channelName] )

		addDepth2["zBackMode"].setValue( GafferImage.FlatToDeep.ZBackMode.Thickness )
		addDepth2["thickness"].setValue( 0.1 )

		expectedChannelData["ZBack"] = IECore.FloatVectorData( [ 12.0, 20.1 ] * ts * ts )

		for channelName in expectedChannelData :
			actualChannelData = merge["out"].channelData( channelName, imath.V2i( 0 ) )
			self.assertEqual( actualChannelData, expectedChannelData[channelName] )

	def testDataWindow( self ) :

		sourceFormat = GafferImage.Format( imath.Box2i( imath.V2i( 0 ), imath.V2i( 512 ) ), 1 )

		constant1 = GafferImage.Constant()
		constant1["format"].setValue( sourceFormat )

		constant2 = GafferImage.Constant()
		constant2["format"].setValue( sourceFormat )

		crop1 = GafferImage.Crop()
		crop1["in"].setInput( constant1["out"] )
		crop1["affectDisplayWindow"].setValue( False )

		crop2 = GafferImage.Crop()
		crop2["in"].setInput( constant2["out"] )
		crop2["affectDisplayWindow"].setValue( False )

		merge = GafferImage.DeepMerge()
		merge["in"][0].setInput( crop1["out"] )
		merge["in"][1].setInput( crop2["out"] )

		for i in range( 100 ) :
			crop1Area = imath.Box2i()
			crop1Area.extendBy( imath.V2i( int( random.uniform( 0, sourceFormat.width() ) ), int( random.uniform( 0, sourceFormat.height() ) ) ) )
			crop1Area.extendBy( imath.V2i( int( random.uniform( 0, sourceFormat.width() ) ), int( random.uniform( 0, sourceFormat.height() ) ) ) )
			crop1["area"].setValue( crop1Area )

			crop2Area = imath.Box2i()
			crop2Area.extendBy( imath.V2i( int( random.uniform( 0, sourceFormat.width() ) ), int( random.uniform( 0, sourceFormat.height() ) ) ) )
			crop2Area.extendBy( imath.V2i( int( random.uniform( 0, sourceFormat.width() ) ), int( random.uniform( 0, sourceFormat.height() ) ) ) )
			crop2["area"].setValue( crop2Area )

			expectedDataWindow = crop1Area
			expectedDataWindow.extendBy( crop2Area.min() )
			expectedDataWindow.extendBy( crop2Area.max() )

			self.assertEqual( merge["out"]["dataWindow"].getValue(), expectedDataWindow )

	def testChannelRequest( self ) :

		ts = GafferImage.ImagePlug.tileSize()

		a = GafferImage.Constant()
		a["color"].setValue( imath.Color4f( 0.1, 0.2, 0.3, 0.4 ) )

		addDepthA = GafferImage.FlatToDeep()
		addDepthA["in"].setInput( a["out"] )
		addDepthA["depth"].setValue( 2.0 )
		addDepthA["zBackMode"].setValue( GafferImage.FlatToDeep.ZBackMode.Thickness )
		addDepthA["thickness"].setValue( 1.0 )

		ad = GafferImage.DeleteChannels()
		ad["in"].setInput( addDepthA["out"] )
		ad["mode"].setValue( GafferImage.DeleteChannels.Mode.Delete )
		ad["channels"].setValue( IECore.StringVectorData( [ "G", "Z", "ZBack" ] ) )

		b = GafferImage.Constant()
		b["color"].setValue( imath.Color4f( 0.5, 0.6, 0.7, 0.8 ) )

		addDepthB = GafferImage.FlatToDeep()
		addDepthB["in"].setInput( b["out"] )
		addDepthB["depth"].setValue( 4.0 )
		addDepthB["zBackMode"].setValue( GafferImage.FlatToDeep.ZBackMode.Thickness )
		addDepthB["thickness"].setValue( 1.0 )

		bd = GafferImage.DeleteChannels()
		bd["in"].setInput( addDepthB["out"] )
		bd["mode"].setValue( GafferImage.DeleteChannels.Mode.Delete )
		bd["channels"].setValue( IECore.StringVectorData( [ "R", "A" ] ) )

		merge = GafferImage.DeepMerge()
		merge["in"][0].setInput( ad["out"] )
		merge["in"][1].setInput( bd["out"] )

		ad["enabled"].setValue( False )
		bd["enabled"].setValue( False )

		expectedChannelData = {}
		expectedChannelData["R"] = IECore.FloatVectorData( [ 0.1, 0.5 ] * ts * ts )
		expectedChannelData["G"] = IECore.FloatVectorData( [ 0.2, 0.6 ] * ts * ts )
		expectedChannelData["B"] = IECore.FloatVectorData( [ 0.3, 0.7 ] * ts * ts )
		expectedChannelData["A"] = IECore.FloatVectorData( [ 0.4, 0.8 ] * ts * ts )
		expectedChannelData["Z"] = IECore.FloatVectorData( [ 2.0, 4.0 ] * ts * ts )
		expectedChannelData["ZBack"] = IECore.FloatVectorData( [ 3.0, 5.0 ] * ts * ts )

		for channelName in expectedChannelData :
			actualChannelData = merge["out"].channelData( channelName, imath.V2i( 0 ) )
			self.assertEqual( actualChannelData, expectedChannelData[channelName] )

		ad["enabled"].setValue( True )
		bd["enabled"].setValue( True )

		expectedChannelData = {}
		expectedChannelData["R"] = IECore.FloatVectorData( [ 0.1, 0.0 ] * ts * ts )
		expectedChannelData["G"] = IECore.FloatVectorData( [ 0.0, 0.6 ] * ts * ts )
		expectedChannelData["B"] = IECore.FloatVectorData( [ 0.3, 0.7 ] * ts * ts )
		expectedChannelData["A"] = IECore.FloatVectorData( [ 0.4, 0.0 ] * ts * ts )
		expectedChannelData["Z"] = IECore.FloatVectorData( [ 0.0, 4.0 ] * ts * ts )
		expectedChannelData["ZBack"] = IECore.FloatVectorData( [ 0.0, 5.0 ] * ts * ts )

		for channelName in expectedChannelData :
			actualChannelData = merge["out"].channelData( channelName, imath.V2i( 0 ) )
			self.assertEqual( actualChannelData, expectedChannelData[channelName] )


	def testMergedDifferentDataWindows( self ) :
		self.__testMergedDifferentDataWindows()

	def testMergedOverlappingDataWindows( self ) :
		self.__testMergedDifferentDataWindows( True )

	def __testMergedDifferentDataWindows( self, ensureOverlap = False ) :

		ts = GafferImage.ImagePlug.tileSize()
		tileCount = 2

		values1 = { "R": 0.25, "G": 0.5, "B": 1.0, "A": 0.5, "Z": 10.0, "ZBack": 12.0 }
		values2 = { "R": 2.0, "G": 3.0, "B": 4.0, "A": 1.0, "Z": 20.0, "ZBack": 20.0 }

		sourceFormat = GafferImage.Format( imath.Box2i( imath.V2i( 0 ), imath.V2i( ts * tileCount ) ), 1 )

		constant1 = GafferImage.Constant()
		constant1["format"].setValue( sourceFormat )
		constant1["color"].setValue( imath.Color4f( values1["R"], values1["G"], values1["B"], values1["A"] ) )

		addDepth1 = GafferImage.FlatToDeep()
		addDepth1["in"].setInput( constant1["out"] )
		addDepth1["depth"].setValue( values1["Z"] )
		addDepth1["zBackMode"].setValue( GafferImage.FlatToDeep.ZBackMode.Thickness )
		addDepth1["thickness"].setValue( values1["ZBack"] - values1["Z"] )

		constant2 = GafferImage.Constant()
		constant2["format"].setValue( sourceFormat )
		constant2["color"].setValue( imath.Color4f( values2["R"], values2["G"], values2["B"], values2["A"] ) )

		addDepth2 = GafferImage.FlatToDeep()
		addDepth2["in"].setInput( constant2["out"] )
		addDepth2["depth"].setValue( values2["Z"] )
		addDepth2["zBackMode"].setValue( GafferImage.FlatToDeep.ZBackMode.Thickness )
		addDepth2["thickness"].setValue( values2["ZBack"] - values2["Z"] )

		crop1 = GafferImage.Crop()
		crop1["in"].setInput( addDepth1["out"] )
		crop1["affectDisplayWindow"].setValue( False )

		crop2 = GafferImage.Crop()
		crop2["in"].setInput( addDepth2["out"] )
		crop2["affectDisplayWindow"].setValue( False )

		merge = GafferImage.DeepMerge()
		merge["in"][0].setInput( crop1["out"] )
		merge["in"][1].setInput( crop2["out"] )

		for i in range( 10 ) :
			crop1Area = imath.Box2i()
			crop1Area.extendBy( imath.V2i( int( random.uniform( 0, sourceFormat.width() ) ), int( random.uniform( 0, sourceFormat.height() ) ) ) )
			crop1Area.extendBy( imath.V2i( int( random.uniform( 0, sourceFormat.width() ) ), int( random.uniform( 0, sourceFormat.height() ) ) ) )

			crop2Area = imath.Box2i()
			crop2Area.extendBy( imath.V2i( int( random.uniform( 0, sourceFormat.width() ) ), int( random.uniform( 0, sourceFormat.height() ) ) ) )
			crop2Area.extendBy( imath.V2i( int( random.uniform( 0, sourceFormat.width() ) ), int( random.uniform( 0, sourceFormat.height() ) ) ) )

			# If we want to ensure that the two crop areas overlap, extend the second one to a random point
			# within the first one's area
			if ensureOverlap and not GafferImage.intersects( crop1Area, crop2Area ):
				crop2Area.extendBy( imath.V2i( int( random.uniform( crop1Area.min().x, crop1Area.max().x ) ), int( random.uniform( crop1Area.min().y, crop1Area.max().y ) ) ) )

			crop1["area"].setValue( crop1Area )
			crop2["area"].setValue( crop2Area )

			for tileX in range( tileCount ) :
				for tileY in range( tileCount ) :
					tileOrigin = imath.V2i( tileX * ts, tileY * ts )

					sampleOffsets = merge["out"].sampleOffsets( tileOrigin )

					self.assertEqual( sampleOffsets, self.__getExpectedSampleOffsets( tileOrigin, crop1Area, crop2Area ) )

					for channelName in values1.keys() :
						channelData = merge["out"].channelData( channelName, tileOrigin )

						self.assertEqual( channelData, self.__getExpectedChannelData( tileOrigin, crop1Area, values1[channelName], crop2Area, values2[channelName] ) )

	def __getExpectedChannelData( self, tileOrigin, area1, area1Value, area2, area2Value ) :

		ts = GafferImage.ImagePlug.tileSize()

		data = []

		for y in range( tileOrigin.y, tileOrigin.y + ts ) :
			for x in range( tileOrigin.x, tileOrigin.x + ts ) :
				pixel = imath.V2i( x, y )
				if GafferImage.contains( area1, pixel ) :
					data.append( area1Value )
				if GafferImage.contains( area2, pixel ) :
					data.append( area2Value )

		return IECore.FloatVectorData( data )

	def __getExpectedSampleOffsets( self, tileOrigin, area1, area2 ) :

		ts = GafferImage.ImagePlug.tileSize()

		data = []

		for y in range( tileOrigin.y, tileOrigin.y + ts ) :
			for x in range( tileOrigin.x, tileOrigin.x + ts ) :
				pixel = imath.V2i( x, y )
				data.append( data[-1] if data else 0 )
				if GafferImage.contains( area1, pixel ) :
					data[-1] += 1
				if GafferImage.contains( area2, pixel ) :
					data[-1] += 1

		return IECore.IntVectorData( data )


if __name__ == "__main__":
	unittest.main()
