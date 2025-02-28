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

import functools
from xml.etree import cElementTree

import imath

import IECore

import Gaffer

## Parses a RenderMan `.args` file, converting it to a dictionary
# using Gaffer's standard metadata conventions :
#
# ```
# {
#	"description" : ...,
#	"parameters" : {
# 		"parameter1" : {
#       	"description" : ...
#       	"plugValueWidget:type" : ...
#           ...
#		}
#   }
# }
# ```
def parseMetadata( argsFile ) :

	result = { "parameters" : {} }

	pageStack = []
	currentParameter = None
	for event, element in cElementTree.iterparse( argsFile, events = ( "start", "end" ) ) :

		if element.tag == "page" :

			if event == "start" :
				pageStack.append( element.attrib["name"] )
			else :
				pageStack.pop()

		elif element.tag == "param" :

			if event == "start" :

				currentParameter = {}
				result["parameters"][element.attrib["name"]] = currentParameter

				# We need to know the parameter type to be able to parse presets and
				# default values. There are two different ways this is defined, so try
				# to normalise on the "Sdr" type.
				currentParameter["__type"] = element.attrib.get( "sdrUsdDefinitionType" )
				if currentParameter["__type"] is None :
					currentParameter["__type"] = element.attrib["type"] + element.attrib.get( "arraySize", "" )

				currentParameter["label"] = element.attrib.get( "label" )
				currentParameter["description"] = element.attrib.get( "help" )
				currentParameter["layout:section"] = ".".join( pageStack )
				currentParameter["plugValueWidget:type"] = __widgetTypes.get( element.attrib.get( "widget" ) )

				if element.attrib.get( "connectable", "true" ).lower() == "false" or currentParameter["plugValueWidget:type"] == "" :
					currentParameter["nodule:type"] = ""
				elif element.attrib.get( "isDynamicArray" ) == "1" :
					currentParameter["nodule:type"] = "GafferUI::CompoundNodule"

				defaultValue = __parseValue( element.attrib.get( "default" ), currentParameter["__type"] )
				if defaultValue is not None :
					currentParameter["defaultValue"] = defaultValue

				if element.attrib.get( "options" ) :
					__parsePresets( element.attrib.get( "options" ), currentParameter )

			elif event == "end" :

				del currentParameter["__type"] # Implementation detail not for public consumption
				currentParameter = None

		elif element.tag == "help" and event == "end" :

			if currentParameter :
				currentParameter["description"] = element.text
			else :
				result["description"] = element.text

		elif element.tag == "hintdict" and element.attrib.get( "name" ) == "options" :
			if event == "end" :
				__parsePresets( element, currentParameter )

	return result

## Parses a RenderMan `.args` file, registering Gaffer metadata for all its parameters
# against targets named `{targetPrefix}{parameterName}`.
def registerMetadata( argsFile, targetPrefix, parametersToIgnore = set() ) :

	metadata = parseMetadata( argsFile )
	for name, values in metadata["parameters"].items() :

		if name in parametersToIgnore :
			continue

		target = f"{targetPrefix}{name}"
		for key, value in values.items() :
			Gaffer.Metadata.registerValue( target, key, value )

__widgetTypes = {
	"number" : "GafferUI.NumericPlugValueWidget",
	"string" : "GafferUI.StringPlugValueWidget",
	"boolean" : "GafferUI.BoolPlugValueWidget",
	"checkBox" : "GafferUI.BoolPlugValueWidget",
	"popup" : "GafferUI.PresetsPlugValueWidget",
	"mapper" : "GafferUI.PresetsPlugValueWidget",
	"filename" : "GafferUI.PathPlugValueWidget",
	"assetIdInput" : "GafferUI.PathPlugValueWidget",
	"null" : "",
}

def __boolParser( string ) :

	return bool( int( string ) )

def __floatParser( string ) :

	if string.endswith( "f" ) :
		string = string[:-1]

	return float( string )

def __vectorParser( string, vectorType, baseType ) :

	return vectorType( *[ baseType( x ) for x in string.split() ] )

def __stringVectorDataParser( string ) :

	return IECore.StringVectorData( string.split( "," ) )

__valueParsers = {
	"bool" : __boolParser,
	"int" : int,
	"float" : __floatParser,
	"string" : str,
	"int2" : functools.partial( __vectorParser, vectorType = imath.V2i, baseType = int ),
	"float2" : functools.partial( __vectorParser, vectorType = imath.V2f, baseType = float ),
	"float3" : functools.partial( __vectorParser, vectorType = imath.V3f, baseType = float ),
	"float4" : functools.partial( __vectorParser, vectorType = imath.V4f, baseType = float ),
	"point" : functools.partial( __vectorParser, vectorType = imath.V3f, baseType = float ),
	"vector" : functools.partial( __vectorParser, vectorType = imath.V3f, baseType = float ),
	"normal" : functools.partial( __vectorParser, vectorType = imath.V3f, baseType = float ),
	"color" : functools.partial( __vectorParser, vectorType = imath.Color3f, baseType = float ),
	"string2" : __stringVectorDataParser,
}

def __parseValue( string, parameterType ) :

	if string is None :
		return None

	parser = __valueParsers.get( parameterType )
	if parser is None :
		return None

	try :
		return parser( string )
	except :
		return None

__presetContainers = {
	"int" : IECore.IntVectorData,
	"float" : IECore.FloatVectorData,
	"string" : IECore.StringVectorData,
}

def __parsePresets( options, parameter ) :

	containerType = __presetContainers.get( parameter["__type"] )
	if containerType is None :
		return

	presetNames = IECore.StringVectorData()
	presetValues = containerType()

	if isinstance( options, str ) :
		for option in options.split( "|" ) :
			optionSplit = option.split( ":" )
			if len( optionSplit ) == 2 :
				name = optionSplit[0]
				value = __parseValue( optionSplit[1], parameter["__type"] )
			else :
				assert( len( optionSplit ) == 1 )
				name = IECore.CamelCase.toSpaced( optionSplit[0] )
				value = __parseValue( optionSplit[0], parameter["__type"] )
			presetNames.append( name )
			presetValues.append( value )
	else :
		# Hint dict
		for option in options :
			value = option.attrib["value"]
			name = option.attrib.get( "name" )
			if name is None :
				name = IECore.CamelCase.toSpaced( value )
			presetNames.append( name )
			presetValues.append( __parseValue( value, parameter["__type"] ) )

	parameter["presetNames"] = presetNames
	parameter["presetValues"] = presetValues
