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

import Gaffer
import GafferTest
import GafferScene
import GafferOSL
import GafferOSLTest

class OSLObjectTest( GafferOSLTest.OSLTestCase ) :

	def test( self ) :

		p = GafferScene.Plane()
		p["dimensions"].setValue( IECore.V2f( 1, 2 ) )
		p["divisions"].setValue( IECore.V2i( 10 ) )

		self.assertSceneValid( p["out"] )

		o = GafferOSL.OSLObject()
		o["in"].setInput( p["out"] )

		self.assertScenesEqual( p["out"], o["out"] )

		# shading network to swap x and y

		inPoint = GafferOSL.OSLShader()
		inPoint.loadShader( "ObjectProcessing/InPoint" )

		splitPoint = GafferOSL.OSLShader()
		splitPoint.loadShader( "Utility/SplitPoint" )
		splitPoint["parameters"]["p"].setInput( inPoint["out"]["value"] )

		buildPoint = GafferOSL.OSLShader()
		buildPoint.loadShader( "Utility/BuildPoint" )
		buildPoint["parameters"]["x"].setInput( splitPoint["out"]["y"] )
		buildPoint["parameters"]["y"].setInput( splitPoint["out"]["x"] )

		outPoint = GafferOSL.OSLShader()
		outPoint.loadShader( "ObjectProcessing/OutPoint" )
		outPoint["parameters"]["value"].setInput( buildPoint["out"]["p"] )

		primVarShader = GafferOSL.OSLShader()
		primVarShader.loadShader( "ObjectProcessing/OutObject" )
		primVarShader["parameters"]["in0"].setInput( outPoint["out"]["primitiveVariable"] )

		o["shader"].setInput( primVarShader["out"] )

		self.assertScenesEqual( p["out"], o["out"] )

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		o["filter"].setInput( filter["out"] )

		self.assertSceneValid( o["out"] )

		boundIn = p["out"].bound( "/plane" )
		boundOut = o["out"].bound( "/plane" )

		self.assertEqual( boundIn.min.x, boundOut.min.y )
		self.assertEqual( boundIn.max.x, boundOut.max.y )
		self.assertEqual( boundIn.min.y, boundOut.min.x )
		self.assertEqual( boundIn.max.y, boundOut.max.x )

	def testTransform( self ) :

		p = GafferScene.Plane()
		p["transform"]["translate"].setValue( IECore.V3f( 2, 0, 0 ) )

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

		o["shader"].setInput( primVarShader["out"] )

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		o["filter"].setInput( filter["out"] )

		self.assertEqual( o["out"].object( "/plane" )["transformed"].data, IECore.Color3fVectorData( [ IECore.Color3f( 1.5, -0.5, 0 ), IECore.Color3f( 2.5, -0.5, 0 ), IECore.Color3f( 1.5, 0.5, 0 ), IECore.Color3f( 2.5, 0.5, 0 ) ] ) )
		self.assertEqual( o["out"].object( "/plane" )["transformedBack"].data, IECore.Color3fVectorData( [ IECore.Color3f( -0.5, -0.5, 0 ), IECore.Color3f( 0.5, -0.5, 0 ), IECore.Color3f( -0.5, 0.5, 0 ), IECore.Color3f( 0.5, 0.5, 0 ) ] ) )

	def testOnlyAcceptsSurfaceShaders( self ) :

		object = GafferOSL.OSLObject()
		shader = GafferOSL.OSLShader()

		shader.loadShader( "ObjectProcessing/OutPoint" )
		self.assertFalse( object["shader"].acceptsInput( shader["out"] ) )

		shader.loadShader( "ObjectProcessing/OutObject" )
		self.assertTrue( object["shader"].acceptsInput( shader["out"] ) )

	def testAcceptsNone( self ) :

		object = GafferOSL.OSLObject()
		self.assertTrue( object["shader"].acceptsInput( None ) )

	def testAcceptsShaderSwitch( self ) :

		script = Gaffer.ScriptNode()
		script["object"] = GafferOSL.OSLObject()
		script["switch"] = GafferScene.ShaderSwitch()

		# We're testing a backwards compatibility special case that is
		# only enabled when loading a script, hence the use of `execute()`.
		script.execute( """script["object"]["shader"].setInput( script["switch"]["out"] )""" )
		self.assertTrue( script["object"]["shader"].getInput().isSame( script["switch"]["out"] ) )

	def testAcceptsDot( self ) :

		script = Gaffer.ScriptNode()
		script["object"] = GafferOSL.OSLObject()
		script["switch"] = GafferScene.ShaderSwitch()
		script["dot"] = Gaffer.Dot()
		script["dot"].setup( script["switch"]["out"] )

		# We're testing a backwards compatibility special case that is
		# only enabled when loading a script, hence the use of `execute()`.
		script.execute( """script["object"]["shader"].setInput( script["dot"]["out"] )""" )
		self.assertTrue( script["object"]["shader"].getInput().isSame( script["dot"]["out"] ) )

	def testPrimitiveVariableWithZeroValue( self ) :

		outPoint = GafferOSL.OSLShader()
		outPoint.loadShader( "ObjectProcessing/OutPoint" )
		outPoint["parameters"]["name"].setValue( "velocity" )
		outPoint["parameters"]["value"].setValue( IECore.V3f( 0 ) )

		primVarShader = GafferOSL.OSLShader()
		primVarShader.loadShader( "ObjectProcessing/OutObject" )
		primVarShader["parameters"]["in0"].setInput( outPoint["out"]["primitiveVariable"] )

		p = GafferScene.Plane()
		p["dimensions"].setValue( IECore.V2f( 1, 2 ) )
		p["divisions"].setValue( IECore.V2i( 10 ) )

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		o = GafferOSL.OSLObject()
		o["in"].setInput( p["out"] )
		o["shader"].setInput( primVarShader["out"] )
		o["filter"].setInput( filter["out"] )

		for v in o["out"].object( "/plane" )["velocity"].data :
			self.assertEqual( v, IECore.V3f( 0 ) )

	def testShaderAffectsBoundAndObject( self ) :

		o = GafferOSL.OSLObject()
		s = GafferOSL.OSLShader()
		s.loadShader( "ObjectProcessing/OutObject" )

		cs = GafferTest.CapturingSlot( o.plugDirtiedSignal() )

		o["shader"].setInput( s["out"] )

		self.assertTrue( o["out"]["object"] in set( x[0] for x in cs ) )
		self.assertTrue( o["out"]["bound"] in set( x[0] for x in cs ) )

	def testReferencePromotedPlug( self ) :

		s = Gaffer.ScriptNode()

		s["b"] = Gaffer.Box()
		s["b"]["o"] = GafferOSL.OSLObject()
		p = Gaffer.PlugAlgo.promote( s["b"]["o"]["shader"] )
		p.setName( "p" )

		s["b"].exportForReference( self.temporaryDirectory() + "/test.grf" )

		s["r"] = Gaffer.Reference()
		s["r"].load( self.temporaryDirectory() + "/test.grf" )

		s["s"] = GafferOSL.OSLShader()
		s["s"].loadShader( "ObjectProcessing/OutObject" )

		s["r"]["p"].setInput( s["s"]["out"] )

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
		self.assertEqual(c["out"].object("/cube")['P'].interpolation, IECore.PrimitiveVariable.Interpolation.Vertex )

		o['in'].setInput( c["out"] )
		o['interpolation'].setValue( IECore.PrimitiveVariable.Interpolation.Uniform )

		inPoint = GafferOSL.OSLShader( "InPoint" )
		s.addChild( inPoint )
		inPoint.loadShader( "ObjectProcessing/InPoint" )

		vectorAdd = GafferOSL.OSLShader( "VectorAdd" )
		s.addChild( vectorAdd )
		vectorAdd.loadShader( "Maths/VectorAdd" )
		vectorAdd["parameters"]["b"].setValue( IECore.V3f( 1, 2, 3 ) )

		vectorAdd["parameters"]["a"].setInput( inPoint["out"]["value"] )

		outPoint = GafferOSL.OSLShader( "OutPoint" )
		s.addChild( outPoint )
		outPoint.loadShader( "ObjectProcessing/OutPoint" )
		outPoint['parameters']['name'].setValue("P_copy")

		outPoint["parameters"]["value"].setInput( vectorAdd["out"]["out"] )

		outObject = GafferOSL.OSLShader( "OutObject" )
		s.addChild( outObject )
		outObject.loadShader( "ObjectProcessing/OutObject" )
		outObject["parameters"]["in0"].setInput( outPoint["out"]["primitiveVariable"] )

		o["shader"].setInput( outObject["out"] )

		cubeObject = s['OSLObject']['out'].object( "/cube" )

		self.assertTrue( "P_copy" in cubeObject.keys() )
		self.assertEqual( cubeObject["P_copy"].interpolation, IECore.PrimitiveVariable.Interpolation.Uniform)

		self.assertEqual( cubeObject["P_copy"].data[0], IECore.V3f(  0.0,  0.0, -0.5 ) + IECore.V3f( 1, 2, 3 ))
		self.assertEqual( cubeObject["P_copy"].data[1], IECore.V3f(  0.5,  0.0,  0.0 ) + IECore.V3f( 1, 2, 3 ))
		self.assertEqual( cubeObject["P_copy"].data[2], IECore.V3f(  0.0,  0.0,  0.5 ) + IECore.V3f( 1, 2, 3 ))
		self.assertEqual( cubeObject["P_copy"].data[3], IECore.V3f( -0.5,  0.0,  0.0 ) + IECore.V3f( 1, 2, 3 ))
		self.assertEqual( cubeObject["P_copy"].data[4], IECore.V3f(  0.0,  0.5,  0.0 ) + IECore.V3f( 1, 2, 3 ))
		self.assertEqual( cubeObject["P_copy"].data[5], IECore.V3f(  0.0, -0.5,  0.0 ) + IECore.V3f( 1, 2, 3 ))

	def testCanShadeFaceVaryingInterpolatedPrimitiveVariablesAsVertex( self ) :

		s = Gaffer.ScriptNode()

		p = GafferScene.Plane()
		p["divisions"].setValue( IECore.V2i( 2, 2 ) ) #  2x2 plane = 4 quads & 9 vertices
		s.addChild( p )

		o = GafferOSL.OSLObject()
		s.addChild( o )

		f = GafferScene.PathFilter( "PathFilter" )
		s.addChild( f )
		f["paths"].setValue( IECore.StringVectorData( [ '/plane' ] ) )
		o["filter"].setInput( f["out"] )

		# ensure the source primvars are face varying
		self.assertEqual(p["out"].object("/plane")['s'].interpolation, IECore.PrimitiveVariable.Interpolation.FaceVarying )
		self.assertEqual(p["out"].object("/plane")['t'].interpolation, IECore.PrimitiveVariable.Interpolation.FaceVarying )

		o['in'].setInput( p["out"] )
		o['interpolation'].setValue( IECore.PrimitiveVariable.Interpolation.Vertex )

		inS = GafferOSL.OSLShader( "InFloat" )
		s.addChild( inS )
		inS.loadShader( "ObjectProcessing/InFloat" )
		inS['parameters']['name'].setValue('s')

		inT = GafferOSL.OSLShader( "InFloat" )
		s.addChild( inT )
		inT.loadShader( "ObjectProcessing/InFloat" )
		inT['parameters']['name'].setValue('t')

		floatAdd = GafferOSL.OSLShader( "FloatAdd" )
		s.addChild( floatAdd )
		floatAdd.loadShader( "Maths/FloatAdd" )

		floatAdd["parameters"]["a"].setInput( inT["out"]["value"] )
		floatAdd["parameters"]["b"].setInput( inS["out"]["value"] )

		outFloat = GafferOSL.OSLShader( "OutFloat" )
		s.addChild( outFloat )
		outFloat.loadShader( "ObjectProcessing/OutFloat" )
		outFloat['parameters']['name'].setValue("st_add")

		outFloat["parameters"]["value"].setInput( floatAdd["out"]["out"] )

		outObject = GafferOSL.OSLShader( "OutObject" )
		s.addChild( outObject )
		outObject.loadShader( "ObjectProcessing/OutObject" )
		outObject["parameters"]["in0"].setInput( outFloat["out"]["primitiveVariable"] )

		o["shader"].setInput( outObject["out"] )

		planeObject = s['OSLObject']['out'].object( "/plane" )

		self.assertTrue( "st_add" in planeObject.keys() )
		self.assertEqual( planeObject["st_add"].interpolation, IECore.PrimitiveVariable.Interpolation.Vertex)

		# note our plane origin position (0,0,0) has a UV (0,1) because of 1.0 - t convention in cortex.
		self.assertEqual( planeObject["st_add"].data[0], 0.0 + 1.0)
		self.assertEqual( planeObject["st_add"].data[1], 0.5 + 1.0)
		self.assertEqual( planeObject["st_add"].data[2], 1.0 + 1.0)
		self.assertEqual( planeObject["st_add"].data[3], 0.0 + 0.5)
		self.assertEqual( planeObject["st_add"].data[4], 0.5 + 0.5)
		self.assertEqual( planeObject["st_add"].data[5], 1.0 + 0.5)
		self.assertEqual( planeObject["st_add"].data[6], 0.0 + 0.0)
		self.assertEqual( planeObject["st_add"].data[7], 0.5 + 0.0)
		self.assertEqual( planeObject["st_add"].data[8], 1.0 + 0.0)


	def testCanReadFromConstantPrimitiveVariables( self ) :

		s = Gaffer.ScriptNode()

		p = GafferScene.Plane()
		p["divisions"].setValue( IECore.V2i( 2, 2 ) ) #  2x2 plane = 4 quads & 9 vertices
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
		o['interpolation'].setValue( IECore.PrimitiveVariable.Interpolation.Vertex )

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

		o["shader"].setInput( outObject["out"] )

		planeObject = s['OSLObject']['out'].object( "/plane" )

		self.assertTrue( "out_foo" in planeObject.keys() )
		self.assertEqual( planeObject["out_foo"].interpolation, IECore.PrimitiveVariable.Interpolation.Vertex)

		self.assertEqual( planeObject["out_foo"].data[0], 1)
		self.assertEqual( planeObject["out_foo"].data[1], 1)
		self.assertEqual( planeObject["out_foo"].data[2], 1)
		self.assertEqual( planeObject["out_foo"].data[3], 1)
		self.assertEqual( planeObject["out_foo"].data[4], 1)
		self.assertEqual( planeObject["out_foo"].data[5], 1)
		self.assertEqual( planeObject["out_foo"].data[6], 1)
		self.assertEqual( planeObject["out_foo"].data[7], 1)
		self.assertEqual( planeObject["out_foo"].data[8], 1)

	def testCanReadAndWriteMatrices( self ) :

		s = Gaffer.ScriptNode()

		p = GafferScene.Plane()
		p["divisions"].setValue( IECore.V2i( 2, 2 ) )  # 2x2 plane = 4 quads & 9 vertices
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
		oslCode["out"].addChild( Gaffer.M44fPlug( "outMat", direction = Gaffer.Plug.Direction.Out, defaultValue = IECore.M44f( 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1 ),
			flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ) )

		outMatrix["parameters"]["value"].setInput( oslCode['out']['outMat'] )

		outObject = GafferOSL.OSLShader( "OutObject" )
		s.addChild( outObject )
		outObject.loadShader( "ObjectProcessing/OutObject" )
		outObject["parameters"]["in0"].setInput( outMatrix["out"]["primitiveVariable"] )

		o["shader"].setInput( outObject["out"] )

		matrixPrimvar = o['out'].object( "/plane" )["out_foo"]
		for index, m in enumerate( matrixPrimvar.data ) :
			self.assertEqual( m, IECore.M44f( index ) )

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
		o2["shader"].setInput( outObject2["out"] )
		o2["filter"].setInput( f["out"] )

		matrixPrimvar = o2['out'].object( "/plane" )["out_foo2"]
		for index, m in enumerate( matrixPrimvar.data ) :
			self.assertEqual( m, IECore.M44f( index ) )

if __name__ == "__main__":
	unittest.main()


