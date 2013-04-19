##########################################################################
#  
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
#  Copyright (c) 2011-2012, Image Engine Design Inc. All rights reserved.
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

import IECore

import GafferUI

QtCore = GafferUI._qtImport( "QtCore" )
QtGui = GafferUI._qtImport( "QtGui" )

## This class provides the event loops used to run GafferUI based applications.
class EventLoop() :
	
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
		if isinstance( self.__qtEventLoop, QtGui.QApplication ) :
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
				self.__runStyle = self.__RunStyle.Houdini
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
				hou.ui.addEventLoopCallback( IECore.curry( self.__pump, 5 ) )
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
	if QtGui.QApplication.instance() :
		__qtApplication = QtGui.QApplication.instance()
	else :
		# set the style explicitly so we don't inherit one from the desktop
		# environment, which could mess with our own style (on gnome for instance,
		# our icons can come out the wrong size).
		QtGui.QApplication.setStyle( "plastique" )
	  	__qtApplication = QtGui.QApplication( [] )
		
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
	@classmethod
	def addIdleCallback( cls, callback ) :
		
		assert( callback not in cls.__idleCallbacks )
		cls.__idleCallbacks.append( callback )
		
		if cls.__idleTimer is None :
			cls.__idleTimer = QtCore.QTimer( cls.__qtApplication )
			cls.__idleTimer.timeout.connect( cls.__qtIdleCallback )
		
		if not cls.__idleTimer.isActive() :
			cls.__idleTimer.start()
	
	## Removes an idle callback previously created with addIdleCallback().
	@classmethod
	def removeIdleCallback( cls, callback ) :
	
		cls.__idleCallbacks.remove( callback )
		
		if len( cls.__idleCallbacks )==0 :
			cls.__idleTimer.stop()
	
	## Widgets may only be manipulated on the thread where mainEventLoop() is running. It
	# is common to want to perform some background processing on a secondary thread, and
	# to update the UI during processing or upon completion. This function can be used from
	# such a secondary thread to queue a callable to be called on the main thread.
	@classmethod
	def executeOnUIThread( cls, callable, waitForResult=False ) :
		
		resultCondition = threading.Condition() if waitForResult else None
		
		# we only use a weakref here, because we don't want to be keeping the object
		# alive from this thread, and hence deleting it from this thread. instead it
		# is deleted in _UIThreadExecutor.event().
		uiThreadExecutor = weakref.ref( _UIThreadExecutor( callable, resultCondition ) )
		uiThreadExecutor().moveToThread( cls.__qtApplication.thread() )

		if resultCondition is not None :
			resultCondition.acquire()
			cls.__qtApplication.postEvent( uiThreadExecutor(), QtCore.QEvent( QtCore.QEvent.Type( _UIThreadExecutor.executeEventType ) ) )
			resultCondition.wait()
			resultCondition.release()
			return resultCondition.resultValue
		else :
			cls.__qtApplication.postEvent( uiThreadExecutor(), QtCore.QEvent( QtCore.QEvent.Type( _UIThreadExecutor.executeEventType ) ) )
			return None
			
	# This is a staticmethod rather than a classmethod because PySide 1.0.5
	# doesn't support classmethods as slots.
	@staticmethod
	def __qtIdleCallback() :
	
		toRemove = []
		for c in EventLoop.__idleCallbacks :
			try :
				if not c() :
					toRemove.append( c )
			except Exception, e :
				# if the callback throws then we remove it anyway, because
				# we don't want to keep invoking the same error over and over.
				toRemove.append( c )
				# report the error
				IECore.msg( IECore.Msg.Level.Error, "EventLoop.__qtIdleCallback", "".join( traceback.format_exc( e ) ) )
				
		for c in toRemove :
			EventLoop.removeIdleCallback( c )
				
	def __pumpThreadFn( self ) :
	
		import maya.utils
		
		while 1 :
			time.sleep( 0.01 )
			maya.utils.executeDeferred( self.__pump )
				
	def __pump( self, thrusts=1 ) :
	
		for thrust in range( 0, thrusts ) :
			self.__qtEventLoop.processEvents()

class _UIThreadExecutor( QtCore.QObject ) :

	executeEventType = QtCore.QEvent.registerEventType()

	__instances = set()
	
	def __init__( self, callable, resultCondition = None ) :
	
		QtCore.QObject.__init__( self )
		
		self.__callable = callable
		self.__resultCondition = resultCondition
		# we store a reference to ourselves in __instances, as otherwise
		# we go out of scope and get deleted at the end of executeOnUIThread
		# above. that's bad because we never live long enough to get our event,
		# and we'll also be being deleted from the calling thread, not the ui
		# thread where we live.
		self.__instances.add( self )
		
	def event( self, event ) :
	
		if event.type() == self.executeEventType :
			result = self.__callable()
			if self.__resultCondition is not None :
				self.__resultCondition.acquire()
				self.__resultCondition.resultValue = result
				self.__resultCondition.notify()
				self.__resultCondition.release()
			
			self.__instances.remove( self )
		
			return True
			
		return False
		
