##########################################################################
#
#  Copyright (c) 2023, Cinesite VFX Ltd. All rights reserved.
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

import collections
import functools
import imath
import os
import traceback

import IECore

import Gaffer
import GafferUI
import GafferImage
import GafferScene
import GafferSceneUI

from GafferUI.PlugValueWidget import sole

from . import _GafferSceneUI

from Qt import QtWidgets
from Qt import QtCore

class RenderPassEditor( GafferSceneUI.SceneEditor ) :

	class Settings( GafferSceneUI.SceneEditor.Settings ) :

		def __init__( self ) :

			GafferSceneUI.SceneEditor.Settings.__init__( self )

			self["tabGroup"] = Gaffer.StringPlug( defaultValue = "Cycles" )
			self["section"] = Gaffer.StringPlug( defaultValue = "Main" )
			self["editScope"] = Gaffer.Plug()
			self["displayGrouped"] = Gaffer.BoolPlug()

			self["favouriteColumns"] = Gaffer.StringVectorDataPlug()

			self["__adaptors"] = GafferSceneUI.RenderPassEditor._createRenderAdaptors()
			self["__adaptors"]["in"].setInput( self["in"] )

			self["__filter"] = _Filter()
			self["__filter"]["in"].setInput( self["__adaptors"]["out"] )
			Gaffer.PlugAlgo.promote( self["__filter"]["filter"] )
			Gaffer.PlugAlgo.promote( self["__filter"]["hideDisabled"] )

			self["__filteredIn"] = GafferScene.ScenePlug()
			self["__filteredIn"].setInput( self["__filter"]["out"] )

	IECore.registerRunTimeTyped( Settings, typeName = "GafferSceneUI::RenderPassEditor::Settings" )

	def __init__( self, scriptNode, **kw ) :

		mainColumn = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, borderWidth = 4, spacing = 4 )

		GafferSceneUI.SceneEditor.__init__( self, mainColumn, scriptNode, **kw )

		with mainColumn :

			GafferUI.PlugLayout(
				self.settings(),
				orientation = GafferUI.ListContainer.Orientation.Horizontal,
				rootSection = "Settings"
			)

			with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :

				GafferUI.PlugLayout(
					self.settings(),
					orientation = GafferUI.ListContainer.Orientation.Horizontal,
					rootSection = "Filter"
				)

			self.__renderPassNameColumn = _GafferSceneUI._RenderPassEditor.RenderPassNameColumn()
			self.__renderPassActiveColumn = _GafferSceneUI._RenderPassEditor.RenderPassActiveColumn()
			self.__pathListing = GafferUI.PathListingWidget(
				_GafferSceneUI._RenderPassEditor.RenderPassPath(
					self.settings()["__filteredIn"], self.context(), "/", grouped = self.settings()["displayGrouped"].getValue()
				),
				columns = [
					self.__renderPassNameColumn,
					self.__renderPassActiveColumn,
				],
				selectionMode = GafferUI.PathListingWidget.SelectionMode.Cells,
				displayMode = GafferUI.PathListingWidget.DisplayMode.Tree,
				horizontalScrollMode = GafferUI.ScrollMode.Automatic
			)

			## \todo Provide public API for this in PathListingWidget, we currently use a different approach
			# for header-only context menus in CatalogueUI.
			self.__pathListing._qtWidget().header().setContextMenuPolicy( QtCore.Qt.CustomContextMenu )
			self.__pathListing._qtWidget().header().customContextMenuRequested.connect( Gaffer.WeakMethod( self.__headerContextMenuRequested ) )

			with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :

				self.__addButton = GafferUI.Button(
					image = "plus.png",
					hasFrame = False
				)

				self.__removeButton = GafferUI.Button(
					image = "minus.png",
					hasFrame = False
				)

				GafferUI.Spacer( imath.V2i( 1 ), imath.V2i( 999999, 1 ), parenting = { "expand" : True } )

			self.__addButton.clickedSignal().connect( Gaffer.WeakMethod( self.__addButtonClicked ) )
			self.__removeButton.clickedSignal().connect( Gaffer.WeakMethod( self.__removeButtonClicked ) )
			Gaffer.Metadata.nodeValueChangedSignal().connect( Gaffer.WeakMethod( self.__metadataChanged ) )

			self.__pathListing.buttonDoubleClickSignal().connectFront( Gaffer.WeakMethod( self.__buttonDoubleClick ) )
			self.__pathListing.keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPress ) )
			self.__pathListing.columnContextMenuSignal().connect( Gaffer.WeakMethod( self.__columnContextMenuSignal ) )
			self.__pathListing.selectionChangedSignal().connect( Gaffer.WeakMethod( self.__selectionChanged ) )
			GafferSceneUI.Private.InspectorColumn.connectToDragBeginSignal( self.__pathListing )

		self.__columnCache = {}

		self._updateFromSet()
		self.__updateColumns()
		self.__updateButtonStatus()

	__columnRegistry = collections.OrderedDict()

	@classmethod
	def registerOption( cls, groupKey, optionName, section = "Main", columnName = None, index = None ) :

		GafferSceneUI.RenderPassEditor.registerColumn(
			groupKey,
			optionName,
			cls.__optionColumnCreator( optionName, columnName ),
			section,
			index
		)

	@classmethod
	def __optionColumnCreator( cls, optionName, columnName = None ) :

		optionLabel = Gaffer.Metadata.value( "option:" + optionName, "label" )
		if not columnName :
			columnName = optionLabel or optionName.split( ":" )[-1]

		toolTip = "<h3>{}</h3> Option : <code>{}</code>".format( optionLabel or columnName, optionName )
		optionDescription = Gaffer.Metadata.value( "option:" + optionName, "description" )
		if optionDescription :
			## \todo PathListingWidget's PathModel should be handling this instead.
			toolTip += GafferUI.DocumentationAlgo.markdownToHTML( optionDescription )

		return lambda scene, editScope : GafferSceneUI.Private.InspectorColumn(
			GafferSceneUI.Private.OptionInspector( scene, editScope, optionName ),
			columnName,
			toolTip
		)

	# Registers a column in the Render Pass Editor.
	# `inspectorFunction` is a callable object of the form
	# `inspectorFunction( scene, editScope )` returning a
	# `GafferSceneUI.Private.InspectorColumn` object.
	@classmethod
	def registerColumn( cls, groupKey, columnKey, inspectorFunction, section = "Main", index = None ) :

		sections = cls.__columnRegistry.setdefault( groupKey, collections.OrderedDict() )
		section = sections.setdefault( section, collections.OrderedDict() )

		section[columnKey] = ( inspectorFunction, index )

	@classmethod
	def deregisterColumn( cls, groupKey, columnKey, section = "Main" ) :

		sections = cls.__columnRegistry.get( groupKey )
		if sections is not None and section in sections.keys() and columnKey in sections[section].keys() :
			del sections[section][columnKey]

	__addRenderPassButtonMenuSignal = None
	## This signal is emitted whenever the add render pass button is clicked.
	# If the resulting menu definition has been populated with items,
	# a popup menu will be presented from the button.
	# If only a single item is present, its command will be called
	# immediately instead of presenting a menu.
	# If no items are present, then the default behaviour is to
	# add a single new render pass with a user specified name.

	@classmethod
	def addRenderPassButtonMenuSignal( cls ) :

		if cls.__addRenderPassButtonMenuSignal is None :
			cls.__addRenderPassButtonMenuSignal = _AddButtonMenuSignal()

		return cls.__addRenderPassButtonMenuSignal

	## Registration of the function used to group render passes when
	# `RenderPassEditor.Settings.displayGrouped` is enabled.
	# 'f' should be a callable that takes a render pass name and returns
	# a string or list of strings containing the path names that the
	# render pass should be grouped under.
	# For example: If "char_gafferBot_beauty" should be displayed grouped
	# under `/char/gafferBot`, then `f( "char_gafferBot_beauty" )` should
	# return `"/char/gafferBot" or `[ "char", "gafferBot" ]`.
	@staticmethod
	def registerPathGroupingFunction( f ) :

		_GafferSceneUI._RenderPassEditor.RenderPassPath.registerPathGroupingFunction( f )

	@staticmethod
	def pathGroupingFunction() :

		return _GafferSceneUI._RenderPassEditor.RenderPassPath.pathGroupingFunction()

	@staticmethod
	def _createRenderAdaptors() :

		adaptors = GafferScene.SceneProcessor()

		adaptors["__renderAdaptors"] = GafferScene.SceneAlgo.createRenderAdaptors()
		## \todo We currently masquerade as the RenderPassWedge in order to include
		# adaptors that disable render passes. We may want to find a more general
		# client name for this usage...
		adaptors["__renderAdaptors"]["client"].setValue( "RenderPassWedge" )
		adaptors["__renderAdaptors"]["in"].setInput( adaptors["in"] )

		adaptors["__adaptorSwitch"] = Gaffer.Switch()
		adaptors["__adaptorSwitch"].setup( GafferScene.ScenePlug() )
		adaptors["__adaptorSwitch"]["in"]["in0"].setInput( adaptors["in"] )
		adaptors["__adaptorSwitch"]["in"]["in1"].setInput( adaptors["__renderAdaptors"]["out"] )

		adaptors["__contextQuery"] = Gaffer.ContextQuery()
		adaptors["__contextQuery"].addQuery( Gaffer.BoolPlug( "enableAdaptors", defaultValue = False ) )
		adaptors["__contextQuery"]["queries"][0]["name"].setValue( "renderPassEditor:enableAdaptors" )

		adaptors["__adaptorSwitch"]["index"].setInput( adaptors["__contextQuery"]["out"][0]["value"] )
		adaptors["__adaptorSwitch"]["deleteContextVariables"].setValue( "renderPassEditor:enableAdaptors" )

		adaptors["out"].setInput( adaptors["__adaptorSwitch"]["out"] )

		return adaptors

	def __repr__( self ) :

		return "GafferSceneUI.RenderPassEditor( scriptNode )"

	def _updateFromContext( self, modifiedItems ) :

		self.__lazyUpdateFromContext()

	def _updateFromSettings( self, plug ) :

		if plug in ( self.settings()["section"], self.settings()["tabGroup"] ) :
			self.__updateColumns()
		elif plug == self.settings()["favouriteColumns"] and self.__currentSectionEditable() :
			self.__updateColumns()
		elif plug == self.settings()["displayGrouped"] :
			self.__displayGroupedChanged()
		elif plug in ( self.settings()["in"], self.settings()["editScope"] ) :
			self.__updateButtonStatus()

	@GafferUI.LazyMethod( deferUntilVisible = False, deferUntilPlaybackStops = True )
	def __lazyUpdateFromContext( self ) :

		self.__pathListing.getPath().setContext( self.context() )

	@GafferUI.LazyMethod()
	def __updateColumns( self ) :

		tabGroup = self.settings()["tabGroup"].getValue()
		currentSection = self.settings()["section"].getValue()

		sectionColumns = []

		if currentSection == "Favourites" :
			for ( index, favouriteName ) in enumerate( self.settings()["favouriteColumns"].getValue() ) :
				if favouriteName.startswith( "option:" ) :
					sectionColumns.append( ( self.__acquireColumn( favouriteName, currentSection ), index ) )
				else :
					IECore.msg( IECore.Msg.Level.Warning, "RenderPassEditor", "Unknown favourite \"{}\". Option favourites should start with \"option:\".".format( favouriteName ) )

			if len( sectionColumns ) == 0 :
				# Include a blank spacer column when there are no favourites.
				sectionColumns.append( ( GafferUI.StandardPathColumn( "", "", GafferUI.PathColumn.SizeMode.Stretch ), 0 ) )

		else :
			for groupKey, sections in self.__columnRegistry.items() :
				if IECore.StringAlgo.match( tabGroup, groupKey ) :
					section = sections.get( currentSection or None, {} )
					sectionColumns += [ ( self.__acquireColumn( c, currentSection ), index ) for ( c, index ) in section.values() ]

		self.__pathListing.setColumns( [ self.__renderPassNameColumn, self.__renderPassActiveColumn ] + self.__orderedColumns( sectionColumns ) )

	def __acquireColumn( self, columnCreator, section ) :

		column = self.__columnCache.get( ( columnCreator, section ) )
		if column is None :
			columnKey = columnCreator
			if isinstance( columnCreator, str ) and columnCreator.startswith( "option:" ) :
				columnCreator = self.__optionColumnCreator( columnCreator[7:], section )

			column = columnCreator( self.settings()["in"], self.settings()["editScope"] )
			self.__columnCache[ ( columnKey, section ) ] = column

		return column

	@staticmethod
	def __orderedColumns( columnsAndIndices ) :

		for i, ( column, index ) in enumerate( columnsAndIndices ) :
			if index is not None :
				# Negative indices are remapped to their absolute position in the column list.
				columnsAndIndices[i] = ( column, index if index >= 0 else len( columnsAndIndices ) + index )

		# As column indices may be sparse, we fill in the gaps with any unspecified indices before sorting.
		availableIndices = iter( sorted( set( range( len( columnsAndIndices ) ) ) - { x[1] for x in columnsAndIndices } ) )
		orderedColumns = sorted(
			[ ( column, index if index is not None else next( availableIndices ) ) for column, index in columnsAndIndices ],
			key = lambda x: x[1]
		)

		return [ x[0] for x in orderedColumns ]

	def __favouriteColumn( self, column, favourite ) :

		if not isinstance( column, GafferSceneUI.Private.InspectorColumn ) :
			return

		inspector = column.inspector( self.__pathListing.getPath() )
		if isinstance( inspector, GafferSceneUI.Private.OptionInspector ) :
			self.__favourite( "option:" + inspector.name(), favourite )

	def __favourite( self, optionName, favourite = True, index = None ) :

		favourites = list( self.settings()["favouriteColumns"].getValue() )
		if favourite :
			if optionName not in favourites :
				if index is not None :
					favourites.insert( index, optionName )
				else :
					favourites.append( optionName )
		else :
			favourites.remove( optionName )

		self.settings()["favouriteColumns"].setValue( IECore.StringVectorData( favourites ) )

	def __resetFavourites( self, userDefault = False ) :

		if userDefault :
			Gaffer.NodeAlgo.applyUserDefault( self.settings()["favouriteColumns"] )
		else :
			self.settings()["favouriteColumns"].setToDefault()

	def __currentSectionEditable( self ) :

		return self.settings()["section"].getValue() == "Favourites"

	def __headerContextMenuRequested( self, pos ) :

		column = self.__pathListing.columnAt( imath.V2f( pos.x(), pos.y() ) )
		m = IECore.MenuDefinition()
		userEditableSection = self.__currentSectionEditable()
		if isinstance( column, GafferSceneUI.Private.InspectorColumn ) :

			if userEditableSection :
				m.append(
					"/Remove",
					{
						"command" : functools.partial( Gaffer.WeakMethod( self.__favouriteColumn ), column, False ),
					}
				)
			else :
				m.append(
					"/Favourite",
					{
						"command" : functools.partial( Gaffer.WeakMethod( self.__favouriteColumn ), column ),
						"checkBox" : "option:{}".format( column.inspector( self.__pathListing.getPath() ).name() ) in self.settings()["favouriteColumns"].getValue(),
					}
				)

		if userEditableSection and column not in self.__commonColumns :

			m.append( "/__resetFavouritesDivider", { "divider" : True } )

			if Gaffer.NodeAlgo.hasUserDefault( self.settings()["favouriteColumns"] ) :
				m.append(
					"/Reset to Default",
					{
						"command" : functools.partial( Gaffer.WeakMethod( self.__resetFavourites ), True ),
					}
				)

			m.append(
				"/Remove All",
				{
					"command" : Gaffer.WeakMethod( self.__resetFavourites ),
				}
			)

		if m.size() :
			self.__contextMenu = GafferUI.Menu( m )
			self.__contextMenu.popup( parent = self )

	def __displayGroupedChanged( self ) :

		selection = self.__pathListing.getSelection()
		renderPassPath = self.__pathListing.getPath().copy()
		grouped = self.settings()["displayGrouped"].getValue()

		# Remap selection so it is maintained when switching to/from grouped display
		for i, pathMatcher in enumerate( selection ) :
			remappedPaths = IECore.PathMatcher()
			for path in pathMatcher.paths() :
				renderPassPath.setFromString( path )
				renderPassName = renderPassPath.property( "renderPassPath:name" )
				if renderPassName is None :
					continue

				if grouped :
					newPath = GafferScene.ScenePlug.stringToPath( self.pathGroupingFunction()( renderPassName ) )
					newPath.append( renderPassName )
				else :
					newPath = renderPassName

				remappedPaths.addPath( newPath )

			selection[i] = remappedPaths

		self.__pathListing.getPath().setGrouped( grouped )
		self.__pathListing.setSelection( selection )

	def __buttonDoubleClick( self, pathListing, event ) :

		# A small corner area below the vertical scroll bar may pass through
		# to us, causing odd selection behavior. Check that we're within the
		# scroll area.
		if pathListing.pathAt( event.line.p0 ) is None :
			return False

		if event.button == event.Buttons.Left :
			column = pathListing.columnAt( event.line.p0 )
			if column == self.__renderPassNameColumn :
				if self.__canEditRenderPasses() and len( self.__selectedRenderPasses() ) == 1 :
					self.__renameSelectedRenderPass()
					return True

			if column == self.__renderPassActiveColumn :
				self.__setActiveRenderPass( pathListing )
				return True

		return False

	def __keyPress( self, pathListing, event ) :

		if event.modifiers == event.Modifiers.None_ :

			if event.key == "Return" or event.key == "Enter" :
				selectedRenderPasses = self.__selectedRenderPasses()
				if self.__canEditRenderPasses() and len( selectedRenderPasses ) == 1 :
					self.__renameSelectedRenderPass()
					return True

				selection = pathListing.getSelection()
				if len( selection[1].paths() ) :
					self.__setActiveRenderPass( pathListing )
					return True

	def __selectedRenderPasses( self, columns = [ 0 ] ) :

		# There may be multiple columns with a selection, but we only operate on the specified column indices.
		selection = self.__pathListing.getSelection()
		# Any selection outside of our desired column(s) is ambiguous, so we return no names in that situation
		for i, pathMatcher in enumerate( selection ) :
			if i not in columns and not pathMatcher.isEmpty() :
				return []

		renderPassPath = self.__pathListing.getPath().copy()
		result = set()
		for c in columns :
			for path in selection[c].paths() :
				renderPassPath.setFromString( path )
				name = renderPassPath.property( "renderPassPath:name" )
				if name is not None :
					result.add( name )

		return list( result )

	def __setActiveRenderPass( self, pathListing ) :

		selectedPassNames = self.__selectedRenderPasses( columns = [ 1 ] )

		if len( selectedPassNames ) != 1 :
			return

		script = self.scriptNode()
		if Gaffer.MetadataAlgo.readOnly( script ) :
			GafferUI.PopupWindow.showWarning( "The script is read-only.", parent = self )
			return

		with Gaffer.UndoScope( script ) :
			GafferSceneUI.ScriptNodeAlgo.setCurrentRenderPass(
				script,
				selectedPassNames[0] if selectedPassNames[0] != GafferSceneUI.ScriptNodeAlgo.getCurrentRenderPass( script ) else ""
			)

	def __columnContextMenuSignal( self, column, pathListing, menuDefinition ) :

		columns = pathListing.getColumns()
		columnIndex = -1
		for i in range( 0, len( columns ) ) :
			if column == columns[i] :
				columnIndex = i

		if columnIndex == 0 :
			# Render pass operations

			if menuDefinition.size() :
				menuDefinition.append( "/__renderPassEditorRenameDivider", { "divider" : True } )

			menuDefinition.append(
				"Rename Selected Render Pass...",
				{
					"command" : Gaffer.WeakMethod( self.__renameSelectedRenderPass ),
					"active" : self.__canEditRenderPasses() and len( self.__selectedRenderPasses() ) == 1
				}
			)

			menuDefinition.append( "__DeleteDivider__", { "divider" : True } )

			menuDefinition.append(
				"Delete Selected Render Passes",
				{
					"command" : Gaffer.WeakMethod( self.__deleteSelectedRenderPasses ),
					"active" : self.__canEditRenderPasses()
				}
			)

	def __canEditRenderPasses( self, editScope = None ) :

		input = self.settings()["in"].getInput()
		if input is None :
			# No input scene
			return False

		inputNode = input.node()

		if editScope is None :
			# No edit scope provided so use the current selected
			editScope = self.editScope()
			if editScope is None :
				# No edit scope selected
				return False

		if inputNode != editScope and editScope not in Gaffer.NodeAlgo.upstreamNodes( inputNode ) :
			# Edit scope is downstream of input
			return False
		elif GafferScene.EditScopeAlgo.renderPassesReadOnlyReason( editScope ) is not None :
			# RenderPasses node or the edit scope is read only
			return False
		else :
			with self.context() :
				if not editScope["enabled"].getValue() :
					# Edit scope is disabled
					return False

		renderPassesProcessor = editScope.acquireProcessor( "RenderPasses", createIfNecessary = False )
		if renderPassesProcessor is not None and ( not renderPassesProcessor["enabled"].getValue() or not renderPassesProcessor["names"].settable() ) :
			# RenderPasses node is disabled
			return False

		return True

	def __addRenderPass( self, renderPass, editScope ) :

		assert( self.__canEditRenderPasses( editScope ) )

		renderPassesProcessor = editScope.acquireProcessor( "RenderPasses", createIfNecessary = True )

		renderPasses = renderPassesProcessor["names"].getValue()
		renderPasses.append( renderPass )

		with Gaffer.UndoScope( editScope.ancestor( Gaffer.ScriptNode ) ) :
			renderPassesProcessor["names"].setValue( renderPasses )

	def __warningPopup( self, title, message ) :

		with GafferUI.PopupWindow() as self.__popup :
			with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing = 4 ) :
				with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :
					GafferUI.Image( "warningSmall.png" )
					GafferUI.Label( "<h4>{}</h4>".format( title ) )
				GafferUI.Label( message )

		self.__popup.popup( parent = self )

	def __renameSelectedRenderPass( self ) :

		selectedRenderPasses = self.__selectedRenderPasses()
		if len( selectedRenderPasses ) != 1 :
			return

		editScope = self.editScope()
		if editScope is None :
			return

		renderPassesProcessor = editScope.acquireProcessor( "RenderPasses", createIfNecessary = False )
		if renderPassesProcessor is None or selectedRenderPasses[0] not in renderPassesProcessor["names"].getValue() :
			self.__warningPopup( "Unable to rename", "Pass was not created in {}.".format( editScope.relativeName( self.scriptNode() ) ) )
			return

		dialogue = _RenderPassCreationDialogue(
			existingNames = [ x for x in self.__renderPassNames( self.settings()["in"] ) if x != selectedRenderPasses[0] ],
			editScope = editScope,
			title = "Rename Render Pass",
			confirmLabel = "Rename",
			actionDescription = "Rename render pass in",
			defaultName = selectedRenderPasses[0],
			message = "<h4>Renaming will only affect the current edit scope.</h4>\nReferences elsewhere in the node graph may need to be updated manually."
		)

		renderPassName = dialogue.waitForRenderPassName( parentWindow = self.ancestor( GafferUI.Window ) )
		if renderPassName is not None and renderPassName != selectedRenderPasses[0] :

			nonEditableReason = GafferScene.EditScopeAlgo.renameRenderPassNonEditableReason( editScope, renderPassName )
			if nonEditableReason is not None :
				self.__warningPopup( "Unable to rename", nonEditableReason )
				return

			with Gaffer.UndoScope( editScope.ancestor( Gaffer.ScriptNode ) ) :
				GafferScene.EditScopeAlgo.renameRenderPass( editScope, selectedRenderPasses[0], renderPassName )

			if self.settings()["displayGrouped"].getValue() :
				renamedPath = GafferScene.ScenePlug.stringToPath( self.pathGroupingFunction()( renderPassName ) )
				renamedPath.append( renderPassName )
			else :
				renamedPath = renderPassName

			self.__pathListing.setSelection(
				[ IECore.PathMatcher( [ renamedPath ] ) if i == 0 else IECore.PathMatcher() for i in range( len( self.__pathListing.getSelection() ) ) ]
			)

	def __disableRenderPasses( self, renderPasses, editScope ) :

		with Gaffer.UndoScope( editScope.ancestor( Gaffer.ScriptNode ) ) :
			for renderPass in renderPasses :
				edit = GafferScene.EditScopeAlgo.acquireRenderPassOptionEdit(
					editScope, renderPass, "renderPass:enabled", createIfNecessary = True
				)
				edit["enabled"].setValue( True )
				edit["value"].setValue( False )

	def __deleteSelectedRenderPasses( self ) :

		selectedRenderPasses = self.__selectedRenderPasses()
		if len( selectedRenderPasses ) == 0 :
			return

		editScope = self.editScope()
		if editScope is None :
			return

		localRenderPasses = []
		renderPassesProcessor = editScope.acquireProcessor( "RenderPasses", createIfNecessary = False )
		if renderPassesProcessor is not None :
			localRenderPasses = renderPassesProcessor["names"].getValue()

		## \todo: This tracing would be better performed by an Inspector showing the existence history of a render pass
		# allowing us to pinpoint the node each render pass originated from and deal with any Context changes along the way.
		upstreamRenderPasses = self.__renderPassNames( renderPassesProcessor["in"] if renderPassesProcessor else editScope["in"] )
		localSelection = []
		upstreamSelection = []
		downstreamSelection = []

		for x in selectedRenderPasses :
			if x in localRenderPasses :
				localSelection.append( x )
			elif x in upstreamRenderPasses :
				upstreamSelection.append( x )
			else :
				downstreamSelection.append( x )

		with Gaffer.UndoScope( editScope.ancestor( Gaffer.ScriptNode ) ) :
			upstreamCount = len( upstreamSelection )
			if upstreamCount > 0 :

				dialogue = GafferUI.ConfirmationDialogue(
					"Unable to Delete Upstream Render Passes",
					"{count} render pass{suffix} created upstream of <b>{editScopeName}</b>.<br><br>We recommend deleting {target} in the upstream Edit Scope, or disabling {target} in <b>{editScopeName}</b>.".format(
						count = upstreamCount,
						suffix = "es were" if upstreamCount != 1 else " was",
						editScopeName = editScope.relativeName( self.scriptNode() ),
						target = "them" if upstreamCount != 1 else "it"
					),
					details = "\n".join( sorted( upstreamSelection ) ),
					confirmLabel = "Disable Render Pass{}".format( "es" if upstreamCount != 1 else "" ),
				)
				if dialogue.waitForConfirmation( parentWindow = self.ancestor( GafferUI.Window ) ) :
					self.__disableRenderPasses( upstreamSelection, editScope )
				else :
					return

			if len( localRenderPasses ) > 0 and len( localSelection ) > 0 :
				renderPassesProcessor["names"].setValue( IECore.StringVectorData( [ x for x in localRenderPasses if x not in localSelection ] ) )

		downstreamCount = len( downstreamSelection )
		if downstreamCount > 0 :

			dialogue = GafferUI.ConfirmationDialogue(
				"Unable to Delete Downstream Render Passes",
				"{count} render pass{suffix} created downstream of <b>{editScopeName}</b>.<br><br>We recommend deleting {target} in the downstream Edit Scope.".format(
					count = downstreamCount,
					suffix = "es were" if downstreamCount != 1 else " was",
					editScopeName = editScope.relativeName( self.scriptNode() ),
					target = "them" if downstreamCount != 1 else "it"
				),
				details = "\n".join( sorted( downstreamSelection ) ),
				confirmLabel = "Close",
				cancelLabel = None
			)
			dialogue.waitForConfirmation( parentWindow = self.ancestor( GafferUI.Window ) )

	def __renderPassNames( self, plug ) :

		with self.context() :
			return plug["globals"].getValue().get( "option:renderPass:names", IECore.StringVectorData() )

	def __renderPassCreationDialogue( self ) :

		editScope = self.editScope()
		assert( editScope is not None )

		dialogue = _RenderPassCreationDialogue( self.__renderPassNames( self.settings()["in"] ), editScope )
		renderPassName = dialogue.waitForRenderPassName( parentWindow = self.ancestor( GafferUI.Window ) )
		if renderPassName :
			self.__addRenderPass( renderPassName, editScope )

	def __addButtonClicked( self, button ) :

		menuDefinition = IECore.MenuDefinition()
		self.addRenderPassButtonMenuSignal()( menuDefinition, self )

		if menuDefinition.size() == 0 :
			self.__renderPassCreationDialogue()
		elif menuDefinition.size() == 1 :
			_, item = menuDefinition.items()[0]
			item.command()
		else :
			menuDefinition.prepend(
				"Add...",
				{
					"command" : Gaffer.WeakMethod( self.__renderPassCreationDialogue )
				}
			)
			self.__popupMenu = GafferUI.Menu( menuDefinition )
			self.__popupMenu.popup( parent = self )

	def __removeButtonClicked( self, button ) :

		self.__deleteSelectedRenderPasses()
		self.__updateButtonStatus()

	def __metadataChanged( self, nodeTypeId, key, node ) :

		editScope = self.editScope()
		if editScope is None :
			return

		renderPassesProcessor = editScope.acquireProcessor( "RenderPasses", createIfNecessary = False )

		if (
			Gaffer.MetadataAlgo.readOnlyAffectedByChange( editScope, nodeTypeId, key, node ) or
			( renderPassesProcessor and Gaffer.MetadataAlgo.readOnlyAffectedByChange( renderPassesProcessor, nodeTypeId, key, node ) )
		) :
			self.__updateButtonStatus()

	def __selectionChanged( self, pathListing ) :

		self.__updateButtonStatus()

	def __updateButtonStatus( self, *unused ) :

		editable = self.__canEditRenderPasses()
		selection = len( self.__selectedRenderPasses() ) > 0

		self.__removeButton.setEnabled( editable and selection )
		if not editable :
			removeToolTip = "To delete render passes, first choose an editable Edit Scope."
		elif not selection :
			removeToolTip = "To delete render passes, select them from the Name column."
		else :
			removeToolTip = "Click to delete selected render passes."
		self.__removeButton.setToolTip( removeToolTip )

		self.__addButton.setEnabled( editable )
		self.__addButton.setToolTip( "Click to add render pass." if editable else "To add a render pass, first choose an editable Edit Scope." )

GafferUI.Editor.registerType( "RenderPassEditor", RenderPassEditor )

##########################################################################
# Metadata controlling the settings UI
##########################################################################

Gaffer.Metadata.registerNode(

	RenderPassEditor.Settings,

	## \todo Doing spacers with custom widgets is tedious, and we're doing it
	# in all the View UIs. Maybe we could just attach metadata to the plugs we
	# want to add space around, in the same way we use `divider` to add a divider?
	"layout:customWidget:spacer:widgetType", "GafferSceneUI.RenderPassEditor._Spacer",
	"layout:customWidget:spacer:section", "Settings",
	"layout:customWidget:spacer:index", 3,

	plugs = {

		"*" : {

			"label" : "",

		},

		"tabGroup" : {

			"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",
			"layout:width" : 100,

		},

		"section" : {

			"plugValueWidget:type" : "GafferSceneUI.RenderPassEditor._SectionPlugValueWidget",

		},

		"editScope" : {

			"plugValueWidget:type" : "GafferUI.EditScopeUI.EditScopePlugValueWidget",
			"layout:width" : 130,

		},

		"displayGrouped" : {

			"description" :
			"""
			Click to toggle between list and grouped display of render passes.
			""",

			"layout:section" : "Filter",
			"layout:divider" : True,
			"plugValueWidget:type" : "GafferUI.TogglePlugValueWidget",
			"togglePlugValueWidget:image:on" : "pathListingTree.png",
			"togglePlugValueWidget:image:off" : "pathListingList.png",

		},

		"filter" : {

			"description" :
			"""
			Filters the displayed render passes. Accepts standard wildcards such as `*` and `?`.
			""",

			"plugValueWidget:type" : "GafferUI.TogglePlugValueWidget",
			"togglePlugValueWidget:imagePrefix" : "search",
			"togglePlugValueWidget:defaultToggleValue" : "*",
			"stringPlugValueWidget:placeholderText" : "Filter...",
			"layout:section" : "Filter",

		},

		"hideDisabled" : {

			"description" :
			"""
			Hides render passes that are disabled for rendering.
			""",

			"boolPlugValueWidget:labelVisible" : True,
			"layout:section" : "Filter",

		},

		"favouriteColumns" : [

			"plugValueWidget:type", "",

		]

	}

)

##########################################################################
# _Filter node
##########################################################################

class _Filter( GafferScene.SceneProcessor ) :

	def __init__( self, name = "_Filter" ) :

		GafferScene.SceneProcessor.__init__( self, name )

		self["filter"] = Gaffer.StringPlug()
		self["hideDisabled"] = Gaffer.BoolPlug()

		self["__keepFilteredPasses"] = GafferScene.DeleteRenderPasses()
		self["__keepFilteredPasses"]["in"].setInput( self["in"] )
		self["__keepFilteredPasses"]["enabled"].setInput( self["filter"] )
		self["__keepFilteredPasses"]["mode"].setValue( GafferScene.DeleteRenderPasses.Mode.Keep )

		self["__filterExpression"] = Gaffer.Expression()
		self["__filterExpression"].setExpression(
			"pattern = parent['filter'];"
			"pattern = f'*{pattern}*' if not IECore.StringAlgo.hasWildcards( pattern ) else pattern;"
			"parent['__keepFilteredPasses']['names'] = pattern;"
		)

		self["__adaptorEnabler"] = Gaffer.ContextVariables()
		self["__adaptorEnabler"].setup( self["__keepFilteredPasses"]["out"] )
		self["__adaptorEnabler"]["in"].setInput( self["__keepFilteredPasses"]["out"] )
		self["__adaptorEnabler"]["variables"].addChild( Gaffer.NameValuePlug( "renderPassEditor:enableAdaptors", True ) )

		self["__optionQuery"] = GafferScene.OptionQuery()
		self["__optionQuery"]["scene"].setInput( self["__adaptorEnabler"]["out"] )
		self["__optionQuery"].addQuery( Gaffer.StringVectorDataPlug( defaultValue = IECore.StringVectorData() ) )
		self["__optionQuery"].addQuery( Gaffer.BoolPlug( defaultValue = True ) )
		self["__optionQuery"]["queries"][0]["name"].setValue( "renderPass:names" )
		self["__optionQuery"]["queries"][1]["name"].setValue( "renderPass:enabled" )

		self["__collectEnabledPasses"] = Gaffer.Collect()
		self["__collectEnabledPasses"]["contextVariable"].setValue( "renderPass" )
		self["__collectEnabledPasses"]["contextValues"].setInput( self["__optionQuery"]["out"][0]["value"] )
		self["__collectEnabledPasses"]["enabled"].setInput( self["__optionQuery"]["out"][1]["value"] )
		self["__collectEnabledPasses"].addInput( Gaffer.StringPlug( "names", defaultValue = "${renderPass}" ) )

		self["__keepEnabledPasses"] = GafferScene.DeleteRenderPasses()
		self["__keepEnabledPasses"]["in"].setInput( self["__keepFilteredPasses"]["out"] )
		self["__keepEnabledPasses"]["names"].setInput( self["__collectEnabledPasses"]["out"]["names"] )
		self["__keepEnabledPasses"]["enabled"].setInput( self["hideDisabled"] )
		self["__keepEnabledPasses"]["mode"].setValue( GafferScene.DeleteRenderPasses.Mode.Keep )

		self["out"].setInput( self["__keepEnabledPasses"]["out"] )

IECore.registerRunTimeTyped( _Filter, typeName = "GafferSceneUI::RenderPassEditor::_Filter" )

##########################################################################
# Widgets
##########################################################################

class _SectionPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		GafferUI.PlugValueWidget.__init__( self, QtWidgets.QTabBar(), plug, **kw )

		self._qtWidget().setDrawBase( False )

		self._qtWidget().currentChanged.connect( Gaffer.WeakMethod( self.__currentChanged ) )
		self.__ignoreCurrentChanged = False

		plug.node().plugSetSignal().connect( Gaffer.WeakMethod( self.__plugSet ) )

		# Borrow the styling from the Spreadsheet's section chooser.
		## \todo Should we be introducing a `GafferUI.TabBar` class which can be used in
		# both?
		self._qtWidget().setProperty( "gafferClass", "GafferUI.SpreadsheetUI._SectionChooser" )

		self.__updateTabs()

	def _updateFromValues( self, values, exception ) :

		for i in range( 0, self._qtWidget().count() ) :
			if self._qtWidget().tabText( i ) == values[0] :
				try :
					self.__ignoreCurrentChanged = True
					self._qtWidget().setCurrentIndex( i )
				finally :
					self.__ignoreCurrentChanged = False
				break

	def __currentChanged( self, index ) :

		if self.__ignoreCurrentChanged :
			return

		index = self._qtWidget().currentIndex()
		text = self._qtWidget().tabText( index )
		with self._blockedUpdateFromValues() :
			self.getPlug().setValue( text )

	def __updateTabs( self ) :

		try :
			self.__ignoreCurrentChanged = True
			while self._qtWidget().count() :
				self._qtWidget().removeTab( 0 )

			tabGroup = self.getPlug().node()["tabGroup"].getValue()

			tabNames = []
			for groupKey, sections in RenderPassEditor._RenderPassEditor__columnRegistry.items() :
				if IECore.StringAlgo.match( tabGroup, groupKey ) :
					tabNames.extend( sections.keys() )
			# Deduplicate sections while preserving order in case the same
			# section has been registered to multiple matching groupKeys.
			for name in list( dict.fromkeys( tabNames ) ) :
				self._qtWidget().addTab( name )

			self._qtWidget().addTab( "Favourites" )
		finally :
			self.__ignoreCurrentChanged = False

	def __plugSet( self, plug ) :

		if plug == self.getPlug().node()["tabGroup"] :
			self.__updateTabs()
			# Preserve the current section if there is an equivalently
			# named section registered for the new renderer
			self._updateFromValues( [ self.getPlug().getValue() ], None )
			self.__currentChanged( self._qtWidget().currentIndex() )

RenderPassEditor._SectionPlugValueWidget = _SectionPlugValueWidget

class _Spacer( GafferUI.Spacer ) :

	def __init__( self, settingsNode, **kw ) :

		GafferUI.Spacer.__init__( self, imath.V2i( 0 ) )

RenderPassEditor._Spacer = _Spacer

class _RenderPassCreationDialogue( GafferUI.Dialogue ) :

	def __init__( self, existingNames = [], editScope = None, title = "Add Render Pass", cancelLabel = "Cancel", confirmLabel = "Add", actionDescription = "Add render pass to", defaultName = "", message = "", **kw ) :

		GafferUI.Dialogue.__init__( self, title, sizeMode=GafferUI.Window.SizeMode.Fixed, **kw )

		self.__existingNames = set( existingNames or [] )

		self.__column = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing = 8 )
		with self.__column :
			if editScope :
				with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :
					GafferUI.Label( actionDescription )
					editScopeColor = Gaffer.Metadata.value( editScope, "nodeGadget:color" )
					if editScopeColor :
						GafferUI.Image.createSwatch( editScopeColor )
					GafferUI.Label( "<h4>{}</h4>".format( editScope.relativeName( editScope.ancestor( Gaffer.ScriptNode ) ) ) )

			if message != "" :
				lines = message.split( "\n" )
				with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing = 4 ) :
					with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :
						GafferUI.Image( "infoSmall.png" )
						GafferUI.Label( "{}".format( lines[0] ) )
					for line in lines[1:] :
						GafferUI.Label( "{}".format( line ) )

			self.__renderPassNameWidget = GafferSceneUI.RenderPassesUI.createRenderPassNameWidget()
			if defaultName != "" :
				self.__renderPassNameWidget.setRenderPassName( defaultName )

		self._setWidget( self.__column )

		self._addButton( cancelLabel )
		self.__confirmButton = self._addButton( confirmLabel )

		if hasattr( self.__renderPassNameWidget, "activatedSignal" ) :
			self.__renderPassNameWidget.activatedSignal().connect( Gaffer.WeakMethod( self.__renderPassNameActivated ) )
		if hasattr( self.__renderPassNameWidget, "renderPassNameChangedSignal" ) :
			self.__renderPassNameWidget.renderPassNameChangedSignal().connect( Gaffer.WeakMethod( self.__renderPassNameChanged ) )
			self.__updateButtonState()

	def waitForRenderPassName( self, **kw ) :

		if isinstance( self.__renderPassNameWidget, GafferUI.TextWidget ) :
			self.__renderPassNameWidget.grabFocus()

		button = self.waitForButton( **kw )
		if button is self.__confirmButton :
			return self.__renderPassNameWidget.getRenderPassName()

		return None

	def __renderPassNameActivated( self, renderPassNameWidget ) :

		assert( renderPassNameWidget is self.__renderPassNameWidget )

		if self.__confirmButton.getEnabled() :
			self.__confirmButton.clickedSignal()( self.__confirmButton )

	def __renderPassNameChanged( self, renderPassNameWidget ) :

		assert( renderPassNameWidget is self.__renderPassNameWidget )

		self.__updateButtonState()

	def __updateButtonState( self, *unused ) :

		name = self.__renderPassNameWidget.getRenderPassName()
		unique = name not in self.__existingNames

		self.__confirmButton.setEnabled( unique and name != "" )
		self.__confirmButton.setImage( None if unique else "warningSmall.png" )
		self.__confirmButton.setToolTip( "" if unique else "A render pass named '{}' already exists.".format( name ) )

# Signal with custom result combiner to prevent bad
# slots blocking the execution of others.
class _AddButtonMenuSignal( Gaffer.Signals.Signal2 ) :

	def __init__( self ) :

		Gaffer.Signals.Signal2.__init__( self, self.__combiner )

	@staticmethod
	def __combiner( results ) :

		while True :
			try :
				next( results )
			except StopIteration :
				return
			except Exception as e :
				# Print message but continue to execute other slots
				IECore.msg(
					IECore.Msg.Level.Error,
					"RenderPassEditor Add Button menu", traceback.format_exc()
				)
				# Remove circular references that would keep the widget in limbo.
				e.__traceback__ = None

class RenderPassChooserWidget( GafferUI.Widget ) :

	def __init__( self, settingsNode, **kw ) :

		self.__container = GafferUI.ListContainer()
		GafferUI.Widget.__init__( self, self.__container, **kw )

		self.__scriptNode = settingsNode["__scriptNode"].getInput().node()
		self.__scriptNode["variables"].childAddedSignal().connect( Gaffer.WeakMethod( self.__updateWidget ) )
		self.__scriptNode["variables"].childRemovedSignal().connect( Gaffer.WeakMethod( self.__updateWidget ) )

		self.__updateWidget()

	def __updateWidget( self, *args ) :

		renderPassPlug = GafferSceneUI.ScriptNodeAlgo.acquireRenderPassPlug( self.__scriptNode, createIfMissing = False )

		if renderPassPlug is not None :
			widgets = self.__container[:]
			if not widgets or not widgets[0].getPlug().isSame( renderPassPlug["value"] ) :
				widgets = [ _RenderPassPlugValueWidget( renderPassPlug["value"], showLabel = True ) ]
		else :
			widgets = []

		self.__container[:] = widgets

RenderPassEditor.RenderPassChooserWidget = RenderPassChooserWidget

# Supported metadata :
#
# - `renderPassPlugValueWidget:scene` : The name of a plug on the same node,
#   used to provide the list of passes to choose from. If not specified, the
#   focus node is used instead.
# - `renderPassPlugValueWidget:searchable` : Boolean to toggle
#   the search field. Defaults on.
# - `renderPassPlugValueWidget:displayGrouped` : Boolean to toggle
#   grouping into submenus. Defaults off.
# - `renderPassPlugValueWidget:hideDisabled` : Boolean to toggle
#   hiding of disabled passes. Defaults off.
#
## \todo We should probably move this to its own file and expose it
# publicly as `GafferSceneUI.RenderPassPlugValueWidget`.
class _RenderPassPlugValueWidget( GafferUI.PlugValueWidget ) :

	## \todo We're cheekily reusing the Editor.Settings node here
	# in order to take advantage of the existing hack allowing
	# BackgroundTask to find the cancellation subject via the
	#  "__scriptNode" plug. This should be replaced with a cleaner
	# way for BackgroundTask to recover the ScriptNode.
	class Settings( GafferUI.Editor.Settings ) :

		def __init__( self ) :

			GafferUI.Editor.Settings.__init__( self )

			self["in"] = GafferScene.ScenePlug()
			self["__adaptors"] = GafferSceneUI.RenderPassEditor._createRenderAdaptors()
			self["__adaptors"]["in"].setInput( self["in"] )

	IECore.registerRunTimeTyped( Settings, typeName = "GafferSceneUI::RenderPassPlugValueWidget::Settings" )

	__PassStatus = collections.namedtuple( "__PassStatus", [ "enabled", "adaptedEnabled" ] )

	def __init__( self, plug, showLabel = False, **kw ) :

		self.__settings = self.Settings()
		self.__settings.setName( "RenderPassPlugValueWidgetSettings" )

		self.__listContainer = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 )

		GafferUI.PlugValueWidget.__init__( self, self.__listContainer, plug, **kw )

		self.__settings["__scriptNode"].setInput( self.scriptNode()["fileName"] )

		with self.__listContainer :
			if showLabel :
				GafferUI.Label( "Render Pass" )
			self.__busyWidget = GafferUI.BusyWidget( size = 18 )
			self.__busyWidget.setVisible( False )
			searchable = Gaffer.Metadata.value( plug, "renderPassPlugValueWidget:searchable" )
			self.__menuButton = GafferUI.MenuButton(
				"",
				menu = GafferUI.Menu( Gaffer.WeakMethod( self.__menuDefinition ), searchable = searchable if searchable is not None else True ),
				highlightOnOver = False
			)

		self.__currentRenderPass = ""
		# Maps from pass name to __PassStatus
		self.__renderPasses = {}
		self.__updatePending = False

		self.__updateSettingsInput()
		self.__updateMenuButton()

	def __del__( self ) :

		# Remove connection to ScriptNode now, on the UI thread.
		# See comment in `GafferUI.Editor.__del__()` for details.
		self.__settings.plugDirtiedSignal().disconnectAllSlots()
		self.__settings["__scriptNode"].setInput( None )

	def getToolTip( self ) :

		if self.__currentRenderPass == "" :
			return "No render pass is active."

		if self.__currentRenderPass not in self.__renderPasses :
			return "{} is not available.".format( self.__currentRenderPass )
		else :
			return "{} is the current render pass.".format( self.__currentRenderPass )

	def _auxiliaryPlugs( self, plug ) :

		return [ self.__settings["__adaptors"]["out"]["globals"] ]

	@staticmethod
	def _valuesForUpdate( plugs, auxiliaryPlugs ) :

		result = []

		for plug, ( globalsPlug, ) in zip( plugs, auxiliaryPlugs ) :

			renderPasses = {}

			with Gaffer.Context( Gaffer.Context.current() ) as context :
				context["renderPassEditor:enableAdaptors"] = True
				adaptedRenderPassNames = globalsPlug.getValue().get( "option:renderPass:names", IECore.StringVectorData() )
				context["renderPassEditor:enableAdaptors"] = False
				for renderPass in globalsPlug.getValue().get( "option:renderPass:names", IECore.StringVectorData() ) :
					context["renderPass"] = renderPass
					context["renderPassEditor:enableAdaptors"] = False
					enabled = globalsPlug.getValue().get( "option:renderPass:enabled", IECore.BoolData( True ) ).value
					context["renderPassEditor:enableAdaptors"] = True
					adaptedEnabled = renderPass in adaptedRenderPassNames and globalsPlug.getValue().get( "option:renderPass:enabled", IECore.BoolData( True ) ).value
					renderPasses[renderPass] = _RenderPassPlugValueWidget.__PassStatus( enabled, adaptedEnabled )

			result.append( {
				"value" : plug.getValue(),
				"renderPasses" : renderPasses
			} )

		return result

	def _updateFromValues( self, values, exception ) :

		self.__currentRenderPass = sole( v["value"] for v in values )
		self.__renderPasses = sole( v["renderPasses"] for v in values ) or {}

		# We're called with an empty set of values as a signal that a background
		# update is starting.
		self.__updatePending = exception is None and not len( values ) and self.getPlugs()
		if not self.__updatePending :
			self.__busyWidget.setVisible( False )

		if self.__currentRenderPass is not None :
			self.__updateMenuButton()

		if exception is not None and not isinstance( exception, Gaffer.ProcessException ) :
			# A ProcessException indicates an error computing plug values, which
			# we leave to the rest of the UI to report. Any other type of exception
			# indicates a coding error, which we want to know about.
			IECore.msg(
				IECore.Msg.Level.Error, "_RenderPassPlugValueWidget",
				"".join( traceback.format_exception( exception ) )
			)

	def _updateFromMetadata( self ) :

		self.__updateSettingsInput()

	def _updateFromEditable( self ) :

		self.__menuButton.setEnabled( self._editable() )

	def __getDisplayGrouped( self ) :

		return any( Gaffer.Metadata.value( plug, "renderPassPlugValueWidget:displayGrouped" ) for plug in self.getPlugs() )

	def __setDisplayGrouped( self, grouped ) :

		for plug in self.getPlugs() :
			Gaffer.Metadata.registerValue( plug, "renderPassPlugValueWidget:displayGrouped", grouped )

	def __getHideDisabled( self ) :

		return any( Gaffer.Metadata.value( plug, "renderPassPlugValueWidget:hideDisabled" ) for plug in self.getPlugs() )

	def __setHideDisabled( self, hide ) :

		for plug in self.getPlugs() :
			Gaffer.Metadata.registerValue( plug, "renderPassPlugValueWidget:hideDisabled", hide )

	def __menuDefinition( self ) :

		result = IECore.MenuDefinition()

		result.append( "/__RenderPassesDivider__", { "divider" : True, "label" : "Render Passes" } )

		if self.__getHideDisabled() :
			renderPasses = [ name for name, status in self.__renderPasses.items() if status.adaptedEnabled ]
		else :
			renderPasses = self.__renderPasses.keys()

		if self.__updatePending :
			result.append( "/Refresh", { "command" : Gaffer.WeakMethod( self.__refreshMenu ), "searchable" : False } )
		elif len( renderPasses ) == 0 :
			if not self.__renderPasses :
				result.append( "/No Render Passes Available", { "active" : False, "searchable" : False } )
			else :
				result.append( "/All Render Passes Disabled", { "active" : False, "searchable" : False } )
		else :
			groupingFn = GafferSceneUI.RenderPassEditor.pathGroupingFunction()
			prefixes = IECore.PathMatcher()
			if self.__getDisplayGrouped() :
				for name in renderPasses :
					prefixes.addPath( groupingFn( name ) )

			for name in sorted( renderPasses ) :

				prefix = "/"
				if self.__getDisplayGrouped() :
					if prefixes.match( name ) & IECore.PathMatcher.Result.ExactMatch :
						prefix += name
					else :
						prefix = groupingFn( name )

				result.append(
					os.path.join( prefix, name ),
					{
						"command" : functools.partial( Gaffer.WeakMethod( self.__setCurrentRenderPass ), name ),
						"icon" : self.__renderPassIcon( name, activeIndicator = True ),
						"description" : self.__renderPassDescription( name )
					}
				)

		result.append( "/__NoneDivider__", { "divider" : True } )

		result.append(
			"/None",
			{
				"command" : functools.partial( Gaffer.WeakMethod( self.__setCurrentRenderPass ), "" ),
				"icon" : self.__activeRenderPassIcon() if self.__currentRenderPass == "" else None,
			}
		)

		result.append( "/__OptionsDivider__", { "divider" : True, "label" : "Options" } )

		result.append(
			"/Display Grouped",
			{
				"checkBox" : self.__getDisplayGrouped(),
				"command" : functools.partial( Gaffer.WeakMethod( self.__setDisplayGrouped ) ),
				"description" : "Toggle grouped display of render passes.",
				"searchable" : False
			}
		)

		result.append(
			"/Hide Disabled",
			{
				"checkBox" : self.__getHideDisabled(),
				"command" : functools.partial( Gaffer.WeakMethod( self.__setHideDisabled ) ),
				"description" : "Hide render passes disabled for rendering.",
				"searchable" : False
			}
		)

		return result

	def __refreshMenu( self ) :

		self.__busyWidget.setVisible( True )

	def __setCurrentRenderPass( self, renderPass, *unused ) :

		with Gaffer.UndoScope( self.scriptNode() ) :
			for plug in self.getPlugs() :
				plug.setValue( renderPass )

	def __renderPassDescription( self, renderPass ) :

		if renderPass == "" :
			return ""

		match self.__renderPasses[renderPass] : # `enabled`, `adaptedEnabled`
			case ( True, True ) :
				return ""
			case ( True, False ) :
				return f"{renderPass} has been automatically disabled by a render adaptor."
			case ( False, False ) :
				return f"{renderPass} has been disabled."
			case ( False, True ) :
				return f"{renderPass} has been automatically enabled by a render adaptor."

		return ""

	def __activeRenderPassIcon( self ) :

		renderPassPlug = GafferSceneUI.ScriptNodeAlgo.acquireRenderPassPlug( self.scriptNode(), createIfMissing = False )
		if renderPassPlug is not None and renderPassPlug["value"] in self.getPlugs() :
			# The plug is driving the main ScriptNode context, so use a nice
			# "context yellow" icon to signify this.
			return "activeRenderPass.png"
		else :
			# The plug is just any old plug, so use regular menu styling.
			return "menuChecked.png"

	def __renderPassIcon( self, renderPass, activeIndicator = False ) :

		if renderPass == "" :
			return None

		if activeIndicator and renderPass == self.__currentRenderPass :
			return self.__activeRenderPassIcon()
		elif renderPass not in self.__renderPasses :
			return "warningSmall.png"
		else :
			match self.__renderPasses[renderPass] : # `enabled`, `adaptedEnabled`
				case ( True, True ) :
					return "renderPass.png"
				case ( True, False ) :
					return "adaptorDisabledRenderPass.png"
				case ( False, False ) :
					return "disabledRenderPass.png"
				case ( False, True ) :
					## \todo We don't have a different icon for this, but perhaps
					# we should? One use case might be an adaptor that automatically
					# adds variants of existing render passes.
					return "renderPass.png"

	def __updateMenuButton( self ) :

		self.__menuButton.setText( self.__currentRenderPass or "None" )
		self.__menuButton.setImage( self.__renderPassIcon( self.__currentRenderPass ) )

	def __updateSettingsInput( self ) :

		sceneMetadata = sole( Gaffer.Metadata.value( p, "renderPassPlugValueWidget:scene" ) for p in self.getPlugs() )
		if sceneMetadata :
			self.__focusChangedConnection = None
			scenePlugs = [ p.node().descendant( sceneMetadata ) for p in self.getPlugs() ]
			self.__settings["in"].setInput( next( p for p in scenePlugs if p is not None ) )
		else :
			self.__focusChangedConnection = self.scriptNode().focusChangedSignal().connect(
				Gaffer.WeakMethod( self.__focusChanged ), scoped = True
			)
			self.__updateSettingsInputFromFocus()

	def __focusChanged( self, scriptNode, node ) :

		self.__updateSettingsInputFromFocus()

	def __updateSettingsInputFromFocus( self ) :

		self.__settings["in"].setInput( self.__scenePlugFromFocus() )

	def __scenePlugFromFocus( self ) :

		focusNode = self.scriptNode().getFocus()

		if focusNode is not None :
			outputScene = next(
				( p for p in GafferScene.ScenePlug.RecursiveOutputRange( focusNode ) if not p.getName().startswith( "__" ) ),
				None
			)
			if outputScene is not None :
				return outputScene

			outputImage = next(
				( p for p in  GafferImage.ImagePlug.RecursiveOutputRange( focusNode ) if not p.getName().startswith( "__" ) ),
				None
			)
			if outputImage is not None :
				with self.context() :
					return GafferScene.SceneAlgo.sourceScene( outputImage )

		return None

RenderPassEditor._RenderPassPlugValueWidget = _RenderPassPlugValueWidget
