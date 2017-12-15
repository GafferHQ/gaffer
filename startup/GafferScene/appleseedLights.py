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

import math
import imath

import IECore
import Gaffer

Gaffer.Metadata.registerValue( "as:light:latlong_map_environment_edf", "type", "environment" )
Gaffer.Metadata.registerValue( "as:light:latlong_map_environment_edf", "textureNameParameter", "radiance_map" )
Gaffer.Metadata.registerValue( "as:light:latlong_map_environment_edf", "intensityParameter", "radiance_multiplier" )
Gaffer.Metadata.registerValue( "as:light:latlong_map_environment_edf", "exposureParameter", "exposure" )
Gaffer.Metadata.registerValue( "as:light:latlong_map_environment_edf", "visualiserOrientation", imath.M44f().rotate( imath.V3f( 0, 0.5 * math.pi, 0 ) ) )

Gaffer.Metadata.registerValue( "as:light:hosek_environment_edf", "type", "environment" )

Gaffer.Metadata.registerValue( "as:light:spot_light", "type", "spot" )
Gaffer.Metadata.registerValue( "as:light:spot_light", "coneAngleParameter", "outer_angle" )
Gaffer.Metadata.registerValue( "as:light:spot_light", "penumbraAngleParameter", "inner_angle" )
Gaffer.Metadata.registerValue( "as:light:spot_light", "penumbraType", "absolute" )
Gaffer.Metadata.registerValue( "as:light:spot_light", "intensityParameter", "intensity_multiplier" )
Gaffer.Metadata.registerValue( "as:light:spot_light", "exposureParameter", "exposure" )
Gaffer.Metadata.registerValue( "as:light:spot_light", "colorParameter", "intensity" )

Gaffer.Metadata.registerValue( "as:light:point_light", "type", "point" )
Gaffer.Metadata.registerValue( "as:light:point_light", "intensityParameter", "intensity_multiplier" )
Gaffer.Metadata.registerValue( "as:light:point_light", "exposureParameter", "exposure" )
Gaffer.Metadata.registerValue( "as:light:point_light", "colorParameter", "intensity" )

Gaffer.Metadata.registerValue( "as:light:directional_light", "type", "distant" )
Gaffer.Metadata.registerValue( "as:light:directional_light", "intensityParameter", "irradiance_multiplier" )
Gaffer.Metadata.registerValue( "as:light:directional_light", "exposureParameter", "exposure" )
Gaffer.Metadata.registerValue( "as:light:directional_light", "colorParameter", "irradiance" )

Gaffer.Metadata.registerValue( "as:light:diffuse_edf", "type", "quad" )
Gaffer.Metadata.registerValue( "as:light:diffuse_edf", "intensityParameter", "radiance_multiplier" )
Gaffer.Metadata.registerValue( "as:light:diffuse_edf", "exposureParameter", "exposure" )
Gaffer.Metadata.registerValue( "as:light:diffuse_edf", "colorParameter", "radiance" )
