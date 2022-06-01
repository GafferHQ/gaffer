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

	def testPruneReadOnlyReason( self ) :

		s = Gaffer.ScriptNode()

		s["cube"] = GafferScene.Cube()

		s["scope"] = Gaffer.EditScope()
		s["scope"].setup( s["cube"]["out"] )
		s["scope"]["in"].setInput( s["cube"]["out"] )

		s["box"] = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["cube"], s["scope"] ] ) )

		self.assertIsNone( GafferScene.EditScopeAlgo.prunedReadOnlyReason( s["box"]["scope"] ) )

		for component in ( s["box"], s["box"]["scope"] ):
			Gaffer.MetadataAlgo.setReadOnly( component, True )
			self.assertEqual( GafferScene.EditScopeAlgo.prunedReadOnlyReason( s["box"]["scope"] ), s["box"] )

		Gaffer.MetadataAlgo.setReadOnly( s["box"], False )
		self.assertEqual( GafferScene.EditScopeAlgo.prunedReadOnlyReason( s["box"]["scope"] ), s["box"]["scope"] )

		Gaffer.MetadataAlgo.setReadOnly( s["box"]["scope"], False )
		GafferScene.EditScopeAlgo.setPruned( s["box"]["scope"], "/cube", True )

		self.assertIsNone( GafferScene.EditScopeAlgo.prunedReadOnlyReason( s["box"]["scope"] ) )

		for component in (
			s["box"]["scope"]["PruningEdits"]["paths"],
			s["box"]["scope"]["PruningEdits"],
			s["box"]["scope"],
			s["box"]
		) :
			Gaffer.MetadataAlgo.setReadOnly( component, True )
			self.assertEqual( GafferScene.EditScopeAlgo.prunedReadOnlyReason( s["box"]["scope"] ), component )

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

	def testTransformEditReadOnlyReason( self ) :

		s = Gaffer.ScriptNode()

		s["cube"] = GafferScene.Cube()

		s["scope"] = Gaffer.EditScope()
		s["scope"].setup( s["cube"]["out"] )
		s["scope"]["in"].setInput( s["cube"]["out"] )

		s["box"] = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["cube"], s["scope"] ] ) )

		self.assertIsNone( GafferScene.EditScopeAlgo.transformEditReadOnlyReason( s["box"]["scope"], "/cube" ) )

		for component in ( s["box"], s["box"]["scope"] ):
			Gaffer.MetadataAlgo.setReadOnly( component, True )
			self.assertEqual( GafferScene.EditScopeAlgo.transformEditReadOnlyReason( s["box"]["scope"], "/cube" ), s["box"] )

		Gaffer.MetadataAlgo.setReadOnly( s["box"], False )
		self.assertEqual( GafferScene.EditScopeAlgo.transformEditReadOnlyReason( s["box"]["scope"], "/cube" ), s["box"]["scope"] )

		Gaffer.MetadataAlgo.setReadOnly( s["box"]["scope"], False )
		GafferScene.EditScopeAlgo.acquireTransformEdit( s["box"]["scope"], "/cube" )

		self.assertIsNone( GafferScene.EditScopeAlgo.transformEditReadOnlyReason( s["box"]["scope"], "/cube" ) )

		candidateComponents = (
			s["box"]["scope"]["TransformEdits"]["edits"][1]["cells"]["pivot"][1],
			s["box"]["scope"]["TransformEdits"]["edits"][1]["cells"]["pivot"],
			s["box"]["scope"]["TransformEdits"]["edits"][1]["cells"]["scale"],
			s["box"]["scope"]["TransformEdits"]["edits"][1]["cells"]["rotate"],
			s["box"]["scope"]["TransformEdits"]["edits"][1]["cells"]["translate"],
			s["box"]["scope"]["TransformEdits"]["edits"][1]["cells"],
			s["box"]["scope"]["TransformEdits"]["edits"][1],
			s["box"]["scope"]["TransformEdits"]["edits"],
			s["box"]["scope"]["TransformEdits"],
			s["box"]["scope"],
			s["box"]
		)

		for component in candidateComponents :
			Gaffer.MetadataAlgo.setReadOnly( component, True )
			self.assertEqual( GafferScene.EditScopeAlgo.transformEditReadOnlyReason( s["box"]["scope"], "/cube" ), component )

		for component in candidateComponents :
			Gaffer.MetadataAlgo.setReadOnly( component, False )

		GafferScene.EditScopeAlgo.removeTransformEdit( s["box"]["scope"], "/cube" )
		self.assertIsNone( GafferScene.EditScopeAlgo.acquireTransformEdit( s["box"]["scope"], "/cube", createIfNecessary = False ) )

		for component in (
			s["box"]["scope"]["TransformEdits"]["edits"],
			s["box"]["scope"]["TransformEdits"]
		) :
			Gaffer.MetadataAlgo.setReadOnly( component, True )
			self.assertEqual( GafferScene.EditScopeAlgo.transformEditReadOnlyReason( s["box"]["scope"], "/cube" ), component )

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

	def testParameterEditReadOnlyReason( self ) :

		s = Gaffer.ScriptNode()

		s["light"] = GafferSceneTest.TestLight()

		s["scope"] = Gaffer.EditScope()
		s["scope"].setup( s["light"]["out"] )
		s["scope"]["in"].setInput( s["light"]["out"] )

		s["box"] = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["light"], s["scope"] ] ) )

		self.assertIsNone( GafferScene.EditScopeAlgo.parameterEditReadOnlyReason( s["box"]["scope"], "/light", "light", ( "", "intensity" ) ) )

		for component in ( s["box"], s["box"]["scope"] ):
			Gaffer.MetadataAlgo.setReadOnly( component, True )
			self.assertEqual( GafferScene.EditScopeAlgo.parameterEditReadOnlyReason( s["box"]["scope"], "/light", "light", ( "", "intensity" ) ), s["box"] )

		Gaffer.MetadataAlgo.setReadOnly( s["box"], False )
		self.assertEqual( GafferScene.EditScopeAlgo.parameterEditReadOnlyReason( s["box"]["scope"], "/light", "light", ( "", "intensity" ) ), s["box"]["scope"] )

		Gaffer.MetadataAlgo.setReadOnly( s["box"]["scope"], False )
		GafferScene.EditScopeAlgo.acquireParameterEdit( s["box"]["scope"], "/light", "light", ( "", "intensity" ) )

		self.assertIsNone( GafferScene.EditScopeAlgo.parameterEditReadOnlyReason( s["box"]["scope"], "/light", "light", ( "", "intensity" ) ) )

		candidateComponents = (
			s["box"]["scope"]["LightEdits"]["edits"][1]["cells"]["intensity"]["value"]["value"][1],
			s["box"]["scope"]["LightEdits"]["edits"][1]["cells"]["intensity"]["value"]["mode"],
			s["box"]["scope"]["LightEdits"]["edits"][1]["cells"]["intensity"]["value"]["enabled"],
			s["box"]["scope"]["LightEdits"]["edits"][1]["cells"]["intensity"]["value"]["name"],
			s["box"]["scope"]["LightEdits"]["edits"][1]["cells"]["intensity"]["value"],
			s["box"]["scope"]["LightEdits"]["edits"][1]["cells"]["intensity"],
			s["box"]["scope"]["LightEdits"]["edits"][1]["cells"],
			s["box"]["scope"]["LightEdits"]["edits"][1],
			s["box"]["scope"]["LightEdits"]["edits"],
			s["box"]["scope"]["LightEdits"],
			s["box"]["scope"],
			s["box"]
		)

		for component in candidateComponents :
			Gaffer.MetadataAlgo.setReadOnly( component, True )
			self.assertEqual( GafferScene.EditScopeAlgo.parameterEditReadOnlyReason( s["box"]["scope"], "/light", "light", ( "", "intensity" ) ), component )

		for component in candidateComponents :
			Gaffer.MetadataAlgo.setReadOnly( component, False )

		# We can't remove parameter edits, they're just disabled (as the row is shared with other parameters),
		# so we try to create one for another light instead
		s["box"]["light"]["name"].setValue( "light2" )

		self.assertIsNone( GafferScene.EditScopeAlgo.acquireParameterEdit( s["box"]["scope"], "/light2", "light", ( "", "intensity" ), createIfNecessary = False ) )

		for component in (
			s["box"]["scope"]["LightEdits"]["edits"],
			s["box"]["scope"]["LightEdits"]
		) :
			Gaffer.MetadataAlgo.setReadOnly( component, True )
			self.assertEqual( GafferScene.EditScopeAlgo.parameterEditReadOnlyReason( s["box"]["scope"], "/light2", "light", ( "", "intensity" ) ), component )

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
		light["visualiserAttributes"]["scale"]["enabled"].setValue( True )

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

		with six.assertRaisesRegex( self, RuntimeError, 'Attribute "gl:visualiser:scale" is not a shader' ) :
			GafferScene.EditScopeAlgo.acquireParameterEdit( editScope, "/light", "gl:visualiser:scale", ( "", "intensity" ) )
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

	def testAttributeEdits( self ) :

		light = GafferSceneTest.TestLight()
		light["visualiserAttributes"]["scale"]["enabled"].setValue( True )

		editScope = Gaffer.EditScope()
		editScope.setup( light["out"] )
		editScope["in"].setInput( light["out"] )
		self.assertEqual( editScope["out"].attributes( "/light" )["gl:visualiser:scale"].value, 1.0 )

		self.assertFalse(
			GafferScene.EditScopeAlgo.hasAttributeEdit( editScope, "/light", "gl:visualiser:scale" )
		)
		self.assertIsNone(
			GafferScene.EditScopeAlgo.acquireAttributeEdit(
				editScope,
				"/light",
				"gl:visualiser:scale",
				createIfNecessary = False
			)
		)

		edit = GafferScene.EditScopeAlgo.acquireAttributeEdit(
			editScope,
			"/light",
			"gl:visualiser:scale"
		)
		self.assertIsInstance( edit, GafferScene.TweakPlug )
		self.assertIsInstance( edit["value"], Gaffer.FloatPlug )
		self.assertEqual( edit["mode"].getValue(), GafferScene.TweakPlug.Mode.Replace )
		self.assertEqual( edit["value"].getValue(), 1.0 )
		self.assertEqual( edit["enabled"].getValue(), False )

		edit["enabled"].setValue( True )
		edit["value"].setValue( 2.0 )
		self.assertEqual( editScope["out"].attributes( "/light" )["gl:visualiser:scale"].value, 2.0 )

		self.assertEqual(
			GafferScene.EditScopeAlgo.acquireAttributeEdit( editScope, "/light", "gl:visualiser:scale" ),
			edit
		)

		light["visualiserAttributes"]["scale"]["value"].setValue( 0.5 )
		edit["enabled"].setValue( False )
		self.assertEqual( editScope["out"].attributes( "/light" )["gl:visualiser:scale"].value, 0.5 )

		self.assertIsNone(
			GafferScene.EditScopeAlgo.acquireAttributeEdit(
				editScope,
				"/light",
				"gl:visualiser:maxTextureResolution",
				createIfNecessary = False
			)
		)

	def testAttributeEditReadOnlyReason( self ) :

		s = Gaffer.ScriptNode()

		s["light"] = GafferSceneTest.TestLight()
		s["light"]["visualiserAttributes"]["scale"]["enabled"].setValue( True )

		s["scope"] = Gaffer.EditScope()
		s["scope"].setup( s["light"]["out"] )
		s["scope"]["in"].setInput( s["light"]["out"] )

		s["box"] = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["light"], s["scope"] ] ) )

		self.assertIsNone(
			GafferScene.EditScopeAlgo.attributeEditReadOnlyReason(
				s["box"]["scope"],
				"/light",
				"gl:visualiser:scale"
			)
		)

		for component in ( s["box"], s["box"]["scope"] ) :
			Gaffer.MetadataAlgo.setReadOnly( component, True )
			self.assertEqual(
				GafferScene.EditScopeAlgo.attributeEditReadOnlyReason(
					s["box"]["scope"],
					"/light",
					"gl:visualiser:scale"
				),
				s["box"]
			)

		Gaffer.MetadataAlgo.setReadOnly( s["box"], False )
		self.assertEqual(
			GafferScene.EditScopeAlgo.attributeEditReadOnlyReason(
				s["box"]["scope"],
				"/light",
				"gl:visualiser:scale"
			),
			s["box"]["scope"]
		)

		Gaffer.MetadataAlgo.setReadOnly( s["box"]["scope"], False )
		GafferScene.EditScopeAlgo.acquireAttributeEdit(
			s["box"]["scope"],
			"/light",
			"gl:visualiser:scale"
		)

		self.assertIsNone(
			GafferScene.EditScopeAlgo.attributeEditReadOnlyReason(
				s["box"]["scope"],
				"/light",
				"gl:visualiser:scale"
			)
		)

		candidateComponents = (
			s["box"]["scope"]["AttributeEdits"]["edits"][1]["cells"]["gl_visualiser_scale"]["value"]["value"],
			s["box"]["scope"]["AttributeEdits"]["edits"][1]["cells"]["gl_visualiser_scale"]["value"]["mode"],
			s["box"]["scope"]["AttributeEdits"]["edits"][1]["cells"]["gl_visualiser_scale"]["value"]["enabled"],
			s["box"]["scope"]["AttributeEdits"]["edits"][1]["cells"]["gl_visualiser_scale"]["value"]["name"],
			s["box"]["scope"]["AttributeEdits"]["edits"][1]["cells"]["gl_visualiser_scale"]["value"],
			s["box"]["scope"]["AttributeEdits"]["edits"][1]["cells"]["gl_visualiser_scale"],
			s["box"]["scope"]["AttributeEdits"]["edits"][1]["cells"],
			s["box"]["scope"]["AttributeEdits"]["edits"][1],
			s["box"]["scope"]["AttributeEdits"]["edits"],
			s["box"]["scope"]["AttributeEdits"],
			s["box"]["scope"],
			s["box"]
		)

		for component in candidateComponents :
			Gaffer.MetadataAlgo.setReadOnly( component, True )
			self.assertEqual(
				GafferScene.EditScopeAlgo.attributeEditReadOnlyReason(
					s["box"]["scope"],
					"/light",
					"gl:visualiser:scale"
				),
				component
			)

		for component in candidateComponents :
			Gaffer.MetadataAlgo.setReadOnly( component, False )

		# We can't remove attribute edits, they're just disabled (as the row is shared with
		# other attributes), so we try to create one for another light instead.
		s["box"]["light"]["name"].setValue( "light2" )

		self.assertIsNone(
			GafferScene.EditScopeAlgo.acquireAttributeEdit(
				s["box"]["scope"],
				"/light2",
				"gl:visualiser:scale",
				createIfNecessary = False
			)
		)

		for component in (
			s["box"]["scope"]["AttributeEdits"]["edits"],
			s["box"]["scope"]["AttributeEdits"]
		) :
			Gaffer.MetadataAlgo.setReadOnly( component, True )
			self.assertEqual(
				GafferScene.EditScopeAlgo.attributeEditReadOnlyReason(
					s["box"]["scope"],
					"/light2",
					"gl:visualiser:scale"
				),
				component
			)

	def testAttributeEditsDontAffectOtherObjects( self ) :

		# Make two lights and an EditScope

		light1 = GafferSceneTest.TestLight()
		light1["name"].setValue( "light1" )
		light1["visualiserAttributes"]["scale"]["enabled"].setValue( True )
		light1["visualiserAttributes"]["scale"]["value"].setValue( 2.0 )

		light2 = GafferSceneTest.TestLight()
		light2["name"].setValue( "light2" )
		light2["visualiserAttributes"]["scale"]["enabled"].setValue( True )
		light2["visualiserAttributes"]["scale"]["value"].setValue( 0.5 )

		group = GafferScene.Group()
		group["in"][0].setInput( light1["out"] )
		group["in"][1].setInput( light2["out"] )

		editScope = Gaffer.EditScope()
		editScope.setup( group["out"] )
		editScope["in"].setInput( group["out"] )
		self.assertEqual( editScope["out"].attributes( "/group/light1" )["gl:visualiser:scale"].value, 2.0 )
		self.assertEqual( editScope["out"].attributes( "/group/light2" )["gl:visualiser:scale"].value, 0.5 )

		# Edit light1

		scaleEdit1 = GafferScene.EditScopeAlgo.acquireAttributeEdit(
			editScope,
			"/group/light1",
			"gl:visualiser:scale"
		)
		scaleEdit1["enabled"].setValue( True )
		scaleEdit1["value"].setValue( 4.0 )

		self.assertEqual( editScope["out"].attributes( "/group/light1" )["gl:visualiser:scale"].value, 4.0 )

		# This shouldn't create an edit for light2

		self.assertIsNone(
			GafferScene.EditScopeAlgo.acquireAttributeEdit(
				editScope,
				"/group/light2",
				"gl:visualiser:scale",
				createIfNecessary = False
			)
		)
		self.assertEqual(
			editScope["in"].attributes( "/group/light2" ),
			editScope["out"].attributes( "/group/light2" )
		)

		# But if we edit a _different_ attribute on light2, then both lights are in the
		# spreadsheet, and we must therefore expect both to have edits for both
		# attributes. We just need to make sure that the extra edits are disabled.

		light1["visualiserAttributes"]["maxTextureResolution"]["enabled"].setValue( True )
		light2["visualiserAttributes"]["maxTextureResolution"]["enabled"].setValue( True )

		resEdit2 = GafferScene.EditScopeAlgo.acquireAttributeEdit(
			editScope,
			"/group/light2",
			"gl:visualiser:maxTextureResolution"
		)
		resEdit2["enabled"].setValue( True )
		resEdit2["value"].setValue( 128 )

		resEdit1 = GafferScene.EditScopeAlgo.acquireAttributeEdit(
			editScope,
			"/group/light1",
			"gl:visualiser:maxTextureResolution",
			createIfNecessary = False
		)
		self.assertEqual( resEdit1["enabled"].getValue(), False )

		scaleEdit2 = GafferScene.EditScopeAlgo.acquireAttributeEdit(
			editScope,
			"/group/light2",
			"gl:visualiser:scale",
			createIfNecessary = False
		)
		self.assertEqual( scaleEdit2["enabled"].getValue(), False )

		self.assertEqual( editScope["out"].attributes( "/group/light1" )["gl:visualiser:scale"].value, 4.0 )
		self.assertEqual( editScope["out"].attributes( "/group/light2" )["gl:visualiser:scale"].value, 0.5 )
		self.assertEqual( editScope["out"].attributes( "/group/light1" )["gl:visualiser:maxTextureResolution"].value, 512 )
		self.assertEqual( editScope["out"].attributes( "/group/light2" )["gl:visualiser:maxTextureResolution"].value, 128 )

	def testAttributeEditExceptions( self ) :

		light = GafferSceneTest.TestLight()
		editScope = Gaffer.EditScope()
		editScope.setup( light["out"] )
		editScope["in"].setInput( light["out"] )
		emptyKeys = editScope.keys()

		with six.assertRaisesRegex( self, RuntimeError, 'Location "/bogus" does not exist' ) :
			GafferScene.EditScopeAlgo.acquireAttributeEdit( editScope, "/bogus", "gl:visualiser:scale" )
		self.assertEqual( editScope.keys(), emptyKeys )

		with six.assertRaisesRegex( self, RuntimeError, 'Attribute "light" cannot be tweaked' ) :
			GafferScene.EditScopeAlgo.acquireAttributeEdit( editScope, "/light", "light" )
		self.assertEqual( editScope.keys(), emptyKeys )

		with six.assertRaisesRegex( self, RuntimeError, 'Attribute "bogus" does not exist' ) :
			GafferScene.EditScopeAlgo.acquireAttributeEdit( editScope, "/light", "bogus" )
		self.assertEqual( editScope.keys(), emptyKeys )

	def testAttributeEditLocalisation( self ) :

		light = GafferSceneTest.TestLight()

		group = GafferScene.Group()
		group["in"][0].setInput( light["out"] )

		groupFilter = GafferScene.PathFilter()
		groupFilter["paths"].setValue( IECore.StringVectorData( [ "/group" ] ) )

		customAttributes = GafferScene.CustomAttributes()
		customAttributes["in"].setInput( group["out"] )
		customAttributes["filter"].setInput( groupFilter["out"] )
		customAttributes["attributes"].addMember( "test:hello", "hi" )

		editScope = Gaffer.EditScope()
		editScope.setup( customAttributes["out"] )
		editScope["in"].setInput( customAttributes["out"] )

		self.assertIn( "test:hello", editScope["out"].attributes( "/group" ) )
		self.assertNotIn( "test:hello", editScope["out"].attributes( "/group/light" ) )

		edit = GafferScene.EditScopeAlgo.acquireAttributeEdit( editScope, "/group/light", "test:hello" )
		edit["enabled"].setValue( True )
		edit["value"].setValue( "aloha" )

		self.assertEqual( editScope["out"].attributes( "/group" ), editScope["in"].attributes( "/group" ) )
		self.assertIn( "test:hello", editScope["out"].attributes( "/group/light" ) )
		self.assertEqual( editScope["out"].attributes( "/group/light" )["test:hello"].value, "aloha" )

	def testAttributeEditSerialisation( self ) :

		script = Gaffer.ScriptNode()

		script["light1"] = GafferSceneTest.TestLight()
		script["light1"]["name"].setValue( "light1" )
		script["light1"]["visualiserAttributes"]["scale"]["enabled"].setValue( True )
		script["light1"]["visualiserAttributes"]["maxTextureResolution"]["enabled"].setValue( True )

		script["light2"] = GafferSceneTest.TestLight()
		script["light2"]["name"].setValue( "light2" )
		script["light2"]["visualiserAttributes"]["scale"]["enabled"].setValue( True )
		script["light2"]["visualiserAttributes"]["maxTextureResolution"]["enabled"].setValue( True )

		script["group"] = GafferScene.Group()
		script["group"]["in"][0].setInput( script["light1"]["out"] )
		script["group"]["in"][1].setInput( script["light2"]["out"] )

		script["editScope"] = Gaffer.EditScope()
		script["editScope"].setup( script["group"]["out"] )
		script["editScope"]["in"].setInput( script["group"]["out"] )

		edit1 = GafferScene.EditScopeAlgo.acquireAttributeEdit( script["editScope"], "/group/light1", "gl:visualiser:scale" )
		edit1["enabled"].setValue( True )
		edit1["value"].setValue( 2.0 )

		edit2 = GafferScene.EditScopeAlgo.acquireAttributeEdit( script["editScope"], "/group/light2", "gl:visualiser:maxTextureResolution" )
		edit2["enabled"].setValue( True )
		edit2["value"].setValue( 128 )

		script2 = Gaffer.ScriptNode()
		script2.execute( script.serialise() )

		self.assertScenesEqual( script2["editScope"]["out"], script["editScope"]["out"] )

		for path, attribute, enabled, value in [
			( "/group/light1", "gl:visualiser:scale", True, 2.0 ),
			( "/group/light1", "gl:visualiser:maxTextureResolution", False, 512 ),
			( "/group/light2", "gl:visualiser:scale", False, 1.0 ),
			( "/group/light2", "gl:visualiser:maxTextureResolution", True, 128 ),
		] :
			edit = GafferScene.EditScopeAlgo.acquireAttributeEdit(
				script2["editScope"], path, attribute, createIfNecessary = False
			)
			self.assertIsNotNone( edit )
			self.assertEqual( edit["enabled"].getValue(), enabled )
			self.assertEqual( edit["value"].getValue(), value )

	def testAttributeEditsDontAffectOtherAttributes( self ) :

		light = GafferSceneTest.TestLight()
		light["visualiserAttributes"]["scale"]["enabled"].setValue( True )

		lightFilter = GafferScene.PathFilter()
		lightFilter["paths"].setValue( IECore.StringVectorData( [ "/light" ] ) )

		shuffleAttributes = GafferScene.ShuffleAttributes()
		shuffleAttributes["in"].setInput( light["out"] )
		shuffleAttributes["filter"].setInput( lightFilter["out"] )

		editScope = Gaffer.EditScope()
		editScope.setup( shuffleAttributes["out"] )
		editScope["in"].setInput( shuffleAttributes["out"] )

		edit = GafferScene.EditScopeAlgo.acquireAttributeEdit( editScope, "/light", "gl:visualiser:scale" )
		edit["enabled"].setValue( True )
		edit["value"].setValue( 2.0 )
		self.assertEqual( editScope["out"].attributes( "/light" )["gl:visualiser:scale"].value, 2.0 )

		# Shuffle "gl:visualiser:scale" to another attribute. It should not be affected by the edit.

		shuffleAttributes["shuffles"].addChild( Gaffer.ShufflePlug( "gl:visualiser:scale", "test:scale" ) )
		self.assertEqual( editScope["out"].attributes( "/light" )["test:scale"].value, 1.0 )

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
