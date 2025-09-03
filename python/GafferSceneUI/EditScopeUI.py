##########################################################################
#
#  Copyright (c) 2019, Cinesite VFX Ltd. All rights reserved.
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
import weakref

import IECore

import Gaffer
import GafferUI
import GafferScene
import GafferSceneUI

def appendViewContextMenuItems( viewer, view, menuDefinition ) :

	if not isinstance( view, GafferSceneUI.SceneView ) :
		return None

	scriptNode = view["in"].getInput().ancestor( Gaffer.ScriptNode )
	__appendContextMenuItems( viewer, scriptNode, view.editScope(), menuDefinition, "/Visibility and Pruning" )

def appendColumnContextMenuItems( column, pathListing, menuDefinition ) :

	if pathListing.getColumns().index( column ) != 0 :
		return None

	editor = pathListing.ancestor( GafferUI.Editor )
	__appendContextMenuItems( editor, editor.scriptNode(), editor.editScope(), menuDefinition, "" )

def __appendContextMenuItems( editor, scriptNode, editScope, menuDefinition, prefix ) :

	selection = GafferSceneUI.ScriptNodeAlgo.getSelectedPaths( scriptNode )

	if prefix == "" :
		menuDefinition.append( "/VisibilityDivider", { "divider" : True } )

	menuDefinition.append(
		prefix + "/Hide",
		{
			"command" : functools.partial( __editSelectionVisibility, weakref.ref( editor ) ),
			"active" : not selection.isEmpty() and editScope is not None,
			"shortCut" : "Ctrl+H"
		}
	)
	menuDefinition.append(
		prefix + "/Unhide",
		{
			"command" : functools.partial( __editSelectionVisibility, weakref.ref( editor ), True ),
			"active" : not selection.isEmpty() and editScope is not None,
			"shortCut" : "Ctrl+Shift+H"
		}
	)

	menuDefinition.append( prefix + "/PruningDivider", { "divider" : True } )
	menuDefinition.append(
		prefix + "/Prune",
		{
			"command" : functools.partial( __pruneSelection, weakref.ref( editor ) ),
			"active" : not selection.isEmpty() and editScope is not None,
			"shortCut" : "Ctrl+Backspace, Ctrl+Delete"
		}
	)

# Pruning/Visibility hotkeys
# ==========================

def addPruningActions( editor ) :

	if isinstance( editor, ( GafferUI.Viewer, GafferSceneUI.AttributeEditor, GafferSceneUI.LightEditor, GafferSceneUI.HierarchyView ) ) :
		editor.keyPressSignal().connect( __pruningKeyPress )

def addVisibilityActions( editor ) :

	if isinstance( editor, ( GafferUI.Viewer, GafferSceneUI.AttributeEditor, GafferSceneUI.LightEditor, GafferSceneUI.HierarchyView ) ) :
		editor.keyPressSignal().connect( __visibilityKeyPress )

def connectToEditor( editor ) :

	addVisibilityActions( editor )
	addPruningActions( editor )

	if isinstance( editor, ( GafferSceneUI.AttributeEditor, GafferSceneUI.LightEditor, GafferSceneUI.HierarchyView ) ) :
		editor.sceneListing().columnContextMenuSignal().connect( appendColumnContextMenuItems )

def _hiddenAncestors( scene, paths ) :

	result = IECore.PathMatcher()

	ancestorPaths = IECore.PathMatcher()
	for path in paths.paths() :
		parentPath = path.split( "/" )[1:]
		parentPath.pop()
		while len( parentPath ) > 0 :
			ancestorPaths.addPath( parentPath )
			parentPath.pop()

	for ancestor in ancestorPaths.paths() :
		# Return ancestor locations with a "scene:visible" attribute set to `False`
		if not scene.attributes( ancestor ).get( "scene:visible", IECore.BoolData( True ) ).value :
			result.addPath( ancestor )

	return result

def __pruningKeyPress( editor, event ) :

	if event.key not in ( "Backspace", "Delete" ) :
		return False

	if event.modifiers != event.Modifiers.Control :
		# We require a modifier for now, because being able to delete
		# directly in the Viewer is a significant change, and we're
		# worried it could happen unnoticed by someone trying to
		# delete a _node_ instead. But we swallow the event anyway, to
		# reserve the unmodified keypress for our use in a future where
		# a Gaffer viewer with rich interaction might not be so
		# unexpected.
		return True

	return __pruneSelection( editor )

def __pruneSelection( editor ) :

	if isinstance( editor, weakref.ref ) :
		editor = editor()

	if isinstance( editor, GafferUI.Viewer ) :
		if not isinstance( editor.view(), GafferSceneUI.SceneView ) :
			return False

		editScope = editor.view().editScope()
		inPlug = editor.view()["in"]
	elif isinstance( editor, GafferSceneUI.SceneEditor ) :
		if "editScope" not in editor.settings() :
			return False

		editScope = editor.editScope()
		inPlug = editor.settings()["in"]

	# We return True even when we don't do anything, so the keypress doesn't
	# leak out and get used to delete nodes in the node graph.
	## \todo Maybe we might want to ask if we can prune a common ancestor
	# in the case that all its descendants are selected?
	if editScope is None :
		__warningPopup( editor, "To prune locations, first choose an edit scope." )
		return True
	if Gaffer.MetadataAlgo.readOnly( editScope ) :
		__warningPopup( editor, "The target edit scope {} is read-only.".format( editScope.getName() ) )
		return True

	viewedNode = inPlug.getInput().node()
	if editScope != viewedNode and editScope not in Gaffer.NodeAlgo.upstreamNodes( viewedNode ) :
		# Spare folks from deleting things in a downstream EditScope.
		## \todo When we have a nice Viewer notification system we
		# should emit a warning here.
		__warningPopup( editor, "The target edit scope {} is downstream of the viewed node.".format( editScope.getName() ) )
		return True

	readOnlyReason = GafferScene.EditScopeAlgo.prunedReadOnlyReason( editScope )
	if readOnlyReason is not None :
		__warningPopup( editor, "{} is read-only.".format( readOnlyReason ) )
		return True

	# \todo This needs encapsulating in EditScopeAlgo some how so we don't need
	# to interact with processors directly.
	with editor.context() :
		if not editScope["enabled"].getValue() :
			# Spare folks from deleting something when it won't be
			# apparent what they've done until they reenable the
			# EditScope.
			__warningPopup( editor, "The target edit scope {} is disabled.".format( editScope.getName() ) )
			return True
		pruningProcessor = editScope.acquireProcessor( "PruningEdits", createIfNecessary = False )
		if pruningProcessor is not None and not pruningProcessor["enabled"].getValue() :
			__warningPopup( editor, "{} is disabled.".format( pruningProcessor.relativeName( editScope.parent() ) ) )
			return True

	selection = GafferSceneUI.ScriptNodeAlgo.getSelectedPaths( editor.scriptNode() )
	if not selection.isEmpty() :
		with Gaffer.UndoScope( editScope.ancestor( Gaffer.ScriptNode ) ) :
			GafferScene.EditScopeAlgo.setPruned( editScope, selection, True )

	return True

def __visibilityKeyPress( editor, event ) :

	if not ( event.key == "H" and event.modifiers & event.Modifiers.Control ) :
		return False

	return __editSelectionVisibility( editor, event.modifiers & event.Modifiers.Shift )

def __editSelectionVisibility( editor, makeVisible = False ) :

	if isinstance( editor, weakref.ref ) :
		editor = editor()

	if isinstance( editor, GafferUI.Viewer ) :
		if not isinstance( editor.view(), GafferSceneUI.SceneView ) :
			return False

		editScope = editor.view().editScope()
		inPlug = editor.view()["in"]
		editScopePlug = editor.view()["editScope"]
	elif isinstance( editor, GafferSceneUI.SceneEditor ) :
		if "editScope" not in editor.settings() :
			return False

		editScope = editor.editScope()
		inPlug = editor.settings()["in"]
		editScopePlug = editor.settings()["editScope"]
	else :
		return False

	if editScope is None :
		__warningPopup( editor, "To hide or unhide locations, first choose an edit scope." )
		return True
	if Gaffer.MetadataAlgo.readOnly( editScope ) :
		__warningPopup( editor, "The target edit scope {} is read-only.".format( editScope.getName() ) )
		return True

	selection = GafferSceneUI.ScriptNodeAlgo.getSelectedPaths( editor.scriptNode() )
	if selection.isEmpty() :
		return True

	inspector = GafferSceneUI.Private.AttributeInspector(
		inPlug.getInput(),
		editScopePlug,
		"scene:visible"
	)

	with editor.context() as context :
		if not editScope["enabled"].getValue() :
			# Spare folks from hiding something when it won't be
			# apparent what they've done until they reenable the
			# EditScope or processor.
			__warningPopup( editor, "The target edit scope {} is disabled.".format( editScope.getName() ) )
			return True
		attributeEdits = editScope.acquireProcessor( "AttributeEdits", createIfNecessary = False )
		if attributeEdits is not None and not attributeEdits["enabled"].getValue() :
			__warningPopup( editor, "{} is disabled.".format( attributeEdits.relativeName( editScope.parent() ) ) )
			return True

		with Gaffer.UndoScope( editScope.ancestor( Gaffer.ScriptNode ) ) :
			for path in selection.paths() :
				context["scene:path"] = IECore.InternedStringVectorData( path.split( "/" )[1:] )
				inspection = inspector.inspect()

				if inspection is None or not inspection.editable() :
					continue

				GafferScene.EditScopeAlgo.setVisibility( inspection.editScope(), path, makeVisible )

		if makeVisible :
			hiddenAncestors = _hiddenAncestors( editScope["out"], selection )
			if not hiddenAncestors.isEmpty() :
				__selectInvisibleAncestorsPopup( editor, hiddenAncestors )

	return True

def __selectInvisibleAncestorsPopup( editor, ancestors ) :

	with GafferUI.PopupWindow() as editor.__selectInvisibleAncestorsPopup :
		with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :
			GafferUI.Image( "warningSmall.png" )
			GafferUI.Label( "<h4>Location(s) have been unhidden, but are still not visible because they have invisible ancestors.</h4>" )
			button = GafferUI.Button( image = "selectInvisibleAncestors.png", hasFrame = False, toolTip = "Select invisible ancestors" )
			button.clickedSignal().connect( functools.partial( __selectAncestorsClicked, scriptNode = editor.scriptNode(), ancestors = ancestors ) )

	editor.__selectInvisibleAncestorsPopup.popup( parent = editor )

def __selectAncestorsClicked( widget, scriptNode, ancestors ) :

	GafferSceneUI.ScriptNodeAlgo.setSelectedPaths( scriptNode, ancestors )
	widget.ancestor( GafferUI.Window ).close()
	return True

def __warningPopup( parent, message ) :

	with GafferUI.PopupWindow() as parent.__editScopeWarningPopup :
		with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :
			GafferUI.Image( "warningSmall.png" )
			GafferUI.Label( "<h4>{}</h4>".format( message ) )

	parent.__editScopeWarningPopup.popup( parent = parent )

# Processor Widgets
# =================

class _SceneProcessorWidget( GafferUI.EditScopeUI.SimpleProcessorWidget ) :

	def _linkActivated( self, linkData ) :

		GafferSceneUI.ScriptNodeAlgo.setSelectedPaths(
			self.processor().ancestor( Gaffer.ScriptNode ), linkData
		)

class __LocationEditsWidget( _SceneProcessorWidget ) :

	@staticmethod
	def _summary( processor, linkCreator ) :

		# Get the locations being edited from the spreadsheet.

		canceller = Gaffer.Context.current().canceller()
		activePathMatcher = IECore.PathMatcher()
		disabledPathMatcher = IECore.PathMatcher()
		for row in processor["edits"] :
			IECore.Canceller.check( canceller )
			path = row["name"].getValue()
			if not path :
				continue
			if row["enabled"].getValue() :
				activePathMatcher.addPath( path )
			else :
				disabledPathMatcher.addPath( path )

		# Match those against the scene.

		activePaths = IECore.PathMatcher()
		disabledPaths = IECore.PathMatcher()
		GafferScene.SceneAlgo.matchingPaths( activePathMatcher, processor["in"], activePaths )
		GafferScene.SceneAlgo.matchingPaths( disabledPathMatcher, processor["in"], disabledPaths )

		# Build a summary describing what we found.

		summaries = []
		if activePaths.size() :
			activeLink = linkCreator(
				"{} location{}".format( activePaths.size(), "s" if activePaths.size() > 1 else "" ),
				activePaths
			)
			summaries.append( f"edits on {activeLink}" )
		if disabledPaths.size() :
			disabledLink = linkCreator(
				"{} location{}".format( disabledPaths.size(), "s" if disabledPaths.size() > 1 else "" ),
				disabledPaths
			)
			summaries.append( f"disabled edits on {disabledLink}" )

		if not summaries :
			return "None"

		summaries[0] = summaries[0][0].upper() + summaries[0][1:]
		return " and ".join( summaries )

GafferUI.EditScopeUI.ProcessorWidget.registerProcessorWidget( "AttributeEdits TransformEdits *LightEdits *SurfaceEdits *FilterEdits", __LocationEditsWidget )

class __PruningEditsWidget( _SceneProcessorWidget ) :

	@staticmethod
	def _summary( processor, linkCreator ) :

		paths = IECore.PathMatcher()
		GafferScene.SceneAlgo.matchingPaths( processor["PathFilter"], processor["in"], paths )

		if paths.isEmpty() :
			return "None"
		else :
			link = linkCreator(
				"{} location{}".format( paths.size(), "s" if paths.size() > 1 else "" ),
				paths
			)
			return f"{link} pruned"

GafferUI.EditScopeUI.ProcessorWidget.registerProcessorWidget( "PruningEdits", __PruningEditsWidget )

class __RenderPassesWidget( GafferUI.EditScopeUI.SimpleProcessorWidget ) :

	@staticmethod
	def _summary( processor, linkCreator ) :

		names = processor["names"].getValue()
		return "{} render pass{} created".format(
			len( names ) if names else "No",
			"es" if len( names ) > 1 else "",
		)

GafferUI.EditScopeUI.ProcessorWidget.registerProcessorWidget( "RenderPasses", __RenderPassesWidget )

class __RenderPassOptionEditsWidget( GafferUI.EditScopeUI.SimpleProcessorWidget ) :

	@staticmethod
	def _summary( processor, linkCreator ) :

		enabledOptions = set()
		enabledPasses = set()
		disabledPasses = set()
		for row in processor["edits"].children()[1:] :
			renderPass = row["name"].getValue()
			if not renderPass :
				continue
			if not row["enabled"].getValue() :
				disabledPasses.add( renderPass )
				continue

			passEnabledOptions = {
				cell["value"]["name"].getValue()
				for cell in row["cells"]
				if cell["value"]["enabled"].getValue()
			}

			if passEnabledOptions :
				enabledPasses.add( renderPass )
				enabledOptions = enabledOptions | passEnabledOptions

		summaries = []
		if enabledOptions :
			summaries.append(
				"edits to {} option{} in {} render pass{}".format(
					len( enabledOptions ), "s" if len( enabledOptions ) > 1 else "",
					len( enabledPasses ), "es" if len( enabledPasses ) > 1 else "",
				)
			)

		if disabledPasses :
			summaries.append(
				"disabled edits for {} render pass{}".format(
					len( disabledPasses ), "es" if len( disabledPasses ) > 1 else ""
				)
			)

		if not summaries :
			return "None"

		summaries[0] = summaries[0][0].upper() + summaries[0][1:]
		return " and ".join( summaries )


GafferUI.EditScopeUI.ProcessorWidget.registerProcessorWidget( "RenderPassOptionEdits", __RenderPassOptionEditsWidget )

class __SetMembershipEditsWidget( GafferUI.EditScopeUI.SimpleProcessorWidget ) :

	@staticmethod
	def _summary( processor, linkCreator ) :

		enabledSetCount = 0
		disabledSetCount = 0
		for r in processor["edits"] :
			if r.getName() == "default" :
				continue
			if r["enabled"].getValue() :
				enabledSetCount += 1
			else :
				disabledSetCount += 1

		summaries = []
		if enabledSetCount > 0 :
			summaries.append( "edits to {} set{}".format( enabledSetCount, "s" if enabledSetCount > 1 else "" ) )
		if disabledSetCount > 0 :
			summaries.append( "disabled edits to {} set{}".format( disabledSetCount, "s" if disabledSetCount > 1 else "" ) )

		if not summaries :
			return None
		summaries[0] = summaries[0][0].upper() + summaries[0][1:]
		return " and ".join( summaries )

GafferUI.EditScopeUI.ProcessorWidget.registerProcessorWidget( "SetMembershipEdits", __SetMembershipEditsWidget )
