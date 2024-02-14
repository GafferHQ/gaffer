##########################################################################
#
#  Copyright (c) 2022, Cinesite VFX Ltd. All rights reserved.
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
#      * Neither the name of Cinesite VFX Ltd nor the names of
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
import pathlib

import Gaffer
import GafferOSL
import GafferSceneTest
import GafferCycles

class CyclesShaderTest( GafferSceneTest.SceneTestCase ) :

	def testInitialPlugs( self ) :

		shader = GafferCycles.CyclesShader()
		self.assertIn( "parameters", shader )
		self.assertIn( "out", shader )
		self.assertIs( type( shader["parameters"] ), Gaffer.Plug )
		self.assertIs( type( shader["out"] ), Gaffer.Plug )
		self.assertEqual( len( shader["parameters"] ), 0 )
		self.assertEqual( len( shader["out"] ), 0 )

	def testLoadOutputs( self ) :

		shader = GafferCycles.CyclesShader()
		shader.loadShader( "attribute" )

		self.assertEqual( shader["out"].keys(), [ "color", "vector", "fac", "alpha" ] )
		self.assertIsInstance( shader["out"]["color"], Gaffer.Color3fPlug )
		self.assertIsInstance( shader["out"]["vector"], Gaffer.V3fPlug )
		self.assertIsInstance( shader["out"]["fac"], Gaffer.FloatPlug )
		self.assertIsInstance( shader["out"]["alpha"], Gaffer.FloatPlug )

	def testLoadRemovesUnneededChildren( self ) :

		shader = GafferCycles.CyclesShader()
		shader.loadShader( "principled_bsdf" )
		self.assertEqual( shader["out"].keys(), [ "BSDF" ] )

		shader.loadShader( "attribute" )
		self.assertEqual( shader["out"].keys(), [ "color", "vector", "fac", "alpha" ] )

	def testLoadAllShaders( self ) :

		shader = GafferCycles.CyclesShader()
		for s in GafferCycles.shaders :
			shader.loadShader( s )

	def testLoadEmission( self ) :

		shader = GafferCycles.CyclesShader()
		shader.loadShader( "emission" )
		self.assertEqual( shader["type"].getValue(), "cycles:surface" )

	def testShaderCompatibility( self ) :

		script = Gaffer.ScriptNode()
		script["fileName"].setValue( pathlib.Path( __file__ ).parent / "scripts" / "principledBSDF-3.x.gfr" )
		script.load()

		self.assertIn( "emission_color", script["principled_bsdf"]["parameters"] )
		self.assertNotIn( "emission", script["principled_bsdf"]["parameters"] )

if __name__ == "__main__":
	unittest.main()
