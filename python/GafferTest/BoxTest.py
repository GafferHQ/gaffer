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

import IECore

import Gaffer
import GafferTest

class BoxTest( unittest.TestCase ) :
		
	def testSerialisation( self ) :
	
		s = Gaffer.ScriptNode()
		
		s["b"] = Gaffer.Box()
		s["b"]["n1"] = GafferTest.AddNode()
		s["b"]["n2"] = GafferTest.AddNode()
		s["b"]["n2"]["op1"].setInput( s["b"]["n1"]["sum"] )
		
		s2 = Gaffer.ScriptNode()		
		s2.execute( s.serialise() )

		self.assert_( s2["b"]["n2"]["op1"].getInput().isSame( s2["b"]["n1"]["sum"] ) )
	
	def testCreate( self ) :
	
		s = Gaffer.ScriptNode()
		
		s["n1"] = GafferTest.AddNode()
		s["n2"] = GafferTest.AddNode()
		s["n3"] = GafferTest.AddNode()
		s["n4"] = GafferTest.AddNode()
		
		s["n2"]["op1"].setInput( s["n1"]["sum"] )
		s["n2"]["op2"].setInput( s["n1"]["sum"] )
		
		s["n3"]["op1"].setInput( s["n2"]["sum"] )
		
		s["n4"]["op1"].setInput( s["n3"]["sum"] )
		s["n4"]["op2"].setInput( s["n3"]["sum"] )
		
		def assertPreConditions() :
		
			self.assertTrue( "Box" not in s )
			
			self.assertTrue( s["n2"]["op1"].getInput().isSame( s["n1"]["sum"] ) )
			self.assertTrue( s["n2"]["op2"].getInput().isSame( s["n1"]["sum"] ) )
		
			self.assertTrue( s["n3"]["op1"].getInput().isSame( s["n2"]["sum"] ) )
			
			self.assertTrue( s["n4"]["op1"].getInput().isSame( s["n3"]["sum"] ) )
			self.assertTrue( s["n4"]["op2"].getInput().isSame( s["n3"]["sum"] ) )
		
		assertPreConditions()
			
		with Gaffer.UndoContext( s ) :
			b = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["n2"], s["n3"] ] ) )
		
		def assertPostConditions() :
		
			self.assertTrue( isinstance( b, Gaffer.Box ) )
			self.assertTrue( b.parent().isSame( s ) )

			self.assertTrue( "n2" not in s )
			self.assertTrue( "n3" not in s )

			self.assertTrue( "n2" in b )
			self.assertTrue( "n3" in b )

			self.assertTrue( b["n3"]["op1"].getInput().isSame( b["n2"]["sum"] ) )

			self.assertTrue( b["n2"]["op1"].getInput().node().isSame( b ) )
			self.assertTrue( b["n2"]["op2"].getInput().node().isSame( b ) )

			self.assertTrue( b["n2"]["op1"].getInput().getInput().isSame( s["n1"]["sum"] ) )
			self.assertTrue( b["n2"]["op2"].getInput().getInput().isSame( s["n1"]["sum"] ) )
			self.assertTrue( b["n2"]["op1"].getInput().isSame( b["n2"]["op2"].getInput() ) )

			self.assertTrue( s["n4"]["op1"].getInput().node().isSame( b ) )
			self.assertTrue( s["n4"]["op2"].getInput().node().isSame( b ) )

			self.assertTrue( s["n4"]["op1"].getInput().isSame( s["n4"]["op2"].getInput() ) )
	
		assertPostConditions()
	
		s.undo()
		assertPreConditions()
	
		s.redo()
		assertPostConditions()
	
	def testCreateWithScriptSelection( self ) :
	
		s = Gaffer.ScriptNode()
		
		s["n1"] = GafferTest.AddNode()
		s["n2"] = GafferTest.AddNode()
		s["n3"] = GafferTest.AddNode()
		s["n4"] = GafferTest.AddNode()
		
		s["n2"]["op1"].setInput( s["n1"]["sum"] )
		s["n2"]["op2"].setInput( s["n1"]["sum"] )
		
		s["n3"]["op1"].setInput( s["n2"]["sum"] )
		
		s["n4"]["op1"].setInput( s["n3"]["sum"] )
		s["n4"]["op2"].setInput( s["n3"]["sum"] )

		s.selection().add( [ s["n2"], s["n3"] ] )

		b = Gaffer.Box.create( s, s.selection() )
	
	def testCreateWithScriptSelectionReversed( self ) :
	
		s = Gaffer.ScriptNode()
		
		s["n1"] = GafferTest.AddNode()
		s["n2"] = GafferTest.AddNode()
		s["n3"] = GafferTest.AddNode()
		s["n4"] = GafferTest.AddNode()
		
		s["n2"]["op1"].setInput( s["n1"]["sum"] )
		s["n2"]["op2"].setInput( s["n1"]["sum"] )
		
		s["n3"]["op1"].setInput( s["n2"]["sum"] )
		
		s["n4"]["op1"].setInput( s["n3"]["sum"] )
		s["n4"]["op2"].setInput( s["n3"]["sum"] )

		s.selection().add( [ s["n3"], s["n2"] ] )

		b = Gaffer.Box.create( s, s.selection() )
		
	def testCompute( self ) :
	
		s = Gaffer.ScriptNode()
		
		s["n1"] = GafferTest.AddNode()
		s["n2"] = GafferTest.AddNode()
		s["n3"] = GafferTest.AddNode()
		s["n4"] = GafferTest.AddNode()
		
		s["n2"]["op1"].setInput( s["n1"]["sum"] )
		s["n2"]["op2"].setInput( s["n1"]["sum"] )
		
		s["n3"]["op1"].setInput( s["n2"]["sum"] )
		
		s["n4"]["op1"].setInput( s["n3"]["sum"] )
		s["n4"]["op2"].setInput( s["n3"]["sum"] )
		
		s["n1"]["op1"].setValue( 2 )
		s["n3"]["op2"].setValue( 3 )
		
		self.assertEqual( s["n1"]["sum"].getValue(), 2 )
		self.assertEqual( s["n2"]["sum"].getValue(), 4 )
		self.assertEqual( s["n3"]["sum"].getValue(), 7 )
		self.assertEqual( s["n4"]["sum"].getValue(), 14 )
		
		b = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["n2"], s["n3"] ] ) )
	
		self.assertEqual( s["n1"]["sum"].getValue(), 2 )
		self.assertEqual( s["Box"]["n2"]["sum"].getValue(), 4 )
		self.assertEqual( s["Box"]["n3"]["sum"].getValue(), 7 )
		self.assertEqual( s["n4"]["sum"].getValue(), 14 )
	
	def testCreateWithNodesWithInternalConnections( self ) :
	
		s = Gaffer.ScriptNode()
		
		s["n1"] = GafferTest.AddNode()
		s["n2"] = Gaffer.Node()
		s["n3"] = GafferTest.AddNode()
		
		s["n2"]["in"] = Gaffer.IntPlug()
		s["n2"]["out"] = Gaffer.IntPlug( direction = Gaffer.Plug.Direction.Out )
		s["n2"]["__in"] = Gaffer.IntPlug()
		s["n2"]["__out"] = Gaffer.IntPlug( direction = Gaffer.Plug.Direction.Out )
		
		
		s["n2"]["in"].setInput( s["n1"]["sum"] )
		s["n2"]["out"].setInput( s["n2"]["in"] ) # internal shortcut connection
		s["n2"]["__in"].setInput( s["n2"]["__out"] ) # internal input connection
		s["n3"]["op1"].setInput( s["n2"]["out"] )
		
		s.selection().add( s["n2"] )
		b = Gaffer.Box.create( s, s.selection() )
		
		self.assertEqual( len( b ), 4 ) # the user plug, one child node, an in plug and an out plug
		
		self.assertTrue( b["n2"]["in"].getInput().isSame( b["in"] ) )
		self.assertTrue( b["in"].getInput().isSame( s["n1"]["sum"] ) )
		
		self.assertTrue( b["n2"]["out"].getInput().isSame( b["n2"]["in"] ) )
		self.assertTrue( s["n3"]["op1"].getInput().isSame( b["out"] ) )
	
	def testSerialisationOfCreatedResult( self ) :
	
		s = Gaffer.ScriptNode()
		
		s["n1"] = GafferTest.AddNode()
		s["n2"] = GafferTest.AddNode()
		s["n3"] = GafferTest.AddNode()
		s["n4"] = GafferTest.AddNode()
		
		s["n2"]["op1"].setInput( s["n1"]["sum"] )
		s["n2"]["op2"].setInput( s["n1"]["sum"] )
		
		s["n3"]["op1"].setInput( s["n2"]["sum"] )
		
		s["n4"]["op1"].setInput( s["n3"]["sum"] )
		s["n4"]["op2"].setInput( s["n3"]["sum"] )
		
		Gaffer.Box.create( s, Gaffer.StandardSet( [ s["n2"], s["n3"] ] ) )
				
		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )
		
		self.assertTrue( isinstance( s2["Box"], Gaffer.Box ) )

		self.assertTrue( "n2" not in s2 )
		self.assertTrue( "n3" not in s2 )

		self.assertTrue( "n2" in s2["Box"] )
		self.assertTrue( "n3" in s2["Box"] )

		self.assertTrue( s2["Box"]["n3"]["op1"].getInput().isSame( s2["Box"]["n2"]["sum"] ) )

		self.assertTrue( s2["Box"]["n2"]["op1"].getInput().node().isSame( s2["Box"] ) )
		self.assertTrue( s2["Box"]["n2"]["op2"].getInput().node().isSame( s2["Box"] ) )

		self.assertTrue( s2["Box"]["n2"]["op1"].getInput().getInput().isSame( s2["n1"]["sum"] ) )
		self.assertTrue( s2["Box"]["n2"]["op2"].getInput().getInput().isSame( s2["n1"]["sum"] ) )
		self.assertTrue( s2["Box"]["n2"]["op1"].getInput().isSame( s2["Box"]["n2"]["op2"].getInput() ) )

		self.assertTrue( s2["n4"]["op1"].getInput().node().isSame( s2["Box"] ) )
		self.assertTrue( s2["n4"]["op2"].getInput().node().isSame( s2["Box"] ) )

		self.assertTrue( s2["n4"]["op1"].getInput().isSame( s2["n4"]["op2"].getInput() ) )
	
	def testSelection( self ) :
	
		s = Gaffer.ScriptNode()
		
		s["n"] = Gaffer.Node()
		s["b"] = Gaffer.Box()
		s["b"]["n"] = Gaffer.Node()
		
		s.selection().add( s["n"] )
		s.selection().add( s["b"]["n"] )
		
		self.assertTrue( s["n"] in s.selection() )
		self.assertTrue( s["b"]["n"] in s.selection() )
		
	def testPromote( self ) :

		s = Gaffer.ScriptNode()

		s["n1"] = GafferTest.AddNode()
		s["n1"]["op1"].setValue( -10 )
		s["n2"] = GafferTest.AddNode()

		b = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["n1"] ] ) )

		self.assertTrue( b.canPromotePlug( b["n1"]["op1"] ) )
		self.assertFalse( b.canPromotePlug( b["n1"]["sum"] ) )
		self.assertFalse( b.canPromotePlug( s["n2"]["op1"] ) )

		self.assertFalse( b.plugIsPromoted( b["n1"]["op1"] ) )
		self.assertFalse( b.plugIsPromoted( b["n1"]["op2"] ) )
		self.assertFalse( b.plugIsPromoted( s["n2"]["op1"] ) )

		p = b.promotePlug( b["n1"]["op1"] )
		self.assertEqual( p.getName(), "n1_op1" )
		self.assertTrue( p.parent().isSame( b["user"] ) )
		self.assertTrue( b["n1"]["op1"].getInput().isSame( p ) )
		self.assertTrue( b.plugIsPromoted( b["n1"]["op1"] ) )
		self.assertFalse( b.canPromotePlug( b["n1"]["op1"] ) )
		self.assertEqual( p.getValue(), -10 )

	def testPromoteColor( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["c"] = Gaffer.Color3fPlug()
		s["n"]["c"].setValue( IECore.Color3f( 1, 0, 1 ) )

		b = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["n"] ] ) )

		self.assertTrue( b.canPromotePlug( b["n"]["c"] ) )
		self.assertFalse( b.plugIsPromoted( b["n"]["c"] ) )

		p = b.promotePlug( b["n"]["c"] )

		self.assertTrue( isinstance( p, Gaffer.Color3fPlug ) )
		self.assertTrue( b["n"]["c"].getInput().isSame( p ) )
		self.assertTrue( b["n"]["c"]["r"].getInput().isSame( p["r"] ) )
		self.assertTrue( b["n"]["c"]["g"].getInput().isSame( p["g"] ) )
		self.assertTrue( b["n"]["c"]["b"].getInput().isSame( p["b"] ) )
		self.assertEqual( p.getValue(), IECore.Color3f( 1, 0, 1 ) )

	def testPromoteCompoundPlugAndSerialise( self ) :
	
		s = Gaffer.ScriptNode()
		
		s["n"] = GafferTest.CompoundPlugNode()
		s["n"]["p"]["s"].setValue( "hello" )
		
		b = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["n"] ] ) )
		b.promotePlug( b["n"]["p"] )
		
		ss = s.serialise()
		
		s = Gaffer.ScriptNode()
		s.execute( ss )

		self.assertEqual( s["Box"]["n"]["p"]["s"].getValue(), "hello" )

	def testPromoteDynamicColorPlugAndSerialise( self ) :
	
		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["c"] = Gaffer.Color3fPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		
		b = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["n"] ] ) )
		b.promotePlug( b["n"]["c"] )
		
		ss = s.serialise()
				
		s = Gaffer.ScriptNode()
		s.execute( ss )
		
		self.assertTrue( isinstance( s["Box"]["user"]["n_c"], Gaffer.Color3fPlug ) )
		self.assertTrue( s["Box"]["n"]["c"].getInput().isSame( s["Box"]["user"]["n_c"] ) )
	
	def testCantPromoteNonSerialisablePlugs( self ) :
	
		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["p"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default & ~Gaffer.Plug.Flags.Serialisable )
		
		b = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["n"] ] ) )
		self.assertEqual( b.canPromotePlug( b["n"]["p"] ), False )
		self.assertRaises( RuntimeError, b.promotePlug, b["n"]["p"] )
	
	def testUnpromoting( self ) :
	
		s = Gaffer.ScriptNode()

		s["n1"] = GafferTest.AddNode()

		b = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["n1"] ] ) )
		p = b.promotePlug( b["n1"]["op1"] )
		self.assertTrue( b.plugIsPromoted( b["n1"]["op1"] ) )
		self.assertTrue( p.node().isSame( b ) )
		
		b.unpromotePlug( b["n1"]["op1"] )
		self.assertFalse( b.plugIsPromoted( b["n1"]["op1"] ) )
		self.assertTrue( p.node() is None )
	
	def testColorUnpromoting( self ) :
	
		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["c"] = Gaffer.Color3fPlug()
		
		b = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["n"] ] ) )
		p = b.promotePlug( b["n"]["c"] )
		self.assertTrue( b.plugIsPromoted( b["n"]["c"] ) )
		self.assertTrue( b.plugIsPromoted( b["n"]["c"]["r"] ) )
		self.assertTrue( b.plugIsPromoted( b["n"]["c"]["g"] ) )
		self.assertTrue( b.plugIsPromoted( b["n"]["c"]["b"] ) )
		self.assertTrue( p.node().isSame( b ) )
		
		b.unpromotePlug( b["n"]["c"] )
		self.assertFalse( b.plugIsPromoted( b["n"]["c"] ) )
		self.assertFalse( b.plugIsPromoted( b["n"]["c"]["r"] ) )
		self.assertFalse( b.plugIsPromoted( b["n"]["c"]["g"] ) )
		self.assertFalse( b.plugIsPromoted( b["n"]["c"]["b"] ) )
		self.assertTrue( p.node() is None )
		
	def testIncrementalUnpromoting( self ) :
	
		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["c"] = Gaffer.Color3fPlug()
		
		b = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["n"] ] ) )
		p = b.promotePlug( b["n"]["c"] )
		self.assertTrue( b.plugIsPromoted( b["n"]["c"] ) )
		self.assertTrue( b.plugIsPromoted( b["n"]["c"]["r"] ) )
		self.assertTrue( b.plugIsPromoted( b["n"]["c"]["g"] ) )
		self.assertTrue( b.plugIsPromoted( b["n"]["c"]["b"] ) )
		self.assertTrue( p.node().isSame( b ) )
		
		b.unpromotePlug( b["n"]["c"]["r"] )
		self.assertFalse( b.plugIsPromoted( b["n"]["c"] ) )
		self.assertFalse( b.plugIsPromoted( b["n"]["c"]["r"] ) )
		self.assertTrue( b.plugIsPromoted( b["n"]["c"]["g"] ) )
		self.assertTrue( b.plugIsPromoted( b["n"]["c"]["b"] ) )
		self.assertTrue( p.node().isSame( b ) )
		
		b.unpromotePlug( b["n"]["c"]["g"] )
		self.assertFalse( b.plugIsPromoted( b["n"]["c"] ) )
		self.assertFalse( b.plugIsPromoted( b["n"]["c"]["r"] ) )
		self.assertFalse( b.plugIsPromoted( b["n"]["c"]["g"] ) )
		self.assertTrue( b.plugIsPromoted( b["n"]["c"]["b"] ) )
		self.assertTrue( p.node().isSame( b ) )
		
		b.unpromotePlug( b["n"]["c"]["b"] )
		self.assertFalse( b.plugIsPromoted( b["n"]["c"] ) )
		self.assertFalse( b.plugIsPromoted( b["n"]["c"]["r"] ) )
		self.assertFalse( b.plugIsPromoted( b["n"]["c"]["g"] ) )
		self.assertFalse( b.plugIsPromoted( b["n"]["c"]["b"] ) )
		self.assertTrue( p.node() is None )
	
	def testDeletedNodesAreUnselected( self ) :
	
		s = Gaffer.ScriptNode()
		
		s["n1"] = Gaffer.Node()
		s["n2"] = Gaffer.Node()
		
		b = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["n1"], s["n2"] ] ) )
		
		s.selection().add( b["n1"] )
		s.selection().add( b["n2"] )
		
		self.assertEqual( len( s.selection() ), 2 )
		
		n1 = b["n1"]
		del b["n1"]
		
		self.assertTrue( b["n2"] in s.selection() )
		self.assertFalse( n1 in s.selection() )
		self.assertEqual( len( s.selection() ), 1 )
		
if __name__ == "__main__":
	unittest.main()
	
