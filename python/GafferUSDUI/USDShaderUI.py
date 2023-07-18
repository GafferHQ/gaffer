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

import IECore

import Gaffer
import GafferUI
import GafferSceneUI
import GafferUSD

def __sdrProperty( plug ) :

	shaderName = plug.node()["name"].getValue()

	sdrNode = Sdr.Registry().GetNodeByName( shaderName )
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

	shaderName = plug.node()["name"].getValue()
	order = __propertyOrder.get( shaderName )
	if order is None :
		return None

	return order.get( plug.getName() )

def __widgetType( plug ) :

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
		"{}.{}".format( plug.node()["name"].getValue(), plug.getName() )
	)

def __presetNames( plug ) :

	property = __sdrProperty( plug )
	options = property.GetOptions()
	if options :
		return IECore.StringVectorData( [ o[0] for o in options ] )

def __presetValues( plug ) :

	property = __sdrProperty( plug )
	options = property.GetOptions()
	if options :
		if len( options ) > 1 and all( o[1] == "" for o in options ) :
			# USD's `_CreateSdrShaderProperty` method in `shaderDefUtils.cpp`
			# always uses an empty string for the option value when converting
			# from `allowedTokens`. Ignore that, and use the names as the values
			# as intended by the author of `allowedTokens`.
			return IECore.StringVectorData( [ o[0] for o in options ] )
		else :
			return IECore.StringVectorData( [ o[1] for o in options ] )

def __noduleType( plug ) :

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

			## \todo Get USD to actually provide help metadata. It's defined in a `doc`
			# attribute in `shaderDefs.usda`, but not actually converted to Sdr by
			# UsdShadeShaderDefUtils.
			"description", functools.partial( __sdrMetadata, name = "help" ),
			"layout:index", __layoutIndex,
			"noduleLayout:index", __layoutIndex,
			"plugValueWidget:type", __widgetType,
			"presetNames", __presetNames,
			"presetValues", __presetValues,
			"nodule:type", __noduleType,

		],

		"out.*" : [

			"description", functools.partial( __sdrMetadata, name = "help" ),
			"layout:index", __layoutIndex,
			"noduleLayout:index", __layoutIndex,

		],

	}
)

def __orderDict( names ) :

	return dict( zip( names, range( 0, len( names ) ) ) )

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

}

__widgetTypes = {

	"UsdPreviewSurface.useSpecularWorkflow" : "GafferUI.BoolPlugValueWidget",
	"UsdUVTexture.file" : "GafferUI.FileSystemPathPlugValueWidget",

}
