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

import imath
import six

import IECore
import IECoreScene

import Gaffer
import GafferUI
import GafferScene
import GafferSceneUI

from . import ContextAlgo
from . import _GafferSceneUI

from Qt import QtWidgets

## \todo There's some scope for reducing code duplication here, by
# introducing something like a SceneListingWidget that could be shared
# with HierarchyView.
class LightEditor( GafferUI.NodeSetEditor ) :

	# We store our settings as plugs on a node for a few reasons :
	#
	# - We want to use an EditScopePlugValueWidget, and that requires it.
	# - We get a bunch of useful widgets and signals for free.
	# - Longer term we want to refactor all Editors to derive from Node,
	#   in the same way that View does already. This will let us serialise
	#   _all_ layout state in the same format we serialise node graphs in.
	# - The `userDefault` metadata provides a convenient way of configuring
	#   defaults.
	# - The PlugLayout we use to display the settings allows users to add
	#   their own widgets to the UI.
	class Settings( Gaffer.Node ) :

		def __init__( self ) :

			Gaffer.Node.__init__( self, "LightEditorSettings" )

			self["in"] = GafferScene.ScenePlug()
			self["attribute"] = Gaffer.StringPlug( defaultValue = "light" )
			self["section"] = Gaffer.StringPlug( defaultValue = "" )
			self["editScope"] = Gaffer.Plug()

	IECore.registerRunTimeTyped( Settings )

	def __init__( self, scriptNode, **kw ) :

		column = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, borderWidth = 4, spacing = 4 )

		GafferUI.NodeSetEditor.__init__( self, column, scriptNode, nodeSet = scriptNode.focusSet(), **kw )

		self.__settingsNode = self.Settings()
		Gaffer.NodeAlgo.applyUserDefaults( self.__settingsNode )

		self.__setFilter = _GafferSceneUI._HierarchyViewSetFilter()
		self.__setFilter.setSetNames( [ "__lights" ] )

		with column :

			GafferUI.PlugLayout(
				self.__settingsNode,
				orientation = GafferUI.ListContainer.Orientation.Horizontal,
				rootSection = "Settings"
			)

			self.__pathListing = GafferUI.PathListingWidget(
				Gaffer.DictPath( {}, "/" ), # Temp till we make a ScenePath
				columns = [ _GafferSceneUI._LightEditorLocationNameColumn() ],
				allowMultipleSelection = True,
				displayMode = GafferUI.PathListingWidget.DisplayMode.Tree,
			)
			self.__pathListing.setDragPointer( "objects" )
			self.__pathListing.setSortable( False )
			self.__selectionChangedConnection = self.__pathListing.selectionChangedSignal().connect(
				Gaffer.WeakMethod( self.__selectionChanged ), scoped = False
			)
			self.__pathListing.buttonDoubleClickSignal().connectFront( Gaffer.WeakMethod( self.__buttonDoubleClick ), scoped = False )

		self.__settingsNode.plugSetSignal().connect( Gaffer.WeakMethod( self.__settingsPlugSet ), scoped = False )

		self.__plug = None
		self._updateFromSet()
		self.__transferSelectionFromContext()
		self.__updateColumns()

	__columnRegistry = collections.OrderedDict()

	@classmethod
	def registerParameter( cls, attribute, parameter, section = None ) :

		# We use `tuple` to store `ShaderNetwork.Parameter`, because
		# the latter isn't hashable and we need to use it as a dict key.
		if isinstance( parameter, six.string_types ) :
			parameter = ( "", parameter )
		else :
			assert( isinstance( parameter, IECoreScene.ShaderNetwork.Parameter ) )
			parameter = ( parameter.shader, parameter.name )

		sections = cls.__columnRegistry.setdefault( attribute, collections.OrderedDict() )
		section = sections.setdefault( section, collections.OrderedDict() )
		section[parameter] = lambda scene, editScope : _GafferSceneUI._LightEditorInspectorColumn(
			GafferSceneUI.Private.ParameterInspector( scene, editScope, attribute, parameter )
		)

	def __repr__( self ) :

		return "GafferSceneUI.LightEditor( scriptNode )"

	def _updateFromSet( self ) :

		# Decide what plug we're viewing.
		self.__plug = None
		self.__plugParentChangedConnection = None
		node = self._lastAddedNode()
		if node is not None :
			self.__plug = next( GafferScene.ScenePlug.RecursiveOutputRange( node ), None )
			if self.__plug is not None :
				self.__plugParentChangedConnection = self.__plug.parentChangedSignal().connect( Gaffer.WeakMethod( self.__plugParentChanged ) )

		self.__settingsNode["in"].setInput( self.__plug )

		# Call base class update - this will trigger a call to _titleFormat(),
		# hence the need for already figuring out the plug.
		GafferUI.NodeSetEditor._updateFromSet( self )

		# Update our view of the hierarchy.
		self.__setPathListingPath()

	def _updateFromContext( self, modifiedItems ) :

		if any( ContextAlgo.affectsSelectedPaths( x ) for x in modifiedItems ) :
			self.__transferSelectionFromContext()

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

	@GafferUI.LazyMethod()
	def __updateColumns( self ) :

		sections = self.__columnRegistry[self.__settingsNode["attribute"].getValue()]
		section = sections[self.__settingsNode["section"].getValue() or None]
		sectionColumns = [ c( self.__settingsNode["in"], self.__settingsNode["editScope"] ) for c in section.values() ]

		nameColumn = self.__pathListing.getColumns()[0]
		self.__pathListing.setColumns( [ nameColumn ] + sectionColumns )

	def __settingsPlugSet( self, plug ) :

		if plug in ( self.__settingsNode["section"], self.__settingsNode["attribute"] ) :
			self.__updateColumns()

	def __plugParentChanged( self, plug, oldParent ) :

		# The plug we were viewing has been deleted or moved - find
		# another one to view.
		self._updateFromSet()

	@GafferUI.LazyMethod( deferUntilPlaybackStops = True )
	def __setPathListingPath( self ) :

		self.__setFilter.setScene( self.__plug )

		if self.__plug is not None :
			# We take a static copy of our current context for use in the ScenePath - this prevents the
			# PathListing from updating automatically when the original context changes, and allows us to take
			# control of updates ourselves in _updateFromContext(), using LazyMethod to defer the calls to this
			# function until we are visible and playback has stopped.
			contextCopy = Gaffer.Context( self.getContext() )
			self.__setFilter.setContext( contextCopy )
			self.__pathListing.setPath( GafferScene.ScenePath( self.__settingsNode["in"], contextCopy, "/", filter = self.__setFilter ) )
		else :
			self.__pathListing.setPath( Gaffer.DictPath( {}, "/" ) )

	def __selectionChanged( self, pathListing ) :

		assert( pathListing is self.__pathListing )

		with Gaffer.Signals.BlockedConnection( self._contextChangedConnection() ) :
			ContextAlgo.setSelectedPaths( self.getContext(), pathListing.getSelection() )

	@GafferUI.LazyMethod( deferUntilPlaybackStops = True )
	def __transferSelectionFromContext( self ) :

		selection = ContextAlgo.getSelectedPaths( self.getContext() )
		with Gaffer.Signals.BlockedConnection( self.__selectionChangedConnection ) :
			self.__pathListing.setSelection( selection, scrollToFirst=True, expandNonLeaf=False )

	def __buttonDoubleClick( self, pathListing, event ) :

		if event.button != event.Buttons.Left :
			return False

		path = pathListing.pathAt( event.line.p0 )
		if path is None :
			return False

		column = pathListing.columnAt( event.line.p0 )
		if not isinstance( column, _GafferSceneUI._LightEditorInspectorColumn ) :
			return False

		with Gaffer.Context( self.getContext() ) as context :
			context["scene:path"] = IECore.InternedStringVectorData( path[:] )
			inspection = column.inspector().inspect()

		if inspection is None :
			return False

		if inspection.editable() :

			self.__popup = GafferUI.PlugPopup( [ inspection.acquireEdit() ], warning = inspection.editWarning() )
			if isinstance( self.__popup.plugValueWidget(), GafferSceneUI.TweakPlugValueWidget ) :
				self.__popup.plugValueWidget().setNameVisible( False )
			self.__popup.popup()

		else :

			# See todo in `PlugPopup._PopupWindow`
			PopupWindow = GafferUI.PlugPopup.__bases__[0]

			with PopupWindow() as self.__popup :
				with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :
					GafferUI.Image( "warningSmall.png" )
					GafferUI.Label( "<h4>{}</h4>".format( inspection.nonEditableReason() ) )

			self.__popup.popup()

		return True

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

		],

	}

)

class _SectionPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		GafferUI.PlugValueWidget.__init__( self, QtWidgets.QTabBar(), plug, **kw )

		self._qtWidget().setDrawBase( False )

		self._qtWidget().currentChanged.connect( Gaffer.WeakMethod( self.__currentChanged ) )
		self.__ignoreCurrentChanged = False

		plug.node().plugSetSignal().connect( Gaffer.WeakMethod( self.__plugSet ), scoped = False )

		# Borrow the styling from the Spreadsheet's section chooser.
		## \todo Should we be introducing a `GafferUI.TabBar` class which can be used in
		# both?
		self._qtWidget().setProperty( "gafferClass", "GafferUI.SpreadsheetUI._SectionChooser" )

		self.__updateTabs()

	def _updateFromPlug( self ) :

		with self.getContext() :
			text = self.getPlug().getValue()

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
		with Gaffer.Signals.BlockedConnection( self._plugConnections() ) :
			self.getPlug().setValue(
				text if text != "Main" else ""
			)

	def __updateTabs( self ) :

		try :
			self.__ignoreCurrentChanged = True
			while self._qtWidget().count() :
				self._qtWidget().removeTab( 0 )
			attribute = self.getPlug().node()["attribute"].getValue()
			if attribute in LightEditor._LightEditor__columnRegistry :
				for section in LightEditor._LightEditor__columnRegistry[attribute].keys() :
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
