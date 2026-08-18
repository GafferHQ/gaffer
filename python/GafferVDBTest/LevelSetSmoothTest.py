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

import pathlib
import time

import IECore
import IECoreVDB

import Gaffer
import GafferTest
import GafferScene
import GafferVDB
import GafferVDBTest

## \todo Remove from Gaffer 1.8 once we're building with OpenVDB 12 as a minimum.
try :
	import openvdb
	filletAvailable = True
except ImportError :
	filletAvailable = False

class LevelSetSmoothTest( GafferVDBTest.VDBTestCase ) :

	def testAffects( self ) :

		cube = GafferScene.Cube()

		pathFilter = GafferScene.PathFilter()
		pathFilter["paths"].setValue( IECore.StringVectorData( [ "/cube"] ) )

		meshToLevelSet = GafferVDB.MeshToLevelSet()
		meshToLevelSet["in"].setInput( cube["out"] )
		meshToLevelSet["filter"].setInput( pathFilter["out"] )

		smooth = GafferVDB.LevelSetSmooth()
		smooth["in"].setInput( meshToLevelSet["out"] )
		smooth["filter"].setInput( pathFilter["out"] )

		cs = GafferTest.CapturingSlot( smooth.plugDirtiedSignal() )

		def checkAffected( expected ) :

			self.assertEqual(
				{ i[0].getName() for i in cs if i[0].parent() == smooth["out"] },
				set( expected )
			)
			del cs[:]

		smooth["iterations"].setValue( 2 )
		checkAffected( [ "object", "bound", "childBounds" ] )

		smooth["radius"].setValue( 2 )
		checkAffected( [ "object", "bound", "childBounds" ] )

		smooth["mode"].setValue( GafferVDB.LevelSetSmooth.Mode.Gaussian )
		checkAffected( [ "object", "bound", "childBounds" ] )

		smooth["adjustBounds"].setValue( False )
		checkAffected( [ "bound", "childBounds" ] )

	def testSmoothing( self ) :

		cube = GafferScene.Cube()

		pathFilter = GafferScene.PathFilter()
		pathFilter["paths"].setValue( IECore.StringVectorData( [ "/cube"] ) )

		meshToLevelSet = GafferVDB.MeshToLevelSet()
		meshToLevelSet["in"].setInput( cube["out"] )
		meshToLevelSet["filter"].setInput( pathFilter["out"] )

		inputLevelSet = meshToLevelSet["out"].object( "/cube" )

		smooth = GafferVDB.LevelSetSmooth()
		smooth["in"].setInput( meshToLevelSet["out"] )
		smooth["filter"].setInput( pathFilter["out"] )

		smoothedLevelSet = smooth["out"].object( "/cube" )
		self.assertNotEqual( smoothedLevelSet, inputLevelSet )

		smooth["iterations"].setValue( 4 )

		furtherSmoothedLevelSet = smooth["out"].object( "/cube" )
		self.assertNotEqual( furtherSmoothedLevelSet, smoothedLevelSet )
		self.assertNotEqual( furtherSmoothedLevelSet, inputLevelSet )

		smooth["radius"].setValue( 2 )

		increasedRadiusLevelSet = smooth["out"].object( "/cube" )
		self.assertNotEqual( increasedRadiusLevelSet, furtherSmoothedLevelSet )
		self.assertNotEqual( increasedRadiusLevelSet, smoothedLevelSet )
		self.assertNotEqual( increasedRadiusLevelSet, inputLevelSet )

	def testSmoothingModes( self ) :

		cube = GafferScene.Cube()

		pathFilter = GafferScene.PathFilter()
		pathFilter["paths"].setValue( IECore.StringVectorData( [ "/cube"] ) )

		meshToLevelSet = GafferVDB.MeshToLevelSet()
		meshToLevelSet["in"].setInput( cube["out"] )
		meshToLevelSet["filter"].setInput( pathFilter["out"] )

		inputLevelSet = meshToLevelSet["out"].object( "/cube" )

		smooth = GafferVDB.LevelSetSmooth()
		smooth["in"].setInput( meshToLevelSet["out"] )
		smooth["filter"].setInput( pathFilter["out"] )

		for mode in GafferVDB.LevelSetSmooth.Mode.values.values() :
			with self.subTest( mode = mode ) :

				if mode == GafferVDB.LevelSetSmooth.Mode.Fillet and not filletAvailable :
					continue

				smooth["mode"].setValue( mode )

				smoothedLevelSet = smooth["out"].object( "/cube" )
				self.assertIsInstance( smoothedLevelSet, IECoreVDB.VDBObject )
				self.assertEqual( smoothedLevelSet.gridNames(), [ "surface" ] )

				self.assertNotEqual( smoothedLevelSet, inputLevelSet )

				grid = smoothedLevelSet.findGrid( "surface" )
				self.assertEqual( grid.gridClass, "level set" )

	def testRadiusDoesntAffectMeanCurvatureLaplacianAndFillet( self ) :

		cube = GafferScene.Cube()

		pathFilter = GafferScene.PathFilter()
		pathFilter["paths"].setValue( IECore.StringVectorData( [ "/cube"] ) )

		meshToLevelSet = GafferVDB.MeshToLevelSet()
		meshToLevelSet["in"].setInput( cube["out"] )
		meshToLevelSet["filter"].setInput( pathFilter["out"] )

		smooth = GafferVDB.LevelSetSmooth()
		smooth["in"].setInput( meshToLevelSet["out"] )
		smooth["filter"].setInput( pathFilter["out"] )

		for mode in GafferVDB.LevelSetSmooth.Mode.values.values() :
			with self.subTest( mode = mode ) :

				if mode == GafferVDB.LevelSetSmooth.Mode.Fillet and not filletAvailable :
					continue

				smooth["mode"].setValue( mode )

				smooth["radius"].setValue( 1 )
				smoothedRadius1 = smooth["out"].object( "/cube" )
				hashRadius1 = smooth["out"].objectHash( "/cube" )

				smooth["radius"].setValue( 2 )
				smoothedRadius2 = smooth["out"].object( "/cube" )
				hashRadius2 = smooth["out"].objectHash( "/cube" )

				if mode in ( GafferVDB.LevelSetSmooth.Mode.MeanCurvature, GafferVDB.LevelSetSmooth.Mode.Laplacian, GafferVDB.LevelSetSmooth.Mode.Fillet ) :
					self.assertEqual( smoothedRadius1, smoothedRadius2 )
					self.assertEqual( hashRadius1, hashRadius2 )
				else :
					self.assertNotEqual( smoothedRadius1, smoothedRadius2 )
					self.assertNotEqual( hashRadius1, hashRadius2 )

	def testBounds( self ) :

		cube = GafferScene.Cube()

		pathFilter = GafferScene.PathFilter()
		pathFilter["paths"].setValue( IECore.StringVectorData( [ "/cube"] ) )

		meshToLevelSet = GafferVDB.MeshToLevelSet()
		meshToLevelSet["in"].setInput( cube["out"] )
		meshToLevelSet["filter"].setInput( pathFilter["out"] )

		smooth = GafferVDB.LevelSetSmooth()
		smooth["in"].setInput( meshToLevelSet["out"] )
		smooth["filter"].setInput( pathFilter["out"] )

		self.assertNotEqual( smooth["out"].bound( "/cube" ), meshToLevelSet["out"].bound( "/cube" ) )

		smooth["adjustBounds"].setValue( False )

		self.assertEqual( smooth["out"].bound( "/cube" ), meshToLevelSet["out"].bound( "/cube" ) )

	def testZeroIterations( self ) :

		cube = GafferScene.Cube()

		pathFilter = GafferScene.PathFilter()
		pathFilter["paths"].setValue( IECore.StringVectorData( [ "/cube"] ) )

		meshToLevelSet = GafferVDB.MeshToLevelSet()
		meshToLevelSet["in"].setInput( cube["out"] )
		meshToLevelSet["filter"].setInput( pathFilter["out"] )

		smooth = GafferVDB.LevelSetSmooth()
		smooth["in"].setInput( meshToLevelSet["out"] )
		smooth["filter"].setInput( pathFilter["out"] )

		smooth["iterations"].setValue( 0 )

		self.assertScenesEqual( smooth["out"], meshToLevelSet["out"] )
		self.assertSceneHashesEqual( smooth["out"], meshToLevelSet["out"] )

	def testZeroRadius( self ) :

		cube = GafferScene.Cube()

		pathFilter = GafferScene.PathFilter()
		pathFilter["paths"].setValue( IECore.StringVectorData( [ "/cube"] ) )

		meshToLevelSet = GafferVDB.MeshToLevelSet()
		meshToLevelSet["in"].setInput( cube["out"] )
		meshToLevelSet["filter"].setInput( pathFilter["out"] )

		smooth = GafferVDB.LevelSetSmooth()
		smooth["in"].setInput( meshToLevelSet["out"] )
		smooth["filter"].setInput( pathFilter["out"] )

		smooth["radius"].setValue( 0 )

		for mode in GafferVDB.LevelSetSmooth.Mode.values.values() :
			with self.subTest( mode = mode ) :

				if mode == GafferVDB.LevelSetSmooth.Mode.Fillet and not filletAvailable :
					continue

				smooth["mode"].setValue( mode )

				if mode in ( GafferVDB.LevelSetSmooth.Mode.MeanCurvature, GafferVDB.LevelSetSmooth.Mode.Laplacian, GafferVDB.LevelSetSmooth.Mode.Fillet ) :

					self.assertNotEqual( smooth["out"].object( "/cube" ), meshToLevelSet["out"].object( "/cube" ) )
					self.assertNotEqual( smooth["out"].objectHash( "/cube" ), meshToLevelSet["out"].objectHash( "/cube" ) )

				else :

					self.assertScenesEqual( smooth["out"], meshToLevelSet["out"] )
					self.assertSceneHashesEqual( smooth["out"], meshToLevelSet["out"] )

	def testGridName( self ) :

		cube = GafferScene.Cube()

		pathFilter = GafferScene.PathFilter()
		pathFilter["paths"].setValue( IECore.StringVectorData( [ "/cube"] ) )

		meshToLevelSet = GafferVDB.MeshToLevelSet()
		meshToLevelSet["in"].setInput( cube["out"] )
		meshToLevelSet["filter"].setInput( pathFilter["out"] )
		meshToLevelSet["grid"].setValue( "custom" )

		smooth = GafferVDB.LevelSetSmooth()
		smooth["in"].setInput( meshToLevelSet["out"] )
		smooth["filter"].setInput( pathFilter["out"] )
		smooth["grids"].setValue( "custom" )

		smoothedLevelSet = smooth["out"].object( "/cube" )
		self.assertIsInstance( smoothedLevelSet, IECoreVDB.VDBObject )
		self.assertEqual( smoothedLevelSet.gridNames(), [ "custom" ] )
		self.assertNotEqual( smoothedLevelSet, meshToLevelSet["out"].object( "/cube" ) )

		smooth["grids"].setValue( "missing" )
		missingGridLevelSet = smooth["out"].object( "/cube" )

		self.assertIsInstance( missingGridLevelSet, IECoreVDB.VDBObject )
		self.assertEqual( missingGridLevelSet.gridNames(), [ "custom" ] )
		self.assertEqual( missingGridLevelSet, meshToLevelSet["out"].object( "/cube" ) )

		smooth["grids"].setValue( "*" )
		wildcardLevelSet = smooth["out"].object( "/cube" )
		self.assertIsInstance( wildcardLevelSet, IECoreVDB.VDBObject )
		self.assertEqual( wildcardLevelSet.gridNames(), [ "custom" ] )
		self.assertEqual( wildcardLevelSet, smoothedLevelSet )

	def testNonVDBsPassThrough( self ) :

		cube = GafferScene.Cube()

		pathFilter = GafferScene.PathFilter()
		pathFilter["paths"].setValue( IECore.StringVectorData( [ "/cube" ] ) )

		smooth = GafferVDB.LevelSetSmooth()
		smooth["in"].setInput( cube["out"] )
		smooth["filter"].setInput( pathFilter["out"] )

		self.assertEqual( smooth["out"].object( "/cube" ), smooth["in"].object( "/cube" ) )

	def testCancellation( self ) :

		# Start a computation in the background, and
		# then cancel it.

		script = Gaffer.ScriptNode()

		script["sphere"] = GafferScene.Sphere()

		script["pathFilter"] = GafferScene.PathFilter()
		script["pathFilter"]["paths"].setValue( IECore.StringVectorData( [ "/sphere"] ) )

		script["meshToLevelSet"] = GafferVDB.MeshToLevelSet()
		script["meshToLevelSet"]["in"].setInput( script["sphere"]["out"] )
		script["meshToLevelSet"]["filter"].setInput( script["pathFilter"]["out"] )
		script["meshToLevelSet"]["voxelSize"].setValue( 0.01 )

		script["smooth"] = GafferVDB.LevelSetSmooth()
		script["smooth"]["in"].setInput( script["meshToLevelSet"]["out"] )
		script["smooth"]["filter"].setInput( script["pathFilter"]["out"] )
		script["smooth"]["iterations"].setValue( 4 )

		def computeObject() :

			script["smooth"]["out"].object( "/sphere" )

		backgroundTask = Gaffer.ParallelAlgo.callOnBackgroundThread(
			script["smooth"]["out"]["object"], computeObject
		)
		# Delay so that the computation actually starts, rather
		# than being avoided entirely.
		time.sleep( 0.2 )
		backgroundTask.cancelAndWait()

		# Get the value again. If cancellation has been managed properly, this
		# will do a fresh compute to get a full result, and not pull a half-finished
		# result out of the cache.
		vdbAfterCancellation = script["smooth"]["out"].object( "/sphere" )

		# Compare against a result computed from scratch.
		Gaffer.ValuePlug.clearCache()
		vdb = script["smooth"]["out"].object( "/sphere" )

		self.assertEqual(
			vdbAfterCancellation.findGrid( "surface" ).activeVoxelCount(),
			vdb.findGrid( "surface" ).activeVoxelCount(),
		)

	def testParallelGetValueComputesObjectOnce( self ) :

		reader = GafferScene.SceneReader()
		reader["fileName"].setValue( pathlib.Path( __file__ ).parent / "data" / "sphere.vdb" )

		pathFilter = GafferScene.PathFilter()
		pathFilter["paths"].setValue( IECore.StringVectorData( [ "/vdb" ] ) )

		smooth = GafferVDB.LevelSetSmooth()
		smooth["in"].setInput( reader["out"] )
		smooth["filter"].setInput( pathFilter["out"] )
		smooth["grids"].setValue( "ls_sphere" )

		self.assertParallelGetValueComputesObjectOnce( smooth["out"], "/vdb" )
