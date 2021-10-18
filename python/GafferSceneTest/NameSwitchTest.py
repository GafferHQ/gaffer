##########################################################################
#
#  Copyright (c) 2021, Cinesite VFX Ltd. All rights reserved.
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

import inspect
import unittest

import Gaffer
import GafferScene
import GafferSceneTest

class NameSwitchTest( GafferSceneTest.SceneTestCase ) :

	def testSelectorFromGlobals( self ) :

		script = Gaffer.ScriptNode()

		script["options"] = GafferScene.CustomOptions()
		script["options"]["options"]["selector"] = Gaffer.NameValuePlug( "selector", "sphere" )

		script["plane"] = GafferScene.Plane()
		script["sphere"] = GafferScene.Sphere()

		script["switch"] = Gaffer.NameSwitch()
		script["switch"].setup( GafferScene.ScenePlug() )
		script["switch"]["in"][0]["name"].setValue( "plane" )
		script["switch"]["in"][0]["value"].setInput( script["plane"]["out"] )
		script["switch"]["in"][1]["name"].setValue( "sphere" )
		script["switch"]["in"][1]["value"].setInput( script["sphere"]["out"] )

		script["expression"] = Gaffer.Expression()
		script["expression"].setExpression( inspect.cleandoc(
			"""
			g = parent["options"]["out"]["globals"]
			parent["switch"]["selector"] = g["option:selector"]
			"""
		) )

		# As well as asserting that the scene is as expected here, we're also
		# indirectly testing that `scene:path` isn't leaked into the context
		# used to evaluate the globals (because SceneTestCase installs a
		# ContextSanitiser for the duration of the test).

		self.assertEqual(
			script["switch"]["out"]["value"].object( "/sphere" ),
			script["sphere"]["out"].object( "/sphere" )
		)

	def testEnabledFromGlobals( self ) :

		script = Gaffer.ScriptNode()

		script["options"] = GafferScene.CustomOptions()
		script["options"]["options"]["enabled"] = Gaffer.NameValuePlug( "enabled", True )

		script["plane"] = GafferScene.Plane()
		script["sphere"] = GafferScene.Sphere()

		script["switch"] = Gaffer.NameSwitch()
		script["switch"].setup( GafferScene.ScenePlug() )
		script["switch"]["selector"].setValue( "sphere" )
		script["switch"]["in"][0]["name"].setValue( "plane" )
		script["switch"]["in"][0]["value"].setInput( script["plane"]["out"] )
		script["switch"]["in"][1]["name"].setValue( "sphere" )
		script["switch"]["in"][1]["value"].setInput( script["sphere"]["out"] )

		script["expression"] = Gaffer.Expression()
		script["expression"].setExpression( inspect.cleandoc(
			"""
			g = parent["options"]["out"]["globals"]
			parent["switch"]["enabled"] = g["option:enabled"]
			"""
		) )

		# As well as asserting that the scene is as expected here, we're also
		# indirectly testing that `scene:path` isn't leaked into the context
		# used to evaluate the globals (because SceneTestCase installs a
		# ContextSanitiser for the duration of the test).

		self.assertEqual(
			script["switch"]["out"]["value"].object( "/sphere" ),
			script["sphere"]["out"].object( "/sphere" )
		)

if __name__ == "__main__":
	unittest.main()
