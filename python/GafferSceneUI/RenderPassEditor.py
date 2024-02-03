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

import IECore

import Gaffer
import GafferUI
import GafferScene
import GafferSceneUI

from . import _GafferSceneUI

from GafferUI.PlugValueWidget import sole
from GafferSceneUI._HistoryWindow import _HistoryWindow

from Qt import QtWidgets

## \todo Make a SceneEditor base class to encapsulate the logic about what
# scene to view, and to track the reparenting of the plug.
class RenderPassEditor( GafferUI.NodeSetEditor ) :

	# We store our settings as plugs on a node for a few reasons :
	#
	# - We want to use an EditScopePlugValueWidget, and that requires it.
	# - We get a bunch of useful widgets and signals for free.
	# - Longer term we want to refactor all Editors to derive from Node,
	#   in the same way that View does already. This will let us serialise
	#   _all_ layout state in the same format we serialise node graphs in.
	# - The `userDefault` metadata provides a convenient way of configuring
	#   defaults.
	# - The PlugLayout we use to display the settings allows users to add
	#   their own widgets to the UI.
	class Settings( Gaffer.Node ) :

		def __init__( self ) :

			Gaffer.Node.__init__( self, "Settings" )

			self["in"] = GafferScene.ScenePlug()
			self["tabGroup"] = Gaffer.StringPlug( defaultValue = "Cycles" )
			self["section"] = Gaffer.StringPlug( defaultValue = "Main" )
			self["editScope"] = Gaffer.Plug()

	IECore.registerRunTimeTyped( Settings, typeName = "GafferSceneUI::RenderPassEditor::Settings" )

	def __init__( self, scriptNode, **kw ) :

		mainColumn = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, borderWidth = 4, spacing = 4 )

		GafferUI.NodeSetEditor.__init__( self, mainColumn, scriptNode, nodeSet = scriptNode.focusSet(), **kw )

		self.__settingsNode = self.Settings()
		Gaffer.NodeAlgo.applyUserDefaults( self.__settingsNode )

		searchFilter = _GafferSceneUI._RenderPassEditor.SearchFilter()
		disabledRenderPassFilter = _GafferSceneUI._RenderPassEditor.DisabledRenderPassFilter()
		disabledRenderPassFilter.userData()["UI"] = { "label" : "Hide Disabled", "toolTip" : "Hide render passes that are disabled for rendering" }
		disabledRenderPassFilter.setEnabled( False )

		self.__filter = Gaffer.CompoundPathFilter( [ searchFilter, disabledRenderPassFilter ] )

		with mainColumn :

			GafferUI.PlugLayout(
				self.__settingsNode,
				orientation = GafferUI.ListContainer.Orientation.Horizontal,
				rootSection = "Settings"
			)

			with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :

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

			self.__pathListing.buttonDoubleClickSignal().connectFront( Gaffer.WeakMethod( self.__buttonDoubleClick ), scoped = False )
			self.__pathListing.keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPress ), scoped = False )
			self.__pathListing.buttonPressSignal().connectFront( Gaffer.WeakMethod( self.__buttonPress ), scoped = False )

			self.__settingsNode.plugSetSignal().connect( Gaffer.WeakMethod( self.__settingsPlugSet ), scoped = False )

		self._updateFromSet()
		self.__updateColumns()

	__columnRegistry = collections.OrderedDict()

	@classmethod
	def registerOption( cls, groupKey, optionName, section = "Main", columnName = None ) :

		optionLabel = Gaffer.Metadata.value( "option:" + optionName, "label" )
		if not columnName :
			columnName = optionLabel or optionName.split( ":" )[-1]

		toolTip = "<h3>{}</h3>".format( optionLabel or columnName )
		optionDescription = Gaffer.Metadata.value( "option:" + optionName, "description" )
		if optionDescription :
			toolTip += "\n\n" + optionDescription

		GafferSceneUI.RenderPassEditor.registerColumn(
			groupKey,
			optionName,
			lambda scene, editScope : _GafferSceneUI._RenderPassEditor.OptionInspectorColumn(
				GafferSceneUI.Private.OptionInspector( scene, editScope, optionName ),
				columnName,
				toolTip
			),
			section
		)

	# Registers a column in the Render Pass Editor.
	# `inspectorFunction` is a callable object of the form
	# `inspectorFunction( scene, editScope )` returning a
	# `GafferSceneUI._RenderPassEditor.OptionInspectorColumn` object.
	@classmethod
	def registerColumn( cls, groupKey, columnKey, inspectorFunction, section = "Main" ) :

		sections = cls.__columnRegistry.setdefault( groupKey, collections.OrderedDict() )
		section = sections.setdefault( section, collections.OrderedDict() )

		section[columnKey] = inspectorFunction

	def __repr__( self ) :

		return "GafferSceneUI.RenderPassEditor( scriptNode )"

	def __firstValidScenePlug( self, node ):

		for plug in GafferScene.ScenePlug.RecursiveOutputRange( node ) :
			if not plug.getName().startswith( "__" ):
				return plug
		return None

	def _updateFromSet( self ) :

		# Decide what plug we're viewing.
		plug = None
		self.__plugParentChangedConnection = None
		node = self._lastAddedNode()
		if node is not None :
			plug = self.__firstValidScenePlug( node )
			if plug is not None :
				self.__plugParentChangedConnection = plug.parentChangedSignal().connect(
					Gaffer.WeakMethod( self.__plugParentChanged ), scoped = True
				)

		self.__settingsNode["in"].setInput( plug )

		# call base class update - this will trigger a call to _titleFormat(),
		# hence the need for already figuring out the plug.
		GafferUI.NodeSetEditor._updateFromSet( self )

		## \todo Remove in Gaffer 1.4 when we can drive `RenderPassEditor.Settings` from
		# `GafferUI.Editor.Settings` to follow the changes introduced with ImageInspector.
		self.__setPathListingPath()

	def _updateFromContext( self, modifiedItems ) :

		if any( not i.startswith( "ui:" ) for i in modifiedItems ) :
			self.__setPathListingPath()

	def _titleFormat( self ) :

		return GafferUI.NodeSetEditor._titleFormat(
			self,
			_maxNodes = 1 if self.__settingsNode["in"].getInput() is not None else 0,
			_reverseNodes = True,
			_ellipsis = False
		)

	@GafferUI.LazyMethod()
	def __updateColumns( self ) :

		tabGroup = self.__settingsNode["tabGroup"].getValue()
		currentSection = self.__settingsNode["section"].getValue()

		sectionColumns = []

		for groupKey, sections in self.__columnRegistry.items() :
			if IECore.StringAlgo.match( tabGroup, groupKey ) :
				section = sections.get( currentSection or None, {} )
				sectionColumns += [ c( self.__settingsNode["in"], self.__settingsNode["editScope"] ) for c in section.values() ]

		self.__pathListing.setColumns( [ self.__renderPassNameColumn, self.__renderPassActiveColumn ] + sectionColumns )

	def __settingsPlugSet( self, plug ) :

		if plug in ( self.__settingsNode["section"], self.__settingsNode["tabGroup"] ) :
			self.__updateColumns()

	def __plugParentChanged( self, plug, oldParent ) :

		# if a plug has been removed or moved to another node, then
		# we need to stop viewing it - _updateFromSet() will find the
		# next suitable plug from the current node set.
		self._updateFromSet()

	@GafferUI.LazyMethod( deferUntilPlaybackStops = True )
	def __setPathListingPath( self ) :

		## \todo Simplify in Gaffer 1.4, we shouldn't require the fallback to DictPath when we have no input.
		if self.__settingsNode["in"].getInput() is not None :
			# We take a static copy of our current context for use in the RenderPassPath - this prevents the
			# PathListing from updating automatically when the original context changes, and allows us to take
			# control of updates ourselves in _updateFromContext(), using LazyMethod to defer the calls to this
			# function until we are visible and playback has stopped.
			contextCopy = Gaffer.Context( self.getContext() )
			self.__pathListing.setPath( _GafferSceneUI._RenderPassEditor.RenderPassPath( self.__settingsNode["in"], contextCopy, "/", filter = self.__filter ) )
		else :
			self.__pathListing.setPath( Gaffer.DictPath( {}, "/" ) )

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
			else :
				self.__editSelectedCells( pathListing )

			return True

		return False

	def __keyPress( self, pathListing, event ) :

		if event.modifiers == event.Modifiers.None_ :

			if event.key == "Return" or event.key == "Enter" :
				selection = pathListing.getSelection()
				if len( selection[1].paths() ) :
					self.__setActiveRenderPass( pathListing )
				else :
					self.__editSelectedCells( pathListing )
				return True

			if event.key == "D" and len( self.__disablableInspectionTweaks( pathListing ) ) > 0 :
				self.__disableEdits( pathListing )
				return True

	def __selectedRenderPasses( self, columns = [ 0 ] ) :

		# There may be multiple columns with a selection, but we only operate on the specified column indices.
		selection = self.__pathListing.getSelection()
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
			with GafferUI.PopupWindow() as self.__popup :
				with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :
					GafferUI.Image( "warningSmall.png" )
					GafferUI.Label( "<h4>The script is read-only.</h4>" )

			self.__popup.popup()
			return

		if "renderPass" not in script["variables"] :
			renderPassPlug = Gaffer.NameValuePlug( "renderPass", "", "renderPass", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
			script["variables"].addChild( renderPassPlug )
			Gaffer.MetadataAlgo.setReadOnly( renderPassPlug["name"], True )
		else :
			renderPassPlug = script["variables"]["renderPass"]

		renderPassPlug["value"].setValue( selectedPassNames[0] )

	## \todo Consider consolidating this with `LightEditor.__editSelectedCells()`.
	# The main difference being the name of the context variable that is set before inspection,
	# (`renderPass` vs `scene:path`) and the source of data for that variable.
	def __editSelectedCells( self, pathListing, quickBoolean = True ) :

		# A dictionary of the form :
		# { inspector : { renderPass1 : inspection, renderPass2 : inspection, ... }, ... }
		inspectors = {}
		inspections = []

		with Gaffer.Context( self.getContext() ) as context :
			renderPassPath = self.__pathListing.getPath().copy()
			for selection, column in zip( pathListing.getSelection(), pathListing.getColumns() ) :
				if not isinstance( column, _GafferSceneUI._RenderPassEditor.OptionInspectorColumn ) :
					continue
				for path in selection.paths() :
					renderPassPath.setFromString( path )
					renderPassName = renderPassPath.property( "renderPassPath:name" )
					if not renderPassName :
						continue

					context["renderPass"] = renderPassName
					inspection = column.inspector().inspect()

					if inspection is not None :
						inspectors.setdefault( column.inspector(), {} )[renderPassName] = inspection
						inspections.append( inspection )

		if len( inspectors ) == 0 :
			with GafferUI.PopupWindow() as self.__popup :
				with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :
					GafferUI.Image( "warningSmall.png" )
					GafferUI.Label( "<h4>The selected cells cannot be edited in the current Edit Scope</h4>" )

			self.__popup.popup()

			return

		nonEditable = [ i for i in inspections if not i.editable() ]

		if len( nonEditable ) == 0 :
			with Gaffer.Context( self.getContext() ) as context :
				if not quickBoolean or not self.__toggleBoolean( inspectors, inspections ) :
					edits = [ i.acquireEdit() for i in inspections ]
					warnings = "\n".join( [ i.editWarning() for i in inspections if i.editWarning() != "" ] )
					# The plugs are either not boolean, boolean with mixed values,
					# or attributes that don't exist and are not boolean. Show the popup.
					self.__popup = GafferUI.PlugPopup( edits, warning = warnings )

					if isinstance( self.__popup.plugValueWidget(), GafferUI.TweakPlugValueWidget ) :
						self.__popup.plugValueWidget().setNameVisible( False )

					## \todo : Adjust popup width based on the inspector column width(s) to improve
					# editing of long paths, similar to how we handle this in the Spreadsheet.
					self.__popup.popup()

		else :

			with GafferUI.PopupWindow() as self.__popup :
				with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :
					GafferUI.Image( "warningSmall.png" )
					GafferUI.Label( "<h4>{}</h4>".format( nonEditable[0].nonEditableReason() ) )

			self.__popup.popup()

	def __toggleBoolean( self, inspectors, inspections ) :

		plugs = [ i.acquireEdit() for i in inspections ]
		# Make sure all the plugs either contain, or are themselves a BoolPlug
		if not all (
			(
				isinstance( plug, ( Gaffer.TweakPlug, Gaffer.NameValuePlug ) ) and
				isinstance( plug["value"], Gaffer.BoolPlug )
			) or (
				isinstance( plug, ( Gaffer.BoolPlug ) )
			)
			for plug, inspector in zip( plugs, inspectors )
		) :
			return False

		currentValues = []

		# Use a single new value for all plugs.
		# First we need to find out what the new value would be for each plug in isolation.
		for inspector, pathInspections in inspectors.items() :
			for path, inspection in pathInspections.items() :
				currentValue = inspection.value().value if inspection.value() is not None else None
				currentValues.append( currentValue )

		# Now set the value for all plugs, defaulting to `True` if they are not
		# currently all the same.
		newValue = not sole( currentValues )

		with Gaffer.UndoScope( self.scriptNode() ) :
			for inspector, pathInspections in inspectors.items() :
				for path, inspection in pathInspections.items() :
					plug = inspection.acquireEdit()
					if isinstance( plug, ( Gaffer.TweakPlug, Gaffer.NameValuePlug ) ) :
						plug["value"].setValue( newValue )
						plug["enabled"].setValue( True )
						if isinstance( plug, Gaffer.TweakPlug ) :
							plug["mode"].setValue( Gaffer.TweakPlug.Mode.Create )
					else :
						plug.setValue( newValue )

		return True

	def __disablableInspectionTweaks( self, pathListing ) :

		tweaks = []

		with Gaffer.Context( self.getContext() ) as context :
			renderPassPath = self.__pathListing.getPath().copy()
			for columnSelection, column in zip( pathListing.getSelection(), pathListing.getColumns() ) :
				if not isinstance( column, _GafferSceneUI._RenderPassEditor.OptionInspectorColumn ) :
					continue
				for path in columnSelection.paths() :
					renderPassPath.setFromString( path )
					renderPassName = renderPassPath.property( "renderPassPath:name" )
					if not renderPassName :
						continue

					context["renderPass"] = renderPassName
					inspection = column.inspector().inspect()
					if inspection is not None and inspection.editable() :
						source = inspection.source()
						editScope = self.__settingsNode["editScope"].getInput()
						if (
							(
								isinstance( source, ( Gaffer.TweakPlug, Gaffer.NameValuePlug ) ) and
								source["enabled"].getValue()
							) and
							( editScope is None or editScope.node().isAncestorOf( source ) )
						) :
							tweaks.append( ( path, column.inspector() ) )
						else :
							return []
					else :
						return []

		return tweaks

	def __disableEdits( self, pathListing ) :

		edits = self.__disablableInspectionTweaks( pathListing )

		with Gaffer.UndoScope( self.scriptNode() ), Gaffer.Context( self.getContext() ) as context :
			renderPassPath = self.__pathListing.getPath().copy()
			for path, inspector in edits :
				renderPassPath.setFromString( path )
				context["renderPass"] = renderPassPath.property( "renderPassPath:name" )
				inspection = inspector.inspect()
				if inspection is not None and inspection.editable() :
					source = inspection.source()

					if isinstance( source, ( Gaffer.TweakPlug, Gaffer.NameValuePlug ) ) :
						source["enabled"].setValue( False )

	def __buttonPress( self, pathListing, event ) :

		if event.button != event.Buttons.Right or event.modifiers != event.Modifiers.None_ :
			return False

		selection = pathListing.getSelection()

		columns = pathListing.getColumns()
		cellColumn = pathListing.columnAt( event.line.p0 )
		columnIndex = -1
		for i in range( 0, len( columns ) ) :
			if cellColumn == columns[i] :
				columnIndex = i

		cellPath = pathListing.pathAt( event.line.p0 )
		if cellPath is None :
			return False

		if not selection[columnIndex].match( str( cellPath ) ) & IECore.PathMatcher.Result.ExactMatch :
			for p in selection :
				p.clear()
			selection[columnIndex].addPath( str( cellPath ) )
			pathListing.setSelection( selection, scrollToFirst = False )

		menuDefinition = IECore.MenuDefinition()

		if columnIndex > 1 :
			# Option cells

			menuDefinition.append(
				"Show History...",
				{
					"command" : Gaffer.WeakMethod( self.__showEditHistory )
				}
			)
			menuDefinition.append(
				"Edit...",
				{
					"command" : functools.partial( self.__editSelectedCells, pathListing, False ),
					"active" : pathListing.getSelection()[0].isEmpty(),
				}
			)
			menuDefinition.append(
				"Disable Edit",
				{
					"command" : functools.partial( self.__disableEdits, pathListing ),
					"active" : len( self.__disablableInspectionTweaks( pathListing ) ) > 0,
					"shortCut" : "D",
				}
			)

		self.__contextMenu = GafferUI.Menu( menuDefinition )
		self.__contextMenu.popup( pathListing )

		return True

	def __showEditHistory( self, *unused ) :

		selection = self.__pathListing.getSelection()
		columns = self.__pathListing.getColumns()
		renderPassPath = self.__pathListing.getPath().copy()

		for i in range( 0, len( columns ) ) :
			column = columns[ i ]
			if not isinstance( column, _GafferSceneUI._RenderPassEditor.OptionInspectorColumn ) :
				continue

			for path in selection[i].paths() :
				renderPassPath.setFromString( path )
				renderPassName = renderPassPath.property( "renderPassPath:name" )
				if renderPassName is None :
					continue

				historyContext = Gaffer.Context( self.getContext() )
				historyContext["renderPass"] = renderPassName
				window = _HistoryWindow(
					column.inspector(),
					"/",
					historyContext,
					self.ancestor( GafferUI.ScriptWindow ).scriptNode(),
					"History : {} : {}".format( renderPassName, column.headerData().value )
				)
				self.ancestor( GafferUI.Window ).addChildWindow( window, removeOnClose = True )
				window.setVisible( True )

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

		],

	}

)

class _SectionPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		GafferUI.PlugValueWidget.__init__( self, QtWidgets.QTabBar(), plug, **kw )

		self._qtWidget().setDrawBase( False )

		self._qtWidget().currentChanged.connect( Gaffer.WeakMethod( self.__currentChanged ) )
		self.__ignoreCurrentChanged = False

		plug.node().plugSetSignal().connect( Gaffer.WeakMethod( self.__plugSet ), scoped = False )

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

##########################################################################
# _SearchFilterWidget
##########################################################################

class _SearchFilterWidget( GafferUI.PathFilterWidget ) :

	def __init__( self, pathFilter ) :

		self.__patternWidget = GafferUI.TextWidget()
		GafferUI.PathFilterWidget.__init__( self, self.__patternWidget, pathFilter )

		self.__patternWidget._qtWidget().setPlaceholderText( "Filter..." )

		self.__patternWidget.editingFinishedSignal().connect( Gaffer.WeakMethod( self.__patternEditingFinished ), scoped = False )
		self.__patternWidget.dragEnterSignal().connectFront( Gaffer.WeakMethod( self.__dragEnter ), scoped = False )
		self.__patternWidget.dragLeaveSignal().connectFront( Gaffer.WeakMethod( self.__dragLeave ), scoped = False )
		self.__patternWidget.dropSignal().connectFront( Gaffer.WeakMethod( self.__drop ), scoped = False )

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
