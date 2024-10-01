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

import threading
import unittest
import timeit
import queue
import _thread

import IECore

import Gaffer
import GafferTest

class ParallelAlgoTest( GafferTest.TestCase ) :

	# Context manager used to test code which uses `ParallelAlgo::callOnUIThread()`.
	# This emulates the call handler that the UI would usually install.
	class UIThreadCallHandler( object ) :

		def __enter__( self ) :

			self.__assertDone = False
			self.__queue = queue.Queue()
			Gaffer.ParallelAlgo.pushUIThreadCallHandler( self.__callOnUIThread )
			return self

		def __exit__( self, type, value, traceBack ) :

			Gaffer.ParallelAlgo.popUIThreadCallHandler()
			while True :
				try :
					f = self.__queue.get( block = False )
				except queue.Empty:
					return
				if self.__assertDone :
					raise AssertionError( "UIThread call queue not empty" )
				f()

		def __callOnUIThread( self, f ) :

			self.__queue.put( f )

		# Waits for a single use of `callOnUIThread()`, raising
		# a test failure if none arises before `timeout` seconds.
		def assertCalled( self, timeout = 30.0 ) :

			try :
				f = self.__queue.get( block = True, timeout = timeout )
			except queue.Empty :
				raise AssertionError( "UIThread call not made within {} seconds".format( timeout ) )

			f()

		# Asserts that no further uses of `callOnUIThread()` will
		# be made with this handler. This is checked on context exit.
		def assertDone( self ) :

			self.__assertDone = True

		# Waits for `time` seconds, processing any calls to
		# `ParallelAlgo::callOnUIThread()` made during that time.
		def waitFor( self, time ) :

			startTime = timeit.default_timer()
			elapsed = 0.0

			while elapsed < time:
				try:
					f = self.__queue.get( block = True, timeout = time - elapsed )
				except queue.Empty:
					return

				f()
				elapsed = timeit.default_timer() - startTime

	def testCallOnUIThread( self ) :

		s = Gaffer.ScriptNode()

		def uiThreadFunction() :

			s.setName( "test" )
			s.uiThreadId = _thread.get_ident()

		with self.UIThreadCallHandler() as h :

			self.assertTrue( Gaffer.ParallelAlgo.canCallOnUIThread() )

			t = threading.Thread(
				target = lambda : Gaffer.ParallelAlgo.callOnUIThread( uiThreadFunction )
			)
			t.start()
			h.assertCalled()
			t.join()
			h.assertDone()

		self.assertEqual( s.getName(), "test" )
		self.assertEqual( s.uiThreadId, _thread.get_ident() )

	def testNestedUIThreadCallHandler( self ) :

		# This is testing our `UIThreadCallHandler` utility
		# class more than it's testing `ParallelAlgo`.

		s = Gaffer.ScriptNode()

		def uiThreadFunction1() :

			s.setName( "test" )
			s.uiThreadId1 = _thread.get_ident()

		def uiThreadFunction2() :

			s["fileName"].setValue( "test" )
			s.uiThreadId2 = _thread.get_ident()

		with self.UIThreadCallHandler() as h1 :

			self.assertTrue( Gaffer.ParallelAlgo.canCallOnUIThread() )

			t1 = threading.Thread(
				target = lambda : Gaffer.ParallelAlgo.callOnUIThread( uiThreadFunction1 )
			)
			t1.start()
			h1.assertCalled()
			h1.assertDone()

			with self.UIThreadCallHandler() as h2 :

				self.assertTrue( Gaffer.ParallelAlgo.canCallOnUIThread() )

				t2 = threading.Thread(
					target = lambda : Gaffer.ParallelAlgo.callOnUIThread( uiThreadFunction2 )
				)
				t2.start()
				h2.assertCalled()
				h2.assertDone()

		self.assertEqual( s.getName(), "test" )
		self.assertEqual( s.uiThreadId1, _thread.get_ident() )
		self.assertEqual( s["fileName"].getValue(), "test" )
		self.assertEqual( s.uiThreadId2, _thread.get_ident() )

		t1.join()
		t2.join()

	def testCallOnBackgroundThread( self ) :

		script = Gaffer.ScriptNode()
		script["n"] = GafferTest.AddNode()

		foregroundContext = Gaffer.Context( script.context() )
		foregroundContext["a"] = "a"

		def f() :

			backgroundContext = Gaffer.Context.current()
			self.assertFalse( backgroundContext.isSame( foregroundContext ) )
			self.assertEqual( backgroundContext, foregroundContext )

			with self.assertRaises( IECore.Cancelled ) :
				while True :
					script["n"]["sum"].getValue()
					# We might expect that `script["n"]["sum"].getValue()`
					# would be guaranteed to throw after cancellation has been
					# requested. But that is not the case if both the hash and the
					# value are already cached, because cancellation is only checked
					# for automatically when a Process is constructed. So we take
					# a belt and braces approach and perform an explicit check here.
					#
					# The alternative would be to move the cancellation check outside
					# of the Process class, so it is performed before the cache lookup.
					# This may be the better approach, but we would need to benchmark
					# it to ensure that performance was not adversely affected. To our
					# knowledge, this "cache hits avoid cancellation" problem has not
					# been responsible for unresponsive cancellation in the wild, because
					# background tasks are typically triggered by `plugDirtiedSignal()`,
					# and the hash cache is cleared when a plug is dirtied.
					IECore.Canceller.check( backgroundContext.canceller() )

		# Explicit cancellation

		with foregroundContext :
			backgroundTask = Gaffer.ParallelAlgo.callOnBackgroundThread( script["n"]["sum"], f )

		backgroundTask.cancel()

		# Implicit cancellation through graph edit

		with foregroundContext :
			backgroundTask = Gaffer.ParallelAlgo.callOnBackgroundThread( script["n"]["sum"], f )

		script["n"]["op1"].setValue( 10 )

		# Cancellation through deletion

		with foregroundContext :
			backgroundTask = Gaffer.ParallelAlgo.callOnBackgroundThread( script["n"]["sum"], f )

		del backgroundTask

	def testBackgroundThreadMonitoring( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.MultiplyNode()
		s["n"]["op2"].setValue( 1 )
		s["e"] = Gaffer.Expression()
		s["e"].setExpression( """parent["n"]["op1"] = context["op1"]""" )

		def backgroundFunction() :

			with Gaffer.Context() as c :
				for i in range( 0, 10000 ) :
					c["op1"] = i
					self.assertEqual( s["n"]["product"].getValue(), i )

		with Gaffer.PerformanceMonitor() as m :
			t = Gaffer.ParallelAlgo.callOnBackgroundThread(
				s["n"]["product"], backgroundFunction
			)
		t.wait()

		# The monitor was active when we launched the background
		# process, so we expect it to have been transferred to the
		# background thread and remained active there for the duration.
		self.assertEqual( m.plugStatistics( s["n"]["product"] ).computeCount, 10000 )

if __name__ == "__main__":
	unittest.main()
