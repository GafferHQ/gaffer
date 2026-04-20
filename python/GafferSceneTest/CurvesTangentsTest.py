##########################################################################
#
#  Copyright (c) 2026, Cinesite VFX Ltd. All rights reserved.
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
import GafferTest

class CurvesTangentsTest( GafferSceneTest.SceneTestCase ) :

	def testFirstDifference( self ) :

		Wrap = IECoreScene.CurvesPrimitive.Wrap
		for wrap, expectedTangents in [
			( Wrap.NonPeriodic, [ imath.V3f( 2, 0, 0 ), imath.V3f( -1, 1, 0 ), imath.V3f( 0, 1, 0 ), imath.V3f( 0, 1, 0 ) ] ),
			( Wrap.Periodic, [ imath.V3f( 2, 0, 0 ), imath.V3f( -1, 1, 0 ), imath.V3f( 0, 1, 0 ), imath.V3f( -1, -2, 0 ) ] ),
		] :

			with self.subTest( wrap = wrap ) :

				curves = IECoreScene.CurvesPrimitive(
					IECore.IntVectorData( [ 4 ] ),
					IECore.CubicBasisf.linear(), wrap,
					IECore.V3fVectorData( [
						imath.V3f( 0, 0, 0 ), imath.V3f( 2, 0, 0 ), imath.V3f( 1, 1, 0 ), imath.V3f( 1, 2, 0 ),
					] )
				)

				objectToScene = GafferScene.ObjectToScene()
				objectToScene["object"].setValue( curves )

				objectFilter = GafferScene.PathFilter()
				objectFilter["paths"].setValue( IECore.StringVectorData( [ "/object" ] ) )

				node = GafferScene.CurvesTangents()
				node["in"].setInput( objectToScene["out"] )
				node["filter"].setInput( objectFilter["out"] )
				node["mode"].setValue( node.Mode.FirstDifference )

				tangents = node["out"].object( "/object" )["tangent"]
				self.assertEqual( tangents.interpolation, IECoreScene.PrimitiveVariable.Interpolation.Vertex )
				self.assertEqual( list( tangents.data ), expectedTangents )
				self.assertEqual( tangents.data.getInterpretation(), IECore.GeometricData.Interpretation.Vector )

				node["normalize"].setValue( True )
				tangents = node["out"].object( "/object" )["tangent"]
				self.assertEqual( list( tangents.data ), [ t.normalized() for t in expectedTangents ] )

	def testCentralDifference( self ) :

		Wrap = IECoreScene.CurvesPrimitive.Wrap
		for wrap, expectedTangents in [
			( Wrap.NonPeriodic, [ imath.V3f( 2, 0, 0 ), imath.V3f( 1, 1, 0 ), imath.V3f( -1, 2, 0 ), imath.V3f( 0, 1, 0 ) ] ),
			( Wrap.Periodic, [ imath.V3f( 1, -2, 0 ), imath.V3f( 1, 1, 0 ), imath.V3f( -1, 2, 0 ), imath.V3f( -1, -1, 0 ) ] ),
		] :

			with self.subTest( wrap = wrap ) :

				curves = IECoreScene.CurvesPrimitive(
					IECore.IntVectorData( [ 4 ] ),
					IECore.CubicBasisf.linear(), wrap,
					IECore.V3fVectorData( [
						imath.V3f( 0, 0, 0 ), imath.V3f( 2, 0, 0 ), imath.V3f( 1, 1, 0 ), imath.V3f( 1, 2, 0 ),
					] )
				)

				objectToScene = GafferScene.ObjectToScene()
				objectToScene["object"].setValue( curves )

				objectFilter = GafferScene.PathFilter()
				objectFilter["paths"].setValue( IECore.StringVectorData( [ "/object" ] ) )

				node = GafferScene.CurvesTangents()
				node["in"].setInput( objectToScene["out"] )
				node["filter"].setInput( objectFilter["out"] )
				node["mode"].setValue( node.Mode.CentralDifference )

				tangents = node["out"].object( "/object" )["tangent"]
				self.assertEqual( tangents.interpolation, IECoreScene.PrimitiveVariable.Interpolation.Vertex )
				self.assertEqual( list( tangents.data ), expectedTangents )
				self.assertEqual( tangents.data.getInterpretation(), IECore.GeometricData.Interpretation.Vector )

				node["normalize"].setValue( True )
				tangents = node["out"].object( "/object" )["tangent"]
				self.assertEqual( list( tangents.data ), [ t.normalized() for t in expectedTangents ] )

	def testDerivative( self ) :

		Wrap = IECoreScene.CurvesPrimitive.Wrap
		for wrap, expectedTangents in [
			( Wrap.Pinned, [ imath.V3f( 2, 0, 0 ), imath.V3f( 0.5, 0.5, 0 ), imath.V3f( -0.5, 1, 0 ), imath.V3f( 0, 1, 0 ) ] ),
			( Wrap.NonPeriodic, [ imath.V3f( 0.5, 0.5, 0 ), imath.V3f( -0.5, 1, 0 ) ] ),
			( Wrap.Periodic, [ imath.V3f( 0.5, -1, 0 ), imath.V3f( 0.5, 0.5, 0 ), imath.V3f( -0.5, 1, 0 ), imath.V3f( -0.5, -0.5, 0 ) ] ),
		] :

			with self.subTest( wrap = wrap ) :

				curves = IECoreScene.CurvesPrimitive(
					IECore.IntVectorData( [ 4 ] ),
					IECore.CubicBasisf.catmullRom(), wrap,
					IECore.V3fVectorData( [
						imath.V3f( 0, 0, 0 ), imath.V3f( 2, 0, 0 ), imath.V3f( 1, 1, 0 ), imath.V3f( 1, 2, 0 ),
					] )
				)

				objectToScene = GafferScene.ObjectToScene()
				objectToScene["object"].setValue( curves )

				objectFilter = GafferScene.PathFilter()
				objectFilter["paths"].setValue( IECore.StringVectorData( [ "/object" ] ) )

				node = GafferScene.CurvesTangents()
				node["in"].setInput( objectToScene["out"] )
				node["filter"].setInput( objectFilter["out"] )
				node["mode"].setValue( node.Mode.Derivative )

				self.assertTrue( node["out"].object( "/object" ).arePrimitiveVariablesValid() )

				tangents = node["out"].object( "/object" )["tangent"]
				self.assertEqual( tangents.interpolation, IECoreScene.PrimitiveVariable.Interpolation.Varying )
				self.assertEqual( list( tangents.data ), expectedTangents )
				self.assertEqual( tangents.data.getInterpretation(), IECore.GeometricData.Interpretation.Vector )

				node["normalize"].setValue( True )
				tangents = node["out"].object( "/object" )["tangent"]
				self.assertEqual( list( tangents.data ), [ t.normalized() for t in expectedTangents ] )

	def testDerivativeOnLinearCurves( self ) :

		curves = IECoreScene.CurvesPrimitive(
			IECore.IntVectorData( [ 4 ] ),
			IECore.CubicBasisf.linear(), IECoreScene.CurvesPrimitive.Wrap.NonPeriodic,
			IECore.V3fVectorData( [
				imath.V3f( 0, 0, 0 ), imath.V3f( 2, 0, 0 ), imath.V3f( 1, 1, 0 ), imath.V3f( 1, 2, 0 ),
			] )
		)

		objectToScene = GafferScene.ObjectToScene()
		objectToScene["object"].setValue( curves )

		objectFilter = GafferScene.PathFilter()
		objectFilter["paths"].setValue( IECore.StringVectorData( [ "/object" ] ) )

		node = GafferScene.CurvesTangents()
		node["in"].setInput( objectToScene["out"] )
		node["filter"].setInput( objectFilter["out"] )
		node["mode"].setValue( node.Mode.Derivative )

		self.assertTrue( node["out"].object( "/object" ).arePrimitiveVariablesValid() )

		tangents = node["out"].object( "/object" )["tangent"]
		self.assertEqual( tangents.interpolation, IECoreScene.PrimitiveVariable.Interpolation.Varying )
		self.assertEqual(
			tangents.data,
			IECore.V3fVectorData(
				[ imath.V3f( 2, 0, 0 ), imath.V3f( -1, 1, 0 ), imath.V3f( 0, 1, 0 ), imath.V3f( 0, 1, 0 ) ],
				IECore.GeometricData.Interpretation.Vector
			)
		)

	def testTangentName( self ) :

		grid = GafferScene.Grid()

		allFilter = GafferScene.PathFilter()
		allFilter["paths"].setValue( IECore.StringVectorData( [ "/..." ] ) )

		node = GafferScene.CurvesTangents()
		node["in"].setInput( grid["out"] )
		node["filter"].setInput( allFilter["out"] )

		curves = node["out"].object( "/grid/centerLines" )
		self.assertIn( "tangent", curves )
		self.assertNotIn( "myTangent", curves )

		node["tangent"].setValue( "myTangent" )
		curves = node["out"].object( "/grid/centerLines" )
		self.assertNotIn( "tangent", curves )
		self.assertIn( "myTangent", curves )

	def testPositionName( self ) :

		curves = IECoreScene.CurvesPrimitive(
			IECore.IntVectorData( [ 4 ] ),
			IECore.CubicBasisf.linear(), IECoreScene.CurvesPrimitive.Wrap.NonPeriodic,
			IECore.V3fVectorData( [ imath.V3f( x, 0, 0 ) for x in range( 0, 4 ) ] ),
		)
		curves["Pref"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.V3fVectorData( [ imath.V3f( 0, y, 0 ) for y in range( 0, 4 ) ] )
		)

		objectToScene = GafferScene.ObjectToScene()
		objectToScene["object"].setValue( curves )

		objectFilter = GafferScene.PathFilter()
		objectFilter["paths"].setValue( IECore.StringVectorData( [ "/object" ] ) )

		node = GafferScene.CurvesTangents()
		node["in"].setInput( objectToScene["out"] )
		node["filter"].setInput( objectFilter["out"] )
		node["position"].setValue( "Pref" )
		node["mode"].setValue( node.Mode.FirstDifference )

		processedCurves = node["out"].object( "/object" )
		self.assertEqual( list( processedCurves["tangent"].data ), [ imath.V3f( 0, 1, 0 ) ] * 4 )

	def testNonCurvesPassThrough( self ) :

		cube = GafferScene.Cube()

		cubeFilter = GafferScene.PathFilter()
		cubeFilter["paths"].setValue( IECore.StringVectorData( [ "/cube" ] ) )

		node = GafferScene.CurvesTangents()
		node["in"].setInput( cube["out"] )
		node["filter"].setInput( cubeFilter["out"] )

		self.assertEqual( node["out"].object( "/cube" ), node["in"].object( "/cube" ) )

	def testMissingPositionThrows( self ) :

		grid = GafferScene.Grid()

		allFilter = GafferScene.PathFilter()
		allFilter["paths"].setValue( IECore.StringVectorData( [ "/..." ] ) )

		node = GafferScene.CurvesTangents()
		node["in"].setInput( grid["out"] )
		node["filter"].setInput( allFilter["out"] )
		node["position"].setValue( "missing" )

		with self.assertRaisesRegex( Gaffer.ProcessException, "No primvar named 'missing' found" ) :
			node["out"].object( "/grid/centerLines" )

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testPerformance( self ) :

		# 10,000 curves of 100 vertices each = 1M vertices total.
		numCurves = 10000
		numVertsPerCurve = 100

		vertsPerCurve = IECore.IntVectorData( [numVertsPerCurve] * numCurves )
		p = IECore.V3fVectorData(
			[
				imath.V3f( c, float(v) / float(numVertsPerCurve - 1), 0 )
				for c in range( numCurves )
				for v in range( numVertsPerCurve )
			]
		)
		curves = IECoreScene.CurvesPrimitive( vertsPerCurve, IECore.CubicBasisf.linear(), False, p )

		objectToScene = GafferScene.ObjectToScene()
		objectToScene["object"].setValue( curves )

		pathFilter = GafferScene.PathFilter()
		pathFilter["paths"].setValue( IECore.StringVectorData( ["/object"] ) )

		node = GafferScene.CurvesTangents()
		node["in"].setInput( objectToScene["out"] )
		node["filter"].setInput( pathFilter["out"] )

		# Precache input so it is not included in the measurement.
		node["in"].object( "/object" )

		with GafferTest.TestRunner.PerformanceScope() :
			node["out"].object( "/object" )

if __name__ == "__main__" :
	unittest.main()
