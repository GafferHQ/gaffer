##########################################################################
#
#  Copyright (c) 2026, Cinesite VFX Ltd. All rights reserved.
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

import Gaffer
import GafferScene
import GafferSceneTest

class ReflectionConstraintTest( GafferSceneTest.SceneTestCase ) :

	def testPosition( self ) :

		target = GafferScene.Plane()
		target["name"].setValue( "target" )

		sphere = GafferScene.Sphere()
		camera = GafferScene.Camera()

		parent = GafferScene.Parent()
		parent["parent"].setValue( "/" )
		parent["in"].setInput( target["out"] )
		parent["children"][0].setInput( sphere["out"] )
		parent["children"][1].setInput( camera["out"] )

		sphereFilter = GafferScene.PathFilter()
		sphereFilter["paths"].setValue( IECore.StringVectorData( [ "/sphere" ] ) )

		constraint = GafferScene.ReflectionConstraint()
		constraint["in"].setInput( parent["out"] )
		constraint["filter"].setInput( sphereFilter["out"] )
		constraint["target"].setValue( "/target" )
		constraint["targetMode"].setValue( constraint.TargetMode.UV )
		constraint["targetUV"].setValue( imath.V2f( 0.5 ) )
		constraint["camera"].setValue( "/camera" )

		for cameraTranslation in [
			imath.V3f( 0 ),
			imath.V3f( 1, 0, 0 ),
			imath.V3f( 1, 1, 0 ),
			imath.V3f( 10, 2, 0 ),
		] :

			for distance in ( None, 1.0, 10.0 ) :

				with self.subTest( cameraTranslation = cameraTranslation, distance = distance ) :

					camera["transform"]["translate"].setValue( cameraTranslation )

					if distance is None :
						constraint["distanceMode"].setValue( constraint.DistanceMode.Camera )
					else :
						constraint["distanceMode"].setValue( constraint.DistanceMode.Constant )
						constraint["distance"].setValue( distance )

					transform = constraint["out"].fullTransform( "/sphere" )

					if distance is None :
						self.assertEqual( transform.translation(), -cameraTranslation )
					else :
						self.assertEqual( transform.translation(), -cameraTranslation.normalized() * distance )

					self.__assertRotationsEqual( transform, constraint["in"].fullTransform( "/sphere" ) )

	def testOrientation( self ) :

		target = GafferScene.Plane()
		target["name"].setValue( "target" )

		sphere = GafferScene.Sphere()
		sphere["transform"]["rotate"].setValue( imath.V3f( 90, 0, 0 ) )
		camera = GafferScene.Camera()
		camera["transform"]["translate"].setValue( imath.V3f( 1, 1, 0 ) )

		parent = GafferScene.Parent()
		parent["parent"].setValue( "/" )
		parent["in"].setInput( target["out"] )
		parent["children"][0].setInput( sphere["out"] )
		parent["children"][1].setInput( camera["out"] )

		sphereFilter = GafferScene.PathFilter()
		sphereFilter["paths"].setValue( IECore.StringVectorData( [ "/sphere" ] ) )

		constraint = GafferScene.ReflectionConstraint()
		constraint["in"].setInput( parent["out"] )
		constraint["filter"].setInput( sphereFilter["out"] )
		constraint["target"].setValue( "/target" )
		constraint["targetMode"].setValue( constraint.TargetMode.UV )
		constraint["targetUV"].setValue( imath.V2f( 0.5 ) )
		constraint["camera"].setValue( "/camera" )

		transform = constraint["out"].fullTransform( "/sphere" )
		self.assertEqual( transform.translation(), -camera["transform"]["translate"].getValue() )
		self.__assertRotationsEqual( transform, constraint["in"].fullTransform( "/sphere" ) )

		constraint["aimEnabled"].setValue( True )
		transform = constraint["out"].fullTransform( "/sphere" )

		expectedRotation = imath.M44f().rotationMatrixWithUpDir( imath.V3f( 0, 0, -1 ), -transform.translation(), imath.V3f( 0, 1, 0 ) )
		self.__assertRotationsEqual( transform, expectedRotation )

	def testMissingCamera( self ) :

		plane = GafferScene.Plane()
		sphere = GafferScene.Sphere()

		parent = GafferScene.Parent()
		parent["parent"].setValue( "/" )
		parent["in"].setInput( plane["out"] )
		parent["children"][0].setInput( sphere["out"] )

		sphereFilter = GafferScene.PathFilter()
		sphereFilter["paths"].setValue( IECore.StringVectorData( [ "/sphere" ] ) )

		constraint = GafferScene.ReflectionConstraint()
		constraint["in"].setInput( parent["out"] )
		constraint["filter"].setInput( sphereFilter["out"] )
		constraint["target"].setValue( "/plane" )
		constraint["camera"].setValue( "/camera" )

		with self.assertRaisesRegex( Gaffer.ProcessException, "Camera \"/camera\" does not exist. Error may be suppressed using `ignoreMissingTarget`." ) :
			constraint["out"].fullTransform( "/sphere" )

		constraint["ignoreMissingTarget"].setValue( True )
		self.assertEqual( constraint["out"].fullTransform( "/sphere" ), constraint["in"].fullTransform( "/sphere" ) )

	def __assertRotationsEqual( self, matrix1, matrix2 ) :

		rotation1 = imath.Eulerf()
		matrix1.extractEulerXYZ( rotation1 )
		rotation2 = imath.Eulerf()
		matrix2.extractEulerXYZ( rotation2 )

		self.assertEqual( rotation1, rotation2 )

if __name__ == "__main__":
	unittest.main()
