##########################################################################
#
#  Copyright (c) 2022, Cinesite VFX Ltd. All rights reserved.
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

Gaffer.Metadata.registerValue( "light:RectLight", "type", "quad" )
Gaffer.Metadata.registerValue( "light:SphereLight", "type", "point" )
Gaffer.Metadata.registerValue( "light:DiskLight", "type", "disk" )
Gaffer.Metadata.registerValue( "light:CylinderLight", "type", "cylinder" )
Gaffer.Metadata.registerValue( "light:DistantLight", "type", "distant" )
Gaffer.Metadata.registerValue( "light:GeometryLight", "type", "mesh" )
Gaffer.Metadata.registerValue( "light:DomeLight", "type", "environment" )

for light in [ "RectLight", "SphereLight", "DiskLight", "CylinderLight", "DistantLight", "GeometryLight", "DomeLight" ] :

	metadataTarget = "light:{}".format( light )
	Gaffer.Metadata.registerValue( metadataTarget, "colorParameter", "color" )
	Gaffer.Metadata.registerValue( metadataTarget, "intensityParameter", "intensity" )
	Gaffer.Metadata.registerValue( metadataTarget, "exposureParameter", "exposure" )
	Gaffer.Metadata.registerValue( metadataTarget, "coneAngleParameter", "shaping:cone:angle" )
	Gaffer.Metadata.registerValue( metadataTarget, "coneAngleType", "half" )

Gaffer.Metadata.registerValue( "light:SphereLight", "radiusParameter", "radius" )

Gaffer.Metadata.registerValue( "light:DiskLight", "radiusParameter", "radius" )

Gaffer.Metadata.registerValue( "light:RectLight", "widthParameter", "width" )
Gaffer.Metadata.registerValue( "light:RectLight", "heightParameter", "height" )

Gaffer.Metadata.registerValue( "light:CylinderLight", "radiusParameter", "radius" )
Gaffer.Metadata.registerValue( "light:CylinderLight", "lengthParameter", "length" )
Gaffer.Metadata.registerValue( "light:CylinderLight", "visualiserOrientation", imath.M44f().rotate( imath.V3f( 0, 0.5 * math.pi, 0 ) ) )

Gaffer.Metadata.registerValue( "light:DomeLight", "textureNameParameter", "texture:file" )
