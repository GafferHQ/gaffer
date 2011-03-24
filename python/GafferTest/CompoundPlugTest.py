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
import gc

import IECore
import Gaffer
import GafferTest

class CompoundPlugTest( unittest.TestCase ) :

	def testContructor( self ) :

		p = Gaffer.CompoundPlug()
		self.assertEqual( p.getName(), "CompoundPlug" )
		self.assertEqual( p.direction(), Gaffer.Plug.Direction.In )

		p = Gaffer.V3fPlug( name="b", direction=Gaffer.Plug.Direction.Out )
		self.assertEqual( p.getName(), "b" )
		self.assertEqual( p.direction(), Gaffer.Plug.Direction.Out )

	def testSerialisation( self ) :
	
		s = Gaffer.ScriptNode()
		s["n1"] = GafferTest.CompoundPlugNode()
		s["n2"] = GafferTest.CompoundPlugNode()
		
		s["n1"]["p"]["f"].setValue( 10 )
		s["n1"]["p"]["s"].setInput( s["n2"]["p"]["s"] )
		
		ss = s.serialise()
				
		s = Gaffer.ScriptNode()
		s.execute( ss )
		
		self.assertEqual( s["n1"]["p"]["f"].getValue(), 10 )
		self.failUnless( s["n1"]["p"]["s"].getInput().isSame( s["n2"]["p"]["s"] ) )
		
	def testDynamicSerialisation( self ) :
	
		s = Gaffer.ScriptNode()
		s["n1"] = Gaffer.Node()
		s["n1"]["p"] = Gaffer.CompoundPlug( flags = Gaffer.Plug.Flags.Dynamic )
		s["n1"]["p"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Dynamic )
		s["n1"]["p"]["f"].setValue( 10 )
		
		ss = s.serialise()
				
		s = Gaffer.ScriptNode()
		s.execute( ss )
		
		self.assertEqual( s["n1"]["p"]["f"].getValue(), 10 )
		
	def testMasterConnectionTracksChildConnections( self ) :
	
		c = Gaffer.CompoundPlug( "c" )
		c["f1"] = Gaffer.FloatPlug()
		c["f2"] = Gaffer.FloatPlug()
		n = Gaffer.Node()
		n["c"] = c		

		c2 = Gaffer.CompoundPlug( "c" )
		c2["f1"] = Gaffer.FloatPlug()
		c2["f2"] = Gaffer.FloatPlug()
		n2 = Gaffer.Node()
		n2["c"] = c2		
		
		n2["c"]["f1"].setInput( n["c"]["f1"] )
		n2["c"]["f2"].setInput( n["c"]["f2"] )
		self.failUnless( n2["c"].getInput().isSame( n["c"] ) )
		
		n2["c"]["f2"].setInput( None )
		self.failUnless( n2["c"].getInput() is None )

		n2["c"]["f2"].setInput( n["c"]["f2"] )
		self.failUnless( n2["c"].getInput().isSame( n["c"] ) )

		c["f3"] = Gaffer.FloatPlug()
		c2["f3"] = Gaffer.FloatPlug()
		
		self.failUnless( n2["c"].getInput() is None )
		
		n2["c"]["f3"].setInput( n["c"]["f3"] )
		self.failUnless( n2["c"].getInput().isSame( n["c"] ) )
		

	def testInputChangedCrash( self ) :
	
		ca = Gaffer.CompoundPlug( "ca" )
		ca["fa1"] = Gaffer.FloatPlug()
		ca["fa2"] = Gaffer.FloatPlug()
		na = Gaffer.Node()
		na["ca"] = ca		

		cb = Gaffer.CompoundPlug( "cb" )
		cb["fb1"] = Gaffer.FloatPlug()
		cb["fb2"] = Gaffer.FloatPlug()
		nb = Gaffer.Node()
		nb["cb"] = cb		
		
		nb["cb"]["fb1"].setInput( na["ca"]["fa1"] )
				
		del ca, na, cb, nb
		while gc.collect() :
			pass
		IECore.RefCounted.collectGarbage()
		
	def testDirtyPropagation( self ) :
	
		c = Gaffer.CompoundPlug( direction=Gaffer.Plug.Direction.Out )
		c["f1"] = Gaffer.FloatPlug( direction=Gaffer.Plug.Direction.Out )
		c["f2"] = Gaffer.FloatPlug( direction=Gaffer.Plug.Direction.Out )
		
		n = Gaffer.Node()
		n["c"] = c

		c["f1"].setValue( 10 )
		c["f2"].setValue( 10 )
		
		self.failIf( c["f1"].getDirty() )
		self.failIf( c["f2"].getDirty() )
		self.failIf( n["c"].getDirty() )
		
		c["f1"].setDirty()

		self.failUnless( c["f1"].getDirty() )
		self.failIf( c["f2"].getDirty() )
		self.failUnless( n["c"].getDirty() )
		
		c["f1"].setValue( 10 )
						
		self.failIf( c["f1"].getDirty() )
		self.failIf( c["f2"].getDirty() )
		self.failIf( n["c"].getDirty() )

		c.setDirty()
		self.failUnless( c["f1"].getDirty() )
		self.failUnless( c["f2"].getDirty() )
		self.failUnless( n["c"].getDirty() )

		c["f1"].setValue( 10 )
		c["f2"].setValue( 10 )

		self.failIf( c["f1"].getDirty() )
		self.failIf( c["f2"].getDirty() )
		self.failIf( n["c"].getDirty() )
		
	def testPlugSetPropagation( self ) :
	
		c = Gaffer.CompoundPlug()
		c["f1"] = Gaffer.FloatPlug()
		
		n = Gaffer.Node()
		n["c"] = c
		
		def setCallback( plug ) :
			
			if plug.isSame( c ) :
				self.set = True

		cn = n.plugSetSignal().connect( setCallback )

		self.set = False
		
		c["f1"].setValue( 10 )
		
		self.failUnless( self.set )
	
	def testMultipleLevelsOfPlugSetPropagation( self ) :
	
		c = Gaffer.CompoundPlug( "c" )
		c["c1"] = Gaffer.CompoundPlug()
		c["c1"]["f1"] = Gaffer.FloatPlug()
		
		n = Gaffer.Node()
		n["c"] = c
		
		def setCallback( plug ) :
		
			self.setPlugs.append( plug.getName() )
		
		cn = n.plugSetSignal().connect( setCallback )
		
		self.setPlugs = []
		
		c["c1"]["f1"].setValue( 10 )
				
		self.failUnless( len( self.setPlugs )==3 )
		self.failUnless( "c" in self.setPlugs )
		self.failUnless( "c1" in self.setPlugs )
		self.failUnless( "f1" in self.setPlugs )
		
	def testAcceptsInput( self ) :
	
		i = Gaffer.CompoundPlug()
		o = Gaffer.CompoundPlug( direction=Gaffer.Plug.Direction.Out )
		s = Gaffer.StringPlug( direction=Gaffer.Plug.Direction.Out )
		
		i.addChild( Gaffer.IntPlug() )
		o.addChild( Gaffer.IntPlug( direction=Gaffer.Plug.Direction.Out ) )
		
		self.failUnless( i.acceptsInput( o ) )
		self.failIf( i.acceptsInput( s ) )
				
if __name__ == "__main__":
	unittest.main()
	
