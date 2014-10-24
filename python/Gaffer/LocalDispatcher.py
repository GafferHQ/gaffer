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

	_BatchStatus = IECore.Enum.create( "Waiting", "Running", "Complete", "Failed", "Killed" )
	
	class Job :
		
		def __init__( self, batch, dispatcher, name, jobId, directory ) :
			
			assert( isinstance( batch, Gaffer.Dispatcher._TaskBatch ) )
			assert( isinstance( dispatcher, Gaffer.Dispatcher ) )
			
			self.__batch = batch
			self.__dispatcher = dispatcher
			self.__name = name
			self.__id = jobId
			self.__directory = directory
			
			self.__stats = {}
		
		def name( self ) :
			
			return self.__name
		
		def id( self ) :
			
			return self.__id
		
		def directory( self ) :
			
			return self.__directory
		
		def statistics( self ) :
			
			batch = LocalDispatcher.Job.__currentBatch( self.__batch )
			if batch is None or "pid" not in batch.blindData().keys() :
				return {}
			
			rss = 0
			pcpu = 0.0
			pid = batch.blindData().get( "pid" )
			
			try :
				stats = subprocess.Popen( "ps -s `ps -p %i -o sess=` -o pcpu=,rss=" % pid, shell=True, stdout=subprocess.PIPE ).communicate()[0].split()
				for i in range( 0, len(stats), 2 ) :
					pcpu += float(stats[i])
					rss += float(stats[i+1])
			except :
				return {}
			
			return {
				"pid" : pid,
				"pcpu" : pcpu,
				"rss" : rss,
			}
		
		def failed( self ) :
			
			return LocalDispatcher._getStatus( self.__batch ) == LocalDispatcher._BatchStatus.Failed
		
		def _fail( self ) :
			
			LocalDispatcher._setStatus( self.__batch, LocalDispatcher._BatchStatus.Failed )
		
		def kill( self ) :
			
			if not self.failed() :
				self.__kill( self.__batch )
		
		def killed( self ) :
			
			return "killed" in self.__batch.blindData().keys()
		
		def __kill( self, batch ) :
			
			# this doesn't set the status to Killed because that could
			# run into a race condition with a background dispatch.
			batch.blindData()["killed"] = IECore.BoolData( True )
			for requirement in batch.requirements() :
				self.__kill( requirement )
		
		@staticmethod
		def __currentBatch( batch ) :
			
			if LocalDispatcher._getStatus( batch ) == LocalDispatcher._BatchStatus.Running :
				return batch
			
			for requirement in batch.requirements() :
				
				batch = LocalDispatcher.Job.__currentBatch( requirement )
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

		script = batch.requirements()[0].node().scriptNode()
		context = Gaffer.Context.current()
		scriptFileName = script["fileName"].getValue()
		jobName = context.substitute( self["jobName"].getValue() )
		jobDirectory = self.jobDirectory()
		messageTitle = "%s : Job %s %s" % ( self.getName(), jobName, os.path.basename( jobDirectory ) )
		tmpScript = os.path.join( jobDirectory, os.path.basename( scriptFileName ) if scriptFileName else "untitled.gfr" )

		job = LocalDispatcher.Job(
			batch = batch,
			dispatcher = self,
			name = jobName,
			jobId = os.path.basename( jobDirectory ),
			directory = jobDirectory,
		)
		
		self.__jobPool._append( job )
		
		script.serialiseToFile( tmpScript )

		LocalDispatcher._setStatus( batch, LocalDispatcher._BatchStatus.Waiting, recursive = True )
		
		if self["executeInBackground"].getValue() :
			
			if not self.__preBackgroundDispatch( job, batch, messageTitle ) :
				return
			
			threading.Thread( target = IECore.curry( self.__backgroundDispatch, job, batch, tmpScript, messageTitle ) ).start()
		
		else :
			self.__foregroundDispatch( job, batch, messageTitle )
			self.__dispatchComplete( job, batch, messageTitle )

	def __foregroundDispatch( self, job, batch, messageTitle ) :

		for currentBatch in batch.requirements() :
			if not self.__foregroundDispatch( job, currentBatch, messageTitle ) :
				return False
		
		if batch.blindData().get( "killed" ) :
			self.__dispatchKilled( job, batch, messageTitle )
			return False
		
		if not batch.node() or LocalDispatcher._getStatus( batch ) == LocalDispatcher._BatchStatus.Complete :
			LocalDispatcher._setStatus( batch, LocalDispatcher._BatchStatus.Complete )
			return True

		script = batch.node().scriptNode()

		description = "executing %s on %s" % ( batch.node().relativeName( script ), str(batch.frames()) )
		IECore.msg( IECore.MessageHandler.Level.Info, messageTitle, description )

		try :
			LocalDispatcher._setStatus( batch, LocalDispatcher._BatchStatus.Running )
			batch.execute()
		except :
			traceback.print_exc()
			self.__dispatchFailed( job, batch, messageTitle )
			return False
		
		LocalDispatcher._setStatus( batch, LocalDispatcher._BatchStatus.Complete )
		
		return True

	def __preBackgroundDispatch( self, job, batch, messageTitle ) :

		if batch.node() and batch.node()["dispatcher"]["local"]["executeInForeground"].getValue() :
			if not self.__foregroundDispatch( job, batch, messageTitle ) :
				return False
		else :
			for currentBatch in batch.requirements() :
				if not self.__preBackgroundDispatch( job, currentBatch, messageTitle ) :
					return False
		
		return True

	def __backgroundDispatch( self, job, batch, scriptFile, messageTitle ) :

		if LocalDispatcher._getStatus( batch ) == LocalDispatcher._BatchStatus.Complete :
			return True

		for currentBatch in batch.requirements() :
			if not self.__backgroundDispatch( job, currentBatch, scriptFile, messageTitle ) :
				return False

		if batch.blindData().get( "killed" ) :
			self.__dispatchKilled( job, batch, messageTitle )
			return False
		
		if not batch.node() :
			self.__dispatchComplete( job, batch, messageTitle )
			return True

		script = batch.node().scriptNode()

		if isinstance( batch.node(), Gaffer.TaskList ) :
			LocalDispatcher._setStatus( batch, LocalDispatcher._BatchStatus.Complete )
			IECore.msg( IECore.MessageHandler.Level.Info, messageTitle, "Finished " + batch.node().relativeName( script ) )
			return True
		
		taskContext = batch.context()
		frames = str( IECore.frameListFromList( [ int(x) for x in batch.frames() ] ) )

		cmd = [
			"gaffer", "execute",
			"-script", scriptFile,
			"-nodes", batch.node().relativeName( script ),
			"-frames", frames,
		]

		contextArgs = []
		for entry in taskContext.keys() :
			if entry != "frame" and ( entry not in script.context().keys() or taskContext[entry] != script.context()[entry] ) :
				contextArgs.extend( [ "-" + entry, repr(taskContext[entry]) ] )

		if contextArgs :
			cmd.extend( [ "-context" ] + contextArgs )

		LocalDispatcher._setStatus( batch, LocalDispatcher._BatchStatus.Running )
		IECore.msg( IECore.MessageHandler.Level.Info, messageTitle, " ".join( cmd ) )
		process = subprocess.Popen( " ".join( cmd ), shell=True, preexec_fn=os.setsid )
		batch.blindData()["pid"] = IECore.IntData( process.pid )
		
		while process.poll() is None :
			
			if batch.blindData().get( "killed" ) :
				os.killpg( process.pid, signal.SIGTERM )
				self.__dispatchKilled( job, batch, messageTitle )
				return False
			
			time.sleep( 0.01 )
		
		if process.returncode :
			self.__dispatchFailed( job, batch, messageTitle )
			return False

		LocalDispatcher._setStatus( batch, LocalDispatcher._BatchStatus.Complete )
		
		return True

	@staticmethod
	def _getStatus( batch ) :
		
		return LocalDispatcher._BatchStatus( batch.blindData().get( "status", IECore.IntData( int(LocalDispatcher._BatchStatus.Waiting) ) ).value )
	
	@staticmethod
	def _setStatus( batch, status, recursive = False ) :
		
		batch.blindData()["status"] = IECore.IntData( int(status) )
		
		if recursive :
			for requirement in batch.requirements() :
				LocalDispatcher._setStatus( requirement, status, recursive = True )
	
	def __dispatchComplete( self, job, batch, messageTitle ) :
		
		LocalDispatcher._setStatus( batch, LocalDispatcher._BatchStatus.Complete )
		self.__jobPool._remove( job )
		IECore.msg( IECore.MessageHandler.Level.Info, messageTitle, "Dispatched all tasks for " + job.name() )
	
	def __dispatchFailed( self, job, batch, messageTitle ) :
		
		LocalDispatcher._setStatus( batch, LocalDispatcher._BatchStatus.Failed )
		self.__jobPool._fail( job )
		frames = str( IECore.frameListFromList( [ int(x) for x in batch.frames() ] ) )
		IECore.msg( IECore.MessageHandler.Level.Error, messageTitle, "Failed to execute " + batch.node().getName() + " on frames " + frames )
	
	def __dispatchKilled( self, job, batch, messageTitle ) :
		
		LocalDispatcher._setStatus( batch, LocalDispatcher._BatchStatus.Killed )
		self.__jobPool._remove( job )
		IECore.msg( IECore.MessageHandler.Level.Info, messageTitle, "Killed " + job.name() )
	
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
