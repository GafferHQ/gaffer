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

import GafferTest

import GafferVDB
import IECore
import IECoreScene
import IECoreVDB
import GafferVDBTest
import os
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
