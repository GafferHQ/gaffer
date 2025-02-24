##########################################################################
#
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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
import GafferScene

def __attributeMetadata( plug, key ) :

	if not isinstance( plug, Gaffer.NameValuePlug ) :
		plug = plug.parent()

	target = "attribute:" + plug["name"].getValue()
	return Gaffer.Metadata.value( target, key )

Gaffer.Metadata.registerNode(

	GafferScene.Attributes,

	"description",
	"""
	The base type for nodes that apply attributes to the scene.
	""",

	"layout:activator:isNotGlobal", lambda node : not node["global"].getValue(),

	plugs = {

		"attributes" : [

			"description",
			"""
			The attributes to be applied - arbitrary numbers of user defined
			attributes may be added as children of this plug via the user
			interface, or using the CompoundDataPlug API via python.
			""",

			"compoundDataPlugValueWidget:editable", False,

		],

		"attributes.*" : [

			"nameValuePlugPlugValueWidget:ignoreNamePlug", True,

			"description", lambda plug : __attributeMetadata( plug, "description" ),
			"label", lambda plug : __attributeMetadata( plug, "label" ),
			"layout:section", lambda plug : __attributeMetadata( plug, "layout:section" ),

		],

		"attributes.*.value" : [

			"plugValueWidget:type", lambda plug : __attributeMetadata( plug, "plugValueWidget:type" ),
			"presetNames", lambda plug : __attributeMetadata( plug, "presetNames" ),
			"presetValues", lambda plug : __attributeMetadata( plug, "presetValues" ),

		],

		"global" : [

			"description",
			"""
			Causes the attributes to be applied to the scene globals
			instead of the individual locations defined by the filter.
			""",

			"layout:section", "Filter",

		],

		"filter" : [

			"layout:activator", "isNotGlobal",

		],

		"extraAttributes" : [

			"description",
			"""
			An additional set of attributes to be added. Arbitrary numbers
			of attributes may be specified within a single `IECore.CompoundObject`,
			where each key/value pair in the object defines an attribute.
			This is convenient when using an expression to define the attributes
			and the attribute count might be dynamic. It can also be used to
			create attributes whose type cannot be handled by the `attributes`
			CompoundDataPlug, with `IECoreScene.ShaderNetwork` being one example.

			If the same attribute is defined by both the attributes and the
			extraAttributes plugs, then the value from the extraAttributes
			is taken.
			""",

			"plugValueWidget:type", "",
			"layout:section", "Extra",
			"nodule:type", "",

		],

	}

)
