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

__metadata = collections.defaultdict( dict )

with IECoreArnold.UniverseBlock() :

	nodeIt = arnold.AiUniverseGetNodeEntryIterator( arnold.AI_NODE_SHADER | arnold.AI_NODE_LIGHT )
	while not arnold.AiNodeEntryIteratorFinished( nodeIt ) :

		nodeEntry = arnold.AiNodeEntryIteratorGetNext( nodeIt )
		nodeName = arnold.AiNodeEntryGetName( nodeEntry )

		description = __aiMetadataGetStr( nodeEntry, None, "desc" )
		if description is not None :
			__metadata[nodeName]["description"] = description

		paramIt = arnold.AiNodeEntryGetParamIterator( nodeEntry )
		while not arnold.AiParamIteratorFinished( paramIt ) :

			## \todo We could allow custom ui types to be specified using
			# arnold metadata entries.
			param = arnold.AiParamIteratorGetNext( paramIt )
			paramName = arnold.AiParamGetName( param )
			paramPath = nodeName + "." + paramName

			description = __aiMetadataGetStr( nodeEntry, paramName, "desc" )
			if description is not None :
				__metadata[paramPath]["description"] = description

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

def __plugMetadata( plug, name ) :

	if isinstance( plug.node(), GafferArnold.ArnoldShader ) :
		key = plug.node()["name"].getValue() + "." + plug.getName()
	else :
		# Node type is ArnoldLight.
		key = plug.node()["__shaderName"].getValue() + "." + plug.getName()

	return __metadata[key].get( name )

def __noduleType( plug ) :

	if isinstance( plug, ( Gaffer.BoolPlug, Gaffer.IntPlug, Gaffer.StringPlug ) ) :
		return ""

	return "GafferUI::StandardNodule"

for nodeType in ( GafferArnold.ArnoldShader, GafferArnold.ArnoldLight ) :

	Gaffer.Metadata.registerNodeValue( nodeType, "description", __nodeDescription )
	GafferUI.Metadata.registerPlugValue( nodeType, "parameters.*", "nodule:type", __noduleType )

	for name in [
		"description",
		"presetNames",
		"presetValues",
		"plugValueWidget:type"
	] :

		Gaffer.Metadata.registerPlugValue(
			nodeType,
			"parameters.*",
			name,
			functools.partial( __plugMetadata, name = name )
		)
