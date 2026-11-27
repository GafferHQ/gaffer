##########################################################################
#
#  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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
import OpenImageIO

import IECore
import IECoreScene
import IECoreGL

import GafferTest
import GafferScene

@unittest.skipIf( GafferTest.inCI(), "OpenGL not set up" )
class RendererTest( GafferTest.TestCase ) :

	def setUp( self ) :

		GafferTest.TestCase.setUp( self )

	def tearDown( self ) :

		# IECoreGL expects all GL contexts to share resources, so that
		# `CachedConverter::defaultCachedConverter()` can be used everywhere.
		# That idea falls down when using the OpenGL renderer with GafferUI,
		# because the former calls `IECoreGL.init( False )` to create a new
		# context and the latter calls `IECoreGL.init( True )` to share with Qt.
		# That can lead to creating resources in one context and attempting to
		# destroy them in another.
		#
		# For now, we work around this problem by clearing all shared resources
		# created by the renderer here, while we're still in the right context.
		IECoreGL.ShaderLoader.defaultShaderLoader().clear()
		IECoreGL.CachedConverter.defaultCachedConverter().clearUnused()

		GafferTest.TestCase.tearDown( self )

	def testFactory( self ) :

		self.assertTrue( "OpenGL" in GafferScene.Private.IECoreScenePreview.Renderer.types() )

		r = GafferScene.Private.IECoreScenePreview.Renderer.create( "OpenGL" )
		self.assertTrue( isinstance( r, GafferScene.Private.IECoreScenePreview.Renderer ) )
		self.assertEqual( r.name(), "OpenGL" )

	def testOtherRendererAttributes( self ) :

		# Attributes destined for other renderers should be silently ignored

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create( "OpenGL" )

		with IECore.CapturingMessageHandler() as handler :

			renderer.attributes(
				IECore.CompoundObject( {
					"ai:visibility:camera" : IECore.IntData( 0 )
				} )
			)

		self.assertEqual( len( handler.messages ), 0 )

	def testPrimVars( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create( "OpenGL" )
		renderer.output( "test", IECoreScene.Output( str( self.temporaryDirectory() / "testPrimVars.exr" ), "exr", "rgba", {} ) )

		fragmentSource = """
		uniform float red;
		uniform float green;
		uniform float blue;

		void main()
		{
			gl_FragColor = vec4( red, green, blue, 1 );
		}
		"""

		attributes = renderer.attributes(
			IECore.CompoundObject( {
				"gl:surface" : IECoreScene.ShaderNetwork(
					{
						"output" : IECoreScene.Shader( "rgbColor", "surface", { "gl:fragmentSource" : fragmentSource } )
					},
					output = "output"
				)
			} )
		)

		def sphere( red, green, blue ) :

			s = IECoreScene.SpherePrimitive()
			s["red"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Constant, IECore.FloatData( red ) )
			s["green"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Constant, IECore.FloatData( green ) )
			s["blue"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Constant, IECore.FloatData( blue ) )

			return s

		renderer.object(
			"redSphere",
			sphere( 1, 0, 0 ),
			attributes
		).transform(
			imath.M44f().translate( imath.V3f( 0, 0, -5 ) )
		)

		renderer.object(
			"greenSphere",
			sphere( 0, 1, 0 ),
			attributes
		).transform(
			imath.M44f().translate( imath.V3f( -1, 0, -5 ) )
		)

		renderer.object(
			"blueSphere",
			sphere( 0, 0, 1 ),
			attributes
		).transform(
			imath.M44f().translate( imath.V3f( 1, 0, -5 ) )
		)

		renderer.render()

		image = OpenImageIO.ImageBuf( str( self.temporaryDirectory() / "testPrimVars.exr" ) )
		self.assertEqual(
			self.__colorAtUV( image, imath.V2f( 0, 0.5 ) ),
			imath.Color4f( 0, 1, 0, 1 )
		)
		self.assertEqual(
			self.__colorAtUV( image, imath.V2f( 0.5, 0.5 ) ),
			imath.Color4f( 1, 0, 0, 1 )
		)
		self.assertEqual(
			self.__colorAtUV( image, imath.V2f( 1.0, 0.5 ) ),
			imath.Color4f( 0, 0, 1, 1 )
		)

	def testShaderParameters( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create( "OpenGL" )
		renderer.output( "test", IECoreScene.Output( str( self.temporaryDirectory() / "testShaderParameters.exr" ), "exr", "rgba", {} ) )

		fragmentSource = """
		uniform vec3 colorValue;
		void main()
		{
			gl_FragColor = vec4( colorValue, 1 );
		}
		"""

		attributes = renderer.attributes(
			IECore.CompoundObject( {
				"gl:surface" : IECoreScene.ShaderNetwork(
					shaders = {
						"output" : IECoreScene.Shader(
							"color",
							"surface",
							{
								"gl:fragmentSource" : fragmentSource,
								"colorValue" : imath.Color3f( 1, 0, 0 )
							}
						)
					},
					output = "output"
				)
			} )
		)

		renderer.object(
			"sphere",
			IECoreScene.SpherePrimitive(),
			attributes
		).transform(
			imath.M44f().translate( imath.V3f( 0, 0, -5 ) )
		)

		renderer.render()

	def testQueryBound( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"OpenGL",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Interactive
		)

		cube = IECoreScene.MeshPrimitive.createBox( imath.Box3f( imath.V3f( -1 ), imath.V3f( 9 ) ) )

		o = renderer.object(
			"/cube",
			cube,
			renderer.attributes( IECore.CompoundObject() )
		)
		o.transform(
			imath.M44f().translate( imath.V3f( 1 ) )
		)

		self.assertEqual(
			renderer.command( "gl:queryBound", {} ),
			imath.Box3f(
				cube.bound().min() + imath.V3f( 1 ),
				cube.bound().max() + imath.V3f( 1 )
			)
		)

		del o

	def testTransforms( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"OpenGL",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Interactive
		)

		cube = IECoreScene.MeshPrimitive.createBox( imath.Box3f( imath.V3f( -1 ), imath.V3f( 9 ) ) )

		o = renderer.object(
			"/cube",
			cube,
			renderer.attributes( IECore.CompoundObject() )
		)
		o.transform(
			imath.M44f().scale( imath.V3f( 0 ) )
		)

		renderer.render()

	def testPointInstancer( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create( "OpenGL" )
		renderer.output( "test", IECoreScene.Output( str( self.temporaryDirectory() / "testPointInstancer.exr" ), "exr", "rgba", {} ) )

		fragmentSource = """
		uniform vec3 color;

		void main()
		{
			gl_FragColor = vec4( color, 1 );
		}
		"""

		def prototype( primitive, color ) :

			return renderer.Prototype(
				[ primitive ], [],
				renderer.attributes(
					IECore.CompoundObject( {
						"gl:surface" : IECoreScene.ShaderNetwork(
							{
								"output" : IECoreScene.Shader( "color", "surface", { "gl:fragmentSource" : fragmentSource, "color" : color } )
							},
							output = "output"
						)
					} )
				)
			)

		plane = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -0.5 ), imath.V2f( 0.5 ) ) )
		prototypes = [
			prototype( plane, imath.Color3f( 1, 0, 0 ) ),
			prototype( plane, imath.Color3f( 0, 1, 0 ) ),
			# Not a mesh, to check other primitive types can be instanced.
			prototype( IECoreScene.SpherePrimitive( 0.5 ), imath.Color3f( 0, 0, 1 ) ),
		]

		pointInstancer = IECoreScene.PointInstancer( 4 )
		pointInstancer.setPosition(
			IECore.V3fVectorData( [ imath.V3f( -1, 0, 0 ), imath.V3f( 0, 0, 0 ), imath.V3f( 1, 0, 0 ), imath.V3f( 0, 0.5, 0 ) ] )
		)
		pointInstancer.setPrototypeIndex( IECore.IntVectorData( [ 1, 0, 2, 1 ] ) )
		pointInstancer.setID( IECore.Int64VectorData( [ 0, 1, 2, 3 ] ) )
		pointInstancer.setInvisibleIDs( IECore.Int64VectorData( [ 3 ] ) )
		# Scale the central instance down, so we can check transforms are applied.
		pointInstancer["scale"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.V3fVectorData( [ imath.V3f( 1 ), imath.V3f( 0.5 ), imath.V3f( 1 ), imath.V3f( 1 ) ] )
		)

		object = renderer.pointInstancer(
			"/instancer", [ pointInstancer ], [], prototypes,
			renderer.attributes( IECore.CompoundObject() )
		)
		object.transform( imath.M44f().translate( imath.V3f( 0, 0, -5 ) ) )

		renderer.render()

		del object

		image = OpenImageIO.ImageBuf( str( self.temporaryDirectory() / "testPointInstancer.exr" ) )
		self.assertEqual( self.__colorAtUV( image, imath.V2f( 0, 0.5 ) ), imath.Color4f( 0, 1, 0, 1 ) )
		self.assertEqual( self.__colorAtUV( image, imath.V2f( 0.5, 0.5 ) ), imath.Color4f( 1, 0, 0, 1 ) )
		self.assertEqual( self.__colorAtUV( image, imath.V2f( 1, 0.5 ) ), imath.Color4f( 0, 0, 1, 1 ) )
		# Outside the scaled-down central instance.
		self.assertEqual( self.__colorAtUV( image, imath.V2f( 0.5, 0.3 ) ), imath.Color4f( 0 ) )
		self.assertEqual( self.__colorAtUV( image, imath.V2f( 0.5, 0.7 ) ), imath.Color4f( 0 ) )
		# Invisible instance.
		self.assertEqual( self.__colorAtUV( image, imath.V2f( 0.5, 0.25 ) ), imath.Color4f( 0 ) )

	def testPointInstancerBound( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"OpenGL",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Interactive
		)

		cube = IECoreScene.MeshPrimitive.createBox( imath.Box3f( imath.V3f( -1 ), imath.V3f( 1 ) ) )
		pointInstancer = IECoreScene.PointInstancer( 2 )
		pointInstancer.setPosition( IECore.V3fVectorData( [ imath.V3f( -10, 0, 0 ), imath.V3f( 10, 0, 0 ) ] ) )
		pointInstancer.setPrototypeIndex( IECore.IntVectorData( [ 0, 0 ] ) )

		object = renderer.pointInstancer(
			"/instancer", [ pointInstancer ], [],
			[ renderer.Prototype( [ cube ], [], renderer.attributes( IECore.CompoundObject() ) ) ],
			renderer.attributes( IECore.CompoundObject() )
		)
		object.transform( imath.M44f().translate( imath.V3f( 0, 1, 0 ) ) )

		# Bound doesn't currently consider the prototype - it is just the bound
		# of the points.
		self.assertEqual(
			renderer.command( "gl:queryBound", {} ),
			imath.Box3f( imath.V3f( -10, 1, 0 ), imath.V3f( 10, 1, 0 ) )
		)

		del object

	def __colorAtUV( self, image, uv ) :

		pixel = image.getpixel( int( uv.x * (image.spec().width - 1) ), int( uv.y * (image.spec().height - 1) ) )
		return imath.Color4f( *pixel )
