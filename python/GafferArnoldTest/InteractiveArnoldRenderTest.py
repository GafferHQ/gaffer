##########################################################################
#
#  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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
import sys
import time
import unittest
import imath

import IECore
import IECoreScene
import IECoreImage

import Gaffer
import GafferTest
import GafferScene
import GafferSceneTest
import GafferImage
import GafferArnold

class InteractiveArnoldRenderTest( GafferSceneTest.InteractiveRenderTest ) :

	def testTwoRenders( self ) :

		s = Gaffer.ScriptNode()
		s["s"] = GafferScene.Sphere()

		s["o"] = GafferScene.Outputs()
		s["o"].addOutput(
			"beauty",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ImageDisplayDriver",
					"handle" : "myLovelySphere",
				}
			)
		)
		s["o"]["in"].setInput( s["s"]["out"] )

		s["r"] = self._createInteractiveRender()
		s["r"]["in"].setInput( s["o"]["out"] )

		s["r"]["state"].setValue( s["r"].State.Running )

		time.sleep( 0.5 )

		image = IECoreImage.ImageDisplayDriver.storedImage( "myLovelySphere" )
		self.assertTrue( isinstance( image, IECoreImage.ImagePrimitive ) )

		# Try to start a second render while the first is running.
		# Arnold is limited to one instance per process, so this
		# will fail miserably.

		s["r2"] = self._createInteractiveRender()
		s["r2"]["in"].setInput( s["o"]["out"] )

		errors = GafferTest.CapturingSlot( s["r2"].errorSignal() )
		s["r2"]["state"].setValue( s["r"].State.Running )

		self.assertEqual( len( errors ), 1 )
		self.assertTrue( "Arnold is already in use" in errors[0][2] )

	def testEditSubdivisionAttributes( self ) :

		script = Gaffer.ScriptNode()

		script["cube"] = GafferScene.Cube()
		script["cube"]["dimensions"].setValue( imath.V3f( 2 ) )

		script["meshType"] = GafferScene.MeshType()
		script["meshType"]["in"].setInput( script["cube"]["out"] )
		script["meshType"]["meshType"].setValue( "catmullClark" )

		script["attributes"] = GafferArnold.ArnoldAttributes()
		script["attributes"]["in"].setInput( script["meshType"]["out"] )
		script["attributes"]["attributes"]["subdivIterations"]["enabled"].setValue( True )

		script["catalogue"] = GafferImage.Catalogue()

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
					"displayPort" : str( script['catalogue'].displayDriverServer().portNumber() ),
					"remoteDisplayType" : "GafferImage::GafferDisplayDriver",
				}
			)
		)
		script["outputs"]["in"].setInput( script["attributes"]["out"] )

		script["imageStats"] = GafferImage.ImageStats()
		script["imageStats"]["in"].setInput( script["catalogue"]["out"] )
		script["imageStats"]["channels"].setValue( IECore.StringVectorData( [ "R", "G", "B", "A" ] ) )
		script["imageStats"]["area"].setValue( imath.Box2i( imath.V2i( 0 ), imath.V2i( 640, 480 ) ) )

		script["options"] = GafferScene.StandardOptions()
		script["options"]["in"].setInput( script["outputs"]["out"] )
		script["options"]["options"]["filmFit"]["enabled"].setValue( True )
		script["options"]["options"]["filmFit"]["value"].setValue( IECoreScene.Camera.FilmFit.Fit )

		script["render"] = self._createInteractiveRender()
		script["render"]["in"].setInput( script["options"]["out"] )

		# Render the cube with one level of subdivision. Check we get roughly the
		# alpha coverage we expect.

		with GafferTest.ParallelAlgoTest.UIThreadCallHandler() as handler :

			script["render"]["state"].setValue( script["render"].State.Running )

			handler.waitFor( 1 )

			self.assertAlmostEqual( script["imageStats"]["average"][3].getValue(), 0.381, delta = 0.001 )

			# Now up the number of subdivision levels. The alpha coverage should
			# increase as the shape tends towards the limit surface.

			script["attributes"]["attributes"]["subdivIterations"]["value"].setValue( 4 )
			handler.waitFor( 1 )

			self.assertAlmostEqual( script["imageStats"]["average"][3].getValue(), 0.424, delta = 0.001 )

			script["render"]["state"].setValue( script["render"].State.Stopped )

	def testLightLinkingAfterParameterUpdates( self ) :

		s = Gaffer.ScriptNode()
		s["catalogue"] = GafferImage.Catalogue()


		s["s"] = GafferScene.Sphere()

		s["PathFilter"] = GafferScene.PathFilter( "PathFilter" )
		s["PathFilter"]["paths"].setValue( IECore.StringVectorData( [ '/sphere' ] ) )

		s["ShaderAssignment"] = GafferScene.ShaderAssignment( "ShaderAssignment" )
		s["ShaderAssignment"]["in"].setInput( s["s"]["out"] )
		s["ShaderAssignment"]["filter"].setInput( s["PathFilter"]["out"] )

		s["lambert"], _ = self._createMatteShader()
		s["ShaderAssignment"]["shader"].setInput( s["lambert"]["out"] )

		s["StandardAttributes"] = GafferScene.StandardAttributes( "StandardAttributes" )
		s["StandardAttributes"]["attributes"]["linkedLights"]["enabled"].setValue( True )
		s["StandardAttributes"]["attributes"]["linkedLights"]["value"].setValue( "defaultLights" )
		s["StandardAttributes"]["filter"].setInput( s["PathFilter"]["out"] )
		s["StandardAttributes"]["in"].setInput( s["ShaderAssignment"]["out"] )

		s["Light"] = GafferArnold.ArnoldLight( "skydome_light" )
		s["Light"].loadShader( "skydome_light" )

		s["FloatToRGB"] = GafferArnold.ArnoldShader( "FloatToRGB" )
		s["FloatToRGB"].loadShader( "float_to_rgb" )
		s["FloatToRGB"]["parameters"]["r"].setValue( 1.0 )
		s["FloatToRGB"]["parameters"]["g"].setValue( 1.0 )
		s["FloatToRGB"]["parameters"]["b"].setValue( 1.0 )

		s["Light"]["parameters"]["color"].setInput( s["FloatToRGB"]["out"] )

		s["c"] = GafferScene.Camera()
		s["c"]["transform"]["translate"]["z"].setValue( 2 )

		s["group"] = GafferScene.Group()
		s["group"]["in"][0].setInput( s["StandardAttributes"]["out"] )
		s["group"]["in"][1].setInput( s["Light"]["out"] )
		s["group"]["in"][2].setInput( s["c"]["out"] )

		s["o"] = GafferScene.Outputs()
		s["o"].addOutput(
			"beauty",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ClientDisplayDriver",
					"displayHost" : "localhost",
					"displayPort" : str( s['catalogue'].displayDriverServer().portNumber() ),
					"remoteDisplayType" : "GafferImage::GafferDisplayDriver",
				}
			)
		)
		s["o"]["in"].setInput( s["group"]["out"] )

		s["so"] = GafferScene.StandardOptions()
		s["so"]["options"]["renderCamera"]["value"].setValue( "/group/camera" )
		s["so"]["options"]["renderCamera"]["enabled"].setValue( True )
		s["so"]["in"].setInput( s["o"]["out"] )

		s["r"] = self._createInteractiveRender()
		s["r"]["in"].setInput( s["so"]["out"] )

		# Start rendering and make sure the light is linked to the sphere

		with GafferTest.ParallelAlgoTest.UIThreadCallHandler() as handler :

			s["r"]["state"].setValue( s["r"].State.Running )

			handler.waitFor( 0.5 )

			c = self._color3fAtUV( s["catalogue"], imath.V2f( 0.5 ) )

			self.assertEqual( c, imath.Color3f( 1.0 ) )

			# Change a value on the light. The light should still be linked to the sphere
			# and we should get the same result as before.
			s["Light"]['parameters']['shadow_density'].setValue( 0.0 )

			handler.waitFor( 0.5 )

			c = self._color3fAtUV( s["catalogue"], imath.V2f( 0.5 ) )

			self.assertEqual( c, imath.Color3f( 1.0 ) )

			s["r"]["state"].setValue( s["r"].State.Stopped )

	def _createInteractiveRender( self ) :

		return GafferArnold.InteractiveArnoldRender()

	def _createConstantShader( self ) :

		shader = GafferArnold.ArnoldShader()
		shader.loadShader( "flat" )
		return shader, shader["parameters"]["color"]

	def _createMatteShader( self ) :

		shader = GafferArnold.ArnoldShader()
		shader.loadShader( "lambert" )
		shader["parameters"]["Kd"].setValue( 1 )
		return shader, shader["parameters"]["Kd_color"]

	def _createTraceSetShader( self ) :
		# It's currently pretty ugly how we need to disable the trace set when it is left empty,
		# to match the behaviour expected by GafferSceneTest.InteractiveRenderTest.
		# Would be somewhat cleaner if we had the primaryInput metadata on trace_set
		# available, so we could just put an expression on it to disable it when no trace set is given,
		# but it doesn't seem very safe to do a metadata load in the middle of the tests
		shaderBox = Gaffer.Box()

		shader = GafferArnold.ArnoldShader("shader")
		shader.loadShader( "standard_surface" )

		shader["parameters"]["base"].setValue( 1 )
		shader["parameters"]["specular_roughness"].setValue( 0 )
		shader["parameters"]["metalness"].setValue( 1 )
		shader["parameters"]["specular_IOR"].setValue( 100 )

		#return shader, Gaffer.StringPlug( "unused" )

		traceSetShader = GafferArnold.ArnoldShader("traceSetShader")
		traceSetShader.loadShader( "trace_set" )
		traceSetShader["parameters"]["passthrough"].setInput( shader["out"] )

		switchShader = GafferArnold.ArnoldShader("switchShader")
		switchShader.loadShader( "switch_shader" )
		switchShader["parameters"]["input0"].setInput( shader["out"] )
		switchShader["parameters"]["input1"].setInput( traceSetShader["out"] )

		shaderBox.addChild( shader )
		shaderBox.addChild( traceSetShader )
		shaderBox.addChild( switchShader )

		shaderBox["enableExpression"] = Gaffer.Expression()
		shaderBox["enableExpression"].setExpression( 'parent.switchShader.parameters.index = parent.traceSetShader.parameters.trace_set != ""', "OSL" )

		Gaffer.PlugAlgo.promote( switchShader["out"] )

		return shaderBox, traceSetShader["parameters"]["trace_set"]

	def _cameraVisibilityAttribute( self ) :

		return "ai:visibility:camera"

	def _traceDepthOptions( self ) :

		return "ai:GI_specular_depth", "ai:GI_diffuse_depth", "ai:GI_transmission_depth"

	def _createPointLight( self ) :

		light = GafferArnold.ArnoldLight()
		light.loadShader( "point_light" )
		return light, light["parameters"]["color"]

	def _createSpotLight( self ) :

		light = GafferArnold.ArnoldLight()
		light.loadShader( "spot_light" )
		return light, light["parameters"]["color"]

	def _createLightFilter( self ) :

		lightFilter = GafferArnold.ArnoldLightFilter()
		lightFilter.loadShader( "light_blocker" )
		return lightFilter, lightFilter["parameters"]["density"]

	def _createGobo( self ) :

		gobo = GafferArnold.ArnoldShader()
		gobo.loadShader( "gobo" )

		return gobo, gobo["parameters"]["slidemap"]

if __name__ == "__main__":
	unittest.main()
