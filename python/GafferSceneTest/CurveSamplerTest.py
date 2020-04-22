##########################################################################
#
#  Copyright (c) 2020, Cinesite VFX Ltd. All rights reserved.
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

import GafferScene
import GafferSceneTest

class CurveSamplerTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		curvesPrimitive = IECoreScene.CurvesPrimitive(
			IECore.IntVectorData( [ 2, 2 ] ),
			IECore.CubicBasisf.linear(),
			False,
			IECore.V3fVectorData( [
				imath.V3f( 0 ), imath.V3f( 1, 0, 0 ),
				imath.V3f( 0 ), imath.V3f( 0, 1, 0 )
			] )
		)

		curves = GafferScene.ObjectToScene()
		curves["object"].setValue( curvesPrimitive )
		curves["name"].setValue( "curves" )

		points = GafferScene.ObjectToScene()
		points["name"].setValue( "points" )

		pointsFilter = GafferScene.PathFilter()
		pointsFilter["paths"].setValue( IECore.StringVectorData( [ "/points" ] ) )

		sampler = GafferScene.CurveSampler()
		sampler["in"].setInput( points["out"] )
		sampler["source"].setInput( curves["out"] )
		sampler["filter"].setInput( pointsFilter["out"] )
		sampler["sourceLocation"].setValue( "/curves" )
		sampler["primitiveVariables"].setValue( "P" )
		sampler["status"].setValue( "status" )
		sampler["curveIndex"].setValue( "curveIndex" )
		sampler["v"].setValue( "v" )

		def __sampleCurves( curveIndex, v ) :

			pointsPrimitive = IECoreScene.PointsPrimitive(
				IECore.V3fVectorData( [ imath.V3f( 0 ) ] )
			)
			pointsPrimitive["curveIndex"] = IECoreScene.PrimitiveVariable(
				IECoreScene.PrimitiveVariable.Interpolation.Vertex,
				IECore.IntVectorData( [ curveIndex ] ),
			)
			pointsPrimitive["v"] = IECoreScene.PrimitiveVariable(
				IECoreScene.PrimitiveVariable.Interpolation.Vertex,
				IECore.FloatVectorData( [ v ] ),
			)

			points["object"].setValue( pointsPrimitive )

			sampledPoints = sampler["out"].object( "/points" )
			return sampledPoints["P"].data[0], sampledPoints["status"].data[0]

		self.assertEqual(
			__sampleCurves( 0, 0.5 ),
			( imath.V3f( 0.5, 0, 0 ), True )
		)

		self.assertEqual(
			__sampleCurves( 1, 0.5 ),
			( imath.V3f( 0, 0.5, 0 ), True )
		)

		self.assertEqual(
			__sampleCurves( -1, 0.5 ), # Curve index out of range
			( imath.V3f( 0, 0, 0 ), False )
		)

		self.assertEqual(
			__sampleCurves( 2, 0.5 ), # Curve index out of range
			( imath.V3f( 0, 0, 0 ), False )
		)

		self.assertEqual(
			__sampleCurves( 0, -0.01 ), # v out of range
			( imath.V3f( 0, 0, 0 ), False )
		)

		self.assertEqual(
			__sampleCurves( 0, 1.01 ), # v out of range
			( imath.V3f( 0, 0, 0 ), False )
		)

if __name__ == "__main__":
	unittest.main()
