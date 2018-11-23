##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
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
import inspect
import unittest

import IECore

import Gaffer
import GafferTest

class StringPlugTest( GafferTest.TestCase ) :

	def inOutNode( self, name="StringInOutNode", defaultValue="", substitutions = IECore.StringAlgo.Substitutions.AllSubstitutions ) :

		return GafferTest.StringInOutNode( name = name, defaultValue = defaultValue, substitutions = substitutions )

	def testExpansion( self ) :

		n = self.inOutNode()
		self.assertHashesValid( n )

		# nothing should be expanded when we're in a non-computation context
		n["in"].setValue( "testyTesty.##.exr" )
		self.assertEqual( n["in"].getValue(), "testyTesty.##.exr" )

		n["in"].setValue( "${a}-$b-${a:b}" )
		self.assertEqual( n["in"].getValue(), "${a}-$b-${a:b}" )

		# but expansions should happen magically when the compute()
		# calls getValue().
		context = Gaffer.Context()
		context.setFrame( 10 )
		n["in"].setValue( "testyTesty.###.exr" )
		with context :
			self.assertEqual( n["out"].getValue(), "testyTesty.010.exr" )

		context["A"] = "apple"
		n["in"].setValue( "what a lovely $A" )
		with context :
			self.assertEqual( n["out"].getValue(), "what a lovely apple" )
		n["in"].setValue( "what a lovely ${A}" )
		with context :
			self.assertEqual( n["out"].getValue(), "what a lovely apple" )
		context["A"] = "peach"
		with context :
			self.assertEqual( n["out"].getValue(), "what a lovely peach" )

		context["env:dir"] = "a-path"
		n["in"].setValue( "a-${env:dir}-b" )
		with context :
			self.assertEqual( n["out"].getValue(), "a-a-path-b" )

		n["in"].setValue( "$dontExist" )
		with context :
			self.assertEqual( n["out"].getValue(), "" )

		# once again, nothing should be expanded when we're in a
		# non-computation context
		n["in"].setValue( "testyTesty.##.exr" )
		self.assertEqual( n["in"].getValue(), "testyTesty.##.exr" )

	def testRecursiveExpansion( self ) :

		n = self.inOutNode()
		n["in"].setValue( "$a" )

		context = Gaffer.Context()
		context["a"] = "a$b"
		context["b"] = "b"

		with context :
			self.assertEqual( n["out"].getValue(), "ab" )

	def testRecursiveExpansionCycles( self ) :

		n = self.inOutNode()
		n["in"].setValue( "$a" )

		context = Gaffer.Context()
		context["a"] = "a$b"
		context["b"] = "b$a"

		with context :
			self.assertRaises( RuntimeError, n["out"].getValue )

	def testTildeExpansion( self ) :

		n = self.inOutNode()

		n["in"].setValue( "~" )
		self.assertEqual( n["out"].getValue(), os.path.expanduser( "~" ) )

		n["in"].setValue( "~/something.tif" )
		self.assertEqual( n["out"].getValue(), os.path.expanduser( "~/something.tif" ) )

		# ~ shouldn't be expanded unless it's at the front - it would
		# be meaningless in other cases.
		n["in"].setValue( "in ~1900" )
		self.assertEqual( n["out"].getValue(), "in ~1900" )

	def testEnvironmentExpansion( self ) :

		n = self.inOutNode()

		n["in"].setValue( "${NOT_AN_ENVIRONMENT_VARIABLE}" )
		h1 = n["out"].hash()
		self.assertEqual( n["out"].getValue(), "" )

		n["in"].setValue( "${GAFFER_ROOT}" )
		self.assertEqual( n["out"].getValue(), os.environ["GAFFER_ROOT"] )
		h2 = n["out"].hash()
		self.assertNotEqual( h1, h2 )

		context = Gaffer.Context()
		context["GAFFER_ROOT"] = "b"
		with context :
			# context should win against environment
			self.assertEqual( n["out"].getValue(), "b" )
			self.assertNotEqual( n["out"].hash(), h1 )
			self.assertNotEqual( n["out"].hash(), h2 )

	def testDefaultValueExpansion( self ) :

		n = self.inOutNode( defaultValue = "${A}" )
		context = Gaffer.Context()
		context["A"] = "b"
		with context :
			self.assertEqual( n["out"].getValue(), "b" )

	def testExpansionFromInputConnection( self ) :

		p = Gaffer.StringPlug()
		p.setValue( "${foo}" )

		n = self.inOutNode()
		n["in"].setInput( p )

		c = Gaffer.Context()
		with c :
			self.assertEqual( n["out"].getValue(), "" )
			h = n["out"].hash()

		c["foo"] = "foo"
		with c :
			self.assertNotEqual( n["out"].hash(), h )
			self.assertEqual( n["out"].getValue(), "foo" )

	def testExpansionMask( self ) :

		n1 = self.inOutNode( substitutions = IECore.StringAlgo.Substitutions.AllSubstitutions )
		n2 = self.inOutNode( substitutions = IECore.StringAlgo.Substitutions.AllSubstitutions & ~IECore.StringAlgo.Substitutions.FrameSubstitutions )

		n1["in"].setValue( "hello.####.${ext}" )
		n2["in"].setValue( "hello.####.${ext}" )
		self.assertEqual( n1["out"].getValue(), os.path.expanduser( "hello.0001." ) )
		self.assertEqual( n2["out"].getValue(), os.path.expanduser( "hello.####." ) )

		c = Gaffer.Context()
		c["ext"] = "cob"
		c.setFrame( 10 )
		with c :
			self.assertEqual( n1["out"].getValue(), os.path.expanduser( "hello.0010.cob" ) )
			self.assertEqual( n2["out"].getValue(), os.path.expanduser( "hello.####.cob" ) )

	def testSubstitutionsSerialisation( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["p"] = Gaffer.StringPlug(
			"p",
			flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic,
			substitutions = IECore.StringAlgo.Substitutions.AllSubstitutions & ~IECore.StringAlgo.Substitutions.FrameSubstitutions
		)
		self.assertEqual( s["n"]["p"].substitutions(), IECore.StringAlgo.Substitutions.AllSubstitutions & ~IECore.StringAlgo.Substitutions.FrameSubstitutions )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )
		self.assertEqual( s["n"]["p"].substitutions(), s2["n"]["p"].substitutions() )

	def testLoadSubstitutionsVersion0_56( self ) :

		s = Gaffer.ScriptNode()
		s["fileName"].setValue( os.path.join( os.path.dirname( __file__ ), "scripts", "stringPlugSubstitutions-0.56.0.0.gfr" ) )
		s.load()

		self.assertEqual( s["n"]["user"]["p"].substitutions(), IECore.StringAlgo.Substitutions.AllSubstitutions & ~IECore.StringAlgo.Substitutions.FrameSubstitutions )

	def testLoadSubstitutionsVersion0_55( self ) :

		s = Gaffer.ScriptNode()
		s["fileName"].setValue( os.path.join( os.path.dirname( __file__ ), "scripts", "stringPlugSubstitutions-0.55.4.0.gfr" ) )
		s.load()

		self.assertEqual( s["n"]["user"]["p"].substitutions(), IECore.StringAlgo.Substitutions.AllSubstitutions & ~IECore.StringAlgo.Substitutions.FrameSubstitutions )

	def testSubstitutionsRepr( self ) :

		p = Gaffer.StringPlug(
			substitutions = IECore.StringAlgo.Substitutions.TildeSubstitutions | IECore.StringAlgo.Substitutions.FrameSubstitutions
		)

		p2 = eval( repr( p ) )
		self.assertEqual( p.substitutions(), p2.substitutions() )

	def testSubstitutionsCounterpart( self ) :

		p = Gaffer.StringPlug(
			substitutions = IECore.StringAlgo.Substitutions.TildeSubstitutions | IECore.StringAlgo.Substitutions.FrameSubstitutions
		)

		p2 = p.createCounterpart( "p2", p.Direction.In )
		self.assertEqual( p.substitutions(), p2.substitutions() )

	def testSubstitutionsFromExpressionInput( self ) :

		s = Gaffer.ScriptNode()

		# Should output a substituted version of the input.
		s["substitionsOn"] = self.inOutNode()

		# Should pass through the input directly, without substitutions.
		s["substitionsOff"] = self.inOutNode( substitutions = IECore.StringAlgo.Substitutions.NoSubstitutions )

		# The third case is trickier. The "in" plug on the node
		# itself requests no substitutions, but it receives its
		# input via an indirect connection with substitutions
		# turned on. We resolve this by defining substitutions
		# to occur only when observing a value inside a compute,
		# and to always be determined by the plug used to access
		# the value. A chain of connections can be thought of as
		# carrying an unsubstituted string all the way along
		# internally, with each plug along the way determining
		# the substitutions applied when peeking in to see the value
		# at that point.
		#
		# In practice this works best because typically it is only
		# nodes that know when a substitution is relevant, and the
		# user shouldn't be burdened with the job of thinking about
		# them when making intermediate connections to that node.
		s["substitionsOnIndirectly"] = self.inOutNode( substitutions = IECore.StringAlgo.Substitutions.NoSubstitutions )
		s["substitionsOnIndirectly"]["user"]["in"] = Gaffer.StringPlug()
		s["substitionsOnIndirectly"]["in"].setInput( s["substitionsOnIndirectly"]["user"]["in"] )

		# All three nodes above receive their input from this expression
		# which outputs a sequence value to be substituted (or not).

		s["e"] = Gaffer.Expression()
		s["e"].setExpression( inspect.cleandoc(
			"""
			parent["substitionsOn"]["in"] = "test.#.exr"
			parent["substitionsOff"]["in"] = "test.#.exr"
			parent["substitionsOnIndirectly"]["user"]["in"] = "test.#.exr"
			"""
		) )

		with Gaffer.Context() as c :

			# Frame 1
			#########

			c.setFrame( 1 )

			# The output of the expression itself is not substituted.
			# Substitutions occur only on input plugs.

			self.assertEqual( s["substitionsOn"]["in"].getInput().getValue(), "test.#.exr" )
			self.assertEqual( s["substitionsOff"]["in"].getInput().getValue(), "test.#.exr" )
			self.assertEqual( s["substitionsOnIndirectly"]["user"]["in"].getInput().getValue(), "test.#.exr" )

			# We should get frame numbers out of the substituting node.

			self.assertEqual( s["substitionsOn"]["out"].getValue(), "test.1.exr" )
			substitutionsOnHash1 = s["substitionsOn"]["out"].hash()
			self.assertEqual( s["substitionsOn"]["out"].getValue( _precomputedHash = substitutionsOnHash1 ), "test.1.exr" )

			# We should get sequences out of the non-substituting node.

			self.assertEqual( s["substitionsOff"]["out"].getValue(), "test.#.exr" )
			substitutionsOffHash1 = s["substitionsOff"]["out"].hash()
			self.assertEqual( s["substitionsOff"]["out"].getValue( _precomputedHash = substitutionsOffHash1 ), "test.#.exr" )
			self.assertNotEqual( substitutionsOnHash1, substitutionsOffHash1 )

			# We shouldn't get frame numbers out of the third node, because the
			# requirements of the node (no substitutions) trump any upstream opinions.
			# Substitutions are performed by the plug during value access, and do not
			# affect the actual data flow.

			self.assertEqual( s["substitionsOnIndirectly"]["out"].getValue(), "test.#.exr" )
			substitionsOnIndirectlyHash1 = s["substitionsOnIndirectly"]["out"].hash()
			self.assertEqual( s["substitionsOnIndirectly"]["out"].getValue( _precomputedHash = substitionsOnIndirectlyHash1 ), "test.#.exr" )

			# Frame 2
			#########

			c.setFrame( 2 )

			# The output of the expression itself is not substituted.
			# Substitutions occur only on input plugs.

			self.assertEqual( s["substitionsOn"]["in"].getInput().getValue(), "test.#.exr" )
			self.assertEqual( s["substitionsOff"]["in"].getInput().getValue(), "test.#.exr" )
			self.assertEqual( s["substitionsOnIndirectly"]["user"]["in"].getInput().getValue(), "test.#.exr" )

			# We should get frame numbers out of the substituting node.
			# The hash must has changed to make this possible.

			self.assertEqual( s["substitionsOn"]["out"].getValue(), "test.2.exr" )
			substitutionsOnHash2 = s["substitionsOn"]["out"].hash()
			self.assertEqual( s["substitionsOn"]["out"].getValue( _precomputedHash = substitutionsOnHash2 ), "test.2.exr" )
			self.assertNotEqual( substitutionsOnHash2, substitutionsOnHash1 )

			# We should still get sequences out of the non-substituting node,
			# and it should have the same output hash as it had on frame 1.

			self.assertEqual( s["substitionsOff"]["out"].getValue(), "test.#.exr" )
			substitutionsOffHash2 = s["substitionsOff"]["out"].hash()
			self.assertEqual( s["substitionsOff"]["out"].getValue( _precomputedHash = substitutionsOffHash2 ), "test.#.exr" )
			self.assertEqual( substitutionsOffHash1, substitutionsOffHash2 )
			self.assertNotEqual( substitutionsOnHash2, substitutionsOffHash2 )

			# The third node should still be non-substituting.

			self.assertEqual( s["substitionsOnIndirectly"]["out"].getValue(), "test.#.exr" )
			substitionsOnIndirectlyHash2 = s["substitionsOnIndirectly"]["out"].hash()
			self.assertEqual( s["substitionsOnIndirectly"]["out"].getValue( _precomputedHash = substitionsOnIndirectlyHash2 ), "test.#.exr" )
			self.assertEqual( substitionsOnIndirectlyHash2, substitionsOnIndirectlyHash1 )

	def testHashUsesValue( self ) :

		script = Gaffer.ScriptNode()
		script["node"] = self.inOutNode()

		script["expression"] = Gaffer.Expression()
		script["expression"].setExpression(
			"""parent["node"]["in"] = str( min( context.getFrame(), 10.0 ) )"""
		)

		hashes = {}
		with Gaffer.Context() as context :
			for i in range( 0, 20 ) :
				context.setFrame( i )
				hashes[i] = str( script["node"]["in"].hash() )

		self.assertEqual( len( set( hashes.values() ) ), 11 )
		for i in range( 10, 20 ) :
			self.assertEqual( hashes[i], hashes[10] )

	def testStringVectorDataInput( self ) :

		node = Gaffer.ComputeNode()
		node["user"]["string"] = Gaffer.StringPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		node["user"]["stringVector"] = Gaffer.StringVectorDataPlug( defaultValue = IECore.StringVectorData(), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		self.assertTrue( node["user"]["string"].acceptsInput( node["user"]["stringVector"] ) )
		node["user"]["string"].setInput( node["user"]["stringVector"] )

		hashes = set()
		for input, output in [
			( [], "", ),
			( [ "test" ], "test" ),
			( [ "a", "b", "c" ], "a b c" ),
			( [ "dog", "cat" ], "dog cat" ),
			( [ "a", "b", "", "c" ], "a b  c" ),
		] :

			node["user"]["stringVector"].setValue( IECore.StringVectorData( input ) )

			h = node["user"]["string"].hash()
			self.assertNotIn( h, hashes )
			hashes.add( h )

			self.assertEqual( node["user"]["string"].getValue(), output )

	def testStringVectorDataConversionCachedOnce( self ) :

		# StringVectorDataPlug driving StringPlug, with a variable
		# substitution in the value.

		node = Gaffer.ComputeNode()
		node["user"]["string"] = Gaffer.StringPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		node["user"]["stringVector"] = Gaffer.StringVectorDataPlug( defaultValue = IECore.StringVectorData( [ "${test}" ] ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		node["user"]["string"].setInput( node["user"]["stringVector"] )

		# The conversion from StringVectorData to StringData is performed once and
		# cached. It doesn't depend on the context because the variable substitutions
		# are performed later in `StringPlug.getValue()`. Assert this by checking that
		# cache memory usage doesn't grow after the first call.
		cacheUsage = None
		hashes = set()
		with Gaffer.Context() as context :
			for v in [ "cat", "dog", "fish" ] :
				context["test"] = v
				node["user"]["string"].getValue()
				if cacheUsage is None :
					cacheUsage = Gaffer.ValuePlug.cacheMemoryUsage()
				else :
					self.assertEqual( Gaffer.ValuePlug.cacheMemoryUsage(), cacheUsage )
				hashes.add( node["user"]["string"].hash() )

		# We do expect a different result from `StringPlug.hash()` for each context though,
		# because the hash accounts for the substitutions.
		self.assertEqual( len( hashes ), 3 )

if __name__ == "__main__":
	unittest.main()
