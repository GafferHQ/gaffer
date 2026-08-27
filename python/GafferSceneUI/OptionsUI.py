##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
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
import GafferScene

# The following functions are protected rather than private so that
# they can be shared by OptionTweaksUI.

def _optionMetadata( plug, name ) :

	if not isinstance( plug, ( Gaffer.TweakPlug, Gaffer.NameValuePlug ) ) :
		plug = plug.parent()

	source = "option:" + plug["name"].getValue()
	return Gaffer.Metadata.value( source, name )

def _optionPresetNames( plug ) :

	names = list( __optionPresets( plug ).keys() )
	return IECore.StringVectorData( names ) if names else None

def _optionPresetValues( plug ) :

	values = list( __optionPresets( plug ).values() )
	return IECore.DataTraits.dataFromElement( values ) if values else None

def __optionPresets( plug ) :

	result = {}
	option = plug.parent()["name"].getValue()
	source = "option:{}".format( option )

	for n in Gaffer.Metadata.registeredValues( source ) :
		if n.startswith( "preset:" ) :
			result[n[7:]] = Gaffer.Metadata.value( source, n )

	presetNames = Gaffer.Metadata.value( source, "presetNames" )
	presetValues = Gaffer.Metadata.value( source, "presetValues" )
	if presetNames and presetValues :
		for presetName, presetValue in zip( presetNames, presetValues ) :
			result.setdefault( presetName, presetValue )

	return result

Gaffer.Metadata.registerNode(

	GafferScene.Options,

	"description",
	"""
	The base type for nodes that apply options to the scene.
	""",

	plugs = {

		"options" : {

			"description" :
			"""
			The options to be applied - arbitrary numbers of user defined options may be added
			as children of this plug via the user interface, or using the CompoundDataPlug API via
			python.
			""",

			"layout:customWidget:addButton:visibilityActivator" : False,

		},

		"options.*" : {

			"nameValuePlugPlugValueWidget:ignoreNamePlug" : True,

			"description" : lambda plug : _optionMetadata( plug, "description" ),
			"label" : lambda plug : _optionMetadata( plug, "label" ),
			"layout:section" : lambda plug : _optionMetadata( plug, "layout:section" ),

		},

		"options.*.value" : {

			"plugValueWidget:type" : lambda plug : _optionMetadata( plug, "plugValueWidget:type" ),
			"presetNames" : _optionPresetNames,
			"presetValues" : _optionPresetValues,
			"presetsPlugValueWidget:allowCustom" : lambda plug : _optionMetadata( plug, "presetsPlugValueWidget:allowCustom" ),
			"path:leaf" : lambda plug : _optionMetadata( plug, "path:leaf" ),
			"path:valid" : lambda plug : _optionMetadata( plug, "path:valid" ),
			"fileSystemPath:extensions" : lambda plug : _optionMetadata( plug, "fileSystemPath:extensions" ),
			"fileSystemPath:extensionsLabel" : lambda plug : _optionMetadata( plug, "fileSystemPath:extensionsLabel" ),
			"scenePathPlugValueWidget:setNames" : lambda plug : _optionMetadata( plug, "scenePathPlugValueWidget:setNames" ),
			"scenePathPlugValueWidget:setsLabel" : lambda plug : _optionMetadata( plug, "scenePathPlugValueWidget:setsLabel" ),

		},

		"extraOptions" : {

			"description" :
			"""
			An additional set of options to be added. Arbitrary numbers
			of options may be specified within a single `IECore.CompoundObject`,
			where each key/value pair in the object defines an option.
			This is convenient when using an expression to define the options
			and the option count might be dynamic. It can also be used to
			create options whose type cannot be handled by the `options`
			CompoundDataPlug.

			If the same option is defined by both the `options` and the
			`extraOptions` plugs, then the value from the `extraOptions`
			is taken.
			""",

			"plugValueWidget:type" : "",
			"layout:section" : "Extra",
			"nodule:type" : "",

		},

	}

)
