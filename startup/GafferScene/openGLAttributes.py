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

import IECore
import Gaffer

Gaffer.Metadata.registerValue( "attribute:gl:light:drawingMode", "label", "Light Drawing Mode" )
Gaffer.Metadata.registerValue( "attribute:gl:light:drawingMode", "defaultValue", IECore.StringData( "texture" ) )
Gaffer.Metadata.registerValue(
	"attribute:gl:light:drawingMode",
	"description",
	"""
	Controls how lights are presented in the Viewer.
	"""
)

Gaffer.Metadata.registerValue( "attribute:gl:light:frustumScale", "label", "Light Frustum Scale" )
Gaffer.Metadata.registerValue( "attribute:gl:light:frustumScale", "defaultValue", IECore.FloatData( 1.0 ) )
Gaffer.Metadata.registerValue(
	"attribute:gl:light:frustumScale",
	"description",
	"""
	Allows light projections to be scaled to better suit the scene.
	"""
)

Gaffer.Metadata.registerValue( "attribute:gl:visualiser:frustum", "label", "Frustum" )
Gaffer.Metadata.registerValue( "attribute:gl:visualiser:frustum", "defaultValue", IECore.StringData( "whenSelected" ) )
Gaffer.Metadata.registerValue(
	"attribute:gl:visualiser:frustum",
	"description",
	"""
	Controls whether applicable locations draw a representation of
	their projection or frustum.
	"""
)

Gaffer.Metadata.registerValue( "attribute:gl:visualiser:maxTextureResolution", "label", "Max Texture Resolution" )
Gaffer.Metadata.registerValue( "attribute:gl:visualiser:maxTextureResolution", "defaultValue", IECore.IntData( 512 ) )
Gaffer.Metadata.registerValue(
	"attribute:gl:visualiser:maxTextureResolution",
	"description",
	"""
	Visualisers that load textures will respect this setting to
	limit their resolution.
	"""
)

Gaffer.Metadata.registerValue( "attribute:gl:visualiser:scale", "label", "Scale" )
Gaffer.Metadata.registerValue( "attribute:gl:visualiser:scale", "defaultValue", IECore.FloatData( 1.0 ) )
Gaffer.Metadata.registerValue(
	"attribute:gl:visualiser:scale",
	"description",
	"""
	Scales non-geometric visualisations in the viewport to make them
	easier to work with.
	"""
)
