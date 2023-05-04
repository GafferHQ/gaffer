##########################################################################
#
#  Copyright (c) 2023, Image Engine Design Inc. All rights reserved.
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
import GafferTest

import GafferScene
import GafferSceneTest

class MeshNormalsTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		sourceMesh = IECoreScene.MeshPrimitive.createBox( imath.Box3f( imath.V3f( -1 ), imath.V3f( 1 ) ) )

		source = GafferScene.ObjectToScene()
		source["object"].setValue( sourceMesh )

		pathFilter = GafferScene.PathFilter( "PathFilter" )
		pathFilter["paths"].setValue( IECore.StringVectorData( ['/object'] ) )

		meshNormals = GafferScene.MeshNormals()
		meshNormals["in"].setInput( source["out"] )
		meshNormals["filter"].setInput( pathFilter["out"] )

		# Test uniform

		meshNormals["interpolation"].setValue( IECoreScene.PrimitiveVariable.Interpolation.Uniform )

		facetedM = meshNormals["out"].object( "/object" )
		self.assertEqual( facetedM["N"].data, IECore.V3fVectorData( [
			imath.V3f( 0, 0, -1 ), imath.V3f( 1, 0, 0 ), imath.V3f( 0, 0, 1 ),
			imath.V3f( -1, 0, 0 ), imath.V3f( 0, 1, 0 ), imath.V3f( 0, -1, 0 )
		], IECore.GeometricData.Interpretation.Normal ) )

		# Test vertex

		meshNormals["interpolation"].setValue( IECoreScene.PrimitiveVariable.Interpolation.Vertex )

		smoothM = meshNormals["out"].object( "/object" )
		for n, p in zip( smoothM["N"].data, smoothM["P"].data ):
			self.assertEqual( n, p.normalized() )

		# Test face-varying ( with 2 different thresholdAngles )

		meshNormals["interpolation"].setValue( IECoreScene.PrimitiveVariable.Interpolation.FaceVarying )
		faceVaryLowThreshM = meshNormals["out"].object( "/object" )
		facetedFaceVaryingN = IECoreScene.PrimitiveVariable( facetedM["N"] )
		IECoreScene.MeshAlgo.resamplePrimitiveVariable( facetedM, facetedFaceVaryingN, IECoreScene.PrimitiveVariable.Interpolation.FaceVarying )

		self.assertEqual( faceVaryLowThreshM["N"], facetedFaceVaryingN )

		meshNormals["thresholdAngle"].setValue( 91 )
		faceVaryHighThreshM = meshNormals["out"].object( "/object" )
		smoothFaceVaryingN = IECoreScene.PrimitiveVariable( smoothM["N"] )
		IECoreScene.MeshAlgo.resamplePrimitiveVariable( smoothM, smoothFaceVaryingN, IECoreScene.PrimitiveVariable.Interpolation.FaceVarying )

		self.assertEqual( faceVaryHighThreshM["N"], smoothFaceVaryingN )

		# Test different weighting types
		meshNormals["interpolation"].setValue( IECoreScene.PrimitiveVariable.Interpolation.Vertex )

		source["object"].setValue( IECoreScene.MeshAlgo.triangulate( sourceMesh ) )
		triangulatedM = meshNormals["out"].object( "/object" )
		for n, p in zip( triangulatedM["N"].data, triangulatedM["P"].data ):
			self.assertAlmostEqual( n[0], p.normalized()[0], places = 6 )
			self.assertAlmostEqual( n[1], p.normalized()[1], places = 6 )
			self.assertAlmostEqual( n[2], p.normalized()[2], places = 6 )

		# Try out the naive "equal weighting" mode on the triangulated mesh, which yields ugly results
		meshNormals["weighting"].setValue( IECoreScene.MeshAlgo.NormalWeighting.Equal )
		triangulatedBadM = meshNormals["out"].object( "/object" )

		# Every vertex ends up touching both triangles on at least one face, so all the normals are at
		# some sort of weird off-kilter angle
		for n in triangulatedBadM["N"].data:
			sortedVec = imath.V3f( *sorted( [ abs(i) for i in n ] ) )
			self.assertTrue(
				sortedVec.equalWithRelError( imath.V3f( 1, 1, 2 ).normalized(), 1e-7 ) or
				sortedVec.equalWithRelError( imath.V3f( 1, 2, 2 ).normalized(), 1e-7 )
			)

if __name__ == "__main__":
	unittest.main()
