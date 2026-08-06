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
import inspect

import IECore

import Gaffer
import GafferUI
import GafferScene
import GafferSceneUI

from Qt import QtWidgets

from . import _GafferSceneUI

class LightLinkingEditor( GafferSceneUI.SceneEditor ) :

	class Settings( GafferSceneUI.SceneEditor.Settings ) :

		def __init__( self ) :

			GafferSceneUI.SceneEditor.Settings.__init__( self, withHierarchyFilter = True )

			self["editScope"] = Gaffer.Plug()

			self["mode"] = Gaffer.StringPlug( defaultValue = "append" )
			self["attribute"] = Gaffer.StringPlug( defaultValue = "linkedLights" )

			self["setsFilter"] = Gaffer.StringPlug()
			self["onlyLinkedToSelection"] = Gaffer.BoolPlug()

			self["__lightsSetFilter"] = GafferScene.SetFilter()
			self["__lightsSetFilter"]["setExpression"].setValue( "__lights" )

			self["__isolateLights"] = GafferScene.Isolate()
			self["__isolateLights"]["in"].setInput( self["__adaptedIn"] )
			self["__isolateLights"]["filter"].setInput( self["__lightsSetFilter"]["out"] )

			self["__linkedLightsSetFilter"] = GafferScene.SetFilter()

			self["__isolateLightsLinkedToSelection"] = GafferScene.Isolate()
			self["__isolateLightsLinkedToSelection"]["in"].setInput( self["__isolateLights"]["out"] )
			self["__isolateLightsLinkedToSelection"]["filter"].setInput( self["__linkedLightsSetFilter"]["out"] )
			self["__isolateLightsLinkedToSelection"]["enabled"].setInput( self["onlyLinkedToSelection"] )

			self["__lightsAndFiltersSetFilter"] = GafferScene.SetFilter()
			self["__lightsAndFiltersSetFilter"]["setExpression"].setValue( "__lights __lightFilters" )

			self["__filteredObjects"] = GafferScene.Prune()
			self["__filteredObjects"]["in"].setInput( self["__filteredIn"] )
			self["__filteredObjects"]["filter"].setInput( self["__lightsAndFiltersSetFilter"]["out"] )

			self["__deleteContextVariables"] = Gaffer.DeleteContextVariables()
			self["__deleteContextVariables"].setup( self["__adaptedIn"] )
			self["__deleteContextVariables"]["in"].setInput( self["__adaptedIn"] )
			self["__deleteContextVariables"]["variables"].setValue( "collect:value collect:index" )

			self["__isolateObjects"] = GafferScene.Prune()
			self["__isolateObjects"]["in"].setInput( self["__deleteContextVariables"]["out"] )
			self["__isolateObjects"]["filter"].setInput( self["__lightsAndFiltersSetFilter"]["out"] )

			self["__lightsHierarchyFilter"] = GafferSceneUI.SceneEditor._HierarchyFilter()
			self["__lightsHierarchyFilter"]["in"].setInput( self["__isolateLightsLinkedToSelection"]["out"] )

			self["__lightFiltersSetFilter"] = GafferScene.SetFilter()
			self["__lightFiltersSetFilter"]["setExpression"].setValue( "__lightFilters" )

			self["__isolateLightFilters"] = GafferScene.Isolate()
			self["__isolateLightFilters"]["in"].setInput( self["__deleteContextVariables"]["out"] )
			self["__isolateLightFilters"]["filter"].setInput( self["__lightFiltersSetFilter"]["out"] )

			self["__lightFilterHierarchyFilter"] = GafferSceneUI.SceneEditor._HierarchyFilter()
			self["__lightFilterHierarchyFilter"]["in"].setInput( self["__isolateLightFilters"]["out"] )

			Gaffer.PlugAlgo.promoteWithName( self["__lightsHierarchyFilter"]["filter"], "lightsFilter" )
			Gaffer.PlugAlgo.promoteWithName( self["__lightsHierarchyFilter"]["setFilter"], "lightsSetFilter" )

			Gaffer.PlugAlgo.promoteWithName( self["__lightFilterHierarchyFilter"]["filter"], "lightFiltersFilter" )
			Gaffer.PlugAlgo.promoteWithName( self["__lightFilterHierarchyFilter"]["setFilter"], "lightFiltersSetFilter" )

			self["__linkedLightsAttributeQuery"] = GafferScene.AttributeQuery()
			self["__linkedLightsAttributeQuery"].setup( Gaffer.StringPlug() )
			self["__linkedLightsAttributeQuery"]["location"].setValue( "${collect:value}" )
			self["__linkedLightsAttributeQuery"]["inherit"].setValue( True )
			self["__linkedLightsAttributeQuery"]["attribute"].setValue( "linkedLights" )
			self["__linkedLightsAttributeQuery"]["default"].setValue( "defaultLights" )
			self["__linkedLightsAttributeQuery"]["scene"].setInput( self["__deleteContextVariables"]["out"] )

			self["__excludedLightsAttributeQuery"] = GafferScene.AttributeQuery()
			self["__excludedLightsAttributeQuery"].setup( Gaffer.StringPlug() )
			self["__excludedLightsAttributeQuery"]["location"].setValue( "${collect:value}" )
			self["__excludedLightsAttributeQuery"]["inherit"].setValue( True )
			self["__excludedLightsAttributeQuery"]["attribute"].setValue( "linkedLights:exclusions" )
			self["__excludedLightsAttributeQuery"]["scene"].setInput( self["__deleteContextVariables"]["out"] )

			self["__filteredLightsAttributeQuery"] = GafferScene.AttributeQuery()
			self["__filteredLightsAttributeQuery"].setup( Gaffer.StringPlug() )
			self["__filteredLightsAttributeQuery"]["location"].setValue( "${collect:value}" )
			self["__filteredLightsAttributeQuery"]["inherit"].setValue( True )
			self["__filteredLightsAttributeQuery"]["attribute"].setValue( "filteredLights" )
			self["__filteredLightsAttributeQuery"]["scene"].setInput( self["__deleteContextVariables"]["out"] )

			self["__excludedFilteredLightsAttributeQuery"] = GafferScene.AttributeQuery()
			self["__excludedFilteredLightsAttributeQuery"].setup( Gaffer.StringPlug() )
			self["__excludedFilteredLightsAttributeQuery"]["location"].setValue( "${collect:value}" )
			self["__excludedFilteredLightsAttributeQuery"]["inherit"].setValue( True )
			self["__excludedFilteredLightsAttributeQuery"]["attribute"].setValue( "filteredLights:exclusions" )
			self["__excludedFilteredLightsAttributeQuery"]["scene"].setInput( self["__deleteContextVariables"]["out"] )

			self["__objectsExistenceQuery"] = GafferScene.ExistenceQuery()
			self["__objectsExistenceQuery"]["location"].setValue( "${collect:value}" )
			self["__objectsExistenceQuery"]["scene"].setInput( self["__isolateObjects"]["out"] )

			self["__lightFiltersExistenceQuery"] = GafferScene.ExistenceQuery()
			self["__lightFiltersExistenceQuery"]["location"].setValue( "${collect:value}" )
			self["__lightFiltersExistenceQuery"]["scene"].setInput( self["__isolateLightFilters"]["out"] )

			self["__inclusionsSwitch"] = Gaffer.Switch()
			self["__inclusionsSwitch"].setup( Gaffer.StringPlug() )
			self["__inclusionsSwitch"]["in"].resize( 2 )
			self["__inclusionsSwitch"]["in"][0].setInput( self["__linkedLightsAttributeQuery"]["value"] )
			self["__inclusionsSwitch"]["in"][1].setInput( self["__filteredLightsAttributeQuery"]["value"] )
			self["__inclusionsSwitch"]["index"].setInput( self["__lightFiltersExistenceQuery"]["exists"] )

			self["__exclusionsSwitch"] = Gaffer.Switch()
			self["__exclusionsSwitch"].setup( Gaffer.StringPlug() )
			self["__exclusionsSwitch"]["in"].resize( 2 )
			self["__exclusionsSwitch"]["in"][0].setInput( self["__excludedLightsAttributeQuery"]["value"] )
			self["__exclusionsSwitch"]["in"][1].setInput( self["__excludedFilteredLightsAttributeQuery"]["value"] )
			self["__exclusionsSwitch"]["index"].setInput( self["__lightFiltersExistenceQuery"]["exists"] )

			# This Switch acts as an or of __lightFiltersExistenceQuery.exists and __objectsExistenceQuery.exists
			# enabling __collect when either are true.
			self["__collectEnabledSwitch"] = Gaffer.Switch()
			self["__collectEnabledSwitch"].setup( Gaffer.BoolPlug() )
			self["__collectEnabledSwitch"]["in"].resize( 2 )
			self["__collectEnabledSwitch"]["in"][0].setInput( self["__lightFiltersExistenceQuery"]["exists"] )
			self["__collectEnabledSwitch"]["in"][1].setInput( self["__objectsExistenceQuery"]["exists"] )
			self["__collectEnabledSwitch"]["index"].setInput( self["__objectsExistenceQuery"]["exists"] )

			self["__collect"] = Gaffer.Collect()
			self["__collect"].addInput( Gaffer.StringPlug( "inclusions" ) )
			self["__collect"].addInput( Gaffer.StringPlug( "exclusions" ) )
			self["__collect"]["in"]["inclusions"].setInput( self["__inclusionsSwitch"]["out"] )
			self["__collect"]["in"]["exclusions"].setInput( self["__exclusionsSwitch"]["out"] )
			self["__collect"]["enabled"].setInput( self["__collectEnabledSwitch"]["out"] )

			self["__linkedLightsSetExpressionExpression"] = Gaffer.Expression()
			self["__linkedLightsSetExpressionExpression"].setExpression( inspect.cleandoc(
				"""
				allInclusions = parent["__collect"]["out"]["inclusions"]
				allExclusions = parent["__collect"]["out"]["exclusions"]

				linkingExpressions = set()
				for inclusions, exclusions in zip( allInclusions, allExclusions ) :
					if inclusions and not inclusions.isspace() :
						if exclusions and not exclusions.isspace() :
							linkingExpressions.add( f"({inclusions}) - ({exclusions})" )
						else :
							linkingExpressions.add( f"({inclusions})" )

				parent["__linkedLightsSetFilter"]["setExpression"] = " ".join( linkingExpressions ) if len( allInclusions ) else "__lights"
				"""
			), "python" )

	IECore.registerRunTimeTyped( Settings, typeName = "GafferSceneUI::LightLinkingEditor::Settings" )

	def __init__( self, scriptNode, **kw ) :

		column = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, borderWidth = 4, spacing = 4 )

		GafferSceneUI.SceneEditor.__init__( self, column, scriptNode, **kw )

		with column :

			with GafferUI.SplitContainer( GafferUI.SplitContainer.Orientation.Horizontal ) :

				with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing = 4 ) :

					with GafferUI.TabbedContainer() as self.__lightsAndSetsTabbedContainer :

						with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing = 4, parenting = { "label" : "Lights" } ) as self.__lightsColumn :

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

					with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :

						self.__statusLabel = GafferUI.Label( "" )
						# Ensure a long status text doesn't enforce the minimum width of this side of the SplitContainer.
						self.__statusLabel._qtWidget().setSizePolicy( QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Fixed )
						GafferUI.Spacer( size = imath.V2i( 1, 22 ), maximumSize = imath.V2i( 1, 22 ) )

				with GafferUI.TabbedContainer() as self.__objectsAndLightFiltersTabbedContainer :

					with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing = 4, parenting = { "label" : "Objects" } ) as self.__objectsColumn :

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

						self.__linkedLightsColumn = self.__attributeColumn( "linkedLights", self.settings()["__adaptedIn"], self.settings()["editScope"] )
						self.__linkedLightsExclusionsColumn = self.__attributeColumn( "linkedLights:exclusions", self.settings()["__adaptedIn"], self.settings()["editScope"] )
						self.__shadowedLightsColumn = self.__attributeColumn( "shadowedLights", self.settings()["__adaptedIn"], self.settings()["editScope"] )
						self.__shadowedLightsExclusionsColumn = self.__attributeColumn( "shadowedLights:exclusions", self.settings()["__adaptedIn"], self.settings()["editScope"] )

						self.__objectsPathListing = GafferUI.PathListingWidget(
							GafferScene.ScenePath( self.settings()["__filteredObjects"]["out"], self.context(), "/" ),
							columns = [
								GafferUI.PathListingWidget.StandardColumn( "Name", "name", GafferUI.PathColumn.SizeMode.Stretch ),
								self.__linkedLightsColumn,
								self.__linkedLightsExclusionsColumn,
								self.__shadowedLightsColumn,
								self.__shadowedLightsExclusionsColumn,
							],
							selectionMode = GafferUI.PathListingWidget.SelectionMode.Cells,
							displayMode = GafferUI.PathListingWidget.DisplayMode.Tree,
							horizontalScrollMode = GafferUI.ScrollMode.Automatic
						)
						self.__objectsPathListing.setSortable( False )
						GafferSceneUI.Private.InspectorColumn.connectToDragBeginSignal( self.__objectsPathListing )

						with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :

							self.__linkSelectedButton = GafferUI.Button( image = "link.png", toolTip = "Link", hasFrame = False )
							self.__linkSelectedButton.clickedSignal().connect( functools.partial( Gaffer.WeakMethod( self.__linkSelected ), True ) )

							self.__unlinkSelectedButton = GafferUI.Button( image = "unlink.png", toolTip = "Unlink", hasFrame = False )
							self.__unlinkSelectedButton.clickedSignal().connect( functools.partial( Gaffer.WeakMethod( self.__linkSelected ), False ) )

							GafferUI.Spacer( size = imath.V2i( 1, 22 ), maximumSize = imath.V2i( 1, 22 ) )

							GafferUI.PlugLayout(
								self.settings(),
								orientation = GafferUI.ListContainer.Orientation.Horizontal,
								rootSection = "Mode",
							)

							GafferUI.PlugLayout(
								self.settings(),
								orientation = GafferUI.ListContainer.Orientation.Horizontal,
								rootSection = "Attribute",
							)

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

						self.__filteredLightsColumn = self.__attributeColumn( "filteredLights", self.settings()["__adaptedIn"], self.settings()["editScope"] )
						self.__filteredLightsExclusionsColumn = self.__attributeColumn( "filteredLights:exclusions", self.settings()["__adaptedIn"], self.settings()["editScope"] )

						self.__lightFiltersPathListing = GafferUI.PathListingWidget(
							GafferScene.ScenePath( self.settings()["__lightFilterHierarchyFilter"]["out"], self.context(), "/" ),
							columns = [
								_GafferSceneUI._LightEditorLocationNameColumn( GafferUI.PathColumn.SizeMode.Stretch ),
								self.__filteredLightsColumn,
								self.__filteredLightsExclusionsColumn,
							],
							selectionMode = GafferUI.PathListingWidget.SelectionMode.Cells,
							displayMode = GafferUI.PathListingWidget.DisplayMode.Tree,
							horizontalScrollMode = GafferUI.ScrollMode.Automatic
						)
						self.__lightFiltersPathListing.setSortable( False )
						GafferSceneUI.Private.InspectorColumn.connectToDragBeginSignal( self.__lightFiltersPathListing )

						with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :

							self.__filterSelectedButton = GafferUI.Button( image = "link.png", toolTip = "Link", hasFrame = False )
							self.__filterSelectedButton.clickedSignal().connect( functools.partial( Gaffer.WeakMethod( self.__filterSelected ), True ) )

							self.__unfilterSelectedButton = GafferUI.Button( image = "unlink.png", toolTip = "Unlink", hasFrame = False )
							self.__unfilterSelectedButton.clickedSignal().connect( functools.partial( Gaffer.WeakMethod( self.__filterSelected ), False ) )

							GafferUI.Spacer( size = imath.V2i( 1, 22 ), maximumSize = imath.V2i( 1, 22 ) )

							GafferUI.PlugLayout(
								self.settings(),
								orientation = GafferUI.ListContainer.Orientation.Horizontal,
								rootSection = "Mode",
							)

			self.__lightsSelectionChangedConnection = self.__lightsPathListing.selectionChangedSignal().connect(
				Gaffer.WeakMethod( self.__lightsSelectionChanged )
			)
			self.__setsPathListing.selectionChangedSignal().connect(
				Gaffer.WeakMethod( self.__setsSelectionChanged )
			)
			self.__objectsSelectionChangedConnection = self.__objectsPathListing.selectionChangedSignal().connect(
				Gaffer.WeakMethod( self.__objectsOrLightFiltersSelectionChanged )
			)
			self.__lightFiltersSelectionChangedConnection = self.__lightFiltersPathListing.selectionChangedSignal().connect(
				Gaffer.WeakMethod( self.__objectsOrLightFiltersSelectionChanged )
			)

			self.__lightsAndSetsTabbedContainer.currentChangedSignal().connect( Gaffer.WeakMethod( self.__currentTabChanged ) )
			self.__objectsAndLightFiltersTabbedContainer.currentChangedSignal().connect( Gaffer.WeakMethod( self.__currentTabChanged ) )

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

		self.settings()["__filteredObjects"].plugDirtiedSignal().connect( Gaffer.WeakMethod( self.__objectsPlugDirtied ) )

		Gaffer.Metadata.nodeValueChangedSignal().connect( Gaffer.WeakMethod( self.__metadataChanged ) )

		self._updateFromSet()
		self.__transferSelectionFromScriptNode()
		self.__updateButtonStatus()

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
		elif plug in ( self.settings()["in"], self.settings()["editScope"] ) :
			self.__updateButtonStatus()

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

	def __metadataChanged( self, nodeTypeId, key, node ) :

		editScope = self.editScope()
		if editScope is None :
			return

		if Gaffer.MetadataAlgo.readOnlyAffectedByChange( editScope, nodeTypeId, key, node ) :
			self.__updateButtonStatus()

	def __currentTabChanged( self, *unused ) :

		self.__updateButtonStatus()

	def __selectedPathsChanged( self, scriptNode ) :

		self.__transferSelectionFromScriptNode()

	def __lightsSelectionChanged( self, pathListing ) :

		assert( pathListing is self.__lightsPathListing )

		with Gaffer.Signals.BlockedConnection( self.__selectedPathsChangedConnection ) :
			GafferSceneUI.ScriptNodeAlgo.setSelectedPaths( self.scriptNode(), pathListing.getSelection() )

		with Gaffer.Signals.BlockedConnection( self.__objectsSelectionChangedConnection ) :
			self.__objectsPathListing.setSelection(
				[pathListing.getSelection()] + [IECore.PathMatcher()] * ( len( self.__objectsPathListing.getColumns() ) - 1 ), scrollToFirst = False
			)
		with Gaffer.Signals.BlockedConnection( self.__lightFiltersSelectionChangedConnection ) :
			self.__lightFiltersPathListing.setSelection(
				[pathListing.getSelection()] + [IECore.PathMatcher()] * ( len( self.__lightFiltersPathListing.getColumns() ) - 1 ), scrollToFirst = False
			)

		self.__updateButtonStatus()

	def __setsSelectionChanged( self, pathListing ) :

		self.__updateButtonStatus()

	def __objectsOrLightFiltersSelectionChanged( self, pathListing ) :

		assert( pathListing in ( self.__objectsPathListing, self.__lightFiltersPathListing ) )

		with Gaffer.Signals.BlockedConnection( self.__selectedPathsChangedConnection ) :
			GafferSceneUI.ScriptNodeAlgo.setSelectedPaths( self.scriptNode(), pathListing.getSelection()[0] )

		with Gaffer.Signals.BlockedConnection( self.__lightsSelectionChangedConnection ) :
			self.__lightsPathListing.setSelection( pathListing.getSelection()[0], scrollToFirst = False )

		if pathListing == self.__objectsPathListing :
			with Gaffer.Signals.BlockedConnection( self.__lightFiltersSelectionChangedConnection ) :
				self.__lightFiltersPathListing.setSelection(
					[pathListing.getSelection()[0]] + [IECore.PathMatcher()] * ( len( self.__lightFiltersPathListing.getColumns() ) - 1 ), scrollToFirst = False
				)
		else :
			with Gaffer.Signals.BlockedConnection( self.__objectsSelectionChangedConnection ) :
				self.__objectsPathListing.setSelection(
					[pathListing.getSelection()[0]] + [IECore.PathMatcher()] * ( len( self.__objectsPathListing.getColumns() ) - 1 ), scrollToFirst = False
				)

		# Accumulate selection across all columns so selecting
		# only cells in non-name columns doesn't cause the filter
		# to clear.
		selection = IECore.PathMatcher()
		for s in pathListing.getSelection() :
			selection.addPaths( s )

		self.__linkedToSelectionFilterPaths = selection
		self.__lazyUpdateLinkedLightsSetFilter()
		self.__updateButtonStatus()

	@GafferUI.LazyMethod( deferUntilPlaybackStops = True )
	def __transferSelectionFromScriptNode( self ) :

		selectedPaths = GafferSceneUI.ScriptNodeAlgo.getSelectedPaths( self.scriptNode() )
		with Gaffer.Signals.BlockedConnection( self.__lightsSelectionChangedConnection ) :
			self.__lightsPathListing.setSelection( selectedPaths, scrollToFirst = True )
		with Gaffer.Signals.BlockedConnection( self.__objectsSelectionChangedConnection ) :
			self.__objectsPathListing.setSelection(
				[selectedPaths] + [IECore.PathMatcher()] * ( len( self.__objectsPathListing.getColumns() ) - 1 ), scrollToFirst = True
			)
		with Gaffer.Signals.BlockedConnection( self.__lightFiltersSelectionChangedConnection ) :
			self.__lightFiltersPathListing.setSelection(
				[selectedPaths] + [IECore.PathMatcher()] * ( len( self.__lightFiltersPathListing.getColumns() ) - 1 ), scrollToFirst = True
			)

		self.__linkedToSelectionFilterPaths = selectedPaths
		self.__updateLinkedLightsSetFilter()
		self.__updateButtonStatus()

	@GafferUI.LazyMethod()
	def __lazyUpdateLinkedLightsSetFilter( self ) :

		self.__updateLinkedLightsSetFilter()

	def __updateLinkedLightsSetFilter( self ) :

		if not self.settings()["onlyLinkedToSelection"].getValue() or self.scene() is None :
			return

		self.settings()["__collect"]["contextValues"].setValue( IECore.StringVectorData( self.__linkedToSelectionFilterPaths.paths() ) )

	def __objectsPlugDirtied( self, plug ) :

		if plug == self.settings()["__filteredObjects"]["out"]["attributes"] :
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

	def __selectedLights( self ) :

		if self.__lightsAndSetsTabbedContainer.getCurrent() != self.__lightsColumn :
			return self.__selectedSetNames()

		lights = []
		with self.context() :
			lightSet = self.settings()["__adaptedIn"].set( "__lights" ).value
			for path in self.__lightsPathListing.getSelection().paths() :
				if lightSet.match( path ) & IECore.PathMatcher.Result.ExactMatch :
					lights.append( path )

		return lights

	def __editScopeNonEditableReason( self ) :

		input = self.settings()["in"].getInput()
		if input is None :
			return "No scene viewed"

		editScope = self.editScope()
		if editScope is None :
			return ""

		inputNode = input.node()
		if inputNode != editScope and editScope not in Gaffer.NodeAlgo.upstreamNodes( inputNode ) :
			return "The target edit scope {} is downstream of the viewed node.".format( editScope.getName() )
		if Gaffer.MetadataAlgo.readOnly( editScope ) :
			return "The target edit scope {} is read-only.".format( editScope.getName() )
		with self.context() :
			if not editScope["enabled"].getValue() :
				return "The target edit scope {} is disabled.".format( editScope.getName() )

		return ""

	def __updateButtonStatus( self, *unused ) :

		nonEditableReason = self.__editScopeNonEditableReason()

		target = "lights" if self.__lightsAndSetsTabbedContainer.getCurrent() == self.__lightsColumn else "sets"

		if self.__objectsAndLightFiltersTabbedContainer.getCurrent() == self.__objectsColumn :

			objectsSelected = len( self.__objectsPathListing.visualOrder( self.__objectsPathListing.getSelection()[0] ) ) > 0
			selection = objectsSelected and len( self.__selectedLights() ) > 0

			if not selection :
				nonEditableReason = f"To edit light linking, first select a combination of {target} and objects."

			self.__linkSelectedButton.setEnabled( not nonEditableReason )
			self.__linkSelectedButton.setToolTip( nonEditableReason if nonEditableReason else f"Click to link selected {target} to the selected objects" )

			self.__unlinkSelectedButton.setEnabled( not nonEditableReason )
			self.__unlinkSelectedButton.setToolTip( nonEditableReason if nonEditableReason else f"Click to unlink selected {target} from the selected objects" )

		else :

			objectsSelected = len( self.__lightFiltersPathListing.visualOrder( self.__lightFiltersPathListing.getSelection()[0] ) ) > 0
			selection = objectsSelected and len( self.__selectedLights() ) > 0

			if not selection :
				nonEditableReason = f"To edit light filter assignment, first select a combination of {target} and light filters."

			self.__filterSelectedButton.setEnabled( not nonEditableReason )
			self.__filterSelectedButton.setToolTip( nonEditableReason if nonEditableReason else f"Click to assign the selected light filters to the selected {target}" )

			self.__unfilterSelectedButton.setEnabled( not nonEditableReason )
			self.__unfilterSelectedButton.setToolTip( nonEditableReason if nonEditableReason else f"Click to unassign the selected light filters from the selected {target}" )

		self.__statusLabel.setText( nonEditableReason or f"Use the buttons to link or unlink the selected {target} and locations" )

	def __linkSelected( self, link, *unused ) :

		self.__editSelectedLightLinks( link, self.settings()["attribute"].getValue(), self.settings()["mode"].getValue() == "replace" )

	def __filterSelected( self, link, *unused ) :

		self.__editSelectedLightLinks( link, "filteredLights", self.settings()["mode"].getValue() == "replace" )

	## \todo Add equivalent linking actions to the SceneView "Light Links" context menu.
	def __editSelectedLightLinks( self, link, attribute, replaceExisting = False ) :

		if attribute == "linkedLights" :
			pathListing = self.__objectsPathListing
			inclusionsColumn = self.__linkedLightsColumn
			exclusionsColumn = self.__linkedLightsExclusionsColumn
		elif attribute == "shadowedLights" :
			pathListing = self.__objectsPathListing
			inclusionsColumn = self.__shadowedLightsColumn
			exclusionsColumn = self.__shadowedLightsExclusionsColumn
		elif attribute == "filteredLights" :
			pathListing = self.__lightFiltersPathListing
			inclusionsColumn = self.__filteredLightsColumn
			exclusionsColumn = self.__filteredLightsExclusionsColumn

		pathsToEdit = pathListing.visualOrder( pathListing.getSelection()[0] )
		if not pathsToEdit :
			return

		if self.__lightsAndSetsTabbedContainer.getCurrent() == self.__lightsColumn :
			targets = self.__selectedLights()
		else :
			targets = self.__selectedSetNames()

		rootPath = pathListing.getPath()
		path = rootPath.copy()
		edits = []
		warnings = set()
		with self.context() :

			for pathString in pathsToEdit :
				path.setFromString( pathString )
				if not path.isValid() :
					continue

				inclusionsInspection = inclusionsColumn.inspect( path )
				if replaceExisting and link :
					inclusions = ""
				else :
					inclusions = inclusionsInspection.value()
					inclusions = inclusions.value if inclusions is not None else ""

				exclusionsInspection = exclusionsColumn.inspect( path )
				if replaceExisting and not link :
					exclusions = ""
				else :
					exclusions = exclusionsInspection.value()
					exclusions = exclusions.value if exclusions is not None else ""

				if link :
					newInclusions = Gaffer.SetExpressionAlgo.include( inclusions, " ".join( targets ) )
					newExclusions = Gaffer.SetExpressionAlgo.exclude( exclusions, " ".join( targets ) )
				else :
					newInclusions = Gaffer.SetExpressionAlgo.remove( inclusions, " ".join( targets ) )
					newExclusions = Gaffer.SetExpressionAlgo.include( exclusions, " ".join( targets ) )

				if newInclusions != inclusions :
					value = IECore.StringData( newInclusions )
					if inclusionsInspection.canEdit( value ) :
						edits.append( ( inclusionsInspection, value ) )
					else :
						warnings.add( f"{inclusionsColumn.headerData( rootPath ).value} : {inclusionsInspection.nonEditableReason( value )}" )

				if newExclusions != exclusions :
					value = IECore.StringData( newExclusions )
					if exclusionsInspection.canEdit( value ) :
						edits.append( ( exclusionsInspection, value ) )
					else :
						warnings.add( f"{exclusionsColumn.headerData( rootPath ).value} : {exclusionsInspection.nonEditableReason( value )}" )

			if warnings :
				GafferUI.PopupWindow.showWarning( "<br>".join( sorted( warnings ) ), parent = self )
				return

			with Gaffer.UndoScope( self.scriptNode() ) :
				for inspection, value in edits :
					inspection.edit( value )

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

		"mode" : {

			"description" :
			"""
			How the edit is applied.

			- Append : Modifies the input set expression to include or exclude the selected lights or sets.
			- Replace : Replaces the input set expression with only the selected lights or sets.
			""",

			"label" : "Mode",
			"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",
			"labelPlugValueWidget:showValueChangedIndicator" : False,
			"preset:Append" : "append",
			"preset:Replace" : "replace",
			"layout:width" : 130,
			"layout:section" : "Mode"

		},

		"attribute" : {

			"description" :
			"""
			The attribute to edit.
			""",

			"label" : "Attribute",
			"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",
			"labelPlugValueWidget:showValueChangedIndicator" : False,
			"preset:Linked Lights" : "linkedLights",
			"preset:Shadowed Lights" : "shadowedLights",
			"layout:width" : 130,
			"layout:section" : "Attribute"

		},

	}

)
