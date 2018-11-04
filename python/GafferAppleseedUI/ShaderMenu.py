##########################################################################
#
#  Copyright (c) 2018, Esteban Tovagliari. All rights reserved.
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
import glob
import os

import appleseed as asr

import IECore

import GafferOSL
import GafferUI
import GafferSceneUI

def __shaderNodeCreator( shaderName ) :

	node = GafferOSL.OSLShader( shaderName )
	node.loadShader( shaderName )

	return node

def appendShaders( menuDefinition ) :

	# Collect all OSL shaders.

	categorisedMenuItems = {}
	uncategorisedMenuItems = []

	q = asr.ShaderQuery()

	for path in os.environ["APPLESEED_SEARCHPATH"].split( ":" ) :

		for shader in glob.glob( os.path.join( path, "*.oso" ) ) :
			shaderFilename = os.path.basename( shader )

			if shaderFilename.startswith( "as_" ) :

				shaderName = shaderFilename.replace( ".oso", "" )
				category = None
				menuPath = "/Appleseed/Shader"

				q.open( shader )
				shaderMetadata = q.get_metadata()

				if 'as_node_name' in shaderMetadata :
					displayName = shaderMetadata['as_node_name']['value']
				else:
					displayName = " ".join( [ IECore.CamelCase.toSpaced( x ) for x in shaderName.split( "_" ) ] )

				if 'as_category' in shaderMetadata :
					category = shaderMetadata['as_category']['value']
					menuPath += "/" + category.capitalize()

					if not category in categorisedMenuItems :
						categorisedMenuItems[category] = []
				else :
					menuPath += "/Other"

				menuPath += "/" + displayName
				nodeCreator = functools.partial( __shaderNodeCreator, shaderName )

				if category :
					categorisedMenuItems[category].append( ( displayName, menuPath, nodeCreator ) )
				else :
					uncategorisedMenuItems.append( ( displayName, menuPath, nodeCreator ) )

	# Create menu entries.

	for category in categorisedMenuItems :
		shaders = categorisedMenuItems[category]
		shaders.sort()

		for shader in shaders :
			name, menuPath , nodeCreator = shader

			menuDefinition.append(
				menuPath,
				{
					"command" : GafferUI.NodeMenu.nodeCreatorWrapper( nodeCreator ),
					"searchText" : menuPath.rpartition( "/" )[2].replace( " ", "" ),
				}
			)

	uncategorisedMenuItems.sort()

	for shader in uncategorisedMenuItems :
		name, menuPath , nodeCreator = shader

		menuDefinition.append(
			menuPath,
			{
				"command" : GafferUI.NodeMenu.nodeCreatorWrapper( nodeCreator ),
				"searchText" : "as" + menuPath.rpartition( "/" )[2].replace( " ", "" ),
			}
		)
