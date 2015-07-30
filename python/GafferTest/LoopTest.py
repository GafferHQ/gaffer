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

		result = Gaffer.LoopComputeNode()
		result["out"] = Gaffer.IntPlug( direction = Gaffer.Plug.Direction.Out, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic  )
		result["in"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

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

if __name__ == "__main__":
	unittest.main()
