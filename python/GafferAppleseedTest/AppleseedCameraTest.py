##########################################################################
#
#  Copyright (c) 2016, Esteban Tovagliari. All rights reserved.
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

import appleseed as asr

import IECore

import Gaffer
import GafferScene
import GafferTest
import GafferAppleseed

from .AppleseedTest import appleseedProjectSchemaPath

class AppleseedCameraTest( GafferTest.TestCase ) :

	def setUp( self ) :

		GafferTest.TestCase.setUp( self )

		self.__scriptFileName = self.temporaryDirectory() / "test.gfr"

	def testOneCamera( self ) :

		s = Gaffer.ScriptNode()

		s["camera"] = GafferScene.Camera( "Camera" )

		s["options"] = GafferScene.StandardOptions( "StandardOptions" )
		s["options"]["in"].setInput( s["camera"]["out"] )
		s["options"]["options"]["renderCamera"]["value"].setValue( '/camera' )
		s["options"]["options"]["renderCamera"]["enabled"].setValue( True )

		s["render"] = GafferAppleseed.AppleseedRender()
		s["render"]["in"].setInput( s["options"]["out"] )
		s["render"]["mode"].setValue( s["render"].Mode.SceneDescriptionMode )

		projectFilename =  self.temporaryDirectory() / "test.appleseed"
		s["render"]["fileName"].setValue( projectFilename )
		s["render"]["task"].execute()

		reader = asr.ProjectFileReader()
		options = asr.ProjectFileReaderOptions.OmitReadingMeshFiles
		project = reader.read( str( projectFilename ), str( appleseedProjectSchemaPath() ), options )
		scene = project.get_scene()

		self.assertEqual( len( scene.cameras() ), 1 )
		camera = scene.cameras()[ 0 ]
		self.assertEqual( camera.get_name(), "/camera" )

		frame = project.get_frame()
		self.assertEqual( frame.get_parameters()["camera"], camera.get_name() )

	def testMultipleCameras( self ) :

		s = Gaffer.ScriptNode()

		s["camera"] = GafferScene.Camera( "Camera" )
		s["camera2"] = GafferScene.Camera( "Camera2" )
		s["camera3"] = GafferScene.Camera( "Camera3" )

		s["group"] = GafferScene.Group( "Group" )
		s["group"]["in"][0].setInput( s["camera"]["out"] )
		s["group"]["in"][1].setInput( s["camera2"]["out"] )
		s["group"]["in"][2].setInput( s["camera3"]["out"] )

		s["options"] = GafferScene.StandardOptions( "StandardOptions" )
		s["options"]["in"].setInput( s["group"]["out"] )
		s["options"]["options"]["renderCamera"]["value"].setValue( '/group/camera2' )
		s["options"]["options"]["renderCamera"]["enabled"].setValue( True )

		s["render"] = GafferAppleseed.AppleseedRender()
		s["render"]["in"].setInput( s["options"]["out"] )
		s["render"]["mode"].setValue( s["render"].Mode.SceneDescriptionMode )

		projectFilename =  self.temporaryDirectory() / "test.appleseed"
		s["render"]["fileName"].setValue( projectFilename )
		s["render"]["task"].execute()

		reader = asr.ProjectFileReader()
		options = asr.ProjectFileReaderOptions.OmitReadingMeshFiles
		project = reader.read( str( projectFilename ), str( appleseedProjectSchemaPath() ), options )
		scene = project.get_scene()

		self.assertEqual( len( scene.cameras() ), 3 )
		camera = scene.cameras().get_by_name( "/group/camera2" )

		frame = project.get_frame()
		self.assertEqual( frame.get_parameters()["camera"], camera.get_name() )

if __name__ == "__main__":
	unittest.main()
