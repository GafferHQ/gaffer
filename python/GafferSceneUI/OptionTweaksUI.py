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

	GafferScene.OptionTweaks,

	"description",
	"""
	Makes modifications to options.
	""",

	"layout:section:Settings.Tweaks:collapsed", False,

	plugs = {

		"ignoreMissing" : {

			"description" :
			"""
			Ignores tweaks targeting missing options. When off, missing options
			cause the node to error.
			"""

		},

		"tweaks" : {

			"description" :
			"""
			The tweaks to be made to the options. Arbitrary numbers of user defined
			tweaks may be added as children of this plug via the user interface, or
			using the OptionTweaks API via python.
			""",

			"layout:section" : "Settings.Tweaks",
			"plugValueWidget:type" : "GafferUI.LayoutPlugValueWidget",
			"layout:customWidget:addButton:widgetType" : "GafferUI.PlugCreationWidget",
			"layout:customWidget:addButton:index" : -1,
			"plugCreationWidget:excludedTypes" : "Gaffer.ObjectPlug",

			"nodule:type" : "",
			"ui:scene:acceptsOptions" : True,

		},

		"tweaks.*" : {

			"tweakPlugValueWidget:propertyType" : "option",

		},

		"tweaks.*.value" : {

			"description" : functools.partial( GafferSceneUI.OptionsUI._optionMetadata, name = "description" ),
			"plugValueWidget:type" : functools.partial( GafferSceneUI.OptionsUI._optionMetadata, name = "plugValueWidget:type" ),
			"presetsPlugValueWidget:allowCustom" : functools.partial( GafferSceneUI.OptionsUI._optionMetadata, name = "presetsPlugValueWidget:allowCustom" ),
			"ui:scene:acceptsSetExpression" : functools.partial( GafferSceneUI.OptionsUI._optionMetadata, name = "ui:scene:acceptsSetExpression" ),

			"presetNames" : GafferSceneUI.OptionsUI._optionPresetNames,
			"presetValues" : GafferSceneUI.OptionsUI._optionPresetValues,

		},

	}
)
