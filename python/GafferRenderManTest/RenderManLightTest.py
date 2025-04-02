##########################################################################
#
#  Copyright (c) 2019, John Haddon. All rights reserved.
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

import IECore

import Gaffer
import GafferSceneTest
import GafferRenderMan

class RenderManLightTest( GafferSceneTest.SceneTestCase ) :

	def testLoading( self ) :

		light = GafferRenderMan.RenderManLight()
		light.loadShader( "PxrRectLight" )

		self.assertIsInstance( light["parameters"]["intensity"], Gaffer.FloatPlug )
		self.assertIsInstance( light["parameters"]["lightColor"], Gaffer.Color3fPlug )

	def testLoadAllLightTypes( self ) :

		for name in [
			"PxrAovLight", "PxrDistantLight", "PxrMeshLight", "PxrSphereLight",
			"PxrCylinderLight", "PxrDomeLight", "PxrPortalLight",
			"PxrDiskLight", "PxrEnvDayLight", "PxrRectLight",
		] :
			with self.subTest( name = name ) :
				light = GafferRenderMan.RenderManLight()
				light.loadShader( name )

	def testSerialisation( self ) :

		script = Gaffer.ScriptNode()

		script["light"] = GafferRenderMan.RenderManLight()
		script["light"].loadShader( "PxrRectLight" )

		script["light"]["parameters"]["intensity"].setValue( 10 )

		script2 = Gaffer.ScriptNode()
		script2.execute( script.serialise() )

		self.assertEqual( script2["light"]["parameters"]["intensity"].getValue(), 10 )

	def testVisualiserAttributes( self ) :

		light = GafferRenderMan.RenderManLight()
		light.loadShader( "PxrRectLight" )

		self.assertNotIn( "gl:visualiser:scale", light["out"].attributes( "/light" ) )
		light["visualiserAttributes"]["scale"]["enabled"].setValue( True )
		self.assertIn( "gl:visualiser:scale", light["out"].attributes( "/light" ) )

	def testMinMax( self ) :

		light = GafferRenderMan.RenderManLight()
		light.loadShader( "PxrDomeLight" )

		self.assertFalse( light["parameters"]["exposure"].hasMinValue() )
		self.assertTrue( light["parameters"]["intensity"].hasMinValue() )
		self.assertEqual( light["parameters"]["intensity"].minValue(), 0 )

	def testPortalLight( self ) :

		light = GafferRenderMan.RenderManLight()
		light.loadShader( "PxrPortalLight" )
		self.assertEqual(
			set( light["out"].attributes( "/light" )["ri:light"].outputShader().parameters.keys() ),
			{ "intensityMult", "tint" }
		)

	def testCameraVisibility( self ) :

		light = GafferRenderMan.RenderManLight()
		light.loadShader( "PxrRectLight" )
		self.assertNotIn( "ri:visibility:camera", light["out"].attributes( "/light" ) )

		light["attributes"]["ri:visibility:camera"]["enabled"].setValue( True )
		self.assertEqual( light["out"].attributes( "/light" )["ri:visibility:camera"], IECore.IntData( 1 ) )

		light["attributes"]["ri:visibility:camera"]["value"].setValue( 0 )
		self.assertEqual( light["out"].attributes( "/light" )["ri:visibility:camera"], IECore.IntData( 0 ) )

if __name__ == "__main__":
	unittest.main()
