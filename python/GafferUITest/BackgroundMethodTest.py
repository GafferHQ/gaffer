##########################################################################
#
#  Copyright (c) 2018, Image Engine Design Inc. All rights reserved.
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

import time
import six

import IECore

import Gaffer
import GafferTest
import GafferUI
import GafferUITest

class BackgroundMethodTest( GafferUITest.TestCase ) :

	class TestWidget( GafferUI.NumericWidget ) :

		def __init__( self, **kw ) :

			GafferUI.NumericWidget.__init__( self, 0, **kw )

			self.__script = Gaffer.ScriptNode()
			self.__script["n"] = GafferTest.AddNode()

			self.numPreCalls = 0
			self.numBackgroundCalls = 0
			self.numPostCalls = 0

		def node( self ) :

			return self.__script["n"]

		@GafferUI.BackgroundMethod()
		def updateInBackground( self, arg ) :

			self.numBackgroundCalls += 1
			self.backgroundCallArg = arg
			self.backgroundCallThreadId = six.moves._thread.get_ident()

			canceller = Gaffer.Context.current().canceller()

			# Give the main thread time to cancel, so we
			# can test `cancelWhenHidden`.
			for i in range( 0, 100 ) :
				IECore.Canceller.check( canceller )
				time.sleep( 0.01 )

			# Simulate an error if we've been asked to.
			if getattr( self, "throw", False ) :
				raise Exception( "Oops!" )

			return self.__script["n"]["sum"].getValue()

		@updateInBackground.preCall
		def __updateInBackgroundPreCall( self ) :

			self.numPreCalls += 1
			self.preCallThreadId = six.moves._thread.get_ident()

			self.setEnabled( False )

		@updateInBackground.postCall
		def __updateInBackgroundPostCall( self, value ) :

			self.postCallArg = value
			self.numPostCalls += 1
			self.postCallThreadId = six.moves._thread.get_ident()

			self.setValue( value if isinstance( value, int ) else -1 )
			self.setEnabled( True )

		@updateInBackground.plug
		def __setTextPlug( self ) :

			return self.__script["n"]["sum"]

	class WaitingSlot( GafferTest.CapturingSlot ) :

		def __init__( self, signal ) :

			GafferTest.CapturingSlot.__init__( self, signal )

		def wait( self ) :

			while len( self ) == 0 :
				GafferUI.EventLoop.waitForIdle()

	def test( self ) :

		with GafferUI.Window() as window :
			w = self.TestWidget()

		window.setVisible( True )

		self.assertFalse( w.updateInBackground.running( w ) )
		self.assertEqual( w.numPreCalls, 0 )
		self.assertEqual( w.numBackgroundCalls, 0 )
		self.assertEqual( w.numPostCalls, 0 )

		w.node()["op1"].setValue( 1 )

		ws = self.WaitingSlot( w.valueChangedSignal() )

		w.updateInBackground( 100 )
		self.assertEqual( w.getEnabled(), False )
		self.assertEqual( w.getValue(), 0 )
		self.assertTrue( w.updateInBackground.running( w ) )

		ws.wait()

		self.assertFalse( w.updateInBackground.running( w ) )

		self.assertEqual( w.getValue(), 1 )

		self.assertEqual( w.numPreCalls, 1 )
		self.assertEqual( w.numBackgroundCalls, 1 )
		self.assertEqual( w.numPostCalls, 1 )

		self.assertEqual( w.postCallArg, 1 )
		self.assertEqual( w.backgroundCallArg, 100 )

		self.assertNotEqual( w.backgroundCallThreadId, six.moves._thread.get_ident() )
		self.assertEqual( w.preCallThreadId, six.moves._thread.get_ident() )
		self.assertEqual( w.postCallThreadId, six.moves._thread.get_ident() )

	def testCancelWhenHidden( self ) :

		with GafferUI.Window() as window :
			w = self.TestWidget()

		window.setVisible( True )

		ws = self.WaitingSlot( w.valueChangedSignal() )
		w.updateInBackground( 1 )
		window.setVisible( False )

		ws.wait()
		self.assertEqual( w.getValue(), -1 )

		self.assertEqual( w.numPreCalls, 1 )
		# Background function may have been cancelled before
		# it even started, in which case it will not even have
		# been called.
		self.assertIn( w.numBackgroundCalls, { 0, 1 } )
		# But no matter what, we always expect a matching postCall
		# for the original preCall.
		self.assertEqual( w.numPostCalls, 1 )

		self.assertIsInstance( w.postCallArg, IECore.Cancelled )

	def testExceptions( self ) :

		with GafferUI.Window() as window :
			w = self.TestWidget()
			w.throw = True

		window.setVisible( True )

		ws = self.WaitingSlot( w.valueChangedSignal() )
		w.updateInBackground( 1000 )

		ws.wait()
		self.assertEqual( w.getValue(), -1 )

		self.assertEqual( w.numPreCalls, 1 )
		self.assertEqual( w.numBackgroundCalls, 1 )
		self.assertEqual( w.numPostCalls, 1 )

		self.assertIsInstance( w.postCallArg, Exception )

	def testSecondCallSupercedesFirst( self ) :

		with GafferUI.Window() as window :
			w = self.TestWidget()

		window.setVisible( True )

		w.node()["op1"].setValue( 2 )

		ws = self.WaitingSlot( w.valueChangedSignal() )

		w.updateInBackground( 10 )
		w.updateInBackground( 11 )

		ws.wait()
		self.assertEqual( w.getValue(), 2 )

		# Second call re-uses the first precall
		self.assertEqual( w.numPreCalls, 1 )
		# The first call may have got started before
		# it was cancelled by the second, or it may
		# not.
		self.assertIn( w.numBackgroundCalls, { 1, 2 } )
		# But either way the first call doesn't make it to
		# the post-call stage.
		self.assertEqual( w.numPostCalls, 1 )
		self.assertEqual( w.backgroundCallArg, 11 )

if __name__ == "__main__":
	unittest.main()
