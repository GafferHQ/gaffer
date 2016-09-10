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

import Gaffer

Gaffer.Metadata.registerValue( "ri:light:spotlight", "type", "spot" )
Gaffer.Metadata.registerValue( "ri:light:spotlight", "coneAngleParameter", "coneangle" )
Gaffer.Metadata.registerValue( "ri:light:spotlight", "penumbraAngleParameter", "conedeltaangle" )
Gaffer.Metadata.registerValue( "ri:light:spotlight", "penumbraType", "inset" )
Gaffer.Metadata.registerValue( "ri:light:spotlight", "angleUnit", "radians" )
Gaffer.Metadata.registerValue( "ri:light:spotlight", "intensityParameter", "intensity" )
Gaffer.Metadata.registerValue( "ri:light:spotlight", "colorParameter", "lightcolor" )

Gaffer.Metadata.registerValue( "ri:light:pointlight", "type", "point" )
Gaffer.Metadata.registerValue( "ri:light:pointlight", "intensityParameter", "intensity" )
Gaffer.Metadata.registerValue( "ri:light:pointlight", "colorParameter", "lightcolor" )

Gaffer.Metadata.registerValue( "ri:light:distantlight", "type", "distant" )
Gaffer.Metadata.registerValue( "ri:light:distantlight", "intensityParameter", "intensity" )
Gaffer.Metadata.registerValue( "ri:light:distantlight", "colorParameter", "lightcolor" )
