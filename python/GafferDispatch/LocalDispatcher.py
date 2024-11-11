##########################################################################
#
#  Copyright (c) 2013-2014, Image Engine Design Inc. All rights reserved.
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

import atexit
import collections
import datetime
import enum
import functools
import os
import re
import signal
import shlex
import subprocess
import threading
import time
import traceback

import psutil

import IECore

import Gaffer
import GafferDispatch

class LocalDispatcher( GafferDispatch.Dispatcher ) :

	def __init__( self, name = "LocalDispatcher", jobPool = None ) :

		GafferDispatch.Dispatcher.__init__( self, name )

		self["executeInBackground"] = Gaffer.BoolPlug( defaultValue = False )
		self["ignoreScriptLoadErrors"] = Gaffer.BoolPlug( defaultValue = False )
		self["environmentCommand"] = Gaffer.StringPlug()

		self.__jobPool = jobPool if jobPool else LocalDispatcher.defaultJobPool()

	class Job( object ) :

		Status = enum.IntEnum( "Status", [ "Waiting", "Running", "Complete", "Failed", "Killed" ] )

		def __init__( self, batch, dispatcher ) :

			assert( isinstance( batch, GafferDispatch.Dispatcher._TaskBatch ) )
			assert( isinstance( dispatcher, GafferDispatch.Dispatcher ) )

			self.__rootBatch = batch

			script = batch.preTasks()[0].plug().ancestor( Gaffer.ScriptNode )
			self.__context = Gaffer.Context( script.context() )

			# Store all dispatcher settings now, as we can't access the dispatcher
			# again if we're executing in the background (as it may be modified on
			# the main thread).
			self.__name = dispatcher["jobName"].getValue()
			self.__directory = Gaffer.Context.current()["dispatcher:jobDirectory"]
			self.__scriptFile = Gaffer.Context.current()["dispatcher:scriptFileName"]
			self.__frameRange = dispatcher.frameRange()
			self.__id = os.path.basename( self.__directory )
			self.__ignoreScriptLoadErrors = dispatcher["ignoreScriptLoadErrors"].getValue()
			self.__environmentCommand = dispatcher["environmentCommand"].getValue()
			self.__executeInBackground = dispatcher["executeInBackground"].getValue()

			if self.__executeInBackground :
				application = script.ancestor( Gaffer.ApplicationRoot )
				if application is not None and application.getName() == "execute" :
					# Background execution makes no sense within the `execute`
					# app, since the app will exit as soon as `_doDispatch()`
					# returns, and the background job will be killed before it
					# can complete.
					IECore.msg( IECore.Msg.Level.Warning, "LocalDispatcher", "Forcing foreground execution" )
					self.__executeInBackground = False

			self.__startTime = datetime.datetime.now( datetime.timezone.utc )
			self.__endTime = None

			self.__messageHandler = _MessageHandler()
			self.__messagesChangedSignal = Gaffer.Signal1()
			self.__messageHandler.messagesChangedSignal().connect( Gaffer.WeakMethod( self.__messagesChanged, fallbackResult = None ) )

			self.__initBatchWalk( batch )

			self.__statusChangedSignal = Gaffer.Signal1()

			self.__currentProcess = None
			self.__status = self.Status.Waiting
			self.__backgroundTask = None

		def name( self ) :

			return self.__name

		def id( self ) :

			return self.__id

		def directory( self ) :

			return self.__directory

		def frameRange( self ) :

			return self.__frameRange

		def environmentCommand( self ) :

			return self.__environmentCommand

		def startTime( self ) :

			return self.__startTime

		def runningTime( self ) :

			if self.__endTime is not None :
				return self.__endTime - self.__startTime
			else :
				return datetime.datetime.now( datetime.timezone.utc ) - self.__startTime

		def processID( self ) :

			return self.__currentProcess.pid if self.__currentProcess is not None else None

		def memoryUsage( self ) :

			if self.__currentProcess is None :
				return None

			try :
				return self.__currentProcess.memory_info().rss
			except psutil.NoSuchProcess :
				return None

		def cpuUsage( self ) :

			if self.__currentProcess is None :
				return None

			try :
				return self.__currentProcess.cpu_percent()
			except psutil.NoSuchProcess :
				return None

		def status( self ) :

			return self.__status

		def kill( self ) :

			if self.__backgroundTask is not None :
				self.__backgroundTask.cancel()
				if self.__backgroundTask.status() == self.__backgroundTask.Status.Cancelled :
					# Usually we'll get to update our status naturally because `__executeInternal()`
					# will throw `IECore.Cancelled.`. But if `__executeInternal()` hasn't been called
					# by the BackgroundTask yet, then it will _never_ be called, and the BackgroundTask
					# will have transitioned to a Cancelled status _immediately_. We work around this by
					# updating status manually.
					#
					# In many ways it would be great if we used `__backgroundTask.status()` directly
					# as _our_ status. But that can't work for foreground dispatches, so for the moment
					# we prefer to track foreground/background status identically.
					self.__updateStatus( self.Status.Killed )

		def statusChangedSignal( self ) :

			return self.__statusChangedSignal

		def messages( self ) :

			return self.__messageHandler.messages()

		def messagesChangedSignal( self ) :

			return self.__messagesChangedSignal

		def _execute( self ) :

			if self.__executeInBackground :
				self.__backgroundTask = Gaffer.BackgroundTask( None, Gaffer.WeakMethod( self.__executeInternal ) )
			else :
				self.__executeInternal()

		def __executeInternal( self, canceller = None ) :

			with self.__messageHandler :
				self.__updateStatus( self.Status.Running )
				try :
					self.__executeWalk( self.__rootBatch, canceller )
				except IECore.Cancelled :
					self.__updateStatus( self.Status.Killed )
				except :
					self.__updateStatus( self.Status.Failed )
					if not self.__executeInBackground :
						raise
				else :
					self.__updateStatus( self.Status.Complete )

		def __executeWalk( self, batch, canceller ) :

			if "localDispatcher:executed" in batch.blindData() :
				# Visited this batch by another path
				return

			for upstreamBatch in batch.preTasks() :
				self.__executeWalk( upstreamBatch, canceller )

			if batch.plug() is None :
				assert( batch is self.__rootBatch )
				return

			if len( batch.frames() ) == 0 :
				# This case occurs for nodes like TaskList and
				# TaskContextProcessors, because they don't do anything in
				# execute (they have empty hashes). Their batches exist only to
				# depend on upstream batches, so we don't need to do any work
				# here.
				return

			IECore.Canceller.check( canceller )

			frames = "frame{framesPlural} {frames}".format(
				framesPlural = "s" if len( batch.frames() ) > 1 else "",
				frames = str( IECore.frameListFromList( [ int( x ) for x in batch.frames() ] ) )
			)

			IECore.msg(
				IECore.MessageHandler.Level.Info, batch.blindData()["nodeName"].value,
				f"Executing {frames}"
			)

			try :
				startTime = time.perf_counter()
				self.__executeBatch( batch, canceller )
				IECore.msg(
					IECore.MessageHandler.Level.Info, batch.blindData()["nodeName"].value,
					"Completed {frames} in {time}".format(
						frames = frames,
						time = datetime.timedelta( seconds = int( 0.5 + time.perf_counter() - startTime ) )
					)
				)
				batch.blindData()["localDispatcher:executed"] = IECore.BoolData( True )
			except Exception as e :
				IECore.msg( IECore.MessageHandler.Level.Debug, batch.blindData()["nodeName"].value, traceback.format_exc().strip() )
				IECore.msg(
					IECore.MessageHandler.Level.Error, batch.blindData()["nodeName"].value,
					f"Execution failed for {frames}"
				)
				raise e

		def __executeBatch( self, batch, canceller ) :

			# Simple case for foreground execution.

			if not self.__executeInBackground :
				batch.execute()
				return

			# Background execution. Launch a separate process.
			# Start by building the command arguments.

			taskContext = batch.context()
			frames = str( IECore.frameListFromList( [ int(x) for x in batch.frames() ] ) )

			args = shlex.split( self.__environmentCommand ) + [
				str( Gaffer.executablePath() ),
				"execute",
				"-script", str( self.__scriptFile ),
				"-nodes", batch.blindData()["nodeName"].value,
				"-frames", frames,
			]

			if self.__ignoreScriptLoadErrors :
				args.append( "-ignoreScriptLoadErrors" )

			contextArgs = []
			for entry in [ k for k in taskContext.keys() if k != "frame" and not k.startswith( "ui:" ) ] :
				if entry not in self.__context.keys() or taskContext[entry] != self.__context[entry] :
					contextArgs.extend( [ "-" + entry, IECore.repr( taskContext[entry] ) ] )

			if contextArgs :
				args.extend( [ "-context" ] + contextArgs )

			# Build environment. We want to enable all Cortex message levels so
			# we can capture everything and then let the LocalJobs UI filter
			# it dynamically.

			env = os.environ.copy()
			env["IECORE_LOG_LEVEL"] = "DEBUG"

			# Launch process.

			IECore.msg( IECore.Msg.Level.Debug, batch.blindData()["nodeName"].value, "Executing `{}`".format( " ".join( args ) ) )

			platformKW = { "start_new_session" : True } if os.name != "nt" else {}
			process = subprocess.Popen(
				args,
				text = True, stdout = subprocess.PIPE, stderr = subprocess.STDOUT,
				shell = os.name == "nt" and self.__environmentCommand, env = env,
				**platformKW,
			)
			self.__currentProcess = psutil.Process( process.pid )

			# Launch a thread to monitor the output stream and feed it into a
			# our message handler. We must do this on a thread because reading
			# from the stream is a blocking operation, and we need to check for
			# cancellation periodically even if there is no output.
			# > Note : `os.set_blocking( False )` is not a good solution because :
			# >  1. It is not available on Windows until Python 3.12.
			# >  2. If we interleave sleeping and reading on one thread, processes
			# >     with a lot of output are artifically slowed by the sleeps.

			def handleOutput( stream, messageContext, messageHandler ) :

				for line in iter( stream.readline, "" ) :
					message, level = _messageLevel( line[:-1] )
					messageHandler.handle( level, messageContext, message )
				stream.close()

			outputHandler = threading.Thread(
				target = handleOutput,
				args = [ process.stdout, str( batch.blindData()["nodeName"] ), self.__messageHandler ],
				name = "localDispatcherOutputHandler",
			)
			outputHandler.start()

			# Wait for the process to complete, killing it if cancellation
			# is requested in the meantime.

			try :

				while process.poll() is None :

					if canceller is not None and canceller.cancelled() :
						if os.name == "nt" :
							for toKill in self.__currentProcess.children( recursive = True ) + [ self.__currentProcess ] :
								toKill.kill()
						else :
							os.killpg( process.pid, signal.SIGTERM )
						raise IECore.Cancelled()

					time.sleep( 0.01 )

				if process.returncode :
					raise subprocess.CalledProcessError(
						process.returncode,
						" ".join( args )
					)

			finally :

				self.__currentProcess = None
				outputHandler.join()

		def __initBatchWalk( self, batch ) :

			if "nodeName" in batch.blindData() :
				# Already visited via another path
				return

			nodeName = ""
			if batch.plug() is not None :
				nodeName = batch.plug().node().relativeName( batch.plug().node().scriptNode() )
			batch.blindData()["nodeName"] = nodeName

			for upstreamBatch in batch.preTasks() :
				self.__initBatchWalk( upstreamBatch )

		def __updateStatus( self, status ) :

			if status == self.__status :
				return

			self.__status = status

			if status in ( self.Status.Complete, self.Status.Failed, self.Status.Killed ) :
				self.__endTime = datetime.datetime.now( datetime.timezone.utc )

			if threading.current_thread() is threading.main_thread() :
				self.__emitStatusChanged()
			elif Gaffer.ParallelAlgo.canCallOnUIThread() :
				Gaffer.ParallelAlgo.callOnUIThread( Gaffer.WeakMethod( self.__emitStatusChanged, fallbackResult = None ) )

			IECore.msg(
				IECore.MessageHandler.Level.Info, f"{self.__name} {self.__id}", str( status )
			)

		def __messagesChanged( self ) :

			self.__messagesChangedSignal( self )

		def __emitStatusChanged( self ) :

			self.statusChangedSignal()( self )

	class JobPool :

		def __init__( self ) :

			self.__jobs = collections.OrderedDict()
			self.__nextId = 0

			self.__jobAddedSignal = Gaffer.Signals.Signal1()
			self.__jobRemovedSignal = Gaffer.Signals.Signal1()

		# Returns a list of jobs in the order they were added.
		def jobs( self ) :

			return list( self.__jobs.values() )

		# Returns an ordered dictionary mapping from unique IDs to jobs.
		def jobsDict( self ) :

			return self.__jobs

		def waitForAll( self ) :

			while any( j.status() in ( j.Status.Waiting, j.Status.Running ) for j in self.__jobs.values() ) :
				time.sleep( 0.2 )

		def jobAddedSignal( self ) :

			return self.__jobAddedSignal

		def jobRemovedSignal( self ) :

			return self.__jobRemovedSignal

		def addJob( self, job ) :

			assert( isinstance( job, LocalDispatcher.Job ) )

			job.__jobPoolId = self.__nextId
			self.__nextId += 1
			self.__jobs[job.__jobPoolId] = job

			self.jobAddedSignal()( job )

		def removeJob( self, job ) :

			del self.__jobs[job.__jobPoolId]
			self.jobRemovedSignal()( job )

	__defaultJobPool = None

	@staticmethod
	def defaultJobPool() :

		if LocalDispatcher.__defaultJobPool is not None :
			return LocalDispatcher.__defaultJobPool

		LocalDispatcher.__defaultJobPool = LocalDispatcher.JobPool()

		def cleanupJobPool( jobPool ) :

			for job in jobPool.jobs() :
				job.kill()

			jobPool.waitForAll()

		atexit.register( cleanupJobPool, LocalDispatcher.__defaultJobPool )

		return LocalDispatcher.__defaultJobPool

	def jobPool( self ) :

		return self.__jobPool

	def _doDispatch( self, batch ) :

		job = LocalDispatcher.Job(
			batch = batch,
			dispatcher = self,
		)

		self.__jobPool.addJob( job )
		job._execute()

IECore.registerRunTimeTyped( LocalDispatcher, typeName = "GafferDispatch::LocalDispatcher" )
GafferDispatch.Dispatcher.registerDispatcher( "Local", LocalDispatcher )

## \todo Should this be a shared component implemented in C++ in `Messages.h`?
# It is incredibly similar to the handler in `InteractiveRender.cpp`.
class _MessageHandler( IECore.MessageHandler ) :

	def __init__( self ) :

		IECore.MessageHandler.__init__( self )

		self.__mutex = threading.Lock()
		self.__messages = Gaffer.Private.IECorePreview.Messages()
		self.__messagesChangedSignal = Gaffer.Signal0()
		self.__messagesChangedPending = False

	def messages( self ) :

		with self.__mutex :
			return Gaffer.Private.IECorePreview.Messages( self.__messages )

	def messagesChangedSignal( self ) :

		return self.__messagesChangedSignal

	def handle( self, level, context, message ) :

		lines = message.split( "\n" ) # A message per line works better with `MessageWidget.Role.Log`
		with self.__mutex :
			for line in lines :
				self.__messages.add( Gaffer.Private.IECorePreview.Message( level, context, line ) )
			pendingAlready = self.__messagesChangedPending
			self.__messagesChangedPending = True

		if threading.current_thread() is threading.main_thread() :
			self.__messagesChangedSignal()
			return

		if pendingAlready :
			return

		if Gaffer.ParallelAlgo.canCallOnUIThread() :
			Gaffer.ParallelAlgo.callOnUIThread( Gaffer.WeakMethod( self.__messagesChangedUICall, fallbackResult = None ) )

	def __messagesChangedUICall( self ) :

		with self.__mutex :
			self.__messagesChangedPending = False

		self.__messagesChangedSignal()

__messageLevelRE = re.compile(
	r"(DEBUG|INFO|WARNING|ERROR) +[:|] ",
)

# Uses heuristics to discern the IECore.Msg.Level for an arbitrary line of output
# captured from a subproces, returning the message and level.
def _messageLevel( line ) :

	m = __messageLevelRE.search( line )
	if m is not None :
		level = IECore.Msg.Level.names[m.group(1).title()]
		if m.start() == 0 :
			# Level is at start of line - strip it so it's not doubled
			# up with our own level.
			line = line[:m.start()] + line[m.end():]
		return line, level

	return line, IECore.Msg.Level.Info
