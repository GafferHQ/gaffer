##########################################################################
#
#  Copyright (c) 2022, John Haddon. All rights reserved.
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

import GafferSceneTest
import GafferCycles

class CyclesLightTest( GafferSceneTest.SceneTestCase ) :

	def testLoadAllLightsWithoutWarnings( self ) :

		for light in GafferCycles.lights :
			with IECore.CapturingMessageHandler() as mh :
				node = GafferCycles.CyclesLight()
				node.loadShader( light )
				self.assertEqual( [ m.message for m in mh.messages ], [], "Error loading %s" % light )

	def testSpotlightCone( self ) :

		node = GafferCycles.CyclesLight()
		node.loadShader( "spot_light" )

		self.assertEqual( node["parameters"]["spot_angle"].defaultValue(), 45.0 )
		self.assertTrue( node["parameters"]["spot_angle"].isSetToDefault() )
		self.assertEqual( node["parameters"]["spot_smooth"].defaultValue(), 0.0 )
		self.assertTrue( node["parameters"]["spot_smooth"].isSetToDefault() )

		self.assertNotIn( "penumbraAngle", node["parameters"] )
		self.assertNotIn( "coneAngle", node["parameters"] )

		shader = node["out"].attributes( "/light" )["ccl:light"].outputShader()
		self.assertEqual( shader.parameters["spot_angle"].value, 45.0 )
		self.assertEqual( shader.parameters["spot_smooth"].value, 0.0 )

		self.assertNotIn( "penumbraAngle", shader.parameters )
		self.assertNotIn( "coneAngle", shader.parameters )

	def testQuadSpread( self ) :

		node = GafferCycles.CyclesLight()
		node.loadShader( "quad_light" )

		self.assertEqual( node["parameters"]["spread"].defaultValue(), 180.0 )
		self.assertTrue( node["parameters"]["spread"].isSetToDefault() )

		shader = node["out"].attributes( "/light" )["ccl:light"].outputShader()
		self.assertEqual( shader.parameters["spread"].value, 180.0 )

	def testLightAttribute( self ) :

		light = GafferCycles.CyclesLight()
		light.loadShader( "point_light" )

		light["parameters"]["intensity"].setValue( 10 )
		light["parameters"]["exposure"].setValue( 1 )
		light["parameters"]["color"].setValue( imath.Color3f( 1, 2, 3 ) )
		light["parameters"]["size"].setValue( 2 )

		attributes = light["out"].attributes( "/light" )
		self.assertEqual( attributes.keys(), [ "ccl:light" ] )

		shaderNetwork = attributes["ccl:light"]
		self.assertIsInstance( shaderNetwork, IECoreScene.ShaderNetwork )
		self.assertEqual( len( shaderNetwork.shaders() ), 1 )

		shader = shaderNetwork.outputShader()
		self.assertEqual( shader.parameters["intensity"], IECore.FloatData( 10 ) )
		self.assertEqual( shader.parameters["exposure"], IECore.FloatData( 1 ) )
		self.assertEqual( shader.parameters["color"], IECore.Color3fData( imath.Color3f( 1, 2, 3 ) ) )
		self.assertEqual( shader.parameters["size"], IECore.FloatData( 2 ) )

if __name__ == "__main__":
	unittest.main()
