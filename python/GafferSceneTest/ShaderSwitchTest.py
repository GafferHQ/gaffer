##########################################################################
#
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

import Gaffer
import GafferScene
import GafferSceneTest

class ShaderSwitchTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		shader1 = GafferSceneTest.TestShader()
		shader2 = GafferSceneTest.TestShader()

		shader1["type"].setValue( "test:surface" )
		shader2["type"].setValue( "test:surface" )

		shader1["parameters"]["i"].setValue( 1 )
		shader2["parameters"]["i"].setValue( 2 )

		switch = GafferScene.ShaderSwitch()
		switch["in"].setInput( shader1["out"] )
		switch["in1"].setInput( shader2["out"] )

		assignment = GafferScene.ShaderAssignment()
		assignment["shader"].setInput( switch["out"] )

		sphere = GafferScene.Sphere()
		assignment["in"].setInput( sphere["out"] )

		self.assertEqual( assignment["out"].attributes( "/sphere" )["test:surface"][0].parameters["i"].value, 1 )

		switch["index"].setValue( 1 )
		self.assertEqual( assignment["out"].attributes( "/sphere" )["test:surface"][0].parameters["i"].value, 2 )

		switch["enabled"].setValue( False )
		self.assertEqual( assignment["out"].attributes( "/sphere" )["test:surface"][0].parameters["i"].value, 1 )

	def testSerialisation( self ) :

		script = Gaffer.ScriptNode()

		script["shader1"] = GafferSceneTest.TestShader()
		script["shader2"] = GafferSceneTest.TestShader()

		script["shader1"]["parameters"]["i"].setValue( 1 )
		script["shader2"]["parameters"]["i"].setValue( 2 )

		script["switch"] = GafferScene.ShaderSwitch()
		script["switch"]["in"].setInput( script["shader1"]["out"] )
		script["switch"]["in1"].setInput( script["shader2"]["out"] )

		script2 = Gaffer.ScriptNode()

		script2.execute( script.serialise() )

		self.assertTrue( script2["switch"]["in"].getInput().isSame( script2["shader1"]["out"] ) )
		self.assertTrue( script2["switch"]["in1"].getInput().isSame( script2["shader2"]["out"] ) )
		self.assertTrue( script2["switch"]["in2"].getInput() is None )
		self.assertFalse( "in3" in script2["switch"] )
		self.assertTrue( script2["switch"]["out"].source().isSame( script2["shader1"]["out"] ) )

	def testCorrespondingInput( self ) :

		s = GafferScene.ShaderSwitch()
		self.assertTrue( s.correspondingInput( s["out"] ).isSame( s["in"] ) )

if __name__ == "__main__":
	unittest.main()
