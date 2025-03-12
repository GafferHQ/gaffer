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

import unittest

import IECoreScene

import GafferSceneTest
import GafferRenderMan

class RenderManIntegratorTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		shader = GafferRenderMan.RenderManShader()
		shader.loadShader( "PxrPathTracer" )

		self.assertEqual( shader["name"].getValue(), "PxrPathTracer" )
		self.assertEqual( shader["type"].getValue(), "ri:integrator" )

		shader["parameters"]["maxIndirectBounces"].setValue( 2 )

		integrator = GafferRenderMan.RenderManIntegrator()
		self.assertNotIn( "option:ri:integrator", integrator["out"].globals() )

		integrator["shader"].setInput( shader["out"] )
		self.assertIn( "option:ri:integrator", integrator["out"].globals() )

		network = integrator["out"].globals()["option:ri:integrator"]
		self.assertIsInstance( network, IECoreScene.ShaderNetwork )

		self.assertEqual( len( network.shaders() ), 1 )
		self.assertEqual( network.outputShader().name, "PxrPathTracer" )
		self.assertEqual( network.outputShader().type, "ri:integrator" )
		self.assertEqual( network.outputShader().parameters["maxIndirectBounces"].value, 2 )

	def testRejectsNonIntegratorInputs( self ) :

		shader = GafferRenderMan.RenderManShader()
		shader.loadShader( "PxrConstant" )

		node = GafferRenderMan.RenderManIntegrator()
		self.assertFalse( node["shader"].acceptsInput( shader["out"] ) )

if __name__ == "__main__":
	unittest.main()
