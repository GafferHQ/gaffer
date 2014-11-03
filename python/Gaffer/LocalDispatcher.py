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

import os
import errno
import signal
import subprocess
import threading
import time
import traceback

import Gaffer
import IECore

class LocalDispatcher( Gaffer.Dispatcher ) :

	def __init__( self, name = "LocalDispatcher", jobPool = None ) :

		Gaffer.Dispatcher.__init__( self, name )

		backgroundPlug = Gaffer.BoolPlug( "executeInBackground", defaultValue = False )
		self.addChild( backgroundPlug )
		
		self.__jobPool = jobPool if jobPool else LocalDispatcher.defaultJobPool()

	class Job :
		
		Status = IECore.Enum.create( "Waiting", "Running", "Complete", "Failed", "Killed" )
		
		def __init__( self, batch, dispatcher, name, jobId, directory ) :
			
			assert( isinstance( batch, Gaffer.Dispatcher._TaskBatch ) )
			assert( isinstance( dispatcher, Gaffer.Dispatcher ) )
			
			self.__batch = batch
			self.__dispatcher = dispatcher
			
			self.__name = name
			self.__id = jobId
			self.__directory = directory
			self.__stats = {}
			
			self.__messageHandler = IECore.CapturingMessageHandler()
			self.__messageTitle = "%s : Job %s %s" % ( self.__dispatcher.getName(), self.__name, self.__id )
			
			script = batch.requirements()[0].node().scriptNode()
			scriptFileName = script["fileName"].getValue()
			self.__scriptFile = os.path.join( self.__directory, os.path.basename( scriptFileName ) if scriptFileName else "untitled.gfr" )
			script.serialiseToFile( self.__scriptFile )
			
			self.__setStatus( batch, LocalDispatcher.Job.Status.Waiting, recursive = True )
		
		def name( self ) :
			
			return self.__name
		
		def id( self ) :
			
			return self.__id
		
		def directory( self ) :
			
			return self.__directory
		
		def description( self ) :
			
			batch = self.__currentBatch( self.__batch )
			if batch is None or batch.node() is None :
				return "N/A"
			
			node = batch.node().relativeName( batch.node().scriptNode() )
			frames = str( IECore.frameListFromList( [ int(x) for x in batch.frames() ] ) )
			
			return "Executing " + node + " on frames " + frames
		
		def statistics( self ) :
			
			batch = self.__currentBatch( self.__batch )
			if batch is None or "pid" not in batch.blindData().keys() :
				return {}
			
			rss = 0
			pcpu = 0.0
			pid = batch.blindData().get( "pid" )
			
			try :
				stats = subprocess.Popen( ( "ps -Ao pid,ppid,pgid,sess,pcpu,rss" ).split( " " ), stdout=subprocess.PIPE, stderr=subprocess.PIPE ).communicate()[0].split()
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
		
		def execute( self, background = False ) :
			
			if background :
				
				with self.__messageHandler :
					if not self.__preBackgroundDispatch( self.__batch ) :
						return
				
				threading.Thread( target = self.__backgroundDispatch ).start()
			
			else :
				with self.__messageHandler :
					self.__foregroundDispatch( self.__batch )
					self.__reportCompleted( self.__batch )
		
		def failed( self ) :
			
			return self.__getStatus( self.__batch ) == LocalDispatcher.Job.Status.Failed
		
		def kill( self ) :
			
			if not self.failed() :
				self.__kill( self.__batch )
		
		def killed( self ) :
			
			return "killed" in self.__batch.blindData().keys()
		
		def _fail( self ) :
			
			self.__setStatus( self.__batch, LocalDispatcher.Job.Status.Failed )
		
		def __kill( self, batch ) :
			
			# this doesn't set the status to Killed because that could
			# run into a race condition with a background dispatch.
			batch.blindData()["killed"] = IECore.BoolData( True )
			for requirement in batch.requirements() :
				self.__kill( requirement )
		
		def __foregroundDispatch( self, batch ) :
			
			for currentBatch in batch.requirements() :
				if not self.__foregroundDispatch( currentBatch ) :
					return False
			
			if batch.blindData().get( "killed" ) :
				self.__reportKilled( batch )
				return False
			
			if not batch.node() or self.__getStatus( batch ) == LocalDispatcher.Job.Status.Complete :
				self.__setStatus( batch, LocalDispatcher.Job.Status.Complete )
				return True
			
			script = batch.node().scriptNode()
			
			description = "executing %s on %s" % ( batch.node().relativeName( script ), str(batch.frames()) )
			IECore.msg( IECore.MessageHandler.Level.Info, self.__messageTitle, description )
			
			try :
				self.__setStatus( batch, LocalDispatcher.Job.Status.Running )
				batch.execute()
			except :
				traceback.print_exc()
				self.__reportFailed( batch )
				return False
			
			self.__setStatus( batch, LocalDispatcher.Job.Status.Complete )
			
			return True
		
		def __preBackgroundDispatch( self, batch ) :
			
			if batch.node() and batch.node()["dispatcher"]["local"]["executeInForeground"].getValue() :
				if not self.__foregroundDispatch( batch ) :
					return False
			else :
				for currentBatch in batch.requirements() :
					if not self.__preBackgroundDispatch( currentBatch ) :
						return False
			
			return True
		
		def __backgroundDispatch( self ) :
			
			with self.__messageHandler :
				self.__doBackgroundDispatch( self.__batch )
		
		def __doBackgroundDispatch( self, batch ) :
			
			if self.__getStatus( batch ) == LocalDispatcher.Job.Status.Complete :
				return True
			
			for currentBatch in batch.requirements() :
				if not self.__doBackgroundDispatch( currentBatch ) :
					return False
			
			if batch.blindData().get( "killed" ) :
				self.__reportKilled( batch )
				return False
			
			if not batch.node() :
				self.__reportCompleted( batch )
				return True
			
			script = batch.node().scriptNode()
			
			if isinstance( batch.node(), Gaffer.TaskList ) :
				self.__setStatus( batch, LocalDispatcher.Job.Status.Complete )
				IECore.msg( IECore.MessageHandler.Level.Info, self.__messageTitle, "Finished " + batch.node().relativeName( script ) )
				return True
			
			taskContext = batch.context()
			frames = str( IECore.frameListFromList( [ int(x) for x in batch.frames() ] ) )
			
			args = [
				"gaffer", "execute",
				"-script", self.__scriptFile,
				"-nodes", batch.node().relativeName( script ),
				"-frames", frames,
			]
			
			contextArgs = []
			for entry in [ k for k in taskContext.keys() if k != "frame" and not k.startswith( "ui:" ) ] :
				if entry not in script.context().keys() or taskContext[entry] != script.context()[entry] :
					contextArgs.extend( [ "-" + entry, repr(taskContext[entry]) ] )
			
			if contextArgs :
				args.extend( [ "-context" ] + contextArgs )
			
			self.__setStatus( batch, LocalDispatcher.Job.Status.Running )
			IECore.msg( IECore.MessageHandler.Level.Info, self.__messageTitle, " ".join( args ) )
			process = subprocess.Popen( args, preexec_fn=os.setsid )
			batch.blindData()["pid"] = IECore.IntData( process.pid )
			
			while process.poll() is None :
				
				if batch.blindData().get( "killed" ) :
					os.killpg( process.pid, signal.SIGTERM )
					self.__reportKilled( batch )
					return False
				
				time.sleep( 0.01 )
			
			if process.returncode :
				self.__reportFailed( batch )
				return False
			
			self.__setStatus( batch, LocalDispatcher.Job.Status.Complete )
			
			return True
		
		def __getStatus( self, batch ) :
			
			return LocalDispatcher.Job.Status( batch.blindData().get( "status", IECore.IntData( int(LocalDispatcher.Job.Status.Waiting) ) ).value )
		
		def __setStatus( self, batch, status, recursive = False ) :
			
			batch.blindData()["status"] = IECore.IntData( int(status) )
			
			if recursive :
				for requirement in batch.requirements() :
					self.__setStatus( requirement, status, recursive = True )
		
		def __reportCompleted( self, batch ) :
			
			self.__setStatus( batch, LocalDispatcher.Job.Status.Complete )
			self.__dispatcher.jobPool()._remove( self )
			IECore.msg( IECore.MessageHandler.Level.Info, self.__messageTitle, "Dispatched all tasks for " + self.name() )
		
		def __reportFailed( self, batch ) :
			
			self.__setStatus( batch, LocalDispatcher.Job.Status.Failed )
			self.__dispatcher.jobPool()._fail( self )
			frames = str( IECore.frameListFromList( [ int(x) for x in batch.frames() ] ) )
			IECore.msg( IECore.MessageHandler.Level.Error, self.__messageTitle, "Failed to execute " + batch.node().getName() + " on frames " + frames )
		
		def __reportKilled( self, batch ) :
			
			self.__setStatus( batch, LocalDispatcher.Job.Status.Killed )
			self.__dispatcher.jobPool()._remove( self )
			IECore.msg( IECore.MessageHandler.Level.Info, self.__messageTitle, "Killed " + self.name() )
		
		def __currentBatch( self, batch ) :
			
			if self.__getStatus( batch ) == LocalDispatcher.Job.Status.Running :
				return batch
			
			for requirement in batch.requirements() :
				
				batch = self.__currentBatch( requirement )
				if batch is not None :
					return batch
			
			return None
	
	class JobPool( IECore.RunTimeTyped ) :
		
		def __init__( self ) :
			
			self.__jobs = []
			self.__failedJobs = []
			self.__jobAddedSignal = Gaffer.Signal1()
			self.__jobRemovedSignal = Gaffer.Signal1()
			self.__jobFailedSignal = Gaffer.Signal1()
		
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
		
		def _remove( self, job ) :
			
			if job in self.__jobs :
				self.__jobs.remove( job )
				self.jobRemovedSignal()( job )
		
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
			name = Gaffer.Context.current().substitute( self["jobName"].getValue() ),
			jobId = os.path.basename( self.jobDirectory() ),
			directory = self.jobDirectory(),
		)
		
		self.__jobPool._append( job )
		
		job.execute( background = self["executeInBackground"].getValue() )
	
	@staticmethod
	def _doSetupPlugs( parentPlug ) :

		if "local" not in parentPlug :
			localPlug = Gaffer.CompoundPlug( "local" )
			parentPlug.addChild( localPlug )

		parentPlug["local"].clearChildren()

		foregroundPlug = Gaffer.BoolPlug( "executeInForeground", defaultValue = False )
		parentPlug["local"].addChild( foregroundPlug )

IECore.registerRunTimeTyped( LocalDispatcher, typeName = "Gaffer::LocalDispatcher" )
IECore.registerRunTimeTyped( LocalDispatcher.JobPool, typeName = "Gaffer::LocalDispatcher::JobPool" )

Gaffer.Dispatcher.registerDispatcher( "Local", LocalDispatcher, setupPlugsFn = LocalDispatcher._doSetupPlugs )
