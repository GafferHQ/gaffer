##########################################################################
#
#  Copyright (c) 2024, Cinesite VFX Ltd. All rights reserved.
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

import Gaffer
import GafferUI
import GafferScene
import GafferSceneUI

import IECore

global __renderPassShaders
__renderPassShaders = set()

def registerShaderName( name ) :

	global __renderPassShaders
	__renderPassShaders.add( name )

def shaderNames() :

	global __renderPassShaders
	return sorted( list( __renderPassShaders ) )

def deregisterShaderName( name ) :

	global __renderPassShaders
	__renderPassShaders.remove( name )

def __rendererNames( plug ) :

	return [
		x for x in GafferSceneUI.RenderUI.rendererPresetNames( plug )
		if x not in ( "OpenGL", "3Delight Cloud" )
	]

def __rendererPresetNames( plug ) :

	return IECore.StringVectorData( [ "All" ] + __rendererNames( plug ) )

def __rendererPresetValues( plug ) :

	return IECore.StringVectorData( [ "*" ] + __rendererNames( plug ) )

def __usagePresetNames( plug ) :

	return IECore.StringVectorData( [ IECore.CamelCase.toSpaced( x ) for x in  shaderNames() ] )

def __usagePresetValues( plug ) :

	return IECore.StringVectorData( shaderNames() )

Gaffer.Metadata.registerNode(

	GafferScene.RenderPassShader,

	"description",
	"""
	Sets up a global shader in the options to replace a shader used by a render pass type.
	""",

	plugs = {

		"renderer" : [

			"description",
			"""
			The renderer the shader should affect. Shaders assigned to a specific
			renderer will take precedence over shaders assigned to "All" when
			rendering with that renderer.
			""",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

			"presetNames", __rendererPresetNames,
			"presetValues", __rendererPresetValues,

		],

		"usage" : [

			"description",
			"""
			How the shader is to be used.
			""",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

			"presetNames", __usagePresetNames,
			"presetValues", __usagePresetValues,

		],

		"shader" : [

			"layout:index", -1,

		],

	}

)
