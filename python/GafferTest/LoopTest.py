##########################################################################
#
#  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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

import Gaffer
import GafferTest

class LoopTest( GafferTest.TestCase ) :

	def intLoop( self ) :

		result = Gaffer.Loop()
		result.setup( Gaffer.IntPlug() )
		return result

	def test( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = self.intLoop()
		s["a"] = GafferTest.AddNode()

		s["n"]["in"].setValue( 0 )
		s["n"]["next"].setInput( s["a"]["sum"] )
		s["a"]["op1"].setInput( s["n"]["previous"] )
		s["a"]["op2"].setValue( 1 )

		s["n"]["iterations"].setValue( 1 )
		self.assertEqual( s["n"]["out"].getValue(), 1 )

		s["n"]["iterations"].setValue( 10 )
		self.assertEqual( s["n"]["out"].getValue(), 10 )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( s2["n"].keys(), s["n"].keys() )
		self.assertEqual( s2["n"]["out"].getValue(), 10 )

	def testLoopIndex( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = self.intLoop()
		s["a"] = GafferTest.AddNode()

		s["n"]["in"].setValue( 0 )
		s["n"]["next"].setInput( s["a"]["sum"] )
		s["a"]["op1"].setInput( s["n"]["previous"] )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression( 'parent["a"]["op2"] = context.get( "loop:index", 0 )' )

		s["n"]["iterations"].setValue( 4 )
		self.assertEqual( s["n"]["out"].getValue(), 1 + 2 + 3 )

		s["n"]["iterations"].setValue( 5 )
		self.assertEqual( s["n"]["out"].getValue(), 1 + 2 + 3 + 4 )

		# Make sure the loop index is undefined when pulling the input, instead of leaking out upstream

		s["e2"] = Gaffer.Expression()
		s["e2"].setExpression( 'parent["n"]["in"] = context.get( "loop:index", -100 )' )

		self.assertEqual( s["n"]["out"].getValue(), 1 + 2 + 3 + 4 - 100 )

	def testChangeLoopNetwork( self ) :

		n = self.intLoop()
		a1 = GafferTest.AddNode()
		a2 = GafferTest.AddNode()

		n["in"].setValue( 0 )
		n["next"].setInput( a2["sum"] )

		a2["op1"].setInput( a1["sum"] )
		a2["op2"].setValue( 1 )

		a1["op1"].setInput( n["previous"] )
		a1["op2"].setValue( 1 )

		n["iterations"].setValue( 2 )
		self.assertEqual( n["out"].getValue(), 4 )

		a2["op2"].setValue( 2 )
		self.assertEqual( n["out"].getValue(), 6 )

	def testDirtyPropagation( self ) :

		n = self.intLoop()
		a = GafferTest.AddNode()

		n["in"].setValue( 0 )
		n["next"].setInput( a["sum"] )

		a["op1"].setInput( n["previous"] )
		a["op2"].setValue( 1 )

		cs = GafferTest.CapturingSlot( n.plugDirtiedSignal() )

		a["op2"].setValue( 2 )
		self.assertEqual( set( [ s[0] for s in cs ] ), { n["next"], n["out"], n["previous"] } )

		del cs[:]
		n["iterations"].setValue( 100 )
		self.assertEqual( set( [ s[0] for s in cs ] ), { n["iterations"], n["out"] } )

		del cs[:]
		n["indexVariable"].setValue( "myIndex" )
		self.assertEqual( set( [ s[0] for s in cs ] ), { n["indexVariable"], n["out"], n["previous"], n["next"] } )

	def testCustomLoopIndex( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = self.intLoop()
		s["n"]["indexVariable"].setValue( "myIndex" )
		s["a"] = GafferTest.AddNode()

		s["n"]["in"].setValue( 0 )
		s["n"]["next"].setInput( s["a"]["sum"] )
		s["a"]["op1"].setInput( s["n"]["previous"] )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression( 'parent["a"]["op2"] = context.get( "myIndex", 0 )' )

		s["n"]["iterations"].setValue( 4 )
		self.assertEqual( s["n"]["out"].getValue(), 1 + 2 + 3 )

		s["n"]["iterations"].setValue( 5 )
		self.assertEqual( s["n"]["out"].getValue(), 1 + 2 + 3 + 4 )

	def testEnabled( self ) :

		n = self.intLoop()
		a = GafferTest.AddNode()

		n["in"].setValue( 0 )
		n["next"].setInput( a["sum"] )

		a["op1"].setInput( n["previous"] )
		a["op2"].setValue( 1 )

		n["iterations"].setValue( 4 )
		self.assertEqual( n["out"].getValue(), 4 )

		n["enabled"].setValue( False )
		self.assertEqual( n["out"].getValue(), 0 )

		self.assertTrue( n.correspondingInput( n["out"] ).isSame( n["in"] ) )

	def testSetup( self ) :

		n = Gaffer.Loop()

		self.assertNotIn( "in", n )
		self.assertNotIn( "out", n )
		self.assertNotIn( "previous", n )
		self.assertNotIn( "next", n )

		n.setup( Gaffer.StringPlug() )

		self.assertIsInstance( n["in"], Gaffer.StringPlug )
		self.assertIsInstance( n["out"], Gaffer.StringPlug )
		self.assertIsInstance( n["previous"], Gaffer.StringPlug )
		self.assertIsInstance( n["next"], Gaffer.StringPlug )

	def testSerialisationUsesSetup( self ) :

		s1 = Gaffer.ScriptNode()
		s1["c"] = Gaffer.Loop()
		s1["c"].setup( Gaffer.IntPlug() )

		ss = s1.serialise()
		self.assertIn( "setup", ss )
		self.assertEqual( ss.count( "addChild" ), 1 )
		self.assertNotIn( "Dynamic", ss )
		self.assertNotIn( "Serialisable", ss )
		self.assertNotIn( "setInput", ss )

		s2 = Gaffer.ScriptNode()
		s2.execute( ss )
		self.assertIn( "in", s2["c"] )
		self.assertIn( "out", s2["c"] )
		self.assertIsInstance( s2["c"]["in"], Gaffer.IntPlug )
		self.assertIsInstance( s2["c"]["out"], Gaffer.IntPlug )
		self.assertIsInstance( s2["c"]["previous"], Gaffer.IntPlug )
		self.assertIsInstance( s2["c"]["next"], Gaffer.IntPlug )

	def testComputeDuringDirtyPropagation( self ) :

		# Make a loop

		loop = self.intLoop()
		add = GafferTest.AddNode()

		loop["in"].setValue( 0 )
		loop["next"].setInput( add["sum"] )
		loop["iterations"].setValue( 5 )

		add["op1"].setInput( loop["previous"] )
		add["op2"].setValue( 1 )

		self.assertEqual( loop["out"].getValue(), 5 )

		# Edit `loop["in"]` to trigger dirty propagation, and capture the
		# value of each plug at the point `plugDirtiedSignal()` is emitted
		# for it.

		def plugValue( plug ) :

			with Gaffer.Context() as c :

				if plug in {
					loop["next"], loop["previous"], add["op1"], add["sum"]
				} :
					# These plugs are sensitive to "loop:index", so we provide it
					# manually. We are spying on the values in the last-but-one
					# iteration of the loop.
					c["loop:index"] = 3

				return plug.getValue()

		valuesWhenDirtied = {}
		def plugDirtied( plug ) :

			valuesWhenDirtied[plug] = plugValue( plug )

		loop.plugDirtiedSignal().connect( plugDirtied, scoped = False )
		add.plugDirtiedSignal().connect( plugDirtied, scoped = False )
		loop["in"].setValue( 1 )

		# Check that we saw the values we expected.

		self.assertEqual( valuesWhenDirtied[loop["in"]], 1 )
		self.assertEqual( valuesWhenDirtied[loop["out"]], 6 )
		self.assertEqual( valuesWhenDirtied[loop["next"]], 5 )
		self.assertEqual( valuesWhenDirtied[loop["previous"]], 4 )
		self.assertEqual( valuesWhenDirtied[add["sum"]], 5 )
		self.assertEqual( valuesWhenDirtied[add["op1"]], 4 )

		# Double check that we see the same values after
		# clearing the cache and doing a fresh compute.

		Gaffer.ValuePlug.clearCache()
		Gaffer.ValuePlug.clearHashCache()

		for plug, value in valuesWhenDirtied.items() :
			self.assertEqual( plugValue( plug ), value )

	@GafferTest.TestRunner.CategorisedTestMethod( { "taskCollaboration:hashAliasing" } )
	def testHashAliasingDeadlock( self ) :

		script = Gaffer.ScriptNode()

		script["loop"] = Gaffer.Loop()
		script["loop"].setup( Gaffer.StringPlug() )

		# Dumb expression that just sets the value for the next iteration to
		# the value from the previous iteration. Because of de8ab79d6f958cef3b80954798f8083a346945a7,
		# the hash for the expression output is identical for every iteration of
		# the loop, even though the context differs.
		script["expression"] = Gaffer.Expression()
		script["expression"].setExpression( """parent["loop"]["next"] = parent["loop"]["previous"]""" )

		# Get the result of the loop. This actually computes the _first_ iteration of the loop first,
		# while computing the hash of the result, and reuses the result for every other loop iteration.
		script["loop"]["out"].getValue()
		# Simulate cache eviction by clearing the compute cache.
		Gaffer.ValuePlug.clearCache()
		# Get the value again. Now, because the hash is still cached, this will first start the
		# compute for the _last_ iteration. This leads to a recursive compute, which can cause deadlock
		# if not handled appropriately.
		script["loop"]["out"].getValue()

if __name__ == "__main__":
	unittest.main()
