##########################################################################
#
#  Copyright (c) 2024, Cinesite VFX Ltd. All rights reserved.
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
import imath

import IECore
import IECoreScene
import IECoreRenderMan

import Gaffer
import GafferTest
import GafferScene

import GafferRenderMan
import GafferSceneTest

@unittest.skipIf( GafferTest.inCI() and os.name == "nt", "RenderMan cannot get license on Windows.")
class RenderManRenderTest( GafferSceneTest.RenderTest ) :

	renderer = "RenderMan"

	def testRepeatedRender( self ) :

		s = Gaffer.ScriptNode()

		s["cube"] = GafferScene.Cube()
		s["cube"]["transform"]["translate"]["z"].setValue( -3 )

		s["camera"] = GafferScene.Camera()
		s["camera"]["fieldOfView"].setValue( 90 )

		s["parent"] = GafferScene.Parent()
		s["parent"]["parent"].setValue( "/" )
		s["parent"]["in"].setInput( s["cube"]["out"] )
		s["parent"]["children"]["child0"].setInput( s["camera"]["out"] )

		s["options"] = GafferScene.StandardOptions()
		s["options"]["in"].setInput( s["parent"]["out"] )
		s["options"]["options"]["render:camera"]["enabled"].setValue( True )
		s["options"]["options"]["render:camera"]["value"].setValue( "/camera" )

		s["outputs"] = GafferScene.Outputs()
		s["outputs"].addOutput(
			"beauty",
			IECoreScene.Output(
				str( self.temporaryDirectory() / "test.exr" ),
				"exr",
				"rgba",
				{
				}
			)
		)
		s["outputs"]["in"].setInput( s["options"]["out"] )

		s["render"] = GafferScene.Render()
		s["render"]["renderer"].setValue( self.renderer )
		s["render"]["in"].setInput( s["outputs"]["out"] )

		for i in range( 10 ) :

			s["render"]["task"].execute()

			image = IECore.Reader.create( str( self.temporaryDirectory() / "test.exr" ) ).read()

			upperPixel = self.__colorAtUV( image, imath.V2f( 0.5, 0.05 ) )
			middlePixel = self.__colorAtUV( image, imath.V2f( 0.5 ) )
			lowerPixel = self.__colorAtUV( image, imath.V2f( 0.5, 0.95 ) )

			self.assertEqual( upperPixel, imath.Color4f( 0 ) )
			self.assertAlmostEqual( middlePixel.g, 1, delta = 0.01 )
			self.assertAlmostEqual( middlePixel.b, 1, delta = 0.01 )
			self.assertAlmostEqual( middlePixel.a, 1, delta = 0.01 )
			self.assertEqual( lowerPixel, imath.Color4f( 0 ) )

	def _createDiffuseShader( self ) :

		shader = GafferRenderMan.RenderManShader()
		shader.loadShader( "PxrDiffuse" )
		return shader, shader["parameters"]["diffuseColor"], shader["out"]

	def _createPointLight( self ) :

		light = GafferRenderMan.RenderManLight()
		light.loadShader( "PxrSphereLight" )
		light["attributes"]["ri:visibility:camera"]["enabled"].setValue( True )
		light["attributes"]["ri:visibility:camera"]["value"].setValue( False )

		return light, light["parameters"]["lightColor"]

	def _createDistantLight( self ) :

		light = GafferRenderMan.RenderManLight()
		light.loadShader( "PxrDistantLight" )
		return light, light["parameters"]["lightColor"]

	def _cameraVisibilityAttribute( self ) :

		return "ri:visibility:camera"

	def __colorAtUV( self, image, uv ) :

		dimensions = image.dataWindow.size() + imath.V2i( 1 )

		ix = int( uv.x * ( dimensions.x - 1 ) )
		iy = int( uv.y * ( dimensions.y - 1 ) )
		i = iy * dimensions.x + ix

		return imath.Color4f( image["R"][i], image["G"][i], image["B"][i], image["A"][i] if "A" in image.keys() else 0.0 )

	@unittest.skip( "Instance IDs only work with encapsulated instancers. We don't have encapsulation support yet in our RenderMan backend" )
	def testInstanceIDOutput( self ) :

		pass

@unittest.skipIf( IECoreRenderMan.renderManMajorVersion() < 27, "XPU only supported for RenderMan 27+" )
class RenderManXPURenderTest( RenderManRenderTest ) :

	renderer = "RenderManXPU"

	## \todo Either find a way of getting float outputs in the style of RIS,
	# or update OpenImageIOReader to load integer IDs via `reinterpret_cast`.
	@unittest.skip( "XPU only renders integer ID outputs, but we want floats" )
	def testIDOutput( self ) :

		pass

if __name__ == "__main__":
	unittest.main()
