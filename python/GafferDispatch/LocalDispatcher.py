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

import enum
import functools
import os
import signal
import shlex
import subprocess
import threading
import time
import traceback

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

			self.__batch = batch

			script = batch.preTasks()[0].plug().ancestor( Gaffer.ScriptNode )
			self.__context = Gaffer.Context( script.context() )

			# Store all dispatcher settings now, as we can't access the dispatcher
			# again if we're executing in the background (as it may be modified on
			# the main thread).
			self.__name = Gaffer.Context.current().substitute( dispatcher["jobName"].getValue() )
			self.__directory = Gaffer.Context.current()["dispatcher:jobDirectory"]
			self.__scriptFile = Gaffer.Context.current()["dispatcher:scriptFileName"]
			self.__id = os.path.basename( self.__directory )
			self.__ignoreScriptLoadErrors = dispatcher["ignoreScriptLoadErrors"].getValue()
			## \todo Make `Dispatcher::dispatch()` use a Process, so we don't need to
			# do substitutions manually like this.
			self.__environmentCommand = Gaffer.Context.current().substitute(
				dispatcher["environmentCommand"].getValue()
			)
			self.__executeInBackground = dispatcher["executeInBackground"].getValue()

			self.__messageHandler = IECore.CapturingMessageHandler()
			self.__messageTitle = "%s : Job %s %s" % ( dispatcher.getName(), self.__name, self.__id )

			self.__initBatchWalk( batch )

			self.__statusChangedSignal = Gaffer.Signal1()

			self.__currentBatch = None
			self.__status = self.Status.Waiting
			self.__backgroundTask = None

		def name( self ) :

			return self.__name

		def id( self ) :

			return self.__id

		def directory( self ) :

			return self.__directory

		def description( self ) :

			batch = self.__currentBatch
			if batch is None or batch.plug() is None :
				return "N/A"

			frames = str( IECore.frameListFromList( [ int(x) for x in batch.frames() ] ) )

			return "Executing " + batch.blindData()["nodeName"].value + " on frames " + frames

		def statistics( self ) :

			batch = self.__currentBatch
			if batch is None or "pid" not in batch.blindData().keys() :
				return {}

			rss = 0
			pcpu = 0.0
			pid = batch.blindData().get( "pid" )

			try :
				stats = subprocess.check_output(
					[ "ps", "-Ao", "pid,ppid,pgid,sess,pcpu,rss" ],
					universal_newlines = True,
				).split()
				for i in range( 0, len(stats), 6 ) :
					if str(pid) in stats[i:i+4] :
						pcpu += float(stats[i+4])
						rss += float(stats[i+5])
			except :
				return {}

			return {
				"pid" : pid,
				"pcpu" : pcpu,
				"rss" : rss,
			}

		def messageHandler( self ) :

			return self.__messageHandler

		def status( self ) :

			return self.__status

		def kill( self ) :

			if self.__backgroundTask is not None :
				self.__backgroundTask.cancel()

		def statusChangedSignal( self ) :

			return self.__statusChangedSignal

		def _execute( self ) :

			if self.__executeInBackground :
				self.__backgroundTask = Gaffer.BackgroundTask( None, self.__executeInternal )
			else :
				self.__executeInternal()

		def __executeInternal( self, canceller = None ) :

			with self.__messageHandler :
				self.__updateStatus( self.Status.Running )
				try :
					self.__executeWalk( self.__batch, canceller )
				except IECore.Cancelled :
					self.__updateStatus( self.Status.Killed )
					IECore.msg( IECore.MessageHandler.Level.Info, self.__messageTitle, "Killed " + self.name() )
				except :
					self.__updateStatus( self.Status.Failed )
					if not self.__executeInBackground :
						raise
				else :
					self.__updateStatus( self.Status.Complete )
					IECore.msg( IECore.MessageHandler.Level.Info, self.__messageTitle, "Dispatched all tasks for " + self.name() )

		def __executeWalk( self, batch, canceller ) :

			if "localDispatcher:executed" in batch.blindData() :
				# Visited this batch by another path
				return

			for upstreamBatch in batch.preTasks() :
				self.__executeWalk( upstreamBatch, canceller )

			IECore.Canceller.check( canceller )

			IECore.msg(
				IECore.MessageHandler.Level.Info, self.__messageTitle,
				"Executing {node}{framesSeparator}{frames}".format(
					node = batch.blindData()["nodeName"].value,
					framesSeparator = " on frames " if len( batch.frames() ) > 1 else " on frame " if len( batch.frames() ) else "",
					frames = str( IECore.frameListFromList( [ int(x) for x in batch.frames() ] ) )
				)
			)

			try :
				self.__currentBatch = batch
				self.__executeBatch( batch, canceller )
				batch.blindData()["localDispatcher:executed"] = IECore.BoolData( True )
			except Exception as e :
				IECore.msg( IECore.MessageHandler.Level.Debug, self.__messageTitle, traceback.format_exc() )
				IECore.msg(
					IECore.MessageHandler.Level.Error, self.__messageTitle,
					"Failed to execute {} on frames {}".format(
						batch.blindData()["nodeName"].value, IECore.frameListFromList( [ int(x) for x in batch.frames() ] )
					)
				)
				raise e
			finally :
				self.__currentBatch = None

		def __executeBatch( self, batch, canceller ) :

			# Simple cases for foreground execution and no-ops.

			if batch.plug() is None or not batch.frames() :
				# Root batch or no-op batch.
				return
			elif not self.__executeInBackground :
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

			# Launch process.

			platformKW = { "start_new_session" : True } if os.name != "nt" else {}
			process = subprocess.Popen(
				args,
				text = True, stdout = subprocess.PIPE, stderr = subprocess.STDOUT,
				shell = os.name == "nt" and self.__environmentCommand,
				**platformKW,
			)
			batch.blindData()["pid"] = IECore.IntData( process.pid )

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
					messageHandler.handle( IECore.Msg.Level.Info, messageContext, line[:-1] )
				stream.close()

			outputHandler = threading.Thread(
				target = handleOutput,
				args = [ process.stdout, str( batch.blindData()["nodeName"] ), self.__messageHandler ],
				name = "localDispatcherOutputHandler",
			)
			outputHandler.start()

			# Wait for the process to complete, killing it if cancellation
			# is requested in the meantime.

			while process.poll() is None :

				if canceller is not None and canceller.cancelled() :
					if os.name == "nt" :
						subprocess.check_call( [ "TASKKILL", "/F", "/PID", str( process.pid ), "/T" ] )
					else :
						os.killpg( process.pid, signal.SIGTERM )
					outputHandler.join()
					raise IECore.Cancelled()

				time.sleep( 0.01 )

			outputHandler.join()

			if process.returncode :
				raise subprocess.CalledProcessError(
					process.returncode,
					" ".join( shlex.quote( a ) for a in args )
				)

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

			self.__status = status
			if threading.current_thread() is threading.main_thread() :
				self.statusChangedSignal()( self )
			elif Gaffer.ParallelAlgo.canCallOnUIThread() :
				Gaffer.ParallelAlgo.callOnUIThread( functools.partial( self.statusChangedSignal(), self ) )

	class JobPool :

		def __init__( self ) :

			self.__jobs = []
			self.__jobAddedSignal = Gaffer.Signals.Signal1()
			self.__jobRemovedSignal = Gaffer.Signals.Signal1()

		def jobs( self ) :

			return list(self.__jobs)

		def waitForAll( self ) :

			while any( j.status() in ( j.Status.Waiting, j.Status.Running ) for j in self.__jobs ) :
				time.sleep( 0.2 )

		def jobAddedSignal( self ) :

			return self.__jobAddedSignal

		def jobRemovedSignal( self ) :

			return self.__jobRemovedSignal

		def addJob( self, job ) :

			assert( isinstance( job, LocalDispatcher.Job ) )

			self.__jobs.append( job )
			self.jobAddedSignal()( job )

		def removeJob( self, job ) :

			if job in self.__jobs :
				self.__jobs.remove( job )
				self.jobRemovedSignal()( job )

	__jobPool = JobPool()

	@staticmethod
	def defaultJobPool() :

		return LocalDispatcher.__jobPool

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
