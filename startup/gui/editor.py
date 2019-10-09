##########################################################################
#
#  Copyright (c) 2018, Image Engine Design Inc. All rights reserved.
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
import weakref

import GafferUI
import GafferSceneUI

def __editorCreated( editor ) :

	GafferUI.GraphBookmarksUI.connectToEditor( editor )
	GafferSceneUI.SceneHistoryUI.connectToEditor( editor )

GafferUI.Editor.instanceCreatedSignal().connect( __editorCreated, scoped = False )


#### Editor follows Scene Selection

# This makes the supplied editor follow the source node of the scene selection of another editor.
# When followSelectionSource is True, the editor will follow the source node for the scene
# selection (as observed by the targetEditor's nodeSet), instead of the targets nodeSet itself.
# For example, a NodeEditor linked to a Viewer with followSelectionSource would show the source
# node for any selected lights/objects.

def __driveFromSceneSelectionSourceChangeCallback( editor, targetEditor ) :

	sourceSet = targetEditor.getNodeSet()
	context = targetEditor.getContext()
	return GafferSceneUI.SourceSet( context, sourceSet )

DriverModeSceneSelectionSource = "SceneSelectionSource"
GafferUI.NodeSetEditor.registerNodeSetDriverMode(
	DriverModeSceneSelectionSource, __driveFromSceneSelectionSourceChangeCallback,
	"Following the scene selection's source node from {editor}."
)


### Pinning Menu Items

# Helper for registering unique menu items considering current state
def __addFollowMenuItem( menuDefinition, editor, targetEditor, subMenuTitle, mode, dedupe ) :

		title = targetEditor.getTitle()

		# We could easily have collisions
		dedupe[ title ] = dedupe.setdefault( title, 0 ) + 1
		if dedupe[ title ] > 1 :
			title += " (%d)" % dedupe[ title ]

		existingDriver, existingMode = editor.getNodeSetDriver()
		weakEditor = weakref.ref( editor )
		weakTarget = weakref.ref( targetEditor )

		highlightTarget = weakref.ref( targetEditor.parent().parent() if targetEditor._qtWidget().isHidden() else targetEditor.parent() )

		isCurrent = existingMode == mode if existingDriver is targetEditor else False
		menuDefinition.insertBefore( "/%s/%s" % ( subMenuTitle, title ), {
			"command" : lambda _ : weakEditor().setNodeSetDriver( weakTarget(), mode ),
			"active" : not editor.drivesNodeSet( targetEditor ),
			"checkBox" : isCurrent,
			"enter" : lambda : highlightTarget().setHighlighted( True ),
			"leave" : lambda : highlightTarget().setHighlighted( False )
		}, "/Pin Divider" )

# Simple follows, eg: Hierarchy -> Viewer
def __registerEditorNodeSetDriverItems( editor, menuDefinition ) :

	if not isinstance( editor, (
		GafferUI.Viewer,
		GafferUI.NodeEditor,
		GafferUI.AnimationEditor,
		GafferSceneUI.HierarchyView,
		GafferSceneUI.SceneInspector,
		GafferSceneUI.PrimitiveInspector,
		GafferSceneUI.UVInspector
	) ) :
		return

	# Generally, we consider the Viewer/Hierarchy views 'focal' editors as
	# they can affect the context selection/expansion state, etc...
	parentCompoundEditor = editor.ancestor( GafferUI.CompoundEditor )
	targets = parentCompoundEditor.editors( GafferUI.Viewer )
	targets.extend( parentCompoundEditor.editors( GafferSceneUI.HierarchyView ) )

	itemNameCounts = {}
	for target in targets :
		if target is not editor :
			__addFollowMenuItem( menuDefinition,
				editor, target,
				"Editor",
				GafferUI.NodeSetEditor.DriverModeNodeSet ,
				itemNameCounts
			)

# Selection follows, ie: NodeEditor -> Viewer
def __registerNodeSetFollowsSceneSelectionItems( editor, menuDefinition ) :

	if not isinstance( editor, GafferUI.NodeEditor ) :
		return

	# We support Viewers and Hierarchy Views as they are the only
	# standard editors that manipulate the selection in the context.
	parentCompoundEditor = editor.ancestor( GafferUI.CompoundEditor )
	targets = parentCompoundEditor.editors( GafferUI.Viewer )
	targets.extend( parentCompoundEditor.editors( GafferSceneUI.HierarchyView ) )

	itemNameCounts = {}
	for target in targets :
		if target is not editor :
			__addFollowMenuItem( menuDefinition,
				editor, target,
				"Scene Selection",
				DriverModeSceneSelectionSource,
				itemNameCounts
			)

## Registration

def __registerNodeSetMenuItems( editor, menuDefinition ) :

	__registerNodeSetFollowsSceneSelectionItems( editor, menuDefinition )
	__registerEditorNodeSetDriverItems( editor, menuDefinition )

	GafferUI.GraphBookmarksUI.appendNodeSetMenuDefinitions( editor, menuDefinition )

GafferUI.CompoundEditor.nodeSetMenuSignal().connect( __registerNodeSetMenuItems, scoped = False )
