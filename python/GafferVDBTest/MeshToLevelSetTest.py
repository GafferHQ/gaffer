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
import time

import IECore
import IECoreVDB

import Gaffer
import GafferTest
import GafferVDB
import GafferVDBTest
import GafferScene

class MeshToLevelSetTest( GafferVDBTest.VDBTestCase ) :

	def testAffects( self ) :

		sphere = GafferScene.Sphere()
		meshToLevelSet = GafferVDB.MeshToLevelSet()
		meshToLevelSet["in"].setInput( sphere["out"] )

		cs = GafferTest.CapturingSlot( meshToLevelSet.plugDirtiedSignal() )
		self.setFilter( meshToLevelSet, path = "/sphere" )
		self.assertIn( meshToLevelSet["out"]["object"], { x[0] for x in cs } )

		del cs[:]
		sphere["radius"].setValue( 2 )
		self.assertIn( meshToLevelSet["out"]["object"], { x[0] for x in cs } )

	def testCanConvertMeshToLevelSetVolume( self ) :
		sphere = GafferScene.Sphere()
		meshToLevelSet = GafferVDB.MeshToLevelSet()
		self.setFilter( meshToLevelSet, path='/sphere' )
		meshToLevelSet["voxelSize"].setValue( 0.05 )
		meshToLevelSet["in"].setInput( sphere["out"] )

		obj = meshToLevelSet['out'].object( "sphere" )
		self.assertTrue( isinstance( obj, IECoreVDB.VDBObject ) )

		self.assertEqual( obj.gridNames(), ['surface'] )
		grid = obj.findGrid( "surface" )

		meshBounds = sphere['out'].bound( "sphere" )
		vdbBounds = meshToLevelSet['out'].bound( "sphere" )

		self.assertEqual( vdbBounds, meshBounds )
		self.assertEqual( grid.gridClass, "level set" )
		self.assertFalse( obj.unmodifiedFromFile() )
		self.assertFalse( obj.fileName(), "" )

	def testDecreasingVoxelSizeIncreasesLeafCount( self ) :
		sphere = GafferScene.Sphere()
		meshToLevelSet = GafferVDB.MeshToLevelSet()
		self.setFilter( meshToLevelSet, path='/sphere' )
		meshToLevelSet["voxelSize"].setValue( 0.1 )
		meshToLevelSet["in"].setInput( sphere["out"] )

		obj1 = meshToLevelSet['out'].object( "sphere" )
		meshToLevelSet["voxelSize"].setValue( 0.05 )
		obj2 = meshToLevelSet['out'].object( "sphere" )

		ls1 = obj1.findGrid( "surface" )
		ls2 = obj2.findGrid( "surface" )

		self.assertEqual( 56, ls1.leafCount() )
		self.assertEqual( 158, ls2.leafCount() )

	def testIncreasingInteriorOrExteriorBandwidthIncreasesLeafCount( self ) :
		sphere = GafferScene.Sphere()
		sphere["radius"].setValue( 4.0 )

		meshToLevelSet = GafferVDB.MeshToLevelSet()
		self.setFilter( meshToLevelSet, '/sphere' )
		meshToLevelSet["voxelSize"].setValue( 0.1 )
		meshToLevelSet["in"].setInput( sphere["out"] )

		self.assertTrue( 640 <= meshToLevelSet['out'].object( "sphere" ).findGrid( "surface" ).leafCount() <= 650 )

		meshToLevelSet["exteriorBandwidth"].setValue( 4.0 )
		self.assertTrue( 685 <= meshToLevelSet['out'].object( "sphere" ).findGrid( "surface" ).leafCount() <= 695 )

		meshToLevelSet["interiorBandwidth"].setValue( 4.0 )
		self.assertTrue( 715 <= meshToLevelSet['out'].object( "sphere" ).findGrid( "surface" ).leafCount() <= 725 )

	def testCanSpecifyLevelsetGridname( self ) :
		sphere = GafferScene.Sphere()
		meshToLevelSet = GafferVDB.MeshToLevelSet()
		self.setFilter( meshToLevelSet, path='/sphere' )
		meshToLevelSet["voxelSize"].setValue( 0.1 )
		meshToLevelSet["in"].setInput( sphere["out"] )

		obj1 = meshToLevelSet['out'].object( "sphere" )
		self.assertEqual( obj1.gridNames(), ["surface"] )

		meshToLevelSet["grid"].setValue( "fooBar" )
		obj2 = meshToLevelSet['out'].object( "sphere" )
		self.assertEqual( obj2.gridNames(), ["fooBar"] )

	def testCancellation( self ) :

		# Start a computation in the background, and
		# then cancel it.

		script = Gaffer.ScriptNode()

		script["sphere"] = GafferScene.Sphere()

		script["meshToLevelSet"] = GafferVDB.MeshToLevelSet()
		script["meshToLevelSet"]["in"].setInput( script["sphere"]["out"] )
		self.setFilter( script["meshToLevelSet"], path = "/sphere" )
		script["meshToLevelSet"]["voxelSize"].setValue( 0.01 )

		def computeObject() :

			script["meshToLevelSet"]["out"].object( "/sphere" )

		backgroundTask = Gaffer.ParallelAlgo.callOnBackgroundThread(
			script["meshToLevelSet"]["out"]["object"], computeObject
		)
		# Delay so that the computation actually starts, rather
		# than being avoided entirely.
		time.sleep( 0.01 )
		backgroundTask.cancelAndWait()

		# Get the value again. If cancellation has been managed properly, this
		# will do a fresh compute to get a full result, and not pull a half-finished
		# result out of the cache.
		vdbAfterCancellation = script["meshToLevelSet"]["out"].object( "/sphere" )

		# Compare against a result computed from scratch.
		Gaffer.ValuePlug.clearCache()
		vdb = script["meshToLevelSet"]["out"].object( "/sphere" )

		self.assertEqual(
			vdbAfterCancellation.findGrid( "surface" ).activeVoxelCount(),
			vdb.findGrid( "surface" ).activeVoxelCount(),
		)

	def testParallelGetValueComputesObjectOnce( self ) :

		cube = GafferScene.Cube()

		pathFilter = GafferScene.PathFilter()
		pathFilter["paths"].setValue( IECore.StringVectorData( [ "/cube" ] ) )

		meshToLevelSet = GafferVDB.MeshToLevelSet()
		meshToLevelSet["in"].setInput( cube["out"] )
		meshToLevelSet["filter"].setInput( pathFilter["out"] )

		self.assertParallelGetValueComputesObjectOnce( meshToLevelSet["out"], "/cube" )

	@GafferTest.TestRunner.CategorisedTestMethod( { "taskCollaboration:hashAliasing" } )
	def testRecursionViaIntermediateQuery( self ) :

		cube = GafferScene.Cube()

		cubeFilter = GafferScene.PathFilter()
		cubeFilter["paths"].setValue( IECore.StringVectorData( [ "/cube" ] ) )

		# Two identical MeshToLevelSet nodes, with the same input scene.

		meshToLevelSet1 = GafferVDB.MeshToLevelSet()
		meshToLevelSet1["in"].setInput( cube["out"] )
		meshToLevelSet1["filter"].setInput( cubeFilter["out"] )

		meshToLevelSet2 = GafferVDB.MeshToLevelSet()
		meshToLevelSet2["in"].setInput( cube["out"] )
		meshToLevelSet2["filter"].setInput( cubeFilter["out"] )

		# Use a PrimitiveVariableQuery to make one node depend on the other,
		# while keeping the input values they receive identical. Dastardly!

		query = GafferScene.PrimitiveVariableQuery()
		query["scene"].setInput( meshToLevelSet1["out"] )
		query["location"].setValue( "/cube" )
		p = query.addQuery( Gaffer.StringPlug(), "thisVariableDoesNotExist" )
		# Query will fail and output this default value, but not without
		# pulling on `meshToLevelSet1` first.
		p["value"].setValue( "surface" )
		meshToLevelSet2["grid"].setInput( query.valuePlugFromQuery( p ) )

		# The two nodes now have the same hash, despite one depending
		# on the other. This is because `surface` is a StringPlug, which
		# hashes based on value, thanks to de8ab79d6f958cef3b80954798f8083a346945a7.

		self.assertEqual(
			meshToLevelSet2["out"].objectHash( "/cube" ),
			meshToLevelSet1["out"].objectHash( "/cube" )
		)

		# Evict all values from the compute cache, keeping the hashes in
		# the hash cache.

		Gaffer.ValuePlug.clearCache()

		# Now, when we get the value from the downstream node, it will
		# trigger a recursive compute of the upstream node, for the
		# _same_ compute cache entry. If we don't handle this appropriately
		# we'll get deadlock.

		meshToLevelSet2["out"].object( "/cube" )

	def testMerging( self ):

		# Create two non-overlapping spheres
		sphere = GafferScene.Sphere()
		sphere["radius"].setValue( 1.0 )

		sphere2 = GafferScene.Sphere()
		sphere2["name"].setValue( "sphere2" )
		sphere2["radius"].setValue( 1.0 )
		sphere2["transform"]["translate"]["x"].setValue( 5 )

		freezeTransform = GafferScene.FreezeTransform()
		freezeTransform["in"].setInput( sphere2["out"] )
		self.setFilter( freezeTransform, '/sphere2' )

		parent = GafferScene.Parent()
		parent["parent"].setValue( "/" )
		parent["in"].setInput( sphere["out"] )
		parent["children"][0].setInput( freezeTransform["out"] )


		meshToLevelSet = GafferVDB.MeshToLevelSet()
		meshToLevelSet["in"].setInput( parent["out"] )
		self.setFilter( meshToLevelSet, '/*' )

		voxelCountA = meshToLevelSet["out"].object( "/sphere" ).findGrid( "surface" ).activeVoxelCount()
		voxelCountB = meshToLevelSet["out"].object( "/sphere2" ).findGrid( "surface" ).activeVoxelCount()

		# Maybe this could change if OpenVDB's algorithm changes, but I would expect it to be constant
		# unless something weird changes, so might as well check the actual numbers
		self.assertEqual( voxelCountA, 7712 )
		self.assertEqual( voxelCountB, 7712 )

		meshToLevelSet["destination"].setValue( "/merged" )

		# If we write both locations to the same destination, they get merged
		self.assertEqual(
			meshToLevelSet["out"].object( "/merged" ).findGrid( "surface" ).activeVoxelCount(),
			voxelCountA + voxelCountB
		)

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testBasicPerf( self ):
		sphere = GafferScene.Sphere()
		sphere["radius"].setValue( 2.0 )
		sphere["divisions"].setValue( imath.V2i( 1000, 1000 ) )

		meshToLevelSet = GafferVDB.MeshToLevelSet()
		self.setFilter( meshToLevelSet, '/sphere' )
		meshToLevelSet["voxelSize"].setValue( 0.05 )
		meshToLevelSet["in"].setInput( sphere["out"] )

		meshToLevelSet["in"].object( "/sphere" )

		with GafferTest.TestRunner.PerformanceScope() :
			meshToLevelSet["out"].object( "/sphere" )
