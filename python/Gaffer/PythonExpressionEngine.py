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

import re
import ast
import functools
import inspect
import imath

import IECore

import Gaffer

class PythonExpressionEngine( Gaffer.Expression.Engine ) :

	def __init__( self ) :

		Gaffer.Expression.Engine.__init__( self )

	def parse( self, node, expression, inPlugs, outPlugs, contextNames ) :

		parser = _Parser( expression )

		self.__expression = expression
		self.__inPlugPaths = list( parser.plugReads )
		self.__outPlugPaths = list( parser.plugWrites )

		inPlugs.extend( [ self.__plug( node, p ) for p in self.__inPlugPaths ] )
		outPlugs.extend( [ self.__plug( node, p ) for p in self.__outPlugPaths ] )
		contextNames.extend( parser.contextReads )

	def execute( self, context, inputs ) :

		plugDict = {}
		for plugPath, plug in zip( self.__inPlugPaths, inputs ) :
			parentDict = plugDict
			plugPathSplit = plugPath.split( "." )
			for p in plugPathSplit[:-1] :
				parentDict = parentDict.setdefault( p, {} )
			if isinstance( plug, Gaffer.CompoundDataPlug ) :
				value = IECore.CompoundData()
				plug.fillCompoundData( value )
			else :
				value = plug.getValue()
			parentDict[plugPathSplit[-1]] = value

		for plugPath in self.__outPlugPaths :
			parentDict = plugDict
			for p in plugPath.split( "." )[:-1] :
				parentDict = parentDict.setdefault( p, {} )

		executionDict = { "imath" : imath, "IECore" : IECore, "parent" : plugDict, "context" : _ContextProxy( context ) }

		exec( self.__expression, executionDict, executionDict )

		result = IECore.ObjectVector()
		for plugPath in self.__outPlugPaths :
			parentDict = plugDict
			plugPathSplit = plugPath.split( "." )
			for p in plugPathSplit[:-1] :
				parentDict = parentDict[p]
			result.append( parentDict.get( plugPathSplit[-1], IECore.NullObject.defaultNullObject() ) )

		return result

	def apply( self, proxyOutput, topLevelProxyOutput, value ) :

		# NullObject signifies that the expression didn't
		# provide a value at all - set the plug to its default.
		if isinstance( value, IECore.NullObject ) :
			proxyOutput.setToDefault()
			return

		value = _extractPlugValue( proxyOutput, topLevelProxyOutput, value )
		if value is None :
			raise TypeError( "Unsupported value type \"%s\"" % type( value ).__name__ )
		else :
			proxyOutput.setValue( value )

	def identifier( self, node, plug ) :

		if node.isAncestorOf( plug ) :
			relativeName = plug.relativeName( node )
		else :
			relativeName = plug.relativeName( node.parent() )

		return 'parent' + "".join( [ '["%s"]' % n for n in relativeName.split( "." ) ] )

	def replace( self, node, expression, oldPlugs, newPlugs ) :

		for oldPlug, newPlug in zip( oldPlugs, newPlugs ) :
			if newPlug is not None :
				replacement = self.identifier( node, newPlug )
			else :
				if oldPlug.direction() == Gaffer.Plug.Direction.In :
					replacement = repr( oldPlug.defaultValue() )
				else :
					replacement = "__disconnected"

			expression = self.__plugRegex( node, oldPlug ).sub(
				replacement, expression
			)

		return expression

	def defaultExpression( self, plug ) :

		# If there's no parent scope, we can't make an expression.
		parentNode = plug.node().ancestor( Gaffer.Node )
		if parentNode is None :
			return ""

		# If we can't extract a value, we can't make an expression.
		if not hasattr( plug, "getValue" ) :
			return ""

		# If we can't store the value in an ObjectVector, we can't
		# return the value in execute().
		value = plug.getValue()
		objectVector = IECore.ObjectVector()
		try :
			objectVector.append( value )
		except :
			return ""

		# If we can't extract the appropriate value for every leaf
		# plug, we can't apply the value after execution.

		def canExtractValue( plug, topLevelPlug, value ) :

			if not len( plug ) :
				# no children - must be able to extract
				# a value for use in apply.
				return _extractPlugValue( plug, topLevelPlug, value ) is not None
			else :
				# compound plug - check all children.
				for child in plug.children() :
					if not canExtractValue( child, topLevelPlug, value ) :
						return False

				return True

		if not canExtractValue( plug, plug, objectVector[0] ) :
			return ""

		# Looks like we can support this plug, so make and return
		# a suitable expression.

		result = ""

		modulePath = Gaffer.Serialisation.modulePath( value )
		if modulePath not in ( "IECore", "" ) :
			result += "import " + modulePath + "\n\n"

		result += "parent[\""
		result += plug.relativeName( parentNode ).replace( ".", "\"][\"" )
		result += "\"] = "

		result += IECore.repr( value )

		return result

	def __plug( self, node, plugPath ) :

		plug = node.parent().descendant( plugPath )
		if isinstance( plug, Gaffer.ValuePlug ) :
			return plug

		if plug is None :
			raise RuntimeError( "\"%s\" does not exist" % plugPath )
		else :
			raise RuntimeError( "\"%s\" is not a ValuePlug" % plugPath )

	def __plugRegex( self, node, plug ) :

		identifier = self.identifier( node, plug )
		regex = identifier.replace( "[", r"\[" )
		regex = regex.replace( "]", r"\]" )
		regex = regex.replace( '"', "['\"']" )

		return re.compile( regex )

Gaffer.Expression.Engine.registerEngine( "python", PythonExpressionEngine )

##########################################################################
# Parser. This is used to figure out what plugs an expression wants
# to read from and write to, and what context variables it wants to read.
##########################################################################

class _Parser( ast.NodeVisitor ) :

	def __init__( self, expression ) :

		ast.NodeVisitor.__init__( self )

		self.plugWrites = set()
		self.plugReads = set()
		self.contextReads = set()

		self.visit( ast.parse( expression ) )

	def visit_Assign( self, node ) :

		if len( node.targets ) == 1 :
			if isinstance( node.targets[0], ast.Subscript ) :
				plugPath = self.__plugPath( self.__path( node.targets[0] ) )
				if plugPath :
					self.plugWrites.add( plugPath )

		self.visit( node.value )

	def visit_Subscript( self, node ) :

		if isinstance( node.ctx, ast.Load ) :
			path = self.__path( node )
			plugPath = self.__plugPath( path )
			if plugPath :
				self.plugReads.add( plugPath )
			else :
				contextName = self.__contextName( path )
				if contextName :
					self.contextReads.add( contextName )

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

	def visit_Compare( self, node ) :

		ast.NodeVisitor.generic_visit( self, node )

		# Look for `"x" in context` and `"x" not in context`

		if not isinstance( node.ops[0], ( ast.In, ast.NotIn ) ) :
			return

		if not isinstance( node.comparators[0], ast.Name ) :
			return

		if node.comparators[0].id != "context" :
			return

		if not isinstance( node.left, ast.Str ) :
			raise SyntaxError( "Context name must be a string" )

		self.contextReads.add( node.left.s )

	def __path( self, node ) :

		result = []
		while node is not None :
			if isinstance( node, ast.Subscript ) :
				if isinstance( node.slice, ast.Index ) :
					if isinstance( node.slice.value, ast.Str ) :
						result.insert( 0, node.slice.value.s )
					else :
						return []
				node = node.value
			elif isinstance( node, ast.Name ) :
				result.insert( 0, node.id )
				node = None
			else :
				return []

		return result

	def __plugPath( self, path ) :

		if len( path ) < 2 or path[0] != "parent" :
			return ""
		else :
			return ".".join( path[1:] )

	def __contextName( self, path ) :

		if len( path ) !=2 or path[0] != "context" :
			return ""
		else :
			return path[1]

##########################################################################
# Functions for setting plug values.
##########################################################################

def __typedPlugValueExtractor( plug, topLevelPlug, value, converter = None ) :

	if converter is not None :
		return converter( value.value )
	else :
		return value.value

def __compoundNumericPlugValueExtractor( plug, topLevelPlug, value ) :

	index = topLevelPlug.children().index( plug )
	return value.value[index]

def __boxPlugValueExtractor( plug, topLevelPlug, value ) :

	vectorPlug = plug.parent()
	index = vectorPlug.children().index( plug )

	vector = value.value.min() if vectorPlug.getName() == "min" else value.value.max()

	return vector[index]

def __defaultValueExtractor( plug, topLevelPlug, value ) :

	with IECore.IgnoredExceptions( AttributeError ) :
		value = value.value

	# Deal with the simple atomic plug case.
	if plug.isSame( topLevelPlug ) :
		return value

	# Plug must be a child of a compound of
	# some sort. We need to try to extract
	# the right part of the compound value.
	for name in plug.relativeName( topLevelPlug ).split( "." ) :
		try :
			value = getattr( value, name )
			if inspect.ismethod( value ) :
				value = value()
		except AttributeError :
			accessor = getattr( value, "get" + name[0].upper() + name[1:], None )
			if accessor is not None :
				value = accessor()
			else :
				return None

	return value

_valueExtractors = {
	Gaffer.IntPlug : functools.partial( __typedPlugValueExtractor, converter = int ),
	Gaffer.FloatPlug : __typedPlugValueExtractor,
	Gaffer.StringPlug : __typedPlugValueExtractor,
	Gaffer.BoolPlug : __typedPlugValueExtractor,
	Gaffer.V2fPlug : __compoundNumericPlugValueExtractor,
	Gaffer.V2iPlug : __compoundNumericPlugValueExtractor,
	Gaffer.V3fPlug : __compoundNumericPlugValueExtractor,
	Gaffer.V3iPlug : __compoundNumericPlugValueExtractor,
	Gaffer.Color3fPlug : __compoundNumericPlugValueExtractor,
	Gaffer.Color4fPlug : __compoundNumericPlugValueExtractor,
	Gaffer.Box2fPlug : __boxPlugValueExtractor,
	Gaffer.Box2iPlug : __boxPlugValueExtractor,
	Gaffer.Box3fPlug : __boxPlugValueExtractor,
	Gaffer.Box3iPlug : __boxPlugValueExtractor,
}

def _extractPlugValue( plug, topLevelPlug, value ) :

	return _valueExtractors.get( type( topLevelPlug ), __defaultValueExtractor )( plug, topLevelPlug, value )

##########################################################################
# _ContextProxy
##########################################################################

class _ContextProxy( object ) :

	__whitelist = { "get", "getFrame", "getFramesPerSecond", "getTime", "canceller" }

	def __init__( self, context ) :

		self.__context = context

	def __getitem__( self, key ) :

		return self.__context[key]

	def __contains__( self, key ) :

		return key in self.__context

	def __getattr__( self, name ) :

		if name in self.__whitelist :
			return getattr( self.__context, name )
		else :
			raise AttributeError( name )

