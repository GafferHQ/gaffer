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

import IECore

import Gaffer
import GafferUI
import GafferScene
import GafferSceneUI

# Pruning/Visibility hotkeys
# ==========================

def addPruningActions( editor ) :

	if isinstance( editor, GafferUI.Viewer ) :
		editor.keyPressSignal().connect( __pruningKeyPress, scoped = False )

def addVisibilityActions( editor ) :

	if isinstance( editor, GafferUI.Viewer ) :
		editor.keyPressSignal().connect( __visibilityKeyPress, scoped = False )

def __pruningKeyPress( viewer, event ) :

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

	if not isinstance( viewer.view(), GafferSceneUI.SceneView ) :
		return False

	editScope = viewer.view().editScope()
	if editScope is None or Gaffer.MetadataAlgo.readOnly( editScope ) :
		# We return True even when we don't do anything, so the keypress doesn't
		# leak out and get used to delete nodes in the node graph.
		## \todo Add a discreet notification system to the Viewer so we can
		# prompt the user to select a scope etc when necessary. Maybe we might
		# also want to ask them if we can prune a common ancestor in the case
		# that all its descendants are selected?
		return True

	viewedNode = viewer.view()["in"].getInput().node()
	if editScope != viewedNode and editScope not in Gaffer.NodeAlgo.upstreamNodes( viewedNode ) :
		# Spare folks from deleting things in a downstream EditScope.
		## \todo When we have a nice Viewer notification system we
		# should emit a warning here.
		return True

	if GafferScene.EditScopeAlgo.prunedReadOnlyReason( editScope ) is not None :
		return True

	# \todo This needs encapsulating in EditScopeAlgo some how so we don't need
	# to interact with processors directly.
	with viewer.getContext() :
		if not editScope["enabled"].getValue() :
			# Spare folks from deleting something when it won't be
			# apparent what they've done until they reenable the
			# EditScope.
			return True
		pruningProcessor = editScope.acquireProcessor( "PruningEdits", createIfNecessary = False )
		if pruningProcessor is not None and not pruningProcessor["enabled"].getValue() :
			return True

	sceneGadget = viewer.view().viewportGadget().getPrimaryChild()
	selection = sceneGadget.getSelection()
	if not selection.isEmpty() :
		with Gaffer.UndoScope( editScope.ancestor( Gaffer.ScriptNode ) ) :
			GafferScene.EditScopeAlgo.setPruned( editScope, selection, True )

	return True

def __visibilityKeyPress( viewer, event ) :

	if not ( event.key == "H" and event.Modifiers.Control ) :
		return False

	if not isinstance( viewer.view(), GafferSceneUI.SceneView ) :
		return False

	editScope = viewer.view().editScope()
	if editScope is None or Gaffer.MetadataAlgo.readOnly( editScope ) :
		return True

	sceneGadget = viewer.view().viewportGadget().getPrimaryChild()
	selection = sceneGadget.getSelection()

	if selection.isEmpty() :
		return True

	inspector = GafferSceneUI.Private.AttributeInspector(
		viewer.view()["in"].getInput(),
		viewer.view()["editScope"],
		"scene:visible"
	)

	with viewer.getContext() as context :
		attributeEdits = editScope.acquireProcessor( "AttributeEdits", createIfNecessary = False )
		if not editScope["enabled"].getValue() or ( attributeEdits is not None and not attributeEdits["enabled"].getValue() ) :
			# Spare folks from hiding something when it won't be
			# apparent what they've done until they reenable the
			# EditScope or processor.
			return True

		with Gaffer.UndoScope( editScope.ancestor( Gaffer.ScriptNode ) ) :
			for path in selection.paths() :
				context["scene:path"] = IECore.InternedStringVectorData( path.split( "/" )[1:] )
				inspection = inspector.inspect()

				if inspection is None or not inspection.editable() :
					continue

				tweakPlug = inspection.acquireEdit()
				tweakPlug["enabled"].setValue( True )
				tweakPlug["value"].setValue( False )

	return True


# Processor Widgets
# =================

class _SceneProcessorWidget( GafferUI.EditScopeUI.SimpleProcessorWidget ) :

	def _linkActivated( self, linkData ) :

		GafferSceneUI.ContextAlgo.setSelectedPaths(
			self.processor().ancestor( Gaffer.ScriptNode ).context(), linkData
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