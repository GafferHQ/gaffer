##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
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

import functools
import collections

import arnold

import IECore
import IECoreArnold

import GafferUI
import GafferArnold

def appendShaders( menuDefinition, prefix="/Arnold" ) :

	MenuItem = collections.namedtuple( "MenuItem", [ "menuPath", "nodeCreator" ] )

	# Build a list of menu items we want to create.

	categorisedMenuItems = []
	uncategorisedMenuItems = []
	with IECoreArnold.UniverseBlock() :

		it = arnold.AiUniverseGetNodeEntryIterator( arnold.AI_NODE_SHADER | arnold.AI_NODE_LIGHT )

		while not arnold.AiNodeEntryIteratorFinished( it ) :

			nodeEntry = arnold.AiNodeEntryIteratorGetNext( it )
			shaderName = arnold.AiNodeEntryGetName( nodeEntry )
			displayName = " ".join( [ IECore.CamelCase.toSpaced( x ) for x in shaderName.split( "_" ) ] )

			category = __aiMetadataGetStr( nodeEntry, "", "gaffer.nodeMenu.category" )
			if category == "" :
				continue

			if arnold.AiNodeEntryGetType( nodeEntry ) == arnold.AI_NODE_SHADER :
				menuPath = "Shader"
				nodeCreator = functools.partial( __shaderCreator, shaderName, GafferArnold.ArnoldShader )
			else :
				menuPath = "Light"
				if shaderName != "mesh_light" :
					nodeCreator = functools.partial( __shaderCreator, shaderName, GafferArnold.ArnoldLight )
				else :
					nodeCreator = GafferArnold.ArnoldMeshLight

			if category :
				menuPath += "/" + category.strip( "/" )
			menuPath += "/" + displayName

			if category :
				categorisedMenuItems.append( MenuItem( menuPath, nodeCreator ) )
			else :
				uncategorisedMenuItems.append( MenuItem( menuPath, nodeCreator ) )

		arnold.AiNodeEntryIteratorDestroy( it )

	# Tidy up uncategorised shaders into a submenu if necessary.

	rootsWithCategories = set( [ m.menuPath.partition( "/" )[0] for m in categorisedMenuItems ] )

	for i, menuItem in enumerate( uncategorisedMenuItems ) :
		s = menuItem.menuPath.split( "/" )
		if s[0] in rootsWithCategories :
			uncategorisedMenuItems[i] = MenuItem( "/".join( [ s[0], "Other", s[1] ] ), menuItem.nodeCreator )

	# Create the actual menu items.

	for menuItem in categorisedMenuItems + uncategorisedMenuItems :
		menuDefinition.append(
			prefix + "/" + menuItem.menuPath,
			{
				"command" : GafferUI.NodeMenu.nodeCreatorWrapper( menuItem.nodeCreator ),
				"searchText" : "ai" + menuItem.menuPath.rpartition( "/" )[2].replace( " ", "" ),
			}
		)

def __shaderCreator( name, nodeType ) :

	shader = nodeType( name )
	shader.loadShader( name )
	return shader

def __aiMetadataGetStr( nodeEntry, paramName, name ) :

	value = arnold.AtString()
	if arnold.AiMetaDataGetStr( nodeEntry, paramName, name, value ) :
		return value.value

	return None
