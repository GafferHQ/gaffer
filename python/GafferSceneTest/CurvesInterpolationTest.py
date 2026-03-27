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
import IECoreScene

import Gaffer
import GafferScene
import GafferSceneTest

class CurvesInterpolationTest( GafferSceneTest.SceneTestCase ) :

	def testPassThrough( self ) :

		objectToScene = GafferScene.ObjectToScene()
		objectToScene["object"].setValue(
			IECoreScene.CurvesPrimitive(
				IECore.IntVectorData( [ 4 ] ), IECore.CubicBasisf.catmullRom()
			)
		)

		interpolation = GafferScene.CurvesInterpolation()
		interpolation["in"].setInput( objectToScene["out"] )

		# No filter

		self.assertTrue( interpolation["out"].exists( "/object" ) )
		self.assertScenesEqual( interpolation["out"], interpolation["in"] )
		self.assertSceneHashesEqual( interpolation["out"], interpolation["in"] )

		# Filter, but not matching anything yet

		pathFilter = GafferScene.PathFilter()
		interpolation["filter"].setInput( pathFilter["out"] )

		self.assertTrue( interpolation["out"].exists( "/object" ) )
		self.assertScenesEqual( interpolation["out"], interpolation["in"] )
		self.assertSceneHashesEqual( interpolation["out"], interpolation["in"] )

		# Filter matching something, but node disabled

		pathFilter["paths"].setValue( IECore.StringVectorData( [ "/object" ] ) )
		interpolation["enabled"].setValue( False )

		self.assertTrue( interpolation["out"].exists( "/object" ) )
		self.assertScenesEqual( interpolation["out"], interpolation["in"] )
		self.assertSceneHashesEqual( interpolation["out"], interpolation["in"] )

		# Node enabled, but not doing anything

		interpolation["enabled"].setValue( True )

		self.assertTrue( interpolation["out"].exists( "/object" ) )
		self.assertScenesEqual( interpolation["out"], interpolation["in"] )
		self.assertSceneHashesEqual( interpolation["out"], interpolation["in"] )

	def testChangeWrap( self ) :

		objectToScene = GafferScene.ObjectToScene()
		objectToScene["object"].setValue(
			IECoreScene.CurvesPrimitive(
				IECore.IntVectorData( [ 4 ] ), IECore.CubicBasisf.catmullRom(),
				wrap = IECoreScene.CurvesPrimitive.Wrap.Pinned,
				p = IECore.V3fVectorData( [ imath.V3f( x ) for x in range( 0, 4 ) ] )
			)
		)

		pathFilter = GafferScene.PathFilter()
		pathFilter["paths"].setValue( IECore.StringVectorData( [ "/object" ] ) )

		interpolation = GafferScene.CurvesInterpolation()
		interpolation["in"].setInput( objectToScene["out"] )
		interpolation["filter"].setInput( pathFilter["out"] )

		self.assertEqual( interpolation["out"].object( "/object" ).wrap(), IECoreScene.CurvesPrimitive.Wrap.Pinned )

		interpolation["wrap"]["enabled"].setValue( True )
		interpolation["wrap"]["value"].setValue( IECoreScene.CurvesPrimitive.Wrap.NonPeriodic )

		self.assertEqual( interpolation["out"].object( "/object" ).wrap(), IECoreScene.CurvesPrimitive.Wrap.NonPeriodic )
		self.assertEqual( interpolation["out"].object( "/object" )["P"], interpolation["in"].object( "/object" )["P"] )

		interpolation["expandPinned"].setValue( True )
		self.assertEqual( interpolation["out"].object( "/object" ).wrap(), IECoreScene.CurvesPrimitive.Wrap.NonPeriodic )
		self.assertEqual(
			interpolation["out"].object( "/object" )["P"].data,
			IECore.V3fVectorData( [ imath.V3f( x ) for x in range( -1, 5 ) ], IECore.GeometricData.Interpretation.Point )
		)

	def testChangeBasis( self ) :

		objectToScene = GafferScene.ObjectToScene()
		objectToScene["object"].setValue(
			IECoreScene.CurvesPrimitive(
				IECore.IntVectorData( [ 4 ] ), IECore.CubicBasisf.catmullRom(),
				p = IECore.V3fVectorData( [ imath.V3f( x ) for x in range( 0, 4 ) ] )
			)
		)

		pathFilter = GafferScene.PathFilter()
		pathFilter["paths"].setValue( IECore.StringVectorData( [ "/object" ] ) )

		interpolation = GafferScene.CurvesInterpolation()
		interpolation["in"].setInput( objectToScene["out"] )
		interpolation["filter"].setInput( pathFilter["out"] )

		self.assertEqual( interpolation["out"].object( "/object" ).basis(), IECore.CubicBasisf.catmullRom() )

		interpolation["basis"]["enabled"].setValue( True )
		interpolation["basis"]["value"].setValue( IECore.StandardCubicBasis.BSpline )

		self.assertEqual( interpolation["out"].object( "/object" ).basis(), IECore.CubicBasisf.bSpline() )

if __name__ == "__main__":
	unittest.main()
