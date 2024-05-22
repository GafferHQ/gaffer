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

import unittest

import imath

import IECore
import IECoreScene

import Gaffer
import GafferScene
import GafferSceneTest

class RenderPassAdaptorTest( GafferSceneTest.SceneTestCase ) :

	# Derived classes should set `renderer` to the name of the renderer
	# to be tested.
	renderer = None

	# Derived classes may set `reverseCamera` if their default camera
	# faces down +ve Z rather than -ve Z.
	reverseCamera = False

	# Derived classes may set `shadowColor` and `litColor` to match
	# their renderer's shadow catcher behaviour.
	shadowColor = imath.Color4f( 1 )
	litColor = imath.Color4f( 0 )

	@classmethod
	def setUpClass( cls ) :

		GafferSceneTest.SceneTestCase.setUpClass()

		if cls.renderer is None :
			# We expect derived classes to set the renderer, and will
			# run the tests there.
			raise unittest.SkipTest( "No renderer available" )

	def testShadowPass( self ) :

		s = Gaffer.ScriptNode()

		s["plane"] = GafferScene.Plane()

		s["cube"] = GafferScene.Cube()
		s["cube"]["dimensions"].setValue( imath.V3f( 0.3 ) )

		s["light"], _ = self._createDistantLight()
		s["light"]["transform"]["rotate"]["x"].setValue( 120 if self.reverseCamera else -60 )

		s["group"] = GafferScene.Group()
		s["group"]["transform"]["translate"]["z"].setValue( 1 if self.reverseCamera else -1 )
		s["group"]["in"][0].setInput( s["cube"]["out"] )
		s["group"]["in"][1].setInput( s["plane"]["out"] )
		s["group"]["in"][2].setInput( s["light"]["out"] )

		s["shader"], colorPlug = self._createStandardShader()
		colorPlug.setValue( imath.Color3f( 1, 0, 0 ) )

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

		s["rendererOptions"] = self._createOptions()
		s["rendererOptions"]["in"].setInput( s["options"]["out"] )

		s["render"] = GafferScene.Render()
		s["render"]["renderer"].setValue( self.renderer )
		s["render"]["in"].setInput( s["rendererOptions"]["out"] )

		for catcher, caster in [
			( "/group/plane", "/group/cube" ),
			( "/group", "/group/cube" ),
			( "/", "/group/cube" ),
			( "/group/plane", "/group" ),
			( "/group/plane", "/" ),
		] :

			with self.subTest( catcher = catcher, caster = caster ) :

				s["options"]["options"]["NameValuePlug1"]["value"].setValue( catcher )
				s["options"]["options"]["NameValuePlug2"]["value"].setValue( caster )

				s["render"]["task"].execute()

				image = IECore.Reader.create( str( self.temporaryDirectory() / "shadow.exr" ) ).read()

				upperPixel = self.__colorAtUV( image, imath.V2f( 0.5, 0.05 ) )
				middlePixel = self.__colorAtUV( image, imath.V2f( 0.5 ) )
				lowerPixel = self.__colorAtUV( image, imath.V2f( 0.5, 0.75 ) )

				self.__assertColorsAlmostEqual( upperPixel, self.litColor, delta = 0.01 )
				self.__assertColorsAlmostEqual( middlePixel, self.shadowColor, delta = 0.01 )
				self.__assertColorsAlmostEqual( lowerPixel, self.shadowColor, delta = 0.01 )

	def testReflectionPass( self ) :

		s = Gaffer.ScriptNode()

		s["plane"] = GafferScene.Plane()

		s["cube"] = GafferScene.Cube()
		# translate cube behind camera so it is only visible in reflection
		s["cube"]["transform"]["translate"]["z"].setValue( -3 if self.reverseCamera else 3 )

		s["group"] = GafferScene.Group()
		s["group"]["transform"]["translate"]["z"].setValue( 1 if self.reverseCamera else -1 )
		s["group"]["in"][0].setInput( s["cube"]["out"] )
		s["group"]["in"][1].setInput( s["plane"]["out"] )

		s["flatRed"], colorPlug = self._createFlatShader()
		colorPlug.setValue( imath.Color3f( 1, 0, 0 ) )

		s["cubeFilter"] = GafferScene.PathFilter()
		s["cubeFilter"]["paths"].setValue( IECore.StringVectorData( [ "/group/cube" ] ) )

		s["assignment"] = GafferScene.ShaderAssignment()
		s["assignment"]["in"].setInput( s["group"]["out"] )
		s["assignment"]["shader"].setInput( s["flatRed"]["out"] )
		s["assignment"]["filter"].setInput( s["cubeFilter"]["out"] )

		s["customAttributes"] = GafferScene.CustomAttributes()
		s["customAttributes"]["in"].setInput( s["assignment"]["out"] )
		# Use an attribute to optionally adjust the reflection catcher roughness.
		s["customAttributes"]["attributes"].addChild( Gaffer.NameValuePlug( "user:renderPass:reflectionCatcher:roughness", 0.5 ) )

		s["flatGreen"], colorPlug = self._createFlatShader()
		colorPlug.setValue( imath.Color3f( 0, 1, 0 ) )

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
		s["outputs"]["in"].setInput( s["customAttributes"]["out"] )

		s["options"] = GafferScene.CustomOptions()
		s["options"]["in"].setInput( s["outputs"]["out"] )
		s["options"]["options"].addChild( Gaffer.NameValuePlug( "renderPass:type", "reflection" ) )
		s["options"]["options"].addChild( Gaffer.NameValuePlug( "render:cameraInclusions", "/group/plane" ) )
		s["options"]["options"].addChild( Gaffer.NameValuePlug( "render:cameraExclusions", "/group/cube" ) )

		s["rendererOptions"] = self._createOptions()
		s["rendererOptions"]["in"].setInput( s["options"]["out"] )

		s["render"] = GafferScene.Render()
		s["render"]["renderer"].setValue( self.renderer )
		s["render"]["in"].setInput( s["rendererOptions"]["out"] )

		for withCustomAttribute, testColor, delta in [
			( False, imath.Color4f( 1, 0, 0, 1 ), 0.01 ),
			( True, imath.Color4f( 0.2, 0, 0, 1 ), 0.15 ),
		] :

			for catcher, caster in [
				( "/group/plane", "/group/cube" ),
				( "/group", "/group/cube" ),
				( "/", "/group/cube" ),
				( "/group/plane", "/group" ),
				( "/group/plane", "/" ),
			] :

				with self.subTest( withCustomAttribute = withCustomAttribute, catcher = catcher, caster = caster ) :

					s["customAttributes"]["enabled"].setValue( withCustomAttribute )
					s["options"]["options"]["NameValuePlug1"]["value"].setValue( catcher )
					s["options"]["options"]["NameValuePlug2"]["value"].setValue( caster )

					s["render"]["task"].execute()

					image = IECore.Reader.create( str( self.temporaryDirectory() / "reflection.exr" ) ).read()

					upperPixel = self.__colorAtUV( image, imath.V2f( 0.5, 0.05 ) )
					middlePixel = self.__colorAtUV( image, imath.V2f( 0.5 ) )
					lowerPixel = self.__colorAtUV( image, imath.V2f( 0.5, 0.95 ) )

					self.__assertColorsAlmostEqual( upperPixel, imath.Color4f( 0 ), delta = 0.01 )
					self.__assertColorsAlmostEqual( middlePixel, testColor, delta = delta )
					self.__assertColorsAlmostEqual( lowerPixel, imath.Color4f( 0 ), delta = 0.01 )

	def testReflectionAlphaPass( self ) :

		s = Gaffer.ScriptNode()

		s["plane"] = GafferScene.Plane()

		s["cube"] = GafferScene.Cube()
		# translate cube behind camera so it is only visible in reflection
		s["cube"]["transform"]["translate"]["z"].setValue( -3 if self.reverseCamera else 3 )

		s["group"] = GafferScene.Group()
		s["group"]["transform"]["translate"]["z"].setValue( 1 if self.reverseCamera else -1 )
		s["group"]["in"][0].setInput( s["cube"]["out"] )
		s["group"]["in"][1].setInput( s["plane"]["out"] )

		s["flat"], colorPlug = self._createFlatShader()
		colorPlug.setValue( imath.Color3f( 1, 0, 0 ) )

		s["filter"] = GafferScene.PathFilter()
		s["filter"]["paths"].setValue( IECore.StringVectorData( [ "/group/cube", "/group/plane" ] ) )

		s["assignment"] = GafferScene.ShaderAssignment()
		s["assignment"]["in"].setInput( s["group"]["out"] )
		s["assignment"]["shader"].setInput( s["flat"]["out"] )
		s["assignment"]["filter"].setInput( s["filter"]["out"] )

		s["customAttributes"] = GafferScene.CustomAttributes()
		s["customAttributes"]["in"].setInput( s["assignment"]["out"] )
		# Use an attribute to optionally adjust the reflection caster colour.
		s["customAttributes"]["attributes"].addChild( Gaffer.NameValuePlug( "user:renderPass:reflectionCaster:color", imath.Color3f( 1, 0, 1 ) ) )

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
		s["outputs"]["in"].setInput( s["customAttributes"]["out"] )

		s["options"] = GafferScene.CustomOptions()
		s["options"]["in"].setInput( s["outputs"]["out"] )
		s["options"]["options"].addChild( Gaffer.NameValuePlug( "renderPass:type", "reflectionAlpha" ) )
		s["options"]["options"].addChild( Gaffer.NameValuePlug( "render:cameraInclusions", "/group/plane" ) )
		s["options"]["options"].addChild( Gaffer.NameValuePlug( "render:cameraExclusions", "/group/cube" ) )

		s["rendererOptions"] = self._createOptions()
		s["rendererOptions"]["in"].setInput( s["options"]["out"] )

		s["render"] = GafferScene.Render()
		s["render"]["renderer"].setValue( self.renderer )
		s["render"]["in"].setInput( s["rendererOptions"]["out"] )

		for withCustomAttribute, testColor in [
			( False, imath.Color4f( 1 ) ),
			( True, imath.Color4f( 1, 0, 1, 1 ) ),
		] :

			for catcher, caster in [
				( "/group/plane", "/group/cube" ),
				( "/group", "/group/cube" ),
				( "/", "/group/cube" ),
				( "/group/plane", "/group" ),
				( "/group/plane", "/" ),
			] :

				with self.subTest( withCustomAttribute = withCustomAttribute, catcher = catcher, caster = caster ) :

					s["customAttributes"]["enabled"].setValue( withCustomAttribute )
					s["options"]["options"]["NameValuePlug1"]["value"].setValue( catcher )
					s["options"]["options"]["NameValuePlug2"]["value"].setValue( caster )

					s["render"]["task"].execute()

					image = IECore.Reader.create( str( self.temporaryDirectory() / "reflectionAlpha.exr" ) ).read()

					upperPixel = self.__colorAtUV( image, imath.V2f( 0.5, 0.05 ) )
					middlePixel = self.__colorAtUV( image, imath.V2f( 0.5 ) )
					lowerPixel = self.__colorAtUV( image, imath.V2f( 0.5, 0.95 ) )

					self.__assertColorsAlmostEqual( upperPixel, imath.Color4f( 0 ), delta = 0.01 )
					self.__assertColorsAlmostEqual( middlePixel, testColor, delta = 0.01 )
					self.__assertColorsAlmostEqual( lowerPixel, imath.Color4f( 0 ), delta = 0.01 )

	def testReflectionCasterLightLinks( self ) :

		s = Gaffer.ScriptNode()

		s["plane"] = GafferScene.Plane()

		s["cube"] = GafferScene.Cube()
		# translate cube behind camera so it is only visible in reflection
		s["cube"]["transform"]["translate"]["z"].setValue( -3 if self.reverseCamera else 3 )

		s["light"], _ = self._createDistantLight()
		s["light"]["transform"]["rotate"]["x"].setValue( 30 if self.reverseCamera else -150 )

		s["group"] = GafferScene.Group()
		s["group"]["transform"]["translate"]["z"].setValue( 1 if self.reverseCamera else -1 )
		s["group"]["in"][0].setInput( s["cube"]["out"] )
		s["group"]["in"][1].setInput( s["plane"]["out"] )
		s["group"]["in"][2].setInput( s["light"]["out"] )

		s["flatRed"], colorPlug = self._createStandardShader()
		colorPlug.setValue( imath.Color3f( 1, 0, 0 ) )

		s["cubeFilter"] = GafferScene.PathFilter()
		s["cubeFilter"]["paths"].setValue( IECore.StringVectorData( [ "/group/cube" ] ) )

		s["assignment"] = GafferScene.ShaderAssignment()
		s["assignment"]["in"].setInput( s["group"]["out"] )
		s["assignment"]["shader"].setInput( s["flatRed"]["out"] )
		s["assignment"]["filter"].setInput( s["cubeFilter"]["out"] )

		s["flatGreen"], colorPlug = self._createFlatShader()
		colorPlug.setValue( imath.Color3f( 0, 1, 0 ) )

		s["planeFilter"] = GafferScene.PathFilter()
		s["planeFilter"]["paths"].setValue( IECore.StringVectorData( [ "/group/plane" ] ) )

		s["assignmentGreen"] = GafferScene.ShaderAssignment()
		s["assignmentGreen"]["in"].setInput( s["assignment"]["out"] )
		s["assignmentGreen"]["shader"].setInput( s["flatGreen"]["out"] )
		s["assignmentGreen"]["filter"].setInput( s["planeFilter"]["out"] )

		s["standardAttributes"] = GafferScene.StandardAttributes()
		s["standardAttributes"]["in"].setInput( s["assignmentGreen"]["out"] )

		s["outputs"] = GafferScene.Outputs()
		s["outputs"].addOutput(
			"beauty",
			IECoreScene.Output(
				str( self.temporaryDirectory() / "lightLinking.exr" ),
				"exr",
				"rgba",
				{
				}
			)
		)
		s["outputs"]["in"].setInput( s["standardAttributes"]["out"] )

		s["options"] = GafferScene.CustomOptions()
		s["options"]["in"].setInput( s["outputs"]["out"] )
		# We test reflection casters that are descendants of catchers to ensure their
		# attributes (such as linkedLights) aren't stomped on by the overrides required for a catcher.
		s["options"]["options"].addChild( Gaffer.NameValuePlug( "renderPass:type", "reflection" ) )
		s["options"]["options"].addChild( Gaffer.NameValuePlug( "render:cameraInclusions", "/group" ) )
		s["options"]["options"].addChild( Gaffer.NameValuePlug( "render:cameraExclusions", "/group/cube" ) )

		s["rendererOptions"] = self._createOptions()
		s["rendererOptions"]["in"].setInput( s["options"]["out"] )

		s["render"] = GafferScene.Render()
		s["render"]["renderer"].setValue( self.renderer )
		s["render"]["in"].setInput( s["rendererOptions"]["out"] )

		for lightLinks, testColor in [
			( None, imath.Color4f( 0.25, 0, 0, 1 ) ),
			( "__lights", imath.Color4f( 0.25, 0, 0, 1 ) ),
			( "", imath.Color4f( 0, 0, 0, 1 ) ),
		] :

			with self.subTest( lightLinks = lightLinks ) :

				s["standardAttributes"]["attributes"]["linkedLights"]["enabled"].setValue( lightLinks is not None )
				s["standardAttributes"]["attributes"]["linkedLights"]["value"].setValue( lightLinks or "" )

				s["render"]["task"].execute()

				image = IECore.Reader.create( str( self.temporaryDirectory() / "lightLinking.exr" ) ).read()

				upperPixel = self.__colorAtUV( image, imath.V2f( 0.5, 0.05 ) )
				middlePixel = self.__colorAtUV( image, imath.V2f( 0.5 ) )
				lowerPixel = self.__colorAtUV( image, imath.V2f( 0.5, 0.95 ) )

				self.__assertColorsAlmostEqual( upperPixel, imath.Color4f( 0 ), delta = 0.01 )
				self.assertGreaterEqual( middlePixel.r, testColor.r )
				self.assertAlmostEqual( middlePixel.g, testColor.g, delta = 0.01)
				self.assertAlmostEqual( middlePixel.b, testColor.b, delta = 0.01 )
				self.assertAlmostEqual( middlePixel.a, testColor.a, delta = 0.01 )
				self.__assertColorsAlmostEqual( lowerPixel, imath.Color4f( 0 ), delta = 0.01 )

	# Should be implemented by derived classes to return
	# an appropriate Light node with a distant light loaded.
	def _createDistantLight( self ) :

		raise NotImplementedError

	# Should be implemented by derived classes to return
	# an appropriate Shader node with a standard shader loaded.
	def _createStandardShader( self ) :

		raise NotImplementedError

	# Should be implemented by derived classes to return
	# an appropriate Shader node with a flat shader loaded.
	def _createFlatShader( self ) :

		raise NotImplementedError

	# May be implemented to return a node to set any renderer-specific
	# options that should be used by the tests.
	def _createOptions( self ) :

		return GafferScene.CustomOptions()

	def __colorAtUV( self, image, uv ) :

		dimensions = image.dataWindow.size() + imath.V2i( 1 )

		ix = int( uv.x * ( dimensions.x - 1 ) )
		iy = int( uv.y * ( dimensions.y - 1 ) )
		i = iy * dimensions.x + ix

		return imath.Color4f( image["R"][i], image["G"][i], image["B"][i], image["A"][i] if "A" in image.keys() else 0.0 )

	def __assertColorsAlmostEqual( self, c0, c1, **kw ) :

		for i in range( 0, 4 ) :
			self.assertAlmostEqual( c0[i], c1[i], **kw )

if __name__ == "__main__":
	unittest.main()
