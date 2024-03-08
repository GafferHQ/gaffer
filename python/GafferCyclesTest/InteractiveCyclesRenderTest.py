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

import unittest

import imath

import IECoreScene

import Gaffer
import GafferImage
import GafferScene
import GafferSceneTest
import GafferCycles

class InteractiveCyclesRenderTest( GafferSceneTest.InteractiveRenderTest ) :

	interactiveRenderNodeClass = GafferCycles.InteractiveCyclesRender

	def testSVMRenderWithCPU( self ) :

		# This used to crash due to some unknown problem that looked a lot like
		# memory corruption, and which I assumed was due to the way we swapped
		# between `ccl::Sessions` internally. At one point it crashed 100% reliably
		# but now it doesn't, and I don't know why. Seems like a useful canary to
		# keep around.

		script = Gaffer.ScriptNode()
		script["catalogue"] = GafferImage.Catalogue()
		script["catalogue"]["directory"].setValue( self.temporaryDirectory() )

		script["sphere"] = GafferScene.Sphere()

		script["outputs"] = GafferScene.Outputs()
		script["outputs"].addOutput(
			"beauty",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ClientDisplayDriver",
					"displayHost" : "localhost",
					"displayPort" : str( script["catalogue"].displayDriverServer().portNumber() ),
					"remoteDisplayType" : "GafferImage::GafferDisplayDriver",
				}
			)
		)
		script["outputs"]["in"].setInput( script["sphere"]["out"] )

		script["options"] = GafferCycles.CyclesOptions()
		script["options"]["in"].setInput( script["outputs"]["out"] )
		script["options"]["options"]["shadingSystem"]["enabled"].setValue( True )
		script["options"]["options"]["shadingSystem"]["value"].setValue( "SVM" )

		script["renderer"] = self._createInteractiveRender()
		script["renderer"]["in"].setInput( script["options"]["out"] )

		script["renderer"]["state"].setValue( script["renderer"].State.Running )

		self.uiThreadCallHandler.waitFor( 1.0 )

		script["renderer"]["state"].setValue( script["renderer"].State.Stopped )

		self.uiThreadCallHandler.waitFor( 1.0 )

	@unittest.skip( "Resolution edits not supported yet" )
	def testEditResolution( self ) :

		pass

	@unittest.skip( "Outputs edits not supported yet" )
	def testAddAndRemoveOutput( self ) :

		pass

	@unittest.skip( "Light linking not supported" )
	def testLightLinking( self ) :

		pass

	@unittest.skip( "Light linking not supported" )
	def testHideLinkedLight( self ) :

		pass

	def _createConstantShader( self ) :

		shader = GafferCycles.CyclesShader()
		shader.loadShader( "emission" )
		shader["parameters"]["strength"].setValue( 1 )
		return shader, shader["parameters"]["color"]

	def _createMatteShader( self ) :

		shader = GafferCycles.CyclesShader()
		shader.loadShader( "diffuse_bsdf" )
		return shader, shader["parameters"]["color"]

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
		options["options"]["useAdaptiveSampling"]["enabled"].setValue( True )
		options["options"]["useAdaptiveSampling"]["value"].setValue( False )

		return options

if __name__ == "__main__":
	unittest.main()
