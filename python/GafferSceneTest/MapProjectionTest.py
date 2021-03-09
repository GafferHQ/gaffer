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
import imath
import six

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

		deleteUV = GafferScene.DeletePrimitiveVariables()
		deleteUV["in"].setInput( cube["out"] )
		deleteUV["names"].setValue( "uv" )

		group = GafferScene.Group()
		group["in"][0].setInput( deleteUV["out"] )
		group["in"][1].setInput( camera["out"] )

		map = GafferScene.MapProjection()
		map["in"].setInput( group["out"] )
		map["camera"].setValue( "/group/camera" )

		oIn = group["out"].object( "/group/cube" )
		self.assertTrue( "uv" not in oIn )

		oOut = map["out"].object( "/group/cube" )
		self.assertTrue( "uv" in oOut )
		self.assertTrue( oOut.arePrimitiveVariablesValid() )

		oIn["uv"] = oOut["uv"]
		self.assertEqual( oIn, oOut )

		camera["transform"]["translate"]["z"].setValue( 3 )
		oOut2 = map["out"].object( "/group/cube" )

		self.assertNotEqual( oOut, oOut2 )

	def testAffects( self ) :

		cube = GafferScene.Cube()
		camera = GafferScene.Camera()

		group = GafferScene.Group()
		group["in"][0].setInput( cube["out"] )
		group["in"][1].setInput( camera["out"] )

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
		group["in"][0].setInput( cube["out"] )
		group["in"][1].setInput( camera["out"] )

		map = GafferScene.MapProjection()
		map["in"].setInput( group["out"] )

		h = map["out"].objectHash( "/group/cube" )
		self.assertNotEqual( h, group["out"].objectHash( "/group/cube" ) )

		cube["transform"]["translate"]["y"].setValue( 1 )
		h2 = map["out"].objectHash( "/group/cube" )
		self.assertNotEqual( h, h2 )

	def testCustomPosition( self ) :

		littleCube = GafferScene.Cube()
		littleCube["name"].setValue( "little" )

		bigCube = GafferScene.Cube()
		bigCube["dimensions"].setValue( imath.V3f( 10, 10, 10 ) )
		bigCube["name"].setValue( "big" )

		camera = GafferScene.Camera()
		camera["transform"]["translate"]["z"].setValue( 10 )

		group = GafferScene.Group()
		group["in"][0].setInput( littleCube["out"] )
		group["in"][1].setInput( bigCube["out"] )
		group["in"][2].setInput( camera["out"] )

		self.assertNotEqual(
			group["out"].object( "/group/little" )["P"].data,
			group["out"].object( "/group/big" )["P"].data,
		)

		bigCubeFilter = GafferScene.PathFilter()
		bigCubeFilter["paths"].setValue( IECore.StringVectorData( [ "/group/big" ] ) )

		shuffle = GafferScene.ShufflePrimitiveVariables()
		shuffle["in"].setInput( group["out"] )
		shuffle["filter"].setInput( bigCubeFilter["out"] )
		shuffle["shuffles"].addChild( Gaffer.ShufflePlug( "P", "Pref" ) )

		littleCubeFilter = GafferScene.PathFilter()
		littleCubeFilter["paths"].setValue( IECore.StringVectorData( [ "/group/little" ] ) )

		copy = GafferScene.CopyPrimitiveVariables()
		copy["in"].setInput( shuffle["out"] )
		copy["source"].setInput( shuffle["out"] )
		copy["filter"].setInput( littleCubeFilter["out"] )
		copy["sourceLocation"].setValue( "/group/big" )
		copy["primitiveVariables"].setValue( "Pref" )

		self.assertEqual(
			copy["out"].object( "/group/little" )["Pref"].data,
			copy["out"].object( "/group/big" )["Pref"].data,
		)

		unionFilter = GafferScene.UnionFilter()
		unionFilter["in"][0].setInput( littleCubeFilter["out"] )
		unionFilter["in"][1].setInput( bigCubeFilter["out"] )

		projection = GafferScene.MapProjection()
		projection["in"].setInput( copy["out"] )
		projection["filter"].setInput( unionFilter["out"] )
		projection["camera"].setValue( "/group/camera" )
		projection["uvSet"].setValue( "projectedUV" )

		self.assertNotEqual(
			projection["out"].object( "/group/little" )["projectedUV"].data,
			projection["out"].object( "/group/big" )["projectedUV"].data,
		)

		projection["position"].setValue( "Pref" )

		self.assertEqual(
			projection["out"].object( "/group/little" )["projectedUV"].data[0],
			projection["out"].object( "/group/big" )["projectedUV"].data[0],
		)

		self.assertEqual(
			projection["out"].object( "/group/little" )["projectedUV"].data,
			projection["out"].object( "/group/big" )["projectedUV"].data,
		)

	def testWrongPositionType( self ) :

		cube = GafferScene.Cube()
		camera = GafferScene.Camera()

		group = GafferScene.Group()
		group["in"][0].setInput( cube["out"] )
		group["in"][1].setInput( camera["out"] )

		cubeFilter = GafferScene.PathFilter()
		cubeFilter["paths"].setValue( IECore.StringVectorData( [ "/group/cube" ] ) )

		projection = GafferScene.MapProjection()
		projection["in"].setInput( group["out"] )
		projection["filter"].setInput( cubeFilter["out"] )
		projection["position"].setValue( "uv" )

		with six.assertRaisesRegex( self, RuntimeError, r'Position primitive variable "uv" on object "/group/cube" should be V3fVectorData \(but is V2fVectorData\)' ) :
			projection["out"].object( "/group/cube" )

if __name__ == "__main__":
	unittest.main()
