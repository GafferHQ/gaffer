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

import IECore

import GafferOSL
import GafferOSLTest

class ShadingEngineTest( GafferOSLTest.OSLTestCase ) :

	def rectanglePoints( self, bound = IECore.Box2f( IECore.V2f( -1 ), IECore.V2f( 1 ) ), divisions = IECore.V2i( 10 ) ) :

		r = IECore.Rand48()

		pData = IECore.V3fVectorData()
		uData = IECore.FloatVectorData()
		vData = IECore.FloatVectorData()
		floatUserData = IECore.FloatVectorData()
		colorUserData = IECore.Color3fVectorData()
		for y in range( 0, divisions. y ) :
			for x in range( 0, divisions.x ) :
				u = float( x ) / float( divisions.x - 1 )
				v = float( y ) / float( divisions.y - 1 )
				pData.append( IECore.V3f(
					bound.min.x + u * bound.size().x,
					bound.min.y + v * bound.size().y,
					0
				) )
				uData.append( u )
				vData.append( v )
				floatUserData.append( r.nextf( 0, 1 ) )
				colorUserData.append( r.nextColor3f() )

		return IECore.CompoundData( {
			"P" : pData,
			"u" : uData,
			"v" : vData,
			"floatUserData" : floatUserData,
			"colorUserData" : colorUserData,
		} )

	def test( self ) :

		s = self.compileShader( os.path.dirname( __file__ ) +  "/shaders/constant.osl" )

		e = GafferOSL.ShadingEngine( IECore.ObjectVector( [
			IECore.Shader( s, "surface", { "Cs" : IECore.Color3f( 1, 0.5, 0.25 ) } )
		] ) )

		p = e.shade( self.rectanglePoints() )

		self.assertEqual( p["Ci"], IECore.Color3fVectorData( [ IECore.Color3f( 1, 0.5, 0.25 ) ] * 100 ) )

	def testNetwork( self ) :

		constant = self.compileShader( os.path.dirname( __file__ ) +  "/shaders/constant.osl" )
		input = self.compileShader( os.path.dirname( __file__ ) +  "/shaders/outputTypes.osl" )

		e = GafferOSL.ShadingEngine( IECore.ObjectVector( [
			IECore.Shader( input, "shader", { "input" : 0.5, "__handle" : "h" } ),
			IECore.Shader( constant, "surface", { "Cs" : "link:h.c" } ),
		] ) )

		p = e.shade( self.rectanglePoints() )

		self.assertEqual( p["Ci"], IECore.Color3fVectorData( [ IECore.Color3f( 0.5 ) ] * 100 ) )

	def testGlobals( self ) :

		shader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/globals.osl" )

		rp = self.rectanglePoints()

		for n in ( "P", "u", "v" ) :
			e = GafferOSL.ShadingEngine( IECore.ObjectVector( [
				IECore.Shader( shader, "surface", { "global" : n } )
			] ) )
			p = e.shade( rp )
			v1 = p["Ci"]
			v2 = rp[n]
			for i in range( 0, len( v1 ) ) :
				self.assertEqual( v1[i], IECore.Color3f( v2[i] ) )

	def testUserDataViaGetAttribute( self ) :

		shader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/attribute.osl" )

		rp = self.rectanglePoints()

		e = GafferOSL.ShadingEngine( IECore.ObjectVector( [
			IECore.Shader( shader, "surface", { "name" : "floatUserData" } ),
		] ) )
		p = e.shade( rp )

		for i, c in enumerate( p["Ci"] ) :
			self.assertEqual( c.r, rp["floatUserData"][i] )

		e = GafferOSL.ShadingEngine( IECore.ObjectVector( [
			IECore.Shader( shader, "surface", { "name" : "colorUserData" } ),
		] ) )
		p = e.shade( rp )

		for i, c in enumerate( p["Ci"] ) :
			self.assertEqual( c, rp["colorUserData"][i] )

	def testStructs( self ) :

		shader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/structs.osl" )
		constant = self.compileShader( os.path.dirname( __file__ ) + "/shaders/constant.osl" )

		e = GafferOSL.ShadingEngine( IECore.ObjectVector( [
			IECore.Shader( shader, "shader", { "s.c" : IECore.Color3f( 0.1, 0.2, 0.3 ), "__handle" : "h" } ),
			IECore.Shader( constant, "surface", { "Cs" : "link:h.c" } ),
		] ) )
		p = e.shade( self.rectanglePoints() )

		for c in p["Ci"] :
			self.assertEqual( c, IECore.Color3f( 0.1, 0.2, 0.3 ) )

	def testClosureParameters( self ) :

		outputClosure = self.compileShader( os.path.dirname( __file__ ) + "/shaders/outputClosure.osl" )
		inputClosure = self.compileShader( os.path.dirname( __file__ ) + "/shaders/inputClosure.osl" )

		e = GafferOSL.ShadingEngine( IECore.ObjectVector( [
			IECore.Shader( outputClosure, "shader", { "e" : IECore.Color3f( 0.1, 0.2, 0.3 ), "__handle" : "h" } ),
			IECore.Shader( inputClosure, "surface", { "i" : "link:h.c" } ),
		] ) )
		p = e.shade( self.rectanglePoints() )

		for c in p["Ci"] :
			self.assertEqual( c, IECore.Color3f( 0.1, 0.2, 0.3 ) )

	def testDebugClosure( self ) :

		shader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/debugClosure.osl" )

		e = GafferOSL.ShadingEngine( IECore.ObjectVector( [
			IECore.Shader( shader, "surface", { "name" : "a", "weight" : IECore.Color3f( 1, 0, 0 ) } ),
		] ) )

		points = self.rectanglePoints()
		shading = e.shade( points )

		self.assertTrue( "Ci" in shading )
		self.assertTrue( "a" in shading )

		self.assertEqual( len( shading["a"] ), len( points["P"] ) )

		for c in shading["Ci"] :
			self.assertEqual( c, IECore.Color3f( 0 ) )

		for a in shading["a"] :
			self.assertEqual( a, IECore.Color3f( 1, 0, 0 ) )

	def testMultipleDebugClosures( self ) :

		shader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/multipleDebugClosures.osl" )

		e = GafferOSL.ShadingEngine( IECore.ObjectVector( [
			IECore.Shader( shader, "surface", {} ),
		] ) )

		points = self.rectanglePoints()
		shading =e.shade( self.rectanglePoints() )

		for n in ( "u", "v", "P" ) :
			for i in range( 0, len( shading[n] ) ) :
				self.assertEqual( shading[n][i], IECore.Color3f( points[n][i] ) )

	def testTypedDebugClosure( self ) :

		shader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/typedDebugClosure.osl" )

		e = GafferOSL.ShadingEngine( IECore.ObjectVector( [
			IECore.Shader( shader, "surface", {} ),
		] ) )

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
			self.assertEqual( shading["f"][i], points["u"][i] )

		for n in ( "p", "v", "n", "c" ) :
			for i in range( 0, len( points["P"] ) ) :
				self.assertEqual( shading[n][i][0], points["P"][i][0] )
				self.assertEqual( shading[n][i][1], points["P"][i][1] )
				self.assertEqual( shading[n][i][2], points["P"][i][2] )

	def testDebugClosureWithInternalValue( self ) :

		shader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/debugClosureWithInternalValue.osl" )

		e = GafferOSL.ShadingEngine( IECore.ObjectVector( [
			IECore.Shader( shader, "surface", { "value" : IECore.Color3f( 1, 0.5, 0.25 ) } ),
		] ) )

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
			self.assertEqual( shading["p"][i], IECore.V3f( 1, 0.5, 0.25 ) )
			self.assertEqual( shading["v"][i], IECore.V3f( 1, 0.5, 0.25 ) )
			self.assertEqual( shading["n"][i], IECore.V3f( 1, 0.5, 0.25 ) )
			self.assertEqual( shading["c"][i], IECore.Color3f( 1, 0.5, 0.25 ) )

	def testDebugClosureWithZeroValue( self ) :

		shader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/debugClosureWithInternalValue.osl" )

		e = GafferOSL.ShadingEngine( IECore.ObjectVector( [
			IECore.Shader( shader, "surface", { "value" : IECore.Color3f( 0 ) } ),
		] ) )

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
			self.assertEqual( shading["p"][i], IECore.V3f( 0 ) )
			self.assertEqual( shading["v"][i], IECore.V3f( 0 ) )
			self.assertEqual( shading["n"][i], IECore.V3f( 0 ) )
			self.assertEqual( shading["c"][i], IECore.Color3f( 0 ) )

	def testSpline( self ) :

		shader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/splineParameters.osl" )
		spline =  IECore.SplinefColor3f(
			IECore.CubicBasisf.bSpline(),
			[
				( 0, IECore.Color3f( 1 ) ),
				( 0, IECore.Color3f( 1 ) ),
				( 1, IECore.Color3f( 0 ) ),
				( 1, IECore.Color3f( 0 ) ),
			]
		)

		e = GafferOSL.ShadingEngine( IECore.ObjectVector( [
			IECore.Shader( shader, "surface", { "colorSpline" : spline } )
		] ) )

		rp = self.rectanglePoints()
		p = e.shade( rp )
		for i in range( 0, len( p["Ci"] ) ) :
			self.assertTrue( p["Ci"][i].equalWithAbsError( spline( rp["v"][i] ), 0.001 ) )

	def testMatrixInput( self ) :

		shader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/extractTranslate.osl" )

		e = GafferOSL.ShadingEngine( IECore.ObjectVector( [
			IECore.Shader( shader, "surface", { "m" : IECore.M44f().translate( IECore.V3f( 1, 2, 3 ) ) } )
		] ) )

		p = e.shade( self.rectanglePoints() )
		for i in range( 0, len( p["Ci"] ) ) :
			self.assertEqual( p["translate"][i], IECore.V3f( 1, 2, 3 ) )

	def testParameters( self ) :

		shader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/parameterTypes.osl" )
		e = GafferOSL.ShadingEngine( IECore.ObjectVector( [
			IECore.Shader( shader, "surface", {
				"f" : 1.0,
				"i" : 2,
				"s" : "three",
				"c" : IECore.Color3f( 4, 5, 6 ),
				"vec" : IECore.V3fData( IECore.V3f( 7, 8, 9 ), IECore.GeometricData.Interpretation.Vector ),
				"p" : IECore.V3fData( IECore.V3f( 10, 11, 12 ), IECore.GeometricData.Interpretation.Point ),
				"n" : IECore.V3fData( IECore.V3f( 13, 14, 15 ), IECore.GeometricData.Interpretation.Normal ),
				"noInterp" : IECore.V3f( 16, 17, 18 ),

			 } )
		] ) )

		rp = self.rectanglePoints()
		p = e.shade( rp )
		for i in range( 0, len( p["Ci"] ) ) :
			self.assertEqual( p["Ci"][i], IECore.Color3f( 0, 1, 0 ) )

	def testTransform( self ) :

		s = self.compileShader( os.path.dirname( __file__ ) +  "/shaders/transform.osl" )

		e = GafferOSL.ShadingEngine( IECore.ObjectVector( [
			IECore.Shader( s, "surface" )
		] ) )

		p = e.shade( self.rectanglePoints() )

		# Transform has no effect if world matrix not set
		self.assertEqual( p["Ci"], IECore.Color3fVectorData( [ IECore.Color3f( i ) for i in self.rectanglePoints()["P"] ] ) )

		worldMatrix = IECore.M44f()
		worldMatrix.translate( IECore.V3f( 2, 0, 0 ) )
		p = e.shade( self.rectanglePoints(), { "world" : GafferOSL.ShadingEngine.Transform( worldMatrix ) } )

		# Transform from object to world
		self.assertEqual( p["Ci"], IECore.Color3fVectorData( [ IECore.Color3f( i + IECore.V3f( 2, 0, 0 ) ) for i in self.rectanglePoints()["P"] ] ) )

		e = GafferOSL.ShadingEngine( IECore.ObjectVector( [
			IECore.Shader( s, "surface", { "backwards" : IECore.IntData( 1 ) } )
		] ) )

		p = e.shade( self.rectanglePoints(), { "world" : GafferOSL.ShadingEngine.Transform( worldMatrix ) } )

		# Transform from world to object
		self.assertEqual( p["Ci"], IECore.Color3fVectorData( [ IECore.Color3f( i + IECore.V3f( -2, 0, 0 ) ) for i in self.rectanglePoints()["P"] ] ) )


if __name__ == "__main__":
	unittest.main()
