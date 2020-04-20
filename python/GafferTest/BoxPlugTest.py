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
import imath

import IECore

import Gaffer
import GafferTest

class BoxPlugTest( GafferTest.TestCase ) :

	def testRunTimeTyped( self ) :

		p = Gaffer.Box3fPlug()
		self.assertTrue( p.isInstanceOf( Gaffer.ValuePlug.staticTypeId() ) )
		self.assertTrue( p.isInstanceOf( Gaffer.Plug.staticTypeId() ) )

		t = p.typeId()
		self.assertEqual( IECore.RunTimeTyped.baseTypeId( t ), Gaffer.ValuePlug.staticTypeId() )

	def testCreateCounterpart( self ) :

		p1 = Gaffer.Box3fPlug( "b", Gaffer.Plug.Direction.Out, imath.Box3f( imath.V3f( -1 ), imath.V3f( 1 ) ), Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		p2 = p1.createCounterpart( "c", Gaffer.Plug.Direction.In )

		self.assertEqual( p2.getName(), "c" )
		self.assertEqual( p2.direction(), Gaffer.Plug.Direction.In )
		self.assertEqual( p2.defaultValue(), p1.defaultValue() )

	def testDynamicSerialisation( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["p"] = Gaffer.Box3fPlug( minValue=imath.V3f( -1 ), maxValue=imath.V3f( 1 ), flags=Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["p"].setValue( imath.Box3f( imath.V3f( -100 ), imath.V3f( 1, 2, 3 ) ) )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( s2["n"]["p"].getValue(), s["n"]["p"].getValue() )
		self.assertEqual( s2["n"]["p"].minValue(), s["n"]["p"].minValue() )
		self.assertEqual( s2["n"]["p"].maxValue(), s["n"]["p"].maxValue() )

	def testMinMax( self ) :

		b = Gaffer.Box3fPlug( "p", Gaffer.Plug.Direction.In, imath.Box3f( imath.V3f( -0.5 ), imath.V3f( 0.5 ) ) )
		v = Gaffer.V3fPlug()

		self.assertEqual( b.minValue(), v.minValue() )
		self.assertEqual( b.maxValue(), v.maxValue() )
		self.assertFalse( b.hasMinValue() )
		self.assertFalse( b.hasMaxValue() )
		self.assertEqual( b.minValue(), v.minValue() )
		self.assertEqual( b.maxValue(), v.maxValue() )

		b = Gaffer.Box3fPlug( "p", minValue = imath.V3f( -1, -2, -3 ), maxValue = imath.V3f( 1, 2, 3 ) )
		self.assertTrue( b.hasMinValue() )
		self.assertTrue( b.hasMaxValue() )
		self.assertEqual( b.minValue(), imath.V3f( -1, -2, -3 ) )
		self.assertEqual( b.maxValue(), imath.V3f( 1, 2, 3 ) )

		c = b.createCounterpart( "c", Gaffer.Plug.Direction.In )
		self.assertTrue( c.hasMinValue() )
		self.assertTrue( c.hasMaxValue() )
		self.assertEqual( c.minValue(), imath.V3f( -1, -2, -3 ) )
		self.assertEqual( c.maxValue(), imath.V3f( 1, 2, 3 ) )

	def testValueSerialisation( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["user"]["b"] = Gaffer.Box2iPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["user"]["i"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		def assertExpectedValues( numSetValueCalls ) :

			ss = s.serialise( filter = Gaffer.StandardSet( { s["n"] } ) )
			self.assertEqual( ss.count( "setValue" ), numSetValueCalls )

			s2 = Gaffer.ScriptNode()
			s2.execute( ss )

			self.assertEqual( s2["n"]["user"]["b"].getValue(), s["n"]["user"]["b"].getValue() )

		assertExpectedValues( 0 )

		s["n"]["user"]["b"].setValue( imath.Box2i( imath.V2i( 1, 2 ), imath.V2i( 3, 4 ) ) )
		assertExpectedValues( 1 ) # One setValue() call for plug b.

		s["n"]["user"]["b"]["min"]["x"].setInput( s["n"]["user"]["i"] )
		assertExpectedValues( 2 ) # One setValue() call for b.min.y, another for b.max.

		s["n"]["user"]["b"]["max"]["x"].setInput( s["n"]["user"]["i"] )
		assertExpectedValues( 2 ) # One setValue() call for b.min.y, another for b.max.y.

		s["n"]["user"]["b"]["max"]["y"].setInput( s["n"]["user"]["i"] )
		assertExpectedValues( 1 ) # One setValue() call for b.min.y

		s["n"]["user"]["b"]["min"]["y"].setInput( s["n"]["user"]["i"] )
		assertExpectedValues( 0 ) # All leaf plugs have inputs, so no setValue() calls needed.

	def testNoRedundantSetInputCalls( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["user"]["b1"] = Gaffer.Box2iPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["user"]["b2"] = Gaffer.Box2iPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		def assertExpectedInputs( numSetInputCalls ) :

			ss = s.serialise()
			self.assertEqual( ss.count( "setInput" ), numSetInputCalls )

			s2 = Gaffer.ScriptNode()
			s2.execute( ss )

			for p2 in [ s2["n"]["user"]["b2"] ] + list( Gaffer.Plug.RecursiveRange( s2["n"]["user"]["b2"] ) ) :
				p = s.descendant( p2.relativeName( s2 ) )
				i2 = p2.getInput()
				if i2 is not None :
					self.assertEqual( p.getInput().relativeName( s ), i2.relativeName( s2 ) )
				else :
					self.assertIsNone( p.getInput() )

		assertExpectedInputs( 0 )

		s["n"]["user"]["b2"]["min"]["x"].setInput( s["n"]["user"]["b1"]["min"]["y"] )
		assertExpectedInputs( 1 )

		s["n"]["user"]["b2"]["max"]["y"].setInput( s["n"]["user"]["b1"]["max"]["x"] )
		assertExpectedInputs( 2 )

		s["n"]["user"]["b2"]["max"].setInput( s["n"]["user"]["b1"]["max"] )
		assertExpectedInputs( 2 )

		s["n"]["user"]["b2"].setInput( s["n"]["user"]["b1"] )
		assertExpectedInputs( 1 )

if __name__ == "__main__":
	unittest.main()
