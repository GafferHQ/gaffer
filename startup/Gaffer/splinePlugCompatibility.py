##########################################################################
#
#  Copyright (c) 2025, Image Engine Design Inc. All rights reserved.
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
import IECore

Gaffer.SplineDefinitionInterpolation = IECore.RampInterpolation

Gaffer.SplineDefinitionff = IECore.Rampff
Gaffer.SplineDefinitionfColor3f = IECore.RampfColor3f
Gaffer.SplineDefinitionfColor4f = IECore.RampfColor4f


# There are two main places that may need this compatibility config for Ramp*Plug.
# The first is the same as most of our compatibility configs: old Gaffer scripts
# that were saved out with Spline*Plug.
# The second is more obscure: python/Gaffer/ExtensionAlgo.py uses a __nodeTemplate
# that adds a constructor to remove the dynamic flag from children of a Ramp*Plug.
# Any custom nodes that were exported using ExtensionAlgo from Gaffer 1.6 or earlier
# will have the "Spline*Plug" names baked, and will depend on this config. The long
# term plan is to fix it so those Dynamic flags would never be set ... we probably
# shouldn't remove this compatibility until after we sort that out.

Gaffer.SplineffPlug = Gaffer.RampffPlug
Gaffer.SplinefColor3fPlug = Gaffer.RampfColor3fPlug
Gaffer.SplinefColor4fPlug = Gaffer.RampfColor4fPlug
