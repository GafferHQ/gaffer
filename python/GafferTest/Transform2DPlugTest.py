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
#      * Neither the name of Image Engine Design nor the names of
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

class Transform2DPlugTest( GafferTest.TestCase ) :

	def testMatrix( self ) :

		p = Gaffer.Transform2DPlug()

		p["pivot"].setValue( imath.V2f( 1, 1 ) )
		p["translate"].setValue( imath.V2f( 1, 2 ) )
		p["rotate"].setValue( 45 )
		p["scale"].setValue( imath.V2f( 2, 3 ) )

		pivotValue = p["pivot"].getValue()
		pivot = imath.M33f().translate( pivotValue )

		translateValue = p["translate"].getValue()
		translate = imath.M33f().translate( translateValue )

		rotate = imath.M33f().rotate( IECore.degreesToRadians( p["rotate"].getValue() ) )
		scale = imath.M33f().scale( p["scale"].getValue() )
		invPivot = imath.M33f().translate( pivotValue * imath.V2f(-1.) )

		transforms = {
			"p" : pivot,
			"t" : translate,
			"r" : rotate,
			"s" : scale,
			"pi" : invPivot,
		}

		transform = imath.M33f()
		for m in ( "pi", "s", "r", "t", "p" ) :
			transform = transform * transforms[m]

		self.assertEqual( p.matrix(), transform )

	def testTransformOrderExplicit( self ) :

		plug = Gaffer.Transform2DPlug()

		displayWindow = imath.Box2i( imath.V2i(0), imath.V2i(9) )
		pixelAspect = 1.

		t =	imath.V2f( 100, 0 )
		r =	90
		s =	imath.V2f( 2, 2 )
		p = imath.V2f( 10, -10 )
		plug["translate"].setValue(  t )
		plug["rotate"].setValue( r )
		plug["scale"].setValue( s )
		plug["pivot"].setValue( p )

		# Test if this is equal to a simple hardcoded matrix, down to floating point error
		# This verifies that translation is not being affected by rotation and scale,
		# which is what users will expect
		self.assertTrue( plug.matrix().equalWithAbsError(
			imath.M33f(
				0,   2, 0,
				-2,  0, 0,
				90, -30, 1),
			2e-6
		) )

	def testCreateCounterpart( self ) :

		t = Gaffer.Transform2DPlug()
		t2 = t.createCounterpart( "a", Gaffer.Plug.Direction.Out )

		self.assertEqual( t2.getName(), "a" )
		self.assertEqual( t2.direction(), Gaffer.Plug.Direction.Out )
		self.assertTrue( isinstance( t2, Gaffer.Transform2DPlug ) )

	def testRunTimeTyped( self ) :

		p = Gaffer.Transform2DPlug()
		self.assertNotEqual( p.typeId(), Gaffer.ValuePlug.staticTypeId() )
		self.assertTrue( p.isInstanceOf( Gaffer.ValuePlug.staticTypeId() ) )

	def testDefaultValues( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["user"]["p"] = Gaffer.Transform2DPlug(
			defaultTranslate = imath.V2f( 1, 2 ),
			defaultRotate = 3,
			defaultScale = imath.V2f( 4, 5 ),
			defaultPivot = imath.V2f( 6, 7 ),
			flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic
		)
		self.assertEqual( s["n"]["user"]["p"]["translate"].defaultValue(), imath.V2f( 1, 2 ) )
		self.assertEqual( s["n"]["user"]["p"]["rotate"].defaultValue(), 3 )
		self.assertEqual( s["n"]["user"]["p"]["scale"].defaultValue(), imath.V2f( 4, 5 ) )
		self.assertEqual( s["n"]["user"]["p"]["pivot"].defaultValue(), imath.V2f( 6, 7 ) )

		s["n"]["user"]["p2"] = s["n"]["user"]["p"].createCounterpart( "p2", Gaffer.Plug.Direction.In )
		self.assertEqual( s["n"]["user"]["p2"]["translate"].defaultValue(), imath.V2f( 1, 2 ) )
		self.assertEqual( s["n"]["user"]["p2"]["rotate"].defaultValue(), 3 )
		self.assertEqual( s["n"]["user"]["p2"]["scale"].defaultValue(), imath.V2f( 4, 5 ) )
		self.assertEqual( s["n"]["user"]["p2"]["pivot"].defaultValue(), imath.V2f( 6, 7 ) )

		s["n"]["user"]["p2"]["translate"].setValue( imath.V2f( -1, -2 ) )
		s["n"]["user"]["p2"]["translate"].resetDefault()
		self.assertEqual( s["n"]["user"]["p2"]["translate"].defaultValue(), imath.V2f( -1, -2 ) )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( s2["n"]["user"]["p"]["translate"].defaultValue(), imath.V2f( 1, 2 ) )
		self.assertEqual( s2["n"]["user"]["p"]["rotate"].defaultValue(), 3 )
		self.assertEqual( s2["n"]["user"]["p"]["scale"].defaultValue(), imath.V2f( 4, 5 ) )
		self.assertEqual( s2["n"]["user"]["p"]["pivot"].defaultValue(), imath.V2f( 6, 7 ) )
		self.assertEqual( s2["n"]["user"]["p2"]["translate"].defaultValue(), imath.V2f( -1, -2 ) )
		self.assertEqual( s2["n"]["user"]["p2"]["rotate"].defaultValue(), 3 )
		self.assertEqual( s2["n"]["user"]["p2"]["scale"].defaultValue(), imath.V2f( 4, 5 ) )
		self.assertEqual( s2["n"]["user"]["p2"]["pivot"].defaultValue(), imath.V2f( 6, 7 ) )

if __name__ == "__main__":
	unittest.main()
