##########################################################################
#
#  Copyright (c) 2023, Cinesite VFX Ltd. All rights reserved.
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
#      * Neither the name of Image Engine Design Inc nor the names of
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
import GafferUSD
import GafferScene
import GafferSceneTest

class USDLightTest( GafferSceneTest.SceneTestCase ) :

	def testLoad( self ) :

		light = GafferUSD.USDLight()
		for name in ( "DistantLight", "DiskLight", "DomeLight", "RectLight", "SphereLight", "CylinderLight" ) :
			light.loadShader( name )

	def testShaderNetwork( self ) :

		light = GafferUSD.USDLight()
		light.loadShader( "SphereLight" )

		attributes = light["out"].attributes( "/light" )
		self.assertIn( "light", attributes )
		network = attributes["light"]
		self.assertIsInstance( network, IECoreScene.ShaderNetwork )

		self.assertEqual( len( network ), 1 )
		shader = network.outputShader()
		self.assertEqual( shader.name, "SphereLight" )

	def testSerialisation( self ) :

		script = Gaffer.ScriptNode()
		script["light"] = GafferUSD.USDLight()
		script["light"].loadShader( "RectLight" )
		script["light"]["parameters"]["exposure"].setValue( 10 )

		script2 = Gaffer.ScriptNode()
		script2.execute( script.serialise() )
		self.assertEqual( script2["light"]["name"].getValue(), script["light"]["name"].getValue() )
		self.assertEqual( script2["light"]["parameters"].keys(), script["light"]["parameters"].keys() )
		self.assertEqual( script2["light"]["parameters"]["exposure"].getValue(), script["light"]["parameters"]["exposure"].getValue() )

	def testShapingAndShadowAPIs( self ) :

		light = GafferUSD.USDLight()
		light.loadShader( "SphereLight" )

		# Check that inputs are wrapped in an OptionalValuePlug

		for name, defaultValue in {
			"shaping:cone:angle" : 90.0,
			"shaping:cone:softness" : 0.0,
			"shaping:focus" : 0.0,
			"shaping:focusTint" : imath.Color3f( 0 ),
			"shaping:ies:angleScale" : 0,
			"shaping:ies:file" : "",
			"shaping:ies:normalize" : False,
			"shadow:color" : imath.Color3f( 0 ),
			"shadow:distance" : -1.0,
			"shadow:enable" : True,
			"shadow:falloff" : -1.0,
			"shadow:falloffGamma" : 1.0,
		}.items() :
			with self.subTest( name = name ) :
				self.assertIn( name, light["parameters"] )
				self.assertIsInstance( light["parameters"][name], Gaffer.OptionalValuePlug )
				self.assertEqual( light["parameters"][name]["enabled"].defaultValue(), False )
				self.assertEqual( light["parameters"][name]["enabled"].getValue(), False )
				self.assertEqual( light["parameters"][name]["value"].defaultValue(), defaultValue )
				self.assertEqual( light["parameters"][name]["value"].getValue(), defaultValue )

		# Check that reload keeps existing values and connections

		light["parameters"]["shaping:cone:angle"]["value"].setValue( 10 )
		light["parameters"]["shaping:cone:softness"]["value"].setInput(
			light["parameters"]["shaping:focus"]["value"]
		)

		light.loadShader( "SphereLight", keepExistingValues = True )

		self.assertEqual( light["parameters"]["shaping:cone:angle"]["value"].getValue(), 10 )
		self.assertEqual(
			light["parameters"]["shaping:cone:softness"]["value"].getInput(),
			light["parameters"]["shaping:focus"]["value"]
		)

if __name__ == "__main__":
	unittest.main()
