##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
#  Copyright (c) 2013-2014, Image Engine Design Inc. All rights reserved.
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

class TransformPlugTest( GafferTest.TestCase ) :

	def testMatrix( self ) :

		p = Gaffer.TransformPlug()

		p["translate"].setValue( imath.V3f( 1, 2, 3 ) )
		p["rotate"].setValue( imath.V3f( 90, 45, 0 ) )
		p["scale"].setValue( imath.V3f( 1, 2, 4 ) )

		translate = imath.M44f().translate( p["translate"].getValue() )
		rotate = imath.Eulerf( IECore.degreesToRadians( p["rotate"].getValue() ), imath.Eulerf.Order.XYZ )
		rotate = rotate.toMatrix44()
		scale = imath.M44f().scale( p["scale"].getValue() )
		transforms = {
			"t" : translate,
			"r" : rotate,
			"s" : scale,
		}
		transform = imath.M44f()
		for m in ( "s", "r", "t" ) :
			transform = transform * transforms[m]

		self.assertEqual( p.matrix(), transform )

	def testTransformOrderExplicit( self ) :

		p = Gaffer.TransformPlug()

		t =	imath.V3f( 100, 0, 0 )
		r =	imath.V3f( 0, 90, 0 )
		s =	imath.V3f( 2, 2, 2 )
		p["translate"].setValue(  t )
		p["rotate"].setValue( r )
		p["scale"].setValue( s )

		# Test if this is equal to a simple hardcoded matrix, down to floating point error
		# This verifies that translation is not being affected by rotation and scale,
		# which is what users will expect
		self.assertTrue( p.matrix().equalWithAbsError(
			imath.M44f(
				0,   0,  -2,   0,
				0,   2,   0,   0,
				2,   0,   0,   0,
				100, 0,   0,   1 ),
			1e-6
		) )

	def testCreateCounterpart( self ) :

		t = Gaffer.TransformPlug()
		t2 = t.createCounterpart( "a", Gaffer.Plug.Direction.Out )

		self.assertEqual( t2.getName(), "a" )
		self.assertEqual( t2.direction(), Gaffer.Plug.Direction.Out )
		self.assertTrue( isinstance( t2, Gaffer.TransformPlug ) )

	def testRunTimeTyped( self ) :

		p = Gaffer.TransformPlug()
		self.assertNotEqual( p.typeId(), Gaffer.ValuePlug.staticTypeId() )
		self.assertTrue( p.isInstanceOf( Gaffer.ValuePlug.staticTypeId() ) )

	def testPivot( self ) :

		p = Gaffer.TransformPlug()

		p["rotate"].setValue( imath.V3f( 0, 90, 0 ) )

		self.assertTrue(
			imath.V3f( 0, 0, -1 ).equalWithAbsError(
				imath.V3f( 1, 0, 0 ) * p.matrix(),
				1e-6
			)
		)

		p["pivot"].setValue( imath.V3f( 1, 0, 0 ) )

		self.assertTrue(
			imath.V3f( 1, 0, 0 ).equalWithAbsError(
				imath.V3f( 1, 0, 0 ) * p.matrix(),
				1e-6
			)
		)

		p["pivot"].setValue( imath.V3f( -1, 0, 0 ) )

		self.assertTrue(
			imath.V3f( -1, 0, -2 ).equalWithAbsError(
				imath.V3f( 1, 0, 0 ) * p.matrix(),
				1e-6
			)
		)

		p["rotate"].setValue( imath.V3f( 0, 0, 0 ) )
		p["scale"].setValue( imath.V3f( 2, 1, 1 ) )

		self.assertTrue(
			imath.V3f( 3, 0, 0 ).equalWithAbsError(
				imath.V3f( 1, 0, 0 ) * p.matrix(),
				1e-6
			)
		)

	def testDynamicSerialisation( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["p"] = Gaffer.TransformPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["p"]["translate"].setValue( imath.V3f( 1, 2, 3 ) )
		s["n"]["p"]["rotate"].setValue( imath.V3f( 4, 5, 6 ) )
		ss = s.serialise()

		s2 = Gaffer.ScriptNode()
		s2.execute( ss )

		self.assertEqual( s2["n"]["p"]["translate"].getValue(), imath.V3f( 1, 2, 3 ) )
		self.assertEqual( s2["n"]["p"]["rotate"].getValue(), imath.V3f( 4, 5, 6 ) )

if __name__ == "__main__":
	unittest.main()
