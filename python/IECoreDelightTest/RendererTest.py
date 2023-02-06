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

import imath

import IECore
import IECoreScene
import IECoreDelight

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
			str( self.temporaryDirectory() / "test.nsi" )
		)

		r.render()

		self.assertTrue( ( self.temporaryDirectory() / "test.nsi" ).exists() )

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
			"rgba" : [
				'"variablename" "string" 1 "Ci"',
				'"variablesource" "string" 1 "shader"',
				'"layertype" "string" 1 "color"',
				'"withalpha" "int" 1 1',
			],
			"z" : [
				'"variablename" "string" 1 "z"',
				'"variablesource" "string" 1 "builtin"',
				'"layertype" "string" 1 "scalar"',
				'"withalpha" "int" 1 0',
			],
			"color diffuse" : [
				'"variablename" "string" 1 "diffuse"',
				'"variablesource" "string" 1 "shader"',
				'"layertype" "string" 1 "color"',
				'"withalpha" "int" 1 0',
			],
			"color attribute:test" : [
				'"variablename" "string" 1 "test"',
				'"variablesource" "string" 1 "attribute"',
				'"layertype" "string" 1 "color"',
				'"withalpha" "int" 1 0',
			],
			"point builtin:P" : [
				'"variablename" "string" 1 "P"',
				'"variablesource" "string" 1 "builtin"',
				'"layertype" "string" 1 "vector"',
				'"withalpha" "int" 1 0',
			],
			"float builtin:alpha" : [
				'"variablename" "string" 1 "alpha"',
				'"variablesource" "string" 1 "builtin"',
				'"layertype" "string" 1 "scalar"',
				'"withalpha" "int" 1 0',
			],
		}.items() :

			r = GafferScene.Private.IECoreScenePreview.Renderer.create(
				"3Delight",
				GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
				str( self.temporaryDirectory() / "test.nsi" )
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

			nsi = self.__parse( self.temporaryDirectory() / "test.nsi" )
			for e in expected :
				self.__assertInNSI( e, nsi )

	def testMesh( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"3Delight",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			str( self.temporaryDirectory() / "test.nsi" ),
		)

		r.object(
			"testPlane",
			IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ), imath.V2i( 2, 1 ) ),
			r.attributes( IECore.CompoundObject() ),
		)

		r.render()
		del r

		nsi = self.__parse( self.temporaryDirectory() / "test.nsi" )

		self.__assertInNSI( '"P.indices" "int" 8 [ 0 1 4 3 1 2 5 4 ]', nsi )
		self.__assertInNSI( '"P" "v point" 6 [ -1 -1 0 0 -1 0 1 -1 0 -1 1 0 0 1 0 1 1 0 ]', nsi )
		self.__assertInNSI( '"nvertices" "int" 2 [ 4 4 ]', nsi )
		self.__assertInNSI( '"uv" "float[2]" 6 [ 0 0 0.5 0 1 0 0 1 0.5 1 1 1 ]', nsi )
		self.__assertInNSI( '"uv.indices" "int" 8 [ 0 1 4 3 1 2 5 4 ]', nsi )

	def testAnimatedMesh( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"3Delight",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			str( self.temporaryDirectory() / "test.nsi" ),
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

		nsi = self.__parse( self.temporaryDirectory() / "test.nsi" )

		self.__assertInNSI( '"P.indices" "int" 4 [ 0 1 3 2 ]', nsi )
		self.assertEqual( nsi.count( '"P.indices"' ), 1 )
		self.__assertInNSI( '"P" "v point" 4 [ -1 -1 0 1 -1 0 -1 1 0 1 1 0 ]', nsi )
		self.__assertInNSI( '"P" "v point" 4 [ -2 -2 0 2 -2 0 -2 2 0 2 2 0 ]', nsi )
		self.__assertInNSI( '"nvertices" "int" 1 4', nsi )
		self.assertEqual( nsi.count( '"nvertices"' ), 1 )

	def testPoints( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"3Delight",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			str( self.temporaryDirectory() / "test.nsi" ),
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

		nsi = self.__parse( self.temporaryDirectory() / "test.nsi" )
		self.__assertInNSI( '"P" "v point" 4 [ 0 0 0 1 1 1 2 2 2 3 3 3 ]', nsi )
		self.__assertInNSI( '"width" "v float" 4 [ 1 2 3 4 ]', nsi )

	def testPointsWithoutWidth( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"3Delight",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			str( self.temporaryDirectory() / "test.nsi" ),
		)

		points = IECoreScene.PointsPrimitive( IECore.V3fVectorData( [ imath.V3f( x ) for x in range( 0, 4 ) ] ) )

		r.object(
			"testPoints",
			points,
			r.attributes( IECore.CompoundObject() ),
		)

		r.render()
		del r

		nsi = self.__parse( self.temporaryDirectory() / "test.nsi" )
		self.__assertInNSI( '"width" "float" 1 1', nsi )

	def testCurves( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"3Delight",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			str( self.temporaryDirectory() / "test.nsi" ),
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

		nsi = self.__parse( self.temporaryDirectory() / "test.nsi" )
		self.__assertInNSI( '"nvertices" "int" 2 [ 4 4 ]', nsi )
		self.__assertInNSI( '"basis" "string" 1 "b-spline"', nsi )
		self.__assertInNSI( '"P" "v point" 8 [ 0 0 0 1 1 1 2 2 2 3 3 3 0 0 0 -1 -1 -1 -2 -2 -2 -3 -3 -3 ]', nsi )

	def testDisk( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"3Delight",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			str( self.temporaryDirectory() / "test.nsi" ),
		)

		r.object(
			"testDisk",
			IECoreScene.DiskPrimitive( 2, 1 ),
			r.attributes( IECore.CompoundObject() ),
		)

		r.render()
		del r

		nsi = self.__parse( self.temporaryDirectory() / "test.nsi" )

		# 3Delight doesn't have a disk, so we must convert to particles
		self.__assertInNSI( '"particles"', nsi )
		self.__assertInNSI( '"P" "v point" 1 [ 0 0 1 ]', nsi )
		self.__assertInNSI( '"width" "v float" 1 4', nsi )
		self.__assertInNSI( '"N" "v normal" 1 [ 0 0 -1 ]', nsi )

	def testSphere( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"3Delight",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			str( self.temporaryDirectory() / "test.nsi" ),
		)

		r.object(
			"testSphere",
			IECoreScene.SpherePrimitive( 2 ),
			r.attributes( IECore.CompoundObject() ),
		)

		r.render()
		del r

		nsi = self.__parse( self.temporaryDirectory() / "test.nsi" )

		# 3Delight doesn't have a sphere, so we must convert to particles
		self.__assertInNSI( '"particles"', nsi )
		self.__assertInNSI( '"P" "v point" 1 [ 0 0 0 ]', nsi )
		self.__assertInNSI( '"width" "v float" 1 4', nsi )
		self.__assertNotInNSI( '"N"', nsi )

	def testEnvironment( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"3Delight",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			str( self.temporaryDirectory() / "test.nsi" ),
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

		nsi = self.__parse( self.temporaryDirectory() / "test.nsi" )

		self.__assertInNSI( '"environment"', nsi )
		self.__assertInNSI( '"angle" "double" 1 25', nsi )

	def testAttributes( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"3Delight",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			str( self.temporaryDirectory() / "test.nsi" ),
		)

		r.attributes( IECore.CompoundObject( {
			"dl:visibility.diffuse" : IECore.BoolData( True ),
			"dl:visibility.camera" : IECore.BoolData( False ),
			"dl:visibility.specular" : IECore.IntData( 0 ),
			"dl:visibility.reflection" : IECore.IntData( 1 ),
		} ) )

		del r

		nsi = self.__parse( self.temporaryDirectory() / "test.nsi" )

		self.__assertInNSI( '"visibility.diffuse" "int" 1 1', nsi )
		self.__assertInNSI( '"visibility.camera" "int" 1 0', nsi )
		self.__assertInNSI( '"visibility.specular" "int" 1 0', nsi )
		self.__assertInNSI( '"visibility.reflection" "int" 1 1', nsi )

	def testCamera( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"3Delight",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			str( self.temporaryDirectory() / "test.nsi" ),
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
				}
			),
			r.attributes( IECore.CompoundObject() )
		)

		r.option( "camera", IECore.StringData( "testCamera" ) )

		r.render()
		del r

		nsi = self.__parse( self.temporaryDirectory() / "test.nsi" )

		self.__assertInNSI( '"fov" "float" 1 90', nsi )
		self.__assertInNSI( '"resolution" "int[2]" 1 [ 2000 1000 ]', nsi )
		self.__assertInNSI( '"screenwindow" "double[2]" 2 [ -1.5 -0.75 1.5 0.75 ]', nsi )
		self.__assertInNSI( '"pixelaspectratio" "float" 1 1', nsi )
		self.__assertInNSI( '"clippingrange" "double" 2 [ 0.25 10 ]', nsi )
		self.__assertInNSI( '"shutterrange" "double" 2 [ 0 1 ]', nsi )

	def testObjectInstancing( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"3Delight",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			str( self.temporaryDirectory() / "test.nsi" ),
		)

		m = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) )
		a = r.attributes( IECore.CompoundObject() )

		r.object( "testPlane1", m, a )
		r.object( "testPlane2", m, a )

		r.render()
		del r

		nsi = self.__parse( self.temporaryDirectory() / "test.nsi" )

		self.assertEqual( nsi.count( '"transform"' ), 2 )
		self.assertEqual( nsi.count( '"mesh"' ), 1 )

	def testTransform( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"3Delight",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
			str( self.temporaryDirectory() / "test.nsi" ),
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

		nsi = self.__parse( self.temporaryDirectory() / "test.nsi" )

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
				str( self.temporaryDirectory() / "test.nsi" ),
			)

			s = IECoreScene.ShaderNetwork( { "output" : IECoreScene.Shader( "testShader", "surface", { "testStringSubstituted" : text } ) }, output = "output" )

			m = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) )
			attrs = attributes.copy()
			attrs["osl:surface"] = s
			a = r.attributes( IECore.CompoundObject( attrs ) )

			r.object( "object", m, a )

			r.render()
			del r

			nsi = open( self.temporaryDirectory() / "test.nsi", encoding = "utf-8" ).read()
			return re.findall( '\n *"testStringSubstituted" "string" 1 "(.*)" \n', nsi )[0]

		self.assertEqual( runSubstitutions( "<attr:test:foo> TEST <attr:test:bar>", {} ), " TEST " )
		self.assertEqual( runSubstitutions( "<attr:test:foo> TEST <attr:test:bar>", { "test:bar" : IECore.StringData( "AAA" ) } ), " TEST AAA" )
		self.assertEqual( runSubstitutions( "<attr:test:foo> TEST <attr:test:bar>", { "test:foo" : IECore.StringData( "AAA" ), "test:bar" : IECore.StringData( "BBB" ) } ), "AAA TEST BBB" )

	def testMessageHandler( self ) :

		RenderType = GafferScene.Private.IECoreScenePreview.Renderer.RenderType

		for renderType, fileName, expected in (
			( RenderType.Batch, "", 2 ),
			( RenderType.Interactive, "", 2 ),
			( RenderType.SceneDescription, str( self.temporaryDirectory() / "test.nsi" ), 1 )
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

if __name__ == "__main__":
	unittest.main()
