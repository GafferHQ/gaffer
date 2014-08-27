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

import IECore

import Gaffer
import GafferTest
import GafferScene
import GafferSceneTest

class SceneSwitchTest( GafferSceneTest.SceneTestCase ) :

	def testDefaultName( self ) :

		s = GafferScene.SceneSwitch()
		self.assertEqual( s.getName(), "SceneSwitch" )

	def testEnabledPlug( self ) :

		s = GafferScene.SceneSwitch()
		self.assertTrue( isinstance( s["enabled"], Gaffer.BoolPlug ) )
		self.assertTrue( s["enabled"].isSame( s.enabledPlug() ) )
		self.assertFalse( "enabled1" in s )

	def testAffects( self ) :

		plane = GafferScene.Plane()
		sphere = GafferScene.Sphere()

		switch = GafferScene.SceneSwitch()
		switch["in"].setInput( plane["out"] )
		switch["in1"].setInput( sphere["out"] )

		for p in [ switch["in"], switch["in1"] ] :
			for n in [ "globals", "object", "attributes", "transform", "bound", "childNames" ] :
				a = switch.affects( p[n] )
				self.assertEqual( len( a ), 1 )
				self.assertTrue( a[0].isSame( switch["out"][n] ) )

		a = set( [ plug.relativeName( plug.node() ) for plug in switch.affects( switch["enabled"] ) ] )
		self.assertEqual(
			a,
			set( [
				"out.globals", "out.object", "out.attributes",
				"out.transform", "out.bound", "out.childNames"
			] ),
		)

		a = set( [ plug.relativeName( plug.node() ) for plug in switch.affects( switch["index"] ) ] )
		self.assertEqual(
			a,
			set( [
				"out.globals", "out.object", "out.attributes",
				"out.transform", "out.bound", "out.childNames"
			] ),
		)

	def testSwitching( self ) :

		plane = GafferScene.Plane()
		sphere = GafferScene.Sphere()

		switch = GafferScene.SceneSwitch()
		switch["in"].setInput( plane["out"] )
		switch["in1"].setInput( sphere["out"] )

		self.assertScenesEqual( switch["out"], plane["out"] )
		self.assertSceneHashesEqual( switch["out"], plane["out"] )

		switch["index"].setValue( 1 )

		self.assertScenesEqual( switch["out"], sphere["out"] )
		self.assertSceneHashesEqual( switch["out"], sphere["out"] )

		switch["enabled"].setValue( False )

		self.assertScenesEqual( switch["out"], plane["out"] )
		self.assertSceneHashesEqual( switch["out"], plane["out"] )

	def testSerialisation( self ) :

		script = Gaffer.ScriptNode()

		script["switch"] = GafferScene.SceneSwitch()
		script["plane"] = GafferScene.Plane()
		script["sphere"] = GafferScene.Sphere()

		script["switch"]["in"].setInput( script["plane"]["out"] )
		script["switch"]["in1"].setInput( script["sphere"]["out"] )

		script2 = Gaffer.ScriptNode()
		script2.execute( script.serialise() )

		self.assertTrue( script2["switch"]["in"].getInput().isSame( script2["plane"]["out"] ) )
		self.assertTrue( script2["switch"]["in1"].getInput().isSame( script2["sphere"]["out"] ) )
		self.assertTrue( script2["switch"]["in2"].getInput() is None )

if __name__ == "__main__":
	unittest.main()
