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

import IECore
import Gaffer

## \todo Migrate ArnoldOptions to use this metadata so we have one source of truth.
Gaffer.Metadata.registerValue( "option:ai:AA_samples", "label", "AA Samples" )
Gaffer.Metadata.registerValue( "option:ai:AA_samples", "defaultValue", IECore.IntData( 3 ) )
Gaffer.Metadata.registerValue(
	"option:ai:AA_samples",
	"description",
	"""
	Controls the number of rays per pixel
	traced from the camera. The more samples,
	the better the quality of antialiasing,
	motion blur and depth of field. The actual
	number of rays per pixel is the square of
	the AA Samples value - so a value of 3
	means 9 rays are traced, 4 means 16 rays are
	traced and so on.
	"""
)

Gaffer.Metadata.registerValue( "option:ai:enable_adaptive_sampling", "label", "Enable Adaptive Sampling" )
Gaffer.Metadata.registerValue( "option:ai:enable_adaptive_sampling", "defaultValue", IECore.BoolData( False ) )
Gaffer.Metadata.registerValue(
	"option:ai:enable_adaptive_sampling",
	"description",
	"""
	If adaptive sampling is enabled, Arnold will
	take a minimum of ( AA Samples * AA Samples )
	samples per pixel, and will then take up to
	( AA Samples Max * AA Samples Max ) samples per
	pixel, or until the remaining estimated noise
	gets lower than aaAdaptiveThreshold.
	"""
)

Gaffer.Metadata.registerValue( "option:ai:AA_samples_max", "label", "AA Samples Max" )
Gaffer.Metadata.registerValue( "option:ai:AA_samples_max", "defaultValue", IECore.IntData( 0 ) )
Gaffer.Metadata.registerValue(
	"option:ai:AA_samples_max",
	"description",
	"""
	The maximum sampling rate during adaptive
	sampling. Like AA Samples, this value is
	squared. So AA Samples Max == 6 means up to
	36 samples per pixel.
	"""
)

Gaffer.Metadata.registerValue( "option:ai:AA_adaptive_threshold", "label", "AA Adaptive Threshold" )
Gaffer.Metadata.registerValue( "option:ai:AA_adaptive_threshold", "defaultValue", IECore.FloatData( 0.05 ) )
Gaffer.Metadata.registerValue(
	"option:ai:AA_adaptive_threshold",
	"description",
	"""
	How much leftover noise is acceptable when
	terminating adaptive sampling. Higher values
	accept more noise, lower values keep rendering
	longer to achieve smaller amounts of noise.
	"""
)

Gaffer.Metadata.registerValue( "option:ai:GI_diffuse_samples", "label", "Diffuse Samples" )
Gaffer.Metadata.registerValue( "option:ai:GI_diffuse_samples", "defaultValue", IECore.IntData( 2 ) )
Gaffer.Metadata.registerValue(
	"option:ai:GI_diffuse_samples",
	"description",
	"""
	Controls the number of rays traced when
	computing indirect illumination.
	"""
)

Gaffer.Metadata.registerValue( "option:ai:GI_specular_samples", "label", "Specular Samples" )
Gaffer.Metadata.registerValue( "option:ai:GI_specular_samples", "defaultValue", IECore.IntData( 2 ) )
Gaffer.Metadata.registerValue(
	"option:ai:GI_specular_samples",
	"description",
	"""
	Controls the number of rays traced when
	computing specular reflections.
	"""
)

Gaffer.Metadata.registerValue( "option:ai:GI_transmission_samples", "label", "Transmission Samples" )
Gaffer.Metadata.registerValue( "option:ai:GI_transmission_samples", "defaultValue", IECore.IntData( 2 ) )
Gaffer.Metadata.registerValue(
	"option:ai:GI_transmission_samples",
	"description",
	"""
	Controls the number of rays traced when
	computing specular refractions.
	"""
)

Gaffer.Metadata.registerValue( "option:ai:GI_sss_samples", "label", "SSS Samples" )
Gaffer.Metadata.registerValue( "option:ai:GI_sss_samples", "defaultValue", IECore.IntData( 2 ) )
Gaffer.Metadata.registerValue(
	"option:ai:GI_sss_samples",
	"description",
	"""
	Controls the number of rays traced when
	computing subsurface scattering.
	"""
)

Gaffer.Metadata.registerValue( "option:ai:GI_volume_samples", "label", "Volume Samples" )
Gaffer.Metadata.registerValue( "option:ai:GI_volume_samples", "defaultValue", IECore.IntData( 2 ) )
Gaffer.Metadata.registerValue(
	"option:ai:GI_volume_samples",
	"description",
	"""
	Controls the number of rays traced when
	computing indirect lighting for volumes.
	"""
)

Gaffer.Metadata.registerValue( "option:ai:light_samples", "label", "Light Samples" )
Gaffer.Metadata.registerValue( "option:ai:light_samples", "defaultValue", IECore.IntData( 0 ) )
Gaffer.Metadata.registerValue(
	"option:ai:light_samples",
	"description",
	"""
	Specifies a fixed number of light samples to be taken at each
	shading point. This enables "Global Light Sampling", which provides
	significantly improved performance for scenes containing large numbers
	of lights. In this mode, the `samples` setting on each light is ignored,
	and instead the fixed number of samples is distributed among all the
	lights according to their contribution at the shading point.

	A value of `0` disables Global Light Sampling, reverting to the original
	per-light sampling algorithm.
	"""
)

Gaffer.Metadata.registerValue( "option:ai:GI_total_depth", "label", "Total Depth" )
Gaffer.Metadata.registerValue( "option:ai:GI_total_depth", "defaultValue", IECore.IntData( 10 ) )
Gaffer.Metadata.registerValue(
	"option:ai:GI_total_depth",
	"description",
	"""
	The maximum depth of any ray (Diffuse + Specular +
	Transmission + Volume).
	"""
)

Gaffer.Metadata.registerValue( "option:ai:GI_diffuse_depth", "label", "Diffuse Depth" )
Gaffer.Metadata.registerValue( "option:ai:GI_diffuse_depth", "defaultValue", IECore.IntData( 2 ) )
Gaffer.Metadata.registerValue(
	"option:ai:GI_diffuse_depth",
	"description",
	"""
	Controls the number of ray bounces when
	computing indirect illumination ("bounce light").
	"""
)


Gaffer.Metadata.registerValue( "option:ai:GI_specular_depth", "label", "Specular Depth" )
Gaffer.Metadata.registerValue( "option:ai:GI_specular_depth", "defaultValue", IECore.IntData( 2 ) )
Gaffer.Metadata.registerValue(
	"option:ai:GI_specular_depth",
	"description",
	"""
	Controls the number of ray bounces when
	computing specular reflections.
	"""
)

Gaffer.Metadata.registerValue( "option:ai:GI_transmission_depth", "label", "Transmission Depth" )
Gaffer.Metadata.registerValue( "option:ai:GI_transmission_depth", "defaultValue", IECore.IntData( 2 ) )
Gaffer.Metadata.registerValue(
	"option:ai:GI_transmission_depth",
	"description",
	"""
	Controls the number of ray bounces when
	computing specular refractions.
	"""
)

Gaffer.Metadata.registerValue( "option:ai:GI_volume_depth", "label", "Volume Depth" )
Gaffer.Metadata.registerValue( "option:ai:GI_volume_depth", "defaultValue", IECore.IntData( 0 ) )
Gaffer.Metadata.registerValue(
	"option:ai:GI_volume_depth",
	"description",
	"""
	Controls the number of ray bounces when
	computing indirect lighting on volumes.
	"""
)

Gaffer.Metadata.registerValue( "option:ai:auto_transparency_depth", "label", "Transparency Depth" )
Gaffer.Metadata.registerValue( "option:ai:auto_transparency_depth", "defaultValue", IECore.IntData( 10 ) )
Gaffer.Metadata.registerValue(
	"option:ai:auto_transparency_depth",
	"description",
	"""
	The number of allowable transparent layers - after
	this the last object will be treated as opaque.
	"""
)
