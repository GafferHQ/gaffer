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

import imath

import IECore
import IECoreScene

import Gaffer
import GafferTest
import GafferScene
import GafferSceneTest

class PointInstancerTest( GafferSceneTest.SceneTestCase ) :

	def testBasics( self ) :

		plane = GafferScene.Plane()
		planeFilter = GafferScene.PathFilter()
		planeFilter["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		sphere = GafferScene.Sphere()

		instancer = GafferScene.PointInstancer()
		instancer["in"].setInput( plane["out"] )
		instancer["prototypes"].setInput( sphere["out"] )
		instancer["filter"].setInput( planeFilter["out"] )
		instancer["prototypesList"].setValue(
			IECore.StringVectorData( [ "/sphere" ] )
		)

		self.assertSceneValid( instancer["out"] )

		self.assertIsInstance(
			instancer["out"].object( "/plane" ), IECoreScene.PointInstancer
		)
		self.assertEqual(
			list( instancer["out"].object( "/plane" ).getPrototypes() ),
			[ "prototypes/sphere" ]
		)

		self.assertScenesEqual(
			sphere["out"],
			instancer["out"],
			scenePlug2PathPrefix = "/plane/prototypes",
		)

	def testPrototypesMode( self ) :

		plane = GafferScene.Plane()

		primitiveVariables = GafferScene.PrimitiveVariables()
		primitiveVariables["in"].setInput( plane["out"] )
		primitiveVariables["primitiveVariables"]["rootsPrimVar"] = Gaffer.NameValuePlug(
			"rootsPrimVar", IECore.StringVectorData( [ "/group/cube", "/group/sphere" ] )
		)

		planeFilter = GafferScene.PathFilter()
		planeFilter["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		sphere = GafferScene.Sphere()
		cube = GafferScene.Cube()

		group = GafferScene.Group()
		group["in"][0].setInput( sphere["out"] )
		group["in"][1].setInput( cube["out"] )

		instancer = GafferScene.PointInstancer()
		instancer["in"].setInput( primitiveVariables["out"] )
		instancer["prototypes"].setInput( sphere["out"] )
		instancer["filter"].setInput( planeFilter["out"] )

		self.assertEqual( instancer["prototypesMode"].getValue(), instancer.PrototypesMode.List )
		self.assertEqual( list( instancer["out"].object( "/plane" ).getPrototypes() ), [] )

		instancer["prototypesList"].setValue( IECore.StringVectorData( [ "/group/sphere" ] ) )
		self.assertEqual(
			list( instancer["out"].object( "/plane" ).getPrototypes() ), [ "prototypes/sphere" ]
		)

		instancer["prototypesMode"].setValue( instancer.PrototypesMode.PrimitiveVariable )
		self.assertEqual( list( instancer["out"].object( "/plane" ).getPrototypes() ), [] )

		instancer["prototypesPrimitiveVariable"].setValue( "rootsPrimVar" )
		self.assertEqual( list( instancer["out"].object( "/plane" ).getPrototypes() ), [ "prototypes/cube", "prototypes/sphere" ] )

	def testPrototypeIndexMode( self ) :

		points = IECoreScene.PointsPrimitive( IECore.V3fVectorData( [ imath.V3f( x ) for x in range( 0, 20 ) ] ) )
		points["index"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.IntVectorData( [ 0, 1 ] * 10 )
		)

		pointsNode = GafferScene.ObjectToScene()
		pointsNode["name"].setValue( "points" )
		pointsNode["object"].setValue( points )

		pointsFilter = GafferScene.PathFilter()
		pointsFilter["paths"].setValue( IECore.StringVectorData( [ "/points" ] ) )

		instancer = GafferScene.PointInstancer()
		instancer["in"].setInput( pointsNode["out"] )
		instancer["filter"].setInput( pointsFilter["out"] )
		instancer["prototypesList"].setValue( IECore.StringVectorData( [ "/proto1", "/proto2" ] ) )

		self.assertEqual( instancer["prototypeIndexMode"].getValue(), instancer.PrototypeIndexMode.Constant )
		self.assertEqual(
			list( instancer["out"].object( "/points" ).getPrototypeIndex() ), [ 0 ] * 20
		)
		instancer["prototypeIndex"].setValue( 1 )
		self.assertEqual(
			list( instancer["out"].object( "/points" ).getPrototypeIndex() ), [ 1 ] * 20
		)

		instancer["prototypeIndexMode"].setValue( instancer.PrototypeIndexMode.Random )
		self.assertEqual(
			list( instancer["out"].object( "/points" ).getPrototypeIndex() ), [ 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 1, 1, 0, 1, 1, 0, 0, 0 ]
		)
		instancer["prototypeIndexSeed"].setValue( 1 )
		self.assertEqual(
			list( instancer["out"].object( "/points" ).getPrototypeIndex() ), [ 0, 0, 1, 1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 0, 1, 1, 0, 0, 1, 1 ]
		)

		instancer["prototypeIndexMode"].setValue( instancer.PrototypeIndexMode.PrimitiveVariable )
		self.assertFalse( instancer["out"].object( "/points" ).getPrototypeIndex() )
		instancer["prototypeIndexPrimitiveVariable"].setValue( "index" )
		self.assertEqual( list( instancer["out"].object( "/points" ).getPrototypeIndex() ), [ 0, 1 ] * 10 )

	def testNoPrototypeOutputWithoutPointsInput( self ) :

		group = GafferScene.Group()
		groupFilter = GafferScene.PathFilter()
		groupFilter["paths"].setValue( IECore.StringVectorData( [ "/group" ] ) )

		sphere = GafferScene.Sphere()

		instancer = GafferScene.PointInstancer()
		instancer["in"].setInput( group["out"] )
		instancer["prototypes"].setInput( sphere["out"] )
		instancer["filter"].setInput( groupFilter["out"] )
		instancer["prototypesList"].setValue(
			IECore.StringVectorData( [ "/sphere" ] )
		)

		self.assertScenesEqual( instancer["in"], instancer["out"] )

	def testPrototypesNotPrunedWhenNoPoints( self ) :

		# /group
		#    /prototypes
		#       /sphere

		group = GafferScene.Group()
		groupFilter = GafferScene.PathFilter()
		groupFilter["paths"].setValue( IECore.StringVectorData( [ "/group" ] ) )

		sphere = GafferScene.Sphere()

		prototypesGroup = GafferScene.Group()
		prototypesGroup["in"][0].setInput( sphere["out"] )
		prototypesGroup["name"].setValue( "prototypes" )

		parent = GafferScene.Parent()
		parent["in"].setInput( group["out"] )
		parent["children"][0].setInput( prototypesGroup["out"] )
		parent["parent"].setValue( "/group" )

		instancer = GafferScene.PointInstancer()
		instancer["in"].setInput( group["out"] )
		instancer["prototypes"].setInput( sphere["out"] )
		instancer["filter"].setInput( groupFilter["out"] )
		instancer["prototypesList"].setValue(
			IECore.StringVectorData( [ "/sphere" ] )
		)

		self.assertScenesEqual( instancer["in"], instancer["out"] )

	def testTimeOffset( self ) :

		points = IECoreScene.PointsPrimitive( IECore.V3fVectorData( [ imath.V3f( 0 ), imath.V3f( 1 ) ] ) )
		points["timeOffset"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.FloatVectorData( [ 0, 1 ] )
		)

		pointsNode = GafferScene.ObjectToScene()
		pointsNode["name"].setValue( "points" )
		pointsNode["object"].setValue( points )

		pointsFilter = GafferScene.PathFilter()
		pointsFilter["paths"].setValue( IECore.StringVectorData( [ "/points" ] ) )

		frame = GafferTest.FrameNode()

		sphere = GafferScene.Sphere()
		sphere["radius"].setInput( frame["output"] )
		sphere["type"].setValue( sphere.Type.Primitive )

		instancer = GafferScene.PointInstancer()
		instancer["in"].setInput( pointsNode["out"] )
		instancer["prototypes"].setInput( sphere["out"] )
		instancer["filter"].setInput( pointsFilter["out"] )
		instancer["prototypesList"].setValue(
			IECore.StringVectorData( [ "/sphere" ] )
		)
		instancer["timeOffset"].setValue( "timeOffset" )

		# Check prototypes.

		self.assertEqual( instancer["out"].childNames( "/points/prototypes" ), IECore.InternedStringVectorData( [ "sphere_0", "sphere_1" ] ) )
		self.assertEqual( instancer["out"].object( "/points/prototypes/sphere_0" ).radius(), 1 )
		self.assertEqual( instancer["out"].object( "/points/prototypes/sphere_1" ).radius(), 2 )

		# Check points.

		points = instancer["out"].object( "/points" )
		self.assertEqual( list( points.getPrototypes() ), [ "prototypes/sphere_0", "prototypes/sphere_1" ] )
		self.assertEqual( list( points.getPrototypeIndex() ), [ 0, 1 ] )

	def testContextVariables( self ) :

		points = IECoreScene.PointsPrimitive( IECore.V3fVectorData( [ imath.V3f( 0 ), imath.V3f( 1 ) ] ) )
		points["varA"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.FloatVectorData( [ 0, 1 ] )
		)
		points["varB"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.FloatVectorData( [ 2, 3 ] )
		)

		pointsNode = GafferScene.ObjectToScene()
		pointsNode["name"].setValue( "points" )
		pointsNode["object"].setValue( points )

		pointsFilter = GafferScene.PathFilter()
		pointsFilter["paths"].setValue( IECore.StringVectorData( [ "/points" ] ) )

		sphere = GafferScene.Sphere()

		primitiveVariables = GafferScene.PrimitiveVariables()
		primitiveVariables["in"].setInput( sphere["out"] )
		primitiveVariables["primitiveVariables"].addChild( Gaffer.NameValuePlug( "varA", "${varA}" ) )
		primitiveVariables["primitiveVariables"].addChild( Gaffer.NameValuePlug( "varB", "${varB}" ) )

		instancer = GafferScene.PointInstancer()
		instancer["in"].setInput( pointsNode["out"] )
		instancer["prototypes"].setInput( primitiveVariables["out"] )
		instancer["filter"].setInput( pointsFilter["out"] )
		instancer["prototypesList"].setValue(
			IECore.StringVectorData( [ "/sphere" ] )
		)
		instancer["contextVariables"].setValue( "var*" )

		# Check prototypes.

		self.assertEqual( instancer["out"].childNames( "/points/prototypes" ), IECore.InternedStringVectorData( [ "sphere_varA_0_varB_2", "sphere_varA_1_varB_3" ] ) )
		self.assertEqual( instancer["out"].object( "/points/prototypes/sphere_varA_0_varB_2" )["varA"].data.value, "0" )
		self.assertEqual( instancer["out"].object( "/points/prototypes/sphere_varA_0_varB_2" )["varB"].data.value, "2" )
		self.assertEqual( instancer["out"].object( "/points/prototypes/sphere_varA_1_varB_3" )["varA"].data.value, "1" )
		self.assertEqual( instancer["out"].object( "/points/prototypes/sphere_varA_1_varB_3" )["varB"].data.value, "3" )

		# Check points.

		points = instancer["out"].object( "/points" )
		self.assertEqual( list( points.getPrototypes() ), [ "prototypes/sphere_varA_0_varB_2", "prototypes/sphere_varA_1_varB_3" ] )
		self.assertEqual( list( points.getPrototypeIndex() ), [ 0, 1 ] )

	def testNoContextLeakage( self ) :

		plane = GafferScene.Plane()
		planeFilter = GafferScene.PathFilter()
		planeFilter["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		sphere = GafferScene.Sphere()

		instancer = GafferScene.PointInstancer()
		instancer["in"].setInput( plane["out"] )
		instancer["prototypes"].setInput( sphere["out"] )
		instancer["filter"].setInput( planeFilter["out"] )
		instancer["prototypesList"].setValue(
			IECore.StringVectorData( [ "/sphere" ] )
		)

		with Gaffer.ContextMonitor( plane ) as pointsMonitor :
			with Gaffer.ContextMonitor( sphere ) as prototypeMonitor :
				# Simple way to process the whole scene.
				self.assertScenesEqual( instancer["out"], instancer["out"] )

		self.assertEqual(
			set( pointsMonitor.combinedStatistics().variableNames() ),
			{ "scene:path", "frame", "framesPerSecond" }
		)

		self.assertEqual(
			set( prototypeMonitor.combinedStatistics().variableNames() ),
			{ "scene:path", "frame", "framesPerSecond" }
		)

	def testAddVariationToExistingPointInstancer( self ) :

		# Make a PointInstancer with a single animated prototype.

		points = IECoreScene.PointsPrimitive( IECore.V3fVectorData( [ imath.V3f( 0 ), imath.V3f( 1 ) ] ) )
		points["timeOffset"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.FloatVectorData( [ 0, 1 ] )
		)

		pointsNode = GafferScene.ObjectToScene()
		pointsNode["name"].setValue( "points" )
		pointsNode["object"].setValue( points )

		pointsFilter = GafferScene.PathFilter()
		pointsFilter["paths"].setValue( IECore.StringVectorData( [ "/points" ] ) )

		frame = GafferTest.FrameNode()

		sphere = GafferScene.Sphere()
		sphere["radius"].setInput( frame["output"] )
		sphere["type"].setValue( sphere.Type.Primitive )

		instancer = GafferScene.PointInstancer()
		instancer["in"].setInput( pointsNode["out"] )
		instancer["prototypes"].setInput( sphere["out"] )
		instancer["filter"].setInput( pointsFilter["out"] )
		instancer["prototypesList"].setValue(
			IECore.StringVectorData( [ "/sphere" ] )
		)
		instancer["attributes"].setValue( "timeOffset" )

		self.assertSceneValid( instancer["out"] )

		self.assertIsInstance(
			instancer["out"].object( "/points" ), IECoreScene.PointInstancer
		)
		self.assertEqual(
			list( instancer["out"].object( "/points" ).getPrototypes() ),
			[ "prototypes/sphere" ]
		)

		# Now make a second PointInstancer node that adds variation to
		# the prototypes downstream. In this way, a user could add interest
		# to a plain PointInstancer imported from USD.

		variationInstancer = GafferScene.PointInstancer()
		variationInstancer["in"].setInput( instancer["out"] )
		variationInstancer["prototypes"].setInput( instancer["out"] )
		variationInstancer["filter"].setInput( pointsFilter["out"] )
		variationInstancer["prototypesMode"].setValue( variationInstancer.PrototypesMode.None_ )

		variationInstancer["prototypeIndexMode"].setValue( variationInstancer.PrototypeIndexMode.None_ )
		variationInstancer["timeOffset"].setValue( "timeOffset" )

		# Check PointInstancer.

		points = variationInstancer["out"].object( "/points" )
		self.assertEqual( list( points.getPrototypes() ), [ "prototypes/sphere_0", "prototypes/sphere_1" ] )
		self.assertEqual( list( points.getPrototypeIndex() ), [ 0, 1 ] )

		# Check prototypes.

		self.assertEqual( variationInstancer["out"].childNames( "/points" ), IECore.InternedStringVectorData( [ "prototypes" ] ) )
		self.assertEqual( variationInstancer["out"].childNames( "/points/prototypes" ), IECore.InternedStringVectorData( [ "sphere_0", "sphere_1" ] ) )
		self.assertEqual( variationInstancer["out"].object( "/points/prototypes/sphere_0" ).radius(), 1 )
		self.assertEqual( variationInstancer["out"].object( "/points/prototypes/sphere_1" ).radius(), 2 )

	def testShadingAttributes( self ) :

		plane = GafferScene.Plane()
		planeFilter = GafferScene.PathFilter()
		planeFilter["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		sphere = GafferScene.Sphere()

		instancer = GafferScene.PointInstancer()
		instancer["in"].setInput( plane["out"] )
		instancer["prototypes"].setInput( sphere["out"] )
		instancer["filter"].setInput( planeFilter["out"] )
		instancer["prototypesList"].setValue(
			IECore.StringVectorData( [ "/sphere" ] )
		)

		self.assertEqual(
			set( instancer["out"].object( "/plane" ).keys() ),
			{ "P", "prototypeRoots", "prototypeIndex" },
		)

		instancer["attributes"].setValue( "uv" )
		self.assertEqual(
			set( instancer["out"].object( "/plane" ).keys() ),
			{ "P", "prototypeRoots", "prototypeIndex", "uv" },
		)
