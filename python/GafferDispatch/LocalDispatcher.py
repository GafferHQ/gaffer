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
import os
import errno
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
			## \todo Stop storing this. It's just a temptation to access potentially
			# invalid data during background dispatches - all dispatcher settings _must_
			# be copied to the job upon construction, because nothing stops a user changing
			# the dispatcher settings during a background dispatch. Currently __dispatcher
			# is used to access the JobPool in __reportCompleted etc - instead the job should
			# use signals to report changes in status, and the JobPool should connect to those
			# signals. Jobs should be blissfully ignorant of JobPools.
			self.__dispatcher = dispatcher
			script = batch.preTasks()[0].plug().ancestor( Gaffer.ScriptNode )
			self.__context = Gaffer.Context( script.context() )

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
			self.__messageTitle = "%s : Job %s %s" % ( self.__dispatcher.getName(), self.__name, self.__id )

			self.__initBatchWalk( batch )

		def name( self ) :

			return self.__name

		def id( self ) :

			return self.__id

		def directory( self ) :

			return self.__directory

		def description( self ) :

			batch = self.__currentBatch()
			if batch is None or batch.plug() is None :
				return "N/A"

			frames = str( IECore.frameListFromList( [ int(x) for x in batch.frames() ] ) )

			return "Executing " + batch.blindData()["nodeName"].value + " on frames " + frames

		def statistics( self ) :

			batch = self.__currentBatch()
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

		def execute( self ) :

			if self.__executeInBackground :
				threading.Thread( target = self.__executeInternal ).start()
			else :
				self.__executeInternal()

		def failed( self ) :

			return self.__getStatus( self.__batch ) == LocalDispatcher.Job.Status.Failed

		def kill( self ) :

			if not self.failed() :
				self.__killBatchWalk( self.__batch )

		def killed( self ) :

			return "killed" in self.__batch.blindData().keys()

		def _fail( self ) :

			self.__setStatus( self.__batch, LocalDispatcher.Job.Status.Failed )

		def __killBatchWalk( self, batch ) :

			if "killed" in batch.blindData() :
				# Already visited via another path
				return

			# this doesn't set the status to Killed because that could
			# run into a race condition with a background dispatch.
			batch.blindData()["killed"] = IECore.BoolData( True )
			for upstreamBatch in batch.preTasks() :
				self.__killBatchWalk( upstreamBatch )

		def __executeInternal( self ) :

			with self.__messageHandler :
				if self.__executeWalk( self.__batch ) :
					self.__reportCompleted( self.__batch )

		def __executeWalk( self, batch ) :

			if self.__getStatus( batch ) == LocalDispatcher.Job.Status.Complete :
				# Visited this batch by another path
				return True

			for upstreamBatch in batch.preTasks() :
				if not self.__executeWalk( upstreamBatch ) :
					return False

			if batch.blindData().get( "killed" ) :
				self.__reportKilled( batch )
				return False

			IECore.msg(
				IECore.MessageHandler.Level.Info, self.__messageTitle,
				"Executing {node}{framesSeparator}{frames}".format(
					node = batch.blindData()["nodeName"].value,
					framesSeparator = " on frames " if len( batch.frames() ) > 1 else " on frame " if len( batch.frames() ) else "",
					frames = str( IECore.frameListFromList( [ int(x) for x in batch.frames() ] ) )
				)
			)

			self.__setStatus( batch, LocalDispatcher.Job.Status.Running )

			try :
				self.__executeBatch( batch )
			except Exception as e :
				IECore.msg( IECore.MessageHandler.Level.Debug, self.__messageTitle, traceback.format_exc() )
				self.__reportFailed( batch )
				if self.__executeInBackground :
					return False
				else :
					raise e

			self.__setStatus( batch, LocalDispatcher.Job.Status.Complete )

			return True

		def __executeBatch( self, batch ) :

			# Simple cases for foreground execution and no-ops.

			if batch.plug() is None or not batch.frames() :
				# Root batch or no-op batch.
				return
			elif not self.__executeInBackground :
				batch.execute()
				return

			# Background execution. Launch a separate process

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

			if os.name == "nt":
				if self.__environmentCommand :
					process = subprocess.Popen( args, shell=True )
				else :
					process = subprocess.Popen( args )
			else:
				process = subprocess.Popen( args, start_new_session=True )

			batch.blindData()["pid"] = IECore.IntData( process.pid )

			while process.poll() is None :

				if batch.blindData().get( "killed" ) :
					if os.name == "nt" :
						subprocess.check_call( [ "TASKKILL", "/F", "/PID", str( process.pid ), "/T" ] )
					else :
						os.killpg( process.pid, signal.SIGTERM )
					self.__reportKilled( batch )
					return False

				time.sleep( 0.01 )

			if process.returncode :
				raise subprocess.CalledProcessError(
					process.returncode,
					" ".join( shlex.quote( a ) for a in args )
				)

		def __getStatus( self, batch ) :

			return LocalDispatcher.Job.Status( batch.blindData().get( "status", IECore.IntData( int(LocalDispatcher.Job.Status.Waiting) ) ).value )

		def __setStatus( self, batch, status ) :

			batch.blindData()["status"] = IECore.IntData( int(status) )

		def __reportCompleted( self, batch ) :

			self.__setStatus( batch, LocalDispatcher.Job.Status.Complete )
			self.__dispatcher.jobPool()._remove( self )
			IECore.msg( IECore.MessageHandler.Level.Info, self.__messageTitle, "Dispatched all tasks for " + self.name() )

		def __reportFailed( self, batch ) :

			self.__setStatus( batch, LocalDispatcher.Job.Status.Failed )
			self.__dispatcher.jobPool()._fail( self )
			frames = str( IECore.frameListFromList( [ int(x) for x in batch.frames() ] ) )
			IECore.msg( IECore.MessageHandler.Level.Error, self.__messageTitle, "Failed to execute " + batch.blindData()["nodeName"].value + " on frames " + frames )

		def __reportKilled( self, batch ) :

			self.__setStatus( batch, LocalDispatcher.Job.Status.Killed )
			self.__dispatcher.jobPool()._remove( self )
			IECore.msg( IECore.MessageHandler.Level.Info, self.__messageTitle, "Killed " + self.name() )

		def __currentBatch( self ) :

			## \todo Consider just storing the current batch, rather
			# than searching each time it is requested.
			return self.__currentBatchWalk( self.__batch, set() )

		def __currentBatchWalk( self, batch, visited ) :

			if batch in visited :
				return None

			visited.add( batch )

			if self.__getStatus( batch ) == LocalDispatcher.Job.Status.Running :
				return batch

			for upstreamBatch in batch.preTasks() :
				currentBatch = self.__currentBatchWalk( upstreamBatch, visited )
				if currentBatch is not None :
					return currentBatch

			return None

		def __initBatchWalk( self, batch ) :

			if "nodeName" in batch.blindData() :
				# Already visited via another path
				return

			nodeName = ""
			if batch.plug() is not None :
				nodeName = batch.plug().node().relativeName( batch.plug().node().scriptNode() )
			batch.blindData()["nodeName"] = nodeName

			self.__setStatus( batch, LocalDispatcher.Job.Status.Waiting )

			for upstreamBatch in batch.preTasks() :
				self.__initBatchWalk( upstreamBatch )

	class JobPool( IECore.RunTimeTyped ) :

		def __init__( self ) :

			self.__jobs = []
			self.__failedJobs = []
			self.__jobAddedSignal = Gaffer.Signals.Signal1()
			self.__jobRemovedSignal = Gaffer.Signals.Signal1()
			self.__jobFailedSignal = Gaffer.Signals.Signal1()

		def jobs( self ) :

			return list(self.__jobs)

		def failedJobs( self ) :

			return list(self.__failedJobs)

		def waitForAll( self ) :

			while len(self.__jobs) :
				time.sleep( 0.2 )

		def jobAddedSignal( self ) :

			return self.__jobAddedSignal

		def jobRemovedSignal( self ) :

			return self.__jobRemovedSignal

		def jobFailedSignal( self ) :

			return self.__jobFailedSignal

		def _append( self, job ) :

			assert( isinstance( job, LocalDispatcher.Job ) )

			self.__jobs.append( job )
			self.jobAddedSignal()( job )

		def _remove( self, job, force = False ) :

			if job in self.__jobs :
				self.__jobs.remove( job )
				self.jobRemovedSignal()( job )

			if force and job in self.__failedJobs :
				self.__failedJobs.remove( job )

		def _fail( self, job ) :

			if job in self.__jobs and job not in self.__failedJobs :
				job._fail()
				self.__failedJobs.append( job )
				self.jobFailedSignal()( job )
				self._remove( job )

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

		self.__jobPool._append( job )

		job.execute()

IECore.registerRunTimeTyped( LocalDispatcher, typeName = "GafferDispatch::LocalDispatcher" )
IECore.registerRunTimeTyped( LocalDispatcher.JobPool, typeName = "GafferDispatch::LocalDispatcher::JobPool" )

GafferDispatch.Dispatcher.registerDispatcher( "Local", LocalDispatcher )
