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

import IECore

import Gaffer
import GafferTest
import GafferScene
import GafferSceneTest

class LightTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		l = GafferSceneTest.TestLight()

		self.assertSceneValid( l["out"] )

		self.assertEqual( l["out"].object( "/" ), IECore.NullObject() )
		self.assertEqual( l["out"].transform( "/" ), IECore.M44f() )
		self.assertEqual( l["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "light" ] ) )

		self.assertTrue( isinstance( l["out"].object( "/light" ), IECore.Light ) )

		self.assertEqual( l["out"].transform( "/light" ), IECore.M44f() )
		self.assertEqual( l["out"].childNames( "/light" ), IECore.InternedStringVectorData() )

		self.assertEqual( l["out"]["setNames"].getValue(), IECore.InternedStringVectorData( [ "__lights" ] ) )
		lightSet = l["out"].set( "__lights" )
		self.assertEqual(
			lightSet,
			GafferScene.PathMatcherData(
				GafferScene.PathMatcher( [ "/light" ] )
			)
		)

	def testGroupMaintainsLightSet( self ) :

		l = GafferSceneTest.TestLight()
		g = GafferScene.Group()
		g["in"].setInput( l["out"] )

		self.assertSceneValid( g["out"] )

		lightSet = g["out"].set( "__lights" )
		self.assertEqual(
			lightSet,
			GafferScene.PathMatcherData(
				GafferScene.PathMatcher( [ "/group/light" ] )
			)
		)

	def testDirtyPropagation( self ) :

		l = GafferSceneTest.TestLight()
		cs = GafferTest.CapturingSlot( l.plugDirtiedSignal() )
		self.assertEqual( len( cs ), 0 )

		l["parameters"]["intensity"]["r"].setValue( 10 )

		dirtiedNames = [ p[0].relativeName( p[0].node() ) for p in cs ]
		self.assertTrue( "out.object" in dirtiedNames )
		self.assertTrue( "out" in dirtiedNames )

	def testDisabled( self ) :

		l = GafferSceneTest.TestLight()
		self.assertTrue( "__lights" in l["out"]["setNames"].getValue() )

		l["enabled"].setValue( False )
		self.assertFalse( "__lights" in l["out"]["setNames"].getValue() )

	def testAdditionalSets( self ) :

		l = GafferSceneTest.TestLight()
		self.assertEqual( l["out"]["setNames"].getValue(), IECore.InternedStringVectorData( [ "__lights" ] ) )

		l["sets"].setValue( "A B")
		self.assertEqual( l["out"]["setNames"].getValue(), IECore.InternedStringVectorData( [ "A", "B", "__lights" ] ) )

		self.assertTrue( l["out"].set( "A", _copy = False ).isSame( l["out"].set( "B", _copy = False ) ) )
		self.assertTrue( l["out"].set( "B", _copy = False ).isSame( l["out"].set( "__lights", _copy = False ) ) )

	def testDisabledHasNoSets( self ) :

		l = GafferSceneTest.TestLight()
		l["sets"].setValue( "A B")
		self.assertEqual( l["out"]["setNames"].getValue(), IECore.InternedStringVectorData( [ "A", "B", "__lights" ] ) )

		l["enabled"].setValue( False )
		self.assertEqual( l["out"]["setNames"].getValue(), IECore.InternedStringVectorData() )
		
	def testNonExistentSets( self ) :

		l = GafferSceneTest.TestLight()
		l["sets"].setValue( "A B")
		self.assertEqual( l["out"]["setNames"].getValue(), IECore.InternedStringVectorData( [ "A", "B", "__lights" ] ) )

		self.assertEqual( l["out"].set( "" ), GafferScene.PathMatcherData() )
		self.assertEqual( l["out"].set( "nonexistent1" ), GafferScene.PathMatcherData() )
		self.assertEqual( l["out"].setHash( "nonexistent1" ), l["out"].setHash( "nonexistent2" ) )
		self.assertTrue( l["out"].set( "nonexistent1", _copy = False ).isSame( l["out"].set( "nonexistent2", _copy = False ) ) )

if __name__ == "__main__":
	unittest.main()
