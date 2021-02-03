##########################################################################
#
#  Copyright (c) 2020, Hypothetical Inc. All rights reserved.
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
import os

import IECore
import IECoreScene

import Gaffer
import GafferTest
import GafferScene
import GafferSceneTest
import GafferImage

class ImageSamplerTest( GafferSceneTest.SceneTestCase ) :

	def checkVector( self, outMesh, primVar ) :
		self.assertTrue( 
			imath.V3f( 1.0, 0.0, 0.0 ).equalWithAbsError( 
				outMesh[primVar].data[0],
				.000001
			)
		)
		self.assertTrue( 
			imath.V3f( 0.0, 1.0, 0.0 ).equalWithAbsError(
				outMesh[primVar].data[1],
				.000001
			)
		)
		self.assertTrue( 
			imath.V3f( 0.0, 0.0, 1.0 ).equalWithAbsError(
				outMesh[primVar].data[5],
				.000001
			)
		)

	def getTestRamp( self ) :

		# Setup the ramp for convenient color interpolation.
		# The ramp goes from pure red to green (at halfway)
		# to blue across the u axis, so samples on the v 
		# axis are identical.

		ramp = GafferImage.Ramp()
		ramp["format"].setValue( GafferImage.Format( 9, 9, 1. ) )
		ramp["startPosition"].setValue( imath.V2f( 0, 0 ) )
		ramp["endPosition"].setValue( imath.V2f( 9, 0 ) )
		ramp["ramp"]["interpolation"].setValue( 0 )	# Linear interpolation

		ramp["ramp"]["p0"]["x"].setValue( ( 1.0 / 9.0 / 2.0 ) )
		ramp["ramp"]["p0"]["y"].setValue( imath.Color4f( 1.0, 0.0, 0.0, 0.0 ) )
		ramp["ramp"]["p1"]["x"].setValue( 1.0 - ( 1.0 / 9.0 / 2.0 ) )
		ramp["ramp"]["p1"]["y"].setValue( imath.Color4f( 0.0, 0.0, 1.0, 0.0 ) )
		ramp["ramp"].addChild( Gaffer.ValuePlug( "p2" ) )
		ramp["ramp"]["p2"].addChild( Gaffer.FloatPlug( "x", defaultValue = 0.5 ) )
		ramp["ramp"]["p2"].addChild( Gaffer.Color4fPlug( "y", defaultValue = imath.Color4f( 0.0, 1.0, 0.0, 0.0 ) ) )

		return ramp

	def test( self ) :

		# Sample from an image ramp onto a plane
		# checking that values are as expected.

		plane = GafferScene.Plane()
		plane["dimensions"].setValue( imath.V2f( 2 ) )
		plane["divisions"].setValue( imath.V2i( 2 ) )

		planeFilter = GafferScene.PathFilter()
		planeFilter["paths"].setValue( IECore.StringVectorData( ["/plane" ] ) )

		ramp = self.getTestRamp()

		imageSampler = GafferScene.ImageSampler()
		imageSampler["in"].setInput( plane["out"] )
		imageSampler["filter"].setInput( planeFilter["out"] )
		imageSampler["image"].setInput( ramp["out"] )
		imageSampler["uvSet"].setValue( "uv" )

		# Test pass through
		self.assertScenesEqual( imageSampler["out"], plane["out"] )

		# Test Color
		imageSampler.addPrimitiveVariableSampler( "Cs", IECore.GeometricData.Interpretation.Color, "R G B")

		self.assertSceneValid( imageSampler["out"] )

		inMesh = imageSampler["in"].object( "/plane" )
		outMesh = imageSampler["out"].object( "/plane" )
		self.assertTrue( set( outMesh.keys() ), set( inMesh.keys() + ["Cs" ] ) )
		self.assertTrue( 
			imath.Color3f( 1.0, 0.0, 0.0 ).equalWithAbsError( 
				outMesh["Cs"].data[0],
				.000001
			)
		)
		self.assertTrue( 
			imath.Color3f( 0.0, 1.0, 0.0 ).equalWithAbsError(
				outMesh["Cs"].data[1],
				.000001
			)
		)
		self.assertTrue( 
			imath.Color3f( 0.0, 0.0, 1.0 ).equalWithAbsError(
				outMesh["Cs"].data[5],
				.000001
			)
		)

		# Test Normal
		imageSampler.addPrimitiveVariableSampler( "N", IECore.GeometricData.Interpretation.Normal, "R G B")
		outMesh = imageSampler["out"].object( "/plane" )
		self.checkVector( outMesh, "N" )

		# Test Point
		imageSampler.addPrimitiveVariableSampler( "P", IECore.GeometricData.Interpretation.Point, "R G B")
		outMesh = imageSampler["out"].object( "/plane" )
		self.checkVector( outMesh, "P" )

		# Test UV
		imageSampler.addPrimitiveVariableSampler( "uv", IECore.GeometricData.Interpretation.UV, "R G")
		outMesh = imageSampler["out"].object( "/plane" )
		self.assertTrue( 
			imath.V2f( 1.0, 0.0 ).equalWithAbsError( 
				outMesh["uv"].data[0],
				.000001
			)
		)
		self.assertTrue( 
			imath.V2f( 0.0, 1.0 ).equalWithAbsError(
				outMesh["uv"].data[1],
				.000001
			)
		)
		self.assertTrue( 
			imath.V2f( 0.0, 0.0 ).equalWithAbsError(
				outMesh["uv"].data[5],
				.000001
			)
		)

		# Test Vector
		imageSampler.addPrimitiveVariableSampler( "velocity", IECore.GeometricData.Interpretation.Vector, "R G B")
		outMesh = imageSampler["out"].object( "/plane" )
		self.checkVector( outMesh, "velocity" )

		# Test None
		imageSampler.addPrimitiveVariableSampler( "test", IECore.GeometricData.Interpretation.None, "R")
		outMesh = imageSampler["out"].object( "/plane" )
		self.assertAlmostEqual( 1.0, outMesh["test"].data[0], places = 5 )
		self.assertAlmostEqual( 0.0, outMesh["test"].data[1], places = 5 )
		self.assertAlmostEqual( 0.0, outMesh["test"].data[5], places = 5 )

	def testUVClamp( self ) :
		pointsPrimitive = IECoreScene.PointsPrimitive(
			IECore.V3fVectorData( [imath.V3f( 0 ) ] * 3 )
		)

		pointsPrimitive["uv"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.V2fVectorData(
				[
					imath.V2f( -0.1, 0.0 ),
					imath.V2f( 0.5, 0.0 ),
					imath.V2f( 1.1, 0.0 ),
				],
				IECore.GeometricData.Interpretation.UV
			),
		)

		points = GafferScene.ObjectToScene()
		points["object"].setValue( pointsPrimitive )

		pointsFilter = GafferScene.PathFilter()
		pointsFilter["paths"].setValue( IECore.StringVectorData( ["/object"] ) )

		ramp = self.getTestRamp()

		imageSampler = GafferScene.ImageSampler()
		imageSampler["in"].setInput( points["out"] )
		imageSampler["filter"].setInput( pointsFilter["out"] )
		imageSampler["image"].setInput( ramp["out"] )
		imageSampler["uvSet"].setValue( "uv" )
		imageSampler.addPrimitiveVariableSampler( "Cs", IECore.GeometricData.Interpretation.Color, "R G B")

		self.assertSceneValid( imageSampler["out"] )

		inMesh = imageSampler["in"].object( "/object" )
		outMesh = imageSampler["out"].object( "/object" )
		self.assertTrue( set( outMesh.keys() ), set( inMesh.keys() + ["Cs"] ) )
		self.assertTrue( 
			imath.Color3f( 1.0, 0.0, 0.0 ).equalWithAbsError( 
				outMesh["Cs"].data[0],
				.000001
			)
		)
		self.assertTrue( 
			imath.Color3f( 0.0, 1.0, 0.0 ).equalWithAbsError(
				outMesh["Cs"].data[1],
				.000001
			)
		)
		self.assertTrue( 
			imath.Color3f( 0.0, 0.0, 1.0 ).equalWithAbsError(
				outMesh["Cs"].data[2],
				.000001
			)
		)

	def testUVTile( self ) :
		pointsPrimitive = IECoreScene.PointsPrimitive(
			IECore.V3fVectorData( [imath.V3f( 0 ) ] * 3 )
		)

		pointsPrimitive["uv"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.V2fVectorData(
				[
					imath.V2f( -1.0 / 8.0, 0.0 ),
					imath.V2f( 0.5, 0.0 ),
					imath.V2f( 9.0 / 8.0, 0.0 ),
				],
				IECore.GeometricData.Interpretation.UV
			),
		)

		points = GafferScene.ObjectToScene()
		points["object"].setValue( pointsPrimitive )

		pointsFilter = GafferScene.PathFilter()
		pointsFilter["paths" ].setValue( IECore.StringVectorData( ["/object"] ) )

		ramp = self.getTestRamp()

		imageSampler = GafferScene.ImageSampler()
		imageSampler["in"].setInput( points["out"] )
		imageSampler["filter"].setInput( pointsFilter["out"] )
		imageSampler["image"].setInput( ramp["out"] )
		imageSampler["uvSet"].setValue( "uv" )
		imageSampler.addPrimitiveVariableSampler( "Cs", IECore.GeometricData.Interpretation.Color, "R G B")
		imageSampler["uvBoundsMode"].setValue( GafferScene.ImageSampler.UVBoundsMode.Tile )

		self.assertSceneValid( imageSampler["out"] )

		inMesh = imageSampler["in"].object( "/object" )
		outMesh = imageSampler["out"].object( "/object" )
		self.assertTrue( set( outMesh.keys() ), set( inMesh.keys() + ["Cs" ] ) )
		self.assertTrue( 
			imath.Color3f( 0, 0.25, 0.75 ).equalWithAbsError( 
				outMesh["Cs"].data[0],
				.000001
			)
		)
		self.assertTrue( 
			imath.Color3f( 0.0, 1.0, 0.0 ).equalWithAbsError(
				outMesh["Cs"].data[1],
				.000001
			)
		)
		self.assertTrue( 
			imath.Color3f( 0.75, 0.25, 0.0 ).equalWithAbsError(
				outMesh["Cs"].data[2],
				.000001
			)
		)

		# Test that we don't flip 0.0 and 1.0 values
		pointsPrimitive["uv"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.V2fVectorData(
				[
					imath.V2f( 0.0, 0.0 ),
					imath.V2f( 0.5, 0.0 ),
					imath.V2f( 1.0, 1.0 ),
				],
				IECore.GeometricData.Interpretation.UV
			),
		)

		points["object"].setValue( pointsPrimitive )

		outMesh = imageSampler["out"].object( "/object" )
		self.assertTrue( set( outMesh.keys() ), set( inMesh.keys() + ["Cs" ] ) )
		self.assertTrue( 
			imath.Color3f( 1.0, 0.0, 0.0 ).equalWithAbsError( 
				outMesh["Cs"].data[0],
				.000001
			)
		)
		self.assertTrue( 
			imath.Color3f( 0.0, 1.0, 0.0 ).equalWithAbsError(
				outMesh["Cs"].data[1],
				.000001
			)
		)
		self.assertTrue( 
			imath.Color3f( 0.0, 0.0, 1.0 ).equalWithAbsError(
				outMesh["Cs"].data[2],
				.000001
			)
		)
		

	def testWrongSampleCount( self ) :
		pointsPrimitive = IECoreScene.PointsPrimitive(
			IECore.V3fVectorData( [imath.V3f( 0 ) ] * 3 )
		)

		pointsPrimitive["uv"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.V2fVectorData(
				[
					imath.V2f( 0.0, 0.0 ),
					imath.V2f( 0.5, 0.0 ),
					imath.V2f( 1.0, 0.0 ),
				],
				IECore.GeometricData.Interpretation.UV
			),
		)

		points = GafferScene.ObjectToScene()
		points["object"].setValue( pointsPrimitive )

		pointsFilter = GafferScene.PathFilter()
		pointsFilter["paths"].setValue( IECore.StringVectorData( ["/object" ] ) )

		ramp = self.getTestRamp()

		imageSampler = GafferScene.ImageSampler()
		imageSampler["in"].setInput( points["out"] )
		imageSampler["filter"].setInput( pointsFilter["out"] )
		imageSampler["image"].setInput( ramp["out"] )
		imageSampler["uvSet"].setValue( "uv" )
		imageSampler.addPrimitiveVariableSampler( "Cs", IECore.GeometricData.Interpretation.Color, "R G")

		self.assertRaises( Gaffer.ProcessException, imageSampler["out"].object, "/object" )

		imageSampler.addPrimitiveVariableSampler( "test", IECore.GeometricData.Interpretation.None, "R G")
		self.assertRaises( Gaffer.ProcessException, imageSampler["out"].object, "/object" )

		imageSampler.addPrimitiveVariableSampler( "N", IECore.GeometricData.Interpretation.Normal, "R G")
		self.assertRaises( Gaffer.ProcessException, imageSampler["out"].object, "/object" )
		
		imageSampler.addPrimitiveVariableSampler( "P", IECore.GeometricData.Interpretation.Point, "R G")
		self.assertRaises( Gaffer.ProcessException, imageSampler["out"].object, "/object" )

		imageSampler.addPrimitiveVariableSampler( "uv", IECore.GeometricData.Interpretation.UV, "R G B")
		self.assertRaises( Gaffer.ProcessException, imageSampler["out"].object, "/object" )

		imageSampler.addPrimitiveVariableSampler( "velocity", IECore.GeometricData.Interpretation.Vector, "R G")
		self.assertRaises( Gaffer.ProcessException, imageSampler["out"].object, "/object" )


	# Make sure the Sampler is not corrupting upstream context
	
	def testContext( self ) :
		pointsPrimitive = IECoreScene.PointsPrimitive(
			IECore.V3fVectorData( [imath.V3f( 0 ) ] * 3 )
		)

		pointsPrimitive["uv"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.V2fVectorData(
				[
					imath.V2f( 0.0, 0.0 ),
					imath.V2f( 0.5, 0.0 ),
					imath.V2f( 1.0, 0.0 ),
				],
				IECore.GeometricData.Interpretation.UV
			),
		)

		points = GafferScene.ObjectToScene()
		points["object"].setValue( pointsPrimitive )

		pointsFilter = GafferScene.PathFilter()
		pointsFilter["paths"].setValue( IECore.StringVectorData( ["/object" ] ) )

		imgReader = GafferImage.ImageReader()
		imgReader["fileName"].setValue( "$a" )

		imageSampler = GafferScene.ImageSampler()
		imageSampler["in"].setInput( points["out"] )
		imageSampler["filter"].setInput( pointsFilter["out"] )
		imageSampler["image"].setInput( imgReader["out"] )
		imageSampler["uvSet"].setValue( "uv" )
		imageSampler.addPrimitiveVariableSampler( "Cs", IECore.GeometricData.Interpretation.Color, "R G B")

		c = Gaffer.ContextVariables()
		c.setup( GafferScene.ScenePlug() )
		c["in"].setInput( imageSampler["out"] )

		if os.name == "nt":
			gaffer_root = os.path.abspath( os.path.expandvars( "%GAFFER_ROOT%" ) ).replace( "\\", "/" )
		else:
			gaffer_root = os.path.expandvars( "$GAFFER_ROOT" )

		c["variables"].addChild( Gaffer.NameValuePlug( "a", IECore.StringData( gaffer_root + "/python/GafferImageTest/images/checker.exr" ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )

		self.assertSceneValid( c["out"] )

		# make sure the image is valid
		self.assertTrue( "R" in imgReader["out"]["channelNames"].getValue() )
		self.assertTrue( "G" in imgReader["out"]["channelNames"].getValue() )
		self.assertTrue( "B" in imgReader["out"]["channelNames"].getValue() )

		inMesh = c["in"].object( "/object" )
		outMesh = c["out"].object( "/object" )
		self.assertTrue( set( outMesh.keys() ), set( inMesh.keys() + ["Cs"] ) )
		self.assertTrue( 
			imath.Color3f( 0.1, 0.1, 0.1 ).equalWithAbsError( 
				outMesh["Cs"].data[0],
				.000001
			)
		)
		self.assertTrue( 
			imath.Color3f( 1.0, 1.0, 0.0 ).equalWithAbsError(
				outMesh["Cs"].data[1],
				.000001
			)
		)
		self.assertTrue( 
			imath.Color3f( 0.5, 0.5, 0.5 ).equalWithAbsError(
				outMesh["Cs"].data[2],
				.000001
			)
		)

if __name__ == "__main__":
	unittest.main()
