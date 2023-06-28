##########################################################################
#
#  Copyright (c) 2023, Cinesite VFX Ltd. All rights reserved.
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
import pathlib
import os

import oslquery

import IECore

import GafferSceneUI
import GafferUI
import GafferOSL

def __shaderCreator( nodeName, shaderName ) :

	node = GafferOSL.OSLShader( nodeName )
	node.loadShader( shaderName )

	return node

shaderMenuItems = None

def __shaderSubMenu( oslPath ) :

	shaders = [ i.stem for i in oslPath.glob( "*.oso" ) ]

	# Dictionary of the form { "subMenuName" : [ ( "shader", "shaderMenuName" ), ... ], ... }
	menu = {}

	global shaderMenuItems

	if shaderMenuItems is None :
		for shader in shaders :
			q = oslquery.OSLQuery( shader, searchpath = str( oslPath ) )
			metadata = {}
			for m in q.metadata :
				metadata[m.name] = m.value

			shaderName = metadata.get( "niceName", IECore.CamelCase.toSpaced( shader ) )

			shaderName = shaderName.replace( "&", "and" )
			shaderName = shaderName[2:].lstrip() if shaderName.lower().startswith( "dl" ) else shaderName

			if "hidden" in metadata.get( "tags", [] ) :
				continue

			subMenu = None
			for tag in metadata.get( "tags", [] ) :
				if tag == "surface" and shader.startswith( "dl" ) :
					subMenu = "Surface"
				elif tag == "volume" :
					subMenu = "Volume"
				elif tag == "displacement" and shader.startswith( "dl" ) :
					subMenu = "Displacement"
				elif tag == "texture/2d" :
					subMenu = "Texture 2D"
				elif tag == "texture/3d" :
					subMenu = "Texture 3D"
				elif tag == "utility" :
					subMenu = "Utility"
				elif tag == "toon" :
					subMenu = "Toon"

			if subMenu is None :
				continue

			menu.setdefault( subMenu, [] ).append( ( shader, shaderName ) )

		shaderMenuItems = sorted( menu.items() )

	result = IECore.MenuDefinition()

	for subMenu, shaderPairs in shaderMenuItems :
		for shaderPair in shaderPairs :
			shader, shaderName = shaderPair

			menuPath = "/{}/{}".format( subMenu, shaderName )

			result.append(
				menuPath,
				{
					"command" : GafferUI.NodeMenu.nodeCreatorWrapper(
						functools.partial( __shaderCreator, shaderName.replace( " ", "" ), shader )
					),
					"searchText":  "dl" + shaderName,
				}
			)

	return result

def appendShaders( menuDefinition, prefix="/3Delight/Shader") :

	delightPath = pathlib.Path( os.environ["DELIGHT"] )
	delightShaders = list( delightPath.glob( "**/*.oso" ) )

	# The first `hideShaders()` can be removed when we remove `$DELIGHT` from the
	# `OSL_SHADERS_PATHS` in the startup wrapper.
	subDirectories = { d.relative_to( delightPath ).parts[0] for d in delightShaders }
	GafferSceneUI.ShaderUI.hideShaders( IECore.PathMatcher( [ "{}/.../*.oso".format( d ) for d in subDirectories ] ) )

	GafferSceneUI.ShaderUI.hideShaders(
		IECore.PathMatcher(
			[ s.name for s in delightShaders if s.relative_to( delightPath ).parts[0] == "osl" ]
		)
	)

	menuDefinition.append(
		prefix,
		{
			"subMenu" : functools.partial( __shaderSubMenu, pathlib.Path( os.environ["DELIGHT"] ) / "osl" )
		}
	)
