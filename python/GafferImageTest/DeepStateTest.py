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

import os
import math
import copy
import sys
import random

import unittest
import imath

import IECore

import Gaffer
import GafferTest
import GafferImage
import GafferImageTest

# \todo : Add tests for how DeepState responds when A, Z and/or ZBack
#         channels do not exist on input


class DeepStateTest( GafferImageTest.ImageTestCase ) :

	representativeImagePath = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/representativeDeepImage.exr" )
	mergeReferencePath = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/deepMergeReference.exr" )


	longMessage = True

	def testDefaultPlugValues( self ) :

		deepState = GafferImage.DeepState()

		self.assertEqual( deepState["deepState"].defaultValue(), GafferImage.DeepState.TargetState.Tidy )

	@staticmethod
	def __createDepthGrade():
		# \todo - this is simple and generally useful node
		# Get John's permission to make it available to our users
		depthGrade = GafferImage.ImageProcessor( "DepthGrade" )
		depthGrade.addChild( GafferImage.Grade("Grade") )
		Gaffer.PlugAlgo.promote( depthGrade["Grade"]["multiply"]["r"] ).setName( "depthMultiply" )
		Gaffer.PlugAlgo.promote( depthGrade["Grade"]["offset"]["r"] ).setName( "depthOffset" )

		depthGrade["Grade"]["in"].setInput( depthGrade["in"] )
		depthGrade["Grade"]["enabled"].setInput( depthGrade["enabled"] )
		depthGrade["out"].setInput( depthGrade["Grade"]["out"] )
		depthGrade["Grade"]["channels"].setValue( 'Z ZBack' )
		depthGrade["Grade"]["blackClamp"].setValue( False )
		return depthGrade

	def __assertDeepStateProcessing( self, deepPlug, flatReferencePlug, refMaxTolerance, refAverageTolerance, expectedMaxPruning, expectedAveragePruning ) :

		# When testing on complex data, we can test that we are close to our reference

		# We can also check that the different sequences of computation supported by DeepState
		# all give identical results.  There are different code paths through the node depending on
		# the input and output state, and by switching between flattening in one step, vs sorting
		# or tidying before flattening, we can test all these paths.
		oneStepFlatten = GafferImage.DeepState()
		oneStepFlatten["in"].setInput( deepPlug )
		oneStepFlatten["deepState"].setValue( GafferImage.DeepState.TargetState.Flat )

		twoStepASort = GafferImage.DeepState()
		twoStepASort["in"].setInput( deepPlug )
		twoStepASort["deepState"].setValue( GafferImage.DeepState.TargetState.Sorted )
		twoStepAFlatten = GafferImage.DeepState( "TwoStepAFlatten" )
		twoStepAFlatten["in"].setInput( twoStepASort["out"] )
		twoStepAFlatten["deepState"].setValue( GafferImage.DeepState.TargetState.Flat )

		twoStepBTidy = GafferImage.DeepState()
		twoStepBTidy["in"].setInput( deepPlug )
		twoStepBTidy["deepState"].setValue( GafferImage.DeepState.TargetState.Tidy )
		twoStepBFlatten = GafferImage.DeepState( "TwoStepBFlatten" )
		twoStepBFlatten["in"].setInput( twoStepBTidy["out"] )
		twoStepBFlatten["deepState"].setValue( GafferImage.DeepState.TargetState.Flat )

		threeStepSort = GafferImage.DeepState()
		threeStepSort["in"].setInput( deepPlug )
		threeStepSort["deepState"].setValue( GafferImage.DeepState.TargetState.Sorted )
		threeStepTidy = GafferImage.DeepState()
		threeStepTidy["in"].setInput( threeStepSort["out"] )
		threeStepTidy["deepState"].setValue( GafferImage.DeepState.TargetState.Tidy )
		threeStepFlatten = GafferImage.DeepState( "ThreeStepFlatten")
		threeStepFlatten["in"].setInput( threeStepTidy["out"] )
		threeStepFlatten["deepState"].setValue( GafferImage.DeepState.TargetState.Flat )

		pruneOne = GafferImage.DeepState()
		pruneOne["in"].setInput( deepPlug )
		pruneOne["deepState"].setValue( GafferImage.DeepState.TargetState.Tidy )
		pruneOne["pruneOccluded"].setValue( True )
		pruneOne["occludedThreshold"].setValue( 1.0 )
		pruneOneFlatten = GafferImage.DeepState( "PruneOneFlatten" )
		pruneOneFlatten["in"].setInput( pruneOne["out"] )
		pruneOneFlatten["deepState"].setValue( GafferImage.DeepState.TargetState.Flat )

		prunePointNine = GafferImage.DeepState()
		prunePointNine["in"].setInput( deepPlug )
		prunePointNine["deepState"].setValue( GafferImage.DeepState.TargetState.Tidy )
		prunePointNine["pruneOccluded"].setValue( True )
		prunePointNine["occludedThreshold"].setValue( 0.9 )
		prunePointNineFlatten = GafferImage.DeepState( "PrunePointNineFlatten" )
		prunePointNineFlatten["in"].setInput( prunePointNine["out"] )
		prunePointNineFlatten["deepState"].setValue( GafferImage.DeepState.TargetState.Flat )

		diff = GafferImage.Merge()
		diff['operation'].setValue( GafferImage.Merge.Operation.Difference )
		diff['in'][0].setInput( oneStepFlatten["out"] )
		diff['in'][1].setInput( flatReferencePlug )

		stats = GafferImage.ImageStats()
		stats["in"].setInput( diff["out"] )
		stats["area"].setValue( diff["out"].dataWindow() )

		m = stats["max"].getValue()
		a = stats["average"].getValue()
		for i in range( 4 ):
			self.assertLessEqual( m[i], refMaxTolerance[i], "%s Channel : Max deviation from reference too high" % "RGBA"[i] )
			self.assertLessEqual( a[i], refAverageTolerance[i], "%s Channel : Average deviation from reference too high" % "RGBA"[i] )

		for method in [ twoStepAFlatten, twoStepBFlatten, threeStepFlatten, pruneOneFlatten, prunePointNineFlatten ]:
			diff["in"][1].setInput( method["out"] )
			if method in [ pruneOneFlatten, prunePointNineFlatten ]:
				# Pruning does require merging alpha at the back before alpha at the front, so floating point
				# imprecision in alpha is introduced
				self.assertLess( stats["max"].getValue(), imath.Color4f( 0.000006, 0.000007, 0.000006, 0.000001 ), "Compute method %s does not match single stage flatten" % method.getName() )
			else:
				# Without pruning, the alpha is processed identically
				self.assertLess( stats["max"].getValue(), imath.Color4f( 0.000007, 0.000007, 0.000007, 0.0000006 ), "Compute method %s does not match single stage flatten" % method.getName() )

		tidyCounts = GafferImage.DeepSampleCounts()
		tidyCounts["in"].setInput( twoStepBTidy["out"] )

		pruneOneCounts = GafferImage.DeepSampleCounts()
		pruneOneCounts["in"].setInput( pruneOne["out"] )

		pruneOneDiff = GafferImage.Merge()
		pruneOneDiff["operation"].setValue( GafferImage.Merge.Operation.Subtract )
		pruneOneDiff["in"][0].setInput( tidyCounts["out"] )
		pruneOneDiff["in"][1].setInput( pruneOneCounts["out"] )

		pruneOneStats = GafferImage.ImageStats()
		pruneOneStats["in"].setInput( pruneOneDiff["out"] )
		pruneOneStats["area"].setValue( diff["out"].dataWindow() )

		prunePointNineCounts = GafferImage.DeepSampleCounts()
		prunePointNineCounts["in"].setInput( prunePointNine["out"] )

		prunePointNineDiff = GafferImage.Merge()
		prunePointNineDiff["operation"].setValue( GafferImage.Merge.Operation.Subtract )
		prunePointNineDiff["in"][0].setInput( tidyCounts["out"] )
		prunePointNineDiff["in"][1].setInput( prunePointNineCounts["out"] )

		prunePointNineStats = GafferImage.ImageStats()
		prunePointNineStats["in"].setInput( prunePointNineDiff["out"] )
		prunePointNineStats["area"].setValue( diff["out"].dataWindow() )

		# All of tests contain some pixels where no samples can be pruned
		# ( But the number of samples should definitely never increase )
		self.assertEqual( pruneOneStats["max"].getValue()[0], 0 )
		self.assertEqual( prunePointNineStats["max"].getValue()[0], 0 )

		# These are rough heuristics, but make sure we are pruning something, and that the .9 threshold
		# prunes more.
		self.assertLessEqual( pruneOneStats["min"].getValue()[0], -expectedMaxPruning )
		self.assertLessEqual( prunePointNineStats["min"].getValue()[0], -expectedMaxPruning )
		self.assertLessEqual( pruneOneStats["average"].getValue()[0], -expectedAveragePruning )
		self.assertLessEqual( prunePointNineStats["average"].getValue()[0], pruneOneStats["average"].getValue()[0] * 2 )


		# Assert that we can repeat an operation on data where it has already been applied, and nothing happens
		resort = GafferImage.DeepState()
		resort["in"].setInput( threeStepSort["out"] )
		resort["deepState"].setValue( GafferImage.DeepState.TargetState.Sorted )
		self.assertImagesEqual( resort["out"], threeStepSort["out"] )

		reprunePointNine = GafferImage.DeepState()
		reprunePointNine["in"].setInput( prunePointNine["out"] )
		reprunePointNine["deepState"].setValue( GafferImage.DeepState.TargetState.Tidy )
		reprunePointNine["pruneOccluded"].setValue( True )
		reprunePointNine["occludedThreshold"].setValue( 0.9 )
		self.assertImagesEqual( reprunePointNine["out"], prunePointNine["out"] )

		reflatten = GafferImage.DeepState()
		reflatten["in"].setInput( oneStepFlatten["out"] )
		reflatten["deepState"].setValue( GafferImage.DeepState.TargetState.Flat )
		self.assertImagesEqual( reflatten["out"], oneStepFlatten["out"] )


	def __getConstant( self, R, G, B, A, Z, ZBack, dim = imath.V2i( 512 ) ) :

		c = GafferImage.Constant()
		c["format"].setValue( GafferImage.Format( imath.Box2i( imath.V2i( 0 ), dim ), 1 ) )
		c["color"].setValue( imath.Color4f( R, G, B, A ) )

		d = GafferImage.FlatToDeep()
		d["in"].setInput( c["out"] )
		d["depth"].setValue( Z )
		d["zBackMode"].setValue( GafferImage.FlatToDeep.ZBackMode.Thickness )
		d["thickness"].setValue( ZBack - Z )

		return (c,d)

	def __getMessy( self, values = None, randomValueCount = 5, forceOverlap = False ) :

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

			if forceOverlap:
				# All samples will overlap 100% - exercise the merge code
				v["Z"] = 1
				v["ZBack"] = 2

			values.append( v )

		nodes['merge'] = GafferImage.DeepMerge()
		nodes['constants'] = []
		nodes['values'] = values

		for i, v in enumerate( values ) :
			c,d = self.__getConstant( **v )
			nodes['constants'].append( c )
			nodes['constants'].append( d )
			nodes['merge']['in'][i].setInput( d["out"] )

		self.assertEqual( nodes['merge']["out"]["deep"].getValue(), True )

		return nodes

	def testHashPassThrough( self ) :

		nodes = self.__getMessy()
		messy = nodes['merge']

		tileOrigin = imath.V2i( 0 )

		st = GafferImage.DeepState()
		st["in"].setInput( messy["out"] )
		st["deepState"].setValue( GafferImage.DeepState.TargetState.Sorted )

		for imagePlug in [ "format", "dataWindow", "metadata", "channelNames", "deep" ] :
			self.assertEqual( messy["out"][imagePlug].hash(), st["out"][imagePlug].hash() )
		self.assertEqual( messy["out"].sampleOffsetsHash( tileOrigin ), st["out"].sampleOffsetsHash( tileOrigin ) )

		self.assertNotEqual( messy["out"].channelDataHash( "R", tileOrigin ), st["out"].channelDataHash( "R", tileOrigin ) )

		st["deepState"].setValue( GafferImage.DeepState.TargetState.Tidy )

		for imagePlug in [ "format", "dataWindow", "metadata", "channelNames", "deep" ] :
			self.assertEqual( messy["out"][imagePlug].hash(), st["out"][imagePlug].hash() )

		self.assertNotEqual( messy["out"].sampleOffsetsHash( tileOrigin ), st["out"].sampleOffsetsHash( tileOrigin ) )
		self.assertNotEqual( messy["out"].channelDataHash( "R", tileOrigin ), st["out"].channelDataHash( "R", tileOrigin ) )

		st["deepState"].setValue( GafferImage.DeepState.TargetState.Flat )

		for imagePlug in [ "format", "dataWindow", "metadata", "channelNames" ] :
			self.assertEqual( messy["out"][imagePlug].hash(), st["out"][imagePlug].hash() )

		for imagePlug in [ "deep" ] :
			self.assertNotEqual( messy["out"][imagePlug].hash(), st["out"][imagePlug].hash() )
		self.assertNotEqual( messy["out"].sampleOffsetsHash( tileOrigin ), st["out"].sampleOffsetsHash( tileOrigin ) )
		self.assertNotEqual( messy["out"].channelDataHash( "R", tileOrigin ), st["out"].channelDataHash( "R", tileOrigin ) )

	def testNoModificationHashPassThrough( self ) :

		nodes = self.__getMessy()
		messy = nodes['merge']

		tileOrigin = imath.V2i( 0 )

		# This first DeepState node will change the state,
		# and then the second will be set to pass through
		# its input state.
		stMod = GafferImage.DeepState()
		stMod["in"].setInput( messy["out"] )

		stChk = GafferImage.DeepState()
		stChk["in"].setInput( stMod["out"] )

		stMod["deepState"].setValue( GafferImage.DeepState.TargetState.Flat )
		stChk["deepState"].setValue( GafferImage.DeepState.TargetState.Flat )

		for imagePlug in [ "format", "dataWindow", "metadata", "channelNames", "deep" ] :
			self.assertEqual( stMod["out"][imagePlug].hash(), stChk["out"][imagePlug].hash() )
		self.assertEqual( stMod["out"].channelDataHash( "R", tileOrigin ), stChk["out"].channelDataHash( "R", tileOrigin ) )

	def testFlattenedWrite( self ) :

		c1 = GafferImage.Constant()
		c1['format'].setValue( GafferImage.Format( 512, 512 ) )
		c2 = GafferImage.Constant()
		c2['format'].setValue( GafferImage.Format( 512, 512 ) )

		m = GafferImage.DeepMerge()
		m['in'][0].setInput( c1["out"] )
		m['in'][1].setInput( c2["out"] )

		iState = GafferImage.DeepState()
		iState['in'].setInput( m['out'] )
		iState['deepState'].setValue( GafferImage.DeepState.TargetState.Flat )

		testFile = self.temporaryDirectory() + "/test.Flat.exr"
		self.assertFalse( os.path.exists( testFile ) )

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
			tileOrigin = imath.V2i( 0 )

			st = GafferImage.DeepState()
			st["in"].setInput( messy["out"] )

			expectedSortedSampleOffsets = messy["out"].sampleOffsets( tileOrigin )

			numTidySamples = len( self.__getModifiedSamples( nodes['values'], GafferImage.DeepState.TargetState.Tidy ) )
			expectedTidySampleOffsets = IECore.IntVectorData( range( numTidySamples, ts * ts * numTidySamples + 1, numTidySamples ) )
			expectedFlatSampleOffsets = IECore.IntVectorData( range( 1, ts * ts + 1 ) )

			self.assertNotEqual( messy["out"].sampleOffsets( tileOrigin ), expectedFlatSampleOffsets )


			st["deepState"].setValue( GafferImage.DeepState.TargetState.Sorted )

			self.assertEqual( st["out"]["deep"].getValue(), True, nodes["values"]  )
			self.assertEqual( st["out"].sampleOffsets( tileOrigin ), expectedSortedSampleOffsets, " with parameter values %s" % nodes["values"]  )


			st["deepState"].setValue( GafferImage.DeepState.TargetState.Tidy )

			self.assertEqual( st["out"]["deep"].getValue(), True, nodes["values"]  )
			self.assertEqual( st["out"].sampleOffsets( tileOrigin ), expectedTidySampleOffsets, " with parameter values %s" % nodes["values"] )

			st["deepState"].setValue( GafferImage.DeepState.TargetState.Flat )
			self.assertEqual( st["out"]["deep"].getValue(), False, nodes["values"]  )


	def testChannelData( self ) :

		for i in range( 100 ) :
			if i < 75:
				nodes = self.__getMessy( forceOverlap = i > 70 )
			else:
				# For the last 25 tests, add a massive overlapping pure emissive sample
				# ( A = 0 hits a special code path )
				nodes = self.__getMessy( [ { "R" : 1, "G" : 2, "B" : 3, "A" : 0, "Z" : 1, "ZBack" : 5 } ])
			messy = nodes['merge']

			tileOrigin = imath.V2i( 0 )
			tileSize = GafferImage.ImagePlug.tileSize()

			st = GafferImage.DeepState()
			st["in"].setInput( messy["out"])

			for deepState in [ GafferImage.DeepState.TargetState.Sorted, GafferImage.DeepState.TargetState.Tidy, GafferImage.DeepState.TargetState.Flat ] :
				st["deepState"].setValue( deepState )
				if deepState == GafferImage.DeepState.TargetState.Flat:
					expectedSampleCount = GafferImage.ImagePlug.tileSize() * GafferImage.ImagePlug.tileSize()
				else:
					sampleOffsets = st["out"].sampleOffsets( tileOrigin )
					expectedSampleCount = sampleOffsets[-1]

				expectedValues = self.__getModifiedSamples( nodes['values'], deepState )

				for channel in [ "R", "G", "B", "A", "Z", "ZBack" ] :
					expectedChannelValues = [ v[channel] for v in expectedValues ]
					expectedData = IECore.FloatVectorData( expectedChannelValues * tileSize * tileSize )

					channelData = st["out"].channelData( channel, tileOrigin )

					self.assertEqual( len( channelData ), expectedSampleCount, "State : {}, Channel : {}, Values : {}".format( deepState, channel, nodes["values"] ) )
					self.assertSimilarList( channelData, expectedData, 0.00001,  "State : {}, Channel : {}, Values : {}".format( deepState, channel, nodes["values"] ) )

	def assertSimilarList( self, actual, expected, tolerance, msg = None ) :
		self.assertEqual( len( actual ), len( expected ) )
		for i in range( len( actual ) ) :
			self.assertAlmostEqual( actual[i], expected[i], delta = tolerance, msg = msg )


	def __getModifiedSamples( self, values, deepState ) :

		if deepState == GafferImage.DeepState.TargetState.Sorted :
			return self.__getSortedSamples( values )
		elif deepState == GafferImage.DeepState.TargetState.Tidy :
			return self.__getTidySamples( values )
		elif deepState == GafferImage.DeepState.TargetState.Flat :
			return self.__getFlatSamples( values )

	def __getSortedSamples( self, values ) :

		for v in values:
			v["ZBack"] = max( v["Z"], v["ZBack"] )

		return sorted( values, key = lambda v : ( v["Z"], v["ZBack"] ) )


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

				MAX = sys.maxsize

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

		#if tidySamples:
			#result['Z'] = tidySamples[0]['Z']

		for v in tidySamples:

			for channel in [ "R", "G", "B", "A" ] :
				vc = v[channel]
				result[channel] = result[channel] + ( vc * ( 1.0 - result['A'] ) )

		if tidySamples :
			result['ZBack'] = tidySamples[-1]['ZBack']
			result['Z'] = tidySamples[0]['Z']

		return [result]


	def testOutputState( self ) :

		nodes = self.__getMessy()
		messy = nodes['merge']

		st = GafferImage.DeepState()
		st["in"].setInput( messy["out"] )

		for deepState in [ GafferImage.DeepState.TargetState.Sorted, GafferImage.DeepState.TargetState.Tidy, GafferImage.DeepState.TargetState.Flat ] :
			st["deepState"].setValue( deepState )
			self.assertEqual( st["out"]["deep"].getValue(), deepState != GafferImage.DeepState.TargetState.Flat )

	def testPruneTransparent( self ) :

		np = GafferImage.ImagePlug.tilePixels()

		messy = self.__getMessy( [
			{ "R":0.25, "G":0.5, "B":1.0, "A":0.5, "Z":10, "ZBack":12 },
			{ "R":2.0, "G":3.0, "B":4.0, "A":1.0, "Z":20, "ZBack":0 },
			{ "R":0.0, "G":0.5, "B":0.1, "A":0.0, "Z":30, "ZBack":0 },
		], 0 )

		deepState = GafferImage.DeepState()
		deepState["in"].setInput( messy["merge"]["out"] )

		expectedChannelData = {}
		expectedChannelData["R"] = IECore.FloatVectorData( [ 0.25, 2.0, 0.0 ] * np )
		expectedChannelData["G"] = IECore.FloatVectorData( [ 0.5, 3.0, 0.5 ] * np )
		expectedChannelData["B"] = IECore.FloatVectorData( [ 1.0, 4.0, 0.1 ] * np )
		expectedChannelData["A"] = IECore.FloatVectorData( [ 0.5, 1.0, 0.0 ] * np )
		expectedChannelData["Z"] = IECore.FloatVectorData( [ 10.0, 20.0, 30.0 ] * np )
		expectedChannelData["ZBack"] = IECore.FloatVectorData( [ 12.0, 20.0, 30.0 ] * np )

		expectedSampleOffsets = IECore.IntVectorData( range( 3, np * 3 + 1, 3 ) )

		self.assertEqual( deepState["out"].sampleOffsets( imath.V2i( 0 ) ), expectedSampleOffsets )

		for channelName in expectedChannelData :
			actualChannelData = deepState["out"].channelData( channelName, imath.V2i( 0 ) )
			self.assertEqual( actualChannelData, expectedChannelData[channelName] )

		deepState["pruneTransparent"].setValue( True )

		expectedChannelData = {}
		expectedChannelData["R"] = IECore.FloatVectorData( [ 0.25, 2.0 ] * np )
		expectedChannelData["G"] = IECore.FloatVectorData( [ 0.5, 3.0 ] * np )
		expectedChannelData["B"] = IECore.FloatVectorData( [ 1.0, 4.0 ] * np )
		expectedChannelData["A"] = IECore.FloatVectorData( [ 0.5, 1.0 ] * np )
		expectedChannelData["Z"] = IECore.FloatVectorData( [ 10.0, 20.0 ] * np )
		expectedChannelData["ZBack"] = IECore.FloatVectorData( [ 12.0, 20.0 ] * np )

		expectedSampleOffsets = IECore.IntVectorData( range( 2, np * 2 + 1, 2 ) )
		self.assertEqual( deepState["out"].sampleOffsets( imath.V2i( 0 ) ), expectedSampleOffsets )

		for channelName in expectedChannelData :
			actualChannelData = deepState["out"].channelData( channelName, imath.V2i( 0 ) )
			self.assertEqual( actualChannelData, expectedChannelData[channelName] )

	def testPruneOccluded( self ) :

		np = GafferImage.ImagePlug.tilePixels()

		messy = self.__getMessy( [
			{ "R":0.25, "G":0.5, "B":1.0, "A":0.9, "Z":10, "ZBack":12 },
			{ "R":2.0, "G":3.0, "B":4.0, "A":1.0, "Z":20, "ZBack":0 },
			{ "R":0.0, "G":0.5, "B":0.1, "A":0.5, "Z":30, "ZBack":0 },
		], 0 )

		deepState = GafferImage.DeepState()
		deepState["in"].setInput( messy["merge"]["out"] )

		expectedSampleOffsets = IECore.IntVectorData( range( 3, np * 3 + 1, 3 ) )

		self.assertEqual( deepState["out"].sampleOffsets( imath.V2i( 0 ) ), expectedSampleOffsets )

		deepState["pruneOccluded"].setValue( True )

		expectedChannelData = {}
		expectedChannelData["R"] = IECore.FloatVectorData( [ 0.25, 2.0 ] * np )
		expectedChannelData["G"] = IECore.FloatVectorData( [ 0.5, 3.0 ] * np )
		expectedChannelData["B"] = IECore.FloatVectorData( [ 1.0, 4.0 ] * np )
		expectedChannelData["A"] = IECore.FloatVectorData( [ 0.9, 1.0 ] * np )
		expectedChannelData["Z"] = IECore.FloatVectorData( [ 10.0, 20.0 ] * np )
		expectedChannelData["ZBack"] = IECore.FloatVectorData( [ 12.0, 20.0 ] * np )

		expectedSampleOffsets = IECore.IntVectorData( range( 2, np * 2 + 1, 2 ) )
		self.assertEqual( deepState["out"].sampleOffsets( imath.V2i( 0 ) ), expectedSampleOffsets )

		for channelName in expectedChannelData :
			actualChannelData = deepState["out"].channelData( channelName, imath.V2i( 0 ) )
			self.assertEqual( actualChannelData, expectedChannelData[channelName] )

		deepState["occludedThreshold"].setValue( 0.9 )

		expectedChannelData = {}
		expectedChannelData["R"] = IECore.FloatVectorData( [ 0.25 + 2.0 * 0.1 ] * np )
		expectedChannelData["G"] = IECore.FloatVectorData( [ 0.5 + 3.0 * 0.1 ] * np )
		expectedChannelData["B"] = IECore.FloatVectorData( [ 1.0 + 4.0 * 0.1 ] * np )
		expectedChannelData["A"] = IECore.FloatVectorData( [ 1.0 ] * np )
		expectedChannelData["Z"] = IECore.FloatVectorData( [ 10.0 ] * np )
		expectedChannelData["ZBack"] = IECore.FloatVectorData( [ 12.0 ] * np )

		expectedSampleOffsets = IECore.IntVectorData( range( 1, np * 1 + 1, 1 ) )
		self.assertEqual( deepState["out"].sampleOffsets( imath.V2i( 0 ) ), expectedSampleOffsets )

		for channelName in expectedChannelData :
			actualChannelData = deepState["out"].channelData( channelName, imath.V2i( 0 ) )
			self.assertEqual( len( actualChannelData ), len( expectedChannelData[channelName] ) )
			for i in range( len( actualChannelData ) ):
				self.assertAlmostEqual( actualChannelData[i], expectedChannelData[channelName][i], places = 6 )

	def testOccludeAll( self ) :
		representativeImage = GafferImage.ImageReader()
		representativeImage["fileName"].setValue( self.representativeImagePath )

		constantNodes = self.__getConstant( 0.1, 0.2, 0.3, 1, -10, -10, imath.V2i( 150, 100 ) )

		empty = GafferImage.Empty()
		empty["format"].setValue( GafferImage.Format( imath.Box2i( imath.V2i( 0 ), imath.V2i( 150, 100 ) ), 1 ) )

		deepConstant = GafferImage.DeepMerge()
		deepConstant["in"][0].setInput( constantNodes[1]["out"] )
		deepConstant["in"][1].setInput( empty["out"] )

		deepMerge = GafferImage.DeepMerge()
		deepMerge["in"][0].setInput( representativeImage["out"] )
		deepMerge["in"][1].setInput( deepConstant["out"] )

		deepState = GafferImage.DeepState()
		deepState["in"].setInput( deepMerge["out"] )
		deepState["pruneOccluded"].setValue( True )

		self.assertEqual( GafferImage.ImageAlgo.tiles( constantNodes[1]["out"] ), GafferImage.ImageAlgo.tiles( constantNodes[1]["out"] ) )

	def testPracticalTransparencyPrune( self ) :
		representativeImage = GafferImage.ImageReader()
		representativeImage["fileName"].setValue( self.representativeImagePath )

		empty = GafferImage.Empty()
		empty["format"].setValue( GafferImage.Format( imath.Box2i( imath.V2i( 0 ), imath.V2i( 150, 100 ) ), 1 ) )

		properlyLabelledIn = GafferImage.DeepMerge()
		properlyLabelledIn["in"][0].setInput( representativeImage["out"] )
		properlyLabelledIn["in"][1].setInput( empty["out"] )

		# The representative image from Arnold actually contains overlaps one floating point epsilon in width.
		# Get rid of those, and then we can see the sampleCounts change in a predictable way
		actuallyTidyIn = GafferImage.DeepState()
		actuallyTidyIn["in"].setInput( properlyLabelledIn["out"] )

		prune = GafferImage.DeepState()
		prune["in"].setInput( actuallyTidyIn["out"] )
		prune["pruneTransparent"].setValue( True )

		flatRef = GafferImage.DeepState()
		flatRef["in"].setInput( actuallyTidyIn["out"] )
		flatRef["deepState"].setValue( GafferImage.DeepState.TargetState.Flat )

		flatPrune = GafferImage.DeepState()
		flatPrune["in"].setInput( prune["out"] )
		flatPrune["deepState"].setValue( GafferImage.DeepState.TargetState.Flat )

		diff = GafferImage.Merge()
		diff['operation'].setValue( GafferImage.Merge.Operation.Difference )
		diff['in'][0].setInput( flatPrune["out"] )
		diff['in'][1].setInput( flatRef["out"] )

		diffStats = GafferImage.ImageStats()
		diffStats["in"].setInput( diff["out"] )
		diffStats["area"].setValue( diff["out"].dataWindow() )


		origCounts = GafferImage.DeepSampleCounts()
		origCounts["in"].setInput( actuallyTidyIn["out"] )

		prunedCounts = GafferImage.DeepSampleCounts()
		prunedCounts["in"].setInput( prune["out"] )

		diffCounts = GafferImage.Merge()
		diffCounts["operation"].setValue( GafferImage.Merge.Operation.Subtract )
		diffCounts["in"][0].setInput( origCounts["out"] )
		diffCounts["in"][1].setInput( prunedCounts["out"] )

		diffCountsStats = GafferImage.ImageStats()
		diffCountsStats["in"].setInput( diffCounts["out"] )
		diffCountsStats["area"].setValue( diffCounts["out"].dataWindow() )

		self.assertEqual( diffCountsStats["max"].getValue()[0], 0 )
		# For some reason, our test data from Arnold has a bunch of transparent pixels to start with,
		# so we've got some stuff to throw out
		self.assertLess( diffCountsStats["min"].getValue()[0], -20 )
		self.assertLess( diffCountsStats["min"].getValue()[0], -0.26 )

		# We've got some moderate error introduced by discarding transparent.  Why is it so large?
		# Looks like those transparent pixels are slightly emissive
		for i in range( 4 ):
			self.assertLessEqual( diffStats["max"].getValue()[i], [0.00001,0.00001,0.00001,0][i] )
			self.assertGreaterEqual( diffStats["max"].getValue()[i], [0.000001,0.000001,0.000001,0][i] )

		# By premulting/unpremulting, we zero out samples with no alpha
		premultiply = GafferImage.Premultiply()
		premultiply["in"].setInput( actuallyTidyIn["out"] )
		unpremultiply = GafferImage.Unpremultiply()
		unpremultiply["in"].setInput( premultiply["out"] )
		flatRef["in"].setInput( unpremultiply["out"] )
		prune["in"].setInput( unpremultiply["out"] )

		# That gets us a couple extra digits of matching - this is more like what we would expect based
		# on floating point precision
		for i in range( 4 ):
			self.assertLessEqual( diffStats["max"].getValue()[i], [0.0000005,0.0000005,0.0000005,0][i] )

		# But now lets hack it to really make some transparent pixels
		grade = GafferImage.Grade()
		grade["in"].setInput( actuallyTidyIn["out"] )
		grade["channels"].setValue( '[A]' )
		grade["multiply"]["a"].setValue( 1.5 )
		grade["offset"]["a"].setValue( -0.5 )

		premultiply['in'].setInput( grade["out"] )

		# Now we can kill lots of samples
		self.assertEqual( diffCountsStats["max"].getValue()[0], 0 )
		self.assertLess( diffCountsStats["min"].getValue()[0], -200 )
		self.assertLess( diffCountsStats["min"].getValue()[0], -10 )

		# And the flattened results still match closely
		for i in range( 4 ):
			self.assertLessEqual( diffStats["max"].getValue()[i], [0.0000005,0.0000005,0.0000005,0.0000002][i] )

	def testRealisticReference( self ) :
		representativeImage = GafferImage.ImageReader()
		representativeImage["fileName"].setValue( self.representativeImagePath )

		offset = GafferImage.Offset()
		offset["in"].setInput( representativeImage["out"] )
		offset["offset"].setValue( imath.V2i( -58, 11 ) )
		depthGrade = self.__createDepthGrade()
		depthGrade["in"].setInput( offset["out"] )
		depthGrade["depthOffset"].setValue( -0.9 )

		offset2 = GafferImage.Offset()
		offset2["in"].setInput( representativeImage["out"] )
		offset2["offset"].setValue( imath.V2i( -44, -46 ) )
		depthGrade2 = self.__createDepthGrade()
		depthGrade2["in"].setInput( offset2["out"] )
		depthGrade2["depthOffset"].setValue( -1.5 )

		deepMerge = GafferImage.DeepMerge()
		deepMerge["in"][-1].setInput( representativeImage["out"] )
		deepMerge["in"][-1].setInput( depthGrade["out"] )
		deepMerge["in"][-1].setInput( depthGrade2["out"] )

		referenceImage = GafferImage.ImageReader()
		referenceImage["fileName"].setValue( self.mergeReferencePath )

		self.__assertDeepStateProcessing( deepMerge["out"], referenceImage["out"], [ 0.002, 0.002, 0.002, 0.0003 ], [ 0.0001, 0.0001, 0.0001, 0.00003 ], 100, 2 )

		firstResult = GafferImage.DeepState()
		firstResult["in"].setInput( deepMerge["out"] )
		firstResult["deepState"].setValue( GafferImage.DeepState.TargetState.Flat )

		giantDepthOffset = self.__createDepthGrade()
		giantDepthOffset["in"].setInput( deepMerge["out"] )
		giantDepthOffset["depthOffset"].setValue( 100000 )

		# A large depth offset means we have insufficient floating point precision to represent
		# some samples, and some samples will collapse together.  This will throw off some pixels,
		# but most pixels should still be close to correct ( and in particular, the alpha channel is independent
		# of the order of results, so it's fine )
		self.__assertDeepStateProcessing( giantDepthOffset["out"], firstResult["out"], [ 0.5, 0.5, 0.5, 0.000002 ], [ 0.0002, 0.0002, 0.0002, 0.00000003 ], 50, 1 )

	def testMoreArbitraryOffsets( self ) :
		representativeImage = GafferImage.ImageReader()
		representativeImage["fileName"].setValue( self.representativeImagePath )

		crop = GafferImage.Crop()
		crop["in"].setInput( representativeImage["out"] )
		offset = GafferImage.Offset()
		offset["in"].setInput( crop["out"] )
		depthGrade = self.__createDepthGrade()
		depthGrade["in"].setInput( offset["out"] )

		deepMerge = GafferImage.DeepMerge()
		deepMerge["in"][-1].setInput( representativeImage["out"] )
		deepMerge["in"][-1].setInput( depthGrade["out"] )

		firstResult = GafferImage.DeepState()
		firstResult["in"].setInput( deepMerge["out"] )
		firstResult["deepState"].setValue( GafferImage.DeepState.TargetState.Flat )

		deepMergeBackwards = GafferImage.DeepMerge()
		deepMergeBackwards["in"][-1].setInput( depthGrade["out"] )
		deepMergeBackwards["in"][-1].setInput( representativeImage["out"] )

		giantDepthOffset = self.__createDepthGrade()
		giantDepthOffset["in"].setInput( deepMerge["out"] )
		giantDepthOffset["depthOffset"].setValue( 100000 )

		flatRepresentative = GafferImage.DeepState()
		flatRepresentative["in"].setInput( representativeImage["out"] )
		flatRepresentative["deepState"].setValue( GafferImage.DeepState.TargetState.Flat )

		flatCrop = GafferImage.Crop()
		flatCrop["in"].setInput( flatRepresentative["out"] )
		flatCrop["area"].setInput( crop["area"] )

		flatOffset = GafferImage.Offset()
		flatOffset["in"].setInput( flatCrop["out"] )
		flatOffset["offset"].setInput( offset["offset"] )

		flatOver = GafferImage.Merge()
		flatOver['operation'].setValue( GafferImage.Merge.Operation.Over )
		flatOver['in'][0].setInput( flatRepresentative["out"] )
		flatOver['in'][1].setInput( flatOffset["out"] )

		for curOffset, curDepthOffset, curCrop  in [
			[ imath.V2i( 0, 0 ), 0, None ],
			[ imath.V2i( 1, 1 ), 0.0001, None ],
			[ imath.V2i( 4, 6 ), 0.2, None ],
			[ imath.V2i( 10, 14 ), 0.3, None ],
			[ imath.V2i( 0, 0 ), 0, imath.Box2i( imath.V2i( 11, 17 ), imath.V2i( 101, 93 ) ) ],
			[ imath.V2i( 10, 14 ), 0.3, imath.Box2i( imath.V2i( 19, 23 ), imath.V2i( 91, 73 ) ) ],
		]:
			offset["offset"].setValue( curOffset )
			depthGrade["depthOffset"].setValue( curDepthOffset )
			if curCrop:
				crop["area"].setValue( curCrop )
			else:
				crop["area"].setValue( imath.Box2i( imath.V2i( 0, 0 ), imath.V2i( 150, 100 ) ) )

			expectedMaxPrune = 4 if curDepthOffset == 0 or curCrop else 100
			expectedAveragePrune = 0.1 if curDepthOffset == 0 or curCrop else 0.45

			# Comparing to a flat over isn't very accurate - we need a big tolerance.  But we can make sure it
			# didn't explode, and we can check the alpha accurately.
			self.__assertDeepStateProcessing( deepMerge["out"], flatOver["out"], [ 8, 8, 8, 0.000003 ], [ 0.09, 0.09, 0.09, 0.0000002 ], expectedMaxPrune, expectedAveragePrune )

			# Switching the order we merge in should have no impact
			self.__assertDeepStateProcessing( deepMergeBackwards["out"], firstResult["out"], [ 0.000002, 0.000002, 0.000002, 0 ], [ 0.00000002, 0.00000002, 0.00000002, 0 ], expectedMaxPrune, expectedAveragePrune )

			# As in prev test, this is large enough to cause precision problems, but things should still mostly work
			self.__assertDeepStateProcessing( giantDepthOffset["out"], firstResult["out"], [ 0.7, 0.7, 0.7, 0.000004 ], [ 0.002, 0.002, 0.002, 0.0000002 ], min( expectedMaxPrune, 20 ), expectedAveragePrune )

	def testMissingChannels( self ) :

		# Create some messy data
		representativeImage = GafferImage.ImageReader()
		representativeImage["fileName"].setValue( self.representativeImagePath )

		offset = GafferImage.Offset()
		offset["in"].setInput( representativeImage["out"] )
		offset["offset"].setValue( imath.V2i( 29, 9 ) )

		deepMerge = GafferImage.DeepMerge()
		deepMerge["in"][0].setInput( representativeImage["out"] )
		deepMerge["in"][1].setInput( offset["out"] )

		referenceFlatten = GafferImage.DeepState()
		referenceFlatten["in"].setInput( deepMerge["out"] )
		referenceFlatten["deepState"].setValue( GafferImage.DeepState.TargetState.Flat )

		deleteChannels = GafferImage.DeleteChannels()
		deleteChannels["in"].setInput( deepMerge["out"] )

		self.__assertDeepStateProcessing( deleteChannels["out"], referenceFlatten["out"], [ 0, 0, 0, 0 ], [ 0, 0, 0, 0 ], 100, 0.45 )

		# Having no ZBack should be equivalent to having ZBack = Z
		deleteChannels["channels"].setValue( "ZBack" )

		referenceNoZBack = GafferImage.Shuffle()
		referenceNoZBack["in"].setInput( deepMerge["out"] )
		referenceNoZBack["channels"].addChild( referenceNoZBack.ChannelPlug( "ZBack", "Z" ) )

		referenceFlatten["in"].setInput( referenceNoZBack["out"] )

		self.__assertDeepStateProcessing( deleteChannels["out"], referenceFlatten["out"], [ 0, 0, 0, 0 ], [ 0, 0, 0, 0 ], 100, 0.45 )

		# Removing A results in all samples just getting summed.
		deleteChannels["channels"].setValue( "A" )

		referenceNoAlphaA = GafferImage.DeleteChannels()
		referenceNoAlphaA["in"].setInput( representativeImage["out"] )
		referenceNoAlphaA["channels"].setValue( "A" )

		referenceFlattenA = GafferImage.DeepState()
		referenceFlattenA["in"].setInput( referenceNoAlphaA["out"] )
		referenceFlattenA["deepState"].setValue( GafferImage.DeepState.TargetState.Flat )

		referenceNoAlphaB = GafferImage.DeleteChannels()
		referenceNoAlphaB["in"].setInput( offset["out"] )
		referenceNoAlphaB["channels"].setValue( "A" )

		referenceFlattenB = GafferImage.DeepState()
		referenceFlattenB["in"].setInput( referenceNoAlphaB["out"] )
		referenceFlattenB["deepState"].setValue( GafferImage.DeepState.TargetState.Flat )

		referenceSum = GafferImage.Merge()
		referenceSum['operation'].setValue( GafferImage.Merge.Operation.Add )
		referenceSum['in'][0].setInput( referenceFlattenA["out"] )
		referenceSum['in'][1].setInput( referenceFlattenB["out"] )

		self.__assertDeepStateProcessing( deleteChannels["out"], referenceSum["out"], [ 3e-6, 3e-6, 3e-6, 10 ], [ 2e-8, 2e-8, 2e-8, 10 ], 0, 0 )

		deleteChannels["channels"].setValue( "A ZBack" )

		self.__assertDeepStateProcessing( deleteChannels["out"], referenceSum["out"], [ 3e-6, 3e-6, 3e-6, 10 ], [ 2e-8, 2e-8, 2e-8, 10 ], 0, 0 )

		deleteChannels["channels"].setValue( "A Z ZBack" )

		self.__assertDeepStateProcessing( deleteChannels["out"], referenceSum["out"], [ 3e-6, 3e-6, 3e-6, 10 ], [ 2e-8, 2e-8, 2e-8, 10 ], 0, 0 )

		# Having no Z should be equivalent to having all the samples composited in their current order
		deleteChannels["channels"].setValue( "Z ZBack" )

		try:
			import GafferOSL
		except:
			raise unittest.SkipTest( "Could not load GafferOSL, skipping DeepState missing alpha test" )

		outZIndexCode = GafferOSL.OSLCode( "OSLCode" )
		outZIndexCode["out"].addChild( Gaffer.FloatPlug( "output1", direction = Gaffer.Plug.Direction.Out ) )
		outZIndexCode["code"].setValue( 'output1 = P[2];' )

		replaceDepths = GafferOSL.OSLImage( "OSLImage" )
		replaceDepths["in"].setInput( deepMerge["out"] )
		replaceDepths["channels"].addChild( Gaffer.NameValuePlug( "Z", Gaffer.FloatPlug( "value" ), True ) )
		replaceDepths["channels"].addChild( Gaffer.NameValuePlug( "ZBack", Gaffer.FloatPlug( "value" ), True ) )
		replaceDepths["channels"][0]["value"].setInput( outZIndexCode["out"]["output1"] )
		replaceDepths["channels"][1]["value"].setInput( outZIndexCode["out"]["output1"] )

		referenceFlatten["in"].setInput( replaceDepths["out"] )

		self.__assertDeepStateProcessing( deleteChannels["out"], referenceFlatten["out"], [ 0, 0, 0, 10 ], [ 0, 0, 0, 10 ], 100, 0.45 )

		deleteChannels["channels"].setValue( "[Z]" ) # Removing just Z has the same effect

		self.__assertDeepStateProcessing( deleteChannels["out"], referenceFlatten["out"], [ 0, 0, 0, 10 ], [ 0, 0, 0, 10 ], 100, 0.45 )

if __name__ == "__main__":
	unittest.main()
