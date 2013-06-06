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

import os
import re
import fnmatch
import string

import IECore
import IECoreRI

import GafferUI

import GafferRenderMan

def __shaderCreator( shaderName ) :

	nodeName = os.path.split( shaderName )[-1]
	nodeName = nodeName.translate( string.maketrans( ".-", "__" ) )

	shader = GafferRenderMan.RenderManShader.shaderLoader().read( shaderName + ".sdl" )
	if shader.type == "light" :
		node = GafferRenderMan.RenderManLight( nodeName )
	else :
		node = GafferRenderMan.RenderManShader( nodeName )
	
	node.loadShader( shaderName )
	
	return node

def _shaderSubMenu( matchExpression = re.compile( ".*" ) ) :
	
	if isinstance( matchExpression, str ) :
		matchExpression = re.compile( fnmatch.translate( matchExpression ) )
	
	shaders = set()
	for path in GafferRenderMan.RenderManShader.shaderLoader().searchPath.paths :

		for root, dirs, files in os.walk( path ) :
			for file in files :
				if os.path.splitext( file )[1] == ".sdl" :
					shaderPath = os.path.join( root, file ).partition( path )[-1].lstrip( "/" )
					if shaderPath not in shaders and matchExpression.match( shaderPath ) :
						shaders.add( os.path.splitext( shaderPath )[0] )
	
	shaders = sorted( list( shaders ) )
	categorisedShaders = [ x for x in shaders if "/" in x ]
	uncategorisedShaders = [ x for x in shaders if "/" not in x ]
	
	shadersAndMenuPaths = []
	for shader in categorisedShaders :
		shadersAndMenuPaths.append( ( shader, "/" + shader ) )
			
	for shader in uncategorisedShaders :
		if not categorisedShaders :
			shadersAndMenuPaths.append( ( shader, "/" + shader ) )
		else :
			shadersAndMenuPaths.append( ( shader, "/Other/" + shader ) )

	result = IECore.MenuDefinition()
	for shader, menuPath in shadersAndMenuPaths :
		result.append(
			menuPath,
			{
				"command" : GafferUI.NodeMenu.nodeCreatorWrapper( IECore.curry( __shaderCreator, shader ) )
			}
		)
		
	return result

GafferUI.NodeMenu.definition().append( "/RenderMan/Shader", { "subMenu" : _shaderSubMenu } )

GafferUI.NodeMenu.append( "/RenderMan/Attributes", GafferRenderMan.RenderManAttributes, searchText = "RenderManAttributes" )
GafferUI.NodeMenu.append( "/RenderMan/Options", GafferRenderMan.RenderManOptions, searchText = "RenderManOptions" )
GafferUI.NodeMenu.append( "/RenderMan/Render", GafferRenderMan.RenderManRender, searchText = "RenderManRender" )
GafferUI.NodeMenu.append( "/RenderMan/InteractiveRender", GafferRenderMan.InteractiveRenderManRender, searchText = "InteractiveRender" )
