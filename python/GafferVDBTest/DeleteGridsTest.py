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

import IECore

import GafferVDB
import GafferVDBTest
import GafferScene

class DeleteGridsTest( GafferVDBTest.VDBTestCase ) :

	def test( self ) :

		smoke = GafferScene.SceneReader()
		smoke["fileName"].setValue( self.dataDir / "smoke.vdb" )
		self.assertEqual( smoke["out"].object( "/vdb" ).gridNames(), [ "density" ] )

		points = GafferScene.SceneReader()
		points["fileName"].setValue( self.dataDir / "points.vdb" )
		self.assertEqual( points["out"].object( "/vdb" ).gridNames(), [ "points" ] )

		group = GafferScene.Group()
		group["in"][0].setInput( smoke["out"] )
		group["in"][1].setInput( points["out"] )

		pathFilter = GafferScene.PathFilter()

		deleteGrids = GafferVDB.DeleteGrids()
		deleteGrids["in"].setInput( group["out"] )
		deleteGrids["filter"].setInput( pathFilter["out"] )

		self.assertScenesEqual( deleteGrids["out"], deleteGrids["in"] )
		self.assertSceneHashesEqual( deleteGrids["out"], deleteGrids["in"] )

		pathFilter["paths"].setValue(
			IECore.StringVectorData( [ "/group/*" ] )
		)

		self.assertScenesEqual( deleteGrids["out"], deleteGrids["in"] )

		deleteGrids["grids"].setValue( "points" )
		self.assertEqual( deleteGrids["out"].object( "/group/vdb" ).gridNames(), [ "density" ] )
		self.assertEqual( deleteGrids["out"].object( "/group/vdb1" ).gridNames(), [] )

		deleteGrids["mode"].setValue( deleteGrids.Mode.Keep )
		self.assertEqual( deleteGrids["out"].object( "/group/vdb" ).gridNames(), [] )
		self.assertEqual( deleteGrids["out"].object( "/group/vdb1" ).gridNames(), [ "points" ] )
