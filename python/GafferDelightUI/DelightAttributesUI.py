##########################################################################
#
#  Copyright (c) 2017, John Haddon. All rights reserved.
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
import GafferDelight

def __visibilitySummary( plug ) :

	info = []
	for childName, label in (

		( "camera", "Camera" ),
		( "diffuse", "Diff" ),
		( "hair", "Hair" ),
		( "reflection", "Refl" ),
		( "refraction", "Refr" ),
		( "shadow", "Shad" ),
		( "specular", "Spec" ),

	)	:
		if plug["dl:visibility_" + childName]["enabled"].getValue() :
			info.append( label + ( " On" if plug["dl:visibility_" + childName]["value"].getValue() else " Off" ) )

	return ", ".join( info )

def __shadingSummary( plug ) :

	info = []
	for childName, label in ( ( "dl:matte", "Matte" ), ) :
		if plug[childName]["enabled"].getValue() :
			info.append( label + ( " On" if plug[childName]["value"].getValue() else " Off" ) )

	return ", ".join( info )

Gaffer.Metadata.registerNode(

	GafferDelight.DelightAttributes,

	"description",
	"""
	Applies 3Delight attributes to objects in the scene.
	""",

	plugs = {

		# Sections

		"attributes" : {

			"layout:section:Visibility:summary" : __visibilitySummary,
			"layout:section:Shading:summary" : __shadingSummary,

		},

	}

)
