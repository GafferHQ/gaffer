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
#      * Neither the name of  Image Engine Design Inc nor the names of
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

import math

import imath

import IECore
import IECoreScene

import Gaffer
import GafferTest
import GafferScene
import GafferSceneTest

class RandomPrimitiveVariableTest( GafferSceneTest.SceneTestCase ) :

	def testUniformInt( self ) :

		plane = GafferScene.Plane()
		plane["divisions"].setValue( imath.V2i( 1000 ) )

		planeFilter = GafferScene.PathFilter()
		planeFilter["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		random = GafferScene.RandomPrimitiveVariable()
		random["in"].setInput( plane["out"] )
		random["filter"].setInput( planeFilter["out"] )
		random["distribution"].setValue( random.Distribution.UniformInt )
		random["intRange"].setValue( imath.V2i( -1001, 10342 ) )

		values = random["out"].object( "/plane" )["random"].data
		self.assertIsInstance( values, IECore.IntVectorData )
		self.assertEqual( min( values ), -1001 ) # We're generating enough points that we can
		self.assertEqual( max( values ), 10342 ) # expect to hit min and max exactly at least once.
		self.assertAlmostEqual( sum( values ) / len( values ), ( -1001 + 10342 ) / 2, delta = 1.1 )

	def testUniformFloat( self ) :

		plane = GafferScene.Plane()
		plane["divisions"].setValue( imath.V2i( 1000 ) )

		planeFilter = GafferScene.PathFilter()
		planeFilter["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		random = GafferScene.RandomPrimitiveVariable()
		random["in"].setInput( plane["out"] )
		random["filter"].setInput( planeFilter["out"] )
		random["distribution"].setValue( random.Distribution.UniformFloat )
		random["floatRange"].setValue( imath.V2f( -1001, 10342 ) )

		values = random["out"].object( "/plane" )["random"].data
		self.assertIsInstance( values, IECore.FloatVectorData )
		minValue = min( values )
		maxValue = max( values )
		self.assertAlmostEqual( minValue, -1001, delta = 0.04 )
		self.assertAlmostEqual( maxValue, 10342, delta = 0.04 )
		self.assertAlmostEqual( sum( values ) / len( values ), ( -1001 + 10342 ) / 2, delta = 1.1 )

	def testGaussian( self ) :

		plane = GafferScene.Plane()
		plane["divisions"].setValue( imath.V2i( 1000 ) )

		planeFilter = GafferScene.PathFilter()
		planeFilter["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		random = GafferScene.RandomPrimitiveVariable()
		random["in"].setInput( plane["out"] )
		random["filter"].setInput( planeFilter["out"] )
		random["distribution"].setValue( random.Distribution.Gaussian )
		random["mean"].setValue( 10 )
		random["deviation"].setValue( 2 )

		values = random["out"].object( "/plane" )["random"].data
		self.assertIsInstance( values, IECore.FloatVectorData )
		mean = sum( values ) / len( values )
		self.assertAlmostEqual( mean, 10, delta = 0.05 )
		deviation = math.sqrt( sum( pow( v - mean, 2 ) for v in values ) / len( values ) )
		self.assertAlmostEqual( deviation, 2, delta = 0.05 )

	def testWeightedChoice( self ) :

		plane = GafferScene.Plane()
		plane["divisions"].setValue( imath.V2i( 1000 ) )

		planeFilter = GafferScene.PathFilter()
		planeFilter["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		random = GafferScene.RandomPrimitiveVariable()
		random["in"].setInput( plane["out"] )
		random["filter"].setInput( planeFilter["out"] )
		random["distribution"].setValue( random.Distribution.WeightedChoice )
		random.setup( Gaffer.FloatVectorDataPlug() )
		random["choices"]["values"].setValue( IECore.FloatVectorData( [ 101, 102, 103 ] ) )
		random["choices"]["weights"].setValue( IECore.FloatVectorData( [ 1, 2, 3 ] ) )

		variable = random["out"].object( "/plane" )["random"]
		self.assertIsNone( variable.indices )
		self.assertIsInstance( variable.data, IECore.FloatVectorData )
		self.assertEqual( set( variable.data ), { 101, 102, 103 } )
		self.assertAlmostEqual( variable.data.count( 101 ) / variable.data.size(), 1 / 6, delta = 0.1 )
		self.assertAlmostEqual( variable.data.count( 102 ) / variable.data.size(), 2 / 6, delta = 0.1 )
		self.assertAlmostEqual( variable.data.count( 103 ) / variable.data.size(), 3 / 6, delta = 0.1 )

	def testWeightedChoiceProducingIndices( self ) :

		plane = GafferScene.Plane()
		plane["divisions"].setValue( imath.V2i( 1000 ) )

		planeFilter = GafferScene.PathFilter()
		planeFilter["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		random = GafferScene.RandomPrimitiveVariable()
		random["in"].setInput( plane["out"] )
		random["filter"].setInput( planeFilter["out"] )
		random["distribution"].setValue( random.Distribution.WeightedChoice )
		random.setup( Gaffer.StringVectorDataPlug() )
		random["choices"]["values"].setValue( IECore.StringVectorData( [ "a", "b", "c" ] ) )
		random["choices"]["weights"].setValue( IECore.FloatVectorData( [ 1, 2, 3 ] ) )

		variable = random["out"].object( "/plane" )["random"]
		self.assertEqual( variable.data, random["choices"]["values"].getValue() )
		self.assertEqual( set( variable.indices ), { 0, 1, 2 } )
		self.assertAlmostEqual( variable.indices.count( 0 ) / variable.indices.size(), 1 / 6, delta = 0.1 )
		self.assertAlmostEqual( variable.indices.count( 1 ) / variable.indices.size(), 2 / 6, delta = 0.1 )
		self.assertAlmostEqual( variable.indices.count( 2 ) / variable.indices.size(), 3 / 6, delta = 0.1 )

	def testWeightedChoiceWithoutSetup( self ) :

		plane = GafferScene.Plane()
		plane["divisions"].setValue( imath.V2i( 1000 ) )

		planeFilter = GafferScene.PathFilter()
		planeFilter["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		random = GafferScene.RandomPrimitiveVariable()
		random["in"].setInput( plane["out"] )
		random["filter"].setInput( planeFilter["out"] )
		random["distribution"].setValue( random.Distribution.WeightedChoice )

		self.assertEqual( random["out"].object( "/plane" ), random["in"].object( "/plane" ) )

	def testWeightedChoiceSerialisation( self ) :

		script = Gaffer.ScriptNode()
		script["random"] = GafferScene.RandomPrimitiveVariable()
		script["random"].setup( Gaffer.IntVectorDataPlug() )
		script["random"]["choices"]["values"].setValue( IECore.IntVectorData( [ 1, 2, 3 ] ) )
		script["random"]["choices"]["weights"].setValue( IECore.FloatVectorData( [ 2, 3, 4 ] ) )

		script2 = Gaffer.ScriptNode()
		script2.execute( script.serialise() )
		self.assertEqual( script2["random"].keys(), script["random"].keys() )
		self.assertEqual( script2["random"]["choices"].keys(), script["random"]["choices"].keys() )
		self.assertEqual( script2["random"]["choices"]["values"].getValue(), script["random"]["choices"]["values"].getValue() )
		self.assertEqual( script2["random"]["choices"]["weights"].getValue(), script["random"]["choices"]["weights"].getValue() )

		script3 = Gaffer.ScriptNode()
		script3.execute( script2.serialise() )
		self.assertEqual( script3["random"].keys(), script["random"].keys() )
		self.assertEqual( script3["random"]["choices"].keys(), script["random"]["choices"].keys() )
		self.assertEqual( script3["random"]["choices"]["values"].getValue(), script["random"]["choices"]["values"].getValue() )
		self.assertEqual( script3["random"]["choices"]["weights"].getValue(), script["random"]["choices"]["weights"].getValue() )

	def testHollowSphere( self ) :

		plane = GafferScene.Plane()
		plane["divisions"].setValue( imath.V2i( 1000 ) )

		planeFilter = GafferScene.PathFilter()
		planeFilter["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		random = GafferScene.RandomPrimitiveVariable()
		random["in"].setInput( plane["out"] )
		random["filter"].setInput( planeFilter["out"] )
		random["distribution"].setValue( random.Distribution.HollowSphere )
		random["radius"].setValue( 10 )

		values = random["out"].object( "/plane" )["random"].data
		self.assertIsInstance( values, IECore.V3fVectorData )
		for v in values :
			self.assertAlmostEqual( v.length(), 10, delta = 0.0001 )
		self.assertEqualWithAbsError(
			sum( values ) / len( values ), imath.V3f( 0 ), 0.01
		)

	def testHollowSphereInterpretation( self ) :

		plane = GafferScene.Plane()

		planeFilter = GafferScene.PathFilter()
		planeFilter["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		random = GafferScene.RandomPrimitiveVariable()
		random["in"].setInput( plane["out"] )
		random["filter"].setInput( planeFilter["out"] )
		random["distribution"].setValue( random.Distribution.HollowSphere )

		for interpretation in [
			IECore.GeometricData.Interpretation.Point,
			IECore.GeometricData.Interpretation.Vector,
			IECore.GeometricData.Interpretation.Normal,
		] :
			random["interpretation"].setValue( interpretation )
			self.assertEqual(
				random["out"].object( "/plane" )["random"].data.getInterpretation(),
				interpretation
			)

	def testSeed( self ) :

		plane = GafferScene.Plane()

		planeFilter = GafferScene.PathFilter()
		planeFilter["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		random = GafferScene.RandomPrimitiveVariable()
		random["in"].setInput( plane["out"] )
		random["filter"].setInput( planeFilter["out"] )

		valuesA = random["out"].object( "/plane" )["random"].data
		random["seed"].setValue( 1 )
		valuesB = random["out"].object( "/plane" )["random"].data

		self.assertNotEqual( valuesA, valuesB )

	def testSeedPrimitiveVariable( self ) :

		points = IECoreScene.PointsPrimitive( IECore.V3fVectorData( [ imath.V3f( 0 ), imath.V3f( 1 ) ] ) )
		points["seed"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.IntVectorData( [ 0, 1 ] )
		)

		objectToScene = GafferScene.ObjectToScene()
		objectToScene["object"].setValue( points )

		objectFilter = GafferScene.PathFilter()
		objectFilter["paths"].setValue( IECore.StringVectorData( [ "/object" ] ) )

		random = GafferScene.RandomPrimitiveVariable()
		random["in"].setInput( objectToScene["out"] )
		random["filter"].setInput( objectFilter["out"] )
		random["seedPrimitiveVariable"].setValue( "seed" )
		random["distribution"].setValue( random.Distribution.UniformInt )

		valuesA = random["out"].object( "/object" )["random"].data

		points["seed"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.IntVectorData( [ 1, 0 ] )
		)
		objectToScene["object"].setValue( points )

		valuesB = random["out"].object( "/object" )["random"].data

		self.assertEqual( valuesA[0], valuesB[1] )
		self.assertEqual( valuesA[1], valuesB[0] )

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testPerformance( self ) :

		plane = GafferScene.Plane()
		plane["divisions"].setValue( imath.V2i( 5000 ) )

		planeFilter = GafferScene.PathFilter()
		planeFilter["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		random = GafferScene.RandomPrimitiveVariable()
		random["in"].setInput( plane["out"] )
		random["filter"].setInput( planeFilter["out"] )
		random["distribution"].setValue( random.Distribution.Gaussian )

		random["in"].object( "/plane" ) # Precache input so it's not included in measurement.

		with GafferTest.TestRunner.PerformanceScope() :
			random["out"].object( "/plane" )
