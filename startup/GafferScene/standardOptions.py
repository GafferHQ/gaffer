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

import imath

import IECore
import Gaffer

Gaffer.Metadata.registerValue( "option:render:camera", "label", "Camera" )
Gaffer.Metadata.registerValue( "option:render:camera", "defaultValue", IECore.StringData( "" ) )
Gaffer.Metadata.registerValue(
	"option:render:camera",
	"description",
	"""
	The primary camera to be used for rendering. If this
	is not specified, then a default orthographic camera
	positioned at the origin is used.
	"""
)

Gaffer.Metadata.registerValue( "option:render:resolution", "label", "Resolution" )
Gaffer.Metadata.registerValue( "option:render:resolution", "defaultValue", IECore.V2iData( imath.V2i( 1024, 778 ) ) )
Gaffer.Metadata.registerValue(
	"option:render:resolution",
	"description",
	"""
	The resolution of the image to be rendered.
	"""
)

Gaffer.Metadata.registerValue( "option:render:resolutionMultiplier", "label", "Resolution Multiplier" )
Gaffer.Metadata.registerValue( "option:render:resolutionMultiplier", "defaultValue", IECore.FloatData( 1.0 ) )
Gaffer.Metadata.registerValue(
	"option:render:resolutionMultiplier",
	"description",
	"""
	Multiplies the resolution of the render by this amount.
	"""
)

Gaffer.Metadata.registerValue( "option:render:deformationBlur", "label", "Deformation Blur" )
Gaffer.Metadata.registerValue( "option:render:deformationBlur", "defaultValue", IECore.BoolData( False ) )
Gaffer.Metadata.registerValue(
	"option:render:deformationBlur",
	"description",
	"""
	Whether or not deformation motion is taken into
	account in the rendered image. To specify the
	number of deformation segments to use for each
	object in the scene, use a StandardAttributes
	node with appropriate filters.
	"""
)

Gaffer.Metadata.registerValue( "option:render:transformBlur", "label", "Transform Blur" )
Gaffer.Metadata.registerValue( "option:render:transformBlur", "defaultValue", IECore.BoolData( False ) )
Gaffer.Metadata.registerValue(
	"option:render:transformBlur",
	"description",
	"""
	Whether or not transform motion is taken into
	account in the rendered image. To specify the
	number of transform segments to use for each
	object in the scene, use a StandardAttributes
	node with appropriate filters.
	"""
)

Gaffer.Metadata.registerValue( "option:render:shutter", "label", "Shutter" )
Gaffer.Metadata.registerValue( "option:render:shutter", "defaultValue", IECore.V2fData( imath.V2f( -0.25, 0.25 ) ) )
Gaffer.Metadata.registerValue(
	"option:render:shutter",
	"description",
	"""
	The interval over which the camera shutter is open. Measured
	in frames, and specified relative to the frame being rendered.
	"""
)

Gaffer.Metadata.registerValue( "option:render:inclusions", "label", "Inclusions" )
Gaffer.Metadata.registerValue( "option:render:inclusions", "defaultValue", IECore.StringData( "/" ) )
Gaffer.Metadata.registerValue(
	"option:render:inclusions",
	"description",
	"""
	A set expression that limits the objects included in the render to only those matched
	and their descendants. Objects not matched by the set expression will be pruned from
	the scene. Cameras are included by default and do not need to be specified here.
	"""
)

Gaffer.Metadata.registerValue( "option:render:exclusions", "label", "Exclusions" )
Gaffer.Metadata.registerValue( "option:render:exclusions", "defaultValue", IECore.StringData( "" ) )
Gaffer.Metadata.registerValue(
	"option:render:exclusions",
	"description",
	"""
	A set expression that excludes the matched objects from the render. Exclusions
	affect both `inclusions` and `additionalLights` and cause the matching objects and
	their descendants to be pruned from the scene.
	"""
)

Gaffer.Metadata.registerValue( "option:render:additionalLights", "label", "Additional Lights" )
Gaffer.Metadata.registerValue( "option:render:additionalLights", "defaultValue", IECore.StringData( "" ) )
Gaffer.Metadata.registerValue(
	"option:render:additionalLights",
	"description",
	"""
	A set expression that specifies additional lights to be included in the render.
	This differs from `inclusions` as only lights will be matched by this set
	expression.
	"""
)
