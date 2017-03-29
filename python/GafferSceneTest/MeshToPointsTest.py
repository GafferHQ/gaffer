##########################################################################
#
#  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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
import GafferScene
import GafferSceneTest

class MeshToPointsTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		plane = GafferScene.Plane()

		group = GafferScene.Group()
		group["in"][0].setInput( plane["out"] )

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/group/plane" ] ) )

		meshToPoints = GafferScene.MeshToPoints()
		meshToPoints["in"].setInput( group["out"] )
		meshToPoints["filter"].setInput( filter["out"] )

		self.assertSceneValid( meshToPoints["out"] )

		mesh = group["out"].object( "/group/plane", _copy = False )
		points = meshToPoints["out"].object( "/group/plane", _copy = False )

		self.assertTrue( points.arePrimitiveVariablesValid() )
		self.assertEqual( points["P"], mesh["P"] )
		self.assertTrue( points["P"].data.isSame( mesh["P"].data ) )

		self.assertEqual( points["type"].data.value, "particle" )

	def testNonPrimitiveObject( self ) :

		c = GafferScene.Camera()

		p = GafferScene.MeshToPoints()
		p["in"].setInput( c["out"] )

		self.assertSceneValid( p["out"] )
		self.failUnless( isinstance( p["out"].object( "/camera" ), IECore.Camera ) )
		self.assertEqual( p["out"].object( "/camera" ), c["out"].object( "/camera" ) )
		self.assertTrue(
			p["out"].object( "/camera", _copy = False ).isSame( c["out"].object( "/camera", _copy = False ) )
		)

	def testCanInstanceOnPolygonWithOrientation( self ) :
		plane = GafferScene.Plane()
		meshToPoints = GafferScene.MeshToPoints()

		meshToPoints["in"].setInput(plane["out"])
		meshToPoints["mode"].setValue("polygon")

		points = meshToPoints['out'].object("/plane")

		self.assertEqual(points.numPoints, 1)
		self.assertTrue('id' in points.keys())
		self.assertTrue('orient' in points.keys())

		self.assertEqual( len( points["orient"].data ), 1 )
		self.assertEqual( len( points["id"].data ), 1 )

		self.assertEqual( points["orient"].data[0], IECore.Quatf( 0, 1, 0, 0 ) )
		self.assertEqual( points["id"].data[0], 0 )

		meshToPoints["rotation"].setValue(45.0)

		rotatedPoints = meshToPoints['out'].object("/plane")

		self.assertEqual( len( rotatedPoints["orient"].data ),1 )
		self.assertAlmostEqual( rotatedPoints["orient"].data[0][0] ,0.0, places = 4 )
		self.assertAlmostEqual( rotatedPoints["orient"].data[0][1] ,0.92388, places = 4 )
		self.assertAlmostEqual( rotatedPoints["orient"].data[0][2] ,-0.382683, places = 4 )
		self.assertAlmostEqual( rotatedPoints["orient"].data[0][3] ,0.0, places = 4 )




if __name__ == "__main__":
	unittest.main()
