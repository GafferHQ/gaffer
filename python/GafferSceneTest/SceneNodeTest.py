##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

import inspect
import unittest
import time
import threading
import imath

import IECore
import IECoreScene

import Gaffer
import GafferTest
import GafferScene
import GafferSceneTest

class SceneNodeTest( GafferSceneTest.SceneTestCase ) :

	def testRootConstraints( self ) :

		# we don't allow the root of the scene ("/") to carry objects, transforms,
		# or attributes. if we did, then there wouldn't be a sensible way of merging
		# them (particularly transforms) when a Group node has multiple inputs.
		# it's also pretty confusing to have stuff go on at the root level,
		# particularly as the root isn't well represented in the HierarchyView editor,
		# and applications like maya don't have stuff happening at the root
		# level either. we achieve this by having the SceneNode simply not
		# call the various processing functions for the root.

		node = GafferSceneTest.CompoundObjectSource()
		node["in"].setValue(
			IECore.CompoundObject( {
				"object" : IECoreScene.SpherePrimitive()
			} )
		)

		self.assertEqual( node["out"].object( "/" ), IECore.NullObject() )

		node = GafferSceneTest.CompoundObjectSource()
		node["in"].setValue(
			IECore.CompoundObject( {
				"transform" : IECore.M44fData( imath.M44f().translate( imath.V3f( 1 ) ) )
			} )
		)

		self.assertEqual( node["out"].transform( "/" ), imath.M44f() )

		node = GafferSceneTest.CompoundObjectSource()
		node["in"].setValue(
			IECore.CompoundObject( {
				"attributes" : IECore.CompoundObject()
			} )
		)

		self.assertEqual( node["out"].attributes( "/" ), IECore.CompoundObject() )

	def testTypeNamePrefixes( self ) :

		self.assertTypeNamesArePrefixed(
			GafferScene,
			namesToIgnore = {
				"PathMatcherData", "Gaffer::PathMatcherDataPlug", "Gaffer::Switch",
				"Gaffer::ContextVariables", "Gaffer::DeleteContextVariables", "Gaffer::TimeWarp",
				"Gaffer::Loop", "GafferScene::ShaderTweaks"
			}
		)

	def testDefaultNames( self ) :

		self.assertDefaultNamesAreCorrect(
			GafferScene,
			namesToIgnore = {
				"SceneSwitch", "ShaderSwitch", "FilterSwitch",
				"DeleteSceneContextVariables", "SceneContextVariables", "SceneTimeWarp",
				"SceneLoop", "LightTweaks"
			}
		)

	def testRootAttributes( self ) :

		# create node inheriting from SceneNode:
		node = GafferScene.CustomAttributes()
		node["attributes"].addChild( Gaffer.NameValuePlug( "user:foobar", True, True ) )

		# scene nodes always have passthrough behaviour for attributes at the root, so this particular one should return an empty compound object:
		context = Gaffer.Context()
		context.set( "scene:path", IECore.InternedStringVectorData([]) )
		with context:
			self.assertEqual( node["out"]["attributes"].getValue(), IECore.CompoundObject() )

		# unless the caching system is misbehaving, it should return the attribute values we asked for at other locations:
		context.set( "scene:path", IECore.InternedStringVectorData(["yup"]) )
		with context:
			self.assertEqual( node["out"]["attributes"].getValue(), IECore.CompoundObject({'user:foobar':IECore.BoolData( 1 )}) )

	def testRootObject( self ):

		# okie dokie - create a sphere node and check it's generating a sphere in the correct place:
		sphere = GafferScene.Sphere()

		context = Gaffer.Context()
		context.set("scene:path", IECore.InternedStringVectorData(["sphere"]) )
		with context:
			self.assertEqual( sphere["out"]["object"].getValue().typeId(), IECoreScene.MeshPrimitive.staticTypeId() )

		# right, now subtree it. If the cache is behaving itself, then there shouldn't be an object at the root of the
		# resulting scene, cuz that aint allowed.
		subTree = GafferScene.SubTree()
		subTree["in"].setInput( sphere["out"] )
		subTree["root"].setValue("sphere")
		context.set("scene:path", IECore.InternedStringVectorData([]) )
		with context:
			self.assertEqual( subTree["out"]["object"].getValue().typeId(), IECore.NullObject.staticTypeId() )

	def testRootTransform( self ):

		# okie dokie - create a sphere node and check it's generating a sphere in the correct place:
		sphere = GafferScene.Sphere()
		sphere["transform"]["translate"]["x"].setValue( 1.0 )
		sphere["transform"]["translate"]["y"].setValue( 2.0 )
		sphere["transform"]["translate"]["z"].setValue( 3.0 )

		context = Gaffer.Context()
		context.set("scene:path", IECore.InternedStringVectorData(["sphere"]) )
		with context:
			self.assertEqual( sphere["out"]["transform"].getValue(), imath.M44f().translate( imath.V3f( 1,2,3 ) ) )

		# right, now subtree it. If the cache is behaving itself, then the transform at the root of the
		# resulting scene should be set to identity.
		subTree = GafferScene.SubTree()
		subTree["in"].setInput( sphere["out"] )
		subTree["root"].setValue("sphere")
		context.set("scene:path", IECore.InternedStringVectorData([]) )
		with context:
			self.assertEqual( subTree["out"]["transform"].getValue(), imath.M44f() )

	def testCacheThreadSafety( self ) :

		p1 = GafferScene.Plane()
		p1["divisions"].setValue( imath.V2i( 50 ) )

		p2 = GafferScene.Plane()
		p2["divisions"].setValue( imath.V2i( 51 ) )

		g = GafferScene.Group()
		g["in"][0].setInput( p1["out"] )
		g["in"][1].setInput( p2["out"] )

		# not enough for both objects - will cause cache thrashing
		Gaffer.ValuePlug.setCacheMemoryLimit( p1["out"].object( "/plane" ).memoryUsage() )

		exceptions = []
		def traverser() :

			try :
				GafferSceneTest.traverseScene( g["out"] )
			except Exception as e :
				exceptions.append( e )

		threads = []
		for i in range( 0, 10 ) :
			thread = threading.Thread( target = traverser )
			threads.append( thread )
			thread.start()

		for thread in threads :
			thread.join()

		for e in exceptions :
			raise e

	def testNodesConstructWithDefaultValues( self ) :

		self.assertNodesConstructWithDefaultValues( GafferScene, nodesToIgnore = { GafferScene.LightTweaks } )

	def testDerivingInPython( self ) :

		# We allow deriving in Python for use as a "shell" node containing
		# an internal node network which provides the implementation. But
		# we don't allow the overriding of the compute*() and hash*() methods
		# because the performance would be abysmal.

		class SphereOrCube( GafferScene.SceneNode ) :

			Type = IECore.Enum.create( "Sphere", "Cube" )

			def __init__( self, name = "SphereOrCube" ) :

				GafferScene.SceneNode.__init__( self, name )

				self["type"] = Gaffer.IntPlug(
					defaultValue = int( self.Type.Sphere ),
					minValue = int( self.Type.Sphere ),
					maxValue = int( self.Type.Cube ),
				)

				self["__sphere"] = GafferScene.Sphere()
				self["__sphere"]["enabled"].setInput( self["enabled"] )

				self["__cube"] = GafferScene.Cube()
				self["__cube"]["enabled"].setInput( self["enabled"] )

				self["__primitiveSwitch"] = Gaffer.Switch()
				self["__primitiveSwitch"].setup( GafferScene.ScenePlug() )

				self["__primitiveSwitch"]["index"].setInput( self["type"] )
				self["__primitiveSwitch"]["in"][0].setInput( self["__sphere"]["out"] )
				self["__primitiveSwitch"]["in"][1].setInput( self["__cube"]["out"] )

				self["out"].setInput( self["__primitiveSwitch"]["out"] )

		IECore.registerRunTimeTyped( SphereOrCube )

		Gaffer.Metadata.registerNode(

			SphereOrCube,

			"description",
			"""
			A little test node
			""",

			plugs = {

				"type" : [

					"description",
					"""
					Pick yer lovely primitive here.
					""",

					"preset:Sphere", int( SphereOrCube.Type.Sphere ),
					"preset:Cube", int( SphereOrCube.Type.Cube ),

				]

			}

		)

		n = SphereOrCube()
		self.assertEqual( n["out"].childNames( "/"), IECore.InternedStringVectorData( [ "sphere" ] ) )

		n["type"].setValue( int( n.Type.Cube ) )
		self.assertEqual( n["out"].childNames( "/"), IECore.InternedStringVectorData( [ "cube" ] ) )

		n["enabled"].setValue( False )
		self.assertEqual( n["out"].childNames( "/"), IECore.InternedStringVectorData() )

		self.assertEqual(
			Gaffer.Metadata.value( n, "description" ),
			"A little test node",
		)

		self.assertEqual(
			Gaffer.Metadata.value( n["type"], "description" ),
			"Pick yer lovely primitive here.",
		)

		self.assertEqual( Gaffer.NodeAlgo.presets( n["type"] ), [ "Sphere", "Cube" ] )

	def testExists( self ) :

		cube = GafferScene.Cube()

		for path, exists in [
			( "/", True ),
			( "/cube", True ),
			( "/cube2", False ),
			( "/cube/child", False ),
			( "/notHere/notHereEither", False ),
		] :
			self.assertEqual( cube["out"].exists( path ), exists )

			with Gaffer.Context() as c :
				c["scene:path"] = GafferScene.ScenePlug.stringToPath( path )
				self.assertEqual( cube["out"].exists(), exists )

	def testExistsInternals( self ) :

		cube = GafferScene.Cube()
		with Gaffer.Context() as c :
			c["scene:path"] = IECore.InternedStringVectorData()
			# When there's only one child, the sorted child names refer
			# to exactly the same object as the regular child names.
			self.assertTrue(
				cube["out"]["__sortedChildNames"].getValue( _copy = False ).isSame(
					cube["out"]["childNames"].getValue( _copy = False )
				)
			)
			# Likewise when there's none
			c["scene:path"] = IECore.InternedStringVectorData( [ "cube" ] )
			self.assertTrue(
				cube["out"]["__sortedChildNames"].getValue( _copy = False ).isSame(
					cube["out"]["childNames"].getValue( _copy = False )
				)
			)

		cs = GafferTest.CapturingSlot( cube.plugDirtiedSignal() )
		cube["name"].setValue( "box" )
		self.assertGreaterEqual(
			{ x[0] for x in cs },
			{ cube["out"]["childNames"], cube["out"]["__sortedChildNames"], cube["out"]["exists"] }
		)

	def testChildBounds( self ) :

		cube = GafferScene.Cube()
		sphere = GafferScene.Sphere()
		group = GafferScene.Group()
		group["in"][0].setInput( cube["out"] )
		group["in"][1].setInput( sphere["out"] )

		with Gaffer.Context() as c :
			c["scene:path"] = IECore.InternedStringVectorData( [ "group" ] )
			h = group["out"]["childBounds"].hash()
			b = group["out"]["childBounds"].getValue()

		self.assertEqual( h, group["out"].childBoundsHash( "/group" ) )
		self.assertEqual( b, group["out"].childBounds( "/group" ) )

		b2 = cube["out"].bound( "/" )
		b2.extendBy( sphere["out"].bound( "/" ) )
		self.assertEqual( b, b2 )

		cube["transform"]["translate"]["x"].setValue( 10 )

		self.assertNotEqual( group["out"].childBoundsHash( "/group"), h )
		b = group["out"].childBounds( "/group" )

		b2 = cube["out"].bound( "/" )
		b2.extendBy( sphere["out"].bound( "/" ) )
		self.assertEqual( b, b2 )

	def testChildBoundsWhenNoChildren( self ) :

		plane = GafferScene.Plane()
		sphere = GafferScene.Sphere()

		self.assertEqual( plane["out"].childBounds( "/plane" ), imath.Box3f() )
		self.assertEqual( sphere["out"].childBounds( "/sphere" ), imath.Box3f() )

	def testEnabledEvaluationUsesGlobalContext( self ) :

		script = Gaffer.ScriptNode()
		script["plane"] = GafferScene.Plane()

		script["expression"] = Gaffer.Expression()
		script["expression"].setExpression( inspect.cleandoc(
			"""
			path = context.get("scene:path", None )
			assert( path is None )
			parent["plane"]["enabled"] = True
			"""
		) )

		with Gaffer.ContextMonitor( script["expression"] ) as monitor :
			self.assertSceneValid( script["plane"]["out"] )

		self.assertEqual( monitor.combinedStatistics().numUniqueValues( "scene:path" ), 0 )

	def testChildBoundsCancellation( self ) :

		# Make Sierpinski triangle type thing.

		script = Gaffer.ScriptNode()

		script["sphere"] = GafferScene.Sphere()

		script["loop"] = Gaffer.Loop()
		script["loop"].setup( script["sphere"]["out"] )
		script["loop"]["in"].setInput( script["sphere"]["out"] )
		script["loop"]["iterations"].setValue( 12 )

		script["filter"] = GafferScene.PathFilter()
		script["filter"]["paths"].setValue( IECore.StringVectorData( [ "/..." ] ) )

		script["transform1"] = GafferScene.Transform()
		script["transform1"]["in"].setInput( script["loop"]["previous"] )
		script["transform1"]["filter"].setInput( script["filter"]["out"] )
		script["transform1"]["transform"]["translate"]["x"].setValue( 1 )

		script["transform2"] = GafferScene.Transform()
		script["transform2"]["in"].setInput( script["loop"]["previous"] )
		script["transform2"]["filter"].setInput( script["filter"]["out"] )
		script["transform2"]["transform"]["translate"]["y"].setValue( 1 )

		script["transform3"] = GafferScene.Transform()
		script["transform3"]["in"].setInput( script["loop"]["previous"] )
		script["transform3"]["filter"].setInput( script["filter"]["out"] )
		script["transform3"]["transform"]["translate"]["z"].setValue( 1 )

		script["group"] = GafferScene.Group()
		script["group"]["in"][0].setInput( script["transform1"]["out"] )
		script["group"]["in"][1].setInput( script["transform2"]["out"] )
		script["group"]["in"][2].setInput( script["transform3"]["out"] )
		script["group"]["transform"]["scale"].setValue( imath.V3f( 0.666 ) )

		script["loop"]["next"].setInput( script["group"]["out"] )

		for i in range( 0, 10 ) :

			# Launch background task to compute root bounds. This will perform
			# a deep recursion through the hierarchy using parallel tasks.

			backgroundTask = Gaffer.ParallelAlgo.callOnBackgroundThread(
				script["loop"]["out"],
				lambda : script["loop"]["out"].bound( "/" )
			)

			time.sleep( 0.1 )

			# Cancel background task so that we don't perform all the work.
			# This triggered a crash bug in TaskMutex, but should return
			# cleanly if it has been fixed.
			backgroundTask.cancelAndWait()

	def setUp( self ) :

		GafferSceneTest.SceneTestCase.setUp( self )

		self.__previousCacheMemoryLimit = Gaffer.ValuePlug.getCacheMemoryLimit()

	def tearDown( self ) :

		GafferSceneTest.SceneTestCase.tearDown( self )

		Gaffer.ValuePlug.setCacheMemoryLimit( self.__previousCacheMemoryLimit )

if __name__ == "__main__":
	unittest.main()
