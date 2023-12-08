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

import pathlib
import inspect
import unittest

import IECore

import Gaffer
import GafferTest
import GafferScene
import GafferSceneTest

class SceneSwitchTest( GafferSceneTest.SceneTestCase ) :

	def testEnabledPlug( self ) :

		s = Gaffer.Switch()
		s.setup( GafferScene.ScenePlug() )

		self.assertTrue( isinstance( s["enabled"], Gaffer.BoolPlug ) )
		self.assertTrue( s["enabled"].isSame( s.enabledPlug() ) )
		self.assertFalse( "enabled1" in s )

	def testAffects( self ) :

		plane = GafferScene.Plane()
		sphere = GafferScene.Sphere()

		switch = Gaffer.Switch()
		switch.setup( GafferScene.ScenePlug() )

		switch["in"][0].setInput( plane["out"] )
		switch["in"][1].setInput( sphere["out"] )

		add = GafferTest.AddNode()
		switch["index"].setInput( add["sum"] )

		for p in [ switch["in"][0], switch["in"][1] ] :
			for n in p.keys() :
				a = switch.affects( p[n] )
				self.assertEqual( a, [ switch["out"][n], switch["connectedInputs"] ] )

		a = set( switch.affects( switch["enabled"] ) )
		self.assertEqual( a, set( switch["out"].children() ) )

		a = set( switch.affects( switch["index"] ) )
		self.assertEqual( a, set( switch["out"].children() ) )

	def testSwitching( self ) :

		plane = GafferScene.Plane()
		sphere = GafferScene.Sphere()

		switch = Gaffer.Switch()
		switch.setup( GafferScene.ScenePlug() )

		switch["in"][0].setInput( plane["out"] )
		switch["in"][1].setInput( sphere["out"] )

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

		script["switch"] = Gaffer.Switch()
		script["switch"].setup( GafferScene.ScenePlug() )

		script["plane"] = GafferScene.Plane()
		script["sphere"] = GafferScene.Sphere()

		script["switch"]["in"][0].setInput( script["plane"]["out"] )
		script["switch"]["in"][1].setInput( script["sphere"]["out"] )

		script2 = Gaffer.ScriptNode()
		script2.execute( script.serialise() )

		self.assertTrue( script2["switch"]["in"][0].getInput().isSame( script2["plane"]["out"] ) )
		self.assertTrue( script2["switch"]["in"][1].getInput().isSame( script2["sphere"]["out"] ) )
		self.assertTrue( script2["switch"]["in"][2].getInput() is None )

	def testScenePathNotAvailableInContextExpressions( self ) :

		# We don't want expressions on the index to be sensitive
		# to the scene:path context entry, because then the scene
		# can be made invalid by splicing together different input
		# scenes without taking care of bounding box propagation etc.

		script = Gaffer.ScriptNode()

		script["plane"] = GafferScene.Plane()
		script["sphere"] = GafferScene.Sphere()

		script["switch"] = Gaffer.Switch()
		script["switch"].setup( GafferScene.ScenePlug() )
		script["switch"]["in"][0].setInput( script["plane"]["out"] )
		script["switch"]["in"][1].setInput( script["sphere"]["out"] )

		script["expression"] = Gaffer.Expression()
		script["expression"].setExpression( inspect.cleandoc(
			"""
			assert( context.get( "scene:path", None ) is None )
			parent["switch"]["index"] = 1
			"""
		) )

		self.assertEqual( script["switch"]["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "sphere" ] ) )

	def testAcceptsInputPerformance( self ) :

		s1 = GafferScene.Sphere()
		lastPlug = s1["out"]

		switches = []
		for i in range( 0, 10 ) :
			switch = Gaffer.Switch()
			switch.setup( GafferScene.ScenePlug() )
			for i in range( 0, 10 ) :
				switch["in"][i].setInput( lastPlug )
			switches.append( switch )
			lastPlug = switch["out"]

		s2 = GafferScene.Sphere()
		self.assertTrue( switches[0]["in"][0].acceptsInput( s2["out"] ) )

	def testLoadFileFromVersion0_49( self ) :

		s = Gaffer.ScriptNode()
		s["fileName"].setValue( pathlib.Path( __file__ ).parent / "scripts" / "sceneSwitch-0.49.1.0.gfr" )
		s.load()

		self.assertEqual( s["SceneSwitch"]["in"][0].getInput(), s["Plane"]["out"] )
		self.assertEqual( s["SceneSwitch"]["in"][1].getInput(), s["Sphere"]["out"] )

	def testNoUnnecessaryDirtyPropagationCrossTalk( self ) :

		#           plane
		#             |
		#     primitiveVariables
		#            / \
		#            | deleteFaces
		#            | |
		#            | |
		#           switch

		plane = GafferScene.Plane()

		primitiveVariables = GafferScene.PrimitiveVariables()
		primitiveVariables["in"].setInput( plane["out"] )
		pv = Gaffer.NameValuePlug( "test", IECore.IntData( 0 ) )
		primitiveVariables["primitiveVariables"].addChild( pv )

		# DeleteFaces has a dependency between the object and the
		# bound, so dirtying the input object also dirties the
		# output bound. There is cross-talk between the plugs.
		deleteFaces = GafferScene.DeleteFaces()
		deleteFaces["in"].setInput( primitiveVariables["out"] )

		switch = Gaffer.Switch()
		switch.setup( primitiveVariables["out"] )
		switch["in"][0].setInput( primitiveVariables["out"] )
		switch["in"][1].setInput( deleteFaces["out"] )

		# When the Switch index is constant 0, we know that DeleteFaces
		# is not the active branch. So we don't expect dirtying the input
		# object to dirty the output bound.
		cs = GafferTest.CapturingSlot( switch.plugDirtiedSignal() )
		pv["value"].setValue( 1 )
		self.assertIn( switch["out"]["object"], { x[0] for x in cs } )
		self.assertNotIn( switch["out"]["bound"], { x[0] for x in cs } )

		# When the Switch index is constant 1, we know that DeleteFaces
		# is the active branch, so we do expect crosstalk.
		switch["index"].setValue( 1 )
		del cs[:]
		pv["value"].setValue( 2 )
		self.assertIn( switch["out"]["object"], { x[0] for x in cs } )
		self.assertIn( switch["out"]["bound"], { x[0] for x in cs } )

		# And when the Switch index is computed (indeterminate during
		# dirty propagation) we also expect crosstalk.
		add = GafferTest.AddNode()
		switch["index"].setInput( add["sum"] )
		del cs[:]
		pv["value"].setValue( 3 )
		self.assertIn( switch["out"]["object"], { x[0] for x in cs } )
		self.assertIn( switch["out"]["bound"], { x[0] for x in cs } )

if __name__ == "__main__":
	unittest.main()
