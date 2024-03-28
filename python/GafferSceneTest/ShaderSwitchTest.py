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
import imath

import IECore

import Gaffer
import GafferScene
import GafferSceneTest

class ShaderSwitchTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		shader1 = GafferSceneTest.TestShader( "s1" )
		shader2 = GafferSceneTest.TestShader( "s2" )

		shader1["type"].setValue( "test:surface" )
		shader2["type"].setValue( "test:surface" )

		shader1["parameters"]["i"].setValue( 1 )
		shader2["parameters"]["i"].setValue( 2 )

		switch = Gaffer.Switch()
		switch.setup( shader1["out"] )
		switch["in"][0].setInput( shader1["out"] )
		switch["in"][1].setInput( shader2["out"] )

		assignment = GafferScene.ShaderAssignment()
		assignment["shader"].setInput( switch["out"] )

		sphere = GafferScene.Sphere()
		assignment["in"].setInput( sphere["out"] )

		self.assertEqual( assignment["out"].attributes( "/sphere" )["test:surface"].getShader( "s1" ).parameters["i"].value, 1 )

		switch["index"].setValue( 1 )
		self.assertEqual( assignment["out"].attributes( "/sphere" )["test:surface"].getShader( "s2" ).parameters["i"].value, 2 )

		switch["enabled"].setValue( False )
		self.assertEqual( assignment["out"].attributes( "/sphere" )["test:surface"].getShader( "s1" ).parameters["i"].value, 1 )

	def testSerialisation( self ) :

		script = Gaffer.ScriptNode()

		script["shader1"] = GafferSceneTest.TestShader()
		script["shader2"] = GafferSceneTest.TestShader()

		script["shader1"]["parameters"]["i"].setValue( 1 )
		script["shader2"]["parameters"]["i"].setValue( 2 )

		script["switch"] = Gaffer.Switch()
		script["switch"].setup( script["shader1"]["out"] )
		script["switch"]["in"][0].setInput( script["shader1"]["out"] )
		script["switch"]["in"][1].setInput( script["shader2"]["out"] )

		script2 = Gaffer.ScriptNode()

		script2.execute( script.serialise() )

		self.assertTrue( script2["switch"]["in"][0].getInput().isSame( script2["shader1"]["out"] ) )
		self.assertTrue( script2["switch"]["in"][1].getInput().isSame( script2["shader2"]["out"] ) )
		self.assertTrue( script2["switch"]["in"][2].getInput() is None )
		self.assertFalse( "in3" in script2["switch"] )
		self.assertTrue( script2["switch"]["out"].source().isSame( script2["shader1"]["out"] ) )

	def testCorrespondingInput( self ) :

		s = Gaffer.Switch()
		s.setup( Gaffer.Color3fPlug() )
		self.assertTrue( s.correspondingInput( s["out"] ).isSame( s["in"][0] ) )

	def testSetup( self ) :

		shader1 = GafferSceneTest.TestShader( "s1" )
		shader2 = GafferSceneTest.TestShader( "s2" )

		shader1["parameters"]["c"].setValue( imath.Color3f( 0 ) )
		shader2["parameters"]["c"].setValue( imath.Color3f( 1 ) )

		switch = Gaffer.Switch()
		switch.setup( shader1["parameters"]["c"] )

		switch["in"][0].setInput( shader1["out"] )
		switch["in"][1].setInput( shader2["out"] )

		shader3 = GafferSceneTest.TestShader( "s3" )
		shader3["type"].setValue( "test:surface" )
		shader3["parameters"]["c"].setInput( switch["out"] )

		for i in range( 0, 2 ) :

			switch["index"].setValue( i )
			network = shader3.attributes()["test:surface"]

			self.assertEqual( len( network ), 2 )
			self.assertEqual(
				network.getShader( "s{0}".format( i + 1 ) ).parameters["c"].value,
				imath.Color3f( i )
			)

	def testContextSensitiveIndex( self ) :

		s = Gaffer.ScriptNode()

		s["n1"] = GafferSceneTest.TestShader()
		s["n1"]["parameters"]["i"].setValue( 1 )

		s["n2"] = GafferSceneTest.TestShader()
		s["n2"]["parameters"]["i"].setValue( 2 )

		s["n3"] = GafferSceneTest.TestShader()
		s["n3"]["parameters"]["i"].setValue( 3 )
		s["n3"]["type"].setValue( "test:surface" )

		s["switch"] = Gaffer.Switch()
		s["switch"].setup( s["n3"]["parameters"]["c"] )

		s["switch"]["in"][0].setInput( s["n1"]["out"] )
		s["switch"]["in"][1].setInput( s["n2"]["out"] )

		s["n3"]["parameters"]["c"].setInput( s["switch"]["out"] )

		s["expression"] = Gaffer.Expression()
		s["expression"].setExpression( 'parent["switch"]["index"] = context.getFrame()' )

		with Gaffer.Context() as context :

			for i in range( 0, 3 ) :

				context.setFrame( i )
				effectiveIndex = i % 2

				network = s["n3"].attributes()["test:surface"]
				self.assertEqual( len( network ), 2 )
				self.assertEqual(
					network.getShader( "n{0}".format( effectiveIndex + 1 ) ).parameters["i"].value,
					effectiveIndex + 1
				)
				self.assertEqual(
					network.inputConnections( "n3" ),
					[ network.Connection( network.Parameter( "n{0}".format( effectiveIndex + 1 ), "out" ), network.Parameter( "n3", "c" ) ) ]
				)

if __name__ == "__main__":
	unittest.main()
