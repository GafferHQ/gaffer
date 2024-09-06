##########################################################################
#
#  Copyright (c) 2022, Cinesite VFX Ltd. All rights reserved.
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
import GafferScene
import GafferUI
import GafferSceneUI

from . import ContextAlgo
from . import _GafferSceneUI

class SetEditor( GafferSceneUI.SceneEditor ) :

	def __init__( self, scriptNode, **kw ) :

		mainColumn = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, borderWidth = 4, spacing = 4 )

		GafferSceneUI.SceneEditor.__init__( self, mainColumn, scriptNode, **kw )

		searchFilter = _GafferSceneUI._SetEditor.SearchFilter()
		emptySetFilter = _GafferSceneUI._SetEditor.EmptySetFilter()
		emptySetFilter.userData()["UI"] = { "label" : "Hide Empty Members", "toolTip" : "Hide sets with no members" }
		emptySetFilter.setEnabled( False )

		emptySelectionFilter = _GafferSceneUI._SetEditor.EmptySetFilter( propertyName = "setPath:selectedMemberCount" )
		emptySelectionFilter.userData()["UI"] = { "label" : "Hide Empty Selection", "toolTip" : "Hide sets with no selected members or descendants" }
		emptySelectionFilter.setEnabled( False )

		self.__filter = Gaffer.CompoundPathFilter( [ searchFilter, emptySetFilter, emptySelectionFilter ] )

		with mainColumn :

			with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :

				self.__searchFilterWidget = _SearchFilterWidget( searchFilter )
				GafferUI.BasicPathFilterWidget( emptySetFilter )
				GafferUI.BasicPathFilterWidget( emptySelectionFilter )

			self.__setMembersColumn = _GafferSceneUI._SetEditor.SetMembersColumn()
			self.__selectedSetMembersColumn = _GafferSceneUI._SetEditor.SetSelectionColumn()
			self.__includedSetMembersColumn = _GafferSceneUI._SetEditor.VisibleSetInclusionsColumn( scriptNode.context() )
			self.__excludedSetMembersColumn = _GafferSceneUI._SetEditor.VisibleSetExclusionsColumn( scriptNode.context() )
			self.__pathListing = GafferUI.PathListingWidget(
				Gaffer.DictPath( {}, "/" ), # temp till we make a SetPath
				columns = [
					_GafferSceneUI._SetEditor.SetNameColumn(),
					self.__setMembersColumn,
					self.__selectedSetMembersColumn,
					self.__includedSetMembersColumn,
					self.__excludedSetMembersColumn,
				],
				selectionMode = GafferUI.PathListingWidget.SelectionMode.Rows,
				displayMode = GafferUI.PathListingWidget.DisplayMode.Tree,
			)

			self.__pathListing.dragBeginSignal().connectFront( Gaffer.WeakMethod( self.__dragBegin ), scoped = False )
			self.__pathListing.columnContextMenuSignal().connect( Gaffer.WeakMethod( self.__columnContextMenuSignal ), scoped = False )
			self.__pathListing.keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPressSignal ), scoped = False )

		self._updateFromSet()
		self.__updatePathListingPath()

	def __repr__( self ) :

		return "GafferSceneUI.SetEditor( scriptNode )"

	def _updateFromContext( self, modifiedItems ) :

		if any( not i.startswith( "ui:" ) for i in modifiedItems ) or any( ContextAlgo.affectsSelectedPaths( i ) for i in modifiedItems ) :
			self.__updatePathListingPath()

	@GafferUI.LazyMethod( deferUntilPlaybackStops = True )
	def __updatePathListingPath( self ) :

		# We take a static copy of our current context for use in the SetPath for two reasons :
		#
		# 1. To prevent the PathListing from updating automatically when the original context
		#    changes, allowing us to use LazyMethod to defer updates until playback stops.
		# 2. Because the PathListingWidget uses a BackgroundTask to evaluate the Path, and it
		#    would not be thread-safe to directly reference a context that could be modified by
		#    the UI thread at any time.
		contextCopy = Gaffer.Context( self.context() )
		self.__searchFilterWidget.setScene( self.settings()["in"] )
		self.__searchFilterWidget.setContext( contextCopy )
		self.__pathListing.setPath( _GafferSceneUI._SetEditor.SetPath( self.settings()["in"], contextCopy, "/", filter = self.__filter ) )

	def __selectedSetNames( self ) :

		selection = self.__pathListing.getSelection()
		path = self.__pathListing.getPath().copy()
		result = []
		for p in selection.paths() :
			path.setFromString( p )
			setName = path.property( "setPath:setName" )
			if setName is not None :
				result.append( setName )

		return result

	def __dragBegin( self, widget, event ) :

		path = self.__pathListing.pathAt( imath.V2f( event.line.p0.x, event.line.p0.y ) )
		selection = self.__pathListing.getSelection()
		setNames = []
		if selection.match( str( path ) ) & IECore.PathMatcher.Result.ExactMatch :
			setNames = self.__selectedSetNames()
		else :
			setName = path.property( "setPath:setName" )
			if setName is not None :
				setNames.append( setName )

		if len( setNames ) == 0 :
			# prevent the path itself from being dragged
			return IECore.StringVectorData()

		column = self.__pathListing.columnAt( imath.V2f( event.line.p0.x, event.line.p0.y ) )
		if isinstance( column, _GafferSceneUI._SetEditor.SetNameColumn ) :
			GafferUI.Pointer.setCurrent( "sets" )
		else :
			GafferUI.Pointer.setCurrent( "paths" )

		if column == self.__setMembersColumn :
			return IECore.StringVectorData( self.__getSetMembers( setNames ).paths() )
		elif column == self.__selectedSetMembersColumn :
			return IECore.StringVectorData( self.__getSelectedSetMembers( setNames ).paths() )
		elif column == self.__includedSetMembersColumn :
			return IECore.StringVectorData( self.__getIncludedSetMembers( setNames ).paths() )
		elif column == self.__excludedSetMembersColumn :
			return IECore.StringVectorData( self.__getExcludedSetMembers( setNames ).paths() )
		else :
			return IECore.StringVectorData( setNames )

	def __keyPressSignal( self, widget, event ) :

		if event.key == "C" and event.modifiers == event.Modifiers.Control :
			self.__copySelectedSetNames()
			return True
		elif event.key == "C" and event.modifiers == event.Modifiers.ShiftControl :
			self.__copySetMembers()
			return True

		return False

	def __columnContextMenuSignal( self, column, pathListingWidget, menuDefinition ) :

		selection = self.__pathListing.getSelection()
		selectedSetNames = self.__selectedSetNames()

		menuDefinition.append(
			"/Copy Set Name%s" % ( "" if selection.size() == 1 else "s" ),
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

	def __copySelectedSetNames( self, *unused ) :

		self.scriptNode().ancestor( Gaffer.ApplicationRoot ).setClipboardContents(
			IECore.StringVectorData( self.__selectedSetNames() )
		)

	def __getSetMembers( self, setNames, *unused ) :

		result = IECore.PathMatcher()
		with Gaffer.Context( self.context() ) :
			for setName in setNames :
				result.addPaths( self.settings()["in"].set( setName ).value )

		return result

	def __getSelectedSetMembers( self, setNames, *unused ) :

		setMembers = self.__getSetMembers( setNames )
		return IECore.PathMatcher( [
			p for p in ContextAlgo.getSelectedPaths( self.context() ).paths()
			if setMembers.match( p ) & ( IECore.PathMatcher.Result.ExactMatch | IECore.PathMatcher.Result.AncestorMatch )
		] )

	def __getIncludedSetMembers( self, setNames, *unused ) :

		return self.__getSetMembers( setNames ).intersection( ContextAlgo.getVisibleSet( self.context() ).inclusions )

	def __getExcludedSetMembers( self, setNames, *unused ) :

		return self.__getSetMembers( setNames ).intersection( ContextAlgo.getVisibleSet( self.context() ).exclusions )

	def __selectSetMembers( self, *unused ) :

		ContextAlgo.setSelectedPaths( self.context(), self.__getSetMembers( self.__selectedSetNames() ) )

	def __copySetMembers( self, *unused ) :

		data = self.__getSetMembers( self.__selectedSetNames() ).paths()
		self.scriptNode().ancestor( Gaffer.ApplicationRoot ).setClipboardContents( IECore.StringVectorData( data ) )

GafferUI.Editor.registerType( "SetEditor", SetEditor )

##########################################################################
# _SearchFilterWidget
##########################################################################

class _SearchFilterWidget( GafferUI.PathFilterWidget ) :

	def __init__( self, pathFilter ) :

		self.__patternWidget = GafferUI.TextWidget()
		GafferUI.PathFilterWidget.__init__( self, self.__patternWidget, pathFilter )

		self.__patternWidget.setPlaceholderText( "Filter..." )

		self.__patternWidget.editingFinishedSignal().connect( Gaffer.WeakMethod( self.__patternEditingFinished ), scoped = False )
		self.__patternWidget.dragEnterSignal().connectFront( Gaffer.WeakMethod( self.__dragEnter ), scoped = False )
		self.__patternWidget.dragLeaveSignal().connectFront( Gaffer.WeakMethod( self.__dragLeave ), scoped = False )
		self.__patternWidget.dropSignal().connectFront( Gaffer.WeakMethod( self.__drop ), scoped = False )

		self.__context = None
		self.__scene = None

		self._updateFromPathFilter()

	def setContext( self, context ) :

		self.__context = context

	def setScene( self, scene ) :

		self.__scene = scene

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
			if event.data[0].startswith( "/" ) :
				# treat as paths, return all sets those paths are members of
				setNames = self.__getSetNamesFromPaths( event.data )
			else :
				# treat as set names
				setNames = event.data

			self.pathFilter().setMatchPattern( " ".join( sorted( setNames ) ) )

		self.__patternWidget.setHighlighted( False )

		return True

	def __setLookup( self, paths ) :

		matchingSets = []
		pathMatcher = IECore.PathMatcher( paths )

		for s in self.__scene["setNames"].getValue() :
				if not self.__scene.set( s ).value.intersection( pathMatcher ).isEmpty() :
					matchingSets.append( str( s ) )

		return matchingSets

	def __getSetNamesFromPaths( self, paths ) :

		if self.__scene is None or self.__context is None :
			return []

		dialogue = GafferUI.BackgroundTaskDialogue( "Querying Set Names" )

		with self.__context :
			result = dialogue.waitForBackgroundTask(
				functools.partial(
					self.__setLookup,
					paths
				),
				parentWindow = self.ancestor( GafferUI.Window )
			)

		if not isinstance( result, Exception ) :
			return result

		return []
