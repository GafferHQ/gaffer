##########################################################################
#
#  Copyright (c) 2022, Cinesite VFX Ltd. All rights reserved.
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

import pathlib
import unittest
import os
import subprocess

import pxr.Usd

import IECore
import IECoreScene

import Gaffer
import GafferTest
import GafferDispatch
import GafferUSD
import GafferScene
import GafferSceneTest

class USDLayerWriterTest( GafferSceneTest.SceneTestCase ) :

	def __writeLayerAndComposition( self, base, layer, frames = None ) :

		baseWriter = GafferScene.SceneWriter()
		baseWriter["in"].setInput( base )
		baseWriter["fileName"].setValue( self.temporaryDirectory() / "base.usda" )
		baseWriter["task"].execute()

		layerWriter = GafferUSD.USDLayerWriter()
		layerWriter["base"].setInput( base )
		layerWriter["layer"].setInput( layer )
		layerWriter["fileName"].setValue( self.temporaryDirectory() / "layer.usda" )
		if frames is None :
			layerWriter["task"].execute()
		else :
			layerWriter["task"].executeSequence( frames )

		compositionFilePath = self.temporaryDirectory() / "composed.usda"
		composition = pxr.Usd.Stage.CreateNew( str( compositionFilePath ) )
		composition.GetRootLayer().subLayerPaths = [
			layerWriter["fileName"].getValue(),
			baseWriter["fileName"].getValue(),
		]
		composition.GetRootLayer().Save()

		return layerWriter["fileName"].getValue(), compositionFilePath

	def test( self ) :

		# Make a simple scene, and write it to a USD file.
		#
		# - group
		#   - plane
		#   - plane1
		#   - sphere
		#   - sphere1

		plane = GafferScene.Plane()
		sphere = GafferScene.Sphere()
		sphere["type"].setValue( GafferScene.Sphere.Type.Primitive )

		group = GafferScene.Group()
		group["in"][0].setInput( plane["out"] )
		group["in"][1].setInput( plane["out"] )
		group["in"][2].setInput( sphere["out"] )
		group["in"][3].setInput( sphere["out"] )

		# Make downstream modifications to the scene :
		#
		#  - Transform `/group/sphere` and assign a shader to it
		#  - Add a visibility attribute to `/group/plane`
		#  - Add a new location at `/group/sphere2`
		#  - Prune `/group/plane1`

		sphereFilter = GafferScene.PathFilter()
		sphereFilter["paths"].setValue( IECore.StringVectorData( [ "/group/sphere" ] ) )

		transform = GafferScene.Transform()
		transform["in"].setInput( group["out"] )
		transform["filter"].setInput( sphereFilter["out"] )
		transform["transform"]["translate"]["x"].setValue( 10 )

		shaderAssignment = GafferScene.CustomAttributes()
		shaderAssignment["in"].setInput( transform["out"] )
		shaderAssignment["filter"].setInput( sphereFilter["out"] )
		# Assigning shader manually, because IECoreUSD won't round-trip the
		# blindData that the Shader and ShaderAssignment nodes would add.
		shaderAssignment["extraAttributes"].setValue( {
			"surface" : IECoreScene.ShaderNetwork( { "output" : IECoreScene.Shader( "flat" ) }, output = "output" )
		} )

		planeFilter = GafferScene.PathFilter()
		planeFilter["paths"].setValue( IECore.StringVectorData( [ "/group/plane" ] ) )

		attributes = GafferScene.StandardAttributes()
		attributes["in"].setInput( shaderAssignment["out"] )
		attributes["filter"].setInput( planeFilter["out"] )

		attributes["attributes"]["visibility"]["enabled"].setValue( True )
		attributes["attributes"]["visibility"]["value"].setValue( False )

		groupFilter = GafferScene.PathFilter()
		groupFilter["paths"].setValue( IECore.StringVectorData( [ "/group" ] ) )

		parent = GafferScene.Parent()
		parent["in"].setInput( attributes["out"] )
		parent["filter"].setInput( groupFilter["out"] )
		parent["children"][0].setInput( sphere["out"] )

		plane1Filter = GafferScene.PathFilter()
		plane1Filter["paths"].setValue( IECore.StringVectorData( [ "/group/plane1" ] ) )

		prune = GafferScene.Prune()
		prune["in"].setInput( parent["out"] )
		prune["filter"].setInput( plane1Filter["out"] )

		# Write the differences into a USD layer, and compose them back with the original.
		# The composed result should be identical to the Gaffer scene.

		layerFileName, compositionFilePath = self.__writeLayerAndComposition( group["out"], prune["out"] )

		reader = GafferScene.SceneReader()
		reader["fileName"].setValue( compositionFilePath )
		self.assertScenesEqual( reader["out"], prune["out"], checks = self.allSceneChecks - { "sets" } )

		# Check that we've actually got a minimal set of opinions in the
		# layer. We could pass the tests above just by writing
		# _everything_!

		layer = pxr.Sdf.Layer.OpenAsAnonymous( layerFileName )

		# We didn't modify `/group/sphere1`, so it shouldn't even be present in the layer.
		self.assertIsNone( layer.GetPrimAtPath( "/group/sphere1" ) )
		# We did modify `/group/plane`, but we didn't change its type, so we expect
		# an "over" in the layer, and a minimal set of authored properties.
		self.assertEqual( layer.GetPrimAtPath( "/group/plane" ).specifier, pxr.Sdf.SpecifierOver )
		self.assertEqual( layer.GetPrimAtPath( "/group/plane" ).typeName, "" )
		self.assertEqual( list( layer.GetPrimAtPath( "/group/plane" ).properties.keys() ), [ "visibility" ] )
		# Likewise for `/group/sphere`.
		self.assertEqual( layer.GetPrimAtPath( "/group/sphere" ).specifier, pxr.Sdf.SpecifierOver )
		self.assertEqual( layer.GetPrimAtPath( "/group/sphere" ).typeName, "" )
		self.assertEqual( set( layer.GetPrimAtPath( "/group/sphere" ).properties.keys() ), { "material:binding", "xformOp:transform" } )
		# `/group/sphere2` is newly added, so should be fully defined.
		self.assertEqual( layer.GetPrimAtPath( "/group/sphere2" ).specifier, pxr.Sdf.SpecifierDef )

	def testCreateDirectories( self ) :

		sphere = GafferScene.Sphere()

		writer = GafferUSD.USDLayerWriter()
		writer["base"].setInput( sphere["out"] )
		writer["layer"].setInput( sphere["out"] )
		writer["fileName"].setValue( self.temporaryDirectory() / "subdir" / "test.usda" )

		writer["task"].execute()
		self.assertTrue( pathlib.Path( writer["fileName"].getValue() ).is_file() )

	def testRemoveAttribute( self ) :

		sphere = GafferScene.Sphere()
		sphereFilter = GafferScene.PathFilter()
		sphereFilter["paths"].setValue( IECore.StringVectorData( [ "/sphere" ] ) )

		attributes = GafferScene.StandardAttributes()
		attributes["in"].setInput( sphere["out"] )
		attributes["filter"].setInput( sphereFilter["out"] )
		attributes["attributes"]["visibility"]["enabled"].setValue( True )

		layer, composition = self.__writeLayerAndComposition( base = attributes["out"], layer = sphere["out"] )

		reader = GafferScene.SceneReader()
		reader["fileName"].setValue( composition )

		self.assertScenesEqual( reader["out"], sphere["out"], checks = self.allSceneChecks - { "sets" } )

	def testKind( self ) :

		sphere = GafferScene.Sphere()
		sphere["type"].setValue( sphere.Type.Primitive )

		sphereFilter = GafferScene.PathFilter()
		sphereFilter["paths"].setValue( IECore.StringVectorData( [ "/sphere" ] ) )

		attributes = GafferUSD.USDAttributes()
		attributes["in"].setInput( sphere["out"] )
		attributes["filter"].setInput( sphereFilter["out"] )
		attributes["attributes"]["kind"]["enabled"].setValue( True )

		layerFileName, compositionFileName = self.__writeLayerAndComposition( sphere["out"], attributes["out"] )

		reader = GafferScene.SceneReader()
		reader["fileName"].setValue( compositionFileName )
		self.assertScenesEqual( reader["out"], attributes["out"], checks = self.allSceneChecks - { "sets" } )

	def testChangePrimitiveType( self ) :

		sphereMesh = GafferScene.Sphere()

		spherePrimitive = GafferScene.Sphere()
		spherePrimitive["type"].setValue( spherePrimitive.Type.Primitive )

		layerFileName, compositionFileName = self.__writeLayerAndComposition( sphereMesh["out"], spherePrimitive["out"] )

		reader = GafferScene.SceneReader()
		reader["fileName"].setValue( compositionFileName )
		self.assertScenesEqual( reader["out"], spherePrimitive["out"], checks = self.allSceneChecks - { "sets" } )

	def testNoContextLeaks( self ) :

		sphere = GafferScene.Sphere()

		layerWriter = GafferUSD.USDLayerWriter()
		layerWriter["base"].setInput( sphere["out"] )
		layerWriter["layer"].setInput( sphere["out"] )
		layerWriter["fileName"].setValue( self.temporaryDirectory() / "layer.usda" )

		with Gaffer.ContextMonitor( sphere ) as monitor :
			layerWriter["task"].execute()

		self.assertNotIn( "usdLayerWriter:fileName", monitor.combinedStatistics().variableNames() )

	def testNoWritePermissions( self ) :

		sphere = GafferScene.Sphere()

		layerWriter = GafferUSD.USDLayerWriter()
		layerWriter["base"].setInput( sphere["out"] )
		layerWriter["layer"].setInput( sphere["out"] )
		layerWriter["fileName"].setValue( self.temporaryDirectory() / "layer.usda" )

		if os.name != "nt" :
			self.temporaryDirectory().chmod( 444 )
		else :
			subprocess.check_call(
				[ "icacls", self.temporaryDirectory(), "/deny", "Users:(OI)(CI)(W)" ],
				stdout = subprocess.DEVNULL,
				stderr = subprocess.STDOUT
			)

		with self.assertRaisesRegex( RuntimeError, 'Failed to export layer to "{}"'.format( layerWriter["fileName"].getValue() ) ) :
			layerWriter["task"].execute()

	def testAddSet( self ) :

		sphere = GafferScene.Sphere()
		group = GafferScene.Group()
		group["in"][0].setInput( sphere["out"] )

		cube = GafferScene.Cube()

		parent = GafferScene.Parent()
		parent["in"].setInput( group["out"] )
		parent["children"][0].setInput( cube["out"] )
		parent["parent"].setValue( "/" )

		pathFilter = GafferScene.PathFilter()
		pathFilter["paths"].setValue( IECore.StringVectorData( [ "/cube", "/group/sphere" ] ) )

		setNode = GafferScene.Set()
		setNode["in"].setInput( parent["out"] )
		setNode["filter"].setInput( pathFilter["out"] )
		setNode["name"].setValue( "setA" )
		self.assertEqual( setNode["out"].set( "setA" ).value, IECore.PathMatcher( [ "/cube", "/group/sphere" ] ) )

		layerFileName, compositionFileName = self.__writeLayerAndComposition( parent["out"], setNode["out"] )

		reader = GafferScene.SceneReader()
		reader["fileName"].setValue( compositionFileName )
		self.assertEqual( reader["out"].set( "setA" ), setNode["out"].set( "setA" ) )

	# We'll need to analyse the list operations on `apiSchemas` metadata and
	# author appropriate deletions to make this work.
	@unittest.expectedFailure
	def testRemoveSet( self ) :

		plane = GafferScene.Plane()
		plane["sets"].setValue( "setA setB" )

		deleteSets = GafferScene.DeleteSets()
		deleteSets["in"].setInput( plane["out"] )
		deleteSets["names"].setValue( "setA" )
		self.assertNotIn( "setA", deleteSets["out"].setNames() )
		self.assertIn( "setB", deleteSets["out"].setNames() )

		layerFileName, compositionFileName = self.__writeLayerAndComposition( plane["out"], deleteSets["out"] )

		reader = GafferScene.SceneReader()
		reader["fileName"].setValue( compositionFileName )
		self.assertNotIn( "setA", reader["out"].setNames() )
		self.assertIn( "setB", reader["out"].setNames() )
		self.assertEqual( reader["out"].set( "setB" ).value, IECore.PathMatcher( [ "/plane" ] ) )

	def testAddToSet( self ) :

		sphere = GafferScene.Sphere()
		sphere["sets"].setValue( "setA" )
		group = GafferScene.Group()
		group["in"][0].setInput( sphere["out"] )

		cube = GafferScene.Cube()

		parent = GafferScene.Parent()
		parent["in"].setInput( group["out"] )
		parent["children"][0].setInput( cube["out"] )
		parent["parent"].setValue( "/" )

		pathFilter = GafferScene.PathFilter()
		pathFilter["paths"].setValue( IECore.StringVectorData( [ "/cube" ] ) )

		setNode = GafferScene.Set()
		setNode["in"].setInput( parent["out"] )
		setNode["filter"].setInput( pathFilter["out"] )
		setNode["name"].setValue( "setA" )
		setNode["mode"].setValue( setNode.Mode.Add )
		self.assertEqual( setNode["out"].set( "setA" ).value, IECore.PathMatcher( [ "/cube", "/group/sphere" ] ) )

		layerFileName, compositionFileName = self.__writeLayerAndComposition( parent["out"], setNode["out"] )

		reader = GafferScene.SceneReader()
		reader["fileName"].setValue( compositionFileName )
		self.assertEqual( reader["out"].set( "setA" ), setNode["out"].set( "setA" ) )

	def testRemoveFromSet( self ) :

		sphere = GafferScene.Sphere()
		sphere["sets"].setValue( "setA" )
		group = GafferScene.Group()
		group["in"][0].setInput( sphere["out"] )
		group["in"][1].setInput( sphere["out"] )

		pathFilter = GafferScene.PathFilter()
		pathFilter["paths"].setValue( IECore.StringVectorData( [ "/group/sphere" ] ) )

		setNode = GafferScene.Set()
		setNode["in"].setInput( group["out"] )
		setNode["filter"].setInput( pathFilter["out"] )
		setNode["name"].setValue( "setA" )
		setNode["mode"].setValue( setNode.Mode.Remove )
		self.assertEqual( setNode["out"].set( "setA" ).value, IECore.PathMatcher( [ "/group/sphere1" ] ) )

		layerFileName, compositionFileName = self.__writeLayerAndComposition( group["out"], setNode["out"] )

		reader = GafferScene.SceneReader()
		reader["fileName"].setValue( compositionFileName )
		self.assertEqual( reader["out"].set( "setA" ), setNode["out"].set( "setA" ) )

	def testAnimatedTransform( self ) :

		sphere = GafferScene.Sphere()

		frame = GafferTest.FrameNode()
		animatedSphere = GafferScene.Sphere()
		animatedSphere["transform"]["translate"]["x"].setInput( frame["output"] )

		with Gaffer.Context() as context :
			# Transforms are identical on frame zero, so we need to detect
			# that they are different on subsequent frames.
			layerFileName, compositionFileName = self.__writeLayerAndComposition( sphere["out"], animatedSphere["out"], frames = [ 0, 1, 2, 3 ] )

		reader = GafferScene.SceneReader()
		reader["fileName"].setValue( compositionFileName )

		with Gaffer.Context() as context :
			for frame in [ 0, 1, 2, 3 ] :
				context.setFrame( frame )
				self.assertEqual( reader["out"].transform( "/sphere" ), animatedSphere["out"].transform( "/sphere" ) )

	def testDispatch( self ) :

		script = Gaffer.ScriptNode()

		script["reader"] = GafferScene.SceneReader()
		script["reader"]["fileName"].setValue( Gaffer.rootPath() / "python" / "GafferSceneTest" / "usdFiles" / "generalTestMesh.usd" )

		script["writer"] = GafferUSD.USDLayerWriter()
		script["writer"]["base"].setInput( script["reader"]["out"] )
		script["writer"]["layer"].setInput( script["reader"]["out"] )
		script["writer"]["fileName"].setValue( self.temporaryDirectory() / "test.usda" )

		script["dispatcher"] = GafferDispatch.LocalDispatcher( jobPool = GafferDispatch.LocalDispatcher.JobPool() )
		script["dispatcher"]["tasks"][0].setInput( script["writer"]["task"] )
		script["dispatcher"]["jobsDirectory"].setValue( self.temporaryDirectory() / "localJobs" )
		script["dispatcher"]["task"].execute()

		self.assertTrue( ( self.temporaryDirectory() / "test.usda" ).is_file() )

	def testIdenticalNamesInDifferentGroups( self ) :

		# /plane  <- modified in layer
		# /group
		#   /plane  <- identical

		plane = GafferScene.Plane()

		group = GafferScene.Group()
		group["in"][0].setInput( plane["out"] )

		parent = GafferScene.Parent()
		parent["in"].setInput( plane["out"] )
		parent["children"][0].setInput( group["out"] )
		parent["parent"].setValue( "/" )

		pathFilter = GafferScene.PathFilter()
		pathFilter["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		primitiveVariables = GafferScene.PrimitiveVariables()
		primitiveVariables["in"].setInput( parent["out"] )
		primitiveVariables["filter"].setInput( pathFilter["out"] )
		primitiveVariables["primitiveVariables"].addChild( Gaffer.NameValuePlug( "a", 10 ) )

		layerFileName, compositionFileName = self.__writeLayerAndComposition( parent["out"], primitiveVariables["out"] )

		reader = GafferScene.SceneReader()
		reader["fileName"].setValue( compositionFileName )
		self.assertScenesEqual( primitiveVariables["out"], reader["out"], checks = self.allSceneChecks - { "sets" } )

if __name__ == "__main__":
	unittest.main()
