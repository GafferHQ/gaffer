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
import pathlib
import re
import weakref

import imath

import IECore

import Gaffer
import GafferUI
import GafferImage
import GafferScene
import GafferSceneUI
import GafferDispatch
import GafferDispatchUI

##########################################################################
# Colour
##########################################################################

Gaffer.Metadata.registerValue( GafferDispatch.TaskNode, "nodeGadget:color", imath.Color3f( 0.61, 0.1525, 0.1525 ) )
Gaffer.Metadata.registerValue( GafferDispatch.TaskNode.TaskPlug, "nodule:color", imath.Color3f( 0.71, 0.35, 0.35 ) )
Gaffer.Metadata.registerValue( GafferDispatch.TaskNode.TaskPlug, "connectionGadget:color", imath.Color3f( 0.71, 0.35, 0.35 ) )

Gaffer.Metadata.registerValue( Gaffer.SubGraph, "nodeGadget:color", imath.Color3f( 0.225 ) )
Gaffer.Metadata.registerValue( Gaffer.BoxIO, "nodeGadget:color", imath.Color3f( 0.225 ) )
Gaffer.Metadata.registerValue( Gaffer.EditScope, "nodeGadget:color", imath.Color3f( 0.1876, 0.3908, 0.6 ) )

Gaffer.Metadata.registerValue( Gaffer.Random, "nodeGadget:color", imath.Color3f( 0.45, 0.3, 0.3 ) )
Gaffer.Metadata.registerValue( Gaffer.RandomChoice, "nodeGadget:color", imath.Color3f( 0.45, 0.3, 0.3 ) )
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

	GafferUI.GraphEditor.appendEnabledPlugMenuDefinitions( graphEditor, node, menuDefinition )
	GafferUI.GraphEditor.appendConnectionVisibilityMenuDefinitions( graphEditor, node, menuDefinition )
	GafferUI.GraphEditor.appendContentsMenuDefinitions( graphEditor, node, menuDefinition )
	GafferUI.UIEditor.appendNodeContextMenuDefinitions( graphEditor, node, menuDefinition )
	GafferUI.AnnotationsUI.appendNodeContextMenuDefinitions( graphEditor, node, menuDefinition )
	GafferSceneUI.FilteredSceneProcessorUI.appendNodeContextMenuDefinitions( graphEditor, node, menuDefinition )
	GafferSceneUI.CryptomatteUI.appendNodeContextMenuDefinitions( graphEditor, node, menuDefinition )
	GafferUI.GraphBookmarksUI.appendNodeContextMenuDefinitions( graphEditor, node, menuDefinition )

GafferUI.GraphEditor.nodeContextMenuSignal().connect( __nodeContextMenu, scoped = False )

def __plugContextMenu( graphEditor, plug, menuDefinition ) :

	GafferUI.GraphBookmarksUI.appendPlugContextMenuDefinitions( graphEditor, plug, menuDefinition )
	GafferUI.NodeUI.appendPlugDeletionMenuDefinitions( plug, menuDefinition )

GafferUI.GraphEditor.plugContextMenuSignal().connect( __plugContextMenu, scoped = False )

def __connectionContextMenu( graphEditor, destinationPlug, menuDefinition ) :

	GafferUI.GraphEditor.appendConnectionNavigationMenuDefinitions( graphEditor, destinationPlug, menuDefinition )

GafferUI.GraphEditor.connectionContextMenuSignal().connect( __connectionContextMenu, scoped = False )

##########################################################################
# File drop handler
##########################################################################

GafferUI.Pointer.registerPointer( "targetObjects", GafferUI.Pointer( "targetObjects.png", imath.V2i( 53, 14 ) ) )

def __sceneFileHandler( fileName ) :

	result = GafferScene.SceneReader()
	result["fileName"].setValue( fileName )
	return result

def __imageFileHandler( fileName ) :

	result = GafferImage.ImageReader()
	result["fileName"].setValue( fileName )
	return result

def __referenceFileHandler( fileName ) :

	# We need a temp ScriptNode to be able to call `load()`,
	# but we can safely discard it afterwards and reparent
	# the Reference somewhere else.
	script = Gaffer.ScriptNode()
	script["Reference"] = Gaffer.Reference()
	script["Reference"].load( fileName )
	return script["Reference"]

## \todo Maybe we should move this to GraphGadget and add a
# public API to allow people to register their own handlers?

__fileHandlers = {
	"grf" : __referenceFileHandler
}

__fileHandlers.update( {
	ext : __sceneFileHandler
	for ext in GafferScene.SceneReader.supportedExtensions()
} )

__fileHandlers.update( {
	ext : __imageFileHandler
	for ext in GafferImage.ImageReader.supportedExtensions()
} )

def __dropHandler( s ) :

	path = pathlib.Path( s )
	if not path.suffix or not path.is_file() :
		return None

	handler = __fileHandlers.get( path.suffix[1:].lower() )
	return functools.partial( handler, path ) if handler is not None else None

def __canDropFiles( graphGadget, event ) :

	return (
		isinstance( event.data, IECore.StringVectorData ) and
		all( __dropHandler( s ) is not None for s in event.data ) and
		not Gaffer.MetadataAlgo.readOnly( graphGadget.getRoot() ) and
		not Gaffer.MetadataAlgo.getChildNodesAreReadOnly( graphGadget.getRoot() )
	)

def __fileDragEnter( graphGadget, event ) :

	return __canDropFiles( graphGadget, event )

def __fileDrop( graphGadget, event ) :

	if not __canDropFiles( graphGadget, event ) :
		return False

	position = imath.V2f( event.line.p0.x, event.line.p0.y  )

	scriptNode = graphGadget.getRoot().scriptNode()
	nodes = Gaffer.StandardSet()
	with Gaffer.UndoScope( scriptNode ) :

		for s in event.data :

			node =  __dropHandler( s )()

			## \todo GraphComponent should either provide a utility
			# to sanitise a name, or `setName()` should just sanitise
			# the name automatically.
			name = re.sub(
				"[^A-Za-z_:0-9]",
				"_",
				pathlib.Path( s ).stem
			)
			if name[0].isdigit() :
				name = "_" + name

			node.setName( name )
			graphGadget.getRoot().addChild( node )

			nodeGadget = graphGadget.nodeGadget( node )
			width = nodeGadget.bound().size().x
			if len( nodes ) :
				position.x += width / 2

			graphGadget.setNodePosition( node, position )
			position.x += 2 + width / 2

			nodes.add( node )

	scriptNode.selection().clear()
	scriptNode.selection().add( nodes )

	return True

##########################################################################
# Scene location drop handler
##########################################################################

def __dropLocationData( event ) :

	if (
		not isinstance( event.data, IECore.StringVectorData ) or
		len( event.data ) != 1 or
		not event.data[0].startswith( "/" ) or
		event.sourceWidget is None
	) :
		return None

	scene = None
	sourceEditor = event.sourceWidget.ancestor( GafferUI.Editor )
	if isinstance( sourceEditor, GafferUI.Viewer ) :
		if isinstance( event.sourceGadget, GafferSceneUI.SceneGadget ) :
			scene = sourceEditor.view()["in"].getInput()
	elif isinstance( sourceEditor, GafferSceneUI.HierarchyView ) :
		scene = sourceEditor.scene()

	if scene is None :
		return None

	return {
		"path" : event.data[0],
		"scene" : scene,
		"context" : sourceEditor.getContext(),
	}

def __locationDragEnter( graphGadget, event ) :

	if __dropLocationData( event ) is None :
		return False

	GafferUI.Pointer.setCurrent( "targetObjects" )
	return True

def __locationDragLeave( graphGadget, event ) :

	if __dropLocationData( event ) is not None :
		if event.destinationWidget is None :
			# Hack to restore (what we assume to have been) the original
			# drag pointer. We don't do this when another widget has
			# accepted the drag, because it would clobber any pointer
			# change they made in `dragEnter`. But of course that means
			# that if another widget _has_ accepted the drag but hasn't
			# changed the pointer themselves (maybe they use highlighting
			# instead), they will be stuck with the wrong pointer.
			## \todo This is far too fragile. We need to manage
			# pointer restoration at a higher level, in Widget.py's
			# _EventFilter (and ViewportGadget's handlers).
			GafferUI.Pointer.setCurrent( "objects" )
		return True

	return False

def __locationDrop( graphGadget, event, graphEditor ) :

	dropLocationData = __dropLocationData( event )
	if dropLocationData is None :
		return False

	with dropLocationData["context"] :
		sourceScene = GafferScene.SceneAlgo.source( dropLocationData["scene"], dropLocationData["path"] )

	if sourceScene is not None :
		graphGadget.setRoot( sourceScene.node().parent() )
		## \todo The `frame()` method should probably be on the GraphGadget itself, and the `at`
		# functionality should be made public.
		graphEditor()._GraphEditor__frame(
			[ sourceScene.node() ],
			at = imath.V2f( GafferUI.Widget.mousePosition( relativeTo = graphEditor() ) )
		)

	return True

def __graphEditorCreated( graphEditor ) :

	graphEditor.graphGadget().dragEnterSignal().connect( __fileDragEnter, scoped = False )
	graphEditor.graphGadget().dropSignal().connect( __fileDrop, scoped = False )

	graphEditor.graphGadget().dragEnterSignal().connect( __locationDragEnter, scoped = False )
	graphEditor.graphGadget().dragLeaveSignal().connect( __locationDragLeave, scoped = False )
	graphEditor.graphGadget().dropSignal().connect( functools.partial( __locationDrop, graphEditor = weakref.ref( graphEditor ) ), scoped = False )

GafferUI.GraphEditor.instanceCreatedSignal().connect( __graphEditorCreated, scoped = False )
