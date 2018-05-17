##########################################################################
#
#  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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

import imath

import IECore
import IECoreScene
import GafferScene
import GafferSceneTest

class DeletePointsTest( GafferSceneTest.SceneTestCase ) :

	def makePoints( self ) :

		testObject = IECoreScene.PointsPrimitive(
			IECore.V3fVectorData(
				[
					imath.V3f( 0, 0, 0 ),
					imath.V3f( 0, 1, 0 ),
					imath.V3f( 1, 1, 0 ),
					imath.V3f( 1, 0, 0 )

				]
			),
			IECore.FloatVectorData( range( 0, 4 ) )
		)

		testObject["deletePoints"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, IECore.IntVectorData( [0, 1, 0, 1] ) )
		testObject["deletePoints2"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, IECore.IntVectorData( [1, 1, 0, 0] ) )

		self.assertTrue( testObject.arePrimitiveVariablesValid() )

		objectToScene = GafferScene.ObjectToScene()
		objectToScene["object"].setValue( testObject )

		return objectToScene

	def testCanDeletePoints( self ) :

		pointsScene = self.makePoints()

		deletePoints = GafferScene.DeletePoints()

		deletePoints["in"].setInput( pointsScene["out"] )

		pathFilter = GafferScene.PathFilter( "PathFilter" )
		pathFilter["paths"].setValue( IECore.StringVectorData( [ '/object' ] ) )
		deletePoints["filter"].setInput( pathFilter["out"] )

		pointsDeletedObject = deletePoints["out"].object( "/object" )

		self.assertEqual( pointsDeletedObject.numPoints, 2 )
		self.assertEqual( pointsDeletedObject["P"].data, IECore.V3fVectorData(
			[
				imath.V3f( 0, 0, 0 ),
				#IECore.V3f( 0, 1, 0 ),
				imath.V3f( 1, 1, 0 )
				#IECore.V3f( 1, 0, 0 )
			], IECore.GeometricData.Interpretation.Point ) )

		self.assertEqual( pointsDeletedObject["r"].data, IECore.FloatVectorData(
			[
				0, 2
			] ) )

		self.assertEqual( pointsDeletedObject["deletePoints"].data, IECore.IntVectorData(
			[
				0, 0
			] ) )

		# invert
		# ======

		deletePoints["invert"].setValue( True )

		pointsDeletedObject = deletePoints["out"].object( "/object" )

		self.assertEqual( pointsDeletedObject.numPoints, 2 )
		self.assertEqual( pointsDeletedObject["P"].data, IECore.V3fVectorData(
			[
				#imath.V3f( 0, 0, 0 ),
				imath.V3f( 0, 1, 0 ),
				#imath.V3f( 1, 1, 0 )
				imath.V3f( 1, 0, 0 )
			], IECore.GeometricData.Interpretation.Point ) )

		self.assertEqual( pointsDeletedObject["r"].data, IECore.FloatVectorData(
			[
				1, 3
			] ) )

		self.assertEqual( pointsDeletedObject["deletePoints"].data, IECore.IntVectorData(
			[
				1, 1
			] ) )


	def testBoundsUpdate( self ) :

		pointsScene = self.makePoints()

		actualOriginalBound = pointsScene["out"].bound( "/object" )

		self.assertEqual(actualOriginalBound, imath.Box3f( imath.V3f( -0.5, -0.5, -0.5 ), imath.V3f( 1.5, 1.5, 0.5 ) ) )

		deletePoints = GafferScene.DeletePoints()
		deletePoints["in"].setInput( pointsScene["out"] )

		pathFilter = GafferScene.PathFilter( "PathFilter" )
		pathFilter["paths"].setValue( IECore.StringVectorData( [ '/object' ] ) )
		deletePoints["filter"].setInput( pathFilter["out"] )
		deletePoints["points"].setValue("deletePoints2")

		actualPointsDeletedBounds = deletePoints["out"].bound( "/object" )
		expectedBoundingBox = imath.Box3f( imath.V3f( 0.5, -0.5, -0.5 ), imath.V3f( 1.5, 1.5, 0.5 ) )

		self.assertEqual( actualPointsDeletedBounds, expectedBoundingBox )

