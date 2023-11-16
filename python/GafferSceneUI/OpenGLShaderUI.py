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
import string
import functools
import pathlib

import IECore

import Gaffer
import GafferUI
import GafferImage
import GafferScene

##########################################################################
# Metadata
##########################################################################

Gaffer.Metadata.registerNode(

	GafferScene.OpenGLShader,

	"description",
	"""
	Loads GLSL shaders for use in the viewer and the OpenGLRender node.
	GLSL shaders are loaded from *.frag and *.vert files in directories
	specified by the IECOREGL_SHADER_PATHS environment variable.

	Use the ShaderAssignment node to assign shaders to objects in the
	scene.
	""",

	plugs = {

		"parameters.*" : [

			"nodule:type", lambda plug : "GafferUI::StandardNodule" if isinstance( plug, GafferImage.ImagePlug ) else ""

		],

	},

)

##########################################################################
# Shader menu
##########################################################################

def __shaderCreator( shaderName ) :

	nodeName = os.path.split( shaderName )[-1]
	nodeName = nodeName.translate( str.maketrans( ".-", "__" ) )

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
		for extension in [ ".vert", ".frag" ] :
			shaderPaths = pathlib.Path( path ).glob( "**/*" + extension )

			for shaderPath in shaderPaths :
				shaders.add( shaderPath.relative_to( path ).as_posix()[:-len( extension )] )

	result = IECore.MenuDefinition()
	for shader in sorted( list( shaders ) ) :
		result.append( "/" + IECore.CamelCase.toSpaced( shader ), { "command" : GafferUI.NodeMenu.nodeCreatorWrapper( functools.partial( __shaderCreator, shader ) ) } )

	return result
