##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
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

import re
import ctypes
import functools
import collections

import arnold

import IECore
import IECoreArnold

import Gaffer
import GafferUI
import GafferArnold

##########################################################################
# Utilities to make it easier to work with the Arnold API, which has a
# fairly bare wrapping using ctypes.
##########################################################################

def __aiMetadataGetStr( nodeEntry, paramName, name, defaultValue = None ) :

	value = arnold.AtStringReturn()
	if arnold.AiMetaDataGetStr( nodeEntry, paramName, name, value ) :
		return arnold.AtStringToStr( value )

	return defaultValue

def __aiMetadataGetBool( nodeEntry, paramName, name, defaultValue = None ) :

	value = ctypes.c_bool()
	if arnold.AiMetaDataGetBool( nodeEntry, paramName, name, value ) :
		return bool( value )

	return defaultValue

##########################################################################
# Build a registry of information retrieved from Arnold metadata. We fill this
# once at startup, as we can only get it from within an AiUniverse block,
# and we don't want to have to keep making those temporarily later.
#
# We take a pragmatic approach to what metadata we support, since there
# are multiple conflicting "standards" in use in practice. In order of
# precedence (most important first), we aim to support the following :
#
# - Arnold's metadata convention. This doesn't define much, but gives
#   us min/max/desc/linkable.
# - The OSL metadata convention. This gives us a bit more, and is also
#   the convention we support already for RSL and OSL shaders.
#
# The alternative to this would be to add one more "standard" by defining
# a Gaffer-specific convention, and then contribute to the AlShaders
# project to add all the necessary metadata. This would be more work
# for no real gain.
##########################################################################

__metadata = collections.defaultdict( dict )

def __translateNodeMetadata( nodeEntry ) :

	nodeName = arnold.AiNodeEntryGetName( nodeEntry )

	# Shader description. We support Arnold-style "desc" and
	# OSL style "help".

	description = __aiMetadataGetStr( nodeEntry, None, "desc",
		defaultValue = __aiMetadataGetStr( nodeEntry, None, "help" )
	)
	if description is not None :
		__metadata[nodeName]["description"] = description

	# Documentation URL. We support OSL-style "URL"

	url = __aiMetadataGetStr( nodeEntry, None, "URL" )
	if url is not None :
		__metadata[nodeName]["documentation:url"] = url

	havePages = False
	paramIt = arnold.AiNodeEntryGetParamIterator( nodeEntry )
	while not arnold.AiParamIteratorFinished( paramIt ) :

		## \todo We could allow custom ui types to be specified using
		# arnold metadata entries.
		param = arnold.AiParamIteratorGetNext( paramIt )
		paramName = arnold.AiParamGetName( param )
		paramPath = nodeName + ".parameters." + paramName

		# Parameter description

		description = __aiMetadataGetStr( nodeEntry, paramName, "desc" )
		if description is not None :
			__metadata[paramPath]["description"] = description

		# Parameter presets from enum values

		paramType = arnold.AiParamGetType( param )
		if paramType == arnold.AI_TYPE_ENUM :

			enum = arnold.AiParamGetEnum( param )
			presets = IECore.StringVectorData()
			while True :
				preset = arnold.AiEnumGetString( enum, len( presets ) )
				if not preset :
					break
				presets.append( preset )

			__metadata[paramPath]["plugValueWidget:type"] = "GafferUI.PresetsPlugValueWidget"
			__metadata[paramPath]["presetNames"] = presets
			__metadata[paramPath]["presetValues"] = presets

		# Nodule type from linkable metadata and parameter type

		linkable = __aiMetadataGetBool(
			nodeEntry, paramName, "linkable",
			defaultValue = paramType not in (
				arnold.AI_TYPE_BYTE, arnold.AI_TYPE_INT, arnold.AI_TYPE_UINT,
				arnold.AI_TYPE_BOOLEAN, arnold.AI_TYPE_ENUM, arnold.AI_TYPE_STRING
			)
		)
		__metadata[paramPath]["nodule:type"] = "GafferUI::StandardNodule" if linkable else ""

		# PlugValueWidget type from OSL "widget"
		widget = None
		widget = __aiMetadataGetStr( nodeEntry, paramName, "widget", widget )
		if widget is not None :
			__metadata[paramPath]["plugValueWidget:type"] = {
				"number" : "GafferUI.NumericPlugValueWidget",
				"string" : "GafferUI.StringPlugValueWidget",
				"boolean" : "GafferUI.BoolPlugValueWidget",
				"checkBox" : "GafferUI.BoolPlugValueWidget",
				"popup" : "GafferUI.PresetsPlugValueWidget",
				"mapper" : "GafferUI.PresetsPlugValueWidget",
				"filename" : "GafferUI.PathPlugValueWidget",
				"null" : "",
			}[widget]

		# Layout section from OSL "page".

		page = __aiMetadataGetStr( nodeEntry, paramName, "page" )
		if page is not None :
			havePages = True
			__metadata[paramPath]["layout:section"] = page

		# Label from OSL "label"
		label = __aiMetadataGetStr( nodeEntry, paramName, "label", label )
		if label is not None :
			__metadata[paramPath]["label"] = label

		# NodeGraph visibility from Gaffer-specific metadata

		visible = __aiMetadataGetBool( nodeEntry, None, "gaffer.nodeGraphLayout.defaultVisibility" )
		visible = __aiMetadataGetBool( nodeEntry, paramName, "gaffer.nodeGraphLayout.visible", visible )
		if visible is not None :
			__metadata[paramPath]["noduleLayout:visible"] = visible

with IECoreArnold.UniverseBlock( writable = False ) :

	nodeIt = arnold.AiUniverseGetNodeEntryIterator( arnold.AI_NODE_SHADER | arnold.AI_NODE_LIGHT )
	while not arnold.AiNodeEntryIteratorFinished( nodeIt ) :

		__translateNodeMetadata( arnold.AiNodeEntryIteratorGetNext( nodeIt ) )

##########################################################################
# Gaffer Metadata queries. These are implemented using the preconstructed
# registry above.
##########################################################################

def __nodeDescription( node ) :

	if isinstance( node, GafferArnold.ArnoldShader ) :
		return __metadata[node["name"].getValue()].get(
			"description",
			"""Loads shaders for use in Arnold renders. Use the ShaderAssignment node to assign shaders to objects in the scene.""",
		)
	else :
		return __metadata[node["__shaderName"].getValue()].get(
			"description",
			"""Loads an Arnold light shader and uses it to output a scene with a single light."""
		)

def __nodeMetadata( node, name ) :

	if isinstance( node, GafferArnold.ArnoldShader ) :
		key = node["name"].getValue()
	else :
		# Node type is ArnoldLight.
		key = node["__shaderName"].getValue()

	return __metadata[key].get( name )

def __plugMetadata( plug, name ) :

	if name == "noduleLayout:visible" and plug.getInput() is not None :
		# Before the introduction of nodule visibility controls,
		# users may have made connections to plugs which are now
		# hidden by default. Make sure we continue to show them
		# by default - they can still be hidden explicitly by
		# adding an instance metadata value.
		return True

	node = plug.node()
	if isinstance( node, GafferArnold.ArnoldShader ) :
		key = plug.node()["name"].getValue() + "." + plug.relativeName( node )
	else :
		# Node type is ArnoldLight.
		key = plug.node()["__shaderName"].getValue() + "." + plug.relativeName( node )

	return __metadata[key].get( name )

for nodeType in ( GafferArnold.ArnoldShader, GafferArnold.ArnoldLight ) :

	nodeKeys = set()
	parametersPlugKeys = set()
	parameterPlugKeys = set()

	for name, metadata in __metadata.items() :
		keys = ( nodeKeys, parametersPlugKeys, parameterPlugKeys )[name.count( ".")]
		keys.update( metadata.keys() )

	for key in nodeKeys :
		Gaffer.Metadata.registerValue( nodeType, key, functools.partial( __nodeMetadata, name = key ) )

	for key in parametersPlugKeys :
		Gaffer.Metadata.registerValue( nodeType, "parameters", key, functools.partial( __plugMetadata, name = key ) )

	for key in parameterPlugKeys :
		Gaffer.Metadata.registerValue( nodeType, "parameters.*", key, functools.partial( __plugMetadata, name = key ) )

	Gaffer.Metadata.registerValue( nodeType, "description", __nodeDescription )


Gaffer.Metadata.registerValue( GafferArnold.ArnoldShader, "attributeSuffix", "plugValueWidget:type", "GafferUI.StringPlugValueWidget" )
Gaffer.Metadata.registerValue( GafferArnold.ArnoldShader, "layout:activator:suffixActivator", lambda parent : parent["type"].getValue() == "ai:lightFilter" )
Gaffer.Metadata.registerValue( GafferArnold.ArnoldShader, "attributeSuffix", "layout:visibilityActivator", "suffixActivator" )
