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

import functools

import Gaffer
import GafferScene
import GafferSceneUI

Gaffer.Metadata.registerNode(

	GafferScene.AttributeTweaks,

	"description",
	"""
	Makes modifications to attributes.
	""",

	"layout:section:Settings.Tweaks:collapsed", False,

	plugs = {

		"localise" : {

			"description" :
			"""
			Turn on to allow location-specific tweaks to be made to attributes
			inherited from ancestors or the scene globals. Attributes will be
			localised to locations matching the node's filter prior to tweaking.
			The original inherited attributes will remain untouched.
			"""

		},

		"ignoreMissing" : {

			"description" :
			"""
			Ignores tweaks targeting missing attributes. When off, missing attributes
			cause the node to error.
			"""

		},

		"tweaks" : {

			"description" :
			"""
			The tweaks to be made to the attributes. Arbitrary numbers of user defined
			tweaks may be added as children of this plug via the user interface, or
			using the AttributeTweaks API via python.
			""",

			"layout:section" : "Settings.Tweaks",
			"plugValueWidget:type" : "GafferUI.LayoutPlugValueWidget",
			"layout:customWidget:addButton:widgetType" : "GafferUI.PlugCreationWidget",
			"layout:customWidget:addButton:index" : -1,
			"plugCreationWidget:excludedTypes" : "Gaffer.ObjectPlug",

			"nodule:type" : "",
			"ui:scene:acceptsAttributes" : True,

		},

		"tweaks.*" : {

			"tweakPlugValueWidget:propertyType" : "attribute",

		},

		"tweaks.*.name" : {

			"ui:scene:acceptsAttributeName" : True,

		},

		"tweaks.*.value" : {

			"description" : functools.partial( GafferSceneUI.AttributesUI._attributeMetadata, name = "description" ),
			"plugValueWidget:type" : functools.partial( GafferSceneUI.AttributesUI._attributeMetadata, name = "plugValueWidget:type" ),
			"presetsPlugValueWidget:allowCustom" : functools.partial( GafferSceneUI.AttributesUI._attributeMetadata, name = "presetsPlugValueWidget:allowCustom" ),
			"ui:scene:acceptsSetExpression" : functools.partial( GafferSceneUI.AttributesUI._attributeMetadata, name = "ui:scene:acceptsSetExpression" ),

			"presetNames" : GafferSceneUI.AttributesUI._attributePresetNames,
			"presetValues" : GafferSceneUI.AttributesUI._attributePresetValues,

		},

	}
)
