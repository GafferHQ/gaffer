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

class DeleteFacesTest( GafferSceneTest.SceneTestCase ) :

	def makeRectangleFromTwoSquaresScene( self ) :

		verticesPerFace = IECore.IntVectorData( [4, 4] )
		vertexIds = IECore.IntVectorData( [0, 1, 4, 3, 1, 2, 5, 4] )
		p = IECore.V3fVectorData( [imath.V3f( 0, 0, 0 ), imath.V3f( 1, 0, 0 ), imath.V3f( 2, 0, 0 ), imath.V3f( 0, 1, 0 ), imath.V3f( 1, 1, 0 ), imath.V3f( 2, 1, 0 )] )
		deleteData = IECore.IntVectorData( [0, 1] )

		mesh = IECoreScene.MeshPrimitive( verticesPerFace, vertexIds, "linear", p )
		mesh["deleteFaces"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Uniform, deleteData )

		mesh["uniform"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Uniform, IECore.IntVectorData( [10, 11] ) )
		mesh["vertex"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, IECore.IntVectorData( [100, 101, 102, 103, 104, 105] ) )
		mesh["faceVarying"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.FaceVarying, IECore.IntVectorData( [20, 21, 22, 23, 24, 25, 26, 27] ) )

		self.assertTrue(mesh.arePrimitiveVariablesValid())

		objectToScene = GafferScene.ObjectToScene()
		objectToScene["object"].setValue( mesh )

		return objectToScene

	def testCanDeleteFaces( self ) :

		rectangleScene = self.makeRectangleFromTwoSquaresScene()

		deleteFaces = GafferScene.DeleteFaces()
		deleteFaces["in"].setInput( rectangleScene["out"] )

		pathFilter = GafferScene.PathFilter( "PathFilter" )
		pathFilter["paths"].setValue( IECore.StringVectorData( [ '/object' ] ) )
		deleteFaces["filter"].setInput( pathFilter["out"] )

		faceDeletedObject = deleteFaces["out"].object( "/object" )

		self.assertEqual( faceDeletedObject.verticesPerFace, IECore.IntVectorData([4]) )
		self.assertEqual( faceDeletedObject.vertexIds, IECore.IntVectorData([0, 1, 3, 2]) )
		self.assertEqual( faceDeletedObject.numFaces(), 1 )
		self.assertEqual( faceDeletedObject["P"].data, IECore.V3fVectorData( [imath.V3f( 0, 0, 0 ), imath.V3f( 1, 0, 0 ), imath.V3f( 0, 1, 0 ), imath.V3f( 1, 1, 0 )], IECore.GeometricData.Interpretation.Point) )

		# verify the primvars are correct
		self.assertEqual( faceDeletedObject["uniform"].data,  IECore.IntVectorData([10]) )
		self.assertEqual( faceDeletedObject["vertex"].data,  IECore.IntVectorData([100, 101, 103, 104]) )
		self.assertEqual( faceDeletedObject["faceVarying"].data,  IECore.IntVectorData([20, 21, 22, 23]) )

		# invert
		# ======

		deleteFaces["invert"].setValue( True )
		faceDeletedObject = deleteFaces["out"].object( "/object" )

		self.assertEqual( faceDeletedObject.verticesPerFace, IECore.IntVectorData([4]) )
		self.assertEqual( faceDeletedObject.vertexIds, IECore.IntVectorData([0, 1, 3, 2]) )
		self.assertEqual( faceDeletedObject.numFaces(), 1 )
		self.assertEqual( faceDeletedObject["P"].data,
			IECore.V3fVectorData( [imath.V3f( 1, 0, 0 ), imath.V3f( 2, 0, 0 ), imath.V3f( 1, 1, 0 ), imath.V3f( 2, 1, 0 )],
				IECore.GeometricData.Interpretation.Point ) )

		# verify the primvars are correct
		self.assertEqual( faceDeletedObject["uniform"].data,  IECore.IntVectorData([11]) )
		self.assertEqual( faceDeletedObject["vertex"].data,  IECore.IntVectorData([101, 102, 104, 105]) )
		self.assertEqual( faceDeletedObject["faceVarying"].data,  IECore.IntVectorData([24, 25, 26, 27]) )

	def testDeletingFacesUpdatesBounds( self ) :

		rectangleScene = self.makeRectangleFromTwoSquaresScene()

		expectedOriginalBound = rectangleScene["out"].bound( "/object" )
		self.assertEqual(expectedOriginalBound, imath.Box3f( imath.V3f( 0, 0, 0 ), imath.V3f( 2, 1, 0 ) ) )

		deleteFaces = GafferScene.DeleteFaces()
		deleteFaces["in"].setInput( rectangleScene["out"] )

		pathFilter = GafferScene.PathFilter( "PathFilter" )
		pathFilter["paths"].setValue( IECore.StringVectorData( [ '/object' ] ) )
		deleteFaces["filter"].setInput( pathFilter["out"] )

		actualFaceDeletedBounds = deleteFaces["out"].bound( "/object" )
		expectedBoundingBox = imath.Box3f( imath.V3f( 0, 0, 0 ), imath.V3f( 1, 1, 0 ) )

		self.assertEqual( actualFaceDeletedBounds, expectedBoundingBox )

	def testBoundsOfChildObjects( self ) :

		rectangle = self.makeRectangleFromTwoSquaresScene()
		sphere = GafferScene.Sphere()
		sphere["radius"].setValue( 10 ) # Totally encloses the rectangle

		parent = GafferScene.Parent()
		parent["in"].setInput( rectangle["out"] )
		parent["parent"].setValue( "/object" )
		parent["children"][0].setInput( sphere["out"] )

		self.assertSceneValid( parent["out"] )

		pathFilter = GafferScene.PathFilter( "PathFilter" )
		pathFilter["paths"].setValue( IECore.StringVectorData( [ "/object" ] ) )

		deleteFaces = GafferScene.DeleteFaces()
		deleteFaces["in"].setInput( parent["out"] )
		deleteFaces["filter"].setInput( pathFilter["out"] )

		# The sphere should not have been modified
		self.assertEqual( deleteFaces["out"].object( "/object/sphere" ), parent["out"].object( "/object/sphere" ) )
		# And the bounding boxes should still enclose all the objects,
		# including the sphere.
		self.assertSceneValid( deleteFaces["out"] )

	def testIgnoreMissing( self ) :

		rectangle = self.makeRectangleFromTwoSquaresScene()
		deleteFaces = GafferScene.DeleteFaces()
		deleteFaces["in"].setInput( rectangle["out"] )
		pathFilter = GafferScene.PathFilter( "PathFilter" )
		pathFilter["paths"].setValue( IECore.StringVectorData( [ '/object' ] ) )
		deleteFaces["filter"].setInput( pathFilter["out"] )

		self.assertNotEqual( deleteFaces["in"].object( "/object" ), deleteFaces["out"].object( "/object" ) )

		deleteFaces["faces"].setValue( "doesNotExist" )
		self.assertRaises( RuntimeError, deleteFaces["out"].object, "/object" )

		deleteFaces["ignoreMissingVariable"].setValue( True )
		self.assertEqual( deleteFaces["in"].object( "/object" ), deleteFaces["out"].object( "/object" ) )

if __name__ == "__main__":
	unittest.main()
