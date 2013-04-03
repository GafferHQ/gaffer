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

	## Registers a textual description for nodes of the specified type.
	# The description may either be a string or a callable which will compute
	# a description when passed a node instance.
	@classmethod
	def registerNodeDescription( cls, nodeType, description ) :
		
		if isinstance( nodeType, IECore.TypeId ) :
			nodeTypeId = nodeType
		else :
			nodeTypeId = nodeType.staticTypeId()
			
		cls.__nodeDescriptions[nodeTypeId] = description
	
	## Returns a description for the specified node instance.
	@classmethod
	def nodeDescription( cls, node ) :
	
		nodeTypeId = node.typeId()
		while nodeTypeId != IECore.TypeId.Invalid :
			
			description = cls.__nodeDescriptions.get( nodeTypeId, None )
			if description is not None :
				if callable( description ) :
					return description( node )
				else :
					return description
					
			nodeTypeId = IECore.RunTimeTyped.baseTypeId( nodeTypeId )
		
		return ""
		
	## Registers a textual description for the specified plug on nodes of the
	# specified type. The plugPath may be a string optionally containing fnmatch
	# wildcard characters or be a regex for performing more complex matches.
	# The description may either be a string or a callable which will compute
	# a description when passed a node instance.
	@classmethod
	def registerPlugDescription( cls, nodeType, plugPath, stringOrCallable ) :
	
		if isinstance( nodeType, IECore.TypeId ) :
			nodeTypeId = nodeType
		else :
			nodeTypeId = nodeType.staticTypeId()
		
		if isinstance( plugPath, basestring ) :
			plugPath = re.compile( fnmatch.translate( plugPath ) )
		else :
			assert( type( plugPath ) is type( re.compile( "" ) ) )
				
		plugDescriptions = cls.__plugDescriptions.setdefault( nodeTypeId, [] )
		plugDescriptions.insert(
			0,
			IECore.Struct(
				plugPathMatcher = plugPath,
				description = stringOrCallable
			)
		)
	
	## Returns a description for the specified plug instance.
	@classmethod
	def plugDescription( cls, plug ) :
	
		node = plug.node()
		if node is None :
			return ""
			
		plugPath = plug.relativeName( node )
		
		nodeTypeId = node.typeId()
		while nodeTypeId != IECore.TypeId.Invalid :
			plugDescriptions = cls.__plugDescriptions.get( nodeTypeId, None )
			if plugDescriptions is not None :
				for d in plugDescriptions :
					if d.plugPathMatcher.match( plugPath ) :
						if callable( d.description ) :
							return d.description( plug )
						else :
							return d.description
			
			nodeTypeId = IECore.RunTimeTyped.baseTypeId( nodeTypeId )

		return ""
		
	__nodeDescriptions = {}
	__plugDescriptions = {}
