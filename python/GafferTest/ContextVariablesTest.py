##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
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
import inspect

import IECore

import Gaffer
import GafferTest

class ContextVariablesTest( GafferTest.TestCase ) :

	def test( self ) :

		n = GafferTest.StringInOutNode()
		self.assertHashesValid( n )

		c = Gaffer.ContextVariables()
		c.setup( Gaffer.StringPlug() )
		c["in"].setInput( n["out"] )

		n["in"].setValue( "$a" )
		self.assertEqual( c["out"].getValue(), "" )

		c["variables"].addChild( Gaffer.NameValuePlug( "a", IECore.StringData( "A" ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		self.assertEqual( c["out"].getValue(), "A" )

	def testDirtyPropagation( self ) :

		n = GafferTest.StringInOutNode()

		c = Gaffer.ContextVariables()
		c.setup( Gaffer.StringPlug() )
		c["in"].setInput( n["out"] )

		# adding a variable should dirty the output:
		dirtied = GafferTest.CapturingSlot( c.plugDirtiedSignal() )
		c["variables"].addChild( Gaffer.NameValuePlug( "a", IECore.StringData( "A" ), "member1", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		self.assertIn( c["out"], [ p[0] for p in dirtied ] )

		# modifying the variable should dirty the output:
		dirtied = GafferTest.CapturingSlot( c.plugDirtiedSignal() )
		c["variables"]["member1"]["value"].setValue("b")
		self.assertIn( c["out"], [ p[0] for p in dirtied ] )

		# removing the variable should also dirty the output:
		dirtied = GafferTest.CapturingSlot( c.plugDirtiedSignal() )
		c["variables"].removeChild(c["variables"]["member1"])
		self.assertIn( c["out"], [ p[0] for p in dirtied ] )

	def testSerialisation( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.StringInOutNode()

		s["c"] = Gaffer.ContextVariables()
		s["c"].setup( Gaffer.StringPlug() )
		s["c"]["in"].setInput( s["n"]["out"] )

		s["n"]["in"].setValue( "$a" )
		self.assertEqual( s["c"]["out"].getValue(), "" )

		s["c"]["variables"].addChild( Gaffer.NameValuePlug( "a", IECore.StringData( "A" ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		self.assertEqual( s["c"]["out"].getValue(), "A" )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( s2["c"].keys(), s["c"].keys() )
		self.assertEqual( s2["c"]["out"].getValue(), "A" )

	def testExtraVariables( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.StringInOutNode()

		s["c"] = Gaffer.ContextVariables()
		s["c"].setup( Gaffer.StringPlug() )
		s["c"]["in"].setInput( s["n"]["out"] )

		s["n"]["in"].setValue( "$a" )
		self.assertEqual( s["c"]["out"].getValue(), "" )

		dirtied = GafferTest.CapturingSlot( s["c"].plugDirtiedSignal() )
		s["c"]["extraVariables"].setValue( IECore.CompoundData( { "a" : "A" } ) )
		self.assertIn( s["c"]["out"], { p[0] for p in dirtied } )
		self.assertEqual( s["c"]["out"].getValue(), "A" )

		# Extra variables trump regular variables of the same name
		s["c"]["variables"].addChild( Gaffer.NameValuePlug( "a", IECore.StringData( "B" ) ) )
		self.assertEqual( s["c"]["out"].getValue(), "A" )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( s2["c"]["out"].getValue(), "A" )

	def testExtraVariablesExpression( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.StringInOutNode()

		s["c"] = Gaffer.ContextVariables()
		s["c"].setup( Gaffer.StringPlug() )
		s["c"]["in"].setInput( s["n"]["out"] )

		s["n"]["in"].setValue( "$a$b$c" )
		self.assertEqual( s["c"]["out"].getValue(), "" )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression( inspect.cleandoc(
			"""
			result = IECore.CompoundData()

			if context.getFrame() > 1 :
				result["a"] = "A"
			if context.getFrame() > 2 :
				result["b"] = "B"
			if context.getFrame() > 3 :
				result["c"] = "C"

			parent["c"]["extraVariables"] = result
			"""
		) )

		with Gaffer.Context() as c :

			self.assertEqual( s["c"]["out"].getValue(), "" )

			c.setFrame( 2 )
			self.assertEqual( s["c"]["out"].getValue(), "A" )

			c.setFrame( 3 )
			self.assertEqual( s["c"]["out"].getValue(), "AB" )

			c.setFrame( 4 )
			self.assertEqual( s["c"]["out"].getValue(), "ABC" )

	def testEnabledPlugAffectsOutput( self ) :

		c = Gaffer.ContextVariables()
		c.setup( Gaffer.StringPlug() )

		cs = GafferTest.CapturingSlot( c.plugDirtiedSignal() )
		c["enabled"].setValue( False )

		self.assertEqual( len( cs ), 2 )
		self.assertEqual( { x[0] for x in cs }, { c["enabled"], c["out"] } )

	def testSerialisationUsesSetup( self ) :

		s1 = Gaffer.ScriptNode()
		s1["c"] = Gaffer.ContextVariables()
		s1["c"].setup( Gaffer.IntPlug() )

		ss = s1.serialise()
		self.assertIn( "setup", ss )
		self.assertEqual( ss.count( "addChild" ), 1 )
		self.assertNotIn( "Dynamic", ss )
		self.assertNotIn( "setInput", ss )

		s2 = Gaffer.ScriptNode()
		s2.execute( ss )
		self.assertIn( "in", s2["c"] )
		self.assertIn( "out", s2["c"] )
		self.assertIsInstance( s2["c"]["in"], Gaffer.IntPlug )
		self.assertIsInstance( s2["c"]["out"], Gaffer.IntPlug )

if __name__ == "__main__":
	unittest.main()
