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

class ShaderTest( GafferSceneTest.SceneTestCase ) :

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

		h = s.attributesHash()
		self.assertEqual( len( s.attributes() ), 1 )

		s["enabled"].setValue( False )

		self.assertEqual( len( s.attributes() ), 0 )
		self.assertNotEqual( s.attributesHash(), h )

	def testNodeNameBlindData( self ) :

		s = GafferSceneTest.TestShader( "node1" )
		s["type"].setValue( "test:surface" )

		h1 = s.attributesHash()
		s1 = s.attributes()["test:surface"]
		cs = GafferTest.CapturingSlot( s.plugDirtiedSignal() )

		s.setName( "node2" )

		self.assertTrue( s["out"] in [ x[0] for x in cs ] )

		self.assertNotEqual( s.attributesHash(), h1 )

		s2 = s.attributes()["test:surface"]
		self.assertNotEqual( s2, s1 )

		self.assertEqual( s1[0].blindData()["gaffer:nodeName"], IECore.StringData( "node1" ) )
		self.assertEqual( s2[0].blindData()["gaffer:nodeName"], IECore.StringData( "node2" ) )

	def testNodeColorBlindData( self ) :

		s = GafferSceneTest.TestShader()
		s["type"].setValue( "test:surface" )

		h1 = s.attributesHash()
		s1 = s.attributes()["test:surface"]

		cs = GafferTest.CapturingSlot( s.plugDirtiedSignal() )

		Gaffer.Metadata.registerValue( s, "nodeGadget:color", IECore.Color3f( 1, 0, 0 ) )

		self.assertTrue( s["out"] in [ x[0] for x in cs ] )

		self.assertNotEqual( s.attributesHash(), h1 )

		s2 = s.attributes()["test:surface"]
		self.assertNotEqual( s2, s1 )

		self.assertEqual( s1[0].blindData()["gaffer:nodeColor"], IECore.Color3fData( IECore.Color3f( 0 ) ) )
		self.assertEqual( s2[0].blindData()["gaffer:nodeColor"], IECore.Color3fData( IECore.Color3f( 1, 0, 0 ) ) )

	def testShaderTypesInAttributes( self ) :

		surface = GafferSceneTest.TestShader( "surface" )
		surface["name"].setValue( "testSurface" )
		surface["type"].setValue( "test:surface" )
		surface["parameters"]["t"] = Gaffer.Color3fPlug()

		texture = GafferSceneTest.TestShader( "texture" )
		texture["name"].setValue( "testTexture" )
		texture["type"].setValue( "test:shader" )

		surface["parameters"]["t"].setInput( texture["out"] )

		network = surface.attributes()["test:surface"]
		self.assertEqual( network[0].type, "test:shader" )
		self.assertEqual( network[1].type, "test:surface" )

	def testDirtyPropagationThroughShaderAssignment( self ) :

		n = GafferSceneTest.TestShader()

		p = GafferScene.Plane()
		a = GafferScene.ShaderAssignment()
		a["in"].setInput( p["out"] )
		a["shader"].setInput( n["out"] )

		cs = GafferTest.CapturingSlot( a.plugDirtiedSignal() )

		n["parameters"]["i"].setValue( 1 )

		self.assertEqual(
			[ c[0] for c in cs ],
			[
				a["shader"],
				a["out"]["attributes"],
				a["out"],
			],
		)

	def testDetectCyclicConnections( self ) :

		n1 = GafferSceneTest.TestShader()
		n2 = GafferSceneTest.TestShader()
		n3 = GafferSceneTest.TestShader()

		n2["parameters"]["i"].setInput( n1["out"]["r"] )
		n3["parameters"]["i"].setInput( n2["out"]["g"] )

		with IECore.CapturingMessageHandler() as mh :
			n1["parameters"]["i"].setInput( n3["out"]["b"] )

		# We expect a message warning of the cycle when the
		# connection is made.
		self.assertEqual( len( mh.messages ), 1 )
		self.assertTrue( "Plug dirty propagation" in mh.messages[0].context )

		# And a hard error when we attempt to actually generate
		# the shader network.
		for node in ( n1, n2, n3 ) :
			self.assertRaisesRegexp( RuntimeError, "cycle", node.attributesHash )
			self.assertRaisesRegexp( RuntimeError, "cycle", node.attributes )

if __name__ == "__main__":
	unittest.main()
