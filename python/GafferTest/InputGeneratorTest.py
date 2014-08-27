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

import unittest
import gc

import IECore

import Gaffer
import GafferTest

class InputGeneratorTest( GafferTest.TestCase ) :

	def test( self ) :

		a = GafferTest.AddNode()
		n = GafferTest.InputGeneratorNode()

		self.assertTrue( "in" in n )
		self.assertTrue( "in1" not in n )
		self.assertEqual( len( n.inputs ), 1 )
		self.assertTrue( n["in"].isSame( n.inputs[0] ) )

		n.inputs[0].setInput( a["sum"] )

		self.assertEqual( len( n.inputs ), 2 )
		self.assertTrue( "in" in n )
		self.assertTrue( "in1" in n )
		self.assertTrue( n["in"].isSame( n.inputs[0] ) )
		self.assertTrue( n["in1"].isSame( n.inputs[1] ) )
		self.assertTrue( n["in"].getInput().isSame( a["sum"] ) )
		self.assertEqual( n["in1"].getInput(), None )

		n.inputs[0].setInput( None )
		self.assertTrue( "in" in n )
		self.assertTrue( "in1" not in n )
		self.assertEqual( len( n.inputs ), 1 )
		self.assertTrue( n["in"].isSame( n.inputs[0] ) )

	def testConnectionGaps( self ) :

		a = GafferTest.AddNode()
		n = GafferTest.InputGeneratorNode()

		n.inputs[0].setInput( a["sum"] )
		n.inputs[1].setInput( a["sum"] )
		n.inputs[2].setInput( a["sum"] )

		self.assertEqual( len( n.inputs ), 4 )
		self.assertTrue( n["in"].isSame( n.inputs[0] ) )
		self.assertTrue( n["in1"].isSame( n.inputs[1] ) )
		self.assertTrue( n["in2"].isSame( n.inputs[2] ) )
		self.assertTrue( n["in3"].isSame( n.inputs[3] ) )

		self.assertTrue( n["in"].getInput(), a["sum"] )
		self.assertTrue( n["in1"].getInput(), a["sum"] )
		self.assertTrue( n["in2"].getInput(), a["sum"] )
		self.assertTrue( n["in3"].getInput() is None )

		n.inputs[1].setInput( None )

		self.assertEqual( len( n.inputs ), 4 )
		self.assertTrue( n["in"].isSame( n.inputs[0] ) )
		self.assertTrue( n["in1"].isSame( n.inputs[1] ) )
		self.assertTrue( n["in2"].isSame( n.inputs[2] ) )
		self.assertTrue( n["in3"].isSame( n.inputs[3] ) )

		self.assertTrue( n["in"].getInput(), a["sum"] )
		self.assertTrue( n["in1"].getInput() is None )
		self.assertTrue( n["in2"].getInput(), a["sum"] )
		self.assertTrue( n["in3"].getInput() is None )

	def testSerialisation( self ) :

		s = Gaffer.ScriptNode()
		s["a"] = GafferTest.AddNode()
		s["n"] = GafferTest.InputGeneratorNode()

		s["n"].inputs[0].setInput( s["a"]["sum"] )
		s["n"].inputs[1].setInput( s["a"]["sum"] )
		s["n"].inputs[2].setInput( s["a"]["sum"] )
		s["n"].inputs[1].setInput( None )

		self.assertEqual( len( s["n"].inputs ), 4 )
		self.assertTrue( s["n"]["in"].isSame( s["n"].inputs[0] ) )
		self.assertTrue( s["n"]["in1"].isSame( s["n"].inputs[1] ) )
		self.assertTrue( s["n"]["in2"].isSame( s["n"].inputs[2] ) )
		self.assertTrue( s["n"]["in3"].isSame( s["n"].inputs[3] ) )

		self.assertTrue( s["n"]["in"].getInput(), s["a"]["sum"] )
		self.assertTrue( s["n"]["in1"].getInput() is None )
		self.assertTrue( s["n"]["in2"].getInput(), s["a"]["sum"] )
		self.assertTrue( s["n"]["in3"].getInput() is None )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

	def testMaximumInputs( self ) :

		a = GafferTest.AddNode()
		n = GafferTest.InputGeneratorNode()

		# connect all inputs

		for i in range( 0, 6 ) :
			n.inputs[i].setInput( a["sum"] )

		self.assertEqual( len( n.inputs ), 6 )
		for i in range( 0, 6 ) :
			self.assertTrue( n.inputs[i].getInput().isSame( a["sum"] ) )

		# check that removing the one before the last
		# leaves the last in place.

		n.inputs[4].setInput( None )
		self.assertEqual( len( n.inputs ), 6 )
		for i in range( 0, 6 ) :
			if i != 4 :
				self.assertTrue( n.inputs[i].getInput().isSame( a["sum"] ) )
			else :
				self.assertTrue( n.inputs[i].getInput() is None )

	def testMakeConnectionAndUndoAndRedo( self ) :

		s = Gaffer.ScriptNode()
		s["a"] = GafferTest.AddNode()
		s["n"] = GafferTest.InputGeneratorNode()

		s["n"]["__customPlug"] = Gaffer.V2fPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		self.assertTrue( "__customPlug" in s["n"] )

		with Gaffer.UndoContext( s ) :
			s["n"]["in"].setInput( s["a"]["sum"] )


		self.assertEqual( len( s["n"].inputs ), 2 )
		self.assertTrue( s["n"].inputs[0].isSame( s["n"]["in"] ) )
		self.assertTrue( s["n"].inputs[1].isSame( s["n"]["in1"] ) )
		self.assertTrue( "in" in s["n"] )
		self.assertTrue( "in1" in s["n"] )
		self.assertTrue( "__customPlug" in s["n"] )

		s.undo()

		self.assertEqual( len( s["n"].inputs ), 1 )
		self.assertTrue( s["n"].inputs[0].isSame( s["n"]["in"] ) )
		self.assertTrue( "in" in s["n"] )
		self.assertFalse( "in1" in s["n"] )
		self.assertTrue( "__customPlug" in s["n"] )

		s.redo()

		self.assertEqual( len( s["n"].inputs ), 2 )
		self.assertTrue( s["n"].inputs[0].isSame( s["n"]["in"] ) )
		self.assertTrue( s["n"].inputs[1].isSame( s["n"]["in1"] ) )
		self.assertTrue( "in" in s["n"] )
		self.assertTrue( "in1" in s["n"] )
		self.assertTrue( "__customPlug" in s["n"] )

		s.undo()

		self.assertEqual( len( s["n"].inputs ), 1 )
		self.assertTrue( s["n"].inputs[0].isSame( s["n"]["in"] ) )
		self.assertTrue( "in" in s["n"] )
		self.assertFalse( "in1" in s["n"] )
		self.assertTrue( "__customPlug" in s["n"] )

	def testMinimumInputs( self ) :

		a = GafferTest.AddNode()
		n = Gaffer.Node()
		g = Gaffer.Behaviours.InputGenerator( n, Gaffer.IntPlug( "in" ), minInputs=3 )

		self.assertEqual( len( g ), 3 )

		# connecting to the middle input shouldn't create
		# any new inputs, because there is still one free on the end
		n["in1"].setInput( a["sum"] )
		self.assertEqual( len( g ), 3 )

		# connecting to the last input should create a new
		# one - there should always be one free input on the
		# end (until the maximum is reached).
		n["in2"].setInput( a["sum"] )

		self.assertEqual( len( g ), 4 )

		n["in2"].setInput( None )

		self.assertEqual( len( g ), 3 )

	def testDeleteAndUndoAndRedo( self ) :

		s = Gaffer.ScriptNode()
		s["a"] = GafferTest.AddNode()
		s["n"] = GafferTest.InputGeneratorNode()

		s["n"]["in"].setInput( s["a"]["sum"] )
		s["n"]["in1"].setInput( s["a"]["sum"] )
		s["n"]["in2"].setInput( s["a"]["sum"] )

		self.assertEqual( len( s["n"].inputs ), 4 )
		self.assertTrue( s["n"]["in"].getInput().isSame( s["a"]["sum"] ) )
		self.assertTrue( s["n"]["in1"].getInput().isSame( s["a"]["sum"] ) )
		self.assertTrue( s["n"]["in2"].getInput().isSame( s["a"]["sum"] ) )

		with Gaffer.UndoContext( s ) :
			s.deleteNodes( s, Gaffer.StandardSet( [ s["n"] ] ) )

		self.assertFalse( "n" in s )

		s.undo()

		self.assertEqual( len( s["n"].inputs ), 4 )
		self.assertTrue( s["n"]["in"].getInput().isSame( s["a"]["sum"] ) )
		self.assertTrue( s["n"]["in1"].getInput().isSame( s["a"]["sum"] ) )
		self.assertTrue( s["n"]["in2"].getInput().isSame( s["a"]["sum"] ) )

		s.redo()

		self.assertFalse( "n" in s )

		s.undo()

		self.assertEqual( len( s["n"].inputs ), 4 )
		self.assertTrue( s["n"]["in"].getInput().isSame( s["a"]["sum"] ) )
		self.assertTrue( s["n"]["in1"].getInput().isSame( s["a"]["sum"] ) )
		self.assertTrue( s["n"]["in2"].getInput().isSame( s["a"]["sum"] ) )

	def testDeleteInputNodeAndUndoAndRedo( self ) :

		s = Gaffer.ScriptNode()
		s["a"] = GafferTest.AddNode()
		s["n"] = GafferTest.InputGeneratorNode()

		s["n"]["in"].setInput( s["a"]["sum"] )
		s["n"]["in1"].setInput( s["a"]["sum"] )
		s["n"]["in2"].setInput( s["a"]["sum"] )

		n = s["n"]

		self.assertEqual( len( s["n"].inputs ), 4 )
		self.assertTrue( s["n"]["in"].getInput().isSame( s["a"]["sum"] ) )
		self.assertTrue( s["n"]["in1"].getInput().isSame( s["a"]["sum"] ) )
		self.assertTrue( s["n"]["in2"].getInput().isSame( s["a"]["sum"] ) )

		with Gaffer.UndoContext( s ) :
			s.deleteNodes( s, Gaffer.StandardSet( [ s["a"] ] ) )

		self.assertFalse( "a" in s )

		s.undo()

		self.assertEqual( len( s["n"].inputs ), 4 )
		self.assertTrue( s["n"]["in"].getInput().isSame( s["a"]["sum"] ) )
		self.assertTrue( s["n"]["in1"].getInput().isSame( s["a"]["sum"] ) )
		self.assertTrue( s["n"]["in2"].getInput().isSame( s["a"]["sum"] ) )

		s.redo()

		self.assertFalse( "a" in s )

		s.undo()

		self.assertEqual( len( s["n"].inputs ), 4 )
		self.assertTrue( s["n"]["in"].getInput().isSame( s["a"]["sum"] ) )
		self.assertTrue( s["n"]["in1"].getInput().isSame( s["a"]["sum"] ) )
		self.assertTrue( s["n"]["in2"].getInput().isSame( s["a"]["sum"] ) )

	def testCompoundPlugParent( self ) :

		n = Gaffer.Node()
		n["p"] = Gaffer.CompoundPlug()

		g = Gaffer.Behaviours.InputGenerator( n["p"], Gaffer.IntPlug( "in" ) )

		self.assertEqual( len( g ), 1 )
		self.assertTrue( isinstance( n["p"][0], Gaffer.IntPlug ) )

		a = GafferTest.AddNode()
		n["p"]["in"].setInput( a["sum"] )

		self.assertEqual( len( g ), 2 )
		self.assertTrue( isinstance( n["p"][0], Gaffer.IntPlug ) )
		self.assertTrue( isinstance( n["p"][1], Gaffer.IntPlug ) )
		self.assertTrue( n["p"][0].getInput().isSame( a["sum"] ) )
		self.assertTrue( n["p"][1].getInput() is None )

		n["p"][0].setInput( None )
		self.assertEqual( len( g ), 1 )
		self.assertTrue( isinstance( n["p"][0], Gaffer.IntPlug ) )
		self.assertTrue( n["p"][0].getInput() is None )

	def testPrototypeWithSuffix( self ) :

		n = Gaffer.Node()
		n["in1"] = Gaffer.IntPlug()

		g = Gaffer.Behaviours.InputGenerator( n, n["in1"] )

		self.assertEqual( len( g ), 1 )
		self.assertEqual( g[0].getName(), "in1" )
		self.assertTrue( g[0].isSame( n["in1"] ) )
		self.assertTrue( g[0].getInput() is None )

		a = GafferTest.AddNode()

		n["in1"].setInput( a["sum"] )

		self.assertEqual( len( g ), 2 )
		self.assertEqual( g[0].getName(), "in1" )
		self.assertTrue( g[0].isSame( n["in1"] ) )
		self.assertTrue( g[0].getInput().isSame( a["sum"] ) )
		self.assertEqual( g[1].getName(), "in2" )
		self.assertTrue( g[1].isSame( n["in2"] ) )
		self.assertTrue( g[1].getInput() is None )

		n["in2"].setInput( a["sum"] )

		self.assertEqual( len( g ), 3 )
		self.assertEqual( g[0].getName(), "in1" )
		self.assertTrue( g[0].isSame( n["in1"] ) )
		self.assertTrue( g[0].getInput().isSame( a["sum"] ) )
		self.assertEqual( g[1].getName(), "in2" )
		self.assertTrue( g[1].isSame( n["in2"] ) )
		self.assertTrue( g[1].getInput().isSame( a["sum"] ) )
		self.assertEqual( g[2].getName(), "in3" )
		self.assertTrue( g[2].isSame( n["in3"] ) )
		self.assertTrue( g[2].getInput() is None )

		n["in2"].setInput( None )

		self.assertEqual( len( g ), 2 )
		self.assertEqual( g[0].getName(), "in1" )
		self.assertTrue( g[0].isSame( n["in1"] ) )
		self.assertTrue( g[0].getInput().isSame( a["sum"] ) )
		self.assertEqual( g[1].getName(), "in2" )
		self.assertTrue( g[1].isSame( n["in2"] ) )
		self.assertTrue( g[1].getInput() is None )

		n["in1"].setInput( None )

		self.assertEqual( len( g ), 1 )
		self.assertEqual( g[0].getName(), "in1" )
		self.assertTrue( g[0].isSame( n["in1"] ) )
		self.assertTrue( g[0].getInput() is None )

	def tearDown( self ) :

		# some bugs in the InputGenerator only showed themselves when
		# the ScriptNode was deleted during garbage collection, often
		# in totally unrelated tests. so we run the garbage collector
		# here to localise any problems to this test, making them
		# easier to diagnose and fix.

		while gc.collect() :
			pass
		IECore.RefCounted.collectGarbage()

if __name__ == "__main__":
	unittest.main()
