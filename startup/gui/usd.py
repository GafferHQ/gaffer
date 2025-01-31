
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

import os
import Gaffer
import GafferUSD

# Default cone angle is 90 (an entire hemisphere), so replace with something
# that actually looks like a cone for all user-created lights.
Gaffer.Metadata.registerValue( GafferUSD.USDLight, "parameters.shaping:cone:angle.value", "userDefault", 25.0 )

# `texture:format == automatic` isn't well supported at present, so default
# user-created lights to `latlong`.
Gaffer.Metadata.registerValue( GafferUSD.USDLight, "parameters.texture:format", "userDefault", "latlong" )

# Put Arnold parameters last. We can't do that using the schemas in GafferArnold.usda
# because they provide no control over property ordering.
for i, parameter in enumerate( [
	"aov", "aov_indirect", "portal_mode", "spread", "roundness", "soft_edge", "camera",
	"transmission", "sss", "indirect", "volume", "max_bounces", "cast_volumetric_shadows",
	"samples", "volume_samples", "resolution"
] ) :
	Gaffer.Metadata.registerValue( GafferUSD.USDLight, f"parameters.arnold:{parameter}", "layout:index", 1000 + i )

# Change Cycles ordering.
for i, parameter in enumerate( [
	"lightgroup",
	"use_mis", "use_camera", "use_diffuse", "use_glossy", "use_transmission", "use_scatter", "use_caustics",
	"spread", "map_resolution", "max_bounces"
] ) :
	Gaffer.Metadata.registerValue( GafferUSD.USDLight, f"parameters.cycles:{parameter}", "layout:index", 2000 + i )

# Only show the Cycles parameters if Cycles exists and not hidden
Gaffer.Metadata.registerValue( GafferUSD.USDLight, "parameters", "layout:activator:cyclesUIEnabled", lambda x : os.environ.get( "CYCLES_ROOT" ) and os.environ.get( "GAFFERCYCLES_HIDE_UI", "" ) != "1" )
Gaffer.Metadata.registerValue( GafferUSD.USDLight, "parameters.cycles:*", "layout:visibilityActivator", "cyclesUIEnabled" )
