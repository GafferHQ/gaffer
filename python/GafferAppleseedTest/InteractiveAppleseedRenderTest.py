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

from AppleseedTest import compileOSLShader

class InteractiveAppleseedRenderTest( GafferSceneTest.InteractiveRenderTest ) :

	# Disabled since appleseed does not support multiple beauty outputs.
	@unittest.expectedFailure
	def testAddAndRemoveOutput( self ):

		self.assertTrue( False )

	# Disabled since appleseed does not support trace sets.
	@unittest.expectedFailure
	def testTraceSets( self ) :

		self.assertTrue( False )

	def _createInteractiveRender( self ) :

		return GafferAppleseed.InteractiveAppleseedRender()

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
