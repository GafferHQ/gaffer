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

import os

import appleseed as asr

import IECore

import Gaffer
import GafferScene
import GafferTest
import GafferAppleseed

from .AppleseedTest import appleseedProjectSchemaPath

class AppleseedAutoInstancingTest( GafferTest.TestCase ) :

	def setUp( self ) :

		GafferTest.TestCase.setUp( self )

		self.__scriptFileName = self.temporaryDirectory() + "/test.gfr"

	def testAutoInstancing( self ) :

		s = Gaffer.ScriptNode()

		s["sphere"] = GafferScene.Sphere( "Sphere" )
		s["sphere1"] = GafferScene.Sphere( "Sphere1" )
		s["sphere2"] = GafferScene.Sphere( "Sphere2" )
		s["sphere3"] = GafferScene.Sphere( "Sphere3" )
		s["sphere4"] = GafferScene.Sphere( "Sphere4" )

		s["group"] = GafferScene.Group( "Group" )
		s["group"]["in"][0].setInput( s["sphere"]["out"] )
		s["group"]["in"][1].setInput( s["sphere1"]["out"] )
		s["group"]["in"][2].setInput( s["sphere2"]["out"] )
		s["group"]["in"][3].setInput( s["sphere3"]["out"] )
		s["group"]["in"][4].setInput( s["sphere4"]["out"] )

		s["render"] = GafferAppleseed.AppleseedRender()
		s["render"]["in"].setInput( s["group"]["out"] )
		s["render"]["mode"].setValue( s["render"].Mode.SceneDescriptionMode )

		projectFilename =  self.temporaryDirectory() + "/test.appleseed"
		s["render"]["fileName"].setValue( projectFilename )
		s["render"]["task"].execute()

		reader = asr.ProjectFileReader()
		options = asr.ProjectFileReaderOptions.OmitReadingMeshFiles
		project = reader.read( projectFilename, appleseedProjectSchemaPath(), options )
		scene = project.get_scene()
		mainAssembly = scene.assemblies().get_by_name( "assembly" )

		self.assertEqual( len( mainAssembly.assemblies() ), 1)
		self.assertEqual( len( mainAssembly.assembly_instances() ), 5 )
		self.assertEqual( len( mainAssembly.objects() ), 0 )
		self.assertEqual( len( mainAssembly.object_instances() ), 0 )

	def testAutoInstancingVaryingAttributes( self ) :

		s = Gaffer.ScriptNode()

		s["sphere"] = GafferScene.Sphere( "Sphere" )
		s["sphere1"] = GafferScene.Sphere( "Sphere1" )
		s["sphere2"] = GafferScene.Sphere( "Sphere2" )
		s["sphere3"] = GafferScene.Sphere( "Sphere3" )
		s["sphere4"] = GafferScene.Sphere( "Sphere4" )

		s["attributes"] = GafferAppleseed.AppleseedAttributes()
		s["attributes"]["in"].setInput( s["sphere4"]["out"] )

		s["attributes"]["attributes"]["shadingSamples"]["enabled"].setValue( True )
		s["attributes"]["attributes"]["shadingSamples"]["value"].setValue( 3 )

		s["group"] = GafferScene.Group( "Group" )
		s["group"]["in"][0].setInput( s["sphere"]["out"] )
		s["group"]["in"][1].setInput( s["sphere1"]["out"] )
		s["group"]["in"][2].setInput( s["sphere2"]["out"] )
		s["group"]["in"][3].setInput( s["sphere3"]["out"] )
		s["group"]["in"][4].setInput( s["attributes"]["out"] )

		s["render"] = GafferAppleseed.AppleseedRender()
		s["render"]["in"].setInput( s["group"]["out"] )
		s["render"]["mode"].setValue( s["render"].Mode.SceneDescriptionMode )

		projectFilename =  self.temporaryDirectory() + "/test.appleseed"
		s["render"]["fileName"].setValue( projectFilename )
		s["render"]["task"].execute()

		reader = asr.ProjectFileReader()
		options = asr.ProjectFileReaderOptions.OmitReadingMeshFiles
		project = reader.read( projectFilename, appleseedProjectSchemaPath(), options )
		scene = project.get_scene()
		mainAssembly = scene.assemblies().get_by_name( "assembly" )

		self.assertEqual( len( mainAssembly.assemblies() ), 1)
		self.assertEqual( len( mainAssembly.assembly_instances() ), 4 )
		self.assertEqual( len( mainAssembly.objects() ), 1 )
		self.assertEqual( len( mainAssembly.object_instances() ), 1 )

if __name__ == "__main__":
	unittest.main()
