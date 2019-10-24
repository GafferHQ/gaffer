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
import subprocess
import inspect

import IECore
import IECoreScene

import Gaffer
import GafferTest
import GafferScene
import GafferOSL
import GafferOSLTest

class OSLObjectTest( GafferOSLTest.OSLTestCase ) :

	def test( self ) :

		p = GafferScene.Plane()
		p["dimensions"].setValue( imath.V2f( 1, 2 ) )
		p["divisions"].setValue( imath.V2i( 10 ) )

		self.assertSceneValid( p["out"] )

		o = GafferOSL.OSLObject()
		o["in"].setInput( p["out"] )

		self.assertScenesEqual( p["out"], o["out"] )

		# shading network to swap x and y

		inPoint = GafferOSL.OSLShader()
		inPoint.loadShader( "ObjectProcessing/InPoint" )

		vectorToFloat = GafferOSL.OSLShader()
		vectorToFloat.loadShader( "Conversion/VectorToFloat" )
		vectorToFloat["parameters"]["p"].setInput( inPoint["out"]["value"] )

		floatToVector = GafferOSL.OSLShader()
		floatToVector.loadShader( "Conversion/FloatToVector" )
		floatToVector["parameters"]["x"].setInput( vectorToFloat["out"]["y"] )
		floatToVector["parameters"]["y"].setInput( vectorToFloat["out"]["x"] )

		outPoint = GafferOSL.OSLShader()
		outPoint.loadShader( "ObjectProcessing/OutPoint" )
		outPoint["parameters"]["value"].setInput( floatToVector["out"]["p"] )

		primVarShader = GafferOSL.OSLShader()
		primVarShader.loadShader( "ObjectProcessing/OutObject" )
		primVarShader["parameters"]["in0"].setInput( outPoint["out"]["primitiveVariable"] )

		o["shader"].setInput( primVarShader["out"]["out"] )

		self.assertScenesEqual( p["out"], o["out"] )

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		o["filter"].setInput( filter["out"] )

		self.assertSceneValid( o["out"] )

		boundIn = p["out"].bound( "/plane" )
		boundOut = o["out"].bound( "/plane" )

		self.assertEqual( boundIn.min().x, boundOut.min().y )
		self.assertEqual( boundIn.max().x, boundOut.max().y )
		self.assertEqual( boundIn.min().y, boundOut.min().x )
		self.assertEqual( boundIn.max().y, boundOut.max().x )

	def testTransform( self ) :

		p = GafferScene.Plane()
		p["transform"]["translate"].setValue( imath.V3f( 2, 0, 0 ) )

		o = GafferOSL.OSLObject()
		o["in"].setInput( p["out"] )

		# shading network to swap x and y

		inPoint = GafferOSL.OSLShader()
		inPoint.loadShader( "ObjectProcessing/InPoint" )

		code = GafferOSL.OSLCode()
		code["parameters"].addChild( Gaffer.V3fPlug( "in" ) )
		code["out"].addChild( Gaffer.Color3fPlug( "transformed", direction = Gaffer.Plug.Direction.Out ) )
		code["out"].addChild( Gaffer.Color3fPlug( "transformedBack", direction = Gaffer.Plug.Direction.Out ) )
		code["code"].setValue( 'transformed = transform( "world", point( in ) );\ntransformedBack = transform( "world", "object", point( transformed ) );' )

		code["parameters"]["in"].setInput( inPoint["out"]["value"] )

		outTransformed = GafferOSL.OSLShader()
		outTransformed.loadShader( "ObjectProcessing/OutColor" )
		outTransformed["parameters"]["name"].setValue( 'transformed' )
		outTransformed["parameters"]["value"].setInput( code["out"]["transformed"] )

		outTransformedBack = GafferOSL.OSLShader()
		outTransformedBack.loadShader( "ObjectProcessing/OutColor" )
		outTransformedBack["parameters"]["name"].setValue( 'transformedBack' )
		outTransformedBack["parameters"]["value"].setInput( code["out"]["transformedBack"] )

		primVarShader = GafferOSL.OSLShader()
		primVarShader.loadShader( "ObjectProcessing/OutObject" )
		primVarShader["parameters"]["in0"].setInput( outTransformed["out"]["primitiveVariable"] )
		primVarShader["parameters"]["in1"].setInput( outTransformedBack["out"]["primitiveVariable"] )

		o["shader"].setInput( primVarShader["out"]["out"] )

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		o["filter"].setInput( filter["out"] )

		self.assertEqual( o["out"].object( "/plane" )["transformed"].data, IECore.Color3fVectorData( [ imath.Color3f( -0.5, -0.5, 0 ), imath.Color3f( 0.5, -0.5, 0 ), imath.Color3f( -0.5, 0.5, 0 ), imath.Color3f( 0.5, 0.5, 0 ) ] ) )

		o["useTransform"].setValue( True )
		self.assertEqual( o["out"].object( "/plane" )["transformed"].data, IECore.Color3fVectorData( [ imath.Color3f( 1.5, -0.5, 0 ), imath.Color3f( 2.5, -0.5, 0 ), imath.Color3f( 1.5, 0.5, 0 ), imath.Color3f( 2.5, 0.5, 0 ) ] ) )
		self.assertEqual( o["out"].object( "/plane" )["transformedBack"].data, IECore.Color3fVectorData( [ imath.Color3f( -0.5, -0.5, 0 ), imath.Color3f( 0.5, -0.5, 0 ), imath.Color3f( -0.5, 0.5, 0 ), imath.Color3f( 0.5, 0.5, 0 ) ] ) )

	def testAcceptsShaderSwitch( self ) :

		script = Gaffer.ScriptNode()
		script["object"] = GafferOSL.OSLObject()
		script["switch"] = Gaffer.Switch()
		script["switch"].setup( Gaffer.Plug() )

		# We're testing a backwards compatibility special case that is
		# only enabled when loading a script, hence the use of `execute()`.
		script.execute( """script["object"]["shader"].setInput( script["switch"]["out"] )""" )
		self.assertTrue( script["object"]["primitiveVariables"]["legacyClosure"]["value"].getInput().isSame( script["switch"]["out"] ) )

	def testAcceptsDot( self ) :

		script = Gaffer.ScriptNode()
		script["object"] = GafferOSL.OSLObject()
		script["switch"] = Gaffer.Switch()
		script["switch"].setup( Gaffer.Plug() )
		script["dot"] = Gaffer.Dot()
		script["dot"].setup( script["switch"]["out"] )

		# We're testing a backwards compatibility special case that is
		# only enabled when loading a script, hence the use of `execute()`.
		script.execute( """script["object"]["shader"].setInput( script["dot"]["out"] )""" )
		self.assertTrue( script["object"]["primitiveVariables"]["legacyClosure"]["value"].getInput().isSame( script["dot"]["out"] ) )

	def testPrimitiveVariableWithZeroValue( self ) :

		outPoint = GafferOSL.OSLShader()
		outPoint.loadShader( "ObjectProcessing/OutPoint" )
		outPoint["parameters"]["name"].setValue( "velocity" )
		outPoint["parameters"]["value"].setValue( imath.V3f( 0 ) )

		primVarShader = GafferOSL.OSLShader()
		primVarShader.loadShader( "ObjectProcessing/OutObject" )
		primVarShader["parameters"]["in0"].setInput( outPoint["out"]["primitiveVariable"] )

		p = GafferScene.Plane()
		p["dimensions"].setValue( imath.V2f( 1, 2 ) )
		p["divisions"].setValue( imath.V2i( 10 ) )

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		o = GafferOSL.OSLObject()
		o["in"].setInput( p["out"] )
		o["shader"].setInput( primVarShader["out"]["out"] )
		o["filter"].setInput( filter["out"] )

		for v in o["out"].object( "/plane" )["velocity"].data :
			self.assertEqual( v, imath.V3f( 0 ) )

	def testShaderAffectsBoundAndObject( self ) :

		o = GafferOSL.OSLObject()
		s = GafferOSL.OSLShader()
		s.loadShader( "ObjectProcessing/OutObject" )

		cs = GafferTest.CapturingSlot( o.plugDirtiedSignal() )

		o["shader"].setInput( s["out"]["out"] )

		self.assertTrue( o["out"]["object"] in set( x[0] for x in cs ) )
		self.assertTrue( o["out"]["bound"] in set( x[0] for x in cs ) )

	def testReferencePromotedPlug( self ) :

		s = Gaffer.ScriptNode()

		s["b"] = Gaffer.Box()
		s["b"]["o"] = GafferOSL.OSLObject()
		s["b"]["o"]["primitiveVariables"].addChild( Gaffer.NameValuePlug( "", GafferOSL.ClosurePlug(), "testClosure", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		p = Gaffer.PlugAlgo.promote( s["b"]["o"]["primitiveVariables"]["testClosure"]["value"] )
		p.setName( "p" )

		s["b"].exportForReference( self.temporaryDirectory() + "/test.grf" )

		s["r"] = Gaffer.Reference()
		s["r"].load( self.temporaryDirectory() + "/test.grf" )

		s["s"] = GafferOSL.OSLShader()
		s["s"].loadShader( "ObjectProcessing/OutObject" )

		s["r"]["p"].setInput( s["s"]["out"]["out"] )

	def testCanShadeVertexInterpolatedPrimitiveVariablesAsUniform( self ) :

		s = Gaffer.ScriptNode()

		c = GafferScene.Cube()
		s.addChild( c )

		o = GafferOSL.OSLObject()
		s.addChild( o )

		f = GafferScene.PathFilter( "PathFilter" )
		s.addChild( f )
		f["paths"].setValue( IECore.StringVectorData( [ '/cube' ] ) )
		o["filter"].setInput( f["out"] )

		# ensure the source position primitive variable interpolation is set to Vertex
		self.assertEqual(c["out"].object("/cube")['P'].interpolation, IECoreScene.PrimitiveVariable.Interpolation.Vertex )

		o['in'].setInput( c["out"] )
		o['interpolation'].setValue( IECoreScene.PrimitiveVariable.Interpolation.Uniform )

		inPoint = GafferOSL.OSLShader( "InPoint" )
		s.addChild( inPoint )
		inPoint.loadShader( "ObjectProcessing/InPoint" )

		addVector = GafferOSL.OSLShader( "AddVector" )
		s.addChild( addVector )
		addVector.loadShader( "Maths/AddVector" )
		addVector["parameters"]["b"].setValue( imath.V3f( 1, 2, 3 ) )

		addVector["parameters"]["a"].setInput( inPoint["out"]["value"] )

		outPoint = GafferOSL.OSLShader( "OutPoint" )
		s.addChild( outPoint )
		outPoint.loadShader( "ObjectProcessing/OutPoint" )
		outPoint['parameters']['name'].setValue("P_copy")

		outPoint["parameters"]["value"].setInput( addVector["out"]["out"] )

		outObject = GafferOSL.OSLShader( "OutObject" )
		s.addChild( outObject )
		outObject.loadShader( "ObjectProcessing/OutObject" )
		outObject["parameters"]["in0"].setInput( outPoint["out"]["primitiveVariable"] )

		o["shader"].setInput( outObject["out"]["out"] )

		cubeObject = s['OSLObject']['out'].object( "/cube" )

		self.assertTrue( "P_copy" in cubeObject.keys() )
		self.assertEqual( cubeObject["P_copy"].interpolation, IECoreScene.PrimitiveVariable.Interpolation.Uniform)

		self.assertEqual( cubeObject["P_copy"].data[0], imath.V3f(  0.0,  0.0, -0.5 ) + imath.V3f( 1, 2, 3 ))
		self.assertEqual( cubeObject["P_copy"].data[1], imath.V3f(  0.5,  0.0,  0.0 ) + imath.V3f( 1, 2, 3 ))
		self.assertEqual( cubeObject["P_copy"].data[2], imath.V3f(  0.0,  0.0,  0.5 ) + imath.V3f( 1, 2, 3 ))
		self.assertEqual( cubeObject["P_copy"].data[3], imath.V3f( -0.5,  0.0,  0.0 ) + imath.V3f( 1, 2, 3 ))
		self.assertEqual( cubeObject["P_copy"].data[4], imath.V3f(  0.0,  0.5,  0.0 ) + imath.V3f( 1, 2, 3 ))
		self.assertEqual( cubeObject["P_copy"].data[5], imath.V3f(  0.0, -0.5,  0.0 ) + imath.V3f( 1, 2, 3 ))

	def testCanShadeFaceVaryingInterpolatedPrimitiveVariablesAsVertex( self ) :

		s = Gaffer.ScriptNode()

		p = GafferScene.Plane()
		p["divisions"].setValue( imath.V2i( 2, 2 ) ) #  2x2 plane = 4 quads & 9 vertices
		s.addChild( p )

		o = GafferOSL.OSLObject()
		s.addChild( o )

		f = GafferScene.PathFilter( "PathFilter" )
		s.addChild( f )
		f["paths"].setValue( IECore.StringVectorData( [ '/plane' ] ) )
		o["filter"].setInput( f["out"] )

		# We're going to copy the FaceVarying UV primvar
		# into a Vertex Color3f primvar. Assert that the source
		# is indeed FaceVarying.
		self.assertEqual( p["out"].object( "/plane" )["uv"].interpolation, IECoreScene.PrimitiveVariable.Interpolation.FaceVarying )

		o['in'].setInput( p["out"] )
		o['interpolation'].setValue( IECoreScene.PrimitiveVariable.Interpolation.Vertex )

		s["inUV"] = GafferOSL.OSLShader()
		s["inUV"].loadShader( "ObjectProcessing/InVector" )
		s["inUV"]["parameters"]["name"].setValue( "uv" )

		s["outColor"] = GafferOSL.OSLShader()
		s["outColor"].loadShader( "ObjectProcessing/OutColor" )
		s["outColor"]["parameters"]["value"].setInput( s["inUV"]["out"]["value"] )
		s["outColor"]["parameters"]["name"].setValue( "c" )

		s["outObject"] = GafferOSL.OSLShader()
		s["outObject"].loadShader( "ObjectProcessing/OutObject" )
		s["outObject"]["parameters"]["in0"].setInput( s["outColor"]["out"]["primitiveVariable"] )

		o["shader"].setInput( s["outObject"]["out"]["out"] )

		planeObject = s['OSLObject']['out'].object( "/plane" )

		self.assertIn( "c", planeObject )
		self.assertEqual( planeObject["c"].interpolation, IECoreScene.PrimitiveVariable.Interpolation.Vertex )

		self.assertEqual( planeObject["c"].data[0], imath.Color3f( 0.0, 0.0, 0.0 ) )
		self.assertEqual( planeObject["c"].data[1], imath.Color3f( 0.5, 0.0, 0.0 ) )
		self.assertEqual( planeObject["c"].data[2], imath.Color3f( 1.0, 0.0, 0.0 ) )
		self.assertEqual( planeObject["c"].data[3], imath.Color3f( 0.0, 0.5, 0.0 ) )
		self.assertEqual( planeObject["c"].data[4], imath.Color3f( 0.5, 0.5, 0.0 ) )
		self.assertEqual( planeObject["c"].data[5], imath.Color3f( 1.0, 0.5, 0.0 ) )
		self.assertEqual( planeObject["c"].data[6], imath.Color3f( 0.0, 1.0, 0.0 ) )
		self.assertEqual( planeObject["c"].data[7], imath.Color3f( 0.5, 1.0, 0.0 ) )
		self.assertEqual( planeObject["c"].data[8], imath.Color3f( 1.0, 1.0, 0.0 ) )

	def testCanReadFromConstantPrimitiveVariables( self ) :

		s = Gaffer.ScriptNode()

		p = GafferScene.Plane()
		p["divisions"].setValue( imath.V2i( 2, 2 ) ) #  2x2 plane = 4 quads & 9 vertices
		s.addChild( p )

		o = GafferOSL.OSLObject()
		s.addChild( o )

		f = GafferScene.PathFilter( "PathFilter" )
		s.addChild( f )
		f["paths"].setValue( IECore.StringVectorData( [ '/plane' ] ) )
		o["filter"].setInput( f["out"] )


		pv = GafferScene.PrimitiveVariables( "PrimitiveVariables" )
		s.addChild( pv )

		pv["primitiveVariables"].addChild( Gaffer.CompoundDataPlug.MemberPlug( "member1", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ) )
		pv["primitiveVariables"]["member1"].addChild( Gaffer.StringPlug( "name", defaultValue = '', flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ) )
		pv["primitiveVariables"]["member1"]["name"].setValue( 'const_foo' )
		pv["primitiveVariables"]["member1"].addChild( Gaffer.FloatPlug( "value", defaultValue = 0.0, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ) )
		pv["primitiveVariables"]["member1"]["value"].setValue( 1 )
		pv["primitiveVariables"]["member1"].addChild( Gaffer.BoolPlug( "enabled", defaultValue = True, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ) )

		pv["in"].setInput( p["out"] )
		pv["filter"].setInput( f["out"] )

		o['in'].setInput( pv["out"] )
		o['interpolation'].setValue( IECoreScene.PrimitiveVariable.Interpolation.Vertex )

		inConstFoo = GafferOSL.OSLShader( "InFloat" )
		s.addChild( inConstFoo )
		inConstFoo.loadShader( "ObjectProcessing/InFloat" )
		inConstFoo['parameters']['name'].setValue('const_foo')


		outFloat = GafferOSL.OSLShader( "OutFloat" )
		s.addChild( outFloat )
		outFloat.loadShader( "ObjectProcessing/OutFloat" )
		outFloat['parameters']['name'].setValue("out_foo")

		outFloat["parameters"]["value"].setInput( inConstFoo["out"]["value"] )

		outObject = GafferOSL.OSLShader( "OutObject" )
		s.addChild( outObject )
		outObject.loadShader( "ObjectProcessing/OutObject" )
		outObject["parameters"]["in0"].setInput( outFloat["out"]["primitiveVariable"] )

		o["shader"].setInput( outObject["out"]["out"] )

		planeObject = s['OSLObject']['out'].object( "/plane" )

		self.assertTrue( "out_foo" in planeObject.keys() )
		self.assertEqual( planeObject["out_foo"].interpolation, IECoreScene.PrimitiveVariable.Interpolation.Vertex)

		self.assertEqual( planeObject["out_foo"].data[0], 1)
		self.assertEqual( planeObject["out_foo"].data[1], 1)
		self.assertEqual( planeObject["out_foo"].data[2], 1)
		self.assertEqual( planeObject["out_foo"].data[3], 1)
		self.assertEqual( planeObject["out_foo"].data[4], 1)
		self.assertEqual( planeObject["out_foo"].data[5], 1)
		self.assertEqual( planeObject["out_foo"].data[6], 1)
		self.assertEqual( planeObject["out_foo"].data[7], 1)
		self.assertEqual( planeObject["out_foo"].data[8], 1)

	def testCanShadeIndexedPrimVar( self ) :

		points = IECoreScene.PointsPrimitive( 4096 )

		points["P"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.V3fVectorData( [imath.V3f( 1, 2, 3 ), imath.V3f( 4, 5, 6 )] ), IECore.IntVectorData( [1, 0] * 2048 ) )

		objectToScene = GafferScene.ObjectToScene()
		objectToScene['object'].setValue( points )

		oslObject = GafferOSL.OSLObject()
		oslObject['in'].setInput( objectToScene["out"] )

		inPoint = GafferOSL.OSLShader( "InPoint" )
		inPoint.loadShader( "ObjectProcessing/InPoint" )

		outPoint = GafferOSL.OSLShader( "OutPoint" )
		outPoint.loadShader( "ObjectProcessing/OutPoint" )

		outObject = GafferOSL.OSLShader( "OutObject" )
		outObject.loadShader( "ObjectProcessing/OutObject" )

		oslObject["shader"].setInput( outObject["out"]["out"] )

		outPoint["parameters"]["value"].setInput( inPoint["out"]["value"] )
		outPoint["parameters"]["value"]["x"].setInput( inPoint["out"]["value"]["x"] )
		outPoint["parameters"]["value"]["y"].setInput( inPoint["out"]["value"]["y"] )
		outPoint["parameters"]["value"]["z"].setInput( inPoint["out"]["value"]["z"] )

		outObject["parameters"]["in0"].setInput( outPoint["out"]["primitiveVariable"] )

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( ["/object"] ) )

		oslObject["filter"].setInput( filter["out"] )

		processedPoints = oslObject['out'].object( "/object" )

		# currently the P should be expanded.
		self.assertEqual( processedPoints["P"].data,
			IECore.V3fVectorData( [imath.V3f( 4, 5, 6 ), imath.V3f( 1, 2, 3 )] * 2048, IECore.GeometricData.Interpretation.Point ) )
		self.assertEqual( processedPoints["P"].indices, None )

	def testTextureOrientation( self ) :

		textureFileName = os.path.dirname( __file__ ) + "/images/vRamp.tx"


		outColor = GafferOSL.OSLCode()
		outColor["out"]["c"] = GafferOSL.ClosurePlug(
			direction = Gaffer.Plug.Direction.Out,
			flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic
		)
		outColor["code"].setValue( 'c = outColor( "Cs", texture( "{}", u, v ) )'.format( textureFileName ) )

		outObject = GafferOSL.OSLShader()
		outObject.loadShader( "ObjectProcessing/OutObject" )
		outObject["parameters"]["in0"].setInput( outColor["out"]["c"] )

		plane = GafferScene.Plane()
		plane["divisions"].setValue( imath.V2i( 32 ) )

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		resample = GafferScene.ResamplePrimitiveVariables()
		resample["in"].setInput( plane["out"] )
		resample["filter"].setInput( filter["out"] )
		resample["names"].setValue( "uv" )

		oslObject = GafferOSL.OSLObject()
		oslObject["in"].setInput( resample["out"] )
		oslObject["shader"].setInput( outObject["out"]["out"] )
		oslObject["filter"].setInput( filter["out"] )

		mesh = oslObject["out"].object( "/plane" )

		for i, c in enumerate( mesh["Cs"].data ) :
			self.assertAlmostEqual( c.r, mesh["uv"].data[i].y, delta = 0.02 )

	def testCanReadAndWriteMatrices( self ) :

		s = Gaffer.ScriptNode()

		p = GafferScene.Plane()
		p["divisions"].setValue( imath.V2i( 2, 2 ) )  # 2x2 plane = 4 quads & 9 vertices
		s.addChild( p )

		o = GafferOSL.OSLObject()
		s.addChild( o )

		o['in'].setInput( p["out"] )

		f = GafferScene.PathFilter( "PathFilter" )
		s.addChild( f )
		f["paths"].setValue( IECore.StringVectorData( ['/plane'] ) )
		o["filter"].setInput( f["out"] )

		outMatrix = GafferOSL.OSLShader( "OutMatrix" )
		s.addChild( outMatrix )
		outMatrix.loadShader( "ObjectProcessing/OutMatrix" )
		outMatrix['parameters']['name'].setValue( "out_foo" )

		inInt = GafferOSL.OSLShader( "InInt" )
		s.addChild( inInt )
		inInt.loadShader( "ObjectProcessing/InInt" )

		oslCode = GafferOSL.OSLCode( "OSLCode" )
		oslCode["code"].setValue( 'outMat = matrix(inIndex, inIndex, inIndex, inIndex, inIndex, inIndex, inIndex, inIndex, inIndex, inIndex, inIndex, inIndex, inIndex, inIndex, inIndex, inIndex);' )
		s.addChild( oslCode )
		inIntPlug = Gaffer.IntPlug( "inIndex", defaultValue = 0, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, )
		oslCode["parameters"].addChild( inIntPlug )
		inIntPlug.setInput( inInt['out']['value'] )
		oslCode["out"].addChild( Gaffer.M44fPlug( "outMat", direction = Gaffer.Plug.Direction.Out, defaultValue = imath.M44f( 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1 ),
			flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ) )

		outMatrix["parameters"]["value"].setInput( oslCode['out']['outMat'] )

		outObject = GafferOSL.OSLShader( "OutObject" )
		s.addChild( outObject )
		outObject.loadShader( "ObjectProcessing/OutObject" )
		outObject["parameters"]["in0"].setInput( outMatrix["out"]["primitiveVariable"] )

		o["shader"].setInput( outObject["out"]["out"] )

		matrixPrimvar = o['out'].object( "/plane" )["out_foo"]
		for index, m in enumerate( matrixPrimvar.data ) :
			self.assertEqual( m, imath.M44f( index ) )

		# check we can read the matrix44 primvar by reading and writing as out_foo2
		inMatrix = GafferOSL.OSLShader( "InMatrix" )
		s.addChild( inMatrix  )
		inMatrix.loadShader( "ObjectProcessing/InMatrix" )
		inMatrix["parameters"]["name"].setValue( 'out_foo' )

		outMatrix2 = GafferOSL.OSLShader( "OutMatrix" )
		s.addChild( outMatrix2 )
		outMatrix2.loadShader( "ObjectProcessing/OutMatrix" )
		outMatrix2["parameters"]["name"].setValue( 'out_foo2' )
		outMatrix2["parameters"]["value"].setInput( inMatrix["out"]["value"] )

		outObject2 = GafferOSL.OSLShader( "OutObject" )
		s.addChild( outObject2 )
		outObject2.loadShader( "ObjectProcessing/OutObject" )
		outObject2["parameters"]["in0"].setInput( outMatrix2["out"]["primitiveVariable"] )

		o2 = GafferOSL.OSLObject()
		s.addChild(o2)
		o2['in'].setInput( o["out"] )
		o2["shader"].setInput( outObject2["out"]["out"] )
		o2["filter"].setInput( f["out"] )

		matrixPrimvar = o2['out'].object( "/plane" )["out_foo2"]
		for index, m in enumerate( matrixPrimvar.data ) :
			self.assertEqual( m, imath.M44f( index ) )

	def testCanWriteStringPrimvar( self ) :

		# The plane will contain 4 vertices &
		# OSL defaults to operating on vertices so we should get 4
		# strings in the output primvar.
		plane = GafferScene.Plane( "Plane" )
		oslObject = GafferOSL.OSLObject( "OSLObject" )
		pathFilter = GafferScene.PathFilter( "PathFilter" )
		pathFilter["paths"].setValue( IECore.StringVectorData( ['/plane'] ) )

		outString = GafferOSL.OSLShader( "OutString" )
		outString.loadShader( "ObjectProcessing/OutString" )

		outObject = GafferOSL.OSLShader( "OutObject" )
		outObject.loadShader( "ObjectProcessing/OutObject" )

		oslCode = GafferOSL.OSLCode( "OSLCode" )

		oslCode["out"].addChild( Gaffer.StringPlug( "foo", direction = Gaffer.Plug.Direction.Out, defaultValue = '' ) )

		# shading:index returns the vertex index 0,1,2,3 and we attempt to write out if the index
		# is odd or even in a string called 'foo'.
		oslCode["code"].setValue( """
		int shadingIndex;
		if (getattribute("shading:index", shadingIndex))
		{
			if (shadingIndex % 2 == 0)
			{
				foo = "even";
			}
			else
			{
				foo = "odd";
			}
		}
		else
		{
			foo = "eh";
		}""" )

		oslObject["in"].setInput( plane["out"] )
		oslObject["filter"].setInput( pathFilter["out"] )
		oslObject["shader"].setInput( outObject["out"]["out"] )
		outString["parameters"]["value"].setInput( oslCode["out"]["foo"] )
		outObject["parameters"]["in0"].setInput( outString["out"]["primitiveVariable"] )

		outputPlane = oslObject['out'].object( "/plane" )

		self.assertTrue( outputPlane )
		self.assertTrue( "name" in outputPlane.keys() )

		pv = outputPlane["name"]
		self.assertEqual( pv.data, IECore.StringVectorData( ["even", "odd", "even", "odd"] ) )

	def testShaderSerialisation( self ) :

		s = Gaffer.ScriptNode()
		s['shader'] = GafferOSL.OSLShader()
		s['shader'].loadShader( "ObjectProcessing/OutObject" )
		s['object'] = GafferOSL.OSLObject()
		s['object']['shader'].setInput( s['shader']['out']['out'] )
		self.assertEqual( s['object']['primitiveVariables']['legacyClosure']["value"].getInput(), s['shader']['out']['out'] )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( s2['object']['primitiveVariables']['legacyClosure']["value"].getInput(), s2['shader']['out']['out'] )

		# same network as above, but reverse the order of node construction

		s3 = Gaffer.ScriptNode()
		s3['object'] = GafferOSL.OSLObject()
		s3['shader'] = GafferOSL.OSLShader()
		s3['shader'].loadShader( "ObjectProcessing/OutObject" )
		s3['object']['shader'].setInput( s3['shader']['out']['out'] )
		self.assertEqual( s3['object']['primitiveVariables']['legacyClosure']["value"].getInput(), s3['shader']['out']['out'] )

		s4 = Gaffer.ScriptNode()
		s4.execute( s3.serialise() )

		self.assertEqual( s4['object']['primitiveVariables']['legacyClosure']["value"].getInput(), s4['shader']['out']['out'] )

	def testWriteUV( self ) :

		plane = GafferScene.Plane()

		inPoint = GafferOSL.OSLShader()
		inPoint.loadShader( "ObjectProcessing/InPoint" )

		outUV = GafferOSL.OSLShader()
		outUV.loadShader( "ObjectProcessing/OutUV" )
		outUV["parameters"]["value"].setInput( inPoint["out"]["value"] )

		outObject = GafferOSL.OSLShader()
		outObject.loadShader( "ObjectProcessing/OutObject" )
		outObject["parameters"]["in0"].setInput( outUV["out"]["primitiveVariable"] )

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		oslObject = GafferOSL.OSLObject()
		oslObject["in"].setInput( plane["out"] )
		oslObject["filter"].setInput( filter["out"] )
		oslObject["shader"].setInput( outObject["out"]["out"] )

		mesh = oslObject["out"].object( "/plane" )
		self.assertEqual( mesh["uv"].interpolation, IECoreScene.PrimitiveVariable.Interpolation.Vertex )
		self.assertEqual(
			mesh["uv"].data,
			IECore.V2fVectorData(
				[ imath.V2f( x[0], x[1] ) for x in mesh["P"].data ],
				IECore.GeometricData.Interpretation.UV
			)
		)
		self.assertEqual( mesh["uv"].indices, None )

	def testColor4fInput( self ) :

		# PointsPrimitive with Color4fVectorData primitive variable

		points = IECoreScene.PointsPrimitive( IECore.V3fVectorData( [ imath.V3f( 0 ), imath.V3f( 1 ) ] ) )
		points["myColor4"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.Color4fVectorData( [ imath.Color4f( 1, 2, 3, 4 ), imath.Color4f( 5, 6, 7, 8 ) ] )
		)

		objectToScene = GafferScene.ObjectToScene()
		objectToScene["object"].setValue( points )

		self.assertSceneValid( objectToScene["out"] )

		# Shading network to read primitive variable in and copy to Color3fVectorData Cs

		inColor = GafferOSL.OSLShader()
		inColor.loadShader( "ObjectProcessing/InColor" )
		inColor["parameters"]["name"].setValue( "myColor4" )

		outColor = GafferOSL.OSLShader()
		outColor.loadShader( "ObjectProcessing/OutColor" )
		outColor["parameters"]["value"].setInput( inColor["out"]["value"] )

		outObject = GafferOSL.OSLShader()
		outObject.loadShader( "ObjectProcessing/OutObject" )
		outObject["parameters"]["in0"].setInput( outColor["out"]["primitiveVariable"] )

		# OSLObject node to apply network

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/object" ] ) )

		oslObject = GafferOSL.OSLObject()
		oslObject["in"].setInput( objectToScene["out"] )
		oslObject["filter"].setInput( filter["out"] )
		oslObject["shader"].setInput( outObject["out"]["out"] )

		# Assertions

		outPoints = oslObject["out"].object( "/object" )

		self.assertIn( "Cs", outPoints )
		self.assertEqual( outPoints["Cs"].interpolation, IECoreScene.PrimitiveVariable.Interpolation.Vertex )
		self.assertEqual(
			outPoints["Cs"].data,
			IECore.Color3fVectorData( [ imath.Color3f( 1, 2, 3 ), imath.Color3f( 5, 6, 7 ) ] )
		)

	def testContextCompatibility( self ) :

		script = Gaffer.ScriptNode()

		# Network to assign the existence of "scene:path" as a primvar called "id"

		script["outInt"] = GafferOSL.OSLShader()
		script["outInt"].loadShader( "ObjectProcessing/OutInt" )

		script["outObject"] = GafferOSL.OSLShader()
		script["outObject"].loadShader( "ObjectProcessing/OutObject" )
		script["outObject"]["parameters"]["in0"].setInput( script["outInt"]["out"]["primitiveVariable"] )

		script["expression"] = Gaffer.Expression()
		script["expression"].setExpression( 'parent["outInt"]["parameters"]["value"] = 1 if context.get( "scene:path", None ) else 0' )

		# OSLObject node to apply network

		script["plane"] = GafferScene.Plane()

		script["filter"] = GafferScene.PathFilter()
		script["filter"]["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		script["oslObject"] = GafferOSL.OSLObject()
		script["oslObject"]["in"].setInput( script["plane"]["out"] )
		script["oslObject"]["filter"].setInput( script["filter"]["out"] )
		script["oslObject"]["shader"].setInput( script["outObject"]["out"]["out"] )

		# Check that "scene:path" isn't exposed to the shader

		self.assertEqual( script["oslObject"]["out"].object( "/plane")["id"].data[0], 0 )

	def testAllTypes( self ) :

		s = Gaffer.ScriptNode()

		c = GafferScene.Cube()
		s.addChild( c )

		o = GafferOSL.OSLObject()
		s.addChild( o )

		f = GafferScene.PathFilter( "PathFilter" )
		s.addChild( f )
		f["paths"].setValue( IECore.StringVectorData( [ '/cube' ] ) )
		o["filter"].setInput( f["out"] )

		o['in'].setInput( c["out"] )
		o["primitiveVariables"].addChild( Gaffer.NameValuePlug( "testString", "blah" ) )
		o["primitiveVariables"].addChild( Gaffer.NameValuePlug( "testInt", 42 ) )
		o["primitiveVariables"].addChild( Gaffer.NameValuePlug( "testFloat", 42.42 ) )
		o["primitiveVariables"].addChild( Gaffer.NameValuePlug(
				"testVector", IECore.V3fData( imath.V3f(1,2,3), IECore.GeometricData.Interpretation.Vector )
		) )
		o["primitiveVariables"].addChild( Gaffer.NameValuePlug(
				"testPoint", IECore.V3fData( imath.V3f(4,5,6), IECore.GeometricData.Interpretation.Point )
		) )
		o["primitiveVariables"].addChild( Gaffer.NameValuePlug(
				"testNormal", IECore.V3fData( imath.V3f(7,8,9), IECore.GeometricData.Interpretation.Normal )
		) )
		o["primitiveVariables"].addChild( Gaffer.NameValuePlug(
				"testUV", IECore.V3fData( imath.V3f(10,11,-42), IECore.GeometricData.Interpretation.UV )
		) )
		o["primitiveVariables"].addChild( Gaffer.NameValuePlug( "testColor", imath.Color3f(12,13,14) ) )
		o["primitiveVariables"].addChild( Gaffer.NameValuePlug( "testMatrix", imath.M44f(15) ) )

		cubeObject = s['OSLObject']['out'].object( "/cube" )

		self.assertEqual( cubeObject["testString"].data, IECore.StringVectorData( ["blah"]*8 ) )
		self.assertEqual( cubeObject["testInt"].data, IECore.IntVectorData( [42]*8 ) )
		self.assertEqual( cubeObject["testFloat"].data, IECore.FloatVectorData( [42.42]*8 ) )
		self.assertEqual( cubeObject["testVector"].data, IECore.V3fVectorData( [ imath.V3f(1,2,3)] * 8, IECore.GeometricData.Interpretation.Vector ) )
		self.assertEqual( cubeObject["testPoint"].data, IECore.V3fVectorData( [ imath.V3f(4,5,6)] * 8, IECore.GeometricData.Interpretation.Point ) )
		self.assertEqual( cubeObject["testNormal"].data, IECore.V3fVectorData( [ imath.V3f(7,8,9)] * 8, IECore.GeometricData.Interpretation.Normal ) )
		self.assertEqual( cubeObject["testUV"].data, IECore.V2fVectorData( [ imath.V2f(10,11)] * 8, IECore.GeometricData.Interpretation.UV ) )
		self.assertEqual( cubeObject["testColor"].data, IECore.Color3fVectorData( [ imath.Color3f(12,13,14)] * 8 ) )
		self.assertEqual( cubeObject["testMatrix"].data, IECore.M44fVectorData( [ imath.M44f(15)] * 8 ) )

	def testClosure( self ) :

		s = Gaffer.ScriptNode()

		c = GafferScene.Cube()
		s.addChild( c )

		o = GafferOSL.OSLObject()
		s.addChild( o )

		f = GafferScene.PathFilter( "PathFilter" )
		s.addChild( f )
		f["paths"].setValue( IECore.StringVectorData( [ '/cube' ] ) )
		o["filter"].setInput( f["out"] )

		o['in'].setInput( c["out"] )
		o["primitiveVariables"].addChild( Gaffer.NameValuePlug( "testClosure", GafferOSL.ClosurePlug() ) )

		code = GafferOSL.OSLCode( "OSLCode" )
		code["out"].addChild( GafferOSL.ClosurePlug( "output1", direction = Gaffer.Plug.Direction.Out ) )
		code["code"].setValue( 'output1 = debug( "testString", "type", "string", "stringValue", "foo" )\n + debug( "testPoint", "type", "point", "value", vector( 1, 10, 100 ) );' )

		o["primitiveVariables"][0]["value"].setInput( code["out"]["output1"] )

		cubeObject = s['OSLObject']['out'].object( "/cube" )

		self.assertEqual( cubeObject["testString"].data, IECore.StringVectorData( ["foo"]*8 ) )
		self.assertEqual( cubeObject["testPoint"].data, IECore.V3fVectorData( [ imath.V3f(1,10,100)] * 8, IECore.GeometricData.Interpretation.Point ) )

	def testUndo( self ) :

		s = Gaffer.ScriptNode()

		o = GafferOSL.OSLObject()
		s.addChild( o )

		self.assertFalse( s.undoAvailable() )

		self.assertEqual( len( o["__oslCode"]["parameters"].children() ), 0 )

		with Gaffer.UndoScope( s ) :
			o["primitiveVariables"].addChild( Gaffer.NameValuePlug( "testInt", 42 ) )
			o["primitiveVariables"].addChild( Gaffer.NameValuePlug( "testFloat", 42.42 ) )

		self.assertTrue( s.undoAvailable() )
		self.assertEqual( len( o["__oslCode"]["parameters"].children() ), 4 )

		with Gaffer.UndoScope( s ) :
			del o["primitiveVariables"][0]
			del o["primitiveVariables"][0]

		self.assertEqual( len( o["__oslCode"]["parameters"].children() ), 0 )

		# Test that the internal connections are recreated correctly when undoing adding and removing primVars
		s.undo()

		self.assertEqual( len( o["__oslCode"]["parameters"].children() ), 4 )

		s.undo()

		self.assertEqual( len( o["__oslCode"]["parameters"].children() ), 0 )

	def testAttributes( self ):

		p = GafferScene.Plane()

		a = GafferScene.CustomAttributes()
		a["attributes"].addChild( Gaffer.NameValuePlug( "a", 42.5 ) )
		a["attributes"].addChild( Gaffer.NameValuePlug( "b", 12 ) )
		a["attributes"].addChild( Gaffer.NameValuePlug( "c", True ) )
		a["attributes"].addChild( Gaffer.NameValuePlug( "d", "blah" ) )
		a["attributes"].addChild( Gaffer.NameValuePlug( "e", imath.V3f( 0.1, 0.2, 0.3 ) ) )
		a["attributes"].addChild( Gaffer.NameValuePlug( "f", imath.V2f( 0.4, 0.5 ) ) )
		a["attributes"].addChild( Gaffer.NameValuePlug( "g", imath.Color3f( 0.6, 0.7, 0.8 ) ) )
		a["attributes"].addChild( Gaffer.NameValuePlug( "h", imath.M44f( 3 ) ) )
		# There's no Color4f type in OSL, so We can't currently get the 4th component, but we can
		# get the first 3
		a["attributes"].addChild( Gaffer.NameValuePlug( "i", imath.Color4f( 0.6, 0.7, 0.8, 0.9 ) ) )

		a["in"].setInput( p["out"] )

		o = GafferOSL.OSLObject()
		o["in"].setInput( p["out"] )
		o["in"].setInput( a["out"] )

		# shading network to output attributes as formatted string.

		inPoint = GafferOSL.OSLShader()
		inPoint.loadShader( "ObjectProcessing/InPoint" )

		code = GafferOSL.OSLCode()
		code["out"].addChild( Gaffer.StringPlug( "testString", direction = Gaffer.Plug.Direction.Out ) )

		o["primitiveVariables"].addChild( Gaffer.NameValuePlug( "testString", "" ) )
		o["primitiveVariables"][0]["value"].setInput( code["out"]["testString"] )

		f = GafferScene.PathFilter()
		f["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		a["filter"].setInput( f["out"] )
		o["filter"].setInput( f["out"] )

		code["code"].setValue( inspect.cleandoc(
			"""
			float a = -1;
			getattribute( "a", a );
			float ax = -1;
			getattribute( "ax", ax );
			int b = -1;
			getattribute( "b", b );
			int c = -1;
			getattribute( "c", c );
			string d = "";
			getattribute( "d", d );
			vector e = -1;
			getattribute( "e", e );
			vector f = -1;
			getattribute( "f", f );
			color g = -1;
			getattribute( "g", g );
			matrix h = -1;
			getattribute( "h", h );
			color i = -1;
			getattribute( "i", i );
			testString = format( "TEST STRING : <%.2f><%.2f><%i><%i><%s><%.2f><%.2f><%.2f><%.2f %.2f %.2f %.2f><%.2f>", a, ax, b, c, d, e, f, g, h[0][0], h[0][1], h[1][0], h[1][1], i );
			"""
		) )

		self.assertEqual(
			o["out"].object( "/plane" )["testString"].data[0],
			"TEST STRING : <-1.00><-1.00><-1><-1><><-1.00 -1.00 -1.00><-1.00 -1.00 -1.00><-1.00 -1.00 -1.00><-1.00 0.00 0.00 -1.00><-1.00 -1.00 -1.00>"
		)
		o["useAttributes"].setValue( True )
		self.assertEqual(
			o["out"].object( "/plane" )["testString"].data[0],
			"TEST STRING : <42.50><-1.00><12><1><blah><0.10 0.20 0.30><0.40 0.50 0.00><0.60 0.70 0.80><3.00 3.00 3.00 3.00><0.60 0.70 0.80>"
		)

		# Try some bogus attributes
		code["code"].setValue( inspect.cleandoc(
			"""
			string badAttribute = "NOT FOUND";
			getattribute( "badAttribute", badAttribute );
			testString = badAttribute;
			"""
		) )

		a["attributes"].addChild( Gaffer.NameValuePlug( "badAttribute", imath.Box2f( imath.V2f( -0.5 ), imath.V2f( 0.5 ) ) ) )

		# Check that bad attribute isn't found
		self.assertEqual( o["out"].object( "/plane" )["testString"].data[0], "NOT FOUND" )

		while a["attributes"].children():
			del a["attributes"][0]
		a["attributes"].addChild( Gaffer.NameValuePlug( "badAttribute", IECore.FloatVectorData([0,1,2]) ) )

		self.assertEqual( o["out"].object( "/plane" )["testString"].data[0], "NOT FOUND" )

		# Try something that isn't even data
		code["code"].setValue( inspect.cleandoc(
			"""
			string badAttribute = "NOT FOUND";
			getattribute( "osl:surface", badAttribute );
			testString = badAttribute;
			"""
		) )
		c = GafferOSL.OSLShader()
		c.loadShader( "Surface/Constant" )
		s = GafferScene.ShaderAssignment()
		s["shader"].setInput( c["out"] )
		s["filter"].setInput( f["out"] )
		s["in"].setInput( p["out"] )
		o["in"].setInput( s["out"] )

		self.assertEqual( o["out"].object( "/plane" )["testString"].data[0], "NOT FOUND" )


	def testAffects( self ) :

		s = GafferScene.Sphere()

		a = GafferScene.CustomAttributes()
		a["attributes"].addChild( Gaffer.NameValuePlug( "a", 0 ) )
		a["in"].setInput( s["out"] )

		o = GafferOSL.OSLObject()
		o["in"].setInput( a["out"] )

		cs = GafferTest.CapturingSlot( o.plugDirtiedSignal() )

		s["transform"]["translate"]["x"].setValue( 1 )
		def checkAffected( expected ):
			self.assertEqual( [ i[0].getName() for i in cs if i[0].parent() == o["out"] ], expected )
			del cs[:]
		checkAffected( ["transform", "bound" ] )

		o["useTransform"].setValue( True )

		checkAffected( ["object", "bound" ] )

		s["transform"]["translate"]["x"].setValue( 2 )

		checkAffected( ["transform", "object", "bound" ] )

		a["attributes"][0]["value"].setValue( 1 )
		checkAffected( ["attributes" ] )

		o["useAttributes"].setValue( True )

		checkAffected( ["object", "bound" ] )

		a["attributes"][0]["value"].setValue( 2 )

		checkAffected( ["attributes", "object", "bound" ] )

	def testBoundsUpdate( self ) :

		plane = GafferScene.Plane()

		planeFilter = GafferScene.PathFilter()
		planeFilter["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		inPoint = GafferOSL.OSLShader()
		inPoint.loadShader( "ObjectProcessing/InPoint" )

		multiplyVector = GafferOSL.OSLShader()
		multiplyVector.loadShader( "Maths/MultiplyVector" )
		multiplyVector["parameters"]["a"].setInput( inPoint["out"]["value"] )
		multiplyVector["parameters"]["b"].setValue( imath.V3f( 2 ) )

		oslObject = GafferOSL.OSLObject()
		oslObject["in"].setInput( plane["out"] )
		oslObject["filter"].setInput( planeFilter["out"] )

		oslObject["primitiveVariables"].addChild(
			Gaffer.NameValuePlug(
				"aPoint", IECore.V3fData( imath.V3f( 0 ), IECore.GeometricData.Interpretation.Point )
			)
		)
		oslObject["primitiveVariables"][0]["value"].setInput( multiplyVector["out"]["out"] )

		# Because we're not manipulating "P", the bounding boxes should remain unchanged.

		self.assertEqual(
			oslObject["out"].object( "/plane" )["aPoint"].data,
			oslObject["in"].object( "/plane" )["P"].data * imath.V3f( 2 )
		)

		self.assertScenesEqual( oslObject["out"], oslObject["in"], checks = { "bound" } )
		self.assertSceneHashesEqual( oslObject["out"], oslObject["in"], checks = { "bound" } )

		# But as soon as we manipulate "P", bounds updates should be triggered.

		oslObject["primitiveVariables"][0]["name"].setValue( "P" )

		self.assertEqual(
			oslObject["out"].object( "/plane" )["P"].data,
			oslObject["in"].object( "/plane" )["P"].data * imath.V3f( 2 )
		)

		self.assertEqual( oslObject["out"].bound( "/plane" ), oslObject["out"].object( "/plane" ).bound() )
		self.assertSceneValid( oslObject["out"] )

		# And we should be able to turn the bounds updates off if we don't want to
		# pay for them.

		oslObject["adjustBounds"].setValue( False )

		self.assertEqual(
			oslObject["out"].object( "/plane" )["P"].data,
			oslObject["in"].object( "/plane" )["P"].data * imath.V3f( 2 )
		)

		self.assertScenesEqual( oslObject["out"], oslObject["in"], checks = { "bound" } )
		self.assertSceneHashesEqual( oslObject["out"], oslObject["in"], checks = { "bound" } )

	def testLoadFrom0_55( self ) :

		script = Gaffer.ScriptNode()
		script["fileName"].setValue( os.path.join( os.path.dirname( __file__ ), "scripts", "oslObjectVersion-0.55.0.0.gfr" ) )
		script.load()

		self.assertNotIn( "__contextCompatibility", script["OSLObject"] )

if __name__ == "__main__":
	unittest.main()

