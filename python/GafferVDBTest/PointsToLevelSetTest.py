##########################################################################
#
#  Copyright (c) 2022, Cinesite VFX Ltd. All rights reserved.
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
#      * Neither the name of Image Engine Design Inc nor the names of
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
import IECoreVDB

import Gaffer
import GafferScene
import GafferVDB
import GafferVDBTest

class PointsToLevelSetTest( GafferVDBTest.VDBTestCase ) :

	def testSupportedPrimitives( self ) :

		sphere = GafferScene.Sphere()

		sphereFilter = GafferScene.PathFilter()
		sphereFilter["paths"].setValue( IECore.StringVectorData( [ "/sphere" ] ) )

		meshToPoints = GafferScene.MeshToPoints()
		meshToPoints["in"].setInput( sphere["out"] )
		meshToPoints["filter"].setInput( sphereFilter["out"] )

		pointsToLevelSet = GafferVDB.PointsToLevelSet()
		pointsToLevelSet["in"].setInput( meshToPoints["out"] )
		pointsToLevelSet["filter"].setInput( sphereFilter["out"] )

		# PointsPrimitives can be converted to level sets.

		self.assertIsInstance( pointsToLevelSet["in"].object( "/sphere" ), IECoreScene.PointsPrimitive )
		self.assertIsInstance( pointsToLevelSet["out"].object( "/sphere" ), IECoreVDB.VDBObject )

		# But so can MeshPrimitives, since our only hard requirement is a primitive variable
		# called "P".

		meshToPoints["enabled"].setValue( False )
		self.assertIsInstance( pointsToLevelSet["in"].object( "/sphere" ), IECoreScene.MeshPrimitive )
		self.assertIsInstance( pointsToLevelSet["out"].object( "/sphere" ), IECoreVDB.VDBObject )

		# Sphere primitives cannot be converted, because they don't have "P".

		sphere["type"].setValue( sphere.Type.Primitive )
		self.assertIsInstance( pointsToLevelSet["in"].object( "/sphere" ), IECoreScene.SpherePrimitive )
		self.assertIsInstance( pointsToLevelSet["out"].object( "/sphere" ), IECoreScene.SpherePrimitive )
		self.assertScenesEqual( pointsToLevelSet["in"], pointsToLevelSet["out"] )

	def testWidth( self ) :

		plane = GafferScene.Plane()

		planeFilter = GafferScene.PathFilter()
		planeFilter["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		pointsToLevelSet = GafferVDB.PointsToLevelSet()
		pointsToLevelSet["in"].setInput( plane["out"] )
		pointsToLevelSet["filter"].setInput( planeFilter["out"] )
		pointsToLevelSet["voxelSize"].setValue( 0.025 )

		levelSetToMesh = GafferVDB.LevelSetToMesh()
		levelSetToMesh["in"].setInput( pointsToLevelSet["out"] )
		levelSetToMesh["filter"].setInput( planeFilter["out"] )

		w = levelSetToMesh["out"].object( "/plane" ).bound().size().z
		pointsToLevelSet["widthScale"].setValue( 2 )
		w2 = levelSetToMesh["out"].object( "/plane" ).bound().size().z
		self.assertAlmostEqual( w2, w * 2, delta = 0.01 )

		primitiveVariables = GafferScene.PrimitiveVariables()
		primitiveVariables["in"].setInput( plane["out"] )
		primitiveVariables["filter"].setInput( planeFilter["out"] )
		primitiveVariables["primitiveVariables"]["width"] = Gaffer.NameValuePlug( "width", 2.0 )
		pointsToLevelSet["in"].setInput( primitiveVariables["out"] )

		w4 = levelSetToMesh["out"].object( "/plane" ).bound().size().z
		self.assertAlmostEqual( w4, w * 4, delta = 0.01 )

	def testPointSizeWarnings( self ) :

		plane = GafferScene.Plane()

		planeFilter = GafferScene.PathFilter()
		planeFilter["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		pointsToLevelSet = GafferVDB.PointsToLevelSet()
		pointsToLevelSet["in"].setInput( plane["out"] )
		pointsToLevelSet["filter"].setInput( planeFilter["out"] )
		pointsToLevelSet["voxelSize"].setValue( 4 )

		with IECore.CapturingMessageHandler() as mh :
			self.assertIsInstance( pointsToLevelSet["out"].object( "/plane" ), IECoreVDB.VDBObject )

		self.assertEqual( len( mh.messages ), 1 )
		self.assertEqual( mh.messages[0].level, IECore.Msg.Level.Warning )
		self.assertEqual( mh.messages[0].context, "PointsToLevelSet" )
		self.assertEqual( mh.messages[0].message, "4 points from \"/plane\" were ignored because they were too small" )

	def testVelocityTrails( self ) :

		points = IECoreScene.PointsPrimitive( IECore.V3fVectorData( [ imath.V3f( 0 ) ] ) )
		points["velocity"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.V3fVectorData( [ imath.V3f( 100, 0, 0 ) ] )
		)

		objectToScene = GafferScene.ObjectToScene()
		objectToScene["object"].setValue( points )

		objectFilter = GafferScene.PathFilter()
		objectFilter["paths"].setValue( IECore.StringVectorData( [ "/object" ] ) )

		pointsToLevelSet = GafferVDB.PointsToLevelSet()
		pointsToLevelSet["in"].setInput( objectToScene["out"] )
		pointsToLevelSet["filter"].setInput( objectFilter["out"] )

		self.assertIsInstance( pointsToLevelSet["out"].object( "/object" ), IECoreVDB.VDBObject )

		levelSetToMesh = GafferVDB.LevelSetToMesh()
		levelSetToMesh["in"].setInput( pointsToLevelSet["out"] )
		levelSetToMesh["filter"].setInput( objectFilter["out"] )

		b1 = levelSetToMesh["out"].object( "/object" ).bound()
		pointsToLevelSet["useVelocity"].setValue( True )
		b2 = levelSetToMesh["out"].object( "/object" ).bound()

		# Trails are in opposite direction to velocity, so in negative X in this case.

		self.assertEqual( b2.max(), b1.max() )
		self.assertEqual( b2.min().y, b1.min().y )
		self.assertEqual( b2.min().z, b1.min().z )
		self.assertLess( b2.min().x, b1.min().x )

		# The length of trails can be changed

		pointsToLevelSet["velocityScale"].setValue( 2 )
		b3 = levelSetToMesh["out"].object( "/object" ).bound()

		self.assertEqual( b3.max(), b2.max() )
		self.assertEqual( b3.min().y, b2.min().y )
		self.assertEqual( b3.min().z, b2.min().z )
		self.assertLess( b3.min().x, b2.min().x )

		# Trails automatically account for framesPerSecond

		with Gaffer.Context() as c :
			c.setFramesPerSecond( 1 )
			b4 = levelSetToMesh["out"].object( "/object" ).bound()

		self.assertLess( b4.min().x, b3.min().x )

if __name__ == "__main__":
	unittest.main()
