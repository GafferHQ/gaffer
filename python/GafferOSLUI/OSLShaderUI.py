##########################################################################
#
#  Copyright (c) 2013-2014, John Haddon. All rights reserved.
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

import IECore

import Gaffer
import GafferUI

import GafferOSL

##########################################################################
# Metadata. We register dynamic Gaffer.Metadata entries which are
# implemented as queries to the OSL metadata held within the shader.
##########################################################################

def __nodeDescription( node ) :

	__defaultDescription = """Loads OSL shaders for use in supported renderers. Use the ShaderAssignment node to assign shaders to objects in the scene."""

	description = node.shaderMetadata( "help" )
	return description or __defaultDescription

def __nodeIcon ( node ) :

	return node.shaderMetadata ( "icon" )

def __nodeIconScale ( node ) :

	return node.shaderMetadata ( "iconScale" )

def __nodeUrl( node ) :

	return node.shaderMetadata( "URL" )

def __plugDescription( plug ) :

	return plug.node().parameterMetadata( plug, "help" ) or ""

def __plugLabel( plug ) :

	return plug.node().parameterMetadata( plug, "label" )

def __plugDivider( plug ) :

	return plug.node().parameterMetadata( plug, "divider" ) or False

def __plugPage( plug ) :

	return plug.node().parameterMetadata( plug, "page" ) or None

def __plugPresetNames( plug ) :

	options = plug.node().parameterMetadata( plug, "options" )
	if not options :
		return None

	return IECore.StringVectorData( [ o.partition( ":" )[0] for o in options.split( "|" ) if o ] )

def __plugPresetValues( plug ) :

	options = plug.node().parameterMetadata( plug, "options" )
	if not options :
		return None

	values = [ o.rpartition( ":" )[2] for o in options.split( "|" ) if o ]

	if isinstance( plug, Gaffer.StringPlug ) :
		return IECore.StringVectorData( values )
	elif isinstance( plug, Gaffer.IntPlug ) :
		return IECore.IntVectorData( [ int( v ) for v in values ] )
	elif isinstance( plug, Gaffer.FloatPlug ) :
		return IECore.FloatVectorData( [ float( v ) for v in values ] )
	elif isinstance( plug, Gaffer.Color3fPlug ) :
		return IECore.Color3fVectorData( [
			imath.Color3f(
				*[ float( x ) for x in v.split( "," ) ]
			) for v in values
		] )
	elif isinstance( plug, Gaffer.V3fPlug ) :
		return IECore.V3fVectorData( [
			imath.V3f(
				*[ float( x ) for x in v.split( "," ) ]
			) for v in values
		] )

	return None

__widgetTypes = {
	"number" : "GafferUI.NumericPlugValueWidget",
	"string" : "GafferUI.StringPlugValueWidget",
	"boolean" : "GafferUI.BoolPlugValueWidget",
	"checkBox" : "GafferUI.BoolPlugValueWidget",
	"popup" : "GafferUI.PresetsPlugValueWidget",
	"mapper" : "GafferUI.PresetsPlugValueWidget",
	"filename" : "GafferUI.FileSystemPathPlugValueWidget",
	# For RenderMan.
	"assetIdInput" : "GafferUI.FileSystemPathPlugValueWidget",
	"null" : "",
}

def __plugWidgetType( plug ) :

	return __widgetTypes.get(
		plug.node().parameterMetadata( plug, "widget" )
	)

def __plugNoduleType( plug ) :

	if isinstance( plug, ( Gaffer.SplinefColor3fPlug, Gaffer.SplineffPlug ) ) :
		return ""
	elif plug.node().parameterMetadata( plug, "connectable" ) == 0 :
		return ""
	else :
		# Causes `Nodule::create()` to choose nodule type
		# based on plug type.
		return None

def __outPlugNoduleType( plug ) :

	return "GafferUI::CompoundNodule" if len( plug ) else "GafferUI::StandardNodule"

def __plugNoduleVisibility( plug ) :

	node = plug.node()
	visible = node.parameterMetadata( plug, "gafferNoduleLayoutVisible" )
	if visible is None :
		visible = node.shaderMetadata( "gafferNoduleLayoutDefaultVisibility" )

	return bool( visible ) if visible is not None else True

def __plugNoduleLabel( plug ) :

	label = __plugLabel( plug )
	if label is None :
		return None

	page = __plugPage( plug )
	if page is not None :
		label = page + "." + label

	return label

def __plugComponentNoduleLabel( plug ) :

	parameterPlug = plug.parent()
	label = __plugNoduleLabel( parameterPlug )
	if label is None :
		label = parameterPlug.getName()

	return label + "." + plug.getName()

Gaffer.Metadata.registerNode(

	GafferOSL.OSLShader,

	"description", __nodeDescription,
	"documentation:url", __nodeUrl,
	"icon", __nodeIcon,
	"iconScale", __nodeIconScale,

	plugs = {

		"parameters.*" : [

			"description", __plugDescription,
			"label", __plugLabel,
			"layout:divider", __plugDivider,
			"layout:section", __plugPage,
			"presetNames", __plugPresetNames,
			"presetValues", __plugPresetValues,
			"plugValueWidget:type", __plugWidgetType,
			"nodule:type", __plugNoduleType,
			"noduleLayout:visible", __plugNoduleVisibility,
			"noduleLayout:label", __plugNoduleLabel,

		],

		"parameters.*.[rgbxyz]" : [

			"noduleLayout:label", __plugComponentNoduleLabel,

		],

		"out" : [

			"nodule:type", __outPlugNoduleType,
			"noduleLayout:spacing", 0.2,

		],

		"out.*" : [

			"noduleLayout:visible", __plugNoduleVisibility,
			"noduleLayout:label", __plugNoduleLabel,

		]

	}

)
