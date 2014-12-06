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

import os

import IECore

import Gaffer
import GafferTest
import GafferAppleseed
import GafferAppleseedUI

class AppleseedLightsTest( GafferTest.TestCase ) :

	def testAppleseedLatLongEnvironmentEDF( self ) :

		l = GafferAppleseedUI.LightMenu._lightCreator( "latlong_map_environment_edf" )
		self.failUnless( "radiance_map" in l["parameters"] )
		self.failUnless( l["parameters"]["radiance_map"].typeName() == "Gaffer::StringPlug" )

		self.failUnless( "radiance_multiplier" in l["parameters"] )
		self.failUnless( l["parameters"]["radiance_multiplier"].typeName() == "Gaffer::FloatPlug" )

	def testAppleseedMirrorBallEnvironmentEDF( self ) :
	
		l = GafferAppleseedUI.LightMenu._lightCreator( "mirrorball_map_environment_edf" )
		self.failUnless( "radiance_map" in l["parameters"] )
		self.failUnless( l["parameters"]["radiance_map"].typeName() == "Gaffer::StringPlug" )

		self.failUnless( "radiance_multiplier" in l["parameters"] )
		self.failUnless( l["parameters"]["radiance_multiplier"].typeName() == "Gaffer::FloatPlug" )

	def testFloatMultiplierPlugs( self ) :
		
		l = GafferAppleseedUI.LightMenu._lightCreator( "point_light" )
		self.failUnless( "intensity_multiplier" in l["parameters"] )
		self.failUnless( l["parameters"]["intensity_multiplier"].typeName() == "Gaffer::FloatPlug" )

	def setUp( self ) :

		GafferAppleseedUI.LightMenu._parseEntitiesMetadata()

	def tearDown( self ) :

		if os.path.isfile( "/tmp/as_input_metadata.xml" ) :
			os.remove( "/tmp/as_input_metadata.xml" )

if __name__ == "__main__":
	unittest.main()
