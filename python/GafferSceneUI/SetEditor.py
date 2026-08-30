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
from GafferUI.i18n import _
import GafferSceneUI

from . import _GafferSceneUI

class _TranslatedColumn( GafferUI.PathColumn ) :

	def __init__( self, column, header ) :

		GafferUI.PathColumn.__init__( self )
		self._inner = column
		self._header = header
		self._inner.changedSignal().connect( Gaffer.WeakMethod( self.__innerChanged ) )

	def cellData( self, path, canceller = None ) :

		return self._inner.cellData( path, canceller )

	def headerData( self, canceller = None ) :

		d = self._inner.headerData( canceller )
		return GafferUI.PathColumn.CellData( value = _( self._header ), icon = d.icon, toolTip = d.toolTip )

	def inspect( self, path ) :

		if hasattr( self._inner, "inspect" ) :
			return self._inner.inspect( path )
		return None

	def inspector( self, path ) :

		if hasattr( self._inner, "inspector" ) :
			return self._inner.inspector( path )
		return None

	def inspectorContext( self, path ) :

		if hasattr( self._inner, "inspectorContext" ) :
			return self._inner.inspectorContext( path )
		return None

	def __innerChanged( self, column ) :

		self.changedSignal()( self )

class SetEditor( GafferSceneUI.SceneEditor ) :

	class Settings( GafferSceneUI.SceneEditor.Settings ) :

		def __init__( self ) :

			GafferSceneUI.SceneEditor.Settings.__init__( self )

			self["filter"] = Gaffer.StringPlug()
			self["hideEmptySets"] = Gaffer.BoolPlug()
			self["hideEmptySelection"] = Gaffer.BoolPlug()

	IECore.registerRunTimeTyped( Settings, typeName = "GafferSceneUI::SetEditor::Settings" )

	def __init__( self, scriptNode, **kw ) :

		mainColumn = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, borderWidth = 4, spacing = 4 )

		GafferSceneUI.SceneEditor.__init__( self, mainColumn, scriptNode, **kw )

		## \todo Consider replacing these with internal node networks in the Settings node.
		self.__searchFilter = _GafferSceneUI._SetEditor.SearchFilter()
		self.__emptySetFilter = _GafferSceneUI._SetEditor.EmptySetFilter( scriptNode )
		self.__emptySetFilter.setEnabled( False )

		self.__emptySelectionFilter = _GafferSceneUI._SetEditor.EmptySetFilter( scriptNode, useSelection = True )
		self.__emptySelectionFilter.setEnabled( False )

		with mainColumn :

			GafferUI.PlugLayout( self.settings(), orientation = GafferUI.ListContainer.Orientation.Horizontal, rootSection = "Filter" )

			self.__setNameColumn = _TranslatedColumn( _GafferSceneUI._SetEditor.SetNameColumn(), "Name" )
			self.__setMembersColumn = _TranslatedColumn( _GafferSceneUI._SetEditor.SetMembersColumn(), "Members" )
			self.__selectedSetMembersColumn = _TranslatedColumn( _GafferSceneUI._SetEditor.SetSelectionColumn( scriptNode ), "Selected" )
			self.__includedSetMembersColumn = _GafferSceneUI._SetEditor.VisibleSetInclusionsColumn( scriptNode )
			self.__excludedSetMembersColumn = _GafferSceneUI._SetEditor.VisibleSetExclusionsColumn( scriptNode )
			self.__pathListing = GafferUI.PathListingWidget(
				_GafferSceneUI._SetEditor.SetPath(
					self.settings()["__adaptedIn"], self.context(), "/",
					filter = Gaffer.CompoundPathFilter( [ self.__searchFilter, self.__emptySetFilter, self.__emptySelectionFilter ] ),
				),
				columns = [
					self.__setNameColumn,
					self.__setMembersColumn,
					self.__selectedSetMembersColumn,
					self.__includedSetMembersColumn,
					self.__excludedSetMembersColumn,
				],
				selectionMode = GafferUI.PathListingWidget.SelectionMode.Rows,
				displayMode = GafferUI.PathListingWidget.DisplayMode.Tree,
			)

			self.__pathListing.dragBeginSignal().connectFront( Gaffer.WeakMethod( self.__dragBegin ) )
			self.__pathListing.columnContextMenuSignal().connect( Gaffer.WeakMethod( self.__columnContextMenuSignal ) )
			self.__pathListing.keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPressSignal ) )

		self._updateFromSet()

	def __repr__( self ) :

		return "GafferSceneUI.SetEditor( scriptNode )"

	def _updateFromSettings( self, plug ) :

		GafferSceneUI.SceneEditor._updateFromSettings( self, plug )

		if plug == self.settings()["filter"] :
			self.__searchFilter.setMatchPattern( plug.getValue() )
		elif plug == self.settings()["hideEmptySets"] :
			self.__emptySetFilter.setEnabled( plug.getValue() )
		elif plug == self.settings()["hideEmptySelection"] :
			self.__emptySelectionFilter.setEnabled( plug.getValue() )

	def _updateFromContext( self, modifiedItems ) :

		self.__lazyUpdateFromContext()

	@GafferUI.LazyMethod( deferUntilPlaybackStops = True )
	def __lazyUpdateFromContext( self ) :

		self.__pathListing.getPath().setContext( self.context() )

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
		if isinstance( getattr( column, '_inner', column ), _GafferSceneUI._SetEditor.SetNameColumn ) :
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
				"shortCut" : "Ctrl+Shift+C",
				"label" : _("Copy Set Members"),
			}
		)

		menuDefinition.append(
			"/Select Set Members",
			{
				"command" : Gaffer.WeakMethod( self.__selectSetMembers ),
				"active" : len( selectedSetNames ) > 0,
				"label" : _("Select Set Members"),
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
				result.addPaths( self.settings()["__adaptedIn"].set( setName ).value )

		return result

	def __getSelectedSetMembers( self, setNames, *unused ) :

		setMembers = self.__getSetMembers( setNames )
		return IECore.PathMatcher( [
			p for p in GafferSceneUI.ScriptNodeAlgo.getSelectedPaths( self.scriptNode() ).paths()
			if setMembers.match( p ) & ( IECore.PathMatcher.Result.ExactMatch | IECore.PathMatcher.Result.AncestorMatch )
		] )

	def __getIncludedSetMembers( self, setNames, *unused ) :

		return self.__getSetMembers( setNames ).intersection( GafferSceneUI.ScriptNodeAlgo.getVisibleSet( self.scriptNode() ).inclusions )

	def __getExcludedSetMembers( self, setNames, *unused ) :

		return self.__getSetMembers( setNames ).intersection( GafferSceneUI.ScriptNodeAlgo.getVisibleSet( self.scriptNode() ).exclusions )

	def __selectSetMembers( self, *unused ) :

		GafferSceneUI.ScriptNodeAlgo.setSelectedPaths( self.scriptNode(), self.__getSetMembers( self.__selectedSetNames() ) )

	def __copySetMembers( self, *unused ) :

		data = self.__getSetMembers( self.__selectedSetNames() ).paths()
		self.scriptNode().ancestor( Gaffer.ApplicationRoot ).setClipboardContents( IECore.StringVectorData( data ) )

GafferUI.Editor.registerType( "SetEditor", SetEditor )

##########################################################################
# Settings UI
##########################################################################

Gaffer.Metadata.registerNode(

	SetEditor.Settings,

	plugs = {

		"filter" : {

			"description" :
			_("""
			Filters the displayed sets by name. Accepts standard wildcards such as `*` and `?`.
			"""),

			"plugValueWidget:type" : "GafferUI.TogglePlugValueWidget",
			"togglePlugValueWidget:image:on" : "searchOn.png",
			"togglePlugValueWidget:image:off" : "search.png",
			"togglePlugValueWidget:defaultToggleValue" : "*",
			"togglePlugValueWidget:customWidgetType" : "GafferSceneUI.SetEditor._FilterPlugValueWidget",
			"stringPlugValueWidget:placeholderText" : "Filter...",

		},

		"hideEmptySets" : {

			"description" : _("Hides sets with no members."),
			"boolPlugValueWidget:labelVisible" : True,
			"layout:section" : "Filter",

		},

		"hideEmptySelection" : {

			"description" : _("Hides sets with no selected members or descendants."),
			"boolPlugValueWidget:labelVisible" : True,
			"layout:section" : "Filter",

		},

	},

)

class _FilterPlugValueWidget( GafferUI.StringPlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		GafferUI.StringPlugValueWidget.__init__( self, plug, **kw )

		self.dropSignal().connectFront( Gaffer.WeakMethod( self.__drop ) )

	def __drop( self, widget, event ) :

		if not (
			isinstance( event.data, IECore.StringVectorData ) and
			len( event.data ) > 0 and
			event.data[0].startswith( "/" )
		) :
			# Not dropping paths - fall back to the default handler.
			return False

		# Dropping paths - convert to sets those paths are members of.
		setNames = self.__getSetNamesFromPaths( event.data )
		self.getPlug().setValue( " ".join( sorted( setNames ) ) )

		return True

	def __scene( self ) :

		return self.getPlug().node()["__adaptedIn"]

	def __setLookup( self, paths ) :

		matchingSets = []
		pathMatcher = IECore.PathMatcher( paths )

		for s in self.__scene().setNames() :
			if not self.__scene().set( s ).value.intersection( pathMatcher ).isEmpty() :
				matchingSets.append( str( s ) )

		return matchingSets

	def __getSetNamesFromPaths( self, paths ) :

		dialogue = GafferUI.BackgroundTaskDialogue( _("Querying Set Names") )

		with self.context() :
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

SetEditor._FilterPlugValueWidget = _FilterPlugValueWidget
