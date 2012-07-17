##########################################################################
#  
#  Copyright (c) 2012, John Haddon. All rights reserved.
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

import Gaffer

class PythonExpressionEngine( Gaffer.ExpressionNode.Engine ) :

	def __init__( self, expression ) :
	
		Gaffer.ExpressionNode.Engine.__init__( self )
		
		self.__expression = expression
		
		parser = _Parser( expression )
		if not parser.plugWrites :
			raise Exception( "Expression does not write to a plug" )
		elif len( parser.plugWrites ) > 1 :
			raise Exception( "Expression may only write to a single plug" )
		
		self.__inPlugs = parser.plugReads
		self.__outPlug = parser.plugWrites[0]
	
	def outPlug( self ) :
	
		return self.__outPlug
		
	def inPlugs( self ) :
	
		return self.__inPlugs
		
	def execute( self, context, inputs, output ) :
	
		plugDict = {}
		for plugPath, plug in zip( self.__inPlugs, inputs ) :
			parentDict = plugDict
			plugPathSplit = plugPath.split( "." )
			for p in plugPathSplit[:-1] :
				parentDict = parentDict.setdefault( p, {} )
			parentDict[plugPathSplit[-1]] = plug.getValue()
		
		outputPlugPathSplit = self.__outPlug.split( "." )
		outputPlugDict = plugDict
		for p in outputPlugPathSplit[:-1] :
			outputPlugDict = outputPlugDict.setdefault( p, {} )
			
		executionDict = { "parent" : plugDict, "context" : context }
				
		exec( self.__expression, executionDict, executionDict )
		
		output.setValue( outputPlugDict[outputPlugPathSplit[-1]] )
	
class _Parser( ast.NodeVisitor ) :

	def __init__( self, expression ) :
	
		ast.NodeVisitor.__init__( self )

		self.plugWrites = []
		self.plugReads = []
		
		self.visit( ast.parse( expression ) )
		
	def visit_Assign( self, node ) :
	
		if len( node.targets ) == 1 :
			if isinstance( node.targets[0], ast.Subscript ) :
				plugPath = self.__plugPath( node.targets[0] )
				if plugPath :
					self.plugWrites.append( plugPath )
		
		self.visit( node.value )
		
	def visit_Subscript( self, node ) :
	
		if isinstance( node.ctx, ast.Load ) :
			plugPath = self.__plugPath( node )
			if plugPath :
				self.plugReads.append( plugPath )
			
	def __plugPath( self, node ) :
	
		path = []
		while node is not None :
			if isinstance( node, ast.Subscript ) :
				if isinstance( node.slice, ast.Index ) :
					if isinstance( node.slice.value, ast.Str ) :
						path.insert( 0, node.slice.value.s )
					else :
						return ""
				node = node.value
			elif isinstance( node, ast.Name ) :
				path.insert( 0, node.id )
				node = None
			else :
				return ""

		if path[0] != "parent" or len( path ) < 2 :
			return ""
		else :
			return ".".join( path[1:] )
		
Gaffer.ExpressionNode.Engine.registerEngine( "python", PythonExpressionEngine )
