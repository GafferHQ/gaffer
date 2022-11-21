##########################################################################
#
#  Copyright (c) 2022, Cinesite VFX Ltd. All rights reserved.
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

import collections
import unittest
import six
import imath

import IECore

import Gaffer
import GafferTest

class RandomChoiceTest( GafferTest.TestCase ) :

	def testSetup( self ) :

		for plugType, valuesPlugType in [
			( Gaffer.BoolPlug, Gaffer.BoolVectorDataPlug ),
			( Gaffer.IntPlug, Gaffer.IntVectorDataPlug ),
			( Gaffer.FloatPlug, Gaffer.FloatVectorDataPlug ),
			( Gaffer.StringPlug, Gaffer.StringVectorDataPlug ),
			( Gaffer.V2iPlug, Gaffer.V2iVectorDataPlug ),
			( Gaffer.V3iPlug, Gaffer.V3iVectorDataPlug ),
			( Gaffer.V2fPlug, Gaffer.V2fVectorDataPlug ),
			( Gaffer.V3fPlug, Gaffer.V3fVectorDataPlug ),
			( Gaffer.Color3fPlug, Gaffer.Color3fVectorDataPlug ),
		] :

			examplePlug = plugType()
			self.assertTrue( Gaffer.RandomChoice.canSetup( examplePlug ) )

			node = Gaffer.RandomChoice()
			node.setup( examplePlug )
			self.assertIsInstance( node["out"], plugType )
			self.assertFalse( node["out"].isSame( examplePlug ) )
			self.assertIsNone( examplePlug.getInput() )
			self.assertEqual( node["out"].defaultValue(), examplePlug.defaultValue() )

			self.assertIsInstance( node["choices"]["values"], valuesPlugType )
			self.assertEqual( len( node["choices"]["values"].getValue() ), 0 )

			with six.assertRaisesRegex( self, Exception, "Already set up" ) :
				node.setup( examplePlug )

		for unsupportedPlug in [
			Gaffer.CompoundDataPlug(),
			Gaffer.CompoundObjectPlug( defaultValue = IECore.CompoundObject() ),
		] :
			self.assertFalse( Gaffer.RandomChoice.canSetup( unsupportedPlug ) )
			node = Gaffer.RandomChoice()
			with six.assertRaisesRegex( self, RuntimeError, "Unsupported plug type" ) :
				node.setup( unsupportedPlug )

	def testChoice( self ) :

		node = Gaffer.RandomChoice()

		node.setup( Gaffer.StringPlug() )
		node["choices"]["values"].setValue( IECore.StringVectorData( [ "apple", "pear", "hat" ] ) )
		node["choices"]["weights"].setValue( IECore.FloatVectorData( [ 0.25, 0.5, 0.25 ] ) )

		iterations = 100000

		count = collections.Counter()
		for seed in range( 0, iterations ) :
			node["seed"].setValue( seed )
			count[node["out"].getValue()] += 1

		for choice, weight in zip( node["choices"]["values"].getValue(), node["choices"]["weights"].getValue() ) :
			self.assertAlmostEqual(
				count[choice] / float( iterations ), weight,
				places = 2
			)

	def testSeedVariable( self ) :

		node = Gaffer.RandomChoice()

		node.setup( Gaffer.StringPlug() )
		node["seedVariable"].setValue( "seed" )
		node["choices"]["values"].setValue( IECore.StringVectorData( [ "apple", "pear", "hat" ] ) )
		node["choices"]["weights"].setValue( IECore.FloatVectorData( [ 0.25, 0.5, 0.25 ] ) )

		iterations = 100000

		count = collections.Counter()
		with Gaffer.Context() as context :
			for seed in range( 0, iterations ) :
				context["seed"] = seed
				count[node["out"].getValue()] += 1

		for choice, weight in zip( node["choices"]["values"].getValue(), node["choices"]["weights"].getValue() ) :
			self.assertAlmostEqual(
				count[choice] / float( iterations ), weight,
				places = 2
			)

	def testNoChoices( self ) :

		for defaultValue in range( 0, 10 ) :

			# Empty list of choices. Expect the default value
			# the node was set up with.
			node = Gaffer.RandomChoice()
			node.setup( Gaffer.IntPlug( defaultValue = defaultValue ) )
			self.assertEqual( node["out"].getValue(), defaultValue )

			# Choices, but all with 0 weight. As above.
			node["choices"]["values"].setValue( IECore.IntVectorData( [ 1, 2, 3 ] ) )
			node["choices"]["weights"].setValue( IECore.FloatVectorData( [ 0, 0, 0 ] ) )
			self.assertEqual( node["out"].getValue(), defaultValue )

	def testSerialisation( self ) :

		script = Gaffer.ScriptNode()
		script["uninitialised"] = Gaffer.RandomChoice()
		script["initialised"] = Gaffer.RandomChoice()

		script["initialised"].setup( Gaffer.StringPlug( defaultValue = "default" )  )
		script["initialised"]["choices"]["values"].setValue( IECore.StringVectorData( [ "one", "two" ] ) )
		script["initialised"]["choices"]["weights"].setValue( IECore.FloatVectorData( [ 1.0, 2.0 ] ) )

		script2 = Gaffer.ScriptNode()
		script2.execute( script.serialise() )

		self.assertNotIn( "out", script2["uninitialised"] )
		self.assertNotIn( "values", script2["uninitialised"]["choices"] )

		self.assertEqual( script2["initialised"]["choices"]["values"].getValue(), script["initialised"]["choices"]["values"].getValue() )
		self.assertEqual( script2["initialised"]["out"].defaultValue(), script["initialised"]["out"].defaultValue() )

	def testCompoundNumericPlugs( self ) :

		node = Gaffer.RandomChoice()
		node.setup( Gaffer.V3fPlug() )
		node["choices"]["values"].setValue(
			IECore.V3fVectorData( [ imath.V3f( 1, 2, 3 ), imath.V3f( 4, 5, 6 ) ] )
		)
		node["choices"]["weights"].setValue(
			IECore.FloatVectorData( [ 0, 1.0 ] )
		)

		self.assertEqual( node["out"].getValue(), imath.V3f( 4, 5,6 ) )

	def testMismatchedLengths( self ) :

		node = Gaffer.RandomChoice()
		node.setup( Gaffer.StringPlug() )
		node["choices"]["values"].setValue(
			IECore.StringVectorData( [ "a", "b", "c" ] )
		)

		with six.assertRaisesRegex(
			self, Gaffer.ProcessException,
			r".*Length of `choices.weights` does not match length of `choices.values` \(0 but should be 3\).*"
		) :
			node["out"].getValue()

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testPerformance( self ) :

		node = Gaffer.RandomChoice()
		node.setup( Gaffer.IntPlug() )
		node["seedVariable"].setValue( "seed" )
		node["choices"]["values"].setValue( IECore.IntVectorData( range( 0, 100000 ) ) )
		node["choices"]["weights"].setValue( IECore.FloatVectorData( [ 1 ] * 100000 ) )

		with GafferTest.TestRunner.PerformanceScope() :
			GafferTest.parallelGetValue( node["out"], 100000, "seed" )

if __name__ == "__main__":
	unittest.main()
