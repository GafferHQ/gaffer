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

import os
import unittest
import imath

import IECore
import IECoreScene
import IECoreGL

import GafferTest
import GafferScene

@unittest.skipIf( GafferTest.inCI(), "OpenGL not set up" )
class RendererTest( GafferTest.TestCase ) :

	def setUp( self ) :

		GafferTest.TestCase.setUp( self )

		IECoreGL.init( False )

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
		renderer.output( "test", IECoreScene.Output( self.temporaryDirectory() + "/testPrimVars.exr", "exr", "rgba", {} ) )

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

		image = IECore.Reader.create(  self.temporaryDirectory() + "/testPrimVars.exr" ).read()
		dimensions = image.dataWindow.size() + imath.V2i( 1 )
		index = dimensions.x * int( dimensions.y * 0.5 )
		self.assertEqual( image["R"][index], 0 )
		self.assertEqual( image["G"][index], 1 )
		self.assertEqual( image["B"][index], 0 )

		index = dimensions.x * int(dimensions.y * 0.5) + int( dimensions.x * 0.5 )
		self.assertEqual( image["R"][index], 1 )
		self.assertEqual( image["G"][index], 0 )
		self.assertEqual( image["B"][index], 0 )

		index = dimensions.x * int(dimensions.y * 0.5) + int( dimensions.x * 1 ) - 1
		self.assertEqual( image["R"][index], 0 )
		self.assertEqual( image["G"][index], 0 )
		self.assertEqual( image["B"][index], 1 )

	def testShaderParameters( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create( "OpenGL" )
		renderer.output( "test", IECoreScene.Output( self.temporaryDirectory() + "/testShaderParameters.exr", "exr", "rgba", {} ) )

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

if __name__ == "__main__":
	unittest.main()
