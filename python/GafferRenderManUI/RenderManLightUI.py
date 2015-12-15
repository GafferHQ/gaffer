##########################################################################
#
#  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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
import GafferRenderMan

Gaffer.Metadata.registerNode(

	GafferRenderMan.RenderManLight,

	"description",
	"""
	Loads a RenderMan light shader and uses
	it to output a scene with a single light.
	""",

)

Gaffer.Metadata.registerValue( "light:ri:spotlight", "type", "spot" )
Gaffer.Metadata.registerValue( "light:ri:spotlight", "coneAngleParameter", "coneangle" )
Gaffer.Metadata.registerValue( "light:ri:spotlight", "penumbraAngleParameter", "conedeltaangle" )
Gaffer.Metadata.registerValue( "light:ri:spotlight", "penumbraType", "inset" )
Gaffer.Metadata.registerValue( "light:ri:spotlight", "angleUnit", "radians" )
Gaffer.Metadata.registerValue( "light:ri:spotlight", "intensityParameter", "intensity" )
Gaffer.Metadata.registerValue( "light:ri:spotlight", "colorParameter", "lightcolor" )

Gaffer.Metadata.registerValue( "light:ri:pointlight", "type", "point" )
Gaffer.Metadata.registerValue( "light:ri:pointlight", "intensityParameter", "intensity" )
Gaffer.Metadata.registerValue( "light:ri:pointlight", "colorParameter", "lightcolor" )

Gaffer.Metadata.registerValue( "light:ri:distantlight", "type", "distant" )
Gaffer.Metadata.registerValue( "light:ri:distantlight", "intensityParameter", "intensity" )
Gaffer.Metadata.registerValue( "light:ri:distantlight", "colorParameter", "lightcolor" )
