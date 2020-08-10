##########################################################################
#
#  Copyright (c) 2018, Esteban Tovagliari. All rights reserved.
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
import unittest

import IECore
import IECoreScene
import IECoreImage

import Gaffer
import GafferTest
import GafferScene
import GafferSceneTest
import GafferImage
import GafferOSL
import GafferAppleseed

from .AppleseedTest import compileOSLShader

class InteractiveAppleseedRenderTest( GafferSceneTest.InteractiveRenderTest ) :

	interactiveRenderNodeClass = GafferAppleseed.InteractiveAppleseedRender

	## \todo Fix error messages and remove. These errors appear to be caused by
	# problems with the default camera code in AppleseedRenderer :
	#
	# ```
	# ERROR : Appleseed : while defining camera "/scene/__default_camera": no "horizontal_fov" or "focal_length" parameter found; using default focal length value "0.035000".
	# ERROR : Appleseed : required parameter "film_dimensions" not found; continuing using value "0.025 0.025".
	# ```
	failureMessageLevel = None

	# Disabled since appleseed does not support multiple beauty outputs.
	@unittest.expectedFailure
	def testAddAndRemoveOutput( self ):

		self.assertTrue( False )

	# Disabled since appleseed does not support trace sets.
	@unittest.expectedFailure
	def testTraceSets( self ) :

		self.assertTrue( False )

	# Disabled since appleseed does not support light filters.
	@unittest.expectedFailure
	def testLightFilters( self ) :

		self.assertTrue( False )

	# Disabled since appleseed does not support light filters.
	@unittest.expectedFailure
	def testLightFiltersAndSetEdits( self ) :

		self.assertTrue( False )

	# Disabled since appleseed does not support light linking.
	@unittest.expectedFailure
	def testHideLinkedLight( self ) :

		self.assertTrue( False )

	# Disabled since appleseed does not support light linking.
	@unittest.expectedFailure
	def testLightLinking( self ) :

		self.assertTrue( False )

	def testMessages( self ) :

		p = GafferScene.Plane()
		i = self._createInteractiveRender()

		i["in"].setInput( p["out"] )

		self.assertEqual( i["messages"].getValue().value.size(), 0 )

		i["state"].setValue( GafferScene.InteractiveRender.State.Running )
		self.uiThreadCallHandler.waitFor( 1 )
		i["state"].setValue( GafferScene.InteractiveRender.State.Stopped )

		self.assertGreater( i["messages"].getValue().value.size(), 0 )

	def _createConstantShader( self ) :

		shader = GafferOSL.OSLShader()
		shader.loadShader(
			compileOSLShader( os.path.dirname( __file__ ) + "/shaders/constant.osl",
			self.temporaryDirectory() ) )
		return shader, shader["parameters"]["constant_color"]

	def _createMatteShader( self ) :

		shader = GafferOSL.OSLShader()
		shader.loadShader(
			compileOSLShader( os.path.dirname( __file__ ) + "/shaders/matte.osl",
			self.temporaryDirectory() ) )
		return shader, shader["parameters"]["Kd_color"]

	def _cameraVisibilityAttribute( self ) :

		return "as:visibility:camera"

	def _createPointLight( self ) :

		light = GafferAppleseed.AppleseedLight( "point_light" )
		light.loadShader( "point_light" )
		return light, light['parameters']['intensity']
