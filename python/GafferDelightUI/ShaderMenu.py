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

			shaderNiceName = metadata.get( "niceName", shader )

			shaderName = metadata.get( "niceName", IECore.CamelCase.toSpaced( shader ) )
			shaderName = shaderName.replace( "&", "and" )
			shaderName = shaderName[2:].lstrip() if shaderName.lower().startswith( "dl" ) else shaderName

			if "hidden" in metadata.get( "tags", [] ) :
				continue
			if "houdini" in metadata.get( "tags", [] ) :
				continue

			if shaderNiceName in [
				"distantLight",
				"directionalLight",
				"pointLight",
				"spotLight",
				"environmentLight",
				"displacementShader",
				"builtinDisplacement",
				"surfaceShader",
				"plusMinusAverage",
				"addDoubleLinear",
				"multDoubleLinear",
				"tripleShadingSwitch",
				"dlAOVGroup",
				"pfx",
				"particleCloud",
				"shadingEngine_surface",
				"shadingEngine_surface_switch",
				"shadingEngine_displacement",
				"shadingEngine_displacement_switch",
				"surfaceLuminance",
				"filter_multiply",
				"lens_distortion",
				"dl3DelightMaterial",
				"transparent"
			] :
				continue

			subMenu = None

			subMenu = {
				"glassInterior" : "Surface",
				"bump2d" : "Bump",
				"bump3d" : "Bump",
				"dlPrimitiveAttribute" : "Utility",
				"hsvToRgb" : "Utility (Legacy)",
				"rgbToHsv" : "Utility (Legacy)",
				"blendColors" : "Utility (Legacy)",
				"Curve UV Coordinates" : "Utility (Legacy)",
				"uvCoord" : "Utility (Legacy)",
				"contrast" : "Utility (Legacy)",
				"remapHsv" : "Utility (Legacy)",
				"remapValue" : "Utility (Legacy)",
				"uvChooser" : "Utility (Legacy)",
				"multiplyDivide" : "Utility (Legacy)",
				"reverse" : "Utility (Legacy)",
				"uvCombine" : "Utility (Legacy)",
				"colorCombine" : "Utility (Legacy)",
				"luminance" : "Utility (Legacy)",
				"smear" : "Utility (Legacy)",
				"remapColor" : "Utility (Legacy)",
				"vectorProduct" : "Utility (Legacy)",
				"fourByFourMatrix" : "Utility (Legacy)",
				"uvCoordEnvironment" : "Utility (Legacy)",
				"channels" : "Utility (Legacy)",
				"samplerInfo" : "Utility (Legacy)",
				"distanceBetween" : "Utility (Legacy)",
				"ocean" : "Texture 2D (Legacy)",
				"psdFileTex" : "Texture 2D (Legacy)",
				"file" : "Texture 2D (Legacy)",
				"place2dTexture" : "Texture 2D (Legacy)",
				"ramp" : "Texture 2D (Legacy)",
				"imagePlane" : "Texture 2D (Legacy)",
				"stencil" : "Texture 2D (Legacy)",
				"place3dTexture" : "Texture 3D (Legacy)",
				"stucco" : "Texture 3D (Legacy)",
				"envChrome" : "Texture 3D (Legacy)",
				"snow" : "Texture 3D (Legacy)"
			}.get( shaderNiceName, None )

			for tag in metadata.get( "tags", [] ) :
				subMenu = tag.capitalize()

			if shaderNiceName == "Set Range" :
				subMenu = "Utility"
				shaderName = "Set Range Float"

			if subMenu is None :
				subMenu = "Other"
			elif subMenu == "Texture/2d" :
				subMenu = "Texture 2D"
			elif subMenu == "Texture/3d" :
				subMenu = "Texture 3D"
			elif subMenu == "Lightfilter" :
				subMenu = "Light"

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
