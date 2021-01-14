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

class DeleteCurvesTest( GafferSceneTest.SceneTestCase ) :

	def makeCurves( self ) :

		testObject = IECoreScene.CurvesPrimitive(

			IECore.IntVectorData( [ 7, 7 ] ),
			IECore.CubicBasisf.bezier(),
			False,
			IECore.V3fVectorData(
				[
					imath.V3f( 0, 0, 0 ),
					imath.V3f( 0, 1, 0 ),
					imath.V3f( 1, 1, 0 ),
					imath.V3f( 1, 0, 0 ),
					imath.V3f( 1, -1, 0 ),
					imath.V3f( 2, -1, 0 ),
					imath.V3f( 2, 0, 0 ),

					imath.V3f( 0, 0, 0 ),
					imath.V3f( 0, 0, 1 ),
					imath.V3f( 1, 0, 1 ),
					imath.V3f( 1, 0, 0 ),
					imath.V3f( 1, 0, -1 ),
					imath.V3f( 2, 0, -1 ),
					imath.V3f( 2, 0, 0 )
				]
			)
		)

		testObject["a"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Constant, IECore.FloatData( 0.5 ) )
		testObject["b"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, IECore.FloatVectorData( range( 0, 14 ) ) )
		testObject["c"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Uniform, IECore.FloatVectorData( range( 0, 2 ) ) )
		testObject["d"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Varying, IECore.FloatVectorData( range( 0, 6 ) ) )
		testObject["e"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.FaceVarying, IECore.FloatVectorData( range( 0, 6 ) ) )

		testObject["deleteCurves"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Uniform, IECore.IntVectorData( [0, 1] ) )

		self.assertTrue( testObject.arePrimitiveVariablesValid() )

		objectToScene = GafferScene.ObjectToScene()
		objectToScene["object"].setValue( testObject )

		return objectToScene

	def testCanDeleteCurves( self ) :

		curvesScene = self.makeCurves()

		deleteCurves = GafferScene.DeleteCurves()

		deleteCurves["in"].setInput( curvesScene["out"] )

		pathFilter = GafferScene.PathFilter( "PathFilter" )
		pathFilter["paths"].setValue( IECore.StringVectorData( [ '/object' ] ) )
		deleteCurves["filter"].setInput( pathFilter["out"] )

		curveDeletedObject = deleteCurves["out"].object( "/object" )

		self.assertEqual( curveDeletedObject.verticesPerCurve(), IECore.IntVectorData([7]) )
		self.assertEqual( curveDeletedObject.numCurves(), 1 )
		self.assertEqual( curveDeletedObject["P"].data, IECore.V3fVectorData(
			[
				imath.V3f( 0, 0, 0 ),
				imath.V3f( 0, 1, 0 ),
				imath.V3f( 1, 1, 0 ),
				imath.V3f( 1, 0, 0 ),
				imath.V3f( 1, -1, 0 ),
				imath.V3f( 2, -1, 0 ),
				imath.V3f( 2, 0, 0 )
			], IECore.GeometricData.Interpretation.Point ) )

		# verify the primvars are correct
		self.assertEqual( curveDeletedObject["a"].data,  IECore.FloatData(0.5) )
		self.assertEqual( curveDeletedObject["a"].interpolation, IECoreScene.PrimitiveVariable.Interpolation.Constant)

		self.assertEqual( curveDeletedObject["b"].data,  IECore.FloatVectorData( range( 0, 7 ) ) )
		self.assertEqual( curveDeletedObject["b"].interpolation,  IECoreScene.PrimitiveVariable.Interpolation.Vertex )

		self.assertEqual( curveDeletedObject["c"].data,  IECore.FloatVectorData([0]) )
		self.assertEqual( curveDeletedObject["c"].interpolation,  IECoreScene.PrimitiveVariable.Interpolation.Uniform )

		self.assertEqual( curveDeletedObject["d"].data,  IECore.FloatVectorData(range( 0, 3 )) )
		self.assertEqual( curveDeletedObject["d"].interpolation,  IECoreScene.PrimitiveVariable.Interpolation.Varying )

		self.assertEqual( curveDeletedObject["e"].data,  IECore.FloatVectorData(range( 0, 3 )) )
		self.assertEqual( curveDeletedObject["e"].interpolation,  IECoreScene.PrimitiveVariable.Interpolation.FaceVarying )

		# invert
		# ======
		deleteCurves["invert"].setValue( True )
		curveDeletedObject = deleteCurves["out"].object( "/object" )

		self.assertEqual( curveDeletedObject.verticesPerCurve(), IECore.IntVectorData([7]) )
		self.assertEqual( curveDeletedObject.numCurves(), 1 )
		self.assertEqual( curveDeletedObject["P"].data, IECore.V3fVectorData(
			[
				imath.V3f( 0, 0, 0 ),
				imath.V3f( 0, 0, 1 ),
				imath.V3f( 1, 0, 1 ),
				imath.V3f( 1, 0, 0 ),
				imath.V3f( 1, 0, -1 ),
				imath.V3f( 2, 0, -1 ),
				imath.V3f( 2, 0, 0 )
			], IECore.GeometricData.Interpretation.Point ) )

		# verify the primvars are correct
		self.assertEqual( curveDeletedObject["a"].data,  IECore.FloatData(0.5) )
		self.assertEqual( curveDeletedObject["a"].interpolation, IECoreScene.PrimitiveVariable.Interpolation.Constant)

		self.assertEqual( curveDeletedObject["b"].data,  IECore.FloatVectorData( range( 7, 14 ) ) )
		self.assertEqual( curveDeletedObject["b"].interpolation,  IECoreScene.PrimitiveVariable.Interpolation.Vertex )

		self.assertEqual( curveDeletedObject["c"].data,  IECore.FloatVectorData([1.0]) )
		self.assertEqual( curveDeletedObject["c"].interpolation,  IECoreScene.PrimitiveVariable.Interpolation.Uniform )

		self.assertEqual( curveDeletedObject["d"].data,  IECore.FloatVectorData(range( 3, 6 )) )
		self.assertEqual( curveDeletedObject["d"].interpolation,  IECoreScene.PrimitiveVariable.Interpolation.Varying )

		self.assertEqual( curveDeletedObject["e"].data,  IECore.FloatVectorData(range( 3, 6 )) )
		self.assertEqual( curveDeletedObject["e"].interpolation,  IECoreScene.PrimitiveVariable.Interpolation.FaceVarying )

	def testBoundsUpdate( self ) :

		curvesScene = self.makeCurves()

		actualOriginalBound = curvesScene["out"].bound( "/object" )

		self.assertEqual(actualOriginalBound, imath.Box3f( imath.V3f( 0, -1, -1 ), imath.V3f( 2, 1, 1 ) ) )

		deleteCurves = GafferScene.DeleteCurves()
		deleteCurves["in"].setInput( curvesScene["out"] )

		pathFilter = GafferScene.PathFilter( "PathFilter" )
		pathFilter["paths"].setValue( IECore.StringVectorData( [ '/object' ] ) )
		deleteCurves["filter"].setInput( pathFilter["out"] )

		actualCurveDeletedBounds = deleteCurves["out"].bound( "/object" )
		expectedBoundingBox = imath.Box3f( imath.V3f( 0, -1, 0 ), imath.V3f( 2, 1, 0 ) )

		self.assertEqual( actualCurveDeletedBounds, expectedBoundingBox )

	def testIgnoreMissing( self ) :

		curvesScene = self.makeCurves()
		deleteCurves = GafferScene.DeleteCurves()
		deleteCurves["in"].setInput( curvesScene["out"] )
		pathFilter = GafferScene.PathFilter( "PathFilter" )
		pathFilter["paths"].setValue( IECore.StringVectorData( [ '/object' ] ) )
		deleteCurves["filter"].setInput( pathFilter["out"] )

		self.assertNotEqual( deleteCurves["in"].object( "/object" ), deleteCurves["out"].object( "/object" ) )

		deleteCurves["curves"].setValue( "doesNotExist" )
		self.assertRaises( RuntimeError, deleteCurves["out"].object, "/object" )

		deleteCurves["ignoreMissingVariable"].setValue( True )
		self.assertEqual( deleteCurves["in"].object( "/object" ), deleteCurves["out"].object( "/object" ) )
