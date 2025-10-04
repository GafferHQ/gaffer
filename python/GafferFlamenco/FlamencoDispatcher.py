##########################################################################
#
#  Copyright (c) 2025, John Haddon. All rights reserved.
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
import json
import re
import socket
import sys
import urllib.error
import urllib.request

import IECore

import Gaffer
import GafferDispatch

class FlamencoDispatcher( GafferDispatch.Dispatcher ) :

	def __init__( self, name = "FlamencoDispatcher" ) :

		GafferDispatch.Dispatcher.__init__( self, name )

		self["managerURL"] = Gaffer.StringPlug( defaultValue = "" )
		self["priority"] = Gaffer.IntPlug( defaultValue = 50, minValue = 0 )
		self["workerTag"] = Gaffer.StringPlug()
		self["startPaused"] = Gaffer.BoolPlug()

	ManagerStatus = enum.Enum(
		"ManagerStatus", [
			"NotFound",
			"JobTypeMissing",
			"OK",
		]
	)

	@staticmethod
	def managerStatus( managerURL ) :

		managerURL = managerURL.rstrip( "/" )

		if not managerURL :
			managerURL = FlamencoDispatcher.__discoverManagerURL()
			if managerURL is None :
				result = FlamencoDispatcher.ManagerStatus.NotFound
				result.url = ""
				return result

		try :
			urllib.request.urlopen( f"{managerURL}/api/v3/jobs/type/gaffer" )
			result = FlamencoDispatcher.ManagerStatus.OK
		except urllib.error.HTTPError as e :
			result = FlamencoDispatcher.ManagerStatus.JobTypeMissing
		except :
			result = FlamencoDispatcher.ManagerStatus.NotFound

		result.url = managerURL
		return result

	def _doDispatch( self, rootBatch ) :

		# Connect to the manager and check we have the job type we need.

		managerStatus = self.managerStatus( self["managerURL"].getValue() )
		if managerStatus == self.ManagerStatus.NotFound :
			raise Exception( "Failed to connect to manager." ) from None
		elif managerStatus == self.ManagerStatus.JobTypeMissing :
			raise Exception( "Gaffer job type not installed in manager." ) from None

		# If a worker tag has been requested, then check it exists and translate
		# it from the human readable name to the UUID that Flamenco requires.

		workerTag = self["workerTag"].getValue()
		if workerTag :
			tagRequest = urllib.request.urlopen( f"{managerStatus.url}/api/v3/worker-mgt/tags" )
			allTags = json.loads( tagRequest.read() )
			matchingTag = next( ( t for t in allTags["tags"] if t["name"] == workerTag ), None )
			if matchingTag is None :
				raise Exception( f"Worker tag \"{workerTag}\" does not exist." ) from None
			workerTag = matchingTag["id"]

		# Flamenco doesn't have a generic file format for scripted job
		# submissions. So we just build a simple list of tasks, which our Gaffer
		# job type translates to a Flamenco job during submission.

		batchesToTasks = {}
		for batch in rootBatch.preTasks() :
			self.__buildTasksWalk( batch, batchesToTasks )

		# Submit a job to run the tasks.

		job = {

			"name" : self["jobName"].getValue(),
			"type" : "gaffer",
			"priority" : self["priority"].getValue(),
			"submitter_platform" : sys.platform if sys.platform != "win32" else "windows",
			"settings" : {
				"tasks" : list( batchesToTasks.values() ),
			},

			"worker_tag" : workerTag,
			"initial_status" : "paused" if self["startPaused"].getValue() else "active",

		}

		request = urllib.request.Request( f"{managerStatus.url}/api/v3/jobs" )
		request.add_header( 'Content-Type', 'application/json; charset=utf-8' )

		urllib.request.urlopen( request, json.dumps( job ).encode( "utf-8" ) )

	def __buildTasksWalk( self, batch, batchesToTasks ) :

		# If we've already visited this batch, then return
		# the name of the task we made already.

		task = batchesToTasks.get( batch )
		if task is not None :
			return task["id"]

		# Otherwise make a new task. Start by getting a unique
		# task name.

		task = { "name" : batch.name(), "id" : str( batch.__hash__() ) }
		if batch.frames() :

			# Add a `gaffer execute` command to the task.

			args = [
				"execute",
				"-script", batch.context()["dispatcher:scriptFileName"],
				"-nodes", batch.node().relativeName( batch.node().scriptNode() ),
				"-frames", str( IECore.frameListFromList( [ int( x ) for x in batch.frames() ] ) ),
			]

			scriptContext = batch.node().scriptNode().context()
			contextArgs = []
			for entry in batch.context().keys() :
				if entry not in scriptContext.keys() or batch.context()[entry] != scriptContext[entry] :
					contextArgs.extend( [ "-" + entry, IECore.repr( batch.context()[entry] ) ] )

			if contextArgs :
				args.extend( [ "-context" ] + contextArgs )

			task["commandArgs"] = args

		# Recurse to upstream batches, adding them as dependencies of this task.

		for upstreamBatch in batch.preTasks() :
			task.setdefault( "dependencies", [] ).append( self.__buildTasksWalk( upstreamBatch, batchesToTasks ) )

		batchesToTasks[batch] = task
		return task["id"]

	@staticmethod
	def _setupPlugs( parentPlug ) :

		## \todo Allow task type to be specified
		return

	@staticmethod
	def __discoverManagerURL() :

		broadcastAddress = "239.255.255.250"
		broadcastPort = 1900

		request = (
			"M-SEARCH * HTTP/1.1\r\n"
			f"HOST: {broadcastAddress}:{broadcastPort}\r\n"
			"MAN: \"ssdp:discover\"\r\n"
			"MX: 1\r\n"
			"ST: urn:flamenco:manager:0\r\n"
			"\r\n"
		)

		sock = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )
		sock.settimeout( 3 )

		try :
			sock.sendto( request.encode( "ASCII" ), ( broadcastAddress, broadcastPort ) )
			data, _ = sock.recvfrom( 1024 )
		except TimeoutError :
			return None

		match = re.search( r"LOCATION:\s*(.*)/upnp/description\.xml",  data.decode( "ASCII" ) )
		if match is not None :
			return match.group( 1 )
		else :
			return None

IECore.registerRunTimeTyped( FlamencoDispatcher, typeName = "GafferFlamenco::FlamencoDispatcher" )

GafferDispatch.Dispatcher.registerDispatcher( "Flamenco", FlamencoDispatcher, FlamencoDispatcher._setupPlugs )
