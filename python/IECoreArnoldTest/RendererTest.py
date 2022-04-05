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
import json
import os
import sys
import time
import unittest

import arnold
import imath

import IECore
import IECoreScene
import IECoreImage
import IECoreArnold

import GafferTest
import GafferScene

class RendererTest( GafferTest.TestCase ) :

	def assertReferSameNode( self, a, b ):
		self.assertEqual( arnold.addressof( a.contents ), arnold.addressof( b.contents ) )

	def assertReferDifferentNode( self, a, b ):
		self.assertNotEqual( arnold.addressof( a.contents ), arnold.addressof( b.contents ) )

	def testFactory( self ) :

		self.assertTrue( "Arnold" in GafferScene.Private.IECoreScenePreview.Renderer.types() )

		r = GafferScene.Private.IECoreScenePreview.Renderer.create( "Arnold" )
		self.assertTrue( isinstance( r, GafferScene.Private.IECoreScenePreview.Renderer ) )
		self.assertEqual( r.name(), "Arnold" )

	def testSceneDescription( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Arnold",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			self.temporaryDirectory() + "/test.ass"
		)

		o = r.object(
			"testPlane",
			IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) ),
			r.attributes( IECore.CompoundObject() ),
		)
		o.transform( imath.M44f().translate( imath.V3f( 1, 2, 3 ) ) )
		del o

		r.render()
		del r

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			arnold.AiSceneLoad( universe, self.temporaryDirectory() + "/test.ass", None )

			n = arnold.AiNodeLookUpByName( universe, "testPlane" )
			self.assertTrue( arnold.AiNodeEntryGetType( arnold.AiNodeGetNodeEntry( n ) ), arnold.AI_NODE_SHAPE )

	def testRenderRegion( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Arnold",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			self.temporaryDirectory() + "/test.ass"
		)

		r.camera(
			"testCamera",
			IECoreScene.Camera(
				parameters = {
					"resolution" : imath.V2i( 2000, 1000 ),
					"cropWindow" : imath.Box2f( imath.V2f( 0 ), imath.V2f( 1, 0.75 ) ),
				}
			),
			r.attributes( IECore.CompoundObject() )
		)

		r.option( "camera", IECore.StringData( "testCamera" ) )

		r.render()
		del r

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			arnold.AiSceneLoad( universe, self.temporaryDirectory() + "/test.ass", None )
			options = arnold.AiUniverseGetOptions( universe )

			self.assertEqual( arnold.AiNodeGetInt( options, "xres" ), 2000 )
			self.assertEqual( arnold.AiNodeGetInt( options, "yres" ), 1000 )

			self.assertEqual( arnold.AiNodeGetInt( options, "region_min_x" ), 0 )
			self.assertEqual( arnold.AiNodeGetInt( options, "region_min_y" ), 0 )
			self.assertEqual( arnold.AiNodeGetInt( options, "region_max_x" ), 1999 )
			self.assertEqual( arnold.AiNodeGetInt( options, "region_max_y" ), 749 )

	def testShaderReuse( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Arnold",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			self.temporaryDirectory() + "/test.ass"
		)

		for i in range( 0, 10 ) :

			a = IECore.CompoundObject( {
				"ai:surface" : IECoreScene.ShaderNetwork( { "output" : IECoreScene.Shader( "flat" ) }, output = "output" ),
			} )

			r.object(
				"testPlane%d" % i,
				IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) ),
				# We keep specifying the same shader, but we'd like the renderer
				# to be frugal and reuse a single arnold shader on the other side.
				r.attributes( a )
			)

		r.render()
		del r

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			arnold.AiSceneLoad( universe, self.temporaryDirectory() + "/test.ass", None )
			self.assertEqual( len( self.__allNodes( universe, type = arnold.AI_NODE_SHADER ) ), 1 )

	def testShaderGarbageCollection( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Arnold",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Interactive,
		)

		r.output(
			"test",
			IECoreScene.Output(
				self.temporaryDirectory() + "/beauty.exr",
				"exr",
				"rgba",
				{
				}
			)
		)

		o = r.object(
			"testPlane",
			IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) ),
			r.attributes( IECore.CompoundObject() )
		)

		# Replace the shader a few times.
		for shader in ( "utility", "flat", "standard_surface" ) :
			a = IECore.CompoundObject( {
				"ai:surface" : IECoreScene.ShaderNetwork( { "output" : IECoreScene.Shader( shader ) }, output = "output" ),
			} )
			o.attributes( r.attributes( a ) )
			del a

		r.render()
		universe = ctypes.cast( r.command( "ai:queryUniverse", {} ), ctypes.POINTER( arnold.AtUniverse ) )
		self.assertEqual( len( self.__allNodes( universe, type = arnold.AI_NODE_SHADER ) ), 1 )

		del o
		del r

	def testShaderNames( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Arnold",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			self.temporaryDirectory() + "/test.ass"
		)

		shader1 = IECoreScene.ShaderNetwork(
			shaders = {
				"myHandle" : IECoreScene.Shader( "noise" ),
				"flat" : IECoreScene.Shader( "flat" ),
			},
			connections = [
				( ( "myHandle", "" ), ( "flat", "color" ) ),
			],
			output = "flat"
		)

		r.object(
			"testPlane1",
			IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) ),
			r.attributes(
				IECore.CompoundObject( {
					"ai:surface" : shader1
				} )
			)
		)

		shader2 = IECoreScene.ShaderNetwork(
			shaders = {
				"myHandle" : IECoreScene.Shader( "noise" ),
				"standard_surface" : IECoreScene.Shader( "standard_surface" ),
			},
			connections = [
				( ( "myHandle", "" ), ( "standard_surface", "base_color" ) ),
			],
			output = "standard_surface"
		)

		r.object(
			"testPlane2",
			IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) ),
			r.attributes(
				IECore.CompoundObject( {
					"ai:surface" : shader2
				} )
			)
		)

		r.render()
		del r

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			arnold.AiSceneLoad( universe, self.temporaryDirectory() + "/test.ass", None )

			shaders = self.__allNodes( universe, type = arnold.AI_NODE_SHADER )
			self.assertEqual( len( shaders ), 4 )
			shaderNames = [ arnold.AiNodeGetName( s ) for s in shaders ]
			self.assertEqual( len( shaderNames ), 4 )
			self.assertEqual( len( [ i for i in shaderNames if i.split(":")[-1] == "myHandle" ] ), 2 )

	def testShaderConnections( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Arnold",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			self.temporaryDirectory() + "/test.ass"
		)

		scalarColorShader = IECoreScene.ShaderNetwork(
			shaders = {
				"scalarColorSource" : IECoreScene.Shader( "image" ),
				"scalarColorTarget" : IECoreScene.Shader( "lambert" ),
			},
			connections = [
				( ( "scalarColorSource", "" ), ( "scalarColorTarget", "Kd_color" ) )
			],
			output = "scalarColorTarget"
		)

		arrayColorShader = IECoreScene.ShaderNetwork(
			shaders = {
				"arrayColorSource" : IECoreScene.Shader( "image" ),
				"arrayColorTarget" : IECoreScene.Shader( "ramp_rgb" ),
			},
			connections = [
				( ( "arrayColorSource", "" ), ( "arrayColorTarget", "color[0]" ) )
			],
			output = "arrayColorTarget"
		)

		for name,s in [ ( "scalarColor", scalarColorShader ), ( "arrayColor", arrayColorShader ) ] :
			r.object(
				"testPlane_%s" % name,
				IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) ),
				r.attributes(
					IECore.CompoundObject( {
						"ai:surface" : s
					} )
				)
			)

		r.render()
		del r

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			arnold.AiSceneLoad( universe, self.temporaryDirectory() + "/test.ass", None )

			target = arnold.AiNodeGetPtr( arnold.AiNodeLookUpByName( universe, "testPlane_scalarColor" ), "shader" )
			source = arnold.AiNodeGetLink( target, "Kd_color" )
			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( source ) ), "image" )

			target = arnold.AiNodeGetPtr( arnold.AiNodeLookUpByName( universe, "testPlane_arrayColor" ), "shader" )
			source = arnold.AiNodeGetLink( target, "color[0]" )
			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( source ) ), "image" )

	def testShaderComponentConnections( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Arnold",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			self.temporaryDirectory() + "/test.ass"
		)

		s = IECoreScene.ShaderNetwork(
			shaders = {
				"source" : IECoreScene.Shader( "image" ),
				"output" : IECoreScene.Shader( "flat" ),
			},
			connections = [
				( ( "source", "r" ), ( "output", "color.g" ) ),
				( ( "source", "g" ), ( "output", "color.b" ) ),
				( ( "source", "b" ), ( "output", "color.r" ) ),
			],
			output = "output"
		)

		r.object(
			"test",
			IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) ),
			r.attributes(
				IECore.CompoundObject( {
					"ai:surface" : s
				} )
			)
		)

		r.render()
		del r

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			arnold.AiSceneLoad( universe, self.temporaryDirectory() + "/test.ass", None )

			outputNode = arnold.AiNodeGetPtr( arnold.AiNodeLookUpByName( universe, "test" ), "shader" )

			componentIndex = ctypes.c_int()
			sourceR = arnold.AiNodeGetLink( outputNode, "color.r", componentIndex )
			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( sourceR ) ), "image" )
			self.assertEqual( componentIndex.value, 2 )

			sourceG = arnold.AiNodeGetLink( outputNode, "color.g", componentIndex )
			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( sourceG ) ), "image" )
			self.assertEqual( componentIndex.value, 0 )

			sourceB = arnold.AiNodeGetLink( outputNode, "color.b", componentIndex )
			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( sourceB ) ), "image" )
			self.assertEqual( componentIndex.value, 1 )

			self.assertReferSameNode( sourceR, sourceG )
			self.assertReferSameNode( sourceR, sourceB )

	def testOSLShaderComponentConnections( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Arnold",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			self.temporaryDirectory() + "/test.ass"
		)

		s = IECoreScene.ShaderNetwork(
			shaders = {
				"source" : IECoreScene.Shader( "Maths/MixColor", "osl:shader" ),
				"output" : IECoreScene.Shader( "Maths/MixColor", "osl:shader" ),
			},
			connections = [
				( ( "source", "out.r" ), ( "output", "a.g" ) ),
				( ( "source", "out.g" ), ( "output", "a.b" ) ),
				( ( "source", "out.b" ), ( "output", "a.r" ) ),
			],
			output = "output"
		)

		r.object(
			"test",
			IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) ),
			r.attributes(
				IECore.CompoundObject( {
					"ai:surface" : s
				} )
			)
		)

		r.render()
		del r

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			arnold.AiSceneLoad( universe, self.temporaryDirectory() + "/test.ass", None )

			outputNode = arnold.AiNodeGetPtr( arnold.AiNodeLookUpByName( universe, "test" ), "shader" )

			pack = arnold.AiNodeGetLink( outputNode, "param_a" )
			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( pack ) ), "osl" )
			self.assertEqual( arnold.AiNodeGetStr( pack, "shadername" ), "MaterialX/mx_pack_color" )

			swizzleR = arnold.AiNodeGetLink( pack, "param_in1" )
			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( swizzleR ) ), "osl" )
			self.assertEqual( arnold.AiNodeGetStr( swizzleR, "shadername" ), "MaterialX/mx_swizzle_color_float" )
			self.assertEqual( arnold.AiNodeGetStr( swizzleR, "param_channels" ), "b" )
			swizzleRSource = arnold.AiNodeGetLink( swizzleR, "param_in" )

			swizzleG = arnold.AiNodeGetLink( pack, "param_in2" )
			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( swizzleG ) ), "osl" )
			self.assertEqual( arnold.AiNodeGetStr( swizzleG, "shadername" ), "MaterialX/mx_swizzle_color_float" )
			self.assertEqual( arnold.AiNodeGetStr( swizzleG, "param_channels" ), "r" )
			swizzleGSource = arnold.AiNodeGetLink( swizzleG, "param_in" )

			swizzleB = arnold.AiNodeGetLink( pack, "param_in3" )
			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( swizzleB ) ), "osl" )
			self.assertEqual( arnold.AiNodeGetStr( swizzleB, "shadername" ), "MaterialX/mx_swizzle_color_float" )
			self.assertEqual( arnold.AiNodeGetStr( swizzleB, "param_channels" ), "g" )
			swizzleBSource = arnold.AiNodeGetLink( swizzleG, "param_in" )

			self.assertReferSameNode( swizzleRSource, swizzleGSource )
			self.assertReferSameNode( swizzleRSource, swizzleBSource )

			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( swizzleRSource ) ), "osl" )
			self.assertEqual( arnold.AiNodeGetStr( swizzleRSource, "shadername" ), "Maths/MixColor" )

	def testLightNames( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Arnold",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			self.temporaryDirectory() + "/test.ass"
		)

		lightShader = IECoreScene.ShaderNetwork( { "light" : IECoreScene.Shader( "point_light", "ai:light" ), }, output = "light" )
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

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			arnold.AiSceneLoad( universe, self.temporaryDirectory() + "/test.ass", None )

			lights = self.__allNodes( universe, type = arnold.AI_NODE_LIGHT )
			self.assertEqual( len( lights ), 1 )
			self.assertEqual( "light:testLight", arnold.AiNodeGetName( lights[0] ) )

	def testLightTransforms( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Arnold",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			self.temporaryDirectory() + "/test.ass"
		)

		lightAttributes = r.attributes(
			IECore.CompoundObject( {
				"ai:light" : IECoreScene.ShaderNetwork( { "light" : IECoreScene.Shader( "point_light", "ai:light" ), }, output = "light" )
			} )
		)

		r.light( "untransformedLight", None, lightAttributes )

		staticLight = r.light( "staticLight", None, lightAttributes )
		staticLight.transform( imath.M44f().translate( imath.V3f( 1, 2, 3 ) ) )

		movingLight = r.light( "movingLight", None, lightAttributes )
		movingLight.transform(
			[ imath.M44f().translate( imath.V3f( 1, 2, 3 ) ), imath.M44f().translate( imath.V3f( 4, 5, 6 ) ) ],
			[ 2.5, 3.5 ]
		)

		del lightAttributes, staticLight, movingLight
		r.render()
		del r

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			arnold.AiSceneLoad( universe, self.temporaryDirectory() + "/test.ass", None )

			untransformedLight = arnold.AiNodeLookUpByName( universe, "light:untransformedLight" )
			staticLight = arnold.AiNodeLookUpByName( universe, "light:staticLight" )
			movingLight = arnold.AiNodeLookUpByName( universe, "light:movingLight" )

			m = arnold.AiNodeGetMatrix( untransformedLight, "matrix" )
			self.assertEqual( self.__m44f( m ), imath.M44f() )

			m = arnold.AiNodeGetMatrix( staticLight, "matrix" )
			self.assertEqual( self.__m44f( m ), imath.M44f().translate( imath.V3f( 1, 2, 3 ) ) )

			self.assertEqual( arnold.AiNodeGetFlt( movingLight, "motion_start" ), 2.5 )
			self.assertEqual( arnold.AiNodeGetFlt( movingLight, "motion_end" ), 3.5 )

			matrices = arnold.AiNodeGetArray( movingLight, "matrix" )

			m = arnold.AiArrayGetMtx( matrices, 0 )
			self.assertEqual( self.__m44f( m ), imath.M44f().translate( imath.V3f( 1, 2, 3 ) ) )
			m = arnold.AiArrayGetMtx( matrices, 1 )
			self.assertEqual( self.__m44f( m ), imath.M44f().translate( imath.V3f( 4, 5, 6 ) ) )

	def testSharedLightAttributes( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Arnold",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			self.temporaryDirectory() + "/test.ass"
		)

		lightShader = IECoreScene.ShaderNetwork( { "output" : IECoreScene.Shader( "point_light", "ai:light" ) }, output = "output" )
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

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			arnold.AiSceneLoad( universe, self.temporaryDirectory() + "/test.ass", None )

			lights = self.__allNodes( universe, type = arnold.AI_NODE_LIGHT )
			self.assertEqual( len( lights ), 2 )
			self.assertEqual( set( [ arnold.AiNodeGetName( l ) for l in lights ] ), { "light:testLight1", "light:testLight2" } )

	def testAttributes( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Arnold",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			self.temporaryDirectory() + "/test.ass"
		)

		r.object(
			"testMesh1",
			IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) ),
			r.attributes( IECore.CompoundObject( {
				"doubleSided" : IECore.BoolData( True ),
				"ai:visibility:camera" : IECore.BoolData( False ),
				"ai:visibility:shadow" : IECore.BoolData( True ),
				"ai:visibility:diffuse_reflect" : IECore.BoolData( False ),
				"ai:visibility:specular_reflect" : IECore.BoolData( True ),
				"ai:visibility:diffuse_transmit" : IECore.BoolData( False ),
				"ai:visibility:specular_transmit" : IECore.BoolData( True ),
				"ai:visibility:volume" : IECore.BoolData( False ),
				"ai:visibility:subsurface" : IECore.BoolData( True ),
				"ai:receive_shadows" : IECore.BoolData( True ),
				"ai:self_shadows" : IECore.BoolData( True ),
				"ai:matte" : IECore.BoolData( True ),
				"ai:opaque" : IECore.BoolData( True ),
			} ) ),
		)

		r.object(
			"testMesh2",
			IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) ),
			r.attributes( IECore.CompoundObject( {
				"doubleSided" : IECore.BoolData( False ),
				"ai:visibility:camera" : IECore.BoolData( True ),
				"ai:visibility:shadow" : IECore.BoolData( False ),
				"ai:visibility:diffuse_reflect" : IECore.BoolData( True ),
				"ai:visibility:specular_reflect" : IECore.BoolData( False ),
				"ai:visibility:diffuse_transmit" : IECore.BoolData( True ),
				"ai:visibility:specular_transmit" : IECore.BoolData( False ),
				"ai:visibility:volume" : IECore.BoolData( True ),
				"ai:visibility:subsurface" : IECore.BoolData( False ),
				"ai:receive_shadows" : IECore.BoolData( False ),
				"ai:self_shadows" : IECore.BoolData( False ),
				"ai:matte" : IECore.BoolData( False ),
				"ai:opaque" : IECore.BoolData( False ),
			} ) ),
		)

		r.object(
			"testMesh3",
			IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) ),
			r.attributes( IECore.CompoundObject() ),
		)

		r.render()
		del r

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			arnold.AiSceneLoad( universe, self.temporaryDirectory() + "/test.ass", None )

			o1 = arnold.AiNodeLookUpByName( universe, "testMesh1" )
			o2 = arnold.AiNodeLookUpByName( universe, "testMesh2" )
			o3 = arnold.AiNodeLookUpByName( universe, "testMesh3" )

			self.assertEqual( arnold.AiNodeGetByte( o1, "sidedness" ), arnold.AI_RAY_ALL )
			self.assertEqual( arnold.AiNodeGetByte( o2, "sidedness" ), arnold.AI_RAY_UNDEFINED )
			self.assertEqual( arnold.AiNodeGetByte( o3, "sidedness" ), arnold.AI_RAY_ALL )

			self.assertEqual(
				arnold.AiNodeGetByte( o1, "visibility" ),
				arnold.AI_RAY_ALL & ~( arnold.AI_RAY_CAMERA | arnold.AI_RAY_DIFFUSE_TRANSMIT | arnold.AI_RAY_DIFFUSE_REFLECT | arnold.AI_RAY_VOLUME )
			)
			self.assertEqual(
				arnold.AiNodeGetByte( o2, "visibility" ),
				arnold.AI_RAY_ALL & ~( arnold.AI_RAY_SHADOW | arnold.AI_RAY_SPECULAR_TRANSMIT | arnold.AI_RAY_SPECULAR_REFLECT | arnold.AI_RAY_SUBSURFACE )
			)
			self.assertEqual(
				arnold.AiNodeGetByte( o3, "visibility" ),
				arnold.AI_RAY_ALL
			)

			for p in ( "receive_shadows", "self_shadows", "matte", "opaque" ) :
				self.assertEqual( arnold.AiNodeGetBool( o1, p ), True )
				self.assertEqual( arnold.AiNodeGetBool( o2, p ), False )
				self.assertEqual( arnold.AiNodeGetBool( o3, p ), p != "matte" )

	def testOutputs( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Arnold",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			self.temporaryDirectory() + "/test.ass"
		)

		r.output(
			"testA",
			IECoreScene.Output(
				"beauty.exr",
				"exr",
				"color A",
				{}
			)
		)

		# NOTE : includeAlpha is currently undocumented, and we have not yet decided exactly how
		# to generalize it across renderer backends, so it may change in the future.
		r.output(
			"testB",
			IECoreScene.Output(
				"beauty.exr",
				"exr",
				"color B",
				{
					"includeAlpha" : True,
				}
			)
		)

		r.render()
		del r

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			arnold.AiSceneLoad( universe, self.temporaryDirectory() + "/test.ass", None )

			options = arnold.AiUniverseGetOptions( universe )
			outputs = arnold.AiNodeGetArray( options, "outputs" )
			self.assertEqual( arnold.AiArrayGetNumElements( outputs ), 2 )
			outputSet = set( [ arnold.AiArrayGetStr( outputs, 0 ), arnold.AiArrayGetStr( outputs, 1 ) ] )
			self.assertEqual( outputSet, set( [
				"A RGB ieCoreArnold:filter:testA ieCoreArnold:display:testA",
				"B RGBA ieCoreArnold:filter:testB ieCoreArnold:display:testB"
			] ) )

	def testOutputFilters( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Arnold",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			self.temporaryDirectory() + "/test.ass"
		)

		r.output(
			"test",
			IECoreScene.Output(
				"beauty.exr",
				"exr",
				"rgba",
				{
					"filter" : "gaussian",
					"filterwidth" : imath.V2f( 3.5 ),
				}
			)
		)

		r.render()
		del r

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			arnold.AiSceneLoad( universe, self.temporaryDirectory() + "/test.ass", None )
			filters = self.__allNodes( universe, type = arnold.AI_NODE_FILTER )
			self.assertEqual( len( filters ), 1 )
			f = filters[0]

			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( f ) ), "gaussian_filter" )
			self.assertEqual( arnold.AiNodeGetFlt( f, "width" ), 3.5 )

	def testOutputLPEs( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Arnold",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			self.temporaryDirectory() + "/test.ass"
		)

		r.output(
			"test",
			IECoreScene.Output(
				"beauty.exr",
				"exr",
				"lpe C.*D.*",
				{}
			)
		)

		r.output(
			"testWithAlpha",
			IECoreScene.Output(
				"beauty.exr",
				"exr",
				"lpe C.*D.*",
				{
					"includeAlpha" : True,
				}
			)
		)

		r.render()
		del r

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			arnold.AiSceneLoad( universe, self.temporaryDirectory() + "/test.ass", None )

			options = arnold.AiUniverseGetOptions( universe )
			outputs = arnold.AiNodeGetArray( options, "outputs" )
			self.assertEqual( arnold.AiArrayGetNumElements( outputs ), 2 )
			outputSet = set( [ arnold.AiArrayGetStr( outputs, 0 ), arnold.AiArrayGetStr( outputs, 1 ) ] )
			self.assertEqual( outputSet, set( [
				"ieCoreArnold:lpe:test RGB ieCoreArnold:filter:test ieCoreArnold:display:test",
				"ieCoreArnold:lpe:testWithAlpha RGBA ieCoreArnold:filter:testWithAlpha ieCoreArnold:display:testWithAlpha"
			] ) )

			lpes = arnold.AiNodeGetArray( options, "light_path_expressions" )
			self.assertEqual( arnold.AiArrayGetNumElements( lpes ), 2 )
			lpeSet = set( [ arnold.AiArrayGetStr( lpes, 0 ), arnold.AiArrayGetStr( lpes, 1 ) ] )
			self.assertEqual( lpeSet, set( [
				"ieCoreArnold:lpe:test C.*D.*",
				"ieCoreArnold:lpe:testWithAlpha C.*D.*"
			] ) )

	def testMultipleCameras( self ) :
		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Arnold",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch,
		)

		for i in range( 3 ):
			c = r.camera(
				"testCamera%i"%i,
				IECoreScene.Camera(
					parameters = {
						"projection" : "orthographic"
					}
				),
				r.attributes( IECore.CompoundObject() )
			)
			c.transform( imath.M44f().translate( imath.V3f( i, 0, 0 ) ) )

			r.output(
				"testBeauty%i"%i,
				IECoreScene.Output(
					self.temporaryDirectory() + "/beauty%i.exr"%i,
					"exr",
					"rgba",
					{
						"camera" : "testCamera%i"%i
					}
				)
			)

		r.output(
			"testDiffuse2",
			IECoreScene.Output(
				self.temporaryDirectory() + "/diffuse2.exr",
				"exr",
				"diffuse RGBA",
				{
					"camera" : "testCamera2"
				}
			)
		)

		r.option( "camera", IECore.StringData( "testCamera2" ) )

		r.render()

		worldToCameraKey = "worldtocamera"
		if hasattr( IECoreImage, "OpenImageIOAlgo" ) and IECoreImage.OpenImageIOAlgo.version() >= 20206 :
			worldToCameraKey = "worldToCamera"

		for i in range( 3 ):
			image = IECoreImage.ImageReader( self.temporaryDirectory() + "/beauty%i.exr"%i ).read()
			self.assertEqual( image.blindData()[worldToCameraKey].value,
				imath.M44f( 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, -1, 0, -i, 0, 0, 1 ) )

		image = IECoreImage.ImageReader( self.temporaryDirectory() + "/diffuse2.exr" ).read()
		self.assertEqual( image.blindData()[worldToCameraKey].value,
			imath.M44f( 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, -1, 0, -2, 0, 0, 1 ) )

	def testCameraMesh( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Arnold",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			self.temporaryDirectory() + "/test.ass"
		)

		r.object(
			"testPlane",
			IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) ),
			r.attributes( IECore.CompoundObject( {} ) )
		)

		r.camera(
			"testCamera",
			IECoreScene.Camera(
				parameters = {
					"projection" : "uv_camera",
					"mesh" : "testPlane"
				}
			),
			r.attributes( IECore.CompoundObject() )
		)

		r.option( "camera", IECore.StringData( "testCamera" ) )

		r.render()
		del r

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			arnold.AiSceneLoad( universe, self.temporaryDirectory() + "/test.ass", None )

			options = arnold.AiUniverseGetOptions( universe )

			camera = arnold.AiNodeGetPtr( options, "camera" )
			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( camera ) ), "uv_camera" )
			mesh = arnold.AiNodeGetPtr( camera, "mesh" )
			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( mesh ) ), "polymesh" )
			self.assertEqual(
				arnold.AiNodeGetName( arnold.AiNodeGetPtr( arnold.AiNodeLookUpByName( universe, "testPlane" ), "node" ) ),
				arnold.AiNodeGetName( mesh )
			)

	def testExrMetadata( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Arnold",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			self.temporaryDirectory() + "/test.ass"
		)

		r.output(
			"exrTest",
			IECoreScene.Output(
				"beauty.exr",
				"exr",
				"rgba",
				{
					"filter" : "gaussian",
					"filterwidth" : imath.V2f( 3.5 ),
					"custom_attributes" : IECore.StringVectorData([ "string 'original data' test" ]),
					"header:bar" : IECore.BoolData( True ),
				}
			)
		)

		r.output(
			"exrDataTest",
			IECoreScene.Output(
				"beauty.exr",
				"exr",
				"rgba",
				{
					"filter" : "gaussian",
					"filterwidth" : imath.V2f( 3.5 ),
					"header:foo" : IECore.StringData( "bar" ),
					"header:bar" : IECore.BoolData( True ),
					"header:nobar" : IECore.BoolData( False ),
					"header:floatbar" : IECore.FloatData( 1.618034 ),
					"header:intbar" : IECore.IntData( 42 ),
					"header:vec2i" : IECore.V2iData( imath.V2i( 100 ) ),
					"header:vec3i" : IECore.V3iData( imath.V3i( 100 ) ),
					"header:vec2f" : IECore.V2fData( imath.V2f( 100 ) ),
					"header:vec3f" : IECore.V3fData( imath.V3f( 100 ) ),
					"header:color3f" : IECore.Color3fData( imath.Color3f( 100 ) ),
					"header:color4f" : IECore.Color4fData( imath.Color4f( 100 ) ),
				}
			)
		)

		msg = IECore.CapturingMessageHandler()
		with msg:
			r.output(
				"tiffTest",
				IECoreScene.Output(
					"beauty.tiff",
					"tiff",
					"rgba",
					{
						"filter" : "gaussian",
						"filterwidth" : imath.V2f( 3.5 ),
						"header:foo" : IECore.StringData( "bar" ),
						"header:bar" : IECore.StringVectorData([ 'one', 'two', 'three' ])  # not supported and should print a warning
					}
				)
			)

		r.render()
		del r

		expectedMessage = 'Cannot convert data "bar" of type "StringVectorData".'

		self.assertEqual( len(msg.messages), 1 )
		self.assertEqual( msg.messages[-1].message, expectedMessage )
		self.assertEqual( msg.messages[-1].level, IECore.Msg.Level.Warning)

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			arnold.AiSceneLoad( universe, self.temporaryDirectory() + "/test.ass", None )

			# test if data was added correctly to existing data
			exrDriver = arnold.AiNodeLookUpByName( universe, "ieCoreArnold:display:exrTest" )
			customAttributes = arnold.AiNodeGetArray( exrDriver, "custom_attributes" )
			customAttributesValues = set([ arnold.AiArrayGetStr( customAttributes, i ) for i in range( arnold.AiArrayGetNumElements( customAttributes.contents ) ) ])
			customAttributesExpected = set([
				"int 'bar' 1",
				"string 'original data' test"])

			self.assertEqual( customAttributesValues, customAttributesExpected )

			# test if all data types work correctly
			exrDriver = arnold.AiNodeLookUpByName( universe, "ieCoreArnold:display:exrDataTest" )
			customAttributes = arnold.AiNodeGetArray( exrDriver, "custom_attributes" )
			customAttributesValues = set([ arnold.AiArrayGetStr( customAttributes, i ) for i in range( arnold.AiArrayGetNumElements( customAttributes.contents ) ) ])

			customAttributesExpected = set([
				"string 'foo' bar",
				"int 'bar' 1",
				"int 'nobar' 0",
				"float 'floatbar' 1.618034",
				"int 'intbar' 42",
				"string 'vec2i' (100 100)",
				"string 'vec3i' (100 100 100)",
				"string 'vec2f' (100 100)",
				"string 'vec3f' (100 100 100)",
				"string 'color3f' (100 100 100)",
				"string 'color4f' (100 100 100 100)"])

			self.assertEqual( customAttributesValues, customAttributesExpected )

			# make sure that attribute isn't added to drivers that don't support it
			tiffDriver = arnold.AiNodeLookUpByName( universe, "ieCoreArnold:display:tiffTest" )
			customAttributes = arnold.AiNodeGetArray( tiffDriver, "custom_attributes" )
			self.assertEqual(customAttributes, None)

	def testInstancing( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Arnold",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			self.temporaryDirectory() + "/test.ass"
		)

		polyPlane = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) )
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
		subdivideLinear = r.attributes(
			IECore.CompoundObject( {
				"ai:polymesh:subdivide_polygons" : IECore.BoolData( True )
			} )
		)
		subdivideLinearAdaptive = r.attributes(
			IECore.CompoundObject( {
				"ai:polymesh:subdivide_polygons" : IECore.BoolData( True ),
				"ai:polymesh:subdiv_adaptive_error" : IECore.FloatData( 0.1 ),
			} )
		)
		smoothDerivsTrueAttributes = r.attributes(
			IECore.CompoundObject( {
				"ai:polymesh:subdiv_smooth_derivs" : IECore.BoolData( True )
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

		# With subdivide_polygons on, poly meshes need the same behaviour as subdivs, breaking instancing
		# when adaptive is on
		r.object( "polySubdivideLinearAttributes1", polyPlane.copy(), subdivideLinear )
		r.object( "polySubdivideLinearAttributes2", polyPlane.copy(), subdivideLinear )

		r.object( "polyAdaptiveSubdivideLinearAttributes1", polyPlane.copy(), subdivideLinearAdaptive )
		r.object( "polyAdaptiveSubdivideLinearAttributes2", polyPlane.copy(), subdivideLinearAdaptive )

		# If smooth derivatives are required, that'll require creating a separate polymesh and an instance of it

		r.object( "subdivSmoothDerivsAttributes1", subdivPlane.copy(), smoothDerivsTrueAttributes )

		r.render()
		del defaultAttributes, adaptiveAttributes, nonAdaptiveAttributes, adaptiveObjectSpaceAttributes
		del r

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			arnold.AiSceneLoad( universe, self.temporaryDirectory() + "/test.ass", None )

			shapes = self.__allNodes( universe, type = arnold.AI_NODE_SHAPE )
			numInstances = len( [ s for s in shapes if arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( s ) ) == "ginstance" ] )
			numPolyMeshes = len( [ s for s in shapes if arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( s ) ) == "polymesh" ] )

			self.assertEqual( numPolyMeshes, 9 )
			self.assertEqual( numInstances, 13 )

			self.__assertInstanced(
				universe,
				"polyDefaultAttributes1",
				"polyDefaultAttributes2",
				"polyAdaptiveAttributes1",
				"polyAdaptiveAttributes2",
			)

			self.__assertInstanced(
				universe,
				"subdivDefaultAttributes1",
				"subdivDefaultAttributes2",
				"subdivNonAdaptiveAttributes1",
				"subdivNonAdaptiveAttributes2",
			)

			self.__assertNotInstanced(
				universe,
				"subdivAdaptiveAttributes1",
				"subdivAdaptiveAttributes2"
			)

			self.__assertInstanced(
				universe,
				"subdivAdaptiveObjectSpaceAttributes1",
				"subdivAdaptiveObjectSpaceAttributes2",
			)

			self.__assertInstanced(
				universe,
				"polySubdivideLinearAttributes1",
				"polySubdivideLinearAttributes2",
			)

			self.__assertNotInstanced(
				universe,
				"polyAdaptiveSubdivideLinearAttributes1",
				"polyAdaptiveSubdivideLinearAttributes2",
			)

	def testTransformTypeAttribute( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Arnold",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			self.temporaryDirectory() + "/test.ass"
		)

		plane = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) )

		r.object(
			"planeDefault",
			plane,
			r.attributes( IECore.CompoundObject() )
		)
		r.object(
			"planeLinear",
			plane,
			r.attributes(
				IECore.CompoundObject( {
					"ai:transform_type" : IECore.StringData( "linear" ),
				} )
			)
		)

		r.render()
		del r

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			arnold.AiSceneLoad( universe, self.temporaryDirectory() + "/test.ass", None )
			defaultNode = arnold.AiNodeLookUpByName( universe, "planeDefault" )
			linearNode = arnold.AiNodeLookUpByName( universe, "planeLinear" )
			self.assertEqual( arnold.AiNodeGetStr( defaultNode, "transform_type" ), "rotate_about_center" )
			self.assertEqual( arnold.AiNodeGetStr( linearNode, "transform_type" ), "linear" )

	def testSubdivisionAttributes( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Arnold",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			self.temporaryDirectory() + "/test.ass"
		)

		subdivPlane = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) )
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
					"ai:polymesh:subdiv_frustum_ignore" : IECore.BoolData( True ),
				} )
			)
		)

		r.render()
		del r

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			arnold.AiSceneLoad( universe, self.temporaryDirectory() + "/test.ass", None )
			node = arnold.AiNodeLookUpByName( universe, "plane" )
			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( node ) ), "polymesh" )
			self.assertEqual( arnold.AiNodeGetByte( node, "subdiv_iterations" ), 10 )
			self.assertEqual( arnold.AiNodeGetFlt( node, "subdiv_adaptive_error" ), 0.25 )
			self.assertEqual( arnold.AiNodeGetStr( node, "subdiv_adaptive_metric" ), "edge_length" )
			self.assertEqual( arnold.AiNodeGetStr( node, "subdiv_adaptive_space" ), "raster" )
			self.assertEqual( arnold.AiNodeGetBool( node, "subdiv_frustum_ignore" ), True )

	def testSSSSetNameAttribute( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Arnold",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			self.temporaryDirectory() + "/test.ass"
		)

		plane = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) )

		r.object(
			"plane",
			plane,
			r.attributes(
				IECore.CompoundObject( {
					"ai:sss_setname" : IECore.StringData( "testSet" ),
				} )
			)
		)

		r.render()
		del r

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			arnold.AiSceneLoad( universe, self.temporaryDirectory() + "/test.ass", None )
			node = arnold.AiNodeLookUpByName( universe, "plane" )
			self.assertEqual( arnold.AiNodeGetStr( node, "sss_setname" ), "testSet" )

	def testCustomAttributes( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Arnold",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			self.temporaryDirectory() + "/test.ass"
		)

		# Current convention : attributes prefixed with "user:"

		r.object(
			"userPlane1",
			IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) ),
			r.attributes(
				IECore.CompoundObject( {
					"user:testInt" : IECore.IntData( 1 ),
					"user:testFloat" : IECore.FloatData( 2.5 ),
					"user:testV3f" : IECore.V3fData( imath.V3f( 1, 2, 3 ) ),
					"user:testColor3f" : IECore.Color3fData( imath.Color3f( 4, 5, 6 ) ),
					"user:testString" : IECore.StringData( "we're all doomed" ),
				} )
			)
		)

		r.object(
			"userPlane2",
			IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) ),
			r.attributes(
				IECore.CompoundObject( {
					"user:testInt" : IECore.IntData( 2 ),
					"user:testFloat" : IECore.FloatData( 25 ),
					"user:testV3f" : IECore.V3fData( imath.V3f( 0, 1, 0 ) ),
					"user:testColor3f" : IECore.Color3fData( imath.Color3f( 1, 0.5, 0 ) ),
					"user:testString" : IECore.StringData( "indeed" ),
				} )
			)
		)

		# Convention we are transitioning to : attributes prefixed with "render:"

		r.object(
			"renderPlane1",
			IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) ),
			r.attributes(
				IECore.CompoundObject( {
					"render:testInt" : IECore.IntData( 1 ),
					"render:testFloat" : IECore.FloatData( 2.5 ),
					"render:testV3f" : IECore.V3fData( imath.V3f( 1, 2, 3 ) ),
					"render:testColor3f" : IECore.Color3fData( imath.Color3f( 4, 5, 6 ) ),
					"render:testString" : IECore.StringData( "we're all doomed" ),
				} )
			)
		)

		r.object(
			"renderPlane2",
			IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) ),
			r.attributes(
				IECore.CompoundObject( {
					"render:testInt" : IECore.IntData( 2 ),
					"render:testFloat" : IECore.FloatData( 25 ),
					"render:testV3f" : IECore.V3fData( imath.V3f( 0, 1, 0 ) ),
					"render:testColor3f" : IECore.Color3fData( imath.Color3f( 1, 0.5, 0 ) ),
					"render:testString" : IECore.StringData( "indeed" ),
				} )
			)
		)

		r.render()
		del r

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			arnold.AiSceneLoad( universe, self.temporaryDirectory() + "/test.ass", None )

			# Test "user:". We expect the prefix to be included in the Arnold
			# parameter name.

			userPlane1 = arnold.AiNodeLookUpByName( universe, "userPlane1" )
			self.assertEqual( arnold.AiNodeGetInt( userPlane1, "user:testInt" ), 1 )
			self.assertEqual( arnold.AiNodeGetFlt( userPlane1, "user:testFloat" ), 2.5 )
			self.assertEqual( arnold.AiNodeGetVec( userPlane1, "user:testV3f" ), arnold.AtVector( 1, 2, 3 ) )
			self.assertEqual( arnold.AiNodeGetRGB( userPlane1, "user:testColor3f" ), arnold.AtRGB( 4, 5, 6 ) )
			self.assertEqual( arnold.AiNodeGetStr( userPlane1, "user:testString" ), "we're all doomed" )

			userPlane2 = arnold.AiNodeLookUpByName( universe, "userPlane2" )
			self.assertEqual( arnold.AiNodeGetInt( userPlane2, "user:testInt" ), 2 )
			self.assertEqual( arnold.AiNodeGetFlt( userPlane2, "user:testFloat" ), 25 )
			self.assertEqual( arnold.AiNodeGetVec( userPlane2, "user:testV3f" ), arnold.AtVector( 0, 1, 0 ) )
			self.assertEqual( arnold.AiNodeGetRGB( userPlane2, "user:testColor3f" ), arnold.AtRGB( 1, 0.5, 0 ) )
			self.assertEqual( arnold.AiNodeGetStr( userPlane2, "user:testString" ), "indeed" )

			# Test "render:". We expect the prefix to have been stripped from
			# the Arnold parameter name.

			renderPlane1 = arnold.AiNodeLookUpByName( universe, "renderPlane1" )
			self.assertEqual( arnold.AiNodeGetInt( renderPlane1, "testInt" ), 1 )
			self.assertEqual( arnold.AiNodeGetFlt( renderPlane1, "testFloat" ), 2.5 )
			self.assertEqual( arnold.AiNodeGetVec( renderPlane1, "testV3f" ), arnold.AtVector( 1, 2, 3 ) )
			self.assertEqual( arnold.AiNodeGetRGB( renderPlane1, "testColor3f" ), arnold.AtRGB( 4, 5, 6 ) )
			self.assertEqual( arnold.AiNodeGetStr( renderPlane1, "testString" ), "we're all doomed" )

			renderPlane2 = arnold.AiNodeLookUpByName( universe, "renderPlane2" )
			self.assertEqual( arnold.AiNodeGetInt( renderPlane2, "testInt" ), 2 )
			self.assertEqual( arnold.AiNodeGetFlt( renderPlane2, "testFloat" ), 25 )
			self.assertEqual( arnold.AiNodeGetVec( renderPlane2, "testV3f" ), arnold.AtVector( 0, 1, 0 ) )
			self.assertEqual( arnold.AiNodeGetRGB( renderPlane2, "testColor3f" ), arnold.AtRGB( 1, 0.5, 0 ) )
			self.assertEqual( arnold.AiNodeGetStr( renderPlane2, "testString" ), "indeed" )

	def testCustomAttributePrecedence( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Arnold",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			self.temporaryDirectory() + "/test.ass"
		)

		# Mix of attributes where `render:` clashes with `user:`

		r.object(
			"plane",
			IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) ),
			r.attributes(
				IECore.CompoundObject( {
					"user:test" : IECore.StringData( "user" ),
					"render:user:test" : IECore.StringData( "render" ),
				} )
			)
		)

		r.render()
		del r

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			arnold.AiSceneLoad( universe, self.temporaryDirectory() + "/test.ass", None )

			# We expect the `render:` attribute to have taken precedence over
			# the `user:` one.

			plane = arnold.AiNodeLookUpByName( universe, "plane" )
			self.assertEqual( arnold.AiNodeGetStr( plane, "user:test" ), "render" )

	def testAddAndRemoveCustomAttributes( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Arnold",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			self.temporaryDirectory() + "/test.ass"
		)

		# Start with one set of attributes.

		o = r.object(
			"plane",
			IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) ),
			r.attributes(
				IECore.CompoundObject( {
					"render:toReplace" : IECore.StringData( "original" ),
					"render:toRemove" : IECore.StringData( "original" ),
					"render:toChangeType" : IECore.StringData( "original" ),
				} )
			)
		)

		# Replace with another set.

		o.attributes(
			r.attributes(
				IECore.CompoundObject( {
					"render:toReplace" : IECore.StringData( "new" ),
					"render:new" : IECore.StringData( "new" ),
					"render:toChangeType" : IECore.IntData( 101 ),
				} )
			)
		)

		r.render()
		del o
		del r

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			arnold.AiSceneLoad( universe, self.temporaryDirectory() + "/test.ass", None )

			plane = arnold.AiNodeLookUpByName( universe, "plane" )

			self.assertEqual( arnold.AiNodeGetStr( plane, "toReplace" ), "new" )
			self.assertEqual( arnold.AiNodeGetStr( plane, "new" ), "new" )
			self.assertEqual( arnold.AiNodeGetInt( plane, "toChangeType" ), 101 )
			self.assertIsNone( arnold.AiNodeLookUpUserParameter( plane, "toRemove" ) )

	def testCustomAttributesCantSetStandardParameters( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Arnold",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			self.temporaryDirectory() + "/test.ass"
		)

		# Try to set `motion_start` on the sly, via a `render:` attribute.
		# We don't want to allow this because we need to manage Arnold's
		# built in parameters via the official renderer API.

		with IECore.CapturingMessageHandler() as mh :

			r.object(
				"plane",
				IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) ),
				r.attributes(
					IECore.CompoundObject( {
						"render:motion_start" : IECore.FloatData( -1 ),
					} )
				)
			)

		self.assertEqual( len( mh.messages ), 1 )
		self.assertEqual(
			mh.messages[0].message,
			"Custom attribute \"motion_start\" will be ignored because it clashes with Arnold's built-in parameters"
		)

		r.render()
		del r

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			arnold.AiSceneLoad( universe, self.temporaryDirectory() + "/test.ass", None )

			plane = arnold.AiNodeLookUpByName( universe, "plane" )
			self.assertEqual( arnold.AiNodeGetFlt( plane, "motion_start" ), 0 )

	def testRemovingCustomAttributesCantResetStandardParameters( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Arnold",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			self.temporaryDirectory() + "/test.ass"
		)

		# Try to set `matrix` on the sly, via a `render:` attribute.
		# We don't want to allow this because we need to manage it
		# via `ObjectInterface:transform()`.

		with IECore.CapturingMessageHandler() as mh :

			o = r.object(
				"plane",
				IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) ),
				r.attributes(
					IECore.CompoundObject( {
						"render:matrix" : IECore.M44fData(
							imath.M44f().translate( imath.V3f( 1, 2, 3 ) ),
						)
					} )
				)
			)

		self.assertEqual( len( mh.messages ), 1 )
		self.assertEqual(
			mh.messages[0].message,
			"Custom attribute \"matrix\" will be ignored because it clashes with Arnold's built-in parameters"
		)

		# Now set `matrix` via the official route.
		o.transform( imath.M44f().translate( imath.V3f( 4, 5, 6 ) ) )
		# And remove the dodgy custom attribute. If it's not implemented
		# carefuly, the code for removing attributes could reset the
		# matrix, which is definitely not what we want.
		o.attributes( r.attributes( IECore.CompoundObject( {} ) ) )

		r.render()
		del o
		del r

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			arnold.AiSceneLoad( universe, self.temporaryDirectory() + "/test.ass", None )

			plane = arnold.AiNodeLookUpByName( universe, "plane" )
			self.assertEqual(
				self.__m44f( arnold.AiNodeGetMatrix( plane, "matrix" ) ),
				imath.M44f().translate( imath.V3f( 4, 5, 6 ) )
			)

	def testDisplacementAttributes( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Arnold",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			self.temporaryDirectory() + "/test.ass"
		)

		plane = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) )
		noise = IECoreScene.ShaderNetwork( { "output" : IECoreScene.Shader( "noise", "ai:displacement", {} ) }, output = "output" )

		sharedAttributes = r.attributes(
			IECore.CompoundObject( {
				"ai:disp_map" : noise,
				"ai:disp_height" : IECore.FloatData( 0.25 ),
				"ai:disp_padding" : IECore.FloatData( 2.5 ),
				"ai:disp_zero_value" : IECore.FloatData( 0.5 ),
				"ai:disp_autobump" : IECore.BoolData( True ),
				"ai:autobump_visibility:camera" : IECore.BoolData( True ),
				"ai:autobump_visibility:diffuse_reflect" : IECore.BoolData( True ),
				"ai:autobump_visibility:specular_reflect" : IECore.BoolData( False ),
				"ai:autobump_visibility:diffuse_transmit" : IECore.BoolData( True ),
				"ai:autobump_visibility:specular_transmit" : IECore.BoolData( False ),
				"ai:autobump_visibility:volume" : IECore.BoolData( True ),
				"ai:autobump_visibility:subsurface" : IECore.BoolData( False ),
			} )
		)

		r.object( "plane1", plane, sharedAttributes )
		r.object( "plane2", plane, sharedAttributes )
		del sharedAttributes

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
					"ai:autobump_visibility:camera" : IECore.BoolData( False ),
					"ai:autobump_visibility:diffuse_reflect" : IECore.BoolData( False ),
					"ai:autobump_visibility:specular_reflect" : IECore.BoolData( True ),
					"ai:autobump_visibility:diffuse_transmit" : IECore.BoolData( False ),
					"ai:autobump_visibility:specular_transmit" : IECore.BoolData( True ),
					"ai:autobump_visibility:volume" : IECore.BoolData( False ),
					"ai:autobump_visibility:subsurface" : IECore.BoolData( True ),
				} )
			)
		)

		r.render()
		del r

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			arnold.AiSceneLoad( universe, self.temporaryDirectory() + "/test.ass", None )

			shapes = self.__allNodes( universe, type = arnold.AI_NODE_SHAPE )
			self.assertEqual( len( shapes ), 5 )

			plane1 = arnold.AiNodeLookUpByName( universe, "plane1" )
			plane2 = arnold.AiNodeLookUpByName( universe, "plane2" )
			plane3 = arnold.AiNodeLookUpByName( universe, "plane3" )

			self.assertTrue( arnold.AiNodeIs( plane1, "ginstance" ) )
			self.assertTrue( arnold.AiNodeIs( plane2, "ginstance" ) )
			self.assertTrue( arnold.AiNodeIs( plane3, "ginstance" ) )

			self.assertReferSameNode( arnold.AiNodeGetPtr( plane1, "node" ), arnold.AiNodeGetPtr( plane2, "node" ) )
			self.assertReferDifferentNode( arnold.AiNodeGetPtr( plane2, "node" ), arnold.AiNodeGetPtr( plane3, "node" ) )

			polymesh1 = arnold.AiNodeGetPtr( plane1, "node" )
			polymesh2 = arnold.AiNodeGetPtr( plane3, "node" )

			self.assertTrue( arnold.AiNodeIs( polymesh1, "polymesh" ) )
			self.assertTrue( arnold.AiNodeIs( polymesh2, "polymesh" ) )

			self.assertReferSameNode( arnold.AiNodeGetPtr( polymesh1, "disp_map" ), arnold.AiNodeGetPtr( polymesh2, "disp_map" ) )
			self.assertEqual( arnold.AiNodeGetFlt( polymesh1, "disp_height" ), 0.25 )
			self.assertEqual( arnold.AiNodeGetFlt( polymesh2, "disp_height" ), 0.5 )
			self.assertEqual( arnold.AiNodeGetFlt( polymesh1, "disp_padding" ), 2.5 )
			self.assertEqual( arnold.AiNodeGetFlt( polymesh2, "disp_padding" ), 5.0 )
			self.assertEqual( arnold.AiNodeGetFlt( polymesh1, "disp_zero_value" ), 0.5 )
			self.assertEqual( arnold.AiNodeGetFlt( polymesh2, "disp_zero_value" ), 0.0 )
			self.assertEqual( arnold.AiNodeGetBool( polymesh1, "disp_autobump" ), True )
			self.assertEqual( arnold.AiNodeGetBool( polymesh2, "disp_autobump" ), True )

			self.assertEqual(
				arnold.AiNodeGetByte( polymesh1, "autobump_visibility" ),
				arnold.AI_RAY_CAMERA | arnold.AI_RAY_DIFFUSE_REFLECT | arnold.AI_RAY_DIFFUSE_TRANSMIT | arnold.AI_RAY_VOLUME
			)
			self.assertEqual(
				arnold.AiNodeGetByte( polymesh2, "autobump_visibility" ),
				arnold.AI_RAY_SPECULAR_REFLECT | arnold.AI_RAY_SPECULAR_TRANSMIT | arnold.AI_RAY_SUBSURFACE
			)

	def testAutobumpVisibilityInit( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Arnold",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			self.temporaryDirectory() + "/test.ass"
		)

		r.object(
			"default",
			IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) ),
			r.attributes( IECore.CompoundObject() )
		)

		r.render()
		del r

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			arnold.AiSceneLoad( universe, self.temporaryDirectory() + "/test.ass", None )

			default = arnold.AiNodeLookUpByName( universe, "default" )
			polymesh = arnold.AiNodeGetPtr( default, "node" )

			self.assertEqual(
				arnold.AiNodeGetByte( polymesh, "autobump_visibility" ),
				arnold.AI_RAY_CAMERA
			)

	def testSubdividePolygonsAttribute( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Arnold",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			self.temporaryDirectory() + "/test.ass"
		)

		meshes = {}
		meshes["linear"] = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) )
		meshes["catmullClark"] = meshes["linear"].copy()
		meshes["catmullClark"].interpolation = "catmullClark"

		attributes = {}
		for subdividePolygons in ( None, False, True ) :
			a = IECore.CompoundObject()
			if subdividePolygons is not None :
				a["ai:polymesh:subdivide_polygons"] = IECore.BoolData( subdividePolygons )
			attributes[subdividePolygons] = r.attributes( a )

		for interpolation in meshes.keys() :
			for subdividePolygons in attributes.keys() :
				r.object( interpolation + "-" + str( subdividePolygons ), meshes[interpolation], attributes[subdividePolygons] )

		del attributes

		r.render()
		del r

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			arnold.AiSceneLoad( universe, self.temporaryDirectory() + "/test.ass", None )

			for interpolation in meshes.keys() :
				for subdividePolygons in ( None, False, True ) :

					instance = arnold.AiNodeLookUpByName( universe, interpolation + "-" + str( subdividePolygons ) )
					self.assertTrue( arnold.AiNodeIs( instance, "ginstance" ) )

					mesh = arnold.AiNodeGetPtr( instance, "node" )
					self.assertTrue( arnold.AiNodeIs( mesh, "polymesh" ) )

					if subdividePolygons and interpolation == "linear" :
						self.assertEqual( arnold.AiNodeGetStr( mesh, "subdiv_type" ), "linear" )
					else :
						self.assertEqual( arnold.AiNodeGetStr( mesh, "subdiv_type" ), "catclark" if interpolation == "catmullClark" else "none" )

	def testUVSmoothingAttribute( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Arnold",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			self.temporaryDirectory() + "/test.ass"
		)

		mesh = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) )
		mesh.interpolation = "catmullClark"

		smoothingTypes = ( "pin_corners", "pin_borders", "linear", "smooth", None )
		for uvSmoothing in smoothingTypes :
			attributes = IECore.CompoundObject()
			if uvSmoothing is not None :
				attributes["ai:polymesh:subdiv_uv_smoothing"] = IECore.StringData( uvSmoothing )
			r.object(
				"mesh-" + ( uvSmoothing or "default" ),
				mesh,
				r.attributes( attributes )
			)

		r.render()
		del r

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			arnold.AiSceneLoad( universe, self.temporaryDirectory() + "/test.ass", None )

			for uvSmoothing in smoothingTypes :

				instance = arnold.AiNodeLookUpByName( universe, "mesh-" + ( uvSmoothing or "default" ) )
				self.assertTrue( arnold.AiNodeIs( instance, "ginstance" ) )

				mesh = arnold.AiNodeGetPtr( instance, "node" )
				self.assertTrue( arnold.AiNodeIs( mesh, "polymesh" ) )

				self.assertEqual( arnold.AiNodeGetStr( mesh, "subdiv_uv_smoothing" ), uvSmoothing or "pin_corners" )

	def testMeshLight( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Arnold",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			self.temporaryDirectory() + "/test.ass"
		)

		l = r.light(
			"myLight",
			IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) ),
			r.attributes(
				IECore.CompoundObject( {
					"ai:light" : IECoreScene.ShaderNetwork( { "light" : IECoreScene.Shader( "mesh_light", "ai:light" ) }, output = "light" )
				} )
			)
		)
		del l

		r.render()
		del r

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			arnold.AiSceneLoad( universe, self.temporaryDirectory() + "/test.ass", None )

			shapes = self.__allNodes( universe, type = arnold.AI_NODE_SHAPE )
			self.assertEqual( len( shapes ), 2 )

			instance = arnold.AiNodeLookUpByName( universe, "myLight" )
			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( instance ) ), "ginstance" )
			mesh = arnold.AiNodeGetPtr( instance, "node" )
			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( mesh ) ), "polymesh" )

			lights = self.__allNodes( universe, type = arnold.AI_NODE_LIGHT )
			self.assertEqual( len( lights ), 1 )
			light = lights[0]
			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( light ) ), "mesh_light" )
			self.assertReferSameNode( arnold.AiNodeGetPtr( light, "mesh" ), instance )

	def testMeshLightsWithSharedShaders( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Arnold",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			self.temporaryDirectory() + "/test.ass"
		)

		lightShaderNetwork = IECoreScene.ShaderNetwork(
			shaders = {
				"colorHandle" : IECoreScene.Shader( "flat", "ai:shader" ),
				"light" : IECoreScene.Shader( "mesh_light", "ai:light" ),
			},
			connections = [
				( ( "colorHandle", "" ), ( "light", "color" ) )
			],
			output = "light"
		)

		l1 = r.light(
			"myLight1",
			IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) ),
			r.attributes( IECore.CompoundObject( {
				"ai:light" : lightShaderNetwork,
			} ) )
		)
		del l1

		l2 = r.light(
			"myLight2",
			IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) ),
			r.attributes( IECore.CompoundObject( {
				"ai:light" : lightShaderNetwork,
			} ) )
		)
		del l2

		r.render()
		del r

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			arnold.AiSceneLoad( universe, self.temporaryDirectory() + "/test.ass", None )

			shapes = self.__allNodes( universe, type = arnold.AI_NODE_SHAPE )
			self.assertEqual( len( shapes ), 3 )

			instance1 = arnold.AiNodeLookUpByName( universe, "myLight1" )
			instance2 = arnold.AiNodeLookUpByName( universe, "myLight2" )
			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( instance1 ) ), "ginstance" )
			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( instance2 ) ), "ginstance" )

			self.assertReferSameNode( arnold.AiNodeGetPtr( instance1, "node" ), arnold.AiNodeGetPtr( instance2, "node" ) )

			mesh = arnold.AiNodeGetPtr( instance1, "node" )
			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( mesh ) ), "polymesh" )

			lights = self.__allNodes( universe, type = arnold.AI_NODE_LIGHT )
			self.assertEqual( len( lights ), 2 )

			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( lights[0] ) ), "mesh_light" )
			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( lights[1] ) ), "mesh_light" )

			flat1 = arnold.AiNodeGetLink( lights[0], "color" )
			flat2 = arnold.AiNodeGetLink( lights[1], "color" )

			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( flat1 ) ), "flat" )
			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( flat2 ) ), "flat" )

	def testOSLShaders( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Arnold",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			self.temporaryDirectory() + "/test.ass"
		)

		network = IECoreScene.ShaderNetwork(
			shaders = {
				"noiseHandle" : IECoreScene.Shader(
					"Pattern/Noise",
					"osl:shader",
					{ "scale" : 10.0 }
				),
				"splineHandle" : IECoreScene.Shader(
					"Pattern/ColorSpline",
					"osl:shader",
					{
						"spline" : IECore.SplinefColor3f(
							IECore.CubicBasisf.bSpline(),
							[
								( 0, imath.Color3f( 0 ) ),
								( 0.25, imath.Color3f( 0.25 ) ),
								( 0.5, imath.Color3f( 0.5 ) ),
								( 1, imath.Color3f( 1 ) ),
							]
						),
					}
				),
				"floatSplineHandle" : IECoreScene.Shader(
					"Pattern/FloatSpline",
					"osl:shader",
					{
						"spline" : IECore.Splineff(
							IECore.CubicBasisf.linear(),
							[
								( 0, 0.25 ),
								( 1, 0.5 ),
							]
						),
					}
				),
				"output" : IECoreScene.Shader( "switch_rgba", "ai:surface" ),
			},
			connections = [
				( ( "splineHandle", "" ), ( "output", "input1" ) ),
				( ( "noiseHandle", "" ), ( "output", "input2" ) ),
				( ( "floatSplineHandle", "" ), ( "output", "input3" ) ),
			],
			output = "output"
		)

		o = r.object(
			"testPlane",
			IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) ),
			r.attributes( IECore.CompoundObject( { "ai:surface" : network } ) )
		)
		del o

		r.render()
		del r

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			arnold.AiSceneLoad( universe, self.temporaryDirectory() + "/test.ass", None )

			options = arnold.AiUniverseGetOptions( universe )
			self.assertTrue( os.path.expandvars( "$GAFFER_ROOT/shaders" ) in arnold.AiNodeGetStr( options, "plugin_searchpath" ) )

			n = arnold.AiNodeLookUpByName( universe, "testPlane" )

			switch = arnold.AiNodeGetPtr( n, "shader" )
			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( switch ) ), "switch_rgba" )

			spline = arnold.AiNodeGetLink( switch, "input1" )
			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( spline ) ), "osl" )
			self.assertEqual( arnold.AiNodeGetStr( spline, "shadername" ), "Pattern/ColorSpline" )
			self.assertEqual( arnold.AiNodeGetStr( spline, "param_splineBasis" ), "bspline" )

			splinePositions = arnold.AiNodeGetArray( spline, "param_splinePositions" )
			self.assertEqual( arnold.AiArrayGetFlt( splinePositions, 0 ), 0 )
			self.assertEqual( arnold.AiArrayGetFlt( splinePositions, 1 ), 0.25 )
			self.assertEqual( arnold.AiArrayGetFlt( splinePositions, 2 ), 0.5 )
			self.assertEqual( arnold.AiArrayGetFlt( splinePositions, 3 ), 1 )

			splineValues = arnold.AiNodeGetArray( spline, "param_splineValues" )
			self.assertEqual( arnold.AiArrayGetRGB( splineValues, 0 ), arnold.AtRGB( 0, 0, 0 ) )
			self.assertEqual( arnold.AiArrayGetRGB( splineValues, 1 ), arnold.AtRGB( 0.25, 0.25, 0.25 ) )
			self.assertEqual( arnold.AiArrayGetRGB( splineValues, 2 ), arnold.AtRGB( 0.5, 0.5, 0.5 ) )
			self.assertEqual( arnold.AiArrayGetRGB( splineValues, 3 ), arnold.AtRGB( 1, 1, 1 ) )

			floatSpline = arnold.AiNodeGetLink( switch, "input3" )
			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( floatSpline ) ), "osl" )
			self.assertEqual( arnold.AiNodeGetStr( floatSpline, "shadername" ), "Pattern/FloatSpline" )
			self.assertEqual( arnold.AiNodeGetStr( floatSpline, "param_splineBasis" ), "linear" )

			floatSplinePositions = arnold.AiNodeGetArray( floatSpline, "param_splinePositions" )
			self.assertEqual( arnold.AiArrayGetFlt( floatSplinePositions, 0 ), 0 )
			self.assertEqual( arnold.AiArrayGetFlt( floatSplinePositions, 1 ), 0 )
			self.assertEqual( arnold.AiArrayGetFlt( floatSplinePositions, 2 ), 1 )
			self.assertEqual( arnold.AiArrayGetFlt( floatSplinePositions, 3 ), 1 )

			floatSplineValues = arnold.AiNodeGetArray( floatSpline, "param_splineValues" )
			self.assertEqual( arnold.AiArrayGetFlt( floatSplineValues, 0 ), 0.25 )
			self.assertEqual( arnold.AiArrayGetFlt( floatSplineValues, 1 ), 0.25 )
			self.assertEqual( arnold.AiArrayGetFlt( floatSplineValues, 2 ), 0.5 )
			self.assertEqual( arnold.AiArrayGetFlt( floatSplineValues, 3 ), 0.5 )

			noise = arnold.AiNodeGetLink( switch, "input2" )
			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( noise ) ), "osl" )
			self.assertEqual( arnold.AiNodeGetStr( noise, "shadername" ), "Pattern/Noise" )
			self.assertEqual( arnold.AiNodeGetFlt( noise, "param_scale" ), 10.0 )

	def testPureOSLShaders( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Arnold",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			self.temporaryDirectory() + "/test.ass"
		)

		network = IECoreScene.ShaderNetwork( { "output" : IECoreScene.Shader( "Pattern/Noise", "osl:shader" ) }, output = "output" )

		o = r.object(
			"testPlane",
			IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) ),
			r.attributes( IECore.CompoundObject( { "osl:shader" : network } ) )
		)
		del o

		r.render()
		del r

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			arnold.AiSceneLoad( universe, self.temporaryDirectory() + "/test.ass", None )

			options = arnold.AiUniverseGetOptions( universe )

			n = arnold.AiNodeLookUpByName( universe, "testPlane" )

			noise = arnold.AiNodeGetPtr( n, "shader" )
			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( noise ) ), "osl" )
			self.assertEqual( arnold.AiNodeGetStr( noise, "shadername" ), "Pattern/Noise" )

	def testOSLMultipleOutputs( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Arnold",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			self.temporaryDirectory() + "/test.ass"
		)

		network = IECoreScene.ShaderNetwork(
			shaders = {
				"colorToFloatHandle" : IECoreScene.Shader(
					"Conversion/ColorToFloat",
					"osl:shader",
					{
						"c" : imath.Color3f( 0.1, 0.2, 0.3 ),
					}
				),
				"output" : IECoreScene.Shader( "Conversion/FloatToColor", "osl:shader" ),
			},
			connections = [
				( ( "colorToFloatHandle", "r" ), ( "output", "r" ) ),
				( ( "colorToFloatHandle", "g" ), ( "output", "g" ) ),
				( ( "colorToFloatHandle", "b" ), ( "output", "b" ) ),
			],
			output = "output"
		)

		r.object(
			"testPlane",
			IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) ),
			r.attributes( IECore.CompoundObject( { "ai:surface" : network } ) )
		)

		r.render()
		del r

		with IECoreArnold.UniverseBlock( writable = True ) as universe :
			arnold.AiSceneLoad( universe, self.temporaryDirectory() + "/test.ass", None )

			n = arnold.AiNodeLookUpByName( universe, "testPlane" )

			floatToColor = arnold.AiNodeGetPtr( n, "shader" )
			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( floatToColor ) ), "osl" )
			self.assertEqual( arnold.AiNodeGetStr( floatToColor, "shadername" ), "Conversion/FloatToColor" )

			colorToFloatR = arnold.AiNodeGetLink( floatToColor, "param_r" )
			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( colorToFloatR ) ), "osl" )
			self.assertEqual( arnold.AiNodeGetStr( colorToFloatR, "output" ), "r" )
			self.assertEqual( arnold.AiNodeGetStr( colorToFloatR, "shadername" ), "Conversion/ColorToFloat" )
			self.assertEqual( arnold.AiNodeGetRGB( colorToFloatR, "param_c" ),  arnold.AtRGB( 0.1, 0.2, 0.3 ))

			colorToFloatG = arnold.AiNodeGetLink( floatToColor, "param_g" )
			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( colorToFloatG ) ), "osl" )
			self.assertEqual( arnold.AiNodeGetStr( colorToFloatG, "output" ), "g" )
			self.assertEqual( arnold.AiNodeGetStr( colorToFloatG, "shadername" ), "Conversion/ColorToFloat" )
			self.assertEqual( arnold.AiNodeGetRGB( colorToFloatG, "param_c" ),  arnold.AtRGB( 0.1, 0.2, 0.3 ))

			colorToFloatB = arnold.AiNodeGetLink( floatToColor, "param_b" )
			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( colorToFloatB ) ), "osl" )
			self.assertEqual( arnold.AiNodeGetStr( colorToFloatB, "output" ), "b" )
			self.assertEqual( arnold.AiNodeGetStr( colorToFloatB, "shadername" ), "Conversion/ColorToFloat" )
			self.assertEqual( arnold.AiNodeGetRGB( colorToFloatB, "param_c" ),  arnold.AtRGB( 0.1, 0.2, 0.3 ))

	def testTraceSets( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Arnold",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			self.temporaryDirectory() + "/test.ass"
		)

		objectNamesAndSets = [
			( "crimsonSphere", IECore.InternedStringVectorData( [ "roundThings", "redThings" ] ) ),
			( "emeraldBall", IECore.InternedStringVectorData( [ "roundThings", "greenThings" ] ) ),
			( "greenFrog", IECore.InternedStringVectorData( [ "livingThings", "greenThings" ] ) ),
			( "scarletPimpernel", IECore.InternedStringVectorData( [ "livingThings", "redThings" ] ) ),
			( "mysterious", IECore.InternedStringVectorData() ),
			( "evasive", None ),
		]

		for objectName, sets in objectNamesAndSets :

			attributes = IECore.CompoundObject()
			if sets is not None :
				attributes["sets"] = sets

			r.object(
				objectName,
				IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) ),
				r.attributes( attributes ),
			)

		r.render()
		del r

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			arnold.AiSceneLoad( universe, self.temporaryDirectory() + "/test.ass", None )

			for objectName, sets in objectNamesAndSets :

				n = arnold.AiNodeLookUpByName( universe, objectName )
				a = arnold.AiNodeGetArray( n, "trace_sets" )

				if sets is None or len( sets ) == 0 :
					sets = [ "__none__" ]

				self.assertEqual( arnold.AiArrayGetNumElements( a.contents ), len( sets ) )
				for i in range( 0, arnold.AiArrayGetNumElements( a.contents ) ) :
					self.assertEqual( arnold.AiArrayGetStr( a, i ), sets[i] )

	def testCurvesAttributes( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Arnold",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			self.temporaryDirectory() + "/test.ass"
		)

		curves = IECoreScene.CurvesPrimitive.createBox( imath.Box3f( imath.V3f( -1 ), imath.V3f( 1 ) ) )

		defaultAttributes = r.attributes( IECore.CompoundObject() )

		pixelWidth1Attributes = r.attributes(
			IECore.CompoundObject( {
				"ai:curves:min_pixel_width" : IECore.FloatData( 1 ),
			} )
		)

		pixelWidth2Attributes = r.attributes(
			IECore.CompoundObject( {
				"ai:curves:min_pixel_width" : IECore.FloatData( 2 ),
			} )
		)

		modeRibbonAttributes = r.attributes(
			IECore.CompoundObject( {
				"ai:curves:mode" : IECore.StringData( "ribbon" ),
			} )
		)

		modeThickAttributes = r.attributes(
			IECore.CompoundObject( {
				"ai:curves:mode" : IECore.StringData( "thick" ),
			} )
		)

		pixelWidth0ModeRibbonAttributes = r.attributes(
			IECore.CompoundObject( {
				"ai:curves:min_pixel_width" : IECore.FloatData( 0 ),
				"ai:curves:mode" : IECore.StringData( "ribbon" ),
			} )
		)

		r.object( "default", curves.copy(), defaultAttributes )
		r.object( "pixelWidth1", curves.copy(), pixelWidth1Attributes )
		r.object( "pixelWidth1Duplicate", curves.copy(), pixelWidth1Attributes )
		r.object( "pixelWidth2", curves.copy(), pixelWidth2Attributes )
		r.object( "modeRibbon", curves.copy(), modeRibbonAttributes )
		r.object( "modeThick", curves.copy(), modeThickAttributes )
		r.object( "pixelWidth0ModeRibbon", curves.copy(), pixelWidth0ModeRibbonAttributes )

		del defaultAttributes, pixelWidth1Attributes, pixelWidth2Attributes, modeRibbonAttributes, modeThickAttributes, pixelWidth0ModeRibbonAttributes

		r.render()
		del r

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			arnold.AiSceneLoad( universe, self.temporaryDirectory() + "/test.ass", None )

			shapes = self.__allNodes( universe, type = arnold.AI_NODE_SHAPE )
			numInstances = len( [ s for s in shapes if arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( s ) ) == "ginstance" ] )
			numCurves = len( [ s for s in shapes if arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( s ) ) == "curves" ] )

			self.assertEqual( numInstances, 4 ) # Can't instance when min_pixel_width != 0
			self.assertEqual( numCurves, 5 )

			self.__assertInstanced(
				universe,
				"default",
				"modeRibbon",
				"pixelWidth0ModeRibbon",
			)

			self.__assertNotInstanced(
				universe,
				"pixelWidth1",
				"pixelWidth1Duplicate",
				"pixelWidth2",
			)

			for name in ( "modeRibbon", "modeThick" ) :
				self.__assertInstanced( universe, name )

			for name, minPixelWidth, mode in (
				( "default", 0, "ribbon" ),
				( "pixelWidth1", 1, "ribbon" ),
				( "pixelWidth1Duplicate", 1, "ribbon" ),
				( "pixelWidth2", 2, "ribbon" ),
				( "modeRibbon", 0, "ribbon" ),
				( "modeThick", 0, "thick" ),
				( "pixelWidth0ModeRibbon", 0, "ribbon" ),
			) :

				node = arnold.AiNodeLookUpByName( universe, name )
				if arnold.AiNodeIs( node, "ginstance" ) :
					shape = arnold.AiNodeGetPtr( node, "node" )
				else :
					shape = node

				self.assertEqual( arnold.AiNodeGetFlt( shape, "min_pixel_width" ), minPixelWidth )
				self.assertEqual( arnold.AiNodeGetStr( shape, "mode" ), mode )

	def testAttributeEditFailures( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Arnold",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Interactive
		)

		polygonMesh = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) )
		subdivMesh = polygonMesh.copy()
		subdivMesh.interpolation = "catmullClark"

		defaultAttributes = r.attributes( IECore.CompoundObject() )

		defaultIterationsAttributes = r.attributes( IECore.CompoundObject( {
			"ai:polymesh:subdiv_iterations" : IECore.IntData( 1 ),
		} ) )

		nonDefaultIterationsAttributes = r.attributes( IECore.CompoundObject( {
			"ai:polymesh:subdiv_iterations" : IECore.IntData( 2 ),
		} ) )

		subdividePolygonsAttributes = r.attributes( IECore.CompoundObject( {
			"ai:polymesh:subdivide_polygons" : IECore.BoolData( True )
		} ) )

		# Polygon mesh
		##############

		# No-op attribute edit should succeed.

		polygonMeshObject = r.object( "polygonMesh", polygonMesh, defaultAttributes )
		self.assertTrue( polygonMeshObject.attributes( defaultAttributes ) )
		self.assertTrue( polygonMeshObject.attributes( defaultIterationsAttributes ) )

		# Changing subdiv iterations should succeed, because it
		# doesn't apply to polygon meshes.

		self.assertTrue( polygonMeshObject.attributes( nonDefaultIterationsAttributes ) )
		self.assertTrue( polygonMeshObject.attributes( defaultAttributes ) )

		# But turning on subdivide polygons should fail, because then
		# we have changed the geometry.

		self.assertFalse( polygonMeshObject.attributes( subdividePolygonsAttributes ) )

		# Likewise, turning off subdivide polygons should fail.

		polygonMeshObject = r.object( "polygonMesh2", polygonMesh, subdividePolygonsAttributes )
		self.assertTrue( polygonMeshObject.attributes( subdividePolygonsAttributes ) )
		self.assertFalse( polygonMeshObject.attributes( defaultAttributes ) )

		# Subdivision mesh
		##################

		# No-op attribute edit should succeed.

		subdivMeshObject = r.object( "subdivMesh", subdivMesh, defaultAttributes )
		self.assertTrue( subdivMeshObject.attributes( defaultAttributes ) )
		self.assertTrue( subdivMeshObject.attributes( defaultIterationsAttributes ) )

		# Turning on subdivide polygons should succeed, because we're already
		# subdividing anyway.

		self.assertTrue( subdivMeshObject.attributes( subdividePolygonsAttributes ) )

		# But changing iterations should fail, because then we're changing the
		# geometry.

		self.assertFalse( subdivMeshObject.attributes( nonDefaultIterationsAttributes ) )

		del defaultAttributes, defaultIterationsAttributes, nonDefaultIterationsAttributes, subdividePolygonsAttributes
		del polygonMeshObject, subdivMeshObject
		del r

	def testStepSizeAndScaleAttribute( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Arnold",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			self.temporaryDirectory() + "/test.ass"
		)

		primitives = {
			"sphere" : IECoreScene.SpherePrimitive(),
			"mesh" : IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) ),
			"curves" : IECoreScene.CurvesPrimitive.createBox( imath.Box3f( imath.V3f( -1 ), imath.V3f( 1 ) ) ),
			"volumeProcedural" : IECoreScene.ExternalProcedural(
				"volume",
				imath.Box3f( imath.V3f( -1 ), imath.V3f( 1 ) ),
			),
		}

		attributes = {
			"default" : IECore.CompoundObject(),
			"stepSizeZero" : IECore.CompoundObject( {
				"ai:shape:step_size" : IECore.FloatData( 0 ),
			} ),
			"stepSizeOne" : IECore.CompoundObject( {
				"ai:shape:step_size" : IECore.FloatData( 1 ),
			} ),
			"stepSizeOneStepScaleHalf" : IECore.CompoundObject( {
				"ai:shape:step_size" : IECore.FloatData( 1 ),
				"ai:shape:step_scale" : IECore.FloatData( 0.5 ),
			} ),
			"stepSizeTwo" : IECore.CompoundObject( {
				"ai:shape:step_size" : IECore.FloatData( 2 ),
			} )
		}

		for pn, p in primitives.items() :
			for an, a in attributes.items() :
				r.object( pn + "_" + an, p, r.attributes( a ) )

		r.render()
		del r

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			arnold.AiSceneLoad( universe, self.temporaryDirectory() + "/test.ass", None )

			shapes = self.__allNodes( universe, type = arnold.AI_NODE_SHAPE )
			numInstances = len( [ s for s in shapes if arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( s ) ) == "ginstance" ] )
			numMeshes = len( [ s for s in shapes if arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( s ) ) == "polymesh" ] )
			numBoxes = len( [ s for s in shapes if arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( s ) ) == "box" ] )
			numSpheres = len( [ s for s in shapes if arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( s ) ) == "sphere" ] )
			numCurves = len( [ s for s in shapes if arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( s ) ) == "curves" ] )
			numVolumes = len( [ s for s in shapes if arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( s ) ) == "volume" ] )

			self.assertEqual( numInstances, 20 )
			self.assertEqual( numMeshes, 4 )
			self.assertEqual( numBoxes, 0 )
			self.assertEqual( numSpheres, 4 )
			self.assertEqual( numCurves, 1 )
			self.assertEqual( numVolumes,  4 )

			self.__assertInstanced(
				universe,
				"mesh_default",
				"mesh_stepSizeZero",
			)

			self.__assertInstanced(
				universe,
				"sphere_default",
				"sphere_stepSizeZero",
			)

			self.__assertInstanced(
				universe,
				"curves_default",
				"curves_stepSizeZero",
				"curves_stepSizeOne",
				"curves_stepSizeTwo",
			)

			for pn in primitives.keys() :
				for an, a in attributes.items() :

					instance = arnold.AiNodeLookUpByName( universe, pn + "_" + an )
					shape = arnold.AiNodeGetPtr( instance, "node" )

					stepSize = a.get( "ai:shape:step_size" )
					stepSize = stepSize.value if stepSize is not None else 0

					stepScale = a.get( "ai:shape:step_scale" )
					stepScale = stepScale.value if stepScale is not None else 1

					stepSize = stepSize * stepScale

					if pn == "curves" :
						self.assertTrue( arnold.AiNodeIs( shape, "curves" ) )
					elif pn == "sphere" :
						self.assertTrue( arnold.AiNodeIs( shape, "sphere" ) )
						self.assertEqual( arnold.AiNodeGetFlt( shape, "step_size" ), stepSize )
					elif pn == "mesh" :
						self.assertTrue( arnold.AiNodeIs( shape, "polymesh" ) )
						self.assertEqual( arnold.AiNodeGetFlt( shape, "step_size" ), stepSize )
					elif pn == "volumeProcedural" :
						self.assertTrue( arnold.AiNodeIs( shape, "volume" ) )
						self.assertEqual( arnold.AiNodeGetFlt( shape, "step_size" ), stepSize )

	def testVolumePaddingAttribute( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Arnold",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			self.temporaryDirectory() + "/test.ass"
		)

		primitives = {
			"sphere" : IECoreScene.SpherePrimitive(),
			"mesh" : IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) ),
			"curves" : IECoreScene.CurvesPrimitive.createBox( imath.Box3f( imath.V3f( -1 ), imath.V3f( 1 ) ) ),
			"volumeProcedural" : IECoreScene.ExternalProcedural(
				"volume",
				imath.Box3f( imath.V3f( -1 ), imath.V3f( 1 ) ),
			),
		}

		attributes = {
			"default" : IECore.CompoundObject(),
			"volumePaddingZero" : IECore.CompoundObject( {
				"ai:shape:volume_padding" : IECore.FloatData( 0 ),
			} ),
			"volumePaddingOne" : IECore.CompoundObject( {
				"ai:shape:volume_padding" : IECore.FloatData( 1 ),
			} ),
			"volumePaddingTwo" : IECore.CompoundObject( {
				"ai:shape:volume_padding" : IECore.FloatData( 2 ),
			} )
		}

		for pn, p in primitives.items() :
			for an, a in attributes.items() :
				r.object( pn + "_" + an, p, r.attributes( a ) )

		r.render()
		del r

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			arnold.AiSceneLoad( universe, self.temporaryDirectory() + "/test.ass", None )

			shapes = self.__allNodes( universe, type = arnold.AI_NODE_SHAPE )
			numInstances = len( [ s for s in shapes if arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( s ) ) == "ginstance" ] )
			numMeshes = len( [ s for s in shapes if arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( s ) ) == "polymesh" ] )
			numBoxes = len( [ s for s in shapes if arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( s ) ) == "box" ] )
			numSpheres = len( [ s for s in shapes if arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( s ) ) == "sphere" ] )
			numCurves = len( [ s for s in shapes if arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( s ) ) == "curves" ] )
			numVolumes = len( [ s for s in shapes if arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( s ) ) == "volume" ] )

			self.assertEqual( numInstances, 16 )
			self.assertEqual( numMeshes, 3 )
			self.assertEqual( numBoxes, 0 )
			self.assertEqual( numSpheres, 3 )
			self.assertEqual( numCurves, 1 )
			self.assertEqual( numVolumes, 3 )

			self.__assertInstanced(
				universe,
				"mesh_default",
				"mesh_volumePaddingZero",
			)

			self.__assertInstanced(
				universe,
				"sphere_default",
				"sphere_volumePaddingZero",
			)

			self.__assertInstanced(
				universe,
				"curves_default",
				"curves_volumePaddingZero",
				"curves_volumePaddingOne",
				"curves_volumePaddingTwo",
			)

			for pn in primitives.keys() :
				for an, a in attributes.items() :

					instance = arnold.AiNodeLookUpByName( universe, pn + "_" + an )
					shape = arnold.AiNodeGetPtr( instance, "node" )

					volumePadding = a.get( "ai:shape:volume_padding" )
					volumePadding = volumePadding.value if volumePadding is not None else 0

					if pn == "curves" :
						self.assertTrue( arnold.AiNodeIs( shape, "curves" ) )
					elif pn == "sphere" :
						self.assertTrue( arnold.AiNodeIs( shape, "sphere" ) )
						self.assertEqual( arnold.AiNodeGetFlt( shape, "volume_padding" ), volumePadding )
					elif pn == "mesh" :
						self.assertTrue( arnold.AiNodeIs( shape, "polymesh" ) )
						self.assertEqual( arnold.AiNodeGetFlt( shape, "volume_padding" ), volumePadding )
					elif pn == "volumeProcedural" :
						self.assertTrue( arnold.AiNodeIs( shape, "volume" ) )
						self.assertEqual( arnold.AiNodeGetFlt( shape, "volume_padding" ), volumePadding )

	def testStepSizeAttributeDefersToProceduralParameter( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Arnold",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			self.temporaryDirectory() + "/test.ass"
		)

		r.object(

			"test",

			IECoreScene.ExternalProcedural(
				"volume",
				imath.Box3f( imath.V3f( -1 ), imath.V3f( 1 ) ),
				IECore.CompoundData( {
					"ai:nodeType" : "volume",
					"step_size" : 0.25,
				} )
			),

			r.attributes( IECore.CompoundObject( {
				"ai:shape:step_size" : IECore.FloatData( 10.0 ),
			} ) )

		)

		r.render()
		del r

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			arnold.AiSceneLoad( universe, self.temporaryDirectory() + "/test.ass", None )

			instance = arnold.AiNodeLookUpByName( universe, "test" )
			self.assertTrue( arnold.AiNodeIs( instance, "ginstance" ) )

			shape = arnold.AiNodeGetPtr( instance, "node" )
			self.assertTrue( arnold.AiNodeIs( shape, "volume" ) )
			self.assertEqual( arnold.AiNodeGetFlt( shape, "step_size" ), 0.25 )

	def testDeclaringCustomOptions( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Arnold",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			self.temporaryDirectory() + "/test.ass"
		)

		r.option( "ai:declare:myCustomOption", IECore.StringData( "myCustomOptionValue" ) )

		r.render()
		del r

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			arnold.AiSceneLoad( universe, self.temporaryDirectory() + "/test.ass", None )
			options = arnold.AiUniverseGetOptions( universe )

			self.assertEqual( arnold.AiNodeGetStr( options, "myCustomOption" ), "myCustomOptionValue" )

	def testFrameAndAASeed( self ) :

		for frame in ( None, 1, 2 ) :
			for seed in ( None, 3, 4 ) :

				r = GafferScene.Private.IECoreScenePreview.Renderer.create(
					"Arnold",
					GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
					self.temporaryDirectory() + "/test.ass"
				)

				if frame is not None :
					r.option( "frame", IECore.IntData( frame ) )
				if seed is not None :
					r.option( "ai:AA_seed", IECore.IntData( seed ) )

				r.render()
				del r

				with IECoreArnold.UniverseBlock( writable = True ) as universe :

					arnold.AiSceneLoad( universe, self.temporaryDirectory() + "/test.ass", None )

					options = arnold.AiUniverseGetOptions( universe )
					self.assertEqual(
						arnold.AiNodeGetInt( options, "AA_seed" ),
						seed or frame or 1
					)

	def testLogDirectoryCreation( self ) :

		# Directory for log file should be made automatically if
		# it doesn't exist.

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Arnold",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			self.temporaryDirectory() + "/test.ass"
		)

		r.option( "ai:log:filename", IECore.StringData( self.temporaryDirectory() + "/test/log.txt" ) )
		r.render()

		self.assertTrue( os.path.isdir( self.temporaryDirectory() + "/test" ) )

		# And it should still be OK to pass a filename where the directory already exists

		r.option( "ai:log:filename", IECore.StringData( self.temporaryDirectory() + "/log.txt" ) )
		r.render()

		self.assertTrue( os.path.isdir( self.temporaryDirectory() ) )

		# Passing an empty filename should be fine too.

		r.option( "ai:log:filename", IECore.StringData( "" ) )
		r.render()

		# Trying to write to a read-only location should result in an
		# error message.

		os.makedirs( self.temporaryDirectory() + "/readOnly" )
		os.chmod( self.temporaryDirectory() + "/readOnly", 444 )

		with IECore.CapturingMessageHandler() as mh :
			r.option( "ai:log:filename", IECore.StringData( self.temporaryDirectory() + "/readOnly/nested/log.txt" ) )
			r.render()

		self.assertEqual( len( mh.messages ), 1 )
		self.assertEqual( mh.messages[0].level, IECore.Msg.Level.Error )
		self.assertTrue( "Permission denied" in mh.messages[0].message )

	def testStatsAndLog( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Arnold",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch,
		)

		r.option( "ai:log:filename", IECore.StringData( self.temporaryDirectory() + "/test/test_log.txt" ) )
		r.option( "ai:statisticsFileName", IECore.StringData( self.temporaryDirectory() + "/test/test_stats.json" ) )
		r.option( "ai:profileFileName", IECore.StringData( self.temporaryDirectory() + "/test/test_profile.json" ) )

		c = r.camera(
			"testCamera",
			IECoreScene.Camera(
				parameters = {
					"projection" : "orthographic"
				}
			),
			r.attributes( IECore.CompoundObject() )
		)

		r.output(
			"testBeauty",
			IECoreScene.Output(
				self.temporaryDirectory() + "/beauty.exr",
				"exr",
				"rgba"
			)
		)

		r.option( "camera", IECore.StringData( "testCamera" ) )

		r.render()

		# required to flush the profile json
		del r

		with open( self.temporaryDirectory() + "/test/test_log.txt", "r" ) as logHandle:
			self.assertNotEqual( logHandle.read().find( "rendering image at 640 x 480" ), -1 )

		with open( self.temporaryDirectory() + "/test/test_stats.json", "r" ) as statsHandle:
			stats = json.load( statsHandle )["render 0000"]
			self.assertTrue( "microseconds" in stats["scene creation time"] )
			self.assertTrue( "microseconds" in stats["frame time"] )
			self.assertTrue( "peak CPU memory used" in stats )

			self.assertTrue( "ray counts" in stats )

		# This test runs OK in isolation, but previous uses of ArnoldRenderer seem
		# to stop Arnold from writing the profile file.
		if int(arnold.AiGetVersion()[0]) == 7 :
			self.skipTest( "Profiling broken in Arnold 7" )

		with open( self.temporaryDirectory() + "/test/test_profile.json", "r" ) as profileHandle :
			stats = json.load( profileHandle )["traceEvents"]
			driverEvents = [ x for x in stats if x["name"] == "ieCoreArnold:display:testBeauty" ]
			self.assertEqual( driverEvents[0]["cat"], "driver_exr" )

	def testMessageHandler( self ) :

		RenderType = GafferScene.Private.IECoreScenePreview.Renderer.RenderType

		for renderType, fileName, output in (
			( RenderType.Batch, "", IECoreScene.Output( self.temporaryDirectory() + "/beauty.exr", "exr", "rgba" ) ),
			( RenderType.Interactive, "", None ),
			( RenderType.SceneDescription, self.temporaryDirectory() + "/test.ass" , None )
		) :

			with IECore.CapturingMessageHandler() as fallbackHandler :

				handler = IECore.CapturingMessageHandler()

				r = GafferScene.Private.IECoreScenePreview.Renderer.create(
					"Arnold",
					renderType,
					fileName = fileName,
					messageHandler = handler
				)

				r.option( "ai:console:info", IECore.BoolData( True ) )
				r.option( "ai:console:progress", IECore.BoolData( True ) )
				r.option( "ai:invalid", IECore.BoolData( True ) )

				if output :
					r.output( "testOutput", output )

				r.render()

				if renderType == RenderType.Interactive :
					time.sleep( 1 )

				# We need to delete this instance, before we construct the next one in
				# the next loop iteration, or the constructor will throw.
				del r

				# We should have at least 1 message from our invalid option plus
				# _something_ from the renderer's own output stream.
				if renderType == RenderType.SceneDescription and int(arnold.AiGetVersion()[0]) == 7 :
					# A bug in Arnold associates the `[ ass ] Writing...` message with the wrong render session
					# in the message callback.
					self.skipTest( "SceneDescription Messaging broken in Arnold 7" )
				else :
					self.assertGreater( len(handler.messages), 1, msg=str(renderType) )

				self.assertEqual( [ m.message for m in fallbackHandler.messages ], [], msg=str(renderType) )

	@unittest.skipIf( [ int( v ) for v in arnold.AiGetVersion()[:3] ] < [ 7, 0, 0 ], "Two renders not supported" )
	# Arnold's message handling is broken. The errors from `AiNodeSetInt()` are sent
	# to the render session for the default universe instead of the render session for
	# the universe the node is in.
	@unittest.expectedFailure
	def testMessageHandlersForTwoRenders( self ) :

		# Make two renderers, each with a different message handler.

		mh1 = IECore.CapturingMessageHandler()
		mh2 = IECore.CapturingMessageHandler()

		r1 = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Arnold",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Interactive,
			messageHandler = mh1
		)


		r2 = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Arnold",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Interactive,
			messageHandler = mh2
		)

		# Generate some artificial errors.

		u1 = ctypes.cast( r1.command( "ai:queryUniverse", {} ), ctypes.POINTER( arnold.AtUniverse ) )
		u2 = ctypes.cast( r2.command( "ai:queryUniverse", {} ), ctypes.POINTER( arnold.AtUniverse ) )

		arnold.AiNodeSetInt( arnold.AiUniverseGetOptions( u1 ), "invalid1", 10 )
		arnold.AiNodeSetInt( arnold.AiUniverseGetOptions( u2 ), "invalid2", 10 )

		# Check that they were directed to the appropriate handler.

		self.assertEqual( len( mh1.messages ), 1 )
		self.assertIn( "invalid1", mh1.messages[0].message )
		self.assertEqual( len( mh2.messages ), 1 )
		self.assertIn( "invalid2", mh2.messages[0].message )

	def testProcedural( self ) :

		class SphereProcedural( GafferScene.Private.IECoreScenePreview.Procedural ) :

			def render( self, renderer ) :

				for i in range( 0, 5 ) :
					o = renderer.object(
						"/sphere{0}".format( i ),
						IECoreScene.SpherePrimitive(),
						renderer.attributes( IECore.CompoundObject() ),
					)
					o.transform( imath.M44f().translate( imath.V3f( i, 0, 0 ) ) )

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Arnold",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch,
		)

		r.output(
			"test",
			IECoreScene.Output(
				self.temporaryDirectory() + "/beauty.exr",
				"exr",
				"rgba",
				{
				}
			)
		)

		r.object( "/sphere", IECoreScene.SpherePrimitive(), r.attributes( IECore.CompoundObject() ) )
		r.object( "/procedural", SphereProcedural(), r.attributes( IECore.CompoundObject() ) )

		universe = ctypes.cast( r.command( "ai:queryUniverse", {} ), ctypes.POINTER( arnold.AtUniverse ) )
		procedurals = self.__allNodes( universe, nodeEntryName = "procedural" )
		self.assertEqual( len( procedurals ), 1 )

		r.render()

		for i in range( 0, 5 ) :
			# Look for spheres of the correct types parented under the procedural
			sphere = arnold.AiNodeLookUpByName( universe, "/sphere%i" % i, procedurals[0] )
			# We actually expect the node to be a ginstance, but during `render()` Arnold seems
			# to switch the type of ginstances to match the type of the node they are instancing.
			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( sphere ) ), "sphere" )

		# We expect to find 8 "spheres" - the 6 ginstances masquerading
		# as spheres (1 from the top level sphere, 5 from the procedural),
		# and the two true spheres that they reference.
		spheres = self.__allNodes( universe, nodeEntryName = "sphere" )
		self.assertEqual( len( spheres ), 8 )
		# Use node names to distinguish the true spheres.
		trueSpheres = [ x for x in spheres if "sphere" not in arnold.AiNodeGetName( x ) ]
		self.assertEqual( len( trueSpheres ), 2 )
		# Check they both have names
		self.assertTrue( all( [ arnold.AiNodeGetName( x ) for x in trueSpheres ] ) )

	def __assertProceduralsInheritShaders( self, inheritedColor, internalColor ) :

		def colorAttributes( renderer, color ) :

			attributes = IECore.CompoundObject()
			if color is not None :
				attributes["ai:surface"] = IECoreScene.ShaderNetwork(
					{
						"output" : IECoreScene.Shader( "flat", "ai:surface",  { "color" : color } ),
					},
					output = "output"
				)

			return renderer.attributes( attributes )

		class SphereProcedural( GafferScene.Private.IECoreScenePreview.Procedural ) :

			def __init__( self, color = None ) :

				GafferScene.Private.IECoreScenePreview.Procedural.__init__( self )
				self.__color = color

			def render( self, renderer ) :

				renderer.object(
					"/sphere",
					IECoreScene.SpherePrimitive(),
					colorAttributes( renderer, self.__color ),
				)

		IECore.registerRunTimeTyped( SphereProcedural )

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Arnold",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch,
		)

		outputFileName = self.temporaryDirectory() + "/beauty.exr"
		r.output(
			"test",
			IECoreScene.Output(
				outputFileName,
				"exr",
				"rgba",
				{
				}
			)
		)

		r.object( "/procedural", SphereProcedural( color = internalColor ), colorAttributes( r, color = inheritedColor ) )
		r.render()

		image = IECoreImage.ImageReader( outputFileName ).read()
		dimensions = image.dataWindow.size() + imath.V2i( 1 )
		centreIndex = dimensions.x * int( dimensions.y * 0.5 ) + int( dimensions.x * 0.5 )
		color = imath.Color3f( image["R"][centreIndex], image["G"][centreIndex], image["B"][centreIndex] )
		self.assertEqual( color, internalColor or inheritedColor )

	def testProceduralShaderInheritance( self ) :

		self.__assertProceduralsInheritShaders( None, imath.Color3f( 0, 1, 0 ) )
		self.__assertProceduralsInheritShaders( imath.Color3f( 1, 0, 0 ), None )
		self.__assertProceduralsInheritShaders( imath.Color3f( 1, 0, 0 ), imath.Color3f( 0, 1, 0 ) )

	def testProceduralInstancingWithAttributes( self ) :

		class SphereProcedural( GafferScene.Private.IECoreScenePreview.Procedural ) :

			def render( self, renderer ) :

				renderer.object(
					"/sphere",
					IECoreScene.SpherePrimitive(),
					renderer.attributes( IECore.CompoundObject() ),
				)

		IECore.registerRunTimeTyped( SphereProcedural )

		# Because we have to manually emulate attribute inheritance for procedural contents,
		# we have to be careful not to instance identical procedurals if they have different
		# attributes. We must make an exception for "user:" attributes though, since Arnold
		# does support those properly, and it is very common to vary user attributes on
		# otherwise identical procedurals (think GafferScene::Instancer).

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Arnold",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch,
		)

		attributeVariants = {
			"defaultAttributes" : IECore.CompoundObject(),
			"cameraOnAttributes" : IECore.CompoundObject( { "ai:visibility:camera" : IECore.BoolData( True ) } ),
			"cameraOffAttributes" : IECore.CompoundObject( { "ai:visibility:camera" : IECore.BoolData( False ) } ),
			"userAttributes" : IECore.CompoundObject( { "user:a" : IECore.IntData( 10 ) } ),
			"userAttributes2" : IECore.CompoundObject( { "user:a" : IECore.IntData( 11 ), "user:b" : IECore.IntData( 12 ) } ),
		}

		attributeVariants["cameraOffUserAttributes"] = attributeVariants["userAttributes"].copy()
		attributeVariants["cameraOffUserAttributes"].update( attributeVariants["cameraOffAttributes"] )

		objectVariants = {}
		for name, attributes in attributeVariants.items() :

			objectVariants[name] = renderer.object(
				name,
				SphereProcedural(),
				renderer.attributes( attributes )
			)

		# Check that we are instancing procedurals as expected.

		universe = ctypes.cast( renderer.command( "ai:queryUniverse", {} ), ctypes.POINTER( arnold.AtUniverse ) )
		self.assertEqual( len( self.__allNodes( universe, nodeEntryName = "procedural" ) ), 2 )
		self.assertEqual( len( self.__allNodes( universe, nodeEntryName = "ginstance" ) ), len( attributeVariants ) )

		instanceSharers = [
			# All the same because camera visibility is on, and user attributes arent' relevant.
			( "defaultAttributes", "cameraOnAttributes", "userAttributes", "userAttributes2" ),
			# All the same because camera visibility is off.
			( "cameraOffAttributes", "cameraOffUserAttributes" ),
		]

		for sharers in instanceSharers :
			firstNode = arnold.AiNodeLookUpByName( universe, sharers[0] )
			for name in sharers :
				node = arnold.AiNodeLookUpByName( universe, name )
				self.assertTrue( arnold.AiNodeIs( node, "ginstance" ) )
				self.assertReferSameNode(
					arnold.AiNodeGetPtr( node, "node" ),
					arnold.AiNodeGetPtr( firstNode, "node" ),
				)

		# Check that the user attributes are applied on the `ginstance` nodes.

		for name, attributes in attributeVariants.items() :

			node = arnold.AiNodeLookUpByName( universe, name )
			for attributeName, attributeValue in attributes.items() :
				if attributeName.startswith( "user:" ) :
					self.assertEqual(
						arnold.AiNodeGetInt( node, attributeName ),
						attributeValue.value
					)

		# Check that attempts to edit the attributes fail if they would
		# require edits to the children of the procedural.

		self.assertTrue(
			objectVariants["defaultAttributes"].attributes(
				renderer.attributes( attributeVariants["cameraOnAttributes"] )
			)
		)

		self.assertFalse(
			objectVariants["defaultAttributes"].attributes(
				renderer.attributes( attributeVariants["cameraOffAttributes"] )
			)
		)

		# Check that the user attributes are not applied to the child nodes
		# generated by the procedurals.

		renderer.output(
			"test",
			IECoreScene.Output(
				self.temporaryDirectory() + "/beauty.exr",
				"exr",
				"rgba",
				{
				}
			)
		)

		renderer.render()

		for sphere in self.__allNodes( universe, nodeEntryName = "sphere" ) :
			self.assertIsNone( arnold.AiNodeLookUpUserParameter( sphere, "user:a" ) )
			self.assertIsNone( arnold.AiNodeLookUpUserParameter( sphere, "user:b" ) )

	def testProceduralWithCurves( self ) :

		class CurvesProcedural( GafferScene.Private.IECoreScenePreview.Procedural ) :

			def __init__( self, minPixelWidth ) :

				GafferScene.Private.IECoreScenePreview.Procedural.__init__( self )

				self.__minPixelWidth = minPixelWidth

			def render( self, renderer ) :

				curves = IECoreScene.CurvesPrimitive(
					IECore.IntVectorData( [ 4 ] ),
					IECore.CubicBasisf.catmullRom(),
					False,
					IECore.V3fVectorData( [
						imath.V3f( 0, -1, 0 ),
						imath.V3f( 0, -1, 0 ),
						imath.V3f( 0, 1, 0 ),
						imath.V3f( 0, 1, 0 ),
					] )
				)

				renderer.object(
					"/curves",
					curves,
					renderer.attributes( IECore.CompoundObject( {
						"ai:curves:min_pixel_width" : IECore.FloatData( self.__minPixelWidth )
					} ) ),
				)

		IECore.registerRunTimeTyped( CurvesProcedural )

		# We repeat the test with and without a min pixel width.
		# This exercises the instanced and non-instanced code paths
		# in the procedural renderer backend.
		for minPixelWidth in ( 0.0, 1.0 ) :

			renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
				"Arnold",
				GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch,
			)

			renderer.object(
				"/procedural",
				CurvesProcedural( minPixelWidth ),
				renderer.attributes( IECore.CompoundObject() )
			).transform( imath.M44f().translate( imath.V3f( 0, 0, -1 ) ) )

			outputFileName = os.path.join( self.temporaryDirectory(), "beauty.exr" )
			renderer.output(
				"test",
				IECoreScene.Output(
					outputFileName,
					"exr",
					"rgba",
					{
					}
				)
			)

			renderer.render()
			del renderer

			# We should find the curves visible in the centre pixel.
			image = IECoreImage.ImageReader( outputFileName ).read()
			dimensions = image.dataWindow.size() + imath.V2i( 1 )
			centreIndex = dimensions.x * int( dimensions.y * 0.5 ) + int( dimensions.x * 0.5 )
			color = imath.Color3f( image["R"][centreIndex], image["G"][centreIndex], image["B"][centreIndex] )
			self.assertEqual( color, imath.Color3f( 1 ) )

	@staticmethod
	def __aovShaders( universe ) :

		options = arnold.AiUniverseGetOptions( universe )
		shaders = arnold.AiNodeGetArray( options, "aov_shaders" )

		result = {}
		for i in range( arnold.AiArrayGetNumElements( shaders ) ):
			node = arnold.cast( arnold.AiArrayGetPtr( shaders, i ), arnold.POINTER( arnold.AtNode ) )
			nodeType = arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( node ) )
			result[nodeType] = node

		return result

	def testAOVShaders( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Arnold",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Interactive
		)

		r.option( "ai:aov_shader:test", IECoreScene.ShaderNetwork(
			shaders = {
				"rgbSource" : IECoreScene.Shader( "float_to_rgb", "ai:shader" ),
				"output" : IECoreScene.Shader( "aov_write_rgb", "ai:shader" ),
			},
			connections = [
				( ( "rgbSource", "" ), ( "output", "aov_input" ) ),
			],
			output = "output"
		) )

		universe = ctypes.cast( r.command( "ai:queryUniverse", {} ), ctypes.POINTER( arnold.AtUniverse ) )

		self.assertEqual( set( self.__aovShaders( universe ).keys() ), set( [ "aov_write_rgb" ] ) )
		source = arnold.AiNodeGetLink( self.__aovShaders( universe )["aov_write_rgb"], "aov_input" )
		self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( source ) ), "float_to_rgb" )

		# Add another
		r.option( "ai:aov_shader:test2", IECoreScene.ShaderNetwork( { "output" : IECoreScene.Shader( "aov_write_float", "ai:shader" ) }, output = "output" ) )
		self.assertEqual( set( self.__aovShaders( universe ).keys() ), set( [ "aov_write_rgb", "aov_write_float" ] ) )

		# Add overwrite
		r.option( "ai:aov_shader:test", IECoreScene.ShaderNetwork( { "output" : IECoreScene.Shader( "aov_write_int", "ai:shader" ) }, output = "output" ) )
		self.assertEqual( set( self.__aovShaders( universe ).keys() ), set( [ "aov_write_int", "aov_write_float" ] ) )

		r.option( "ai:aov_shader:test", None )
		self.assertEqual( set( self.__aovShaders( universe ).keys() ), set( [ "aov_write_float" ] ) )

		r.option( "ai:aov_shader:test2", None )
		self.assertEqual( set( self.__aovShaders( universe ).keys() ), set() )

		del r

	def testAtmosphere( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Arnold",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Interactive
		)

		universe = ctypes.cast( r.command( "ai:queryUniverse", {} ), ctypes.POINTER( arnold.AtUniverse ) )
		options = arnold.AiUniverseGetOptions( universe )
		self.assertEqual( arnold.AiNodeGetPtr( options, "atmosphere" ), None )

		r.option(
			"ai:atmosphere",
			IECoreScene.ShaderNetwork( { "output" : IECoreScene.Shader( "atmosphere_volume", "ai:shader" ) }, output = "output" )
		)

		shader = arnold.AiNodeGetPtr( options, "atmosphere" )
		self.assertEqual(
			arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( shader ) ),
			"atmosphere_volume",
		)

		r.option( "ai:atmosphere", None )
		self.assertEqual( arnold.AiNodeGetPtr( options, "atmosphere" ), None )

	def testBackground( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Arnold",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Interactive
		)

		universe = ctypes.cast( r.command( "ai:queryUniverse", {} ), ctypes.POINTER( arnold.AtUniverse ) )
		options = arnold.AiUniverseGetOptions( universe )
		self.assertEqual( arnold.AiNodeGetPtr( options, "background" ), None )

		r.option(
			"ai:background",
			IECoreScene.ShaderNetwork( { "output" : IECoreScene.Shader( "flat", "ai:shader" ) }, output = "output" )
		)

		shader = arnold.AiNodeGetPtr( options, "background" )
		self.assertEqual(
			arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( shader ) ),
			"flat",
		)

		r.option( "ai:background", None )
		self.assertEqual( arnold.AiNodeGetPtr( options, "background" ), None )

	def testColorManager( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Arnold",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Interactive
		)

		universe = ctypes.cast( r.command( "ai:queryUniverse", {} ), ctypes.POINTER( arnold.AtUniverse ) )
		options = arnold.AiUniverseGetOptions( universe )
		self.assertEqual( arnold.AiNodeGetPtr( options, "color_manager" ), None )

		r.option(
			"ai:color_manager",
			IECoreScene.ShaderNetwork(
				{
					"output" : IECoreScene.Shader(
						"color_manager_ocio", "ai:color_manager",
						{
							"config" : "something.ocio",
							"color_space_narrow" : "narrow",
							"color_space_linear" : "linear",
						}
					)
				},
				output = "output"
			)
		)

		colorManager = arnold.AiNodeGetPtr( options, "color_manager" )
		self.assertEqual(
			arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( colorManager ) ),
			"color_manager_ocio",
		)

		self.assertEqual( arnold.AiNodeGetStr( colorManager, "config" ), "something.ocio" )
		self.assertEqual( arnold.AiNodeGetStr( colorManager, "color_space_narrow" ), "narrow" )
		self.assertEqual( arnold.AiNodeGetStr( colorManager, "color_space_linear" ), "linear" )

		r.option( "ai:color_manager", None )
		self.assertEqual( arnold.AiNodeGetPtr( options, "color_manager" ), None )

	def testBlockerMotionBlur( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Arnold",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			self.temporaryDirectory() + "/test.ass"
		)

		o = r.lightFilter(
			"/lightFilter", IECore.NullObject(),
			r.attributes( IECore.CompoundObject( {
				"ai:lightFilter:filter" : IECoreScene.ShaderNetwork(
					shaders = {
						"filter" : IECoreScene.Shader( "light_blocker", "ai:lightFilter" ),
					},
					output = "filter"
				)
			} ) )
		)

		# Ask for transform motion blur

		o.transform(
			[ imath.M44f().translate( imath.V3f( 1, 0, 0 ) ), imath.M44f().translate( imath.V3f( 2, 0, 0 ) ) ],
			[ 0, 1 ]
		)

		r.render()

		del o
		del r

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			arnold.AiSceneLoad( universe, self.temporaryDirectory() + "/test.ass", None )

			# Since Arnold's `light_blocker` node doesn't support transform blur,
			# we just expect a single matrix with the first transform sample.

			node = arnold.AiNodeLookUpByName( universe, "lightFilter:/lightFilter" )
			self.assertEqual(
				self.__m44f( arnold.AiNodeGetMatrix( node, "geometry_matrix" ) ),
				imath.M44f().translate( imath.V3f( 1, 0, 0 ) )
			)

	def __testVDB( self, stepSize = None, stepScale = 1.0, expectedSize = 0.0, expectedScale = 1.0 ) :

		import IECoreVDB

		tmpFile = self.temporaryDirectory() + "/test.ass"

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Arnold",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			tmpFile
		)

		attributes = IECore.CompoundObject( {
			"ai:volume:velocity_scale" : IECore.FloatData( 10 ),
			"ai:volume:velocity_fps" : IECore.FloatData( 25 ),
			"ai:volume:velocity_outlier_threshold" : IECore.FloatData( 0.5 ),
		} )

		if stepSize is not None:
			attributes["ai:volume:step_size"] = IECore.FloatData( stepSize )

		if stepScale is not None:
			attributes["ai:volume:step_scale"] = IECore.FloatData( stepScale )

		# Camera needs to be added first as it's being used for translating the VDB.
		# We are doing the same when translating actual Gaffer scenes here:
		# https://github.com/GafferHQ/gaffer/blob/master/src/GafferScene/Render.cpp#L254
		r.camera(
			"testCamera",
			IECoreScene.Camera(
				parameters = {
					"shutter" : imath.V2f( 10.75, 11.25 )
				}
			),
			r.attributes( IECore.CompoundObject() )
		)

		r.object( "test_vdb", IECoreVDB.VDBObject(), r.attributes( attributes ) )

		r.option( "camera", IECore.StringData( "testCamera" ) )

		r.render()
		del r

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			arnold.AiSceneLoad( universe, tmpFile, None )

			shapes = self.__allNodes( universe, type = arnold.AI_NODE_SHAPE )
			numInstances = len( [ s for s in shapes if arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( s ) ) == "ginstance" ] )
			numVDBs = len( [ s for s in shapes if arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( s ) ) == "volume" ] )

			self.assertEqual( len( shapes ), 2 )
			self.assertEqual( numInstances, 1 )
			self.assertEqual( numVDBs, 1 )

			vdbInstance = arnold.AiNodeLookUpByName( universe, "test_vdb" )
			vdbShape = arnold.AiNodeGetPtr( vdbInstance, "node" )

			self.assertEqual( arnold.AiNodeGetFlt( vdbShape, "velocity_scale" ), 10 )
			self.assertEqual( arnold.AiNodeGetFlt( vdbShape, "velocity_fps" ), 25 )
			self.assertEqual( arnold.AiNodeGetFlt( vdbShape, "velocity_outlier_threshold" ), 0.5 )

			# make sure motion_start and motion_end parameters were set according to the active camera's shutter
			self.assertEqual( arnold.AiNodeGetFlt( vdbShape, "motion_start" ), 10.75 )
			self.assertEqual( arnold.AiNodeGetFlt( vdbShape, "motion_end" ), 11.25 )

			self.assertAlmostEqual( arnold.AiNodeGetFlt( vdbShape, "step_size"), expectedSize, 7 )
			self.assertAlmostEqual( arnold.AiNodeGetFlt( vdbShape, "step_scale"), expectedScale, 7 )

	def testVDBs( self ) :

		self.__testVDB( stepSize = None, stepScale = 0.25, expectedSize = 0.0, expectedScale = 0.25 )
		self.__testVDB( stepSize = 0.1, stepScale = None, expectedSize = 0.1, expectedScale = 1.0 )
		self.__testVDB( stepSize = None, stepScale = None, expectedSize = 0.0, expectedScale = 1.0 )
		self.__testVDB( stepSize = 1.0, stepScale = 0.5, expectedSize = 0.5, expectedScale = 1.0 )

	def testCameraAttributes( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Arnold",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			self.temporaryDirectory() + "/test.ass"
		)

		r.camera(
			"/camera",
			IECoreScene.Camera( { "projection" : "perspective" } ),
			r.attributes(
				IECore.CompoundObject( {
					"ai:filtermap" : IECoreScene.ShaderNetwork(
						shaders = { "out" : IECoreScene.Shader( "noise" ) },
						output = "out"
					),
					"ai:uv_remap" : IECoreScene.ShaderNetwork(
						shaders = { "out" : IECoreScene.Shader( "flat" ) },
						output = "out"
					)
				} )
			),
		)

		r.option( "camera", IECore.StringData( "/camera" ) )

		r.render()
		del r

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			arnold.AiSceneLoad( universe, self.temporaryDirectory() + "/test.ass", None )

			cameraNode = arnold.AiNodeLookUpByName( universe, "/camera" )

			filterMapNode = arnold.AiNodeGetPtr( cameraNode, "filtermap" )
			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( filterMapNode ) ), "noise" )

			uvRemapNode =  arnold.AiNodeGetLink( cameraNode, "uv_remap" )
			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( uvRemapNode ) ), "flat" )

	def testCantEditQuadLightColor( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Arnold",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Interactive,
		)

		lightParameters = { "color" : IECore.Color3fData( imath.Color3f(1,0,0) ), "exposure" : IECore.FloatData( 1 ) }
		lightParametersChanged = { "color" : IECore.Color3fData( imath.Color3f(0,1,0) ), "exposure" : IECore.FloatData( 2 ) }
		texParameters = { "multiply" : IECore.Color3fData( imath.Color3f(1,0,0) ) }
		texParametersChanged = { "multiply" : IECore.Color3fData( imath.Color3f(0,1,0) ) }

		skydomeLightShader = IECoreScene.ShaderNetwork( { "light" : IECoreScene.Shader( "skydome_light", "ai:light", lightParameters ), }, output = "light" )
		skydomeLight = r.light(
			"skydomeLight",
			None,
			r.attributes(
				IECore.CompoundObject( {
					"ai:light" : skydomeLightShader
				} )
			)
		)

		quadLightShader = IECoreScene.ShaderNetwork( { "light" : IECoreScene.Shader( "quad_light", "ai:light", lightParameters ), }, output = "light" )
		quadLight = r.light(
			"quadLight",
			None,
			r.attributes(
				IECore.CompoundObject( {
					"ai:light" : quadLightShader
				} )
			)
		)

		# All edits of the skydome light should succeed ( The bug we're hacking around only affects quad_light )
		skydomeLightShader = IECoreScene.ShaderNetwork( { "light" : IECoreScene.Shader( "skydome_light", "ai:light", lightParametersChanged), }, output = "light" )
		self.assertTrue( skydomeLight.attributes( r.attributes( IECore.CompoundObject( { "ai:light" : skydomeLightShader } ) ) ) )
		skydomeLightShader = IECoreScene.ShaderNetwork( { "light" : IECoreScene.Shader( "skydome_light", "ai:light", lightParameters), "tex" : IECoreScene.Shader( "image", "ai:shader", texParameters) }, [(("tex", ""), ("light", "color"))], output = "light" )
		self.assertTrue( skydomeLight.attributes( r.attributes( IECore.CompoundObject( { "ai:light" : skydomeLightShader } ) ) ) )
		skydomeLightShader = IECoreScene.ShaderNetwork( { "light" : IECoreScene.Shader( "skydome_light", "ai:light", lightParametersChanged), "tex" : IECoreScene.Shader( "image", "ai:shader", texParameters) }, [(("tex", ""), ("light", "color"))], output = "light" )
		self.assertTrue( skydomeLight.attributes( r.attributes( IECore.CompoundObject( { "ai:light" : skydomeLightShader } ) ) ) )
		skydomeLightShader = IECoreScene.ShaderNetwork( { "light" : IECoreScene.Shader( "skydome_light", "ai:light", lightParametersChanged), "tex" : IECoreScene.Shader( "image", "ai:shader", texParametersChanged) }, [(("tex", ""), ("light", "color"))], output = "light" )
		self.assertTrue( skydomeLight.attributes( r.attributes( IECore.CompoundObject( { "ai:light" : skydomeLightShader } ) ) ) )

		# Most edits of the quad lights should succeed
		quadLightShader = IECoreScene.ShaderNetwork( { "light" : IECoreScene.Shader( "quad_light", "ai:light", lightParametersChanged), }, output = "light" )
		self.assertTrue( quadLight.attributes( r.attributes( IECore.CompoundObject( { "ai:light" : quadLightShader } ) ) ) )
		quadLightShader = IECoreScene.ShaderNetwork( { "light" : IECoreScene.Shader( "quad_light", "ai:light", lightParameters), "tex" : IECoreScene.Shader( "image", "ai:shader", texParameters) }, [(("tex", ""), ("light", "color"))], output = "light" )
		self.assertTrue( quadLight.attributes( r.attributes( IECore.CompoundObject( { "ai:light" : quadLightShader } ) ) ) )
		quadLightShader = IECoreScene.ShaderNetwork( { "light" : IECoreScene.Shader( "quad_light", "ai:light", lightParametersChanged), "tex" : IECoreScene.Shader( "image", "ai:shader", texParameters) }, [(("tex", ""), ("light", "color"))], output = "light" )
		self.assertTrue( quadLight.attributes( r.attributes( IECore.CompoundObject( { "ai:light" : quadLightShader } ) ) ) )

		# The one exception is changing a parameter of a shader upstream of the color parameter
		quadLightShader = IECoreScene.ShaderNetwork( { "light" : IECoreScene.Shader( "quad_light", "ai:light", lightParametersChanged), "tex" : IECoreScene.Shader( "image", "ai:shader", texParametersChanged) }, [(("tex", ""), ("light", "color"))], output = "light" )
		self.assertFalse( quadLight.attributes( r.attributes( IECore.CompoundObject( { "ai:light" : quadLightShader } ) ) ) )

		# Must delete objects before the renderer.
		del skydomeLight, quadLight

	def testAnimatedCameras( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Arnold",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			self.temporaryDirectory() + "/test.ass"
		)

		c1 = IECoreScene.Camera()
		c1.setProjection( "perspective" )
		c1.setFocalLengthFromFieldOfView( 45 )
		c2 = c1.copy()
		c2.setFocalLengthFromFieldOfView( 55 )

		r.camera(
			"testCamera",
			[ c1, c2 ], [ 1, 2 ],
			r.attributes( IECore.CompoundObject() ),
		)

		r.render()
		del r

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			arnold.AiSceneLoad( universe, self.temporaryDirectory() + "/test.ass", None )

			n = arnold.AiNodeLookUpByName( universe, "testCamera" )
			self.assertTrue( arnold.AiNodeEntryGetType( arnold.AiNodeGetNodeEntry( n ) ), arnold.AI_NODE_CAMERA )

			self.assertEqual( arnold.AiNodeGetFlt( n, "motion_start" ), 1 )
			self.assertEqual( arnold.AiNodeGetFlt( n, "motion_end" ), 2 )

			array = arnold.AiNodeGetArray( n, "fov" )
			self.assertEqual( arnold.AiArrayGetNumElements( array ), 1 )
			self.assertEqual( arnold.AiArrayGetNumKeys( array ), 2 )

			self.assertAlmostEqual( arnold.AiArrayGetFlt( array, 0 ), c1.calculateFieldOfView().x, delta = 0.00001 )
			self.assertAlmostEqual( arnold.AiArrayGetFlt( array, 1 ), c2.calculateFieldOfView().x, delta = 0.00001 )

	def testImager( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Arnold",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			self.temporaryDirectory() + "/test.ass"
		)

		# Create an output

		r.output(
			"test1",
			IECoreScene.Output(
				self.temporaryDirectory() + "/beauty1.exr", "exr", "rgba", {}
			)
		)

		# Specify the imagers

		r.option(
			"ai:imager",
			IECoreScene.ShaderNetwork(
				{
					"exposure" : IECoreScene.Shader(
						"imager_exposure", "ai:imager",
						{ "exposure" : 2.5 },
					),
					"lensEffects" : IECoreScene.Shader(
						"imager_lens_effects", "ai:imager",
						{ "bloom_radius" : 5 },
					),
				},
				connections = [
					( "exposure", ( "lensEffects", "input" ) )
				],
				output = "lensEffects",
			)
		)

		# Create a second output

		r.output(
			"test2",
			IECoreScene.Output(
				self.temporaryDirectory() + "/beauty2.exr", "exr", "rgba", {}
			)
		)

		r.render()
		del r

		# We expect the imager to be applied to both outputs (independent of
		# creation order).

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			arnold.AiSceneLoad( universe, self.temporaryDirectory() + "/test.ass", None )

			drivers = self.__allNodes( universe, type = arnold.AI_NODE_DRIVER, nodeEntryName = "driver_exr" )
			self.assertEqual( len( drivers ), 2 )

			for driver in drivers :

				lensEffects = arnold.AiNodeGetPtr( driver, "input" )
				self.assertIsNotNone( lensEffects )
				self.assertEqual(
					arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( lensEffects ) ),
					"imager_lens_effects",
				)
				self.assertEqual( arnold.AiNodeGetInt( lensEffects, "bloom_radius" ), 5 )

				exposure = arnold.AiNodeGetPtr( lensEffects, "input" )
				self.assertIsNotNone( exposure )
				self.assertEqual(
					arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( exposure ) ),
					"imager_exposure",
				)
				self.assertEqual( arnold.AiNodeGetFlt( exposure, "exposure" ), 2.5 )

	def testEditEmptyShaderNetwork( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Arnold",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Interactive,
		)

		# Make a light with a shader that doesn't exist.
		badLightShader = IECoreScene.ShaderNetwork( { "light" : IECoreScene.Shader( "NonexistentShader", "ai:light", {} ), }, output = "light" )
		with IECore.CapturingMessageHandler() as mh :
			light = r.light(
				"test",
				None,
				r.attributes(
					IECore.CompoundObject( {
						"ai:light" : badLightShader
					} )
				)
			)

		self.assertEqual( len( mh.messages ), 1 )
		self.assertIn( """Couldn't load shader "NonexistentShader""", mh.messages[0].message )

		# Try to replace it with a shader that does exist. This
		# should fail, because lights must be updated in place
		# and that's not possible if there was no light node in
		# the first place.
		quadLightShader = IECoreScene.ShaderNetwork( { "light" : IECoreScene.Shader( "quad_light", "ai:light", {} ), }, output = "light" )
		self.assertFalse(
			light.attributes(
				r.attributes(
					IECore.CompoundObject( {
						"ai:light" : quadLightShader
					} )
				)
			)
		)

		# Must delete objects before the renderer.
		del light

	@staticmethod
	def __m44f( m ) :

		return imath.M44f( *[ i for row in m.data for i in row ] )

	def __allNodes( self, universe, type = arnold.AI_NODE_ALL, ignoreBuiltIn = True, nodeEntryName = None ) :

		result = []
		i = arnold.AiUniverseGetNodeIterator( universe, type )
		while not arnold.AiNodeIteratorFinished( i ) :
			node = arnold.AiNodeIteratorGetNext( i )
			if ignoreBuiltIn and arnold.AiNodeGetName( node ) in ( "root", "ai_default_reflection_shader" ) :
				continue
			if nodeEntryName is not None and arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( node ) ) != nodeEntryName :
				continue
			result.append( node )

		return result

	def __assertInstanced( self, universe, *names ) :

		firstInstanceNode = arnold.AiNodeLookUpByName( universe, names[0] )
		for name in names :

			instanceNode = arnold.AiNodeLookUpByName( universe, name )
			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( instanceNode ) ), "ginstance" )

			nodePtr = arnold.AiNodeGetPtr( instanceNode, "node" )
			self.assertReferSameNode( nodePtr, arnold.AiNodeGetPtr( firstInstanceNode, "node" ) )
			self.assertEqual( arnold.AiNodeGetByte( nodePtr, "visibility" ), 0 )

	def __assertNotInstanced( self, universe, *names ) :

		for name in names :
			node = arnold.AiNodeLookUpByName( universe, name )
			self.assertNotEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( node ) ), "ginstance" )

if __name__ == "__main__":
	unittest.main()
