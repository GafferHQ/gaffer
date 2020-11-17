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
import IECoreScene

import Gaffer
import GafferTest

import GafferScene
import GafferSceneTest

class MeshTypeTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		r = GafferScene.SceneReader()
		r["fileName"].setValue( "${GAFFER_ROOT}/resources/cow/cow.scc" )

		m = GafferScene.MeshType()
		m["in"].setInput( r["out"] )

		# Test unchanged settings.

		self.assertEqual( m["meshType"].getValue(), "" ) # do nothing
		self.assertEqual( r["out"].object( "/cow" ), m["out"].object( "/cow" ) )
		self.assertScenesEqual( r["out"], m["out"] )

		# Test converting poly to poly ( shouldn't do anything )

		m["meshType"].setValue( "linear" )

		self.assertEqual( r["out"].object( "/cow" ), m["out"].object( "/cow" ) )
		self.assertScenesEqual( r["out"], m["out"] )

		self.assertIn( "P", m["out"].object( "/cow" ) )
		self.assertIn( "N", m["out"].object( "/cow" ) )

		# Test converting poly to subdiv

		m["meshType"].setValue( "catmullClark" )

		self.assertNotEqual( r["out"].object( "/cow" ), m["out"].object( "/cow" ) )
		self.assertSceneHashesEqual( r["out"], m["out"], checks = self.allPathChecks - { "object" } )

		self.assertScenesEqual( r["out"], m["out"], pathsToPrune = ( "/cow", ) )

		self.assertEqual( m["out"].object( "/cow" ).interpolation, "catmullClark" )
		self.assertNotIn( "N", m["out"].object( "/cow" ) )

		# Test converting back to poly

		m2 = GafferScene.MeshType()
		m2["in"].setInput( m["out"] )

		m2["meshType"].setValue( "linear" )
		self.assertEqual( m2["out"].object( "/cow" ).interpolation, "linear" )
		self.assertTrue( "N" not in m2["out"].object( "/cow" ) )

		m2["calculatePolygonNormals"].setValue( True )
		self.assertIn( "N", m2["out"].object( "/cow" ) )

	def testNonPrimitiveObject( self ) :

		c = GafferScene.Camera()

		d = GafferScene.MeshType()
		d["in"].setInput( c["out"] )

		self.assertSceneValid( d["out"] )
		self.assertIsInstance( d["out"].object( "/camera" ), IECoreScene.Camera )
		self.assertEqual( d["out"].object( "/camera" ), c["out"].object( "/camera" ) )

	def testEnabledPlugAffects( self ) :

		n = GafferScene.MeshType()
		cs = GafferTest.CapturingSlot( n.plugDirtiedSignal() )

		n["enabled"].setValue( False )
		self.assertIn( n["out"], { x[0] for x in cs } )

if __name__ == "__main__":
	unittest.main()
