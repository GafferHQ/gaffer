##########################################################################
#
#  Copyright (c) 2023, Cinesite VFX Ltd. All rights reserved.
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

import Gaffer
import GafferScene
import GafferUITest
import GafferSceneUI
import GafferSceneTest

class LightPositionToolTest( GafferUITest.TestCase ) :

	@staticmethod
	def assertAnglesAlmostEqual( a, b, places = 7 ) :
		# Check for equivalent euler orientations. `a` and `b` in degrees.
		a[0] = a[0] % 360
		a[1] = a[1] % 360
		a[2] = a[2] % 360
		b[0] = b[0] % 360
		b[1] = b[1] % 360
		b[2] = b[2] % 360

		if (
			round( abs( a[0] - b[0] ), places ) == 0 and
			round( abs( a[1] - b[1] ), places ) == 0 and
			round( abs( a[2] - b[2] ), places ) == 0
		) :
			return
		if (
			round( abs( ( 180.0 + a[0] ) % 360 - b[0] ), places ) == 0 and
			round( abs( ( 180.0 - a[1] ) % 360 - b[1] ), places ) == 0 and
			round( abs( ( 180.0 + a[2] ) % 360 - b[2] ), places ) == 0
		) :
			return
		diff = a - b
		diff[0] = abs( diff[0] )
		diff[1] = abs( diff[1] )
		diff[2] = abs( diff[2] )
		raise AssertionError( f"{a} != {b} within {places} places ({diff} difference)" )

	def __shadowSource( self, lightP, shadowPivot, shadowPoint ) :
		return ( shadowPivot - shadowPoint ).normalize() * ( lightP - shadowPivot ).length() + shadowPivot

	def testPosition( self ) :

		random.seed( 42 )

		script = Gaffer.ScriptNode()
		script["light"] = GafferSceneTest.TestLight()

		view = GafferSceneUI.SceneView()
		view["in"].setInput( script["light"]["out"] )
		GafferSceneUI.ContextAlgo.setSelectedPaths( view.getContext(), IECore.PathMatcher( [ "/light" ] ) )

		tool = GafferSceneUI.LightPositionTool( view )
		tool["active"].setValue( True )

		for i in range( 0, 5 ) :
			lightP = imath.V3f( random.random() * 10 - 5, random.random() * 10 - 5, random.random() * 10 - 5 )
			shadowPivot = imath.V3f( random.random() * 10 - 5, random.random() * 10 - 5, random.random() * 10 - 5 )
			shadowPoint = imath.V3f( random.random() * 10 - 5, random.random() * 10 - 5, random.random() * 10 - 5 )

			script["light"]["transform"]["translate"].setValue( lightP )

			d0 = ( lightP - shadowPivot ).length()
			upDir = script["light"]["transform"].matrix().multDirMatrix( imath.V3f( 0, 1, 0 ) )

			with Gaffer.Context() :
				tool.positionShadow( shadowPivot, shadowPoint, d0 )

			p = script["light"]["transform"]["translate"].getValue()

			d1 = ( p - shadowPivot ).length()
			self.assertAlmostEqual( d0, d1, places = 4 )

			desiredP = self.__shadowSource( lightP, shadowPivot, shadowPoint )

			for j in range( 0, 3 ) :
				self.assertAlmostEqual( p[j], desiredP[j], places = 4 )

			desiredO = imath.M44f()
			imath.M44f.rotationMatrixWithUpDir( desiredO, imath.V3f( 0, 0, -1 ), shadowPoint - shadowPivot, upDir )
			rotationO = imath.V3f()
			desiredO.extractEulerXYZ( rotationO )

			o = script["light"]["transform"]["rotate"].getValue()

			self.assertAnglesAlmostEqual(
					o,
					IECore.radiansToDegrees( imath.V3f( rotationO ) ),
					places = 4
				)

	def testPositionWithParentTransform( self ) :

		random.seed( 44 )

		script = Gaffer.ScriptNode()

		script["light"] = GafferSceneTest.TestLight()

		script["group"] = GafferScene.Group()
		script["group"]["in"][0].setInput( script["light"]["out"] )

		view = GafferSceneUI.SceneView()
		view["in"].setInput( script["group"]["out"] )
		GafferSceneUI.ContextAlgo.setSelectedPaths( view.getContext(), IECore.PathMatcher( [ "/group/light"] ) )

		tool = GafferSceneUI.LightPositionTool( view )
		tool["active"].setValue( True )

		for i in range( 0, 10 ) :
			with self.subTest( i = i ) :
				script["light"]["transform"]["translate"].setValue( imath.V3f( random.random() * 10 - 5, random.random() * 10 - 5, random.random() * 10 - 5 ) )
				script["light"]["transform"]["rotate"].setValue( imath.V3f( random.random() * 10 - 5, random.random() * 10 - 5, random.random() * 10 - 5 ) )

				script["group"]["transform"]["translate"].setValue( imath.V3f( random.random() * 10 - 5, random.random() * 10 - 5, random.random() * 10 - 5 ) )
				script["group"]["transform"]["rotate"].setValue( imath.V3f( random.random() * 10 - 5, random.random() * 10 - 5, random.random() * 10 - 5 ) )

				shadowPivot = imath.V3f( random.random() * 10 - 5, random.random() * 10 - 5, random.random() * 10 - 5 )
				shadowPoint = imath.V3f( random.random() * 10 - 5, random.random() * 10 - 5, random.random() * 10 - 5 )

				worldTransform = script["group"]["out"].fullTransform( "/group/light" )
				worldP = imath.V3f( 0 ) * worldTransform

				d = ( worldP - shadowPivot ).length()

				with Gaffer.Context() :
					tool.positionShadow( shadowPivot, shadowPoint, d )

				parentInverseTransform = script["group"]["out"].fullTransform( "/group" ).inverse()

				desiredWorldP = self.__shadowSource( worldP, shadowPivot, shadowPoint )
				desiredLocalP = desiredWorldP * parentInverseTransform
				t = script["light"]["transform"]["translate"].getValue()
				for j in range( 0, 3 ) :
					with self.subTest( j = j ) :
						self.assertAlmostEqual( t[j], desiredLocalP[j], places = 4 )

				upDir = worldTransform.multDirMatrix( imath.V3f( 0, 1, 0 ) )

				desiredWorldO = imath.M44f()
				imath.M44f.rotationMatrixWithUpDir( desiredWorldO, imath.V3f( 0, 0, -1 ), shadowPoint - shadowPivot, upDir )

				worldTransform = script["group"]["out"].fullTransform( "/group/light" )
				worldO = worldTransform
				worldO[3][0] = worldO[3][1] = worldO[3][2] = 0.0
				for j in range( 0, 4 ) :
					with self.subTest( j = j ) :
						for k in range( 0, 4 ) :
							with self.subTest( k = k ) :
								self.assertAlmostEqual( desiredWorldO[j][k], worldO[j][k], places = 3 )

				parentInverseO = parentInverseTransform
				parentInverseO[3][0] = parentInverseO[3][1] = parentInverseO[3][2] = 0.0
				desiredLocalO = desiredWorldO * parentInverseO
				localTransform = script["group"]["out"].transform( "/group/light" )
				localO = localTransform
				localO[3][0] = localO[3][1] = localO[3][2] = 0.0

				for j in range( 0, 4 ) :
					with self.subTest( j = j ) :
						for k in range( 0, 4 ) :
							with self.subTest( k = k ) :
								self.assertAlmostEqual( desiredLocalO[j][k], localO[j][k], places = 3 )


				r = script["light"]["transform"]["rotate"].getValue()

				desiredLocalR = imath.Eulerf()
				desiredLocalO.extractEulerXYZ( desiredLocalR )

				self.assertAnglesAlmostEqual(
					r,
					IECore.radiansToDegrees( imath.V3f( desiredLocalR ) ),
					places = 4
				)

if __name__ == "__main__" :
	unittest.main()
