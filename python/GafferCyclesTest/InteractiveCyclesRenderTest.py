##########################################################################
#
#  Copyright (c) 2022, Cinesite VFX Ltd. All rights reserved.
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

import functools
import unittest

import imath

import IECoreScene

import Gaffer
import GafferScene
import GafferSceneTest
import GafferCycles

class InteractiveCyclesRenderTest( GafferSceneTest.InteractiveRenderTest ) :

	renderer = "Cycles"
	__extraOptions = {}

	def testShaderEditsWithSVM( self ) :

		self.__extraOptions = { "cycles:shadingsystem" : "SVM" }
		GafferSceneTest.InteractiveRenderTest.testShaderEdits( self )

	def testLightsWithSVM( self ) :

		self.__extraOptions = { "cycles:shadingsystem" : "SVM" }
		GafferSceneTest.InteractiveRenderTest.testLights( self )

	def testBasicLightLinkingWithSVM( self ) :

		self.__extraOptions = { "cycles:shadingsystem" : "SVM" }
		GafferSceneTest.InteractiveRenderTest.testBasicLightLinking( self )

	@unittest.skip( "Resolution edits not supported yet" )
	def testEditResolution( self ) :

		pass

	@unittest.skip( "Outputs edits not supported yet" )
	def testAddAndRemoveOutput( self ) :

		pass

	def _createConstantShader( self ) :

		shader = GafferCycles.CyclesShader()
		shader.loadShader( "emission" )
		shader["parameters"]["strength"].setValue( 1 )
		return shader, shader["parameters"]["color"], shader["out"]["emission"]

	def _createMatteShader( self ) :

		shader = GafferCycles.CyclesShader()
		shader.loadShader( "diffuse_bsdf" )
		return shader, shader["parameters"]["color"], shader["out"]["BSDF"]

	def _createTraceSetShader( self ) :

		self.skipTest( "Trace sets not supported" )

	def _cameraVisibilityAttribute( self ) :

		return "cycles:visibility:camera"

	def _createPointLight( self ) :

		light = GafferCycles.CyclesLight()
		light.loadShader( "point_light" )
		return light, light["parameters"]["color"]

	def _createSpotLight( self ) :

		light = GafferCycles.CyclesLight()
		light.loadShader( "spot_light" )
		return light, light["parameters"]["color"]

	def _createLightFilter( self ) :

		self.skipTest( "Light filters not supported" )

	def _createGobo( self ) :

		self.skipTest( "Light filters not supported" )

	def _createOptions( self ) :

		options = GafferCycles.CyclesOptions()

		# We get much better convergence in `testAddLight()` if we disable
		# adaptive sampling.
		options["options"]["cycles:integrator:use_adaptive_sampling"]["enabled"].setValue( True )
		options["options"]["cycles:integrator:use_adaptive_sampling"]["value"].setValue( False )

		for name, value in self.__extraOptions.items() :
			options["options"][name]["enabled"].setValue( True )
			options["options"][name]["value"].setValue( value )

		return options

if __name__ == "__main__":
	unittest.main()
