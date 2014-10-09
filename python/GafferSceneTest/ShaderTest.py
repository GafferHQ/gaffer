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
import GafferScene
import GafferSceneTest

class ShaderTest( unittest.TestCase ) :

	def testDirtyPropagation( self ) :

		s = GafferSceneTest.TestShader( "s" )

		cs = GafferTest.CapturingSlot( s.plugDirtiedSignal() )

		s["parameters"]["i"].setValue( 10 )

		d = set( [ a[0].fullName() for a in cs ] )

		self.assertTrue( "s.out" in d )
		self.assertTrue( "s.out.r" in d )
		self.assertTrue( "s.out.g" in d )
		self.assertTrue( "s.out.b" in d )

	def testDisabling( self ) :

		s = GafferSceneTest.TestShader()

		self.assertTrue( s["enabled"].isSame( s.enabledPlug() ) )
		self.assertEqual( s.correspondingInput( s["out"] ), None )

		h = s.stateHash()
		self.assertEqual( len( s.state() ), 1 )

		s["enabled"].setValue( False )

		self.assertEqual( len( s.state() ), 0 )
		self.assertNotEqual( s.stateHash(), h )

	def testNodeNameBlindData( self ) :

		s = GafferSceneTest.TestShader( "node1" )

		h1 = s.stateHash()
		s1 = s.state()

		cs = GafferTest.CapturingSlot( s.plugDirtiedSignal() )

		s.setName( "node2" )

		self.assertTrue( s["out"] in [ x[0] for x in cs ] )

		self.assertNotEqual( s.stateHash(), h1 )

		s2 = s.state()
		self.assertNotEqual( s2, s1 )

		self.assertEqual( s1[0].blindData()["gaffer:nodeName"], IECore.StringData( "node1" ) )
		self.assertEqual( s2[0].blindData()["gaffer:nodeName"], IECore.StringData( "node2" ) )

	def testShaderTypesInState( self ) :

		surface = GafferSceneTest.TestShader( "surface" )
		surface["name"].setValue( "testSurface" )
		surface["type"].setValue( "test:surface" )
		surface["parameters"]["t"] = Gaffer.Color3fPlug()

		texture = GafferSceneTest.TestShader( "texture" )
		texture["name"].setValue( "testTexture" )
		texture["type"].setValue( "test:shader" )

		surface["parameters"]["t"].setInput( texture["out"] )

		state = surface.state()
		self.assertEqual( state[0].type, "test:shader" )
		self.assertEqual( state[1].type, "test:surface" )

if __name__ == "__main__":
	unittest.main()
