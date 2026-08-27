##########################################################################
#
#  Copyright (c) 2025, Cinesite VFX Ltd. All rights reserved.
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

import IECoreScene

import Gaffer
import GafferSceneTest
import GafferRenderMan

class RenderManLightFilterTest( GafferSceneTest.SceneTestCase ) :

	def testLoadShader( self ) :

		lightFilter = GafferRenderMan.RenderManLightFilter()
		lightFilter.loadShader( "PxrBarnLightFilter" )

		for name, value in {
			"width" : 1.0,
			"height" : 1.0,
			"radius" : 0.5,
			"density" : 1.0,
		}.items() :

			self.assertIn( name, lightFilter["parameters"] )
			self.assertEqual( lightFilter["parameters"][name].getValue(), value )
			self.assertEqual( lightFilter["parameters"][name].defaultValue(), value )

	def testAttributes( self ) :

		lightFilter = GafferRenderMan.RenderManLightFilter()
		lightFilter.loadShader( "PxrBarnLightFilter" )

		attributes = lightFilter["out"].attributes( "/lightFilter" )
		self.assertEqual( attributes.keys(), [ "ri:lightFilter" ] )
		network = attributes["ri:lightFilter"]
		self.assertIsInstance( network, IECoreScene.ShaderNetwork )
		self.assertEqual( len( network.shaders() ), 1 )
		shader = network.outputShader()
		self.assertEqual( shader.name, "PxrBarnLightFilter" )
		self.assertEqual( shader.parameters["width"].value, 1.0 )

	def testSerialisation( self ) :

		script = Gaffer.ScriptNode()

		script["lightFilter"] = GafferRenderMan.RenderManLightFilter()
		script["lightFilter"].loadShader( "PxrCookieLightFilter" )

		script2 = Gaffer.ScriptNode()
		script2.execute( script.serialise() )

		self.assertEqual( script2["lightFilter"]["parameters"].keys(), script2["lightFilter"]["parameters"].keys() )

		for plug in script2["lightFilter"]['parameters'].values():
			relativeName = plug.relativeName( script2["lightFilter"] )
			self.assertEqual( plug.getValue(), script["lightFilter"].descendant( relativeName ).getValue() )

		self.assertEqual( script2["lightFilter"]["out"].attributes( "/lightFilter" ), script["lightFilter"]["out"].attributes( "/lightFilter" ) )
