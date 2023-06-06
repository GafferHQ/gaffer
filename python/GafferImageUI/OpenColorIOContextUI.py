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

import imath

import Gaffer
import GafferUI
import GafferImage

##########################################################################
# Metadata
##########################################################################

Gaffer.Metadata.registerNode(

	GafferImage.OpenColorIOContext,

	"description",
	"""
	Creates Gaffer context variables which define the OpenColorIO config
	to be used by upstream nodes. This allows different configs to be used
	in different contexts.
	""",

	"layout:section:Settings.Variables:collapsed", False,

	plugs = {

		"in" : [

			"plugValueWidget:type", "",

		],

		"out" : [

			"plugValueWidget:type", "",

		],

		"config" : [

			"description",
			"""
			The OpenColorIO config to use.
			""",

			"nodule:type", "",
			"plugValueWidget:type", "GafferUI.LayoutPlugValueWidget",
			"layoutPlugValueWidget:orientation", "horizontal",

		],

		"config.enabled" : [

			"description",
			"""
			Enables the `config.value` plug, allowing the OpenColorIO config
			to be specified.
			""",

			"nodule:type", "",
			"boolPlugValueWidget:displayMode", "switch",
			"label", "",

		],

		"config.value" : [

			"description",
			"""
			Specifies the OpenColorIO config to be used.
			""",

			"nodule:type", "",
			"label", "",
			"layout:activator", lambda plug : plug.parent()["enabled"].getValue(),
			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
			"presetsPlugValueWidget:allowCustom", True,

			"preset:$OCIO", "",
			"preset:ACES 1.3 - CG Config", "ocio://cg-config-v1.0.0_aces-v1.3_ocio-v2.1",
			"preset:ACES 1.3 - Studio Config", "ocio://studio-config-v1.0.0_aces-v1.3_ocio-v2.1",

		],

		"variables" : [

			"description",
			"""
			Context variables used to customise the
			[OpenColorIO context](https://opencolorio.readthedocs.io/en/latest/guides/authoring/overview.html#environment)
			used by upstream nodes. OpenColorIO refers to these variously as "string vars", "context vars" or
			"environment vars".
			""",

			"plugValueWidget:type", "GafferUI.LayoutPlugValueWidget",
			"layout:section", "Settings.Variables",
			"nodule:type", "",

			"layout:customWidget:footer:widgetType", "GafferImageUI.OpenColorIOContextUI._VariablesFooter",
			"layout:customWidget:footer:index", -1,

		],

		"variables.*.name" : [

			"description",
			"""
			The name of the variable to be created.
			""",

		],

		"variables.*.value" : [

			"description",
			"""
			The value to be given to the variable.
			""",

		],

		"extraVariables" : [

			"description",
			"""
			An additional set of variables to be created. These are defined as
			key/value pairs in an `IECore::CompoundData` object, which
			allows a single expression to define a dynamic number of variables.

			If the same variable is defined by both the `variables` and the
			`extraVariables` plugs, then the value from the `variables` plug
			is taken.
			""",

			"layout:section", "Extra",
			"nodule:type", "",

		],

	}

)

class _VariablesFooter( GafferUI.PlugValueWidget ) :

	def __init__( self, plug ) :

		row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal )

		GafferUI.PlugValueWidget.__init__( self, row, plug )

		with row :

			GafferUI.Spacer( imath.V2i( GafferUI.PlugWidget.labelWidth(), 1 ) )

			self.__addButton = GafferUI.Button( image = "plus.png", hasFrame = False )
			self.__addButton.clickedSignal().connect( Gaffer.WeakMethod( self.__addVariable ), scoped = False )

			GafferUI.Spacer( imath.V2i( 1 ), imath.V2i( 999999, 1 ), parenting = { "expand": True } )

	def _updateFromEditable( self ) :

		self.__addButton.setEnabled( not Gaffer.MetadataAlgo.readOnly( self.getPlug() ) )

	def __addVariable( self, *unused ) :

		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			self.getPlug().addChild(
				Gaffer.NameValuePlug(
					name = "variable0", nameDefault = "", defaultEnabled = True, valueDefault = "",
					flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic
				)
			)
