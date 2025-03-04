##########################################################################
#
#  Copyright (c) 2019, John Haddon. All rights reserved.
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

import os
import functools
import pathlib
from xml.etree import cElementTree

import oslquery

import IECore

import Gaffer
import GafferUI
import GafferSceneUI
import GafferOSL
import GafferRenderMan

##########################################################################
# Node menu
##########################################################################

def appendShaders( menuDefinition, prefix = "/RenderMan" ) :

	plugins = __plugins()

	menuDefinition.append(
		prefix + "/Shader",
		{
			"subMenu" : functools.partial( __shadersSubMenu, plugins ),
		}
	)

def __plugins() :

	result = {}

	searchPaths = IECore.SearchPath( os.environ.get( "RMAN_RIXPLUGINPATH", "" ) )

	pathsVisited = set()
	for path in searchPaths.paths :

		if path in pathsVisited :
			continue
		else :
			pathsVisited.add( path )

		for root, dirs, files in os.walk( path ) :
			for file in [ f for f in files  ] :

				name, extension = os.path.splitext( file )
				if extension != ".args" :
					continue

				plugin = __plugin( os.path.join( root, file ) )
				if plugin is not None :
					result[name] = plugin

	return result

def __plugin( argsFile ) :

	pluginType = None
	classification = ""
	for event, element in cElementTree.iterparse( argsFile, events = ( "start", "end" ) ) :
		if element.tag == "shaderType" and event == "end" :
			tag = element.find( "tag" )
			if tag is not None :
				pluginType = tag.attrib.get( "value" )
		elif element.tag == "rfhdata" :
			classification = element.attrib.get( "classification" )

	if pluginType is None :
		return None

	return {
		"type" : pluginType,
		"classification" : classification
	}

def __loadShader( shaderName, nodeType ) :

	nodeName = os.path.split( shaderName )[-1]
	nodeName = nodeName.replace( ".", "" )

	node = nodeType( nodeName )
	node.loadShader( shaderName )

	if isinstance( node, GafferOSL.OSLShader ) :
		if "matchCppPattern" in node["parameters"] :
			# This parameter is only useful for compatibility with RenderMan 23,
			# which is not a concern for us since we are starting with RenderMan
			# 26. Hide it.
			Gaffer.Metadata.registerValue( node["parameters"]["matchCppPattern"], "layout:visibilityActivator", False )

	return node

def __shadersSubMenu( plugins ) :

	result = IECore.MenuDefinition()

	for name, plugin in plugins.items() :

		if name in [ "PxrSeExpr" ] :
			# Deprecated in RenderMan 24 - don't let folks become dependent on it.
			continue

		if plugin["type"] not in { "bxdf", "pattern", "integrator" } :
			continue

		result.append(
			"/{0}/{1}".format( plugin["classification"], name ),
			{
				"command" : GafferUI.NodeMenu.nodeCreatorWrapper(
					functools.partial( __loadShader, name, GafferRenderMan.RenderManShader )
				)
			}
		)

	oslDir = pathlib.Path( os.environ["RMANTREE"] ) / "lib" / "shaders"
	for shader in sorted( oslDir.glob( "*.oso" ) ) :
		query = oslquery.OSLQuery( str( shader ) )
		classification = "Other"
		for metadata in query.metadata :
			if metadata.name == "rfh_classification" :
				classification = metadata.value

		result.append(
			"/{}/{}".format( classification, shader.stem ),
			{
				"command" : GafferUI.NodeMenu.nodeCreatorWrapper(
					functools.partial( __loadShader, shader.stem, GafferOSL.OSLShader )
				)
			}
		)

	return result

GafferSceneUI.ShaderUI.hideShaders( IECore.PathMatcher( [ "/Pxr*" ] ) )

##########################################################################
# Metadata. We register dynamic Gaffer.Metadata entries which are
# implemented as lookups to data queried from .args files.
##########################################################################

__metadataCache = {}
def __shaderMetadata( node ) :

	global __metadataCache

	shaderName = node["name"].getValue()

	try :
		return __metadataCache[shaderName]
	except KeyError :
		pass

	searchPaths = IECore.SearchPath( os.environ.get( "RMAN_RIXPLUGINPATH", "" ) )
	argsFile = searchPaths.find( "Args/" + shaderName + ".args" )
	if argsFile :
		result = GafferRenderMan.ArgsFileAlgo.parseMetadata( argsFile )
	else :
		result = {}

	__metadataCache[shaderName] = result
	return result

def __parameterMetadata( plug, key ) :

	return __shaderMetadata( plug.node() )["parameters"].get( plug.getName(), {} ).get( key )

def __nodeDescription( node ) :

	defaultDescription = """Loads RenderMan shaders. Use the ShaderAssignment node to assign shaders to objects in the scene."""
	metadata = __shaderMetadata( node )
	return metadata.get( "description", defaultDescription )

Gaffer.Metadata.registerValue( GafferRenderMan.RenderManShader, "description", __nodeDescription )

for key in [
	"label",
	"description",
	"layout:section",
	"plugValueWidget:type",
	"presetNames",
	"presetValues",
	"nodule:type",
] :

	Gaffer.Metadata.registerValue(
		GafferRenderMan.RenderManShader, "parameters.*", key,
		functools.partial( __parameterMetadata, key = key )
	)

Gaffer.Metadata.registerValue( GafferRenderMan.RenderManShader, "out", "nodule:type", lambda plug : "GafferUI::CompoundNodule" if len( plug ) else "GafferUI::StandardNodule" )
