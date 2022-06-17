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

import IECore

import Gaffer
import GafferUSD

import pxr.Kind

Gaffer.Metadata.registerNode(

	GafferUSD.USDAttributes,

	"description",
	"""
	Authors attributes which have specific meaning in USD, but which
	do not influence Gaffer's native behaviour in any way (in which
	case they would belong on the StandardAttributes node).
	""",

	plugs = {

		"attributes.purpose" : [

			"description",
			"""
			Specifies the purpose of a location to be `default`, `render`,
			`proxy` or `guide`. See the [USD documentation](https://graphics.pixar.com/usd/release/glossary.html#usdglossary-purpose)
			for more details.

			> Note : Gaffer doesn't assign any intrinsic meaning to USD's
			> purpose. To control visibility using purpose, we recommend
			> using an AttributeQuery and Expression to query `usd:purpose`
			> and drive `StandardAttributes.visibility` appropriately.
			>
			> Also note that native proxy workflows can be built using
			> Gaffer's contexts, such that proxy or render geometry can appear
			> at the _same_ location in the scene hierarchy, depending on the
			> value of a context variable. This has benefits when selecting
			> and filtering objects.
			""",

		],

		"attributes.purpose.value" : [

			"preset:Default", "default",
			"preset:Render", "render",
			"preset:Proxy", "proxy",
			"preset:Guide", "guide",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		"attributes.kind" : [

			"description",
			"""
			Specifies the kind of a location to be any of the values
			from USD's kind registry. See the [USD documentation](https://graphics.pixar.com/usd/release/glossary.html#usdglossary-kind)
			for more details.

			> Note : Gaffer doesn't assign any intrinsic meaning to USD's
			> kind.
			""",

		],

		"attributes.kind.value" : [

			"presetNames", IECore.StringVectorData( [ IECore.CamelCase.toSpaced( k ) for k in pxr.Kind.Registry().GetAllKinds() if k != "model" ] ),
			"presetValues", IECore.StringVectorData( k for k in pxr.Kind.Registry().GetAllKinds() if k != "model" ),

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

	}

)
