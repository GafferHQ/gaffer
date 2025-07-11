##########################################################################
#
#  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

import dataclasses

import IECore

import Gaffer
import GafferDispatch
import GafferTractor

class TractorDispatcher( GafferDispatch.Dispatcher ) :

	def __init__( self, name = "TractorDispatcher" ) :

		GafferDispatch.Dispatcher.__init__( self, name )

		self["service"] = Gaffer.StringPlug( defaultValue = '"*"' )
		self["envKey"] = Gaffer.StringPlug()

	## Decribes the Gaffer task associated with a particular Tractor task.
	@dataclasses.dataclass
	class TaskData :

		# The `GafferDispatch.TaskPlug` being executed. The associated node
		# can be accessed via `plug.node()`.
		plug : Gaffer.Plug
		# The Gaffer context in which the task is executed. Does not
		# contain the frame number, which is provided via `frames`.
		context : Gaffer.Context
		# The list of frames being executed.
		frames : list

	## Emitted prior to spooling the Tractor job, to allow custom modifications to
	# be applied. Slots should have the signature `slot( dispatcher, job, taskData )` :
	#
	# - `dispatcher` : The TractorDispatcher that is about to spool the job.
	# - `job` : The `tractor.api.author.Job` that is about to be spooled.
	#   This may be modified in place.
	# - `taskData` : A dictionary mapping from `tractor.api.author.Task` to
	#   TaskData, specifying the Gaffer tasks that will be executed by each
	#   Tractor task. For example, the Gaffer node for the first Tractor task
	#   can be accessed as `taskData[job.subtasks[0]].plug.node()`.
	@classmethod
	def preSpoolSignal( cls ) :

		return cls.__preSpoolSignal

	__preSpoolSignal = Gaffer.Signals.Signal3()

	def _doDispatch( self, rootBatch ) :

		# If the Tractor API isn't available, issue an informative
		# error.

		try :
			GafferTractor.tractorAPI()
		except ImportError :
			raise RuntimeError( "Tractor API not found. Please ensure the `tractor` Python module is accessible on the `PYTHONPATH`." ) from None

		# Construct an object to track everything we need
		# to generate the job. I have a suspicion that at
		# some point we'll want a Dispatcher::Job base class
		# which _doDispatch() must return, in which case this
		# might just be member data for a subclass of one of those.
		dispatchData = {}
		dispatchData["scriptNode"] = rootBatch.preTasks()[0].node().scriptNode()
		dispatchData["scriptFile"] = Gaffer.Context.current()["dispatcher:scriptFileName"]
		dispatchData["batchesToTasks"] = {}
		dispatchData["taskData"] = {}

		# Create a Tractor job and set its basic properties.

		context = Gaffer.Context.current()

		job = GafferTractor.tractorAPI().Job(
			title = self["jobName"].getValue() or "untitled",
			service = self["service"].getValue(),
			envkey = self["envKey"].getValue().split(),
		)

		# Populate the job with tasks from the batch tree
		# that was prepared by our base class.

		batchesToTasks = {}
		for upstreamBatch in rootBatch.preTasks() :
			self.__buildJobWalk( job, upstreamBatch, dispatchData )

		# Signal anyone who might want to make just-in-time
		# modifications to the job.

		self.preSpoolSignal()( self, job, dispatchData["taskData"] )

		# Save a copy of our job script to the job directory.
		# This isn't strictly necessary because we'll spool via
		# the python API, but it's useful for debugging. Because
		# dispatches can be nested, a file may already exist from
		# the outer dispatcher, in which case we don't overwrite
		# it - the outer job script is sufficient to recreate the
		# whole job if needed.

		with IECore.IgnoredExceptions( FileExistsError ) :
			with open( self.jobDirectory() / "job.alf", "x", encoding = "utf-8" ) as alf :
				alf.write( "# Generated by Gaffer " + Gaffer.About.versionString() + "\n\n" )
				alf.write( job.asTcl() )

		# Finally, we can spool the job.

		job.spool( block = True )

	def __buildJobWalk( self, tractorParent, batch, dispatchData ) :

		task = self.__acquireTask( batch, dispatchData )
		tractorParent.addChild( task )

		if batch.blindData().get( "tractorDispatcher:visited" ) :
			return

		for upstreamBatch in batch.preTasks() :
			self.__buildJobWalk( task, upstreamBatch, dispatchData )

		batch.blindData()["tractorDispatcher:visited"] = IECore.BoolData( True )

	def __acquireTask( self, batch, dispatchData ) :

		# If we've already created a task for this batch, then
		# just return it. The Tractor API will take care of turning
		# it into an Instance if we add it as a subtask of more than
		# one parent.

		task = dispatchData["batchesToTasks"].get( batch )
		if task is not None :
			return task

		# Make a task.

		nodeName = batch.node().relativeName( dispatchData["scriptNode"] )
		task = GafferTractor.tractorAPI().Task( title = nodeName )

		if batch.frames() :

			# Generate a `gaffer execute` command line suitable for
			# executing all the frames in the batch.

			frames = str( IECore.frameListFromList( [ int( x ) for x in batch.frames() ] ) )
			task.title += " " + frames

			args = [
				"gaffer", "execute",
				"-script", dispatchData["scriptFile"],
				"-nodes", nodeName,
				"-frames", frames,
			]

			scriptContext = dispatchData["scriptNode"].context()
			contextArgs = []
			for entry in [ k for k in batch.context().keys() if k != "frame" ] :
				if entry not in scriptContext.keys() or batch.context()[entry] != scriptContext[entry] :
					contextArgs.extend( [ "-" + entry, IECore.repr( batch.context()[entry] ) ] )

			if contextArgs :
				args.extend( [ "-context" ] + contextArgs )

			# Create a Tractor command to execute that command line, and add
			# it to the task.

			command = GafferTractor.tractorAPI().Command( argv = args )
			task.addCommand( command )

			# Apply any custom dispatch settings to the command.

			tractorPlug = batch.node()["dispatcher"].getChild( "tractor" )
			if tractorPlug is not None :
				with Gaffer.Context( batch.context() ) as batchContextWithFrame:
					# tags and services can not be varied per-frame within a batch, but we provide the context variable
					# as a concession to existing production setups that would error without it
					batchContextWithFrame["frame"] = min( batch.frames() )
					command.service = tractorPlug["service"].getValue()
					command.tags = tractorPlug["tags"].getValue().split()

		# Remember the task for next time, and return it.

		dispatchData["batchesToTasks"][batch] = task
		dispatchData["taskData"][task] = self.TaskData(
			batch.plug(), batch.context(), batch.frames()
		)
		return task

	@staticmethod
	def _setupPlugs( parentPlug ) :

		if "tractor" in parentPlug :
			return

		parentPlug["tractor"] = Gaffer.Plug()
		parentPlug["tractor"]["service"] = Gaffer.StringPlug()
		parentPlug["tractor"]["tags"] = Gaffer.StringPlug()

IECore.registerRunTimeTyped( TractorDispatcher, typeName = "GafferTractor::TractorDispatcher" )

GafferDispatch.Dispatcher.registerDispatcher( "Tractor", TractorDispatcher, TractorDispatcher._setupPlugs )
