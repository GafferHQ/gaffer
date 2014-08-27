##########################################################################
#
#  Copyright (c) 2013, John Haddon. All rights reserved.
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

import os
import unittest

import IECore

import Gaffer
import GafferTest
import GafferScene
import GafferSceneTest

class MapProjectionTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		cube = GafferScene.Cube()
		camera = GafferScene.Camera()
		camera["transform"]["translate"]["z"].setValue( 2 )

		group = GafferScene.Group()
		group["in"].setInput( cube["out"] )
		group["in1"].setInput( camera["out"] )

		map = GafferScene.MapProjection()
		map["in"].setInput( group["out"] )
		map["camera"].setValue( "/group/camera" )

		oIn = group["out"].object( "/group/cube" )
		self.assertTrue( "s" not in oIn )
		self.assertTrue( "t" not in oIn )

		oOut = map["out"].object( "/group/cube" )
		self.assertTrue( "s" in oOut )
		self.assertTrue( "t" in oOut )
		self.assertTrue( oOut.arePrimitiveVariablesValid() )

		oIn["s"] = oOut["s"]
		oIn["t"] = oOut["t"]
		self.assertEqual( oIn, oOut )

		camera["transform"]["translate"]["z"].setValue( 3 )
		oOut2 = map["out"].object( "/group/cube" )

		self.assertNotEqual( oOut, oOut2 )

	def testAffects( self ) :

		cube = GafferScene.Cube()
		camera = GafferScene.Camera()

		group = GafferScene.Group()
		group["in"].setInput( cube["out"] )
		group["in1"].setInput( camera["out"] )

		map = GafferScene.MapProjection()
		map["in"].setInput( group["out"] )

		cs = GafferTest.CapturingSlot( map.plugDirtiedSignal() )

		camera["transform"]["translate"]["z"].setValue( 2 )
		self.assertTrue( "out.object" in [ x[0].relativeName( x[0].node() ) for x in cs ] )

		del cs[:]

		camera["fieldOfView"].setValue( 10 )
		self.assertTrue( "out.object" in [ x[0].relativeName( x[0].node() ) for x in cs ] )

		del cs[:]

		cube["transform"]["translate"]["z"].setValue( 2 )
		self.assertTrue( "out.object" in [ x[0].relativeName( x[0].node() ) for x in cs ] )

	def testHash( self ) :

		cube = GafferScene.Cube()
		camera = GafferScene.Camera()

		group = GafferScene.Group()
		group["in"].setInput( cube["out"] )
		group["in1"].setInput( camera["out"] )

		map = GafferScene.MapProjection()
		map["in"].setInput( group["out"] )

		h = map["out"].objectHash( "/group/cube" )
		self.assertNotEqual( h, group["out"].objectHash( "/group/cube" ) )

		cube["transform"]["translate"]["y"].setValue( 1 )
		h2 = map["out"].objectHash( "/group/cube" )
		self.assertNotEqual( h, h2 )

if __name__ == "__main__":
	unittest.main()
