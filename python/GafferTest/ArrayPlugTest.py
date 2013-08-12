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

class ArrayPlugTest( unittest.TestCase ) :
		
	def test( self ) :

		a = GafferTest.AddNode()
		n = GafferTest.ArrayPlugNode()
		
		self.assertTrue( "e1" in n["in"] )
		self.assertTrue( "e2" not in n["in"] )
		self.assertEqual( len( n["in"] ), 1 )
		self.assertTrue( n["in"]["e1"].isSame( n["in"][0] ) )

		n["in"][0].setInput( a["sum"] )

		self.assertEqual( len( n["in"] ), 2 )
		self.assertTrue( "e1" in n["in"] )
		self.assertTrue( "e2" in n["in"] )
		
		n["in"][0].setInput( None )
		self.assertTrue( "e1" in n["in"] )
		self.assertTrue( "e2" not in n["in"] )
		self.assertEqual( len( n["in"] ), 1 )
	
	def testConnectionGaps( self ) :
	
		a = GafferTest.AddNode()
		n = GafferTest.ArrayPlugNode()
		
		n["in"][0].setInput( a["sum"] )
		n["in"][1].setInput( a["sum"] )
		n["in"][2].setInput( a["sum"] )
		
		self.assertEqual( len( n["in"] ), 4 )
		
		self.assertTrue( n["in"]["e1"].getInput(), a["sum"] )
		self.assertTrue( n["in"]["e2"].getInput(), a["sum"] )
		self.assertTrue( n["in"]["e3"].getInput(), a["sum"] )
		self.assertTrue( n["in"]["e4"].getInput() is None )
		
		n["in"][1].setInput( None )
		
		self.assertEqual( len( n["in"] ), 4 )
		
		self.assertTrue( n["in"]["e1"].getInput(), a["sum"] )
		self.assertTrue( n["in"]["e2"].getInput() is None )
		self.assertTrue( n["in"]["e3"].getInput(), a["sum"] )
		self.assertTrue( n["in"]["e4"].getInput() is None )
	
	def testSerialisation( self ) :
	
		s = Gaffer.ScriptNode()
		s["a"] = GafferTest.AddNode()
		s["n"] = GafferTest.ArrayPlugNode()
		
		s["n"]["in"][0].setInput( s["a"]["sum"] )
		s["n"]["in"][1].setInput( s["a"]["sum"] )
		s["n"]["in"][2].setInput( s["a"]["sum"] )
		s["n"]["in"][1].setInput( None )
		
		self.assertEqual( len( s["n"]["in"] ), 4 )
		self.assertTrue( s["n"]["in"]["e1"].isSame( s["n"]["in"][0] ) )
		self.assertTrue( s["n"]["in"]["e2"].isSame( s["n"]["in"][1] ) )
		self.assertTrue( s["n"]["in"]["e3"].isSame( s["n"]["in"][2] ) )
		self.assertTrue( s["n"]["in"]["e4"].isSame( s["n"]["in"][3] ) )
		
		self.assertTrue( s["n"]["in"]["e1"].getInput(), s["a"]["sum"] )
		self.assertTrue( s["n"]["in"]["e2"].getInput() is None )
		self.assertTrue( s["n"]["in"]["e3"].getInput(), s["a"]["sum"] )
		self.assertTrue( s["n"]["in"]["e4"].getInput() is None )
				
		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )
		
	def testMaximumInputs( self ) :
	
		a = GafferTest.AddNode()
		n = GafferTest.ArrayPlugNode()

		# connect all inputs

		for i in range( 0, 6 ) :
			n["in"][i].setInput( a["sum"] )
				
		self.assertEqual( len( n["in"] ), 6 )
		for i in range( 0, 6 ) :
			self.assertTrue( n["in"][i].getInput().isSame( a["sum"] ) )
		
		# check that removing the one before the last
		# leaves the last in place.
		
		n["in"][4].setInput( None )
		self.assertEqual( len( n["in"] ), 6 )
		for i in range( 0, 6 ) :
			if i != 4 :
				self.assertTrue( n["in"][i].getInput().isSame( a["sum"] ) )
			else :
				self.assertTrue( n["in"][i].getInput() is None )
				
	def testMakeConnectionAndUndoAndRedo( self ) :
	
		s = Gaffer.ScriptNode()
		s["a"] = GafferTest.AddNode()
		s["n"] = GafferTest.ArrayPlugNode()
						
		with Gaffer.UndoContext( s ) :
			s["n"]["in"][0].setInput( s["a"]["sum"] )
		
		self.assertEqual( len( s["n"]["in"] ), 2 )
		self.assertTrue( s["n"]["in"][0].isSame( s["n"]["in"]["e1"] ) )
		self.assertTrue( s["n"]["in"][1].isSame( s["n"]["in"]["e2"] ) )
		
		s.undo()
		
		self.assertEqual( len( s["n"]["in"] ), 1 )		
		self.assertTrue( s["n"]["in"][0].isSame( s["n"]["in"]["e1"] ) )
		
		s.redo()
		
		self.assertEqual( len( s["n"]["in"] ), 2 )		
		self.assertTrue( s["n"]["in"][0].isSame( s["n"]["in"]["e1"] ) )
		self.assertTrue( s["n"]["in"][1].isSame( s["n"]["in"]["e2"] ) )
		
		s.undo()
		
		self.assertEqual( len( s["n"]["in"] ), 1 )		
		self.assertTrue( s["n"]["in"][0].isSame( s["n"]["in"]["e1"] ) )
		self.assertTrue( "in" in s["n"] )
		self.assertFalse( "in1" in s["n"] )
	
	def testMinimumInputs( self ) :
	
		a = GafferTest.AddNode()
		n = Gaffer.Node()
		n["in"] = Gaffer.ArrayPlug( "in", element = Gaffer.IntPlug( "e1" ), minSize=3 )
		
		self.assertEqual( len( n["in"] ), 3 )
		
		# connecting to the middle input shouldn't create
		# any new inputs, because there is still one free on the end
		n["in"]["e2"].setInput( a["sum"] )
		self.assertEqual( len( n["in"] ), 3 )

		# connecting to the last input should create a new
		# one - there should always be one free input on the
		# end (until the maximum is reached).
		n["in"]["e3"].setInput( a["sum"] )
		
		self.assertEqual( len( n["in"] ), 4 )
		
		n["in"]["e3"].setInput( None )
		
		self.assertEqual( len( n["in"] ), 3 )		
	
	def testDeleteAndUndoAndRedo( self ) :
	
		s = Gaffer.ScriptNode()
		s["a"] = GafferTest.AddNode()
		s["n"] = GafferTest.ArrayPlugNode()
		
		s["n"]["in"]["e1"].setInput( s["a"]["sum"] )
		s["n"]["in"]["e2"].setInput( s["a"]["sum"] )
		s["n"]["in"]["e3"].setInput( s["a"]["sum"] )
		
		self.assertEqual( len( s["n"]["in"] ), 4 )
		self.assertTrue( s["n"]["in"]["e1"].getInput().isSame( s["a"]["sum"] ) )
		self.assertTrue( s["n"]["in"]["e2"].getInput().isSame( s["a"]["sum"] ) )
		self.assertTrue( s["n"]["in"]["e3"].getInput().isSame( s["a"]["sum"] ) )
		
		with Gaffer.UndoContext( s ) :
			s.deleteNodes( s, Gaffer.StandardSet( [ s["n"] ] ) )
		
		self.assertFalse( "n" in s )
		
		s.undo()
		
		self.assertEqual( len( s["n"]["in"] ), 4 )
		self.assertTrue( s["n"]["in"]["e1"].getInput().isSame( s["a"]["sum"] ) )
		self.assertTrue( s["n"]["in"]["e2"].getInput().isSame( s["a"]["sum"] ) )
		self.assertTrue( s["n"]["in"]["e3"].getInput().isSame( s["a"]["sum"] ) )
		
		s.redo()
		
		self.assertFalse( "n" in s )

		s.undo()
		
		self.assertEqual( len( s["n"]["in"] ), 4 )
		self.assertTrue( s["n"]["in"]["e1"].getInput().isSame( s["a"]["sum"] ) )
		self.assertTrue( s["n"]["in"]["e2"].getInput().isSame( s["a"]["sum"] ) )
		self.assertTrue( s["n"]["in"]["e3"].getInput().isSame( s["a"]["sum"] ) )
	
	def testDeleteInputNodeAndUndoAndRedo( self ) :
	
		s = Gaffer.ScriptNode()
		s["a"] = GafferTest.AddNode()
		s["n"] = GafferTest.ArrayPlugNode()
		
		s["n"]["in"][0].setInput( s["a"]["sum"] )
		s["n"]["in"][1].setInput( s["a"]["sum"] )
		s["n"]["in"][2].setInput( s["a"]["sum"] )
		
		n = s["n"]
		
		self.assertEqual( len( s["n"]["in"] ), 4 )
		self.assertTrue( s["n"]["in"][0].getInput().isSame( s["a"]["sum"] ) )
		self.assertTrue( s["n"]["in"][1].getInput().isSame( s["a"]["sum"] ) )
		self.assertTrue( s["n"]["in"][2].getInput().isSame( s["a"]["sum"] ) )
		
		with Gaffer.UndoContext( s ) :
			s.deleteNodes( s, Gaffer.StandardSet( [ s["a"] ] ) )
		
		self.assertFalse( "a" in s )
		
		s.undo()
				
		self.assertEqual( len( s["n"]["in"] ), 4 )
		self.assertTrue( s["n"]["in"][0].getInput().isSame( s["a"]["sum"] ) )
		self.assertTrue( s["n"]["in"][1].getInput().isSame( s["a"]["sum"] ) )
		self.assertTrue( s["n"]["in"][2].getInput().isSame( s["a"]["sum"] ) )
		
		s.redo()
		
		self.assertFalse( "a" in s )

		s.undo()
		
		self.assertEqual( len( s["n"]["in"] ), 4 )
		self.assertTrue( s["n"]["in"][0].getInput().isSame( s["a"]["sum"] ) )
		self.assertTrue( s["n"]["in"][1].getInput().isSame( s["a"]["sum"] ) )
		self.assertTrue( s["n"]["in"][2].getInput().isSame( s["a"]["sum"] ) )
	
	def testFixedLengthDynamic( self ) :
	
		s = Gaffer.ScriptNode()
		
		s["a"] = GafferTest.AddNode()
		s["n"] = Gaffer.Node()
		s["n"]["a"] = Gaffer.ArrayPlug( "a", element = Gaffer.IntPlug(), minSize = 4, maxSize = 4, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["a"][1].setInput( s["a"]["sum"] )
		s["n"]["a"][2].setInput( s["a"]["sum"] )
		
		self.assertEqual( s["n"]["a"].minSize(), 4 )
		self.assertEqual( s["n"]["a"].maxSize(), 4 )
		self.assertEqual( len( s["n"]["a"] ), 4 )
		self.assertTrue( s["n"]["a"][0].getInput() is None )
		self.assertTrue( s["n"]["a"][1].getInput().isSame( s["a"]["sum"] ) )
		self.assertTrue( s["n"]["a"][1].getInput().isSame( s["a"]["sum"] ) )
		self.assertTrue( s["n"]["a"][3].getInput() is None )
				
		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )
		
		self.assertEqual( s2["n"]["a"].minSize(), 4 )
		self.assertEqual( s2["n"]["a"].maxSize(), 4 )
		self.assertEqual( len( s2["n"]["a"] ), 4 )
		self.assertTrue( s2["n"]["a"][0].getInput() is None )
		self.assertTrue( s2["n"]["a"][1].getInput().isSame( s2["a"]["sum"] ) )
		self.assertTrue( s2["n"]["a"][1].getInput().isSame( s2["a"]["sum"] ) )
		self.assertTrue( s2["n"]["a"][3].getInput() is None )
		
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
