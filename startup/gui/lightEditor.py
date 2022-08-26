##########################################################################
#
#  Copyright (c) 2021, Cinesite VFX Ltd. All rights reserved.
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
import Gaffer
import GafferSceneUI

if os.environ.get( "GAFFERAPPLESEED_HIDE_UI", "" ) != "1" :

	with IECore.IgnoredExceptions( ImportError ) :

		# Register Light Editor sections for Appleseed before the generic "Visualisation" section
		import GafferAppleseedUI

		Gaffer.Metadata.registerValue( GafferSceneUI.LightEditor.Settings, "attribute", "preset:Appleseed", "as:light" )
		# Default to showing Appleseed lights, since that is the renderer we ship with.
		Gaffer.Metadata.registerValue( GafferSceneUI.LightEditor.Settings, "attribute", "userDefault", "as:light" )


if os.environ.get( "CYCLES_ROOT" ) and os.environ.get( "GAFFERCYCLES_HIDE_UI", "" ) != "1" :

	Gaffer.Metadata.registerValue( GafferSceneUI.LightEditor.Settings, "attribute", "preset:Cycles", "cycles:light" )

	GafferSceneUI.LightEditor.registerParameter( "cycles:light", "color" )
	GafferSceneUI.LightEditor.registerParameter( "cycles:light", "intensity" )
	GafferSceneUI.LightEditor.registerParameter( "cycles:light", "exposure" )
	GafferSceneUI.LightEditor.registerParameter( "cycles:light", "lightgroup" )

	GafferSceneUI.LightEditor.registerParameter( "cycles:light", "cast_shadow", "Contribution" )
	GafferSceneUI.LightEditor.registerParameter( "cycles:light", "use_diffuse", "Contribution" )
	GafferSceneUI.LightEditor.registerParameter( "cycles:light", "use_glossy", "Contribution" )
	GafferSceneUI.LightEditor.registerParameter( "cycles:light", "use_transmission", "Contribution" )
	GafferSceneUI.LightEditor.registerParameter( "cycles:light", "use_scatter", "Contribution" )
	GafferSceneUI.LightEditor.registerParameter( "cycles:light", "max_bounces", "Contribution" )

	GafferSceneUI.LightEditor.registerParameter( "cycles:light", "size", "Shape" )
	GafferSceneUI.LightEditor.registerParameter( "cycles:light", "spot_angle", "Shape" )
	GafferSceneUI.LightEditor.registerParameter( "cycles:light", "spot_smooth", "Shape" )
	GafferSceneUI.LightEditor.registerParameter( "cycles:light", "spread", "Shape" )
	GafferSceneUI.LightEditor.registerParameter( "cycles:light", "angle", "Shape" )

	# Assume that Cycles would be preferred to Appleseed.
	Gaffer.Metadata.registerValue( GafferSceneUI.LightEditor.Settings, "attribute", "userDefault", "cycles:light" )

with IECore.IgnoredExceptions( ImportError ) :

	# This import appears unused, but it is intentional; it prevents us from
	# adding the OSL lights when 3Delight isn't available.
	import GafferDelight
	import GafferOSL

	shader = GafferOSL.OSLShader()

	for light in [
		"maya/osl/pointLight",
		"maya/osl/spotLight",
		"maya/osl/distantLight",
		"maya/osl/environmentLight"
	] :
		shader.loadShader( light )
		for parameter in shader["parameters"] :
			GafferSceneUI.LightEditor.registerParameter(
				"osl:light", parameter.getName(),
				shader.parameterMetadata( parameter, "page" )
			)

	Gaffer.Metadata.registerValue( GafferSceneUI.LightEditor.Settings, "attribute", "preset:OSL", "osl:light" )
	# If 3Delight is available, then assume it will be used in preference to Appleseed.
	Gaffer.Metadata.registerValue( GafferSceneUI.LightEditor.Settings, "attribute", "userDefault", "osl:light" )

with IECore.IgnoredExceptions( ImportError ) :

	import GafferArnold
	# Register Light Editor sections for Arnold before the generic "Visualisation" section
	import GafferArnoldUI

	Gaffer.Metadata.registerValue( GafferSceneUI.LightEditor.Settings, "attribute", "preset:Arnold", "ai:light" )
	# If Arnold is available, then assume it is the renderer of choice.
	Gaffer.Metadata.registerValue( GafferSceneUI.LightEditor.Settings, "attribute", "userDefault", "ai:light" )

# UsdLux lights

Gaffer.Metadata.registerValue( GafferSceneUI.LightEditor.Settings, "attribute", "preset:USD", "light" )

GafferSceneUI.LightEditor.registerParameter( "light", "color" )
GafferSceneUI.LightEditor.registerParameter( "light", "intensity" )
GafferSceneUI.LightEditor.registerParameter( "light", "exposure" )
GafferSceneUI.LightEditor.registerParameter( "light", "colorTemperature" )
GafferSceneUI.LightEditor.registerParameter( "light", "enableColorTemperature" )
GafferSceneUI.LightEditor.registerParameter( "light", "normalize" )
GafferSceneUI.LightEditor.registerParameter( "light", "diffuse" )
GafferSceneUI.LightEditor.registerParameter( "light", "specular" )

GafferSceneUI.LightEditor.registerParameter( "light", "width", "Geometry" )
GafferSceneUI.LightEditor.registerParameter( "light", "height", "Geometry" )
GafferSceneUI.LightEditor.registerParameter( "light", "radius", "Geometry" )
GafferSceneUI.LightEditor.registerParameter( "light", "treatAsPoint", "Geometry" )
GafferSceneUI.LightEditor.registerParameter( "light", "length", "Geometry" )
GafferSceneUI.LightEditor.registerParameter( "light", "treatAsLine", "Geometry" )
GafferSceneUI.LightEditor.registerParameter( "light", "angle", "Geometry" )

GafferSceneUI.LightEditor.registerParameter( "light", "texture:file", "Texture" )
GafferSceneUI.LightEditor.registerParameter( "light", "texture:format", "Texture" )

GafferSceneUI.LightEditor.registerParameter( "light", "shaping:cone:angle", "Shaping" )
GafferSceneUI.LightEditor.registerParameter( "light", "shaping:cone:softness", "Shaping" )
GafferSceneUI.LightEditor.registerParameter( "light", "shaping:focus", "Shaping" )
GafferSceneUI.LightEditor.registerParameter( "light", "shaping:focusTint", "Shaping" )
GafferSceneUI.LightEditor.registerParameter( "light", "shaping:ies:file", "Shaping" )
GafferSceneUI.LightEditor.registerParameter( "light", "shaping:ies:angleScale", "Shaping" )
GafferSceneUI.LightEditor.registerParameter( "light", "shaping:ies:normalize", "Shaping" )

# Register generic light attributes
for attributeName in [
	"gl:visualiser:scale",
	"gl:visualiser:maxTextureResolution",
	"gl:visualiser:frustum",
	"gl:light:frustumScale",
	"gl:light:drawingMode",
] :
	GafferSceneUI.LightEditor.registerAttribute( "*", attributeName, "Visualisation" )
