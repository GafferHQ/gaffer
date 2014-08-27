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
import os

import IECore

import Gaffer
import GafferTest

import GafferScene
import GafferSceneTest

class MeshTypeTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		## \todo - this test just needs an arbitrary mesh with normals.
		# We should maybe have a more concise way of achieving this.  How about a cow primitive?
		fileName = os.path.expandvars( "$GAFFER_ROOT/python/GafferTest/cobs/pSphereShape1.cob" )

		read = Gaffer.ObjectReader()
		read["fileName"].setValue( fileName )
		object = IECore.Reader.create( fileName ).read()

		p = GafferScene.ObjectToScene()
		p["object"].setInput( read["out"] )

		m = GafferScene.MeshType()
		m["in"].setInput( p["out"] )

		# Test unchanged settings.

		self.assertEqual( m["meshType"].getValue(), "" ) # do nothing
		self.assertEqual( p["out"].object( "/object" ), m["out"].object( "/object" ) )
		self.assertScenesEqual( p["out"], m["out"] )

		# Test converting poly to poly ( shouldn't do anything )

		m["meshType"].setValue( "linear" )

		self.assertEqual( p["out"].object( "/object" ), m["out"].object( "/object" ) )
		self.assertScenesEqual( p["out"], m["out"] )

		self.failUnless( "P" in m["out"].object( "/object" ) )
		self.failUnless( "N" in m["out"].object( "/object" ) )

		# Test converting poly to subdiv

		m["meshType"].setValue( "catmullClark" )

		self.assertNotEqual( p["out"].object( "/object" ), m["out"].object( "/object" ) )
		self.assertSceneHashesEqual( p["out"], m["out"], childPlugNames = ( "attributes", "bound", "transform", "globals", "childNames" ) )

		self.assertScenesEqual( p["out"], m["out"], pathsToIgnore = ( "/object", ) )

		self.assertEqual( m["out"].object( "/object" ).interpolation, "catmullClark" )
		self.failUnless( "N" not in m["out"].object( "/object" ) )

		# Test converting back to poly

		m2 = GafferScene.MeshType()
		m2["in"].setInput( m["out"] )

		m2["meshType"].setValue( "linear" )
		self.assertEqual( m2["out"].object( "/object" ).interpolation, "linear" )
		self.assertTrue( "N" not in m2["out"].object( "/object" ) )

		m2["calculatePolygonNormals"].setValue( True )
		self.failUnless( "N" in m2["out"].object( "/object" ) )

	def testNonPrimitiveObject( self ) :

		c = GafferScene.Camera()

		d = GafferScene.MeshType()
		d["in"].setInput( c["out"] )

		self.assertSceneValid( d["out"] )
		self.failUnless( isinstance( d["out"].object( "/camera" ), IECore.Camera ) )
		self.assertEqual( d["out"].object( "/camera" ), c["out"].object( "/camera" ) )

	def testEnabledPlugAffects( self ) :

		n = GafferScene.MeshType()
		cs = GafferTest.CapturingSlot( n.plugDirtiedSignal() )

		n["enabled"].setValue( False )
		self.assertTrue( len( cs ) )
		self.assertTrue( cs[1][0].isSame( n["out"] ) )

if __name__ == "__main__":
	unittest.main()
