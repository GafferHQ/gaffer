##########################################################################
#
#  Copyright (c) 2014, Esteban Tovagliari. All rights reserved.
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
import GafferTest
import GafferAppleseed

from .AppleseedTest import appleseedProjectSchemaPath

class AppleseedLightTest( GafferTest.TestCase ) :

	def setUp( self ) :

		GafferTest.TestCase.setUp( self )

		self.__scriptFileName = self.temporaryDirectory() / "test.gfr"

	def testAppleseedLatLongEnvironmentEDF( self ) :

		l = GafferAppleseed.AppleseedLight( "latlong_map_environment_edf" )
		l.loadShader( "latlong_map_environment_edf" )

		self.assertIn( "radiance_map", l["parameters"] )
		self.assertEqual( l["parameters"]["radiance_map"].typeName(), "Gaffer::StringPlug" )

		self.assertIn( "radiance_multiplier", l["parameters"] )
		self.assertEqual( l["parameters"]["radiance_multiplier"].typeName(), "Gaffer::FloatPlug" )

	def testAppleseedMirrorBallEnvironmentEDF( self ) :

		l = GafferAppleseed.AppleseedLight( "mirrorball_map_environment_edf" )
		l.loadShader( "mirrorball_map_environment_edf" )

		self.assertIn( "radiance_map", l["parameters"] )
		self.assertEqual( l["parameters"]["radiance_map"].typeName(), "Gaffer::StringPlug" )

		self.assertIn( "radiance_multiplier", l["parameters"] )
		self.assertEqual( l["parameters"]["radiance_multiplier"].typeName(), "Gaffer::FloatPlug" )

	def testFloatMultiplierPlugs( self ) :

		l = GafferAppleseed.AppleseedLight( "point_light" )
		l.loadShader( "point_light" )

		self.assertIn( "intensity_multiplier", l["parameters"] )
		self.assertEqual( l["parameters"]["intensity_multiplier"].typeName(), "Gaffer::FloatPlug" )

	def testRectLightVisibilityAttributes( self ) :

		s = Gaffer.ScriptNode()

		s["diffuse_edf"] = GafferAppleseed.AppleseedLight( "diffuse_edf" )
		s["diffuse_edf"].loadShader( "diffuse_edf" )

		s["AppleseedAttributes"] = GafferAppleseed.AppleseedAttributes( "AppleseedAttributes" )
		s["AppleseedAttributes"]["in"].setInput( s["diffuse_edf"]["out"] )
		s["AppleseedAttributes"]["attributes"]["cameraVisibility"]["value"].setValue( False )
		s["AppleseedAttributes"]["attributes"]["cameraVisibility"]["enabled"].setValue( True )
		s["AppleseedAttributes"]["attributes"]["cameraVisibility"]["value"].setValue( False )
		s["AppleseedAttributes"]["attributes"]["cameraVisibility"]["enabled"].setValue( True )
		s["AppleseedAttributes"]["attributes"]["lightVisibility"]["value"].setValue( False )
		s["AppleseedAttributes"]["attributes"]["lightVisibility"]["enabled"].setValue( True )
		s["AppleseedAttributes"]["attributes"]["shadowVisibility"]["value"].setValue( False )
		s["AppleseedAttributes"]["attributes"]["shadowVisibility"]["enabled"].setValue( True )
		s["AppleseedAttributes"]["attributes"]["diffuseVisibility"]["value"].setValue( False )
		s["AppleseedAttributes"]["attributes"]["diffuseVisibility"]["enabled"].setValue( True )
		s["AppleseedAttributes"]["attributes"]["specularVisibility"]["value"].setValue( False )
		s["AppleseedAttributes"]["attributes"]["specularVisibility"]["enabled"].setValue( True )
		s["AppleseedAttributes"]["attributes"]["glossyVisibility"]["value"].setValue( False )
		s["AppleseedAttributes"]["attributes"]["glossyVisibility"]["enabled"].setValue( True )

		s["render"] = GafferAppleseed.AppleseedRender( "AppleseedRender" )
		s["render"]["in"].setInput( s["AppleseedAttributes"]["out"] )
		s["render"]["mode"].setValue( s["render"].Mode.SceneDescriptionMode )

		projectFilename =  self.temporaryDirectory() / "test.appleseed"
		s["render"]["fileName"].setValue( projectFilename )
		s["render"]["task"].execute()

		reader = asr.ProjectFileReader()
		options = asr.ProjectFileReaderOptions.OmitReadingMeshFiles
		project = reader.read( str( projectFilename ), str( appleseedProjectSchemaPath() ), options )
		scene = project.get_scene()
		mainAssembly = scene.assemblies().get_by_name( "assembly" )

		objInstance = mainAssembly.object_instances()[0]
		params = objInstance.get_parameters()

		visFlags = params['visibility']
		self.assertFalse(visFlags['camera'])
		self.assertFalse(visFlags['diffuse'])
		self.assertFalse(visFlags['glossy'])
		self.assertFalse(visFlags['light'])
		self.assertFalse(visFlags['shadow'])
		self.assertFalse(visFlags['specular'])

if __name__ == "__main__":
	unittest.main()
