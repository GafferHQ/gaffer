##########################################################################
#
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
#  Copyright (c) 2011-2015, Image Engine Design Inc. All rights reserved.
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
import weakref
import threading
import traceback
import functools
import queue

import IECore

import Gaffer
import GafferUI

from Qt import QtCore
from Qt import QtWidgets

## This class provides the event loops used to run GafferUI based applications.
class EventLoop( object ) :

	__RunStyle = IECore.Enum.create( "Normal", "PumpThread", "AlreadyRunning", "Houdini" )

	## Creates a new EventLoop. Note that if you are creating the primary
	# EventLoop for an application then you should use mainEventLoop() instead.
	def __init__( self, __qtEventLoop=None ) :

		if __qtEventLoop is None :
			if self.__mainEventLoop is None or self.__mainEventLoop.__startCount==0 :
				raise Exception( "Main event loop is not running - perhaps you should use EventLoop.mainEventLoop()?" )
			self.__qtEventLoop = QtCore.QEventLoop()
		else :
			self.__qtEventLoop = __qtEventLoop

		self.__runStyle = self.__RunStyle.Normal
		if isinstance( self.__qtEventLoop, QtWidgets.QApplication ) :
			try :
				import maya.OpenMaya
				if maya.OpenMaya.MGlobal.apiVersion() < 201100 :
					self.__runStyle = self.__RunStyle.PumpThread
				else :
					self.__runStyle = self.__RunStyle.AlreadyRunning
			except ImportError :
				pass

			try :
				import hou
				if hou.applicationVersion()[0] < 14 :
					self.__runStyle = self.__RunStyle.Houdini
				else :
					self.__runStyle = self.__RunStyle.AlreadyRunning
			except ImportError :
				pass

			try :
				import nuke
				self.__runStyle = self.__RunStyle.AlreadyRunning
			except ImportError :
				pass

		self.__startCount = 0
		self.__pumpThread = None
		self.__houdiniCallback = None

	## Starts the event loop, passing control to the UI code. This function returns
	# when the corresponding stop() method is called. See documentation for
	# mainEventLoop() for exceptions to this rule.
	def start( self ) :

		self.__startCount += 1

		if self.__runStyle == self.__RunStyle.Normal :
			assert( self.__startCount == 1 )
			self.__qtEventLoop.exec_()
		elif self.__runStyle == self.__RunStyle.PumpThread :
			if self.__pumpThread is None :
				self.__pumpThread = threading.Thread( target = self.__pumpThreadFn )
				self.__pumpThread.start()
		elif self.__runStyle == self.__RunStyle.Houdini :
			if self.__houdiniCallback is None :
				import hou
				hou.ui.addEventLoopCallback( functools.partial( self.__pump, 5 ) )
				self.__houdiniCallback = hou.ui.eventLoopCallbacks()[-1]
		else :
			# RunStyle.AlreadyRunning
			# host application is using qt natively, no need to do anything.
			pass

	## Stops the event loop last started using start().
	def stop( self ) :

		assert( self.__startCount > 0 )

		if self.__runStyle == self.__RunStyle.Normal :
			assert( self.__startCount == 1 )
			self.__qtEventLoop.exit()
		elif self.__runStyle == self.__RunStyle.PumpThread :
			## \todo Should we try to stop the pump thread
			# when self.__startCount hits 0? Right not we're
			# just keeping it running on the assumption we'll
			# need it again soon.
			pass
		elif self.__runStyle == self.__RunStyle.Houdini :
			if self.__startCount == 1 and self.__houdiniCallback :
				import hou
				hou.ui.removeEventLoopCallback( self.__houdiniCallback )
				self.__houdiniCallback = None
		else :
			# RunStyle.AlreadyRunning
			pass

		self.__startCount -= 1

	## Returns true if this event loop is currently running.
	def running( self ) :

		return self.__startCount > 0

	# if we're running embedded in an application which already uses qt (like maya 2011 or later)
	# then there'll already be an application, which we'll share. if not we'll make our own.
	if QtWidgets.QApplication.instance() :
		__qtApplication = QtWidgets.QApplication.instance()
	else :
		# Set the style explicitly so we don't inherit one from the desktop
		# environment, which could mess with our own style (on GNOME for instance,
		# our icons can come out the wrong size).
		style = QtWidgets.QApplication.setStyle( "Fusion" )
		# Stop icons/fonts being tiny on high-dpi monitors. Must be set before
		# the application is created.
		QtWidgets.QApplication.setAttribute( QtCore.Qt.AA_EnableHighDpiScaling )
		assert( style is not None )
		__qtApplication = QtWidgets.QApplication( [ "gaffer" ] )
		# Fixes laggy interaction with tablets, equivalent to the old
		# QT_COMPRESS_TABLET_EVENTS env var supported in Maya Qt builds.
		__qtApplication.setAttribute( QtCore.Qt.AA_CompressTabletEvents, True )

	__mainEventLoop = None
	## Returns the main event loop for the application. This should always
	# be started before running any other nested event loops. In the standalone
	# Gaffer applications, the main event loop acts like any other, but when
	# GafferUI is embedded in another application (like Maya) it behaves slightly
	# differently. In this case, the start() method returns immediately so that
	# the GafferUI event loop may be interleaved with the event loop of the host
	# application. Additionally, the start() method may also be called multiple
	# times to allow several GafferUI-based applications to run in the same host.
	# The main event loop will therefore only cease running when the number of
	# calls to stop() matches the number of calls to start().
	@classmethod
	def mainEventLoop( cls ) :

		if cls.__mainEventLoop is None :
			cls.__mainEventLoop = cls( cls.__qtApplication )

		return cls.__mainEventLoop

	__idleCallbacks = []
	__idleTimer = None
	## Adds a function to be called when the event loop is idle (has no events
	# remaining to be processed). If callback returns False then it will be removed
	# automatically after running, if it returns True it will be called again until
	# it returns False, or until removeIdleCallback() is called.
	## \todo This should probably be replaced with an idleSignal() like the one we
	# have in GafferUI.Gadget.
	@classmethod
	def addIdleCallback( cls, callback ) :

		assert( callback not in cls.__idleCallbacks )
		cls.__idleCallbacks.append( callback )
		cls.__ensureIdleTimer()

	## Removes an idle callback previously created with addIdleCallback().
	@classmethod
	def removeIdleCallback( cls, callback ) :

		cls.__idleCallbacks.remove( callback )

	## Convenience method to introduce a delay on the mainEventLoop().
	@classmethod
	def waitForIdle( cls, count = 1000 ) :

		cls.__idleCount = 0

		def f() :

			cls.__idleCount += 1

			if cls.__idleCount >= count :
				EventLoop.mainEventLoop().stop()
				return False

			return True

		EventLoop.addIdleCallback( f )
		EventLoop.mainEventLoop().start()

	## Widgets may only be manipulated on the thread where mainEventLoop() is running. It
	# is common to want to perform some background processing on a secondary thread, and
	# to update the UI during processing or upon completion. This function can be used from
	# such a secondary thread to queue a callable to be called on the main thread. If called
	# from the main thread, the callable is called immediately.
	@classmethod
	def executeOnUIThread( cls, callable, waitForResult=False ) :

		return _uiThreadExecutor.execute( callable, waitForResult )

	## Context manager that blocks callables queued with `executeOnUIThread()`.
	# The calls will be deferred until after the block exits. This is useful
	# to defer graph edits that would cause unwanted cancellation of a
	# BackgroundTask.
	## \todo Blocking all UI thread execution is overkill. We could add a
	# `subject` argument to `ParallelAlgo::callOnUIThread()`, mirroring the
	# existing argument to `ParallelAlgo::callOnBackgroundThread()`. Then
	# we could limit the blocking to calls with the relevant subject.
	class BlockedUIThreadExecution( object ) :

		def __enter__( self ) :

			_uiThreadExecutor.blockExecution()

		def __exit__( self, type, value, traceBack ) :

			_uiThreadExecutor.unblockExecution()

	@classmethod
	def __ensureIdleTimer( cls ) :

		assert( QtCore.QThread.currentThread() == EventLoop.__qtApplication.thread() )

		if cls.__idleTimer is None :
			cls.__idleTimer = QtCore.QTimer( cls.__qtApplication )
			cls.__idleTimer.timeout.connect( cls.__qtIdleCallback )

		if not cls.__idleTimer.isActive() :
			cls.__idleTimer.start()

	# This is a staticmethod rather than a classmethod because PySide 1.0.5
	# doesn't support classmethods as slots.
	@staticmethod
	def __qtIdleCallback() :

		assert( QtCore.QThread.currentThread() == EventLoop.__qtApplication.thread() )

		GafferUI.Gadget.idleSignal()()

		for c in EventLoop.__idleCallbacks[:] : # slice takes copy, so we can remove during iteration
			try :
				if not c() :
					EventLoop.__idleCallbacks.remove( c )
			except Exception as e :
				# if the callback throws then we remove it anyway, because
				# we don't want to keep invoking the same error over and over.
				EventLoop.__idleCallbacks.remove( c )
				# report the error
				IECore.msg( IECore.Msg.Level.Error, "EventLoop.__qtIdleCallback", "".join( traceback.format_exc() ) )

		if len( EventLoop.__idleCallbacks )==0 and GafferUI.Gadget.idleSignal().empty() :
			EventLoop.__idleTimer.stop()

	@classmethod
	def _gadgetIdleSignalAccessed( cls ) :

		# It would be an error to access the idle signal from anything but the main
		# thread, because it would imply multiple threads fighting over the same signal.
		assert( QtCore.QThread.currentThread() == EventLoop.__qtApplication.thread() )

		cls.__ensureIdleTimer()

	def __pumpThreadFn( self ) :

		import maya.utils

		while 1 :
			time.sleep( 0.01 )
			maya.utils.executeDeferred( self.__pump )

	def __pump( self, thrusts=1 ) :

		for thrust in range( 0, thrusts ) :
			self.__qtEventLoop.processEvents()

GafferUI.Gadget._idleSignalAccessedSignal().connect( EventLoop._gadgetIdleSignalAccessed, scoped = False )

# Internal implementation for `EventLoop.executeOnUIThread()`. There are
# multiple ways of achieving this in Qt, but they all boil down to scheduling an
# event on the main loop. We have tried the following :
#
# - Creating a new QObject to wrap the callable, moving it to the main thread,
#   and then using `postEvent()` to trigger a call to `customEvent()`, which
#   executes the callable. This triggered GIL/refcount bugs in PySide which meant
#   that the QObject was occasionally deleted prematurely.
# - Having a single QObject living on the main thread, with a signal which we
#   emitted from the background thread to schedule execution. This was more reliable,
#   but still triggered occasional PySide crashes.
# - Having a single QObject living on the main thread, and using `QMetaObject.invokeMethod()`
#   to queue a call to one of its methods. This is the approach we currently use.
class _UIThreadExecutor( QtCore.QObject ) :

	def __init__( self ) :

		QtCore.QObject.__init__( self )

		# In an ideal world, we'd pass the callables via arguments to
		# `__executeInternal`. But I haven't figured out how to do that via
		# `invokeMethod()` and doing the equivalent via signals crashes PySide.
		# So instead we pass the callables via this queue and just use
		# `invokeMethod()` to schedule their removal on the UI thread.
		self.__queue = queue.Queue()
		self.__blockedCallables = None

	def execute( self, callable, waitForResult ) :

		if QtCore.QThread.currentThread() == QtWidgets.QApplication.instance().thread() :
			# Already on the UI thread - just do it.
			return callable()

		resultCondition = threading.Condition() if waitForResult else None
		if resultCondition is not None :
			resultCondition.acquire()

		self.__queue.put( ( callable, resultCondition ) )
		QtCore.QMetaObject.invokeMethod( self, "__executeInternal", QtCore.Qt.ConnectionType.QueuedConnection )

		if resultCondition is not None :
			resultCondition.wait()
			resultCondition.release()
			return resultCondition.resultValue

	def blockExecution( self ) :

		assert( QtCore.QThread.currentThread() == QtWidgets.QApplication.instance().thread() )

		# Set up a container to buffer into
		assert( self.__blockedCallables is None )
		self.__blockedCallables = []

	def unblockExecution( self ) :

		assert( QtCore.QThread.currentThread() == QtWidgets.QApplication.instance().thread() )

		# Schedule each of the buffered calls again, and then clear the buffer.
		# We don't just execute them immediately because it would be surprising
		# to the user of `BlockedUIThreadExecution` to have arbitrary code be
		# executed in the middle of their function.
		assert( isinstance( self.__blockedCallables, list ) )
		for callable, resultCondition in self.__blockedCallables :
			self.__queue.put( ( callable, resultCondition ) )
			QtCore.QMetaObject.invokeMethod( self, "__executeInternal", QtCore.Qt.ConnectionType.QueuedConnection )

		self.__blockedCallables = None

	@QtCore.Slot()
	def __executeInternal( self ) :

		assert( QtCore.QThread.currentThread() == QtWidgets.QApplication.instance().thread() )
		callable, resultCondition = self.__queue.get()
		if self.__blockedCallables is not None :
			self.__blockedCallables.append( ( callable, resultCondition ) )
		else :
			result = callable()
			if resultCondition is not None :
				resultCondition.acquire()
				resultCondition.resultValue = result
				resultCondition.notify()
				resultCondition.release()

_uiThreadExecutor = _UIThreadExecutor()

# Service the requests made to `ParallelAlgo::callOnUIThread()`.
Gaffer.ParallelAlgo.pushUIThreadCallHandler( EventLoop.executeOnUIThread )
