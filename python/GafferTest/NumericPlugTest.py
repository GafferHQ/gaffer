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

import IECore

import Gaffer
import GafferTest

class NumericPlugTest( unittest.TestCase ) :

	def testConstructor( self ) :
	
		f = Gaffer.FloatPlug()
		self.assertEqual( f.defaultValue(), 0 )
		self.assertEqual( f.getName(), "FloatPlug" )
		self.assertEqual( f.getValue(), 0 )
		
		f = Gaffer.FloatPlug( direction=Gaffer.Plug.Direction.Out, defaultValue = 1,
			minValue = -1, maxValue = 10 )
			
		self.assertEqual( f.direction(), Gaffer.Plug.Direction.Out )
		self.assertEqual( f.defaultValue(), 1 )
		self.assertEqual( f.minValue(), -1 )
		self.assertEqual( f.maxValue(), 10 )
		# cannot get the value of an output plug unless it's on a Node
		self.assertRaises( RuntimeError, f.getValue )
		
		f = Gaffer.FloatPlug( defaultValue=10, name="a" )
		self.assertEqual( f.defaultValue(), 10 )
		self.assertEqual( f.getName(), "a" )
		self.assertEqual( f.typeName(), "Gaffer::FloatPlug" )
		self.assertEqual( f.getValue(), 10 )
	
	def testHaveMinMaxValues( self ) :
	
		f = Gaffer.FloatPlug()
		self.assertEqual( f.hasMinValue(), False )
		self.assertEqual( f.hasMaxValue(), False )
		
		f = Gaffer.FloatPlug( minValue=1 )
		self.assertEqual( f.hasMinValue(), True )
		self.assertEqual( f.hasMaxValue(), False )
		
		f = Gaffer.FloatPlug( maxValue=1 )
		self.assertEqual( f.hasMinValue(), False )
		self.assertEqual( f.hasMaxValue(), True )
			
	def testRunTimeTyping( self ) :
	
		f = Gaffer.FloatPlug()
		i = Gaffer.IntPlug()
		
		self.assert_( f.isInstanceOf( Gaffer.FloatPlug.staticTypeId() ) )			
		self.assert_( not f.isInstanceOf( Gaffer.IntPlug.staticTypeId() ) )			
		self.assert_( not i.isInstanceOf( Gaffer.FloatPlug.staticTypeId() ) )			
		self.assert_( i.isInstanceOf( Gaffer.IntPlug.staticTypeId() ) )
		
	def testAcceptsInput( self ) :
	
		i = Gaffer.IntPlug()		
		o = Gaffer.IntPlug( direction=Gaffer.Plug.Direction.Out )
		s = Gaffer.StringPlug( direction=Gaffer.Plug.Direction.Out )
		
		self.failUnless( i.acceptsInput( o ) )
		self.failIf( i.acceptsInput( s ) )
	
	def testAcceptsNoneInput( self ) :
	
		p = Gaffer.IntPlug( "hello" )
		self.failUnless( p.acceptsInput( None ) )
	
	def testAppliesMinMaxInSetValue( self ) :
	
		i = Gaffer.IntPlug( "i", defaultValue = 1, minValue = 0, maxValue = 10 )
		
		i.setValue( 5 )
		self.assertEqual( i.getValue(), 5 )
		
		i.setValue( -1 )
		self.assertEqual( i.getValue(), 0 )
		
		i.setValue( 11 )
		self.assertEqual( i.getValue(), 10 )
	
	def testSetInputShortcut( self ) :
	
		n1 = GafferTest.AddNode()		
		n2 = GafferTest.AddNode()
		
		inputChangedSignals = GafferTest.CapturingSlot( n1.plugInputChangedSignal() )
		self.assertEqual( len( inputChangedSignals ), 0 )
		
		dirtiedSignals = GafferTest.CapturingSlot( n1.plugDirtiedSignal() )
		self.assertEqual( len( dirtiedSignals ), 0 )
		
		n1["op1"].setInput( n2["sum"] )
		# we should get signals the first time
		self.assertEqual( len( inputChangedSignals ), 1 )
		self.assertEqual( len( dirtiedSignals ), 2 )
		self.assertEqual( dirtiedSignals[0][0].getName(), "op1" )
		self.assertEqual( dirtiedSignals[1][0].getName(), "sum" )
		
		n1["op1"].setInput( n2["sum"] )
		# but the second time there should be no signalling,
		# because it was the same.
		self.assertEqual( len( inputChangedSignals ), 1 )
		self.assertEqual( len( dirtiedSignals ), 2 )
	
	def testSetToDefault( self ) :
	
		i = Gaffer.IntPlug( "i", defaultValue = 10 )
		self.assertEqual( i.getValue(), 10 )
		
		i.setValue( 1 )
		self.assertEqual( i.getValue(), 1 )
		
		i.setToDefault()
		self.assertEqual( i.getValue(), 10 )
		
	def testDisconnectRevertsToPreviousValue( self ) :
	
		n1 = GafferTest.AddNode()
		n2 = GafferTest.AddNode()
		
		n2["op1"].setValue( 1010 )
		self.assertEqual( n2["op1"].getValue(), 1010 )
		
		n2["op1"].setInput( n1["sum"] )
		self.failUnless( n2["op1"].getInput().isSame( n1["sum"] ) )
		self.assertEqual( n2["op1"].getValue(), 0 )
		
		n2["op1"].setInput( None )
		self.assertEqual( n2["op1"].getInput(), None )
		self.assertEqual( n2["op1"].getValue(), 1010 )
	
	def testDisconnectEmitsPlugSet( self ) :
	
		n1 = GafferTest.AddNode()
		n2 = GafferTest.AddNode()
		
		n2["op1"].setInput( n1["sum"] )
	
		set = GafferTest.CapturingSlot( n2.plugSetSignal() )
		
		n2["op1"].setInput( None )
		
		self.assertEqual( len( set ), 1 )
		self.failUnless( set[0][0].isSame( n2["op1"] ) )
		
	def testDefaultValue( self ) :
	
		p = Gaffer.IntPlug(
			"p",
			Gaffer.Plug.Direction.In,
			10,
			0,
			20
		)
		
		self.assertEqual( p.defaultValue(), 10 )
		self.assertEqual( p.getValue(), 10 )
		
		p.setValue( 5 )
		self.assertEqual( p.getValue(), 5 )
		self.assertEqual( p.defaultValue(), 10 )
		
		p.setToDefault()
		self.assertEqual( p.defaultValue(), 10 )
		self.assertEqual( p.getValue(), 10 )
		
		p.setValue( 5 )
		self.assertEqual( p.getValue(), 5 )
		self.assertEqual( p.defaultValue(), 10 )
	
	def testDefaultValueHash( self ) :
	
		p1 = Gaffer.IntPlug(
			"p",
			Gaffer.Plug.Direction.In,
			10
		)

		p2 = Gaffer.IntPlug(
			"p",
			Gaffer.Plug.Direction.In,
			20
		)
		
		p3 = Gaffer.IntPlug(
			"p",
			Gaffer.Plug.Direction.In,
			20
		)
		
		self.assertNotEqual( p1.hash(), p2.hash() )
		self.assertEqual( p2.hash(), p3.hash() )

	def testReadOnlySetValueRaises( self ) :
	
		p = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.ReadOnly )
		self.assertRaises( RuntimeError, p.setValue, 10 )
	
	def testRepr( self ) :
	
		p1 = Gaffer.IntPlug(
			"p",
			Gaffer.Plug.Direction.Out,
			10,
			-10,
			100,
			Gaffer.Plug.Flags.Default & ~Gaffer.Plug.Flags.AcceptsInputs,
		)
		
		p2 = eval( repr( p1 ) )
		
		self.assertEqual( p1.getName(), p2.getName() )
		self.assertEqual( p1.direction(), p2.direction() )
		self.assertEqual( p1.defaultValue(), p2.defaultValue() )
		self.assertEqual( p1.minValue(), p2.minValue() )
		self.assertEqual( p1.maxValue(), p2.maxValue() )
		self.assertEqual( p1.getFlags(), p2.getFlags() )
	
	def testCreateCounterpart( self ) :
	
		p1 = Gaffer.IntPlug(
			"p",
			Gaffer.Plug.Direction.Out,
			10,
			-10,
			100,
			Gaffer.Plug.Flags.Default & ~Gaffer.Plug.Flags.AcceptsInputs,
		)
		
		p2 = p1.createCounterpart( "c", Gaffer.Plug.Direction.In )
		
		self.assertEqual( p2.getName(), "c" )
		self.assertEqual( p2.direction(), Gaffer.Plug.Direction.In )
		self.assertEqual( p2.getFlags(), p1.getFlags() )
		self.assertEqual( p2.defaultValue(), p1.defaultValue() )
		self.assertEqual( p2.minValue(), p1.minValue() )
		self.assertEqual( p2.maxValue(), p1.maxValue() )
			
if __name__ == "__main__":
	unittest.main()
	
