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
import threading

import Gaffer
import IECore

class LocalDispatcher( Gaffer.Dispatcher ) :

	def __init__( self, name = "LocalDispatcher" ) :

		Gaffer.Dispatcher.__init__( self, name )

		backgroundPlug = Gaffer.BoolPlug( "executeInBackground", defaultValue = False )
		self.addChild( backgroundPlug )

	def _doDispatch( self, batch ) :

		script = batch.requirements()[0].node().scriptNode()
		context = Gaffer.Context.current()
		scriptFileName = script["fileName"].getValue()
		jobName = context.substitute( self["jobName"].getValue() )
		jobDirectory = self.jobDirectory()
		messageTitle = "%s : Job %s %s" % ( self.getName(), jobName, os.path.basename( jobDirectory ) )
		tmpScript = os.path.join( jobDirectory, os.path.basename( scriptFileName ) if scriptFileName else "untitled.gfr" )

		script.serialiseToFile( tmpScript )

		if self["executeInBackground"].getValue() :
			self.__preBackgroundDispatch( batch, messageTitle )
			threading.Thread( target = IECore.curry( self.__backgroundDispatch, batch, tmpScript, messageTitle ) ).start()
		else :
			self.__foregroundDispatch( batch, messageTitle )
			IECore.msg( IECore.MessageHandler.Level.Info, messageTitle, "Dispatched all tasks." )

	def __foregroundDispatch( self, batch, messageTitle ) :

		for currentBatch in batch.requirements() :
			self.__foregroundDispatch( currentBatch, messageTitle )

		if not batch.node() or batch.blindData().get( "dispatched" ) :
			return

		script = batch.node().scriptNode()

		description = "executing %s on %s" % ( batch.node().relativeName( script ), str(batch.frames()) )
		IECore.msg( IECore.MessageHandler.Level.Info, messageTitle, description )

		batch.execute()

		batch.blindData()["dispatched"] = IECore.BoolData( True )

	def __preBackgroundDispatch( self, batch, messageTitle ) :

		if batch.node() and batch.node()["dispatcher"]["local"]["executeInForeground"].getValue() :
			self.__foregroundDispatch( batch, messageTitle )
		else :
			for currentBatch in batch.requirements() :
				self.__preBackgroundDispatch( currentBatch, messageTitle )

	def __backgroundDispatch( self, batch, scriptFile, messageTitle ) :

		if batch.blindData().get( "dispatched" ) :
			return

		for currentBatch in batch.requirements() :
			self.__backgroundDispatch( currentBatch, scriptFile, messageTitle )

		if not batch.node() :
			IECore.msg( IECore.MessageHandler.Level.Info, messageTitle, "Dispatched all tasks." )
			return

		script = batch.node().scriptNode()

		if isinstance( batch.node(), Gaffer.TaskList ) :
			IECore.msg( IECore.MessageHandler.Level.Info, messageTitle, "Finished " + batch.node().relativeName( script ) )
			return
		
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

		IECore.msg( IECore.MessageHandler.Level.Info, messageTitle, " ".join( cmd ) )
		result = subprocess.call( cmd )
		if result :
			IECore.msg( IECore.MessageHandler.Level.Error, messageTitle, "Failed to execute " + batch.node().getName() + " on frames " + frames )

		batch.blindData()["dispatched"] = IECore.BoolData( True )

	def _doSetupPlugs( self, parentPlug ) :

		if "local" not in parentPlug :
			localPlug = Gaffer.CompoundPlug( "local" )
			parentPlug.addChild( localPlug )

		parentPlug["local"].clearChildren()

		foregroundPlug = Gaffer.BoolPlug( "executeInForeground", defaultValue = False )
		parentPlug["local"].addChild( foregroundPlug )

IECore.registerRunTimeTyped( LocalDispatcher, typeName = "Gaffer::LocalDispatcher" )

Gaffer.Dispatcher.registerDispatcher( "Local", LocalDispatcher() )
