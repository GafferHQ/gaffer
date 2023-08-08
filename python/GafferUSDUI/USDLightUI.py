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
import GafferUSD

Gaffer.Metadata.registerNode(

	GafferUSD.USDLight,

	plugs = {

		"parameters.colorTemperature" : [ "layout:activator", lambda plug : plug.parent()["enableColorTemperature"].getValue() ],

		"parameters.width" : [ "layout:section", "Geometry" ],
		"parameters.height" : [ "layout:section", "Geometry" ],
		"parameters.radius" : [ "layout:section", "Geometry" ],
		"parameters.length" : [ "layout:section", "Geometry" ],
		"parameters.angle" : [ "layout:section", "Geometry" ],

		"parameters.texture:file" : [ "layout:section", "Texture" ],
		"parameters.texture:format" : [ "layout:section", "Texture" ],

		"parameters.texture:*" : [
			"label", lambda plug : IECore.CamelCase.toSpaced( plug.getName().replace( "texture:", "" ) )
		],

		"parameters.shaping:cone:angle" : [ "layout:section", "Shaping" ],
		"parameters.shaping:cone:softness" : [ "layout:section", "Shaping" ],
		"parameters.shaping:focus" : [ "layout:section", "Shaping" ],
		"parameters.shaping:focusTint" : [ "layout:section", "Shaping" ],
		"parameters.shaping:ies:file" : [ "layout:section", "Shaping" ],
		"parameters.shaping:ies:angleScale" : [ "layout:section", "Shaping" ],
		"parameters.shaping:ies:normalize" : [ "layout:section", "Shaping" ],

		"parameters.shaping:*" : [
			"label", lambda plug : " ".join( IECore.CamelCase.toSpaced( t ) for t in plug.getName().split( ":" )[1:] )
		],

		"parameters.shadow:enable" : [ "layout:section", "Shadow" ],
		"parameters.shadow:color" : [ "layout:section", "Shadow" ],
		"parameters.shadow:distance" : [ "layout:section", "Shadow" ],
		"parameters.shadow:falloff" : [ "layout:section", "Shadow" ],
		"parameters.shadow:falloffGamma" : [ "layout:section", "Shadow" ],

		"parameters.shadow:*" : [
			"label", lambda plug : IECore.CamelCase.toSpaced( plug.getName().replace( "shadow:", "" ) )
		]

	}
)
