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

import ctypes
import functools
import collections

import arnold

import IECore
import IECoreArnold
import imath

import Gaffer
import GafferUI
import GafferImageUI
import GafferSceneUI
import GafferArnold

# Arnold shaders to add to the light editor.
lightEditorShaders = {
	# "shaderName" : ( "shaderAttributeName", "lightEditorSection" )
	"light_blocker" : ( "ai:lightFilter:filter", "Blocker" ),
	"barndoor" : ( "ai:lightFilter:barndoor", "Barndoor" ),
	"gobo" : ( "ai:lightFilter:gobo", "Gobo" ),
	"light_decay" : ( "ai:lightFilter:light_decay", "Decay" ),
}

##########################################################################
# Utilities to make it easier to work with the Arnold API, which has a
# fairly bare wrapping using ctypes.
##########################################################################

def __aiMetadataGetStr( nodeEntry, paramName, name, defaultValue = None ) :

	value = arnold.AtStringStruct()
	if arnold.AiMetaDataGetStr( nodeEntry, paramName, name, value ) :
		return arnold.AtStringToStr( value )

	return defaultValue

def __aiMetadataGetBool( nodeEntry, paramName, name, defaultValue = None ) :

	value = ctypes.c_bool()
	if arnold.AiMetaDataGetBool( nodeEntry, paramName, name, value ) :
		return bool( value )

	return defaultValue

def __aiMetadataGetInt( nodeEntry, paramName, name, defaultValue = None ) :

	value = ctypes.c_int()
	if arnold.AiMetaDataGetInt( nodeEntry, paramName, name, value ) :
		return int( value.value )

	return defaultValue

def __aiMetadataGetFlt( nodeEntry, paramName, name, defaultValue = None ) :

	value = ctypes.c_float()
	if arnold.AiMetaDataGetFlt( nodeEntry, paramName, name, value ) :
		return float( value.value )

	return defaultValue

def __aiMetadataGetRGB( nodeEntry, paramName, name, defaultValue = None ) :

	value = arnold.AtRGB()
	if arnold.AiMetaDataGetRGB( nodeEntry, paramName, name, value ) :
		return imath.Color3f( value.r, value.g, value.b )

	return defaultValue

# SolidAngle does not appear to have wrapped AiMetaDataGetRGBA in Python, so we don't
# support the RGBA case
"""
def __aiMetadataGetRGBA( nodeEntry, paramName, name, defaultValue = None ) :

	value = arnold.AtRGBA()
	if arnold.AiMetaDataGetRGBA( nodeEntry, paramName, name, value ) :
		return imath.Color4f( value.r, value.g, value.b, value.a )

	return defaultValue
"""

def __aiMetadataGetVec2( nodeEntry, paramName, name, defaultValue = None ) :

	value = arnold.AtVector2()
	if arnold.AiMetaDataGetVec2( nodeEntry, paramName, name, value ) :
		return imath.V2f( value.x, value.y )

	return defaultValue

def __aiMetadataGetVec( nodeEntry, paramName, name, defaultValue = None ) :

	value = arnold.AtVector()
	if arnold.AiMetaDataGetVec( nodeEntry, paramName, name, value ) :
		return imath.V3f( value.x, value.y, value.z )

	return defaultValue

def __enumPresetValues( param ):

	presets = IECore.StringVectorData()

	enum = arnold.AiParamGetEnum( param )
	while True :
		preset = arnold.AiEnumGetString( enum, len( presets ) )
		if not preset :
			break
		presets.append( preset )

	return presets

def __plugPresetNames( nodeEntry, paramName ) :

	# options STRING "name:value|..."

	options = __aiMetadataGetStr( nodeEntry, paramName, "options" )
	if options :
		return IECore.StringVectorData( [ o.partition( ":" )[0] for o in options.split( "|" ) if o ] )

def __plugPresetValues( nodeEntry, paramName, paramType ) :

	# options STRING "name:value|..."

	options = __aiMetadataGetStr( nodeEntry, paramName, "options" )
	if not options :
		return None

	values = [ o.rpartition( ":" )[2] for o in options.split( "|" ) if o ]

	if paramType == arnold.AI_TYPE_STRING :
		return IECore.StringVectorData( values )
	elif paramType in ( arnold.AI_TYPE_INT, arnold.AI_TYPE_BYTE ) :
		return IECore.IntVectorData( [ int( v ) for v in values ] )
	elif paramType == arnold.AI_TYPE_UINT :
		return IECore.UIntVectorData( [ int( v ) for v in values ] )
	elif paramType == arnold.AI_TYPE_FLOAT :
		return IECore.FloatVectorData( [ float( v ) for v in values ] )
	elif paramType == arnold.AI_TYPE_BOOLEAN :
		falseVals = ( "false", "no", "0" )
		return IECore.BoolVectorData( [ False if v.lower() in falseVals else True for v in values ] )
	elif paramType == arnold.AI_TYPE_RGB :
		return IECore.Color3fVectorData( [ imath.Color3f( *[ float( x ) for x in v.split( "," ) ]) for v in values ] )
	elif paramType == arnold.AI_TYPE_RGBA :
		return IECore.Color4fVectorData( [ imath.Color4f( *[ float( x ) for x in v.split( "," ) ]) for v in values ] )
	elif paramType in ( arnold.AI_TYPE_VECTOR, arnold.AI_TYPE_POINT ):
		return IECore.V3fVectorData( [ imath.V3f( *[ float( x ) for x in v.split( "," ) ]) for v in values ] )
	elif paramType == arnold.AI_TYPE_POINT2 :
		return IECore.V2fVectorData( [ imath.V2f( *[ float( x ) for x in v.split( "," ) ]) for v in values ] )

	return None

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
	## \todo It seems that Arnold's standard is now "help", so
	# we may be able to remove "desc".

	description = __aiMetadataGetStr( nodeEntry, None, "desc",
		defaultValue = __aiMetadataGetStr( nodeEntry, None, "help" )
	)
	if description is not None :
		__metadata[nodeName]["description"] = description

	# Documentation URL. We support OSL-style "URL"

	url = __aiMetadataGetStr( nodeEntry, None, "URL" )
	if url is not None :
		__metadata[nodeName]["documentation:url"] = url

	# Icon. There doesn't appear to be a standard for this, so
	# we support "gaffer.icon" and "gaffer.iconScale".

	icon = __aiMetadataGetStr( nodeEntry, None, "gaffer.icon" )
	if icon is not None :
		__metadata[nodeName]["icon"] = icon

	iconScale = __aiMetadataGetFlt( nodeEntry, None, "gaffer.iconScale" )
	if iconScale is not None :
		__metadata[nodeName]["iconScale"] = iconScale

	# Node color.

	color = __aiMetadataGetRGB( nodeEntry, None, "gaffer.nodeGadget.color" )
	if color is not None :
		Gaffer.Metadata.registerValue( "ai:surface:{}".format( nodeName ), "nodeGadget:color", color )

	# Parameters
	# ----------

	paramIt = arnold.AiNodeEntryGetParamIterator( nodeEntry )
	while not arnold.AiParamIteratorFinished( paramIt ) :

		## \todo We could allow custom ui types to be specified using
		# arnold metadata entries.
		param = arnold.AiParamIteratorGetNext( paramIt )
		paramName = arnold.AiParamGetName( param )
		if paramName == "name" :
			# Arnold node name, never represented as a plug in Gaffer
			continue

		paramPath = nodeName + ".parameters." + paramName
		paramType = arnold.AiParamGetType( param )

		# Parameter description

		description = __aiMetadataGetStr(
			nodeEntry, paramName, "desc",
			defaultValue = __aiMetadataGetStr( nodeEntry, paramName, "help" )
		)
		if description is not None :
			__metadata[paramPath]["description"] = description

		# Presets

		if paramType == arnold.AI_TYPE_ENUM :
			# Parameter presets from enum values
			presetValues = __enumPresetValues( param )
			presetNames = presetValues
		else :
			# Manually specified presets for other types
			presetValues = __plugPresetValues( nodeEntry, paramName, paramType )
			presetNames = __plugPresetNames( nodeEntry, paramName )

		if presetValues :
			__metadata[paramPath]["plugValueWidget:type"] = "GafferUI.PresetsPlugValueWidget"
			__metadata[paramPath]["presetValues"] = presetValues
			__metadata[paramPath]["presetNames"] = presetNames

		# Nodule type from linkable metadata and parameter type

		linkable = __aiMetadataGetBool(
			nodeEntry, paramName, "linkable",
			defaultValue = paramType not in (
				arnold.AI_TYPE_BYTE, arnold.AI_TYPE_INT, arnold.AI_TYPE_UINT,
				arnold.AI_TYPE_BOOLEAN, arnold.AI_TYPE_ENUM, arnold.AI_TYPE_STRING,
				arnold.AI_TYPE_NODE
			)
		)
		__metadata[paramPath]["nodule:type"] = None if linkable else ""

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
				"filename" : "GafferUI.FileSystemPathPlugValueWidget",
				"camera" : "GafferSceneUI.ScenePathPlugValueWidget",
				"colorSpace" : "GafferUI.PresetsPlugValueWidget",
				"null" : "",
			}.get( widget )

			if widget == "camera" :
				__metadata[paramPath]["scenePathPlugValueWidget:setNames"] = IECore.StringVectorData( [ "__cameras" ] )
				__metadata[paramPath]["scenePathPlugValueWidget:setsLabel"] = "Show only cameras"

			if widget == "colorSpace" :
				# Here we're assuming that Arnold is being used with an OCIO
				# colour manager configured to match Gaffer.
				__metadata[paramPath]["presetNames"] = GafferImageUI.OpenColorIOTransformUI.colorSpacePresetNames
				__metadata[paramPath]["presetValues"] = GafferImageUI.OpenColorIOTransformUI.colorSpacePresetValues
				__metadata[paramPath]["openColorIO:extraPresetNames"] = IECore.StringVectorData( [ "Auto" ] )
				__metadata[paramPath]["openColorIO:extraPresetValues"] = IECore.StringVectorData( [ "auto" ] )
				__metadata[paramPath]["openColorIO:includeRoles"] = True
				# Allow custom values in case Arnold has been configured to use
				# some other colour manager instead.
				__metadata[paramPath]["presetsPlugValueWidget:allowCustom"] = True

		# Layout section from OSL "page".

		page = __aiMetadataGetStr( nodeEntry, paramName, "page" )
		if page is not None :
			__metadata[paramPath]["layout:section"] = page

			# Uncollapse sections if desired

			collapsed = __aiMetadataGetBool( nodeEntry, None, "gaffer.layout.section.%s.collapsed" % page )
			if collapsed == False :
				parent = paramPath.rsplit( '.', 1 )[0]
				__metadata[parent]["layout:section:%s:collapsed" % page] = collapsed

		# Label from OSL "label"
		defaultLabel = " ".join( [ i.capitalize() for i in paramName.split( "_" ) ] )
		label = __aiMetadataGetStr( nodeEntry, paramName, "label" )
		if label is None :
			label = defaultLabel

		__metadata[paramPath]["label"] = label
		# Custom labels typically only make sense in the context of `page`, so we
		# use the default label for the GraphEditor.
		__metadata[paramPath]["noduleLayout:label"] = defaultLabel

		if (
			arnold.AiNodeEntryGetType( nodeEntry ) == arnold.AI_NODE_LIGHT and
			__aiMetadataGetStr( nodeEntry, paramName, "gaffer.plugType" ) != ""
		) :
			GafferSceneUI.LightEditor.registerParameter(
				"ai:light", paramName, page
			)

		if (
			nodeName in lightEditorShaders and
			__aiMetadataGetStr( nodeEntry, paramName, "gaffer.plugType" ) != ""
		) :
			attributeName, sectionName = lightEditorShaders[nodeName]
			GafferSceneUI.LightEditor.registerShaderParameter(
				"ai:light",
				paramName,
				attributeName,
				sectionName,
				f"{page} {label}" if page is not None and label is not None else paramName
			)

		childComponents = {
			arnold.AI_TYPE_VECTOR2 : "xy",
			arnold.AI_TYPE_VECTOR : "xyz",
			arnold.AI_TYPE_RGB : "rgb",
			arnold.AI_TYPE_RGBA : "rgba",
		}.get( paramType )
		if childComponents is not None :
			for c in childComponents :
				__metadata["{}.{}".format( paramPath, c )]["noduleLayout:label"] = "{}.{}".format( label, c )

		# NodeEditor layout from other Gaffer-specific metadata

		divider = __aiMetadataGetBool( nodeEntry, paramName, "gaffer.layout.divider" )
		if divider :
			__metadata[paramPath]["layout:divider"] = True

		index = __aiMetadataGetInt( nodeEntry, paramName, "gaffer.layout.index" )
		if index is not None :
			__metadata[paramPath]["layout:index"] = index

		# GraphEditor visibility from Gaffer-specific metadata

		visible = __aiMetadataGetBool( nodeEntry, None, "gaffer.graphEditorLayout.defaultVisibility" )
		visible = __aiMetadataGetBool( nodeEntry, paramName, "gaffer.graphEditorLayout.visible", visible )
		if visible is not None :
			__metadata[paramPath]["noduleLayout:visible"] = visible

		userDefault = None
		if paramType in [ arnold.AI_TYPE_BYTE, arnold.AI_TYPE_INT, arnold.AI_TYPE_UINT ]:
			userDefault = __aiMetadataGetInt( nodeEntry, paramName, "gaffer.userDefault" )
		elif paramType == arnold.AI_TYPE_BOOLEAN:
			userDefault = __aiMetadataGetBool( nodeEntry, paramName, "gaffer.userDefault" )
		elif paramType == arnold.AI_TYPE_FLOAT:
			userDefault = __aiMetadataGetFlt( nodeEntry, paramName, "gaffer.userDefault" )
		elif paramType == arnold.AI_TYPE_RGB:
			userDefault = __aiMetadataGetRGB( nodeEntry, paramName, "gaffer.userDefault" )
		#elif paramType == arnold.AI_TYPE_RGBA:
		#	userDefault = __aiMetadataGetRGBA( nodeEntry, paramName, "gaffer.userDefault" )
		elif paramType == arnold.AI_TYPE_VECTOR:
			userDefault = __aiMetadataGetVec( nodeEntry, paramName, "gaffer.userDefault" )
		elif paramType == arnold.AI_TYPE_VECTOR2:
			userDefault = __aiMetadataGetVec2( nodeEntry, paramName, "gaffer.userDefault" )
		elif paramType == arnold.AI_TYPE_STRING:
			userDefault = __aiMetadataGetStr( nodeEntry, paramName, "gaffer.userDefault" )
		elif paramType == arnold.AI_TYPE_ENUM:
			userDefault = __aiMetadataGetStr( nodeEntry, paramName, "gaffer.userDefault" )

		if userDefault:
			nodeName, _, plugName = paramPath.split( "." )
			Gaffer.Metadata.registerValue( "ai:surface:%s:%s" % ( nodeName, plugName ), "userDefault", userDefault )

		# Activator from Gaffer-specific metadata

		def addActivator( activator ) :
			parentActivator = "layout:activator:" + activator

			if parentActivator not in __metadata[nodeName + ".parameters"] :
				activatorCode = __aiMetadataGetStr( nodeEntry, None, "gaffer.layout.activator." + activator )
				__metadata[nodeName + ".parameters"][parentActivator] = eval( "lambda parameters : " + activatorCode )

		activator = __aiMetadataGetStr( nodeEntry, paramName, "gaffer.layout.activator" )
		if activator is not None :
			addActivator( activator )
			__metadata[paramPath]["layout:activator"] = activator

		visibilityActivator = __aiMetadataGetStr( nodeEntry, paramName, "gaffer.layout.visibilityActivator" )
		if visibilityActivator is not None :
			addActivator( visibilityActivator )
			__metadata[paramPath]["layout:visibilityActivator"] = visibilityActivator

		# FileSystemPathPlugValueWidget metadata

		for gafferKey, arnoldGetter in [
			( "path:leaf", __aiMetadataGetBool ),
			( "path:valid", __aiMetadataGetBool ),
			( "path:bookmarks", __aiMetadataGetStr ),
			( "fileSystemPath:extensions", __aiMetadataGetStr ),
			( "fileSystemPath:extensionsLabel", __aiMetadataGetStr ),
		] :
			value = arnoldGetter( nodeEntry, paramName, "gaffer.{}".format( gafferKey.replace( ":", "." ) ) )
			if value is not None :
				__metadata[paramPath][gafferKey] = value

if [ int( x ) for x in arnold.AiGetVersion()[:3] ] < [ 7, 3, 1 ] :
	__AI_NODE_IMAGER = arnold.AI_NODE_DRIVER
else :
	__AI_NODE_IMAGER = arnold.AI_NODE_IMAGER

with IECoreArnold.UniverseBlock( writable = False ) :

	nodeIt = arnold.AiUniverseGetNodeEntryIterator( arnold.AI_NODE_SHADER | arnold.AI_NODE_LIGHT | arnold.AI_NODE_COLOR_MANAGER | __AI_NODE_IMAGER )
	while not arnold.AiNodeEntryIteratorFinished( nodeIt ) :

		__translateNodeMetadata( arnold.AiNodeEntryIteratorGetNext( nodeIt ) )

# Manually add width and height for `quad_light`
__metadata["quad_light.parameters.width"]["nodule:type"] = ""
__metadata["quad_light.parameters.height"]["nodule:type"] = ""
__metadata["quad_light.parameters.width"]["layout:section"] = "Shape"
__metadata["quad_light.parameters.height"]["layout:section"] = "Shape"
__metadata["quad_light.parameters.width"]["layout:index"] = 0
__metadata["quad_light.parameters.height"]["layout:index"] = 1
GafferSceneUI.LightEditor.registerParameter( "ai:light", "width", "Shape" )
GafferSceneUI.LightEditor.registerParameter( "ai:light", "height", "Shape" )

# Manually add the `filteredLights` parameter for `light_blocker`
GafferSceneUI.LightEditor.registerAttribute( "ai:light", "filteredLights", "Blocker" )

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
		return __metadata[node["__shader"]["name"].getValue()].get(
			"description",
			"""Loads an Arnold light shader and uses it to output a scene with a single light."""
		)

def __nodeMetadata( node, name ) :

	if isinstance( node, GafferArnold.ArnoldShader ) :
		key = node["name"].getValue()
	else :
		# Other nodes hold an internal shader
		key = node["__shader"]["name"].getValue()

	return __metadata[key].get( name )

def __plugMetadata( plug, name ) :

	if name == "noduleLayout:visible" and plug.getInput() is not None and not plug.node().getName().startswith( "__" ) :
		# Before the introduction of nodule visibility controls,
		# users may have made connections to plugs which are now
		# hidden by default. Make sure we continue to show them
		# by default - they can still be hidden explicitly by
		# adding an instance metadata value.
		# For private nodes this behaviour is skipped as their
		# inputs might be driven by the parent.
		return True

	node = plug.node()
	relativeName = plug.relativeName( node )
	if isinstance( node, GafferArnold.ArnoldShader ) :
		key = plug.node()["name"].getValue() + "." + relativeName
	else :
		# Other nodes hold an internal shader
		key = plug.node()["__shader"]["name"].getValue() + "." + relativeName

	result = __metadata[key].get( name )
	if callable( result ) :
		return result( plug )
	else :
		return result

for nodeType in ( GafferArnold.ArnoldShader, GafferArnold.ArnoldLight, GafferArnold.ArnoldMeshLight, GafferArnold.ArnoldColorManager, GafferArnold.ArnoldLightFilter ) :

	nodeKeys = set()
	parametersPlugKeys = set()
	parameterPlugKeys = set()
	parameterPlugComponentKeys = set()

	for name, metadata in __metadata.items() :
		keys = ( nodeKeys, parametersPlugKeys, parameterPlugKeys, parameterPlugComponentKeys )[name.count( "." )]
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

Gaffer.Metadata.registerValue( GafferArnold.ArnoldShader, "attributeSuffix", "plugValueWidget:type", "GafferUI.StringPlugValueWidget" )
Gaffer.Metadata.registerValue( GafferArnold.ArnoldShader, "layout:activator:suffixActivator", lambda parent : parent["type"].getValue() == "ai:lightFilter" )
Gaffer.Metadata.registerValue( GafferArnold.ArnoldShader, "attributeSuffix", "layout:visibilityActivator", "suffixActivator" )
