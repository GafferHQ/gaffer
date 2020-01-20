##########################################################################
#
#  Copyright (c) 2020 Don Boogert. All rights reserved.
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
#      * Neither the name of Don Boogert nor the names of
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

import GafferVDB
import GafferVDBTest

import imath

class SphereLevelSetTest( GafferVDBTest.VDBTestCase ) :

	def testCanCreateSphereLevelSet( self ) :
		sphereLevelSet = GafferVDB.SphereLevelSet( "SphereLevelSet" )
		surfaceGrid = sphereLevelSet['out'].object( "vdb" ).findGrid( "surface" )
		self.assertTrue( surfaceGrid is not None )
		self.assertEqual( surfaceGrid.gridClass, "level set" )

	def testCanSetGridName( self ) :
		sphereLevelSet = GafferVDB.SphereLevelSet( "SphereLevelSet" )
		sphereLevelSet["grid"].setValue( "foo" )

		surfaceGrid = sphereLevelSet['out'].object( "vdb" ).findGrid( "foo" )
		self.assertTrue( surfaceGrid is not None )

	def testSignedDistanceIsNearlyZeroForPointsOnSphere( self ) :
		sphereLevelSet = GafferVDB.SphereLevelSet( "SphereLevelSet" )
		surfaceGrid = sphereLevelSet['out'].object( "vdb" ).findGrid( "surface" )
		accessor = surfaceGrid.getAccessor()
		# default voxel size is 0.1 and radius 1.0 so the radius of the sphere in index space is 10
		self.assertEqual( accessor.probeValue( ( 10, 0, 0 ) ) , ( 0.0, True ) )
		self.assertEqual( accessor.probeValue( ( 0, 10, 0 ) ) , ( 0.0, True ) )
		self.assertEqual( accessor.probeValue( ( 0, 0, 10 ) ) , ( 0.0, True ) )

	def testCanSetSphereRadius( self ) :
		sphereLevelSet = GafferVDB.SphereLevelSet( "SphereLevelSet" )
		sphereLevelSet["radius"].setValue( 2.0 )

		surfaceGrid = sphereLevelSet['out'].object( "vdb" ).findGrid( "surface" )
		accessor = surfaceGrid.getAccessor()
		# default voxel size is 0.1 and radius 2.0 so the radius of the sphere in index space is 20
		self.assertEqual( accessor.probeValue( ( 20, 0, 0 ) ) , ( 0.0, True ) )
		self.assertEqual( accessor.probeValue( ( 0, 20, 0 ) ) , ( 0.0, True ) )
		self.assertEqual( accessor.probeValue( ( 0, 0, 20 ) ) , ( 0.0, True ) )

	def testBounds( self ) :
		sphereLevelSet = GafferVDB.SphereLevelSet( "SphereLevelSet" )

		sphereLevelSet["radius"].setValue( 2.0 )
		bounds = sphereLevelSet['out'].bound( "vdb")
		self.assertEqual(bounds, imath.Box3f( imath.V3f( -2.25, -2.25, -2.25 ), imath.V3f( 2.25, 2.25, 2.25 ) ) )

		sphereLevelSet["voxelSize"].setValue( 0.2 )
		bounds = sphereLevelSet['out'].bound( "vdb" )
		self.assertEqual(bounds, imath.Box3f( imath.V3f( -2.5, -2.5, -2.5 ), imath.V3f( 2.5, 2.5, 2.5 ) ) )

		sphereLevelSet["center"].setValue( imath.V3f( 2.5, 0, 0 ) )
		bounds = sphereLevelSet['out'].bound( "vdb")
		self.assertBoundsNearlyEqual( bounds, imath.Box3f( imath.V3f( -0.1, -2.5, -2.5 ), imath.V3f(5.1, 2.5, 2.5) ) )

	def testVoxelCount( self ) :
		sphereLevelSet = GafferVDB.SphereLevelSet( "SphereLevelSet" )

		originalLeafCount = sphereLevelSet['out'].object( "vdb" ).findGrid( "surface" ).leafCount()

		sphereLevelSet["voxelSize"].setValue( 0.05 )
		sphereLevelSet["halfWidth"].setValue( 6.0 )
		newLeafCount = sphereLevelSet['out'].object( "vdb" ).findGrid( "surface" ).leafCount()

		self.assertTrue( newLeafCount >  originalLeafCount )

		sphereLevelSet["center"].setValue( imath.V3f( 3, 0, 0 ) )
		translatedLeafCount = sphereLevelSet['out'].object( "vdb" ).findGrid( "surface" ).leafCount()
		self.assertTrue( abs( translatedLeafCount - newLeafCount ) < 10 )

	def assertBoundsNearlyEqual( self, lhs, rhs ):
		self.assertAlmostEqual( lhs.min()[0], lhs.min()[0] )
		self.assertAlmostEqual( lhs.min()[1], lhs.min()[1] )
		self.assertAlmostEqual( lhs.min()[2], lhs.min()[2] )

		self.assertAlmostEqual( lhs.max()[0], lhs.max()[0] )
		self.assertAlmostEqual( lhs.max()[1], lhs.max()[1] )
		self.assertAlmostEqual( lhs.max()[2], lhs.max()[2] )

if __name__ == "__main__":
	unittest.main()