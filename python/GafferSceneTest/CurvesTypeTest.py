##########################################################################
#
#  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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
import os

import IECore

import Gaffer
import GafferTest

import GafferScene
import GafferSceneTest

class CurvesTypeTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		p = GafferSceneTest.CompoundObjectSource()
		curves = IECore.CurvesPrimitive( IECore.IntVectorData( [ 4 ] ), IECore.CubicBasisf.bSpline() )
		p["in"].setValue(
			IECore.CompoundObject( {
				"bound" : IECore.Box3fData( curves.bound() ),
				"children" : {
					"object" : {					
						"bound" : IECore.Box3fData( curves.bound() ),
						"object" : curves,
					},
				}
			} ),
		)

		c = GafferScene.CurvesType()
		c["in"].setInput( p["out"] )

		# Test unchanged settings.

		self.assertEqual( c["basis"].getValue(), "" ) # do nothing
		self.assertEqual( p["out"].object( "/object" ), c["out"].object( "/object" ) )
		self.assertScenesEqual( p["out"], c["out"] )

		# Test converting bSpline to bSpline ( shouldn't do anything )

		c["basis"].setValue( "bSpline" )

		self.assertEqual( p["out"].object( "/object" ), c["out"].object( "/object" ) )
		self.assertScenesEqual( p["out"], c["out"] )

		# Test converting bSpline to catmullRom

		c["basis"].setValue( "catmullRom" )

		self.assertNotEqual( p["out"].object( "/object" ), c["out"].object( "/object" ) )
		self.assertSceneHashesEqual( p["out"], c["out"], childPlugNames = ( "attributes", "bound", "transform", "globals", "childNames" ) )

		self.assertScenesEqual( p["out"], c["out"], pathsToIgnore = ( "/object", ) )

		self.assertEqual( c["out"].object( "/object" ).basis(), IECore.CubicBasisf.catmullRom() )

		# Test converting to linear

		m2 = GafferScene.CurvesType()
		m2["in"].setInput( c["out"] )

		m2["basis"].setValue( "linear" )
		self.assertEqual( m2["out"].object( "/object" ).basis(), IECore.CubicBasisf.linear() )

	def testNonPrimitiveObject( self ) :

		c = GafferScene.Camera()

		d = GafferScene.CurvesType()
		d["in"].setInput( c["out"] )

		self.assertSceneValid( d["out"] )
		self.failUnless( isinstance( d["out"].object( "/camera" ), IECore.Camera ) )
		self.assertEqual( d["out"].object( "/camera" ), c["out"].object( "/camera" ) )

	def testEnabledPlugAffects( self ) :

		n = GafferScene.CurvesType()
		cs = GafferTest.CapturingSlot( n.plugDirtiedSignal() )

		n["enabled"].setValue( False )
		self.assertTrue( len( cs ) )
		self.assertTrue( cs[-1][0].isSame( n["out"] ) )


if __name__ == "__main__":
	unittest.main()
