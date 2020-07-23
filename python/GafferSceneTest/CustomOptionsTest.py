##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
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
import IECoreScene

import Gaffer
import GafferTest
import GafferScene
import GafferSceneTest

class CustomOptionsTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		p = GafferScene.Plane()
		options = GafferScene.CustomOptions()
		options["in"].setInput( p["out"] )

		# check that the scene hierarchy is passed through

		self.assertEqual( options["out"].object( "/" ), IECore.NullObject() )
		self.assertEqual( options["out"].transform( "/" ), imath.M44f() )
		self.assertEqual( options["out"].bound( "/" ), imath.Box3f( imath.V3f( -0.5, -0.5, 0 ), imath.V3f( 0.5, 0.5, 0 ) ) )
		self.assertEqual( options["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "plane" ] ) )

		self.assertEqual( options["out"].object( "/plane" ), IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -0.5 ), imath.V2f( 0.5 ) ) ) )
		self.assertEqual( options["out"].transform( "/plane" ), imath.M44f() )
		self.assertEqual( options["out"].bound( "/plane" ), imath.Box3f( imath.V3f( -0.5, -0.5, 0 ), imath.V3f( 0.5, 0.5, 0 ) ) )
		self.assertEqual( options["out"].childNames( "/plane" ), IECore.InternedStringVectorData() )

		# check that we can make options

		options["options"].addChild( Gaffer.NameValuePlug( "test", IECore.IntData( 10 ) ) )
		options["options"].addChild( Gaffer.NameValuePlug( "test2", IECore.StringData( "10" ) ) )

		g = options["out"]["globals"].getValue()
		self.assertEqual( len( g ), 2 )
		self.assertEqual( g["option:test"], IECore.IntData( 10 ) )
		self.assertEqual( g["option:test2"], IECore.StringData( "10" ) )

	def testSerialisation( self ) :

		s = Gaffer.ScriptNode()
		s["optionsNode"] = GafferScene.CustomOptions()
		s["optionsNode"]["options"].addChild( Gaffer.NameValuePlug( "test", IECore.IntData( 10 ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		s["optionsNode"]["options"].addChild( Gaffer.NameValuePlug( "test2", IECore.StringData( "10" ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )

		ss = s.serialise()

		s2 = Gaffer.ScriptNode()
		s2.execute( ss )

		g = s2["optionsNode"]["out"]["globals"].getValue()
		self.assertEqual( len( g ), 2 )
		self.assertEqual( g["option:test"], IECore.IntData( 10 ) )
		self.assertEqual( g["option:test2"], IECore.StringData( "10" ) )
		self.assertTrue( "options1" not in s2["optionsNode"] )

	def testHashPassThrough( self ) :

		# The hash of everything except the globals should be
		# identical to the input, so that they share cache entries.

		p = GafferScene.Plane()
		options = GafferScene.CustomOptions()
		options["in"].setInput( p["out"] )
		options["options"].addChild( Gaffer.NameValuePlug( "test", IECore.IntData( 10 ) ) )

		self.assertSceneHashesEqual( p["out"], options["out"], checks = self.allSceneChecks - { "globals" } )

	def testDisabled( self ) :

		p = GafferScene.Plane()
		options = GafferScene.CustomOptions()
		options["in"].setInput( p["out"] )
		options["options"].addChild( Gaffer.NameValuePlug( "test", IECore.IntData( 10 ) ) )

		self.assertSceneHashesEqual( p["out"], options["out"], checks = self.allSceneChecks - { "globals" } )
		self.assertNotEqual( options["out"]["globals"].hash(), p["out"]["globals"].hash() )

		options["enabled"].setValue( False )

		self.assertSceneHashesEqual( p["out"], options["out"] )
		self.assertScenesEqual( p["out"], options["out"] )

	def testDirtyPropagation( self ) :

		p = GafferScene.Plane()
		o = GafferScene.CustomOptions()

		o["in"].setInput( p["out"] )

		cs = GafferTest.CapturingSlot( o.plugDirtiedSignal() )

		p["dimensions"]["x"].setValue( 100.1 )

		dirtiedPlugs = { x[0] for x in cs if not x[0].getName().startswith( "__" ) }
		self.assertEqual(
			dirtiedPlugs,
			{
				o["in"]["bound"],
				o["in"]["childBounds"],
				o["in"]["object"],
				o["in"],
				o["out"]["bound"],
				o["out"]["childBounds"],
				o["out"]["object"],
				o["out"],
			}
		)

	def testSubstitution( self ) :

		o = GafferScene.CustomOptions()
		o["options"].addChild( Gaffer.NameValuePlug( "test", "${foo}" ) )

		self.assertEqual( o["out"]["globals"].getValue()["option:test"], IECore.StringData( "" ) )
		h = o["out"]["globals"].hash()

		c = Gaffer.Context()
		c["foo"] = "foo"

		with c :
			self.assertNotEqual( o["out"]["globals"].hash(), h )
			self.assertEqual( o["out"]["globals"].getValue()["option:test"], IECore.StringData( "foo" ) )

	def testDirtyPropagationOnMemberAdditionAndRemoval( self ) :

		o = GafferScene.CustomOptions()
		cs = GafferTest.CapturingSlot( o.plugDirtiedSignal() )

		p = Gaffer.NameValuePlug( "test", IECore.IntData( 10 ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		o["options"].addChild( p )
		self.assertTrue( o["out"]["globals"] in [ c[0] for c in cs ] )

		del cs[:]
		o["options"].removeChild( p )
		self.assertTrue( o["out"]["globals"] in [ c[0] for c in cs ] )

	def testSetsPassThrough( self ) :

		p = GafferScene.Plane()
		p["sets"].setValue( "a b" )

		o = GafferScene.CustomOptions()
		o["in"].setInput( p["out"] )

		self.assertEqual( p["out"]["setNames"].hash(), o["out"]["setNames"].hash() )
		self.assertTrue( p["out"]["setNames"].getValue( _copy = False ).isSame( o["out"]["setNames"].getValue( _copy = False ) ) )

		self.assertEqual( p["out"].setHash( "a" ), o["out"].setHash( "b" ) )
		self.assertTrue( p["out"].set( "a", _copy = False ).isSame( o["out"].set( "b", _copy = False ) ) )

	def testPrefix( self ) :

		options = GafferScene.CustomOptions()

		options["options"].addChild( Gaffer.NameValuePlug( "test", IECore.IntData( 10 ) ) )
		options["prefix"].setValue( "myCategory:" )

		g = options["out"]["globals"].getValue()

		self.assertEqual( g["option:myCategory:test"], IECore.IntData( 10 ) )

if __name__ == "__main__":
	unittest.main()
