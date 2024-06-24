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

import imath

import IECore

import Gaffer
import GafferTest
import GafferUI
import GafferUITest

class AnnotationsGadgetTest( GafferUITest.TestCase ) :

	def testSimpleText( self ) :

		script = Gaffer.ScriptNode()
		script["node"] = Gaffer.Node()

		graphGadget = GafferUI.GraphGadget( script )
		gadget = graphGadget["__annotations"]
		self.assertEqual( gadget.annotationText( script["node"] ), "" )

		Gaffer.MetadataAlgo.addAnnotation( script["node"], "user", Gaffer.MetadataAlgo.Annotation( "test" ) )
		self.assertEqual( gadget.annotationText( script["node"] ), "test" )

		Gaffer.MetadataAlgo.addAnnotation( script["node"], "user", Gaffer.MetadataAlgo.Annotation( "test2" ) )
		self.assertEqual( gadget.annotationText( script["node"] ), "test2" )

		Gaffer.MetadataAlgo.removeAnnotation( script["node"], "user" )
		self.assertEqual( gadget.annotationText( script["node"] ), "" )

	def testExtendLifetimePastGraphGadget( self ) :

		script = Gaffer.ScriptNode()
		script["node"] = Gaffer.Node()

		graphGadget = GafferUI.GraphGadget( script )
		gadget = graphGadget["__annotations"]
		del graphGadget

		Gaffer.MetadataAlgo.addAnnotation( script["node"], "user", Gaffer.MetadataAlgo.Annotation( "test" ) )
		self.assertEqual( gadget.annotationText( script["node"] ), "" )

	def testSubstitutedText( self ) :

		script = Gaffer.ScriptNode()
		script["node"] = GafferTest.AddNode()

		graphGadget = GafferUI.GraphGadget( script )
		gadget = graphGadget["__annotations"]
		self.assertEqual( gadget.annotationText( script["node"] ), "" )

		Gaffer.MetadataAlgo.addAnnotation( script["node"], "user", Gaffer.MetadataAlgo.Annotation( "test : {op1}" ) )
		self.assertEqual( gadget.annotationText( script["node"] ), "test : 0" )

		script["node"]["op1"].setValue( 1 )
		self.assertEqual( gadget.annotationText( script["node"] ), "test : 1" )

		Gaffer.MetadataAlgo.addAnnotation( script["node"], "user", Gaffer.MetadataAlgo.Annotation( "{}" ) )
		self.assertEqual( gadget.annotationText( script["node"] ), "" )

		Gaffer.MetadataAlgo.addAnnotation( script["node"], "user", Gaffer.MetadataAlgo.Annotation( "{notAPlug}" ) )
		self.assertEqual( gadget.annotationText( script["node"] ), "" )

	def testSubstitutionsByPlugType( self ) :

		script = Gaffer.ScriptNode()
		script["node"] = GafferTest.AddNode()
		Gaffer.MetadataAlgo.addAnnotation( script["node"], "user", Gaffer.MetadataAlgo.Annotation( "{plug}" ) )

		graphGadget = GafferUI.GraphGadget( script )
		gadget = graphGadget["__annotations"]

		for plugType, value, substitution in [
			( Gaffer.BoolPlug, True, "On" ),
			( Gaffer.BoolPlug, False, "Off" ),
			( Gaffer.IntPlug, 1, "1" ),
			( Gaffer.FloatPlug, 1.1, "1.1" ),
			( Gaffer.V2iPlug, imath.V2i( 1, 2 ), "1, 2" ),
			( Gaffer.Color3fPlug, imath.Color3f( 1, 2, 3 ), "1, 2, 3" ),
			( Gaffer.StringVectorDataPlug, IECore.StringVectorData( [ "1", "2", "3" ] ), "1, 2, 3" ),
			( Gaffer.IntVectorDataPlug, IECore.IntVectorData( [ 1, 2, 3 ] ), "1, 2, 3" ),
		] :

			script["node"]["plug"] = plugType( defaultValue = value )
			self.assertEqual( gadget.annotationText( script["node"] ), substitution )

	def testInitialSubstitutedText( self ) :

		script = Gaffer.ScriptNode()
		script["node"] = GafferTest.AddNode()
		Gaffer.MetadataAlgo.addAnnotation( script["node"], "user", Gaffer.MetadataAlgo.Annotation( "test : {op1}" ) )

		graphGadget = GafferUI.GraphGadget( script )
		gadget = graphGadget["__annotations"]
		self.assertEqual( gadget.annotationText( script["node"] ), "test : 0" )

	def testComputedText( self ) :

		script = Gaffer.ScriptNode()
		script["node"] = GafferTest.AddNode()
		script["errorNode"] = GafferTest.BadNode()
		Gaffer.MetadataAlgo.addAnnotation( script["node"], "user", Gaffer.MetadataAlgo.Annotation( "test : {sum}" ) )

		errorCondition = threading.Condition()
		def error( *unused ) :
			with errorCondition :
				errorCondition.notify()
		script["errorNode"].errorSignal().connect( error, scoped = False )

		with GafferTest.ParallelAlgoTest.UIThreadCallHandler() as callHandler :

			graphGadget = GafferUI.GraphGadget( script )
			gadget = graphGadget["__annotations"]

			# Value must be computed in background, so initially we expect a placeholder
			self.assertEqual( gadget.annotationText( script["node"] ), "test : ---" )

			# But if we wait for the background update we should get some updated text.
			callHandler.assertCalled()
			self.assertEqual( gadget.annotationText( script["node"] ), "test : 0" )

			# Same applies when the plug is dirtied. We expect a placeholder first.
			script["node"]["op1"].setValue( 1 )
			self.assertEqual( gadget.annotationText( script["node"] ), "test : ---" )

			# Then we get the real value when the computation is done.
			callHandler.assertCalled()
			self.assertEqual( gadget.annotationText( script["node"] ), "test : 1" )

			# And when the plug is dirtied by an upstream change we again expect
			# placeholder text at first.
			script["node"]["op1"].setInput( script["errorNode"]["out3"] )
			self.assertEqual( gadget.annotationText( script["node"] ), "test : ---" )

			# But this time we don't expect to get updated text, because the computation
			# will error.
			with errorCondition :
				errorCondition.wait()

			# Handle UI thread calls made by StandardNodeGadget to show errors,
			# and assert that there are no more calls.
			callHandler.assertCalled()
			callHandler.assertCalled()

			callHandler.assertDone()

		self.assertEqual( gadget.annotationText( script["node"] ), "test : ---" )

	def testComputedTextCancellation( self ) :

		script = Gaffer.ScriptNode()
		script["node"] = GafferTest.AddNode()
		script["node2"] = GafferTest.AddNode()

		AnnotationsGadgetTest.expressionStartedCondition = threading.Condition()
		AnnotationsGadgetTest.expressionContinueCondition = threading.Condition()

		script["expression"] = Gaffer.Expression()
		script["expression"].setExpression( inspect.cleandoc(
			"""
			# Let the test know the expression has started running.
			import GafferUITest
			with GafferUITest.AnnotationsGadgetTest.expressionStartedCondition :
				GafferUITest.AnnotationsGadgetTest.expressionStartedCondition.notify()

			# And loop checking for cancellation until the test
			# allows us to continue.
			while True :
				IECore.Canceller.check( context.canceller() )
				with GafferUITest.AnnotationsGadgetTest.expressionContinueCondition :
					if GafferUITest.AnnotationsGadgetTest.expressionContinueCondition.wait( timeout = 0.1 ) :
						break

			parent["node"]["op1"] = parent["node"]["op2"]
			"""
		) )


		Gaffer.MetadataAlgo.addAnnotation( script["node"], "user", Gaffer.MetadataAlgo.Annotation( "{sum}" ) )

		with GafferTest.ParallelAlgoTest.UIThreadCallHandler() as callHandler :

			graphGadget = GafferUI.GraphGadget( script )
			viewportGadget = GafferUI.ViewportGadget( graphGadget )
			gadget = graphGadget["__annotations"]

			# Value must be computed in background, so initially we expect a placeholder
			self.assertEqual( gadget.annotationText( script["node"] ), "---" )

			# Wait for compute to start, and make a graph edit to cancel it.
			with AnnotationsGadgetTest.expressionStartedCondition :
				AnnotationsGadgetTest.expressionStartedCondition.wait()

			script["node"]["op2"].setValue( 2 )

			# We expect a call on the UI thread to re-dirty the annotation.

			renderRequests = GafferTest.CapturingSlot( viewportGadget.renderRequestSignal() )
			callHandler.assertCalled()
			self.assertEqual( len( renderRequests ), 1 )
			self.assertEqual( gadget.annotationText( script["node"] ), "---" )

			# A new background task should have been launched to compute the
			# text again. If we let the expression run to completion then we
			# should get the final text.
			with AnnotationsGadgetTest.expressionStartedCondition :
				AnnotationsGadgetTest.expressionStartedCondition.wait()

			with GafferUITest.AnnotationsGadgetTest.expressionContinueCondition :
				GafferUITest.AnnotationsGadgetTest.expressionContinueCondition.notify()

			callHandler.assertCalled()
			self.assertEqual( gadget.annotationText( script["node"] ), "4" )

			# Try one more time. But this time do the cancellation by
			# modifying a completely unrelated plug.

			script["node"]["op2"].setValue( 3 )
			self.assertEqual( gadget.annotationText( script["node"] ), "---" )
			with AnnotationsGadgetTest.expressionStartedCondition :
				AnnotationsGadgetTest.expressionStartedCondition.wait()

			script["node2"]["op1"].setValue( 1 ) # Cancels

			renderRequests = GafferTest.CapturingSlot( viewportGadget.renderRequestSignal() )
			callHandler.assertCalled()
			self.assertEqual( len( renderRequests ), 1 )
			self.assertEqual( gadget.annotationText( script["node"] ), "---" )

			with AnnotationsGadgetTest.expressionStartedCondition :
				AnnotationsGadgetTest.expressionStartedCondition.wait()

			with GafferUITest.AnnotationsGadgetTest.expressionContinueCondition :
				GafferUITest.AnnotationsGadgetTest.expressionContinueCondition.notify()

			callHandler.assertCalled()
			self.assertEqual( gadget.annotationText( script["node"] ), "6" )

			callHandler.assertDone()

	def testContextSensitiveText( self ) :

		script = Gaffer.ScriptNode()
		script["node"] = GafferTest.FrameNode()
		Gaffer.MetadataAlgo.addAnnotation( script["node"], "user", Gaffer.MetadataAlgo.Annotation( "{output}" ) )

		with GafferTest.ParallelAlgoTest.UIThreadCallHandler() as callHandler :

			graphGadget = GafferUI.GraphGadget( script )
			gadget = graphGadget["__annotations"]

			# Value must be computed in background, so initially we expect a placeholder
			self.assertEqual( gadget.annotationText( script["node"] ), "---" )

			# But if we wait for the background update we should get some updated text.
			callHandler.assertCalled()
			self.assertEqual( gadget.annotationText( script["node"] ), "1" )

			# Same applies when the context is changed. We expect a placeholder first.
			script.context().setFrame( 10 )
			self.assertEqual( gadget.annotationText( script["node"] ), "---" )

			# Then we get the real value when the computation is done.
			callHandler.assertCalled()
			self.assertEqual( gadget.annotationText( script["node"] ), "10" )

			callHandler.assertDone()

	def testSubstitutedTextRenderRequests( self ) :

		script = Gaffer.ScriptNode()
		script["node"] = GafferTest.AddNode()

		graphGadget = GafferUI.GraphGadget( script )
		gadget = graphGadget["__annotations"]
		viewportGadget = GafferUI.ViewportGadget( graphGadget )
		renderRequests = GafferTest.CapturingSlot( viewportGadget.renderRequestSignal() )

		Gaffer.MetadataAlgo.addAnnotation( script["node"], "user", Gaffer.MetadataAlgo.Annotation( "test" ) )
		self.assertEqual( len( renderRequests ), 1 )
		self.assertEqual( gadget.annotationText( script["node"] ), "test" )

		script["node"]["op1"].setValue( 1 )
		self.assertEqual( len( renderRequests ), 1 ) # No new request, because no substitutions

		Gaffer.MetadataAlgo.addAnnotation( script["node"], "user", Gaffer.MetadataAlgo.Annotation( "test : {op1}" ) )
		self.assertEqual( len( renderRequests ), 2 ) # New request, because annotations changed
		self.assertEqual( gadget.annotationText( script["node"] ), "test : 1" )

		script["node"]["op1"].setValue( 2 )
		self.assertEqual( len( renderRequests ), 3 ) # New request, because substitution changed

		script["node"]["op2"].setValue( 2 )
		self.assertEqual( len( renderRequests ), 3 ) # No new request, because plug doesn't affect substitution

		script.context().setFrame( 10 )
		self.assertEqual( len( renderRequests ), 4 ) # One new request, from unrelated code in GraphGadget

		Gaffer.MetadataAlgo.addAnnotation( script["node"], "user", Gaffer.MetadataAlgo.Annotation( "test : {sum}" ) )
		self.assertEqual( len( renderRequests ), 5 ) # New request, because annotation changed
		self.assertEqual( gadget.annotationText( script["node"] ), "test : ---" )

		script.context().setFrame( 11 )
		# 2 new requests, one because substitution depends on compute, and one from unrelated code in GraphGadget.
		self.assertEqual( len( renderRequests ), 7 )

	def testDestroyGadgetWhileBackgroundThreadRuns( self ) :

		script = Gaffer.ScriptNode()
		script["node"] = GafferTest.AddNode()

		Gaffer.MetadataAlgo.addAnnotation( script["node"], "user", Gaffer.MetadataAlgo.Annotation( "{sum}" ) )

		with GafferTest.ParallelAlgoTest.UIThreadCallHandler() as callHandler :

			graphGadget = GafferUI.GraphGadget( script )
			gadget = graphGadget["__annotations"]

			# Value must be computed in background, so initially we expect a placeholder.
			self.assertEqual( gadget.annotationText( script["node"], "user" ), "---" )

			# Wait for the UI thread call that will be scheduled to update the gadget.
			call = callHandler.receive()
			# But then delete our references to the gadget _before_ we execute
			# the call. This simulates a user removing a GraphEditor while the
			# AnnotationsGadget is still updating. If we don't handle lifetimes
			# well, then this could crash.
			del graphGadget, gadget
			call()

			callHandler.assertDone()

	def testRemoveNodeWhileBackgroundThreadRuns( self ) :

		script = Gaffer.ScriptNode()
		script["node"] = GafferTest.AddNode()

		Gaffer.MetadataAlgo.addAnnotation( script["node"], "test", Gaffer.MetadataAlgo.Annotation( "{sum}" ) )

		with GafferTest.ParallelAlgoTest.UIThreadCallHandler() as callHandler :

			graphGadget = GafferUI.GraphGadget( script )
			gadget = graphGadget["__annotations"]

			# Value must be computed in background, so initially we expect a placeholder
			self.assertEqual( gadget.annotationText( script["node"], "test" ), "---" )

			# Wait for the UI thread call that will be scheduled to update the gadget.
			call = callHandler.receive()
			# But then delete the node _before_ we execute the call. This
			# simulates a user deleting a node while the AnnotationsGadget is
			# still updating. If we don't handle lifetimes well, then this could
			# crash.
			del script["node"]
			call()

			callHandler.assertDone()

	def testRemoveAnnotationWhileBackgroundThreadRuns( self ) :

		script = Gaffer.ScriptNode()
		script["node"] = GafferTest.AddNode()

		numAnnotations = 100
		for i in range( 0, numAnnotations ) :
			Gaffer.MetadataAlgo.addAnnotation( script["node"], f"test{i}", Gaffer.MetadataAlgo.Annotation( "{sum}" ) )

		with GafferTest.ParallelAlgoTest.UIThreadCallHandler() as callHandler :

			graphGadget = GafferUI.GraphGadget( script )
			gadget = graphGadget["__annotations"]

			# Value must be computed in background, so initially we expect a placeholder
			self.assertEqual( gadget.annotationText( script["node"], "test0" ), "---" )

			# Remove annotations while the background task runs.
			for i in range( 0, numAnnotations ) :
				Gaffer.MetadataAlgo.removeAnnotation( script["node"], f"test{i}" )
			self.assertEqual( gadget.annotationText( script["node"], "test0" ), "" )

			# And wait for the task to complete.
			callHandler.assertCalled()

if __name__ == "__main__":
	unittest.main()
