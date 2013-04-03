##########################################################################
#  
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

import fnmatch

import IECore

import Gaffer
import GafferUI

import GafferRenderMan

##########################################################################
# Nodules
##########################################################################

def __parameterNoduleCreator( plug ) :

	# only coshader parameters should be connectable in the node
	# graph.
	if plug.typeId() == Gaffer.Plug.staticTypeId() :
		return GafferUI.StandardNodule( plug )

	return None

GafferUI.Nodule.registerNodule( GafferRenderMan.RenderManShader.staticTypeId(), fnmatch.translate( "parameters.*" ), __parameterNoduleCreator )

##########################################################################
# PlugValueWidgets. We use annotations stored in the shader to provide
# hints as to how we should build the UI. We use the OSL specification
# for shader metadata in the hope that one day we'll get to use OSL in
# Gaffer and then we'll have a consistent metadata convention across
# both shader types.
##########################################################################

__shaderAnnotations = {}

def __optionValue( plug, stringValue ) :

	if isinstance( plug, Gaffer.StringPlug ) :
		return stringValue
	elif isinstance( plug, Gaffer.IntPlug ) :
		return int( stringValue )
	elif isinstance( plug, Gaffer.FloatPlug ) :
		return float( stringValue )
	else :
		raise Exception( "Unsupported parameter type." )

def __numberCreator( plug, annotations ) :

	return GafferUI.NumericPlugValueWidget( plug )
	
def __stringCreator( plug, annotations ) :

	return GafferUI.StringPlugValueWidget( plug )
	
def __booleanCreator( plug, annotations ) :

	return GafferUI.BoolPlugValueWidget( plug )

def __popupCreator( plug, annotations ) :

	options = annotations.get( plug.getName() + ".options", None )
	if options is None :
		raise Exception( "No \"options\" annotation." )
	
	options = options.value.split( "|" )
	labelsAndValues = [ ( x, __optionValue( plug, x ) ) for x in options ]
	return GafferUI.EnumPlugValueWidget( plug, labelsAndValues )

def __mapperCreator( plug, annotations ) :

	options = annotations.get( plug.getName() + ".options", None )
	if options is None :
		raise Exception( "No \"options\" annotation." )
	
	options = options.value.split( "|" )
	labelsAndValues = []
	for option in options :
		tokens = option.split( ":" )
		if len( tokens ) != 2 :
			raise Exception( "Option \"%s\" is not of form name:value" % option )
		labelsAndValues.append( ( tokens[0], __optionValue( plug, tokens[1] ) ) )
	
	return GafferUI.EnumPlugValueWidget( plug, labelsAndValues )

def __fileNameCreator( plug, annotations ) :

	extensions = annotations.get( plug.getName() + ".extensions", None )
	if extensions is not None :
		extensions = extensions.value.split( "|" )
	else :
		extensions = []
			
	return GafferUI.PathPlugValueWidget(
		plug,
		path = Gaffer.FileSystemPath(
			"/",
			filter = Gaffer.FileSystemPath.createStandardFilter(
				extensions = extensions,
				extensionsLabel = "Show only supported files",
			),
		)
	)

def __nullCreator( plug, annotations ) :

	return None

__creators = {
	"number" : __numberCreator,
	"string" : __stringCreator,
	"boolean" : __booleanCreator,
	"checkBox" : __booleanCreator,
	"popup" : __popupCreator,
	"mapper" : __mapperCreator,
	"filename" : __fileNameCreator,
	"null" : __nullCreator,
}

def __plugValueWidgetCreator( plug ) :

	global __shaderAnnotations
	global __creators

	shaderName = plug.node()["__shaderName"].getValue()
	if shaderName not in __shaderAnnotations :
		try :
			shader = GafferRenderMan.RenderManShader.shaderLoader().read( shaderName + ".sdl" )
		except Exception, e :
			shader = None
		annotations = shader.blindData().get( "ri:annotations", None ) if shader is not None else {}
		__shaderAnnotations[shaderName] = annotations

	annotations = __shaderAnnotations[shaderName]
	parameterName = plug.getName()
		
	widgetType = annotations.get( parameterName + ".widget", None )
	widgetCreator = None
	if widgetType is not None :
		widgetCreator = __creators.get( widgetType.value, None )
		if widgetCreator is None :
			IECore.msg(
				IECore.Msg.Level.Warning,
				"RenderManShaderUI",
				"Shader parameter \"%s.%s\" has unsupported widget type \"%s\"" %
					( shaderName, parameterName, widgetType )
			)
			
	if widgetCreator is not None :
		try :
			return widgetCreator( plug, annotations )
		except Exception, e :
			IECore.msg(
				IECore.Msg.Level.Warning,
				"RenderManShaderUI",
				"Error creating UI for parameter \"%s.%s\" : \"%s\"" %
					( shaderName, parameterName, str( e ) )
			)
	
	return GafferUI.PlugValueWidget.create( plug, useTypeOnly=True )

GafferUI.PlugValueWidget.registerCreator( GafferRenderMan.RenderManShader.staticTypeId(), "parameters.*", __plugValueWidgetCreator )
