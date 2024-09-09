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
import imath
import traceback

import IECore

import Gaffer
import GafferUI
import GafferScene
import GafferSceneUI

from . import _GafferSceneUI

from Qt import QtWidgets

class RenderPassEditor( GafferSceneUI.SceneEditor ) :

	class Settings( GafferSceneUI.SceneEditor.Settings ) :

		def __init__( self ) :

			GafferSceneUI.SceneEditor.Settings.__init__( self )

			self["tabGroup"] = Gaffer.StringPlug( defaultValue = "Cycles" )
			self["section"] = Gaffer.StringPlug( defaultValue = "Main" )
			self["editScope"] = Gaffer.Plug()
			self["displayGrouped"] = Gaffer.BoolPlug()

	IECore.registerRunTimeTyped( Settings, typeName = "GafferSceneUI::RenderPassEditor::Settings" )

	def __init__( self, scriptNode, **kw ) :

		mainColumn = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, borderWidth = 4, spacing = 4 )

		GafferSceneUI.SceneEditor.__init__( self, mainColumn, scriptNode, **kw )

		searchFilter = _GafferSceneUI._RenderPassEditor.SearchFilter()
		disabledRenderPassFilter = _GafferSceneUI._RenderPassEditor.DisabledRenderPassFilter()
		disabledRenderPassFilter.userData()["UI"] = { "label" : "Hide Disabled", "toolTip" : "Hide render passes that are disabled for rendering" }
		disabledRenderPassFilter.setEnabled( False )

		self.__filter = Gaffer.CompoundPathFilter( [ searchFilter, disabledRenderPassFilter ] )

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
					rootSection = "Grouping"
				)
				GafferUI.Divider( orientation = GafferUI.Divider.Orientation.Vertical )

				_SearchFilterWidget( searchFilter )
				GafferUI.BasicPathFilterWidget( disabledRenderPassFilter )

			self.__renderPassNameColumn = _GafferSceneUI._RenderPassEditor.RenderPassNameColumn()
			self.__renderPassActiveColumn = _GafferSceneUI._RenderPassEditor.RenderPassActiveColumn()
			self.__pathListing = GafferUI.PathListingWidget(
				Gaffer.DictPath( {}, "/" ), # temp till we make an RenderPassPath
				columns = [
					self.__renderPassNameColumn,
					self.__renderPassActiveColumn,
				],
				selectionMode = GafferUI.PathListingWidget.SelectionMode.Cells,
				displayMode = GafferUI.PathListingWidget.DisplayMode.Tree,
				horizontalScrollMode = GafferUI.ScrollMode.Automatic
			)

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
			self.__pathListing.dragBeginSignal().connectFront( Gaffer.WeakMethod( self.__dragBegin ) )

		self._updateFromSet()
		self.__setPathListingPath()
		self.__updateColumns()
		self.__updateButtonStatus()

	__columnRegistry = collections.OrderedDict()

	@classmethod
	def registerOption( cls, groupKey, optionName, section = "Main", columnName = None ) :

		optionLabel = Gaffer.Metadata.value( "option:" + optionName, "label" )
		if not columnName :
			columnName = optionLabel or optionName.split( ":" )[-1]

		toolTip = "<h3>{}</h3>".format( optionLabel or columnName )
		optionDescription = Gaffer.Metadata.value( "option:" + optionName, "description" )
		if optionDescription :
			## \todo PathListingWidget's PathModel should be handling this instead.
			toolTip += GafferUI.DocumentationAlgo.markdownToHTML( optionDescription )

		GafferSceneUI.RenderPassEditor.registerColumn(
			groupKey,
			optionName,
			lambda scene, editScope : GafferSceneUI.Private.InspectorColumn(
				GafferSceneUI.Private.OptionInspector( scene, editScope, optionName ),
				columnName,
				toolTip
			),
			section
		)

	# Registers a column in the Render Pass Editor.
	# `inspectorFunction` is a callable object of the form
	# `inspectorFunction( scene, editScope )` returning a
	# `GafferSceneUI.Private.InspectorColumn` object.
	@classmethod
	def registerColumn( cls, groupKey, columnKey, inspectorFunction, section = "Main" ) :

		sections = cls.__columnRegistry.setdefault( groupKey, collections.OrderedDict() )
		section = sections.setdefault( section, collections.OrderedDict() )

		section[columnKey] = inspectorFunction

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

	def __repr__( self ) :

		return "GafferSceneUI.RenderPassEditor( scriptNode )"

	def _updateFromContext( self, modifiedItems ) :

		if any( not i.startswith( "ui:" ) for i in modifiedItems ) :
			self.__setPathListingPath()

	def _updateFromSettings( self, plug ) :

		if plug in ( self.settings()["section"], self.settings()["tabGroup"] ) :
			self.__updateColumns()
		elif plug == self.settings()["displayGrouped"] :
			self.__displayGroupedChanged()
		elif plug in ( self.settings()["in"], self.settings()["editScope"] ) :
			self.__updateButtonStatus()

	@GafferUI.LazyMethod()
	def __updateColumns( self ) :

		tabGroup = self.settings()["tabGroup"].getValue()
		currentSection = self.settings()["section"].getValue()

		sectionColumns = []

		for groupKey, sections in self.__columnRegistry.items() :
			if IECore.StringAlgo.match( tabGroup, groupKey ) :
				section = sections.get( currentSection or None, {} )
				sectionColumns += [ c( self.settings()["in"], self.settings()["editScope"] ) for c in section.values() ]

		self.__pathListing.setColumns( [ self.__renderPassNameColumn, self.__renderPassActiveColumn ] + sectionColumns )

	@GafferUI.LazyMethod( deferUntilPlaybackStops = True )
	def __setPathListingPath( self ) :

		# We take a static copy of our current context for use in the RenderPassPath - this prevents the
		# PathListing from updating automatically when the original context changes, and allows us to take
		# control of updates ourselves in _updateFromContext(), using LazyMethod to defer the calls to this
		# function until we are visible and playback has stopped.
		contextCopy = Gaffer.Context( self.context() )
		self.__pathListing.setPath( _GafferSceneUI._RenderPassEditor.RenderPassPath( self.settings()["in"], contextCopy, "/", filter = self.__filter, grouped = self.settings()["displayGrouped"].getValue() ) )

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

		self.__setPathListingPath()
		self.__pathListing.setSelection( selection )

	def __buttonDoubleClick( self, pathListing, event ) :

		# A small corner area below the vertical scroll bar may pass through
		# to us, causing odd selection behavior. Check that we're within the
		# scroll area.
		if pathListing.pathAt( event.line.p0 ) is None :
			return False

		if event.button == event.Buttons.Left :
			column = pathListing.columnAt( event.line.p0 )
			if column == self.__renderPassActiveColumn :
				self.__setActiveRenderPass( pathListing )
				return True

		return False

	def __keyPress( self, pathListing, event ) :

		if event.modifiers == event.Modifiers.None_ :

			if event.key == "Return" or event.key == "Enter" :
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

	def __dragBegin( self, widget, event ) :

		# Return render pass names rather than the path when dragging the Name column.
		selection = self.__pathListing.getSelection()[0]
		if not selection.isEmpty() :
			return IECore.StringVectorData( self.__selectedRenderPasses() )

	def __setActiveRenderPass( self, pathListing ) :

		selectedPassNames = self.__selectedRenderPasses( columns = [ 1 ] )

		if len( selectedPassNames ) != 1 :
			return

		script = self.scriptNode()
		if Gaffer.MetadataAlgo.readOnly( script ) :
			with GafferUI.PopupWindow() as self.__popup :
				with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :
					GafferUI.Image( "warningSmall.png" )
					GafferUI.Label( "<h4>The script is read-only.</h4>" )

			self.__popup.popup( parent = self )
			return

		if "renderPass" not in script["variables"] :
			renderPassPlug = Gaffer.NameValuePlug( "renderPass", "", "renderPass", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
			script["variables"].addChild( renderPassPlug )
			Gaffer.MetadataAlgo.setReadOnly( renderPassPlug["name"], True )
		else :
			renderPassPlug = script["variables"]["renderPass"]

		with Gaffer.Context( self.getContext() ) :
			currentRenderPass = renderPassPlug["value"].getValue()

		renderPassPlug["value"].setValue( selectedPassNames[0] if selectedPassNames[0] != currentRenderPass else "" )

	def __columnContextMenuSignal( self, column, pathListing, menuDefinition ) :

		columns = pathListing.getColumns()
		columnIndex = -1
		for i in range( 0, len( columns ) ) :
			if column == columns[i] :
				columnIndex = i

		if columnIndex == 0 :
			# Render pass operations

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
			editScopeInput = self.settings()["editScope"].getInput()
			if editScopeInput is None :
				# No edit scope selected
				return False

			editScope = editScopeInput.node()

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

		editScopeInput = self.settings()["editScope"].getInput()
		if editScopeInput is None :
			return

		editScope = editScopeInput.node()
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

		editScopeInput = self.settings()["editScope"].getInput()
		assert( editScopeInput is not None )

		editScope = editScopeInput.node()
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

		editScopeInput = self.settings()["editScope"].getInput()
		if editScopeInput is None :
			return

		renderPassesProcessor = editScopeInput.node().acquireProcessor( "RenderPasses", createIfNecessary = False )

		if (
			Gaffer.MetadataAlgo.readOnlyAffectedByChange( editScopeInput, nodeTypeId, key, node ) or
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

		"*" : [

			"label", "",

		],

		"tabGroup" : [

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
			"layout:width", 100,

		],

		"section" : [

			"plugValueWidget:type", "GafferSceneUI.RenderPassEditor._SectionPlugValueWidget",

		],

		"editScope" : [

			"plugValueWidget:type", "GafferUI.EditScopeUI.EditScopePlugValueWidget",
			"layout:width", 225,

		],

		"displayGrouped" : [

			"description",
			"""
			Click to toggle between list and grouped display of render passes.
			""",

			"layout:section", "Grouping",
			"plugValueWidget:type", "GafferSceneUI.RenderPassEditor._ToggleGroupingPlugValueWidget",

		],

	}

)

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

			for groupKey, sections in RenderPassEditor._RenderPassEditor__columnRegistry.items() :
				if IECore.StringAlgo.match( tabGroup, groupKey ) :
					for section in sections.keys() :
						self._qtWidget().addTab( section )
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

## \todo Should this be a new displayMode of BoolPlugValueWidget?
class _ToggleGroupingPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plugs, **kw ) :

		self.__row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 )

		GafferUI.PlugValueWidget.__init__( self, self.__row, plugs )

		self.__groupingModeButton = GafferUI.Button( image = "pathListingList.png", hasFrame=False )
		self.__groupingModeButton.clickedSignal().connect( Gaffer.WeakMethod( self.__groupingModeButtonClicked ) )
		self.__row.append(
			self.__groupingModeButton
		)

	def __groupingModeButtonClicked( self, button ) :

		[ plug.setValue( not plug.getValue() ) for plug in self.getPlugs() ]

	def _updateFromValues( self, values, exception ) :

		self.__groupingModeButton.setImage( "pathListingTree.png" if all( values ) else "pathListingList.png" )

RenderPassEditor._ToggleGroupingPlugValueWidget = _ToggleGroupingPlugValueWidget

##########################################################################
# _SearchFilterWidget
##########################################################################

class _SearchFilterWidget( GafferUI.PathFilterWidget ) :

	def __init__( self, pathFilter ) :

		self.__patternWidget = GafferUI.TextWidget()
		GafferUI.PathFilterWidget.__init__( self, self.__patternWidget, pathFilter )

		self.__patternWidget.setPlaceholderText( "Filter..." )

		self.__patternWidget.editingFinishedSignal().connect( Gaffer.WeakMethod( self.__patternEditingFinished ) )
		self.__patternWidget.dragEnterSignal().connectFront( Gaffer.WeakMethod( self.__dragEnter ) )
		self.__patternWidget.dragLeaveSignal().connectFront( Gaffer.WeakMethod( self.__dragLeave ) )
		self.__patternWidget.dropSignal().connectFront( Gaffer.WeakMethod( self.__drop ) )

		self._updateFromPathFilter()

	def _updateFromPathFilter( self ) :

		self.__patternWidget.setText( self.pathFilter().getMatchPattern() )

	def __patternEditingFinished( self, widget ) :

		self.pathFilter().setMatchPattern( self.__patternWidget.getText() )

	def __dragEnter( self, widget, event ) :

		if not isinstance( event.data, IECore.StringVectorData ) :
			return False

		if not len( event.data ) :
			return False

		self.__patternWidget.setHighlighted( True )

		return True

	def __dragLeave( self, widget, event ) :

		self.__patternWidget.setHighlighted( False )

		return True

	def __drop( self, widget, event ) :

		if isinstance( event.data, IECore.StringVectorData ) and len( event.data ) > 0 :
			self.pathFilter().setMatchPattern( " ".join( sorted( event.data ) ) )

		self.__patternWidget.setHighlighted( False )

		return True

class _RenderPassCreationDialogue( GafferUI.Dialogue ) :

	def __init__( self, existingNames = [], editScope = None, title = "Add Render Pass", cancelLabel = "Cancel", confirmLabel = "Add", **kw ) :

		GafferUI.Dialogue.__init__( self, title, sizeMode=GafferUI.Window.SizeMode.Fixed, **kw )

		self.__existingNames = set( existingNames or [] )

		self.__column = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing = 8 )
		with self.__column :
			if editScope :
				with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :
					GafferUI.Label( "Add render pass to" )
					editScopeColor = Gaffer.Metadata.value( editScope, "nodeGadget:color" )
					if editScopeColor :
						GafferUI.Image.createSwatch( editScopeColor )
					GafferUI.Label( "<h4>{}</h4>".format( editScope.relativeName( editScope.ancestor( Gaffer.ScriptNode ) ) ) )

			self.__renderPassNameWidget = GafferSceneUI.RenderPassesUI.createRenderPassNameWidget()

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
