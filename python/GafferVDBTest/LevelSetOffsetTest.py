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

import pathlib

import IECore

import GafferScene
import GafferVDB
import GafferVDBTest

class LevelSetOffsetTest( GafferVDBTest.VDBTestCase ) :

	def testBoundsUpdated( self ) :

		sphere = GafferScene.Sphere()
		sphere["radius"].setValue( 5 )

		meshToLevelSet = GafferVDB.MeshToLevelSet()
		self.setFilter( meshToLevelSet, path='/sphere')
		meshToLevelSet["voxelSize"].setValue( 0.1 )
		meshToLevelSet["in"].setInput( sphere["out"] )

		levelSetOffset = GafferVDB.LevelSetOffset()
		self.setFilter( levelSetOffset, path='/sphere' )
		levelSetOffset["offset"].setValue( 0.0 )
		levelSetOffset["in"].setInput( meshToLevelSet["out"] )

		# sphere centred at the origin so we just take the x value of the max and it should equal the radius
		# hopefully the leafCounts should go like the square of the radius.
		self.assertAlmostEqual( 5.0, levelSetOffset['out'].bound( "sphere" ).max()[0], delta = 0.05 )
		self.assertTrue( 1020 <= levelSetOffset['out'].object( "sphere" ).findGrid( "surface" ).leafCount() <= 1040 )

		levelSetOffset["offset"].setValue( -1.0 )
		self.assertAlmostEqual( 6.0, levelSetOffset['out'].bound( "sphere" ).max()[0], delta = 0.05 )
		self.assertTrue( 1420 <= levelSetOffset['out'].object( "sphere" ).findGrid( "surface" ).leafCount() <= 1450)

		levelSetOffset["offset"].setValue( 1.0 )
		self.assertAlmostEqual( 4.0, levelSetOffset['out'].bound( "sphere" ).max()[0], delta = 0.05 )
		self.assertTrue( 640 <= levelSetOffset['out'].object( "sphere" ).findGrid( "surface" ).leafCount() <= 650)

	def testParallelGetValueComputesObjectOnce( self ) :

		reader = GafferScene.SceneReader()
		reader["fileName"].setValue( pathlib.Path( __file__ ).parent / "data" / "sphere.vdb" )

		pathFilter = GafferScene.PathFilter()
		pathFilter["paths"].setValue( IECore.StringVectorData( [ "/vdb" ] ) )

		offset = GafferVDB.LevelSetOffset()
		offset["in"].setInput( reader["out"] )
		offset["filter"].setInput( pathFilter["out"] )
		offset["grid"].setValue( "ls_sphere" )

		self.assertParallelGetValueComputesObjectOnce( offset["out"], "/vdb" )
