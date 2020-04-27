##########################################################################
#
#  Copyright (c) 2020, Cinesite VFX Ltd. All rights reserved.
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
import IECoreScene

import Gaffer
import GafferTest
import GafferScene
import GafferSceneTest
import GafferArnold

class ArnoldColorManagerTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		# Loading

		colorManager = GafferArnold.ArnoldColorManager()

		colorManager.loadColorManager( "color_manager_ocio" )

		for name, plugType, defaultValue in [
			( "config", Gaffer.StringPlug, "" ),
			( "color_space_narrow", Gaffer.StringPlug, "" ),
			( "color_space_linear", Gaffer.StringPlug, "" ),
		] :
			self.assertIn( "config", colorManager["parameters"] )
			self.assertIsInstance( colorManager["parameters"][name], plugType )
			self.assertEqual( colorManager["parameters"][name].getValue(), defaultValue )
			self.assertEqual( colorManager["parameters"][name].defaultValue(), defaultValue )

		# Affects

		options = GafferScene.StandardOptions()
		colorManager["in"].setInput( options["out"] )

		cs = GafferTest.CapturingSlot( colorManager.plugDirtiedSignal() )
		options["enabled"].setValue( False )
		self.assertEqual(
			{ x[0] for x in cs if not x[0].getName().startswith( "__" ) },
			{ colorManager["in"]["globals"], colorManager["in"], colorManager["out"]["globals"], colorManager["out"] }
		)

		del cs[:]
		colorManager["parameters"]["color_space_linear"].setValue( "linear" )
		self.assertEqual(
			{ x[0] for x in cs if not x[0].getName().startswith( "__" ) },
			{ colorManager["parameters"]["color_space_linear"], colorManager["parameters"], colorManager["out"]["globals"], colorManager["out"] }
		)

		# Compute

		g = colorManager["out"].globals()
		self.assertIn( "option:ai:color_manager", g )
		cm = g["option:ai:color_manager"]
		self.assertIsInstance( cm, IECoreScene.ShaderNetwork )
		self.assertEqual( cm.outputShader().name, "color_manager_ocio" )
		self.assertEqual( cm.outputShader().type, "ai:color_manager" )
		self.assertEqual(
			cm.outputShader().parameters,
			IECore.CompoundData( {
				"color_space_linear" : "linear",
				"color_space_narrow" : "",
				"config" : "",
			} )
		)

		colorManager["enabled"].setValue( False )
		self.assertNotIn( "ai:color_manager", colorManager["out"].globals() )

	def testSerialisation( self ) :

		s = Gaffer.ScriptNode()
		s["m"] = GafferArnold.ArnoldColorManager()
		s["m"].loadColorManager( "color_manager_ocio" )
		s["m"]["parameters"]["color_space_narrow"].setValue( "narrow" )
		s["m"]["parameters"]["color_space_linear"].setValue( "linear" )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertIn( "m", s2 )
		self.assertIsInstance( s2["m"], GafferArnold.ArnoldColorManager )
		self.assertEqual( s2["m"]["parameters"].keys(), s["m"]["parameters"].keys() )
		self.assertEqual( s2["m"]["parameters"]["color_space_narrow"].getValue(), "narrow" )
		self.assertEqual( s2["m"]["parameters"]["color_space_linear"].getValue(), "linear" )

		self.assertEqual( s2["m"]["out"].globals(), s["m"]["out"].globals() )

if __name__ == "__main__":
	unittest.main()
