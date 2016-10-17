##########################################################################
#
#  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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
import GafferArnold

def __shaderMetadata( plug, name ) :

	return Gaffer.Metadata.value( plug.node()["__shader"].descendant( plug.relativeName( plug.node() ) ), name )

Gaffer.Metadata.registerNode(

	GafferArnold.ArnoldMeshLight,

	"description",
	"""
	Turns mesh primitives into Arnold mesh lights by assigning
	a mesh_light shader, turning off all visibility except for camera rays,
	and adding the meshes to the default lights set.
	""",

	plugs = {

		"cameraVisibility" : [

			"description",
			"""
			Whether or not the mesh light is visible to camera
			rays.
			""",

		],

		"parameters" : [

			"description",
			"""
			The parameters of the Arnold mesh_light shader that
			is applied to the meshes.
			""",

			## \todo Extend the Metadata API so we can register a provider for "*",
			# which can automatically transfer all internal metadata.
			"nodeGadget:nodulePosition", functools.partial( __shaderMetadata, name = "nodeGadget:nodulePosition" ),
			"nodule:type", functools.partial( __shaderMetadata, name = "nodule:type" ),
			"compoundNodule:orientation", functools.partial( __shaderMetadata, name = "compoundNodule:orientation" ),
			"compoundNodule:spacing", functools.partial( __shaderMetadata, name = "compoundNodule:spacing" ),
			"plugValueWidget:type", functools.partial( __shaderMetadata, name = "plugValueWidget:type" ),

		],

		"parameters.*" : [

			"description",
			"""
			Refer to Arnold's documentation for the mesh_light
			shader.
			""",

			"nodule:type", functools.partial( __shaderMetadata, name = "nodule:type" ),
			"nodeGadget:nodulePosition", functools.partial( __shaderMetadata, name = "nodeGadget:nodulePosition" ),
			"nodule:color", functools.partial( __shaderMetadata, name = "nodule:color" ),
			"plugValueWidget:type", functools.partial( __shaderMetadata, name = "plugValueWidget:type" ),
			"presetNames", functools.partial( __shaderMetadata, name = "presetNames" ),
			"presetValues", functools.partial( __shaderMetadata, name = "presetValues" ),

		],

	}

)
