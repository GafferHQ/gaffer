##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
#  Copyright (c) 2013-2014, Image Engine Design Inc. All rights reserved.
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

import math

import imath

import IECore
import IECoreScene

import Gaffer
import GafferTest
import GafferDispatch
import GafferScene
import GafferSceneTest

class InstancerTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		sphere = IECoreScene.SpherePrimitive()
		instanceInput = GafferSceneTest.CompoundObjectSource()
		instanceInput["in"].setValue(
			IECore.CompoundObject( {
				"bound" : IECore.Box3fData( imath.Box3f( imath.V3f( -2 ), imath.V3f( 2 ) ) ),
				"children" : {
					"sphere" : {
						"object" : sphere,
						"bound" : IECore.Box3fData( sphere.bound() ),
						"transform" : IECore.M44fData( imath.M44f().scale( imath.V3f( 2 ) ) ),
					},
				}
			} )
		)

		seeds = IECoreScene.PointsPrimitive(
			IECore.V3fVectorData(
				[ imath.V3f( 1, 0, 0 ), imath.V3f( 1, 1, 0 ), imath.V3f( 0, 1, 0 ), imath.V3f( 0, 0, 0 ) ]
			)
		)
		seedsInput = GafferSceneTest.CompoundObjectSource()
		seedsInput["in"].setValue(
			IECore.CompoundObject( {
				"bound" : IECore.Box3fData( imath.Box3f( imath.V3f( 1, 0, 0 ), imath.V3f( 2, 1, 0 ) ) ),
				"children" : {
					"seeds" : {
						"bound" : IECore.Box3fData( seeds.bound() ),
						"transform" : IECore.M44fData( imath.M44f().translate( imath.V3f( 1, 0, 0 ) ) ),
						"object" : seeds,
					},
				},
			}, )
		)

		instancer = GafferScene.Instancer()
		instancer["in"].setInput( seedsInput["out"] )
		instancer["prototypes"].setInput( instanceInput["out"] )
		instancer["parent"].setValue( "/seeds" )
		instancer["name"].setValue( "instances" )

		self.assertEqual( instancer["out"].object( "/" ), IECore.NullObject() )
		self.assertEqual( instancer["out"].transform( "/" ), imath.M44f() )
		self.assertEqual( instancer["out"].bound( "/" ), imath.Box3f( imath.V3f( -1, -2, -2 ), imath.V3f( 4, 3, 2 ) ) )
		self.assertEqual( instancer["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "seeds" ] ) )

		self.assertEqual( instancer["out"].object( "/seeds" ), IECore.NullObject() )
		self.assertEqual( instancer["out"].transform( "/seeds" ), imath.M44f().translate( imath.V3f( 1, 0, 0 ) ) )
		self.assertEqual( instancer["out"].bound( "/seeds" ), imath.Box3f( imath.V3f( -2, -2, -2 ), imath.V3f( 3, 3, 2 ) ) )
		self.assertEqual( instancer["out"].childNames( "/seeds" ), IECore.InternedStringVectorData( [ "instances" ] ) )

		self.assertEqual( instancer["out"].object( "/seeds/instances" ), IECore.NullObject() )
		self.assertEqual( instancer["out"].transform( "/seeds/instances" ), imath.M44f() )
		self.assertEqual( instancer["out"].bound( "/seeds/instances" ), imath.Box3f( imath.V3f( -2, -2, -2 ), imath.V3f( 3, 3, 2 ) ) )
		self.assertEqual( instancer["out"].childNames( "/seeds/instances" ), IECore.InternedStringVectorData( [ "sphere" ] ) )

		self.assertEqual( instancer["out"].object( "/seeds/instances/sphere" ), IECore.NullObject() )
		self.assertEqual( instancer["out"].transform( "/seeds/instances/sphere" ), imath.M44f() )
		self.assertEqual( instancer["out"].bound( "/seeds/instances/sphere" ), imath.Box3f( imath.V3f( -2, -2, -2 ), imath.V3f( 3, 3, 2 ) ) )
		self.assertEqual( instancer["out"].childNames( "/seeds/instances/sphere" ), IECore.InternedStringVectorData( [ "0", "1", "2", "3" ] ) )

		for i in range( 0, 4 ) :

			instancePath = "/seeds/instances/sphere/%d" % i

			self.assertEqual( instancer["out"].object( instancePath ), sphere )
			self.assertEqual(
				instancer["out"].transform( instancePath ),
				imath.M44f().scale( imath.V3f( 2 ) ) * imath.M44f().translate( seeds["P"].data[i] )
			)
			self.assertEqual( instancer["out"].bound( instancePath ), sphere.bound() )
			self.assertEqual( instancer["out"].childNames( instancePath ), IECore.InternedStringVectorData() )

	def testThreading( self ) :

		sphere = IECoreScene.SpherePrimitive()
		instanceInput = GafferSceneTest.CompoundObjectSource()
		instanceInput["in"].setValue(
			IECore.CompoundObject( {
				"bound" : IECore.Box3fData( imath.Box3f( imath.V3f( -2 ), imath.V3f( 2 ) ) ),
				"children" : {
					"sphere" : {
						"object" : sphere,
						"bound" : IECore.Box3fData( sphere.bound() ),
						"transform" : IECore.M44fData( imath.M44f().scale( imath.V3f( 2 ) ) ),
					},
				}
			} )
		)

		seeds = IECoreScene.PointsPrimitive(
			IECore.V3fVectorData(
				[ imath.V3f( 1, 0, 0 ), imath.V3f( 1, 1, 0 ), imath.V3f( 0, 1, 0 ), imath.V3f( 0, 0, 0 ) ]
			)
		)
		seedsInput = GafferSceneTest.CompoundObjectSource()
		seedsInput["in"].setValue(
			IECore.CompoundObject( {
				"bound" : IECore.Box3fData( imath.Box3f( imath.V3f( 1, 0, 0 ), imath.V3f( 2, 1, 0 ) ) ),
				"children" : {
					"seeds" : {
						"bound" : IECore.Box3fData( seeds.bound() ),
						"transform" : IECore.M44fData( imath.M44f().translate( imath.V3f( 1, 0, 0 ) ) ),
						"object" : seeds,
					},
				},
			}, )
		)

		instancer = GafferScene.Instancer()
		instancer["in"].setInput( seedsInput["out"] )
		instancer["prototypes"].setInput( instanceInput["out"] )
		instancer["parent"].setValue( "/seeds" )
		instancer["name"].setValue( "instances" )

		GafferSceneTest.traverseScene( instancer["out"] )

	def testNamePlugDefaultValue( self ) :

		n = GafferScene.Instancer()
		self.assertEqual( n["name"].defaultValue(), "instances" )
		self.assertEqual( n["name"].getValue(), "instances" )

	def testAffects( self ) :

		n = GafferScene.Instancer()
		a = n.affects( n["name"] )
		self.assertGreaterEqual( { x.relativeName( n ) for x in a }, { "out.childNames", "out.bound", "out.set" } )

	def testParentBoundsWhenNoInstances( self ) :

		sphere = GafferScene.Sphere()
		sphere["type"].setValue( sphere.Type.Primitive ) # no points, so we can't instance onto it

		instancer = GafferScene.Instancer()
		instancer["in"].setInput( sphere["out"] )
		instancer["parent"].setValue( "/sphere" )
		instancer["prototypes"].setInput( sphere["out"] )

		self.assertSceneValid( instancer["out"] )
		self.assertEqual( instancer["out"].bound( "/sphere" ), sphere["out"].bound( "/sphere" ) )

	def testEmptyName( self ) :

		plane = GafferScene.Plane()

		instancer = GafferScene.Instancer()
		instancer["in"].setInput( plane["out"] )
		instancer["parent"].setValue( "/plane" )
		instancer["name"].setValue( "" )

		self.assertScenesEqual( instancer["out"], plane["out"], pathsToIgnore = ( "/plane", ) )

	def testEmptyParent( self ) :

		plane = GafferScene.Plane()
		sphere = GafferScene.Sphere()

		instancer = GafferScene.Instancer()
		instancer["in"].setInput( plane["out"] )
		instancer["prototypes"].setInput( sphere["out"] )

		instancer["parent"].setValue( "" )

		self.assertScenesEqual( instancer["out"], plane["out"] )
		self.assertSceneHashesEqual( instancer["out"], plane["out"] )

	def testSeedsAffectBound( self ) :

		plane = GafferScene.Plane()
		sphere = GafferScene.Sphere()

		instancer = GafferScene.Instancer()
		instancer["in"].setInput( plane["out"] )
		instancer["prototypes"].setInput( sphere["out"] )

		instancer["parent"].setValue( "/plane" )

		h1 = instancer["out"].boundHash( "/plane/instances" )
		b1 = instancer["out"].bound( "/plane/instances" )

		plane["dimensions"].setValue( plane["dimensions"].getValue() * 2 )

		h2 = instancer["out"].boundHash( "/plane/instances" )
		b2 = instancer["out"].bound( "/plane/instances" )

		self.assertNotEqual( h1, h2 )
		self.assertNotEqual( b1, b2 )

	def testBoundHashIsStable( self ) :

		plane = GafferScene.Plane()
		sphere = GafferScene.Sphere()

		instancer = GafferScene.Instancer()
		instancer["in"].setInput( plane["out"] )
		instancer["prototypes"].setInput( sphere["out"] )

		instancer["parent"].setValue( "/plane" )

		h = instancer["out"].boundHash( "/plane/instances" )
		for i in range( 0, 100 ) :
			self.assertEqual( instancer["out"].boundHash( "/plane/instances" ), h )

	def testObjectAffectsChildNames( self ) :

		plane = GafferScene.Plane()
		sphere = GafferScene.Sphere()

		instancer = GafferScene.Instancer()
		instancer["in"].setInput( plane["out"] )
		instancer["prototypes"].setInput( sphere["out"] )
		instancer["parent"].setValue( "/plane" )

		cs = GafferTest.CapturingSlot( instancer.plugDirtiedSignal() )
		plane["divisions"]["x"].setValue( 2 )

		dirtiedPlugs = [ s[0] for s in cs ]

		self.assertTrue( instancer["out"]["childNames"] in dirtiedPlugs )
		self.assertTrue( instancer["out"]["bound"] in dirtiedPlugs )
		self.assertTrue( instancer["out"]["transform"] in dirtiedPlugs )

	def testPythonExpressionAndGIL( self ) :

		script = Gaffer.ScriptNode()

		script["plane"] = GafferScene.Plane()
		script["plane"]["divisions"].setValue( imath.V2i( 20 ) )

		script["sphere"] = GafferScene.Sphere()

		script["expression"] = Gaffer.Expression()
		script["expression"].setExpression( "parent['sphere']['radius'] = context.getFrame()" )

		script["instancer"] = GafferScene.Instancer()
		script["instancer"]["in"].setInput( script["plane"]["out"] )
		script["instancer"]["prototypes"].setInput( script["sphere"]["out"] )
		script["instancer"]["parent"].setValue( "/plane" )

		# The Instancer spawns its own threads, so if we don't release the GIL
		# when invoking it, and an upstream node enters Python, we'll end up
		# with a deadlock. Test that isn't the case. We increment the frame
		# between each test to ensure the expression result is not cached and
		# we do truly enter python.
		with Gaffer.Context() as c :

			c.setFrame( 1 )
			script["instancer"]["out"]["globals"].getValue()

			c.setFrame( 101 )
			script["instancer"]["out"]["globals"].hash()

			c["scene:path"] = IECore.InternedStringVectorData( [ "plane" ] )

			c.setFrame( 2 )
			script["instancer"]["out"]["bound"].getValue()
			c.setFrame( 3 )
			script["instancer"]["out"]["transform"].getValue()
			c.setFrame( 4 )
			script["instancer"]["out"]["object"].getValue()
			c.setFrame( 5 )
			script["instancer"]["out"]["attributes"].getValue()
			c.setFrame( 6 )
			script["instancer"]["out"]["childNames"].getValue()
			c.setFrame( 7 )

			c.setFrame( 102 )
			script["instancer"]["out"]["bound"].hash()
			c.setFrame( 103 )
			script["instancer"]["out"]["transform"].hash()
			c.setFrame( 104 )
			script["instancer"]["out"]["object"].hash()
			c.setFrame( 105 )
			script["instancer"]["out"]["attributes"].hash()
			c.setFrame( 106 )
			script["instancer"]["out"]["childNames"].hash()
			c.setFrame( 107 )

			# The same applies for the higher level helper functions on ScenePlug

			c.setFrame( 200 )
			script["instancer"]["out"].bound( "/plane" )
			c.setFrame( 201 )
			script["instancer"]["out"].transform( "/plane" )
			c.setFrame( 202 )
			script["instancer"]["out"].fullTransform( "/plane" )
			c.setFrame( 203 )
			script["instancer"]["out"].attributes( "/plane" )
			c.setFrame( 204 )
			script["instancer"]["out"].fullAttributes( "/plane" )
			c.setFrame( 205 )
			script["instancer"]["out"].object( "/plane" )
			c.setFrame( 206 )
			script["instancer"]["out"].childNames( "/plane" )
			c.setFrame( 207 )

			c.setFrame( 300 )
			script["instancer"]["out"].boundHash( "/plane" )
			c.setFrame( 301 )
			script["instancer"]["out"].transformHash( "/plane" )
			c.setFrame( 302 )
			script["instancer"]["out"].fullTransformHash( "/plane" )
			c.setFrame( 303 )
			script["instancer"]["out"].attributesHash( "/plane" )
			c.setFrame( 304 )
			script["instancer"]["out"].fullAttributesHash( "/plane" )
			c.setFrame( 305 )
			script["instancer"]["out"].objectHash( "/plane" )
			c.setFrame( 306 )
			script["instancer"]["out"].childNamesHash( "/plane" )
			c.setFrame( 307 )

	def testDynamicPlugsAndGIL( self ) :

		script = Gaffer.ScriptNode()

		script["plane"] = GafferScene.Plane()
		script["plane"]["divisions"].setValue( imath.V2i( 20 ) )

		script["sphere"] = GafferScene.Sphere()

		script["expression"] = Gaffer.Expression()
		script["expression"].setExpression( "parent['sphere']['radius'] = context.getFrame()" )

		script["instancer"] = GafferScene.Instancer()
		script["instancer"]["in"].setInput( script["plane"]["out"] )
		script["instancer"]["prototypes"].setInput( script["sphere"]["out"] )
		script["instancer"]["parent"].setValue( "/plane" )

		script["attributes"] = GafferScene.CustomAttributes()
		script["attributes"]["in"].setInput( script["instancer"]["out"] )

		script["outputs"] = GafferScene.Outputs()
		script["outputs"]["in"].setInput( script["attributes"]["out"] )

		# Simulate an InteractiveRender or Viewer traversal of the scene
		# every time it is dirtied. If the GIL isn't released when dirtiness
		# is signalled, we'll end up with a deadlock as the traversal enters
		# python on another thread to evaluate the expression. We increment the frame
		# between each test to ensure the expression result is not cached and
		# we do truly enter python.
		traverseConnection = Gaffer.ScopedConnection( GafferSceneTest.connectTraverseSceneToPlugDirtiedSignal( script["outputs"]["out"] ) )
		with Gaffer.Context() as c :

			c.setFrame( 1 )
			script["attributes"]["attributes"].addChild( Gaffer.NameValuePlug( "test1", IECore.IntData( 10 ) ) )

			c.setFrame( 2 )
			script["attributes"]["attributes"].addChild( Gaffer.NameValuePlug( "test2", IECore.IntData( 20 ), True ) )

			c.setFrame( 3 )
			script["attributes"]["attributes"].addMembers(
				IECore.CompoundData( {
					"test3" : 30,
					"test4" : 40,
				} )
			)

			c.setFrame( 4 )
			p = script["attributes"]["attributes"][0]
			del script["attributes"]["attributes"][p.getName()]

			c.setFrame( 5 )
			script["attributes"]["attributes"].addChild( p )

			c.setFrame( 6 )
			script["attributes"]["attributes"].removeChild( p )

			c.setFrame( 7 )
			script["attributes"]["attributes"].setChild( p.getName(), p )

			c.setFrame( 8 )
			script["attributes"]["attributes"].removeChild( p )

			c.setFrame( 9 )
			script["attributes"]["attributes"][p.getName()] = p

			c.setFrame( 10 )
			script["outputs"].addOutput( "test", IECoreScene.Output( "beauty.exr", "exr", "rgba" ) )

	def testLoadReferenceAndGIL( self ) :

		script = Gaffer.ScriptNode()

		script["plane"] = GafferScene.Plane()
		script["plane"]["divisions"].setValue( imath.V2i( 20 ) )

		script["sphere"] = GafferScene.Sphere()

		script["expression"] = Gaffer.Expression()
		script["expression"].setExpression( "parent['sphere']['radius'] = 0.1 + context.getFrame()" )

		script["instancer"] = GafferScene.Instancer()
		script["instancer"]["in"].setInput( script["plane"]["out"] )
		script["instancer"]["prototypes"].setInput( script["sphere"]["out"] )
		script["instancer"]["parent"].setValue( "/plane" )

		script["box"] = Gaffer.Box()
		script["box"]["in"] = GafferScene.ScenePlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		script["box"]["out"] = GafferScene.ScenePlug( direction = Gaffer.Plug.Direction.Out, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		script["box"]["out"].setInput( script["box"]["in"] )
		script["box"].exportForReference( self.temporaryDirectory() + "/test.grf" )

		script["reference"] = Gaffer.Reference()
		script["reference"].load( self.temporaryDirectory() + "/test.grf" )
		script["reference"]["in"].setInput( script["instancer"]["out"] )

		script["attributes"] = GafferScene.CustomAttributes()
		script["attributes"]["in"].setInput( script["reference"]["out"] )

		traverseConnection = Gaffer.ScopedConnection( GafferSceneTest.connectTraverseSceneToPlugDirtiedSignal( script["attributes"]["out"] ) )
		with Gaffer.Context() as c :

			script["reference"].load( self.temporaryDirectory() + "/test.grf" )

	def testContextChangedAndGIL( self ) :

		script = Gaffer.ScriptNode()

		script["plane"] = GafferScene.Plane()
		script["plane"]["divisions"].setValue( imath.V2i( 20 ) )

		script["sphere"] = GafferScene.Sphere()

		script["expression"] = Gaffer.Expression()
		script["expression"].setExpression( "parent['sphere']['radius'] = context.get( 'minRadius', 0.1 ) + context.getFrame()" )

		script["instancer"] = GafferScene.Instancer()
		script["instancer"]["in"].setInput( script["plane"]["out"] )
		script["instancer"]["prototypes"].setInput( script["sphere"]["out"] )
		script["instancer"]["parent"].setValue( "/plane" )

		context = Gaffer.Context()
		traverseConnection = Gaffer.ScopedConnection( GafferSceneTest.connectTraverseSceneToContextChangedSignal( script["instancer"]["out"], context ) )
		with context :

			context.setFrame( 10 )
			context.setFramesPerSecond( 50 )
			context.setTime( 1 )

			context.set( "a", 1 )
			context.set( "a", 2.0 )
			context.set( "a", "a" )
			context.set( "a", imath.V2i() )
			context.set( "a", imath.V3i() )
			context.set( "a", imath.V2f() )
			context.set( "a", imath.V3f() )
			context.set( "a", imath.Color3f() )
			context.set( "a", IECore.BoolData( True ) )

			context["b"] = 1
			context["b"] = 2.0
			context["b"] = "b"
			context["b"] = imath.V2i()
			context["b"] = imath.V3i()
			context["b"] = imath.V2f()
			context["b"] = imath.V3f()
			context["b"] = imath.Color3f()
			context["b"] = IECore.BoolData( True )

			with Gaffer.BlockedConnection( traverseConnection ) :
				# Must add it with the connection disabled, otherwise
				# the addition causes a traversal, and then remove() gets
				# all its results from the cache.
				context["minRadius"] = 0.2

			context.remove( "minRadius" )

			with Gaffer.BlockedConnection( traverseConnection ) :
				context["minRadius"] = 0.3

			del context["minRadius"]

	def testDispatchAndGIL( self ) :

		script = Gaffer.ScriptNode()

		script["plane"] = GafferScene.Plane()
		script["plane"]["divisions"].setValue( imath.V2i( 20 ) )

		script["sphere"] = GafferScene.Sphere()

		script["expression"] = Gaffer.Expression()
		script["expression"].setExpression( "parent['sphere']['radius'] = context.get( 'minRadius', 0.1 ) + context.getFrame()" )

		script["instancer"] = GafferScene.Instancer()
		script["instancer"]["in"].setInput( script["plane"]["out"] )
		script["instancer"]["prototypes"].setInput( script["sphere"]["out"] )
		script["instancer"]["parent"].setValue( "/plane" )

		script["pythonCommand"] = GafferDispatch.PythonCommand()
		script["pythonCommand"]["command"].setValue( "pass" )

		traverseConnection = Gaffer.ScopedConnection( GafferSceneTest.connectTraverseSceneToPreDispatchSignal( script["instancer"]["out"] ) )

		dispatcher = GafferDispatch.LocalDispatcher()
		dispatcher["jobsDirectory"].setValue( self.temporaryDirectory() )

		with Gaffer.Context() as c :
			for i in range( 1, 10 ) :
				c.setFrame( i )
				dispatcher.dispatch( [ script["pythonCommand"] ] )

	def testTransform( self ) :

		point = IECoreScene.PointsPrimitive( IECore.V3fVectorData( [ imath.V3f( 4, 0, 0 ) ] ) )
		point["orientation"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.QuatfVectorData( [ imath.Quatf().setAxisAngle( imath.V3f( 0, 1, 0 ), math.pi / 2.0 ) ] )
		)
		point["scale"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.V3fVectorData( [ imath.V3f( 2, 3, 4 ) ] )
		)
		point["uniformScale"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.FloatVectorData( [ 10 ] )
		)

		objectToScene = GafferScene.ObjectToScene()
		objectToScene["object"].setValue( point )

		sphere = GafferScene.Sphere()

		instancer = GafferScene.Instancer()
		instancer["in"].setInput( objectToScene["out"] )
		instancer["prototypes"].setInput( sphere["out"] )
		instancer["parent"].setValue( "/object" )

		self.assertEqual( instancer["out"].transform( "/object/instances/sphere/0" ), imath.M44f().translate( imath.V3f( 4, 0, 0 ) ) )

		instancer["orientation"].setValue( "orientation" )
		self.assertTrue(
			imath.V3f( 4, 0, -1 ).equalWithAbsError(
				imath.V3f( 1, 0, 0 ) * instancer["out"].transform( "/object/instances/sphere/0" ),
				0.00001
			)
		)

		instancer["scale"].setValue( "scale" )
		self.assertTrue(
			imath.V3f( 4, 0, -2 ).equalWithAbsError(
				imath.V3f( 1, 0, 0 ) * instancer["out"].transform( "/object/instances/sphere/0" ),
				0.00001
			)
		)

		instancer["scale"].setValue( "uniformScale" )
		self.assertTrue(
			imath.V3f( 4, 0, -10 ).equalWithAbsError(
				imath.V3f( 1, 0, 0 ) * instancer["out"].transform( "/object/instances/sphere/0" ),
				0.00001
			)
		)

	def testIndices( self ) :

		points = IECoreScene.PointsPrimitive( IECore.V3fVectorData( [ imath.V3f( x, 0, 0 ) for x in range( 0, 4 ) ] ) )
		points["index"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.IntVectorData( [ 0, 1, 1, 0 ] ),
		)

		objectToScene = GafferScene.ObjectToScene()
		objectToScene["object"].setValue( points )

		sphere = GafferScene.Sphere()
		cube = GafferScene.Cube()
		instances = GafferScene.Parent()
		instances["in"].setInput( sphere["out"] )
		instances["children"][0].setInput( cube["out"] )
		instances["parent"].setValue( "/" )

		instancer = GafferScene.Instancer()
		instancer["in"].setInput( objectToScene["out"] )
		instancer["prototypes"].setInput( instances["out"] )
		instancer["parent"].setValue( "/object" )
		instancer["prototypeIndex"].setValue( "index" )

		self.assertEqual( instancer["out"].childNames( "/object/instances" ), IECore.InternedStringVectorData( [ "sphere", "cube" ] ) )
		self.assertEqual( instancer["out"].childNames( "/object/instances/sphere" ), IECore.InternedStringVectorData( [ "0", "3" ] ) )
		self.assertEqual( instancer["out"].childNames( "/object/instances/cube" ), IECore.InternedStringVectorData( [ "1", "2" ] ) )
		self.assertEqual( instancer["out"].childNames( "/object/instances/sphere/0" ), IECore.InternedStringVectorData() )
		self.assertEqual( instancer["out"].childNames( "/object/instances/sphere/3" ), IECore.InternedStringVectorData() )
		self.assertEqual( instancer["out"].childNames( "/object/instances/cube/1" ), IECore.InternedStringVectorData() )
		self.assertEqual( instancer["out"].childNames( "/object/instances/cube/2" ), IECore.InternedStringVectorData() )

		self.assertEqual( instancer["out"].object( "/object/instances" ), IECore.NullObject.defaultNullObject() )
		self.assertEqual( instancer["out"].object( "/object/instances/sphere" ), IECore.NullObject.defaultNullObject() )
		self.assertEqual( instancer["out"].object( "/object/instances/cube" ), IECore.NullObject.defaultNullObject() )
		self.assertEqual( instancer["out"].object( "/object/instances/sphere/0" ), sphere["out"].object( "/sphere" ) )
		self.assertEqual( instancer["out"].object( "/object/instances/sphere/3" ), sphere["out"].object( "/sphere" ) )
		self.assertEqual( instancer["out"].object( "/object/instances/cube/1" ), cube["out"].object( "/cube" ) )
		self.assertEqual( instancer["out"].object( "/object/instances/cube/2" ), cube["out"].object( "/cube" ) )

		self.assertSceneValid( instancer["out"] )

	def testSets( self ) :

		points = IECoreScene.PointsPrimitive( IECore.V3fVectorData( [ imath.V3f( x, 0, 0 ) for x in range( 0, 4 ) ] ) )
		points["index"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.IntVectorData( [ 0, 1, 1, 0 ] ),
		)

		objectToScene = GafferScene.ObjectToScene()
		objectToScene["object"].setValue( points )

		sphere = GafferScene.Sphere()
		sphere["sets"].setValue( "sphereSet" )

		cube = GafferScene.Cube()
		cube["sets"].setValue( "cubeSet" )
		cubeGroup = GafferScene.Group()
		cubeGroup["name"].setValue( "cubeGroup" )
		cubeGroup["in"][0].setInput( cube["out"] )

		instances = GafferScene.Parent()
		instances["in"].setInput( sphere["out"] )
		instances["children"][0].setInput( cubeGroup["out"] )
		instances["parent"].setValue( "/" )

		instancer = GafferScene.Instancer()
		instancer["in"].setInput( objectToScene["out"] )
		instancer["prototypes"].setInput( instances["out"] )
		instancer["parent"].setValue( "/object" )
		instancer["prototypeIndex"].setValue( "index" )

		self.assertEqual(
			instancer["out"]["setNames"].getValue(),
			IECore.InternedStringVectorData( [ "sphereSet", "cubeSet" ] )
		)

		self.assertEqual(
			set( instancer["out"].set( "sphereSet" ).value.paths() ),
			{
				"/object/instances/sphere/0",
				"/object/instances/sphere/3",
			}
		)

		self.assertEqual(
			set( instancer["out"].set( "cubeSet" ).value.paths() ),
			{
				"/object/instances/cubeGroup/1/cube",
				"/object/instances/cubeGroup/2/cube",
			}
		)

	def testIds( self ) :

		points = IECoreScene.PointsPrimitive( IECore.V3fVectorData( [ imath.V3f( x, 0, 0 ) for x in range( 0, 4 ) ] ) )
		points["id"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.IntVectorData( [ 10, 100, 111, 5 ] ),
		)
		points["index"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.IntVectorData( [ 0, 1, 0, 1 ] ),
		)

		objectToScene = GafferScene.ObjectToScene()
		objectToScene["object"].setValue( points )

		sphere = GafferScene.Sphere()
		cube = GafferScene.Cube()
		instances = GafferScene.Parent()
		instances["in"].setInput( sphere["out"] )
		instances["children"][0].setInput( cube["out"] )
		instances["parent"].setValue( "/" )

		instancer = GafferScene.Instancer()
		instancer["in"].setInput( objectToScene["out"] )
		instancer["prototypes"].setInput( instances["out"] )
		instancer["parent"].setValue( "/object" )
		instancer["prototypeIndex"].setValue( "index" )
		instancer["id"].setValue( "id" )

		self.assertEqual( instancer["out"].childNames( "/object/instances" ), IECore.InternedStringVectorData( [ "sphere", "cube" ] ) )
		self.assertEqual( instancer["out"].childNames( "/object/instances/sphere" ), IECore.InternedStringVectorData( [ "10", "111" ] ) )
		self.assertEqual( instancer["out"].childNames( "/object/instances/cube" ), IECore.InternedStringVectorData( [ "5", "100" ] ) )
		self.assertEqual( instancer["out"].childNames( "/object/instances/sphere/10" ), IECore.InternedStringVectorData() )
		self.assertEqual( instancer["out"].childNames( "/object/instances/sphere/111" ), IECore.InternedStringVectorData() )
		self.assertEqual( instancer["out"].childNames( "/object/instances/cube/100" ), IECore.InternedStringVectorData() )
		self.assertEqual( instancer["out"].childNames( "/object/instances/cube/5" ), IECore.InternedStringVectorData() )

		self.assertEqual( instancer["out"].object( "/object/instances" ), IECore.NullObject.defaultNullObject() )
		self.assertEqual( instancer["out"].object( "/object/instances/sphere" ), IECore.NullObject.defaultNullObject() )
		self.assertEqual( instancer["out"].object( "/object/instances/cube" ), IECore.NullObject.defaultNullObject() )
		self.assertEqual( instancer["out"].object( "/object/instances/sphere/10" ), sphere["out"].object( "/sphere" ) )
		self.assertEqual( instancer["out"].object( "/object/instances/sphere/111" ), sphere["out"].object( "/sphere" ) )
		self.assertEqual( instancer["out"].object( "/object/instances/cube/100" ), cube["out"].object( "/cube" ) )
		self.assertEqual( instancer["out"].object( "/object/instances/cube/5" ), cube["out"].object( "/cube" ) )

		self.assertEqual( instancer["out"].transform( "/object/instances" ), imath.M44f() )
		self.assertEqual( instancer["out"].transform( "/object/instances/sphere" ), imath.M44f() )
		self.assertEqual( instancer["out"].transform( "/object/instances/cube" ), imath.M44f() )
		self.assertEqual( instancer["out"].transform( "/object/instances/sphere/10" ), imath.M44f() )
		self.assertEqual( instancer["out"].transform( "/object/instances/sphere/111" ), imath.M44f().translate( imath.V3f( 2, 0, 0 ) ) )
		self.assertEqual( instancer["out"].transform( "/object/instances/cube/100" ), imath.M44f().translate( imath.V3f( 1, 0, 0 ) ) )
		self.assertEqual( instancer["out"].transform( "/object/instances/cube/5" ), imath.M44f().translate( imath.V3f( 3, 0, 0 ) ) )

		self.assertSceneValid( instancer["out"] )

	def testNegativeIdsAndIndices( self ) :

		points = IECoreScene.PointsPrimitive( IECore.V3fVectorData( [ imath.V3f( x, 0, 0 ) for x in range( 0, 2 ) ] ) )
		points["id"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.IntVectorData( [ -10, -5 ] ),
		)
		points["index"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.IntVectorData( [ -1, -2 ] ),
		)

		objectToScene = GafferScene.ObjectToScene()
		objectToScene["object"].setValue( points )

		sphere = GafferScene.Sphere()
		cube = GafferScene.Cube()
		instances = GafferScene.Parent()
		instances["in"].setInput( sphere["out"] )
		instances["children"][0].setInput( cube["out"] )
		instances["parent"].setValue( "/" )

		instancer = GafferScene.Instancer()
		instancer["in"].setInput( objectToScene["out"] )
		instancer["prototypes"].setInput( instances["out"] )
		instancer["parent"].setValue( "/object" )
		instancer["prototypeIndex"].setValue( "index" )
		instancer["id"].setValue( "id" )

		self.assertEqual( instancer["out"].childNames( "/object/instances" ), IECore.InternedStringVectorData( [ "sphere", "cube" ] ) )
		self.assertEqual( instancer["out"].childNames( "/object/instances/sphere" ), IECore.InternedStringVectorData( [ "-5" ] ) )
		self.assertEqual( instancer["out"].childNames( "/object/instances/cube" ), IECore.InternedStringVectorData( [ "-10" ] ) )
		self.assertEqual( instancer["out"].childNames( "/object/instances/sphere/-5" ), IECore.InternedStringVectorData() )
		self.assertEqual( instancer["out"].childNames( "/object/instances/cube/-10" ), IECore.InternedStringVectorData() )

		self.assertEqual( instancer["out"].object( "/object/instances" ), IECore.NullObject.defaultNullObject() )
		self.assertEqual( instancer["out"].object( "/object/instances/sphere" ), IECore.NullObject.defaultNullObject() )
		self.assertEqual( instancer["out"].object( "/object/instances/cube" ), IECore.NullObject.defaultNullObject() )
		self.assertEqual( instancer["out"].object( "/object/instances/sphere/-5" ), sphere["out"].object( "/sphere" ) )
		self.assertEqual( instancer["out"].object( "/object/instances/cube/-10" ), cube["out"].object( "/cube" ) )

		self.assertSceneValid( instancer["out"] )

	def testDuplicateIds( self ) :

		points = IECoreScene.PointsPrimitive( IECore.V3fVectorData( [ imath.V3f( x, 0, 0 ) for x in range( 6 ) ] ) )
		points["id"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.IntVectorData( [ 0, 0, 2, 2, 4, 4 ] ),
		)

		objectToScene = GafferScene.ObjectToScene()
		objectToScene["object"].setValue( points )

		sphere = GafferScene.Sphere()

		instancer = GafferScene.Instancer()
		instancer["in"].setInput( objectToScene["out"] )
		instancer["prototypes"].setInput( sphere["out"] )
		instancer["parent"].setValue( "/object" )
		instancer["id"].setValue( "id" )

		self.assertSceneValid( instancer["out"] )

		self.assertEqual( instancer["out"].childNames( "/object/instances/sphere" ), IECore.InternedStringVectorData( [ "0", "2", "4" ] ) )

		self.assertEqual( instancer["out"].transform( "/object/instances/sphere/0" ), imath.M44f().translate( imath.V3f( 0, 0, 0 ) ) )
		self.assertEqual( instancer["out"].transform( "/object/instances/sphere/2" ), imath.M44f().translate( imath.V3f( 2, 0, 0 ) ) )
		self.assertEqual( instancer["out"].transform( "/object/instances/sphere/4" ), imath.M44f().translate( imath.V3f( 4, 0, 0 ) ) )


	def testAttributes( self ) :

		points = IECoreScene.PointsPrimitive( IECore.V3fVectorData( [ imath.V3f( x, 0, 0 ) for x in range( 0, 2 ) ] ) )
		points["testFloat"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.FloatVectorData( [ 0, 1 ] ),
		)
		points["testColor"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.Color3fVectorData( [ imath.Color3f( 1, 0, 0 ), imath.Color3f( 0, 1, 0 ) ] ),
		)
		points["testPoint"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.V3fVectorData(
				[ imath.V3f( 0, 0, 0 ), imath.V3f( 1, 1, 1 ) ],
				IECore.GeometricData.Interpretation.Point
			),
		)

		objectToScene = GafferScene.ObjectToScene()
		objectToScene["object"].setValue( points )

		sphere = GafferScene.Sphere()

		instancer = GafferScene.Instancer()
		instancer["in"].setInput( objectToScene["out"] )
		instancer["prototypes"].setInput( sphere["out"] )
		instancer["parent"].setValue( "/object" )

		self.assertEqual(
			instancer["out"].attributes( "/object/instances" ),
			IECore.CompoundObject()
		)

		self.assertEqual(
			instancer["out"].attributes( "/object/instances/sphere" ),
			IECore.CompoundObject()
		)

		self.assertEqual(
			instancer["out"].attributes( "/object/instances/sphere/0" ),
			IECore.CompoundObject()
		)

		instancer["attributes"].setValue( "testFloat testColor testPoint" )

		self.assertEqual(
			instancer["out"].attributes( "/object/instances/sphere/0" ),
			IECore.CompoundObject( {
				"testFloat" : IECore.FloatData( 0.0 ),
				"testColor" : IECore.Color3fData( imath.Color3f( 1, 0, 0 ) ),
				"testPoint" : IECore.V3fData(
					imath.V3f( 0 ),
					IECore.GeometricData.Interpretation.Point
				)
			} )
		)

		self.assertEqual(
			instancer["out"].attributes( "/object/instances/sphere/1" ),
			IECore.CompoundObject( {
				"testFloat" : IECore.FloatData( 1.0 ),
				"testColor" : IECore.Color3fData( imath.Color3f( 0, 1, 0 ) ),
				"testPoint" : IECore.V3fData(
					imath.V3f( 1 ),
					IECore.GeometricData.Interpretation.Point
				)
			} )
		)

		instancer["attributePrefix"].setValue( "user:" )

		self.assertEqual(
			instancer["out"].attributes( "/object/instances/sphere/0" ),
			IECore.CompoundObject( {
				"user:testFloat" : IECore.FloatData( 0.0 ),
				"user:testColor" : IECore.Color3fData( imath.Color3f( 1, 0, 0 ) ),
				"user:testPoint" : IECore.V3fData(
					imath.V3f( 0 ),
					IECore.GeometricData.Interpretation.Point
				)
			} )
		)

		self.assertEqual(
			instancer["out"].attributes( "/object/instances/sphere/1" ),
			IECore.CompoundObject( {
				"user:testFloat" : IECore.FloatData( 1.0 ),
				"user:testColor" : IECore.Color3fData( imath.Color3f( 0, 1, 0 ) ),
				"user:testPoint" : IECore.V3fData(
					imath.V3f( 1 ),
					IECore.GeometricData.Interpretation.Point
				)
			} )
		)

		instancer["attributePrefix"].setValue( "foo:" )

		self.assertEqual(
			instancer["out"].attributes( "/object/instances/sphere/0" ),
			IECore.CompoundObject( {
				"foo:testFloat" : IECore.FloatData( 0.0 ),
				"foo:testColor" : IECore.Color3fData( imath.Color3f( 1, 0, 0 ) ),
				"foo:testPoint" : IECore.V3fData(
					imath.V3f( 0 ),
					IECore.GeometricData.Interpretation.Point
				)
			} )
		)

		self.assertEqual(
			instancer["out"].attributes( "/object/instances/sphere/1" ),
			IECore.CompoundObject( {
				"foo:testFloat" : IECore.FloatData( 1.0 ),
				"foo:testColor" : IECore.Color3fData( imath.Color3f( 0, 1, 0 ) ),
				"foo:testPoint" : IECore.V3fData(
					imath.V3f( 1 ),
					IECore.GeometricData.Interpretation.Point
				)
			} )
		)

	def testEmptyAttributesHaveConstantHash( self ) :

		points = IECoreScene.PointsPrimitive( IECore.V3fVectorData( [ imath.V3f( x, 0, 0 ) for x in range( 0, 2 ) ] ) )
		objectToScene = GafferScene.ObjectToScene()
		objectToScene["object"].setValue( points )

		sphere = GafferScene.Sphere()

		instancer = GafferScene.Instancer()
		instancer["in"].setInput( objectToScene["out"] )
		instancer["prototypes"].setInput( sphere["out"] )
		instancer["parent"].setValue( "/object" )

		self.assertEqual(
			instancer["out"].attributesHash( "/object/instances/sphere/0" ),
			instancer["out"].attributesHash( "/object/instances/sphere/1" ),
		)

		self.assertEqual(
			instancer["out"].attributes( "/object/instances/sphere/0" ),
			instancer["out"].attributes( "/object/instances/sphere/1" ),
		)

	def testEditAttributes( self ) :

		points = IECoreScene.PointsPrimitive( IECore.V3fVectorData( [ imath.V3f( x, 0, 0 ) for x in range( 0, 2 ) ] ) )
		points["testFloat"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.FloatVectorData( [ 0, 1 ] ),
		)

		objectToScene = GafferScene.ObjectToScene()
		objectToScene["object"].setValue( points )

		sphere = GafferScene.Sphere()

		instancer = GafferScene.Instancer()
		instancer["in"].setInput( objectToScene["out"] )
		instancer["prototypes"].setInput( sphere["out"] )
		instancer["parent"].setValue( "/object" )

		instancer["attributes"].setValue( "test*" )

		self.assertEqual(
			instancer["out"].attributes( "/object/instances/sphere/0" ),
			IECore.CompoundObject( {
				"testFloat" : IECore.FloatData( 0.0 ),
			} )
		)

		self.assertEqual(
			instancer["out"].attributes( "/object/instances/sphere/1" ),
			IECore.CompoundObject( {
				"testFloat" : IECore.FloatData( 1.0 ),
			} )
		)

		points["testFloat"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.FloatVectorData( [ 1, 2 ] ),
		)
		objectToScene["object"].setValue( points )

		self.assertEqual(
			instancer["out"].attributes( "/object/instances/sphere/0" ),
			IECore.CompoundObject( {
				"testFloat" : IECore.FloatData( 1.0 ),
			} )
		)

		self.assertEqual(
			instancer["out"].attributes( "/object/instances/sphere/1" ),
			IECore.CompoundObject( {
				"testFloat" : IECore.FloatData( 2.0 ),
			} )
		)

	def testUnconnectedInstanceInput( self ) :

		plane = GafferScene.Plane()
		plane["sets"].setValue( "A" )
		plane["divisions"].setValue( imath.V2i( 1, 500 ) )

		instancer = GafferScene.Instancer()
		instancer["in"].setInput( plane["out"] )
		instancer["parent"].setValue( "/plane" )

		self.assertEqual( instancer["out"].set( "A" ).value.paths(), [ "/plane" ] )

	def testDirtyPropagation( self ) :

		plane = GafferScene.Plane()
		instancer = GafferScene.Instancer()
		instancer["in"].setInput( plane["out"] )
		instancer["prototypes"].setInput( plane["out"] )

		cs = GafferTest.CapturingSlot( instancer.plugDirtiedSignal() )
		instancer["parent"].setValue( "plane" )
		self.assertIn( instancer["out"]["childNames"], { x[0] for x in cs } )

		del cs[:]
		filter = GafferScene.PathFilter()
		instancer["filter"].setInput( filter["out"] )
		self.assertIn( instancer["out"]["childNames"], { x[0] for x in cs } )

if __name__ == "__main__":
	unittest.main()
