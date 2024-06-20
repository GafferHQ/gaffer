##########################################################################
#
#  Copyright (c) 2024, Cinesite VFX Ltd. All rights reserved.
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
import GafferTest
import GafferUI
import GafferUITest

class ContextTrackerTest( GafferUITest.TestCase ) :

	def testSimpleNodes( self ) :

		script = Gaffer.ScriptNode()

		script["add1"] = GafferTest.AddNode()
		script["add2"] = GafferTest.AddNode()
		script["add3"] = GafferTest.AddNode()
		script["add4"] = GafferTest.AddNode()
		script["unconnected"] = GafferTest.AddNode()

		script["add3"]["op1"].setInput( script["add1"]["sum"] )
		script["add3"]["op2"].setInput( script["add2"]["sum"] )
		script["add4"]["op1"].setInput( script["add3"]["sum"] )

		context = Gaffer.Context()
		tracker = GafferUI.ContextTracker( script["add4"], context )

		def assertExpectedContexts() :

			# Inactive nodes and plugs fall back to using the target
			# context, so everything has the same context.

			for node in Gaffer.Node.Range( script ) :
				self.assertEqual( tracker.context( node ), context )
				for plug in Gaffer.Plug.RecursiveRange( node ) :
					self.assertEqual( tracker.context( plug ), context )

		assertExpectedContexts( )

		for node in [ script["add1"], script["add2"], script["add3"], script["add4"] ] :
			for graphComponent in [ node, node["op1"], node["op2"], node["sum"], node["enabled"] ] :
				self.assertTrue( tracker.isActive( graphComponent ), graphComponent.fullName() )

		for graphComponent in [ script["unconnected"], script["unconnected"]["op1"], script["unconnected"]["op2"], script["unconnected"]["sum"], script["unconnected"]["enabled"] ] :
			self.assertFalse( tracker.isActive( graphComponent ) )

		script["add3"]["enabled"].setValue( False )

		assertExpectedContexts( )

		self.assertTrue( tracker.isActive( script["add4"] ) )
		self.assertTrue( tracker.isActive( script["add3"] ) )
		self.assertTrue( tracker.isActive( script["add3"]["op1"] ) )
		self.assertFalse( tracker.isActive( script["add3"]["op2"] ) )
		self.assertTrue( tracker.isActive( script["add1"] ) )
		self.assertFalse( tracker.isActive( script["add2"] ) )

	def testSwitch( self ) :

		# Static case - switch will have internal pass-through connections.

		script = Gaffer.ScriptNode()

		script["add1"] = GafferTest.AddNode()
		script["add2"] = GafferTest.AddNode()

		script["switch"] = Gaffer.Switch()
		script["switch"].setup( script["add1"]["sum"] )
		script["switch"]["in"][0].setInput( script["add1"]["sum"] )
		script["switch"]["in"][1].setInput( script["add2"]["sum"] )

		context = Gaffer.Context()
		tracker = GafferUI.ContextTracker( script["switch"], context )

		def assertExpectedContexts() :

			# Inactive nodes and plugs fall back to using the target
			# context, so everything has the same context.

			for node in [ script["add1"], script["add2"], script["switch"] ] :
				self.assertEqual( tracker.context( node ), context, node.fullName() )
				for plug in Gaffer.Plug.RecursiveRange( node ) :
					self.assertEqual( tracker.context( plug ), context, plug.fullName() )

		assertExpectedContexts()

		self.assertTrue( tracker.isActive( script["switch"] ) )
		self.assertTrue( tracker.isActive( script["switch"]["out"] ) )
		self.assertTrue( tracker.isActive( script["switch"]["index"] ) )
		self.assertTrue( tracker.isActive( script["switch"]["enabled"] ) )
		self.assertTrue( tracker.isActive( script["switch"]["in"][0] ) )
		self.assertFalse( tracker.isActive( script["switch"]["in"][1] ) )
		self.assertTrue( tracker.isActive( script["add1"] ) )
		self.assertFalse( tracker.isActive( script["add2"] ) )

		script["switch"]["index"].setValue( 1 )

		assertExpectedContexts()

		self.assertTrue( tracker.isActive( script["switch"] ) )
		self.assertTrue( tracker.isActive( script["switch"]["out"] ) )
		self.assertTrue( tracker.isActive( script["switch"]["index"] ) )
		self.assertTrue( tracker.isActive( script["switch"]["enabled"] ) )
		self.assertFalse( tracker.isActive( script["switch"]["in"][0] ) )
		self.assertTrue( tracker.isActive( script["switch"]["in"][1] ) )
		self.assertFalse( tracker.isActive( script["add1"] ) )
		self.assertTrue( tracker.isActive( script["add2"] ) )

		script["switch"]["enabled"].setValue( False )

		assertExpectedContexts()

		self.assertTrue( tracker.isActive( script["switch"] ) )
		self.assertTrue( tracker.isActive( script["switch"]["out"] ) )
		self.assertFalse( tracker.isActive( script["switch"]["index"] ) )
		self.assertTrue( tracker.isActive( script["switch"]["enabled"] ) )
		self.assertTrue( tracker.isActive( script["switch"]["in"][0] ) )
		self.assertFalse( tracker.isActive( script["switch"]["in"][1] ) )
		self.assertTrue( tracker.isActive( script["add1"] ) )
		self.assertFalse( tracker.isActive( script["add2"] ) )

		# Dynamic case - switch will compute input on the fly.

		script["add3"] = GafferTest.AddNode()
		script["switch"]["index"].setInput( script["add3"]["sum"] )
		script["switch"]["enabled"].setValue( True )

		assertExpectedContexts()

		self.assertTrue( tracker.isActive( script["switch"] ) )
		self.assertTrue( tracker.isActive( script["switch"]["out"] ) )
		self.assertTrue( tracker.isActive( script["switch"]["index"] ) )
		self.assertTrue( tracker.isActive( script["switch"]["enabled"] ) )
		self.assertTrue( tracker.isActive( script["switch"]["in"][0] ) )
		self.assertFalse( tracker.isActive( script["switch"]["in"][1] ) )
		self.assertTrue( tracker.isActive( script["add1"] ) )
		self.assertFalse( tracker.isActive( script["add2"] ) )
		self.assertTrue( tracker.isActive( script["add3"] ) )
		self.assertEqual( tracker.context( script["add3"] ), context )

		script["add3"]["op1"].setValue( 1 )

		assertExpectedContexts()

		self.assertTrue( tracker.isActive( script["switch"] ) )
		self.assertTrue( tracker.isActive( script["switch"]["out"] ) )
		self.assertTrue( tracker.isActive( script["switch"]["index"] ) )
		self.assertTrue( tracker.isActive( script["switch"]["enabled"] ) )
		self.assertFalse( tracker.isActive( script["switch"]["in"][0] ) )
		self.assertTrue( tracker.isActive( script["switch"]["in"][1] ) )
		self.assertFalse( tracker.isActive( script["add1"] ) )
		self.assertTrue( tracker.isActive( script["add2"] ) )
		self.assertTrue( tracker.isActive( script["add3"] ) )
		self.assertEqual( tracker.context( script["add3"] ), context )

	def testNameSwitch( self ) :

		# Static case - switch will have internal pass-through connections.

		script = Gaffer.ScriptNode()

		script["add1"] = GafferTest.AddNode()
		script["add2"] = GafferTest.AddNode()

		script["switch"] = Gaffer.NameSwitch()
		script["switch"].setup( script["add1"]["sum"] )
		script["switch"]["in"][0]["value"].setInput( script["add1"]["sum"] )
		script["switch"]["in"][1]["value"].setInput( script["add2"]["sum"] )
		script["switch"]["in"][1]["name"].setValue( "add2" )

		context = Gaffer.Context()
		tracker = GafferUI.ContextTracker( script["switch"], context )

		def assertExpectedContexts() :

			# Inactive nodes and plugs fall back to using the target
			# context, so everything has the same context.

			for node in [ script["add1"], script["add2"], script["switch"] ] :
				self.assertEqual( tracker.context( node ), context )
				for plug in Gaffer.Plug.RecursiveRange( node ) :
					self.assertEqual( tracker.context( plug ), context )

		assertExpectedContexts()

		self.assertTrue( tracker.isActive( script["switch"] ) )
		self.assertTrue( tracker.isActive( script["switch"]["out"] ) )
		self.assertTrue( tracker.isActive( script["switch"]["selector"] ) )
		self.assertTrue( tracker.isActive( script["switch"]["in"][0] ) )
		self.assertFalse( tracker.isActive( script["switch"]["in"][1] ) )
		self.assertTrue( tracker.isActive( script["add1"] ) )
		self.assertFalse( tracker.isActive( script["add2"] ) )

		script["switch"]["selector"].setValue( "add2" )

		assertExpectedContexts()

		self.assertTrue( tracker.isActive( script["switch"] ) )
		self.assertTrue( tracker.isActive( script["switch"]["out"] ) )
		self.assertTrue( tracker.isActive( script["switch"]["selector"] ) )
		self.assertFalse( tracker.isActive( script["switch"]["in"][0] ) )
		self.assertTrue( tracker.isActive( script["switch"]["in"][1] ) )
		self.assertFalse( tracker.isActive( script["add1"] ) )
		self.assertTrue( tracker.isActive( script["add2"] ) )

		script["switch"]["enabled"].setValue( False )

		assertExpectedContexts()

		self.assertTrue( tracker.isActive( script["switch"] ) )
		self.assertTrue( tracker.isActive( script["switch"]["out"] ) )
		self.assertFalse( tracker.isActive( script["switch"]["selector"] ) )
		self.assertTrue( tracker.isActive( script["switch"]["in"][0] ) )
		self.assertFalse( tracker.isActive( script["switch"]["in"][1] ) )
		self.assertTrue( tracker.isActive( script["add1"] ) )
		self.assertFalse( tracker.isActive( script["add2"] ) )

		# Dynamic case - switch will compute input on the fly.

		stringNode = GafferTest.StringInOutNode()
		script["switch"]["selector"].setInput( stringNode["out"] )
		script["switch"]["enabled"].setValue( True )

		assertExpectedContexts()

		self.assertTrue( tracker.isActive( script["switch"] ) )
		self.assertTrue( tracker.isActive( script["switch"]["out"] ) )
		self.assertTrue( tracker.isActive( script["switch"]["selector"] ) )
		self.assertTrue( tracker.isActive( script["switch"]["in"][0] ) )
		self.assertFalse( tracker.isActive( script["switch"]["in"][1] ) )
		self.assertTrue( tracker.isActive( script["add1"] ) )
		self.assertFalse( tracker.isActive( script["add2"] ) )
		self.assertTrue( tracker.isActive( stringNode ) )
		self.assertEqual( tracker.context( stringNode ), context )

		stringNode["in"].setValue( "add2" )

		assertExpectedContexts()

		self.assertTrue( tracker.isActive( script["switch"] ) )
		self.assertTrue( tracker.isActive( script["switch"]["out"] ) )
		self.assertTrue( tracker.isActive( script["switch"]["selector"] ) )
		self.assertFalse( tracker.isActive( script["switch"]["in"][0] ) )
		self.assertTrue( tracker.isActive( script["switch"]["in"][1] ) )
		self.assertFalse( tracker.isActive( script["add1"] ) )
		self.assertTrue( tracker.isActive( script["add2"] ) )
		self.assertTrue( tracker.isActive( stringNode ) )
		self.assertEqual( tracker.context( stringNode ), context )

	def testMultipleActiveNameSwitchBranches( self ) :

		script = Gaffer.ScriptNode()

		script["add1"] = GafferTest.AddNode()
		script["add2"] = GafferTest.AddNode()

		script["switch"] = Gaffer.NameSwitch()
		script["switch"].setup( script["add1"]["sum"] )
		script["switch"]["in"][0]["value"].setInput( script["add1"]["sum"] )
		script["switch"]["in"][1]["value"].setInput( script["add2"]["sum"] )
		script["switch"]["in"][1]["name"].setValue( "add2" )
		script["switch"]["selector"].setValue( "${selector}" )

		script["contextVariables"] = Gaffer.ContextVariables()
		script["contextVariables"].setup( script["switch"]["out"]["value"] )
		script["contextVariables"]["in"].setInput( script["switch"]["out"]["value"] )
		script["contextVariables"]["variables"].addChild( Gaffer.NameValuePlug( "selector", "add2" ) )

		script["add3"] = GafferTest.AddNode()
		script["add3"]["op1"].setInput( script["switch"]["out"]["value"] )
		script["add3"]["op2"].setInput( script["contextVariables"]["out"] )

		context = Gaffer.Context()
		tracker = GafferUI.ContextTracker( script["add3"], context )

		self.assertEqual( tracker.context( script["add3"] ), context )
		self.assertEqual( tracker.context( script["switch"] ), context )
		self.assertEqual( tracker.context( script["switch"]["in"][0]["value"] ), context )
		self.assertEqual( tracker.context( script["switch"]["in"][1]["value"] ), script["contextVariables"].inPlugContext() )
		self.assertEqual( tracker.context( script["add1"] ), context )
		self.assertEqual( tracker.context( script["add2"] ), script["contextVariables"].inPlugContext() )

	def testNameSwitchNamesAndEnabled( self ) :

		script = Gaffer.ScriptNode()

		script["add1"] = GafferTest.AddNode()
		script["add2"] = GafferTest.AddNode()
		script["add3"] = GafferTest.AddNode()
		script["add4"] = GafferTest.AddNode()
		script["add5"] = GafferTest.AddNode()

		script["switch"] = Gaffer.NameSwitch()
		script["switch"]["selector"].setValue( "four" )
		script["switch"].setup( script["add1"]["sum"] )
		script["switch"]["in"].resize( 5 )
		script["switch"]["in"][0]["value"].setInput( script["add1"]["sum"] )
		script["switch"]["in"][0]["name"].setValue( "one" )
		script["switch"]["in"][1]["value"].setInput( script["add2"]["sum"] )
		script["switch"]["in"][1]["name"].setValue( "two" )
		script["switch"]["in"][2]["value"].setInput( script["add3"]["sum"] )
		script["switch"]["in"][2]["name"].setValue( "three" )
		script["switch"]["in"][2]["enabled"].setValue( False )
		script["switch"]["in"][3]["value"].setInput( script["add4"]["sum"] )
		script["switch"]["in"][3]["name"].setValue( "four" )
		script["switch"]["in"][4]["value"].setInput( script["add5"]["sum"] )
		script["switch"]["in"][4]["name"].setValue( "five" )

		script["add6"] = GafferTest.AddNode()
		script["add6"]["op1"].setInput( script["switch"]["out"]["value"] )

		context = Gaffer.Context()
		tracker = GafferUI.ContextTracker( script["add6"], context )

		# Default input `name` and `enabled` are never evaluated and `value`
		# isn't currently active.
		self.assertFalse( tracker.isActive( script["switch"]["in"][0]["enabled"] ) )
		self.assertFalse( tracker.isActive( script["switch"]["in"][0]["name"] ) )
		self.assertFalse( tracker.isActive( script["switch"]["in"][0]["value"] ) )
		# Next input should be evaluated, but it doesn't match so `value`
		# won't be active.
		self.assertTrue( tracker.isActive( script["switch"]["in"][1]["enabled"] ) )
		self.assertTrue( tracker.isActive( script["switch"]["in"][1]["name"] ) )
		self.assertFalse( tracker.isActive( script["switch"]["in"][1]["value"] ) )
		# Next input would be evaluated, but it is disabled so `name` isn't evaluated.
		self.assertTrue( tracker.isActive( script["switch"]["in"][2]["enabled"] ) )
		self.assertFalse( tracker.isActive( script["switch"]["in"][2]["name"] ) )
		self.assertFalse( tracker.isActive( script["switch"]["in"][2]["value"] ) )
		# Next input will be evaluated and will match, so `value` will be active too.
		self.assertTrue( tracker.isActive( script["switch"]["in"][3]["enabled"] ) )
		self.assertTrue( tracker.isActive( script["switch"]["in"][3]["name"] ) )
		self.assertTrue( tracker.isActive( script["switch"]["in"][3]["value"] ) )
		# Last input will be ignored because a match has already been found.
		self.assertFalse( tracker.isActive( script["switch"]["in"][4]["enabled"] ) )
		self.assertFalse( tracker.isActive( script["switch"]["in"][4]["name"] ) )
		self.assertFalse( tracker.isActive( script["switch"]["in"][4]["value"] ) )

		script["switch"]["enabled"].setValue( False )

		for plug in list( Gaffer.NameValuePlug.Range( script["switch"]["in"] ) ) :
			self.assertFalse( tracker.isActive( plug["name"] ), plug["name"].fullName() )
			self.assertFalse( tracker.isActive( plug["enabled"] ), plug["enabled"].fullName() )
			self.assertEqual(
				tracker.isActive( plug["value"] ),
				plug["value"].isSame( script["switch"]["in"][0]["value"] ),
				plug["value"].fullName()
			)

	def testContextProcessors( self ) :

		script = Gaffer.ScriptNode()

		script["add"] = GafferTest.AddNode()

		script["contextVariables"] = Gaffer.ContextVariables()
		script["contextVariables"].setup( script["add"]["sum"] )
		script["contextVariables"]["in"].setInput( script["add"]["sum"] )

		context = Gaffer.Context()
		tracker = GafferUI.ContextTracker( script["contextVariables"], context )

		self.assertTrue( tracker.isActive( script["contextVariables"] ) )
		self.assertTrue( tracker.isActive( script["contextVariables"]["enabled"] ) )
		self.assertTrue( tracker.isActive( script["contextVariables"]["variables"] ) )
		self.assertEqual( tracker.context( script["contextVariables"] ), context )
		self.assertTrue( tracker.isActive( script["add"] ) )
		self.assertEqual( tracker.context( script["add"] ), context )

		script["contextVariables"]["variables"].addChild( Gaffer.NameValuePlug( "test", 2 ) )

		self.assertTrue( tracker.isActive( script["contextVariables"] ) )
		self.assertTrue( tracker.isActive( script["contextVariables"]["enabled"] ) )
		self.assertTrue( tracker.isActive( script["contextVariables"]["variables"] ) )
		self.assertTrue( tracker.isActive( script["contextVariables"]["variables"][0] ) )
		self.assertTrue( tracker.isActive( script["contextVariables"]["variables"][0]["name"] ) )
		self.assertTrue( tracker.isActive( script["contextVariables"]["variables"][0]["value"] ) )
		self.assertEqual( tracker.context( script["contextVariables"] ), context )
		self.assertTrue( tracker.isActive( script["add"] ) )
		self.assertEqual( tracker.context( script["add"] ), script["contextVariables"].inPlugContext() )

		script["contextVariables"]["enabled"].setValue( False )

		self.assertTrue( tracker.isActive( script["contextVariables"] ) )
		self.assertTrue( tracker.isActive( script["contextVariables"]["enabled"] ) )
		self.assertFalse( tracker.isActive( script["contextVariables"]["variables"] ) )
		self.assertFalse( tracker.isActive( script["contextVariables"]["variables"][0] ) )
		self.assertFalse( tracker.isActive( script["contextVariables"]["variables"][0]["name"] ) )
		self.assertFalse( tracker.isActive( script["contextVariables"]["variables"][0]["value"] ) )
		self.assertEqual( tracker.context( script["contextVariables"] ), context )
		self.assertTrue( tracker.isActive( script["add"] ) )
		self.assertEqual( tracker.context( script["add"] ), context )

	def testContextForInactiveInputs( self ) :

		script = Gaffer.ScriptNode()

		script["add"] = GafferTest.AddNode()
		script["add"]["enabled"].setValue( False )

		script["contextVariables"] = Gaffer.ContextVariables()
		script["contextVariables"].setup( script["add"]["sum"] )
		script["contextVariables"]["in"].setInput( script["add"]["sum"] )
		script["contextVariables"]["variables"].addChild( Gaffer.NameValuePlug( "test", 2 ) )

		context = Gaffer.Context()
		tracker = GafferUI.ContextTracker( script["contextVariables"], context )

		# Even though `op2` is inactive, it still makes most sense to evaluate it
		# in the modified context, because that is the context it will be active in
		# if the node is enabled.
		self.assertFalse( tracker.isActive( script["add"]["op2"] ) )
		self.assertEqual( tracker.context( script["add"]["op2"] ), script["contextVariables"].inPlugContext() )

	def testPlugWithoutNode( self ) :

		plug = Gaffer.IntPlug()

		script = Gaffer.ScriptNode()
		script["node"] = GafferTest.AddNode()
		script["node"]["op1"].setInput( plug )

		context = Gaffer.Context()
		tracker = GafferUI.ContextTracker( script["node"], context )

		self.assertTrue( tracker.isActive( script["node"] ) )
		self.assertEqual( tracker.context( script["node"] ), context )
		self.assertTrue( tracker.isActive( script["node"]["op1"] ) )
		self.assertEqual( tracker.context( script["node"]["op1"] ), context )
		self.assertTrue( tracker.isActive( plug ) )
		self.assertEqual( tracker.context( plug ), context )

	def testLoop( self ) :

		script = Gaffer.ScriptNode()

		script["loopSource"] = GafferTest.AddNode()
		script["loopBody"] = GafferTest.AddNode()

		script["loop"] = Gaffer.Loop()
		script["loop"].setup( script["loopSource"]["sum"] )
		script["loop"]["in"].setInput( script["loopSource"]["sum"] )

		script["loopBody"]["op1"].setInput( script["loop"]["previous"] )
		script["loopBody"]["op2"].setValue( 2 )
		script["loop"]["next"].setInput( script["loopBody"]["sum"] )

		script["loop"]["iterations"].setValue( 10 )
		self.assertEqual( script["loop"]["out"].getValue(), 20 )

		context = Gaffer.Context()
		tracker = GafferUI.ContextTracker( script["loop"], context )

		self.assertTrue( tracker.isActive( script["loop"] ) )
		self.assertEqual( tracker.context( script["loop"] ), context )
		self.assertTrue( tracker.isActive( script["loop"]["iterations"] ) )
		self.assertEqual( tracker.context( script["loop"]["iterations"] ), context )
		self.assertTrue( tracker.isActive( script["loop"]["indexVariable"] ) )
		self.assertEqual( tracker.context( script["loop"]["indexVariable"] ), context )
		self.assertTrue( tracker.isActive( script["loopSource"] ) )
		self.assertEqual( tracker.context( script["loopSource"] ), context )
		self.assertTrue( tracker.isActive( script["loop"]["next"] ) )
		lastIterationContext = script["loop"].previousIteration( script["loop"]["out"] )[1]
		self.assertEqual( tracker.context( script["loop"]["next"] ), lastIterationContext )
		self.assertTrue( tracker.isActive( script["loopBody"] ) )
		self.assertEqual( tracker.context( script["loopBody"] ), lastIterationContext )

		def assertDisabledLoop() :

			self.assertTrue( tracker.isActive( script["loop"] ) )
			self.assertEqual( tracker.context( script["loop"] ), context )
			self.assertEqual( tracker.isActive( script["loop"]["iterations"] ), script["loop"]["enabled"].getValue() )
			self.assertEqual( tracker.context( script["loop"]["iterations"] ), context )
			self.assertEqual( tracker.isActive( script["loop"]["indexVariable"] ), script["loop"]["enabled"].getValue() )
			self.assertEqual( tracker.context( script["loop"]["indexVariable"] ), context )
			self.assertTrue( tracker.isActive( script["loopSource"] ) )
			self.assertEqual( tracker.context( script["loopSource"] ), context )
			self.assertFalse( tracker.isActive( script["loop"]["next"] ) )
			self.assertEqual( tracker.context( script["loop"]["next"] ), context )
			self.assertFalse( tracker.isActive( script["loopBody"] ) )
			self.assertEqual( tracker.context( script["loopBody"] ), context )

		script["loop"]["enabled"].setValue( False )
		assertDisabledLoop()

		script["loop"]["enabled"].setValue( True )
		script["loop"]["iterations"].setValue( 0 )
		assertDisabledLoop()

	def testLoopEvaluatesAllIterations( self ) :

		script = Gaffer.ScriptNode()

		script["loopSource"] = GafferTest.AddNode()
		script["loopBody"] = GafferTest.AddNode()

		script["loopIndexQuery"] = Gaffer.ContextQuery()
		indexQuery = script["loopIndexQuery"].addQuery( Gaffer.IntPlug() )
		indexQuery["name"].setValue( "loop:index" )

		script["loopSwitch"] = Gaffer.Switch()
		script["loopSwitch"].setup( script["loopBody"]["op1"] )
		script["loopSwitch"]["index"].setInput( script["loopIndexQuery"]["out"][0]["value"] )

		script["loop"] = Gaffer.Loop()
		script["loop"].setup( script["loopSource"]["sum"] )
		script["loop"]["in"].setInput( script["loopSource"]["sum"] )

		script["loopBody"]["op1"].setInput( script["loop"]["previous"] )
		script["loopBody"]["op2"].setInput( script["loopSwitch"]["out"] )
		script["loop"]["next"].setInput( script["loopBody"]["sum"] )

		iterations = 10
		script["loop"]["iterations"].setValue( iterations )

		for i in range( 0, iterations ) :
			switchInput = GafferTest.AddNode()
			script[f"switchInput{i}"] = switchInput
			switchInput["op1"].setValue( i )
			script["loopSwitch"]["in"][i].setInput( switchInput["sum"] )

		self.assertEqual( script["loop"]["out"].getValue(), sum( range( 0, iterations ) ) )

		context = Gaffer.Context()
		tracker = GafferUI.ContextTracker( script["loop"], context )
		self.__connectUpdater( tracker )

		for i in range( 0, iterations ) :
			switchInput = script["loopSwitch"]["in"][i]
			self.assertTrue( tracker.isActive( switchInput ), switchInput.fullName() )
			self.assertEqual( tracker.context( switchInput )["loop:index"], i )
			self.assertTrue( tracker.isActive( switchInput.source() ), switchInput.source().fullName() )
			self.assertEqual( tracker.context(  switchInput.source() )["loop:index"], i )
			self.assertTrue( tracker.isActive( switchInput.source().node() ), switchInput.source().node().fullName() )
			self.assertEqual( tracker.context( switchInput.source().node() )["loop:index"], i )

	def testMultiplexedBox( self ) :

		script = Gaffer.ScriptNode()

		script["addA"] = GafferTest.AddNode()
		script["addB"] = GafferTest.AddNode()

		script["box"] = Gaffer.Box()
		script["box"]["addA"] = GafferTest.AddNode()
		script["box"]["addB"] = GafferTest.AddNode()

		Gaffer.PlugAlgo.promoteWithName( script["box"]["addA"]["op1"], "opA" )
		Gaffer.PlugAlgo.promoteWithName( script["box"]["addB"]["op1"], "opB" )
		script["box"]["opA"].setInput( script["addA"]["sum"] )
		script["box"]["opB"].setInput( script["addB"]["sum"] )

		Gaffer.PlugAlgo.promoteWithName( script["box"]["addA"]["sum"], "sumA" )
		Gaffer.PlugAlgo.promoteWithName( script["box"]["addB"]["sum"], "sumB" )
		script["box"]["sumA"].setInput( script["box"]["addA"]["sum"] )
		script["box"]["sumB"].setInput( script["box"]["addB"]["sum"] )

		script["resultA"] = GafferTest.AddNode()
		script["resultA"]["op1"].setInput( script["box"]["sumA"] )

		script["resultB"] = GafferTest.AddNode()
		script["resultB"]["op1"].setInput( script["box"]["sumB"] )

		context = Gaffer.Context()
		tracker = GafferUI.ContextTracker( script["resultA"], context )

		self.assertTrue( tracker.isActive( script["resultA"] ) )
		self.assertFalse( tracker.isActive( script["resultB"] ) )
		self.assertTrue( tracker.isActive( script["box"]["sumA"] ) )
		self.assertFalse( tracker.isActive( script["box"]["sumB"] ) )
		self.assertTrue( tracker.isActive( script["box"] ) )
		self.assertTrue( tracker.isActive( script["box"]["addA"] ) )
		self.assertFalse( tracker.isActive( script["box"]["addB"] ) )
		self.assertTrue( tracker.isActive( script["box"]["opA"] ) )
		self.assertFalse( tracker.isActive( script["box"]["opB"] ) )
		self.assertTrue( tracker.isActive( script["addA"] ) )
		self.assertFalse( tracker.isActive( script["addB"] ) )

if __name__ == "__main__":
	unittest.main()
