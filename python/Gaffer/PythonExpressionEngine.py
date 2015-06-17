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

import ast

import IECore

import Gaffer

class PythonExpressionEngine( Gaffer.Expression.Engine ) :

	def __init__( self, expression ) :

		Gaffer.Expression.Engine.__init__( self )

		self.__expression = expression

		parser = _Parser( expression )
		if not parser.plugWrites :
			raise Exception( "Expression does not write to a plug" )

		self.__inPlugs = list( parser.plugReads )
		self.__outPlugs = list( parser.plugWrites )
		self.__contextNames = list( parser.contextReads )

	def outPlugs( self ) :

		return self.__outPlugs

	def inPlugs( self ) :

		return self.__inPlugs

	def contextNames( self ) :

		return self.__contextNames

	def execute( self, context, inputs ) :

		plugDict = {}
		for plugPath, plug in zip( self.__inPlugs, inputs ) :
			parentDict = plugDict
			plugPathSplit = plugPath.split( "." )
			for p in plugPathSplit[:-1] :
				parentDict = parentDict.setdefault( p, {} )
			parentDict[plugPathSplit[-1]] = plug.getValue()

		for plugPath in self.__outPlugs :
			parentDict = plugDict
			for p in plugPath.split( "." )[:-1] :
				parentDict = parentDict.setdefault( p, {} )

		executionDict = { "IECore" : IECore, "parent" : plugDict, "context" : context }

		exec( self.__expression, executionDict, executionDict )

		result = IECore.ObjectVector()
		for plugPath in self.__outPlugs :
			parentDict = plugDict
			plugPathSplit = plugPath.split( "." )
			for p in plugPathSplit[:-1] :
				parentDict = parentDict[p]
			result.append( parentDict.get( plugPathSplit[-1], IECore.NullObject.defaultNullObject() ) )

		return result

	def setPlugValue( self, plug, value ) :

		_setPlugValue( plug, value )

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
					elif node.func.attr == "get" :
						if not isinstance( node.args[0], ast.Str ) :
							raise SyntaxError( "Context name must be a string" )
						self.contextReads.add( node.args[0].s )

		ast.NodeVisitor.generic_visit( self, node )

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

def __simpleTypedDataSetter( plug, value ) :

	plug.setValue( value.value )

def __compoundNumericDataSetter( plug, value ) :

	index = plug.parent().children().index( plug )
	plug.setValue( value.value[index] )

def __boxDataSetter( plug, value ) :

	value = value.value

	vectorPlug = plug.parent()
	boxPlug = vectorPlug.parent()

	vector = value.min if vectorPlug.getName() == "min" else value.max
	index = vectorPlug.children().index( plug )

	plug.setValue( vector[index] )

def __nullObjectSetter( plug, value ) :

	# NullObject signifies that the expression didn't
	# provide a value at all - set the plug to its default.
	plug.setToDefault()

def __defaultSetter( plug, value ) :

	plug.setValue( value )

_setters = {
	IECore.IntData : __simpleTypedDataSetter,
	IECore.FloatData : __simpleTypedDataSetter,
	IECore.StringData : __simpleTypedDataSetter,
	IECore.BoolData : __simpleTypedDataSetter,
	IECore.V2fData : __compoundNumericDataSetter,
	IECore.V2iData : __compoundNumericDataSetter,
	IECore.V3fData : __compoundNumericDataSetter,
	IECore.V3iData : __compoundNumericDataSetter,
	IECore.Color3fData : __compoundNumericDataSetter,
	IECore.Color4fData : __compoundNumericDataSetter,
	IECore.Box2fData : __boxDataSetter,
	IECore.Box2iData : __boxDataSetter,
	IECore.Box3fData : __boxDataSetter,
	IECore.Box3iData : __boxDataSetter,
	IECore.NullObject : __nullObjectSetter,
}

def _setPlugValue( plug, value ) :

	_setters.get( type( value ), __defaultSetter )( plug, value )