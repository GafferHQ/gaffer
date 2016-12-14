##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

from __future__ import with_statement

import sys

import IECore

import Gaffer
import GafferScene

class ScriptProcedural( IECore.ParameterisedProcedural ) :

	def __init__( self ) :

		IECore.ParameterisedProcedural.__init__( self, "Generates geometry from a node within a .gfr script." )

		self.parameters().addParameters(

			[

				IECore.FileNameParameter(
					name = "fileName",
					description = "The gaffer script which contains a scene to generate geometry from.",
					allowEmptyString = False,
					check = IECore.FileNameParameter.CheckType.MustExist,
					extensions = "gfr",
				),

				IECore.StringParameter(
					name = "node",
					description = "The node to generate geometry from.",
					defaultValue = "",
				),

				IECore.FloatParameter(
					name = "frame",
					description = "The frame to generate geometry at.",
					defaultValue = 1,
				),

				IECore.BoolParameter(
					name = "computeBound",
					description =
						"Determines if the procedural will compute an accurate bound "
						"or just not specify a bound. Not specifying a bound can give "
						"improved performance in cases where the procedurals will all "
						"be expanded immediately anyway.",
					defaultValue = True,
				),

				IECore.StringVectorParameter(
					name = "context",
					description = "Additional context entries to be used during rendering.",
					defaultValue = IECore.StringVectorData( [] ),
					userData = {
						"parser" : {
							"acceptFlags" : IECore.BoolData( True ),
						},
					},
				),

			]

		)

		self.__currentFileName = None
		self.__ensureAllRenderedConnection()

	def doBound( self, args ) :

		plug, context = self.__plugAndContext( args )
		if plug is  None :
			return IECore.Box3f()

		sceneProcedural = GafferScene.SceneProcedural( plug, context, "/", args["computeBound"].value )
		return sceneProcedural.bound()

	def doRender( self, renderer, args ) :

		plug, context = self.__plugAndContext( args )
		if plug is None :
			return

		sceneProcedural = GafferScene.SceneProcedural( plug, context, "/", args["computeBound"].value )
		renderer.procedural( sceneProcedural )

	def __plugAndContext( self, args ) :

		if args["fileName"].value != self.__currentFileName :

			if args["fileName"].value == "" :
				self.__scriptNode = None
			else :
				self.__scriptNode = Gaffer.ScriptNode()
				self.__scriptNode["fileName"].setValue( args["fileName"].value )
				self.__scriptNode.load( continueOnError = True )
				self.__currentFileName = args["fileName"].value

		if self.__scriptNode is None :
			return None, None

		if not args["node"].value :
			return None, None

		node = self.__scriptNode.descendant( args["node"].value )

		context = Gaffer.Context( self.__scriptNode.context() )
		context.setFrame( args["frame"].value )

		for i in range( 0, len(args["context"]), 2 ) :
			entry = args["context"][i].lstrip( "-" )
			context[entry] = eval( args["context"][i+1] )

		self.__ensureErrorConnection( node )

		with context :
			globals = node["out"]["globals"].getValue()
		if "option:render:performanceMonitor" in globals and globals["option:render:performanceMonitor"].value :
			self.__ensurePerformanceMonitor()

		return node["out"], context

	__allRenderedConnection = None
	@classmethod
	def __ensureAllRenderedConnection( cls ) :

		if cls.__allRenderedConnection is not None :
			return

		cls.__allRenderedConnection = GafferScene.SceneProcedural.allRenderedSignal().connect( cls.__allRendered )

	@classmethod
	def __allRendered( cls ):

		if cls.__performanceMonitor is not None :
			cls.__printPerformance()

		# All the procedural expansion's done, so let's clear various Cortex/Gaffer
		# caches to free up some memory.

		IECore.ObjectPool.defaultObjectPool().clear()
		memoryLimit = Gaffer.ValuePlug.getCacheMemoryLimit()
		Gaffer.ValuePlug.setCacheMemoryLimit( 0 )
		Gaffer.ValuePlug.setCacheMemoryLimit( memoryLimit )

	__errorConnections = {}
	@classmethod
	def __ensureErrorConnection( cls, node ) :

		if node in cls.__errorConnections :
			return

		cls.__errorConnections[node] = node.errorSignal().connect( cls.__error )

	@staticmethod
	def __error( plug, source, error ) :

		errorContext = "Plug \"%s\"" % source.relativeName( source.ancestor( Gaffer.ScriptNode ) )
		if "scene:path" in Gaffer.Context.current() :
			path = GafferScene.ScenePlug.pathToString( Gaffer.Context.current()["scene:path"] )
			errorContext += ", Location \"%s\"" % path

		IECore.msg(
			IECore.Msg.Level.Error,
			errorContext,
			error
		)

	__performanceMonitor = None
	@classmethod
	def __ensurePerformanceMonitor( cls ) :

		if cls.__performanceMonitor is not None :
			return

		cls.__performanceMonitor = Gaffer.PerformanceMonitor()
		cls.__performanceMonitor.setActive( True )

	@classmethod
	def __printPerformance( cls ) :

		sys.stderr.write( "\nPerformance Monitor\n===================\n\n" )

		sys.stderr.write( Gaffer.MonitorAlgo.formatStatistics( cls.__performanceMonitor ) )

IECore.registerRunTimeTyped( ScriptProcedural, typeName = "GafferScene::ScriptProcedural" )
