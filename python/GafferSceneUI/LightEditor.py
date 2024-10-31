##########################################################################
#
#  Copyright (c) 2021, Cinesite VFX Ltd. All rights reserved.
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
import IECoreScene

import Gaffer
import GafferUI
import GafferScene
import GafferSceneUI

from . import _GafferSceneUI

from Qt import QtWidgets

class LightEditor( GafferSceneUI.SceneEditor ) :

	class Settings( GafferSceneUI.SceneEditor.Settings ) :

		def __init__( self ) :

			GafferSceneUI.SceneEditor.Settings.__init__( self )

			self["attribute"] = Gaffer.StringPlug( defaultValue = "light" )
			self["section"] = Gaffer.StringPlug( defaultValue = "" )
			self["editScope"] = Gaffer.Plug()

	IECore.registerRunTimeTyped( Settings, typeName = "GafferSceneUI::LightEditor::Settings" )

	def __init__( self, scriptNode, **kw ) :

		column = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, borderWidth = 4, spacing = 4 )

		GafferSceneUI.SceneEditor.__init__( self, column, scriptNode, **kw )

		self.__setFilter = _GafferSceneUI._HierarchyViewSetFilter()
		self.__setFilter.setScene( self.settings()["in"] )
		self.__setFilter.setSetNames( [ "__lights", "__lightFilters" ] )

		with column :

			GafferUI.PlugLayout(
				self.settings(),
				orientation = GafferUI.ListContainer.Orientation.Horizontal,
				rootSection = "Settings"
			)

			self.__pathListing = GafferUI.PathListingWidget(
				Gaffer.DictPath( {}, "/" ), # Temp till we make a ScenePath
				columns = [
					_GafferSceneUI._LightEditorLocationNameColumn(),
					_GafferSceneUI._LightEditorMuteColumn(
						self.settings()["in"],
						self.settings()["editScope"]
					),
					_GafferSceneUI._LightEditorSetMembershipColumn(
						self.settings()["in"],
						self.settings()["editScope"],
						"soloLights",
						"Solo"
					),
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

	@classmethod
	def __parseParameter( cls, parameter ) :

		if isinstance( parameter, str ) :
			shader = ""
			param = parameter
			if "." in parameter :
				shader, dot, param = parameter.partition( "." )
			return IECoreScene.ShaderNetwork.Parameter( shader, param )
		else :
			assert( isinstance( parameter, IECoreScene.ShaderNetwork.Parameter ) )
			return parameter

	# Registers a parameter to be available for editing. `rendererKey` is a pattern
	# that will be matched against `self.settings()["attribute"]` to determine if
	# the column should be shown.
	# \todo Deprecate in favor of method below.
	@classmethod
	def registerParameter( cls, rendererKey, parameter, section = None, columnName = None ) :

		parameter = cls.__parseParameter( parameter )

		GafferSceneUI.LightEditor.registerColumn(
			rendererKey,
			".".join( x for x in [ parameter.shader, parameter.name ] if x ),
			lambda scene, editScope : GafferSceneUI.Private.InspectorColumn(
				GafferSceneUI.Private.ParameterInspector( scene, editScope, rendererKey, parameter ),
				columnName if columnName is not None else ""
			),
			section
		)

	# Registers a parameter to be available for editing. `rendererKey` is a pattern
	# that will be matched against `self.settings()["attribute"]` to determine if
	# the column should be shown. `attribute` is the attribute holding the shader that
	# will be edited. If it is `None`, the attribute will be the same as `rendererKey`.
	@classmethod
	def registerShaderParameter( cls, rendererKey, parameter, shaderAttribute = None, section = None, columnName = None ) :

		parameter = cls.__parseParameter( parameter )

		shaderAttribute = shaderAttribute if shaderAttribute is not None else rendererKey

		GafferSceneUI.LightEditor.registerColumn(
			rendererKey,
			".".join( x for x in [ parameter.shader, parameter.name ] if x ),
			lambda scene, editScope : GafferSceneUI.Private.InspectorColumn(
				GafferSceneUI.Private.ParameterInspector( scene, editScope, shaderAttribute, parameter ),
				columnName if columnName is not None else ""
			),
			section
		)

	@classmethod
	def registerAttribute( cls, rendererKey, attributeName, section = None ) :

		displayName = attributeName.split( ':' )[-1]
		GafferSceneUI.LightEditor.registerColumn(
			rendererKey,
			attributeName,
			lambda scene, editScope : GafferSceneUI.Private.InspectorColumn(
				GafferSceneUI.Private.AttributeInspector( scene, editScope, attributeName ),
				displayName
			),
			section
		)

	# Registers a column in the Light Editor.
	# `inspectorFunction` is a callable object of the form
	# `inspectorFunction( scene, editScope )` returning a
	# `GafferSceneUI.Private.InspectorColumn` object.
	@classmethod
	def registerColumn( cls, rendererKey, columnKey, inspectorFunction, section = None ) :

		assert( isinstance( columnKey, str ) )

		sections = cls.__columnRegistry.setdefault( rendererKey, collections.OrderedDict() )
		section = sections.setdefault( section, collections.OrderedDict() )

		section[columnKey] = inspectorFunction

	# Removes a column from the Light Editor.
	# `rendererKey` should match the value the parameter or attribute was registered with.
	# `columnKey` is the string value of the parameter or attribute name.
	@classmethod
	def deregisterColumn( cls, rendererKey, columnKey, section = None ) :

		assert( isinstance( columnKey, str ) )

		sections = cls.__columnRegistry.get( rendererKey, None )
		if sections is not None and section in sections.keys() and columnKey in sections[section].keys() :
			del sections[section][columnKey]

			if len( sections[section] ) == 0 :
				del sections[section]

	def __repr__( self ) :

		return "GafferSceneUI.LightEditor( scriptNode )"

	def _updateFromContext( self, modifiedItems ) :

		for item in modifiedItems :
			if not item.startswith( "ui:" ) :
				# When the context has changed, the hierarchy of the scene may
				# have too so we should update our PathListingWidget.
				self.__setPathListingPath()
				break

	def _updateFromSettings( self, plug ) :

		if plug in ( self.settings()["section"], self.settings()["attribute"] ) :
			self.__updateColumns()

	@GafferUI.LazyMethod()
	def __updateColumns( self ) :

		attribute = self.settings()["attribute"].getValue()
		currentSection = self.settings()["section"].getValue()

		sectionColumns = []

		for rendererKey, sections in self.__columnRegistry.items() :
			if IECore.StringAlgo.match( attribute, rendererKey ) :
				section = sections.get( currentSection or None, {} )
				sectionColumns += [ c( self.settings()["in"], self.settings()["editScope"] ) for c in section.values() ]

		nameColumn = self.__pathListing.getColumns()[0]
		muteColumn = self.__pathListing.getColumns()[1]
		soloColumn = self.__pathListing.getColumns()[2]
		self.__pathListing.setColumns( [ nameColumn, muteColumn, soloColumn ] + sectionColumns )

	@GafferUI.LazyMethod( deferUntilPlaybackStops = True )
	def __setPathListingPath( self ) :

		# We take a static copy of our current context for use in the ScenePath - this prevents the
		# PathListing from updating automatically when the original context changes, and allows us to take
		# control of updates ourselves in _updateFromContext(), using LazyMethod to defer the calls to this
		# function until we are visible and playback has stopped.
		contextCopy = Gaffer.Context( self.context() )
		self.__setFilter.setContext( contextCopy )
		self.__pathListing.setPath( GafferScene.ScenePath( self.settings()["in"], contextCopy, "/", filter = self.__setFilter ) )

	def __selectedPathsChanged( self, scriptNode ) :

		self.__transferSelectionFromScriptNode()

	def __selectionChanged( self, pathListing ) :

		assert( pathListing is self.__pathListing )

		with Gaffer.Signals.BlockedConnection( self.__selectedPathsChangedConnection ) :
			GafferSceneUI.ScriptNodeAlgo.setSelectedPaths( self.scriptNode(), pathListing.getSelection()[0] )

	@GafferUI.LazyMethod( deferUntilPlaybackStops = True )
	def __transferSelectionFromScriptNode( self ) :

		selectedPaths = GafferSceneUI.ScriptNodeAlgo.getSelectedPaths( self.scriptNode() )
		with Gaffer.Signals.BlockedConnection( self.__selectionChangedConnection ) :
			selection = [selectedPaths] + ( [IECore.PathMatcher()] * ( len( self.__pathListing.getColumns() ) - 1 ) )
			self.__pathListing.setSelection( selection, scrollToFirst=True )

	def __columnContextMenuSignal( self, column, pathListing, menuDefinition ) :

		columns = pathListing.getColumns()
		columnIndex = -1
		for i in range( 0, len( columns ) ) :
			if column == columns[i] :
				columnIndex = i

		if columnIndex == 0 :
			# Whole light operations

			menuDefinition.append(
				"Select Linked Objects",
				{
					"command" : Gaffer.WeakMethod( self.__selectLinked )
				}
			)

			menuDefinition.append( "/deleteDivider", { "divider" : True } )

			# Filter out a number of scenarios where deleting would be impossible
			# or unintuitive
			deleteEnabled = True
			inputNode = self.settings()["in"].getInput().node()
			editScopeNode = self.editScope()
			if editScopeNode is not None :
				if inputNode != editScopeNode and editScopeNode not in Gaffer.NodeAlgo.upstreamNodes( inputNode ) :
					# Edit scope is downstream of input
					deleteEnabled = False
				elif GafferScene.EditScopeAlgo.prunedReadOnlyReason( editScopeNode ) is not None :
					# Pruning or the edit scope is read only
					deleteEnabled = False
				else :
					with self.context() :
						if not editScopeNode["enabled"].getValue() :
							# Edit scope is disabled
							deleteEnabled = False
						else :
							pruningProcessor = editScopeNode.acquireProcessor( "PruningEdits", createIfNecessary = False )
							if pruningProcessor is not None and not pruningProcessor["enabled"].getValue() :
								# Pruning processor is disabled
								deleteEnabled = False
			else :
				# No edit scope selected
				deleteEnabled = False

			menuDefinition.append(
				"Delete",
				{
					"command" : Gaffer.WeakMethod( self.__deleteLights ),
					"active" : deleteEnabled
				}
			)

	def __selectLinked (self, *unused ) :

		context = self.context()

		dialogue = GafferUI.BackgroundTaskDialogue( "Selecting Linked Objects" )

		# There may be multiple columns with a selection, but we only operate on the name column.
		selectedLights = self.__pathListing.getSelection()[0]

		with context :
			result = dialogue.waitForBackgroundTask(
				functools.partial(
					GafferScene.SceneAlgo.linkedObjects,
					self.settings()["in"],
					selectedLights
				)
			)

		if not isinstance( result, Exception ) :
			GafferSceneUI.ScriptNodeAlgo.setSelectedPaths( self.scriptNode(), result )

	def __deleteLights( self, *unused ) :

		# There may be multiple columns with a selection, but we only operate on the name column.
		selection = self.__pathListing.getSelection()[0]

		editScope = self.editScope()

		with Gaffer.UndoScope( editScope.ancestor( Gaffer.ScriptNode ) ) :
			GafferScene.EditScopeAlgo.setPruned( editScope, selection, True )

GafferUI.Editor.registerType( "LightEditor", LightEditor )

##########################################################################
# Metadata controlling the settings UI
##########################################################################

Gaffer.Metadata.registerNode(

	LightEditor.Settings,

	## \todo Doing spacers with custom widgets is tedious, and we're doing it
	# in all the View UIs. Maybe we could just attach metadata to the plugs we
	# want to add space around, in the same way we use `divider` to add a divider?
	"layout:customWidget:spacer:widgetType", "GafferSceneUI.LightEditor._Spacer",
	"layout:customWidget:spacer:section", "Settings",
	"layout:customWidget:spacer:index", 3,

	plugs = {

		"*" : [

			"label", "",

		],

		"attribute" : [

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
			"layout:width", 100,

		],

		"section" : [

			"plugValueWidget:type", "GafferSceneUI.LightEditor._SectionPlugValueWidget",

		],

		"editScope" : [

			"plugValueWidget:type", "GafferUI.EditScopeUI.EditScopePlugValueWidget",
			"layout:width", 185,

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

		text = values[0]
		text = "Main" if text == "" else text
		for i in range( 0, self._qtWidget().count() ) :
			if self._qtWidget().tabText( i ) == text :
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

			attribute = self.getPlug().node()["attribute"].getValue()

			for rendererKey, sections in LightEditor._LightEditor__columnRegistry.items() :
				if IECore.StringAlgo.match( attribute, rendererKey ) :
					for section in sections.keys() :
						self._qtWidget().addTab( section or "Main" )
		finally :
			self.__ignoreCurrentChanged = False

	def __plugSet( self, plug ) :

		if plug == self.getPlug().node()["attribute"] :
			self.__updateTabs()
			self.__currentChanged( self._qtWidget().currentIndex() )

LightEditor._SectionPlugValueWidget = _SectionPlugValueWidget

class _Spacer( GafferUI.Spacer ) :

	def __init__( self, settingsNode, **kw ) :

		GafferUI.Spacer.__init__( self, imath.V2i( 0 ) )

LightEditor._Spacer = _Spacer
