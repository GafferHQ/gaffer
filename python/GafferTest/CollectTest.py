##########################################################################
#
#  Copyright (c) 2023, Cinesite VFX Ltd. All rights reserved.
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
import imath

import IECore

import Gaffer
import GafferTest

class CollectTest( GafferTest.TestCase ) :

	def testAddInput( self ) :

		node = Gaffer.Collect()

		for inputPlugType, outputPlugType in [
			( Gaffer.BoolPlug, Gaffer.BoolVectorDataPlug ),
			( Gaffer.IntPlug, Gaffer.IntVectorDataPlug ),
			( Gaffer.FloatPlug, Gaffer.FloatVectorDataPlug ),
			( Gaffer.StringPlug, Gaffer.StringVectorDataPlug ),
			( Gaffer.V2iPlug, Gaffer.V2iVectorDataPlug ),
			( Gaffer.V3iPlug, Gaffer.V3iVectorDataPlug ),
			( Gaffer.V2fPlug, Gaffer.V2fVectorDataPlug ),
			( Gaffer.V3fPlug, Gaffer.V3fVectorDataPlug ),
			( Gaffer.Color3fPlug, Gaffer.Color3fVectorDataPlug ),
			( Gaffer.Color4fPlug, Gaffer.Color4fVectorDataPlug ),
			( Gaffer.M33fPlug, Gaffer.M33fVectorDataPlug ),
			( Gaffer.M44fPlug, Gaffer.M44fVectorDataPlug ),
			( Gaffer.AtomicCompoundDataPlug, Gaffer.ObjectVectorPlug ),
			( Gaffer.CompoundObjectPlug, Gaffer.ObjectVectorPlug ),
		] :

			with self.subTest( inputPlugType = inputPlugType ) :

				examplePlug = inputPlugType( defaultValue = inputPlugType.ValueType() )
				self.assertTrue( node.canAddInput( examplePlug ) )

				input = node.addInput( examplePlug )
				self.assertIsInstance( input, inputPlugType )
				self.assertTrue( input.parent().isSame( node["in"] ) )
				self.assertFalse( input.isSame( examplePlug ) )

				self.assertIsNone( input.getInput() )
				self.assertIsNone( examplePlug.getInput() )

				output = node.outputPlugForInput( input )
				self.assertIsInstance( output, outputPlugType )
				self.assertTrue( output.parent().isSame( node["out"] ) )

				self.assertTrue( node.outputPlugForInput( input ).isSame( output ) )
				self.assertTrue( node.inputPlugForOutput( output ).isSame( input ) )

		for unsupportedPlug in [
			Gaffer.NameValuePlug(),
			Gaffer.SplineffPlug( defaultValue = Gaffer.SplineDefinitionff() ),
		] :
			with self.subTest( inputPlugType = type( unsupportedPlug ) ) :
				self.assertFalse( node.canAddInput( unsupportedPlug ) )
				with self.assertRaisesRegex( RuntimeError, "Unsupported plug type" ) :
					node.addInput( unsupportedPlug )

	def testRemoveInput( self ) :

		collect = Gaffer.Collect()
		input = collect.addInput( Gaffer.IntPlug() )
		output = collect.outputPlugForInput( input )
		self.assertEqual( len( collect["in"] ), 1 )
		self.assertEqual( len( collect["out"] ), 1 )

		collect.removeInput( input )
		self.assertEqual( len( collect["in"] ), 0 )
		self.assertEqual( len( collect["out"] ), 0 )
		self.assertIsNone( input.parent() )
		self.assertIsNone( output.parent() )

	def testCollectStrings( self ) :

		source = GafferTest.StringInOutNode()
		source["in"].setValue( "${collectionVariable}" )

		collect = Gaffer.Collect()
		collect["contextVariable"].setValue( "collectionVariable" )
		collect["contextValues"].setValue( IECore.StringVectorData( [ "a", "b", "c", "d", "e" ] ) )

		input = collect.addInput( source["out"] )
		input.setInput( source["out"] )
		output = collect.outputPlugForInput( input )

		self.assertEqual( output.getValue(), IECore.StringVectorData( [ "a", "b", "c", "d", "e" ] ) )
		self.assertEqual( collect["enabledValues"].getValue(), IECore.StringVectorData( [ "a", "b", "c", "d", "e" ] ) )

		collect["enabled"].setValue( False )
		self.assertEqual( output.getValue(), IECore.StringVectorData() )
		self.assertEqual( collect["enabledValues"].getValue(), IECore.StringVectorData() )

	def testCollectColors( self ) :

		random = Gaffer.RandomChoice()
		random.setup( Gaffer.Color3fPlug() )
		random["seedVariable"].setValue( "collectionVariable" )
		random["choices"]["values"].setValue(
			IECore.Color3fVectorData( [
				imath.Color3f( 1, 0, 0 ),
				imath.Color3f( 0, 1, 0 ),
				imath.Color3f( 0, 0, 1 ),
			] )
		)
		random["choices"]["weights"].setValue( IECore.FloatVectorData( [ 1, 1, 1 ] ) )

		collect = Gaffer.Collect()
		collect["contextVariable"].setValue( "collectionVariable" )
		collect["contextValues"].setValue( IECore.StringVectorData( [ str( x ) for x in range( 0, 100 ) ] ) )

		input = collect.addInput( random["out"] )
		input.setInput( random["out"] )
		output = collect.outputPlugForInput( input )

		colors = output.getValue()
		self.assertEqual( len( colors ), 100 )
		uniqueColors = { str( c ) for c in colors }
		self.assertEqual( len( uniqueColors ), 3 )

	def testCollectObjects( self ) :

		script = Gaffer.ScriptNode()

		script["collect"] = Gaffer.Collect()
		script["collect"]["contextVariable"].setValue( "collectionVariable" )
		script["collect"]["contextValues"].setValue( IECore.StringVectorData( [ str( x ) for x in range( 0, 10 ) ] ) )

		script["collect"].addInput( Gaffer.CompoundObjectPlug( "object", defaultValue = IECore.CompoundObject() ) )

		script["expression"] = Gaffer.Expression()
		script["expression"].setExpression(
			"parent['collect']['in']['object'] = IECore.CompoundObject( { 'v' : IECore.StringData( context['collectionVariable'] ) } )"
		)

		self.assertEqual(
			script["collect"]["out"]["object"].getValue(),
			IECore.ObjectVector( [ IECore.CompoundObject( { "v" : IECore.StringData( str( x ) ) } ) for x in range( 0, 10 ) ] )
		)

	def testCollectManyBools( self ) :

		# Exposes the need for the `OutputTraits<BoolPlug>` specialisation.

		collect = Gaffer.Collect()
		collect["contextVariable"].setValue( "collectionVariable" )
		collect["contextValues"].setValue( IECore.StringVectorData( [ str( x ) for x in range( 0, 10000 ) ] ) )

		input = collect.addInput( Gaffer.BoolPlug( "test", defaultValue = True ) )
		output = collect.outputPlugForInput( input )

		self.assertEqual( output.getValue(), IECore.BoolVectorData( [ True ] * 10000 ) )

	def testAffects( self ) :

		collect = Gaffer.Collect()
		in1 = collect.addInput( Gaffer.V3fPlug() )
		in2 = collect.addInput( Gaffer.V3fPlug() )

		def assertAffects( input ) :

			# All inputs affect the internal collection plug.

			dependents = set( collect.affects( input ) )
			self.assertEqual( dependents, { collect["__collection"] } )

			# Which in turn affects all outputs.

			dependents = set( collect.affects( collect["__collection"] ) )
			self.assertEqual( dependents, { collect["enabledValues"] } | set( Gaffer.ValuePlug.Range( collect["out"] ) ) )

		assertAffects( in1["x"] )
		assertAffects( in1["y"] )
		assertAffects( in1["z"] )
		assertAffects( in2["x"] )
		assertAffects( in2["y"] )
		assertAffects( in2["z"] )
		assertAffects( collect["contextVariable"] )
		assertAffects( collect["indexContextVariable"] )
		assertAffects( collect["contextValues"] )

	def testEnabledPlug( self ) :

		script = Gaffer.ScriptNode()

		script["collect"] = Gaffer.Collect()
		self.assertTrue( script["collect"].enabledPlug().isSame( script["collect"]["enabled"] ) )

		script["collect"]["contextVariable"].setValue( "collectionVariable" )
		script["collect"]["indexContextVariable"].setValue( "indexVariable" )
		script["collect"]["contextValues"].setValue( IECore.StringVectorData( [ str( x ) for x in range( 0, 10 ) ] ) )

		script["collect"].addInput( Gaffer.IntPlug( "value" ) )
		script["collect"].addInput( Gaffer.IntPlug( "index" ) )

		script["expression"] = Gaffer.Expression()
		script["expression"].setExpression(
			"i = int( context['collectionVariable'] );"
			"parent['collect']['in']['value'] = i;"
			"parent['collect']['in']['index'] = context['indexVariable'];"
			"parent['collect']['enabled'] = i % 2;"
		)

		self.assertEqual(
			script["collect"]["out"]["value"].getValue(),
			IECore.IntVectorData( [ 1, 3, 5, 7, 9 ] )
		)
		self.assertEqual(
			script["collect"]["out"]["index"].getValue(),
			IECore.IntVectorData( [ 1, 3, 5, 7, 9 ] )
		)
		self.assertEqual(
			script["collect"]["enabledValues"].getValue(),
			IECore.StringVectorData( [ str( x ) for x in range( 0, 10 ) if x % 2 ] )
		)

	def testSerialisation( self ) :

		script = Gaffer.ScriptNode()
		script["uninitialised"] = Gaffer.Collect()
		script["initialised"] = Gaffer.Collect()

		script["initialised"].addInput( Gaffer.StringPlug( "a", defaultValue = "default" ) )
		script["initialised"].addInput( Gaffer.CompoundObjectPlug( "b", defaultValue = IECore.CompoundObject() ) )
		# We're trying to eliminate `Dynamic` from the API, but while it still exists, we want
		# to demonstrate that it doesn't matter whether it is on or off when it comes to
		# Collect node serialisation.
		script["initialised"].addInput( Gaffer.IntPlug( "c", defaultValue = 2, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )

		serialisation = script.serialise()
		self.assertEqual( serialisation.count( "addChild" ), 2 ) # One for each node, but none for the inputs and ouputs

		script2 = Gaffer.ScriptNode()
		script2.execute( serialisation )

		self.assertEqual( len( script2["uninitialised"]["in"] ), 0 )
		self.assertEqual( len( script2["uninitialised"]["out"] ), 0 )

		self.assertEqual( script2["initialised"]["in"].keys(), [ "a", "b", "c" ] )
		self.assertEqual( script2["initialised"]["out"].keys(), [ "a", "b", "c" ] )
		self.assertIsInstance( script2["initialised"]["in"]["a"], Gaffer.StringPlug )
		self.assertEqual( script2["initialised"]["in"]["a"].defaultValue(), "default" )
		self.assertIsInstance( script2["initialised"]["out"]["a"], Gaffer.StringVectorDataPlug )
		self.assertIsInstance( script2["initialised"]["in"]["b"], Gaffer.CompoundObjectPlug )
		self.assertEqual( script2["initialised"]["in"]["b"].defaultValue(), IECore.CompoundObject() )
		self.assertIsInstance( script2["initialised"]["out"]["b"], Gaffer.ObjectVectorPlug )
		self.assertIsInstance( script2["initialised"]["in"]["c"], Gaffer.IntPlug )
		self.assertEqual( script2["initialised"]["in"]["c"].defaultValue(), 2 )
		self.assertIsInstance( script2["initialised"]["out"]["c"], Gaffer.IntVectorDataPlug )

	def testChangingCollectionType( self ) :

		collect = Gaffer.Collect()
		collect["contextVariable"].setValue( "collectionVariable" )
		collect["contextValues"].setValue( IECore.StringVectorData( [ str( x ) for x in range( 0, 10 ) ] ) )

		input = collect.addInput( Gaffer.IntPlug( "test", defaultValue = 0 ) )
		output = collect.outputPlugForInput( input )

		self.assertEqual( output.getValue(), IECore.IntVectorData( [ 0 ] * 10 ) )

		collect.removeInput( input )

		input = collect.addInput( Gaffer.FloatPlug( "test", defaultValue = 0 ) )
		output = collect.outputPlugForInput( input )

		self.assertEqual( output.getValue(), IECore.FloatVectorData( [ 0 ] * 10 ) )

	def testChangingCollectionValue( self ) :

		collect = Gaffer.Collect()
		collect["contextVariable"].setValue( "collectionVariable" )
		collect["contextValues"].setValue( IECore.StringVectorData( [ str( x ) for x in range( 0, 10 ) ] ) )

		input = collect.addInput( Gaffer.IntPlug( "test", defaultValue = 0 ) )
		output = collect.outputPlugForInput( input )
		self.assertEqual( output.getValue(), IECore.IntVectorData( [ 0 ] * 10 ) )

		input.setValue( 1 )
		self.assertEqual( output.getValue(), IECore.IntVectorData( [ 1 ] * 10 ) )

	def testPlugAccessors( self ) :

		collect = Gaffer.Collect()
		input = collect.addInput( Gaffer.IntPlug( "test" ) )
		output = collect.outputPlugForInput( input )
		self.assertTrue( output.parent().isSame( collect["out"] ) )
		self.assertEqual( output.getName(), input.getName() )
		self.assertTrue( collect.inputPlugForOutput( output ).isSame( input ) )

		with self.assertRaisesRegex( RuntimeError, "`IntPlug` is not an output of `Collect`" ) :
			collect.inputPlugForOutput( Gaffer.IntPlug() )

		with self.assertRaisesRegex( RuntimeError, "`test` is not an output of `Collect`" ) :
			collect.inputPlugForOutput( Gaffer.IntPlug( "test" ) )

		with self.assertRaisesRegex( RuntimeError, "`IntPlug` is not an input of `Collect`" ) :
			collect.outputPlugForInput( Gaffer.IntPlug() )

		with self.assertRaisesRegex( RuntimeError, "`test` is not an input of `Collect`" ) :
			collect.outputPlugForInput( Gaffer.IntPlug( "test" ) )

	def testRenameInput( self ) :

		script = Gaffer.ScriptNode()

		script["collect"] = Gaffer.Collect()
		script["collect"]["contextValues"].setValue( IECore.StringVectorData( [ "one" ] ) )

		input1 = script["collect"].addInput( Gaffer.IntPlug( "a", defaultValue = 1 ) )
		output1 = script["collect"].outputPlugForInput( input1 )

		input2 = script["collect"].addInput( Gaffer.IntPlug( "b", defaultValue = 2 ) )
		output2 = script["collect"].outputPlugForInput( input2 )

		def assertPreconditions() :

			self.assertEqual( input1.getName(), "a" )
			self.assertEqual( output1.getName(), "a" )
			self.assertEqual( output1.getValue(), IECore.IntVectorData( [ 1 ] ) )

			self.assertEqual( input2.getName(), "b" )
			self.assertEqual( output2.getName(), "b" )
			self.assertEqual( output2.getValue(), IECore.IntVectorData( [ 2 ] ) )

		assertPreconditions()

		with Gaffer.UndoScope( script ) :
			input1.setName( "b" )

		def assertPostconditions() :

			self.assertEqual( input1.getName(), "b1" )
			self.assertEqual( output1.getName(), "b1" )
			self.assertEqual( output1.getValue(), IECore.IntVectorData( [ 1 ] ) )

			self.assertEqual( input2.getName(), "b" )
			self.assertEqual( output2.getName(), "b" )
			self.assertEqual( output2.getValue(), IECore.IntVectorData( [ 2 ] ) )

		assertPostconditions()

		script.undo()
		assertPreconditions()

		script.redo()
		assertPostconditions()

if __name__ == "__main__":
	unittest.main()
