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

import functools

from pxr import Sdr
from pxr import Usd

import IECore

import Gaffer
import GafferUI
import GafferSceneUI
import GafferUSD

def __shaderName( plug ) :

	node = plug.node()
	if isinstance( node, GafferUSD.USDLight ) :
		return plug.node()["__shader"]["name"].getValue()
	else :
		return plug.node()["name"].getValue()

def __primProperty( plug ) :

	if isinstance( plug.parent(), Gaffer.OptionalValuePlug ) :
		plug = plug.parent()

	plugName = plug.getName()

	if plugName.startswith( "shaping:" ) :
		primDefinition = Usd.SchemaRegistry().FindAppliedAPIPrimDefinition( "ShapingAPI" )
	elif plugName.startswith( "shadow:" ) :
		primDefinition = Usd.SchemaRegistry().FindAppliedAPIPrimDefinition( "ShadowAPI" )
	else :
		primDefinition = Usd.SchemaRegistry().FindConcretePrimDefinition( __shaderName( plug ) )

	if primDefinition :
		return primDefinition.GetPropertyDefinition( "inputs:" + plug.getName() )
	else :
		return None

def __sdrProperty( plug ) :

	sdrNode = Sdr.Registry().GetNodeByName( __shaderName( plug ) )
	if plug.direction() == Gaffer.Plug.Direction.In :
		return sdrNode.GetInput( plug.getName() )
	else :
		return sdrNode.GetOutput( plug.getName() )

def __sdrMetadata( plug, name ) :

	return __sdrProperty( plug ).GetMetadata().get( name )

def __layoutIndex( plug ) :

	# Usd carefully defines shader inputs in a sensible order
	# in `shaderDefs.usda`, and then completely discards it
	# during parsing, leaving us with parameters in a useless
	# alphabetical order. Until that is sorted out, we manually
	# match the intended order with our own metadata.
	#
	# See https://github.com/PixarAnimationStudios/OpenUSD/pull/2497.

	shaderName = __shaderName( plug )
	order = __propertyOrder.get( shaderName )
	if order is None :
		return None

	return order.get( plug.getName() )

def __layoutSection( plug ) :

	property = __primProperty( plug )
	if property :
		return property.GetMetadata( "displayGroup" )

	return __sdrProperty( plug ).GetPage()

def __label( plug ) :

	property = __primProperty( plug )
	if property :
		return property.GetMetadata( "displayName" )

	return __sdrProperty( plug ).GetLabel() or None

def __description( plug ) :

	property = __primProperty( plug )
	if property :
		description = property.GetMetadata( "documentation" )
		if description is not None :
			# Spare UsdLux from embarrassment until it defines what
			# various parameters are actually intended to do.
			description = description.replace( "TODO: clarify semantics", "" )
		return description

	## \todo Get USD to actually provide help metadata. It's defined in a `doc`
	# attribute in `shaderDefs.usda`, but not actually converted to Sdr by
	# UsdShadeShaderDefUtils.
	return __sdrMetadata( plug, "help" )

def __widgetType( plug ) :

	if isinstance( plug, Gaffer.OptionalValuePlug ) :
		# We want the default widget.
		return None

	property = __primProperty( plug )
	if property :

		# As far as I can tell, there isn't yet a convention for
		# specifying widgets on `UsdPrimDefinition.Property`, but
		# we can at least use `allowedTokens` to detect enum-like
		# properties.
		if property.GetMetadata( "allowedTokens" ) is not None :
			return "GafferUI.PresetsPlugValueWidget"

	else :

		property = __sdrProperty( plug )

		if property.GetWidget() not in ( "", "default" ) :
			# The UsdPreviewSurface shaders don't provide any useful widget
			# metadata, but we'd love to use it if they did, so alert
			# ourselves if it appears in future.
			IECore.msg(
				IECore.Msg.Level.Warning, "USDShaderUI",
				'Ignoring widget metadata "{}" on "{}"'.format(
					property.GetWidget(), plug.fullName()
				)
			)

		if property.GetOptions() :
			return "GafferUI.PresetsPlugValueWidget"

	# Fall back to metadata we provide ourselves.
	return __widgetTypes.get(
		"{}.{}".format( __shaderName( plug ), plug.getName() )
	)

def __presetNames( plug ) :

	property = __primProperty( plug )
	if property :
		allowedTokens = property.GetMetadata( "allowedTokens" )
		return IECore.StringVectorData( allowedTokens ) if allowedTokens else None

	property = __sdrProperty( plug )
	options = property.GetOptions()
	if options :
		return IECore.StringVectorData( [ o[0] for o in options ] )

def __presetValues( plug ) :

	property = __primProperty( plug )
	if property :
		allowedTokens = property.GetMetadata( "allowedTokens" )
		if allowedTokens and isinstance( plug, Gaffer.IntPlug ) :
			return IECore.IntVectorData( [ i for i in range( len( allowedTokens ) ) ] )
		else :
			return IECore.StringVectorData( allowedTokens ) if allowedTokens else None

	property = __sdrProperty( plug )
	options = property.GetOptions()
	if options :
		if isinstance( plug, Gaffer.IntPlug ) :
			return IECore.IntVectorData( [ i for i in range( len( options ) ) ] )
		elif len( options ) > 1 and all( o[1] == "" for o in options ) :
			# USD's `_CreateSdrShaderProperty` method in `shaderDefUtils.cpp`
			# always uses an empty string for the option value when converting
			# from `allowedTokens`. Ignore that, and use the names as the values
			# as intended by the author of `allowedTokens`.
			return IECore.StringVectorData( [ o[0] for o in options ] )
		else :
			return IECore.StringVectorData( [ o[1] for o in options ] )

def __noduleType( plug ) :

	property = __primProperty( plug )
	if property :
		## \todo Figure out if there's a way of querying connectability from
		# `UsdPrimDefinition.Property` - at the time of writing, I can't find
		# one.
		return None

	property = __sdrProperty( plug )
	# `None` means "no opinion", so a nodule will be created based
	# on the plug's type. `""` means "no nodule please".
	return None if property.IsConnectable() else ""

Gaffer.Metadata.registerNode(

	GafferUSD.USDShader,

	"description",
	"""
	Loads shaders from USD's `SdrRegistry`. This includes shaders such as `UsdPreviewSurface`
	and `UsdUVTexture`.
	""",

	plugs = {

		"out" : [

			"nodule:type", "GafferUI::CompoundNodule",

		],

		"parameters.*" : [

			"nodule:type", __noduleType,

		],

		"out.*" : [

			"description", __description,
			"layout:index", __layoutIndex,
			"noduleLayout:index", __layoutIndex,

		],

	}
)

for nodeType in ( GafferUSD.USDShader, GafferUSD.USDLight ) :

	Gaffer.Metadata.registerNode(

		nodeType,

		plugs = {

			"parameters.*" : [

				"label", __label,
				"description", __description,
				"layout:index", __layoutIndex,
				"layout:section", __layoutSection,
				"noduleLayout:index", __layoutIndex,
				"plugValueWidget:type", __widgetType,
				"presetNames", __presetNames,
				"presetValues", __presetValues,

			],

			# Again, but for the `value` plug on OptionalValuePlugs.
			"parameters.*.value" : [

				"plugValueWidget:type", __widgetType,
				"presetNames", __presetNames,
				"presetValues", __presetValues,

			],

		}

	)

def __orderDict( names ) :

	return dict( zip( names, range( 0, len( names ) ) ) )

__lightPropertyOrder = [ "color", "intensity", "exposure", "enableColorTemperature", "colorTemperature", "normalize", "diffuse", "specular" ]
__apiPropertyOrder = [
	# ShapingAPI
	"shaping:focus", "shaping:focusTint", "shaping:cone:angle", "shaping:cone:softness", "shaping:ies:file", "shaping:ies:angleScale", "shaping:ies:normalize",
	# ShadowAPI
	"shadow:enable", "shadow:color", "shadow:distance", "shadow:falloff", "shadow:falloffGamma",
]

__propertyOrder = {

	"UsdPreviewSurface" : __orderDict( [ "surface", "displacement", "diffuseColor", "emissiveColor", "useSpecularWorkflow", "specularColor", "metallic", "roughness", "clearcoat", "clearcoatRoughness", "opacity", "opacityThreshold", "ior", "normal", "displacement", "occlusion" ] ),
	"UsdUVTexture" : __orderDict( [ "file", "st", "wrapS", "wrapT", "fallback", "scale", "bias", "sourceColorSpace", "r", "g", "b", "a", "rgb" ] ),
	"UsdTransform2d" : __orderDict( [ "in", "rotation", "scale", "translation", "result" ] ),
	"UsdPrimvarReader_int" : __orderDict( [ "varname", "fallback", "result" ] ),
	"UsdPrimvarReader_float" : __orderDict( [ "varname", "fallback", "result" ] ),
	"UsdPrimvarReader_float2" : __orderDict( [ "varname", "fallback", "result" ] ),
	"UsdPrimvarReader_float3" : __orderDict( [ "varname", "fallback", "result" ] ),
	"UsdPrimvarReader_float4" : __orderDict( [ "varname", "fallback", "result" ] ),
	"UsdPrimvarReader_string" : __orderDict( [ "varname", "fallback", "result" ] ),
	"UsdPrimvarReader_point" : __orderDict( [ "varname", "fallback", "result" ] ),
	"UsdPrimvarReader_vector" : __orderDict( [ "varname", "fallback", "result" ] ),
	"UsdPrimvarReader_normal" : __orderDict( [ "varname", "fallback", "result" ] ),

	"DistantLight" : __orderDict( __lightPropertyOrder + [ "angle" ] + __apiPropertyOrder ),
	"DiskLight" : __orderDict( __lightPropertyOrder + [ "radius" ] + __apiPropertyOrder ),
	"DomeLight" : __orderDict( __lightPropertyOrder + [ "texture:file", "texture:format" ] + __apiPropertyOrder ),
	"RectLight" : __orderDict( __lightPropertyOrder + [ "width", "height", "texture:file" ] + __apiPropertyOrder ),
	"SphereLight" : __orderDict( __lightPropertyOrder + [ "radius" ] + __apiPropertyOrder ),
	"CylinderLight" : __orderDict( __lightPropertyOrder + [ "length", "radius" ] + __apiPropertyOrder ),

}

__widgetTypes = {

	"UsdPreviewSurface.useSpecularWorkflow" : "GafferUI.BoolPlugValueWidget",
	"UsdUVTexture.file" : "GafferUI.FileSystemPathPlugValueWidget",

	"DomeLight.texture:file" : "GafferUI.FileSystemPathPlugValueWidget",
	"RectLight.texture:file" : "GafferUI.FileSystemPathPlugValueWidget",

}
