##########################################################################
#
#  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

import ctypes
import unittest

import arnold

import IECore
import IECoreArnold

import GafferTest
import GafferScene

class RendererTest( GafferTest.TestCase ) :

	def testFactory( self ) :

		self.assertTrue( "IECoreArnold::Renderer" in GafferScene.Private.IECoreScenePreview.Renderer.types() )

		r = GafferScene.Private.IECoreScenePreview.Renderer.create( "IECoreArnold::Renderer" )
		self.assertTrue( isinstance( r, GafferScene.Private.IECoreScenePreview.Renderer ) )

	def testSceneDescription( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"IECoreArnold::Renderer",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			self.temporaryDirectory() + "/test.ass"
		)

		o = r.object(
			"testPlane",
			IECore.MeshPrimitive.createPlane( IECore.Box2f( IECore.V2f( -1 ), IECore.V2f( 1 ) ) ),
			r.attributes( IECore.CompoundObject() ),
		)
		o.transform( IECore.M44f().translate( IECore.V3f( 1, 2, 3 ) ) )

		r.render()
		del r

		with IECoreArnold.UniverseBlock() :

			arnold.AiASSLoad( self.temporaryDirectory() + "/test.ass" )

			n = arnold.AiNodeLookUpByName( "testPlane" )
			self.assertTrue( arnold.AiNodeEntryGetType( arnold.AiNodeGetNodeEntry( n ) ), arnold.AI_NODE_SHAPE )

	def testRenderRegion( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"IECoreArnold::Renderer",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			self.temporaryDirectory() + "/test.ass"
		)

		r.camera(
			"testCamera",
			IECore.Camera(
				parameters = {
					"resolution" : IECore.V2i( 2000, 1000 ),
					"renderRegion" : IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( 1999, 749 ) ),
				}
			),
			r.attributes( IECore.CompoundObject() )
		)

		r.option( "camera", IECore.StringData( "testCamera" ) )

		r.render()
		del r

		with IECoreArnold.UniverseBlock() :

			arnold.AiASSLoad( self.temporaryDirectory() + "/test.ass" )
			options = arnold.AiUniverseGetOptions()

			self.assertEqual( arnold.AiNodeGetInt( options, "xres" ), 2000 )
			self.assertEqual( arnold.AiNodeGetInt( options, "yres" ), 1000 )

			self.assertEqual( arnold.AiNodeGetInt( options, "region_min_x" ), 0 )
			self.assertEqual( arnold.AiNodeGetInt( options, "region_min_y" ), 0 )
			self.assertEqual( arnold.AiNodeGetInt( options, "region_max_x" ), 1999 )
			self.assertEqual( arnold.AiNodeGetInt( options, "region_max_y" ), 749 )

	def testShaderReuse( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"IECoreArnold::Renderer",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			self.temporaryDirectory() + "/test.ass"
		)

		for i in range( 0, 10 ) :

			a = IECore.CompoundObject( {
				"ai:surface" : IECore.ObjectVector( [ IECore.Shader( "flat" ) ] ),
			} )

			r.object(
				"testPlane%d" % i,
				IECore.MeshPrimitive.createPlane( IECore.Box2f( IECore.V2f( -1 ), IECore.V2f( 1 ) ) ),
				# We keep specifying the same shader, but we'd like the renderer
				# to be frugal and reuse a single arnold shader on the other side.
				r.attributes( a )
			)

		r.render()
		del r

		with IECoreArnold.UniverseBlock() :

			arnold.AiASSLoad( self.temporaryDirectory() + "/test.ass" )
			self.assertEqual( len( self.__allNodes( type = arnold.AI_NODE_SHADER ) ), 1 )

	def testShaderGarbageCollection( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"IECoreArnold::Renderer",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			self.temporaryDirectory() + "/test.ass"
		)

		o = r.object(
			"testPlane",
			IECore.MeshPrimitive.createPlane( IECore.Box2f( IECore.V2f( -1 ), IECore.V2f( 1 ) ) ),
			r.attributes( IECore.CompoundObject() )
		)

		# Replace the shader a few times.
		for shader in ( "utility", "flat", "standard" ) :
			a = IECore.CompoundObject( {
				"ai:surface" : IECore.ObjectVector( [ IECore.Shader( shader ) ] ),
			} )
			o.attributes( r.attributes( a ) )

		del o, a
		r.render()
		del r

		with IECoreArnold.UniverseBlock() :

			arnold.AiASSLoad( self.temporaryDirectory() + "/test.ass" )
			# We only want one shader to have been saved, because only one was genuinely used.
			self.assertEqual( len( self.__allNodes( type = arnold.AI_NODE_SHADER ) ), 1 )

	def testShaderNames( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"IECoreArnold::Renderer",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			self.temporaryDirectory() + "/test.ass"
		)

		shader1 = IECore.ObjectVector( [
			IECore.Shader( "noise", parameters = { "__handle" : "myHandle" } ),
			IECore.Shader( "flat", parameters = { "color" : "link:myHandle" } ),
		] )

		r.object(
			"testPlane1",
			IECore.MeshPrimitive.createPlane( IECore.Box2f( IECore.V2f( -1 ), IECore.V2f( 1 ) ) ),
			r.attributes(
				IECore.CompoundObject( {
					"ai:surface" : shader1
				} )
			)
		)

		shader2 = IECore.ObjectVector( [
			IECore.Shader( "noise", parameters = { "__handle" : "myHandle" } ),
			IECore.Shader( "standard", parameters = { "Kd_color" : "link:myHandle" } ),
		] )

		r.object(
			"testPlane2",
			IECore.MeshPrimitive.createPlane( IECore.Box2f( IECore.V2f( -1 ), IECore.V2f( 1 ) ) ),
			r.attributes(
				IECore.CompoundObject( {
					"ai:surface" : shader2
				} )
			)
		)

		r.render()
		del r

		with IECoreArnold.UniverseBlock() :

			arnold.AiASSLoad( self.temporaryDirectory() + "/test.ass" )

			shaders = self.__allNodes( type = arnold.AI_NODE_SHADER )
			self.assertEqual( len( shaders ), 4 )
			self.assertEqual( len( set( [ arnold.AiNodeGetName( s ) for s in shaders ] ) ), 4 )

	def testLightNames( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"IECoreArnold::Renderer",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			self.temporaryDirectory() + "/test.ass"
		)

		lightShader = IECore.ObjectVector( [ IECore.Shader( "point_light", "ai:light" ), ] )
		r.light(
			"testLight",
			None,
			r.attributes(
				IECore.CompoundObject( {
					"ai:light" : lightShader
				} )
			)
		)

		r.render()
		del r

		with IECoreArnold.UniverseBlock() :

			arnold.AiASSLoad( self.temporaryDirectory() + "/test.ass" )

			lights = self.__allNodes( type = arnold.AI_NODE_LIGHT )
			self.assertEqual( len( lights ), 1 )
			self.assertEqual( "light:testLight", arnold.AiNodeGetName( lights[0] ) )

	def testSharedLightAttributes( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"IECoreArnold::Renderer",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			self.temporaryDirectory() + "/test.ass"
		)

		lightShader = IECore.ObjectVector( [ IECore.Shader( "point_light", "ai:light" ), ] )
		lightAttributes = r.attributes(
			IECore.CompoundObject( {
				"ai:light" : lightShader
			} )
		)

		r.light( "testLight1", None, lightAttributes )
		r.light( "testLight2", None, lightAttributes )

		del lightAttributes
		r.render()
		del r

		with IECoreArnold.UniverseBlock() :

			arnold.AiASSLoad( self.temporaryDirectory() + "/test.ass" )

			lights = self.__allNodes( type = arnold.AI_NODE_LIGHT )
			self.assertEqual( len( lights ), 2 )
			self.assertEqual( set( [ arnold.AiNodeGetName( l ) for l in lights ] ), { "light:testLight1", "light:testLight2" } )

	def testAttributes( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"IECoreArnold::Renderer",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			self.temporaryDirectory() + "/test.ass"
		)

		r.object(
			"testMesh1",
			IECore.MeshPrimitive.createPlane( IECore.Box2f( IECore.V2f( -1 ), IECore.V2f( 1 ) ) ),
			r.attributes( IECore.CompoundObject( {
				"doubleSided" : IECore.BoolData( True ),
				"ai:visibility:camera" : IECore.BoolData( False ),
				"ai:visibility:shadow" : IECore.BoolData( True ),
				"ai:visibility:reflected" : IECore.BoolData( False ),
				"ai:visibility:refracted" : IECore.BoolData( True ),
				"ai:visibility:diffuse" : IECore.BoolData( False ),
				"ai:visibility:glossy" : IECore.BoolData( True ),
				"ai:receive_shadows" : IECore.BoolData( True ),
				"ai:self_shadows" : IECore.BoolData( True ),
				"ai:matte" : IECore.BoolData( True ),
				"ai:opaque" : IECore.BoolData( True ),
			} ) ),
		)

		r.object(
			"testMesh2",
			IECore.MeshPrimitive.createPlane( IECore.Box2f( IECore.V2f( -1 ), IECore.V2f( 1 ) ) ),
			r.attributes( IECore.CompoundObject( {
				"doubleSided" : IECore.BoolData( False ),
				"ai:visibility:camera" : IECore.BoolData( True ),
				"ai:visibility:shadow" : IECore.BoolData( False ),
				"ai:visibility:reflected" : IECore.BoolData( True ),
				"ai:visibility:refracted" : IECore.BoolData( False ),
				"ai:visibility:diffuse" : IECore.BoolData( True ),
				"ai:visibility:glossy" : IECore.BoolData( False ),
				"ai:receive_shadows" : IECore.BoolData( False ),
				"ai:self_shadows" : IECore.BoolData( False ),
				"ai:matte" : IECore.BoolData( False ),
				"ai:opaque" : IECore.BoolData( False ),
			} ) ),
		)

		r.object(
			"testMesh3",
			IECore.MeshPrimitive.createPlane( IECore.Box2f( IECore.V2f( -1 ), IECore.V2f( 1 ) ) ),
			r.attributes( IECore.CompoundObject() ),
		)

		r.render()
		del r

		with IECoreArnold.UniverseBlock() :

			arnold.AiASSLoad( self.temporaryDirectory() + "/test.ass" )

			o1 = arnold.AiNodeLookUpByName( "testMesh1" )
			o2 = arnold.AiNodeLookUpByName( "testMesh2" )
			o3 = arnold.AiNodeLookUpByName( "testMesh3" )

			self.assertEqual( arnold.AiNodeGetByte( o1, "sidedness" ), arnold.AI_RAY_ALL )
			self.assertEqual( arnold.AiNodeGetByte( o2, "sidedness" ), arnold.AI_RAY_UNDEFINED )
			self.assertEqual( arnold.AiNodeGetByte( o3, "sidedness" ), arnold.AI_RAY_ALL )

			self.assertEqual(
				arnold.AiNodeGetByte( o1, "visibility" ),
				arnold.AI_RAY_ALL & ~( arnold.AI_RAY_CAMERA | arnold.AI_RAY_REFLECTED | arnold.AI_RAY_DIFFUSE )
			)
			self.assertEqual(
				arnold.AiNodeGetByte( o2, "visibility" ),
				arnold.AI_RAY_ALL & ~( arnold.AI_RAY_SHADOW | arnold.AI_RAY_REFRACTED | arnold.AI_RAY_GLOSSY )
			)
			self.assertEqual(
				arnold.AiNodeGetByte( o3, "visibility" ),
				arnold.AI_RAY_ALL
			)

			for p in ( "receive_shadows", "self_shadows", "matte", "opaque" ) :
				self.assertEqual( arnold.AiNodeGetBool( o1, p ), True )
				self.assertEqual( arnold.AiNodeGetBool( o2, p ), False )
				self.assertEqual( arnold.AiNodeGetBool( o3, p ), p != "matte" )

	def testOutputFilters( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"IECoreArnold::Renderer",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			self.temporaryDirectory() + "/test.ass"
		)

		r.output(
			"test",
			IECore.Display(
				"beauty.exr",
				"exr",
				"rgba",
				{
					"filter" : "gaussian",
					"filterwidth" : IECore.V2f( 3.5 ),
				}
			)
		)

		r.render()
		del r

		with IECoreArnold.UniverseBlock() :

			arnold.AiASSLoad( self.temporaryDirectory() + "/test.ass" )
			filters = self.__allNodes( type = arnold.AI_NODE_FILTER )
			self.assertEqual( len( filters ), 1 )
			f = filters[0]

			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( f ) ), "gaussian_filter" )
			self.assertEqual( arnold.AiNodeGetFlt( f, "width" ), 3.5 )

	def testInstancing( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"IECoreArnold::Renderer",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			self.temporaryDirectory() + "/test.ass"
		)

		polyPlane = IECore.MeshPrimitive.createPlane( IECore.Box2f( IECore.V2f( -1 ), IECore.V2f( 1 ) ) )
		subdivPlane = polyPlane.copy()
		subdivPlane.interpolation = "catmullClark"

		defaultAttributes = r.attributes( IECore.CompoundObject() )
		adaptiveAttributes = r.attributes(
			IECore.CompoundObject( {
				"ai:polymesh:subdiv_adaptive_error" : IECore.FloatData( 0.1 ),
			} )
		)
		nonAdaptiveAttributes = r.attributes(
			IECore.CompoundObject( {
				"ai:polymesh:subdiv_adaptive_error" : IECore.FloatData( 0 ),
			} )
		)
		adaptiveObjectSpaceAttributes = r.attributes(
			IECore.CompoundObject( {
				"ai:polymesh:subdiv_adaptive_error" : IECore.FloatData( 0.1 ),
				"ai:polymesh:subdiv_adaptive_space" : IECore.StringData( "object" ),
			} )
		)

		# We should be able to automatically instance polygon meshes
		# regardless of the subdivision settings, because they're
		# irrelevant.

		r.object( "polyDefaultAttributes1", polyPlane.copy(), defaultAttributes )
		r.object( "polyDefaultAttributes2", polyPlane.copy(), defaultAttributes )

		r.object( "polyAdaptiveAttributes1", polyPlane.copy(), adaptiveAttributes )
		r.object( "polyAdaptiveAttributes2", polyPlane.copy(), adaptiveAttributes )

		# And we should be able to instance subdiv meshes with
		# non-adaptive subdivision.

		r.object( "subdivDefaultAttributes1", subdivPlane.copy(), defaultAttributes )
		r.object( "subdivDefaultAttributes2", subdivPlane.copy(), defaultAttributes )

		r.object( "subdivNonAdaptiveAttributes1", subdivPlane.copy(), nonAdaptiveAttributes )
		r.object( "subdivNonAdaptiveAttributes2", subdivPlane.copy(), nonAdaptiveAttributes )

		# But if adaptive subdivision is enabled, we can't, because the
		# mesh can't be subdivided appropriately for both instances.

		r.object( "subdivAdaptiveAttributes1", subdivPlane.copy(), adaptiveAttributes )
		r.object( "subdivAdaptiveAttributes2", subdivPlane.copy(), adaptiveAttributes )

		# Although we should be able to if the adaptive space is "object".

		r.object( "subdivAdaptiveObjectSpaceAttributes1", subdivPlane.copy(), adaptiveObjectSpaceAttributes )
		r.object( "subdivAdaptiveObjectSpaceAttributes2", subdivPlane.copy(), adaptiveObjectSpaceAttributes )

		r.render()
		del r

		def assertInstanced( *names ) :

			firstInstanceNode = arnold.AiNodeLookUpByName( names[0] )
			for name in names :

				instanceNode = arnold.AiNodeLookUpByName( name )
				self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( instanceNode ) ), "ginstance" )

				nodePtr = arnold.AiNodeGetPtr( instanceNode, "node" )
				self.assertEqual( nodePtr, arnold.AiNodeGetPtr( firstInstanceNode, "node" ) )
				self.assertEqual( arnold.AiNodeGetInt( arnold.AtNode.from_address( nodePtr ), "visibility" ), 0 )

		def assertNotInstanced( *names ) :

			for name in names :
				node = arnold.AiNodeLookUpByName( name )
				self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( node ) ), "polymesh" )

		with IECoreArnold.UniverseBlock() :

			arnold.AiASSLoad( self.temporaryDirectory() + "/test.ass" )

			shapes = self.__allNodes( type = arnold.AI_NODE_SHAPE )
			numInstances = len( [ s for s in shapes if arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( s ) ) == "ginstance" ] )
			numPolyMeshes = len( [ s for s in shapes if arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( s ) ) == "polymesh" ] )

			self.assertEqual( numPolyMeshes, 5 )
			self.assertEqual( numInstances, 10 )

			assertInstanced(
				"polyDefaultAttributes1",
				"polyDefaultAttributes2",
				"polyAdaptiveAttributes1",
				"polyAdaptiveAttributes2",
			)

			assertInstanced(
				"subdivDefaultAttributes1",
				"subdivDefaultAttributes2",
				"subdivNonAdaptiveAttributes1",
				"subdivNonAdaptiveAttributes2",
			)

			assertNotInstanced(
				"subdivAdaptiveAttributes1",
				"subdivAdaptiveAttributes2"
			)

			assertInstanced(
				"subdivAdaptiveObjectSpaceAttributes1",
				"subdivAdaptiveObjectSpaceAttributes2",
			)

	def testSubdivisionAttributes( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"IECoreArnold::Renderer",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			self.temporaryDirectory() + "/test.ass"
		)

		subdivPlane = IECore.MeshPrimitive.createPlane( IECore.Box2f( IECore.V2f( -1 ), IECore.V2f( 1 ) ) )
		subdivPlane.interpolation = "catmullClark"

		r.object(
			"plane",
			subdivPlane,
			r.attributes(
				IECore.CompoundObject( {
					"ai:polymesh:subdiv_iterations" : IECore.IntData( 10 ),
					"ai:polymesh:subdiv_adaptive_error" : IECore.FloatData( 0.25 ),
					"ai:polymesh:subdiv_adaptive_metric" : IECore.StringData( "edge_length" ),
					"ai:polymesh:subdiv_adaptive_space" : IECore.StringData( "raster" ),
				} )
			)
		)

		r.render()
		del r

		with IECoreArnold.UniverseBlock() :

			arnold.AiASSLoad( self.temporaryDirectory() + "/test.ass" )
			node = arnold.AiNodeLookUpByName( "plane" )
			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( node ) ), "polymesh" )
			self.assertEqual( arnold.AiNodeGetInt( node, "subdiv_iterations" ), 10 )
			self.assertEqual( arnold.AiNodeGetFlt( node, "subdiv_adaptive_error" ), 0.25 )
			self.assertEqual( arnold.AiNodeGetStr( node, "subdiv_adaptive_metric" ), "edge_length" )
			self.assertEqual( arnold.AiNodeGetStr( node, "subdiv_adaptive_space" ), "raster" )

	def testUserAttributes( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"IECoreArnold::Renderer",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			self.temporaryDirectory() + "/test.ass"
		)

		r.object(
			"plane1",
			IECore.MeshPrimitive.createPlane( IECore.Box2f( IECore.V2f( -1 ), IECore.V2f( 1 ) ) ),
			r.attributes(
				IECore.CompoundObject( {
					"user:testInt" : IECore.IntData( 1 ),
					"user:testFloat" : IECore.FloatData( 2.5 ),
					"user:testV3f" : IECore.V3fData( IECore.V3f( 1, 2, 3 ) ),
					"user:testColor3f" : IECore.Color3fData( IECore.Color3f( 4, 5, 6 ) ),
					"user:testString" : IECore.StringData( "we're all doomed" ),
				} )
			)
		)

		r.object(
			"plane2",
			IECore.MeshPrimitive.createPlane( IECore.Box2f( IECore.V2f( -1 ), IECore.V2f( 1 ) ) ),
			r.attributes(
				IECore.CompoundObject( {
					"user:testInt" : IECore.IntData( 2 ),
					"user:testFloat" : IECore.FloatData( 25 ),
					"user:testV3f" : IECore.V3fData( IECore.V3f( 0, 1, 0 ) ),
					"user:testColor3f" : IECore.Color3fData( IECore.Color3f( 1, 0.5, 0 ) ),
					"user:testString" : IECore.StringData( "indeed" ),
				} )
			)
		)

		r.render()
		del r

		with IECoreArnold.UniverseBlock() :

			arnold.AiASSLoad( self.temporaryDirectory() + "/test.ass" )

			plane1 = arnold.AiNodeLookUpByName( "plane1" )
			self.assertEqual( arnold.AiNodeGetInt( plane1, "user:testInt" ), 1 )
			self.assertEqual( arnold.AiNodeGetFlt( plane1, "user:testFloat" ), 2.5 )
			self.assertEqual( arnold.AiNodeGetVec( plane1, "user:testV3f" ), arnold.AtVector( 1, 2, 3 ) )
			self.assertEqual( arnold.AiNodeGetRGB( plane1, "user:testColor3f" ), arnold.AtRGB( 4, 5, 6 ) )
			self.assertEqual( arnold.AiNodeGetStr( plane1, "user:testString" ), "we're all doomed" )

			plane2 = arnold.AiNodeLookUpByName( "plane2" )
			self.assertEqual( arnold.AiNodeGetInt( plane2, "user:testInt" ), 2 )
			self.assertEqual( arnold.AiNodeGetFlt( plane2, "user:testFloat" ), 25 )
			self.assertEqual( arnold.AiNodeGetVec( plane2, "user:testV3f" ), arnold.AtVector( 0, 1, 0 ) )
			self.assertEqual( arnold.AiNodeGetRGB( plane2, "user:testColor3f" ), arnold.AtRGB( 1, 0.5, 0 ) )
			self.assertEqual( arnold.AiNodeGetStr( plane2, "user:testString" ), "indeed" )

	def testDisplacementAttributes( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"IECoreArnold::Renderer",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			self.temporaryDirectory() + "/test.ass"
		)

		plane = IECore.MeshPrimitive.createPlane( IECore.Box2f( IECore.V2f( -1 ), IECore.V2f( 1 ) ) )
		noise = IECore.ObjectVector( [ IECore.Shader( "noise", "ai:displacement", {} ) ] )

		sharedAttributes = r.attributes(
			IECore.CompoundObject( {
				"ai:disp_map" : noise,
				"ai:disp_height" : IECore.FloatData( 0.25 ),
				"ai:disp_padding" : IECore.FloatData( 2.5 ),
				"ai:disp_zero_value" : IECore.FloatData( 0.5 ),
				"ai:disp_autobump" : IECore.BoolData( True ),
			} )
		)

		r.object( "plane1", plane, sharedAttributes )
		r.object( "plane2", plane, sharedAttributes )

		r.object(
			"plane3",
			plane,
			r.attributes(
				IECore.CompoundObject( {
					"ai:disp_map" : noise,
					"ai:disp_height" : IECore.FloatData( 0.5 ),
					"ai:disp_padding" : IECore.FloatData( 5.0 ),
					"ai:disp_zero_value" : IECore.FloatData( 0.0 ),
					"ai:disp_autobump" : IECore.BoolData( True ),
				} )
			)
		)

		r.render()
		del r

		with IECoreArnold.UniverseBlock() :

			arnold.AiASSLoad( self.temporaryDirectory() + "/test.ass" )

			shapes = self.__allNodes( type = arnold.AI_NODE_SHAPE )
			self.assertEqual( len( shapes ), 5 )

			plane1 = arnold.AiNodeLookUpByName( "plane1" )
			plane2 = arnold.AiNodeLookUpByName( "plane2" )
			plane3 = arnold.AiNodeLookUpByName( "plane3" )

			self.assertTrue( arnold.AiNodeIs( plane1, "ginstance" ) )
			self.assertTrue( arnold.AiNodeIs( plane2, "ginstance" ) )
			self.assertTrue( arnold.AiNodeIs( plane3, "ginstance" ) )

			self.assertEqual( arnold.AiNodeGetPtr( plane1, "node" ), arnold.AiNodeGetPtr( plane2, "node" ) )
			self.assertNotEqual( arnold.AiNodeGetPtr( plane2, "node" ), arnold.AiNodeGetPtr( plane3, "node" ) )

			polymesh1 = arnold.AtNode.from_address( arnold.AiNodeGetPtr( plane1, "node" ) )
			polymesh2 = arnold.AtNode.from_address( arnold.AiNodeGetPtr( plane3, "node" ) )

			self.assertTrue( arnold.AiNodeIs( polymesh1, "polymesh" ) )
			self.assertTrue( arnold.AiNodeIs( polymesh2, "polymesh" ) )

			self.assertEqual( arnold.AiNodeGetPtr( polymesh1, "disp_map" ), arnold.AiNodeGetPtr( polymesh2, "disp_map" ) )
			self.assertEqual( arnold.AiNodeGetFlt( polymesh1, "disp_height" ), 0.25 )
			self.assertEqual( arnold.AiNodeGetFlt( polymesh2, "disp_height" ), 0.5 )
			self.assertEqual( arnold.AiNodeGetFlt( polymesh1, "disp_padding" ), 2.5 )
			self.assertEqual( arnold.AiNodeGetFlt( polymesh2, "disp_padding" ), 5.0 )
			self.assertEqual( arnold.AiNodeGetFlt( polymesh1, "disp_zero_value" ), 0.5 )
			self.assertEqual( arnold.AiNodeGetFlt( polymesh2, "disp_zero_value" ), 0.0 )
			self.assertEqual( arnold.AiNodeGetBool( polymesh1, "disp_autobump" ), True )
			self.assertEqual( arnold.AiNodeGetBool( polymesh2, "disp_autobump" ), True )

	def testSubdividePolygonsAttribute( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"IECoreArnold::Renderer",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			self.temporaryDirectory() + "/test.ass"
		)

		meshes = {}
		meshes["linear"] = IECore.MeshPrimitive.createPlane( IECore.Box2f( IECore.V2f( -1 ), IECore.V2f( 1 ) ) )
		meshes["catmullClark"] = meshes["linear"].copy()
		meshes["catmullClark"].interpolation = "catmullClark"

		attributes = {}
		for t in ( None, False, True ) :
			a = IECore.CompoundObject()
			if t is not None :
				a["ai:polymesh:subdividePolygons"] = IECore.BoolData( t )
			attributes[t] = r.attributes( a )

		for interpolation in meshes.keys() :
			for subdividePolygons in attributes.keys() :
				r.object( interpolation + "-" + str( subdividePolygons ), meshes[interpolation], attributes[subdividePolygons] )

		r.render()
		del r

		with IECoreArnold.UniverseBlock() :

			arnold.AiASSLoad( self.temporaryDirectory() + "/test.ass" )

			for interpolation in meshes.keys() :
				for subdividePolygons in attributes.keys() :

					instance = arnold.AiNodeLookUpByName( interpolation + "-" + str( subdividePolygons ) )
					self.assertTrue( arnold.AiNodeIs( instance, "ginstance" ) )

					mesh = arnold.AtNode.from_address( arnold.AiNodeGetPtr( instance, "node" ) )
					self.assertTrue( arnold.AiNodeIs( mesh, "polymesh" ) )

					if subdividePolygons and interpolation == "linear" :
						self.assertEqual( arnold.AiNodeGetStr( mesh, "subdiv_type" ), "linear" )
					else :
						self.assertEqual( arnold.AiNodeGetStr( mesh, "subdiv_type" ), "catclark" if interpolation == "catmullClark" else "none" )

	def testMeshLight( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"IECoreArnold::Renderer",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			self.temporaryDirectory() + "/test.ass"
		)

		l = r.light(
			"myLight",
			IECore.MeshPrimitive.createPlane( IECore.Box2f( IECore.V2f( -1 ), IECore.V2f( 1 ) ) ),
			r.attributes(
				IECore.CompoundObject( {
					"ai:light" : IECore.ObjectVector( [ IECore.Shader( "mesh_light", "ai:light" ), ] )
				} )
			)
		)
		del l

		r.render()
		del r

		with IECoreArnold.UniverseBlock() :

			arnold.AiASSLoad( self.temporaryDirectory() + "/test.ass" )

			shapes = self.__allNodes( type = arnold.AI_NODE_SHAPE )
			self.assertEqual( len( shapes ), 2 )

			instance = arnold.AiNodeLookUpByName( "myLight" )
			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( instance ) ), "ginstance" )
			mesh = arnold.AtNode.from_address( arnold.AiNodeGetPtr( instance, "node" ) )
			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( mesh ) ), "polymesh" )

			lights = self.__allNodes( type = arnold.AI_NODE_LIGHT )
			self.assertEqual( len( lights ), 1 )
			light = lights[0]
			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( light ) ), "mesh_light" )
			self.assertEqual( arnold.AiNodeGetPtr( light, "mesh" ), ctypes.addressof( instance.contents ) )

	def testMeshLightsWithSharedShaders( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"IECoreArnold::Renderer",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			self.temporaryDirectory() + "/test.ass"
		)

		lightShaderNetwork = IECore.ObjectVector( [
			IECore.Shader( "flat", "ai:shader", { "__handle" : "colorHandle" } ),
			IECore.Shader( "mesh_light", "ai:light", { "color" : "link:colorHandle" } ),
		] )

		l1 = r.light(
			"myLight1",
			IECore.MeshPrimitive.createPlane( IECore.Box2f( IECore.V2f( -1 ), IECore.V2f( 1 ) ) ),
			r.attributes( IECore.CompoundObject( {
				"ai:light" : lightShaderNetwork,
			} ) )
		)
		del l1

		l2 = r.light(
			"myLight2",
			IECore.MeshPrimitive.createPlane( IECore.Box2f( IECore.V2f( -1 ), IECore.V2f( 1 ) ) ),
			r.attributes( IECore.CompoundObject( {
				"ai:light" : lightShaderNetwork,
			} ) )
		)
		del l2

		r.render()
		del r

		with IECoreArnold.UniverseBlock() :

			arnold.AiASSLoad( self.temporaryDirectory() + "/test.ass" )

			shapes = self.__allNodes( type = arnold.AI_NODE_SHAPE )
			self.assertEqual( len( shapes ), 3 )

			instance1 = arnold.AiNodeLookUpByName( "myLight1" )
			instance2 = arnold.AiNodeLookUpByName( "myLight2" )
			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( instance1 ) ), "ginstance" )
			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( instance2 ) ), "ginstance" )

			self.assertEqual( arnold.AiNodeGetPtr( instance1, "node" ), arnold.AiNodeGetPtr( instance2, "node" ) )

			mesh = arnold.AtNode.from_address( arnold.AiNodeGetPtr( instance1, "node" ) )
			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( mesh ) ), "polymesh" )

			lights = self.__allNodes( type = arnold.AI_NODE_LIGHT )
			self.assertEqual( len( lights ), 2 )

			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( lights[0] ) ), "mesh_light" )
			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( lights[1] ) ), "mesh_light" )

			flat1 = arnold.AiNodeGetLink( lights[0], "color" )
			flat2 = arnold.AiNodeGetLink( lights[1], "color" )

			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( flat1 ) ), "flat" )
			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( flat2 ) ), "flat" )

	def __allNodes( self, type = arnold.AI_NODE_ALL, ignoreBuiltIn = True ) :

		result = []
		i = arnold.AiUniverseGetNodeIterator( type )
		while not arnold.AiNodeIteratorFinished( i ) :
			node = arnold.AiNodeIteratorGetNext( i )
			if ignoreBuiltIn and arnold.AiNodeGetName( node ) in ( "root", "ai_default_reflection_shader" ) :
				continue
			result.append( node )

		return result

if __name__ == "__main__":
	unittest.main()
