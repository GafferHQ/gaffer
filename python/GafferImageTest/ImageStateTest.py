##########################################################################
#
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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
import math
import copy
import sys
import random

import unittest

import IECore

import Gaffer
import GafferTest
import GafferImage

# \todo : Add tests for how ImageState responds when A, Z and/or ZBack
#         channels do not exist on input


class ImageStateTest( GafferTest.TestCase ) :

	longMessage = True

	def testDefaultPlugValues( self ) :

		imageState = GafferImage.ImageState()

		self.assertEqual( imageState["deepState"].defaultValue(), GafferImage.ImagePlug.DeepState.Tidy )

	def __getConstant( self, R, G, B, A, Z, ZBack ) :

		c = GafferImage.Constant()
		c["format"].setValue( GafferImage.Format( IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( 512 ) ), 1 ) )
		c["color"].setValue( IECore.Color4f( R, G, B, A ) )
		c["z"].setValue( Z )
		c["zBack"].setValue( ZBack )

		return c

	def __getMessy( self, values = None, randomValueCount = 5 ) :

		nodes = {}

		if not values:
			values = []
			for i in range( randomValueCount ) :
				v = {}
				for channel in [ "R", "G", "B" ] :
					v[channel] = round( random.uniform( 0.0, 5.0 ), 2 )

				v["A"] = round( random.uniform( 0.0, 1.0 ), 2 )

				for channel in [ "Z", "ZBack" ] :
					v[channel] = round( random.uniform( 0.0, 10.0 ) )

				if random.random() > 0.5 :
					v["ZBack"] = v["Z"]
				else:
					v["ZBack"] = max(v["Z"], v["ZBack"])

				values.append( v )

		nodes['merge'] = GafferImage.DeepMerge()
		nodes['constants'] = []
		nodes['values'] = values

		for i, v in enumerate( values ) :
			c = self.__getConstant( **v )
			nodes['constants'].append( c )
			nodes['merge']['in'][i].setInput( c["out"] )

		self.assertEqual( nodes['merge']["out"]["deepState"].getValue(), GafferImage.ImagePlug.DeepState.Messy )

		return nodes

	def testHashPassThrough( self ) :

		nodes = self.__getMessy()
		messy = nodes['merge']

		tileOrigin = IECore.V2i( 0 )

		st = GafferImage.ImageState()
		st["in"].setInput( messy["out"] )
		st["deepState"].setValue( GafferImage.ImagePlug.DeepState.Sorted )

		for imagePlug in [ "format", "dataWindow", "metadata", "channelNames" ] :
			self.assertEqual( messy["out"][imagePlug].hash(), st["out"][imagePlug].hash() )
		self.assertEqual( messy["out"].sampleOffsetsHash( tileOrigin ), st["out"].sampleOffsetsHash( tileOrigin ) )

		for imagePlug in [ "deepState" ] :
			self.assertNotEqual( messy["out"][imagePlug].hash(), st["out"][imagePlug].hash() )
		self.assertNotEqual( messy["out"].channelDataHash( "R", tileOrigin ), st["out"].channelDataHash( "R", tileOrigin ) )

		st["deepState"].setValue( GafferImage.ImagePlug.DeepState.Tidy )

		for imagePlug in [ "format", "dataWindow", "metadata", "channelNames" ] :
			self.assertEqual( messy["out"][imagePlug].hash(), st["out"][imagePlug].hash() )

		for imagePlug in [ "deepState" ] :
			self.assertNotEqual( messy["out"][imagePlug].hash(), st["out"][imagePlug].hash() )
		self.assertNotEqual( messy["out"].sampleOffsetsHash( tileOrigin ), st["out"].sampleOffsetsHash( tileOrigin ) )
		self.assertNotEqual( messy["out"].channelDataHash( "R", tileOrigin ), st["out"].channelDataHash( "R", tileOrigin ) )

		st["deepState"].setValue( GafferImage.ImagePlug.DeepState.Flat )

		for imagePlug in [ "format", "dataWindow", "metadata", "channelNames" ] :
			self.assertEqual( messy["out"][imagePlug].hash(), st["out"][imagePlug].hash() )

		for imagePlug in [ "deepState" ] :
			self.assertNotEqual( messy["out"][imagePlug].hash(), st["out"][imagePlug].hash() )
		self.assertNotEqual( messy["out"].sampleOffsetsHash( tileOrigin ), st["out"].sampleOffsetsHash( tileOrigin ) )
		self.assertNotEqual( messy["out"].channelDataHash( "R", tileOrigin ), st["out"].channelDataHash( "R", tileOrigin ) )

	def testNoModificationHashPassThrough( self ) :

		nodes = self.__getMessy()
		messy = nodes['merge']

		tileOrigin = IECore.V2i( 0 )

		# This first ImageState node will change the state,
		# and then the second will be set to pass through
		# its input state.
		stMod = GafferImage.ImageState()
		stMod["in"].setInput( messy["out"] )

		stChk = GafferImage.ImageState()
		stChk["in"].setInput( stMod["out"] )

		for imagePlug in [ "format", "dataWindow", "metadata", "channelNames", "deepState" ] :
			self.assertEqual( stMod["out"][imagePlug].hash(), stChk["out"][imagePlug].hash() )
		self.assertEqual( stMod["out"].sampleOffsetsHash( tileOrigin ), stChk["out"].sampleOffsetsHash( tileOrigin ) )
		self.assertEqual( stMod["out"].channelDataHash( "R", tileOrigin ), stChk["out"].channelDataHash( "R", tileOrigin ) )

		for imageState in [ GafferImage.ImagePlug.DeepState.Sorted, GafferImage.ImagePlug.DeepState.Tidy, GafferImage.ImagePlug.DeepState.Flat ] :
			stMod["deepState"].setValue( imageState )
			stChk["deepState"].setValue( imageState )

			for imagePlug in [ "format", "dataWindow", "metadata", "channelNames", "deepState" ] :
				self.assertEqual( stMod["out"][imagePlug].hash(), stChk["out"][imagePlug].hash() )
			self.assertEqual( stMod["out"].sampleOffsetsHash( tileOrigin ), stChk["out"].sampleOffsetsHash( tileOrigin ) )
			self.assertEqual( stMod["out"].channelDataHash( "R", tileOrigin ), stChk["out"].channelDataHash( "R", tileOrigin ) )


	def testFlattenedWrite( self ) :

		c1 = GafferImage.Constant()
		c1['format'].setValue( GafferImage.Format( 512, 512 ) )
		c2 = GafferImage.Constant()
		c2['format'].setValue( GafferImage.Format( 512, 512 ) )

		m = GafferImage.DeepMerge()
		m['in'][0].setInput( c1["out"] )
		m['in'][1].setInput( c2["out"] )

		iState = GafferImage.ImageState()
		iState['in'].setInput( m['out'] )
		iState['deepState'].setValue( GafferImage.ImagePlug.DeepState.Flat )

		testFile = self.temporaryDirectory() + "/test.Flat.exr"
		self.failIf( os.path.exists( testFile ) )

		w = GafferImage.ImageWriter()
		w['in'].setInput( iState["out"] )

		w["fileName"].setValue( testFile )
		with Gaffer.Context() :
			w.execute()


	def testSampleOffsets( self ) :

		for i in range( 100 ) :
			nodes = self.__getMessy()
			messy = nodes['merge']

			ts = GafferImage.ImagePlug.tileSize()
			tileOrigin = IECore.V2i( 0 )

			st = GafferImage.ImageState()
			st["in"].setInput( messy["out"] )

			expectedSortedSampleOffsets = messy["out"].sampleOffsets( tileOrigin )

			numTidySamples = len( self.__getModifiedSamples( nodes['values'], GafferImage.ImagePlug.DeepState.Tidy ) )
			expectedTidySampleOffsets = IECore.IntVectorData( range( numTidySamples, ts * ts * numTidySamples + 1, numTidySamples ) )
			expectedFlatSampleOffsets = IECore.IntVectorData( range( 1, ts * ts + 1 ) )

			self.assertNotEqual( messy["out"].sampleOffsets( tileOrigin ), expectedFlatSampleOffsets )


			st["deepState"].setValue( GafferImage.ImagePlug.DeepState.Sorted )

			self.assertEqual( st["out"]["deepState"].getValue(), GafferImage.ImagePlug.DeepState.Sorted, nodes["values"]  )
			self.assertEqual( st["out"].sampleOffsets( tileOrigin ), expectedSortedSampleOffsets, nodes["values"]  )


			st["deepState"].setValue( GafferImage.ImagePlug.DeepState.Tidy )

			self.assertEqual( st["out"]["deepState"].getValue(), GafferImage.ImagePlug.DeepState.Tidy, nodes["values"]  )
			self.assertEqual( list( st["out"].sampleOffsets( tileOrigin ) ), list( expectedTidySampleOffsets ), nodes["values"] )


			st["deepState"].setValue( GafferImage.ImagePlug.DeepState.Flat )

			self.assertEqual( st["out"]["deepState"].getValue(), GafferImage.ImagePlug.DeepState.Flat, nodes["values"]  )
			self.assertEqual( st["out"].sampleOffsets( tileOrigin ), expectedFlatSampleOffsets, nodes["values"]  )


	def testChannelData( self ) :

		for i in range( 100 ) :
			nodes = self.__getMessy()
			messy = nodes['merge']

			tileOrigin = IECore.V2i( 0 )
			tileSize = GafferImage.ImagePlug.tileSize()

			st = GafferImage.ImageState()
			st["in"].setInput( messy["out"])

			for imageState in [ GafferImage.ImagePlug.DeepState.Sorted, GafferImage.ImagePlug.DeepState.Tidy, GafferImage.ImagePlug.DeepState.Flat ] :
				st["deepState"].setValue( imageState )
				sampleOffsets = st["out"].sampleOffsets( tileOrigin )
				expectedSampleCount = sampleOffsets[-1]

				expectedValues = self.__getModifiedSamples( nodes['values'], imageState )

				for channel in [ "R", "G", "B", "A", "Z", "ZBack" ] :
					expectedChannelValues = [ v[channel] for v in expectedValues ]
					expectedData = IECore.FloatVectorData( expectedChannelValues * tileSize * tileSize )

					channelData = st["out"].channelData( channel, tileOrigin )

					self.assertEqual( len( channelData ), expectedSampleCount, "State : {}, Channel : {}, Values : {}".format( imageState, channel, nodes["values"] ) )
					self.assertSimilarList( channelData, expectedData, 0.00001,  "State : {}, Channel : {}, Values : {}".format( imageState, channel, nodes["values"] ) )


	def assertSimilarList( self, actual, expected, tolerance, msg = None ) :
		self.assertEqual( len( actual ), len( expected ) )
		for i in range( len( actual ) ) :
			self.assertAlmostEqual( actual[i], expected[i], delta = tolerance, msg = msg )


	def __getModifiedSamples( self, values, imageState ) :

		if imageState == GafferImage.ImagePlug.DeepState.Sorted :
			return self.__getSortedSamples( values )
		elif imageState == GafferImage.ImagePlug.DeepState.Tidy :
			return self.__getTidySamples( values )
		elif imageState == GafferImage.ImagePlug.DeepState.Flat :
			return self.__getFlatSamples( values )

	def __getSortedSamples( self, values ) :

		for v in values:
			v["ZBack"] = max( v["Z"], v["ZBack"] )

		return sorted( values, cmp = lambda a, b: cmp( a["Z"], b["Z"] ) or cmp( a["ZBack"], b["ZBack"] ) )


	def __getTidySamples( self, values ) :

		sortedSamples = self.__getSortedSamples( values )

		splits = set()

		for sample in sortedSamples :
			sample["ZBack"] = max( sample["Z"], sample["ZBack"] )
			splits.add( sample["Z"] )
			splits.add( sample["ZBack"] )

		splits = sorted( splits )

		splitSamples = []

		for sample in sortedSamples:
			sample["ZBack"] = max( sample["Z"], sample["ZBack"] )
			if sample["Z"] == sample["ZBack"] :
				splitSamples.append( sample )
			else:
				currentZ = sample["Z"]
				for split in splits:
					if split > sample["Z"] and split < sample["ZBack"] :
						splitSamples.append( self.__splitSample( sample, currentZ, split ) )

						currentZ = split

				splitSamples.append( self.__splitSample( sample, currentZ, sample["ZBack"] ) )

		mergeSamples = {}

		for sample in splitSamples :
			key = ( sample["Z"], sample["ZBack"] )
			if key not in mergeSamples :
				mergeSamples[key] = []
			mergeSamples[key].append( sample )

		tidySamples = []

		for samples in mergeSamples.values() :
			if len( samples ) > 1 :
				tidySamples.append( self.__mergeSamples( samples ) )
			elif samples :
				tidySamples.append( samples[0] )

		return self.__getSortedSamples( tidySamples )


	def __mergeSamples( self, samples ) :

		newSample = copy.deepcopy( samples[0] )

		# If any samples have an alpha of 1.0, then average all samples
		# with this value.
		solidSamples = [ s for s in samples if s["A"] == 1.0 ]
		if solidSamples :
			newSample["A"] = 1.0
			for channel in [ "R", "G", "B" ] :
				newSample[channel] = sum( [ s[channel] for s in solidSamples ] ) / len( solidSamples )
		else :
			samples = samples[1:]

			while samples :

				mergedSample = copy.deepcopy( newSample )

				mergedSample["A"] = newSample["A"] + samples[0]["A"] - ( newSample["A"] * samples[0]["A"] )

				MAX = sys.maxint

				u1 = -math.log1p( -newSample["A"] )
				v1 = ( u1 / newSample["A"] ) if ( u1 < ( newSample["A"] * MAX ) ) else 1.0

				u2 = -math.log1p( -samples[0]["A"] )
				v2 = ( u2 / samples[0]["A"] ) if ( u2 < ( samples[0]["A"] * MAX ) ) else 1.0

				u = u1 + u2;
				w = ( mergedSample["A"] / u ) if ( u > 1.0 or mergedSample["A"] < ( u * MAX ) ) else 1.0

				for channel in [ "R", "G", "B" ] :
					mergedSample[channel] = (newSample[channel] * v1 + samples[0][channel] * v2) * w;

				newSample = mergedSample
				samples = samples[1:]

		return newSample

	def __splitSample( self, sample, newZ, newZBack ) :

		newSample = copy.copy( sample )

		newSample["Z"] = newZ
		newSample["ZBack"] = newZBack

		if sample["A"] != 1.0 :
			x = ( newZBack - newZ ) / ( sample["ZBack"] - sample["Z"] )

			if sample["A"] != 0.0 :
				newSample["A"] = -math.expm1 (x * math.log1p (-sample["A"]));
				for channel in [ "R", "G", "B" ] :
					newSample[channel] *= newSample["A"] / sample["A"]
			else:
				for channel in [ "R", "G", "B", "A" ] :
					newSample[channel] *= x

		return newSample


	def __getFlatSamples( self, values ) :

		result = {'R': 0.0, 'G': 0.0, 'B': 0.0, 'A': 0.0, 'Z': 0.0, 'ZBack': 0.0}

		tidySamples = self.__getTidySamples( values )

		if tidySamples:
			result['Z'] = tidySamples[0]['Z']

		setZBack = False

		for v in tidySamples:
			for channel in [ "R", "G", "B", "A" ] :
				result[channel] = result[channel] + ( v[channel] * ( 1.0 - result['A'] ) )

			if v['A'] == 1.0 and not setZBack :
				result['ZBack'] = v['Z']
				setZBack = True

		if tidySamples and not setZBack :
			result['ZBack'] = tidySamples[-1]['ZBack']

		return [result]


	def testOutputState( self ) :

		nodes = self.__getMessy()
		messy = nodes['merge']

		st = GafferImage.ImageState()
		st["in"].setInput( messy["out"] )

		for imageState in [ GafferImage.ImagePlug.DeepState.Sorted, GafferImage.ImagePlug.DeepState.Tidy, GafferImage.ImagePlug.DeepState.Flat ] :
			st["deepState"].setValue( imageState )
			self.assertEqual( st["out"]["deepState"].getValue(), imageState )

if __name__ == "__main__":
	unittest.main()

