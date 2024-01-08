##########################################################################
#
#  Copyright (c) 2017, John Haddon. All rights reserved.
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

import re
import time
import unittest
from collections import deque
import shlex
import pathlib
import os
import subprocess

import imath

import IECore
import IECoreScene
import IECoreDelight
import IECoreVDB

import GafferTest
import GafferScene

class RendererTest( GafferTest.TestCase ) :

	def testFactory( self ) :

		self.assertTrue( "3Delight" in GafferScene.Private.IECoreScenePreview.Renderer.types() )

		r = GafferScene.Private.IECoreScenePreview.Renderer.create( "3Delight" )
		self.assertTrue( isinstance( r, GafferScene.Private.IECoreScenePreview.Renderer ) )
		self.assertEqual( r.name(), "3Delight" )

	def testSceneDescription( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"3Delight",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			str( self.temporaryDirectory() / "test.nsia" )
		)

		r.render()

		self.assertTrue( ( self.temporaryDirectory() / "test.nsia" ).exists() )

	def testOutput( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"3Delight",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch
		)

		r.output(
			"test",
			IECoreScene.Output(
				str( self.temporaryDirectory() / "beauty.exr" ),
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

		self.assertTrue( ( self.temporaryDirectory() / "beauty.exr" ).exists() )

	def testAOVs( self ) :

		for data, expected in {
			"rgba" : {
				"variablename": "Ci",
				"variablesource": "shader",
				"layertype": "color",
				"withalpha": 1
			},
			"z" : {
				"variablename": "z",
				"variablesource": "builtin",
				"layertype": "scalar",
				"withalpha": 0,
			},
			"color diffuse" : {
				"variablename": "diffuse",
				"variablesource": "shader",
				"layertype": "color",
				"withalpha": 0,
			},
			"color attribute:test" : {
				"variablename": "test",
				"variablesource": "attribute",
				"layertype": "color",
				"withalpha": 0,
			},
			"point builtin:P" : {
				"variablename": "P",
				"variablesource": "builtin",
				"layertype": "vector",
				"withalpha": 0,
			},
			"float builtin:alpha" : {
				"variablename": "alpha",
				"variablesource": "builtin",
				"layertype": "scalar",
				"withalpha": 0,
			},
		}.items() :

			r = GafferScene.Private.IECoreScenePreview.Renderer.create(
				"3Delight",
				GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
				str( self.temporaryDirectory() / "test.nsia" )
			)

			r.output(
				"test",
				IECoreScene.Output(
					"beauty.exr",
					"exr",
					data,
					{
						"filter" : "gaussian",
						"filterwidth" : imath.V2f( 3.5 ),
					}
				)
			)

			r.render()
			del r

			nsi = self.__parseDict( self.temporaryDirectory() / "test.nsia" )
			self.assertIn( "outputLayer:test", nsi )
			self.assertEqual( nsi["outputLayer:test"]["nodeType"], "outputlayer")
			for k, v in expected.items() :
				self.assertIn( k, nsi["outputLayer:test"] )
				self.assertEqual( nsi["outputLayer:test"][k], v )

	def testMesh( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"3Delight",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			str( self.temporaryDirectory() / "test.nsia" ),
		)

		r.object(
			"testPlane",
			IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ), imath.V2i( 2, 1 ) ),
			r.attributes( IECore.CompoundObject() ),
		)

		r.render()
		del r

		nsi = self.__parseDict( self.temporaryDirectory() / "test.nsia" )

		meshes = { k: v for k, v in nsi.items() if nsi[k]["nodeType"] == "mesh" }
		self.assertEqual( len( meshes ), 1 )

		mesh = meshes[next( iter( meshes ) ) ]

		self.assertEqual( mesh["P.indices"], [ 0, 1, 4, 3, 1, 2, 5, 4 ] )
		self.assertEqual(
			mesh["P"],
			[
				imath.V3f( -1, -1, 0 ),
				imath.V3f( 0, -1, 0 ),
				imath.V3f( 1, -1, 0 ),
				imath.V3f( -1, 1, 0 ),
				imath.V3f( 0, 1, 0 ),
				imath.V3f( 1, 1, 0 ),
			]
		)
		self.assertEqual( mesh["nvertices"], [ 4, 4 ] )
		self.assertEqual(
			mesh["st"],
			[
				imath.V2f( 0, 0 ),
				imath.V2f( 0.5, 0 ),
				imath.V2f( 1, 0 ),
				imath.V2f( 0, 1 ),
				imath.V2f( 0.5, 1 ),
				imath.V2f( 1, 1 )
			]
		)
		self.assertEqual( mesh["st.indices"], [ 0, 1, 4, 3, 1, 2, 5, 4 ] )

		self.assertNotIn( "uv.indices", mesh )
		self.assertNotIn( "uv", mesh )

	def testAnimatedMesh( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"3Delight",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			str( self.temporaryDirectory() / "test.nsia" ),
		)

		r.object(
			"testPlane",
			[
				IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) ),
				IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -2 ), imath.V2f( 2 ) ) ),
			],
			[ 0, 1 ],
			r.attributes( IECore.CompoundObject() ),
		)

		r.render()
		del r

		nsi = self.__parseDict( self.temporaryDirectory() / "test.nsia" )

		meshes = { k: v for k, v in nsi.items() if nsi[k]["nodeType"] == "mesh" }
		self.assertEqual( len( meshes ), 1 )

		mesh = meshes[next( iter( meshes ) ) ]
		self.assertEqual( mesh["P.indices"], [ 0, 1, 3, 2 ] )
		self.assertEqual(
			mesh["P"],
			{
				0 : [ imath.V3f( -1, -1, 0 ), imath.V3f( 1, -1, 0 ), imath.V3f( -1, 1, 0 ), imath.V3f( 1, 1, 0 ) ],
				1 : [ imath.V3f( -2, -2, 0 ), imath.V3f( 2, -2, 0 ), imath.V3f( -2, 2, 0 ), imath.V3f( 2, 2, 0 ) ],
			}
		)
		self.assertEqual( mesh["nvertices"], 4 )

	def testPoints( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"3Delight",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			str( self.temporaryDirectory() / "test.nsia" ),
		)

		points = IECoreScene.PointsPrimitive( IECore.V3fVectorData( [ imath.V3f( x ) for x in range( 0, 4 ) ] ) )
		points["width"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.FloatVectorData( [ x + 1 for x in range( 0, 4 ) ] )
		)

		r.object(
			"testPoints",
			points,
			r.attributes( IECore.CompoundObject() ),
		)

		r.render()
		del r

		nsi = self.__parse( self.temporaryDirectory() / "test.nsia" )
		self.__assertInNSI( '"P" "v point" 4 [ 0 0 0 1 1 1 2 2 2 3 3 3 ]', nsi )
		self.__assertInNSI( '"width" "v float" 4 [ 1 2 3 4 ]', nsi )

	def testPointsWithoutWidth( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"3Delight",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			str( self.temporaryDirectory() / "test.nsia" ),
		)

		points = IECoreScene.PointsPrimitive( IECore.V3fVectorData( [ imath.V3f( x ) for x in range( 0, 4 ) ] ) )

		r.object(
			"testPoints",
			points,
			r.attributes( IECore.CompoundObject() ),
		)

		r.render()
		del r

		nsi = self.__parse( self.temporaryDirectory() / "test.nsia" )
		self.__assertInNSI( '"width" "float" 1 1', nsi )

	def testCurves( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"3Delight",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			str( self.temporaryDirectory() / "test.nsia" ),
		)

		curves = IECoreScene.CurvesPrimitive(
			IECore.IntVectorData( [ 4, 4 ] ),
			IECore.CubicBasisf.bSpline(),
			False,
			IECore.V3fVectorData(
				[ imath.V3f( x ) for x in range( 0, 4 ) ] +
				[ imath.V3f( -x ) for x in range( 0, 4 ) ]
			)
		)

		r.object(
			"testCurves",
			curves,
			r.attributes( IECore.CompoundObject() ),
		)

		r.render()
		del r

		nsi = self.__parse( self.temporaryDirectory() / "test.nsia" )
		self.__assertInNSI( '"nvertices" "int" 2 [ 4 4 ]', nsi )
		self.__assertInNSI( '"basis" "string" 1 "b-spline"', nsi )
		self.__assertInNSI( '"P" "v point" 8 [ 0 0 0 1 1 1 2 2 2 3 3 3 0 0 0 -1 -1 -1 -2 -2 -2 -3 -3 -3 ]', nsi )

	def testDisk( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"3Delight",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			str( self.temporaryDirectory() / "test.nsia" ),
		)

		r.object(
			"testDisk",
			IECoreScene.DiskPrimitive( 2, 1 ),
			r.attributes( IECore.CompoundObject() ),
		)

		r.render()
		del r

		nsi = self.__parse( self.temporaryDirectory() / "test.nsia" )

		# 3Delight doesn't have a disk, so we must convert to particles
		self.__assertInNSI( '"particles"', nsi )
		self.__assertInNSI( '"P" "v point" 1 [ 0 0 1 ]', nsi )
		self.__assertInNSI( '"width" "v float" 1 4', nsi )
		self.__assertInNSI( '"N" "v normal" 1 [ 0 0 -1 ]', nsi )

	def testSphere( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"3Delight",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			str( self.temporaryDirectory() / "test.nsia" ),
		)

		r.object(
			"testSphere",
			IECoreScene.SpherePrimitive( 2 ),
			r.attributes( IECore.CompoundObject() ),
		)

		r.render()
		del r

		nsi = self.__parse( self.temporaryDirectory() / "test.nsia" )

		# 3Delight doesn't have a sphere, so we must convert to particles
		self.__assertInNSI( '"particles"', nsi )
		self.__assertInNSI( '"P" "v point" 1 [ 0 0 0 ]', nsi )
		self.__assertInNSI( '"width" "v float" 1 4', nsi )
		self.__assertNotInNSI( '"N"', nsi )

	def testEnvironment( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"3Delight",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			str( self.temporaryDirectory() / "test.nsia" ),
		)

		r.object(
			"testEnvironment",
			GafferScene.Private.IECoreScenePreview.Geometry(
				"dl:environment",
				parameters = {
					"angle" : 25.0
				}
			),
			r.attributes( IECore.CompoundObject() ),
		)

		r.render()
		del r

		nsi = self.__parse( self.temporaryDirectory() / "test.nsia" )

		self.__assertInNSI( '"environment"', nsi )
		self.__assertInNSI( '"angle" "double" 1 25', nsi )

	def testAttributes( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"3Delight",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			str( self.temporaryDirectory() / "test.nsia" ),
		)

		r.attributes( IECore.CompoundObject( {
			"dl:visibility.diffuse" : IECore.BoolData( True ),
			"dl:visibility.camera" : IECore.BoolData( False ),
			"dl:visibility.specular" : IECore.IntData( 0 ),
			"dl:visibility.reflection" : IECore.IntData( 1 ),
		} ) )

		del r

		nsi = self.__parse( self.temporaryDirectory() / "test.nsia" )

		self.__assertInNSI( '"visibility.diffuse" "int" 1 1', nsi )
		self.__assertInNSI( '"visibility.camera" "int" 1 0', nsi )
		self.__assertInNSI( '"visibility.specular" "int" 1 0', nsi )
		self.__assertInNSI( '"visibility.reflection" "int" 1 1', nsi )

	def testCamera( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"3Delight",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			str( self.temporaryDirectory() / "test.nsia" ),
		)

		r.camera(
			"testCamera",
			IECoreScene.Camera(
				parameters = {
					"resolution" : imath.V2i( 2000, 1000 ),
					"projection" : "perspective",
					"aperture" : imath.V2f( 6, 6 ),
					"focalLength" : 2.0,
					"clippingPlanes" : imath.V2f( 0.25, 10 ),
					"shutter" : imath.V2f( 0, 1 ),
					"overscan" : True,
					"overscanTop" : 0.1,
					"overscanBottom" : 0.2,
					"overscanLeft" : 0.1,
					"overscanRight" : 0.2,
				}
			),
			r.attributes( IECore.CompoundObject() )
		)

		r.option( "camera", IECore.StringData( "testCamera" ) )

		r.render()
		del r

		nsi = self.__parse( self.temporaryDirectory() / "test.nsia" )

		self.__assertInNSI( '"fov" "float" 1 90', nsi )
		self.__assertInNSI( '"resolution" "int[2]" 1 [ 2000 1000 ]', nsi )
		self.__assertInNSI( '"screenwindow" "double[2]" 2 [ -1.5 -0.75 1.5 0.75 ]', nsi )
		self.__assertInNSI( '"pixelaspectratio" "float" 1 1', nsi )
		self.__assertInNSI( '"clippingrange" "double" 2 [ 0.25 10 ]', nsi )
		self.__assertInNSI( '"shutterrange" "double" 2 [ 0 1 ]', nsi )
		self.__assertInNSI( '"overscan" "int[2]" 2 [ 200 100 400 200 ]', nsi )

	def testObjectInstancing( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"3Delight",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			str( self.temporaryDirectory() / "test.nsia" ),
		)

		m = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) )
		a = r.attributes( IECore.CompoundObject() )

		r.object( "testPlane1", m, a )
		r.object( "testPlane2", m, a )

		r.render()
		del r

		nsi = self.__parse( self.temporaryDirectory() / "test.nsia" )

		self.assertEqual( nsi.count( '"transform"' ), 2 )
		self.assertEqual( nsi.count( '"mesh"' ), 1 )

	def testTransform( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"3Delight",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			str( self.temporaryDirectory() / "test.nsia" ),
		)

		m = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) )
		a = r.attributes( IECore.CompoundObject() )

		r.object( "untransformed", m, a )
		r.object( "identity", m, a ).transform( imath.M44f() )
		r.object( "transformed", m, a ).transform( imath.M44f().translate( imath.V3f( 1, 0, 0 ) ) )
		r.object( "animated", m, a ).transform(
			[ imath.M44f().translate( imath.V3f( x, 0, 0 ) ) for x in range( 0, 2 ) ],
			[ 0, 1 ]
		)

		r.render()
		del r

		nsi = self.__parse( self.temporaryDirectory() / "test.nsia" )

		self.__assertNotInNSI( 'DeleteAttribute', nsi )
		self.__assertNotInNSI( 'SetAttribute "untransformed" "transformationmatrix"', nsi )
		self.__assertNotInNSI( 'SetAttribute "identity" "transformationmatrix"', nsi )
		self.__assertInNSI( 'SetAttribute "transformed" "transformationmatrix" "doublematrix" 1 [ 1 0 0 0 0 1 0 0 0 0 1 0 1 0 0 1 ]', nsi )
		self.__assertInNSI( 'SetAttributeAtTime "animated" 0 "transformationmatrix" "doublematrix" 1 [ 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1 ]', nsi )
		self.__assertInNSI( 'SetAttributeAtTime "animated" 1 "transformationmatrix" "doublematrix" 1 [ 1 0 0 0 0 1 0 0 0 0 1 0 1 0 0 1 ]', nsi )

	def testShaderSubstitutions( self ) :

		def runSubstitutions( text, attributes ):
			r = GafferScene.Private.IECoreScenePreview.Renderer.create(
				"3Delight",
				GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
				str( self.temporaryDirectory() / "test.nsia" ),
			)

			s = IECoreScene.ShaderNetwork( { "output" : IECoreScene.Shader( "testShader", "surface", { "testStringSubstituted" : text } ) }, output = "output" )

			m = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) )
			attrs = attributes.copy()
			attrs["osl:surface"] = s
			a = r.attributes( IECore.CompoundObject( attrs ) )

			r.object( "object", m, a )

			r.render()
			del r

			nsi = open( self.temporaryDirectory() / "test.nsia", encoding = "utf-8" ).read()
			return re.findall( '\n *"testStringSubstituted" "string" 1 "(.*)" \n', nsi )[0]

		self.assertEqual( runSubstitutions( "<attr:test:foo> TEST <attr:test:bar>", {} ), " TEST " )
		self.assertEqual( runSubstitutions( "<attr:test:foo> TEST <attr:test:bar>", { "test:bar" : IECore.StringData( "AAA" ) } ), " TEST AAA" )
		self.assertEqual( runSubstitutions( "<attr:test:foo> TEST <attr:test:bar>", { "test:foo" : IECore.StringData( "AAA" ), "test:bar" : IECore.StringData( "BBB" ) } ), "AAA TEST BBB" )

	def testMessageHandler( self ) :

		RenderType = GafferScene.Private.IECoreScenePreview.Renderer.RenderType

		for renderType, fileName, expected in (
			( RenderType.Batch, "", 2 ),
			( RenderType.Interactive, "", 2 ),
			( RenderType.SceneDescription, str( self.temporaryDirectory() / "test.nsia" ), 1 )
		) :

			with IECore.CapturingMessageHandler() as fallbackHandler :

				handler = IECore.CapturingMessageHandler()

				r = GafferScene.Private.IECoreScenePreview.Renderer.create(
					"3Delight",
					renderType,
					fileName = fileName,
					messageHandler = handler
				)

				r.option( "invalid", IECore.BoolData( True ) )

				r.render()

				if renderType == RenderType.Interactive :
					time.sleep( 1 )

				# We should have at least 1 message from our invalid option,
				# and additional output from actual renders.
				# Stats/progress seem hard coded to stdout.
				self.assertGreaterEqual( len(handler.messages), expected, msg=str(renderType) )

				self.assertEqual( [ m.message for m in fallbackHandler.messages ], [], msg=str(renderType) )

	def testOptions( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"3Delight",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			str( self.temporaryDirectory() / "test.nsia" )
		)

		options = [
			( "dl:bucketorder", IECore.StringData( "spiral" ), "string" ),
			( "dl:numberofthreads", IECore.IntData( 16 ), "int" ),
			( "dl:renderatlowpriority", IECore.BoolData( True ), "int" ),
			( "dl:quality.shadingsamples", IECore.IntData( 32 ), "int" ),
			( "dl:quality.volumesamples", IECore.IntData( 99 ), "int" ),
			( "dl:clampindirect", IECore.FloatData( 10.5 ), "double" ),
			( "dl:show.displacement", IECore.BoolData( False ), "int" ),
			( "dl:show.osl.subsurface", IECore.BoolData( False ), "int" ),
			( "dl:show.atmosphere", IECore.BoolData( False ), "int" ),
			( "dl:show.multiplescattering", IECore.BoolData( False ), "double" ),
			( "dl:statistics.progress", IECore.BoolData( True ), "int" ),
			( "dl:statistics.filename", IECore.StringData( "/stats" ), "string" ),
			( "dl:maximumraydepth.diffuse", IECore.IntData( 10 ), "int" ),
			( "dl:maximumraydepth.hair", IECore.IntData( 10 ), "int" ),
			( "dl:maximumraydepth.reflection", IECore.IntData( 10 ), "int" ),
			( "dl:maximumraydepth.refraction", IECore.IntData( 10 ), "int" ),
			( "dl:maximumraydepth.volume", IECore.IntData( 10 ), "int" ),
			( "dl:maximumraylength.diffuse", IECore.FloatData( 99.5 ), "double" ),
			( "dl:maximumraylength.hair", IECore.FloatData( 99.5 ), "double" ),
			( "dl:maximumraylength.reflection", IECore.FloatData( 99.5 ), "double" ),
			( "dl:maximumraylength.specular", IECore.FloatData( 99.5 ), "double" ),
			( "dl:maximumraylength.volume", IECore.FloatData( 99.5), "double" ),
			( "dl:texturememory", IECore.IntData( 100 ), "int" ),
			( "dl:networkcache.size", IECore.IntData( 5 ), "int" ),
			( "dl:networkcache.directory", IECore.StringData( "/network" ), "string" ),
			( "dl:license.server", IECore.StringData( "server" ), "string" ),
			( "dl:license.wait", IECore.BoolData( False ), "int" ),
		]

		for name, value, type in options :
			r.option( name, value )

		r.render()
		del r

		nsi = self.__parse( self.temporaryDirectory() / "test.nsia" )

		for name, value, type in options :
			self.__assertInNSI(
				'SetAttribute ".global" "{}" "{}" 1 {}{}{}'.format(
				name[3:],
				type,
				"\"" if type == "string" else "",
				value.value if not isinstance( value, IECore.BoolData ) else int( value.value ),
				"\"" if type == "string" else ""
			),
			nsi
		)

	def testVDB( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"3Delight",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			str( self.temporaryDirectory() / "test.nsia" ),
		)

		vdb = IECoreVDB.VDBObject( ( pathlib.Path( __file__ ).parent / "volumes" / "sphere.vdb" ).as_posix() )
		r.object( "test_vdb", vdb, r.attributes( IECore.CompoundObject() ) )

		r.render()
		del r

		nsi = self.__parseDict( self.temporaryDirectory() / "test.nsia" )

		self.assertIn( "test_vdb", nsi )
		self.assertEqual( nsi["test_vdb"]["nodeType"], "transform" )

		volumes = { k: v for k, v in nsi.items() if nsi[k]["nodeType"] == "volume" }
		self.assertEqual( len( volumes ), 1 )

		volume = volumes[next( iter( volumes ) )]

		self.assertEqual( volume["vdbfilename"], vdb.fileName() )
		self.assertEqual( volume["densitygrid"], "density" )

	def testShaderAttributes( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"3Delight",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			str( self.temporaryDirectory() / "test.nsia" ),
		)

		surfaceNetwork = IECoreScene.ShaderNetwork(
			shaders = { "constHandle" : IECoreScene.Shader( "Surface/Constant", "osl:surface", { "Cs": imath.Color3f( 0, 0, 0 ) } ) },
			output = "constHandle"
		)
		volumeNetwork = IECoreScene.ShaderNetwork(
			shaders = { "constHandle" : IECoreScene.Shader( "Surface/Constant", "osl:volume", { "Cs": imath.Color3f( 0.5, 0.5, 0.5 ) } ) },
			output = "constHandle"
		)
		displacementNetwork = IECoreScene.ShaderNetwork(
			shaders = { "constHandle" : IECoreScene.Shader( "Surface/Constant", "osl:displacement", { "Cs": imath.Color3f( 1.0, 1.0, 1.0 ) } ) },
			output = "constHandle"
		)

		o = r.object(
			"testPlane",
			IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) ),
			r.attributes(
				IECore.CompoundObject(
					{
						"osl:surface" : surfaceNetwork,
						"osl:volume" : volumeNetwork,
						"osl:displacement" : displacementNetwork,
					}
				)
			)
		)
		del o

		r.render()
		del r

		nsi = self.__parseDict( self.temporaryDirectory() / "test.nsia" )

		allAttributes = { k: v for k, v in nsi.items() if nsi[k]["nodeType"] == "attributes" }
		self.assertEqual( len( allAttributes ), 1 )
		attributes = allAttributes[next( iter( allAttributes ) )]

		self.assertIn( "surfaceshader", attributes )
		self.assertIn( "volumeshader", attributes )
		self.assertIn( "displacementshader", attributes )

		self.assertGreater( len( attributes["surfaceshader"] ), 0 )
		self.assertGreater( len( attributes["volumeshader"] ), 0 )
		self.assertGreater( len( attributes["displacementshader"] ), 0 )

		surfaceShader = self.__connectionSource( attributes["surfaceshader"][0], nsi )
		volumeShader = self.__connectionSource( attributes["volumeshader"][0], nsi )
		displacementShader = self.__connectionSource( attributes["displacementshader"][0], nsi )

		self.assertEqual( surfaceShader["nodeType"], "shader" )
		self.assertEqual( volumeShader["nodeType"], "shader" )
		self.assertEqual( displacementShader["nodeType"], "shader" )

		self.assertEqual( surfaceShader["Cs"], imath.Color3f( 0, 0, 0 ) )
		self.assertEqual( volumeShader["Cs"], imath.Color3f( 0.5, 0.5, 0.5 ) )
		self.assertEqual( displacementShader["Cs"], imath.Color3f( 1.0, 1.0, 1.0 ) )

	def test3DelightSplineParameters( self ) :

		# Converting from OSL parameters to Gaffer spline parameters is
		# tested in GafferOSLTest.OSLShaderTest

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"3Delight",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			str( self.temporaryDirectory() / "test.nsia" ),
		)

		os.environ["OSL_SHADER_PATHS"] += os.pathsep + ( pathlib.Path( __file__ ).parent / "shaders" ).as_posix()

		s = self.__compileShader( pathlib.Path( __file__ ).parent / "shaders" / "delightSplineParameters.osl" )

		network = IECoreScene.ShaderNetwork(
			shaders = {
				"splineHandle" : IECoreScene.Shader(
					s,
					"osl:shader",
					{
						"floatSpline" : IECore.Splineff(
							IECore.CubicBasisf.linear(),
							[
								( 0, 0.25 ),
								( 0, 0.25 ),
								( 1, 0.75 ),
								( 1, 0.75 ),
							]
						),
						"colorSpline" : IECore.SplinefColor3f(
							IECore.CubicBasisf.bSpline(),
							[
								( 0, imath.Color3f( 0.25 ) ),
								( 0, imath.Color3f( 0.25 ) ),
								( 0, imath.Color3f( 0.25 ) ),
								( 1, imath.Color3f( 0.75 ) ),
								( 1, imath.Color3f( 0.75 ) ),
								( 1, imath.Color3f( 0.75 ) ),
							]
						),
						"dualInterpolationSpline" : IECore.Splineff(
							IECore.CubicBasisf.linear(),
							[
								( 0, 0.25 ),
								( 0, 0.25 ),
								( 1, 0.75 ),
								( 1, 0.75 ),
							]
						),
						"trimmedFloatSpline" : IECore.Splineff(
							IECore.CubicBasisf.catmullRom(),
							[
								( 0, 0.25 ),
								( 0, 0.25 ),
								( 1, 0.75 ),
								( 1, 0.75 ),
							]
						),
						"mayaSpline" : IECore.Splineff(
							IECore.CubicBasisf.linear(),
							[
								( 0, 0.25 ),
								( 0, 0.25 ),
								( 1, 0.75 ),
								( 1, 0.75 ),
							]
						),
						"inconsistentNameSpline": IECore.Splineff(
							IECore.CubicBasisf.bSpline(),
							[
								( 0, 0.25 ),
								( 0, 0.25 ),
								( 0, 0.25 ),
								( 1, 0.75 ),
								( 1, 0.75 ),
								( 1, 0.75 ),
							]
						),
					}
				),
			},
			output = "splineHandle"
		)

		o = r.object(
			"testPlane",
			IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) ),
			r.attributes( IECore.CompoundObject( { "osl:surface" : network } ) )
		)
		del o

		r.render()
		del r

		nsi = self.__parseDict( self.temporaryDirectory() / "test.nsia" )

		shaders = { k: v for k, v in nsi.items() if nsi[k]["nodeType"] == "shader" }
		self.assertEqual( len( shaders ), 1 )
		shader = shaders[next( iter( shaders ) )]

		# 3Delight gives defaults for linear splines as though they have a multiplicity of 2,
		# whereas we expect a multiplicity of 1. These tests mirror 3Delight's convention.
		# This results in two extra segments, with the first and last of zero length.
		# In practice this seems to give correct results, so we leave it as-is rather than
		# adding more edge-case handling.
		self.assertEqual( shader["floatSpline_Knots"], [ 0, 0, 0, 1, 1, 1 ] )
		self.assertEqual( shader["floatSpline_Floats"], [ 0.25, 0.25, 0.25, 0.75, 0.75, 0.75 ] )
		self.assertEqual( shader["floatSpline_Interp"], [ 1, 1, 1, 1, 1, 1 ] )

		self.assertNotIn( "floatSplinePositions", shader )
		self.assertNotIn( "floatSplineValues", shader )
		self.assertNotIn( "floatSplineBasis", shader )

		self.assertEqual( shader["colorSpline_Knots"], [ 0, 0, 0, 1, 1, 1 ] )
		self.assertEqual(
			shader["colorSpline_Colors"],
			[
				imath.Color3f( 0.25, 0.25, 0.25 ),
				imath.Color3f( 0.25, 0.25, 0.25 ),
				imath.Color3f( 0.25, 0.25, 0.25 ),
				imath.Color3f( 0.75, 0.75, 0.75 ),
				imath.Color3f( 0.75, 0.75, 0.75 ),
				imath.Color3f( 0.75, 0.75, 0.75 )
			]
		)
		self.assertEqual( shader["colorSpline_Interp"], [ 3, 3, 3, 3, 3, 3 ] )

		self.assertNotIn( "colorSplinePositions", shader )
		self.assertNotIn( "colorSplineValues", shader )
		self.assertNotIn( "colorSplineBasis", shader )

		self.assertEqual( shader["dualInterpolationSpline_Knots"], [ 0, 0, 0, 1, 1, 1 ] )
		self.assertEqual( shader["dualInterpolationSpline_Floats"], [ 0.25, 0.25, 0.25, 0.75, 0.75, 0.75 ] )
		self.assertEqual( shader["dualInterpolationSpline_Interp"], [ 1, 1, 1, 1, 1, 1 ] )

		self.assertNotIn( "dualInterpolationSplinePositions", shader )
		self.assertNotIn( "dualInterpolationSplineValues", shader )
		self.assertNotIn( "dualInterpolationSplineBasis", shader )

		# Monotone cubic splines - tested here consistently with how 3Delight presents defaults -
		# have a multiplicity of 1, resulting in a single segment.
		self.assertEqual( shader["trimmedFloatSpline_Knots"], [ 0, 0, 1, 1 ] )
		self.assertEqual( shader["trimmedFloatSpline_Floats"], [ 0.25, 0.25, 0.75, 0.75 ] )
		self.assertEqual( shader["trimmedFloatSpline_Interp"], [ 3, 3, 3, 3 ] )

		self.assertNotIn( "trimmedFloatSplinePositions", shader )
		self.assertNotIn( "trimmedFloatSplineValues", shader )
		self.assertNotIn( "trimmedFloatSplineBasis", shader )

		self.assertEqual( shader["mayaSpline_Knots"], [ 0, 0, 0, 1, 1, 1 ] )
		self.assertEqual( shader["mayaSpline_Floats"], [ 0.25, 0.25, 0.25, 0.75, 0.75, 0.75 ] )
		self.assertEqual( shader["mayaSpline_Interp"], [ 1, 1, 1, 1, 1, 1 ] )

		self.assertNotIn( "mayaSplinePositions", shader )
		self.assertNotIn( "maysSplineValues", shader )
		self.assertNotIn( "mayaSplineBasis", shader )

		self.assertEqual( shader["inconsistentNameSpline_chaos"], [ 0, 0, 0, 1, 1, 1 ] )
		self.assertEqual( shader["inconsistentNameSpline_moreChaos"], [ 0.25, 0.25, 0.25, 0.75, 0.75, 0.75 ] )
		self.assertEqual( shader["inconsistentNameSpline_ahhh"], [ 3, 3, 3, 3, 3, 3 ] )

		self.assertNotIn( "inconsistentNameSplinePositions", shader )
		self.assertNotIn( "inconsistentNameSplineValues", shader )
		self.assertNotIn( "inconsistentNameSplineBasis", shader )

	def testGafferSplineParameters( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"3Delight",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			str( self.temporaryDirectory() / "test.nsia" ),
		)

		network = IECoreScene.ShaderNetwork(
			shaders = {
				"splineHandle" : IECoreScene.Shader(
					"Pattern/ColorSpline",
					"osl:shader",
					{
						"spline" : IECore.SplinefColor3f(
							IECore.CubicBasisf.linear(),
							[
								( 0, imath.Color3f( 1, 0, 0 ) ),
								( 0, imath.Color3f( 1, 0, 0 ) ),
								( 1, imath.Color3f( 0, 0, 1 ) ),
								( 1, imath.Color3f( 0, 0, 1 ) ),
							]
						),
					}
				),
				"constHandle" : IECoreScene.Shader( "Surface/Constant", "osl:surface", {} )
			},
			connections = [
				( ( "splineHandle", "" ), ( "constHandle", "Cs" ) ),
			],
			output = "splineHandle"
		)

		o = r.object(
			"testPlane",
			IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) ),
			r.attributes( IECore.CompoundObject( { "osl:surface" : network } ) )
		)
		del o

		r.render()
		del r

		nsi = self.__parseDict( self.temporaryDirectory() / "test.nsia" )

		shaders = { k: v for k, v in nsi.items() if nsi[k]["nodeType"] == "shader" }
		self.assertEqual( len( shaders ), 1 )
		shader = shaders[next( iter( shaders ) )]

		self.assertEqual( shader["splinePositions"], [ 0, 0, 0, 1, 1, 1 ] )
		self.assertEqual(
			shader["splineValues"],
			[
				imath.Color3f( 1, 0, 0 ),
				imath.Color3f( 1, 0, 0 ),
				imath.Color3f( 1, 0, 0 ),
				imath.Color3f( 0, 0, 1 ),
				imath.Color3f( 0, 0, 1 ),
				imath.Color3f( 0, 0, 1 )
			]
		)
		self.assertEqual( shader["splineBasis"], "linear" )

	def testUVCoordShaderInserted( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"3Delight",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			str( self.temporaryDirectory() / "test.nsia" ),
		)

		s = IECoreScene.ShaderNetwork(
			{
				"output" : IECoreScene.Shader( "testShader", "surface", { "uvCoord" : IECore.FloatVectorData() } )
			},
			output = "output"
		)

		m = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) )
		a = r.attributes( IECore.CompoundObject( { "osl:surface": s } ) )

		r.object( "object", m, a )

		r.render()
		del r

		nsi = self.__parseDict( self.temporaryDirectory() / "test.nsia" )

		shaders = { k: v for k, v in nsi.items() if nsi[k]["nodeType"] == "shader" }

		self.assertEqual( len( shaders ), 2 )

		testShader = next( k for k, v in shaders.items() if v["shaderfilename"] == "testShader" )
		uvShader = next( k for k, v in shaders.items() if pathlib.Path( v["shaderfilename"] ).name == "uvCoord.oso" )

		self.assertEqual( len( nsi[testShader]["uvCoord"] ), 1 )
		self.assertEqual( self.__connectionSource( nsi[testShader]["uvCoord"][0], nsi ), nsi[uvShader] )

	def testUVCoordShaderNotInserted( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"3Delight",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			str( self.temporaryDirectory() / "test.nsia" ),
		)

		s = IECoreScene.ShaderNetwork(
			shaders = {
				"output" : IECoreScene.Shader( "testShader", "surface", { "uvCoord" : IECore.FloatVectorData() } ),
				"input" : IECoreScene.Shader( "testUVShader" )
			},
			connections = [
				( ( "input", "" ), ( "output", "uvCoord" ) )
			],
			output = "output"
		)

		m = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) )
		a = r.attributes( IECore.CompoundObject( { "osl:surface": s } ) )

		r.object( "object", m, a )

		r.render()
		del r

		nsi = self.__parseDict( self.temporaryDirectory() / "test.nsia" )

		shaders = { k: v for k, v in nsi.items() if nsi[k]["nodeType"] == "shader" }

		self.assertEqual( len( shaders ), 2 )

		testShader = next( k for k, v in shaders.items() if v["shaderfilename"] == "testShader" )
		uvShader = next( k for k, v in shaders.items() if v["shaderfilename"] == "testUVShader" )

		self.assertEqual( len( nsi[testShader]["uvCoord"] ), 1 )
		self.assertEqual( self.__connectionSource( nsi[testShader]["uvCoord"][0], nsi ), nsi[uvShader] )

	def testCornersAndCreases( self ) :

		mesh = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) )
		mesh.setInterpolation( "catmullClark" )
		mesh.setCorners( IECore.IntVectorData( [ 3 ] ), IECore.FloatVectorData( [ 5 ] ) )
		mesh.setCreases( IECore.IntVectorData( [ 3 ] ), IECore.IntVectorData( [ 0, 1, 2 ] ), IECore.FloatVectorData( [ 6 ] ) )

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"3Delight",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			str( self.temporaryDirectory() / "test.nsia" ),
		)

		renderer.object( "testPlane", mesh, renderer.attributes( IECore.CompoundObject() ) )

		renderer.render()
		del renderer

		nsi = self.__parseDict( self.temporaryDirectory() / "test.nsia" )

		mesh = next( node for node in nsi.values() if node["nodeType"] == "mesh" )
		self.assertEqual( mesh["subdivision.creasevertices"], [ 0, 1, 1, 2 ] )
		self.assertEqual( mesh["subdivision.creasesharpness"], [ 6, 6 ] )
		self.assertEqual( mesh["subdivision.cornervertices"], 3 )
		self.assertEqual( mesh["subdivision.cornersharpness"], 5 )

	# Helper methods used to check that NSI files we write contain what we
	# expect. The 3delight API only allows values to be set, not queried,
	# so we build a simple dictionary-based node graph for now.

	def __connectionSource( self, connection, nsi ) :

		cSplit = connection.split( '.' )
		if len( cSplit ) == 0 :
			return None

		if len( cSplit ) == 1 :
			return nsi[cSplit[0][1:-1]]  # remove <>

		nodeName = cSplit[0][1:-1]
		parameterName = cSplit[1]

		if parameterName not in nsi[nodeName] :
			# Shaders don't list their outputs as parameters, just return the node
			return nsi[nodeName]

		return nsi[nodeName][parameterName]

	def __parseDict( self, nsiFile ) :

		reArraySplit = re.compile( r'(?P<varType>.*)\[(?P<arrayLength>[0-9]+)\]' )

		root = {
			".root": { "nodeType": "root", "objects": [], "geometryattributes": [], },
			".global": { "nodeType": "global", },
		}
		tokens = deque()
		with open( nsiFile, encoding = "utf-8" ) as f :
			for i in f.readlines() :
				if not i.startswith( '#' ) :
					tokens += shlex.split( i )

		currentNode = None  # The node to add attributes to
		currentTime = None # The time to add attributes to

		while len( tokens ) :
			token = tokens.popleft()
			if token == "Create" :
				node = tokens.popleft()
				root.setdefault( node, {} )["nodeType"] = tokens.popleft()
			elif token == "SetAttribute" :
				currentNode = tokens.popleft()
				currentTime = None
			elif token == "SetAttributeAtTime" :
				currentNode = tokens.popleft()
				currentTime = float( tokens.popleft() )
			elif token == "Connect" :
				sourceNode = tokens.popleft()
				sourceAttr = tokens.popleft()
				destNode = tokens.popleft()
				destAttr = tokens.popleft()

				source = "<{}>".format( sourceNode ) + ( ( "." + sourceAttr ) if sourceAttr != "" else "" )

				root[destNode].setdefault( destAttr, [] ).append( source )
			elif token == "Delete" :
				pass
			elif token == "DeleteAttribute" :
				pass
			elif token == "Disconnect" :
				pass
			elif token == "Evaluate" :
				pass
			elif token == "RenderControl" :
				# Pop attributes but don't bother assigning them for now
				currentNode = None
			else :
				# List of attributes
				pType = tokens.popleft()
				if pType == "v normal" or pType == "v point" :
					pType = "v"
				pSize = int( tokens.popleft() )
				pLength = 1

				arraySplit = reArraySplit.match( pType )
				# Currently it seems impossible to reprsent an array of arrays, i.e. an array
				# of float[2] arrays. We treat `float[2]` as it's own unique type.
				if arraySplit is not None and pType != "float[2]" :
					pLength = int( arraySplit.groupdict()["arrayLength"] )
					pType = arraySplit.groupdict()["varType"]

				if pLength == 0 :
					tokens.popleft()  # Opening `[`
					tokens.popleft()  # Closing	`]`
					continue  # And we're done

				numComponents = { "v": 3, "color": 3, "doublematrix": 16, "float[2]": 2 }.get( pType, 1 )
				numElements = pLength * numComponents * pSize
				if numElements > 1 :
					tokens.popleft()  # First `[` of an array
				value = []
				for i in range( 0, pSize * pLength ) :
					if pType == "int" :
						value.append( int( tokens.popleft() ) )
					elif pType == "float" or pType == "double" :
						value.append( float( tokens.popleft() ) )
					elif pType == "string" :
						value.append( tokens.popleft() )
					elif pType == "color" :
						value.append( imath.Color3f( float( tokens.popleft() ), float( tokens.popleft() ), float( tokens.popleft() ) ) )
					elif pType == "v" :
						value.append( imath.V3f( float( tokens.popleft() ), float( tokens.popleft() ), float( tokens.popleft() ) ) )
					elif pType == "doublematrix" :
						value.append(
							imath.M44f(
								float( tokens.popleft() ), float( tokens.popleft() ), float( tokens.popleft() ), float( tokens.popleft() ),
								float( tokens.popleft() ), float( tokens.popleft() ), float( tokens.popleft() ), float( tokens.popleft() ),
								float( tokens.popleft() ), float( tokens.popleft() ), float( tokens.popleft() ), float( tokens.popleft() ),
								float( tokens.popleft() ), float( tokens.popleft() ), float( tokens.popleft() ), float( tokens.popleft() ),
							)
						)
					elif pType == "float[2]" :
						value.append( imath.V2f( float( tokens.popleft() ), float( tokens.popleft() ) ) )

				if numElements > 1 :
					self.assertEqual( tokens.popleft(), ']' )  # If we don't see the closing bracket, we've done something wrong above

				if currentNode is not None :
					if len( value ) == 1 :
						value = value[0]

					if currentTime is None :
						root[currentNode][token] = value
					else :
						root[currentNode].setdefault( token, {} )[currentTime] = value

		return root


	# Helper methods used to check that NSI files we write contain what we
	# expect. This is a very poor substitute to being able to directly query
	# an NSI scene. We could try to write a proper parser that builds a node
	# structure to be queried, but apparently queries will be added to 3delight
	# soon, so we may as well wait.

	def __parse( self, nsiFile ) :

		result = []
		with open( nsiFile, encoding = "utf-8" ) as f :
			for x in f.readlines() :
				result.extend( x.split() )

		return result

	def __assertInNSI( self, s, nsi ) :

		l = s.split()

		pos = 0
		while True :
			try :
				pos = nsi.index( l[0], pos )
			except ValueError :
				self.fail( "\"{}\" not found".format( s ) )
			if nsi[pos:pos+len(l)] == l :
				return # success!
			else :
				# Continue search at next position
				pos += 1

	def __assertNotInNSI( self, s, nsi ) :

		l = s.split()

		pos = 0
		while True :
			try :
				pos = nsi.index( l[0], pos )
			except ValueError :
				return
			if nsi[pos:pos+len(l)] == l :
				self.fail( "\"{}\" found".format( s ) )
			else :
				# Continue search at next position
				pos += 1

	def __compileShader( self, sourceFileName ) :

		outputFileName = self.temporaryDirectory() / pathlib.Path( sourceFileName ).with_suffix( ".oso" ).name

		subprocess.check_call(
			[ "oslc", "-q" ] +
			[ "-I" + p for p in os.environ.get( "OSL_SHADER_PATHS", "" ).split( os.pathsep ) ] +
			[ "-o", str( outputFileName ), str( sourceFileName ) ]
		)

		return outputFileName.with_suffix("").as_posix()

if __name__ == "__main__":
	unittest.main()
