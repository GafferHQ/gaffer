##########################################################################
#  
#  Copyright (c) 2011, John Haddon. All rights reserved.
#  Copyright (c) 2011, Image Engine Design Inc. All rights reserved.
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
		self.assertEqual( p.getFlags(), Gaffer.Plug.Flags.None )
		
		p = Gaffer.Plug( flags=Gaffer.Plug.Flags.Dynamic )
		self.assertEqual( p.getFlags(), Gaffer.Plug.Flags.Dynamic )
		self.assertEqual( p.getFlags( Gaffer.Plug.Flags.Dynamic ), True )
		
		p.setFlags( Gaffer.Plug.Flags.Dynamic, False )
		self.assertEqual( p.getFlags( Gaffer.Plug.Flags.Dynamic ), False )
	
	def testDerivingInPython( self ) :
	
		class TestPlug( Gaffer.Plug ) :
		
			def __init__( self, name = "TestPlug", direction = Gaffer.Plug.Direction.In, flags = Gaffer.Plug.Flags.None ) :
			
				Gaffer.Plug.__init__( self, name, direction, flags )
				
				self.inputHasBeenSet = False

			def acceptsInput( self, plug ) :
			
				if not Gaffer.Plug.acceptsInput( self, plug ) :
					return False
					
				return isinstance( plug, TestPlug )
				
			def setInput( self, plug ) :
			
				Gaffer.Plug.setInput( self, plug )
				
				self.inputHasBeenSet = True
				
			def acceptsParent( self, potentialParent ) :
			
				if not Gaffer.Plug.acceptsParent( self, potentialParent ) :
					return False
					
				if isinstance( potentialParent, Gaffer.CompoundPlug ) :
					return False
					
				return True
				
		IECore.registerRunTimeTyped( TestPlug )
		
		# check the constructor
		
		p1 = TestPlug( "testIn" )
		self.assertEqual( p1.getName(), "testIn" )
		self.assertEqual( p1.direction(), Gaffer.Plug.Direction.In )
		self.assertEqual( p1.getFlags(), Gaffer.Plug.Flags.None )
		
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
	
	def testAcceptsInputForInputRemoval( self ) :
	
		class NoDisconnectionPlug( Gaffer.Plug ) :
		
			def __init__( self, name = "NoDisconnectionPlug", direction = Gaffer.Plug.Direction.In, flags = Gaffer.Plug.Flags.None ) :
			
				Gaffer.Plug.__init__( self, name, direction, flags )
				
			def acceptsInput( self, plug ) :
			
				if not Gaffer.Plug.acceptsInput( self, plug ) :
					return False
				
				if plug is None :
					return False
					
				return True

		IECore.registerRunTimeTyped( NoDisconnectionPlug )
		
		n1 = Gaffer.Node()
		n1.addChild( NoDisconnectionPlug( "testIn" ) )
				
		n2 = Gaffer.Node()
		n2.addChild( Gaffer.IntPlug( name = "intOut", direction = Gaffer.Plug.Direction.Out ) )
		
		self.failUnless( n1["testIn"].acceptsInput( n2["intOut"] ) )
		self.failIf( n1["testIn"].acceptsInput( None ) )
		
		n1["testIn"].setInput( n2["intOut"] )
		self.failUnless( n1["testIn"].getInput().isSame( n2["intOut"] ) )
						
		self.assertRaises( Exception, n1["testIn"].setInput, None )
		self.failUnless( n1["testIn"].getInput().isSame( n2["intOut"] ) )
				
if __name__ == "__main__":
	unittest.main()
	
