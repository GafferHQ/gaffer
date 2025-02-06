##########################################################################
#
#  Copyright (c) 2018, Alex Fuller. All rights reserved.
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

import functools
import collections

import IECore

import Gaffer
import GafferUI
import GafferCycles
import GafferImage
import GafferImageUI

##########################################################################
# Build a registry of information retrieved from GafferCycles metadata.
##########################################################################

def __outPlugNoduleType( plug ) :

	return "GafferUI::CompoundNodule" if len( plug ) else "GafferUI::StandardNodule"

def __getSocketToComponents( socketType ) :
	if( socketType == "point2" ) :
		return "xy"
	elif( socketType == "vector" ) :
		return "xyz"
	elif( socketType == "point" ) :
		return "xyz"
	elif( socketType == "normal" ) :
		return "xyz"
	elif( socketType == "color" ) :
		return "rgb"
	else :
		return None

__metadata = collections.defaultdict( dict )

def __translateParamMetadata( nodeTypeName, socketName, value ) :
	paramPath = nodeTypeName + ".parameters." + socketName
	socketType = value["type"].value
	if socketType == "enum" :
		presetNames = IECore.StringVectorData()
		presetValues = IECore.StringVectorData()
		for enumName, enumValues in value["enum_values"].items() :
			presetNames.append(enumName)
			presetValues.append( enumValues.value )
		__metadata[paramPath]["presetNames"] = presetNames
		__metadata[paramPath]["presetValues"] = presetValues
		__metadata[paramPath]["plugValueWidget:type"] = "GafferUI.PresetsPlugValueWidget"

	if( socketName == "filename" ) :
		__metadata[paramPath]["plugValueWidget:type"] = "GafferUI.FileSystemPathPlugValueWidget"
		__metadata[paramPath]["path:leaf"] = True
		__metadata[paramPath]["path:valid"] = True
		__metadata[paramPath]["path:bookmarks"] = "texture"
		__metadata[paramPath]["fileSystemPath:extensions"] = " ".join( GafferImage.OpenImageIOReader.supportedExtensions() )
		__metadata[paramPath]["fileSystemPath:extensionsLabel"] = "Show only image files"

	__metadata[paramPath]["noduleLayout:visible"] = True
	label = value["ui_name"].value
	__metadata[paramPath]["label"] = label
	__metadata[paramPath]["noduleLayout:label"] = label
	# Linkable
	linkable = bool( value["flags"].value & ( 1 << 0 ) )
	__metadata[paramPath]["nodule:type"] = "" if not linkable else None # "" disables the nodule, and None falls through to the default

	if "category" in value :
		__metadata[paramPath]["layout:section"] = value["category"]

	childComponents = __getSocketToComponents( socketType )
	if childComponents is not None :
		for c in childComponents :
			__metadata["{}.{}".format( paramPath, c )]["noduleLayout:label"] = "{}.{}".format( label, c )

def __translateNodesMetadata( nodeTypes ) :

	for nodeTypeName, nodeType in nodeTypes.items() :
		# Inputs
		for socketName, value in nodeType["in"].items() :
			__translateParamMetadata( nodeTypeName, socketName, value )

__translateNodesMetadata( GafferCycles.lights )
__translateNodesMetadata( GafferCycles.shaders )

# hide the light type
for nodeTypeName, nodeType in GafferCycles.lights.items() :
	paramPath = nodeTypeName + ".parameters.type"
	__metadata[paramPath]["noduleLayout:visible"] = False

# Add OCIO colorspace menus where appropriate. There doesn't seem to be anywhere
# we can query this from the Cycles API, so we just hardcode it to shaders know about.

for parameter in [ "image_texture.parameters.colorspace", "environment_texture.parameters.colorspace" ] :
	# Here we're assuming that Cycles is being used with an OCIO config that matches Gaffer's.
	__metadata[parameter]["plugValueWidget:type"] = "GafferUI.PresetsPlugValueWidget"
	__metadata[parameter]["presetNames"] = GafferImageUI.OpenColorIOTransformUI.colorSpacePresetNames
	__metadata[parameter]["presetValues"] = GafferImageUI.OpenColorIOTransformUI.colorSpacePresetValues
	__metadata[parameter]["openColorIO:extraPresetNames"] = IECore.StringVectorData( [ "Auto" ] )
	__metadata[parameter]["openColorIO:extraPresetValues"] = IECore.StringVectorData( [ "" ] )
	__metadata[parameter]["openColorIO:includeRoles"] = True
	# Allow custom values in case Cycles has been configured to use some other OCIO config.
	__metadata[parameter]["presetsPlugValueWidget:allowCustom"] = True

##########################################################################
# Gaffer Metadata queries. These are implemented using the preconstructed
# registry above.
##########################################################################

def __nodeDescription( node ) :

	if isinstance( node, GafferCycles.CyclesShader ) :
		return __metadata[node["name"].getValue()].get(
			"description",
			"""Loads shaders for use in Cycles renders. Use the ShaderAssignment node to assign shaders to objects in the scene.""",
		)
	else :
		return __metadata[node["__shader"]["name"].getValue()].get(
			"description",
			"""Loads an Cycles light shader and uses it to output a scene with a single light."""
		)

def __nodeMetadata( node, name ) :

	if isinstance( node, GafferCycles.CyclesShader ) :
		key = node["name"].getValue()
	else :
		# Node type is CyclesLight.
		key = node["__shader"]["name"].getValue()

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
	if isinstance( node, GafferCycles.CyclesShader ) :
		key = plug.node()["name"].getValue() + "." + plug.relativeName( node )
	else :
		# Node type is CyclesLight.
		key = plug.node()["__shader"]["name"].getValue() + "." + plug.relativeName( node )

	result = __metadata[key].get( name )
	if callable( result ) :
		return result( plug )
	else :
		return result

for nodeType in ( GafferCycles.CyclesShader, GafferCycles.CyclesLight ) :

	nodeKeys = set()
	parametersPlugKeys = set()
	parameterPlugKeys = set()
	parameterPlugComponentKeys = set()

	for name, metadata in __metadata.items() :
		keys = ( nodeKeys, parametersPlugKeys, parameterPlugKeys, parameterPlugComponentKeys )[name.count( ".")]
		keys.update( metadata.keys() )

	for key in nodeKeys :
		Gaffer.Metadata.registerValue( nodeType, key, functools.partial( __nodeMetadata, name = key ) )

	for key in parametersPlugKeys :
		Gaffer.Metadata.registerValue( nodeType, "parameters", key, functools.partial( __plugMetadata, name = key ) )

	for key in parameterPlugKeys :
		Gaffer.Metadata.registerValue( nodeType, "parameters.*", key, functools.partial( __plugMetadata, name = key ) )

	for key in parameterPlugComponentKeys :
		Gaffer.Metadata.registerValue( nodeType, "parameters.*.[xyzrgb]", key, functools.partial( __plugMetadata, name = key ) )

	Gaffer.Metadata.registerValue( nodeType, "description", __nodeDescription )

Gaffer.Metadata.registerNode(

	GafferCycles.CyclesShader,

	plugs = {

		"out" : [

			"nodule:type", __outPlugNoduleType,
			"noduleLayout:spacing", 0.2,

		],

		"out.*" : [

			"noduleLayout:visible", True,

		]
	}
)
