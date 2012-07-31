##########################################################################
#  
#  Copyright (c) 2012, John Haddon. All rights reserved.
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

import arnold

import IECoreArnold

import GafferUI
import GafferArnold

## \todo This will belong with a Shader base class node at some point, probably in
# GafferScene.
def __nodeGadgetCreator( node ) :

	return GafferUI.StandardNodeGadget( node, GafferUI.LinearContainer.Orientation.Y )

GafferUI.NodeGadget.registerNodeGadget( GafferArnold.ArnoldShader.staticTypeId(), __nodeGadgetCreator )

def __parametersNoduleCreator( plug ) :

	return GafferUI.CompoundNodule( plug, GafferUI.LinearContainer.Orientation.Y )

GafferUI.Nodule.registerNodule( GafferArnold.ArnoldShader.staticTypeId(), "parameters", __parametersNoduleCreator )

__plugValueWidgetCreators = {}

with IECoreArnold.UniverseBlock() :

	nodeIt = arnold.AiUniverseGetNodeEntryIterator( arnold.AI_NODE_SHADER )
	while not arnold.AiNodeEntryIteratorFinished( nodeIt ) :
		
		nodeEntry = arnold.AiNodeEntryIteratorGetNext( nodeIt )
		nodeName = arnold.AiNodeEntryGetName( nodeEntry )
		
		paramIt = arnold.AiNodeEntryGetParamIterator( nodeEntry )
		while not arnold.AiParamIteratorFinished( paramIt ) :
			
			## \todo We could allow custom ui types to be specified using
			# arnold metadata entries.
			param = arnold.AiParamIteratorGetNext( paramIt )
			paramPath = nodeName + "." + arnold.AiParamGetName( param )
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
			
def __plugValueWidgetCreator( plug ) :

	paramPath = plug.node()["__shaderName"].getValue() + "." + plug.getName()
	customCreator = __plugValueWidgetCreators.get( paramPath, None )
	if customCreator is not None :
		return customCreator[0]( plug, *customCreator[1:] )

	return GafferUI.PlugValueWidget.create( plug, useTypeOnly=True )
	
GafferUI.PlugValueWidget.registerCreator( GafferArnold.ArnoldShader.staticTypeId(), "parameters.*", __plugValueWidgetCreator )
GafferUI.PlugValueWidget.registerCreator( GafferArnold.ArnoldShader.staticTypeId(), "parameters", GafferUI.CompoundPlugValueWidget, collapsible=False )
