##########################################################################
#
#  Copyright (c) 2026, Cinesite VFX Ltd. All rights reserved.
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
import imath

import IECore

import Gaffer
import GafferUI
import GafferScene
import GafferSceneUI

from . import _GafferSceneUI

class LightLinkingEditor( GafferSceneUI.SceneEditor ) :

	class Settings( GafferSceneUI.SceneEditor.Settings ) :

		def __init__( self ) :

			GafferSceneUI.SceneEditor.Settings.__init__( self, withHierarchyFilter = True )

			self["editScope"] = Gaffer.Plug()

			self["__lightsSetFilter"] = GafferScene.SetFilter()
			self["__lightsSetFilter"]["setExpression"].setValue( "__lights" )

			self["__isolateLights"] = GafferScene.Isolate()
			self["__isolateLights"]["in"].setInput( self["__adaptedIn"] )
			self["__isolateLights"]["filter"].setInput( self["__lightsSetFilter"]["out"] )

			self["__linkedLightsSetFilter"] = GafferScene.SetFilter()

			self["__isolateLightsLinkedToSelection"] = GafferScene.Isolate()
			self["__isolateLightsLinkedToSelection"]["in"].setInput( self["__isolateLights"]["out"] )
			self["__isolateLightsLinkedToSelection"]["filter"].setInput( self["__linkedLightsSetFilter"]["out"] )

			self["__lightsAndFiltersSetFilter"] = GafferScene.SetFilter()
			self["__lightsAndFiltersSetFilter"]["setExpression"].setValue( "__lights __lightFilters" )

			self["__onlyObjects"] = GafferScene.Prune()
			self["__onlyObjects"]["in"].setInput( self["__filteredIn"] )
			self["__onlyObjects"]["filter"].setInput( self["__lightsAndFiltersSetFilter"]["out"] )

			self["__lightsHierarchyFilter"] = GafferSceneUI.SceneEditor._HierarchyFilter()
			self["__lightsHierarchyFilter"]["in"].setInput( self["__isolateLightsLinkedToSelection"]["out"] )

			self["__lightFiltersSetFilter"] = GafferScene.SetFilter()
			self["__lightFiltersSetFilter"]["setExpression"].setValue( "__lightFilters" )

			self["__isolateLightFilters"] = GafferScene.Isolate()
			self["__isolateLightFilters"]["in"].setInput( self["__adaptedIn"] )
			self["__isolateLightFilters"]["filter"].setInput( self["__lightFiltersSetFilter"]["out"] )

			self["__lightFilterHierarchyFilter"] = GafferSceneUI.SceneEditor._HierarchyFilter()
			self["__lightFilterHierarchyFilter"]["in"].setInput( self["__isolateLightFilters"]["out"] )

			Gaffer.PlugAlgo.promoteWithName( self["__lightsHierarchyFilter"]["filter"], "lightsFilter" )
			Gaffer.PlugAlgo.promoteWithName( self["__lightsHierarchyFilter"]["setFilter"], "lightsSetFilter" )

			Gaffer.PlugAlgo.promoteWithName( self["__lightFilterHierarchyFilter"]["filter"], "lightFiltersFilter" )
			Gaffer.PlugAlgo.promoteWithName( self["__lightFilterHierarchyFilter"]["setFilter"], "lightFiltersSetFilter" )

			self["onlyLinkedToSelection"] = Gaffer.BoolPlug()
			self["__isolateLightsLinkedToSelection"]["enabled"].setInput( self["onlyLinkedToSelection"] )

			self["setsFilter"] = Gaffer.StringPlug()

	IECore.registerRunTimeTyped( Settings, typeName = "GafferSceneUI::LightLinkingEditor::Settings" )

	def __init__( self, scriptNode, **kw ) :

		column = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, borderWidth = 4, spacing = 4 )

		GafferSceneUI.SceneEditor.__init__( self, column, scriptNode, **kw )

		with column :

			with GafferUI.SplitContainer( GafferUI.SplitContainer.Orientation.Horizontal ) :

				with GafferUI.TabbedContainer() :

					with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing = 4, parenting = { "label" : "Lights" } ) :

						with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :

							GafferUI.PlugLayout(
								self.settings(),
								orientation = GafferUI.ListContainer.Orientation.Horizontal,
								rootSection = "Lights"
							)

							GafferUI.Spacer( size = imath.V2i( 1, 24 ), maximumSize = imath.V2i( 1, 24 ) )

							GafferUI.PlugLayout(
								self.settings(),
								orientation = GafferUI.ListContainer.Orientation.Horizontal,
								rootSection = "LightsAndSets"
							)

						self.__lightsPathListing = GafferUI.PathListingWidget(
							GafferScene.ScenePath( self.settings()["__lightsHierarchyFilter"]["out"], self.context(), "/" ),
							columns = [ _GafferSceneUI._LightEditorLocationNameColumn() ],
							selectionMode = GafferUI.PathListingWidget.SelectionMode.Rows,
							displayMode = GafferUI.PathListingWidget.DisplayMode.Tree,
							horizontalScrollMode = GafferUI.ScrollMode.Automatic
						)
						self.__lightsPathListing.setSortable( False )
						self.__lightsPathListing.setDragPointer( "objects" )

					with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing = 4, parenting = { "label" : "Sets" } ) :

						with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :

							GafferUI.PlugLayout(
								self.settings(),
								orientation = GafferUI.ListContainer.Orientation.Horizontal,
								rootSection = "Sets"
							)

							GafferUI.Spacer( size = imath.V2i( 1, 24 ), maximumSize = imath.V2i( 1, 24 ) )

							GafferUI.PlugLayout(
								self.settings(),
								orientation = GafferUI.ListContainer.Orientation.Horizontal,
								rootSection = "LightsAndSets"
							)

							self.__setSearchFilter = _GafferSceneUI._SetEditor.SearchFilter()

						self.__setsPathListing = GafferUI.PathListingWidget(
							_GafferSceneUI._SetEditor.SetPath( self.settings()["__isolateLightsLinkedToSelection"]["out"], self.context(), "/", filter = Gaffer.CompoundPathFilter( [ self.__setSearchFilter, _GafferSceneUI._SetEditor.EmptySetFilter( scriptNode ) ] ) ),
							columns = [ _GafferSceneUI._SetEditor.SetNameColumn() ],
							selectionMode = GafferUI.PathListingWidget.SelectionMode.Rows,
							displayMode = GafferUI.PathListingWidget.DisplayMode.Tree,
						)
						self.__setsPathListing.setSortable( False )
						self.__setsPathListing.dragBeginSignal().connectFront( Gaffer.WeakMethod( self.__setsDragBegin ) )

				with GafferUI.TabbedContainer() :

					with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing = 4, parenting = { "label" : "Objects" } ) :

						with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :

							GafferUI.PlugLayout(
								self.settings(),
								orientation = GafferUI.ListContainer.Orientation.Horizontal,
								rootSection = "Filter",
							)

							GafferUI.Spacer( size = imath.V2i( 1, 24 ), maximumSize = imath.V2i( 1, 24 ) )

							GafferUI.PlugLayout(
								self.settings(),
								orientation = GafferUI.ListContainer.Orientation.Horizontal,
								rootSection = "ObjectsAndLightFilters"
							)

						self.__commonObjectColumns = [
							GafferUI.PathListingWidget.StandardColumn( "Name", "name", GafferUI.PathColumn.SizeMode.Stretch ),
							self.__attributeColumn( "linkedLights", self.settings()["__adaptedIn"], self.settings()["editScope"] ),
							self.__attributeColumn( "linkedLights:exclusions", self.settings()["__adaptedIn"], self.settings()["editScope"] ),
							self.__attributeColumn( "shadowedLights", self.settings()["__adaptedIn"], self.settings()["editScope"] ),
							self.__attributeColumn( "shadowedLights:exclusions", self.settings()["__adaptedIn"], self.settings()["editScope"] ),
						]

						self.__objectsPathListing = GafferUI.PathListingWidget(
							GafferScene.ScenePath( self.settings()["__onlyObjects"]["out"], self.context(), "/" ),
							columns = self.__commonObjectColumns,
							selectionMode = GafferUI.PathListingWidget.SelectionMode.Cells,
							displayMode = GafferUI.PathListingWidget.DisplayMode.Tree,
							horizontalScrollMode = GafferUI.ScrollMode.Automatic
						)
						self.__objectsPathListing.setSortable( False )
						GafferSceneUI.Private.InspectorColumn.connectToDragBeginSignal( self.__objectsPathListing )

					with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing = 4, parenting = { "label" : "Light Filters" } ) :

						with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :

							GafferUI.PlugLayout(
								self.settings(),
								orientation = GafferUI.ListContainer.Orientation.Horizontal,
								rootSection = "LightFilters",
							)

							GafferUI.Spacer( size = imath.V2i( 1, 24 ), maximumSize = imath.V2i( 1, 24 ) )

							GafferUI.PlugLayout(
								self.settings(),
								orientation = GafferUI.ListContainer.Orientation.Horizontal,
								rootSection = "ObjectsAndLightFilters"
							)

						self.__commonLightFilterColumns = [
							_GafferSceneUI._LightEditorLocationNameColumn( GafferUI.PathColumn.SizeMode.Stretch ),
							self.__attributeColumn( "filteredLights", self.settings()["__adaptedIn"], self.settings()["editScope"] ),
							self.__attributeColumn( "filteredLights:exclusions", self.settings()["__adaptedIn"], self.settings()["editScope"] ),
						]

						self.__lightFiltersPathListing = GafferUI.PathListingWidget(
							GafferScene.ScenePath( self.settings()["__lightFilterHierarchyFilter"]["out"], self.context(), "/" ),
							columns = self.__commonLightFilterColumns,
							selectionMode = GafferUI.PathListingWidget.SelectionMode.Cells,
							displayMode = GafferUI.PathListingWidget.DisplayMode.Tree,
							horizontalScrollMode = GafferUI.ScrollMode.Automatic
						)
						self.__lightFiltersPathListing.setSortable( False )
						GafferSceneUI.Private.InspectorColumn.connectToDragBeginSignal( self.__lightFiltersPathListing )

			self.__lightsSelectionChangedConnection = self.__lightsPathListing.selectionChangedSignal().connect(
				Gaffer.WeakMethod( self.__lightsSelectionChanged )
			)
			self.__objectsSelectionChangedConnection = self.__objectsPathListing.selectionChangedSignal().connect(
				Gaffer.WeakMethod( self.__objectsOrLightFiltersSelectionChanged )
			)
			self.__lightFiltersSelectionChangedConnection = self.__lightFiltersPathListing.selectionChangedSignal().connect(
				Gaffer.WeakMethod( self.__objectsOrLightFiltersSelectionChanged )
			)

			self.__lightsPathListing.columnContextMenuSignal().connect( Gaffer.WeakMethod( self.__columnContextMenuSignal ) )
			self.__setsPathListing.columnContextMenuSignal().connect( Gaffer.WeakMethod( self.__columnContextMenuSignal ) )
			self.__objectsPathListing.columnContextMenuSignal().connect( Gaffer.WeakMethod( self.__columnContextMenuSignal ) )

			self.__lightsPathListing.keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPressSignal ) )
			self.__setsPathListing.keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPressSignal ) )
			self.__objectsPathListing.keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPressSignal ) )
			self.__lightFiltersPathListing.keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPressSignal ) )

		self.__selectedPathsChangedConnection = GafferSceneUI.ScriptNodeAlgo.selectedPathsChangedSignal( scriptNode ).connect(
			Gaffer.WeakMethod( self.__selectedPathsChanged )
		)

		self.__linkedToSelectionFilterPaths = IECore.PathMatcher()

		self.settings()["__onlyObjects"].plugDirtiedSignal().connect( Gaffer.WeakMethod( self.__objectsPlugDirtied ) )

		self._updateFromSet()
		self.__transferSelectionFromScriptNode()

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

		return self.__lightsPathListing

	def __repr__( self ) :

		return "GafferSceneUI.LightLinkingEditor( scriptNode )"

	def _updateFromContext( self, modifiedItems ) :

		self.__lazyUpdateFromContext()

	def _updateFromSettings( self, plug ) :

		if plug == self.settings()["setsFilter"] :
			self.__setSearchFilter.setMatchPattern( plug.getValue() )
		elif plug == self.settings()["onlyLinkedToSelection"] :
			self.__lazyUpdateLinkedLightsSetFilter()

	@classmethod
	def __attributeColumn( cls, attributeName, scene, editScope, columnName = None ) :

		label = Gaffer.Metadata.value( "attribute:" + attributeName, "columnLayout:label" ) or Gaffer.Metadata.value( "attribute:" + attributeName, "label" )
		if not columnName :
			columnName = label or attributeName

		toolTip = "<h3>{}</h3> Attribute : <code>{}</code>".format( label or columnName, attributeName )
		description = Gaffer.Metadata.value( "attribute:" + attributeName, "description" )
		if description :
			## \todo PathListingWidget's PathModel should be handling this instead.
			toolTip += GafferUI.DocumentationAlgo.markdownToHTML( description )

		return GafferSceneUI.Private.InspectorColumn(
			GafferSceneUI.Private.AttributeInspector( scene, editScope, attributeName ),
			columnName,
			toolTip
		)

	@GafferUI.LazyMethod( deferUntilVisible = False, deferUntilPlaybackStops = True )
	def __lazyUpdateFromContext( self ) :

		self.__lightsPathListing.getPath().setContext( self.context() )
		self.__setsPathListing.getPath().setContext( self.context() )
		self.__objectsPathListing.getPath().setContext( self.context() )
		self.__lightFiltersPathListing.getPath().setContext( self.context() )

	def __selectedPathsChanged( self, scriptNode ) :

		self.__transferSelectionFromScriptNode()

	def __lightsSelectionChanged( self, pathListing ) :

		assert( pathListing is self.__lightsPathListing )

		with Gaffer.Signals.BlockedConnection( self.__selectedPathsChangedConnection ) :
			GafferSceneUI.ScriptNodeAlgo.setSelectedPaths( self.scriptNode(), pathListing.getSelection() )

		with Gaffer.Signals.BlockedConnection( self.__objectsSelectionChangedConnection ) :
			self.__objectsPathListing.setSelection(
				[IECore.PathMatcher()] * ( len( self.__objectsPathListing.getColumns() ) )
			)
		with Gaffer.Signals.BlockedConnection( self.__lightFiltersSelectionChangedConnection ) :
			self.__lightFiltersPathListing.setSelection(
				[IECore.PathMatcher()] * ( len( self.__lightFiltersPathListing.getColumns() ) )
			)

	def __objectsOrLightFiltersSelectionChanged( self, pathListing ) :

		assert( pathListing in ( self.__objectsPathListing, self.__lightFiltersPathListing ) )

		with Gaffer.Signals.BlockedConnection( self.__selectedPathsChangedConnection ) :
			GafferSceneUI.ScriptNodeAlgo.setSelectedPaths( self.scriptNode(), pathListing.getSelection()[0] )

		with Gaffer.Signals.BlockedConnection( self.__lightsSelectionChangedConnection ) :
			self.__lightsPathListing.setSelection( IECore.PathMatcher() )

		if pathListing == self.__objectsPathListing :
			with Gaffer.Signals.BlockedConnection( self.__lightFiltersSelectionChangedConnection ) :
				self.__lightFiltersPathListing.setSelection(
					[IECore.PathMatcher()] * ( len( self.__lightFiltersPathListing.getColumns() ) )
				)
		else :
			with Gaffer.Signals.BlockedConnection( self.__objectsSelectionChangedConnection ) :
				self.__objectsPathListing.setSelection(
					[IECore.PathMatcher()] * ( len( self.__objectsPathListing.getColumns() ) )
				)

		# Accumulate selection across all columns so selecting
		# only cells in non-name columns doesn't cause the filter
		# to clear.
		selection = IECore.PathMatcher()
		for s in pathListing.getSelection() :
			selection.addPaths( s )

		self.__linkedToSelectionFilterPaths = selection
		self.__lazyUpdateLinkedLightsSetFilter()

	@GafferUI.LazyMethod( deferUntilPlaybackStops = True )
	def __transferSelectionFromScriptNode( self ) :

		selectedPaths = GafferSceneUI.ScriptNodeAlgo.getSelectedPaths( self.scriptNode() )
		with Gaffer.Signals.BlockedConnection( self.__lightsSelectionChangedConnection ) :
			self.__lightsPathListing.setSelection( selectedPaths, scrollToFirst = True )
		with Gaffer.Signals.BlockedConnection( self.__objectsSelectionChangedConnection ) :
			self.__objectsPathListing.setSelection(
				[selectedPaths] + ( [IECore.PathMatcher()] * ( len( self.__objectsPathListing.getColumns() ) - 1 ) ), scrollToFirst = True
			)
		with Gaffer.Signals.BlockedConnection( self.__lightFiltersSelectionChangedConnection ) :
			self.__lightFiltersPathListing.setSelection(
				[selectedPaths] + ( [IECore.PathMatcher()] * ( len( self.__lightFiltersPathListing.getColumns() ) - 1 ) ), scrollToFirst = True
			)

		self.__linkedToSelectionFilterPaths = selectedPaths
		self.__updateLinkedLightsSetFilter()

	@GafferUI.LazyMethod()
	def __lazyUpdateLinkedLightsSetFilter( self ) :

		self.__updateLinkedLightsSetFilter()

	def __updateLinkedLightsSetFilter( self ) :

		if not self.settings()["onlyLinkedToSelection"].getValue() or self.scene() is None :
			return

		with self.context() :
			self.__updateLinkedLightsSetFilterInBackground(
				self.__linkedToSelectionFilterPaths.paths(),
				[
					( self.__objectsPathListing.getPath().getScene(), "linkedLights", "defaultLights" ),
					( self.__lightFiltersPathListing.getPath().getScene(), "filteredLights", "" ),
				]
			)

	@GafferUI.BackgroundMethod()
	def __updateLinkedLightsSetFilterInBackground( self, paths, scenesAndAttributes ) :

		if not paths :
			# When nothing is selected, fall back to displaying all lights
			# in the __lightsPathListing.
			return "__lights"

		linkingExpressions = set()
		match = False
		for path in paths :
			fullAttributes = self.settings()["__adaptedIn"].fullAttributes( path )

			for scenePlug, attributeName, defaultValue in scenesAndAttributes :
				if not scenePlug.exists( path ) :
					continue

				match = True
				inclusions = fullAttributes.get( attributeName, IECore.StringData( defaultValue ) ).value
				if inclusions and not inclusions.isspace() :
					exclusions = fullAttributes.get( f"{attributeName}:exclusions", IECore.StringData( "" ) ).value
					if exclusions and not exclusions.isspace() :
						linkingExpressions.add( f"({inclusions}) - ({exclusions})" )
					else :
						linkingExpressions.add( f"({inclusions})" )

				break

		return " ".join( linkingExpressions ) if match else None

	@__updateLinkedLightsSetFilterInBackground.plug
	def __updateLinkedLightsSetFilterInBackgroundPlug( self ) :

		return self.settings()["__adaptedIn"]

	@__updateLinkedLightsSetFilterInBackground.postCall
	def __updateLinkedLightsSetFilterInBackgroundPostCall( self, backgroundResult ) :

		if isinstance( backgroundResult, Exception ) or backgroundResult is None :
			return

		self.settings()["__linkedLightsSetFilter"]["setExpression"].setValue( backgroundResult )

	def __objectsPlugDirtied( self, plug ) :

		if plug == self.settings()["__onlyObjects"]["out"]["attributes"] :
			self.__lazyUpdateLinkedLightsSetFilter()

	def __columnContextMenuSignal( self, column, pathListing, menuDefinition ) :

		selection = pathListing.getSelection()
		if pathListing == self.__lightsPathListing :

			if menuDefinition.size() :
				menuDefinition.append( "/__lightLinkingEditorCopyDivider", { "divider" : True } )

			menuDefinition.append(
				"Copy Path{}".format( "" if selection.size() == 1 else "s" ),
				{
					"command" : functools.partial( Gaffer.WeakMethod( self.__copyPaths ), selection ),
					"active" : not selection.isEmpty(),
					"shortCut" : "Ctrl+C"
				}
			)

			menuDefinition.append( "/__lightLinkingEditorSelectDivider", { "divider" : True } )

			menuDefinition.append(
				"Select Linked Objects",
				{
					"command" : Gaffer.WeakMethod( self.__selectLinkedObjects )
				}
			)

		elif pathListing == self.__objectsPathListing :

			columns = pathListing.getColumns()
			if columns.index( column ) != 0 :
				return

			if menuDefinition.size() :
				menuDefinition.append( "/__lightLinkingEditorSelectDivider", { "divider" : True } )

			menuDefinition.append(
				"Select Linked Lights",
				{
					"command" : Gaffer.WeakMethod( self.__selectLinkedLights )
				}
			)

		elif pathListing == self.__setsPathListing :

			selectedSetNames = self.__selectedSetNames()

			menuDefinition.append(
				"/Copy Set Name{}".format( "" if len( selectedSetNames ) == 1 else "s" ),
				{
					"command" : Gaffer.WeakMethod( self.__copySelectedSetNames ),
					"active" : len( selectedSetNames ) > 0,
					"shortCut" : "Ctrl+C"
				}
			)

			menuDefinition.append(
				"/Copy Set Members",
				{
					"command" : Gaffer.WeakMethod( self.__copySetMembers ),
					"active" : len( selectedSetNames ) > 0,
					"shortCut" : "Ctrl+Shift+C"
				}
			)

			menuDefinition.append(
				"/Select Set Members",
				{
					"command" : Gaffer.WeakMethod( self.__selectSetMembers ),
					"active" : len( selectedSetNames ) > 0,
				}
			)

	def __keyPressSignal( self, pathListing, event ) :

		if pathListing == self.__lightsPathListing :

			if event.key == "C" and event.modifiers == event.Modifiers.Control :
				self.__copyPaths( pathListing.getSelection() )
				return True

		elif pathListing == self.__setsPathListing :

			if event.key == "C" and event.modifiers == event.Modifiers.Control :
				self.__copySelectedSetNames()
				return True
			elif event.key == "C" and event.modifiers == event.Modifiers.ShiftControl :
				self.__copySetMembers()
				return True

		if event.key == "F" :
			self.__frameSelectedPaths( pathListing )
			return True

		return False

	def __copyPaths( self, selection ) :

		selection = selection[0] if isinstance( selection, list ) else selection
		if not selection.isEmpty() :
			data = IECore.StringVectorData( selection.paths() )
			self.scriptNode().ancestor( Gaffer.ApplicationRoot ).setClipboardContents( data )

	def __frameSelectedPaths( self, pathListing ) :

		selection = pathListing.getSelection()
		selection = selection[0] if isinstance( selection, list ) else selection
		if not selection.isEmpty() :
			pathListing.expandTo( selection )
			pathListing.scrollToFirst( selection )

	def __selectLinkedObjects( self, *unused ) :

		selectedLights = self.__lightsPathListing.getSelection()

		dialogue = GafferUI.BackgroundTaskDialogue( "Selecting Linked Objects" )
		with self.context() :
			result = dialogue.waitForBackgroundTask(
				functools.partial(
					GafferScene.SceneAlgo.linkedObjects,
					self.settings()["__adaptedIn"],
					selectedLights
				)
			)

		if not isinstance( result, Exception ) :
			self.__objectsPathListing.setSelection(
				[result] + ( [IECore.PathMatcher()] * ( len( self.__objectsPathListing.getColumns() ) - 1 ) ), scrollToFirst = True
			)

	def __selectLinkedLights( self, *unused ) :

		selectedObjects = self.__objectsPathListing.getSelection()[0]

		dialogue = GafferUI.BackgroundTaskDialogue( "Selecting Linked Lights" )
		with self.context() :
			result = dialogue.waitForBackgroundTask(
				functools.partial(
					GafferScene.SceneAlgo.linkedLights,
					self.settings()["__adaptedIn"],
					selectedObjects
				)
			)

		if not isinstance( result, Exception ) :
			self.__lightsPathListing.setSelection( result, scrollToFirst = True )

	def __selectedSetNames( self ) :

		selection = self.__setsPathListing.getSelection()
		path = self.__setsPathListing.getPath().copy()
		result = []
		for p in selection.paths() :
			path.setFromString( p )
			setName = path.property( "setPath:setName" )
			if setName is not None :
				result.append( setName )

		return result

	def __setsDragBegin( self, widget, event ) :

		path = self.__setsPathListing.pathAt( imath.V2f( event.line.p0.x, event.line.p0.y ) )
		selection = self.__setsPathListing.getSelection()
		setNames = []
		if selection.match( str( path ) ) & IECore.PathMatcher.Result.ExactMatch :
			setNames = self.__selectedSetNames()
		else :
			setName = path.property( "setPath:setName" )
			if setName is not None :
				setNames.append( setName )

		GafferUI.Pointer.setCurrent( "sets" )
		return IECore.StringVectorData( setNames )


	def __copySelectedSetNames( self, *unused ) :

		self.scriptNode().ancestor( Gaffer.ApplicationRoot ).setClipboardContents(
			IECore.StringVectorData( self.__selectedSetNames() )
		)

	def __getSetMembers( self, setNames, *unused ) :

		result = IECore.PathMatcher()
		with Gaffer.Context( self.context() ) :
			for setName in setNames :
				result.addPaths( self.settings()["__adaptedIn"].set( setName ).value )

		return result

	def __selectSetMembers( self, *unused ) :

		GafferSceneUI.ScriptNodeAlgo.setSelectedPaths( self.scriptNode(), self.__getSetMembers( self.__selectedSetNames() ) )

	def __copySetMembers( self, *unused ) :

		data = self.__getSetMembers( self.__selectedSetNames() ).paths()
		self.scriptNode().ancestor( Gaffer.ApplicationRoot ).setClipboardContents( IECore.StringVectorData( data ) )

GafferUI.Editor.registerType( "LightLinkingEditor", LightLinkingEditor )

##########################################################################
# Metadata controlling the settings UI
##########################################################################

Gaffer.Metadata.registerNode(

	LightLinkingEditor.Settings,

	plugs = {

		"*" : {

			"label" : "",

		},

		"lightsFilter" : {

			"description" :
			"""
			Filters the input scene to isolate locations with matching names.
			The filter may contain any of Gaffer's standard wildcards, and may
			either be used to match individual location names or entire paths.

			Examples
			--------

			- `building` : Matches any location in the scene which has the
			  text `building` anywhere in its name.
			- `/cityA/.../building*` : Matches only locations within `cityA`
			  whose name starts with `building`.
			""",

			"plugValueWidget:type" : "GafferUI.TogglePlugValueWidget",
			"togglePlugValueWidget:image:on" : "searchOn.png",
			"togglePlugValueWidget:image:off" : "search.png",
			# We need a non-default value to toggle to, so that the first
			# toggling can highlight the icon. `*` seems like a reasonable value
			# since it has no effect on the filtering, and hints that wildcards
			# are available.
			"togglePlugValueWidget:defaultToggleValue" : "*",
			"stringPlugValueWidget:placeholderText" : "Filter Lights...",
			"layout:section" : "Lights"

		},

		"lightsSetFilter" : {

			"description" :
			"""
			Filters the input scene to isolate locations belonging to specific
			sets.
			""",

			"label" : "",
			"plugValueWidget:type" : "GafferSceneUI.SceneEditor._SetFilterPlugValueWidget",
			"layout:section" : "Lights"

		},

		"setsFilter" : {

			"description" :
			"""
			Filters the displayed sets by name. Accepts standard wildcards such as `*` and `?`.
			""",

			"plugValueWidget:type" : "GafferUI.TogglePlugValueWidget",
			"togglePlugValueWidget:image:on" : "searchOn.png",
			"togglePlugValueWidget:image:off" : "search.png",
			"togglePlugValueWidget:defaultToggleValue" : "*",
			"togglePlugValueWidget:customWidgetType" : "GafferSceneUI.SetEditor._FilterPlugValueWidget",
			"stringPlugValueWidget:placeholderText" : "Filter Sets...",
			"layout:section" : "Sets"

		},

		"onlyLinkedToSelection" : {

			"description" : "Only show lights and sets containing lights linked to the selected objects and light filters.",
			"boolPlugValueWidget:labelVisible" : True,
			"layout:section" : "LightsAndSets",

		},

		"filter" : {

			"stringPlugValueWidget:placeholderText" : "Filter Objects...",

		},

		"lightFiltersFilter" : {

			"description" :
			"""
			Filters the input scene to isolate locations with matching names.
			The filter may contain any of Gaffer's standard wildcards, and may
			either be used to match individual location names or entire paths.

			Examples
			--------

			- `building` : Matches any location in the scene which has the
			  text `building` anywhere in its name.
			- `/cityA/.../building*` : Matches only locations within `cityA`
			  whose name starts with `building`.
			""",

			"plugValueWidget:type" : "GafferUI.TogglePlugValueWidget",
			"togglePlugValueWidget:image:on" : "searchOn.png",
			"togglePlugValueWidget:image:off" : "search.png",
			# We need a non-default value to toggle to, so that the first
			# toggling can highlight the icon. `*` seems like a reasonable value
			# since it has no effect on the filtering, and hints that wildcards
			# are available.
			"togglePlugValueWidget:defaultToggleValue" : "*",
			"stringPlugValueWidget:placeholderText" : "Filter Light Filters...",
			"layout:section" : "LightFilters"

		},

		"lightFiltersSetFilter" : {

			"description" :
			"""
			Filters the input scene to isolate locations belonging to specific
			sets.
			""",

			"label" : "",
			"plugValueWidget:type" : "GafferSceneUI.SceneEditor._SetFilterPlugValueWidget",
			"layout:section" : "LightFilters"

		},

		"editScope" : {

			"plugValueWidget:type" : "GafferUI.EditScopeUI.EditScopePlugValueWidget",
			"layout:width" : 130,
			"layout:section" : "ObjectsAndLightFilters",

		},

	}

)
