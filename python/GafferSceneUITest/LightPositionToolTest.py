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

	def __shadowSource( self, lightP, shadowPivot, shadowPoint ) :
		return ( shadowPivot - shadowPoint ).normalize() * ( lightP - shadowPivot ).length() + shadowPivot

	def testPositionShadow( self ) :

		random.seed( 42 )

		script = Gaffer.ScriptNode()
		script["light"] = GafferSceneTest.TestLight()

		view = GafferSceneUI.SceneView( script )
		view["in"].setInput( script["light"]["out"] )
		GafferSceneUI.ScriptNodeAlgo.setSelectedPaths( script, IECore.PathMatcher( [ "/light" ] ) )

		tool = GafferSceneUI.LightPositionTool( view )
		tool["active"].setValue( True )

		for i in range( 0, 5 ) :
			lightP = imath.V3f( random.random() * 10 - 5, random.random() * 10 - 5, random.random() * 10 - 5 )
			shadowPivot = imath.V3f( random.random() * 10 - 5, random.random() * 10 - 5, random.random() * 10 - 5 )
			shadowPoint = imath.V3f( random.random() * 10 - 5, random.random() * 10 - 5, random.random() * 10 - 5 )

			script["light"]["transform"]["translate"].setValue( lightP )

			d0 = ( lightP - shadowPivot ).length()

			with Gaffer.Context() :
				tool.positionShadow( shadowPivot, shadowPoint, d0 )

			p = script["light"]["transform"]["translate"].getValue()

			d1 = ( p - shadowPivot ).length()
			self.assertAlmostEqual( d0, d1, places = 4 )

			desiredP = self.__shadowSource( lightP, shadowPivot, shadowPoint )

			self.assertEqualWithAbsError( p, desiredP, error = 0.0001 )

			desiredM = imath.M44f()
			imath.M44f.rotationMatrixWithUpDir( desiredM, imath.V3f( 0, 0, -1 ), shadowPoint - shadowPivot, imath.V3f( 0, 1, 0 ) )
			rotationO = imath.Eulerf()
			desiredM.extractEulerXYZ( rotationO )

			o = imath.Eulerf( IECore.degreesToRadians( script["light"]["transform"]["rotate"].getValue() ) )
			o.makeNear( rotationO )

			self.assertEqualWithAbsError( o, rotationO, 1e-4 )

	def testPositionShadowWithParentTransform( self ) :

		random.seed( 44 )

		script = Gaffer.ScriptNode()

		script["light"] = GafferSceneTest.TestLight()

		script["group"] = GafferScene.Group()
		script["group"]["in"][0].setInput( script["light"]["out"] )

		view = GafferSceneUI.SceneView( script )
		view["in"].setInput( script["group"]["out"] )
		GafferSceneUI.ScriptNodeAlgo.setSelectedPaths( script, IECore.PathMatcher( [ "/group/light"] ) )

		tool = GafferSceneUI.LightPositionTool( view )
		tool["active"].setValue( True )

		for i in range( 0, 10 ) :
			with self.subTest( i = i ) :
				script["light"]["transform"]["translate"].setValue( imath.V3f( random.random() * 10 - 5, random.random() * 10 - 5, random.random() * 10 - 5 ) )

				script["group"]["transform"]["translate"].setValue( imath.V3f( random.random() * 10 - 5, random.random() * 10 - 5, random.random() * 10 - 5 ) )

				shadowPivot = imath.V3f( random.random() * 10 - 5, random.random() * 10 - 5, random.random() * 10 - 5 )
				shadowPoint = imath.V3f( random.random() * 10 - 5, random.random() * 10 - 5, random.random() * 10 - 5 )

				worldM = script["group"]["out"].fullTransform( "/group/light" )
				worldP = imath.V3f( 0 ) * worldM

				d = ( worldP - shadowPivot ).length()

				with Gaffer.Context() :
					tool.positionShadow( shadowPivot, shadowPoint, d )

				parentInverseTransform = script["group"]["out"].fullTransform( "/group" ).inverse()

				desiredWorldP = self.__shadowSource( worldP, shadowPivot, shadowPoint )
				desiredLocalP = desiredWorldP * parentInverseTransform
				t = script["light"]["transform"]["translate"].getValue()
				self.assertEqualWithAbsError( t, desiredLocalP, error = 0.0001 )

				desiredM = imath.M44f()
				imath.M44f.rotationMatrixWithUpDir( desiredM, imath.V3f( 0, 0, -1 ), shadowPoint - shadowPivot, imath.V3f( 0, 1, 0 ) )
				desiredLocalM = desiredM * parentInverseTransform
				desiredO = imath.Eulerf()
				desiredLocalM.extractEulerXYZ( desiredO )

				o = imath.Eulerf( IECore.degreesToRadians( script["light"]["transform"]["rotate"].getValue() ) )
				o.makeNear( desiredO )

				self.assertEqualWithAbsError( o, desiredO, 1e-4 )

	def __highlightSource( self, lightP, highlightP, viewP, normal ) :
		d = ( lightP - highlightP ).length()
		reflected = imath.V3f.reflect( viewP - highlightP, normal ).normalized()
		return highlightP + reflected * d

	def testPositionHighlight( self ) :

		random.seed( 42 )

		script = Gaffer.ScriptNode()
		script["light"] = GafferSceneTest.TestLight()

		view = GafferSceneUI.SceneView( script )
		view["in"].setInput( script["light"]["out"] )
		GafferSceneUI.ScriptNodeAlgo.setSelectedPaths( script, IECore.PathMatcher( [ "/light" ] ) )

		tool = GafferSceneUI.LightPositionTool( view )
		tool["active"].setValue( True )

		for i in range( 0, 5 ) :
			lightP = imath.V3f( random.random() * 10 - 5, random.random() * 10 - 5, random.random() * 10 - 5 )
			viewP = imath.V3f( random.random() * 10 - 5, random.random() * 10 - 5, random.random() * 10 - 5 )
			highlightP = imath.V3f( random.random() * 10 - 5, random.random() * 10 - 5, random.random() * 10 - 5 )
			normal = imath.V3f( random.random() * 2 - 1, random.random() * 2 - 1, random.random() * 2 - 1 ).normalized()

			script["light"]["transform"]["translate"].setValue( lightP )

			d0 = ( lightP - highlightP ).length()

			with Gaffer.Context() :
				tool.positionHighlight( highlightP, viewP, normal, d0 )

			p = script["light"]["transform"]["translate"].getValue()

			d1 = ( p - highlightP ).length()
			self.assertAlmostEqual( d0, d1, places = 4 )

			desiredP = self.__highlightSource( lightP, highlightP, viewP, normal )
			self.assertEqualWithAbsError( p, desiredP, 0.0001 )

			desiredM = imath.M44f()
			imath.M44f.rotationMatrixWithUpDir( desiredM, imath.V3f( 0, 0, -1 ), highlightP - p, imath.V3f( 0, 1, 0 ) )
			rotationO = imath.Eulerf()
			desiredM.extractEulerXYZ( rotationO )

			o = imath.Eulerf( IECore.degreesToRadians( script["light"]["transform"]["rotate"].getValue() ) )
			o.makeNear( rotationO )

			with self.subTest( f"Iteration {i}" ) :
				self.assertEqualWithAbsError( o, rotationO, 1e-4 )

	def __diffuseSource( self, lightP, diffuseP, normal ) :
		d = ( lightP - diffuseP ).length()
		return diffuseP + normal * d

	def testPositionDiffuse( self ) :

		random.seed( 42 )

		script = Gaffer.ScriptNode()
		script["light"] = GafferSceneTest.TestLight()

		view = GafferSceneUI.SceneView( script )
		view["in"].setInput( script["light"]["out"] )
		GafferSceneUI.ScriptNodeAlgo.setSelectedPaths( script, IECore.PathMatcher( [ "/light"] ) )

		tool = GafferSceneUI.LightPositionTool( view )
		tool["active"].setValue( True )

		for i in range( 0, 5 ) :
			lightP = imath.V3f( random.random() * 10 - 5, random.random() * 10 - 5, random.random() * 10 - 5 )
			diffuseP = imath.V3f( random.random() * 10 - 5, random.random() * 10 - 5, random.random() * 10 - 5 )
			normal = imath.V3f( random.random() * 2 - 1, random.random() * 2 - 1, random.random() * 2 - 1 ).normalized()

			script["light"]["transform"]["translate"].setValue( lightP )

			d0 = ( lightP - diffuseP ).length()

			with Gaffer.Context() :
				tool.positionAlongNormal( diffuseP, normal, d0 )

			p = script["light"]["transform"]["translate"].getValue()

			d1 = ( p - diffuseP ).length()
			self.assertAlmostEqual( d0, d1, places = 4 )

			desiredP = self.__diffuseSource( lightP, diffuseP, normal )
			self.assertEqualWithAbsError( p, desiredP, 0.0001 )

			desiredM = imath.M44f()
			imath.M44f.rotationMatrixWithUpDir( desiredM, imath.V3f( 0, 0, -1 ), diffuseP - p, imath.V3f( 0, 1, 0 ) )
			rotationO = imath.Eulerf()
			desiredM.extractEulerXYZ( rotationO )

			o = imath.Eulerf( IECore.degreesToRadians( script["light"]["transform"]["rotate"].getValue() ) )
			o.makeNear( imath.Eulerf( rotationO ) )

			with self.subTest( f"Iteration {i}" ) :
				self.assertEqualWithAbsError( o, rotationO, 1e-4 )

	def testEmptySelectionModeChange( self ) :

		script = Gaffer.ScriptNode()
		script["light"] = GafferSceneTest.TestLight()

		view = GafferSceneUI.SceneView( script )
		view["in"].setInput( script["light"]["out"] )

		tool = GafferSceneUI.LightPositionTool( view )
		tool["active"].setValue( True )

		# Should not raise an exception
		tool["mode"].setValue( GafferSceneUI.LightPositionTool.Mode.Highlight )
		self.assertEqual( tool["mode"].getValue(), GafferSceneUI.LightPositionTool.Mode.Highlight )

if __name__ == "__main__" :
	unittest.main()
