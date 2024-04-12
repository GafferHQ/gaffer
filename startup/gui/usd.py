
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

import Gaffer
import GafferUSD

# Default cone angle is 90 (an entire hemisphere), so replace with something
# that actually looks like a cone for all user-created lights.
Gaffer.Metadata.registerValue( GafferUSD.USDLight, "parameters.shaping:cone:angle.value", "userDefault", 25.0 )

# `texture:format == automatic` isn't well supported at present, so default
# user-created lights to `latlong`.
Gaffer.Metadata.registerValue( GafferUSD.USDLight, "parameters.texture:format", "userDefault", "latlong" )

# Put Arnold section last. We can't do that using the schemas in GafferArnold.usda
# because they provide no control over property ordering.
Gaffer.Metadata.registerValue( GafferUSD.USDLight, "parameters.arnold:*", "layout:index", -1 )
# Open the sub-sections of Arnold light parameters by default, so everything is
# visible as soon as you pop open the main Arnold section.
Gaffer.Metadata.registerValue( GafferUSD.USDLight, "parameters", "layout:section:Arnold.Refine:collapsed", False )
Gaffer.Metadata.registerValue( GafferUSD.USDLight, "parameters", "layout:section:Arnold.Geometry:collapsed", False )
Gaffer.Metadata.registerValue( GafferUSD.USDLight, "parameters", "layout:section:Arnold.Sampling:collapsed", False )
Gaffer.Metadata.registerValue( GafferUSD.USDLight, "parameters", "layout:section:Arnold.Shadows:collapsed", False )
