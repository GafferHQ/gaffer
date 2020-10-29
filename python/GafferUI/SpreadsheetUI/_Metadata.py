##########################################################################
#
#  Copyright (c) 2019, Image Engine Design Inc. All rights reserved.
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

import IECore

import Gaffer

# Metadata registration
# ---------------------
#
# This covers the main UI registration, along with any additional metadata
# for Spreadsheet child plugs.

Gaffer.Metadata.registerNode(

	Gaffer.Spreadsheet,

	"description",
	"""
	Provides a spreadsheet designed for easy management of sets of
	associated plug values. Each column of the spreadsheet corresponds
	to an output value that can be connected to drive a plug on another
	node. Each row of the spreadsheet provides candidate values for each
	output, along with a row name and enabled status. Row names are matched
	against a selector to determine which row is passed through to the output.
	Row matching is performed as follows :

	- Matching starts with the second row and considers all subsequent
	  rows one by one until a match is found. The first matching row
	  is the one that is chosen.
	- Matching is performed using Gaffer's standard wildcard matching.
	  Each "name" may contain several individual patterns each separated
	  by spaces.
	- The first row is used as a default, and is chosen only if no other
	  row matches.

	> Note : The matching rules are identical to the ones used by the
	> NameSwitch node.
	""",

	"nodeGadget:type", "GafferUI::AuxiliaryNodeGadget",
	"nodeGadget:shape", "oval",
	"uiEditor:nodeGadgetTypes", IECore.StringVectorData( [ "GafferUI::AuxiliaryNodeGadget", "GafferUI::StandardNodeGadget" ] ),
	"auxiliaryNodeGadget:label", "#",

	plugs = {

		"*" : [

			"nodule:type", "",

		],

		"selector" : [

			"description",
			"""
			The value that the row names will be matched against.
			Typically this will refer to a Context Variable using
			the `${variableName}` syntax.
			""",

			"divider", True,

		],

		"rows" : [

			"description",
			"""
			Holds a child RowPlug for each row in the spreadsheet.
			""",

		],

		"rows.default" : [

			"description",
			"""
			The default row. This provides output values when no other
			row matches the `selector`.
			""",

		],

		"rows.*.name" : [

			"description",
			"""
			The name of the row. This is matched against the `selector`
			to determine which row is chosen to be passed to the output.
			May contain multiple space separated names and any of Gaffer's
			standard wildcards.
			""",

		],

		"rows.*.enabled" : [

			"description",
			"""
			Enables or disables this row. Disabled rows are ignored.
			""",

		],

		"rows.*.cells" : [

			"description",
			"""
			Contains a child CellPlug for each column in the spreadsheet.
			""",

		],

		"out" : [

			"description",
			"""
			The outputs from the spreadsheet. Contains a child plug for each
			column in the spreadsheet.
			""",

			"plugValueWidget:type", "",

		],

		"activeRowNames" : [

			"description",
			"""
			An output plug containing the names of all currently active rows.
			""",

			"plugValueWidget:type", "",

		],

	}

)

# Metadata methods
# ================
#
# We don't want to copy identical metadata onto every cell of the spreadsheet, as
# that's a lot of pointless duplication. Instead we register metadata onto the
# default row only, and then mirror it dynamically onto the other rows. This isn't
# flawless because we can only mirror metadata we know the names for in advance, but
# since we only support a limited subset of widgets in the spreadsheet it seems
# workable.

def __correspondingDefaultPlug( plug ) :

	rowPlug = plug.ancestor( Gaffer.Spreadsheet.RowPlug )
	rowsPlug = rowPlug.parent()
	return rowsPlug.defaultRow().descendant( plug.relativeName( rowPlug ) )

def __defaultCellMetadata( plug, key ) :

	return Gaffer.Metadata.value( __correspondingDefaultPlug( plug ), key )

for key in [
	"spreadsheet:columnLabel",
	"plugValueWidget:type",
	"presetsPlugValueWidget:allowCustom"
] :

	Gaffer.Metadata.registerValue(
		Gaffer.Spreadsheet.RowsPlug, "row*.cells...", key,
		functools.partial( __defaultCellMetadata, key = key ),
	)

# Presets are tricky because we can't know their names in advance. We register
# "presetNames" and "presetValues" arrays that we can use to gather all "preset:*"
# metadata into on the fly.

__plugPresetTypes = {

	Gaffer.IntPlug : IECore.IntVectorData,
	Gaffer.FloatPlug : IECore.FloatVectorData,
	Gaffer.StringPlug : IECore.StringVectorData,
	Gaffer.V3fPlug : IECore.V3fVectorData,
	Gaffer.V2fPlug : IECore.V2fVectorData,
	Gaffer.V3iPlug : IECore.V3iVectorData,
	Gaffer.V2iPlug : IECore.V2iVectorData,
	Gaffer.Color3fPlug : IECore.Color3fVectorData,
	Gaffer.Color4fPlug : IECore.Color4fVectorData,

}

def __presetNamesMetadata( plug ) :

	if plug.__class__ not in __plugPresetTypes :
		return None

	source = __correspondingDefaultPlug( plug )

	result = IECore.StringVectorData()
	for n in Gaffer.Metadata.registeredValues( source ) :
		if n.startswith( "preset:" ) :
			result.append( n[7:] )

	result.extend( Gaffer.Metadata.value( source, "presetNames" ) or [] )
	return result

def __presetValuesMetadata( plug ) :

	dataType = __plugPresetTypes.get( plug.__class__ )
	if dataType is None :
		return None

	source = __correspondingDefaultPlug( plug )

	result = dataType()
	for n in Gaffer.Metadata.registeredValues( source ) :
		if n.startswith( "preset:" ) :
			result.append( Gaffer.Metadata.value( source, n ) )

	result.extend( Gaffer.Metadata.value( source, "presetValues" ) or [] )
	return result

Gaffer.Metadata.registerValue( Gaffer.Spreadsheet.RowsPlug, "row*.cells...", "presetNames", __presetNamesMetadata )
Gaffer.Metadata.registerValue( Gaffer.Spreadsheet.RowsPlug, "row*.cells...", "presetValues", __presetValuesMetadata )
