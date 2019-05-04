##########################################################################
#
#  Copyright (c) 2014, John Haddon. All rights reserved.
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

import imath

import IECore
import IECoreScene

import Gaffer
import GafferScene
import GafferSceneTest

class PrimitiveVariablesTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		s = GafferScene.Sphere()
		p = GafferScene.PrimitiveVariables()
		p["in"].setInput( s["out"] )

		self.assertScenesEqual( s["out"], p["out"] )
		self.assertSceneHashesEqual( s["out"], p["out"] )

		p["primitiveVariables"].addChild( Gaffer.NameValuePlug( "a", IECore.IntData( 10 ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )

		self.assertScenesEqual( s["out"], p["out"], checks = self.allSceneChecks - { "object" } )
		self.assertSceneHashesEqual( s["out"], p["out"], checks = self.allSceneChecks - { "object" } )

		self.assertNotEqual( s["out"].objectHash( "/sphere" ), p["out"].objectHash( "/sphere" ) )
		self.assertNotEqual( s["out"].object( "/sphere" ), p["out"].object( "/sphere" ) )

		o1 = s["out"].object( "/sphere" )
		o2 = p["out"].object( "/sphere" )

		self.assertEqual( set( o1.keys() + [ "a" ] ), set( o2.keys() ) )
		self.assertEqual( o2["a"], IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Constant, IECore.IntData( 10 ) ) )

		del o2["a"]
		self.assertEqual( o1, o2 )

	def testGeometricInterpretation( self ) :

		s = GafferScene.Sphere()
		p = GafferScene.PrimitiveVariables()
		p["in"].setInput( s["out"] )

		p["primitiveVariables"].addChild( Gaffer.NameValuePlug( "myFirstData", IECore.V3fData( imath.V3f( 0 ), IECore.GeometricData.Interpretation.Vector ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		p["primitiveVariables"].addChild( Gaffer.NameValuePlug( "mySecondData", IECore.V3fData( imath.V3f( 0 ), IECore.GeometricData.Interpretation.Normal ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		p["primitiveVariables"].addChild( Gaffer.NameValuePlug( "myThirdData", IECore.V3fData( imath.V3f( 0 ), IECore.GeometricData.Interpretation.Point ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )

		o = p["out"].object( "/sphere" )

		# test if the geometric interpretation makes it into the primitive variable
		self.assertEqual( o["myFirstData"].data.getInterpretation(), IECore.GeometricData.Interpretation.Vector )
		self.assertEqual( o["mySecondData"].data.getInterpretation(), IECore.GeometricData.Interpretation.Normal )
		self.assertEqual( o["myThirdData"].data.getInterpretation(), IECore.GeometricData.Interpretation.Point )

		del o["myFirstData"]
		del o["mySecondData"]
		del o["myThirdData"]

		self.assertFalse( 'myFirstData' in o )
		self.assertFalse( 'mySecondData' in o )
		self.assertFalse( 'myThirdData' in o )

		p["primitiveVariables"].addChild( Gaffer.NameValuePlug( "myFirstData", IECore.V3fData( imath.V3f( 0 ), IECore.GeometricData.Interpretation.Point ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		p["primitiveVariables"].addChild( Gaffer.NameValuePlug( "mySecondData", IECore.V3fData( imath.V3f( 0 ), IECore.GeometricData.Interpretation.Vector ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		p["primitiveVariables"].addChild( Gaffer.NameValuePlug( "myThirdData", IECore.V3fData( imath.V3f( 0 ), IECore.GeometricData.Interpretation.Normal ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )

		o = p["out"].object( "/sphere" )

		# test if the new geometric interpretation makes it into the primitive variable
		# this tests the hashing on the respective plugs
		self.assertEqual( o["myFirstData"].data.getInterpretation(), IECore.GeometricData.Interpretation.Point )
		self.assertEqual( o["mySecondData"].data.getInterpretation(), IECore.GeometricData.Interpretation.Vector )
		self.assertEqual( o["myThirdData"].data.getInterpretation(), IECore.GeometricData.Interpretation.Normal )

if __name__ == "__main__":
	unittest.main()
