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

import imath

import Gaffer
import GafferScene
import GafferSceneTest

class ShaderPlugTest( GafferSceneTest.SceneTestCase ) :

	def testContextProcessorInput( self ) :

		shader1 = GafferSceneTest.TestShader()
		shader1["type"].setValue( "test:surface" )
		shader1["parameters"]["c"].setValue( imath.Color3f( 1 ) )
		shader2 = GafferSceneTest.TestShader()
		shader2["type"].setValue( "test:surface" )
		shader2["parameters"]["c"].setValue( imath.Color3f( 2 ) )

		nameSwitch = Gaffer.NameSwitch()
		nameSwitch.setup( shader2["out"] )
		nameSwitch["selector"].setValue( "${which}")
		nameSwitch["in"][0]["name"].setValue( "one" )
		nameSwitch["in"][0]["value"].setInput( shader1["out"] )
		nameSwitch["in"][1]["name"].setValue( "two" )
		nameSwitch["in"][1]["value"].setInput( shader2["out"] )

		contextVariables = Gaffer.ContextVariables()
		contextVariables.setup( nameSwitch["out"]["value"] )
		contextVariables["in"].setInput( nameSwitch["out"]["value"] )
		contextVariables["variables"].addChild( Gaffer.NameValuePlug( "which", "two" ) )

		shaderPlug = GafferScene.ShaderPlug()
		shaderPlug.setInput( contextVariables["out"] )

		self.assertEqual( shaderPlug.attributes()["test:surface"].outputShader().parameters["c"].value, imath.Color3f( 2 ) )

	def testRejectsScenePlugInputFromContextProcessor( self ) :

		contextVariables = Gaffer.ContextVariables()
		contextVariables.setup( GafferScene.ScenePlug() )

		shaderPlug = GafferScene.ShaderPlug()
		self.assertFalse( shaderPlug.acceptsInput( contextVariables["out"] ) )

if __name__ == "__main__":
	unittest.main()
