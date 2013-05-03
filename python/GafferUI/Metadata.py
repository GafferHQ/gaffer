##########################################################################
#  
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
import fnmatch

import IECore

import Gaffer

## The Metadata class provides a registry of metadata for the different types
# of Nodes and Plugs. This metadata assists in creating UIs and can be used to
# generate documentation.
class Metadata :

	## Registers a named value associated with a particular node type. The
	# value may optionally be a callable taking a node instance - this defers the
	# computation of the value until it is looked up with nodeValue().
	@classmethod
	def registerNodeValue( cls, nodeType, key, value ) :

		if isinstance( nodeType, IECore.TypeId ) :
			nodeTypeId = nodeType
		else :
			nodeTypeId = nodeType.staticTypeId()
	
		nodeValues = cls.__nodeValues.setdefault( nodeTypeId, {} )
		nodeValues[key] = value
	
	## Looks up a previously registered value for the specified
	# Node instance. Returns None if no such value is found.
	@classmethod
	def nodeValue( cls, nodeInstance, key, inherit=True ) :
		
		typeIds = [ nodeInstance.typeId() ]
		if inherit :
			typeIds += IECore.RunTimeTyped.baseTypeIds( nodeInstance.typeId() )
	
		for nodeTypeId in typeIds :
			
			values = cls.__nodeValues.get( nodeTypeId, None )
			if values is not None :
				value = values.get( key, None )
				if value is not None :
					if callable( value ) :
						return value( nodeInstance )
					else :
						return value

		return None
		
	## Registers a textual description for nodes of the specified type,
	# along with optional metadata for each plug. This is merely a convenience
	# function which calls registerNodeValue() and registerPlugValue() behind
	# the scenes. The additional arguments are paired up and passed to calls to
	# registerPlugValue(). The value in each pair may either be a string in
	# which case it is registered as the plug description, or a dictionary in
	# which case it is used to generate multiple calls to registerPlugValue().
	@classmethod
	def registerNodeDescription( cls, nodeType, description, *args ) :

		assert( ( len( args ) % 2 ) == 0 )

		cls.registerNodeValue( nodeType, "description", description )

		for i in range( 0, len( args ), 2 ) :

			plugPath = args[i]
			assert( " " not in plugPath )
			if isinstance( args[i+1], basestring ) :
				cls.registerPlugDescription( nodeType, plugPath, args[i+1] )
			else :
				for key, value in args[i+1].items() :
					cls.registerPlugValue( nodeType, plugPath, key, value )

	## Returns a description for the specified node instance. This is just
	# a convenience returning nodeValue( node, "description" ), or the
	# empty string if no description has been registered.
	@classmethod
	def nodeDescription( cls, nodeInstance, inherit=True ) :

		return cls.nodeValue( nodeInstance, "description", inherit ) or ""
	
	## Registers a named value associated with particular plugs on a particular
	# node type. The plugPath may be a string optionally containing fnmatch
	# wildcard characters or be a regex for performing more complex matches.
	# The value may optionally be a callable taking a plug instance - this defers
	# the computation of the value until it is looked up with plugValue().
	@classmethod
	def registerPlugValue( cls, nodeType, plugPath, key, value ) :

		if isinstance( nodeType, IECore.TypeId ) :
			nodeTypeId = nodeType
		else :
			nodeTypeId = nodeType.staticTypeId()

		if isinstance( plugPath, basestring ) :
			plugPath = re.compile( fnmatch.translate( plugPath ) )
		else :
			assert( type( plugPath ) is type( re.compile( "" ) ) )

		nodeValues = cls.__nodeValues.setdefault( nodeTypeId, {} )
		plugValuesContainer = nodeValues.setdefault( "__plugValues", {} )
		plugValues = plugValuesContainer.setdefault( plugPath, {} )
		plugValues[key] = value
	
	## Looks up a previously registered value for the specified
	# Plug instance. Returns None if no such value is found.
	@classmethod
	def plugValue( cls, plugInstance, key, inherit=True ) :
	
		node = plugInstance.node()
		if node is None :
			return None
			
		plugPath = plugInstance.relativeName( node )
		
		typeIds = [ node.typeId() ]
		if inherit :
			typeIds += IECore.RunTimeTyped.baseTypeIds( node.typeId() )
	
		for nodeTypeId in typeIds :

			nodeValues = cls.__nodeValues.get( nodeTypeId, None )
			if nodeValues is not None :
				plugValuesContainer = nodeValues.get( "__plugValues", {} )
				for plugPathRegex, plugValues in plugValuesContainer.items() :
					if plugPathRegex.match( plugPath ) :
						plugValue = plugValues.get( key, None )
						if plugValue is not None :
							if callable( plugValue ) :
								return plugValue( plugInstance )
							else :
								return plugValue
			
		return None

	## Registers a textual description for the specified plug on nodes of the
	# specified type. The plugPath may be a string optionally containing fnmatch
	# wildcard characters or be a regex for performing more complex matches.
	# The description may either be a string or a callable which will compute
	# a description when passed a node instance.
	@classmethod
	def registerPlugDescription( cls, nodeType, plugPath, description ) :

		cls.registerPlugValue( nodeType, plugPath, "description", description )

	## Returns a description for the specified plug instance. This is just
	# a convenience returning plugValue( plug, "description" ), or the
	# empty string if no description has been registered.
	@classmethod
	def plugDescription( cls, plugInstance, inherit=True ) :

		return cls.plugValue( plugInstance, "description", inherit ) or ""
		
	__nodeValues = {}
