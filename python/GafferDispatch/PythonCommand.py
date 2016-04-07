##########################################################################
#
#  Copyright (c) 2015, John Haddon. All rights reserved.
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

import ast

import IECore

import Gaffer
import GafferDispatch

class PythonCommand( GafferDispatch.ExecutableNode ) :

	def __init__( self, name = "PythonCommand" ) :

		GafferDispatch.ExecutableNode.__init__( self, name )

		# Turn off automatic substitutions for the command, since it's a pain
		# to have to manually escape things, and the context is available
		# directly anyway.
		self["command"] = Gaffer.StringPlug( substitutions = Gaffer.Context.Substitutions.NoSubstitutions )
		self["variables"] = Gaffer.CompoundDataPlug()
		self["sequence"] = Gaffer.BoolPlug()

	def hash( self, context ) :

		h = GafferDispatch.ExecutableNode.hash( self, context )

		command = self["command"].getValue()
		h.append( command )

		parser = _Parser( command )
		for name in parser.contextReads :
			value = context.get( name )
			if isinstance( value, IECore.Object ) :
				value.hash( h )
			else :
				h.append( value )

		self["variables"].hash( h )

		if self.requiresSequenceExecution() :
			h.append( context.getFrame() )

		return h

	def execute( self ) :

		executionDict = self.__executionDict()
		exec( self["command"].getValue(), executionDict, executionDict )

	def executeSequence( self, frames ) :

		if not self.requiresSequenceExecution() :
			## \todo It'd be nice if the dispatcher didn't call
			# executeSequence() if requiresSequenceExecution() was False.
			# At the same time we could look into properly supporting
			# varying results for requiresSequenceExecution(), with sequences
			# going into their own batch independent of non-sequence batches.
			Gaffer.ExecutableNode.executeSequence( self, frames )
			return

		executionDict = self.__executionDict( frames )
		exec( self["command"].getValue(), executionDict, executionDict )

	def requiresSequenceExecution( self ) :

		return self["sequence"].getValue()

	def __executionDict( self, frames = None ) :

		result = {
			"IECore" : IECore,
			"Gaffer" : Gaffer,
			"self" : self,
			"context" : Gaffer.Context.current(),
			"variables" : _VariablesDict(
				self["variables"],
				Gaffer.Context.current(),
				validFrames = set( frames ) if frames is not None else { Gaffer.Context.current().getFrame() }
			)
		}

		if frames is not None :
			result["frames"] = frames

		return result

class _VariablesDict( dict ) :

	def __init__( self, variables, context, validFrames ) :

		dict.__init__( self )

		self.__variables = variables
		self.__context = context
		self.__validFrames = validFrames
		self.__frame = None

	def keys( self ) :

		self.__update()
		return dict.keys( self )

	def __getitem__( self, key ) :

		self.__update()
		return dict.__getitem__( self, key )

	def __update( self ) :

		if self.__frame == self.__context.getFrame() :
			return

		if self.__context.getFrame() not in self.__validFrames :
			raise ValueError( "Invalid frame" )

		self.clear()
		for plug in self.__variables.children() :
			value, name = self.__variables.memberDataAndName( plug )
			if value is None :
				continue
			with IECore.IgnoredExceptions( Exception ) :
				value = value.value

			self[name] = value

		self.__frame = self.__context.getFrame()

class _Parser( ast.NodeVisitor ) :

	def __init__( self, expression ) :

		ast.NodeVisitor.__init__( self )

		self.contextReads = set()

		self.visit( ast.parse( expression ) )

	def visit_Subscript( self, node ) :

		if not isinstance( node.ctx, ast.Load ) or not isinstance( node.value, ast.Name ) :
			return

		if node.value.id != "context" :
			return

		if not isinstance( node.slice, ast.Index ) or not isinstance( node.slice.value, ast.Str ) :
			return

		self.contextReads.add( node.slice.value.s )

	def visit_Call( self, node ) :

		if isinstance( node.func, ast.Attribute ) :
			if isinstance( node.func.value, ast.Name ) :
				if node.func.value.id == "context" :
					# it's a method call on the context
					if node.func.attr == "getFrame" :
						self.contextReads.add( "frame" )
					elif node.func.attr == "getTime" :
						self.contextReads.add( "frame" )
						self.contextReads.add( "framesPerSecond" )
					elif node.func.attr == "getFramesPerSecond" :
						self.contextReads.add( "framesPerSecond" )
					elif node.func.attr == "get" :
						if not isinstance( node.args[0], ast.Str ) :
							raise SyntaxError( "Context name must be a string" )
						self.contextReads.add( node.args[0].s )

		ast.NodeVisitor.generic_visit( self, node )

IECore.registerRunTimeTyped( PythonCommand, typeName = "GafferDispatch::PythonCommand" )
