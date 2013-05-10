##########################################################################
#  
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
#  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
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
import threading
import time

import IECore

import Gaffer
import GafferTest

class NodeTest( GafferTest.TestCase ) :

	def testParenting( self ) :
	
		c = Gaffer.GraphComponent()
		n = Gaffer.Node()
		self.assertEqual( n.acceptsParent( c ), False )
		self.assertRaises( RuntimeError, c.addChild, n )
	
		n2 = Gaffer.Node()
		self.assertEqual( n.acceptsParent( n2 ), True )
		n2.addChild( n )
	
		p = Gaffer.Plug()
		self.assert_( n.acceptsChild( p ) )
		self.assert_( not n.acceptsParent( p ) )
		n.addChild( p )
		self.assert_( p.parent().isSame( n ) )
	
	def testNaming( self ) :
	
		n = Gaffer.Node()
		self.assertEqual( n.getName(), "Node" )	
	
	def testScriptNode( self ) :
	
		n = Gaffer.Node()
		n2 = Gaffer.Node()
		self.assertEqual( n.scriptNode(), None )
		self.assertEqual( n2.scriptNode(), None )
		
		sn = Gaffer.ScriptNode()
		
		sn.addChild( n )
		n.addChild( n2 )
		
		self.assert_( n.scriptNode().isSame( sn ) )		
		self.assert_( n2.scriptNode().isSame( sn ) )		
		
	def testExtendedConstructor( self ) :
		
		n = Gaffer.Node()
		self.assertEqual( n.getName(), "Node" )
		
		n = Gaffer.Node( "a" )
		self.assertEqual( n.getName(), "a" )
				
		self.assertRaises( Exception, Gaffer.Node, "too", "many" )
		
	def testDynamicPlugSerialisationOrder( self ) :
	
		n = Gaffer.Node()
		
		n["p1"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		n["p2"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		n["p3"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		self.assertEqual( n.children()[0].getName(), "user" )
		self.assertEqual( n.children()[1].getName(), "p1" )
		self.assertEqual( n.children()[2].getName(), "p2" )
		self.assertEqual( n.children()[3].getName(), "p3" )
		
		s = Gaffer.ScriptNode()
		s["n"] = n
		
		ss = s.serialise()
		
		s = Gaffer.ScriptNode()
		s.execute( ss )
		
		self.assertEqual( s["n"].children()[0].getName(), "user" )
		self.assertEqual( s["n"].children()[1].getName(), "p1" )
		self.assertEqual( s["n"].children()[2].getName(), "p2" )
		self.assertEqual( s["n"].children()[3].getName(), "p3" )
	
	def testSerialiseDynamicStringPlugs( self ) :
	
		n = Gaffer.Node()
		
		n["p1"] = Gaffer.StringPlug( defaultValue = "default", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		n["p1"].setValue( "value" )
		self.assertEqual( n["p1"].getValue(), "value" )
		
		s = Gaffer.ScriptNode()
		s["n"] = n
		
		ss = s.serialise()

		s = Gaffer.ScriptNode()
		s.execute( ss )
		
		self.assertEqual( s["n"]["p1"].defaultValue(), "default" )
		self.assertEqual( s["n"]["p1"].getValue(), "value" )
	
	def testSerialiseDynamicBoolPlugs( self ) :
	
		n = Gaffer.Node()
		
		n["p1"] = Gaffer.BoolPlug( defaultValue = True, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		n["p1"].setValue( False )
		
		s = Gaffer.ScriptNode()
		s["n"] = n
		
		ss = s.serialise()
		
		s = Gaffer.ScriptNode()
		s.execute( ss )
		
		self.assertEqual( s["n"]["p1"].defaultValue(), True )
		self.assertEqual( s["n"]["p1"].getValue(), False )
		
	def testUnparentingRemovesConnections( self ) :
	
		s = Gaffer.ScriptNode()
		
		n1 = GafferTest.AddNode( "n1" )
		n2 = GafferTest.AddNode( "n2" )
		
		s.addChild( n1 )
		s.addChild( n2 )
		
		n2["op1"].setInput( n1["sum"] )
		self.failUnless( n2["op1"].getInput().isSame( n1["sum"] ) )
		
		del s["n2"]
		
		self.assertEqual( n2["op1"].getInput(), None )
		
		s.addChild( n2 )

		n2["op1"].setInput( n1["sum"] )
		self.failUnless( n2["op1"].getInput().isSame( n1["sum"] ) )

		del s["n1"]
		
		self.assertEqual( n2["op1"].getInput(), None )
				
	def testOverrideAcceptsInput( self ) :
	
		class AcceptsInputTestNode( Gaffer.Node ) :
		
			def __init__( self, name = "AcceptsInputTestNode" ) :
			
				Gaffer.Node.__init__( self, name )
				
				self.addChild( Gaffer.IntPlug( "in" ) )
				self.addChild( Gaffer.IntPlug( "out", Gaffer.Plug.Direction.Out ) )
				
			def acceptsInput( self, plug, inputPlug ) :
			
				return isinstance( inputPlug.node(), AcceptsInputTestNode )
	
		n1 = AcceptsInputTestNode()
		n2 = AcceptsInputTestNode()
		n3 = GafferTest.AddNode()
	
		self.assertEqual( n1["in"].acceptsInput( n2["out"] ), True )
		self.assertEqual( n1["in"].acceptsInput( n3["sum"] ), False )
			
	def testPlugFlagsChangedSignal( self ) :
	
		n = Gaffer.Node()
		n["p"] = Gaffer.Plug()

		cs = GafferTest.CapturingSlot( n.plugFlagsChangedSignal() )
		self.assertEqual( len( cs ), 0 )
		
		n["p"].setFlags( Gaffer.Plug.Flags.ReadOnly, True )
		self.assertEqual( len( cs ), 1 )
		self.failUnless( cs[0][0].isSame( n["p"] ) )
		
		# second time should have no effect because they're the same
		n["p"].setFlags( Gaffer.Plug.Flags.ReadOnly, True )
		self.assertEqual( len( cs ), 1 )
		
		n["p"].setFlags( Gaffer.Plug.Flags.ReadOnly, False )
		self.assertEqual( len( cs ), 2 )
		self.failUnless( cs[1][0].isSame( n["p"] ) )

	def testUserPlugs( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["user"]["test"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["user"]["test"].setValue( 10 )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( s2["n"]["user"]["test"].getValue(), 10 )
	
if __name__ == "__main__":
	unittest.main()
