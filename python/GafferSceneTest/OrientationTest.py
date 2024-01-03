##########################################################################
#
#  Copyright (c) 2019, Image Engine Design Inc. All rights reserved.
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
import random
import math

import imath

import IECore
import IECoreScene

import Gaffer
import GafferScene
import GafferSceneTest

class OrientationTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		# Prepare some points with a variety of primitive
		# variables specifying the same random orientations.

		points = IECoreScene.PointsPrimitive(
			IECore.V3fVectorData( [ imath.V3f( 0 ) ] * 100 )
		)

		points["euler"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.V3fVectorData()
		)

		points["quaternion"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.QuatfVectorData()
		)

		points["unnormalizedQuaternion"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.QuatfVectorData()
		)

		points["unnormalizedHoudiniAlembicOrderQuaternion"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.QuatfVectorData()
		)

		points["axis"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.V3fVectorData()
		)

		points["angle"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.FloatVectorData()
		)

		random.seed( 0 )
		for i in range( 0, points["P"].data.size() ) :

			radians = imath.Eulerf(
				random.uniform( 0, math.pi / 2 ),
				random.uniform( 0, math.pi / 2 ),
				random.uniform( 0, math.pi / 2 )
			)

			degrees = 180.0 * radians / math.pi

			q = radians.toQuat()

			points["euler"].data.append( degrees )
			points["quaternion"].data.append( q )
			points["unnormalizedQuaternion"].data.append( 0.2 * q )
			points["unnormalizedHoudiniAlembicOrderQuaternion"].data.append(
				0.2 * imath.Quatf( q.v()[0], q.v()[1], q.v()[2], q.r() )
			)
			points["axis"].data.append( q.axis() )
			points["angle"].data.append( q.angle() )

		pointsNode = GafferScene.ObjectToScene()
		pointsNode["object"].setValue( points )

		# No filter is applied, so should be a no-op

		orientation = GafferScene.Orientation()
		orientation["in"].setInput( pointsNode["out"] )

		self.assertScenesEqual( orientation["out"], orientation["in"] )
		self.assertSceneHashesEqual( orientation["out"], orientation["in"] )

		# Apply a filter

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/object" ] ) )
		orientation["filter"].setInput( filter["out"] )

		# Test euler -> euler round tripping

		self.assertEqual( orientation["inMode"].getValue(), orientation.Mode.Euler )
		orientation["inEuler"].setValue( "euler" )
		orientation["outMode"].setValue( orientation.Mode.Euler )
		orientation["outEuler"].setValue( "outEuler" )

		for order in [
			imath.Eulerf.XYZ,
			imath.Eulerf.XZY,
			imath.Eulerf.YZX,
			imath.Eulerf.YXZ,
			imath.Eulerf.ZXY,
			imath.Eulerf.ZYX,
		] :
			orientation["inOrder"].setValue( order )
			orientation["outOrder"].setValue( order )
			self.__assertVectorDataAlmostEqual(
				orientation["in"].object( "/object" )["euler"].data,
				orientation["out"].object( "/object" )["outEuler"].data,
				delta = 0.01
			)

		# Test euler -> quaternion

		orientation["inOrder"].setValue( imath.Eulerf.XYZ )
		orientation["outMode"].setValue( orientation.Mode.Quaternion )
		orientation["outQuaternion"].setValue( "outQuaternion" )

		self.__assertVectorDataAlmostEqual(
			orientation["in"].object( "/object" )["quaternion"].data,
			orientation["out"].object( "/object" )["outQuaternion"].data,
		)

		# Test euler -> axis angle

		orientation["outMode"].setValue( orientation.Mode.AxisAngle )
		orientation["outAxis"].setValue( "outAxis" )
		orientation["outAngle"].setValue( "outAngle" )

		self.__assertVectorDataAlmostEqual(
			orientation["in"].object( "/object" )["axis"].data,
			orientation["out"].object( "/object" )["outAxis"].data,
		)

		self.__assertVectorDataAlmostEqual(
			orientation["in"].object( "/object" )["angle"].data,
			orientation["out"].object( "/object" )["outAngle"].data,
		)

		# Test quaternion -> quaternion

		orientation["inMode"].setValue( orientation.Mode.Quaternion )
		orientation["outMode"].setValue( orientation.Mode.Quaternion )
		orientation["outQuaternion"].setValue( "outQuaternion" )

		orientation["inQuaternion"].setValue( "quaternion" )

		self.__assertVectorDataAlmostEqual(
			orientation["in"].object( "/object" )["quaternion"].data,
			orientation["out"].object( "/object" )["outQuaternion"].data,
		)

		orientation["inQuaternion"].setValue( "unnormalizedQuaternion" )

		self.__assertVectorDataAlmostEqual(
			orientation["in"].object( "/object" )["quaternion"].data,
			orientation["out"].object( "/object" )["outQuaternion"].data,
		)

		orientation["inQuaternion"].setValue( "unnormalizedHoudiniAlembicOrderQuaternion" )
		orientation["inMode"].setValue( orientation.Mode.QuaternionXYZW )

		self.__assertVectorDataAlmostEqual(
			orientation["in"].object( "/object" )["quaternion"].data,
			orientation["out"].object( "/object" )["outQuaternion"].data,
		)

	def testMismatchedInputSizes( self ) :

		points = IECoreScene.PointsPrimitive(
			IECore.V3fVectorData( [ imath.V3f( 0 ) ] * 2 )
		)

		points["axis"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.V3fVectorData( [ imath.V3f( 1, 0, 0 ) ] * 2 )
		)
		points["angle"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.FloatVectorData( [ 0, 0, 0 ] )
		)

		pointsNode = GafferScene.ObjectToScene()
		pointsNode["object"].setValue( points )

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/object" ] ) )

		orientation = GafferScene.Orientation()
		orientation["in"].setInput( pointsNode["out"] )
		orientation["filter"].setInput( filter["out"] )
		orientation["inMode"].setValue( orientation.Mode.AxisAngle )

		with self.assertRaises( RuntimeError ) as cm :
			orientation["out"].object( "/object" )

		self.assertIn(
			"Primitive variable \"angle\" has wrong size (3, but should be 2 to match \"axis\")",
			str( cm.exception )
		)

	def testMissingInputs( self ) :

		sphere = GafferScene.Sphere()

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/sphere" ] ) )

		orientation = GafferScene.Orientation()
		orientation["in"].setInput( sphere["out"] )
		orientation["filter"].setInput( filter["out"] )
		orientation["inMode"].setValue( orientation.Mode.AxisAngle )
		orientation["inAxis"].setValue( "iDontExist" )
		orientation["inAngle"].setValue( "iDontExist" )

		with self.assertRaises( RuntimeError ) as cm :
			orientation["out"].object( "/sphere" )

		self.assertIn(
			"Primitive variable \"iDontExist\" not found",
			str( cm.exception )
		)

	def __assertVectorDataAlmostEqual( self, a, b, delta = 0.00001 ) :

		if isinstance( a, IECore.QuatfVectorData ) :
			equal = [
				aa.v().equalWithAbsError( bb.v(), delta ) and math.fabs( aa.r() - bb.r() ) < delta
				for aa, bb in zip( a, b )
			]
		elif isinstance( a, IECore.V3fVectorData ) :
			equal = [ aa.equalWithAbsError( bb, delta ) for aa, bb in zip( a, b ) ]
		else :
			equal = [ math.fabs( aa - bb ) < delta for aa, bb in zip( a, b ) ]

		self.assertEqual(
			equal,
			[ True ] * len( a )
		)

if __name__ == "__main__":
	unittest.main()
