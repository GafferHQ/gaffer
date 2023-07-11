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
from . import _GafferSceneUI

from . import ContextAlgo
from . import SetUI

##########################################################################
# HierarchyView
##########################################################################

class HierarchyView( GafferUI.NodeSetEditor ) :

	def __init__( self, scriptNode, **kw ) :

		column = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, borderWidth = 4, spacing = 4 )

		GafferUI.NodeSetEditor.__init__( self, column, scriptNode, nodeSet = scriptNode.focusSet(), **kw )

		searchFilter = _GafferSceneUI._HierarchyViewSearchFilter()
		setFilter = _GafferSceneUI._HierarchyViewSetFilter()
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
					_GafferSceneUI._HierarchyViewInclusionsColumn( scriptNode.context() ),
					_GafferSceneUI._HierarchyViewExclusionsColumn( scriptNode.context() )
				],
				selectionMode = GafferUI.PathListingWidget.SelectionMode.Rows,
				displayMode = GafferUI.PathListingWidget.DisplayMode.Tree,
			)
			self.__pathListing.setDragPointer( "objects" )
			self.__pathListing.setSortable( False )

			self.__selectionChangedConnection = self.__pathListing.selectionChangedSignal().connect( Gaffer.WeakMethod( self.__selectionChanged ), scoped = False )
			self.__expansionChangedConnection = self.__pathListing.expansionChangedSignal().connect( Gaffer.WeakMethod( self.__expansionChanged ), scoped = False )

			self.__pathListing.contextMenuSignal().connect( Gaffer.WeakMethod( self.__contextMenuSignal ), scoped = False )
			self.keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPressSignal ), scoped = False )

		self.__plug = None
		self._updateFromSet()
		self.__transferExpansionFromContext()
		self.__transferSelectionFromContext()

	def scene( self ) :

		return self.__plug

	def __repr__( self ) :

		return "GafferSceneUI.HierarchyView( scriptNode )"

	def _updateFromSet( self ) :

		# first of all decide what plug we're viewing.
		self.__plug = None
		self.__plugParentChangedConnection = None
		node = self._lastAddedNode()
		if node is not None :
			self.__plug = next( GafferScene.ScenePlug.RecursiveOutputRange( node ), None )
			if self.__plug is not None :
				self.__plugParentChangedConnection = self.__plug.parentChangedSignal().connect(
					Gaffer.WeakMethod( self.__plugParentChanged ), scoped = True
				)

		# call base class update - this will trigger a call to _titleFormat(),
		# hence the need for already figuring out the plug.
		GafferUI.NodeSetEditor._updateFromSet( self )

		# update our view of the hierarchy
		self.__setPathListingPath()

	def _updateFromContext( self, modifiedItems ) :

		if any( ContextAlgo.affectsSelectedPaths( x ) for x in modifiedItems ) :
			self.__transferSelectionFromContext()
		elif any( ContextAlgo.affectsVisibleSet( x ) for x in modifiedItems ) :
			self.__transferExpansionFromContext()

		for item in modifiedItems :
			if not item.startswith( "ui:" ) :
				# When the context has changed, the hierarchy of the scene may
				# have too so we should update our PathListingWidget.
				self.__setPathListingPath()
				break

	def _titleFormat( self ) :

		return GafferUI.NodeSetEditor._titleFormat(
			self,
			_maxNodes = 1 if self.__plug is not None else 0,
			_reverseNodes = True,
			_ellipsis = False
		)

	def __plugParentChanged( self, plug, oldParent ) :

		# the plug we were viewing has been deleted or moved - find
		# another one to view.
		self._updateFromSet()

	@GafferUI.LazyMethod( deferUntilPlaybackStops = True )
	def __setPathListingPath( self ) :

		for f in self.__filter.getFilters() :
			f.setScene( self.__plug )

		if self.__plug is not None :
			# We take a static copy of our current context for use in the ScenePath - this prevents the
			# PathListing from updating automatically when the original context changes, and allows us to take
			# control of updates ourselves in _updateFromContext(), using LazyMethod to defer the calls to this
			# function until we are visible and playback has stopped.
			contextCopy = Gaffer.Context( self.getContext() )
			for f in self.__filter.getFilters() :
				f.setContext( contextCopy )
			with Gaffer.Signals.BlockedConnection( self.__selectionChangedConnection ) :
				self.__pathListing.setPath( GafferScene.ScenePath( self.__plug, contextCopy, "/", filter = self.__filter ) )
		else :
			with Gaffer.Signals.BlockedConnection( self.__selectionChangedConnection ) :
				self.__pathListing.setPath( Gaffer.DictPath( {}, "/" ) )

	def __expansionChanged( self, pathListing ) :

		assert( pathListing is self.__pathListing )

		with Gaffer.Signals.BlockedConnection( self._contextChangedConnection() ) :
			visibleSet = ContextAlgo.getVisibleSet( self.getContext() )
			visibleSet.expansions = pathListing.getExpansion()
			ContextAlgo.setVisibleSet( self.getContext(), visibleSet )

	def __selectionChanged( self, pathListing ) :

		assert( pathListing is self.__pathListing )

		with Gaffer.Signals.BlockedConnection( self._contextChangedConnection() ) :
			ContextAlgo.setSelectedPaths( self.getContext(), pathListing.getSelection() )

	def __keyPressSignal( self, widget, event ) :

		if event.key == "C" and event.modifiers == event.Modifiers.Control :
			self.__copySelectedPaths()
			return True

		elif event.key == "F" :
			self.__frameSelectedPaths()
			return True

		return False

	def __contextMenuSignal( self, widget ) :

		menuDefinition = IECore.MenuDefinition()

		selection = self.__pathListing.getSelection()
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

		self.__contextMenu = GafferUI.Menu( menuDefinition )
		self.__contextMenu.popup( widget )

		return True

	def __copySelectedPaths( self, *unused ) :

		if self.__plug is None :
			return

		selection = self.__pathListing.getSelection()
		if not selection.isEmpty() :
			data = IECore.StringVectorData( selection.paths() )
			self.__plug.ancestor( Gaffer.ApplicationRoot ).setClipboardContents( data )

	def __frameSelectedPaths( self ) :

		selection = self.__pathListing.getSelection()
		if not selection.isEmpty() :
			self.__pathListing.expandToSelection()
			self.__pathListing.scrollToFirst( selection )

	@GafferUI.LazyMethod( deferUntilPlaybackStops = True )
	def __transferExpansionFromContext( self ) :

		visibleSet = ContextAlgo.getVisibleSet( self.getContext() )
		with Gaffer.Signals.BlockedConnection( self.__expansionChangedConnection ) :
			self.__pathListing.setExpansion( visibleSet.expansions )

	@GafferUI.LazyMethod( deferUntilPlaybackStops = True )
	def __transferSelectionFromContext( self ) :

		selection = ContextAlgo.getSelectedPaths( self.getContext() )
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

		self.__patternWidget._qtWidget().setPlaceholderText( "Filter..." )
		self.__patternWidget.editingFinishedSignal().connect( Gaffer.WeakMethod( self.__patternEditingFinished ), scoped = False )

		self._updateFromPathFilter()

	def _updateFromPathFilter( self ) :

		self.__patternWidget.setText( self.pathFilter().getMatchPattern() )

	def __patternEditingFinished( self, widget ) :

		self.pathFilter().setMatchPattern( self.__patternWidget.getText() )
