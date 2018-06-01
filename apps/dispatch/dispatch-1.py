##########################################################################
#
#  Copyright (c) 2018, Image Engine Design Inc. All rights reserved.
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

import os, sys, traceback

import IECore

import Gaffer
import GafferDispatch

class dispatch( Gaffer.Application ) :

	def __init__( self ) :

		Gaffer.Application.__init__(
			self,
			"""
			Dispatches task nodes such as ImageWriters, SystemCommands and Render nodes,
			either from within an existing .gfr file or by creating a script on the fly.
			This differs from the execute app in that it performs a full dispatch via a
			dispatcher, rather than executing a single task node.

			Example usage :

			```
			gaffer dispatch -script comp.gfr -nodes ImageWriter -dispatcher Local -settings -dispatcher.executeInBackground 1

			gaffer dispatch -gui -nodes GafferDispatch.SystemCommand -dispatcher Local -settings -SystemCommand.command "ls -l"
			```
			"""
		)

		self.parameters().addParameters(

			[
				IECore.BoolParameter(
					name = "gui",
					description = "Determines whether a gui is presented prior to dispatching or the "
						"tasks are dispatched directly.",
					defaultValue = False,
				),

				IECore.FileNameParameter(
					name = "script",
					description = "An optional script containing the task network to be dispatched.",
					defaultValue = "",
					allowEmptyString = True,
					extensions = "gfr",
					check = IECore.FileNameParameter.CheckType.MustExist,
				),

				IECore.BoolParameter(
					name = "ignoreScriptLoadErrors",
					description = "Causes errors which occur while loading the script "
						"to be ignored. Not recommended.",
					defaultValue = False,
				),

				IECore.BoolParameter(
					name = "applyUserDefaults",
					description = "Applies userDefault values to all nodes and plugs created by the app, "
						"including the dispatchers. Note if a script is supplied, the nodes will be unaffected.",
					defaultValue = False,
				),

				IECore.StringVectorParameter(
					name = "nodes",
					description = "The names of the nodes to dispatch. Note if a script is supplied, the nodes must "
						"exist within the script. If no script is supplied, the nodes will be constructed on the fly "
						"and added to a default script.",
					defaultValue = IECore.StringVectorData( [] ),
				),

				IECore.StringParameter(
					name = "dispatcher",
					description = "The type of dispatcher to use for the dispatch. A new dispatcher "
						"of this type will be created, with userDefaults applied.",
					defaultValue = "",
				),

				IECore.StringVectorParameter(
					name = "settings",
					description = "The values to be set on the nodes, dispatcher, or context. Values "
						"should be in the format -nodeA.plugA value -nodeA.plugB value -nodeB.plugC value "
						"-dispatcher.plugD value -context.entry value",
					defaultValue = IECore.StringVectorData( [] ),
					userData = {
						"parser" : {
							"acceptFlags" : IECore.BoolData( True ),
						},
					},
				),

			]

		)

	def _run( self, args ) :

		nodes = []
		if not len( args["nodes"] ) :
			IECore.msg( IECore.Msg.Level.Error, "gaffer dispatch", "No nodes were specified" )
			return 1

		script = Gaffer.ScriptNode()

		if args["script"].value :
			script["fileName"].setValue( os.path.abspath( args["script"].value ) )
			try :
				script.load( continueOnError = args["ignoreScriptLoadErrors"].value )
			except Exception as exception :
				IECore.msg( IECore.Msg.Level.Error, "gaffer dispatch : loading \"%s\"" % script["fileName"].getValue(), str( exception ) )
				return 1

		self.root()["scripts"].addChild( script )

		for nodeName in args["nodes"] :
			if args["script"].value :
				node = script.descendant( nodeName )
				if node is None :
					IECore.msg( IECore.Msg.Level.Error, "gaffer dispatch", "\"%s\" does not exist." % nodeName )
					return 1
			else :
				node = self.__create( nodeName )
				if args["applyUserDefaults"].value :
					Gaffer.NodeAlgo.applyUserDefaults( node )
				script.addChild( node )
			nodes.append( node )

		dispatcherType = args["dispatcher"].value or GafferDispatch.Dispatcher.getDefaultDispatcherType()
		dispatcher = GafferDispatch.Dispatcher.create( dispatcherType )
		if not dispatcher :
			IECore.msg( IECore.Msg.Level.Error, "gaffer dispatch", "{} is not a registered dispatcher.".format( dispatcherType ) )
			return 1

		Gaffer.NodeAlgo.applyUserDefaults( dispatcher )

		if len(args["settings"]) % 2 :
			IECore.msg( IECore.Msg.Level.Error, "gaffer dispatch", "\"settings\" parameter must have matching entry/value pairs" )
			return 1

		for i in range( 0, len(args["settings"]), 2 ) :
			key = args["settings"][i].lstrip( "-" )
			value = args["settings"][i+1]
			if key.startswith( "context." ) :
				entry = key.partition( "context." )[-1]
				status = self.__setValue( entry, value, script, context=True )
			elif key.startswith( "dispatcher." ) :
				identifier = key.partition( "dispatcher." )[-1]
				status = self.__setValue( identifier, value, dispatcher )
			else :
				status = self.__setValue( key, value, script )
			if status :
					return status

		if args["gui"].value :

			import GafferUI
			import GafferDispatchUI

			self.__dialogue = GafferDispatchUI.DispatchDialogue( nodes, [ dispatcher ] )
			self.__dialogueClosedConnection = self.__dialogue.closedSignal().connect( Gaffer.WeakMethod( self.__dialogueClosed ) )
			self.__dialogue.setVisible( True )

			GafferUI.EventLoop.mainEventLoop().start()

		else :

			return self.__dispatch( dispatcher, nodes )

		return 0

	@staticmethod
	def __dispatch( dispatcher, nodes ) :

		script = nodes[0].scriptNode()

		try :

			with script.context() :
				dispatcher.dispatch( nodes )

		except Exception :

			IECore.msg(
				IECore.Msg.Level.Error,
				"gaffer dispatch : dispatching %s" % str( [ node.relativeName( script ) for node in nodes ] ),
				"".join( traceback.format_exception( *sys.exc_info() ) ),
			)

			return 1

		return 0

	def __dialogueClosed( self, dialogue ) :

		import GafferUI

		GafferUI.EventLoop.mainEventLoop().stop()

	@staticmethod
	def __setValue( identifier, value, parent, context=False ) :

		if context :
			parent["variables"].addMember( identifier, eval( value ) )
			return 0

		plug = parent.descendant( identifier )
		if not plug :
			IECore.msg( IECore.Msg.Level.Error, "gaffer dispatch", "\"%s\" does not contain a plug named \"%s\"." % ( parent.getName(), identifier ) )
			return 1
		if not plug.settable() :
			IECore.msg( IECore.Msg.Level.Error, "gaffer dispatch", "\"%s\" cannot be set." % identifier )
			return 1

		try :
			plug.setValue( eval( value ) )
		except Exception as exception :
			IECore.msg( IECore.Msg.Level.Error, "gaffer dispatch : setting \"%s\"" % identifier, str( exception ) )
			return 1

		return 0

	@staticmethod
	def __create( path ) :

		path = path.split( "." )
		result = __import__( path[0] )
		for n in path[1:] :
			result = getattr( result, n )

		return result()

IECore.registerRunTimeTyped( dispatch )
