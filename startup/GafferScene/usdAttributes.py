##########################################################################
#
#  Copyright (c) 2024, Cinesite VFX Ltd. All rights reserved.
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

import pxr.Kind

Gaffer.Metadata.registerValue( "attribute:usd:kind", "label", "Kind" )
Gaffer.Metadata.registerValue( "attribute:usd:kind", "defaultValue", IECore.StringData( "" ) )
Gaffer.Metadata.registerValue(
	"attribute:usd:kind",
	"description",
	"""
	Specifies the kind of a location to be any
	of the values from USD's kind registry. See
	the USD documentation for more details.

	> Note : Gaffer doesn't assign any intrinsic
	> meaning to USD's kind.
	""",
)
Gaffer.Metadata.registerValue( "attribute:usd:kind", "plugValueWidget:type", "GafferUI.PresetsPlugValueWidget" )
Gaffer.Metadata.registerValue( "attribute:usd:kind", "presetNames", IECore.StringVectorData( [ IECore.CamelCase.toSpaced( k ) for k in pxr.Kind.Registry().GetAllKinds() if k != "model" ] ) )
Gaffer.Metadata.registerValue( "attribute:usd:kind", "presetValues", IECore.StringVectorData( k for k in pxr.Kind.Registry().GetAllKinds() if k != "model" ) )

Gaffer.Metadata.registerValue( "attribute:usd:purpose", "label", "Purpose" )
Gaffer.Metadata.registerValue( "attribute:usd:purpose", "defaultValue", IECore.StringData( "default" ) )
Gaffer.Metadata.registerValue(
	"attribute:usd:purpose",
	"description",
	"""
	Specifies the purpose of a location to be
	`default`, `render`, `proxy` or `guide`. See
	the USD documentation for more details.
	""",
)
Gaffer.Metadata.registerValue( "attribute:usd:purpose", "plugValueWidget:type", "GafferUI.PresetsPlugValueWidget" )
Gaffer.Metadata.registerValue( "attribute:usd:purpose", "presetNames", IECore.StringVectorData( [ "Default", "Render", "Proxy", "Guide" ] ) )
Gaffer.Metadata.registerValue( "attribute:usd:purpose", "presetValues", IECore.StringVectorData( [ "default", "render", "proxy", "guide" ] ) )
