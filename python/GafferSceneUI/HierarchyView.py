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

	class Settings( GafferSceneUI.SceneEditor.Settings ) :

		def __init__( self ) :

			GafferSceneUI.SceneEditor.Settings.__init__( self, withHierarchyFilter = True )

	def __init__( self, scriptNode, **kw ) :

		column = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, borderWidth = 4, spacing = 4 )

		GafferSceneUI.SceneEditor.__init__( self, column, scriptNode, **kw )

		with column :

			with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :

				_VisibleSetBookmarkWidget() ## \todo Could be a custom widget in the plug layout
				GafferUI.Divider( GafferUI.Divider.Orientation.Vertical )

				GafferUI.PlugLayout(
					self.settings(),
					orientation = GafferUI.ListContainer.Orientation.Horizontal,
					rootSection = "Filter",
				)

			self.__pathListing = GafferUI.PathListingWidget(
				GafferScene.ScenePath( self.settings()["__filteredIn"], self.context(), "/" ),
				columns = [
					GafferUI.PathListingWidget.StandardColumn( "Name", "name", GafferUI.PathColumn.SizeMode.Stretch ),
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

		self.__lazyUpdateFromContext()

	@GafferUI.LazyMethod( deferUntilPlaybackStops = True )
	def __lazyUpdateFromContext( self ) :

		self.__pathListing.getPath().setContext( self.context() )

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
# _VisibleSetBookmarkWidget
##########################################################################

class _VisibleSetBookmarkWidget( GafferUI.Widget ) :

	def __init__( self ) :

		button = GafferUI.MenuButton(
			image = "bookmarks.png",
			hasFrame = False,
			toolTip = "Visible Set Bookmarks",
			menu = GafferUI.Menu( Gaffer.WeakMethod( self.__menuDefinition ), title = "Visible Set Bookmarks" )
		)

		GafferUI.Widget.__init__( self, button )

	def __menuDefinition( self ) :

		scriptNode = self.ancestor( GafferUI.Editor ).scriptNode()
		readOnly = Gaffer.MetadataAlgo.readOnly( scriptNode )

		menuDefinition = IECore.MenuDefinition()

		bookmarks = sorted( GafferSceneUI.ScriptNodeAlgo.visibleSetBookmarks( scriptNode ) )
		if bookmarks :
			for b in bookmarks :
				menuDefinition.append(
					"/" + b,
					{
						"command" : functools.partial( Gaffer.WeakMethod( self.__restore ), b ),
						"checkBox" : GafferSceneUI.ScriptNodeAlgo.getVisibleSetBookmark( scriptNode, b ) == GafferSceneUI.ScriptNodeAlgo.getVisibleSet( scriptNode ),
					}
				)
			menuDefinition.append( "/RestoreBookmarkDivider", { "divider" : True } )

			for b in bookmarks :
				menuDefinition.append(
					"/Save As/" + b,
					{
						"command" : functools.partial( Gaffer.WeakMethod( self.__saveAs ), b ),
						"active" : not readOnly,
					}
				)
				menuDefinition.append(
					"/Delete/" + b,
					{
						"command" : functools.partial( Gaffer.WeakMethod( self.__delete ), b ),
						"active" : not readOnly,
					}
				)
			menuDefinition.append( "/Save As/Divider", { "divider" : True } )
		else :
			menuDefinition.append( "/No Bookmarks Available", { "active" : False } )
			menuDefinition.append( "/NoBookmarksDivider", { "divider" : True } )

		menuDefinition.append(
			"/Save As/New Bookmark...",
			{
				"command" : functools.partial( Gaffer.WeakMethod( self.__save ) ),
				"active" : not readOnly,
			}
		)

		return menuDefinition

	def __save( self, *unused ) :

		d = GafferUI.TextInputDialogue( initialText = "", title = "Save Bookmark", confirmLabel = "Save" )
		name = d.waitForText( parentWindow = self.ancestor( GafferUI.Window ) )

		if not name :
			return

		if name in GafferSceneUI.ScriptNodeAlgo.visibleSetBookmarks( self.ancestor( GafferUI.Editor ).scriptNode() ) :
			c = GafferUI.ConfirmationDialogue(
				"Replace existing bookmark?",
				"A bookmark named {} already exists. Do you want to replace it?".format( name ),
				confirmLabel = "Replace"
			)
			if not c.waitForConfirmation( parentWindow = self.ancestor( GafferUI.Window ) ) :
				return

		self.__saveAs( name )

	def __saveAs( self, name, *unused ) :

		scriptNode = self.ancestor( GafferUI.Editor ).scriptNode()
		visibleSet = GafferSceneUI.ScriptNodeAlgo.getVisibleSet( scriptNode )
		with Gaffer.UndoScope( scriptNode ) :
			GafferSceneUI.ScriptNodeAlgo.addVisibleSetBookmark( scriptNode, name, visibleSet )

	def __delete( self, name, *unused ) :

		scriptNode = self.ancestor( GafferUI.Editor ).scriptNode()
		with Gaffer.UndoScope( scriptNode ) :
			GafferSceneUI.ScriptNodeAlgo.removeVisibleSetBookmark( scriptNode, name )

	def __restore( self, name, *unused ) :

		scriptNode = self.ancestor( GafferUI.Editor ).scriptNode()
		visibleSet = GafferSceneUI.ScriptNodeAlgo.getVisibleSetBookmark( scriptNode, name )
		GafferSceneUI.ScriptNodeAlgo.setVisibleSet( scriptNode, visibleSet )
