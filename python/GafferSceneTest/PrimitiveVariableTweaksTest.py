##########################################################################
#
#  Copyright (c) 2024, Image Engine Design Inc. All rights reserved.
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

import imath

import IECore
import IECoreScene

import Gaffer
import GafferScene
import GafferSceneTest

class PrimitiveVariableTweaksTest( GafferSceneTest.SceneTestCase ) :


	def testTypes( self ) :

		s = GafferScene.Sphere()
		create = GafferScene.PrimitiveVariableTweaks()
		create["in"].setInput( s["out"] )

		self.assertScenesEqual( s["out"], create["out"] )
		self.assertSceneHashesEqual( s["out"], create["out"] )

		testData = {
			"a" : IECore.IntData( 10 ),
			"b" : IECore.V3fData( imath.V3f( 3 )),
			"c" : IECore.V3fData( imath.V3f( 5 ), IECore.GeometricData.Interpretation.Point ),
			"d" : IECore.V3fData( imath.V3f( 7 ), IECore.GeometricData.Interpretation.Normal ),
			"e" : IECore.Color3fData( imath.Color3f( 0.7, 0.8, 0.6 ) ),
			"f" : IECore.Color4fData( imath.Color4f( 0.1, 0.2, 0.3, 0.4 ) ),
			"g" : IECore.StringData( "hello to a" ),
			"h" : IECore.FloatVectorData( [ 3, 4, 5 ] ),
			"i" : IECore.Color3fVectorData( [ imath.Color3f( 7 ) ] ),
		}

		for ( name, val ) in testData.items():
			create["tweaks"].addChild( Gaffer.TweakPlug( name, val, Gaffer.TweakPlug.Mode.Create ) )

		self.assertScenesEqual( s["out"], create["out"] )
		self.assertSceneHashesEqual( s["out"], create["out"] )

		f = GafferScene.PathFilter()
		f["paths"].setValue( IECore.StringVectorData( [ "/sphere" ] ) )
		create["filter"].setInput( f["out"] )

		with self.assertRaisesRegex( Gaffer.ProcessException, 'Cannot create primitive variable a when "interpolation" is set to "Any". Please select an interpolation.' ):
			create["out"].object( "/sphere" )

		create["interpolation"].setValue( IECoreScene.PrimitiveVariable.Interpolation.Constant )
		o = create["out"].object( "/sphere" )
		self.assertEqual( o.keys(), ['N', 'P'] + list( testData.keys() ) + ['uv'] )
		for k in testData.keys():
			self.assertEqual( o[k], IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Constant, testData[k] ) )

		create["interpolation"].setValue( IECoreScene.PrimitiveVariable.Interpolation.Vertex )
		with self.assertRaisesRegex( Gaffer.ProcessException, 'Invalid type "FloatVectorData" for non-constant primitive variable tweak "h".' ):
			create["out"].object( "/sphere" )

		create["tweaks"][-1]["enabled"].setValue( False )
		create["tweaks"][-2]["enabled"].setValue( False )

		testDataNonConst = testData.copy()
		del testDataNonConst["h"]
		del testDataNonConst["i"]

		for interp in [
			IECoreScene.PrimitiveVariable.Interpolation.Uniform,
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECoreScene.PrimitiveVariable.Interpolation.Varying,
			IECoreScene.PrimitiveVariable.Interpolation.FaceVarying
		]:
			create["interpolation"].setValue( interp )
			o = create["out"].object( "/sphere" )
			self.assertEqual( o.keys(), ['N', 'P'] + list( testDataNonConst.keys() ) + ['uv'] )
			for k in testDataNonConst.keys():
				dataType = getattr( IECore, testDataNonConst[k].typeName().replace( "Data", "VectorData" ) )
				compData = dataType( [ testDataNonConst[k].value ] * o.variableSize( interp ) )
				if hasattr( compData, "setInterpretation" ):
					compData.setInterpretation( testDataNonConst[k].getInterpretation() )
				self.assertEqual( o[k], IECoreScene.PrimitiveVariable( interp, compData ) )


		tweak = GafferScene.PrimitiveVariableTweaks()
		tweak["in"].setInput( create["out"] )
		tweak["filter"].setInput( f["out"] )

		tweak["tweaks"].addChild( Gaffer.TweakPlug( "a", IECore.Color4fData(), Gaffer.TweakPlug.Mode.Replace ) )

		with self.assertRaisesRegex( Gaffer.ProcessException, 'Cannot apply tweak to "a" : Parameter should be of type "IntData" in order to apply to an element of "IntVectorData", but got "Color4fData" instead.' ):
			tweak["out"].object( "/sphere" )

		create["interpolation"].setValue( IECoreScene.PrimitiveVariable.Interpolation.Constant )
		create["tweaks"][-1]["enabled"].setValue( True )
		create["tweaks"][-2]["enabled"].setValue( True )

		with self.assertRaisesRegex( Gaffer.ProcessException, 'Cannot apply tweak to "a" : Variable data of type "IntData" does not match parameter of type "Color4fData".' ):
			tweak["out"].object( "/sphere" )

		del tweak["tweaks"][0]
		tweakData = {
			"a" : IECore.IntData( 100 ),
			"b" : IECore.V3fData( imath.V3f( 0.5 ) ),
			"c" : IECore.V3fData( imath.V3f( 0.5 ) ),
			"d" : IECore.V3fData( imath.V3f( 0.5 ) ),
			"e" : IECore.Color3fData( imath.Color3f( 0.01, 0.02, 0.03 ) ),
			"f" : IECore.Color4fData( imath.Color4f( 0.001, 0.002, 0.003, 0.004 ) ),
			"g" : IECore.StringData( "to a world" ),
			"h" : IECore.FloatVectorData( [ 13, 14, 15 ] ),
			"i" : IECore.Color3fVectorData( [ imath.Color3f( 3 ) ] ),
		}

		for ( name, val ) in tweakData.items():
			tweak["tweaks"].addChild( Gaffer.TweakPlug( name, val, Gaffer.TweakPlug.Mode.Replace ) )

		o = tweak["out"].object( "/sphere" )
		self.assertEqual( o.keys(), ['N', 'P'] + list( testData.keys() ) + ['uv'] )
		for k in tweakData.keys():
			if not k in [ "c", "d" ]:
				self.assertEqual( o[k], IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Constant, tweakData[k] ) )
			else:
				# When replacing the value of a primvar, we keep the interpolation of the original
				self.assertEqual( o[k], IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Constant, IECore.V3fData( imath.V3f( 0.5 ), testData[k].getInterpretation() ) ) )

		for i in tweak["tweaks"]:
			i["mode"].setValue( Gaffer.TweakPlug.Mode.Add )

		expectedAdd = {
			"a" : IECore.IntData( 110 ),
			"b" : IECore.V3fData( imath.V3f( 3.5 )),
			"c" : IECore.V3fData( imath.V3f( 5.5 ), IECore.GeometricData.Interpretation.Point ),
			"d" : IECore.V3fData( imath.V3f( 7.5 ), IECore.GeometricData.Interpretation.Normal ),
			"e" : IECore.Color3fData( imath.Color3f( 0.71, 0.82, 0.63 ) ),
			"f" : IECore.Color4fData( imath.Color4f( 0.101, 0.202, 0.303, 0.404 ) ),
			"g" : IECore.StringData( "hello to a world" ),
			"h" : IECore.FloatVectorData( [ 3, 4, 5, 13, 14, 15 ] ),
			"i" : IECore.Color3fVectorData( [ imath.Color3f( 7 ), imath.Color3f( 3 ) ] ),
		}

		with self.assertRaisesRegex( Gaffer.ProcessException, 'Cannot apply tweak with mode Add to "g" : Data type StringData not supported.' ):
			tweak["out"].object( "/sphere" )

		tweak["tweaks"][-3]["mode"].setValue( Gaffer.TweakPlug.Mode.ListAppend )

		with self.assertRaisesRegex( Gaffer.ProcessException, 'Cannot apply tweak with mode Add to "h" : Data type FloatVectorData not supported.' ):
			tweak["out"].object( "/sphere" )

		tweak["tweaks"][-2]["mode"].setValue( Gaffer.TweakPlug.Mode.ListAppend )

		with self.assertRaisesRegex( Gaffer.ProcessException, 'Cannot apply tweak with mode Add to "i" : Data type Color3fVectorData not supported.' ):
			tweak["out"].object( "/sphere" )

		tweak["tweaks"][-1]["mode"].setValue( Gaffer.TweakPlug.Mode.ListAppend )

		o = tweak["out"].object( "/sphere" )
		for k in tweakData.keys():
			self.assertEqual( o[k], IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Constant, expectedAdd[k] ) )

		create["interpolation"].setValue( IECoreScene.PrimitiveVariable.Interpolation.Vertex )
		create["tweaks"][-1]["enabled"].setValue( False )
		create["tweaks"][-2]["enabled"].setValue( False )
		tweak["tweaks"][-1]["enabled"].setValue( False )
		tweak["tweaks"][-2]["enabled"].setValue( False )

		for i in tweak["tweaks"]:
			i["mode"].setValue( Gaffer.TweakPlug.Mode.Replace )

		tweakDataNonConst = tweakData.copy()
		del tweakDataNonConst["h"]
		del tweakDataNonConst["i"]

		for interp in [
			IECoreScene.PrimitiveVariable.Interpolation.Uniform,
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECoreScene.PrimitiveVariable.Interpolation.Varying,
			IECoreScene.PrimitiveVariable.Interpolation.FaceVarying
		]:
			create["interpolation"].setValue( interp )
			o = tweak["out"].object( "/sphere" )
			self.assertEqual( o.keys(), ['N', 'P'] + list( tweakDataNonConst.keys() ) + ['uv'] )
			for k in tweakDataNonConst.keys():
				dataType = getattr( IECore, tweakDataNonConst[k].typeName().replace( "Data", "VectorData" ) )
				compData = dataType( [ tweakDataNonConst[k].value ] * o.variableSize( interp ) )
				if hasattr( compData, "setInterpretation" ):
					compData.setInterpretation( testDataNonConst[k].getInterpretation() )
				self.assertEqual( o[k], IECoreScene.PrimitiveVariable( interp, compData ) )

		del expectedAdd["h"]
		del expectedAdd["i"]

		for i in tweak["tweaks"]:
			i["mode"].setValue( Gaffer.TweakPlug.Mode.Add )

		# listAppend mode works on string even when those strings are per-vertex
		tweak["tweaks"][-3]["mode"].setValue( Gaffer.TweakPlug.Mode.ListAppend )

		for interp in [
			IECoreScene.PrimitiveVariable.Interpolation.Uniform,
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECoreScene.PrimitiveVariable.Interpolation.Varying,
			IECoreScene.PrimitiveVariable.Interpolation.FaceVarying
		]:
			create["interpolation"].setValue( interp )
			o = tweak["out"].object( "/sphere" )
			self.assertEqual( o.keys(), ['N', 'P'] + list( expectedAdd.keys() ) + ['uv'] )
			for k in expectedAdd.keys():
				dataType = getattr( IECore, expectedAdd[k].typeName().replace( "Data", "VectorData" ) )
				compData = dataType( [ expectedAdd[k].value ] * o.variableSize( interp ) )
				if hasattr( compData, "setInterpretation" ):
					compData.setInterpretation( expectedAdd[k].getInterpretation() )
				self.assertEqual( o[k], IECoreScene.PrimitiveVariable( interp, compData ) )

	def testInterpolations( self ) :

		m = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ), imath.V2i( 2 ) )
		m["vertexIds"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.IntVectorData( [ 10, 11, 12, 20, 21, 21, 30, 31, 33 ] )
		)
		m["badIds"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.IntVectorData( [ 0, 1 ] )
		)

		p = GafferScene.ObjectToScene()
		p["name"].setValue( "plane" )
		p["object"].setValue( m )

		f = GafferScene.PathFilter()
		f["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		createConstant = GafferScene.PrimitiveVariableTweaks()
		createConstant["in"].setInput( p["out"] )
		createConstant["filter"].setInput( f["out"] )
		createConstant["interpolation"].setValue( IECoreScene.PrimitiveVariable.Interpolation.Constant )
		createConstant["tweaks"].addChild( Gaffer.TweakPlug( "a", IECore.FloatData( 7 ), Gaffer.TweakPlug.Mode.Create ) )
		createConstant["tweaks"].addChild( Gaffer.TweakPlug( "c", IECore.IntVectorData( [ 3, 4, 8 ] ), Gaffer.TweakPlug.Mode.Create ) )


		with self.assertRaisesRegex( Gaffer.ProcessException, 'Primitive variable tweak failed - input primitive variables are not valid.' ):
			createConstant["out"].object( "/plane" )

		m["badIds"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.IntVectorData( [ 0, 1 ] ), IECore.IntVectorData( [ 0, 0, 1, 1, 0, 0, 0, 1, 0 ] )
		)
		p["object"].setValue( m )

		self.assertEqual( createConstant["out"].object( "/plane" )["a"].data, IECore.FloatData( 7 ) )

		createUniform = GafferScene.PrimitiveVariableTweaks()
		createUniform["in"].setInput( createConstant["out"] )
		createUniform["filter"].setInput( f["out"] )
		createUniform["interpolation"].setValue( IECoreScene.PrimitiveVariable.Interpolation.Uniform )
		createUniform["tweaks"].addChild( Gaffer.TweakPlug( "b", IECore.IntData( 42 ), Gaffer.TweakPlug.Mode.Create ) )

		o = createUniform["out"].object( "/plane" )
		self.assertEqual( o["b"], IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Uniform, IECore.IntVectorData( [ 42, 42, 42, 42 ] ) ) )

		createUniform["selectionMode"].setValue( GafferScene.PrimitiveVariableTweaks.SelectionMode.IdList )
		createUniform["idList"].setValue( IECore.Int64VectorData( [ 1, 2] ) )

		o = createUniform["out"].object( "/plane" )
		self.assertEqual( o["b"], IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Uniform, IECore.IntVectorData( [ 0, 42, 42, 0 ] ) ) )

		tweak = GafferScene.PrimitiveVariableTweaks()
		tweak["in"].setInput( createUniform["out"] )
		tweak["filter"].setInput( f["out"] )
		tweak["tweaks"].addChild( Gaffer.TweakPlug( "x", IECore.IntData( 7 ), Gaffer.TweakPlug.Mode.Replace ) )

		with self.assertRaisesRegex( Gaffer.ProcessException, 'Cannot apply tweak with mode Replace to "x" : This parameter does not exist.' ):
			tweak["out"].object( "/plane" )

		del tweak["tweaks"][0]
		tweak["tweaks"].addChild( Gaffer.TweakPlug( "x", IECore.FloatVectorData( [ 7 ] ), Gaffer.TweakPlug.Mode.ListAppend ) )

		# Applying a ListAppend tweak when there is no source found will try to create the variable, which will
		# fail if the interpolation isn't set
		with self.assertRaisesRegex( Gaffer.ProcessException, 'Cannot create primitive variable x when "interpolation" is set to "Any". Please select an interpolation.' ):
			tweak["out"].object( "/plane" )

		tweak["ignoreMissing"].setValue( True )

		# This error is not affected by ignoreMissing
		with self.assertRaisesRegex( Gaffer.ProcessException, 'Cannot create primitive variable x when "interpolation" is set to "Any". Please select an interpolation.' ):
			tweak["out"].object( "/plane" )
		tweak["ignoreMissing"].setValue( False )

		tweak["interpolation"].setValue( IECoreScene.PrimitiveVariable.Interpolation.Constant )
		self.assertEqual( tweak["out"].object( "/plane" )["x"], IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Constant, IECore.FloatVectorData( [ 7 ] ) ) )

		del tweak["tweaks"][0]

		tweak["interpolation"].setValue( IECoreScene.PrimitiveVariable.Interpolation.Invalid )
		tweak["tweaks"].addChild( Gaffer.TweakPlug( "c", IECore.IntVectorData( [ 7 ] ), Gaffer.TweakPlug.Mode.ListAppend ) )

		# List append working as intended
		self.assertEqual( tweak["out"].object( "/plane" )["c"], IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Constant, IECore.IntVectorData( [ 3, 4, 8, 7 ] ) ) )

		# List remove is considered successful if the target doesn't exist
		tweak["tweaks"][0]["name"].setValue( "x" )
		tweak["tweaks"][0]["mode"].setValue( Gaffer.TweakPlug.Mode.ListRemove )
		self.assertEqual( tweak["out"].object( "/plane" ), tweak["in"].object( "/plane" ) )

		tweak["tweaks"][0]["name"].setValue( "c" )
		tweak["tweaks"][0]["value"].setValue( IECore.IntVectorData( [ 4 ] ) )
		self.assertEqual( tweak["out"].object( "/plane" )["c"], IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Constant, IECore.IntVectorData( [ 3, 8 ] ) ) )


		del tweak["tweaks"][0]
		tweak["tweaks"].addChild( Gaffer.TweakPlug( "a", IECore.FloatData( 42 ), Gaffer.TweakPlug.Mode.Replace ) )
		self.assertEqual( tweak["out"].object( "/plane" )["a"], IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Constant, IECore.FloatData( 42 ) ) )

		tweak["tweaks"][0]["name"].setValue( "x" )
		with self.assertRaisesRegex( Gaffer.ProcessException, 'Cannot apply tweak with mode Replace to "x" : This parameter does not exist.' ):
			tweak["out"].object( "/plane" )

		tweak["ignoreMissing"].setValue( True )
		self.assertEqual( tweak["out"].object( "/plane" ), tweak["in"].object( "/plane" ) )

		tweak["tweaks"][0]["name"].setValue( "a" )
		tweak["tweaks"][0]["mode"].setValue( Gaffer.TweakPlug.Mode.ListAppend )

		with self.assertRaisesRegex( Gaffer.ProcessException, 'Cannot apply tweak with mode ListAppend to "a" : Data type FloatData not supported.' ):
			tweak["out"].object( "/plane" )

		del tweak["tweaks"][0]

		tweak["tweaks"].addChild( Gaffer.TweakPlug( "P", IECore.V3fData( imath.V3f( 0.5 ) ), Gaffer.TweakPlug.Mode.Replace ) )
		tweak["tweaks"].addChild( Gaffer.TweakPlug( "N", IECore.V3fData( imath.V3f( 0.1 ) ), Gaffer.TweakPlug.Mode.Replace ) )
		tweak["tweaks"].addChild( Gaffer.TweakPlug( "uv", IECore.V2fData( imath.V2f( 10 ) ), Gaffer.TweakPlug.Mode.Replace ) )
		tweak["tweaks"].addChild( Gaffer.TweakPlug( "a", IECore.FloatData( 0.7 ), Gaffer.TweakPlug.Mode.Replace ) )
		tweak["tweaks"].addChild( Gaffer.TweakPlug( "b", IECore.IntData( 7 ), Gaffer.TweakPlug.Mode.Replace ) )
		tweak["tweaks"].addChild( Gaffer.TweakPlug( "c", IECore.IntVectorData( [7] ), Gaffer.TweakPlug.Mode.Replace ) )

		uvIndices = tweak["in"].object( "/plane" )["uv"].indices

		o = tweak["out"].object( "/plane" )
		self.assertEqual( o.keys(), [ "N", "P", "a", "b", "badIds", "c", "uv", "vertexIds" ] )
		self.assertEqual( o["N"], IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, IECore.V3fVectorData( [ imath.V3f( 0.1 ) ] * 9, IECore.GeometricData.Interpretation.Normal ) ) )
		self.assertEqual( o["P"], IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, IECore.V3fVectorData( [ imath.V3f( 0.5 ) ] * 9, IECore.GeometricData.Interpretation.Point ) ) )
		self.assertEqual( o["a"], IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Constant, IECore.FloatData( 0.7 ) ) )
		self.assertEqual( o["b"], IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Uniform, IECore.IntVectorData( [ 7 ] * 4 ) ) )
		self.assertEqual( o["c"], IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Constant, IECore.IntVectorData( [ 7 ] ) ) )
		self.assertEqual( o["uv"], IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.FaceVarying, IECore.V2fVectorData( [ imath.V2f( 10 ) ] * 9, IECore.GeometricData.Interpretation.UV ), uvIndices ) )

		tweak["tweaks"][1]["mode"].setValue( Gaffer.TweakPlug.Mode.Remove )
		tweak["tweaks"][2]["mode"].setValue( Gaffer.TweakPlug.Mode.Remove )
		tweak["tweaks"][3]["mode"].setValue( Gaffer.TweakPlug.Mode.Remove )
		tweak["tweaks"][4]["mode"].setValue( Gaffer.TweakPlug.Mode.Remove )
		tweak["tweaks"][5]["mode"].setValue( Gaffer.TweakPlug.Mode.Remove )

		o = tweak["out"].object( "/plane" )
		self.assertEqual( o.keys(), [ "P", "badIds", "vertexIds" ] )

		for i in tweak["tweaks"]:
			i["mode"].setValue( Gaffer.TweakPlug.Mode.Add )
		tweak["tweaks"][-1]["mode"].setValue( Gaffer.TweakPlug.Mode.ListAppend )

		o = tweak["out"].object( "/plane" )
		self.assertEqual( o.keys(), [ "N", "P", "a", "b", "badIds", "c", "uv", "vertexIds" ] )
		self.assertEqual( o["N"], IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, IECore.V3fVectorData( [ imath.V3f( 0.1, 0.1, 1.1 ) ] * 9, IECore.GeometricData.Interpretation.Normal ) ) )
		self.assertEqual( o["P"], IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex, IECore.V3fVectorData(
				[ imath.V3f( x + 0.5, y + 0.5, 0.5 ) for x, y in
					[ (-1, -1), (0, -1), (1, -1),  ( -1, 0 ), ( 0, 0 ), (1, 0 ),  ( -1, 1 ), ( 0, 1 ), ( 1, 1 ) ] ],
			IECore.GeometricData.Interpretation.Point ) ) )
		self.assertEqual( o["a"], IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Constant, IECore.FloatData( 7.7 ) ) )
		self.assertEqual( o["b"], IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Uniform, IECore.IntVectorData( [ 7, 49, 49, 7 ] ) ) )
		self.assertEqual( o["c"], IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Constant, IECore.IntVectorData( [ 3, 4, 8, 7 ] ) ) )
		self.assertEqual( o["uv"], IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.FaceVarying, IECore.V2fVectorData(
				[ imath.V2f( x + 10, y + 10 ) for x, y in
					[ (0, 0), (0.5, 0), (1, 0),  ( 0, 0.5 ), ( 0.5, 0.5 ), (1, 0.5 ),  ( 0, 1 ), ( 0.5, 1 ), ( 1, 1 ) ] ],
			IECore.GeometricData.Interpretation.UV ), uvIndices ) )

		# Setting the selection mode does nothing while the interpolation is set to "Any"
		tweak["selectionMode"].setValue( GafferScene.PrimitiveVariableTweaks.SelectionMode.IdList )
		tweak["idList"].setValue( IECore.Int64VectorData( [ 0, 3, 4, 5 ] ) )

		self.assertEqual( tweak["out"].object( "/plane" ), o )

		tweak["interpolation"].setValue( IECoreScene.PrimitiveVariable.Interpolation.Vertex )

		with self.assertRaisesRegex( Gaffer.ProcessException, 'Cannot apply tweak to "uv" : Interpolation "Vertex" doesn\'t match primitive variable interpolation "FaceVarying".' ):
			tweak["out"].object( "/plane" )

		tweak["tweaks"][2]["enabled"].setValue( False )

		with self.assertRaisesRegex( Gaffer.ProcessException, 'Cannot apply tweak to "a" : Interpolation "Vertex" doesn\'t match primitive variable interpolation "Constant".' ):
			tweak["out"].object( "/plane" )

		tweak["tweaks"][3]["enabled"].setValue( False )
		tweak["tweaks"][5]["enabled"].setValue( False )

		with self.assertRaisesRegex( Gaffer.ProcessException, 'Cannot apply tweak to "b" : Interpolation "Vertex" doesn\'t match primitive variable interpolation "Uniform".' ):
			tweak["out"].object( "/plane" )

		tweak["tweaks"][4]["enabled"].setValue( False )

		inObj = tweak["in"].object( "/plane" )
		o = tweak["out"].object( "/plane" )
		self.assertEqual( o.keys(), [ "N", "P", "a", "b", "badIds", "c", "uv", "vertexIds" ] )
		self.assertEqual( o["N"], IECoreScene.PrimitiveVariable(
				IECoreScene.PrimitiveVariable.Interpolation.Vertex, IECore.V3fVectorData( [ imath.V3f( *i ) for i in [
					(0.1, 0.1, 1.1), (0, 0, 1), (0, 0, 1),
					(0.1, 0.1, 1.1), (0.1, 0.1, 1.1), (0.1, 0.1, 1.1),
					(0, 0, 1), (0, 0, 1), (0, 0, 1)
				] ], IECore.GeometricData.Interpretation.Normal ) ) )
		self.assertEqual( o["P"], IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex, IECore.V3fVectorData(
				[ imath.V3f( *i ) for i in
					[ (-0.5, -0.5, 0.5), (0, -1, 0), (1, -1, 0),  ( -0.5, 0.5, 0.5 ), ( 0.5, 0.5, 0.5 ), (1.5, 0.5, 0.5 ),  ( -1, 1, 0 ), ( 0, 1, 0 ), ( 1, 1, 0 ) ] ],
			IECore.GeometricData.Interpretation.Point ) ) )
		self.assertEqual( o["a"], inObj["a"] )
		self.assertEqual( o["b"], inObj["b"] )
		self.assertEqual( o["c"], inObj["c"] )
		self.assertEqual( o["uv"], inObj["uv"] )

		# TODO - this is some pretty nasty behaviour that probably needs fixing. If an id occurs twice in
		# the list, it gets tweaked twice. This is probably unexpected ( and it's definitely unexpected that
		# it gets tweaked twice if there is no id primVar, but only once if there is an id primvar ). So we
		# probably need to do something about this, though it's pretty unfortunate that this will mean
		# unnecessarily sticking all the ids in an unordered_set in the common case where the id list doesn't
		# contain duplicates.
		tweak["idList"].setValue( IECore.Int64VectorData( [ 0, 3, 4, 5, 3 ] ) )
		o = tweak["out"].object( "/plane" )
		self.assertEqual( o["N"], IECoreScene.PrimitiveVariable(
				IECoreScene.PrimitiveVariable.Interpolation.Vertex, IECore.V3fVectorData( [ imath.V3f( *i ) for i in [
					(0.1, 0.1, 1.1), (0, 0, 1), (0, 0, 1),
					(0.2, 0.2, 1.2), (0.1, 0.1, 1.1), (0.1, 0.1, 1.1),
					(0, 0, 1), (0, 0, 1), (0, 0, 1)
				] ], IECore.GeometricData.Interpretation.Normal ) ) )

		# Test IdListPrimVarMode
		tweak["selectionMode"].setValue( GafferScene.PrimitiveVariableTweaks.SelectionMode.IdListPrimitiveVariable )
		tweak["idListVariable"].setValue( "bad" )
		with self.assertRaisesRegex( Gaffer.ProcessException, 'Can\'t find id list primitive variable "bad".' ):
			tweak["out"].object( "/plane" )
		tweak["idListVariable"].setValue( "a" )
		with self.assertRaisesRegex( Gaffer.ProcessException, 'Invalid id list primitive variable "a". A constant IntVector or Int64Vector is required.' ):
			tweak["out"].object( "/plane" )
		tweak["idListVariable"].setValue( "vertexIds" )
		with self.assertRaisesRegex( Gaffer.ProcessException, 'Invalid id list primitive variable "vertexIds". A constant IntVector or Int64Vector is required.' ):
			tweak["out"].object( "/plane" )

		tweak["idListVariable"].setValue( "c" )
		o = tweak["out"].object( "/plane" )
		self.assertEqual( o["N"], IECoreScene.PrimitiveVariable(
				IECoreScene.PrimitiveVariable.Interpolation.Vertex, IECore.V3fVectorData( [ imath.V3f( *i ) for i in [
					(0, 0, 1), (0, 0, 1), (0, 0, 1),
					(0.1, 0.1, 1.1), (0.1, 0.1, 1.1), (0, 0, 1),
					(0, 0, 1), (0, 0, 1), (0.1, 0.1, 1.1)
				] ], IECore.GeometricData.Interpretation.Normal ) ) )

		tweak["id"].setValue( "vertexIds" )

		# The current id list doesn't match these new ids
		self.assertEqual( tweak["out"].object( "/plane" ), inObj )

		tweak["selectionMode"].setValue( GafferScene.PrimitiveVariableTweaks.SelectionMode.IdList )
		tweak["idList"].setValue( IECore.Int64VectorData( [ 11, 31 ] ) )

		o = tweak["out"].object( "/plane" )
		self.assertEqual( o["N"], IECoreScene.PrimitiveVariable(
				IECoreScene.PrimitiveVariable.Interpolation.Vertex, IECore.V3fVectorData( [ imath.V3f( *i ) for i in [
					(0, 0, 1), (0.1, 0.1, 1.1), (0, 0, 1),
					(0, 0, 1), (0, 0, 1), (0, 0, 1),
					(0, 0, 1), (0.1, 0.1, 1.1), (0, 0, 1)
				] ], IECore.GeometricData.Interpretation.Normal ) ) )
		self.assertEqual( o["P"], IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex, IECore.V3fVectorData(
				[ imath.V3f( *i ) for i in
					[ (-1, -1, 0), (0.5, -0.5, 0.5), (1, -1, 0),  ( -1, 0, 0 ), ( 0, 0, 0 ), (1, 0, 0 ),  ( -1, 1, 0 ), ( 0.5, 1.5, 0.5 ), ( 1, 1, 0 ) ] ],
			IECore.GeometricData.Interpretation.Point ) ) )

		tweak["id"].setValue( "badIds" )

		with self.assertRaisesRegex( Gaffer.ProcessException, 'Id variable "badIds" is not allowed to be indexed.' ):
			tweak["out"].object( "/plane" )


		tweak["tweaks"][0]["enabled"].setValue( False )
		tweak["tweaks"][1]["enabled"].setValue( False )
		tweak["tweaks"][2]["enabled"].setValue( False )

		tweak["tweaks"][4]["enabled"].setValue( True )

		tweak["interpolation"].setValue( IECoreScene.PrimitiveVariable.Interpolation.Uniform )

		tweak["id"].setValue( "vertexIds" )

		with self.assertRaisesRegex( Gaffer.ProcessException, 'Id variable "vertexIds" : Interpolation "Vertex" doesn\'t match specified interpolation "Uniform".' ):
			tweak["out"].object( "/plane" )

		tweak["id"].setValue( "" )

		# Check that only in-bound ids have any effect
		self.assertEqual( tweak["out"].object( "/plane" ), inObj )

		tweak["idList"].setValue( IECore.Int64VectorData( [ 2, 31 ] ) )

		o = tweak["out"].object( "/plane" )
		self.assertEqual( o["b"], IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Uniform, IECore.IntVectorData( [ 0, 42, 49, 0 ] ) ) )

		tweak["selectionMode"].setValue( GafferScene.PrimitiveVariableTweaks.SelectionMode.All )
		o = tweak["out"].object( "/plane" )
		self.assertEqual( o["b"], IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Uniform, IECore.IntVectorData( [ 7, 49, 49, 7 ] ) ) )

		tweak["interpolation"].setValue( IECoreScene.PrimitiveVariable.Interpolation.FaceVarying )

		tweak["tweaks"][2]["enabled"].setValue( True )
		tweak["tweaks"][4]["enabled"].setValue( False )

		o = tweak["out"].object( "/plane" )
		self.assertEqual( o["P"], inObj["P"] )
		self.assertEqual( o["N"], inObj["N"] )
		self.assertEqual( o["uv"], IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.FaceVarying, IECore.V2fVectorData(
				[ imath.V2f( x + 10, y + 10 ) for x, y in
					[ (0, 0), (0.5, 0), (1, 0),  ( 0, 0.5 ), ( 0.5, 0.5 ), (1, 0.5 ),  ( 0, 1 ), ( 0.5, 1 ), ( 1, 1 ) ] ],
			IECore.GeometricData.Interpretation.UV ), uvIndices ) )
		self.assertEqual( o["a"], inObj["a"] )
		self.assertEqual( o["b"], inObj["b"] )
		self.assertEqual( o["c"], inObj["c"] )

		# When tweaking an indexed primvar, things are a bit more complex - any data that gets tweaked gets
		# a new index, and any data that no longer has any indices referring to it is removed.
		tweak["selectionMode"].setValue( GafferScene.PrimitiveVariableTweaks.SelectionMode.IdList )
		tweak["idList"].setValue( IECore.Int64VectorData( [ 0, 1, 2, 3, 12, 13, 14, 15 ] ) )

		o = tweak["out"].object( "/plane" )
		self.assertEqual( o["uv"], IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.FaceVarying, IECore.V2fVectorData(
				[ imath.V2f( *i ) for i in
					[ ( 0.5, 0 ), ( 1, 0 ), ( 0, 0.5 ), ( 0.5, 0.5 ), ( 1, 0.5 ), ( 0, 1 ), ( 0.5, 1 ), ( 10, 10 ), ( 10.5, 10 ), ( 10.5, 10.5 ), ( 10, 10.5 ), ( 11, 10.5 ), ( 11, 11 ), ( 10.5, 11 ) ] ],
				IECore.GeometricData.Interpretation.UV ),
				IECore.IntVectorData( [ 7, 8, 9, 10, 0, 1, 4, 3, 2, 3, 6, 5, 9, 11, 12, 13 ] )
		) )

		tweak["selectionMode"].setValue( GafferScene.PrimitiveVariableTweaks.SelectionMode.MaskPrimitiveVariable )
		tweak["interpolation"].setValue( IECoreScene.PrimitiveVariable.Interpolation.Vertex )

		tweak["tweaks"][1]["enabled"].setValue( True )
		tweak["tweaks"][2]["enabled"].setValue( False )

		with self.assertRaisesRegex( Gaffer.ProcessException, 'Can\'t find mask primitive variable "".' ):
			tweak["out"].object( "/plane" )

		tweak["idList"].setValue( IECore.Int64VectorData() )
		tweak["idListVariable"].setValue( "" )
		tweak["maskVariable"].setValue( "uv" )
		with self.assertRaisesRegex( Gaffer.ProcessException, 'Mask primitive variable "uv" has wrong interpolation "FaceVarying", expected "Vertex".' ):
			tweak["out"].object( "/plane" )

		tweak["maskVariable"].setValue( "badIds" )
		o = tweak["out"].object( "/plane" )
		self.assertEqual( o["N"], IECoreScene.PrimitiveVariable(
				IECoreScene.PrimitiveVariable.Interpolation.Vertex, IECore.V3fVectorData( [ imath.V3f( *i ) for i in [
					(0, 0, 1), (0, 0, 1), (0.1, 0.1, 1.1),
					(0.1, 0.1, 1.1), (0, 0, 1), (0, 0, 1),
					(0, 0, 1), (0.1, 0.1, 1.1), (0, 0, 1)
				] ], IECore.GeometricData.Interpretation.Normal ) ) )

if __name__ == "__main__":
	unittest.main()
