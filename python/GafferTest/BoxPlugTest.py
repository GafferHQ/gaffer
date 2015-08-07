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

class BoxPlugTest( GafferTest.TestCase ) :

	def testRunTimeTyped( self ) :

		p = Gaffer.Box3fPlug()
		self.failUnless( p.isInstanceOf( Gaffer.ValuePlug.staticTypeId() ) )
		self.failUnless( p.isInstanceOf( Gaffer.Plug.staticTypeId() ) )

		t = p.typeId()
		self.assertEqual( IECore.RunTimeTyped.baseTypeId( t ), Gaffer.ValuePlug.staticTypeId() )

	def testCreateCounterpart( self ) :

		p1 = Gaffer.Box3fPlug( "b", Gaffer.Plug.Direction.Out, IECore.Box3f( IECore.V3f( -1 ), IECore.V3f( 1 ) ), Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		p2 = p1.createCounterpart( "c", Gaffer.Plug.Direction.In )

		self.assertEqual( p2.getName(), "c" )
		self.assertEqual( p2.direction(), Gaffer.Plug.Direction.In )
		self.assertEqual( p2.defaultValue(), p1.defaultValue() )

	def testDynamicSerialisation( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["p"] = Gaffer.Box3fPlug( minValue=IECore.V3f( -1 ), maxValue=IECore.V3f( 1 ), flags=Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["p"].setValue( IECore.Box3f( IECore.V3f( -100 ), IECore.V3f( 1, 2, 3 ) ) )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( s2["n"]["p"].getValue(), s["n"]["p"].getValue() )
		self.assertEqual( s2["n"]["p"].minValue(), s["n"]["p"].minValue() )
		self.assertEqual( s2["n"]["p"].maxValue(), s["n"]["p"].maxValue() )

	def testMinMax( self ) :

		b = Gaffer.Box3fPlug( "p", Gaffer.Plug.Direction.In, IECore.Box3f( IECore.V3f( -0.5 ), IECore.V3f( 0.5 ) ) )
		v = Gaffer.V3fPlug()

		self.assertEqual( b.minValue(), v.minValue() )
		self.assertEqual( b.maxValue(), v.maxValue() )
		self.assertFalse( b.hasMinValue() )
		self.assertFalse( b.hasMaxValue() )
		self.assertEqual( b.minValue(), v.minValue() )
		self.assertEqual( b.maxValue(), v.maxValue() )

		b = Gaffer.Box3fPlug( "p", minValue = IECore.V3f( -1, -2, -3 ), maxValue = IECore.V3f( 1, 2, 3 ) )
		self.assertTrue( b.hasMinValue() )
		self.assertTrue( b.hasMaxValue() )
		self.assertEqual( b.minValue(), IECore.V3f( -1, -2, -3 ) )
		self.assertEqual( b.maxValue(), IECore.V3f( 1, 2, 3 ) )

		c = b.createCounterpart( "c", Gaffer.Plug.Direction.In )
		self.assertTrue( c.hasMinValue() )
		self.assertTrue( c.hasMaxValue() )
		self.assertEqual( c.minValue(), IECore.V3f( -1, -2, -3 ) )
		self.assertEqual( c.maxValue(), IECore.V3f( 1, 2, 3 ) )

if __name__ == "__main__":
	unittest.main()

