##########################################################################
#
#  Copyright (c) 2019, Cinesite VFX Ltd. All rights reserved.
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
import unittest
import six

import imath

import IECore

import Gaffer
import GafferTest
import GafferScene
import GafferSceneTest

class EditScopeAlgoTest( GafferSceneTest.SceneTestCase ) :

	def testPruning( self ) :

		plane = GafferScene.Plane()
		cube = GafferScene.Cube()
		group = GafferScene.Group()

		group["in"][0].setInput( plane["out"] )
		group["in"][1].setInput( cube["out"] )

		scope = Gaffer.EditScope()
		scope.setup( group["out"] )
		scope["in"].setInput( group["out"] )

		self.assertEqual( len( list( GafferScene.SceneProcessor.Range( scope ) ) ), 0 )
		self.assertFalse( GafferScene.EditScopeAlgo.getPruned( scope, "/group/plane" ) )
		self.assertFalse( GafferScene.EditScopeAlgo.getPruned( scope, "/group/cube" ) )
		self.assertEqual( len( list( GafferScene.SceneProcessor.Range( scope ) ) ), 0 )
		self.assertTrue( GafferScene.SceneAlgo.exists( scope["out"], "/group/plane" ) )
		self.assertTrue( GafferScene.SceneAlgo.exists( scope["out"], "/group/cube" ) )

		GafferScene.EditScopeAlgo.setPruned( scope, "/group/plane", True )
		self.assertTrue( GafferScene.EditScopeAlgo.getPruned( scope, "/group/plane" ) )
		self.assertFalse( GafferScene.EditScopeAlgo.getPruned( scope, "/group/cube" ) )
		self.assertEqual( len( list( GafferScene.SceneProcessor.Range( scope ) ) ), 1 )
		self.assertEqual( scope["PruningEdits"]["paths"].getValue(), IECore.StringVectorData( [ "/group/plane" ] ) )
		self.assertFalse( GafferScene.SceneAlgo.exists( scope["out"], "/group/plane" ) )
		self.assertTrue( GafferScene.SceneAlgo.exists( scope["out"], "/group/cube" ) )

		GafferScene.EditScopeAlgo.setPruned( scope, IECore.PathMatcher( [ "/group/plane", "/group/cube" ] ), True )
		self.assertTrue( GafferScene.EditScopeAlgo.getPruned( scope, "/group/plane" ) )
		self.assertTrue( GafferScene.EditScopeAlgo.getPruned( scope, "/group/cube" ) )
		self.assertEqual( len( list( GafferScene.SceneProcessor.Range( scope ) ) ), 1 )
		self.assertEqual( scope["PruningEdits"]["paths"].getValue(), IECore.StringVectorData( [ "/group/cube", "/group/plane" ] ) )
		self.assertFalse( GafferScene.SceneAlgo.exists( scope["out"], "/group/plane" ) )
		self.assertFalse( GafferScene.SceneAlgo.exists( scope["out"], "/group/cube" ) )

		GafferScene.EditScopeAlgo.setPruned( scope, IECore.PathMatcher( [ "/group/plane", "/group/cube" ] ), False )
		self.assertFalse( GafferScene.EditScopeAlgo.getPruned( scope, "/group/plane" ) )
		self.assertFalse( GafferScene.EditScopeAlgo.getPruned( scope, "/group/cube" ) )
		self.assertEqual( len( list( GafferScene.SceneProcessor.Range( scope ) ) ), 1 )
		self.assertEqual( scope["PruningEdits"]["paths"].getValue(), IECore.StringVectorData() )
		self.assertTrue( GafferScene.SceneAlgo.exists( scope["out"], "/group/plane" ) )
		self.assertTrue( GafferScene.SceneAlgo.exists( scope["out"], "/group/cube" ) )

	def testPruningSerialisation( self ) :

		s = Gaffer.ScriptNode()

		s["plane"] = GafferScene.Plane()

		s["editScope"] = Gaffer.EditScope()
		s["editScope"].setup( s["plane"]["out"] )

		GafferScene.EditScopeAlgo.setPruned( s["editScope"], "/plane", True )
		self.assertTrue( GafferScene.EditScopeAlgo.getPruned( s["editScope"], "/plane" ), True )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertTrue( GafferScene.EditScopeAlgo.getPruned( s2["editScope"], "/plane" ), True )

	def testTransform( self ) :

		plane = GafferScene.Plane()
		plane["transform"]["translate"].setValue( imath.V3f( 1, 0, 0 ) )

		editScope = Gaffer.EditScope()
		editScope.setup( plane["out"] )
		editScope["in"].setInput( plane["out"] )

		self.assertFalse( GafferScene.EditScopeAlgo.hasTransformEdit( editScope, "/plane" ) )
		self.assertIsNone( GafferScene.EditScopeAlgo.acquireTransformEdit( editScope, "/plane", createIfNecessary = False ) )
		self.assertEqual( len( list( GafferScene.SceneProcessor.Range( editScope ) ) ), 0 )
		self.assertEqual( editScope["out"].transform( "/plane" ), plane["transform"].matrix() )

		edit = GafferScene.EditScopeAlgo.acquireTransformEdit( editScope, "/plane" )
		self.assertIsInstance( edit, GafferScene.EditScopeAlgo.TransformEdit )
		self.assertTrue( GafferScene.EditScopeAlgo.hasTransformEdit( editScope, "/plane" ) )
		self.assertIsNotNone( GafferScene.EditScopeAlgo.acquireTransformEdit( editScope, "/plane", createIfNecessary = False ) )
		self.assertEqual( editScope["out"].transform( "/plane" ), imath.M44f() )
		edit.translate.setValue( imath.V3f( 2, 3, 4 ) )
		self.assertEqual( editScope["out"].transform( "/plane" ), imath.M44f().translate( imath.V3f( 2, 3, 4 ) ) )

		GafferScene.EditScopeAlgo.removeTransformEdit( editScope, "/plane" )
		self.assertFalse( GafferScene.EditScopeAlgo.hasTransformEdit( editScope, "/plane" ) )
		self.assertIsNone( GafferScene.EditScopeAlgo.acquireTransformEdit( editScope, "/plane", createIfNecessary = False ) )
		self.assertEqual( editScope["out"].transform( "/plane" ), plane["transform"].matrix() )

	def testTransformProcessorNotCreatedPrematurely( self ) :

		plane = GafferScene.Plane()
		plane["transform"]["translate"].setValue( imath.V3f( 1, 0, 0 ) )

		editScope = Gaffer.EditScope()
		editScope.setup( plane["out"] )
		editScope["in"].setInput( plane["out"] )

		self.assertFalse( "TransformEdits" in editScope )
		GafferScene.EditScopeAlgo.acquireTransformEdit( editScope, "/plane", createIfNecessary = False )
		self.assertFalse( "TransformEdits" in editScope )
		GafferScene.EditScopeAlgo.acquireTransformEdit( editScope, "/plane" )
		self.assertTrue( "TransformEdits" in editScope )

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testTransformPerformance( self ) :

		plane = GafferScene.Plane()
		plane["divisions"].setValue( imath.V2i( 100, 10 ) )

		cube = GafferScene.Cube()

		planeFilter = GafferScene.PathFilter()
		planeFilter["paths"].setValue( IECore.StringVectorData( ["/plane"] ) )

		instancer = GafferScene.Instancer()
		instancer["in"].setInput( plane["out"] )
		instancer["prototypes"].setInput( cube["out"] )
		instancer["filter"].setInput( planeFilter["out"] )

		editScope = Gaffer.EditScope()
		editScope.setup( instancer["out"] )
		editScope["in"].setInput( instancer["out"] )

		for name in instancer["out"].childNames( "/plane/instances/cube" ) :
			GafferScene.EditScopeAlgo.acquireTransformEdit(
				editScope, "/plane/instances/cube/{}".format( name )
			)

	def testTransformEditMethods( self ) :

		plane = GafferScene.Plane()
		sphere = GafferScene.Sphere()

		planeEdit = GafferScene.EditScopeAlgo.TransformEdit(
			plane["transform"]["translate"],
			plane["transform"]["rotate"],
			plane["transform"]["scale"],
			plane["transform"]["pivot"]
		)
		sphereEdit = GafferScene.EditScopeAlgo.TransformEdit(
			sphere["transform"]["translate"],
			sphere["transform"]["rotate"],
			sphere["transform"]["scale"],
			sphere["transform"]["pivot"]
		)

		self.assertEqual( planeEdit, planeEdit )
		self.assertFalse( planeEdit != planeEdit )
		self.assertEqual( sphereEdit, sphereEdit )
		self.assertFalse( sphereEdit != sphereEdit )
		self.assertNotEqual( sphereEdit, planeEdit )
		self.assertTrue( sphereEdit != planeEdit )

	def testParameterEdits( self ) :

		light = GafferSceneTest.TestLight()

		editScope = Gaffer.EditScope()
		editScope.setup( light["out"] )
		editScope["in"].setInput( light["out"] )
		self.assertEqual(
			editScope["out"].attributes( "/light" )["light"].outputShader().parameters["intensity"].value,
			imath.Color3f( 0 )
		)

		self.assertFalse( GafferScene.EditScopeAlgo.hasParameterEdit( editScope, "/light", "light", ( "", "intensity" ) ) )
		self.assertIsNone( GafferScene.EditScopeAlgo.acquireParameterEdit( editScope, "/light", "light", ( "", "intensity" ), createIfNecessary = False ) )

		edit = GafferScene.EditScopeAlgo.acquireParameterEdit( editScope, "/light", "light", ( "", "intensity" ) )
		self.assertIsInstance( edit, GafferScene.TweakPlug )
		self.assertIsInstance( edit["value"], Gaffer.Color3fPlug )
		self.assertEqual( edit["mode"].getValue(), GafferScene.TweakPlug.Mode.Replace )
		self.assertEqual( edit["value"].getValue(), imath.Color3f( 0 ) )
		self.assertEqual( edit["enabled"].getValue(), False )

		edit["enabled"].setValue( True )
		edit["value"].setValue( imath.Color3f( 1 ) )
		self.assertEqual(
			editScope["out"].attributes( "/light" )["light"].outputShader().parameters["intensity"].value,
			imath.Color3f( 1 )
		)

		self.assertEqual(
			GafferScene.EditScopeAlgo.acquireParameterEdit( editScope, "/light", "light", ( "", "intensity" ) ),
			edit
		)

		light["parameters"]["intensity"].setValue( imath.Color3f( 0.5 ) )
		edit["enabled"].setValue( False )
		self.assertEqual(
			editScope["out"].attributes( "/light" )["light"].outputShader().parameters["intensity"].value,
			imath.Color3f( 0.5 )
		)

		self.assertIsNone( GafferScene.EditScopeAlgo.acquireParameterEdit( editScope, "/light", "light", ( "", "__areaLight" ), createIfNecessary = False ) )

	def testParameterEditsDontAffectOtherObjects( self ) :

		# Make two lights and an EditScope

		light1 = GafferSceneTest.TestLight()
		light1["name"].setValue( "light1" )
		light1["parameters"]["intensity"].setValue( imath.Color3f( 1, 0, 0 ) )

		light2 = GafferSceneTest.TestLight()
		light2["name"].setValue( "light2" )
		light2["parameters"]["intensity"].setValue( imath.Color3f( 0, 1, 0 ) )

		group = GafferScene.Group()
		group["in"][0].setInput( light1["out"] )
		group["in"][1].setInput( light2["out"] )

		editScope = Gaffer.EditScope()
		editScope.setup( group["out"] )
		editScope["in"].setInput( group["out"] )
		self.assertEqual(
			editScope["out"].attributes( "/group/light1" )["light"].outputShader().parameters["intensity"].value,
			imath.Color3f( 1, 0, 0 )
		)
		self.assertEqual(
			editScope["out"].attributes( "/group/light2" )["light"].outputShader().parameters["intensity"].value,
			imath.Color3f( 0, 1, 0 )
		)

		# Edit light1

		intensityEdit1 = GafferScene.EditScopeAlgo.acquireParameterEdit( editScope, "/group/light1", "light", ( "", "intensity" ) )
		intensityEdit1["enabled"].setValue( True )
		intensityEdit1["value"].setValue( imath.Color3f( 2 ) )

		self.assertEqual(
			editScope["out"].attributes( "/group/light1" )["light"].outputShader().parameters["intensity"].value,
			imath.Color3f( 2 )
		)

		# This shouldn't create an edit for light2

		self.assertIsNone(
			GafferScene.EditScopeAlgo.acquireParameterEdit(
				editScope, "/group/light2", "light", ( "", "intensity" ),
				createIfNecessary = False
			)
		)
		self.assertEqual(
			editScope["in"].attributes( "/group/light2" ),
			editScope["out"].attributes( "/group/light2" ),
		)

		# But if we edit a _different_ parameter on light2, then both lights are in the
		# spreadsheet, and we must therefore expect them both to have edits for both
		# parameters. We just need to make sure that the extra edits are disabled.

		areaEdit2 = GafferScene.EditScopeAlgo.acquireParameterEdit( editScope, "/group/light2", "light", ( "", "__areaLight" ) )
		areaEdit2["enabled"].setValue( True )
		areaEdit2["value"].setValue( True )

		areaEdit1 = GafferScene.EditScopeAlgo.acquireParameterEdit(
			editScope, "/group/light1", "light", ( "", "__areaLight" ), createIfNecessary = False
		)
		self.assertEqual( areaEdit1["enabled"].getValue(), False )

		intensityEdit2 = GafferScene.EditScopeAlgo.acquireParameterEdit(
			editScope, "/group/light2", "light", ( "", "intensity" ), createIfNecessary = False
		)
		self.assertEqual( intensityEdit2["enabled"].getValue(), False )

		self.assertEqual(
			editScope["out"].attributes( "/group/light1" )["light"].outputShader().parameters["__areaLight"].value,
			False
		)

		self.assertEqual(
			editScope["out"].attributes( "/group/light2" )["light"].outputShader().parameters["__areaLight"].value,
			True
		)

		self.assertEqual(
			editScope["out"].attributes( "/group/light1" )["light"].outputShader().parameters["intensity"].value,
			imath.Color3f( 2 )
		)

		self.assertEqual(
			editScope["out"].attributes( "/group/light2" )["light"].outputShader().parameters["intensity"].value,
			imath.Color3f( 0, 1, 0 )
		)

	def testParameterEditExceptions( self ) :

		light = GafferSceneTest.TestLight()
		editScope = Gaffer.EditScope()
		editScope.setup( light["out"] )
		editScope["in"].setInput( light["out"] )
		emptyKeys = editScope.keys()

		with six.assertRaisesRegex( self, RuntimeError, 'Location "/bogus" does not exist' ) :
			GafferScene.EditScopeAlgo.acquireParameterEdit( editScope, "/bogus", "light", ( "", "intensity" ) )
		self.assertEqual( editScope.keys(), emptyKeys )

		with six.assertRaisesRegex( self, RuntimeError, 'Attribute "bogus" does not exist' ) :
			GafferScene.EditScopeAlgo.acquireParameterEdit( editScope, "/light", "bogus", ( "", "intensity" ) )
		self.assertEqual( editScope.keys(), emptyKeys )

		with six.assertRaisesRegex( self, RuntimeError, 'Shader "bogus" does not exist' ) :
			GafferScene.EditScopeAlgo.acquireParameterEdit( editScope, "/light", "light", ( "bogus", "intensity" ) )
		self.assertEqual( editScope.keys(), emptyKeys )

		with six.assertRaisesRegex( self, RuntimeError, 'Parameter "bogus" does not exist' ) :
			GafferScene.EditScopeAlgo.acquireParameterEdit( editScope, "/light", "light", ( "", "bogus" ) )
		self.assertEqual( editScope.keys(), emptyKeys )

	def testParameterEditLocalisation( self ) :

		sphere = GafferScene.Sphere()
		group = GafferScene.Group()
		group["in"][0].setInput( sphere["out"] )

		groupFilter = GafferScene.PathFilter()
		groupFilter["paths"].setValue( IECore.StringVectorData( [ "/group" ] ) )
		shader = GafferSceneTest.TestShader()
		shader["type"].setValue( "test:surface" )

		shaderAssignment = GafferScene.ShaderAssignment()
		shaderAssignment["in"].setInput( group["out"] )
		shaderAssignment["filter"].setInput( groupFilter["out"] )
		shaderAssignment["shader"].setInput( shader["out"] )

		editScope = Gaffer.EditScope()
		editScope.setup( shaderAssignment["out"] )
		editScope["in"].setInput( shaderAssignment["out"] )

		self.assertIn( "test:surface", editScope["out"].attributes( "/group" ) )
		self.assertNotIn( "test:surface", editScope["out"].attributes( "/group/sphere" ) )

		edit = GafferScene.EditScopeAlgo.acquireParameterEdit( editScope, "/group/sphere", "test:surface", ( "", "i" ) )
		edit["enabled"].setValue( True )
		edit["value"].setValue( 10 )

		self.assertEqual( editScope["out"].attributes( "/group" ), editScope["in"].attributes( "/group" ) )
		self.assertIn( "test:surface", editScope["out"].attributes( "/group/sphere" ) )
		self.assertEqual(
			editScope["out"].attributes( "/group/sphere" )["test:surface"].outputShader().parameters["i"].value,
			10
		)

	def testParameterEditSerialisation( self ) :

		script = Gaffer.ScriptNode()

		script["light1"] = GafferSceneTest.TestLight()
		script["light1"]["name"].setValue( "light1" )
		script["light2"] = GafferSceneTest.TestLight()
		script["light2"]["name"].setValue( "light2" )

		script["group"] = GafferScene.Group()
		script["group"]["in"][0].setInput( script["light1"]["out"] )
		script["group"]["in"][1].setInput( script["light2"]["out"] )

		script["editScope"] = Gaffer.EditScope()
		script["editScope"].setup( script["group"]["out"] )
		script["editScope"]["in"].setInput( script["group"]["out"] )

		edit1 = GafferScene.EditScopeAlgo.acquireParameterEdit( script["editScope"], "/group/light1", "light", ( "", "intensity" ) )
		edit1["enabled"].setValue( True )
		edit1["value"].setValue( imath.Color3f( 1, 2, 3 ) )

		edit2 = GafferScene.EditScopeAlgo.acquireParameterEdit( script["editScope"], "/group/light2", "light", ( "", "__areaLight" ) )
		edit2["enabled"].setValue( True )
		edit2["value"].setValue( True )

		script2 = Gaffer.ScriptNode()
		script2.execute( script.serialise() )

		self.assertScenesEqual( script2["editScope"]["out"], script["editScope"]["out"] )

		for path, parameter, enabled, value in [
			( "/group/light1", "intensity", True, imath.Color3f( 1, 2, 3 ) ),
			( "/group/light1", "__areaLight", False, False ),
			( "/group/light2", "intensity", False, imath.Color3f( 0 ) ),
			( "/group/light2", "__areaLight", True, True ),
		] :

			edit = GafferScene.EditScopeAlgo.acquireParameterEdit( script2["editScope"], path, "light", ( "", parameter ), createIfNecessary = False )
			self.assertIsNotNone( edit )
			self.assertEqual( edit["enabled"].getValue(), enabled )
			self.assertEqual( edit["value"].getValue(), value )

	def testParameterEditsDontAffectOtherAttributes( self ) :

		light = GafferSceneTest.TestLight()

		lightFilter = GafferScene.PathFilter()
		lightFilter["paths"].setValue( IECore.StringVectorData( [ "/light" ] ) )

		shuffleAttributes = GafferScene.ShuffleAttributes()
		shuffleAttributes["in"].setInput( light["out"] )
		shuffleAttributes["filter"].setInput( lightFilter["out"] )

		editScope = Gaffer.EditScope()
		editScope.setup( shuffleAttributes["out"] )
		editScope["in"].setInput( shuffleAttributes["out"] )

		# Make an edit for the "light" attribute.

		edit = GafferScene.EditScopeAlgo.acquireParameterEdit( editScope, "/light", "light", ( "", "intensity" ) )
		edit["enabled"].setValue( True )
		edit["value"].setValue( imath.Color3f( 1, 2, 3 ) )
		self.assertEqual(
			editScope["out"].attributes( "/light" )["light"].outputShader().parameters["intensity"].value,
			imath.Color3f( 1, 2, 3 )
		)

		# Shuffle the light shader to another attribute. It should not be affected
		# by the edit.

		shuffleAttributes["shuffles"].addChild( Gaffer.ShufflePlug( "light", "test:light" ) )
		self.assertEqual(
			editScope["out"].attributes( "/light" )["test:light"].outputShader().parameters["intensity"].value,
			imath.Color3f( 0 )
		)

	def testProcessorNames( self ) :

		plane = GafferScene.Plane()

		planeFilter = GafferScene.PathFilter()
		planeFilter["paths"].setValue( IECore.StringVectorData( [ "/plane" ]) )

		shader = GafferSceneTest.TestShader()

		shaderAssignment = GafferScene.ShaderAssignment()
		shaderAssignment["in"].setInput( plane["out"] )
		shaderAssignment["filter"].setInput( planeFilter["out"] )
		shaderAssignment["shader"].setInput( shader["out"] )

		editScope = Gaffer.EditScope()
		editScope.setup( shaderAssignment["out"] )
		editScope["in"].setInput( shaderAssignment["out"] )

		for attributeName, processorName in [
			( "gl:surface", "OpenGLSurfaceEdits" ),
			( "gl:light", "OpenGLLightEdits" ),
			( "surface", "SurfaceEdits" ),
			( "displacement", "DisplacementEdits" ),
			( "test:lightFilter:one", "TestLightFilterOneEdits" ),
			( "test:lightFilter:bigGobo", "TestLightFilterBigGoboEdits" ),
		] :
			shader["type"].setValue( attributeName )
			edit = GafferScene.EditScopeAlgo.acquireParameterEdit( editScope, "/plane", attributeName, ( "", "i" ) )
			self.assertEqual( edit.node().getName(), processorName )

if __name__ == "__main__":
	unittest.main()
