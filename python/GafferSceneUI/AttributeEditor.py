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

class AttributeEditor( GafferSceneUI.SceneEditor ) :

	class Settings( GafferSceneUI.SceneEditor.Settings ) :

		def __init__( self ) :

			GafferSceneUI.SceneEditor.Settings.__init__( self, withHierarchyFilter = True )

			self["tabGroup"] = Gaffer.StringPlug( defaultValue = "Standard" )
			self["section"] = Gaffer.StringPlug( defaultValue = "Attributes" )
			self["columnFilter"] = Gaffer.StringPlug()
			self["editScope"] = Gaffer.Plug()

	IECore.registerRunTimeTyped( Settings, "GafferSceneUI::AttributeEditor::Settings" )

	def __init__( self, scriptNode, **kw ) :

		column = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, borderWidth = 4, spacing = 4 )

		GafferSceneUI.SceneEditor.__init__( self, column, scriptNode, **kw )

		with column :

			GafferUI.PlugLayout(
				self.settings(),
				orientation = GafferUI.ListContainer.Orientation.Horizontal,
				rootSection = "Settings"
			)

			GafferUI.PlugLayout(
				self.settings(),
				orientation = GafferUI.ListContainer.Orientation.Horizontal,
				rootSection = "Filter"
			)

			self.__locationNameColumn = GafferUI.PathListingWidget.StandardColumn( "Name", "name", GafferUI.PathColumn.SizeMode.Stretch )
			self.__visibilityColumn = GafferSceneUI.Private.VisibilityColumn( self.settings()["__adaptedIn"], self.settings()["editScope"] )
			self.__pathListing = GafferUI.PathListingWidget(
				GafferScene.ScenePath( self.settings()["__filteredIn"], self.context(), "/" ),
				columns = [
					self.__locationNameColumn,
					self.__visibilityColumn,
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
			GafferSceneUI.Private.InspectorColumn.connectToDragBeginSignal( self.__pathListing )
			self.keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPressSignal ) )

		self.__selectedPathsChangedConnection = GafferSceneUI.ScriptNodeAlgo.selectedPathsChangedSignal( scriptNode ).connect(
			Gaffer.WeakMethod( self.__selectedPathsChanged )
		)

		self.__columnCache = {}

		self._updateFromSet()
		self.__transferSelectionFromScriptNode()
		self.__updateColumnsAndSections()

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
		section = sections.setdefault( section or "Main", collections.OrderedDict() )

		section[columnKey] = inspectorFunction

	# Removes a column from the Attribute Editor.
	# `groupKey` should match the value the attribute was registered with.
	# `columnKey` is the string value of the attribute name.
	@classmethod
	def deregisterColumn( cls, groupKey, columnKey, section = "Main" ) :

		assert( isinstance( columnKey, str ) )

		section = section or "Main"
		sections = cls.__columnRegistry.get( groupKey )
		if sections is not None and section in sections.keys() and columnKey in sections[section].keys() :
			del sections[section][columnKey]

			if len( sections[section] ) == 0 :
				del sections[section]

	def __repr__( self ) :

		return "GafferSceneUI.AttributeEditor( scriptNode )"

	def _updateFromContext( self, modifiedItems ) :

		self.__lazyUpdateFromContext()

	def _updateFromSettings( self, plug ) :

		if plug in ( self.settings()["section"], self.settings()["tabGroup"], self.settings()["columnFilter"] ) :
			self.__updateColumnsAndSections()

	@GafferUI.LazyMethod( deferUntilVisible = False, deferUntilPlaybackStops = True )
	def __lazyUpdateFromContext( self ) :

		self.__pathListing.getPath().setContext( self.context() )

	@GafferUI.LazyMethod()
	def __updateColumnsAndSections( self ) :

		tabGroup = self.settings()["tabGroup"].getValue()
		filterActive = self.settings()._columnFilterActive()
		rootPath = self.__pathListing.getPath()

		sectionCreators = collections.OrderedDict()
		for groupKey, sections in self.__columnRegistry.items() :
			if IECore.StringAlgo.match( tabGroup, groupKey ) :
				for section, creators in sections.items() :
					sectionCreators.setdefault( section, [] ).extend( [
						c for c in creators.values()
						if not filterActive or self.settings()._columnVisible( self.__acquireColumn( c, section ), rootPath )
					] )

		sectionNames = [ s for s, creators in sectionCreators.items() if creators or not filterActive ]
		if "All" not in sectionNames and len( sectionNames ) > 1 :
			sectionNames.append( "All" )

		Gaffer.Metadata.registerValue( self.settings()["section"], "sectionPlugValueWidget:sections", IECore.StringVectorData( sectionNames ), persistent = False )

		currentSection = self.settings()["section"].getValue()
		sectionColumns = []
		for creators in sectionCreators.values() if currentSection == "All" else [ sectionCreators.get( currentSection, [] ) ] :
			sectionColumns += [ self.__acquireColumn( c, currentSection ) for c in creators ]

		self.__pathListing.setColumns( [ self.__locationNameColumn, self.__visibilityColumn ] + sectionColumns )

	def __acquireColumn( self, columnCreator, section ) :

		column = self.__columnCache.get( ( columnCreator, section ) )
		if column is None :
			column = columnCreator( self.settings()["__adaptedIn"], self.settings()["editScope"] )
			self.__columnCache[ ( columnCreator, section ) ] = column

		return column

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
	"layout:customWidget:spacer:index", 5,

	plugs = {

		"*" : {

			"label" : "",

		},

		"tabGroup" : {

			"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",
			"layout:width" : 100,

		},

		"section" : {

			"plugValueWidget:type" : "GafferSceneUI.SceneEditor._SectionPlugValueWidget",

		},

		"setFilter" : {

			"layout:divider" : True,

		},

		"editScope" : {

			"plugValueWidget:type" : "GafferUI.EditScopeUI.EditScopePlugValueWidget",
			"layout:width" : 130,

		},

	}

)

class _Spacer( GafferUI.Spacer ) :

	def __init__( self, settingsNode, **kw ) :

		GafferUI.Spacer.__init__( self, imath.V2i( 0 ) )

AttributeEditor._Spacer = _Spacer
