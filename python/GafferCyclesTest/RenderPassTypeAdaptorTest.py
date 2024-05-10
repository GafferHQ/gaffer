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

import imath

import IECore
import IECoreScene

import Gaffer
import GafferScene
import GafferSceneTest
import GafferCycles

class RenderPassTypeAdaptorTest( GafferSceneTest.SceneTestCase ) :

	def __colorAtUV( self, image, uv ) :

		dimensions = image.dataWindow.size() + imath.V2i( 1 )

		ix = int( uv.x * ( dimensions.x - 1 ) )
		iy = int( uv.y * ( dimensions.y - 1 ) )
		i = iy * dimensions.x + ix

		return imath.Color4f( image["R"][i], image["G"][i], image["B"][i], image["A"][i] if "A" in image.keys() else 0.0 )

	def testShadowPass( self ) :

		s = Gaffer.ScriptNode()

		s["plane"] = GafferScene.Plane()

		s["cube"] = GafferScene.Cube()
		s["cube"]["dimensions"].setValue( imath.V3f( 0.3 ) )

		s["light"] = GafferCycles.CyclesLight()
		s["light"].loadShader( "distant_light" )
		s["light"]["transform"]["rotate"]["x"].setValue( 120 )

		s["group"] = GafferScene.Group()
		## \todo Default camera is facing down +ve Z but should be facing
		# down -ve Z.
		s["group"]["transform"]["translate"]["z"].setValue( 1 )
		s["group"]["in"][0].setInput( s["cube"]["out"] )
		s["group"]["in"][1].setInput( s["plane"]["out"] )
		s["group"]["in"][2].setInput( s["light"]["out"] )

		s["shader"] = GafferCycles.CyclesShader()
		s["shader"].loadShader( "principled_bsdf" )
		s["shader"]["parameters"]["base_color"].setValue( imath.Color3f( 1, 0, 0 ) )

		s["filter"] = GafferScene.PathFilter()
		s["filter"]["paths"].setValue( IECore.StringVectorData( [ "/group/cube", "/group/plane" ] ) )

		s["assignment"] = GafferScene.ShaderAssignment()
		s["assignment"]["in"].setInput( s["group"]["out"] )
		s["assignment"]["shader"].setInput( s["shader"]["out"] )
		s["assignment"]["filter"].setInput( s["filter"]["out"] )

		s["outputs"] = GafferScene.Outputs()
		s["outputs"].addOutput(
			"beauty",
			IECoreScene.Output(
				str( self.temporaryDirectory() / "shadow.exr" ),
				"exr",
				"rgba",
				{
				}
			)
		)
		s["outputs"]["in"].setInput( s["assignment"]["out"] )

		s["options"] = GafferScene.CustomOptions()
		s["options"]["in"].setInput( s["outputs"]["out"] )
		s["options"]["options"].addChild( Gaffer.NameValuePlug( "renderPass:type", "shadow" ) )
		s["options"]["options"].addChild( Gaffer.NameValuePlug( "render:cameraInclusions", "/group/plane" ) )
		s["options"]["options"].addChild( Gaffer.NameValuePlug( "render:cameraExclusions", "/group/cube" ) )

		s["cyclesOptions"] = GafferCycles.CyclesOptions()
		s["cyclesOptions"]["in"].setInput( s["options"]["out"] )
		s["cyclesOptions"]["options"]["samples"]["enabled"].setValue( True )
		s["cyclesOptions"]["options"]["samples"]["value"].setValue( 16 )

		s["render"] = GafferScene.Render()
		s["render"]["renderer"].setValue( "Cycles" )
		s["render"]["in"].setInput( s["cyclesOptions"]["out"] )
		s["render"]["task"].execute()

		image = IECore.Reader.create( str( self.temporaryDirectory() / "shadow.exr" ) ).read()

		upperPixel = self.__colorAtUV( image, imath.V2f( 0.5, 0.05 ) )
		middlePixel = self.__colorAtUV( image, imath.V2f( 0.5 ) )
		lowerPixel = self.__colorAtUV( image, imath.V2f( 0.5, 0.75 ) )

		# Cycles shadow output is black shadows on white
		self.assertEqual( upperPixel, imath.Color4f( 1, 1, 1, 0 ) )
		self.assertEqual( middlePixel, imath.Color4f( 0 ) )
		self.assertEqual( lowerPixel, imath.Color4f( 0 ) )

	def testReflectionPass( self ) :

		s = Gaffer.ScriptNode()

		s["plane"] = GafferScene.Plane()

		s["cube"] = GafferScene.Cube()
		# translate cube behind camera so it is only visible in reflection
		## \todo Default camera is facing down +ve Z but should be facing
		# down -ve Z.
		s["cube"]["transform"]["translate"]["z"].setValue( -3 )

		s["group"] = GafferScene.Group()
		s["group"]["transform"]["translate"]["z"].setValue( 1 )
		s["group"]["in"][0].setInput( s["cube"]["out"] )
		s["group"]["in"][1].setInput( s["plane"]["out"] )

		s["flatRed"] = GafferCycles.CyclesShader()
		s["flatRed"].loadShader( "emission" )
		s["flatRed"]["parameters"]["strength"].setValue( 1 )
		s["flatRed"]["parameters"]["color"].setValue( imath.Color3f( 1, 0, 0 ) )

		s["cubeFilter"] = GafferScene.PathFilter()
		s["cubeFilter"]["paths"].setValue( IECore.StringVectorData( [ "/group/cube" ] ) )

		s["assignment"] = GafferScene.ShaderAssignment()
		s["assignment"]["in"].setInput( s["group"]["out"] )
		s["assignment"]["shader"].setInput( s["flatRed"]["out"] )
		s["assignment"]["filter"].setInput( s["cubeFilter"]["out"] )

		s["flatGreen"] = GafferCycles.CyclesShader()
		s["flatGreen"].loadShader( "emission" )
		s["flatGreen"]["parameters"]["strength"].setValue( 1 )
		s["flatGreen"]["parameters"]["color"].setValue( imath.Color3f( 0, 1, 0 ) )

		s["planeFilter"] = GafferScene.PathFilter()
		s["planeFilter"]["paths"].setValue( IECore.StringVectorData( [ "/group/plane" ] ) )

		s["assignmentGreen"] = GafferScene.ShaderAssignment()
		s["assignmentGreen"]["in"].setInput( s["assignment"]["out"] )
		s["assignmentGreen"]["shader"].setInput( s["flatGreen"]["out"] )
		s["assignmentGreen"]["filter"].setInput( s["planeFilter"]["out"] )

		s["outputs"] = GafferScene.Outputs()
		s["outputs"].addOutput(
			"beauty",
			IECoreScene.Output(
				str( self.temporaryDirectory() / "reflection.exr" ),
				"exr",
				"rgba",
				{
				}
			)
		)
		s["outputs"]["in"].setInput( s["assignmentGreen"]["out"] )

		s["options"] = GafferScene.CustomOptions()
		s["options"]["in"].setInput( s["outputs"]["out"] )
		s["options"]["options"].addChild( Gaffer.NameValuePlug( "renderPass:type", "reflection" ) )
		s["options"]["options"].addChild( Gaffer.NameValuePlug( "render:cameraInclusions", "/group/plane" ) )
		s["options"]["options"].addChild( Gaffer.NameValuePlug( "render:cameraExclusions", "/group/cube" ) )

		s["cyclesOptions"] = GafferCycles.CyclesOptions()
		s["cyclesOptions"]["in"].setInput( s["options"]["out"] )
		s["cyclesOptions"]["options"]["samples"]["enabled"].setValue( True )
		s["cyclesOptions"]["options"]["samples"]["value"].setValue( 8 )

		s["render"] = GafferScene.Render()
		s["render"]["renderer"].setValue( "Cycles" )
		s["render"]["in"].setInput( s["cyclesOptions"]["out"] )
		s["render"]["task"].execute()

		image = IECore.Reader.create( str( self.temporaryDirectory() / "reflection.exr" ) ).read()

		upperPixel = self.__colorAtUV( image, imath.V2f( 0.5, 0.05 ) )
		middlePixel = self.__colorAtUV( image, imath.V2f( 0.5 ) )
		lowerPixel = self.__colorAtUV( image, imath.V2f( 0.5, 0.95 ) )

		self.assertEqual( upperPixel, imath.Color4f( 0 ) )
		self.assertGreater( middlePixel.r, 0.9 )
		self.assertEqual( middlePixel.g, 0.0 )
		self.assertEqual( middlePixel.b, 0.0 )
		self.assertEqual( middlePixel.a, 1.0 )
		self.assertEqual( lowerPixel, imath.Color4f( 0 ) )

	def testReflectionAlphaPass( self ) :

		s = Gaffer.ScriptNode()

		s["plane"] = GafferScene.Plane()

		s["cube"] = GafferScene.Cube()
		# translate cube behind camera so it is only visible in reflection
		## \todo Default camera is facing down +ve Z but should be facing
		# down -ve Z.
		s["cube"]["transform"]["translate"]["z"].setValue( -3 )

		s["group"] = GafferScene.Group()
		s["group"]["transform"]["translate"]["z"].setValue( 1 )
		s["group"]["in"][0].setInput( s["cube"]["out"] )
		s["group"]["in"][1].setInput( s["plane"]["out"] )

		s["flat"] = GafferCycles.CyclesShader()
		s["flat"].loadShader( "emission" )
		s["flat"]["parameters"]["strength"].setValue( 1 )
		s["flat"]["parameters"]["color"].setValue( imath.Color3f( 1, 0, 0 ) )

		s["filter"] = GafferScene.PathFilter()
		s["filter"]["paths"].setValue( IECore.StringVectorData( [ "/group/cube", "/group/plane" ] ) )

		s["assignment"] = GafferScene.ShaderAssignment()
		s["assignment"]["in"].setInput( s["group"]["out"] )
		s["assignment"]["shader"].setInput( s["flat"]["out"] )
		s["assignment"]["filter"].setInput( s["filter"]["out"] )

		s["outputs"] = GafferScene.Outputs()
		s["outputs"].addOutput(
			"beauty",
			IECoreScene.Output(
				str( self.temporaryDirectory() / "reflectionAlpha.exr" ),
				"exr",
				"rgba",
				{
				}
			)
		)
		s["outputs"]["in"].setInput( s["assignment"]["out"] )

		s["options"] = GafferScene.CustomOptions()
		s["options"]["in"].setInput( s["outputs"]["out"] )
		s["options"]["options"].addChild( Gaffer.NameValuePlug( "renderPass:type", "reflectionAlpha" ) )
		s["options"]["options"].addChild( Gaffer.NameValuePlug( "render:cameraInclusions", "/group/plane" ) )
		s["options"]["options"].addChild( Gaffer.NameValuePlug( "render:cameraExclusions", "/group/cube" ) )

		s["cyclesOptions"] = GafferCycles.CyclesOptions()
		s["cyclesOptions"]["in"].setInput( s["options"]["out"] )
		s["cyclesOptions"]["options"]["samples"]["enabled"].setValue( True )
		s["cyclesOptions"]["options"]["samples"]["value"].setValue( 8 )

		s["render"] = GafferScene.Render()
		s["render"]["renderer"].setValue( "Cycles" )
		s["render"]["in"].setInput( s["cyclesOptions"]["out"] )
		s["render"]["task"].execute()

		image = IECore.Reader.create( str( self.temporaryDirectory() / "reflectionAlpha.exr" ) ).read()

		upperPixel = self.__colorAtUV( image, imath.V2f( 0.5, 0.05 ) )
		middlePixel = self.__colorAtUV( image, imath.V2f( 0.5 ) )
		lowerPixel = self.__colorAtUV( image, imath.V2f( 0.5, 0.95 ) )

		self.assertEqual( upperPixel, imath.Color4f( 0 ) )
		self.assertGreater( middlePixel.r, 0.9 )
		self.assertGreater( middlePixel.g, 0.9 )
		self.assertGreater( middlePixel.b, 0.9 )
		self.assertEqual( middlePixel.a, 1.0 )
		self.assertEqual( lowerPixel, imath.Color4f( 0 ) )

if __name__ == "__main__":
	unittest.main()
