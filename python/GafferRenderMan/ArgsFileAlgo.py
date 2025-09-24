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
import inspect
import re
from xml.etree import ElementTree

import imath

import IECore

import Gaffer

## Parses a RenderMan `.args` file, registering Gaffer metadata for it and all its parameters.
# Returns the target for the metadata registrations, which is automatically determined from
# the `shaderType` declared by the args file.
def registerMetadata( argsFile, parametersToIgnore = set() ) :

	pageStack = []
	target = None
	targetDescription = ""
	currentParameterTarget = None
	currentParameterType = None
	for event, element in ElementTree.iterparse( argsFile, events = ( "start", "end" ) ) :

		if element.tag == "shaderType" and event == "end" :

			assert( target is None )

			tag = element.find( "tag" )
			pluginType = tag.attrib.get( "value" ) if tag is not None else None

			target = {
				"bxdf" : "ri:surface:{name}",
				"pattern" : "ri:shader:{name}",
				"light" : "ri:light:{name}",
				"displayfilter" : "ri:displayfilter:{name}",
				"samplefilter" : "ri:samplefilter:{name}",
				"lightfilter" : "ri:lightFilter:{name}",
				"integrator" : "ri:integrator:{name}",
				"options" : "option:ri",
				"attributes" : "attribute:ri",
				"primvar" : "attribute:ri",
			}.get( pluginType )

			if target is None :
				return None

			target = target.format( name = argsFile.stem )

		elif element.tag == "page" :

			if event == "start" :
				pageStack.append( element.attrib["name"] )
			else :
				pageStack.pop()

		elif element.tag == "param" :

			if event == "start" :

				if element.attrib["name"] in parametersToIgnore :
					continue

				currentParameterTarget = "{}:{}".format( target, element.attrib["name"] )

				# We need to know the parameter type to be able to parse presets and
				# default values. There are two different ways this is defined, so try
				# to normalise on the "Sdr" type.
				currentParameterType = element.attrib.get( "sdrUsdDefinitionType" )
				if currentParameterType is None :
					currentParameterType = element.attrib["type"] + element.attrib.get( "arraySize", "" )

				Gaffer.Metadata.registerValue( currentParameterTarget, "label", element.attrib.get( "label" ) )
				Gaffer.Metadata.registerValue( currentParameterTarget, "description", element.attrib.get( "help" ) )
				Gaffer.Metadata.registerValue( currentParameterTarget, "layout:section", ".".join( pageStack ) )
				Gaffer.Metadata.registerValue( currentParameterTarget, "plugValueWidget:type", __widgetTypes.get( element.attrib.get( "widget" ) ) )

				if element.attrib.get( "connectable", "true" ).lower() == "false" or element.attrib.get( "widget" ) == "null" :
					Gaffer.Metadata.registerValue( currentParameterTarget, "nodule:type", "" )
				elif element.attrib.get( "isDynamicArray" ) == "1" :
					Gaffer.Metadata.registerValue( currentParameterTarget, "nodule:type", "GafferUI::CompoundNodule" )

				for key in ( "default", "min", "max" ) :
					value = __parseValue( element.attrib.get( key ), currentParameterType )
					if value is not None :
						Gaffer.Metadata.registerValue( currentParameterTarget, f"{key}Value", value )

				if element.attrib.get( "options" ) :
					__parsePresets( element.attrib.get( "options" ), currentParameterTarget, currentParameterType )

				__parseConditionalVisibility( element, currentParameterTarget )

			elif event == "end" :

				currentParameterTarget = None
				currentParameterType = None

		elif element.tag == "help" and event == "end" :

			# Using `partial()` to defer processing of description until it is queried,
			# since it relatively expensive.
			description = functools.partial( __cleanDescription, currentParameterTarget, element )
			if currentParameterTarget is not None :
				Gaffer.Metadata.registerValue( currentParameterTarget or target, "description", description )
			else :
				# We may not have the `target` yet, because a couple of files don't
				# specify `shaderType` first. Store it and register at the end.
				targetDescription = description

		elif element.tag == "hintdict" and event == "end" and currentParameterTarget :
			if element.attrib.get( "name" ) == "options" :
				__parsePresets( element, currentParameterTarget, currentParameterType )
			elif element.attrib.get( "name" ) == "conditionalVisOps" :
				__parseConditionalVisibility( element, currentParameterTarget )

		elif element.tag == "rfhdata" and event == "end" :
			Gaffer.Metadata.registerValue( target, "classification", element.attrib.get( "classification" ) )

	Gaffer.Metadata.registerValue( target, "description", targetDescription )
	return target

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

def __parsePresets( options, parameterTarget, parameterType ) :

	containerType = __presetContainers.get( parameterType )
	if containerType is None :
		return

	presetNames = IECore.StringVectorData()
	presetValues = containerType()

	if isinstance( options, str ) :
		for option in options.split( "|" ) :
			optionSplit = option.split( ":" )
			if len( optionSplit ) == 2 :
				name = optionSplit[0]
				value = __parseValue( optionSplit[1], parameterType )
			else :
				assert( len( optionSplit ) == 1 )
				name = IECore.CamelCase.toSpaced( optionSplit[0] )
				value = __parseValue( optionSplit[0], parameterType )
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
			presetValues.append( __parseValue( value, parameterType ) )

	Gaffer.Metadata.registerValue( parameterTarget, "presetNames", presetNames )
	Gaffer.Metadata.registerValue( parameterTarget, "presetValues", presetValues )

def __parseConditionalVisibility( source, parameterTarget ) :

	# Register conditional visibility metadata using an `ri:` prefix on the key,
	# since this isn't a Gaffer-native format. This metadata is picked up by
	# RenderManShaderUI and translated into Gaffer's standard `layout:activator`
	# and `layout:visibilityActivator` metadata on the fly.

	if source.tag == "hintdict" :
		# Visibility definition neatly confined in `hintdict`, where all child
		# elements are relevant.
		for element in source :
			Gaffer.Metadata.registerValue( parameterTarget, "ri:{}".format( element.attrib["name"] ), element.attrib["value"] )
	else :
		# Visibility defined via attributes on param. Since we can't identify
		# all relevant attributes by name alone, we must discover them by
		# following the "parse tree".
		assert( source.tag == "param" )
		prefixes = [ "conditionalVis", "conditionalLock" ]
		while prefixes :
			prefix = prefixes.pop()
			for suffix in [ "Op", "Left", "Right", "Path", "Value" ] :
				name = f"{prefix}{suffix}"
				value = source.attrib.get( name )
				if value is not None :
					Gaffer.Metadata.registerValue( parameterTarget, "ri:{}".format( name ), value )
					if suffix in [ "Left", "Right" ] :
						prefixes.append( value )

def __cleanDescription( parameterTarget, element ) :

	description = ElementTree.tostring( element, encoding = "unicode", method = "html" ).strip()
	description = description.removeprefix( "<help>" )
	description = description.removesuffix( "</help>" )
	description = inspect.cleandoc( description )

	if parameterTarget is not None :
		# Several descriptions start with `{parameterName}:`, which is redundant
		# everywhere it is presented in Gaffer. Strip it out, being careful to
		# maintain any preceding `<p>` tag.
		parameterName = parameterTarget.rpartition( ":" )[-1]
		description = re.sub( rf"^(\<p\>\n?|){parameterName}:", r"\g<1>", description )

	return description
