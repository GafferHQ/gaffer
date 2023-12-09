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

Gaffer.Metadata.registerValue( "option:cycles:session:samples", "label", "Samples" )
Gaffer.Metadata.registerValue( "option:cycles:session:samples", "defaultValue", IECore.IntData( 1024 ) )
Gaffer.Metadata.registerValue(
	"option:cycles:session:samples",
	"description",
	"""
	Number of samples to render for each pixel.
	"""
)

Gaffer.Metadata.registerValue( "option:cycles:integrator:use_adaptive_sampling", "label", "Adaptive Sampling" )
Gaffer.Metadata.registerValue( "option:cycles:integrator:use_adaptive_sampling", "defaultValue", IECore.BoolData( False ) )
Gaffer.Metadata.registerValue(
	"option:cycles:integrator:use_adaptive_sampling",
	"description",
	"""
	Automatically determine the number of samples
	per pixel based on a variance estimation.
	"""
)

Gaffer.Metadata.registerValue( "option:cycles:integrator:adaptive_threshold", "label", "Adaptive Threshold" )
Gaffer.Metadata.registerValue( "option:cycles:integrator:adaptive_threshold", "defaultValue", IECore.FloatData( 0 ) )
Gaffer.Metadata.registerValue(
	"option:cycles:integrator:adaptive_threshold",
	"description",
	"""
	Noise level step to stop sampling at, lower values reduce noise the cost of render time.
	`0` for automatic setting based on number of AA samples.
	"""
)

Gaffer.Metadata.registerValue( "option:cycles:integrator:use_guiding", "label", "Path Guiding" )
Gaffer.Metadata.registerValue( "option:cycles:integrator:use_guiding", "defaultValue", IECore.BoolData( False ) )
Gaffer.Metadata.registerValue(
	"option:cycles:integrator:use_guiding",
	"description",
	"""
	Use path guiding for sampling paths. Path guiding incrementally
	learns the light distribution of the scene and guides paths into directions
	with high direct and indirect light contributions.
	"""
)

Gaffer.Metadata.registerValue( "option:cycles:integrator:min_bounce", "label", "Min Bounces" )
Gaffer.Metadata.registerValue( "option:cycles:integrator:min_bounce", "defaultValue", IECore.IntData( 0 ) )
Gaffer.Metadata.registerValue(
	"option:cycles:integrator:min_bounce",
	"description",
	"""
	Minimum number of light bounces. Setting this higher reduces noise in the first bounces,
	but can also be less efficient for more complex geometry like hair and volumes.
	"""
)

Gaffer.Metadata.registerValue( "option:cycles:integrator:max_bounce", "label", "Max Bounces" )
Gaffer.Metadata.registerValue( "option:cycles:integrator:max_bounce", "defaultValue", IECore.IntData( 7 ) )
Gaffer.Metadata.registerValue(
	"option:cycles:integrator:max_bounce",
	"description",
	"""
	Total maximum number of bounces.
	"""
)

Gaffer.Metadata.registerValue( "option:cycles:integrator:max_diffuse_bounce", "label", "Diffuse" )
Gaffer.Metadata.registerValue( "option:cycles:integrator:max_diffuse_bounce", "defaultValue", IECore.IntData( 7 ) )
Gaffer.Metadata.registerValue(
	"option:cycles:integrator:max_diffuse_bounce",
	"description",
	"""
	Maximum number of diffuse reflection bounces, bounded by total maximum.
	"""
)

Gaffer.Metadata.registerValue( "option:cycles:integrator:max_glossy_bounce", "label", "Glossy" )
Gaffer.Metadata.registerValue( "option:cycles:integrator:max_glossy_bounce", "defaultValue", IECore.IntData( 7 ) )
Gaffer.Metadata.registerValue(
	"option:cycles:integrator:max_glossy_bounce",
	"description",
	"""
	Maximum number of glossy reflection bounces, bounded by total maximum.
	"""
)

Gaffer.Metadata.registerValue( "option:cycles:integrator:max_transmission_bounce", "label", "Transmission" )
Gaffer.Metadata.registerValue( "option:cycles:integrator:max_transmission_bounce", "defaultValue", IECore.IntData( 7 ) )
Gaffer.Metadata.registerValue(
	"option:cycles:integrator:max_transmission_bounce",
	"description",
	"""
	Maximum number of transmission reflection bounces, bounded by total maximum.
	"""
)

Gaffer.Metadata.registerValue( "option:cycles:integrator:max_volume_bounce", "label", "Volume" )
Gaffer.Metadata.registerValue( "option:cycles:integrator:max_volume_bounce", "defaultValue", IECore.IntData( 7 ) )
Gaffer.Metadata.registerValue(
	"option:cycles:integrator:max_volume_bounce",
	"description",
	"""
	Maximum number of volumetric scattering events.
	"""
)

Gaffer.Metadata.registerValue( "option:cycles:integrator:transparent_max_bounce", "label", "Transparency" )
Gaffer.Metadata.registerValue( "option:cycles:integrator:transparent_max_bounce", "defaultValue", IECore.IntData( 7 ) )
Gaffer.Metadata.registerValue(
	"option:cycles:integrator:transparent_max_bounce",
	"description",
	"""
	Maximum number of transparent bounces.
	"""
)
