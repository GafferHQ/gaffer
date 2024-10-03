##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

import IECore

import Gaffer
import GafferUI
import GafferScene
import GafferSceneUI
from . import _GafferSceneUI

from . import SetUI

##########################################################################
# HierarchyView
##########################################################################

class HierarchyView( GafferSceneUI.SceneEditor ) :

	def __init__( self, scriptNode, **kw ) :

		column = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, borderWidth = 4, spacing = 4 )

		GafferSceneUI.SceneEditor.__init__( self, column, scriptNode, **kw )

		searchFilter = _GafferSceneUI._HierarchyViewSearchFilter()
		searchFilter.setScene( self.settings()["in"] )
		setFilter = _GafferSceneUI._HierarchyViewSetFilter()
		setFilter.setScene( self.settings()["in"] )
		setFilter.setEnabled( False )

		self.__filter = Gaffer.CompoundPathFilter( [ searchFilter, setFilter ] )

		with column :

			with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :

				_SearchFilterWidget( searchFilter )
				_SetFilterWidget( setFilter )

			self.__pathListing = GafferUI.PathListingWidget(
				Gaffer.DictPath( {}, "/" ), # temp till we make a ScenePath
				columns = [
					GafferUI.PathListingWidget.defaultNameColumn,
					_GafferSceneUI._HierarchyViewInclusionsColumn( scriptNode ),
					_GafferSceneUI._HierarchyViewExclusionsColumn( scriptNode )
				],
				selectionMode = GafferUI.PathListingWidget.SelectionMode.Rows,
				displayMode = GafferUI.PathListingWidget.DisplayMode.Tree,
			)
			self.__pathListing.setDragPointer( "objects" )
			self.__pathListing.setSortable( False )

			self.__selectionChangedConnection = self.__pathListing.selectionChangedSignal().connect( Gaffer.WeakMethod( self.__selectionChanged ) )
			self.__expansionChangedConnection = self.__pathListing.expansionChangedSignal().connect( Gaffer.WeakMethod( self.__expansionChanged ) )

			self.__pathListing.columnContextMenuSignal().connect( Gaffer.WeakMethod( self.__columnContextMenuSignal ) )
			self.keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPressSignal ) )

		self.__visibleSetChangedConnection = GafferSceneUI.ScriptNodeAlgo.visibleSetChangedSignal( scriptNode ).connect(
			Gaffer.WeakMethod( self.__visibleSetChanged )
		)
		self.__selectedPathsChangedConnection = GafferSceneUI.ScriptNodeAlgo.selectedPathsChangedSignal( scriptNode ).connect(
			Gaffer.WeakMethod( self.__selectedPathsChanged )
		)

		self._updateFromSet()
		self.__setPathListingPath()
		self.__transferExpansionFromScriptNode()
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

		return self.__pathListing

	def __repr__( self ) :

		return "GafferSceneUI.HierarchyView( scriptNode )"

	def _updateFromContext( self, modifiedItems ) :

		for item in modifiedItems :
			if not item.startswith( "ui:" ) :
				# When the context has changed, the hierarchy of the scene may
				# have too so we should update our PathListingWidget.
				self.__setPathListingPath()
				break

	@GafferUI.LazyMethod( deferUntilPlaybackStops = True )
	def __setPathListingPath( self ) :

		# We take a static copy of our current context for use in the ScenePath for two reasons :
		#
		# 1. To prevent the PathListing from updating automatically when the original context
		#    changes, which allows us to take control of updates ourselves in `_updateFromContext()`,
		#    using LazyMethod to defer the calls to this function until we are visible and
		#    playback has stopped.
		# 2. Because the PathListingWidget uses a BackgroundTask to evaluate the Path, and it
		#    would not be thread-safe to directly reference a context that could be modified by
		#    the UI thread at any time.
		contextCopy = Gaffer.Context( self.context() )
		for f in self.__filter.getFilters() :
			f.setContext( contextCopy )
		with Gaffer.Signals.BlockedConnection( self.__selectionChangedConnection ) :
			self.__pathListing.setPath( GafferScene.ScenePath( self.settings()["in"], contextCopy, "/", filter = self.__filter ) )

	def __visibleSetChanged( self, scriptNode ) :

		self.__transferExpansionFromScriptNode()

	def __selectedPathsChanged( self, scriptNode ) :

		self.__transferSelectionFromScriptNode()

	def __expansionChanged( self, pathListing ) :

		assert( pathListing is self.__pathListing )

		with Gaffer.Signals.BlockedConnection( self.__visibleSetChangedConnection ) :
			visibleSet = GafferSceneUI.ScriptNodeAlgo.getVisibleSet( self.scriptNode() )
			visibleSet.expansions = pathListing.getExpansion()
			GafferSceneUI.ScriptNodeAlgo.setVisibleSet( self.scriptNode(), visibleSet )

	def __selectionChanged( self, pathListing ) :

		assert( pathListing is self.__pathListing )

		with Gaffer.Signals.BlockedConnection( self.__selectedPathsChangedConnection ) :
			GafferSceneUI.ScriptNodeAlgo.setSelectedPaths( self.scriptNode(), pathListing.getSelection() )

	def __keyPressSignal( self, widget, event ) :

		if event.key == "C" and event.modifiers == event.Modifiers.Control :
			self.__copySelectedPaths()
			return True

		elif event.key == "F" :
			self.__frameSelectedPaths()
			return True

		return False

	def __columnContextMenuSignal( self, column, pathListing, menuDefinition ) :

		selection = pathListing.getSelection()
		menuDefinition.append(
			"Copy Path%s" % ( "" if selection.size() == 1 else "s" ),
			{
				"command" : Gaffer.WeakMethod( self.__copySelectedPaths ),
				"active" : not selection.isEmpty(),
				"shortCut" : "Ctrl+C"
			}
		)
		menuDefinition.append(
			"Frame Selection",
			{
				"command" : Gaffer.WeakMethod( self.__frameSelectedPaths ),
				"active" : not selection.isEmpty(),
				"shortCut" : "F"
			}
		)

	def __copySelectedPaths( self, *unused ) :

		if self.scene() is None :
			return

		selection = self.__pathListing.getSelection()
		if not selection.isEmpty() :
			data = IECore.StringVectorData( selection.paths() )
			self.scriptNode().ancestor( Gaffer.ApplicationRoot ).setClipboardContents( data )

	def __frameSelectedPaths( self ) :

		selection = self.__pathListing.getSelection()
		if not selection.isEmpty() :
			self.__pathListing.expandToSelection()
			self.__pathListing.scrollToFirst( selection )

	@GafferUI.LazyMethod( deferUntilPlaybackStops = True )
	def __transferExpansionFromScriptNode( self ) :

		visibleSet = GafferSceneUI.ScriptNodeAlgo.getVisibleSet( self.scriptNode() )
		with Gaffer.Signals.BlockedConnection( self.__expansionChangedConnection ) :
			self.__pathListing.setExpansion( visibleSet.expansions )

	@GafferUI.LazyMethod( deferUntilPlaybackStops = True )
	def __transferSelectionFromScriptNode( self ) :

		selection = GafferSceneUI.ScriptNodeAlgo.getSelectedPaths( self.scriptNode() )
		with Gaffer.Signals.BlockedConnection( self.__selectionChangedConnection ) :
			self.__pathListing.setSelection( selection, scrollToFirst=False )

GafferUI.Editor.registerType( "HierarchyView", HierarchyView )

##########################################################################
# _SetFilterWidget
##########################################################################

class _SetFilterWidget( GafferUI.PathFilterWidget ) :

	def __init__( self, pathFilter ) :

		button = GafferUI.MenuButton(
			"Sets",
			menu = GafferUI.Menu(
				Gaffer.WeakMethod( self.__setsMenuDefinition ),
				title = "Set Filter"
			)
		)

		GafferUI.PathFilterWidget.__init__( self, button, pathFilter )

	def _updateFromPathFilter( self ) :

		pass

	def __setsMenuDefinition( self ) :

		m = IECore.MenuDefinition()

		availableSets = set()
		if self.pathFilter().getScene() is not None :
			with self.pathFilter().getContext() :
				availableSets.update( str( s ) for s in self.pathFilter().getScene()["setNames"].getValue() )

		builtInSets = { "__lights", "__cameras", "__coordinateSystems" }
		selectedSets = set( self.pathFilter().getSetNames() )

		m.append( "/Enabled", { "checkBox" : self.pathFilter().getEnabled(), "command" : Gaffer.WeakMethod( self.__toggleEnabled ) } )
		m.append( "/EnabledDivider", { "divider" : True } )

		m.append(
			"/All", {
				"active" : self.pathFilter().getEnabled() and selectedSets.issuperset( availableSets ),
				"checkBox" : selectedSets.issuperset( availableSets ),
				"command" : functools.partial( Gaffer.WeakMethod( self.__setSets ), builtInSets | availableSets | selectedSets )
			}
		)
		m.append(
			"/None", {
				"active" : self.pathFilter().getEnabled() and len( selectedSets ),
				"checkBox" : not len( selectedSets ),
				"command" : functools.partial( Gaffer.WeakMethod( self.__setSets ), set() )
			}
		)
		m.append( "/AllDivider", { "divider" : True } )

		def item( setName ) :

			updatedSets = set( selectedSets )
			if setName in updatedSets :
				updatedSets.remove( setName )
			else :
				updatedSets.add( setName )

			return {
				"active" : self.pathFilter().getEnabled() and s in availableSets,
				"checkBox" : s in selectedSets,
				"command" : functools.partial( Gaffer.WeakMethod( self.__setSets ), updatedSets )
			}

		for s in sorted( builtInSets ) :
			m.append(
				"/%s" % IECore.CamelCase.toSpaced( s[2:] ),
				item( s )
			)

		if len( availableSets - builtInSets ) :
			m.append( "/BuiltInDivider", { "divider" : True } )

		pathFn = SetUI.getMenuPathFunction()

		for s in sorted( availableSets | selectedSets ) :
			if s in builtInSets :
				continue
			m.append( "/" + pathFn( s ), item( s ) )

		return m

	def __toggleEnabled( self, *unused ) :

		self.pathFilter().setEnabled( not self.pathFilter().getEnabled() )

	def __setSets( self, sets, *unused ) :

		self.pathFilter().setSetNames( sets )

##########################################################################
# _SearchFilterWidget
##########################################################################

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
