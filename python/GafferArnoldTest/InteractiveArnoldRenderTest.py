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
import time
import unittest

import IECore

import Gaffer
import GafferTest
import GafferScene
import GafferSceneTest
import GafferImage
import GafferArnold

@unittest.skipIf( "TRAVIS" in os.environ, "No license available on Travis" )
class InteractiveArnoldRenderTest( GafferSceneTest.InteractiveRenderTest ) :

	def testTwoRenders( self ) :

		s = Gaffer.ScriptNode()
		s["s"] = GafferScene.Sphere()

		s["o"] = GafferScene.Outputs()
		s["o"].addOutput(
			"beauty",
			IECore.Display(
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

		image = IECore.ImageDisplayDriver.storedImage( "myLovelySphere" )
		self.assertTrue( isinstance( image, IECore.ImagePrimitive ) )

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
		script["cube"]["dimensions"].setValue( IECore.V3f( 2 ) )

		script["meshType"] = GafferScene.MeshType()
		script["meshType"]["in"].setInput( script["cube"]["out"] )
		script["meshType"]["meshType"].setValue( "catmullClark" )

		script["attributes"] = GafferArnold.ArnoldAttributes()
		script["attributes"]["in"].setInput( script["meshType"]["out"] )
		script["attributes"]["attributes"]["subdivIterations"]["enabled"].setValue( True )

		script["outputs"] = GafferScene.Outputs()
		script["outputs"].addOutput(
			"beauty",
			IECore.Display(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ClientDisplayDriver",
					"displayType" : "IECore::ClientDisplayDriver",
					"displayHost" : "localhost",
					"displayPort" : "2500",
					"remoteDisplayType" : "GafferImage::GafferDisplayDriver",
				}
			)
		)
		script["outputs"]["in"].setInput( script["attributes"]["out"] )

		# Emulate the connection the UI makes, so the Display knows someone is listening and
		# it needs to actually make servers.
		dataReceivedConnection = GafferImage.Display.dataReceivedSignal().connect( lambda plug : None )

		script["display"] = GafferImage.Display()
		script["display"]["port"].setValue( 2500 )

		script["imageStats"] = GafferImage.ImageStats()
		script["imageStats"]["in"].setInput( script["display"]["out"] )
		script["imageStats"]["channels"].setValue( IECore.StringVectorData( [ "R", "G", "B", "A" ] ) )
		script["imageStats"]["regionOfInterest"].setValue( IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( 640, 480 ) ) )

		script["render"] = self._createInteractiveRender()
		script["render"]["in"].setInput( script["outputs"]["out"] )

		# Render the cube with one level of subdivision. Check we get roughly the
		# alpha coverage we expect.

		script["render"]["state"].setValue( script["render"].State.Running )
		time.sleep( 1 )

		self.assertAlmostEqual( script["imageStats"]["average"][3].getValue(), 0.381, delta = 0.001 )

		# Now up the number of subdivision levels. The alpha coverage should
		# increase as the shape tends towards the limit surface.

		script["attributes"]["attributes"]["subdivIterations"]["value"].setValue( 4 )
		time.sleep( 1 )

		self.assertAlmostEqual( script["imageStats"]["average"][3].getValue(), 0.424, delta = 0.001 )

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

		# There appears to be no standard Arnold shader
		# which uses trace sets, so we use an AlSurface.
		# If one is not available, the base class will
		# skip the test.

		shader = GafferArnold.ArnoldShader()
		try :
			shader.loadShader( "alSurface" )
		except :
			return None, None

		shader["parameters"]["diffuseStrength"].setValue( 0 )
		shader["parameters"]["specular1Roughness"].setValue( 0 )
		shader["parameters"]["specular1FresnelMode"].setValue( "metallic" )
		shader["parameters"]["specular1Reflectivity"].setValue( IECore.Color3f( 1 ) )
		shader["parameters"]["specular1EdgeTint"].setValue( IECore.Color3f( 1 ) )

		return shader, shader["parameters"]["traceSetSpecular1"]

	def _cameraVisibilityAttribute( self ) :

		return "ai:visibility:camera"

	def _traceDepthOptions( self ) :

		return "ai:GI_glossy_depth", "ai:GI_diffuse_depth", "ai:GI_reflection_depth"

	def _createPointLight( self ) :

		light = GafferArnold.ArnoldLight()
		light.loadShader( "point_light" )
		return light, light["parameters"]["color"]

if __name__ == "__main__":
	unittest.main()
