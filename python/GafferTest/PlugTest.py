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

from __future__ import with_statement

import unittest

import IECore

import Gaffer
import GafferTest

class PlugTest( unittest.TestCase ) :

	def testParenting( self ) :
	
		n = Gaffer.Node()
		p = Gaffer.Plug()
		self.assert_( p.parent() is None )
		self.assert_( p.node() is None )
		self.assert_( p.acceptsParent( n ) )
		n.addChild( p )
		self.assert_( p.parent().isSame( n ) )
		self.assert_( p.node().isSame( n ) )
	
	def testConnectionAcceptance( self ) :
	
		p1 = Gaffer.Plug( direction=Gaffer.Plug.Direction.In )
		p2 = Gaffer.Plug( direction=Gaffer.Plug.Direction.Out )
		self.assert_( p1.acceptsInput( p2 ) )
		
		p1 = Gaffer.Plug( direction=Gaffer.Plug.Direction.In )
		p2 = Gaffer.Plug( direction=Gaffer.Plug.Direction.In )
		self.assert_( p1.acceptsInput( p2 ) )
		
	def testConnection( self ) :
	
		n1 = Gaffer.Node()
		p1 = Gaffer.Plug()
		n1.addChild( p1 )
		self.assert_( p1.getInput() is None )
		self.assertEqual( p1.outputs(), () )
		
		n2 = Gaffer.Node()
		p2 = Gaffer.Plug()
		n2.addChild( p2 )
		self.assert_( p2.getInput() is None )
		self.assertEqual( p2.outputs(), () )
		
		p2.setInput( p1 )
		self.assert_( p2.getInput().isSame( p1 ) )
		self.assert_( len( p1.outputs() ), 1 )
		self.assert_( p1.outputs()[0].isSame( p2 ) )

		p2.setInput( None )
		self.assert_( p2.getInput() is None )
		self.assertEqual( p1.outputs(), () )
		
	def testConnectionSignals( self ) :
	
		def f( p ) :
		
			PlugTest.__connection = ( p, p.getInput() )
			
		n1 = Gaffer.Node()
		p1 = Gaffer.Plug( direction=Gaffer.Plug.Direction.Out )
		n1.addChild( p1 )
		
		n2 = Gaffer.Node()
		p2 = Gaffer.Plug( direction=Gaffer.Plug.Direction.In )
		n2.addChild( p2 )
		
		c = n2.plugInputChangedSignal().connect( f )
		p2.setInput( p1 )
		self.assert_( PlugTest.__connection[0].isSame( p2 ) ) 
		self.assert_( PlugTest.__connection[1].isSame( p1 ) )
		PlugTest.__connection = None
		p2.setInput( None )
		self.assert_( PlugTest.__connection[0].isSame( p2 ) ) 
		self.assert_( PlugTest.__connection[1] is None )
		
	def testDirectionality( self ) :
	
		p = Gaffer.Plug( direction=Gaffer.Plug.Direction.In )
		self.assertEqual( p.direction(), Gaffer.Plug.Direction.In )
		p = Gaffer.Plug( direction=Gaffer.Plug.Direction.Out )
		self.assertEqual( p.direction(), Gaffer.Plug.Direction.Out )
		
	def testFlags( self ) :
	
		p = Gaffer.Plug()
		self.assertEqual( p.getFlags(), Gaffer.Plug.Flags.Default )
		
		p = Gaffer.Plug( flags=Gaffer.Plug.Flags.Dynamic )
		self.assertEqual( p.getFlags(), Gaffer.Plug.Flags.Dynamic )
		self.assertEqual( p.getFlags( Gaffer.Plug.Flags.Dynamic ), True )
		
		p.setFlags( Gaffer.Plug.Flags.Dynamic, False )
		self.assertEqual( p.getFlags( Gaffer.Plug.Flags.Dynamic ), False )
	
	def testDerivingInPython( self ) :
	
		class TestPlug( Gaffer.Plug ) :
		
			def __init__( self, name = "TestPlug", direction = Gaffer.Plug.Direction.In, flags = Gaffer.Plug.Flags.Default ) :
			
				Gaffer.Plug.__init__( self, name, direction, flags )
				
				self.inputHasBeenSet = False

			def acceptsInput( self, plug ) :
			
				if not Gaffer.Plug.acceptsInput( self, plug ) :
					return False
					
				return isinstance( plug, ( TestPlug, type( None ) ) )
				
			def setInput( self, plug ) :
			
				Gaffer.Plug.setInput( self, plug )
				
				self.inputHasBeenSet = True
				
			def acceptsParent( self, potentialParent ) :
			
				if not Gaffer.Plug.acceptsParent( self, potentialParent ) :
					return False
					
				if isinstance( potentialParent, Gaffer.CompoundPlug ) :
					return False
					
				return True
				
			def createCounterpart( self, name, direction ) :
			
				return TestPlug( name, direction, self.getFlags() )
				
		IECore.registerRunTimeTyped( TestPlug )
		
		# check the constructor
		
		p1 = TestPlug( "testIn" )
		self.assertEqual( p1.getName(), "testIn" )
		self.assertEqual( p1.direction(), Gaffer.Plug.Direction.In )
		self.assertEqual( p1.getFlags(), Gaffer.Plug.Flags.Default )
		
		n1 = Gaffer.Node()
		n1.addChild( p1 )
		self.assertEqual( n1["testIn"], p1 )
		
		n2 = Gaffer.Node()
		n2.addChild( TestPlug( name = "testOut", direction = Gaffer.Plug.Direction.Out ) )
		n2.addChild( Gaffer.IntPlug( name = "intOut", direction = Gaffer.Plug.Direction.Out ) )
		
		# check that accepts input and setInput can be overridden
		
		self.failUnless( n1["testIn"].acceptsInput( n2["testOut"] ) )
		self.failIf( n1["testIn"].acceptsInput( n2["intOut"] ) )
		
		self.assertRaises( RuntimeError, n1["testIn"].setInput, n2["intOut"] )
		self.assertEqual( n1["testIn"].inputHasBeenSet, False )
		
		n1["testIn"].setInput( n2["testOut"] )
		self.assertEqual( n1["testIn"].inputHasBeenSet, True )
		self.assertEqual( n1["testIn"].getInput(), n2["testOut"] )
		
		# check that acceptsParent can be overridden
		
		p2 = TestPlug()
		self.assertRaises( RuntimeError, Gaffer.CompoundPlug().addChild, p2 )
		
		# try making a counterpart
		
		p3 = p2.createCounterpart( "ll", Gaffer.Plug.Direction.Out )
		self.assertEqual( p3.getName(), "ll" )
		self.assertEqual( p3.direction(), Gaffer.Plug.Direction.Out )
		
	def testRemovePlugRemovesInputs( self ) :

		s = Gaffer.ScriptNode()
		
		s["n1"] = Gaffer.Node()
		s["n2"] = Gaffer.Node()
		
		s["n1"]["o"] = Gaffer.IntPlug( direction = Gaffer.Plug.Direction.Out )
		
		s["n2"]["i"] = Gaffer.IntPlug()
		s["n2"]["c"] = Gaffer.CompoundPlug()
		s["n2"]["c"]["i"] = Gaffer.IntPlug()
		
		s["n2"]["i"].setInput( s["n1"]["o"] )
		s["n2"]["c"]["i"].setInput( s["n1"]["o"] )

		self.failUnless( s["n2"]["i"].getInput().isSame( s["n1"]["o"] ) )
		self.failUnless( s["n2"]["c"]["i"].getInput().isSame(  s["n1"]["o"] ) )
		self.assertEqual( len( s["n1"]["o"].outputs() ), 2 )
		
		with Gaffer.UndoContext( s ) :
		
			del s["n2"]["i"]
			del s["n2"]["c"]["i"]
			
		self.assertEqual( len( s["n1"]["o"].outputs() ), 0 )

		s.undo()
		
		self.failUnless( s["n2"]["i"].getInput().isSame( s["n1"]["o"] ) )
		self.failUnless( s["n2"]["c"]["i"].getInput().isSame(  s["n1"]["o"] ) )
		self.assertEqual( len( s["n1"]["o"].outputs() ), 2 )
		
	def testRemovePlugRemovesOutputs( self ) :

		s = Gaffer.ScriptNode()
		
		s["n1"] = Gaffer.Node()
		s["n2"] = Gaffer.Node()
		
		s["n1"]["o"] = Gaffer.IntPlug( direction = Gaffer.Plug.Direction.Out )
		
		s["n2"]["i"] = Gaffer.IntPlug()
		
		s["n2"]["i"].setInput( s["n1"]["o"] )
		
		self.failUnless( s["n2"]["i"].getInput().isSame( s["n1"]["o"] ) )
		self.assertEqual( len( s["n1"]["o"].outputs() ), 1 )
		
		with Gaffer.UndoContext( s ) :
		
			removedPlug = s["n1"]["o"]
			del s["n1"]["o"]
			
		self.assertEqual( len( removedPlug.outputs() ), 0 )

		s.undo()
		
		self.failUnless( s["n2"]["i"].getInput().isSame( s["n1"]["o"] ) )
		self.assertEqual( len( s["n1"]["o"].outputs() ), 1 )
		self.failUnless( s["n1"]["o"].isSame( removedPlug ) )
	
	def testDefaultFlags( self ) :
		
		p = Gaffer.Plug()
		self.failUnless( p.getFlags( Gaffer.Plug.Flags.Serialisable ) )
	
	def testSerialisableFlag( self ) :
	
		s = Gaffer.ScriptNode()
		
		s["n"] = GafferTest.AddNode()
		
		self.failUnless( s["n"]["op1"].getFlags( Gaffer.Plug.Flags.Serialisable ) )
			
		s["n"]["op1"].setValue( 20 )
		ss = s.serialise()
		
		s = Gaffer.ScriptNode()
		s.execute( ss )
		
		self.assertEqual( s["n"]["op1"].getValue(), 20 )
	
		s["n"]["op1"].setFlags( Gaffer.Plug.Flags.Serialisable, False )
		ss = s.serialise()
		
		self.failIf( "op1" in ss )
		
		s = Gaffer.ScriptNode()
		s.execute( ss )
		
		self.assertEqual( s["n"]["op1"].getValue(), 0 )
	
	def testFlagSerialisation( self ) :
	
		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["p"] = Gaffer.Plug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		
		ss = s.serialise()
				
		s = Gaffer.ScriptNode()
		s.execute( ss )
		
		self.assertEqual( s["n"]["p"].getFlags(), Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
	
	def testFlagsNeverSerialisedAsAll( self ) :
	
		# it's a terrible idea to serialise a set of flags that happen to be All
		# as All, rather than as the or-ing of the specific flags, because when new
		# flags are introduced in the future (and default to off) they will suddenly
		# pop on when loading old files.
		
		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["p"] = Gaffer.Plug( flags = Gaffer.Plug.Flags.All )
		
		ss = s.serialise()
		
		self.failIf( "All" in ss )
		
		s = Gaffer.ScriptNode()
		s.execute( ss )
		
		self.assertEqual( s["n"]["p"].getFlags(), Gaffer.Plug.Flags.All )
	
	def testAcceptsInputsFlag( self ) :
	
		pOut = Gaffer.Plug( direction = Gaffer.Plug.Direction.Out )
		
		pIn1 = Gaffer.Plug( flags = Gaffer.Plug.Flags.Default & ~Gaffer.Plug.Flags.AcceptsInputs )
		self.assertEqual( pIn1.getFlags( Gaffer.Plug.Flags.AcceptsInputs ), False )
		self.assertEqual( pIn1.acceptsInput( pOut ), False )
		
		pIn2 = Gaffer.Plug()
		self.assertEqual( pIn2.getFlags( Gaffer.Plug.Flags.AcceptsInputs ), True )
		self.assertEqual( pIn2.acceptsInput( pOut ), True )
		
	def testReadOnlyDefaultsToOff( self ) :
	
		p = Gaffer.Plug()
		self.failIf( p.getFlags( Gaffer.Plug.Flags.ReadOnly ) )
	
	def testReadOnlyDisallowsInputs( self ) :
	
		self.failUnless( Gaffer.Plug.Flags.All & Gaffer.Plug.Flags.ReadOnly )
	
		p1 = Gaffer.Plug()
		p2 = Gaffer.Plug()
		self.failUnless( p1.acceptsInput( p2 ) )
		# read-only plugs can still be used as connection sources
		p2.setFlags( Gaffer.Plug.Flags.ReadOnly, True )	
		self.failUnless( p1.acceptsInput( p2 ) )
		# but cannot be used as destinations
		self.failIf( p2.acceptsInput( p1 ) )
		self.assertRaises( RuntimeError, p2.setInput, p1 )
		
	def testOutputPlugsDisallowReadOnly( self ) :
	
		p = Gaffer.Plug( direction = Gaffer.Plug.Direction.Out )
		self.assertRaises( RuntimeError, p.setFlags, Gaffer.Plug.Flags.ReadOnly, True )
		
		self.assertRaises(
			RuntimeError,
			Gaffer.Plug,
			direction = Gaffer.Plug.Direction.Out,
			flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.ReadOnly
		)
	
	def testRepr( self ) :
	
		p1 = Gaffer.Plug(
			"p",
			Gaffer.Plug.Direction.Out,
			Gaffer.Plug.Flags.Default & ~Gaffer.Plug.Flags.AcceptsInputs,
		)
		
		p2 = eval( repr( p1 ) )
		
		self.assertEqual( p1.getName(), p2.getName() )
		self.assertEqual( p1.direction(), p2.direction() )
		self.assertEqual( p1.getFlags(), p2.getFlags() )
	
	def testCreateCounterpart( self ) :
	
		p = Gaffer.Plug(
			"p",
			Gaffer.Plug.Direction.Out,
			Gaffer.Plug.Flags.Default & ~Gaffer.Plug.Flags.AcceptsInputs,
		)
		
		p2 = p.createCounterpart( "p2", Gaffer.Plug.Direction.In )
		
		self.assertEqual( p2.getName(), "p2" )
		self.assertEqual( p2.direction(), Gaffer.Plug.Direction.In )
		self.assertEqual( p2.getFlags(), p.getFlags() )
	
	def testSource( self ) :
		
		p1 = Gaffer.Plug( "p1" )
		p2 = Gaffer.Plug( "p2" )
		p3 = Gaffer.Plug( "p3" )
		
		self.assertTrue( p1.source().isSame( p1 ) )
		self.assertTrue( p2.source().isSame( p2 ) )
		self.assertTrue( p3.source().isSame( p3 ) )
		
		p2.setInput( p1 )
		self.assertTrue( p1.source().isSame( p1 ) )
		self.assertTrue( p2.source().isSame( p1 ) )
		self.assertTrue( p3.source().isSame( p3 ) )
		
		p3.setInput( p2 )
		self.assertTrue( p1.source().isSame( p1 ) )
		self.assertTrue( p2.source().isSame( p1 ) )
		self.assertTrue( p3.source().isSame( p1 ) )
	
	def testRejectsInputFromSelf( self ) :
	
		p = Gaffer.Plug()
		self.assertFalse( p.acceptsInput( p ) )
		
if __name__ == "__main__":
	unittest.main()
	
