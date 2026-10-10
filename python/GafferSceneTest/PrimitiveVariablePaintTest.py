##########################################################################
#
#  Copyright (c) 2026, Image Engine Design Inc. All rights reserved.
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
import math

import IECore
import IECoreScene

import Gaffer
import GafferTest
import GafferScene
import GafferSceneTest

class PrimitiveVariablePaintTest( GafferSceneTest.SceneTestCase ) :

	def testBasics( self ):
		plane = GafferScene.Plane()
		plane["divisions"].setValue( imath.V2i( 2, 2 ) )

		planeFilter = GafferScene.PathFilter()
		planeFilter["paths"].setValue( IECore.StringVectorData( [ '/plane' ] ) )

		shufflePrimitiveVariables = GafferScene.ShufflePrimitiveVariables()
		shufflePrimitiveVariables["shuffles"].addChild( Gaffer.ShufflePlug( "shuffle0" ) )
		shufflePrimitiveVariables["in"].setInput( plane["out"] )
		shufflePrimitiveVariables["filter"].setInput( planeFilter["out"] )
		shufflePrimitiveVariables["shuffles"]["shuffle0"]["source"].setValue( 'uv' )
		shufflePrimitiveVariables["shuffles"]["shuffle0"]["destination"].setValue( 'test' )

		resamplePrimitiveVariables = GafferScene.ResamplePrimitiveVariables()
		resamplePrimitiveVariables["in"].setInput( shufflePrimitiveVariables["out"] )
		resamplePrimitiveVariables["filter"].setInput( planeFilter["out"] )
		resamplePrimitiveVariables["names"].setValue( 'test' )

		typeFloat = GafferScene.PrimitiveVariableType()
		typeFloat["in"].setInput( resamplePrimitiveVariables["out"] )
		typeFloat["filter"].setInput( planeFilter["out"] )
		typeFloat["primitiveVariables"].setValue( 'test' )
		typeFloat["type"]["enabled"].setValue( True )

		primitiveVariablePaint = GafferScene.PrimitiveVariablePaint()
		primitiveVariablePaint["in"].setInput( typeFloat["out"] )
		primitiveVariablePaint["filter"].setInput( planeFilter["out"] )
		primitiveVariablePaint["primitiveVariables"].addChild( Gaffer.NameValuePlug( "test", Gaffer.ObjectPlug( "value", defaultValue = IECore.NullObject(), ), True, "member0" ) )

		self.assertEqual(
			primitiveVariablePaint["out"].object( "/plane" )["test"],
			IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex,
				IECore.FloatVectorData( [0, 0.5, 1, 0, 0.5, 1, 0, 0.5, 1] )
			)
		)

		primitiveVariablePaint["primitiveVariables"]["member0"]["value"].setValue(
			GafferScene.PrimitiveVariablePaint.PaintOperation(
				IECore.FloatVectorData( [ 10, 10, 10, 10, 10, 10, 10, 10, 10 ] ),
				IECore.FloatVectorData( [ 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5 ] )
			)
		)

		self.assertEqual(
			primitiveVariablePaint["out"].object( "/plane" )["test"],
			IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex,
				IECore.FloatVectorData( [10, 10.25, 10.5, 10, 10.25, 10.5, 10, 10.25, 10.5 ] )
			)
		)

		primitiveVariablePaint["primitiveVariables"]["member0"]["value"].setValue(
			GafferScene.PrimitiveVariablePaint.PaintOperation(
				IECore.FloatVectorData( [ 10, 10, 10, 10, 10, 10, 10, 10, 10 ] ),
				IECore.FloatVectorData( [ 0.5, 0.5, 0.5, 0, 0, 0, 0, 0, 0 ] )
			)
		)

		self.assertEqual(
			primitiveVariablePaint["out"].object( "/plane" )["test"],
			IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex,
				IECore.FloatVectorData( [10, 10.25, 10.5, 10, 10.5, 11, 10, 10.5, 11 ] )
			)
		)

		# No opacity just overwrites
		primitiveVariablePaint["primitiveVariables"]["member0"]["value"].setValue(
			GafferScene.PrimitiveVariablePaint.PaintOperation(
				IECore.FloatVectorData( [ 1, 2, 3, 4, 5, 6, 7, 8, 9 ] )
			)
		)

		self.assertEqual(
			primitiveVariablePaint["out"].object( "/plane" )["test"],
			IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex,
				IECore.FloatVectorData( [ 1, 2, 3, 4, 5, 6, 7, 8, 9 ] )
			)
		)

	def testErrors( self ):
		plane = GafferScene.Plane()

		planeFilter = GafferScene.PathFilter()
		planeFilter["paths"].setValue( IECore.StringVectorData( [ '/plane' ] ) )

		primitiveVariablePaint = GafferScene.PrimitiveVariablePaint()
		primitiveVariablePaint["in"].setInput( plane["out"] )
		primitiveVariablePaint["filter"].setInput( planeFilter["out"] )
		primitiveVariablePaint["primitiveVariables"].addChild( Gaffer.NameValuePlug( "P", Gaffer.ObjectPlug( "value", defaultValue = IECore.NullObject(), ), True, "member0" ) )

		self.assertEqual(
			primitiveVariablePaint["out"].object( "/plane" )["P"],
			IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex,
				IECore.V3fVectorData( [
					imath.V3f( -0.5, -0.5, 0 ), imath.V3f( 0.5, -0.5, 0 ),
					imath.V3f( -0.5, 0.5, 0 ), imath.V3f( 0.5, 0.5, 0 )
				], IECore.GeometricData.Interpretation.Point )
			)
		)

		primitiveVariablePaint["primitiveVariables"]["member0"]["value"].setValue(
			GafferScene.PrimitiveVariablePaint.PaintOperation(
				IECore.V3fVectorData( [ imath.V3f( 10 ) ] * 4 ),
				IECore.FloatVectorData( [ 0, 0, 1, 1 ] )
			)
		)

		self.assertEqual(
			primitiveVariablePaint["out"].object( "/plane" )["P"],
			IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex,
				IECore.V3fVectorData( [
					imath.V3f( 9.5, 9.5, 10 ), imath.V3f( 10.5, 9.5, 10 ),
					imath.V3f( 10 ), imath.V3f( 10 )
				], IECore.GeometricData.Interpretation.Point )
			)
		)

		primitiveVariablePaint["primitiveVariables"]["member0"]["value"].setValue(
			IECore.StringData( "Not a PaintOperation" )
		)

		with self.assertRaisesRegex( Gaffer.ProcessException,
			"Paint value must be of type PaintOperation, not StringData"
		) :
			primitiveVariablePaint["out"].object( "/plane" )

		primitiveVariablePaint["primitiveVariables"]["member0"]["value"].setValue(
			GafferScene.PrimitiveVariablePaint.PaintOperation(
				IECore.FloatVectorData( [ 0 ] ),
			)
		)

		with self.assertRaisesRegex( Gaffer.ProcessException,
			"Invalid paint for variable P at location /plane : Cannot apply PaintOperation with value type FloatVectorData to variable of type V3fVectorData"
		) :
			primitiveVariablePaint["out"].object( "/plane" )

		primitiveVariablePaint["primitiveVariables"]["member0"]["value"].setValue(
			GafferScene.PrimitiveVariablePaint.PaintOperation(
				IECore.V3fVectorData( [] ),
			)
		)

		with self.assertRaisesRegex( Gaffer.ProcessException,
			"Invalid paint for variable P at location /plane : Value size 0 does not match 4"
		) :
			primitiveVariablePaint["out"].object( "/plane" )

		primitiveVariablePaint["primitiveVariables"]["member0"]["value"].setValue(
			GafferScene.PrimitiveVariablePaint.PaintOperation(
				IECore.V3fVectorData( [ imath.V3f( 0 ) ] * 4 ),
				IECore.FloatVectorData( [ 0 ] * 10 )
			)
		)

		with self.assertRaisesRegex( Gaffer.ProcessException,
			"Invalid paint for variable P at location /plane : Opacity size 10 does not match 4"
		) :
			primitiveVariablePaint["out"].object( "/plane" )

	def testIndices( self ):
		plane = GafferScene.Plane()
		plane["divisions"].setValue( imath.V2i( 2, 2 ) )

		planeFilter = GafferScene.PathFilter()
		planeFilter["paths"].setValue( IECore.StringVectorData( [ '/plane' ] ) )

		shufflePrimitiveVariables = GafferScene.ShufflePrimitiveVariables()
		shufflePrimitiveVariables["shuffles"].addChild( Gaffer.ShufflePlug( "shuffle0" ) )
		shufflePrimitiveVariables["in"].setInput( plane["out"] )
		shufflePrimitiveVariables["filter"].setInput( planeFilter["out"] )
		shufflePrimitiveVariables["shuffles"]["shuffle0"]["source"].setValue( 'uv' )
		shufflePrimitiveVariables["shuffles"]["shuffle0"]["destination"].setValue( 'test' )

		resamplePrimitiveVariables = GafferScene.ResamplePrimitiveVariables()
		resamplePrimitiveVariables["in"].setInput( shufflePrimitiveVariables["out"] )
		resamplePrimitiveVariables["filter"].setInput( planeFilter["out"] )
		resamplePrimitiveVariables["names"].setValue( 'test' )

		typeFloat = GafferScene.PrimitiveVariableType()
		typeFloat["in"].setInput( resamplePrimitiveVariables["out"] )
		typeFloat["filter"].setInput( planeFilter["out"] )
		typeFloat["primitiveVariables"].setValue( 'test' )
		typeFloat["type"]["enabled"].setValue( True )

		primitiveVariablePaint = GafferScene.PrimitiveVariablePaint()
		primitiveVariablePaint["in"].setInput( typeFloat["out"] )
		primitiveVariablePaint["filter"].setInput( planeFilter["out"] )
		primitiveVariablePaint["primitiveVariables"].addChild( Gaffer.NameValuePlug( "test", Gaffer.ObjectPlug( "value", defaultValue = IECore.NullObject(), ), True, "member0" ) )


		# Target just two elements using indices
		primitiveVariablePaint["primitiveVariables"]["member0"]["value"].setValue(
			GafferScene.PrimitiveVariablePaint.PaintOperation(
				IECore.FloatVectorData( [ 10, 100 ] ),
				IECore.FloatVectorData( [ 0.5, 0.75 ] ),
				IECore.IntVectorData( [ 1, 4 ] )
			)
		)

		self.assertEqual(
			primitiveVariablePaint["out"].object( "/plane" )["test"],
			IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex,
				IECore.FloatVectorData( [0, 10.25, 1, 0, 100.125, 1, 0, 0.5, 1] )
			)
		)

		# Without opacity, we just overwrite
		primitiveVariablePaint["primitiveVariables"]["member0"]["value"].setValue(
			GafferScene.PrimitiveVariablePaint.PaintOperation(
				IECore.FloatVectorData( [ 10, 100 ] ),
				None,
				IECore.IntVectorData( [ 4, 7 ] )
			)
		)

		self.assertEqual(
			primitiveVariablePaint["out"].object( "/plane" )["test"],
			IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex,
				IECore.FloatVectorData( [0, 0.5, 1, 0, 10, 1, 0, 100, 1] )
			)
		)

		# Now test the various errors

		primitiveVariablePaint["primitiveVariables"]["member0"]["value"].setValue(
			GafferScene.PrimitiveVariablePaint.PaintOperation(
				IECore.FloatVectorData( [ 10, 100 ] ),
				None,
				IECore.IntVectorData( [ 104, 107 ] )
			)
		)

		with self.assertRaisesRegex( Gaffer.ProcessException,
			"Invalid paint for variable test at location /plane : Invalid index 104 in variable size 9"
		) :
			primitiveVariablePaint["out"].object( "/plane" )

		primitiveVariablePaint["primitiveVariables"]["member0"]["value"].setValue(
			GafferScene.PrimitiveVariablePaint.PaintOperation(
				IECore.FloatVectorData( [ 10, 100 ] ),
				IECore.FloatVectorData( [ 0.5, 0.75 ] ),
				IECore.IntVectorData( [ 104, 107 ] )
			)
		)

		with self.assertRaisesRegex( Gaffer.ProcessException,
			"Invalid paint for variable test at location /plane : Invalid index 104 in variable size 9"
		) :
			primitiveVariablePaint["out"].object( "/plane" )

		primitiveVariablePaint["primitiveVariables"]["member0"]["value"].setValue(
			GafferScene.PrimitiveVariablePaint.PaintOperation(
				IECore.FloatVectorData( [ 10, 100, 1000 ] ),
				None,
				IECore.IntVectorData( [ 4, 7 ] )
			)
		)

		with self.assertRaisesRegex( Gaffer.ProcessException,
			"Invalid paint for variable test at location /plane : Value size 3 does not match indices size 2"
		) :
			primitiveVariablePaint["out"].object( "/plane" )

		primitiveVariablePaint["primitiveVariables"]["member0"]["value"].setValue(
			GafferScene.PrimitiveVariablePaint.PaintOperation(
				IECore.FloatVectorData( [ 10, 10 ] ),
				IECore.FloatVectorData( [ 0, 0, 0 ] ),
				IECore.IntVectorData( [ 4, 7 ] )
			)
		)

		with self.assertRaisesRegex( Gaffer.ProcessException,
			"Invalid paint for variable test at location /plane : Opacity size 3 does not match indices size 2"
		) :
			primitiveVariablePaint["out"].object( "/plane" )


	def testMultipleLocationsAndPrimVars( self ) :

		plane = GafferScene.Plane()
		plane["divisions"].setValue( imath.V2i( 2, 2 ) )

		planeFilter = GafferScene.PathFilter()
		planeFilter["paths"].setValue( IECore.StringVectorData( [ '/plane' ] ) )

		shufflePrimitiveVariables = GafferScene.ShufflePrimitiveVariables()
		shufflePrimitiveVariables["shuffles"].addChild( Gaffer.ShufflePlug( "shuffle0" ) )
		shufflePrimitiveVariables["in"].setInput( plane["out"] )
		shufflePrimitiveVariables["filter"].setInput( planeFilter["out"] )
		shufflePrimitiveVariables["shuffles"]["shuffle0"]["source"].setValue( 'uv' )
		shufflePrimitiveVariables["shuffles"]["shuffle0"]["destination"].setValue( 'test' )

		resamplePrimitiveVariables = GafferScene.ResamplePrimitiveVariables()
		resamplePrimitiveVariables["in"].setInput( shufflePrimitiveVariables["out"] )
		resamplePrimitiveVariables["filter"].setInput( planeFilter["out"] )
		resamplePrimitiveVariables["names"].setValue( 'test' )

		typeFloat = GafferScene.PrimitiveVariableType()
		typeFloat["in"].setInput( resamplePrimitiveVariables["out"] )
		typeFloat["filter"].setInput( planeFilter["out"] )
		typeFloat["primitiveVariables"].setValue( 'test' )
		typeFloat["type"]["enabled"].setValue( True )

		typeColor3f = GafferScene.PrimitiveVariableType()
		typeColor3f["in"].setInput( resamplePrimitiveVariables["out"] )
		typeColor3f["filter"].setInput( planeFilter["out"] )
		typeColor3f["primitiveVariables"].setValue( 'test' )
		typeColor3f["type"]["enabled"].setValue( True )
		typeColor3f["type"]["value"].setValue( 14 )

		planeWithoutVar = GafferScene.Plane()
		planeWithoutVar["divisions"].setValue( imath.V2i( 2, 2 ) )

		parent = GafferScene.Parent()
		parent["parent"].setValue( '/' )
		parent["in"].setInput( typeFloat["out"] )
		parent["children"][0].setInput( typeColor3f["out"] )
		parent["children"][1].setInput( planeWithoutVar["out"] )

		allFilter = GafferScene.PathFilter()
		allFilter["paths"].setValue( IECore.StringVectorData( [ '/plane', '/plane1', '/plane2' ] ) )


		primitiveVariablePaint = GafferScene.PrimitiveVariablePaint()
		primitiveVariablePaint["in"].setInput( parent["out"] )
		primitiveVariablePaint["filter"].setInput( allFilter["out"] )
		primitiveVariablePaint["primitiveVariables"].addChild( Gaffer.NameValuePlug( "test", Gaffer.ObjectPlug( "value", defaultValue = IECore.NullObject(), ), True, "member0" ) )

		self.assertEqual(
			primitiveVariablePaint["out"].object( "/plane" )["test"],
			IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex,
				IECore.FloatVectorData( [0, 0.5, 1, 0, 0.5, 1, 0, 0.5, 1] )
			)
		)

		primitiveVariablePaint["primitiveVariables"]["member0"]["value"].setValue(
			GafferScene.PrimitiveVariablePaint.PaintOperation(
				IECore.FloatVectorData( [ 10, 10, 10, 10, 0, 0, 0, 0, 0 ] ),
				IECore.FloatVectorData( [ 0.9, 0.9, 0.9, 0.9, 0, 0, 0, 0, 0 ] )
			)
		)

		# Check float operation applied to float
		self.assertEqual(
			primitiveVariablePaint["out"].object( "/plane" )["test"],
			IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex,
				IECore.FloatVectorData( [10, 10.05, 10.1, 10, 0.5, 1, 0, 0.5, 1] )
			)
		)

		# Check float operation applied to Color3f
		with self.assertRaisesRegex( Gaffer.ProcessException,
			"Invalid paint for variable test at location /plane1 : "
			"Cannot apply PaintOperation with value type FloatVectorData to variable of type Color3fVectorData"
		) :
			primitiveVariablePaint["out"].object( "/plane1" )

		# Check float operation applied to missing primvar
		self.assertEqual(
			primitiveVariablePaint["out"].object( "/plane2" )["test"],
			IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex,
				IECore.FloatVectorData( [10, 10, 10, 10, 0, 0, 0, 0, 0] )
			)
		)

		# Set up a spreadsheet that applies an appropriate value to each location
		spreadsheet = Gaffer.Spreadsheet()
		spreadsheet["rows"].addColumn( Gaffer.ObjectPlug( "testValue", defaultValue = IECore.NullObject(), ) )
		spreadsheet["rows"].addRows( 3 )

		spreadsheet["selector"].setValue( '${scene:path}' )
		spreadsheet["rows"][1]["name"].setValue( '/plane' )
		spreadsheet["rows"][2]["name"].setValue( '/plane1' )
		spreadsheet["rows"][3]["name"].setValue( '/plane2' )

		spreadsheet["rows"][1]["cells"]["testValue"]["value"].setValue(
			GafferScene.PrimitiveVariablePaint.PaintOperation(
				IECore.FloatVectorData( [ 20, 20, 20, 20, 0, 0, 0, 0, 0 ] ),
				IECore.FloatVectorData( [ 0.9, 0.9, 0.9, 0.9, 0, 0, 0, 0, 0 ] )
			)
		)

		spreadsheet["rows"][2]["cells"]["testValue"]["value"].setValue(
			GafferScene.PrimitiveVariablePaint.PaintOperation(
				IECore.Color3fVectorData( [ imath.Color3f(i) for i in [ 20, 20, 20, 20, 0, 0, 0, 0, 0 ] ] ),
				IECore.FloatVectorData( [ 0.9, 0.9, 0.9, 0.9, 0, 0, 0, 0, 0 ] )
			)
		)

		spreadsheet["rows"][3]["cells"]["testValue"]["value"].setValue(
			spreadsheet["rows"][2]["cells"]["testValue"]["value"].getValue()
		)

		primitiveVariablePaint["primitiveVariables"]["member0"]["value"].setInput( spreadsheet["out"]["testValue"] )

		# Check we get the right result for each location using the correct spreadsheet cell

		expected1 = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.FloatVectorData( [20, 20.05, 20.1, 20, 0.5, 1, 0, 0.5, 1] )
		)
		self.assertEqual( primitiveVariablePaint["out"].object( "/plane" )["test"], expected1 )

		expected2 = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.Color3fVectorData( [
				imath.Color3f( 20, 20, 20 ), imath.Color3f( 20.05, 20, 20 ), imath.Color3f( 20.1, 20, 20 ),
				imath.Color3f( 20, 20.05, 20 ), imath.Color3f( 0.5, 0.5, 0 ), imath.Color3f( 1, 0.5, 0 ),
				imath.Color3f( 0, 1, 0 ), imath.Color3f( 0.5, 1, 0 ), imath.Color3f( 1, 1, 0 )
			] )
		)
		self.assertEqual( primitiveVariablePaint["out"].object( "/plane1" )["test"], expected2 )

		expected3 = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.Color3fVectorData( [
				imath.Color3f( 20 ), imath.Color3f( 20 ), imath.Color3f( 20 ),
				imath.Color3f( 20 ), imath.Color3f( 0 ), imath.Color3f( 0 ),
				imath.Color3f( 0 ), imath.Color3f( 0 ), imath.Color3f( 0 )
			] )
		)
		self.assertEqual( primitiveVariablePaint["out"].object( "/plane2" )["test"], expected3 )

		# Add a second var to all locations
		primitiveVariablePaint["primitiveVariables"].addChild( Gaffer.NameValuePlug( "secondVar", Gaffer.ObjectPlug( "value", defaultValue = IECore.NullObject(), ), True, "member1" ) )
		secondVarValue = IECore.FloatVectorData( [ 1, 2, 3, 4, 5, 6, 7, 8, 9 ] )
		primitiveVariablePaint["primitiveVariables"]["member1"]["value"].setValue(
			GafferScene.PrimitiveVariablePaint.PaintOperation(
				secondVarValue,
				IECore.FloatVectorData( [ 0.5 ] * 9 )
			)
		)

		secondVarPrimVar = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			secondVarValue
        )

		self.assertEqual( primitiveVariablePaint["out"].object( "/plane" )["test"], expected1 )
		self.assertEqual( primitiveVariablePaint["out"].object( "/plane" )["secondVar"], secondVarPrimVar )
		self.assertEqual( primitiveVariablePaint["out"].object( "/plane1" )["test"], expected2 )
		self.assertEqual( primitiveVariablePaint["out"].object( "/plane1" )["secondVar"], secondVarPrimVar )
		self.assertEqual( primitiveVariablePaint["out"].object( "/plane2" )["test"], expected3 )
		self.assertEqual( primitiveVariablePaint["out"].object( "/plane2" )["secondVar"], secondVarPrimVar )
