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
import subprocess

import Gaffer
import IECore

class LocalDispatcher( Gaffer.Dispatcher ) :

	def __init__( self, name = "LocalDispatcher" ) :

		Gaffer.Dispatcher.__init__( self, name )
	
	def jobDirectory( self, context ) :
		
		jobDirectory = Gaffer.Dispatcher.jobDirectory( self, context )
		result = os.path.join( jobDirectory, "%06d" % self.__nextJobId( jobDirectory ) )
		
		while True :
			try :
				os.makedirs( result )
				break
			except OSError, e :
				if e.errno == errno.EEXIST :
					result = os.path.join( jobDirectory, "%06d" % self.__nextJobId( jobDirectory ) )
					continue
				else :
					raise e
		
		return result
	
	def _doDispatch( self, taskDescriptions ) :
		
		script = taskDescriptions[0][0].node.scriptNode()
		if script is None :
			IECore.msg( IECore.MessageHandler.Level.Error, self.getName(), "Can only dispatch nodes which are part of a script." )
			return
		
		context = Gaffer.Context.current()
		scriptFileName = script["fileName"].getValue()
		jobName = context.substitute( self["jobName"].getValue() )
		jobDirectory = self.jobDirectory( context )
		
		messageContext = "%s : Job %s %s" % ( self.getName(), jobName, os.path.basename( jobDirectory ) )
		tmpScript = os.path.join( jobDirectory, os.path.basename( scriptFileName ) if scriptFileName else "untitled.gfr" )
		script.serialiseToFile( tmpScript )
		
		for ( task, requirements ) in taskDescriptions :
			
			frames = str(int(task.context.getFrame()))
			
			cmd = [
				"gaffer", "execute",
				"-script", tmpScript,
				"-nodes", task.node.relativeName( script ),
				"-frames", frames,
			]
			
			contextArgs = []
			for entry in task.context.keys() :
				if entry != "frame" and ( entry not in script.context().keys() or task.context[entry] != script.context()[entry] ) :
					contextArgs.extend( [ "-" + entry, repr(task.context[entry]) ] )
			
			if contextArgs :
				cmd.extend( [ "-context" ] + contextArgs )
			
			IECore.msg( IECore.MessageHandler.Level.Info, messageContext, " ".join( cmd ) )
			result = subprocess.call( cmd )
			if result :
				IECore.msg( IECore.MessageHandler.Level.Error, messageContext, "Failed to execute " + task.node.getName() + " on frames " + frames )
				return
		
		IECore.msg( IECore.MessageHandler.Level.Info, messageContext, "Completed all tasks." )
	
	def _doSetupPlugs( self, parentPlug ) :

		pass
	
	def __nextJobId( self, directory ) :
		
		previousJobs = IECore.ls( directory, minSequenceSize = 1 )
		nextJob = max( previousJobs[0].frameList.asList() ) + 1 if previousJobs else 0
		return nextJob

IECore.registerRunTimeTyped( LocalDispatcher, typeName = "Gaffer::LocalDispatcher" )

Gaffer.Dispatcher.registerDispatcher( "local", LocalDispatcher() )
