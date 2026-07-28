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
import GafferTest
import GafferScene
import GafferSceneTest

class PointInstancerAlgoTest( GafferSceneTest.SceneTestCase ) :

	class PrototypeGroup( GafferScene.SceneNode ) :

		def __init__( self, name = "PrototypeGroup" ) :

			GafferScene.SceneNode.__init__( self, name )

			self["name"] = Gaffer.StringPlug( defaultValue = "prototype" )
			self["transform"] = Gaffer.TransformPlug()
			self["sphereEnabled"] = Gaffer.BoolPlug( defaultValue = True )
			self["sphereTransform"] = Gaffer.TransformPlug()
			self["spherePurpose"] = Gaffer.StringPlug()
			self["cubeEnabled"] = Gaffer.BoolPlug( defaultValue = True )
			self["cubeTransform"] = Gaffer.TransformPlug()
			self["cubeDimensions"] = Gaffer.V3fPlug( defaultValue = imath.V3f( 1 ) )
			self["cubePurpose"] = Gaffer.StringPlug()
			self["planeEnabled"] = Gaffer.BoolPlug( defaultValue = True )
			self["planeTransform"] = Gaffer.TransformPlug()

			self["__sphere"] = GafferScene.Sphere()
			self["__sphere"]["enabled"].setInput( self["sphereEnabled"] )
			self["__sphere"]["transform"].setInput( self["sphereTransform"] )

			self["__sphereAttributes"] = GafferScene.CustomAttributes()
			self["__sphereAttributes"]["in"].setInput( self["__sphere"]["out"] )
			self["__sphereAttributes"]["attributes"].addChild( Gaffer.NameValuePlug( "usd:purpose", "", defaultEnabled = True ) )
			self["__sphereAttributes"]["attributes"][0]["enabled"].setInput( self["spherePurpose" ] )
			self["__sphereAttributes"]["attributes"][0]["value"].setInput( self["spherePurpose" ] )

			self["__cube"] = GafferScene.Cube()
			self["__cube"]["enabled"].setInput( self["cubeEnabled"] )
			self["__cube"]["transform"].setInput( self["cubeTransform"] )
			self["__cube"]["dimensions"].setInput( self["cubeDimensions"] )

			self["__plane"] = GafferScene.Plane()
			self["__plane"]["enabled"].setInput( self["planeEnabled"] )
			self["__plane"]["transform"].setInput( self["planeTransform"] )

			self["__group"] = GafferScene.Group()
			self["__group"]["name"].setInput( self["name"] )
			self["__group"]["transform"].setInput( self["transform"] )
			self["__group"]["in"][0].setInput( self["__sphereAttributes"]["out"] )
			self["__group"]["in"][1].setInput( self["__cube"]["out"] )
			self["__group"]["in"][2].setInput( self["__plane"]["out"] )

			self["out"].setInput( self["__group"]["out"] )

	@GafferTest.TestRunner.CategorisedTestMethod( { "pointInstancer" } )
	def testPrototypesHash( self ) :

		prototypeGroup = GafferScene.Group()
		prototypeGroup["name"].setValue( "prototypes" )

		prototypeNodes = []
		prototypeRoots = []
		for i in range( 0, 100 ) :

			prototype = self.PrototypeGroup()
			prototype["name"].setValue( f"prototype{i}" )
			prototypeNodes.append( prototype )

			prototypeGroup["in"][i].setInput( prototype["out"] )
			prototypeRoots.append( f"prototypes/prototype{i}" )

		pointInstancer = IECoreScene.PointInstancer( 2 )
		pointInstancer.setPrototypes( IECore.StringVectorData( prototypeRoots ) )

		pointInstancerNode = GafferScene.ObjectToScene()
		pointInstancerNode["object"].setValue( pointInstancer )
		pointInstancerNode["name"].setValue( "instancer" )

		parent = GafferScene.Parent()
		parent["in"].setInput( pointInstancerNode["out"] )
		parent["children"][0].setInput( prototypeGroup["out"] )
		parent["parent"].setValue( "/instancer" )

		hashes = set()
		with Gaffer.Context() as context :

			context["scene:path"] = GafferScene.ScenePlug.stringToPath( "/instancer" )

			# 100 unique transform edits gives 100 unique hashes.

			for i in range( 0, 100 ) :
				prototypeNodes[i]["sphereTransform"]["translate"].setValue( imath.V3f( i, 0, 0 ) )
				hashes.add( GafferScene.Private.PointInstancerAlgo.prototypesHash( parent["out"] ) )

			self.assertEqual( len( hashes ), 100 )

			# 100 unique object edits gives 100 unique hashes.

			for i in range( 0, 100 ) :
				prototypeNodes[i]["cubeDimensions"]["x"].setValue( 2 + i )
				hashes.add( GafferScene.Private.PointInstancerAlgo.prototypesHash( parent["out"] ) )

			self.assertEqual( len( hashes ), 200 )

			# Attribute edit also affects the hash.

			prototypeNodes[0]["spherePurpose"].setValue( "proxy" )
			self.assertNotIn( GafferScene.Private.PointInstancerAlgo.prototypesHash( parent["out"] ), hashes )

			# Hash is stable from run to run.

			h = GafferScene.Private.PointInstancerAlgo.prototypesHash( parent["out"] )
			for i in range( 1, 100 ) :
				self.assertEqual( GafferScene.Private.PointInstancerAlgo.prototypesHash( parent["out"] ), h )

	@GafferTest.TestRunner.CategorisedTestMethod( { "pointInstancer" } )
	def testPrototypesHashWithoutPointInstancer( self ) :

		plane = GafferScene.Plane()

		with Gaffer.Context() as context :
			context["scene:path"] = GafferScene.ScenePlug.stringToPath( "/plane" )
			self.assertEqual( GafferScene.Private.PointInstancerAlgo.prototypesHash( plane["out"] ), IECore.MurmurHash() )

	@GafferTest.TestRunner.CategorisedTestMethod( { "pointInstancer" } )
	def testPrototypesHashWithoutPrototypes( self ) :

		pointInstancer = IECoreScene.PointInstancer( 2 )
		pointInstancerNode = GafferScene.ObjectToScene()
		pointInstancerNode["object"].setValue( pointInstancer )
		pointInstancerNode["name"].setValue( "instancer" )

		with Gaffer.Context() as context :
			context["scene:path"] = GafferScene.ScenePlug.stringToPath( "/instancer" )
			self.assertEqual( GafferScene.Private.PointInstancerAlgo.prototypesHash( pointInstancerNode["out"] ), IECore.MurmurHash() )

	@GafferTest.TestRunner.CategorisedTestMethod( { "pointInstancer" } )
	def testPrototypesHashWithMissingPrototype( self ) :

		pointInstancer = IECoreScene.PointInstancer( 2 )
		pointInstancer.setPrototypes( IECore.StringVectorData( [ "prototypes/missing" ] ) )

		pointInstancerNode = GafferScene.ObjectToScene()
		pointInstancerNode["object"].setValue( pointInstancer )
		pointInstancerNode["name"].setValue( "instancer" )

		with Gaffer.Context() as context :
			context["scene:path"] = GafferScene.ScenePlug.stringToPath( "/instancer" )
			# Missing prototypes are just ignored at this stage. They'll be reported
			# properly by `flatten()`.
			self.assertEqual( GafferScene.Private.PointInstancerAlgo.prototypesHash( pointInstancerNode["out"] ), IECore.MurmurHash() )

	@GafferTest.TestRunner.CategorisedTestMethod( { "pointInstancer" } )
	def testFlatten( self ) :

		prototype1 = self.PrototypeGroup()
		prototype1["name"].setValue( "prototype1" )
		prototype1["sphereTransform"]["translate"].setValue( imath.V3f( 1, 0, 0 ) )
		prototype2 = self.PrototypeGroup()
		prototype2["name"].setValue( "prototype2" )
		prototype2["planeEnabled"].setValue( False )

		prototypeGroup = GafferScene.Group()
		prototypeGroup["name"].setValue( "prototypes" )
		prototypeGroup["in"][0].setInput( prototype1["out"] )
		prototypeGroup["in"][1].setInput( prototype2["out"] )

		pointInstancer = IECoreScene.PointInstancer( 2 )
		pointInstancer.setPosition( IECore.V3fVectorData( [ imath.V3f( 1, 2, 3 ), imath.V3f( 1, 0, 0 ) ] ) )
		pointInstancer.setPrototypeIndex( IECore.IntVectorData( [ 0, 1 ] ) )
		pointInstancer.setPrototypes( IECore.StringVectorData( [ "prototypes/prototype1", "prototypes/prototype2" ] ) )

		pointInstancerNode = GafferScene.ObjectToScene()
		pointInstancerNode["object"].setValue( pointInstancer )
		pointInstancerNode["name"].setValue( "instancer" )

		parent = GafferScene.Parent()
		parent["in"].setInput( pointInstancerNode["out"] )
		parent["children"][0].setInput( prototypeGroup["out"] )
		parent["parent"].setValue( "/instancer" )

		with Gaffer.Context() as context :

			context["scene:path"] = GafferScene.ScenePlug.stringToPath( "/instancer" )
			pointInstancer = parent["out"]["object"].getValue()
			self.assertEqual( pointInstancer, pointInstancerNode["object"].getValue() )

			flattened = GafferScene.Private.PointInstancerAlgo.flatten(
				pointInstancer, GafferScene.Private.RendererAlgo.RenderOptions(), parent["out"]
			)

			self.assertTrue( isinstance( flattened, IECoreScene.PointInstancer ) )
			self.assertTrue( flattened.arePrimitiveVariablesValid() )
			self.assertEqual( flattened.numPoints, 5 )
			self.assertEqual(
				list( flattened["prototypeRoots"].data ),
				[
					"prototypes/prototype1/cube",
					"prototypes/prototype1/plane",
					"prototypes/prototype1/sphere",
					"prototypes/prototype2/cube",
					"prototypes/prototype2/sphere",
				]
			)

			self.assertEqual(
				list( flattened.getPosition() ),
				[
					imath.V3f( 1, 2, 3 ),
					imath.V3f( 1, 2, 3 ),
					imath.V3f( 2, 2, 3 ),
					imath.V3f( 1, 0, 0 ),
					imath.V3f( 1, 0, 0 ),
				]
			)

	@GafferTest.TestRunner.CategorisedTestMethod( { "pointInstancer" } )
	def testFlattenIncludesRootTransform( self ) :

		prototype = self.PrototypeGroup()
		prototype["transform"]["scale"].setValue( imath.V3f( 2, 3, 4 ) )
		prototype["sphereTransform"]["translate"].setValue( imath.V3f( 1, 0, 0 ) )
		prototype["cubeEnabled"].setValue( False )
		prototype["planeEnabled"].setValue( False )

		pointInstancer = IECoreScene.PointInstancer( 2 )
		pointInstancer.setPosition( IECore.V3fVectorData( [ imath.V3f( 0 ), imath.V3f( 1, 2, 3 ) ] ) )
		pointInstancer.setPrototypeIndex( IECore.IntVectorData( [ 0, 0 ] ) )
		pointInstancer.setPrototypes( IECore.StringVectorData( [ "prototype" ] ) )

		pointInstancerNode = GafferScene.ObjectToScene()
		pointInstancerNode["object"].setValue( pointInstancer )
		pointInstancerNode["name"].setValue( "instancer" )

		parent = GafferScene.Parent()
		parent["in"].setInput( pointInstancerNode["out"] )
		parent["children"][0].setInput( prototype["out"] )
		parent["parent"].setValue( "/instancer" )

		with Gaffer.Context() as context :

			context["scene:path"] = GafferScene.ScenePlug.stringToPath( "/instancer" )
			pointInstancer = parent["out"]["object"].getValue()
			self.assertEqual( pointInstancer, pointInstancerNode["object"].getValue() )

			flattened = GafferScene.Private.PointInstancerAlgo.flatten(
				pointInstancer, GafferScene.Private.RendererAlgo.RenderOptions(), parent["out"]
			)
			self.assertEqual( flattened.numPoints, 2 )
			self.assertTrue( flattened.arePrimitiveVariablesValid() )

			query = IECoreScene.PointInstancer.TransformQuery( flattened )
			for i, point in enumerate( pointInstancer.getPosition() ) :
				self.assertEqual(
					query.transform( i ),
					# Strictly speaking we want the relative transform from `instancer`
					# to `sphere`, but since we know `instancer` has an identify transform
					# we can use the handy `fullTransform()` method instead.
					parent["out"].fullTransform( "/instancer/prototype/sphere" ) * imath.M44f().translate( point )
				)

	@GafferTest.TestRunner.CategorisedTestMethod( { "pointInstancer" } )
	def testFlattenFilteredByPurpose( self ) :

		prototype = self.PrototypeGroup()

		pointInstancer = IECoreScene.PointInstancer( 2 )
		pointInstancer.setPosition( IECore.V3fVectorData( [ imath.V3f( 1, 2, 3 ), imath.V3f( 1, 0, 0 ) ] ) )
		pointInstancer.setPrototypeIndex( IECore.IntVectorData( [ 0, 0 ] ) )
		pointInstancer.setPrototypes( IECore.StringVectorData( [ "prototype" ] ) )

		pointInstancerNode = GafferScene.ObjectToScene()
		pointInstancerNode["object"].setValue( pointInstancer )
		pointInstancerNode["name"].setValue( "instancer" )

		parent = GafferScene.Parent()
		parent["in"].setInput( pointInstancerNode["out"] )
		parent["children"][0].setInput( prototype["out"] )
		parent["parent"].setValue( "/instancer" )

		for spherePurpose in ( "proxy", "render" ) :

			with self.subTest( spherePurpose = spherePurpose ) :

				prototype["spherePurpose"].setValue( spherePurpose )

				with Gaffer.Context() as context :

					context["scene:path"] = GafferScene.ScenePlug.stringToPath( "/instancer" )
					pointInstancer = parent["out"]["object"].getValue()
					options = GafferScene.Private.RendererAlgo.RenderOptions()
					options.includedPurposes = IECore.StringVectorData( [ "proxy" ] )
					flattened = GafferScene.Private.PointInstancerAlgo.flatten(
						pointInstancer, options, parent["out"]
					)

					self.assertTrue( isinstance( flattened, IECoreScene.PointInstancer ) )
					self.assertTrue( flattened.arePrimitiveVariablesValid() )

					if spherePurpose == "proxy" :
						self.assertEqual( flattened.numPoints, 2 )
						self.assertEqual(
							list( flattened.getPrototypes() ),
							[
								"prototype/sphere",
							]
						)
						self.assertEqual(
							list( flattened.getPosition() ),
							[
								imath.V3f( 1, 2, 3 ),
								imath.V3f( 1, 0, 0 ),
							]
						)
					else :
						self.assertEqual( flattened.numPoints, 0 )
						self.assertEqual( len( flattened.getPrototypes() ), 0 )
						self.assertEqual( len( flattened.getPosition() ), 0 )

	@GafferTest.TestRunner.CategorisedTestMethod( { "pointInstancer" } )
	def testFlattenFilteredByVisibility( self ) :

		prototype = GafferScene.Sphere()

		pointInstancer = IECoreScene.PointInstancer( 2 )
		pointInstancer.setPosition( IECore.V3fVectorData( [ imath.V3f( i ) for i in range( 0, 20 ) ] ) )
		pointInstancer.setPrototypeIndex( IECore.IntVectorData( [ 0 ] * 20 ) )
		pointInstancer.setPrototypes( IECore.StringVectorData( [ "sphere" ] ) )
		pointInstancer.setInvisibleIDs( IECore.Int64VectorData( range( 0, 20, 2 ) ) )

		pointInstancerNode = GafferScene.ObjectToScene()
		pointInstancerNode["object"].setValue( pointInstancer )
		pointInstancerNode["name"].setValue( "instancer" )

		parent = GafferScene.Parent()
		parent["in"].setInput( pointInstancerNode["out"] )
		parent["children"][0].setInput( prototype["out"] )
		parent["parent"].setValue( "/instancer" )

		with Gaffer.Context() as context :

			context["scene:path"] = GafferScene.ScenePlug.stringToPath( "/instancer" )
			pointInstancer = parent["out"]["object"].getValue()
			flattened = GafferScene.Private.PointInstancerAlgo.flatten(
				pointInstancer, GafferScene.Private.RendererAlgo.RenderOptions(), parent["out"]
			)

			self.assertTrue( isinstance( flattened, IECoreScene.PointInstancer ) )
			self.assertTrue( flattened.arePrimitiveVariablesValid() )

			self.assertEqual( flattened.numPoints, 10 )
			self.assertEqual( list( flattened.getPosition() ), [ imath.V3f( i ) for i in range( 1, 20, 2 ) ] )

	@GafferTest.TestRunner.CategorisedTestMethod( { "pointInstancer" } )
	def testFlattenWithMissingPrototype( self ) :

		pointInstancer = IECoreScene.PointInstancer( 2 )
		pointInstancer.setPrototypes( IECore.StringVectorData( [ "prototypes/missing" ] ) )
		pointInstancer.setPosition( IECore.V3fVectorData( [ imath.V3f( 0 ) ] ) )
		pointInstancer.setPrototypeIndex( IECore.IntVectorData( [ 0 ] ) )

		pointInstancerNode = GafferScene.ObjectToScene()
		pointInstancerNode["object"].setValue( pointInstancer )
		pointInstancerNode["name"].setValue( "instancer" )

		with Gaffer.Context() as context :

			context["scene:path"] = GafferScene.ScenePlug.stringToPath( "/instancer" )
			pointInstancer = pointInstancerNode["out"]["object"].getValue()
			with IECore.CapturingMessageHandler() as mh :
				flattened = GafferScene.Private.PointInstancerAlgo.flatten(
					pointInstancer, GafferScene.Private.RendererAlgo.RenderOptions( pointInstancerNode["out"] ), pointInstancerNode["out"]
				)

			self.assertTrue( isinstance( flattened, IECoreScene.PointInstancer ) )
			self.assertTrue( flattened.arePrimitiveVariablesValid() )
			self.assertEqual( flattened.numPoints, 0 )
			self.assertEqual( len( flattened.getPrototypes() ), 0 )

			self.assertEqual( len( mh.messages ), 1 )
			self.assertEqual( mh.messages[0].level, IECore.Msg.Level.Warning )
			self.assertEqual( mh.messages[0].message, "Prototype `/instancer/prototypes/missing` does not exist for instancer `/instancer`." )

	@GafferTest.TestRunner.CategorisedTestMethod( { "pointInstancer" } )
	def testFlattenWithPrimitivePrototype( self ) :

		prototype = GafferScene.Sphere()

		prototypeGroup = GafferScene.Group()
		prototypeGroup["name"].setValue( "prototypes" )
		prototypeGroup["in"][0].setInput( prototype["out"] )

		pointInstancer = IECoreScene.PointInstancer( 1 )
		pointInstancer.setPosition( IECore.V3fVectorData( [ imath.V3f( 0 ) ] ) )
		pointInstancer.setPrototypes( IECore.StringVectorData( [ "prototypes/sphere" ] ) )
		pointInstancer.setPrototypeIndex( IECore.IntVectorData( [ 0 ] ) )

		pointInstancerNode = GafferScene.ObjectToScene()
		pointInstancerNode["object"].setValue( pointInstancer )
		pointInstancerNode["name"].setValue( "instancer" )

		parent = GafferScene.Parent()
		parent["in"].setInput( pointInstancerNode["out"] )
		parent["children"][0].setInput( prototypeGroup["out"] )
		parent["parent"].setValue( "/instancer" )

		with Gaffer.Context() as context :

			context["scene:path"] = GafferScene.ScenePlug.stringToPath( "/instancer" )
			pointInstancer = parent["out"]["object"].getValue()
			self.assertEqual( pointInstancer, pointInstancerNode["object"].getValue() )

			flattened = GafferScene.Private.PointInstancerAlgo.flatten(
				pointInstancer, GafferScene.Private.RendererAlgo.RenderOptions(), parent["out"]
			)

			self.assertTrue( isinstance( flattened, IECoreScene.PointInstancer ) )
			self.assertTrue( flattened.arePrimitiveVariablesValid() )
			self.assertEqual( flattened.numPoints, 1 )
			self.assertEqual(
				list( flattened["prototypeRoots"].data ),
				[ "prototypes/sphere" ]
			)

	@GafferTest.TestRunner.CategorisedTestMethod( { "pointInstancer" } )
	def testFlattenWithOutOfRangePrototypeIndex( self ) :

		prototype = GafferScene.Sphere()

		prototypeGroup = GafferScene.Group()
		prototypeGroup["name"].setValue( "prototypes" )
		prototypeGroup["in"][0].setInput( prototype["out"] )

		pointInstancer = IECoreScene.PointInstancer( 3 )
		pointInstancer.setPosition( IECore.V3fVectorData( [ imath.V3f( x ) for x in range( 0, 3 ) ] ) )
		pointInstancer.setPrototypes( IECore.StringVectorData( [ "prototypes/sphere" ] ) )
		pointInstancer.setPrototypeIndex( IECore.IntVectorData( [ -1, 0, 1 ] ) )

		pointInstancerNode = GafferScene.ObjectToScene()
		pointInstancerNode["object"].setValue( pointInstancer )
		pointInstancerNode["name"].setValue( "instancer" )

		parent = GafferScene.Parent()
		parent["in"].setInput( pointInstancerNode["out"] )
		parent["children"][0].setInput( prototypeGroup["out"] )
		parent["parent"].setValue( "/instancer" )

		with Gaffer.Context() as context :

			context["scene:path"] = GafferScene.ScenePlug.stringToPath( "/instancer" )
			pointInstancer = parent["out"]["object"].getValue()
			self.assertEqual( pointInstancer, pointInstancerNode["object"].getValue() )

			flattened = GafferScene.Private.PointInstancerAlgo.flatten(
				pointInstancer, GafferScene.Private.RendererAlgo.RenderOptions(), parent["out"]
			)

			self.assertTrue( isinstance( flattened, IECoreScene.PointInstancer ) )
			self.assertTrue( flattened.arePrimitiveVariablesValid() )
			self.assertEqual( flattened.numPoints, 1 )
			self.assertEqual(
				list( flattened["prototypeRoots"].data ),
				[ "prototypes/sphere" ]
			)

			self.assertEqual(
				list( flattened.getPosition() ),
				[ imath.V3f( 1 ) ]
			)

	@GafferTest.TestRunner.CategorisedTestMethod( { "pointInstancer" } )
	def testFlattenWithoutPrototypes( self ) :

		pointInstancer = IECoreScene.PointInstancer( 1 )
		pointInstancer.setPosition( IECore.V3fVectorData( [ imath.V3f( 0 ) ] ) )

		pointInstancerNode = GafferScene.ObjectToScene()
		pointInstancerNode["object"].setValue( pointInstancer )
		pointInstancerNode["name"].setValue( "instancer" )

		with Gaffer.Context() as context :

			context["scene:path"] = GafferScene.ScenePlug.stringToPath( "/instancer" )
			pointInstancer = pointInstancerNode["out"]["object"].getValue()

			flattened = GafferScene.Private.PointInstancerAlgo.flatten(
				pointInstancer, GafferScene.Private.RendererAlgo.RenderOptions(), pointInstancerNode["out"]
			)

			self.assertTrue( isinstance( flattened, IECoreScene.PointInstancer ) )
			self.assertTrue( flattened.arePrimitiveVariablesValid() )
			self.assertEqual( flattened.numPoints, 1 )
			self.assertNotIn( "prototypeRoots", flattened )
			self.assertEqual( flattened, pointInstancer )

if __name__ == "__main__":
	unittest.main()
