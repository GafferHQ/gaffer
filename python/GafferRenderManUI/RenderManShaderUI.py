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

import GafferRenderMan.ArgsFileAlgo
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

def registerMetadata() :

	searchPaths = IECore.SearchPath( os.environ.get( "RMAN_RIXPLUGINPATH", "" ) )

	for path in set( searchPaths.paths ) :
		for argsFile in pathlib.Path( path ).glob( "**/*.args" ) :
			GafferRenderMan.ArgsFileAlgo.registerMetadata( argsFile )

def appendShaders( menuDefinition, prefix = "/RenderMan" ) :

	# All RenderMan's C++ shaders have already been registered with Gaffer's
	# metadata system, so we can look that up to find everything we might want
	# to create. We just need to sort things so that we get the menus in the
	# order we want.

	def sortKey( metadataTarget ) :

		_, shaderType, shaderName = metadataTarget.split( ":" )
		typeIndex = {
			"surface" : 0,
			"shader" : 1,
			"light" : 2,
			"lightFilter" : 3
		}

		return typeIndex.get( shaderType, 4 ), shaderName

	metadataTargets = Gaffer.Metadata.targetsWithMetadata( "ri:*", "description" )
	metadataTargets = [ t for t in metadataTargets if t.count( ":" ) == 2 ] # Ignore parameter metadata
	metadataTargets = sorted( metadataTargets, key = sortKey )

	toOmit = {
		# Deprecated in RenderMan 24 - don't let folks become dependent on it.
		"PxrSeExpr",
		# Not needed because we combine filters automatically.
		"PxrDisplayFilterCombiner", "PxrSampleFilterCombiner", "PxrCombinerLightFilter",
		# These two are deprecated in RenderMan 26, so best not to let folks
		# get used to them.
		"PxrGoboLightFilter",
		"PxrBlockerLightFilter",
		# This one only seems useful when linked to specific _objects_
		# (rather than lights), and I'm not sure how to do that yet.
		"PxrIntMultLightFilter",
	}

	nodeTypes = {
		"light" : GafferRenderMan.RenderManLight,
		"lightFilter" : GafferRenderMan.RenderManLightFilter,
	}

	nodeCreators = { "PxrMeshLight" : GafferRenderMan.RenderManMeshLight }

	subMenus = {
		"light" : "Light",
		"lightFilter" : "Light Filter",
	}

	for metadataTarget in metadataTargets :

		_, shaderType, shaderName = metadataTarget.split( ":" )
		if shaderName in toOmit :
			continue

		nodeType = nodeTypes.get( shaderType, GafferRenderMan.RenderManShader )
		subMenu = subMenus.get( shaderType )
		if subMenu is None :
			subMenu = "Shader/" + Gaffer.Metadata.value( metadataTarget, "classification" )

		menuDefinition.append(
			f"{prefix}/{subMenu}/{shaderName}",
			{
				"command" : GafferUI.NodeMenu.nodeCreatorWrapper(
					nodeCreators.get( shaderName, functools.partial( __loadShader, shaderName, nodeType ) )
				)
			}
		)

	# Add RenderMan's OSL pattern shaders.

	oslDir = pathlib.Path( os.environ["RMANTREE"] ) / "lib" / "shaders"
	for shader in sorted( oslDir.glob( "*.oso" ) ) :
		query = oslquery.OSLQuery( str( shader ) )
		classification = "Other"
		for metadata in query.metadata :
			if metadata.name == "rfh_classification" :
				classification = metadata.value

		menuDefinition.append(
			f"{prefix}/Shader/{classification}/{shader.stem}",
			{
				"command" : GafferUI.NodeMenu.nodeCreatorWrapper(
					functools.partial( __loadShader, shader.stem, GafferOSL.OSLShader )
				)
			}
		)

def __loadShader( shaderName, nodeType ) :

	nodeName = os.path.split( shaderName )[-1]
	nodeName = nodeName.replace( ".", "" )

	node = nodeType( nodeName )
	if hasattr( node, "loadShader" ) :
		node.loadShader( shaderName )

	if isinstance( node, ( GafferRenderMan.RenderManLight, GafferRenderMan.RenderManLightFilter ) ) :
		node["name"].setValue(
			shaderName.replace( "Pxr", "pxr" )
		)
	elif isinstance( node, GafferOSL.OSLShader ) :
		if "matchCppPattern" in node["parameters"] :
			# This parameter is only useful for compatibility with RenderMan 23,
			# which is not a concern for us since we are starting with RenderMan
			# 26. Hide it.
			Gaffer.Metadata.registerValue( node["parameters"]["matchCppPattern"], "layout:visibilityActivator", False )

	return node

GafferSceneUI.ShaderUI.hideShaders( IECore.PathMatcher( [ "/Pxr*" ] ) )

##########################################################################
# Conditional visibility
##########################################################################

def __parameterActivator( plug ) :

	shader = plug.node()
	metadataTarget = shader["type"].getValue() + ":" + shader["name"].getValue() + ":" + plug.relativeName( shader["parameters"] )
	return not GafferSceneUI.ShaderUI._evaluateConditionalLock(
		shader["parameters"],
		lambda key : Gaffer.Metadata.value( metadataTarget, f"ri:{key}" )
	)

def __parameterVisibilityActivator( plug ) :

	shader = plug.node()
	metadataTarget = shader["type"].getValue() + ":" + shader["name"].getValue() + ":" + plug.relativeName( shader["parameters"] )
	return GafferSceneUI.ShaderUI._evaluateConditionalVisibility(
		shader["parameters"],
		lambda key : Gaffer.Metadata.value( metadataTarget, f"ri:{key}" )
	)

Gaffer.Metadata.registerValue( GafferRenderMan.RenderManShader, "parameters.*", "layout:activator", __parameterActivator )
Gaffer.Metadata.registerValue( GafferRenderMan.RenderManShader, "parameters.*", "layout:visibilityActivator", __parameterVisibilityActivator )

def __internalParameterActivator( plug ) :

	return __parameterActivator( plug.node()["__shader"]["parameters"][plug.getName()] )

def __internalParameterVisibilityActivator( plug ) :

	return __parameterVisibilityActivator( plug.node()["__shader"]["parameters"][plug.getName()] )

for nodeType in ( GafferRenderMan.RenderManLight, GafferRenderMan.RenderManLightFilter ) :
	Gaffer.Metadata.registerValue( nodeType, "parameters.*", "layout:activator", __internalParameterActivator )
	Gaffer.Metadata.registerValue( nodeType, "parameters.*", "layout:visibilityActivator", __internalParameterVisibilityActivator )

##########################################################################
# Additional Metadata
##########################################################################

Gaffer.Metadata.registerValue( GafferRenderMan.RenderManShader, "out", "nodule:type", lambda plug : "GafferUI::CompoundNodule" if len( plug ) else "GafferUI::StandardNodule" )
Gaffer.Metadata.registerValue( GafferRenderMan.RenderManLight, "parameters", "layout:section:Basic:collapsed", False )
