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

class PrimitiveVariableTweaksTest( GafferSceneTest.SceneTestCase ):

	def typesData( self ):
		return {
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

	def typesCreator( self ):

		create = GafferScene.PrimitiveVariableTweaks()
		create["sphere"] = GafferScene.Sphere()
		create["in"].setInput( create["sphere"]["out"] )

		for ( name, val ) in self.typesData().items():
			create["tweaks"].addChild( Gaffer.TweakPlug( name, val, Gaffer.TweakPlug.Mode.Create ) )

		create["pathFilter"] = GafferScene.PathFilter()
		create["pathFilter"]["paths"].setValue( IECore.StringVectorData( [ "/sphere" ] ) )
		create["filter"].setInput( create["pathFilter"]["out"] )

		return create

	def testNoFilterPassThrough( self ):
		create = self.typesCreator()

		create["filter"].setInput( None )
		self.assertScenesEqual( create["sphere"]["out"], create["out"] )
		self.assertSceneHashesEqual( create["sphere"]["out"], create["out"] )

	def testCreateConstants( self ):

		create = self.typesCreator()

		with self.assertRaisesRegex( Gaffer.ProcessException, 'Cannot create primitive variable "a" when interpolation is set to `Any`. Please select an interpolation.' ):
			create["out"].object( "/sphere" )

		create["interpolation"].setValue( IECoreScene.PrimitiveVariable.Interpolation.Constant )
		o = create["out"].object( "/sphere" )

		testData = self.typesData()
		self.assertEqual( o.keys(), ['N', 'P'] + list( testData.keys() ) + ['uv'] )
		for k in testData.keys():
			self.assertEqual( o[k], IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Constant, testData[k] ) )

	def testCreateDifferentInterpolations( self ):

		create = self.typesCreator()
		create["interpolation"].setValue( IECoreScene.PrimitiveVariable.Interpolation.Vertex )
		with self.assertRaisesRegex( Gaffer.ProcessException, 'Invalid type "FloatVectorData" for non-constant element-wise tweak "h".' ):
			create["out"].object( "/sphere" )

		create["tweaks"][-1]["enabled"].setValue( False )
		create["tweaks"][-2]["enabled"].setValue( False )

		testData = self.typesData()
		del testData["h"]
		del testData["i"]

		for interp in [
			IECoreScene.PrimitiveVariable.Interpolation.Uniform,
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECoreScene.PrimitiveVariable.Interpolation.Varying,
			IECoreScene.PrimitiveVariable.Interpolation.FaceVarying
		]:
			create["interpolation"].setValue( interp )
			o = create["out"].object( "/sphere" )
			self.assertEqual( o.keys(), ['N', 'P'] + list( testData.keys() ) + ['uv'] )
			for k in testData.keys():
				dataType = getattr( IECore, testData[k].typeName().replace( "Data", "VectorData" ) )
				compData = dataType( [ testData[k].value ] * o.variableSize( interp ) )
				if hasattr( compData, "setInterpretation" ):
					compData.setInterpretation( testData[k].getInterpretation() )
				with self.subTest( interpolation = interp, name = k ):
					self.assertEqual( o[k], IECoreScene.PrimitiveVariable( interp, compData ) )

	def testBadTweakMessages( self ):

		create = self.typesCreator()
		create["interpolation"].setValue( IECoreScene.PrimitiveVariable.Interpolation.Vertex )
		create["tweaks"][-1]["enabled"].setValue( False )
		create["tweaks"][-2]["enabled"].setValue( False )

		tweak = GafferScene.PrimitiveVariableTweaks()
		tweak["in"].setInput( create["out"] )
		tweak["filter"].setInput( create["pathFilter"]["out"] )

		tweak["tweaks"].addChild( Gaffer.TweakPlug( "a", IECore.Color4fData(), Gaffer.TweakPlug.Mode.Replace ) )

		with self.assertRaisesRegex( Gaffer.ProcessException, 'Cannot apply tweak to "a" : Parameter should be of type "IntData" in order to apply to an element of "IntVectorData", but got "Color4fData" instead.' ):
			tweak["out"].object( "/sphere" )

		create["interpolation"].setValue( IECoreScene.PrimitiveVariable.Interpolation.Constant )

		# \todo - this message should end with a period
		with self.assertRaisesRegex( Gaffer.ProcessException, 'Cannot apply tweak to "a" : Value of type "IntData" does not match parameter of type "Color4fData"' ):
			tweak["out"].object( "/sphere" )

	def tweakData( self ):
		return {
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

	def testReplace( self ):

		create = self.typesCreator()
		create["interpolation"].setValue( IECoreScene.PrimitiveVariable.Interpolation.Constant )

		tweak = GafferScene.PrimitiveVariableTweaks()
		tweak["in"].setInput( create["out"] )
		tweak["filter"].setInput( create["pathFilter"]["out"] )

		tweakData = self.tweakData()

		for ( name, val ) in tweakData.items():
			tweak["tweaks"].addChild( Gaffer.TweakPlug( name, val, Gaffer.TweakPlug.Mode.Replace ) )

		typesData = self.typesData()
		o = tweak["out"].object( "/sphere" )
		self.assertEqual( o.keys(), ['N', 'P'] + list( typesData.keys() ) + ['uv'] )
		for k in tweakData.keys():
			if not k in [ "c", "d" ]:
				self.assertEqual( o[k], IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Constant, tweakData[k] ) )
			else:
				# When replacing the value of a primvar, we keep the interpolation of the original
				self.assertEqual( o[k], IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Constant, IECore.V3fData( imath.V3f( 0.5 ), typesData[k].getInterpretation() ) ) )

	def expectedAddData( self ):
		return {
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

	def testAddConstant( self ):

		create = self.typesCreator()
		create["interpolation"].setValue( IECoreScene.PrimitiveVariable.Interpolation.Constant )

		tweak = GafferScene.PrimitiveVariableTweaks()
		tweak["in"].setInput( create["out"] )
		tweak["filter"].setInput( create["pathFilter"]["out"] )

		tweakData = self.tweakData()

		for ( name, val ) in tweakData.items():
			tweak["tweaks"].addChild( Gaffer.TweakPlug( name, val, Gaffer.TweakPlug.Mode.Add ) )

		expectedAdd = self.expectedAddData()

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


	def testReplaceVertex( self ):

		create = self.typesCreator()
		create["interpolation"].setValue( IECoreScene.PrimitiveVariable.Interpolation.Vertex )

		tweak = GafferScene.PrimitiveVariableTweaks()
		tweak["in"].setInput( create["out"] )
		tweak["filter"].setInput( create["pathFilter"]["out"] )

		tweakData = self.tweakData()
		del tweakData["h"]
		del tweakData["i"]

		for ( name, val ) in tweakData.items():
			tweak["tweaks"].addChild( Gaffer.TweakPlug( name, val, Gaffer.TweakPlug.Mode.Replace ) )

		create["tweaks"][-1]["enabled"].setValue( False )
		create["tweaks"][-2]["enabled"].setValue( False )

		typesData = self.typesData()

		for interp in [
			IECoreScene.PrimitiveVariable.Interpolation.Uniform,
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECoreScene.PrimitiveVariable.Interpolation.Varying,
			IECoreScene.PrimitiveVariable.Interpolation.FaceVarying
		]:
			create["interpolation"].setValue( interp )
			o = tweak["out"].object( "/sphere" )
			self.assertEqual( o.keys(), ['N', 'P'] + list( tweakData.keys() ) + ['uv'] )
			for k in tweakData.keys():
				dataType = getattr( IECore, tweakData[k].typeName().replace( "Data", "VectorData" ) )
				compData = dataType( [ tweakData[k].value ] * o.variableSize( interp ) )
				if hasattr( compData, "setInterpretation" ):
					compData.setInterpretation( typesData[k].getInterpretation() )
				self.assertEqual( o[k], IECoreScene.PrimitiveVariable( interp, compData ) )

	def testAddVertex( self ):

		create = self.typesCreator()
		create["tweaks"][-1]["enabled"].setValue( False )
		create["tweaks"][-2]["enabled"].setValue( False )

		tweak = GafferScene.PrimitiveVariableTweaks()
		tweak["in"].setInput( create["out"] )
		tweak["filter"].setInput( create["pathFilter"]["out"] )

		tweakData = self.tweakData()
		del tweakData["h"]
		del tweakData["i"]

		for ( name, val ) in tweakData.items():
			tweak["tweaks"].addChild( Gaffer.TweakPlug( name, val, Gaffer.TweakPlug.Mode.Add ) )

		# listAppend mode works on string even when those strings are per-vertex
		tweak["tweaks"][-1]["mode"].setValue( Gaffer.TweakPlug.Mode.ListAppend )

		expectedAdd = self.expectedAddData()
		del expectedAdd["h"]
		del expectedAdd["i"]


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

	def testInvalidPrimVar( self ):

		m = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ), imath.V2i( 2 ) )
		m["a"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.IntVectorData( [ 0, 1, 2 ] )
		)

		p = GafferScene.ObjectToScene()
		p["object"].setValue( m )

		f = GafferScene.PathFilter()
		f["paths"].setValue( IECore.StringVectorData( [ "/object" ] ) )

		badTweak = GafferScene.PrimitiveVariableTweaks()
		badTweak["in"].setInput( p["out"] )
		badTweak["filter"].setInput( f["out"] )
		badTweak["interpolation"].setValue( IECoreScene.PrimitiveVariable.Interpolation.Constant )
		badTweak["tweaks"].addChild( Gaffer.TweakPlug( "a", IECore.IntData( 7 ), Gaffer.TweakPlug.Mode.Create ) )

		with self.assertRaisesRegex( Gaffer.ProcessException, 'Cannot tweak "a" : Primitive variable not valid.' ):
			badTweak["out"].object( "/object" )

	def testInvalidId( self ):

		m = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ), imath.V2i( 2 ) )
		m["badIds"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.IntVectorData( [ 0, 1 ] )
		)

		p = GafferScene.ObjectToScene()
		p["object"].setValue( m )

		f = GafferScene.PathFilter()
		f["paths"].setValue( IECore.StringVectorData( [ "/object" ] ) )

		badTweak = GafferScene.PrimitiveVariableTweaks()
		badTweak["in"].setInput( p["out"] )
		badTweak["filter"].setInput( f["out"] )
		badTweak["interpolation"].setValue( IECoreScene.PrimitiveVariable.Interpolation.Vertex )
		badTweak["tweaks"].addChild( Gaffer.TweakPlug( "P", IECore.V3fData( imath.V3f( 7 ) ), Gaffer.TweakPlug.Mode.Replace ) )
		badTweak["selectionMode"].setValue( GafferScene.PrimitiveVariableTweaks.SelectionMode.IdList )
		badTweak["idList"].setValue( IECore.Int64VectorData( [ 1, 2] ) )
		badTweak["id"].setValue( "badIds" )

		with self.assertRaisesRegex( Gaffer.ProcessException, 'Id primitive variable "badIds" is not valid.' ):
			badTweak["out"].object( "/object" )

		m["badIds"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.IntVectorData( [ 0, 1 ] ), IECore.IntVectorData( [ 0, 0, 1, 1, 0, 0, 0, 1, 0 ] )
		)
		p["object"].setValue( m )

		with self.assertRaisesRegex( Gaffer.ProcessException, 'Id variable "badIds" is not allowed to be indexed.' ):
			badTweak["out"].object( "/object" )

	def createConstantsAndUniforms( self ):
		m = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ), imath.V2i( 2 ) )
		m["vertexIds"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.IntVectorData( [ 10, 11, 12, 20, 21, 21, 30, 31, 33 ] )
		)
		m["indexedMask"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.IntVectorData( [ 0, 1 ] ), IECore.IntVectorData( [ 0, 0, 1, 1, 0, 0, 0, 1, 0 ] )
		)

		result = {}
		result["objectToScene"] = GafferScene.ObjectToScene()
		result["objectToScene"]["name"].setValue( "plane" )
		result["objectToScene"]["object"].setValue( m )

		result["filter"] = GafferScene.PathFilter()
		result["filter"]["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		result["constants"] = GafferScene.PrimitiveVariableTweaks()
		result["constants"]["in"].setInput( result["objectToScene"]["out"] )
		result["constants"]["filter"].setInput( result["filter"]["out"] )
		result["constants"]["interpolation"].setValue( IECoreScene.PrimitiveVariable.Interpolation.Constant )
		result["constants"]["tweaks"].addChild( Gaffer.TweakPlug( "a", IECore.FloatData( 7 ), Gaffer.TweakPlug.Mode.Create ) )
		result["constants"]["tweaks"].addChild( Gaffer.TweakPlug( "c", IECore.IntVectorData( [ 3, 4, 8 ] ), Gaffer.TweakPlug.Mode.Create ) )

		result["result"] = GafferScene.PrimitiveVariableTweaks()
		result["result"]["in"].setInput( result["constants"]["out"] )
		result["result"]["filter"].setInput( result["filter"]["out"] )
		result["result"]["interpolation"].setValue( IECoreScene.PrimitiveVariable.Interpolation.Uniform )
		result["result"]["tweaks"].addChild( Gaffer.TweakPlug( "b", IECore.IntData( 42 ), Gaffer.TweakPlug.Mode.Create ) )

		result["result"]["selectionMode"].setValue( GafferScene.PrimitiveVariableTweaks.SelectionMode.IdList )
		result["result"]["idList"].setValue( IECore.Int64VectorData( [ 1, 2] ) )

		return result

	def testCreateConstantsAndUniforms( self ):

		create = self.createConstantsAndUniforms()

		o = create["result"]["out"].object( "/plane" )

		self.assertEqual( o["a"].data, IECore.FloatData( 7 ) )
		self.assertEqual( o["b"], IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Uniform, IECore.IntVectorData( [ 0, 42, 42, 0 ] ) ) )
		self.assertEqual( o["c"], IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Constant, IECore.IntVectorData( [ 3, 4, 8 ] ) ) )

	def testInvalidTweaks( self ):
		create = self.createConstantsAndUniforms()

		tweak = GafferScene.PrimitiveVariableTweaks()
		tweak["in"].setInput( create["result"]["out"] )
		tweak["filter"].setInput( create["filter"]["out"] )
		tweak["tweaks"].addChild( Gaffer.TweakPlug( "a", IECore.FloatData( 42 ), Gaffer.TweakPlug.Mode.Replace ) )

		self.assertEqual( tweak["out"].object( "/plane" )["a"], IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Constant, IECore.FloatData( 42 ) ) )

		tweak["tweaks"][0]["name"].setValue( "x" )
		with self.assertRaisesRegex( Gaffer.ProcessException, 'Cannot find primitive variable "x" to tweak.' ):
			tweak["out"].object( "/plane" )

		tweak["ignoreMissing"].setValue( True )
		self.assertEqual( tweak["out"].object( "/plane" ), tweak["in"].object( "/plane" ) )

		tweak["tweaks"][0]["name"].setValue( "a" )
		tweak["tweaks"][0]["mode"].setValue( Gaffer.TweakPlug.Mode.ListAppend )

		with self.assertRaisesRegex( Gaffer.ProcessException, 'Cannot apply tweak with mode ListAppend to "a" : Data type FloatData not supported.' ):
			tweak["out"].object( "/plane" )

	def testInvalidVectorTweaks( self ):

		create = self.createConstantsAndUniforms()

		tweak = GafferScene.PrimitiveVariableTweaks()
		tweak["in"].setInput( create["result"]["out"] )
		tweak["filter"].setInput( create["filter"]["out"] )
		tweak["tweaks"].addChild( Gaffer.TweakPlug( "x", IECore.IntData( 7 ), Gaffer.TweakPlug.Mode.Replace ) )

		with self.assertRaisesRegex( Gaffer.ProcessException, 'Cannot find primitive variable "x" to tweak.' ):
			tweak["out"].object( "/plane" )

		del tweak["tweaks"][0]
		tweak["tweaks"].addChild( Gaffer.TweakPlug( "x", IECore.FloatVectorData( [ 7 ] ), Gaffer.TweakPlug.Mode.ListAppend ) )

		# Applying a ListAppend tweak when there is no source found will try to create the variable, which will
		# fail if the interpolation isn't set
		with self.assertRaisesRegex( Gaffer.ProcessException, 'Cannot create primitive variable "x" when interpolation is set to `Any`. Please select an interpolation.' ):
			tweak["out"].object( "/plane" )

		tweak["ignoreMissing"].setValue( True )

		# This error is not affected by ignoreMissing
		with self.assertRaisesRegex( Gaffer.ProcessException, 'Cannot create primitive variable "x" when interpolation is set to `Any`. Please select an interpolation.' ):
			tweak["out"].object( "/plane" )
		tweak["ignoreMissing"].setValue( False )

		tweak["interpolation"].setValue( IECoreScene.PrimitiveVariable.Interpolation.Constant )
		self.assertEqual( tweak["out"].object( "/plane" )["x"], IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Constant, IECore.FloatVectorData( [ 7 ] ) ) )

		tweak["interpolation"].setValue( IECoreScene.PrimitiveVariable.Interpolation.Vertex )
		with self.assertRaisesRegex( Gaffer.ProcessException, 'Invalid type "FloatVectorData" for non-constant element-wise tweak "x".' ):
			tweak["out"].object( "/plane" )["x"]


	def testListTweaks( self ):
		create = self.createConstantsAndUniforms()

		tweak = GafferScene.PrimitiveVariableTweaks()
		tweak["in"].setInput( create["result"]["out"] )
		tweak["filter"].setInput( create["filter"]["out"] )
		tweak["tweaks"].addChild( Gaffer.TweakPlug( "c", IECore.IntVectorData( [ 7 ] ), Gaffer.TweakPlug.Mode.ListAppend ) )

		# List append working as intended
		self.assertEqual( tweak["out"].object( "/plane" )["c"], IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Constant, IECore.IntVectorData( [ 3, 4, 8, 7 ] ) ) )

		# List remove is considered successful if the target doesn't exist
		tweak["tweaks"][0]["name"].setValue( "x" )
		tweak["tweaks"][0]["mode"].setValue( Gaffer.TweakPlug.Mode.ListRemove )
		self.assertEqual( tweak["out"].object( "/plane" ), tweak["in"].object( "/plane" ) )

		# List remove working as intended
		tweak["tweaks"][0]["name"].setValue( "c" )
		tweak["tweaks"][0]["value"].setValue( IECore.IntVectorData( [ 4 ] ) )
		self.assertEqual( tweak["out"].object( "/plane" )["c"], IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Constant, IECore.IntVectorData( [ 3, 8 ] ) ) )

	def testCreateEdgeCases( self ):
		create = self.createConstantsAndUniforms()

		tweak = GafferScene.PrimitiveVariableTweaks()
		tweak["in"].setInput( create["result"]["out"] )
		tweak["filter"].setInput( create["filter"]["out"] )
		tweak["tweaks"].addChild( Gaffer.TweakPlug( "P", IECore.V3fData( imath.V3f( 42 ), IECore.GeometricData.Interpretation.Point ), Gaffer.TweakPlug.Mode.CreateIfMissing ) )

		# CreateIfMissing does nothing if there's already something there
		self.assertEqual( tweak["out"].object( "/plane" ), tweak["in"].object( "/plane" ) )

		# It doesn't matter if the type is wrong
		del tweak["tweaks"][0]
		tweak["tweaks"].addChild( Gaffer.TweakPlug( "P", IECore.BoolData( True ), Gaffer.TweakPlug.Mode.CreateIfMissing ) )
		self.assertEqual( tweak["out"].object( "/plane" ), tweak["in"].object( "/plane" ) )

		# Or the interpolation is wrong
		tweak["interpolation"].setValue( IECoreScene.PrimitiveVariable.Interpolation.Uniform )
		self.assertEqual( tweak["out"].object( "/plane" ), tweak["in"].object( "/plane" ) )

		del tweak["tweaks"][0]
		tweak["tweaks"].addChild( Gaffer.TweakPlug( "Px", IECore.V3fData( imath.V3f( 42 ), IECore.GeometricData.Interpretation.Point ), Gaffer.TweakPlug.Mode.CreateIfMissing ) )
		tweak["interpolation"].setValue( IECoreScene.PrimitiveVariable.Interpolation.Vertex )
		o = tweak["out"].object( "/plane" )
		self.assertEqual( o["Px"], IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, IECore.V3fVectorData( [ imath.V3f( 42 ) ] * 9, IECore.GeometricData.Interpretation.Point ) ) )

		# A very weird corner case - ListAppend with a V3f is totally bogus ... but if there is no existing
		# value, ListAppend is treated as a Create, which succeeds.
		tweak["tweaks"][0]["mode"].setValue( Gaffer.TweakPlug.Mode.ListAppend )
		o = tweak["out"].object( "/plane" )
		self.assertEqual( o["Px"], IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, IECore.V3fVectorData( [ imath.V3f( 42 ) ] * 9, IECore.GeometricData.Interpretation.Point ) ) )

		# If there is already a variable there, we get the expected error
		tweak["tweaks"][0]["name"].setValue( "P" )
		with self.assertRaisesRegex( Gaffer.ProcessException, 'Cannot apply tweak with mode ListAppend to "P" : Data type V3fDataBase not supported.' ):
			tweak["out"].object( "/plane" )

		# We can use Create to overwrite a variable with a completely different type
		del tweak["tweaks"][0]
		tweak["tweaks"].addChild( Gaffer.TweakPlug( "P", IECore.StringData( "foo" ), Gaffer.TweakPlug.Mode.Create ) )

		o = tweak["out"].object( "/plane" )
		self.assertEqual( o["P"], IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, IECore.StringVectorData( [ "foo" ] * 9 ) ) )

		# Or use Create to overwrite a variable with a completely different interpolation
		tweak["interpolation"].setValue( IECoreScene.PrimitiveVariable.Interpolation.Uniform )
		o = tweak["out"].object( "/plane" )
		self.assertEqual( o["P"], IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Uniform, IECore.StringVectorData( [ "foo" ] * 4 ) ) )

	def createVariousTweaks( self, mode ):
		tweak = GafferScene.PrimitiveVariableTweaks()
		tweak["interpolation"].setValue( IECoreScene.PrimitiveVariable.Interpolation.Invalid )

		tweak["tweaks"].addChild( Gaffer.TweakPlug( "P", IECore.V3fData( imath.V3f( 0.5 ) ), mode ) )
		tweak["tweaks"].addChild( Gaffer.TweakPlug( "N", IECore.V3fData( imath.V3f( 0.1 ) ), mode ) )
		tweak["tweaks"].addChild( Gaffer.TweakPlug( "uv", IECore.V2fData( imath.V2f( 10 ) ), mode ) )
		tweak["tweaks"].addChild( Gaffer.TweakPlug( "a", IECore.FloatData( 0.7 ), mode ) )
		tweak["tweaks"].addChild( Gaffer.TweakPlug( "b", IECore.IntData( 7 ), mode ) )
		tweak["tweaks"].addChild( Gaffer.TweakPlug( "c", IECore.IntVectorData( [7] ), mode ) )

		return tweak

	def testReplaceVariousInterps( self ):
		create = self.createConstantsAndUniforms()
		tweak = self.createVariousTweaks( Gaffer.TweakPlug.Mode.Replace )
		tweak["in"].setInput( create["result"]["out"] )
		tweak["filter"].setInput( create["filter"]["out"] )

		uvIndices = tweak["in"].object( "/plane" )["uv"].indices

		o = tweak["out"].object( "/plane" )
		self.assertEqual( o.keys(), [ "N", "P", "a", "b", "c", "indexedMask", "uv", "vertexIds" ] )
		self.assertEqual( o["N"], IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, IECore.V3fVectorData( [ imath.V3f( 0.1 ) ] * 9, IECore.GeometricData.Interpretation.Normal ) ) )
		self.assertEqual( o["P"], IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, IECore.V3fVectorData( [ imath.V3f( 0.5 ) ] * 9, IECore.GeometricData.Interpretation.Point ) ) )
		self.assertEqual( o["a"], IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Constant, IECore.FloatData( 0.7 ) ) )
		self.assertEqual( o["b"], IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Uniform, IECore.IntVectorData( [ 7 ] * 4 ) ) )
		self.assertEqual( o["c"], IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Constant, IECore.IntVectorData( [ 7 ] ) ) )
		self.assertEqual( o["uv"], IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.FaceVarying, IECore.V2fVectorData( [ imath.V2f( 10 ) ] * 9, IECore.GeometricData.Interpretation.UV ), uvIndices ) )

	def testRemoveVariousInterps( self ):
		create = self.createConstantsAndUniforms()
		tweak = self.createVariousTweaks( Gaffer.TweakPlug.Mode.Remove )
		tweak["in"].setInput( create["result"]["out"] )
		tweak["filter"].setInput( create["filter"]["out"] )

		# Here, all the types match nicely
		o = tweak["out"].object( "/plane" )
		self.assertEqual( o.keys(), [ "indexedMask", "vertexIds" ] )

		# But it wouldn't matter if we gave a completely wrong type when doing a remove
		del tweak["tweaks"][-1]
		tweak["tweaks"].addChild( Gaffer.TweakPlug( "c", IECore.StringData( "foo" ), Gaffer.TweakPlug.Mode.Remove ) )

		o = tweak["out"].object( "/plane" )
		self.assertEqual( o.keys(), [ "indexedMask", "vertexIds" ] )

		# Currently, though, we do throw an error if the interpolation is wrong
		tweak["interpolation"].setValue( IECoreScene.PrimitiveVariable.Interpolation.Vertex )

		with self.assertRaisesRegex( Gaffer.ProcessException, 'Cannot apply tweak to "uv" : Interpolation `Vertex` doesn\'t match primitive variable interpolation `FaceVarying`.' ):
			tweak["out"].object( "/plane" )

	def testAddVariousInterps( self ):
		create = self.createConstantsAndUniforms()
		tweak = self.createVariousTweaks( Gaffer.TweakPlug.Mode.Add )
		tweak["in"].setInput( create["result"]["out"] )
		tweak["filter"].setInput( create["filter"]["out"] )

		with self.assertRaisesRegex( Gaffer.ProcessException, 'Cannot apply tweak with mode Add to "c" : Data type IntVectorData not supported.' ):
			tweak["out"].object( "/plane" )

		tweak["tweaks"][-1]["mode"].setValue( Gaffer.TweakPlug.Mode.ListAppend )

		uvIndices = tweak["in"].object( "/plane" )["uv"].indices
		o = tweak["out"].object( "/plane" )
		self.assertEqual( o.keys(), [ "N", "P", "a", "b", "c", "indexedMask", "uv", "vertexIds" ] )
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


	def testInvalidVertexTweaks( self ):

		create = self.createConstantsAndUniforms()
		tweak = self.createVariousTweaks( Gaffer.TweakPlug.Mode.Add )
		tweak["in"].setInput( create["result"]["out"] )
		tweak["filter"].setInput( create["filter"]["out"] )

		tweak["tweaks"][-1]["mode"].setValue( Gaffer.TweakPlug.Mode.ListAppend )

		o = tweak["out"].object( "/plane" )

		# Setting the selection mode does nothing while the interpolation is set to `Any`
		tweak["selectionMode"].setValue( GafferScene.PrimitiveVariableTweaks.SelectionMode.IdList )
		tweak["idList"].setValue( IECore.Int64VectorData( [ 0, 3, 4, 5 ] ) )

		self.assertEqual( tweak["out"].object( "/plane" ), o )

		tweak["interpolation"].setValue( IECoreScene.PrimitiveVariable.Interpolation.Vertex )

		with self.assertRaisesRegex( Gaffer.ProcessException, 'Cannot apply tweak to "uv" : Interpolation `Vertex` doesn\'t match primitive variable interpolation `FaceVarying`.' ):
			tweak["out"].object( "/plane" )

		tweak["tweaks"][2]["enabled"].setValue( False )

		with self.assertRaisesRegex( Gaffer.ProcessException, 'Cannot apply tweak to "a" : Interpolation `Vertex` doesn\'t match primitive variable interpolation `Constant`.' ):
			tweak["out"].object( "/plane" )

		tweak["tweaks"][3]["enabled"].setValue( False )
		tweak["tweaks"][5]["enabled"].setValue( False )

		with self.assertRaisesRegex( Gaffer.ProcessException, 'Cannot apply tweak to "b" : Interpolation `Vertex` doesn\'t match primitive variable interpolation `Uniform`.' ):
			tweak["out"].object( "/plane" )

	def testVertexIdList( self ):

		create = self.createConstantsAndUniforms()
		tweak = GafferScene.PrimitiveVariableTweaks()
		tweak["in"].setInput( create["result"]["out"] )
		tweak["filter"].setInput( create["filter"]["out"] )

		tweak["tweaks"].addChild( Gaffer.TweakPlug( "P", IECore.V3fData( imath.V3f( 0.5 ) ), Gaffer.TweakPlug.Mode.Add ) )
		tweak["tweaks"].addChild( Gaffer.TweakPlug( "N", IECore.V3fData( imath.V3f( 0.1 ) ), Gaffer.TweakPlug.Mode.Add ) )

		tweak["interpolation"].setValue( IECoreScene.PrimitiveVariable.Interpolation.Vertex )
		tweak["selectionMode"].setValue( GafferScene.PrimitiveVariableTweaks.SelectionMode.IdList )
		tweak["idList"].setValue( IECore.Int64VectorData( [ 0, 3, 4, 5 ] ) )

		refObj = tweak["in"].object( "/plane" )
		refObj["N"] = IECoreScene.PrimitiveVariable(
				IECoreScene.PrimitiveVariable.Interpolation.Vertex, IECore.V3fVectorData( [ imath.V3f( *i ) for i in [
					(0.1, 0.1, 1.1), (0, 0, 1), (0, 0, 1),
					(0.1, 0.1, 1.1), (0.1, 0.1, 1.1), (0.1, 0.1, 1.1),
					(0, 0, 1), (0, 0, 1), (0, 0, 1)
				] ], IECore.GeometricData.Interpretation.Normal ) )
		refObj["P"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex, IECore.V3fVectorData(
				[ imath.V3f( *i ) for i in
					[ (-0.5, -0.5, 0.5), (0, -1, 0), (1, -1, 0),  ( -0.5, 0.5, 0.5 ), ( 0.5, 0.5, 0.5 ), (1.5, 0.5, 0.5 ),  ( -1, 1, 0 ), ( 0, 1, 0 ), ( 1, 1, 0 ) ] ],
			IECore.GeometricData.Interpretation.Point ) )
		self.assertEqual( tweak["out"].object( "/plane" ), refObj )

		# Check that an id appearing twice in the id list has no extra effect.
		tweak["idList"].setValue( IECore.Int64VectorData( [ 0, 3, 4, 5, 3 ] ) )
		o = tweak["out"].object( "/plane" )
		self.assertEqual( o["N"], IECoreScene.PrimitiveVariable(
				IECoreScene.PrimitiveVariable.Interpolation.Vertex, IECore.V3fVectorData( [ imath.V3f( *i ) for i in [
					(0.1, 0.1, 1.1), (0, 0, 1), (0, 0, 1),
					(0.1, 0.1, 1.1), (0.1, 0.1, 1.1), (0.1, 0.1, 1.1),
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
		self.assertEqual( tweak["out"].object( "/plane" ), tweak["in"].object( "/plane" ) )

		tweak["selectionMode"].setValue( GafferScene.PrimitiveVariableTweaks.SelectionMode.IdList )
		tweak["idList"].setValue( IECore.Int64VectorData( [ 11, 31 ] ) )

		refObj["N"] = IECoreScene.PrimitiveVariable(
				IECoreScene.PrimitiveVariable.Interpolation.Vertex, IECore.V3fVectorData( [ imath.V3f( *i ) for i in [
					(0, 0, 1), (0.1, 0.1, 1.1), (0, 0, 1),
					(0, 0, 1), (0, 0, 1), (0, 0, 1),
					(0, 0, 1), (0.1, 0.1, 1.1), (0, 0, 1)
				] ], IECore.GeometricData.Interpretation.Normal ) )
		refObj["P"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex, IECore.V3fVectorData(
				[ imath.V3f( *i ) for i in
					[ (-1, -1, 0), (0.5, -0.5, 0.5), (1, -1, 0),  ( -1, 0, 0 ), ( 0, 0, 0 ), (1, 0, 0 ),  ( -1, 1, 0 ), ( 0.5, 1.5, 0.5 ), ( 1, 1, 0 ) ] ],
			IECore.GeometricData.Interpretation.Point ) )
		self.assertEqual( tweak["out"].object( "/plane" ), refObj )


	def testUniformIdList( self ):

		create = self.createConstantsAndUniforms()

		tweak = GafferScene.PrimitiveVariableTweaks()
		tweak["in"].setInput( create["result"]["out"] )
		tweak["filter"].setInput( create["filter"]["out"] )
		tweak["tweaks"].addChild( Gaffer.TweakPlug( "b", IECore.IntData( 7 ), Gaffer.TweakPlug.Mode.Add ) )

		tweak["selectionMode"].setValue( GafferScene.PrimitiveVariableTweaks.SelectionMode.IdList )
		tweak["idList"].setValue( IECore.Int64VectorData( [ 11, 31 ] ) )

		tweak["interpolation"].setValue( IECoreScene.PrimitiveVariable.Interpolation.Uniform )

		inObj = tweak["in"].object( "/plane" )

		# Check that only in-bound ids have any effect
		self.assertEqual( tweak["out"].object( "/plane" ), inObj )

		tweak["idList"].setValue( IECore.Int64VectorData( [ 2, 31 ] ) )

		o = tweak["out"].object( "/plane" )
		self.assertEqual( o["b"], IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Uniform, IECore.IntVectorData( [ 0, 42, 49, 0 ] ) ) )

		tweak["idList"].setValue( IECore.Int64VectorData( [ 2, 3 ] ) )
		o = tweak["out"].object( "/plane" )
		self.assertEqual( o["b"], IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Uniform, IECore.IntVectorData( [ 0, 42, 49, 7 ] ) ) )

		# Test inverting selection

		tweak["invertSelection"].setValue( True )
		o = tweak["out"].object( "/plane" )
		self.assertEqual( o["b"], IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Uniform, IECore.IntVectorData( [ 7, 49, 42, 0 ] ) ) )

		# Test selection mode

		tweak["selectionMode"].setValue( GafferScene.PrimitiveVariableTweaks.SelectionMode.All )
		o = tweak["out"].object( "/plane" )
		self.assertEqual( o["b"], IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Uniform, IECore.IntVectorData( [ 7, 49, 49, 7 ] ) ) )

		# Test wrong interpolation

		tweak["selectionMode"].setValue( GafferScene.PrimitiveVariableTweaks.SelectionMode.IdList )
		tweak["id"].setValue( "vertexIds" )

		with self.assertRaisesRegex( Gaffer.ProcessException, 'Id variable "vertexIds" : Interpolation `Vertex` doesn\'t match specified interpolation `Uniform`.' ):
			tweak["out"].object( "/plane" )


	def testFaceVaryingIndexed( self ):

		create = self.createConstantsAndUniforms()
		tweak = GafferScene.PrimitiveVariableTweaks()
		tweak["in"].setInput( create["result"]["out"] )
		tweak["filter"].setInput( create["filter"]["out"] )
		tweak["interpolation"].setValue( IECoreScene.PrimitiveVariable.Interpolation.FaceVarying )
		tweak["tweaks"].addChild( Gaffer.TweakPlug( "uv", IECore.V2fData( imath.V2f( 10 ) ), Gaffer.TweakPlug.Mode.Add ) )

		uvIndices = tweak["in"].object( "/plane" )["uv"].indices
		refObj = tweak["in"].object( "/plane" )
		refObj["uv"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.FaceVarying, IECore.V2fVectorData(
				[ imath.V2f( x + 10, y + 10 ) for x, y in
					[ (0, 0), (0.5, 0), (1, 0),  ( 0, 0.5 ), ( 0.5, 0.5 ), (1, 0.5 ),  ( 0, 1 ), ( 0.5, 1 ), ( 1, 1 ) ] ],
			IECore.GeometricData.Interpretation.UV ), uvIndices )

		self.assertEqual( tweak["out"].object( "/plane" ), refObj )

		# When tweaking an indexed primvar, things are a bit more complex - any data that gets tweaked gets
		# a new index, and any data that no longer has any indices referring to it is removed.
		tweak["selectionMode"].setValue( GafferScene.PrimitiveVariableTweaks.SelectionMode.IdList )
		tweak["idList"].setValue( IECore.Int64VectorData( [ 0, 1, 2, 3, 12, 13, 14, 15 ] ) )

		refObj["uv"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.FaceVarying, IECore.V2fVectorData(
				[ imath.V2f( *i ) for i in
					[ ( 0.5, 0 ), ( 1, 0 ), ( 0, 0.5 ), ( 0.5, 0.5 ), ( 1, 0.5 ), ( 0, 1 ), ( 0.5, 1 ), ( 10, 10 ), ( 10.5, 10 ), ( 10.5, 10.5 ), ( 10, 10.5 ), ( 11, 10.5 ), ( 11, 11 ), ( 10.5, 11 ) ] ],
				IECore.GeometricData.Interpretation.UV ),
				IECore.IntVectorData( [ 7, 8, 9, 10, 0, 1, 4, 3, 2, 3, 6, 5, 9, 11, 12, 13 ] )
		)
		self.assertEqual( tweak["out"].object( "/plane" ), refObj )


	def testMaskVariable( self ):

		create = self.createConstantsAndUniforms()
		tweak = GafferScene.PrimitiveVariableTweaks()
		tweak["in"].setInput( create["result"]["out"] )
		tweak["filter"].setInput( create["filter"]["out"] )

		tweak["tweaks"].addChild( Gaffer.TweakPlug( "N", IECore.V3fData( imath.V3f( 0.1 ) ), Gaffer.TweakPlug.Mode.Add ) )

		tweak["selectionMode"].setValue( GafferScene.PrimitiveVariableTweaks.SelectionMode.MaskPrimitiveVariable )
		tweak["interpolation"].setValue( IECoreScene.PrimitiveVariable.Interpolation.Vertex )

		with self.assertRaisesRegex( Gaffer.ProcessException, 'Can\'t find mask primitive variable "".' ):
			tweak["out"].object( "/plane" )

		tweak["maskVariable"].setValue( "uv" )
		with self.assertRaisesRegex( Gaffer.ProcessException, 'Mask primitive variable "uv" has wrong interpolation `FaceVarying`, expected `Vertex`.' ):
			tweak["out"].object( "/plane" )

		tweak["maskVariable"].setValue( "indexedMask" )
		o = tweak["out"].object( "/plane" )
		self.assertEqual( o["N"], IECoreScene.PrimitiveVariable(
				IECoreScene.PrimitiveVariable.Interpolation.Vertex, IECore.V3fVectorData( [ imath.V3f( *i ) for i in [
					(0, 0, 1), (0, 0, 1), (0.1, 0.1, 1.1),
					(0.1, 0.1, 1.1), (0, 0, 1), (0, 0, 1),
					(0, 0, 1), (0.1, 0.1, 1.1), (0, 0, 1)
				] ], IECore.GeometricData.Interpretation.Normal ) ) )

	def testBoundUpdate( self ) :

		sphere = GafferScene.Sphere()

		sphereFilter = GafferScene.PathFilter()
		sphereFilter["paths"].setValue( IECore.StringVectorData( [ "/sphere" ] ) )

		tweak = GafferScene.PrimitiveVariableTweaks()
		tweak["in"].setInput( sphere["out"] )
		tweak["filter"].setInput( sphereFilter["out"] )

		# We don't want to pay for unnecessary bounds propagation if P isn't being updated.
		self.assertScenesEqual( tweak["out"], tweak["in"], checks = { "bound" } )
		self.assertSceneHashesEqual( tweak["out"], tweak["in"], checks = { "bound" } )
		self.assertEqual( tweak["out"].bound( "/sphere" ), imath.Box3f( imath.V3f( -1 ), imath.V3f( 1 )  ) )

		# Try an actual write to P
		tweak["tweaks"].addChild( Gaffer.TweakPlug( "P", IECore.V3fData( imath.V3f( 1 ) ), Gaffer.TweakPlug.Mode.Add ) )
		self.assertEqual( tweak["out"].bound( "/sphere" ), imath.Box3f( imath.V3f( 0 ), imath.V3f( 2 )  ) )

		# Bounds are passed through if name doesn't match
		tweak["tweaks"][0]["name"].setValue( "notP" )
		self.assertScenesEqual( tweak["out"], tweak["in"], checks = { "bound" } )
		self.assertSceneHashesEqual( tweak["out"], tweak["in"], checks = { "bound" } )
		self.assertEqual( tweak["out"].bound( "/sphere" ), imath.Box3f( imath.V3f( -1 ), imath.V3f( 1 )  ) )

if __name__ == "__main__":
	unittest.main()
