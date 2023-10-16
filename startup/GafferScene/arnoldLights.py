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

import Gaffer

Gaffer.Metadata.registerValue( "ai:light:spot_light", "type", "spot" )
Gaffer.Metadata.registerValue( "ai:light:spot_light", "coneAngleParameter", "cone_angle" )
Gaffer.Metadata.registerValue( "ai:light:spot_light", "penumbraAngleParameter", "penumbra_angle" )
Gaffer.Metadata.registerValue( "ai:light:spot_light", "penumbraType", "inset" )
Gaffer.Metadata.registerValue( "ai:light:spot_light", "intensityParameter", "intensity" )
Gaffer.Metadata.registerValue( "ai:light:spot_light", "exposureParameter", "exposure" )
Gaffer.Metadata.registerValue( "ai:light:spot_light", "colorParameter", "color" )
Gaffer.Metadata.registerValue( "ai:light:spot_light", "radiusParameter", "radius" )
Gaffer.Metadata.registerValue( "ai:light:spot_light", "lensRadiusParameter", "lens_radius" )

Gaffer.Metadata.registerValue( "ai:light:point_light", "type", "point" )
Gaffer.Metadata.registerValue( "ai:light:point_light", "intensityParameter", "intensity" )
Gaffer.Metadata.registerValue( "ai:light:point_light", "exposureParameter", "exposure" )
Gaffer.Metadata.registerValue( "ai:light:point_light", "colorParameter", "color" )
Gaffer.Metadata.registerValue( "ai:light:point_light", "radiusParameter", "radius" )

Gaffer.Metadata.registerValue( "ai:light:distant_light", "type", "distant" )
Gaffer.Metadata.registerValue( "ai:light:distant_light", "intensityParameter", "intensity" )
Gaffer.Metadata.registerValue( "ai:light:distant_light", "exposureParameter", "exposure" )
Gaffer.Metadata.registerValue( "ai:light:distant_light", "colorParameter", "color" )

Gaffer.Metadata.registerValue( "ai:light:quad_light", "type", "quad" )
Gaffer.Metadata.registerValue( "ai:light:quad_light", "intensityParameter", "intensity" )
Gaffer.Metadata.registerValue( "ai:light:quad_light", "exposureParameter", "exposure" )
Gaffer.Metadata.registerValue( "ai:light:quad_light", "colorParameter", "color" )
Gaffer.Metadata.registerValue( "ai:light:quad_light", "widthParameter", "width" )
Gaffer.Metadata.registerValue( "ai:light:quad_light", "heightParameter", "height" )
Gaffer.Metadata.registerValue( "ai:light:quad_light", "portalParameter", "portal" )
Gaffer.Metadata.registerValue( "ai:light:quad_light", "spreadParameter", "spread" )
Gaffer.Metadata.registerValue( "ai:light:quad_light", "uvOrientation", imath.M33f().rotate( 0.5 * math.pi ) )

Gaffer.Metadata.registerValue( "ai:light:disk_light", "type", "disk" )
Gaffer.Metadata.registerValue( "ai:light:disk_light", "intensityParameter", "intensity" )
Gaffer.Metadata.registerValue( "ai:light:disk_light", "exposureParameter", "exposure" )
Gaffer.Metadata.registerValue( "ai:light:disk_light", "colorParameter", "color" )
Gaffer.Metadata.registerValue( "ai:light:disk_light", "spreadParameter", "spread" )
Gaffer.Metadata.registerValue( "ai:light:disk_light", "radiusParameter", "radius" )

Gaffer.Metadata.registerValue( "ai:light:cylinder_light", "type", "cylinder" )
Gaffer.Metadata.registerValue( "ai:light:cylinder_light", "intensityParameter", "intensity" )
Gaffer.Metadata.registerValue( "ai:light:cylinder_light", "exposureParameter", "exposure" )
Gaffer.Metadata.registerValue( "ai:light:cylinder_light", "colorParameter", "color" )
Gaffer.Metadata.registerValue( "ai:light:cylinder_light", "radiusParameter", "radius" )
Gaffer.Metadata.registerValue( "ai:light:cylinder_light", "visualiserOrientation", imath.M44f().rotate( imath.V3f( 0.5 * math.pi, 0 , 0 ) ) )
Gaffer.Metadata.registerValue( "ai:light:cylinder_light", "heightToScaleRatio", 2.0 )

Gaffer.Metadata.registerValue( "ai:light:skydome_light", "intensityParameter", "intensity" )
Gaffer.Metadata.registerValue( "ai:light:skydome_light", "exposureParameter", "exposure" )
Gaffer.Metadata.registerValue( "ai:light:skydome_light", "colorParameter", "color" )
Gaffer.Metadata.registerValue( "ai:light:skydome_light", "type", "environment" )

Gaffer.Metadata.registerValue( "ai:light:mesh_light", "intensityParameter", "intensity" )
Gaffer.Metadata.registerValue( "ai:light:mesh_light", "exposureParameter", "exposure" )
Gaffer.Metadata.registerValue( "ai:light:mesh_light", "colorParameter", "color" )
Gaffer.Metadata.registerValue( "ai:light:mesh_light", "type", "mesh" )

Gaffer.Metadata.registerValue( "ai:light:photometric_light", "intensityParameter", "intensity" )
Gaffer.Metadata.registerValue( "ai:light:photometric_light", "exposureParameter", "exposure" )
Gaffer.Metadata.registerValue( "ai:light:photometric_light", "colorParameter", "color" )
Gaffer.Metadata.registerValue( "ai:light:photometric_light", "radiusParameter", "radius" )
# Most profiles generally shine down -y
Gaffer.Metadata.registerValue( "ai:light:photometric_light", "visualiserOrientation", imath.M44f().rotate( imath.V3f( -0.5 * math.pi, 0 , 0 ) ) )
Gaffer.Metadata.registerValue( "ai:light:photometric_light", "type", "photometric" )
