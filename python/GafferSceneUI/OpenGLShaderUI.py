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
import fnmatch
import string

import IECore

import GafferImage
import GafferScene

import GafferUI

##########################################################################
# Nodules
##########################################################################

def __parameterNoduleCreator( plug ) :

	if isinstance( plug, ( GafferImage.ImagePlug ) ) :
		return GafferUI.StandardNodule( plug )

	return None

GafferUI.Nodule.registerNodule( GafferScene.OpenGLShader, fnmatch.translate( "parameters.*" ), __parameterNoduleCreator )

##########################################################################
# Shader menu
##########################################################################

def __shaderCreator( shaderName ) :

	nodeName = os.path.split( shaderName )[-1]
	nodeName = IECore.CamelCase.toSpaced( nodeName.translate( string.maketrans( ".-", "__" ) ) )

	node = GafferScene.OpenGLShader( nodeName )
	node.loadShader( shaderName )

	return node

## A function which can be used as the "subMenu" field in a shader definition, to
# create a dynamically generated menu for the creation of OpenGLShader nodes.
def shaderSubMenu() :

	shaders = set()

	## \todo Should be searching IECOREGL_SHADER_PATHS but that includes
	# a lot of irrelevancies at IE at the moment.
	paths = [ os.environ["GAFFER_ROOT"] + "/glsl" ]
	for path in paths :
		for root, dirs, files in os.walk( path ) :
			for file in files :
				if os.path.splitext( file )[1] in ( ".vert", ".frag" ) :
					shaderPath = os.path.join( root, file ).partition( path )[-1].lstrip( "/" )
					shaders.add( os.path.splitext( shaderPath )[0] )

	result = IECore.MenuDefinition()
	for shader in sorted( list( shaders ) ) :
		result.append( "/" + IECore.CamelCase.toSpaced( shader ), { "command" : GafferUI.NodeMenu.nodeCreatorWrapper( IECore.curry( __shaderCreator, shader ) ) } )

	return result
