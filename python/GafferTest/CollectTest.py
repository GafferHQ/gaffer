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

	@GafferTest.TestRunner.CategorisedTestMethod( { "taskCollaboration:performance" } )
	@GafferTest.TestRunner.PerformanceTestMethod()
	def testFanOutPerformance( self ) :

		# A network of nested collects that produces a fan-out task pattern,
		# computing all permutations of the product of `numCollects` integers from
		# the range `[ 0, collectLength )`.
		#
		# Node graph         Compute graph (for `collectLength = 2`)
		# ----------------------------------------------------------
		#
		# collect0             o  oo   o
		#    |                  \/  \ /
		# collect1               o   o
		#    |                    \ /
		# collect2                 o

		numCollects = 3
		collectLength = 64

		script = Gaffer.ScriptNode()

		lastNode = None
		for i in range( 0, numCollects ) :

			query = Gaffer.ContextQuery( f"query{i}" )
			query.addQuery( Gaffer.IntPlug(), f"collect{i}:index" )
			script.addChild( query )

			if lastNode is not None :

				multiply = GafferTest.MultiplyNode( f"multiply{i}" )
				script.addChild( multiply )

				if isinstance( lastNode, Gaffer.ContextQuery ) :
					multiply["op1"].setInput( lastNode["out"][0]["value"] )
				else :
					multiply["op1"].setInput( lastNode["product"] )
				multiply["op2"].setInput( query["out"][0]["value"] )

				lastNode = multiply

			else :

				lastNode = query

		for i in range( 0, numCollects ) :

			collect = Gaffer.Collect( f"collect{i}" )
			script.addChild( collect )

			collect["contextVariable"].setValue( f"collect{i}:value" )
			collect["indexContextVariable"].setValue( f"collect{i}:index" )
			collect["contextValues"].setValue( IECore.StringVectorData( [ str( j ) for j in range( 0, collectLength ) ] ) )

			if isinstance( lastNode, GafferTest.MultiplyNode ) :
				collect.addInput( Gaffer.IntPlug( "value" ) ).setInput( lastNode["product"] )
			elif isinstance( lastNode["out"][0], Gaffer.IntVectorDataPlug ) :
				collect.addInput( Gaffer.IntVectorDataPlug( "value", defaultValue = IECore.IntVectorData() ) ).setInput( lastNode["out"][0] )
			else :
				collect.addInput( Gaffer.ObjectVectorPlug( "value", defaultValue = IECore.ObjectVector() ) ).setInput( lastNode["out"][0] )

			lastNode = collect

		# Measure evaluation performance

		with GafferTest.TestRunner.PerformanceScope() :
			result = lastNode["out"]["value"].getValue()

		# Check we were actually computing what we thought we were.

		for i, iData in enumerate( result ) :
			for j, jData in enumerate( iData ) :
				for k, product in enumerate( jData ) :
					self.assertEqual( product, i * j * k )

	@GafferTest.TestRunner.CategorisedTestMethod( { "taskCollaboration:performance" } )
	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 1 )
	def testFanOutGatherPerformance( self ) :

		# This node graph just splits and recollects a `vector<int>`
		# repeatedly, with the expressions getting a specific index
		# determined by the context, and the collects gathering from
		# them to rebuild the vector.
		#
		# Node graph         Compute graph (for `collectLength = 2`)
		# ----------------------------------------------------------
		#
		# expression0           o   o
		#     |                  \ /
		#  collect0               o
		#     |                  / \
		# expression1           o   o
		#     |                  \ /
		#  collect1               o
		#     |                  / \
		# expression2           o   o
		#     |                  \ /
		#  collect2               o
		#
		# The primary purpose of this test is to check the performance
		# of our cycle-detection code, since it presents huge numbers
		# of unique paths through the downstream dependencies of each
		# compute. A naive cycle detector could scale incredibly badly
		# here.

		numCollects = 10
		collectLength = 64

		script = Gaffer.ScriptNode()

		lastCollect = None
		for i in range( 0, numCollects ) :

			collect = Gaffer.Collect( f"collect{i}" )
			collect["contextValues"].setValue( IECore.StringVectorData( [ str( j ) for j in range( 0, collectLength ) ] ) )
			collect.addInput( Gaffer.IntPlug( "value" ) ).fullName()
			script.addChild( collect )

			## \todo Ideally we'd have something like an ArrayToScalar node we
			# could use instead of Python expressions here, so that there's less
			# overhead in the computes themselves and we're more sensitive to
			# performance improvements in the underlying collaboration mechanism
			# itself.
			expression = Gaffer.Expression( f"expression{i}" )
			script.addChild( expression )

			if lastCollect is None :
				expression.setExpression(
					f'parent["collect{i}"]["in"]["value"] = context["collect:index"]'
				)
			else :
				expression.setExpression(
					f'index = context["collect:index"]; array = parent["collect{i-1}"]["out"]["value"]; parent["collect{i}"]["in"]["value"] = array[index]'
				)

			lastCollect = collect

		with GafferTest.TestRunner.PerformanceScope() :
			result = lastCollect["out"]["value"].getValue()

		self.assertEqual( result, IECore.IntVectorData( range( 0, collectLength ) ) )

	@GafferTest.TestRunner.CategorisedTestMethod( { "taskCollaboration:performance" } )
	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 1 )
	def testLoop( self ) :

		# `collect1` evaluates the output for `loop` for various iterations
		# in parallel. Since each iteration depends on the previous iteration,
		# we end up with iteration `n + 1` waiting for an in-flight iteration `n`
		# from a different thread, and depending on timings, this can lead to
		# increasing-length chains of waiting processes.
		#
		# Node graph         Compute graph (for `maxIterations = 3`)
		# ----------------------------------------------------------
		#
		#   loop <----               o
		#     |      |               | \
		#     |   collect0           |  o
		#     |      |               |	| \
		#     |-------               | /   o
		#     |                      |/   /
		#     |                      |   /
		#     |                      |  /
		#     |                      | /
		#     |                      |/
		#  collect1                  o

		maxIterations = 200

		script = Gaffer.ScriptNode()

		script["contextQuery"] = Gaffer.ContextQuery()
		script["contextQuery"].addQuery( Gaffer.IntPlug(), "collect1:index" )

		script["loop"] = Gaffer.Loop()
		script["loop"].setup( Gaffer.ObjectVectorPlug( defaultValue = IECore.ObjectVector() ) )
		script["loop"]["iterations"].setInput( script["contextQuery"]["out"][0]["value"] )

		script["collect0"] = Gaffer.Collect()
		script["collect0"]["contextValues"].setValue( IECore.StringVectorData( [ "one" ] ) )
		script["collect0"].addInput(script["loop"]["previous"] )
		script["collect0"]["in"][0].setInput( script["loop"]["previous"] )
		script["loop"]["next"].setInput( script["collect0"]["out"][0] )

		script["collect1"] = Gaffer.Collect()
		script["collect1"]["contextValues"].setValue( IECore.StringVectorData( [ str( x ) for x in range( 0, maxIterations ) ] ) )
		script["collect1"]["contextVariable"].setValue( "collect1:value" )
		script["collect1"]["indexContextVariable"].setValue( "collect1:index" )
		script["collect1"].addInput( script["loop"]["out"] )
		script["collect1"]["in"][0].setInput( script["loop"]["out"] )

		# Measure performance

		with GafferTest.TestRunner.PerformanceScope() :
			result = script["collect1"]["out"][0].getValue()

		# Check we were actually computing what we thought

		def depth( v ) :
			if len( v ) == 0 :
				return 0
			else :
				self.assertEqual( len( v ), 1 )
				return depth( v[0] ) + 1

		for i in range( maxIterations ) :
			self.assertEqual( depth( result[i] ), i )

if __name__ == "__main__":
	unittest.main()
