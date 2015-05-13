##########################################################################
#
#  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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

class SetTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		p = GafferScene.Plane()
		s = GafferScene.Set()
		s["in"].setInput( p["out"] )

		s["paths"].setValue( IECore.StringVectorData( [ "/one", "/plane" ] ) )

		# Sets have nothing to do with globals.
		self.assertEqual( s["out"]["globals"].getValue(), p["out"]["globals"].getValue() )
		self.assertEqual( s["out"]["globals"].hash(), p["out"]["globals"].hash() )

		self.assertEqual( s["out"]["setNames"].getValue(), IECore.InternedStringVectorData( [ "set" ] ) )
		self.assertEqual( set( s["out"].set( "set" ).value.paths() ), set( [ "/one", "/plane" ] ) )

		s["name"].setValue( "shinyThings" )

		self.assertEqual( s["out"]["setNames"].getValue(), IECore.InternedStringVectorData( [ "shinyThings" ] ) )
		self.assertEqual( set( s["out"].set( "shinyThings" ).value.paths() ), set( [ "/one", "/plane" ] ) )

		s["paths"].setValue( IECore.StringVectorData( [ "/two", "/sphere" ] ) )

		self.assertEqual( s["out"]["setNames"].getValue(), IECore.InternedStringVectorData( [ "shinyThings" ] ) )
		self.assertEqual( set( s["out"].set( "shinyThings" ).value.paths() ), set( [ "/two", "/sphere" ] ) )

	def testInputNotModified( self ) :

		s1 = GafferScene.Set()
		s1["name"].setValue( "setOne" )
		s1["paths"].setValue( IECore.StringVectorData( [ "/one" ] ) )

		s2 = GafferScene.Set()
		s2["in"].setInput( s1["out"] )
		s2["name"].setValue( "setTwo" )
		s2["paths"].setValue( IECore.StringVectorData( [ "/two" ] ) )

		self.assertEqual( s1["out"]["setNames"].getValue(), IECore.InternedStringVectorData( [ "setOne" ] ) )
		self.assertEqual( s1["out"].set( "setOne" ).value.paths(), [ "/one" ] )

		self.assertEqual( s2["out"]["setNames"].getValue(), IECore.InternedStringVectorData( [ "setOne", "setTwo" ] ) )
		self.assertEqual( s2["out"].set( "setOne" ).value.paths(), [ "/one" ] )
		self.assertEqual( s2["out"].set( "setTwo" ).value.paths(), [ "/two" ] )
		self.assertTrue( s2["out"].set( "setOne", _copy = False ).isSame( s1["out"].set( "setOne", _copy = False ) ) )

	def testOverwrite( self ) :

		s1 = GafferScene.Set()
		s1["paths"].setValue( IECore.StringVectorData( [ "/old"] ) )

		s2 = GafferScene.Set()
		s2["paths"].setValue( IECore.StringVectorData( [ "/new"] ) )
		s2["in"].setInput( s1["out"] )

		self.assertEqual( s1["out"]["setNames"].getValue(), IECore.InternedStringVectorData( [ "set" ] ) )
		self.assertEqual( s1["out"].set( "set" ).value.paths(), [ "/old" ] )

		self.assertEqual( s2["out"]["setNames"].getValue(), IECore.InternedStringVectorData( [ "set" ] ) )
		self.assertEqual( s2["out"].set( "set" ).value.paths(), [ "/new" ] )

	def testAdd( self ) :

		s1 = GafferScene.Set()
		s1["paths"].setValue( IECore.StringVectorData( [ "/old"] ) )

		s2 = GafferScene.Set()
		s2["paths"].setValue( IECore.StringVectorData( [ "/new"] ) )
		s2["mode"].setValue( s2.Mode.Add )
		s2["in"].setInput( s1["out"] )

		self.assertEqual( s2["out"]["setNames"].getValue(), IECore.InternedStringVectorData( [ "set" ] ) )
		self.assertEqual( set( s2["out"].set( "set" ).value.paths() ), set( [ "/old", "/new" ] ) )

		s1["enabled"].setValue( False )

		self.assertEqual( s2["out"]["setNames"].getValue(), IECore.InternedStringVectorData( [ "set" ] ) )
		self.assertEqual( s2["out"].set( "set" ).value.paths(), [ "/new" ] )

	def testRemove( self ) :

		s1 = GafferScene.Set()
		s1["paths"].setValue( IECore.StringVectorData( [ "/a", "/b" ] ) )

		s2 = GafferScene.Set()
		s2["paths"].setValue( IECore.StringVectorData( [ "/a"] ) )
		s2["mode"].setValue( s2.Mode.Remove )
		s2["in"].setInput( s1["out"] )

		self.assertEqual( s2["out"]["setNames"].getValue(), IECore.InternedStringVectorData( [ "set" ] ) )
		self.assertEqual( s2["out"].set( "set" ).value.paths(), [ "/b" ] )

		s2["enabled"].setValue( False )

		self.assertEqual( s2["out"]["setNames"].getValue(), IECore.InternedStringVectorData( [ "set" ] ) )
		self.assertEqual( set( s2["out"].set( "set" ).value.paths() ), set( [ "/a", "/b" ] ) )

	def testRemoveFromNonExistentSet( self ) :

		p = GafferScene.Plane()

		s1 = GafferScene.Set()
		s1["paths"].setValue( IECore.StringVectorData( [ "/a", "/b" ] ) )

		s2 = GafferScene.Set()
		s2["paths"].setValue( IECore.StringVectorData( [ "/a"] ) )
		s2["name"].setValue( "thisSetDoesNotExist" )
		s2["mode"].setValue( s2.Mode.Remove )
		s2["in"].setInput( s1["out"] )

		self.assertEqual( s2["out"]["setNames"].getValue(), IECore.InternedStringVectorData( [ "set" ] ) )
		self.assertEqual( set( s2["out"].set( "set" ).value.paths() ), set( [ "/a", "/b" ] ) )

	def testDisabled( self ) :

		s1 = GafferScene.Set()
		s1["paths"].setValue( IECore.StringVectorData( [ "/a" ] ) )

		s2 = GafferScene.Set()
		s2["in"].setInput( s1["out"] )
		s2["paths"].setValue( IECore.StringVectorData( [ "/b" ] ) )
		s2["enabled"].setValue( False )

		self.assertEqual( s1["out"]["setNames"].hash(), s2["out"]["setNames"].hash() )
		self.assertEqual( s1["out"]["setNames"].getValue(), s2["out"]["setNames"].getValue() )
		self.assertEqual( s1["out"].setHash( "set" ), s2["out"].setHash( "set" ) )
		self.assertEqual( s1["out"].set( "set" ), s2["out"].set( "set" ) )
		self.assertEqual( s2["out"].set( "set" ).value.paths(), [ "/a" ] )

	def testAffects( self ) :

		s = GafferScene.Set()

		cs = GafferTest.CapturingSlot( s.plugDirtiedSignal() )

		s["name"].setValue( "a" )

		self.assertTrue( s["out"]["setNames"] in [ p[0] for p in cs ] )
		self.assertTrue( s["out"]["globals"] not in [ p[0] for p in cs ] )

		del cs[:]
		s["paths"].setValue( IECore.StringVectorData( [ "/a" ] ) )

		self.assertTrue( s["out"]["set"] in [ p[0] for p in cs ] )
		self.assertTrue( s["out"]["globals"] not in [ p[0] for p in cs ] )

	def testNoWildcards( self ) :

		s = GafferScene.Set()

		s["paths"].setValue( IECore.StringVectorData( [ "/a/..." ] ) )
		self.assertRaises( RuntimeError, s["out"].set, "set" )

		s["paths"].setValue( IECore.StringVectorData( [ "/a/b*" ] ) )
		self.assertRaises( RuntimeError, s["out"].set, "set" )

if __name__ == "__main__":
	unittest.main()
