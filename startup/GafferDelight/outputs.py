##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
#  Copyright (c) 2025, Image Engine Design Inc. All rights reserved.
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

import IECore
import IECoreScene

import Gaffer
import GafferScene

import GafferDelight

# Add standard AOVs as they are defined in the 3Delight shaders

# Should be kept up to date with
# https://gitlab.com/3Delight/3delight-for-houdini/-/blob/master/ui/aov.cpp
# See `contrib/scripts/3delightOutputs.py` in this repository for a helper script.

for name, displayName, source, dataType in [
	( "rgba", "Beauty", "", "" ),
	( "Ci", "Ci", "shader", "color" ),
	( "Ci.direct", "Ci (direct)", "shader", "color" ),
	( "Ci.indirect", "Ci (indirect)", "shader", "color" ),
	( "diffuse", "Diffuse", "shader", "color" ),
	( "diffuse.direct", "Diffuse (direct)", "shader", "color" ),
	( "diffuse.indirect", "Diffuse (indirect)", "shader", "color" ),
	( "hair", "Hair and Fur", "shader", "color" ),
	( "subsurface", "Subsurface Scattering", "shader", "color" ),
	( "reflection", "Reflection", "shader", "color" ),
	( "reflection.direct", "Reflection (direct)", "shader", "color" ),
	( "reflection.indirect", "Reflection (indirect)", "shader", "color" ),
	( "refraction", "Refraction", "shader", "color" ),
	( "volume", "Volume Scattering", "shader", "color" ),
	( "volume.direct", "Volume Scattering (direct)", "shader", "color" ),
	( "volume.indirect", "Volume Scattering (indirect)", "shader", "color" ),
	( "incandescence", "Incandescence", "shader", "color" ),
	( "toon_base", "Toon Base", "shader", "color" ),
	( "toon_diffuse", "Toon Diffuse", "shader", "color" ),
	( "toon_specular", "Toon Specular", "shader", "color" ),
	( "toon_matte", "Toon Matte", "shader", "color" ),
	( "toon_tint", "Toon Tint", "shader", "color" ),
	( "outlines", "Outlines", "shader", "quad" ),
	( "albedo", "Albedo", "shader", "color" ),
	( "z", "Z (depth)", "builtin", "float" ),
	( "P.camera", "Camera Space Position", "builtin", "point" ),
	( "N.camera", "Camera Space Normal", "builtin", "point" ),
	( "P.world", "World Space Position", "builtin", "point" ),
	( "N.world", "World Space Normal", "builtin", "point" ),
	( "Pref", "Reference Position", "attribute", "point" ),
	( "shadow_mask", "Shadow Mask", "shader", "color" ),
	( "st", "UV", "attribute", "point" ),
	( "id.geometry", "Geometry Cryptomatte", "builtin", "float" ),
	( "id.scenepath", "Scene Path Cryptomatte", "builtin", "float" ),
	( "id.surfaceshader", "Surface Shader Cryptomatte", "builtin", "float" ),
	( "relighting_multiplier", "Relighting Multiplier", "shader", "color" ),
	( "relighting_reference", "Relighting Reference", "shader", "color" ),
	( "motionvector", "Motion Vector", "builtin", "point" ),
	( "occlusion", "Ambient Occlusion", "shader", "color" ),
] :
	if name == "rgba" :
		space = ""
		separator = ""
		slash = ""
	else :
		space = " "
		separator = ":"
		slash ="/"

	GafferScene.Outputs.registerOutput(
		"Interactive/3Delight/{}{}{}".format( source.capitalize(), slash, displayName ),
		IECoreScene.Output(
			name,
			"ieDisplay",
			"{}{}{}{}{}".format( dataType, space, source, separator, name ),
			{
				"driverType" : "ClientDisplayDriver",
				"displayHost" : "localhost",
				"displayPort" : "${image:catalogue:port}",
				"remoteDisplayType" : "GafferScene::GafferDisplayDriver",
				"scalarformat" : "half",
				"colorprofile" : "linear",
				"filter" : "blackman-harris",
				"filterwidth" : 3.0,
			}
		)
	)

	GafferScene.Outputs.registerOutput(
		"Batch/3Delight/{}{}{}".format( source.capitalize(), slash, displayName ),
		IECoreScene.Output(
			"${project:rootDirectory}/renders/${script:name}/${renderPass}/%s/%s.####.exr" % ( name, name ),
			"exr",
			"{}{}{}{}{}".format( dataType, space, source, separator, name ),
			{
				"scalarformat" : "half",
				"colorprofile" : "linear",
				"filter" : "blackman-harris",
				"filterwidth" : 3.0,
			}
		)
	)

