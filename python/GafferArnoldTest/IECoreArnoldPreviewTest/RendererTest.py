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

		o = r.object( "testPlane", IECore.MeshPrimitive.createPlane( IECore.Box2f( IECore.V2f( -1 ), IECore.V2f( 1 ) ) ) )
		o.transform( IECore.M44f().translate( IECore.V3f( 1, 2, 3 ) ) )

		r.render()
		del r

		with IECoreArnold.UniverseBlock() :

			arnold.AiASSLoad( self.temporaryDirectory() + "/test.ass" )

			n = arnold.AiNodeLookUpByName( "testPlane" )
			self.assertTrue( arnold.AiNodeEntryGetType( arnold.AiNodeGetNodeEntry( n ) ), arnold.AI_NODE_SHAPE )

	def testCropWindow( self ) :

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
					"cropWindow" : IECore.Box2f( IECore.V2f( 0 ), IECore.V2f( 1, 0.75 ) ),
				}
			)
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

			o = r.object( "testPlane%d" % i, IECore.MeshPrimitive.createPlane( IECore.Box2f( IECore.V2f( -1 ), IECore.V2f( 1 ) ) ) )
			# We keep specifying the same shader, but we'd like the renderer
			# to be frugal and reuse a single arnold shader on the other side.
			o.attributes( r.attributes( a ) )
			del o

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

		o = r.object( "testPlane", IECore.MeshPrimitive.createPlane( IECore.Box2f( IECore.V2f( -1 ), IECore.V2f( 1 ) ) ) )
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

		o1 = r.object( "testPlane1", IECore.MeshPrimitive.createPlane( IECore.Box2f( IECore.V2f( -1 ), IECore.V2f( 1 ) ) ) )
		o1.attributes(
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

		o2 = r.object( "testPlane2", IECore.MeshPrimitive.createPlane( IECore.Box2f( IECore.V2f( -1 ), IECore.V2f( 1 ) ) ) )
		o2.attributes(
			r.attributes(
				IECore.CompoundObject( {
					"ai:surface" : shader2
				} )
			)
		)

		del o1, o2
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
		o = r.light( "testLight", None )
		o.attributes(
			r.attributes(
				IECore.CompoundObject( {
					"ai:light" : lightShader
				} )
			)
		)

		del o
		r.render()
		del r

		with IECoreArnold.UniverseBlock() :

			arnold.AiASSLoad( self.temporaryDirectory() + "/test.ass" )

			lights = self.__allNodes( type = arnold.AI_NODE_LIGHT )
			self.assertEqual( len( lights ), 1 )
			self.assertEqual( arnold.AiNodeGetName( lights[0] ), "testLight" )

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

		o = r.light( "testLight1", None )
		o.attributes( lightAttributes )

		o = r.light( "testLight2", None )
		o.attributes( lightAttributes )

		del o, lightAttributes
		r.render()
		del r

		with IECoreArnold.UniverseBlock() :

			arnold.AiASSLoad( self.temporaryDirectory() + "/test.ass" )

			lights = self.__allNodes( type = arnold.AI_NODE_LIGHT )
			self.assertEqual( len( lights ), 2 )
			self.assertEqual( set( [ arnold.AiNodeGetName( l ) for l in lights ] ), { "testLight1", "testLight2" } )

	def testAttributes( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"IECoreArnold::Renderer",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			self.temporaryDirectory() + "/test.ass"
		)

		o1 = r.object( "testMesh1", IECore.MeshPrimitive.createPlane( IECore.Box2f( IECore.V2f( -1 ), IECore.V2f( 1 ) ) ) )
		o1.attributes(
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
			} ) )
		)

		o2 = r.object( "testMesh2", IECore.MeshPrimitive.createPlane( IECore.Box2f( IECore.V2f( -1 ), IECore.V2f( 1 ) ) ) )
		o2.attributes(
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
			} ) )
		)

		o3 = r.object( "testMesh3", IECore.MeshPrimitive.createPlane( IECore.Box2f( IECore.V2f( -1 ), IECore.V2f( 1 ) ) ) )

		del o1, o2, o3
		r.render()
		del r

		with IECoreArnold.UniverseBlock() :

			arnold.AiASSLoad( self.temporaryDirectory() + "/test.ass" )
			o1 = self.__allNodes( type = arnold.AI_NODE_SHAPE )[0]
			o2 = self.__allNodes( type = arnold.AI_NODE_SHAPE )[1]
			o3 = self.__allNodes( type = arnold.AI_NODE_SHAPE )[2]

			self.assertEqual( arnold.AiNodeGetStr( o1, "name" ), "testMesh1" )
			self.assertEqual( arnold.AiNodeGetStr( o2, "name" ), "testMesh2" )
			self.assertEqual( arnold.AiNodeGetStr( o3, "name" ), "testMesh3" )

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

	def testMeshLight( self ) :

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

		l = r.light( "myLight", IECore.MeshPrimitive.createPlane( IECore.Box2f( IECore.V2f( -1 ), IECore.V2f( 1 ) ) ) )
		l.attributes(
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

			lights = self.__allNodes( type = arnold.AI_NODE_LIGHT )
			self.assertEqual( len( lights ), 1 )
			light = lights[0]
			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( light ) ), "mesh_light" )

			shapes = self.__allNodes( type = arnold.AI_NODE_SHAPE )
			self.assertEqual( len( shapes ), 1 )
			mesh = shapes[0]
			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( mesh ) ), "polymesh" )
			self.assertEqual( arnold.AiNodeGetName( mesh ), "myLight" )

			self.assertEqual( arnold.AiNodeGetPtr( light, "mesh" ), ctypes.addressof( mesh.contents ) )

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
