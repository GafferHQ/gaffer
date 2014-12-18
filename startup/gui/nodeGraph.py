##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
#  Copyright (c) 2013-2014, Image Engine Design Inc. All rights reserved.
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

import IECore

import Gaffer
import GafferUI
import GafferScene
import GafferSceneUI

##########################################################################
# Colour
##########################################################################

Gaffer.Metadata.registerNodeValue( Gaffer.ExecutableNode, "nodeGadget:color", IECore.Color3f( 0.61, 0.1525, 0.1525 ) )
Gaffer.Metadata.registerPlugValue( Gaffer.ExecutableNode, "requirement", "nodule:color", IECore.Color3f( 0.645, 0.2483, 0.2483 ) )
Gaffer.Metadata.registerPlugValue( Gaffer.ExecutableNode, "requirements.*", "nodule:color", IECore.Color3f( 0.645, 0.2483, 0.2483 ) )
Gaffer.Metadata.registerPlugValue( Gaffer.ExecutableNode, "requirement", "connectionGadget:color", IECore.Color3f( 0.315, 0.0787, 0.0787 ) )
Gaffer.Metadata.registerPlugValue( Gaffer.ExecutableNode, "requirements.*", "connectionGadget:color", IECore.Color3f( 0.315, 0.0787, 0.0787 ) )

Gaffer.Metadata.registerNodeValue( Gaffer.SubGraph, "nodeGadget:color", IECore.Color3f( 0.225 ) )

Gaffer.Metadata.registerPlugValue( GafferScene.SceneNode, "in*", "nodule:color", IECore.Color3f( 0.2401, 0.3394, 0.485 ) )
Gaffer.Metadata.registerPlugValue( GafferScene.SceneNode, "out", "nodule:color", IECore.Color3f( 0.2401, 0.3394, 0.485 ) )
Gaffer.Metadata.registerPlugValue( GafferScene.ExecutableRender, "in", "nodule:color", IECore.Color3f( 0.2346, 0.326, 0.46 ) )
Gaffer.Metadata.registerPlugValue( GafferScene.InteractiveRender, "in", "nodule:color", IECore.Color3f( 0.2346, 0.326, 0.46 ) )
Gaffer.Metadata.registerPlugValue( GafferScene.Parent, "child", "nodule:color", IECore.Color3f( 0.2346, 0.326, 0.46 ) )

Gaffer.Metadata.registerNodeValue( GafferScene.SceneProcessor, "nodeGadget:color", IECore.Color3f( 0.495, 0.2376, 0.4229 ) )
Gaffer.Metadata.registerNodeValue( GafferScene.SceneElementProcessor, "nodeGadget:color", IECore.Color3f( 0.1886, 0.2772, 0.41 ) )

Gaffer.Metadata.registerPlugValue( GafferScene.FilteredSceneProcessor, "filter", "nodule:color", IECore.Color3f( 0.69, 0.5378, 0.2283 ) )
Gaffer.Metadata.registerPlugValue( GafferScene.Filter, "match", "nodule:color", IECore.Color3f( 0.69, 0.5378, 0.2283 ) )

Gaffer.Metadata.registerNodeValue( GafferScene.Transform, "nodeGadget:color", IECore.Color3f( 0.485, 0.3112, 0.2255 ) )
Gaffer.Metadata.registerNodeValue( GafferScene.Constraint, "nodeGadget:color", IECore.Color3f( 0.485, 0.3112, 0.2255 ) )

Gaffer.Metadata.registerNodeValue( GafferScene.GlobalsProcessor, "nodeGadget:color", IECore.Color3f( 0.255, 0.505, 0.28 ) )

__shaderNoduleColors = {
	Gaffer.FloatPlug.staticTypeId() : IECore.Color3fData( IECore.Color3f( 0.2467, 0.3762, 0.47 ) ),
	Gaffer.Color3fPlug.staticTypeId() : IECore.Color3fData( IECore.Color3f( 0.69, 0.5378, 0.2283 ) ),
	Gaffer.V3fPlug.staticTypeId() : IECore.Color3fData( IECore.Color3f( 0.47, 0.181, 0.181 ) ),
}

def __shaderNoduleColor( plug ) :

	return __shaderNoduleColors.get( plug.typeId(), None )

Gaffer.Metadata.registerPlugValue( GafferScene.Shader, "*", "nodule:color", __shaderNoduleColor )

##########################################################################
# Behaviour
##########################################################################

## \todo Make this behaviour a part of the preferences.
def __nodeDoubleClick( nodeGraph, node ) :

	GafferUI.NodeEditor.acquire( node )

__nodeDoubleClickConnection = GafferUI.NodeGraph.nodeDoubleClickSignal().connect( __nodeDoubleClick )

def __nodeContextMenu( nodeGraph, node, menuDefinition ) :

	menuDefinition.append( "/Edit...", { "command" : IECore.curry( GafferUI.NodeEditor.acquire, node ) } )

	GafferUI.NodeGraph.appendEnabledPlugMenuDefinitions( nodeGraph, node, menuDefinition )
	GafferUI.NodeGraph.appendConnectionVisibilityMenuDefinitions( nodeGraph, node, menuDefinition )
	GafferUI.DispatcherUI.appendNodeContextMenuDefinitions( nodeGraph, node, menuDefinition )
	GafferUI.BoxUI.appendNodeContextMenuDefinitions( nodeGraph, node, menuDefinition )
	GafferUI.UIEditor.appendNodeContextMenuDefinitions( nodeGraph, node, menuDefinition )
	GafferSceneUI.FilteredSceneProcessorUI.appendNodeContextMenuDefinitions( nodeGraph, node, menuDefinition )

__nodeContextMenuConnection = GafferUI.NodeGraph.nodeContextMenuSignal().connect( __nodeContextMenu )
