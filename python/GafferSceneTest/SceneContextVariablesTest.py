##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
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

import IECore

import Gaffer
import GafferTest
import GafferScene
import GafferSceneTest

class SceneContextVariablesTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		p = GafferScene.Plane()

		a = GafferScene.Attributes()
		a["in"].setInput( p["out"] )
		a["attributes"].addChild( Gaffer.NameValuePlug( "render:something", IECore.StringData( "$a" ) ) )

		c = Gaffer.ContextVariables()
		c.setup( GafferScene.ScenePlug() )
		c["in"].setInput( a["out"] )
		c["variables"].addChild( Gaffer.NameValuePlug( "a", IECore.StringData( "aardvark" ) ) )

		self.assertEqual( a["out"].attributes( "/plane" )["render:something"], IECore.StringData( "" ) )
		self.assertEqual( c["out"].attributes( "/plane" )["render:something"], IECore.StringData( "aardvark" ) )

	def testNullMember( self ) :

		p = GafferScene.Plane()

		c = Gaffer.ContextVariables()
		c.setup( GafferScene.ScenePlug() )
		c["in"].setInput( p["out"] )
		c["variables"].addChild( Gaffer.NameValuePlug( "", IECore.StringData( "aardvark" ) ) )

		self.assertSceneValid( c["out"] )

	def testContextLeaks( self ) :

		script = Gaffer.ScriptNode()

		script["plane"] = GafferScene.Plane()
		script["plane"]["sets"].setValue( "A" )

		script["contextVariables"] = Gaffer.ContextVariables()
		script["contextVariables"].setup( GafferScene.ScenePlug() )
		script["contextVariables"]["in"].setInput( script["plane"]["out"] )
		script["contextVariables"]["variables"].addChild( Gaffer.NameValuePlug( "a", IECore.StringData( "aardvark" ), True, "a" ) )

		script["expression"] = Gaffer.Expression()
		script["expression"].setExpression( inspect.cleandoc(
			"""
			parent["contextVariables"]["enabled"] = True
			parent["contextVariables"]["variables"]["a"]["enabled"] = True
			parent["contextVariables"]["variables"]["a"]["name"] = "b"
			parent["contextVariables"]["variables"]["a"]["value"] = "b"
			"""
		) )

		with Gaffer.ContextMonitor( script["expression"] ) as cm :
			self.assertSceneValid( script["contextVariables"]["out"] )

		self.assertFalse(
			set( cm.combinedStatistics().variableNames() ).intersection(
				{ "scene:path", "scene:setName", "scene:filter:inputScene" }
			)
		)

if __name__ == "__main__":
	unittest.main()
