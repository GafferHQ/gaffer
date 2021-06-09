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

import imath


class PointsGridToPointsTest( GafferVDBTest.VDBTestCase ) :
	def setUp( self ) :
		GafferVDBTest.VDBTestCase.setUp( self )
		self.sourcePath = os.path.join( self.dataDir, "points.vdb" )
		self.sceneInterface = IECoreScene.SceneInterface.create( self.sourcePath, IECore.IndexedIO.OpenMode.Read )

	def testCanConvertPointsGridToPoints( self ) :

		sceneReader = GafferScene.SceneReader( "SceneReader" )
		sceneReader["fileName"].setValue( self.sourcePath )

		pointsFilter = GafferScene.PathFilter()
		pointsFilter["paths"].setValue( IECore.StringVectorData( [ "/vdb" ] ) )

		pointsGridToPoints = GafferVDB.PointsGridToPoints( "PointsGridToPoints" )
		pointsGridToPoints["in"].setInput( sceneReader["out"] )
		pointsGridToPoints["filter"].setInput( pointsFilter["out"] )

		points = pointsGridToPoints["out"].object("/vdb")

		self.assertTrue( isinstance( points, IECoreScene.PointsPrimitive ) )
		self.assertTrue( "P" in points )
		self.assertEqual( len( points["P"].data), 8 )
		self.assertEqual( points["P"].data[0], imath.V3f( -0.500004232, 0.366468042, 0.261457711  ) )

	def testVDBObjectLeftUnchangedIfIncorrectGrid( self ) :

		sceneReader = GafferScene.SceneReader( "SceneReader" )
		sceneReader["fileName"].setValue( self.sourcePath )

		pointsFilter = GafferScene.PathFilter()
		pointsFilter["paths"].setValue( IECore.StringVectorData( [ "/vdb" ] ) )

		pointsGridToPoints = GafferVDB.PointsGridToPoints( "PointsGridToPoints" )
		pointsGridToPoints["in"].setInput( sceneReader["out"] )
		pointsGridToPoints["filter"].setInput( pointsFilter["out"] )
		pointsGridToPoints["grid"].setValue( "nogridhere" )

		vdb = pointsGridToPoints["out"].object("/vdb")
		self.assertTrue( isinstance( vdb, IECoreVDB.VDBObject) )

if __name__ == "__main__":
	unittest.main()
