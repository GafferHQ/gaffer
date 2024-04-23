#########################################################################
#
#  Copyright (c) 2022, Cinesite VFX Ltd. All rights reserved.
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

import IECore
import IECoreScene
import Gaffer
import GafferScene
import GafferSceneTest

class PrimitiveVariableQueryTest( GafferSceneTest.SceneTestCase ):

	nonVectorSuffix = "NonVector"

	names = (
		"b",
		"i",
		"f",
		"s",
		"v2i",
		"v3i",
		"v2f",
		"v3f",
		"c3f",
	)

	dataTypes = (
		IECore.BoolData,
		IECore.IntData,
		IECore.FloatData,
		IECore.StringData,
		IECore.V2iData,
		IECore.V3iData,
		IECore.V2fData,
		IECore.V3fData,
		IECore.Color3fData,
	)

	vectorDataTypes = (
		IECore.BoolVectorData,
		IECore.IntVectorData,
		IECore.FloatVectorData,
		IECore.StringVectorData,
		IECore.V2iVectorData,
		IECore.V3iVectorData,
		IECore.V2fVectorData,
		IECore.V3fVectorData,
		IECore.Color3fVectorData,
	)

	values = (
		True,
		10,
		11.0,
		"foo",
		imath.V2i( 12, 22 ),
		imath.V3i( 13, 23, 33 ),
		imath.V2f( 120.0, 220.0 ),
		imath.V3f( 130.0, 230.0, 330.0 ),
		imath.Color3f( 250.0, 450.0, 650.0 ),
	)

	defaultValues = (
		False,
		2,
		6.0,
		"baa",
		imath.V2i( 62, 72 ),
		imath.V3i( 63, 73, 73 ),
		imath.V2f( 620.0, 720.0 ),
		imath.V3f( 630.0, 730.0, 830.0 ),
		imath.Color3f( 150.0, 350.0, 550.0 ),
	)

	plugTypes = (
		Gaffer.BoolPlug,
		Gaffer.IntPlug,
		Gaffer.FloatPlug,
		Gaffer.StringPlug,
		Gaffer.V2iPlug,
		Gaffer.V3iPlug,
		Gaffer.V2fPlug,
		Gaffer.V3fPlug,
		Gaffer.Color3fPlug,
	)

	vectorPlugTypes = (
		Gaffer.BoolVectorDataPlug,
		Gaffer.IntVectorDataPlug,
		Gaffer.FloatVectorDataPlug,
		Gaffer.StringVectorDataPlug,
		Gaffer.V2iVectorDataPlug,
		Gaffer.V3iVectorDataPlug,
		Gaffer.V2fVectorDataPlug,
		Gaffer.V3fVectorDataPlug,
		Gaffer.Color3fVectorDataPlug,
	)

	interpolations = (
		IECoreScene.PrimitiveVariable.Interpolation.Constant,
		IECoreScene.PrimitiveVariable.Interpolation.Uniform,
		IECoreScene.PrimitiveVariable.Interpolation.Vertex,
		IECoreScene.PrimitiveVariable.Interpolation.Varying,
		IECoreScene.PrimitiveVariable.Interpolation.FaceVarying,
	)

	def makeQuad( self ) :

		mesh = IECoreScene.MeshPrimitive.createPlane( bounds=imath.Box2f( imath.V2f( 0 ), imath.V2f( 1 ) ) )

		# create constant primitive variables with non vector data

		interpolation = IECoreScene.PrimitiveVariable.Interpolation.Constant
		for ( name, dataType, value ) in zip( self.names, self.dataTypes, self.values ) :
			mesh[ name + str(interpolation) + self.nonVectorSuffix ] = IECoreScene.PrimitiveVariable(
				interpolation, dataType( value ) )

		# create primitive variables with vector data

		for interpolation in self.interpolations :
			for ( name, vectorDataType, value ) in zip( self.names, self.vectorDataTypes, self.values ) :
				mesh[ name + str(interpolation) ] = IECoreScene.PrimitiveVariable(
					interpolation, vectorDataType( [ value ] * mesh.variableSize( interpolation ) ) )

		self.assertTrue( mesh.arePrimitiveVariablesValid() )
		objectToScene = GafferScene.ObjectToScene()
		objectToScene["object"].setValue( mesh )

		return objectToScene

	def makeCamera( self ) :

		# add camera (non primitive) object to scene

		camera = IECoreScene.Camera()
		objectToScene = GafferScene.ObjectToScene()
		objectToScene["object"].setValue( camera )

		return objectToScene

	def testDefault( self ) :

		q = GafferScene.PrimitiveVariableQuery()

		self.assertEqual( len( q["queries"].children() ), 0 )
		self.assertEqual( len( q["out"].children() ), 0 )

	def testOutput( self ) :

		query = GafferScene.PrimitiveVariableQuery()

		n1 = query.addQuery( Gaffer.IntPlug( defaultValue=1 ) )
		n2 = query.addQuery( Gaffer.Color3fVectorDataPlug( defaultValue=IECore.Color3fVectorData( [ imath.Color3f( 0.1, 0.2, 0.3 ) ] ) ) )
		n3 = query.addQuery( Gaffer.V2iVectorDataPlug( defaultValue=IECore.V2iVectorData( [ imath.V2i( 1, 2 ) ] ) ) )
		badPlug = Gaffer.NameValuePlug( "missing", Gaffer.FloatVectorDataPlug( defaultValue=IECore.FloatVectorData() ), "badPlug" )

		self.assertEqual( query.outPlugFromQuery( n1 ), query["out"][0] )
		self.assertEqual( query.outPlugFromQuery( n2 ), query["out"][1] )
		self.assertEqual( query.outPlugFromQuery( n3 ), query["out"][2] )

		self.assertEqual( query.existsPlugFromQuery( n1 ), query["out"][0]["exists"] )
		self.assertEqual( query.existsPlugFromQuery( n2 ), query["out"][1]["exists"] )
		self.assertEqual( query.existsPlugFromQuery( n3 ), query["out"][2]["exists"] )

		self.assertEqual( query.valuePlugFromQuery( n1 ), query["out"][0]["value"] )
		self.assertEqual( query.valuePlugFromQuery( n2 ), query["out"][1]["value"] )
		self.assertEqual( query.valuePlugFromQuery( n3 ), query["out"][2]["value"] )

		self.assertEqual( query.typePlugFromQuery( n1 ), query["out"][0]["type"] )
		self.assertEqual( query.typePlugFromQuery( n2 ), query["out"][1]["type"] )
		self.assertEqual( query.typePlugFromQuery( n3 ), query["out"][2]["type"] )

		self.assertEqual( query.interpolationPlugFromQuery( n1 ), query["out"][0]["interpolation"] )
		self.assertEqual( query.interpolationPlugFromQuery( n2 ), query["out"][1]["interpolation"] )
		self.assertEqual( query.interpolationPlugFromQuery( n3 ), query["out"][2]["interpolation"] )

		self.assertEqual( query.queryPlug( query["out"][0]["value"] ), n1 )
		self.assertEqual( query.queryPlug( query["out"][1]["value"] ), n2 )
		self.assertEqual( query.queryPlug( query["out"][2]["value"] ), n3 )
		self.assertRaises( IECore.Exception, query.queryPlug, badPlug )

	def testAddRemoveQuery( self ) :

		def checkChildrenCount( plug, count ) :
			self.assertEqual( len( plug["queries"].children() ), count )
			self.assertEqual( len( plug["out"].children() ), count )

		query = GafferScene.PrimitiveVariableQuery()

		checkChildrenCount( query, 0 )

		a = query.addQuery( Gaffer.FloatPlug( defaultValue=5.0 ) )
		checkChildrenCount( query, 1 )
		self.assertEqual( query["queries"][0]["name"].getValue(), "" )
		self.assertEqual( query["queries"][0]["value"].getValue(), 5.0 )
		self.assertEqual( query["out"][0]["exists"].typeId(), Gaffer.BoolPlug.staticTypeId() )
		self.assertEqual( query["out"][0]["value"].typeId(), Gaffer.FloatPlug.staticTypeId() )
		self.assertEqual( query["out"][0]["type"].typeId(), Gaffer.StringPlug.staticTypeId() )
		self.assertEqual( query["out"][0]["interpolation"].typeId(), Gaffer.IntPlug.staticTypeId() )

		b = query.addQuery( Gaffer.Color3fVectorDataPlug( "c3f", defaultValue=IECore.Color3fVectorData() ), "c" )
		checkChildrenCount( query, 2 )
		self.assertEqual( query["queries"].children(), ( a, b ) )
		self.assertEqual( query["queries"][1]["name"].getValue(), "c" )
		self.assertEqual( query["queries"][1]["value"].getValue(), IECore.Color3fVectorData() )
		self.assertEqual( query["out"][0]["value"].typeId(), Gaffer.FloatPlug.staticTypeId() )
		self.assertEqual( query["out"][1]["value"].typeId(), Gaffer.Color3fVectorDataPlug.staticTypeId() )
		for i in range( 0, 2 ) :
			self.assertEqual( query["out"][i]["exists"].typeId(), Gaffer.BoolPlug.staticTypeId() )
			self.assertEqual( query["out"][i]["type"].typeId(), Gaffer.StringPlug.staticTypeId() )
			self.assertEqual( query["out"][i]["interpolation"].typeId(), Gaffer.IntPlug.staticTypeId() )

		c = query.addQuery( Gaffer.V2iVectorDataPlug( "v2i", Gaffer.Plug.Direction.Out, defaultValue=IECore.V2iVectorData( [ imath.V2i( 1, 2 ) ] ) ), "v" )
		checkChildrenCount( query, 3 )
		self.assertEqual( query["queries"].children(), ( a, b, c ) )
		self.assertEqual( query["queries"][2]["name"].getValue(), "v" )
		self.assertEqual( query["queries"][2]["value"].getValue(), IECore.V2iVectorData( [ imath.V2i( 1, 2 ) ] ) )
		self.assertEqual( query["out"][0]["value"].typeId(), Gaffer.FloatPlug.staticTypeId() )
		self.assertEqual( query["out"][1]["value"].typeId(), Gaffer.Color3fVectorDataPlug.staticTypeId() )
		self.assertEqual( query["out"][2]["value"].typeId(), Gaffer.V2iVectorDataPlug.staticTypeId() )
		for i in range( 0, 3 ) :
			self.assertEqual( query["out"][i]["exists"].typeId(), Gaffer.BoolPlug.staticTypeId() )
			self.assertEqual( query["out"][i]["type"].typeId(), Gaffer.StringPlug.staticTypeId() )
			self.assertEqual( query["out"][i]["interpolation"].typeId(), Gaffer.IntPlug.staticTypeId() )

		query.removeQuery( b )
		checkChildrenCount( query, 2 )
		self.assertEqual( query["queries"].children(), ( a, c ) )
		self.assertEqual( query["out"][0]["value"].typeId(), Gaffer.FloatPlug.staticTypeId() )
		self.assertEqual( query["out"][1]["value"].typeId(), Gaffer.V2iVectorDataPlug.staticTypeId() )
		for i in range( 0, 2 ) :
			self.assertEqual( query["out"][i]["exists"].typeId(), Gaffer.BoolPlug.staticTypeId() )
			self.assertEqual( query["out"][i]["type"].typeId(), Gaffer.StringPlug.staticTypeId() )
			self.assertEqual( query["out"][i]["interpolation"].typeId(), Gaffer.IntPlug.staticTypeId() )

		query.removeQuery( c )
		checkChildrenCount( query, 1 )
		query.removeQuery( a )
		checkChildrenCount( query, 0 )

	def testExists( self ) :

		scene = self.makeQuad()

		# query with correct name and value plug type exists

		q0 = GafferScene.PrimitiveVariableQuery()
		q0["scene"].setInput( scene["out"] )
		q0["location"].setValue( "/object" )

		for interpolation in self.interpolations :
			for ( name, vectorPlugType, vectorDataType ) in zip( self.names, self.vectorPlugTypes, self.vectorDataTypes ) :
				q0.addQuery( vectorPlugType( defaultValue=vectorDataType() ), name + str(interpolation) )

		interpolation = IECoreScene.PrimitiveVariable.Interpolation.Constant
		for ( name, plugType, defaultValue ) in zip( self.names, self.plugTypes, self.defaultValues ) :
			q0.addQuery( plugType( defaultValue=defaultValue ), name + str(interpolation) + self.nonVectorSuffix )

		for output in q0["out"] :
			self.assertTrue( output["exists"].getValue() )

		# query with correct name and wrong plug type exists

		q1 = GafferScene.PrimitiveVariableQuery()
		q1["scene"].setInput( scene["out"] )
		q1["location"].setValue( "/object" )

		for interpolation in self.interpolations :
			for name in self.names :
				q1.addQuery( Gaffer.M44fPlug( defaultValue=imath.M44f() ), name + str(interpolation) )

		interpolation = IECoreScene.PrimitiveVariable.Interpolation.Constant
		for name in self.names :
			q1.addQuery( Gaffer.M44fPlug( defaultValue=imath.M44f() ), name + str(interpolation) + self.nonVectorSuffix )

		for output in q1["out"] :
			self.assertTrue( output["exists"].getValue() )

		# query with wrong name does not exist

		q2 = GafferScene.PrimitiveVariableQuery()
		q2["scene"].setInput( scene["out"] )
		q2["location"].setValue( "/object" )

		for ( vectorPlugType, vectorDataType ) in zip( self.vectorPlugTypes, self.vectorDataTypes ) :
			q2.addQuery( vectorPlugType( defaultValue=vectorDataType() ), "sy" )
		for ( plugType, defaultValue ) in zip( self.plugTypes, self.defaultValues ) :
			q2.addQuery( plugType( defaultValue=defaultValue ), "vibes" )

		for output in q2["out"] :
			self.assertFalse( output["exists"].getValue() )

	def testInterpolation( self ) :

		scene = self.makeQuad()

		# query with correct name and value plug type returns interpolation (vector data)

		q0 = GafferScene.PrimitiveVariableQuery()
		q0["scene"].setInput( scene["out"] )
		q0["location"].setValue( "/object" )

		for interpolation in self.interpolations :
			for ( name, vectorPlugType, vectorDataType ) in zip( self.names, self.vectorPlugTypes, self.vectorDataTypes ) :
				q0.addQuery( vectorPlugType( defaultValue=vectorDataType() ), name + str(interpolation) )

		for i, interpolation in enumerate( self.interpolations ) :
			for j, _ in enumerate( self.names ) :
				output = q0["out"][ i * len( self.names ) + j ]
				self.assertEqual( output["interpolation"].getValue(), interpolation )

		# query with correct name and value plug type returns interpolation (non-vector data)

		q1 = GafferScene.PrimitiveVariableQuery()
		q1["scene"].setInput( scene["out"] )
		q1["location"].setValue( "/object" )

		interpolation = IECoreScene.PrimitiveVariable.Interpolation.Constant
		for ( name, plugType, defaultValue ) in zip( self.names, self.plugTypes, self.defaultValues ) :
			q1.addQuery( plugType( defaultValue=defaultValue ), name + str(interpolation) + self.nonVectorSuffix )

		for output in q1["out"] :
			self.assertEqual( output["interpolation"].getValue(), interpolation )

		# query with correct name and wrong plug type returns interpolation (vector data)

		q2 = GafferScene.PrimitiveVariableQuery()
		q2["scene"].setInput( scene["out"] )
		q2["location"].setValue( "/object" )

		for interpolation in self.interpolations :
			for name in self.names :
				q2.addQuery( Gaffer.M44fPlug( defaultValue=imath.M44f() ), name + str(interpolation) )

		for i, interpolation in enumerate( self.interpolations ) :
			for j, _ in enumerate( self.names ) :
				output = q2["out"][ i * len( self.names ) + j ]
				self.assertEqual( output["interpolation"].getValue(), interpolation )

		# query with correct name and wrong plug type returns interpolation (non-vector data)

		q3 = GafferScene.PrimitiveVariableQuery()
		q3["scene"].setInput( scene["out"] )
		q3["location"].setValue( "/object" )

		interpolation = IECoreScene.PrimitiveVariable.Interpolation.Constant
		for name in self.names :
			q3.addQuery( Gaffer.M44fPlug( defaultValue=imath.M44f() ), name + str(interpolation) + self.nonVectorSuffix )

		for i, _ in enumerate( self.names ) :
			output = q3["out"][ i ]
			self.assertEqual( output["interpolation"].getValue(), interpolation )

		# query with wrong name returns `Invalid` interpolation

		q4 = GafferScene.PrimitiveVariableQuery()
		q4["scene"].setInput( scene["out"] )
		q4["location"].setValue( "/object" )

		for ( vectorPlugType, vectorDataType ) in zip( self.vectorPlugTypes, self.vectorDataTypes ) :
			q4.addQuery( vectorPlugType( defaultValue=vectorDataType() ), "tango" )
		for ( plugType, defaultValue ) in zip( self.plugTypes, self.defaultValues ) :
			q4.addQuery( plugType( defaultValue=defaultValue ), "ratty" )

		for output in q4["out"] :
			self.assertEqual( output["interpolation"].getValue(), IECoreScene.PrimitiveVariable.Interpolation.Invalid )

	def testType( self ) :

		scene = self.makeQuad()

		# query with correct name and value plug type returns type name (vector data)

		q0 = GafferScene.PrimitiveVariableQuery()
		q0["scene"].setInput( scene["out"] )
		q0["location"].setValue( "/object" )

		for interpolation in self.interpolations :
			for ( name, vectorPlugType, vectorDataType ) in zip( self.names, self.vectorPlugTypes, self.vectorDataTypes ) :
				q0.addQuery( vectorPlugType( defaultValue=vectorDataType() ), name + str(interpolation) )

		for i, _ in enumerate( self.interpolations ) :
			for j, vectorDataType in enumerate( self.vectorDataTypes ) :
				output = q0["out"][ i * len( self.vectorDataTypes ) + j ]
				self.assertEqual( output["type"].getValue(), vectorDataType.staticTypeName() )

		# query with correct name and value plug type returns type name (non-vector data)

		q1 = GafferScene.PrimitiveVariableQuery()
		q1["scene"].setInput( scene["out"] )
		q1["location"].setValue( "/object" )

		interpolation = IECoreScene.PrimitiveVariable.Interpolation.Constant
		for ( name, plugType, defaultValue ) in zip( self.names, self.plugTypes, self.defaultValues ) :
			q1.addQuery( plugType( defaultValue=defaultValue ), name + str(interpolation) + self.nonVectorSuffix )

		for i, dataType in enumerate( self.dataTypes ) :
			output = q1["out"][ i ]
			self.assertEqual( output["type"].getValue(), dataType.staticTypeName() )

		# query with correct name and wrong plug type returns type name (vector data)

		q2 = GafferScene.PrimitiveVariableQuery()
		q2["scene"].setInput( scene["out"] )
		q2["location"].setValue( "/object" )

		for interpolation in self.interpolations :
			for name in self.names :
				q2.addQuery( Gaffer.M44fPlug( defaultValue=imath.M44f() ), name + str(interpolation) )

		for i, _ in enumerate( self.interpolations ) :
			for j, vectorDataType in enumerate( self.vectorDataTypes ) :
				output = q2["out"][ i * len( self.vectorDataTypes ) + j ]
				self.assertEqual( output["type"].getValue(), vectorDataType.staticTypeName() )

		# query with correct name and wrong plug type returns type name (non-vector data)

		q3 = GafferScene.PrimitiveVariableQuery()
		q3["scene"].setInput( scene["out"] )
		q3["location"].setValue( "/object" )

		interpolation = IECoreScene.PrimitiveVariable.Interpolation.Constant
		for name in self.names :
			q3.addQuery( Gaffer.M44fPlug( defaultValue=imath.M44f() ), name + str(interpolation) + self.nonVectorSuffix )

		for i, dataType in enumerate( self.dataTypes ) :
			output = q3["out"][ i ]
			self.assertEqual( output["type"].getValue(), dataType.staticTypeName() )

		# query with wrong name returns empty string "" type name

		q4 = GafferScene.PrimitiveVariableQuery()
		q4["scene"].setInput( scene["out"] )
		q4["location"].setValue( "/object" )

		for ( vectorPlugType, vectorDataType ) in zip( self.vectorPlugTypes, self.vectorDataTypes ) :
			q4.addQuery( vectorPlugType( defaultValue=vectorDataType() ), "ez" )
		for ( plugType, defaultValue ) in zip( self.plugTypes, self.defaultValues ) :
			q4.addQuery( plugType( defaultValue=defaultValue ), "hermit" )

		for output in q4["out"] :
			self.assertEqual( output["type"].getValue(), "" )

	def testValues( self ) :

		scene = self.makeQuad()
		mesh = scene["out"].object("/object")

		# query with correct name and value plug type returns primitive variable value (vector data)

		q0 = GafferScene.PrimitiveVariableQuery()
		q0["scene"].setInput( scene["out"] )
		q0["location"].setValue( "/object" )

		for interpolation in self.interpolations :
			for ( name, vectorPlugType, vectorDataType, defaultValue ) in zip(
				self.names,
				self.vectorPlugTypes,
				self.vectorDataTypes,
				self.defaultValues
			) :
				q0.addQuery( vectorPlugType( defaultValue=vectorDataType( [ defaultValue ] ) ), name + str(interpolation) )

		for i, interpolation in enumerate( self.interpolations ) :
			for j, ( vectorDataType, value ) in enumerate( zip( self.vectorDataTypes, self.values ) ) :
				output = q0["out"][ i * len( self.names ) + j ]
				self.assertEqual( output["value"].getValue(), vectorDataType( [ value ] * mesh.variableSize( interpolation ) ) )

		# query with correct name and value plug type returns primitive variable value (non-vector data)

		q1 = GafferScene.PrimitiveVariableQuery()
		q1["scene"].setInput( scene["out"] )
		q1["location"].setValue( "/object" )

		interpolation = IECoreScene.PrimitiveVariable.Interpolation.Constant
		for ( name, plugType, defaultValue ) in zip(
			self.names,
			self.plugTypes,
			self.defaultValues
		) :
			q1.addQuery( plugType( defaultValue=defaultValue ), name + str(interpolation) + self.nonVectorSuffix )

		for i, ( _, value ) in enumerate( zip( self.dataTypes, self.values ) ) :
			output = q1["out"][ i ]
			self.assertEqual( output["value"].getValue(), value )

		# query with wrong name returns query default value (vector data)

		q2 = GafferScene.PrimitiveVariableQuery()
		q2["scene"].setInput( scene["out"] )
		q2["location"].setValue( "/object" )

		for ( vectorPlugType, vectorDataType, defaultValue ) in zip(
			self.vectorPlugTypes,
			self.vectorDataTypes,
			self.defaultValues
		) :
			q2.addQuery( vectorPlugType( defaultValue=vectorDataType( [ defaultValue ] ) ), "hype" )

		for i, ( vectorDataType, defaultValue ) in enumerate( zip( self.vectorDataTypes, self.defaultValues ) ) :
			query = q2["queries"][ i ]
			output = q2["out"][ i ]
			self.assertEqual( output["value"].getValue(), vectorDataType( [ defaultValue ] ) )
			self.assertEqual( output["value"].getValue(), query[ "value" ].getValue() )

		# query with wrong name returns query default value (non-vector data)

		q3 = GafferScene.PrimitiveVariableQuery()
		q3["scene"].setInput( scene["out"] )
		q3["location"].setValue( "/object" )

		for ( plugType, defaultValue ) in zip(
			self.plugTypes,
			self.defaultValues
		) :
			q3.addQuery( plugType( defaultValue=defaultValue ), "ron" )

		for i, defaultValue in enumerate( self.defaultValues ) :
			query = q3["queries"][ i ]
			output = q3["out"][ i ]
			self.assertEqual( output["value"].getValue(), defaultValue )
			self.assertEqual( output["value"].getValue(), query[ "value" ].getValue() )

	def testMissingLocation( self ) :

		scene = self.makeQuad()

		q0 = GafferScene.PrimitiveVariableQuery()
		q0["scene"].setInput( scene["out"] )
		q0["location"].setValue( "/foo" )

		q0.addQuery( Gaffer.V3fVectorDataPlug( defaultValue=IECore.V3fVectorData( [ imath.V3f( 1.0, 2.0, 3.0 ) ] ) ), "P" )

		self.assertFalse( q0["out"][0]["exists"].getValue() )
		self.assertEqual( q0["out"][0]["type"].getValue(), "" )
		self.assertEqual( q0["out"][0]["interpolation"].getValue(), IECoreScene.PrimitiveVariable.Interpolation.Invalid )
		self.assertEqual( q0["out"][0]["value"].getValue(), IECore.V3fVectorData( [ imath.V3f( 1.0, 2.0, 3.0 ) ] ) )

	def testNonPrimitiveLocation( self ) :

		scene = self.makeCamera()

		q0 = GafferScene.PrimitiveVariableQuery()
		q0["scene"].setInput( scene["out"] )
		q0["location"].setValue( "/object" )

		q0.addQuery( Gaffer.V3fVectorDataPlug( defaultValue=IECore.V3fVectorData( [ imath.V3f( 1.0, 2.0, 3.0 ) ] ) ), "P" )

		self.assertFalse( q0["out"][0]["exists"].getValue() )
		self.assertEqual( q0["out"][0]["type"].getValue(), "" )
		self.assertEqual( q0["out"][0]["interpolation"].getValue(), IECoreScene.PrimitiveVariable.Interpolation.Invalid )
		self.assertEqual( q0["out"][0]["value"].getValue(), IECore.V3fVectorData( [ imath.V3f( 1.0, 2.0, 3.0 ) ] ) )

	def testSerialisation( self ) :

		scene = self.makeQuad()
		mesh = scene["out"].object("/object")

		qv = GafferScene.PrimitiveVariableQuery( "qv" )
		qv["scene"].setInput( scene["out"] )
		qv["location"].setValue( "/object" )

		qnv = GafferScene.PrimitiveVariableQuery( "qnv" )
		qnv["scene"].setInput( scene["out"] )
		qnv["location"].setValue( "/object" )

		# add queries (vector data)

		for interpolation in self.interpolations :
			for ( name, vectorPlugType, vectorDataType, defaultValue ) in zip(
				self.names,
				self.vectorPlugTypes,
				self.vectorDataTypes,
				self.defaultValues
			) :
				qv.addQuery( vectorPlugType( defaultValue=vectorDataType( [ defaultValue ] ) ), name + str(interpolation) )

		# check queries (vector data)

		for i, interpolation in enumerate( self.interpolations ) :
			for j, ( vectorDataType, value ) in enumerate( zip( self.vectorDataTypes, self.values ) ) :
				output = qv["out"][ i * len( self.names ) + j ]
				self.assertTrue( output["exists"].getValue() )
				self.assertEqual( output["interpolation"].getValue(), interpolation )
				self.assertEqual( output["type"].getValue(), vectorDataType.staticTypeName() )
				self.assertEqual( output["value"].getValue(), vectorDataType( [ value ] * mesh.variableSize( interpolation ) ) )

		# add queries (non-vector data)

		interpolation = IECoreScene.PrimitiveVariable.Interpolation.Constant
		for ( name, plugType, defaultValue ) in zip(
			self.names,
			self.plugTypes,
			self.defaultValues
		) :
			qnv.addQuery( plugType( defaultValue=defaultValue ), name + str(interpolation) + self.nonVectorSuffix )

		# check queries (non-vector data)

		for i, ( dataType, value ) in enumerate( zip( self.dataTypes, self.values ) ) :
			output = qnv["out"][ i ]
			self.assertTrue( output["exists"].getValue() )
			self.assertEqual( output["interpolation"].getValue(), interpolation )
			self.assertEqual( output["type"].getValue(), dataType.staticTypeName() )
			self.assertEqual( output["value"].getValue(), value )

		# add nodes to script node

		scriptNode = Gaffer.ScriptNode()
		scriptNode.addChild( scene )
		scriptNode.addChild( qnv )
		scriptNode.addChild( qv )

		# check queries

		for i, interpolation in enumerate( self.interpolations ) :
			for j, ( vectorDataType, value ) in enumerate( zip( self.vectorDataTypes, self.values ) ) :
				output = scriptNode["qv"]["out"][ i * len( self.names ) + j ]
				self.assertTrue( output["exists"].getValue() )
				self.assertEqual( output["interpolation"].getValue(), interpolation )
				self.assertEqual( output["type"].getValue(), vectorDataType.staticTypeName() )
				self.assertEqual( output["value"].getValue(), vectorDataType( [ value ] * mesh.variableSize( interpolation ) ) )

		interpolation = IECoreScene.PrimitiveVariable.Interpolation.Constant
		for i, ( dataType, value ) in enumerate( zip( self.dataTypes, self.values ) ) :
			output = scriptNode["qnv"]["out"][ i ]
			self.assertTrue( output["exists"].getValue() )
			self.assertEqual( output["interpolation"].getValue(), interpolation )
			self.assertEqual( output["type"].getValue(), dataType.staticTypeName() )
			self.assertEqual( output["value"].getValue(), value )

		# round trip serialise

		serialised = scriptNode.serialise()

		scriptNode = Gaffer.ScriptNode()
		scriptNode.execute( serialised )

		# check queries

		for i, interpolation in enumerate( self.interpolations ) :
			for j, ( vectorDataType, value ) in enumerate( zip( self.vectorDataTypes, self.values ) ) :
				output = scriptNode["qv"]["out"][ i * len( self.names ) + j ]
				self.assertTrue( output["exists"].getValue() )
				self.assertEqual( output["interpolation"].getValue(), interpolation )
				self.assertEqual( output["type"].getValue(), vectorDataType.staticTypeName() )
				self.assertEqual( output["value"].getValue(), vectorDataType( [ value ] * mesh.variableSize( interpolation ) ) )

		interpolation = IECoreScene.PrimitiveVariable.Interpolation.Constant
		for i, ( dataType, value ) in enumerate( zip( self.dataTypes, self.values ) ) :
			output = scriptNode["qnv"]["out"][ i ]
			self.assertTrue( output["exists"].getValue() )
			self.assertEqual( output["interpolation"].getValue(), interpolation )
			self.assertEqual( output["type"].getValue(), dataType.staticTypeName() )
			self.assertEqual( output["value"].getValue(), value )

	def testArrayScalarConversion( self ) :

		cube = GafferScene.Cube()

		cubeFilter = GafferScene.PathFilter()
		cubeFilter["paths"].setValue( IECore.StringVectorData( [ "/cube" ] ) )

		primitiveVariables = GafferScene.PrimitiveVariables()
		primitiveVariables["in"].setInput( cube["out"] )
		primitiveVariables["filter"].setInput( cubeFilter["out"] )

		primitiveVariables["primitiveVariables"].addChild( Gaffer.NameValuePlug( "testLengthZero", IECore.IntVectorData() ) )
		primitiveVariables["primitiveVariables"].addChild( Gaffer.NameValuePlug( "testLengthOne", IECore.IntVectorData( [ 2 ] ) ) )
		primitiveVariables["primitiveVariables"].addChild( Gaffer.NameValuePlug( "testLengthTwo", IECore.IntVectorData( [ 3, 3 ] ) ) )

		query = GafferScene.PrimitiveVariableQuery()
		query["scene"].setInput( primitiveVariables["out"] )
		query["location"].setValue( "/cube" )
		query.addQuery( Gaffer.IntPlug( defaultValue = -1 ), "testLengthZero" )

		self.assertEqual( query["out"][0]["exists"].getValue(), True )
		self.assertTrue( query["out"][0]["value"].getValue(), -1 )

		query["queries"][0]["name"].setValue( "testLengthOne" )
		self.assertEqual( query["out"][0]["exists"].getValue(), True )
		self.assertTrue( query["out"][0]["value"].getValue(), 2 )

		query["queries"][0]["name"].setValue( "testLengthTwo" )
		self.assertEqual( query["out"][0]["exists"].getValue(), True )
		self.assertTrue( query["out"][0]["value"].getValue(), -1 )

if __name__ == "__main__":
	unittest.main()
