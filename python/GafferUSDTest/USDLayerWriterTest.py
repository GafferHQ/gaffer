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

import os
import unittest

import pxr.Usd

import IECore
import IECoreScene

import GafferUSD
import GafferScene
import GafferSceneTest

class USDLayerWriterTest( GafferSceneTest.SceneTestCase ) :

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

		sceneWriter = GafferScene.SceneWriter()
		sceneWriter["in"].setInput( group["out"] )
		sceneWriter["fileName"].setValue( os.path.join( self.temporaryDirectory(), "base.usda" ) )
		sceneWriter["task"].execute()

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

		# Write the differences to a new USD layer.

		layerWriter = GafferUSD.USDLayerWriter()
		layerWriter["base"].setInput( group["out"] )
		layerWriter["layer"].setInput( prune["out"] )
		layerWriter["fileName"].setValue( os.path.join( self.temporaryDirectory(), "layer.usda" ) )
		layerWriter["task"].execute()

		# Compose the layer with the original scene using the USD
		# API, and write the composition to a new file.

		compositionFileName = os.path.join( self.temporaryDirectory(), "composed.usda" )
		composition = pxr.Usd.Stage.CreateNew( compositionFileName )
		composition.GetRootLayer().subLayerPaths = [
			layerWriter["fileName"].getValue(),
			sceneWriter["fileName"].getValue(),
		]
		composition.GetRootLayer().Save()

		# The composed result should be identical to the Gaffer scene.

		reader = GafferScene.SceneReader()
		reader["fileName"].setValue( compositionFileName )
		self.assertScenesEqual( reader["out"], layerWriter["layer"], checks = self.allSceneChecks - { "sets" } )

		# Check that we've actually got a minimal set of opinions in the
		# layer. We could pass the tests above just by writing
		# _everything_!

		layer = pxr.Sdf.Layer.OpenAsAnonymous( layerWriter["fileName"].getValue() )

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
		writer["fileName"].setValue( os.path.join( self.temporaryDirectory(), "subdir", "test.usda" ) )

		writer["task"].execute()
		self.assertTrue( os.path.isfile( writer["fileName"].getValue() ) )

if __name__ == "__main__":
	unittest.main()
