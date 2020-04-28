##########################################################################
#
#  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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
import GafferScene
import GafferSceneTest

class PointsTypeTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		points = IECoreScene.PointsPrimitive( 1 )
		points["P"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.V3fVectorData(
				[ imath.V3f( 1, 2, 3 ) ],
				IECore.GeometricData.Interpretation.Point
			),
		)

		objectToScene = GafferScene.ObjectToScene()
		objectToScene["object"].setValue( points )

		group = GafferScene.Group()
		group["in"][0].setInput( objectToScene["out"] )

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/group/object" ] ) )

		pointsType = GafferScene.PointsType()
		pointsType["in"].setInput( group["out"] )
		pointsType["filter"].setInput( filter["out"] )

		def assertExpectedOutput( type, unchanged ) :

			self.assertSceneValid( pointsType["out"] )

			if type is not None :
				self.assertEqual( pointsType["out"].object( "/group/object" )["type"].data.value, type )
			else :
				self.assertFalse( "type" in pointsType["out"].object( "/group/object" ) )

			if unchanged :
				self.assertScenesEqual( pointsType["out"], group["out"] )
				self.assertEqual( pointsType["out"].object( "/group/object" ), group["out"].object( "/group/object" ) )
				self.assertTrue(
					pointsType["out"].object( "/group/object", _copy = False ).isSame( group["out"].object( "/group/object", _copy = False ) )
				)

		# Test unchanged settings (no type on input points).

		assertExpectedOutput( type = None, unchanged = True )

		# Test unchanged settings.

		points["type"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Constant, IECore.StringData( "particles" ) )
		objectToScene["object"].setValue( points )

		assertExpectedOutput( type = "particles", unchanged = True )

		# Test converting particles to particles ( shouldn't do anything )

		pointsType["type"].setValue( "particles" )
		assertExpectedOutput( type = "particles", unchanged = True )

		# Test converting particles to sphere

		pointsType["type"].setValue( "sphere" )
		assertExpectedOutput( type = "sphere", unchanged = False )

		# Test converting particles to patches. The bound should change at this point.

		pointsType["type"].setValue( "patch" )
		assertExpectedOutput( type = "patch", unchanged = False )

	def testNonPrimitiveObject( self ) :

		c = GafferScene.Camera()

		p = GafferScene.PointsType()
		p["in"].setInput( c["out"] )

		self.assertSceneValid( p["out"] )
		self.assertIsInstance( p["out"].object( "/camera" ), IECoreScene.Camera )
		self.assertEqual( p["out"].object( "/camera" ), c["out"].object( "/camera" ) )
		self.assertTrue(
			p["out"].object( "/camera", _copy = False ).isSame( c["out"].object( "/camera", _copy = False ) )
		)

if __name__ == "__main__":
	unittest.main()
