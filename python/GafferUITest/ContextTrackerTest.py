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

import inspect
import threading
import unittest

import IECore

import Gaffer
import GafferTest
import GafferUI
import GafferUITest

class ContextTrackerTest( GafferUITest.TestCase ) :

	class UpdateHandler( GafferTest.ParallelAlgoTest.UIThreadCallHandler ) :

		def __exit__( self, type, value, traceBack ) :

			GafferUITest.TestCase().waitForIdle()
			self.assertCalled()

			GafferTest.ParallelAlgoTest.UIThreadCallHandler.__exit__( self, type, value, traceBack )

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
		with self.UpdateHandler()  :
			tracker = GafferUI.ContextTracker( script["add4"], context )

		def assertExpectedContexts() :

			# Untracked nodes and plugs fall back to using the target
			# context, so everything has the same context.

			for node in Gaffer.Node.Range( script ) :
				self.assertEqual( tracker.context( node ), context )
				for plug in Gaffer.Plug.RecursiveRange( node ) :
					self.assertEqual( tracker.context( plug ), context )

		assertExpectedContexts( )

		for node in [ script["add1"], script["add2"], script["add3"], script["add4"] ] :
			for graphComponent in [ node, node["op1"], node["op2"], node["sum"], node["enabled"] ] :
				self.assertTrue( tracker.isTracked( graphComponent ), graphComponent.fullName() )

		for graphComponent in [ script["unconnected"], script["unconnected"]["op1"], script["unconnected"]["op2"], script["unconnected"]["sum"], script["unconnected"]["enabled"] ] :
			self.assertFalse( tracker.isTracked( graphComponent ) )

		with self.UpdateHandler()  :
			script["add3"]["enabled"].setValue( False )

		assertExpectedContexts( )

		self.assertTrue( tracker.isTracked( script["add4"] ) )
		self.assertTrue( tracker.isTracked( script["add3"] ) )
		self.assertTrue( tracker.isTracked( script["add3"]["op1"] ) )
		self.assertFalse( tracker.isTracked( script["add3"]["op2"] ) )
		self.assertTrue( tracker.isTracked( script["add1"] ) )
		self.assertFalse( tracker.isTracked( script["add2"] ) )

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
		with self.UpdateHandler()  :
			tracker = GafferUI.ContextTracker( script["switch"], context )

		def assertExpectedContexts() :

			# Untracked nodes and plugs fall back to using the target
			# context, so everything has the same context.

			for node in [ script["add1"], script["add2"], script["switch"] ] :
				self.assertEqual( tracker.context( node ), context, node.fullName() )
				for plug in Gaffer.Plug.RecursiveRange( node ) :
					self.assertEqual( tracker.context( plug ), context, plug.fullName() )

		assertExpectedContexts()

		self.assertTrue( tracker.isTracked( script["switch"] ) )
		self.assertTrue( tracker.isTracked( script["switch"]["out"] ) )
		self.assertTrue( tracker.isTracked( script["switch"]["index"] ) )
		self.assertTrue( tracker.isTracked( script["switch"]["enabled"] ) )
		self.assertTrue( tracker.isTracked( script["switch"]["in"][0] ) )
		self.assertFalse( tracker.isTracked( script["switch"]["in"][1] ) )
		self.assertTrue( tracker.isTracked( script["add1"] ) )
		self.assertFalse( tracker.isTracked( script["add2"] ) )

		with self.UpdateHandler()  :
			script["switch"]["index"].setValue( 1 )

		assertExpectedContexts()

		self.assertTrue( tracker.isTracked( script["switch"] ) )
		self.assertTrue( tracker.isTracked( script["switch"]["out"] ) )
		self.assertTrue( tracker.isTracked( script["switch"]["index"] ) )
		self.assertTrue( tracker.isTracked( script["switch"]["enabled"] ) )
		self.assertFalse( tracker.isTracked( script["switch"]["in"][0] ) )
		self.assertTrue( tracker.isTracked( script["switch"]["in"][1] ) )
		self.assertFalse( tracker.isTracked( script["add1"] ) )
		self.assertTrue( tracker.isTracked( script["add2"] ) )

		with self.UpdateHandler()  :
			script["switch"]["enabled"].setValue( False )

		assertExpectedContexts()

		self.assertTrue( tracker.isTracked( script["switch"] ) )
		self.assertTrue( tracker.isTracked( script["switch"]["out"] ) )
		self.assertFalse( tracker.isTracked( script["switch"]["index"] ) )
		self.assertTrue( tracker.isTracked( script["switch"]["enabled"] ) )
		self.assertTrue( tracker.isTracked( script["switch"]["in"][0] ) )
		self.assertFalse( tracker.isTracked( script["switch"]["in"][1] ) )
		self.assertTrue( tracker.isTracked( script["add1"] ) )
		self.assertFalse( tracker.isTracked( script["add2"] ) )

		# Dynamic case - switch will compute input on the fly.

		with self.UpdateHandler()  :
			script["add3"] = GafferTest.AddNode()
			script["switch"]["index"].setInput( script["add3"]["sum"] )
			script["switch"]["enabled"].setValue( True )

		assertExpectedContexts()

		self.assertTrue( tracker.isTracked( script["switch"] ) )
		self.assertTrue( tracker.isTracked( script["switch"]["out"] ) )
		self.assertTrue( tracker.isTracked( script["switch"]["index"] ) )
		self.assertTrue( tracker.isTracked( script["switch"]["enabled"] ) )
		self.assertTrue( tracker.isTracked( script["switch"]["in"][0] ) )
		self.assertFalse( tracker.isTracked( script["switch"]["in"][1] ) )
		self.assertTrue( tracker.isTracked( script["add1"] ) )
		self.assertFalse( tracker.isTracked( script["add2"] ) )
		self.assertTrue( tracker.isTracked( script["add3"] ) )
		self.assertEqual( tracker.context( script["add3"] ), context )

		with self.UpdateHandler()  :
			script["add3"]["op1"].setValue( 1 )

		assertExpectedContexts()

		self.assertTrue( tracker.isTracked( script["switch"] ) )
		self.assertTrue( tracker.isTracked( script["switch"]["out"] ) )
		self.assertTrue( tracker.isTracked( script["switch"]["index"] ) )
		self.assertTrue( tracker.isTracked( script["switch"]["enabled"] ) )
		self.assertFalse( tracker.isTracked( script["switch"]["in"][0] ) )
		self.assertTrue( tracker.isTracked( script["switch"]["in"][1] ) )
		self.assertFalse( tracker.isTracked( script["add1"] ) )
		self.assertTrue( tracker.isTracked( script["add2"] ) )
		self.assertTrue( tracker.isTracked( script["add3"] ) )
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
		with self.UpdateHandler()  :
			tracker = GafferUI.ContextTracker( script["switch"], context )

		def assertExpectedContexts() :

			# Untracked nodes and plugs fall back to using the target
			# context, so everything has the same context.

			for node in [ script["add1"], script["add2"], script["switch"] ] :
				self.assertEqual( tracker.context( node ), context )
				for plug in Gaffer.Plug.RecursiveRange( node ) :
					self.assertEqual( tracker.context( plug ), context )

		assertExpectedContexts()

		self.assertTrue( tracker.isTracked( script["switch"] ) )
		self.assertTrue( tracker.isTracked( script["switch"]["out"] ) )
		self.assertTrue( tracker.isTracked( script["switch"]["selector"] ) )
		self.assertTrue( tracker.isTracked( script["switch"]["in"][0] ) )
		self.assertFalse( tracker.isTracked( script["switch"]["in"][1] ) )
		self.assertTrue( tracker.isTracked( script["add1"] ) )
		self.assertFalse( tracker.isTracked( script["add2"] ) )

		with self.UpdateHandler()  :
			script["switch"]["selector"].setValue( "add2" )

		assertExpectedContexts()

		self.assertTrue( tracker.isTracked( script["switch"] ) )
		self.assertTrue( tracker.isTracked( script["switch"]["out"] ) )
		self.assertTrue( tracker.isTracked( script["switch"]["selector"] ) )
		self.assertFalse( tracker.isTracked( script["switch"]["in"][0] ) )
		self.assertTrue( tracker.isTracked( script["switch"]["in"][1] ) )
		self.assertFalse( tracker.isTracked( script["add1"] ) )
		self.assertTrue( tracker.isTracked( script["add2"] ) )

		with self.UpdateHandler()  :
			script["switch"]["enabled"].setValue( False )

		assertExpectedContexts()

		self.assertTrue( tracker.isTracked( script["switch"] ) )
		self.assertTrue( tracker.isTracked( script["switch"]["out"] ) )
		self.assertFalse( tracker.isTracked( script["switch"]["selector"] ) )
		self.assertTrue( tracker.isTracked( script["switch"]["in"][0] ) )
		self.assertFalse( tracker.isTracked( script["switch"]["in"][1] ) )
		self.assertTrue( tracker.isTracked( script["add1"] ) )
		self.assertFalse( tracker.isTracked( script["add2"] ) )

		# Dynamic case - switch will compute input on the fly.

		with self.UpdateHandler()  :
			stringNode = GafferTest.StringInOutNode()
			script["switch"]["selector"].setInput( stringNode["out"] )
			script["switch"]["enabled"].setValue( True )

		assertExpectedContexts()

		self.assertTrue( tracker.isTracked( script["switch"] ) )
		self.assertTrue( tracker.isTracked( script["switch"]["out"] ) )
		self.assertTrue( tracker.isTracked( script["switch"]["selector"] ) )
		self.assertTrue( tracker.isTracked( script["switch"]["in"][0] ) )
		self.assertFalse( tracker.isTracked( script["switch"]["in"][1] ) )
		self.assertTrue( tracker.isTracked( script["add1"] ) )
		self.assertFalse( tracker.isTracked( script["add2"] ) )
		self.assertTrue( tracker.isTracked( stringNode ) )
		self.assertEqual( tracker.context( stringNode ), context )

		with self.UpdateHandler()  :
			stringNode["in"].setValue( "add2" )

		assertExpectedContexts()

		self.assertTrue( tracker.isTracked( script["switch"] ) )
		self.assertTrue( tracker.isTracked( script["switch"]["out"] ) )
		self.assertTrue( tracker.isTracked( script["switch"]["selector"] ) )
		self.assertFalse( tracker.isTracked( script["switch"]["in"][0] ) )
		self.assertTrue( tracker.isTracked( script["switch"]["in"][1] ) )
		self.assertFalse( tracker.isTracked( script["add1"] ) )
		self.assertTrue( tracker.isTracked( script["add2"] ) )
		self.assertTrue( tracker.isTracked( stringNode ) )
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
		with self.UpdateHandler()  :
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
		with self.UpdateHandler()  :
			tracker = GafferUI.ContextTracker( script["add6"], context )

		# Default input `name` and `enabled` are never evaluated and `value`
		# isn't currently active.
		self.assertFalse( tracker.isTracked( script["switch"]["in"][0]["enabled"] ) )
		self.assertFalse( tracker.isTracked( script["switch"]["in"][0]["name"] ) )
		self.assertFalse( tracker.isTracked( script["switch"]["in"][0]["value"] ) )
		# Next input should be evaluated, but it doesn't match so `value`
		# won't be active.
		self.assertTrue( tracker.isTracked( script["switch"]["in"][1]["enabled"] ) )
		self.assertTrue( tracker.isTracked( script["switch"]["in"][1]["name"] ) )
		self.assertFalse( tracker.isTracked( script["switch"]["in"][1]["value"] ) )
		# Next input would be evaluated, but it is disabled so `name` isn't evaluated.
		self.assertTrue( tracker.isTracked( script["switch"]["in"][2]["enabled"] ) )
		self.assertFalse( tracker.isTracked( script["switch"]["in"][2]["name"] ) )
		self.assertFalse( tracker.isTracked( script["switch"]["in"][2]["value"] ) )
		# Next input will be evaluated and will match, so `value` will be active too.
		self.assertTrue( tracker.isTracked( script["switch"]["in"][3]["enabled"] ) )
		self.assertTrue( tracker.isTracked( script["switch"]["in"][3]["name"] ) )
		self.assertTrue( tracker.isTracked( script["switch"]["in"][3]["value"] ) )
		# Last input will be ignored because a match has already been found.
		self.assertFalse( tracker.isTracked( script["switch"]["in"][4]["enabled"] ) )
		self.assertFalse( tracker.isTracked( script["switch"]["in"][4]["name"] ) )
		self.assertFalse( tracker.isTracked( script["switch"]["in"][4]["value"] ) )

		with self.UpdateHandler()  :
			script["switch"]["enabled"].setValue( False )

		for plug in list( Gaffer.NameValuePlug.Range( script["switch"]["in"] ) ) :
			self.assertFalse( tracker.isTracked( plug["name"] ), plug["name"].fullName() )
			self.assertFalse( tracker.isTracked( plug["enabled"] ), plug["enabled"].fullName() )
			self.assertEqual(
				tracker.isTracked( plug["value"] ),
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
		with self.UpdateHandler()  :
			tracker = GafferUI.ContextTracker( script["contextVariables"], context )

		self.assertTrue( tracker.isTracked( script["contextVariables"] ) )
		self.assertTrue( tracker.isTracked( script["contextVariables"]["enabled"] ) )
		self.assertTrue( tracker.isTracked( script["contextVariables"]["variables"] ) )
		self.assertEqual( tracker.context( script["contextVariables"] ), context )
		self.assertTrue( tracker.isTracked( script["add"] ) )
		self.assertEqual( tracker.context( script["add"] ), context )

		with self.UpdateHandler()  :
			script["contextVariables"]["variables"].addChild( Gaffer.NameValuePlug( "test", 2 ) )

		self.assertTrue( tracker.isTracked( script["contextVariables"] ) )
		self.assertTrue( tracker.isTracked( script["contextVariables"]["enabled"] ) )
		self.assertTrue( tracker.isTracked( script["contextVariables"]["variables"] ) )
		self.assertTrue( tracker.isTracked( script["contextVariables"]["variables"][0] ) )
		self.assertTrue( tracker.isTracked( script["contextVariables"]["variables"][0]["name"] ) )
		self.assertTrue( tracker.isTracked( script["contextVariables"]["variables"][0]["value"] ) )
		self.assertEqual( tracker.context( script["contextVariables"] ), context )
		self.assertTrue( tracker.isTracked( script["add"] ) )
		self.assertEqual( tracker.context( script["add"] ), script["contextVariables"].inPlugContext() )

		with self.UpdateHandler()  :
			script["contextVariables"]["enabled"].setValue( False )

		self.assertTrue( tracker.isTracked( script["contextVariables"] ) )
		self.assertTrue( tracker.isTracked( script["contextVariables"]["enabled"] ) )
		self.assertFalse( tracker.isTracked( script["contextVariables"]["variables"] ) )
		self.assertFalse( tracker.isTracked( script["contextVariables"]["variables"][0] ) )
		self.assertFalse( tracker.isTracked( script["contextVariables"]["variables"][0]["name"] ) )
		self.assertFalse( tracker.isTracked( script["contextVariables"]["variables"][0]["value"] ) )
		self.assertEqual( tracker.context( script["contextVariables"] ), context )
		self.assertTrue( tracker.isTracked( script["add"] ) )
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
		with self.UpdateHandler()  :
			tracker = GafferUI.ContextTracker( script["contextVariables"], context )

		# Even though `op2` is inactive, it still makes most sense to evaluate it
		# in the modified context, because that is the context it will be active in
		# if the node is enabled.
		self.assertFalse( tracker.isTracked( script["add"]["op2"] ) )
		self.assertEqual( tracker.context( script["add"]["op2"] ), script["contextVariables"].inPlugContext() )

	def testPlugWithoutNode( self ) :

		plug = Gaffer.IntPlug()

		script = Gaffer.ScriptNode()
		script["node"] = GafferTest.AddNode()
		script["node"]["op1"].setInput( plug )

		context = Gaffer.Context()
		with self.UpdateHandler()  :
			tracker = GafferUI.ContextTracker( script["node"], context )

		self.assertTrue( tracker.isTracked( script["node"] ) )
		self.assertEqual( tracker.context( script["node"] ), context )
		self.assertTrue( tracker.isTracked( script["node"]["op1"] ) )
		self.assertEqual( tracker.context( script["node"]["op1"] ), context )
		self.assertTrue( tracker.isTracked( plug ) )
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
		with self.UpdateHandler()  :
			tracker = GafferUI.ContextTracker( script["loop"], context )

		self.assertTrue( tracker.isTracked( script["loop"] ) )
		self.assertEqual( tracker.context( script["loop"] ), context )
		self.assertTrue( tracker.isTracked( script["loop"]["iterations"] ) )
		self.assertEqual( tracker.context( script["loop"]["iterations"] ), context )
		self.assertTrue( tracker.isTracked( script["loop"]["indexVariable"] ) )
		self.assertEqual( tracker.context( script["loop"]["indexVariable"] ), context )
		self.assertTrue( tracker.isTracked( script["loopSource"] ) )
		self.assertEqual( tracker.context( script["loopSource"] ), context )
		self.assertTrue( tracker.isTracked( script["loop"]["next"] ) )
		lastIterationContext = script["loop"].previousIteration( script["loop"]["out"] )[1]
		self.assertEqual( tracker.context( script["loop"]["next"] ), lastIterationContext )
		self.assertTrue( tracker.isTracked( script["loopBody"] ) )
		self.assertEqual( tracker.context( script["loopBody"] ), lastIterationContext )

		def assertDisabledLoop() :

			self.assertTrue( tracker.isTracked( script["loop"] ) )
			self.assertEqual( tracker.context( script["loop"] ), context )
			self.assertEqual( tracker.isTracked( script["loop"]["iterations"] ), script["loop"]["enabled"].getValue() )
			self.assertEqual( tracker.context( script["loop"]["iterations"] ), context )
			self.assertEqual( tracker.isTracked( script["loop"]["indexVariable"] ), script["loop"]["enabled"].getValue() )
			self.assertEqual( tracker.context( script["loop"]["indexVariable"] ), context )
			self.assertTrue( tracker.isTracked( script["loopSource"] ) )
			self.assertEqual( tracker.context( script["loopSource"] ), context )
			self.assertFalse( tracker.isTracked( script["loop"]["next"] ) )
			self.assertEqual( tracker.context( script["loop"]["next"] ), context )
			self.assertFalse( tracker.isTracked( script["loopBody"] ) )
			self.assertEqual( tracker.context( script["loopBody"] ), context )

		with self.UpdateHandler()  :
			script["loop"]["enabled"].setValue( False )
		assertDisabledLoop()

		with self.UpdateHandler()  :
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
		with self.UpdateHandler()  :
			tracker = GafferUI.ContextTracker( script["loop"], context )

		for i in range( 0, iterations ) :
			switchInput = script["loopSwitch"]["in"][i]
			self.assertTrue( tracker.isTracked( switchInput ), switchInput.fullName() )
			self.assertEqual( tracker.context( switchInput )["loop:index"], i )
			self.assertTrue( tracker.isTracked( switchInput.source() ), switchInput.source().fullName() )
			self.assertEqual( tracker.context(  switchInput.source() )["loop:index"], i )
			self.assertTrue( tracker.isTracked( switchInput.source().node() ), switchInput.source().node().fullName() )
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
		with self.UpdateHandler()  :
			tracker = GafferUI.ContextTracker( script["resultA"], context )

		self.assertTrue( tracker.isTracked( script["resultA"] ) )
		self.assertFalse( tracker.isTracked( script["resultB"] ) )
		self.assertTrue( tracker.isTracked( script["box"]["sumA"] ) )
		self.assertFalse( tracker.isTracked( script["box"]["sumB"] ) )
		self.assertTrue( tracker.isTracked( script["box"] ) )
		self.assertTrue( tracker.isTracked( script["box"]["addA"] ) )
		self.assertFalse( tracker.isTracked( script["box"]["addB"] ) )
		self.assertTrue( tracker.isTracked( script["box"]["opA"] ) )
		self.assertFalse( tracker.isTracked( script["box"]["opB"] ) )
		self.assertTrue( tracker.isTracked( script["addA"] ) )
		self.assertFalse( tracker.isTracked( script["addB"] ) )

	def testAcquire( self ) :

		script = Gaffer.ScriptNode()

		script["add1"] = GafferTest.AddNode()
		script["add2"] = GafferTest.AddNode()

		with self.UpdateHandler()  :
			tracker1 = GafferUI.ContextTracker.acquire( script["add1"] )
		self.assertTrue( tracker1.isSame( GafferUI.ContextTracker.acquire( script["add1"] ) ) )
		self.assertTrue( tracker1.isTracked( script["add1"] ) )
		self.assertFalse( tracker1.isTracked( script["add2"] ) )

		with self.UpdateHandler()  :
			tracker2 = GafferUI.ContextTracker.acquire( script["add2"] )
		self.assertTrue( tracker2.isSame( GafferUI.ContextTracker.acquire( script["add2"] ) ) )
		self.assertTrue( tracker2.isTracked( script["add2"] ) )
		self.assertFalse( tracker2.isTracked( script["add1"] ) )

	def testAcquireLifetime( self ) :

		script = Gaffer.ScriptNode()

		script["node"] = GafferTest.MultiplyNode()
		nodeSlots = script["node"].plugDirtiedSignal().numSlots()
		nodeRefCount = script["node"].refCount()

		with self.UpdateHandler()  :
			tracker = GafferUI.ContextTracker.acquire( script["node"] )
		del tracker

		# Indicates that `tracker` was truly destroyed.
		self.assertEqual( script["node"].plugDirtiedSignal().numSlots(), nodeSlots )
		self.assertEqual( script["node"].refCount(), nodeRefCount )

		# Should be a whole new instance.
		with self.UpdateHandler()  :
			tracker = GafferUI.ContextTracker.acquire( script["node"] )
		self.assertTrue( tracker.isTracked( script["node"] ) )

	def testAcquireForFocus( self ) :

		script = Gaffer.ScriptNode()

		script["add1"] = GafferTest.AddNode()
		script["add2"] = GafferTest.AddNode()

		tracker = GafferUI.ContextTracker.acquireForFocus( script )
		self.assertTrue( tracker.isSame( GafferUI.ContextTracker.acquireForFocus( script ) ) )

		self.assertFalse( tracker.isTracked( script["add1" ] ) )
		self.assertFalse( tracker.isTracked( script["add2" ] ) )

		with self.UpdateHandler()  :
			script.setFocus( script["add1"] )
		self.assertTrue( tracker.isTracked( script["add1" ] ) )
		self.assertFalse( tracker.isTracked( script["add2" ] ) )

		with self.UpdateHandler()  :
			script.setFocus( script["add2"] )
		self.assertFalse( tracker.isTracked( script["add1" ] ) )
		self.assertTrue( tracker.isTracked( script["add2" ] ) )

		script.setFocus( None )
		self.assertFalse( tracker.isTracked( script["add1" ] ) )
		self.assertFalse( tracker.isTracked( script["add2" ] ) )

	def testAcquireForFocusLifetime( self ) :

		script = Gaffer.ScriptNode()
		contextSlots = script.context().changedSignal().numSlots()
		contextRefCount = script.context().refCount()

		tracker = GafferUI.ContextTracker.acquireForFocus( script )
		del tracker

		# Indicates that `tracker` was truly destroyed.
		self.assertEqual( script.context().changedSignal().numSlots(), contextSlots )
		self.assertEqual( script.context().refCount(), contextRefCount )

		# Should be a whole new instance.
		script["node"] = GafferTest.MultiplyNode()
		script.setFocus( script["node"] )
		with self.UpdateHandler()  :
			tracker = GafferUI.ContextTracker.acquireForFocus( script )
		self.assertTrue( tracker.isTracked( script["node"] ) )

	def testAcquireNone( self ) :

		tracker1 = GafferUI.ContextTracker.acquire( None )
		self.assertTrue( tracker1.isSame( GafferUI.ContextTracker.acquire( None ) ) )

		tracker2 = GafferUI.ContextTracker.acquireForFocus( None )
		self.assertTrue( tracker2.isSame( GafferUI.ContextTracker.acquireForFocus( None ) ) )

		self.assertTrue( tracker1.isSame( tracker2 ) )
		self.assertEqual( tracker1.targetContext(), Gaffer.Context() )

		node = GafferTest.AddNode()
		self.assertFalse( tracker1.isTracked( node ) )
		self.assertFalse( tracker1.isTracked( node["sum"] ) )
		self.assertEqual( tracker1.context( node ), tracker1.targetContext() )
		self.assertEqual( tracker1.context( node["sum"] ), tracker1.targetContext() )

	def testCancellation( self ) :

		script = Gaffer.ScriptNode()
		script["node"] = GafferTest.AddNode()

		ContextTrackerTest.expressionStartedCondition = threading.Condition()

		script["expression"] = Gaffer.Expression()
		script["expression"].setExpression( inspect.cleandoc(
			"""
			import IECore
			import GafferUITest

			if context.get( "waitForCancellation", True ) :

				# Let the test know the expression has started running.
				with GafferUITest.ContextTrackerTest.expressionStartedCondition :
					GafferUITest.ContextTrackerTest.expressionStartedCondition.notify()

				# Loop forever unless we're cancelled
				while True :
					IECore.Canceller.check( context.canceller() )

			parent["node"]["enabled"] = True
			"""
		) )

		# Start an update, and wait for the expression to start on the
		# background thread.

		context = Gaffer.Context()
		with ContextTrackerTest.expressionStartedCondition :
			tracker = GafferUI.ContextTracker( script["node"], context )
			self.waitForIdle()
			ContextTrackerTest.expressionStartedCondition.wait()

		# The update won't have completed because the expression is stuck.
		self.assertFalse( tracker.isTracked( script["node"] ) )

		# Make a graph edit that will cancel the expression and restart
		# the background task.

		with ContextTrackerTest.expressionStartedCondition :
			with GafferTest.ParallelAlgoTest.UIThreadCallHandler() as handler :
				script["node"]["op1"].setValue( 1 )
				handler.assertCalled() # Handle UI thread call made when background task detects cancellation.
				self.waitForIdle() # Handle idle event used to restart update.
				ContextTrackerTest.expressionStartedCondition.wait()

		# Again, the update won't have completed because the expression is stuck.
		self.assertFalse( tracker.isTracked( script["node"] ) )

		# Make a context edit that will cancel the expression and restart the
		# background task.

		with self.UpdateHandler() as handler :
			context["waitForCancellation"] = False
			# Handles UI thread call made when background task is cancelled.
			handler.assertCalled()
			# `handler.__exit__()` then handles the events needed to restart
			# and successfully complete the update.

		# This time we expect the update to have finished successfully.

		self.assertTrue( tracker.isTracked( script["node"] ) )

	def testNoCancellersInCapturedContexts( self ) :

		script = Gaffer.ScriptNode()
		script["add"] = GafferTest.AddNode()
		script["contextVariables"] = Gaffer.ContextVariables()
		script["contextVariables"].setup( script["add"]["sum"] )
		script["contextVariables"]["in"].setInput( script["add"]["sum"] )
		script["contextVariables"].addChild( Gaffer.NameValuePlug( "test", "test" ) )

		context = Gaffer.Context()
		with self.UpdateHandler() :
			tracker = GafferUI.ContextTracker( script["contextVariables"], context )

		for g in Gaffer.GraphComponent.Range( script ) :
			self.assertIsNone( tracker.context( g ).canceller(), g.fullName() )

	def testBadChangedSlot( self ) :

		script = Gaffer.ScriptNode()
		script["add"] = GafferTest.AddNode()

		context = Gaffer.Context()
		with self.UpdateHandler() :
			tracker = GafferUI.ContextTracker( script["add"], context )

		callsMade = 0
		def slot( tracker ) :

			nonlocal callsMade
			callsMade += 1
			if callsMade == 2 :
				raise RuntimeError( "Bad callback" )

		for i in range( 0, 10 ) :
			tracker.changedSignal().connect( slot, scoped = False )

		with IECore.CapturingMessageHandler() as mh :
			with self.UpdateHandler() :
				script["add"]["op1"].setValue( 1 )

		# One bad slot in the middle shouldn't prevent other slots being
		# invoked. Instead, the error should just be reported as a message.

		self.assertEqual( callsMade, 10 )
		self.assertEqual( len( mh.messages ), 1 )
		self.assertIn( "RuntimeError: Bad callback", mh.messages[0].message )

	def testDeleteDuringUpdate( self ) :

		for i in range( 0, 10 ) :

			script = Gaffer.ScriptNode()
			script["add"] = GafferTest.AddNode()

			ContextTrackerTest.expressionStartedCondition = threading.Condition()

			script["expression"] = Gaffer.Expression()
			script["expression"].setExpression(
				inspect.cleandoc(
					"""
					import GafferUITest
					with GafferUITest.ContextTrackerTest.expressionStartedCondition :
						GafferUITest.ContextTrackerTest.expressionStartedCondition.notify()

					# Loop forever unless we're cancelled
					while True :
						IECore.Canceller.check( context.canceller() )

					parent["add"]["enabled"] = True
					"""
				)
			)

			context = Gaffer.Context()

			with ContextTrackerTest.expressionStartedCondition :
				tracker = GafferUI.ContextTracker( script["add"], context )
				# Wait for the background update to start.
				GafferUITest.TestCase().waitForIdle()
				ContextTrackerTest.expressionStartedCondition.wait()

			# Blow everything away while the background update is still going on.
			del tracker

if __name__ == "__main__":
	unittest.main()
