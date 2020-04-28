##########################################################################
#
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
#  Copyright (c) 2012, Image Engine Design Inc. All rights reserved.
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
import threading
import time
import functools

import IECore

import Gaffer
import GafferUI
import GafferUITest

from Qt import QtCore
from Qt import QtWidgets

class EventLoopTest( GafferUITest.TestCase ) :

	def testIdleCallbacks( self ) :

		self.__idleCalls = 0

		def idle() :

			self.__idleCalls += 1
			return self.__idleCalls < 2

		def stop() :

			if self.__idleCalls==2 :
				GafferUI.EventLoop.mainEventLoop().stop()
				return False

			return True

		GafferUI.EventLoop.addIdleCallback( idle )
		GafferUI.EventLoop.addIdleCallback( stop )
		GafferUI.EventLoop.mainEventLoop().start()

		self.assertEqual( self.__idleCalls, 2 )

	def testWaitForIdle( self ) :

		self.__idleCalls = 0

		def idle( total ) :

			self.__idleCalls += 1
			return self.__idleCalls < total

		GafferUI.EventLoop.addIdleCallback( functools.partial( idle, 1000 ) )
		GafferUI.EventLoop.waitForIdle()
		self.assertEqual( self.__idleCalls, 1000 )

		GafferUI.EventLoop.addIdleCallback( functools.partial( idle, 1005 ) )
		GafferUI.EventLoop.waitForIdle( 5 )
		self.assertEqual( self.__idleCalls, 1005 )

	def testExecuteOnUITheadAndWaitForResult( self ) :

		def f() :

			GafferUI.EventLoop.mainEventLoop().stop()
			self.__uiThreadFunctionCalled = True
			self.__uiThreadCalledOnCorrectThread = QtCore.QThread.currentThread() == QtWidgets.QApplication.instance().thread()
			return 101

		def t() :

			self.__uiThreadResult = GafferUI.EventLoop.executeOnUIThread( f, waitForResult=True )

		thread = threading.Thread( target = t )

		GafferUI.EventLoop.addIdleCallback( thread.start )
		GafferUI.EventLoop.mainEventLoop().start()

		thread.join()
		self.assertEqual( self.__uiThreadFunctionCalled, True )
		self.assertEqual( self.__uiThreadCalledOnCorrectThread, True )
		self.assertEqual( self.__uiThreadResult, 101 )

	def testExecuteOnUITheadAndDontWaitForResult( self ) :

		def f() :

			time.sleep( 2 )
			GafferUI.EventLoop.mainEventLoop().stop()
			self.__uiThreadFunctionCalled = True
			self.__uiThreadCalledOnCorrectThread = QtCore.QThread.currentThread() == QtWidgets.QApplication.instance().thread()
			return 101

		def t() :

			st = time.clock()
			self.__uiThreadResult = GafferUI.EventLoop.executeOnUIThread( f, waitForResult=False )
			self.__executeOnUIThreadDuration = time.clock() - st

		thread = threading.Thread( target = t )

		GafferUI.EventLoop.addIdleCallback( thread.start )
		GafferUI.EventLoop.mainEventLoop().start()

		thread.join()
		self.assertEqual( self.__uiThreadFunctionCalled, True )
		self.assertEqual( self.__uiThreadCalledOnCorrectThread, True )
		self.assertEqual( self.__uiThreadResult, None )
		# we shouldn't be waiting for the result of ui thread, so the return should be quicker
		# than the actual function called
		self.assertLess( self.__executeOnUIThreadDuration, 2 )

	def testExceptionsInIdleCallbacks( self ) :

		self.__idle1Calls = 0
		self.__idle2Calls = 0

		def idle1() :

			self.__idle1Calls += 1
			raise RuntimeError( "I am a very naughty boy" )

		def idle2() :

			self.__idle2Calls += 1
			return True

		def stop() :

			if self.__idle2Calls==4 :
				GafferUI.EventLoop.mainEventLoop().stop()
				return False

			return True

		GafferUI.EventLoop.addIdleCallback( idle1 )
		GafferUI.EventLoop.addIdleCallback( idle2 )
		GafferUI.EventLoop.addIdleCallback( stop )

		mh = IECore.CapturingMessageHandler()
		with mh :
			GafferUI.EventLoop.mainEventLoop().start()

		self.assertEqual( self.__idle1Calls, 1 )
		self.assertGreaterEqual( self.__idle2Calls, 4 )
		self.assertEqual( len( mh.messages ), 1 )
		self.assertEqual( mh.messages[0].level, IECore.Msg.Level.Error )
		self.assertIn( "I am a very naughty boy", mh.messages[0].message )

	def testExecuteOnUITheadFromUIThread( self ) :

		# if we're on the ui thread already when we call executeOnUIThread(),
		# then our function should be called immediately.

		self.__executed = False
		def f() :
			self.__executed = True
			return 10

		r = GafferUI.EventLoop.executeOnUIThread( f )

		self.assertEqual( r, 10 )
		self.assertEqual( self.__executed, True )

	def testAddIdleCallbackFromIdleCallback( self ) :

		self.__runOnceCalls = 0
		self.__addRunOnceCalls = 0

		def runOnce() :

			self.__runOnceCalls += 1
			return False # so we're removed immediately

		def addRunOnce() :

			self.__addRunOnceCalls += 1

			if self.__addRunOnceCalls==2 :
				GafferUI.EventLoop.mainEventLoop().stop()
				return False

			GafferUI.EventLoop.mainEventLoop().addIdleCallback( runOnce )

			return True

		GafferUI.EventLoop.addIdleCallback( runOnce )
		GafferUI.EventLoop.addIdleCallback( addRunOnce )
		GafferUI.EventLoop.mainEventLoop().start()

		self.assertEqual( self.__runOnceCalls, 2 )
		self.assertEqual( self.__addRunOnceCalls, 2 )

	def setUp( self ) :

		GafferUITest.TestCase.setUp( self )

		self.__uiThreadFunctionCalled = False
		self.__uiThreadCalledOnCorrectThread = False
		self.__uiThreadResult = None
		self.__executeOnUIThreadDuration = 10000

if __name__ == "__main__":
	unittest.main()
