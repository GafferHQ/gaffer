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
import GafferArnold

class RenderPassTypeAdaptorTest( GafferSceneTest.SceneTestCase ) :

	def __colorAtUV( self, image, uv ) :

		dimensions = image.dataWindow.size() + imath.V2i( 1 )

		ix = int( uv.x * ( dimensions.x - 1 ) )
		iy = int( uv.y * ( dimensions.y - 1 ) )
		i = iy * dimensions.x + ix

		return imath.Color4f( image["R"][i], image["G"][i], image["B"][i], image["A"][i] )

	def testShadowPass( self ) :

		s = Gaffer.ScriptNode()

		s["plane"] = GafferScene.Plane()

		s["cube"] = GafferScene.Cube()
		s["cube"]["dimensions"].setValue( imath.V3f( 0.3 ) )

		s["light"] = GafferArnold.ArnoldLight()
		s["light"].loadShader( "distant_light" )
		s["light"]["transform"]["rotate"]["x"].setValue( -60 )

		s["group"] = GafferScene.Group()
		s["group"]["transform"]["translate"]["z"].setValue( -1 )
		s["group"]["in"][0].setInput( s["cube"]["out"] )
		s["group"]["in"][1].setInput( s["plane"]["out"] )
		s["group"]["in"][2].setInput( s["light"]["out"] )

		s["shader"] = GafferArnold.ArnoldShader()
		s["shader"].loadShader( "standard_surface" )
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

		s["render"] = GafferScene.Render()
		s["render"]["renderer"].setValue( "Arnold" )
		s["render"]["in"].setInput( s["options"]["out"] )
		s["render"]["task"].execute()

		image = IECore.Reader.create( str( self.temporaryDirectory() / "shadow.exr" ) ).read()

		upperPixel = self.__colorAtUV( image, imath.V2f( 0.5, 0.05 ) )
		middlePixel = self.__colorAtUV( image, imath.V2f( 0.5 ) )
		lowerPixel = self.__colorAtUV( image, imath.V2f( 0.5, 0.75 ) )

		self.assertEqual( upperPixel, imath.Color4f( 0 ) )
		self.assertEqual( middlePixel, imath.Color4f( 1 ) )
		self.assertEqual( lowerPixel, imath.Color4f( 1 ) )

	def testReflectionPass( self ) :

		s = Gaffer.ScriptNode()

		s["plane"] = GafferScene.Plane()

		s["cube"] = GafferScene.Cube()
		# translate cube behind camera so it is only visible in reflection
		s["cube"]["transform"]["translate"]["z"].setValue( 3 )

		s["group"] = GafferScene.Group()
		s["group"]["transform"]["translate"]["z"].setValue( -1 )
		s["group"]["in"][0].setInput( s["cube"]["out"] )
		s["group"]["in"][1].setInput( s["plane"]["out"] )

		s["flatRed"] = GafferArnold.ArnoldShader()
		s["flatRed"].loadShader( "flat" )
		s["flatRed"]["parameters"]["color"].setValue( imath.Color3f( 1, 0, 0 ) )

		s["cubeFilter"] = GafferScene.PathFilter()
		s["cubeFilter"]["paths"].setValue( IECore.StringVectorData( [ "/group/cube" ] ) )

		s["assignment"] = GafferScene.ShaderAssignment()
		s["assignment"]["in"].setInput( s["group"]["out"] )
		s["assignment"]["shader"].setInput( s["flatRed"]["out"] )
		s["assignment"]["filter"].setInput( s["cubeFilter"]["out"] )

		s["flatGreen"] = GafferArnold.ArnoldShader()
		s["flatGreen"].loadShader( "flat" )
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

		s["render"] = GafferScene.Render()
		s["render"]["renderer"].setValue( "Arnold" )
		s["render"]["in"].setInput( s["options"]["out"] )
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
		s["cube"]["transform"]["translate"]["z"].setValue( 3 )

		s["group"] = GafferScene.Group()
		s["group"]["transform"]["translate"]["z"].setValue( -1 )
		s["group"]["in"][0].setInput( s["cube"]["out"] )
		s["group"]["in"][1].setInput( s["plane"]["out"] )

		s["flat"] = GafferArnold.ArnoldShader()
		s["flat"].loadShader( "flat" )
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

		s["render"] = GafferScene.Render()
		s["render"]["renderer"].setValue( "Arnold" )
		s["render"]["in"].setInput( s["options"]["out"] )
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
