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
Gaffer.Metadata.registerValue( GafferDispatch.TaskNode.TaskPlug, "nodule:color", imath.Color3f( 0.645, 0.2483, 0.2483 ) )
Gaffer.Metadata.registerValue( GafferDispatch.TaskNode.TaskPlug, "connectionGadget:color", imath.Color3f( 0.315, 0.0787, 0.0787 ) )

Gaffer.Metadata.registerValue( Gaffer.SubGraph, "nodeGadget:color", imath.Color3f( 0.225 ) )
Gaffer.Metadata.registerValue( Gaffer.BoxIO, "nodeGadget:color", imath.Color3f( 0.225 ) )
Gaffer.Metadata.registerValue( Gaffer.EditScope, "nodeGadget:color", imath.Color3f( 0.1876, 0.3908, 0.6 ) )

Gaffer.Metadata.registerValue( Gaffer.Random, "nodeGadget:color", imath.Color3f( 0.45, 0.3, 0.3 ) )
Gaffer.Metadata.registerValue( Gaffer.Expression, "nodeGadget:color", imath.Color3f( 0.3, 0.45, 0.3 ) )
Gaffer.Metadata.registerValue( Gaffer.Animation, "nodeGadget:color", imath.Color3f( 0.3, 0.3, 0.45 ) )
Gaffer.Metadata.registerValue( Gaffer.Spreadsheet, "nodeGadget:color", imath.Color3f( 0.69, 0.5445, 0.2208 ) )

Gaffer.Metadata.registerValue( GafferScene.ScenePlug, "nodule:color", imath.Color3f( 0.2401, 0.3394, 0.485 ) )

Gaffer.Metadata.registerValue( GafferScene.SceneProcessor, "nodeGadget:color", imath.Color3f( 0.495, 0.2376, 0.4229 ) )
Gaffer.Metadata.registerValue( GafferScene.SceneElementProcessor, "nodeGadget:color", imath.Color3f( 0.1886, 0.2772, 0.41 ) )

Gaffer.Metadata.registerValue( GafferScene.FilterPlug, "nodule:color", imath.Color3f( 0.69, 0.5378, 0.2283 ) )

Gaffer.Metadata.registerValue( GafferScene.Transform, "nodeGadget:color", imath.Color3f( 0.485, 0.3112, 0.2255 ) )
Gaffer.Metadata.registerValue( GafferScene.Constraint, "nodeGadget:color", imath.Color3f( 0.485, 0.3112, 0.2255 ) )

Gaffer.Metadata.registerValue( GafferScene.GlobalsProcessor, "nodeGadget:color", imath.Color3f( 0.255, 0.505, 0.28 ) )

Gaffer.Metadata.registerValue( Gaffer.FloatPlug, "nodule:color", imath.Color3f( 0.2467, 0.3762, 0.47 ) )
Gaffer.Metadata.registerValue( Gaffer.Color3fPlug, "nodule:color", imath.Color3f( 0.69, 0.5378, 0.2283 ) )
Gaffer.Metadata.registerValue( Gaffer.V3fPlug, "nodule:color", imath.Color3f( 0.47, 0.181, 0.181 ) )

##########################################################################
# Behaviour
##########################################################################

def __nodeDoubleClick( graphEditor, node ) :

	GafferUI.NodeEditor.acquire( node, floating = True )
	return True

GafferUI.GraphEditor.nodeDoubleClickSignal().connect( __nodeDoubleClick, scoped = False )

def __nodeContextMenu( graphEditor, node, menuDefinition ) :

	menuDefinition.append( "/Edit...", { "command" : functools.partial( GafferUI.NodeEditor.acquire, node, floating = True ) } )

	GafferUI.GraphEditor.appendFocusMenuDefinitions( graphEditor, node, menuDefinition )
	GafferUI.GraphEditor.appendEnabledPlugMenuDefinitions( graphEditor, node, menuDefinition )
	GafferUI.GraphEditor.appendConnectionVisibilityMenuDefinitions( graphEditor, node, menuDefinition )
	GafferDispatchUI.DispatcherUI.appendNodeContextMenuDefinitions( graphEditor, node, menuDefinition )
	GafferUI.GraphEditor.appendContentsMenuDefinitions( graphEditor, node, menuDefinition )
	GafferUI.UIEditor.appendNodeContextMenuDefinitions( graphEditor, node, menuDefinition )
	GafferSceneUI.FilteredSceneProcessorUI.appendNodeContextMenuDefinitions( graphEditor, node, menuDefinition )
	GafferUI.GraphBookmarksUI.appendNodeContextMenuDefinitions( graphEditor, node, menuDefinition )

GafferUI.GraphEditor.nodeContextMenuSignal().connect( __nodeContextMenu, scoped = False )

def __plugContextMenu( graphEditor, plug, menuDefinition ) :

	GafferUI.GraphBookmarksUI.appendPlugContextMenuDefinitions( graphEditor, plug, menuDefinition )
	GafferUI.NodeUI.appendPlugDeletionMenuDefinitions( plug, menuDefinition )

GafferUI.GraphEditor.plugContextMenuSignal().connect( __plugContextMenu, scoped = False )

def __connectionContextMenu( graphEditor, destinationPlug, menuDefinition ) :

	GafferUI.GraphEditor.appendConnectionNavigationMenuDefinitions( graphEditor, destinationPlug, menuDefinition )

GafferUI.GraphEditor.connectionContextMenuSignal().connect( __connectionContextMenu, scoped = False )
