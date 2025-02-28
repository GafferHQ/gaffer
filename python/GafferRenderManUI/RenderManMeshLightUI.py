##########################################################################
#
#  Copyright (c) 2025, Cinesite VFX Ltd. All rights reserved.
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

import Gaffer
import GafferRenderMan

def __shaderMetadata( plug, name ) :

	return Gaffer.Metadata.value( plug.node()["__shader"].descendant( plug.relativeName( plug.node() ) ), name )

Gaffer.Metadata.registerNode(

	GafferRenderMan.RenderManMeshLight,

	"description",
	"""
	Turns mesh primitives into RenderMan mesh lights by assigning
	a PxrMeshLight shader, turning off all visibility except for camera rays,
	and adding the meshes to the default lights set.
	""",

	plugs = {

		"cameraVisibility" : [

			"description",
			"""
			Whether or not the mesh light is visible to camera
			rays.
			""",

			"nameValuePlugPlugValueWidget:ignoreNamePlug", True,

		],

		"cameraVisibility.value" : [

			"plugValueWidget:type", "GafferUI.BoolPlugValueWidget",

		],

		"parameters" : [

			"description",
			"""
			The parameters of the PxrMeshLight shader that is applied to the
			meshes.
			""",

			## \todo Extend the Metadata API so we can register a provider for "*",
			# which can automatically transfer all internal metadata.
			"noduleLayout:section", functools.partial( __shaderMetadata, name = "noduleLayout:section" ),
			"nodule:type", functools.partial( __shaderMetadata, name = "nodule:type" ),
			"noduleLayout:spacing", functools.partial( __shaderMetadata, name = "noduleLayout:spacing" ),
			"plugValueWidget:type", functools.partial( __shaderMetadata, name = "plugValueWidget:type" ),
			"layout:section:Basic:collapsed", False

		],

		"parameters.*" : [

			"description", functools.partial( __shaderMetadata, name = "description" ),
			"nodule:type", functools.partial( __shaderMetadata, name = "nodule:type" ),
			"noduleLayout:section", functools.partial( __shaderMetadata, name = "noduleLayout:section" ),
			"nodule:color", functools.partial( __shaderMetadata, name = "nodule:color" ),
			"layout:section", functools.partial( __shaderMetadata, name = "layout:section" ),
			"plugValueWidget:type", functools.partial( __shaderMetadata, name = "plugValueWidget:type" ),
			"presetNames", functools.partial( __shaderMetadata, name = "presetNames" ),
			"presetValues", functools.partial( __shaderMetadata, name = "presetValues" ),

		],

		"defaultLight" : [

			"description",
			"""
			Whether this light illuminates all geometry by default. When
			toggled, the light will be added to the `defaultLights` set, which
			can be referenced in set expressions and manipulated by downstream
			nodes.
			""",

			"layout:section", "Light Linking",

		]

	}

)
