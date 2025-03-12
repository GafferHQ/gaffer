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

import IECore

import Gaffer
import GafferScene
import GafferSceneTest
import GafferRenderMan

class RenderManMeshLightTest( GafferSceneTest.SceneTestCase ) :

	def testParameters( self ) :

		light = GafferRenderMan.RenderManMeshLight()

		# Should have all the parameters of a PxrMeshLight shader.

		shader = GafferRenderMan.RenderManShader()
		shader.loadShader( "PxrMeshLight" )
		self.assertEqual( light["parameters"].keys(), shader["parameters"].keys() )

		# Parameters should drive a light shader in the scene.

		sphere = GafferScene.Sphere()
		sphereFilter = GafferScene.PathFilter()
		sphereFilter["paths"].setValue( IECore.StringVectorData( [ "/sphere" ] ) )
		light["in"].setInput( sphere["out"] )
		light["filter"].setInput( sphereFilter["out"] )

		light["parameters"]["exposure"].setValue( 10 )
		self.assertEqual( light["out"].attributes( "/sphere" )["ri:light"].outputShader().parameters["exposure"], IECore.FloatData( 10 ) )

	def testSerialisation( self ) :

		script = Gaffer.ScriptNode()
		script["light"] = GafferRenderMan.RenderManMeshLight()
		script["light"]["parameters"]["intensity"].setValue( 10 )

		serialisation = script.serialise()

		script2 = Gaffer.ScriptNode()
		script2.execute( serialisation )
		self.assertEqual( script2["light"]["parameters"]["intensity"].getValue(), 10 )

		# One for the node. None for plugs, since they are not dynamic.
		self.assertEqual( serialisation.count( "addChild" ), 1 )

if __name__ == "__main__":
	unittest.main()
