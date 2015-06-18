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

import arnold

import IECoreArnold

import Gaffer
import GafferUI
import GafferArnold

##########################################################################
# Utilities to make it easier to work with the Arnold API, which has a
# fairly bare wrapping using ctypes.
##########################################################################

def __aiMetadataGetStr( nodeEntry, paramName, name ) :

	value = arnold.AtString()
	if arnold.AiMetaDataGetStr( nodeEntry, paramName, name, value ) :
		return value.value

	return None

##########################################################################
# Build a registry of information retrieved from Arnold metadata. We fill this
# once at startup, as we can only get it from within an AiUniverse block,
# and we don't want to have to keep making those temporarily later.
##########################################################################

__descriptions = {}
__plugValueWidgetCreators = {}

with IECoreArnold.UniverseBlock() :

	nodeIt = arnold.AiUniverseGetNodeEntryIterator( arnold.AI_NODE_SHADER | arnold.AI_NODE_LIGHT )
	while not arnold.AiNodeEntryIteratorFinished( nodeIt ) :

		nodeEntry = arnold.AiNodeEntryIteratorGetNext( nodeIt )
		nodeName = arnold.AiNodeEntryGetName( nodeEntry )

		description = __aiMetadataGetStr( nodeEntry, None, "desc" )
		if description is not None :
			__descriptions[nodeName] = description

		paramIt = arnold.AiNodeEntryGetParamIterator( nodeEntry )
		while not arnold.AiParamIteratorFinished( paramIt ) :

			## \todo We could allow custom ui types to be specified using
			# arnold metadata entries.
			param = arnold.AiParamIteratorGetNext( paramIt )
			paramName = arnold.AiParamGetName( param )
			paramPath = nodeName + "." + paramName

			description = __aiMetadataGetStr( nodeEntry, paramName, "desc" )
			if description is not None :
				__descriptions[paramPath] = description

			paramType = arnold.AiParamGetType( param )
			if paramType == arnold.AI_TYPE_ENUM :

				enum = arnold.AiParamGetEnum( param )
				namesAndValues = []
				while True :
					enumLabel = arnold.AiEnumGetString( enum, len( namesAndValues ) )
					if not enumLabel :
						break
					namesAndValues.append( ( enumLabel, enumLabel ) )

				__plugValueWidgetCreators[paramPath] = ( GafferUI.EnumPlugValueWidget, namesAndValues )

##########################################################################
# Gaffer Metadata queries. These are implemented using the preconstructed
# registry above.
##########################################################################

def __nodeDescription( node ) :

	shaderDefault = """Loads shaders for use in Arnold renderers. Use the ShaderAssignment node to assign shaders to objects in the scene."""
	lightDefault = """Loads an Arnold light shader and uses it to output a scene with a single light."""

	return __descriptions.get(
		node["name"].getValue(),
		shaderDefault if isinstance( node, GafferArnold.ArnoldShader ) else lightDefault
	)

def __plugDescription( plug ) :

	return __descriptions.get( plug.node()["name"].getValue() + "." + plug.getName() )

for nodeType in ( GafferArnold.ArnoldShader, GafferArnold.ArnoldLight ) :

	Gaffer.Metadata.registerNodeValue( nodeType, "description", __nodeDescription )
	Gaffer.Metadata.registerPlugValue( nodeType, "parameters.*", "description", __plugDescription )

##########################################################################
# Nodule and widget creators
##########################################################################

def __parameterNoduleType( plug ) :

	if isinstance( plug, ( Gaffer.BoolPlug, Gaffer.IntPlug, Gaffer.StringPlug ) ) :
		return ""

	return "GafferUI::StandardNodule"

GafferUI.Metadata.registerPlugValue( GafferArnold.ArnoldShader, "parameters.*", "nodule:type", __parameterNoduleType )

def __plugValueWidgetCreator( plug ) :

	paramPath = plug.node()["name"].getValue() + "." + plug.getName()
	customCreator = __plugValueWidgetCreators.get( paramPath, None )
	if customCreator is not None :
		return customCreator[0]( plug, *customCreator[1:] )

	return GafferUI.PlugValueWidget.create( plug, useTypeOnly=True )

GafferUI.PlugValueWidget.registerCreator( GafferArnold.ArnoldShader, "parameters.*", __plugValueWidgetCreator )
GafferUI.PlugValueWidget.registerCreator( GafferArnold.ArnoldLight, "parameters.*", __plugValueWidgetCreator )
