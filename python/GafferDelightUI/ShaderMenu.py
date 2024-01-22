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

			shaderFileName = metadata.get( "niceName", shader )

			shaderName = metadata.get( "niceName", IECore.CamelCase.toSpaced( shader ) )
			shaderName = shaderName.replace( "&", "and" )
			shaderName = shaderName[2:].lstrip() if shaderName.lower().startswith( "dl" ) else shaderName

			if "hidden" in metadata.get( "tags", [] ) :
				continue
			if "houdini" in metadata.get( "tags", [] ) :
				continue

			subMenu = None
			for tag in metadata.get( "tags", [] ) :
				subMenu = tag.capitalize()

			if shaderFileName == "distantLight" :
				continue
			elif shaderFileName == "directionalLight" :
				continue
			elif shaderFileName == "distantLight" :
				continue
			elif shaderFileName == "pointLight" :
				continue
			elif shaderFileName == "spotLight" :
				continue
			elif shaderFileName == "environmentLight" :
				continue
			elif shaderFileName == "displacementShader" :
				continue
			elif shaderFileName == "surfaceShader" :
				continue
			elif shaderFileName == "plusMinusAverage" :
				continue
			elif shaderFileName == "addDoubleLinear" :
				continue
			elif shaderFileName == "multDoubleLinear" :
				continue
			elif shaderFileName == "tripleShadingSwitch" :
				continue
			elif shaderFileName == "pfx" :
				continue
			elif shaderFileName == "particleCloud" :
				continue
			elif shaderFileName == "shadingEngine_surface" :
				continue
			elif shaderFileName == "surfaceLuminance" :
				continue
			elif shaderFileName == "filter_multiply" :
				continue
			elif shaderFileName == "lens_distortion" :
				continue
			elif shaderFileName == "dl3DelightMaterial" :
				continue
			elif shaderFileName == "transparent" :
				continue
			elif shaderFileName == "shadingEngine_displacement" :
				subMenu = "Displacement"
			elif shaderFileName == "builtinDisplacement" :
				subMenu = "Displacement"
			elif shaderFileName == "glassInterior" :
				subMenu = "Surface"
			elif shaderFileName == "bump2d" :
				subMenu = "Bump"
			elif shaderFileName == "bump3d" :
				subMenu = "Bump"
			elif shaderFileName == "dlPrimitiveAttribute" :
				subMenu = "Utility"
			elif shaderFileName == "dlAOVGroup" :
				subMenu = "AOV"
			elif shaderFileName == "dlAOVGroupFour" :
				subMenu = "AOV"
			elif shaderFileName == "hsvToRgb" :
				subMenu = "Utility (Legacy)"
			elif shaderFileName == "rgbToHsv" :
				subMenu = "Utility (Legacy)"
			elif shaderFileName == "blendColors" :
				subMenu = "Utility (Legacy)"
			elif shaderFileName == "Curve UV Coordinates" :
				subMenu = "Utility (Legacy)"
			elif shaderFileName == "uvCoord" :
				subMenu = "Utility (Legacy)"
			elif shaderFileName == "contrast" :
				subMenu = "Utility (Legacy)"
			elif shaderFileName == "remapHsv" :
				subMenu = "Utility (Legacy)"
			elif shaderFileName == "remapValue" :
				subMenu = "Utility (Legacy)"
			elif shaderFileName == "shadingEngine_surface_switch" :
				subMenu = "Utility (Legacy)"
			elif shaderFileName == "shadingEngine_displacement_switch" :
				subMenu = "Utility (Legacy)"
			elif shaderFileName == "uvChooser" :
				subMenu = "Utility (Legacy)"
			elif shaderFileName == "multiplyDivide" :
				subMenu = "Utility (Legacy)"
			elif shaderFileName == "Set Range" :
				subMenu = "Utility (Legacy)"
			elif shaderFileName == "reverse" :
				subMenu = "Utility (Legacy)"
			elif shaderFileName == "uvCombine" :
				subMenu = "Utility (Legacy)"
			elif shaderFileName == "colorCombine" :
				subMenu = "Utility (Legacy)"
			elif shaderFileName == "luminance" :
				subMenu = "Utility (Legacy)"
			elif shaderFileName == "smear" :
				subMenu = "Utility (Legacy)"
			elif shaderFileName == "remapColor" :
				subMenu = "Utility (Legacy)"
			elif shaderFileName == "vectorProduct" :
				subMenu = "Utility (Legacy)"
			elif shaderFileName == "fourByFourMatrix" :
				subMenu = "Utility (Legacy)"
			elif shaderFileName == "uvCoordEnvironment" :
				subMenu = "Utility (Legacy)"
			elif shaderFileName == "channels" :
				subMenu = "Utility (Legacy)"
			elif shaderFileName == "samplerInfo" :
				subMenu = "Utility (Legacy)"
			elif shaderFileName == "distanceBetween" :
				subMenu = "Utility (Legacy)"
			elif shaderFileName == "ocean" :
				subMenu = "Texture 2D (Legacy)"
			elif shaderFileName == "psdFileTex" :
				subMenu = "Texture 2D (Legacy)"
			elif shaderFileName == "file" :
				subMenu = "Texture 2D (Legacy)"
			elif shaderFileName == "place2dTexture" :
				subMenu = "Texture 2D (Legacy)"
			elif shaderFileName == "ramp" :
				subMenu = "Texture 2D (Legacy)"
			elif shaderFileName == "imagePlane" :
				subMenu = "Texture 2D (Legacy)"
			elif shaderFileName == "stencil" :
				subMenu = "Texture 2D (Legacy)"
			elif shaderFileName == "place3dTexture" :
				subMenu = "Texture 3D (Legacy)"
			elif shaderFileName == "stucco" :
				subMenu = "Texture 3D (Legacy)"
			elif shaderFileName == "envChrome" :
				subMenu = "Texture 3D (Legacy)"
			elif shaderFileName == "snow" :
				subMenu = "Texture 3D (Legacy)"

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
