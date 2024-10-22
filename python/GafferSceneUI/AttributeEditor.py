##########################################################################
#
#  Copyright (c) 2024, Cinesite VFX Ltd. All rights reserved.
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

import IECore

import Gaffer
import GafferUI
import GafferScene
import GafferSceneUI

from . import _GafferSceneUI

from Qt import QtWidgets

class AttributeEditor( GafferSceneUI.SceneEditor ) :

	class Settings( GafferSceneUI.SceneEditor.Settings ) :

		def __init__( self ) :

			GafferSceneUI.SceneEditor.Settings.__init__( self )

			self["tabGroup"] = Gaffer.StringPlug( defaultValue = "Standard" )
			self["section"] = Gaffer.StringPlug( defaultValue = "Attributes" )
			self["editScope"] = Gaffer.Plug()

	IECore.registerRunTimeTyped( Settings, typeName = "GafferSceneUI::AttributeEditor::Settings" )

	def __init__( self, scriptNode, **kw ) :

		column = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, borderWidth = 4, spacing = 4 )

		GafferSceneUI.SceneEditor.__init__( self, column, scriptNode, **kw )

		searchFilter = _GafferSceneUI._HierarchyViewSearchFilter()
		searchFilter.setScene( self.settings()["in"] )
		self.__filter = searchFilter

		with column :

			GafferUI.PlugLayout(
				self.settings(),
				orientation = GafferUI.ListContainer.Orientation.Horizontal,
				rootSection = "Settings"
			)

			_SearchFilterWidget( searchFilter )

			self.__locationNameColumn = GafferUI.PathListingWidget.defaultNameColumn
			self.__pathListing = GafferUI.PathListingWidget(
				Gaffer.DictPath( {}, "/" ), # Temp till we make a ScenePath
				columns = [
					self.__locationNameColumn,
				],
				selectionMode = GafferUI.PathListingWidget.SelectionMode.Cells,
				displayMode = GafferUI.PathListingWidget.DisplayMode.Tree,
				horizontalScrollMode = GafferUI.ScrollMode.Automatic
			)

			self.__pathListing.setDragPointer( "objects" )
			self.__pathListing.setSortable( False )
			self.__selectionChangedConnection = self.__pathListing.selectionChangedSignal().connect(
				Gaffer.WeakMethod( self.__selectionChanged )
			)
			self.__pathListing.columnContextMenuSignal().connect( Gaffer.WeakMethod( self.__columnContextMenuSignal ) )
			self.keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPressSignal ) )

		self.__selectedPathsChangedConnection = GafferSceneUI.ScriptNodeAlgo.selectedPathsChangedSignal( scriptNode ).connect(
			Gaffer.WeakMethod( self.__selectedPathsChanged )
		)

		self._updateFromSet()
		self.__setPathListingPath()
		self.__transferSelectionFromScriptNode()
		self.__updateColumns()

	__columnRegistry = collections.OrderedDict()

	def scene( self ) :

		return self.settings()["in"].getInput()

	## Returns the widget used for showing the main scene listing, with the
	# intention that clients can add custom context menu items via
	# `sceneListing.columnContextMenuSignal()`.
	#
	# > Caution : This currently returns a PathListingWidget, but in future
	# > will probably return a more specialised widget with fewer privileges.
	# > Please limit usage to `columnContextMenuSignal()`.
	def sceneListing( self ) :

		return self.__pathListing

	@classmethod
	def registerAttribute( cls, groupKey, attributeName, section = "Main", columnName = None ) :

		label = Gaffer.Metadata.value( "attribute:" + attributeName, "label" )
		if not columnName :
			columnName = label or attributeName.split( ":" )[-1]

		toolTip = "<h3>{}</h3> Attribute : <code>{}</code>".format( label or columnName, attributeName )
		description = Gaffer.Metadata.value( "attribute:" + attributeName, "description" )
		if description :
			## \todo PathListingWidget's PathModel should be handling this instead.
			toolTip += GafferUI.DocumentationAlgo.markdownToHTML( description )

		GafferSceneUI.AttributeEditor.registerColumn(
			groupKey,
			attributeName,
			lambda scene, editScope : GafferSceneUI.Private.InspectorColumn(
				GafferSceneUI.Private.AttributeInspector( scene, editScope, attributeName ),
				columnName,
				toolTip
			),
			section
		)

	# Registers a column in the Attribute Editor.
	# `inspectorFunction` is a callable object of the form
	# `inspectorFunction( scene, editScope )` returning a
	# `GafferSceneUI.Private.InspectorColumn` object.
	@classmethod
	def registerColumn( cls, groupKey, columnKey, inspectorFunction, section = "Main" ) :

		assert( isinstance( columnKey, str ) )

		sections = cls.__columnRegistry.setdefault( groupKey, collections.OrderedDict() )
		section = sections.setdefault( section, collections.OrderedDict() )

		section[columnKey] = inspectorFunction

	# Removes a column from the Attribute Editor.
	# `groupKey` should match the value the attribute was registered with.
	# `columnKey` is the string value of the attribute name.
	@classmethod
	def deregisterColumn( cls, groupKey, columnKey, section = "Main" ) :

		assert( isinstance( columnKey, str ) )

		sections = cls.__columnRegistry.get( groupKey )
		if sections is not None and section in sections.keys() and columnKey in sections[section].keys() :
			del sections[section][columnKey]

			if len( sections[section] ) == 0 :
				del sections[section]

	def __repr__( self ) :

		return "GafferSceneUI.AttributeEditor( scriptNode )"

	def _updateFromContext( self, modifiedItems ) :

		for item in modifiedItems :
			if not item.startswith( "ui:" ) :
				# When the context has changed, the hierarchy of the scene may
				# have too so we should update our PathListingWidget.
				self.__setPathListingPath()
				break

	def _updateFromSettings( self, plug ) :

		if plug in ( self.settings()["section"], self.settings()["tabGroup"] ) :
			self.__updateColumns()

	@GafferUI.LazyMethod()
	def __updateColumns( self ) :

		tabGroup = self.settings()["tabGroup"].getValue()
		currentSection = self.settings()["section"].getValue()

		sectionColumns = []

		for groupKey, sections in self.__columnRegistry.items() :
			if IECore.StringAlgo.match( tabGroup, groupKey ) :
				if currentSection == "All" and not sections.get( "All" ) :
					for section in sections.values() :
						sectionColumns += [ c( self.settings()["in"], self.settings()["editScope"] ) for c in section.values() ]
				else :
					section = sections.get( currentSection or None, {} )
					sectionColumns += [ c( self.settings()["in"], self.settings()["editScope"] ) for c in section.values() ]

		self.__pathListing.setColumns( [ self.__locationNameColumn ] + sectionColumns )

	@GafferUI.LazyMethod( deferUntilPlaybackStops = True )
	def __setPathListingPath( self ) :

		# We take a static copy of our current context for use in the ScenePath - this prevents the
		# PathListing from updating automatically when the original context changes, and allows us to take
		# control of updates ourselves in _updateFromContext(), using LazyMethod to defer the calls to this
		# function until we are visible and playback has stopped.
		## \todo With the ContextTracker now providing a new and immutable context for each update, we
		# should be safe to remove this copy, and those from other Editors using PathListingWidgets.
		contextCopy = Gaffer.Context( self.context() )
		self.__filter.setContext( contextCopy )
		self.__pathListing.setPath( GafferScene.ScenePath( self.settings()["in"], contextCopy, "/", filter = self.__filter ) )

	def __selectedPathsChanged( self, scriptNode ) :

		self.__transferSelectionFromScriptNode()

	def __selectionChanged( self, pathListing ) :

		assert( pathListing is self.__pathListing )

		with Gaffer.Signals.BlockedConnection( self.__selectedPathsChangedConnection ) :
			GafferSceneUI.ScriptNodeAlgo.setSelectedPaths( self.scriptNode(), pathListing.getSelection()[0] )

	def __keyPressSignal( self, widget, event ) :

		if event.key == "F" :
			self.__frameSelectedPaths()
			return True

		return False

	def __columnContextMenuSignal( self, column, pathListing, menuDefinition ) :

		columns = pathListing.getColumns()

		if columns.index( column ) == 0 :

			selection = pathListing.getSelection()
			menuDefinition.append(
				"Frame Selection",
				{
					"command" : Gaffer.WeakMethod( self.__frameSelectedPaths ),
					"active" : not selection[0].isEmpty(),
					"shortCut" : "F"
				}
			)

	def __frameSelectedPaths( self, *unused ) :

		selection = self.__pathListing.getSelection()
		if not selection[0].isEmpty() :
			self.__pathListing.expandTo( selection[0] )
			self.__pathListing.scrollToFirst( selection[0] )

	@GafferUI.LazyMethod( deferUntilPlaybackStops = True )
	def __transferSelectionFromScriptNode( self ) :

		selectedPaths = GafferSceneUI.ScriptNodeAlgo.getSelectedPaths( self.scriptNode() )
		with Gaffer.Signals.BlockedConnection( self.__selectionChangedConnection ) :
			selection = [selectedPaths] + ( [IECore.PathMatcher()] * ( len( self.__pathListing.getColumns() ) - 1 ) )
			self.__pathListing.setSelection( selection, scrollToFirst = False )

GafferUI.Editor.registerType( "AttributeEditor", AttributeEditor )

##########################################################################
# Metadata controlling the settings UI
##########################################################################

Gaffer.Metadata.registerNode(

	AttributeEditor.Settings,

	## \todo Doing spacers with custom widgets is tedious, and we're doing it
	# in all the View UIs. Maybe we could just attach metadata to the plugs we
	# want to add space around, in the same way we use `divider` to add a divider?
	"layout:customWidget:spacer:widgetType", "GafferSceneUI.AttributeEditor._Spacer",
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

			"plugValueWidget:type", "GafferSceneUI.AttributeEditor._SectionPlugValueWidget",

		],

		"editScope" : [

			"plugValueWidget:type", "GafferUI.EditScopeUI.EditScopePlugValueWidget",
			"layout:width", 225,

		],

	}

)

## \todo Consolidate with the equivalent widgets in the LightEditor and RenderPassEditor.
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
			self.getPlug().setValue(
				text if text != "Main" else ""
			)

	def __updateTabs( self ) :

		try :
			self.__ignoreCurrentChanged = True
			while self._qtWidget().count() :
				self._qtWidget().removeTab( 0 )

			tabGroup = self.getPlug().node()["tabGroup"].getValue()

			for groupKey, sections in AttributeEditor._AttributeEditor__columnRegistry.items() :
				if IECore.StringAlgo.match( tabGroup, groupKey ) :
					for section in sections.keys() :
						self._qtWidget().addTab( section or "Main" )
					if "All" not in sections.keys() and len( sections.keys() ) > 1 :
						self._qtWidget().addTab( "All" )
		finally :
			self.__ignoreCurrentChanged = False

	def __plugSet( self, plug ) :

		if plug == self.getPlug().node()["tabGroup"] :
			self.__updateTabs()
			# Preserve the current section if there is an equivalently
			# named section registered for the new tabGroup
			self._updateFromValues( [ self.getPlug().getValue() ], None )
			self.__currentChanged( self._qtWidget().currentIndex() )

AttributeEditor._SectionPlugValueWidget = _SectionPlugValueWidget

class _Spacer( GafferUI.Spacer ) :

	def __init__( self, settingsNode, **kw ) :

		GafferUI.Spacer.__init__( self, imath.V2i( 0 ) )

AttributeEditor._Spacer = _Spacer

##########################################################################
# _SearchFilterWidget
##########################################################################

## \todo Perhaps the search text should live on a Settings plug, with
# _updateFromSettings() syncing it to the filter?
class _SearchFilterWidget( GafferUI.PathFilterWidget ) :

	def __init__( self, pathFilter ) :

		self.__patternWidget = GafferUI.TextWidget()
		GafferUI.PathFilterWidget.__init__( self, self.__patternWidget, pathFilter )

		self.__patternWidget.setPlaceholderText( "Filter..." )
		self.__patternWidget.editingFinishedSignal().connect( Gaffer.WeakMethod( self.__patternEditingFinished ) )

		self._updateFromPathFilter()

	def _updateFromPathFilter( self ) :

		self.__patternWidget.setText( self.pathFilter().getMatchPattern() )

	def __patternEditingFinished( self, widget ) :

		self.pathFilter().setMatchPattern( self.__patternWidget.getText() )
