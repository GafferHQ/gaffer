##########################################################################
#  
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
#  Copyright (c) 2012, Image Engine Design Inc. All rights reserved.
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

class CompoundNumericPlugTest( unittest.TestCase ) :

	def testContructor( self ) :
	
		p = Gaffer.V3fPlug()
		self.assertEqual( p.getName(), "V3fPlug" )
		self.assertEqual( p.direction(), Gaffer.Plug.Direction.In )
		
		p = Gaffer.V3fPlug( name="b", direction=Gaffer.Plug.Direction.Out )
		self.assertEqual( p.getName(), "b" )
		self.assertEqual( p.direction(), Gaffer.Plug.Direction.Out )
	
	def testChildRejection( self ) :
	
		p = Gaffer.V3fPlug()
		c = Gaffer.FloatPlug()
		self.assertRaises( Exception, p.addChild, c )
	
	def testChildNames( self ) :
	
		p = Gaffer.V3fPlug()
		p["x"].setValue( 1 )
		p["y"].setValue( 2 )
		p["z"].setValue( 3 )
		
		self.assertEqual( p.getValue(), IECore.V3f( 1, 2, 3 ) )
		
	def testMinMaxValues( self ) :
	
		p = Gaffer.V3fPlug()
		self.failIf( p.hasMinValue() )
		self.failIf( p.hasMaxValue() )
		for a in ( "x", "y", "z" ) :
			self.failIf( p[a].hasMinValue() )
			self.failIf( p[a].hasMaxValue() )
		
		p = Gaffer.V3fPlug(
			minValue = IECore.V3f( -1, -2, -3 ),
			maxValue = IECore.V3f( 1, 2, 3 )
		)
		
		self.failUnless( p.hasMinValue() )
		self.failUnless( p.hasMaxValue() )
		for a in ( "x", "y", "z" ) :
			self.failUnless( p[a].hasMinValue() )
			self.failUnless( p[a].hasMaxValue() )
		
		minValue = p.minValue()
		maxValue = p.maxValue()
		self.assertEqual( minValue, IECore.V3f( -1, -2, -3 ) )
		self.assertEqual( maxValue, IECore.V3f( 1, 2, 3 ) )
		i = 0
		for a in ( "x", "y", "z" ) :
			self.assertEqual( p[a].minValue(), minValue[i] )
			self.assertEqual( p[a].maxValue(), maxValue[i] )
			i += 1
	
	def testDefaultValue( self ) :
	
		p = Gaffer.V3fPlug( defaultValue = IECore.V3f( 1, 2, 3 ) )
		self.assertEqual( p.defaultValue(), IECore.V3f( 1, 2, 3 ) )
		self.assertEqual( p["x"].defaultValue(), 1 )
		self.assertEqual( p["y"].defaultValue(), 2 )
		self.assertEqual( p["z"].defaultValue(), 3 )
		
	def testSerialisation( self ) :
	
		s = Gaffer.ScriptNode()		
		n = GafferTest.CompoundNumericNode()
		n["p"].setValue( IECore.V3f( 1, 2, 3 ) )
		s["n"] = n
		
		ss = s.serialise()
								
		s = Gaffer.ScriptNode()
		s.execute( ss )
				
		self.assertEqual( s["n"]["p"].getValue(), IECore.V3f( 1, 2, 3 ) )		

	def testSerialisationWithConnection( self ) :
	
		s = Gaffer.ScriptNode()
		n1 = GafferTest.CompoundNumericNode()
		n2 = GafferTest.CompoundNumericNode()
		n1["p"].setInput( n2["p"] )
		s["n1"] = n1
		s["n2"] = n2
		
		ss = s.serialise()
				
		s = Gaffer.ScriptNode()
		s.execute( ss )
		
		self.failUnless( s["n1"]["p"].getInput().isSame( s["n2"]["p"] ) )
		self.failUnless( s["n1"]["p"]["x"].getInput().isSame( s["n2"]["p"]["x"] ) )
		self.failUnless( s["n1"]["p"]["y"].getInput().isSame( s["n2"]["p"]["y"] ) )
		self.failUnless( s["n1"]["p"]["z"].getInput().isSame( s["n2"]["p"]["z"] ) )

	def testSerialisationWithPartialConnections( self ) :
	
		s = Gaffer.ScriptNode()
		n = GafferTest.CompoundNumericNode()
		a = GafferTest.AddNode()
		n["p"]["x"].setValue( 10 )
		n["p"]["y"].setInput( a["sum"] )
		s["n"] = n
		a["a"] = a
		
		ss = s.serialise()
		
		s = Gaffer.ScriptNode()
		s.execute( ss )
		
		self.assertEqual( s["n"]["p"]["x"].getValue(), 10 )
		self.failUnless( s["n"]["p"]["y"].getInput().isSame( s["a"]["sum"] ) )
		self.assertEqual( s["n"]["p"]["z"].getValue(), 0 )
		
	def testDynamicSerialisation( self ) :
	
		s = Gaffer.ScriptNode()
		n = Gaffer.Node()
		n["p"] = Gaffer.V3fPlug( flags=Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		n["p"].setValue( IECore.V3f( 1, 2, 3 ) )
		s["n"] = n
		
		ss = s.serialise()
				
		s = Gaffer.ScriptNode()
		s.execute( ss )
		
		self.assertEqual( s["n"]["p"].getValue(), IECore.V3f( 1, 2, 3 ) )

	def testDynamicSerialisationWithConnection( self ) :
	
		s = Gaffer.ScriptNode()
		s["n1"] = Gaffer.Node()
		s["n2"] = Gaffer.Node()
		
		s["n1"]["p"] = Gaffer.V3fPlug( flags=Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n2"]["p"] = Gaffer.V3fPlug( direction=Gaffer.Plug.Direction.In, flags=Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		
		s["n1"]["p"].setInput( s["n2"]["p"] )

		ss = s.serialise()
						
		s = Gaffer.ScriptNode()
		s.execute( ss )
		
		self.failUnless( s["n1"]["p"].getInput().isSame( s["n2"]["p"] ) )
		self.failUnless( s["n1"]["p"]["x"].getInput().isSame( s["n2"]["p"]["x"] ) )
		self.failUnless( s["n1"]["p"]["y"].getInput().isSame( s["n2"]["p"]["y"] ) )
		self.failUnless( s["n1"]["p"]["z"].getInput().isSame( s["n2"]["p"]["z"] ) )
		
	def testRunTimeTyped( self ) :
	
		p = Gaffer.Color3fPlug()
		self.failUnless( p.isInstanceOf( Gaffer.CompoundPlug.staticTypeId() ) )
		self.failUnless( p.isInstanceOf( Gaffer.Plug.staticTypeId() ) )

		t = p.typeId()
		self.assertEqual( IECore.RunTimeTyped.baseTypeId( t ), Gaffer.CompoundPlug.staticTypeId() )

	def testSetToDefault( self ) :
	
		p = Gaffer.V3fPlug( defaultValue = IECore.V3f( 1, 2, 3 ) )
		self.assertEqual( p.getValue(), IECore.V3f( 1, 2, 3 ) )
		
		p.setValue( IECore.V3f( 4 ) )
		self.assertEqual( p.getValue(), IECore.V3f( 4 ) )
		
		p.setToDefault()
		self.assertEqual( p.getValue(), IECore.V3f( 1, 2, 3 ) )
			
	def testReadOnlySetValueRaises( self ) :
	
		p = Gaffer.V3fPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.ReadOnly )
		self.assertRaises( RuntimeError, p.setValue, IECore.V3f( 1 ) )
		
	def testColor3fAcceptsColor4fInput( self ) :
	
		p4 = Gaffer.Color4fPlug( direction = Gaffer.Plug.Direction.Out )
		p3 = Gaffer.Color3fPlug()
		
		self.failUnless( p3.acceptsInput( p4 ) )
		
		p3.setInput( p4 )
		
		self.failUnless( p3.getInput().isSame( p4 ) )
		self.failUnless( p3[0].getInput().isSame( p4[0] ) )
		self.failUnless( p3[1].getInput().isSame( p4[1] ) )
		self.failUnless( p3[2].getInput().isSame( p4[2] ) )
		self.assertEqual( p4[3].outputs(), () )
		
	def testColor4fDoesntAcceptColor3fInput( self ) :
	
		p4 = Gaffer.Color4fPlug()
		p3 = Gaffer.Color3fPlug( direction = Gaffer.Plug.Direction.Out )
		
		self.failIf( p4.acceptsInput( p3 ) )
		
		self.assertRaises( RuntimeError, p3.setInput, p4 )
				
if __name__ == "__main__":
	unittest.main()
	
