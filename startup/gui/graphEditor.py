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

import functools
import imath

import IECore

import Gaffer
import GafferUI
import GafferScene
import GafferSceneUI
import GafferDispatch
import GafferDispatchUI

##########################################################################
# Colour
##########################################################################

Gaffer.Metadata.registerValue( GafferDispatch.TaskNode, "nodeGadget:color", imath.Color3f( 0.61, 0.1525, 0.1525 ) )
Gaffer.Metadata.registerValue( GafferDispatch.TaskNode, "task", "nodule:color", imath.Color3f( 0.645, 0.2483, 0.2483 ) )
Gaffer.Metadata.registerValue( GafferDispatch.TaskNode, "preTasks.*", "nodule:color", imath.Color3f( 0.645, 0.2483, 0.2483 ) )
Gaffer.Metadata.registerValue( GafferDispatch.TaskNode, "postTasks.*", "nodule:color", imath.Color3f( 0.645, 0.2483, 0.2483 ) )
Gaffer.Metadata.registerValue( GafferDispatch.TaskNode, "task", "connectionGadget:color", imath.Color3f( 0.315, 0.0787, 0.0787 ) )
Gaffer.Metadata.registerValue( GafferDispatch.TaskNode, "preTasks.*", "connectionGadget:color", imath.Color3f( 0.315, 0.0787, 0.0787 ) )
Gaffer.Metadata.registerValue( GafferDispatch.TaskNode, "postTasks.*", "connectionGadget:color", imath.Color3f( 0.315, 0.0787, 0.0787 ) )

Gaffer.Metadata.registerValue( Gaffer.SubGraph, "nodeGadget:color", imath.Color3f( 0.225 ) )
Gaffer.Metadata.registerValue( Gaffer.BoxIO, "nodeGadget:color", imath.Color3f( 0.225 ) )

Gaffer.Metadata.registerValue( Gaffer.Random, "nodeGadget:color", imath.Color3f( 0.45, 0.3, 0.3 ) )
Gaffer.Metadata.registerValue( Gaffer.Expression, "nodeGadget:color", imath.Color3f( 0.3, 0.45, 0.3 ) )
Gaffer.Metadata.registerValue( Gaffer.Animation, "nodeGadget:color", imath.Color3f( 0.3, 0.3, 0.45 ) )

Gaffer.Metadata.registerValue( GafferScene.SceneNode, "in...", "nodule:color", imath.Color3f( 0.2401, 0.3394, 0.485 ) )
Gaffer.Metadata.registerValue( GafferScene.SceneNode, "out", "nodule:color", imath.Color3f( 0.2401, 0.3394, 0.485 ) )
Gaffer.Metadata.registerValue( GafferScene.InteractiveRender, "in", "nodule:color", imath.Color3f( 0.2346, 0.326, 0.46 ) )
Gaffer.Metadata.registerValue( GafferScene.Parent, "child", "nodule:color", imath.Color3f( 0.2346, 0.326, 0.46 ) )

Gaffer.Metadata.registerValue( GafferScene.SceneProcessor, "nodeGadget:color", imath.Color3f( 0.495, 0.2376, 0.4229 ) )
Gaffer.Metadata.registerValue( GafferScene.SceneElementProcessor, "nodeGadget:color", imath.Color3f( 0.1886, 0.2772, 0.41 ) )

Gaffer.Metadata.registerValue( GafferScene.FilteredSceneProcessor, "filter", "nodule:color", imath.Color3f( 0.69, 0.5378, 0.2283 ) )
Gaffer.Metadata.registerValue( GafferScene.Filter, "out", "nodule:color", imath.Color3f( 0.69, 0.5378, 0.2283 ) )
Gaffer.Metadata.registerValue( GafferScene.Filter, "in...", "nodule:color", imath.Color3f( 0.69, 0.5378, 0.2283 ) )

Gaffer.Metadata.registerValue( GafferScene.Transform, "nodeGadget:color", imath.Color3f( 0.485, 0.3112, 0.2255 ) )
Gaffer.Metadata.registerValue( GafferScene.Constraint, "nodeGadget:color", imath.Color3f( 0.485, 0.3112, 0.2255 ) )

Gaffer.Metadata.registerValue( GafferScene.GlobalsProcessor, "nodeGadget:color", imath.Color3f( 0.255, 0.505, 0.28 ) )

__shaderNoduleColors = {
	Gaffer.FloatPlug.staticTypeId() : IECore.Color3fData( imath.Color3f( 0.2467, 0.3762, 0.47 ) ),
	Gaffer.Color3fPlug.staticTypeId() : IECore.Color3fData( imath.Color3f( 0.69, 0.5378, 0.2283 ) ),
	Gaffer.V3fPlug.staticTypeId() : IECore.Color3fData( imath.Color3f( 0.47, 0.181, 0.181 ) ),
}

def __shaderNoduleColor( plug ) :

	return __shaderNoduleColors.get( plug.typeId(), None )

Gaffer.Metadata.registerValue( GafferScene.Shader, "...", "nodule:color", __shaderNoduleColor )

##########################################################################
# Behaviour
##########################################################################

def __nodeDoubleClick( graphEditor, node ) :

	GafferUI.NodeEditor.acquire( node, floating = True )
	return True

GafferUI.GraphEditor.nodeDoubleClickSignal().connect( __nodeDoubleClick, scoped = False )

def __nodeContextMenu( graphEditor, node, menuDefinition ) :

	menuDefinition.append( "/Edit...", { "command" : functools.partial( GafferUI.NodeEditor.acquire, node, floating = True ) } )

	GafferUI.GraphEditor.appendEnabledPlugMenuDefinitions( graphEditor, node, menuDefinition )
	GafferUI.GraphEditor.appendConnectionVisibilityMenuDefinitions( graphEditor, node, menuDefinition )
	GafferDispatchUI.DispatcherUI.appendNodeContextMenuDefinitions( graphEditor, node, menuDefinition )
	GafferUI.GraphEditor.appendContentsMenuDefinitions( graphEditor, node, menuDefinition )
	GafferUI.UIEditor.appendNodeContextMenuDefinitions( graphEditor, node, menuDefinition )
	GafferSceneUI.FilteredSceneProcessorUI.appendNodeContextMenuDefinitions( graphEditor, node, menuDefinition )

GafferUI.GraphEditor.nodeContextMenuSignal().connect( __nodeContextMenu, scoped = False )

GafferUI.GraphBookmarksUI.connect( application.root() )
