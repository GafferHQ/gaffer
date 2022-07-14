##########################################################################
#
#  Copyright (c) 2013-2014, John Haddon. All rights reserved.
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
import imath

import IECore
import IECoreScene

import Gaffer
import GafferOSL
import GafferOSLTest

class ShadingEngineTest( GafferOSLTest.OSLTestCase ) :

	def rectanglePoints( self, bound = imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ), divisions = imath.V2i( 10 ) ) :

		r = imath.Rand48()

		pData = IECore.V3fVectorData()
		uData = IECore.FloatVectorData()
		vData = IECore.FloatVectorData()
		floatUserData = IECore.FloatVectorData()
		colorUserData = IECore.Color3fVectorData()
		doubleUserData = IECore.DoubleVectorData()
		for y in range( 0, divisions.y ) :
			for x in range( 0, divisions.x ) :
				u = float( x ) / float( divisions.x - 1 )
				v = float( y ) / float( divisions.y - 1 )
				pData.append( imath.V3f(
					bound.min().x + u * bound.size().x,
					bound.min().y + v * bound.size().y,
					0
				) )
				uData.append( u )
				vData.append( v )
				floatUserData.append( r.nextf( 0, 1 ) )
				colorUserData.append( imath.Color3f( r.nextf(), r.nextf(), r.nextf() ) )
				doubleUserData.append( y * divisions.x  + x )

		return IECore.CompoundData( {
			"P" : pData,
			"u" : uData,
			"v" : vData,
			"floatUserData" : floatUserData,
			"colorUserData" : colorUserData,
			"doubleUserData" : doubleUserData
		} )

	def test( self ) :

		s = self.compileShader( os.path.dirname( __file__ ) +  "/shaders/constant.osl" )

		e = GafferOSL.ShadingEngine( IECoreScene.ShaderNetwork(
			shaders = {
				"constant" : IECoreScene.Shader( s, "osl:surface", { "Cs" : imath.Color3f( 1, 0.5, 0.25 ) } ),
			},
			output = "constant",
		) )

		p = e.shade( self.rectanglePoints() )

		self.assertEqual( p["Ci"], IECore.Color3fVectorData( [ imath.Color3f( 1, 0.5, 0.25 ) ] * 100 ) )

	def testNetwork( self ) :

		constant = self.compileShader( os.path.dirname( __file__ ) +  "/shaders/constant.osl" )
		input = self.compileShader( os.path.dirname( __file__ ) +  "/shaders/outputTypes.osl" )

		e = GafferOSL.ShadingEngine( IECoreScene.ShaderNetwork(
			shaders = {
				"outputTypes" : IECoreScene.Shader( input, "osl:shader", { "input" : 0.5 } ),
				"constant" : IECoreScene.Shader( constant, "osl:surface" ),
			},
			connections = [
				( ( "outputTypes", "c" ), ( "constant", "Cs" ) )
			],
			output = "constant"
		) )

		p = e.shade( self.rectanglePoints() )

		self.assertEqual( p["Ci"], IECore.Color3fVectorData( [ imath.Color3f( 0.5 ) ] * 100 ) )

	def testGlobals( self ) :

		shader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/globals.osl" )

		rp = self.rectanglePoints()

		for n in ( "P", "u", "v" ) :
			e = GafferOSL.ShadingEngine( IECoreScene.ShaderNetwork(
				shaders = {
					"output" : IECoreScene.Shader( shader, "osl:surface", { "global" : n } )
				},
				output = "output"
			) )
			p = e.shade( rp )
			v1 = p["Ci"]
			v2 = rp[n]
			for i in range( 0, len( v1 ) ) :
				self.assertEqual( v1[i], imath.Color3f( v2[i] ) )

	def testDoubleAsIntViaGetAttribute( self ) :

		shader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/intAttribute.osl" )

		rp = self.rectanglePoints()

		e = GafferOSL.ShadingEngine( IECoreScene.ShaderNetwork(
			shaders = {
				"output" : IECoreScene.Shader( shader, "osl:surface", { "name" : "doubleUserData" } ),
			},
			output = "output"
		) )

		self.assertEqual( e.needsAttribute( "floatUserData" ), False )
		self.assertEqual( e.needsAttribute( "doubleUserData" ), True )

		p = e.shade( rp )

		for i, c in enumerate( p["Ci"] ) :
			self.assertEqual( c[0], float(i) )

	def testUserDataViaGetAttribute( self ) :

		shader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/attribute.osl" )

		rp = self.rectanglePoints()

		e = GafferOSL.ShadingEngine( IECoreScene.ShaderNetwork(
			shaders = {
				"output" : IECoreScene.Shader( shader, "osl:surface", { "name" : "floatUserData" } ),
			},
			output = "output"
		) )

		self.assertEqual( e.needsAttribute( "floatUserData" ), True )
		self.assertEqual( e.needsAttribute( "doubleUserData" ), False )
		self.assertEqual( e.needsAttribute( "colorUserData" ), False )
		self.assertEqual( e.needsAttribute( "shading:index" ), False )

		p = e.shade( rp )

		e = GafferOSL.ShadingEngine( IECoreScene.ShaderNetwork(
			shaders = {
				"output" : IECoreScene.Shader( shader, "osl:surface", { "name" : "doubleUserData" } ),
			},
			output = "output"
		) )

		self.assertEqual( e.needsAttribute( "floatUserData" ), False )
		self.assertEqual( e.needsAttribute( "doubleUserData" ), True )
		self.assertEqual( e.needsAttribute( "colorUserData" ), False )
		self.assertEqual( e.needsAttribute( "shading:index" ), False )

		p = e.shade( rp )

		for i, c in enumerate( p["Ci"] ) :
			self.assertEqual( c[0], float(i) )

		e = GafferOSL.ShadingEngine( IECoreScene.ShaderNetwork(
			shaders = {
				"output" : IECoreScene.Shader( shader, "osl:surface", { "name" : "colorUserData" } ),
			},
			output = "output"
		) )

		self.assertEqual( e.needsAttribute( "floatUserData" ), False )
		self.assertEqual( e.needsAttribute( "doubleUserData" ), False )
		self.assertEqual( e.needsAttribute( "colorUserData" ), True )
		self.assertEqual( e.needsAttribute( "shading:index" ), False )

		p = e.shade( rp )

		for i, c in enumerate( p["Ci"] ) :
			self.assertEqual( c, rp["colorUserData"][i] )


		e = GafferOSL.ShadingEngine( IECoreScene.ShaderNetwork(
			shaders = {
				"output" : IECoreScene.Shader( shader, "osl:surface", { "name" : "shading:index" } ),
			},
			output = "output"
		) )

		self.assertEqual( e.needsAttribute( "floatUserData" ), False )
		self.assertEqual( e.needsAttribute( "doubleUserData" ), False )
		self.assertEqual( e.needsAttribute( "colorUserData" ), False )
		self.assertEqual( e.needsAttribute( "shading:index" ), True )

		p = e.shade( rp )

		for i, c in enumerate( p["Ci"] ) :
			self.assertEqual( c, imath.Color3f(i) )

	def testDynamicAttributesAllAttributesAreNeeded( self ) :

		shader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/dynamicAttribute.osl" )

		e = GafferOSL.ShadingEngine( IECoreScene.ShaderNetwork(
			shaders = {
				"output" : IECoreScene.Shader( shader, "osl:surface" )
			},
			output = "output"
		) )

		self.assertEqual( e.needsAttribute( "foo" ), True )
		self.assertEqual( e.needsAttribute( "bar" ), True )

	def testStructs( self ) :

		shader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/structs.osl" )
		constant = self.compileShader( os.path.dirname( __file__ ) + "/shaders/constant.osl" )

		e = GafferOSL.ShadingEngine( IECoreScene.ShaderNetwork(
			shaders = {
				"structs" : IECoreScene.Shader( shader, "osl:shader", { "s.c" : imath.Color3f( 0.1, 0.2, 0.3 ) } ),
				"constant" : IECoreScene.Shader( constant, "osl:surface" ),
			},
			connections = [
				( ( "structs", "c" ), ( "constant", "Cs" ) )
			],
			output = "constant"
		) )
		p = e.shade( self.rectanglePoints() )

		for c in p["Ci"] :
			self.assertEqual( c, imath.Color3f( 0.1, 0.2, 0.3 ) )

	def testClosureParameters( self ) :

		outputClosure = self.compileShader( os.path.dirname( __file__ ) + "/shaders/outputClosure.osl" )
		inputClosure = self.compileShader( os.path.dirname( __file__ ) + "/shaders/inputClosure.osl" )

		e = GafferOSL.ShadingEngine( IECoreScene.ShaderNetwork(
			shaders = {
				"outputClosure" : IECoreScene.Shader( outputClosure, "osl:shader", { "e" : imath.Color3f( 0.1, 0.2, 0.3 ) } ),
				"inputClosure" : IECoreScene.Shader( inputClosure, "osl:surface" ),
			},
			connections = [
				( ( "outputClosure", "c" ), ( "inputClosure", "i" ) )
			],
			output = "inputClosure"
		) )
		p = e.shade( self.rectanglePoints() )

		for c in p["Ci"] :
			self.assertEqual( c, imath.Color3f( 0.1, 0.2, 0.3 ) )

	def testDebugClosure( self ) :

		shader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/debugClosure.osl" )

		e = GafferOSL.ShadingEngine( IECoreScene.ShaderNetwork(
			shaders = {
				"output" : IECoreScene.Shader( shader, "osl:surface", { "name" : "a", "weight" : imath.Color3f( 1, 0, 0 ) } ),
			},
			output = "output"
		) )

		points = self.rectanglePoints()
		shading = e.shade( points )

		self.assertTrue( "Ci" in shading )
		self.assertTrue( "a" in shading )

		self.assertEqual( len( shading["a"] ), len( points["P"] ) )

		for c in shading["Ci"] :
			self.assertEqual( c, imath.Color3f( 0 ) )

		for a in shading["a"] :
			self.assertEqual( a, imath.Color3f( 1, 0, 0 ) )

	def testMultipleDebugClosures( self ) :

		shader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/multipleDebugClosures.osl" )

		e = GafferOSL.ShadingEngine( IECoreScene.ShaderNetwork(
			shaders = {
				"output" : IECoreScene.Shader( shader, "osl:surface", {} ),
			},
			output = "output"
		) )

		points = self.rectanglePoints()
		shading =e.shade( self.rectanglePoints() )

		for n in ( "u", "v", "P" ) :
			for i in range( 0, len( shading[n] ) ) :
				self.assertEqual( shading[n][i], imath.Color3f( points[n][i] ) )

	def testTypedDebugClosure( self ) :

		shader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/typedDebugClosure.osl" )

		e = GafferOSL.ShadingEngine( IECoreScene.ShaderNetwork(
			shaders = {
				"output" : IECoreScene.Shader( shader, "osl:surface", {} ),
			},
			output = "output"
		) )

		points = self.rectanglePoints()
		shading = e.shade( self.rectanglePoints() )

		self.assertTrue( isinstance( shading["f"], IECore.FloatVectorData ) )
		self.assertTrue( isinstance( shading["p"], IECore.V3fVectorData ) )
		self.assertTrue( isinstance( shading["v"], IECore.V3fVectorData ) )
		self.assertTrue( isinstance( shading["n"], IECore.V3fVectorData ) )
		self.assertTrue( isinstance( shading["c"], IECore.Color3fVectorData ) )
		self.assertTrue( isinstance( shading["p2"], IECore.V2fVectorData ) )
		self.assertTrue( isinstance( shading["v2"], IECore.V2fVectorData ) )
		self.assertTrue( isinstance( shading["n2"], IECore.V2fVectorData ) )
		self.assertTrue( isinstance( shading["uv"], IECore.V2fVectorData ) )

		self.assertEqual( shading["p"].getInterpretation(), IECore.GeometricData.Interpretation.Point )
		self.assertEqual( shading["v"].getInterpretation(), IECore.GeometricData.Interpretation.Vector )
		self.assertEqual( shading["n"].getInterpretation(), IECore.GeometricData.Interpretation.Normal )
		self.assertEqual( shading["p2"].getInterpretation(), IECore.GeometricData.Interpretation.Point )
		self.assertEqual( shading["v2"].getInterpretation(), IECore.GeometricData.Interpretation.Vector )
		self.assertEqual( shading["n2"].getInterpretation(), IECore.GeometricData.Interpretation.Normal )
		self.assertEqual( shading["uv"].getInterpretation(), IECore.GeometricData.Interpretation.UV )

		for i in range( 0, len( points["P"] ) ) :
			self.assertEqual( shading["f"][i], points["u"][i] )

		for n in ( "p", "v", "n", "c" ) :
			for i in range( 0, len( points["P"] ) ) :
				self.assertEqual( shading[n][i][0], points["P"][i][0] )
				self.assertEqual( shading[n][i][1], points["P"][i][1] )
				self.assertEqual( shading[n][i][2], points["P"][i][2] )

		for n in ( "p2", "v2", "n2", "uv" ) :
			for i in range( 0, len( points["P"] ) ) :
				self.assertEqual( shading[n][i][0], points["P"][i][0] )
				self.assertEqual( shading[n][i][1], points["P"][i][1] )

	def testDebugClosureWithInternalValue( self ) :

		shader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/debugClosureWithInternalValue.osl" )

		e = GafferOSL.ShadingEngine( IECoreScene.ShaderNetwork(
			shaders = {
				"output" : IECoreScene.Shader( shader, "osl:surface", { "value" : imath.Color3f( 1, 0.5, 0.25 ) } ),
			},
			output = "output",
		) )

		points = self.rectanglePoints()
		shading = e.shade( self.rectanglePoints() )

		self.assertTrue( isinstance( shading["f"], IECore.FloatVectorData ) )
		self.assertTrue( isinstance( shading["p"], IECore.V3fVectorData ) )
		self.assertTrue( isinstance( shading["v"], IECore.V3fVectorData ) )
		self.assertTrue( isinstance( shading["n"], IECore.V3fVectorData ) )
		self.assertTrue( isinstance( shading["c"], IECore.Color3fVectorData ) )

		self.assertEqual( shading["p"].getInterpretation(), IECore.GeometricData.Interpretation.Point )
		self.assertEqual( shading["v"].getInterpretation(), IECore.GeometricData.Interpretation.Vector )
		self.assertEqual( shading["n"].getInterpretation(), IECore.GeometricData.Interpretation.Normal )

		for i in range( 0, len( points["P"] ) ) :
			self.assertEqual( shading["f"][i], 1 )
			self.assertEqual( shading["p"][i], imath.V3f( 1, 0.5, 0.25 ) )
			self.assertEqual( shading["v"][i], imath.V3f( 1, 0.5, 0.25 ) )
			self.assertEqual( shading["n"][i], imath.V3f( 1, 0.5, 0.25 ) )
			self.assertEqual( shading["c"][i], imath.Color3f( 1, 0.5, 0.25 ) )

	def testDebugClosureWithZeroValue( self ) :

		shader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/debugClosureWithInternalValue.osl" )

		e = GafferOSL.ShadingEngine( IECoreScene.ShaderNetwork(
			shaders = {
				"output" : IECoreScene.Shader( shader, "osl:surface", { "value" : imath.Color3f( 0 ) } ),
			},
			output = "output"
		) )

		points = self.rectanglePoints()
		shading = e.shade( self.rectanglePoints() )

		self.assertTrue( isinstance( shading["f"], IECore.FloatVectorData ) )
		self.assertTrue( isinstance( shading["p"], IECore.V3fVectorData ) )
		self.assertTrue( isinstance( shading["v"], IECore.V3fVectorData ) )
		self.assertTrue( isinstance( shading["n"], IECore.V3fVectorData ) )
		self.assertTrue( isinstance( shading["c"], IECore.Color3fVectorData ) )

		self.assertEqual( shading["p"].getInterpretation(), IECore.GeometricData.Interpretation.Point )
		self.assertEqual( shading["v"].getInterpretation(), IECore.GeometricData.Interpretation.Vector )
		self.assertEqual( shading["n"].getInterpretation(), IECore.GeometricData.Interpretation.Normal )

		for i in range( 0, len( points["P"] ) ) :
			self.assertEqual( shading["f"][i], 0 )
			self.assertEqual( shading["p"][i], imath.V3f( 0 ) )
			self.assertEqual( shading["v"][i], imath.V3f( 0 ) )
			self.assertEqual( shading["n"][i], imath.V3f( 0 ) )
			self.assertEqual( shading["c"][i], imath.Color3f( 0 ) )

	def testSpline( self ) :

		shader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/splineParameters.osl" )
		spline =  IECore.SplinefColor3f(
			IECore.CubicBasisf.bSpline(),
			[
				( 0, imath.Color3f( 1 ) ),
				( 0, imath.Color3f( 1 ) ),
				( 1, imath.Color3f( 0 ) ),
				( 1, imath.Color3f( 0 ) ),
			]
		)

		e = GafferOSL.ShadingEngine( IECoreScene.ShaderNetwork(
			shaders = {
				"output" : IECoreScene.Shader( shader, "osl:surface", { "colorSpline" : spline } )
			},
			output = "output"
		) )

		rp = self.rectanglePoints()
		p = e.shade( rp )
		for i in range( 0, len( p["Ci"] ) ) :
			self.assertTrue( p["Ci"][i].equalWithAbsError( spline( rp["v"][i] ), 0.001 ) )

	def testMatrixInput( self ) :

		shader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/extractTranslate.osl" )

		e = GafferOSL.ShadingEngine( IECoreScene.ShaderNetwork(
			shaders = {
				"output" : IECoreScene.Shader( shader, "osl:surface", { "m" : imath.M44f().translate( imath.V3f( 1, 2, 3 ) ) } )
			},
			output = "output"
		) )

		p = e.shade( self.rectanglePoints() )
		for i in range( 0, len( p["Ci"] ) ) :
			self.assertEqual( p["translate"][i], imath.V3f( 1, 2, 3 ) )

	def testParameters( self ) :

		shader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/parameterTypes.osl" )
		e = GafferOSL.ShadingEngine( IECoreScene.ShaderNetwork(
			shaders = {
				"output" : IECoreScene.Shader( shader, "osl:surface", {
					"f" : 1.0,
					"i" : 2,
					"s" : "three",
					"c" : imath.Color3f( 4, 5, 6 ),
					"vec" : IECore.V3fData( imath.V3f( 7, 8, 9 ), IECore.GeometricData.Interpretation.Vector ),
					"p" : IECore.V3fData( imath.V3f( 10, 11, 12 ), IECore.GeometricData.Interpretation.Point ),
					"n" : IECore.V3fData( imath.V3f( 13, 14, 15 ), IECore.GeometricData.Interpretation.Normal ),
					"noInterp" : imath.V3f( 16, 17, 18 ),

				} )
			},
			output = "output"
		) )

		rp = self.rectanglePoints()
		p = e.shade( rp )
		for i in range( 0, len( p["Ci"] ) ) :
			self.assertEqual( p["Ci"][i], imath.Color3f( 0, 1, 0 ) )

	def testTransform( self ) :

		s = self.compileShader( os.path.dirname( __file__ ) +  "/shaders/transform.osl" )

		e = GafferOSL.ShadingEngine( IECoreScene.ShaderNetwork(
			shaders = {
				"output" : IECoreScene.Shader( s, "osl:surface" )
			},
			output = "output"
		) )

		p = e.shade( self.rectanglePoints() )

		# Transform has no effect if world matrix not set
		self.assertEqual( p["Ci"], IECore.Color3fVectorData( [ imath.Color3f( i ) for i in self.rectanglePoints()["P"] ] ) )

		worldMatrix = imath.M44f()
		worldMatrix.translate( imath.V3f( 2, 0, 0 ) )
		p = e.shade( self.rectanglePoints(), { "world" : GafferOSL.ShadingEngine.Transform( worldMatrix ) } )

		# Transform from object to world
		self.assertEqual( p["Ci"], IECore.Color3fVectorData( [ imath.Color3f( i + imath.V3f( 2, 0, 0 ) ) for i in self.rectanglePoints()["P"] ] ) )

		e = GafferOSL.ShadingEngine( IECoreScene.ShaderNetwork(
			shaders = {
				"output" : IECoreScene.Shader( s, "osl:surface", { "backwards" : IECore.IntData( 1 ) } )
			},
			output = "output"
		) )

		p = e.shade( self.rectanglePoints(), { "world" : GafferOSL.ShadingEngine.Transform( worldMatrix ) } )

		# Transform from world to object
		self.assertEqual( p["Ci"], IECore.Color3fVectorData( [ imath.Color3f( i + imath.V3f( -2, 0, 0 ) ) for i in self.rectanglePoints()["P"] ] ) )

	def testVectorToColorConnections( self ) :

		e = GafferOSL.ShadingEngine( IECoreScene.ShaderNetwork(
			shaders = {
				"globals" : IECoreScene.Shader( "Utility/Globals", "osl:shader" ),
				"constant" : IECoreScene.Shader( "Surface/Constant", "osl:surface" ),
			},
			connections = [
				( ( "globals", "globalP" ), ( "constant", "Cs" ) )
			],
			output = "constant"
		) )

		p = self.rectanglePoints()
		r = e.shade( p )

		for i, c in enumerate( r["Ci"] ) :
			self.assertEqual( imath.V3f( *c ), p["P"][i] )

	def testCanReadV3iArrayUserData( self ) :

		s = self.compileShader( os.path.dirname( __file__ ) +  "/shaders/V3iArrayAttributeRead.osl" )

		e = GafferOSL.ShadingEngine( IECoreScene.ShaderNetwork(
			shaders = {
				"output" : IECoreScene.Shader( s, "osl:surface" )
			},
			output = "output"
		) )

		p = self.rectanglePoints()

		numPoints = len(p["P"])
		p["v3i"] = IECore.V3iVectorData( numPoints )

		for i in range( numPoints ) :
			p["v3i"][i] = imath.V3i( [i, i + 1 , i + 2 ] )

		r = e.shade( p )

		for i, c in enumerate( r["Ci"] ) :
			if i < 50:
				expected = imath.Color3f( 0.0, i / 100.0, i / 200.0 )
			else:
				expected = imath.Color3f( 1.0, 0.0, 0.0 )

			self.assertEqual( c, expected )

	def testWarningForInvalidShaders( self ) :

		with self.assertRaises( Exception ) as engineError :
			e = GafferOSL.ShadingEngine( IECoreScene.ShaderNetwork(
				shaders = {
					"image1" : IECoreScene.Shader( "aiImage", "shader", {} ),
					"image2" : IECoreScene.Shader( "aiImage", "shader", {} ),
					"output" : IECoreScene.Shader( "Surface/Constant", "osl:surface", {} ),
				},
				connections = [
					( ( "image1", "" ), ( "output", "p1" ) ),
					( ( "image2", "" ), ( "output", "p2" ) ),
				],
				output = "output"
			) )

		self.assertEqual( str(engineError.exception), "The following shaders can't be used as they are not OSL shaders: aiImage (shader), aiImage (shader)" )

	def testReadV2fUserData( self ) :

		s = self.compileShader( os.path.dirname( __file__ ) +  "/shaders/attribute.osl" )
		e = GafferOSL.ShadingEngine( IECoreScene.ShaderNetwork(
			shaders = {
				"output" : IECoreScene.Shader( s, "osl:surface", { "name" : "v2f" } )
			},
			output = "output"
		) )

		p = self.rectanglePoints()
		p["v2f"] = IECore.V2fVectorData( [ imath.V2f( x.x, x.y ) for x in p["P"] ] )

		r = e.shade( p )

		for i, c in enumerate( r["Ci"] ) :
			self.assertEqual(
				c,
				imath.Color3f( p["P"][i].x, p["P"][i].y, 0 )
			)

	def testCanReadStringData( self ):

		s = self.compileShader( os.path.dirname( __file__ ) +  "/shaders/stringAttribute.osl" )
		e = GafferOSL.ShadingEngine( IECoreScene.ShaderNetwork(
			shaders = {
				"output" : IECoreScene.Shader( s, "osl:surface", { "name" : "strattr" } )
			},
			output = "output"
		) )

		p = self.rectanglePoints()
		p["strattr"] = IECore.StringVectorData( [ "testo" if i % 2 == 0 else "no-testo" for i in range(len(p["P"])) ] )

		r = e.shade( p )

		for i, c in enumerate( r["Ci"] ) :

			f = 1.0 if i % 2 == 0 else 0.0

			self.assertEqual(
				c,
				imath.Color3f( f, f, f )
			)

	def testUVProvidedAsV2f( self ) :

		shader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/globals.osl" )

		rp = self.rectanglePoints()
		rp["uv"] = IECore.V2fVectorData(
			[ imath.V2f( u, v ) for u, v in zip( rp["u"], rp["v"] ) ]
		)
		del rp["u"]
		del rp["v"]

		for uvIndex, uvName in enumerate( [ "u", "v" ] ) :

			e = GafferOSL.ShadingEngine( IECoreScene.ShaderNetwork(
				shaders = {
					"output" : IECoreScene.Shader( shader, "osl:surface", { "global" : uvName } ),
				},
				output = "output"
			) )

			p = e.shade( rp )
			for i, c in enumerate( p["Ci"] ) :
				self.assertEqual( c, imath.Color3f( rp["uv"][i][uvIndex] ) )

	def testTextureOrientation( self ) :

		s = self.compileShader( os.path.dirname( __file__ ) +  "/shaders/uvTextureMap.osl" )
		e = GafferOSL.ShadingEngine( IECoreScene.ShaderNetwork(
			shaders = {
				"output" : IECoreScene.Shader( s, "osl:surface", { "fileName" : os.path.dirname( __file__ ) + "/images/vRamp.tx" } )
			},
			output = "output"
		) )

		p = self.rectanglePoints()
		r = e.shade( p )

		for i, c in enumerate( r["Ci"] ) :
			self.assertAlmostEqual( c[1], p["v"][i], delta = 0.02 )

	def testArea( self ) :

		s = self.compileShader( os.path.dirname( __file__ ) +  "/shaders/area.osl" )

		e = GafferOSL.ShadingEngine( IECoreScene.ShaderNetwork(
			shaders = {
				"output" : IECoreScene.Shader( s, "osl:surface", {} )
			},
			output = "output"
		) )

		p = e.shade( self.rectanglePoints() )

		self.assertEqual( p["Ci"], IECore.Color3fVectorData( [ imath.Color3f( 0 ) ] * 100 ) )

	def testDerivatives( self ) :

		s = self.compileShader( os.path.dirname( __file__ ) +  "/shaders/derivatives.osl" )

		for direction in [ "X", "Y", "Z" ] :

			e = GafferOSL.ShadingEngine( IECoreScene.ShaderNetwork(
				shaders = {
					"output" : IECoreScene.Shader( s, "osl:surface", { "direction" : direction } ),
				},
				output = "output"
			) )

			p = e.shade( self.rectanglePoints() )
			self.assertEqual( p["Ci"], IECore.Color3fVectorData( [ imath.Color3f( 0 ) ] * 100 ) )

	def testTime( self ) :

		s = self.compileShader( os.path.dirname( __file__ ) + "/shaders/globals.osl" )

		# A shader that doesn't read time should yield a hash which
		# doesn't vary with time.

		def hashAtFrame( e, frame ) :

			with Gaffer.Context() as c :
				c.setFrame( frame )
				h = IECore.MurmurHash()
				e.hash( h )
				return h

		e = GafferOSL.ShadingEngine( IECoreScene.ShaderNetwork(
			shaders = {
				"output" : IECoreScene.Shader( s, "osl:surface", { "global" : "P" } ),
			},
			output = "output"
		) )
		self.assertEqual( hashAtFrame( e, 0 ), hashAtFrame( e, 1 ) )
		self.assertEqual( hashAtFrame( e, 1 ), hashAtFrame( e, 2 ) )

		# And a shader that does read time needs to reflect that
		# in the hash.

		e = GafferOSL.ShadingEngine( IECoreScene.ShaderNetwork(
			shaders = {
				"output" : IECoreScene.Shader( s, "osl:surface", { "global" : "time" } ),
			},
			output = "output"
		) )
		self.assertNotEqual( hashAtFrame( e, 0 ), hashAtFrame( e, 1 ) )
		self.assertNotEqual( hashAtFrame( e, 1 ), hashAtFrame( e, 2 ) )
		self.assertEqual( hashAtFrame( e, 1 ), hashAtFrame( e, 1 ) )

		# And should be able to read the time from the current context.

		def assertCanReadTime( e, time ) :

			with Gaffer.Context() as c :
				c.setTime( time )
				r = e.shade( self.rectanglePoints() )
				for c in r["Ci"] :
					self.assertEqual( c, imath.Color3f( time ) )

		assertCanReadTime( e, 0 )
		assertCanReadTime( e, 1 )

	def testContextVariable( self ) :

		s = self.compileShader( os.path.dirname( __file__ ) + "/shaders/contextVariable.osl" )

		# A shader which doesn't read a context variable should
		# have a hash which is constant with respect to that variable.

		e = GafferOSL.ShadingEngine( IECoreScene.ShaderNetwork(
			shaders = {
				"output" : IECoreScene.Shader( s, "osl:surface", { "name" : "" } ),
			},
			output = "output"
		) )

		def hashWithVariable( e, name, value ) :

			with Gaffer.Context() as c :
				c[name] = value
				h = IECore.MurmurHash()
				e.hash( h )
				return h

		self.assertEqual( hashWithVariable( e, "unused", 0 ), hashWithVariable( e, "unused", 1 ) );

		# And a shader which does read a context variable needs to reflect
		# that in the hash.

		e = GafferOSL.ShadingEngine( IECoreScene.ShaderNetwork(
			shaders = {
				"output" : IECoreScene.Shader( s, "osl:surface", { "name" : "myVariable", "type" : "int" } ),
			},
			output = "output"
		) )

		self.assertEqual( hashWithVariable( e, "unrelated", 0 ), hashWithVariable( e, "unrelated", 1 ) )
		self.assertNotEqual( hashWithVariable( e, "myVariable", 0 ), hashWithVariable( e, "myVariable", 1 ) )
		self.assertNotEqual( hashWithVariable( e, "myVariable", 1 ), hashWithVariable( e, "myVariable", 2 ) )
		self.assertEqual( hashWithVariable( e, "myVariable", 0 ), hashWithVariable( e, "myVariable", 0 ) )

		# And should be able to read the variable from the current context.

		def assertCanReadVariable( e, name, value ) :

			with Gaffer.Context() as c :
				c[name] = value
				r = e.shade( self.rectanglePoints() )
				for c in r["Ci"] :
					self.assertEqual( c, imath.Color3f( value ) )

		assertCanReadVariable( e, "myVariable", 0 )
		assertCanReadVariable( e, "myVariable", 1 )

		# Same goes for variables of other types

		e = GafferOSL.ShadingEngine( IECoreScene.ShaderNetwork(
			shaders = {
				"output" : IECoreScene.Shader( s, "osl:surface", { "name" : "myVariable", "type" : "color" } ),
			},
			output = "output"
		) )

		assertCanReadVariable( e, "myVariable", imath.Color3f( 0, 0.5, 1 ) )
		assertCanReadVariable( e, "myVariable", imath.Color3f( 1, 0.5, 0 ) )

	def testGlobalAsNeededAttribute( self ) :

		s = self.compileShader( os.path.dirname( __file__ ) + "/shaders/red.osl" )

		e = GafferOSL.ShadingEngine( IECoreScene.ShaderNetwork(
			shaders = {
				"output" : IECoreScene.Shader( s, "osl:surface", { } ),
			},
			output = "output",
		) )

		self.assertTrue( e.needsAttribute( "P" ) )
		self.assertFalse( e.needsAttribute( "N" ) )
		self.assertFalse( e.needsAttribute( "u" ) )
		self.assertFalse( e.needsAttribute( "v" ) )
		self.assertFalse( e.needsAttribute( "time" ) )

		s = self.compileShader( os.path.dirname( __file__ ) + "/shaders/globals.osl" )

		e = GafferOSL.ShadingEngine( IECoreScene.ShaderNetwork(
			shaders = {
				"output" : IECoreScene.Shader( s, "osl:surface", { "global" : "P" } ),
			},
			output = "output"
		) )

		self.assertTrue( e.needsAttribute( "P" ) )
		self.assertFalse( e.needsAttribute( "N" ) )
		self.assertFalse( e.needsAttribute( "uv" ) )
		self.assertFalse( e.needsAttribute( "u" ) )
		self.assertFalse( e.needsAttribute( "v" ) )
		self.assertFalse( e.needsAttribute( "time" ) )

		e = GafferOSL.ShadingEngine( IECoreScene.ShaderNetwork(
			shaders = {
				"output" : IECoreScene.Shader( s, "osl:surface", { "global" : "u" } ),
			},
			output = "output"
		) )

		self.assertTrue( e.needsAttribute( "P" ) )
		self.assertFalse( e.needsAttribute( "N" ) )
		self.assertTrue( e.needsAttribute( "uv" ) )
		self.assertTrue( e.needsAttribute( "u" ) )
		self.assertFalse( e.needsAttribute( "v" ) )
		self.assertFalse( e.needsAttribute( "time" ) )

	def testComponentConnections( self ) :

		e = GafferOSL.ShadingEngine( IECoreScene.ShaderNetwork(
			shaders = {
				"color1" : IECoreScene.Shader(
					"Maths/MixColor", "osl:shader",
					{
						"a" : imath.Color3f( 1, 0, 0 ),
					}
				),
				"color2" : IECoreScene.Shader( "Maths/MixColor", "osl:shader" ),
				"output" : IECoreScene.Shader( "Surface/Constant", "osl:surface" ),
			},
			connections = [
				( ( "color1", "out.r" ), ( "color2", "a.g" ) ),
				( ( "color2", "out" ), ( "output", "Cs" ) ),
			],
			output = "output"
		) )

		s = e.shade( self.rectanglePoints() )
		for c in s["Ci"] :
			self.assertEqual( c, imath.Color3f( 0, 1, 0 ) )

	def testHasDeformation( self ) :

		inputClosureShader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/inputClosure.osl" )

		e = GafferOSL.ShadingEngine( IECoreScene.ShaderNetwork(
			shaders = {
				"outPoint" : IECoreScene.Shader(
					"ObjectProcessing/OutPoint", "osl:shader",
					{
						"name" : "P"
					}
				),
				"output" : IECoreScene.Shader( inputClosureShader, "osl:surface" ),
			},
			connections = [
				( ( "outPoint", "primitiveVariable" ), ( "output", "i" ) ),
			],
			output = "output"
		) )

		self.assertTrue( e.hasDeformation() )

		e = GafferOSL.ShadingEngine( IECoreScene.ShaderNetwork(
			shaders = {
				"outPoint" : IECoreScene.Shader(
					"ObjectProcessing/OutPoint", "osl:shader",
					{
						"name" : "notP"
					}
				),
				"output" : IECoreScene.Shader( inputClosureShader, "osl:surface" ),
			},
			connections = [
				( ( "outPoint", "primitiveVariable" ), ( "output", "i" ) ),
			],
			output = "output"
		) )

		self.assertFalse( e.hasDeformation() )

	def testReadConstantArraySize1( self ) :

		s = self.compileShader( os.path.dirname( __file__ ) +  "/shaders/attribute.osl" )
		e = GafferOSL.ShadingEngine( IECoreScene.ShaderNetwork(
			shaders = {
				"output" : IECoreScene.Shader( s, "osl:surface", { "name" : "constantColor" } )
			},
			output = "output"
		) )

		p = self.rectanglePoints()
		p["constantColor"] = IECore.Color3fVectorData( [ imath.Color3f( 1, 2, 3 ) ] )

		r = e.shade( p )

		for i, c in enumerate( r["Ci"] ) :
			self.assertEqual(
				c,
				imath.Color3f( 1, 2, 3 )
			)

if __name__ == "__main__":
	unittest.main()
