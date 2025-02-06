##########################################################################
#
#  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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
#      * Neither the name of Image Engine Design Inc nor the names of
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
import pathlib

import IECore
import IECoreScene
import IECoreVDB

import GafferScene
import GafferVDB
import GafferVDBTest

class LevelSetToMeshTest( GafferVDBTest.VDBTestCase ) :

	def testCanConvertLevelSetToMesh( self ) :

		sphere = GafferScene.Sphere()
		meshToLevelSet = GafferVDB.MeshToLevelSet()
		self.setFilter( meshToLevelSet, path='/sphere' )
		meshToLevelSet["voxelSize"].setValue( 0.05 )
		meshToLevelSet["in"].setInput( sphere["out"] )

		obj = meshToLevelSet["out"].object( "sphere" )

		self.assertTrue( isinstance( obj, IECoreVDB.VDBObject ) )

		self.assertEqual( obj.gridNames(), ['surface'] )
		grid = obj.findGrid( "surface" )

		levelSetToMesh = GafferVDB.LevelSetToMesh()
		self.setFilter( levelSetToMesh, path='/sphere' )
		levelSetToMesh["in"].setInput( meshToLevelSet["out"] )

		mesh = levelSetToMesh["out"].object( "sphere" )
		self.assertTrue( isinstance( mesh, IECoreScene.MeshPrimitive) )

	def testChangingIsoValueDoesntUpdateBounds ( self ) :

		sphere = GafferScene.Sphere()
		sphere["radius"].setValue( 5 )

		meshToLevelSet = GafferVDB.MeshToLevelSet()
		self.setFilter( meshToLevelSet, path='/sphere' )
		meshToLevelSet["voxelSize"].setValue( 0.05 )
		meshToLevelSet["interiorBandwidth"].setValue( 100 )
		meshToLevelSet["in"].setInput( sphere["out"] )

		levelSetToMesh = GafferVDB.LevelSetToMesh()
		self.setFilter( levelSetToMesh, path='/sphere' )
		levelSetToMesh["in"].setInput( meshToLevelSet["out"] )

		self.assertSceneValid( levelSetToMesh["out"] )
		self.assertEqual( levelSetToMesh["out"].bound( "/sphere" ), levelSetToMesh["in"].bound( "/sphere" ) )

	def testIncreasingAdapativityDecreasesPolyCount( self ) :

		sphere = GafferScene.Sphere()
		sphere["radius"].setValue( 5 )

		meshToLevelSet = GafferVDB.MeshToLevelSet()
		self.setFilter( meshToLevelSet, path='/sphere' )
		meshToLevelSet["voxelSize"].setValue( 0.05 )
		meshToLevelSet["exteriorBandwidth"].setValue( 4.0 )
		meshToLevelSet["interiorBandwidth"].setValue( 4.0 )
		meshToLevelSet["in"].setInput( sphere["out"] )

		levelSetToMesh = GafferVDB.LevelSetToMesh()
		self.setFilter( levelSetToMesh, path='/sphere')
		levelSetToMesh["in"].setInput( meshToLevelSet["out"] )

		levelSetToMesh['adaptivity'].setValue(0.0)
		self.assertTrue( 187000 <=  len( levelSetToMesh['out'].object( "sphere" ).verticesPerFace ) <= 188000 )

		levelSetToMesh['adaptivity'].setValue(1.0)
		self.assertTrue( 2800 <= len( levelSetToMesh['out'].object( "sphere" ).verticesPerFace ) <= 3200 )

	def testParallelGetValueComputesObjectOnce( self ) :

		reader = GafferScene.SceneReader()
		reader["fileName"].setValue( pathlib.Path( __file__ ).parent / "data" / "sphere.vdb" )

		pathFilter = GafferScene.PathFilter()
		pathFilter["paths"].setValue( IECore.StringVectorData( [ "/vdb" ] ) )

		levelSetToMesh = GafferVDB.LevelSetToMesh()
		levelSetToMesh["in"].setInput( reader["out"] )
		levelSetToMesh["filter"].setInput( pathFilter["out"] )
		levelSetToMesh["grid"].setValue( "ls_sphere" )

		self.assertParallelGetValueComputesObjectOnce( levelSetToMesh["out"], "/vdb" )

	def testMerging( self ):

		# Quick test of merging a ring of spheres into a torus.
		# This test checks the number of faces produced, which is quick way to check that we're
		# getting the right amount of overlap, but relies on the specific algorithm used by OpenVDB.
		# A future update to OpenVDB might cause this test to fail and require updating, but it would
		# be easy enough to validate these results and update the numbers if that happens. ( An OpenVDB
		# update that changes this algorithm seems possible, but unlikely ).

		sphere = GafferScene.Sphere( "sphere" )

		duplicate = GafferScene.Duplicate( "duplicate" )
		duplicate["in"].setInput( sphere["out"] )
		duplicate["copies"].setValue( 11 )
		duplicate["transform"]["rotate"].setValue( imath.V3f( 0, 30, 0 ) )
		duplicate["transform"]["pivot"].setValue( imath.V3f( -2, 0, 0 ) )
		self.setFilter( duplicate, path='/sphere' )

		freezeTransform = GafferScene.FreezeTransform( "freezeTransform" )
		freezeTransform["enabled"].setValue( False )
		freezeTransform["in"].setInput( duplicate["out"] )
		self.setFilter( freezeTransform, path='/*' )

		meshToLevelSet = GafferVDB.MeshToLevelSet( "meshToLevelSet" )
		meshToLevelSet["in"].setInput( freezeTransform["out"] )
		self.setFilter( meshToLevelSet, path='/*' )

		levelSetToMesh = GafferVDB.LevelSetToMesh( "levelSetToMesh" )
		levelSetToMesh["in"].setInput( meshToLevelSet["out"] )
		self.setFilter( levelSetToMesh, path='/*' )

		# We're not yet merging, so the spheres all get converted to the same mesh
		self.assertEqual( levelSetToMesh["out"].object( "/sphere" ).numFaces(), 1854 )
		self.assertEqual( levelSetToMesh["out"].object( "/sphere6" ).numFaces(), 1854 )

		# Merge into a big donut
		levelSetToMesh["destination"].setValue( '/merged' )

		unfrozen = levelSetToMesh["out"].object( "/merged" )
		self.assertEqual( unfrozen.numFaces(), 11336 )

		# Now try freezing the transform to make sure we get matching results
		freezeTransform["enabled"].setValue( True )

		# The individual spheres are now each a bit different
		levelSetToMesh["destination"].setValue( '${scene:path}' )
		self.assertEqual( levelSetToMesh["out"].object( "/sphere" ).numFaces(), 1854 )
		self.assertEqual( levelSetToMesh["out"].object( "/sphere5" ).numFaces(), 1842 )
		levelSetToMesh["destination"].setValue( '/merged' )

		# The combined mesh is very slightly different ( only because of resampling error
		# when rotating the grids ). The result is different, but not enough to change the
		# face count.
		frozen = levelSetToMesh["out"].object( "/merged" )
		self.assertNotEqual( frozen["P"], unfrozen["P"] )
		self.assertEqual( frozen.numFaces(), 11336 )
