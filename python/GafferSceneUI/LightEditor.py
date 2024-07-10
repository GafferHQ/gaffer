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

from GafferUI.PlugValueWidget import sole
from GafferSceneUI._HistoryWindow import _HistoryWindow

from . import ContextAlgo
from . import _GafferSceneUI

from Qt import QtWidgets

## \todo There's some scope for reducing code duplication here, by
# introducing something like a SceneListingWidget that could be shared
# with HierarchyView.
class LightEditor( GafferUI.NodeSetEditor ) :

	class Settings( GafferUI.Editor.Settings ) :

		def __init__( self, script ) :

			GafferUI.Editor.Settings.__init__( self, "LightEditorSettings", script )

			self["in"] = GafferScene.ScenePlug()
			self["attribute"] = Gaffer.StringPlug( defaultValue = "light" )
			self["section"] = Gaffer.StringPlug( defaultValue = "" )
			self["editScope"] = Gaffer.Plug()

	IECore.registerRunTimeTyped( Settings, typeName = "GafferSceneUI::LightEditor::Settings" )

	def __init__( self, scriptNode, **kw ) :

		column = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, borderWidth = 4, spacing = 4 )

		GafferUI.NodeSetEditor.__init__( self, column, scriptNode, nodeSet = scriptNode.focusSet(), **kw )

		self.__settingsNode = self.Settings( scriptNode )
		Gaffer.NodeAlgo.applyUserDefaults( self.__settingsNode )

		self.__setFilter = _GafferSceneUI._HierarchyViewSetFilter()
		self.__setFilter.setSetNames( [ "__lights", "__lightFilters" ] )

		with column :

			GafferUI.PlugLayout(
				self.__settingsNode,
				orientation = GafferUI.ListContainer.Orientation.Horizontal,
				rootSection = "Settings"
			)

			self.__pathListing = GafferUI.PathListingWidget(
				Gaffer.DictPath( {}, "/" ), # Temp till we make a ScenePath
				columns = [
					_GafferSceneUI._LightEditorLocationNameColumn(),
					_GafferSceneUI._LightEditorMuteColumn(
						self.__settingsNode["in"],
						self.__settingsNode["editScope"]
					),
					_GafferSceneUI._LightEditorSetMembershipColumn(
						self.__settingsNode["in"],
						self.__settingsNode["editScope"],
						"soloLights",
						"Solo"
					),
				],
				selectionMode = GafferUI.PathListingWidget.SelectionMode.Cells,
				displayMode = GafferUI.PathListingWidget.DisplayMode.Tree,
				horizontalScrollMode = GafferUI.ScrollMode.Automatic
			)

			self.__soloColumnIndex = 2

			self.__pathListing.setDragPointer( "objects" )
			self.__pathListing.setSortable( False )
			self.__selectionChangedConnection = self.__pathListing.selectionChangedSignal().connect(
				Gaffer.WeakMethod( self.__selectionChanged ), scoped = False
			)
			self.__pathListing.buttonDoubleClickSignal().connectFront( Gaffer.WeakMethod( self.__buttonDoubleClick ), scoped = False )
			self.__pathListing.keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPress ), scoped = False )
			self.__pathListing.buttonPressSignal().connectFront( Gaffer.WeakMethod( self.__buttonPress ), scoped = False )

		self.__settingsNode.plugSetSignal().connect( Gaffer.WeakMethod( self.__settingsPlugSet ), scoped = False )

		self.__plug = None
		self._updateFromSet()
		self.__transferSelectionFromContext()
		self.__updateColumns()

	__columnRegistry = collections.OrderedDict()

	def scene( self ) :

		return self.__plug

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
	# that will be matched against `self.__settingsNode["attribute"]` to determine if
	# the column should be shown.
	# \todo Deprecate in favor of method below.
	@classmethod
	def registerParameter( cls, rendererKey, parameter, section = None, columnName = None ) :

		parameter = cls.__parseParameter( parameter )

		GafferSceneUI.LightEditor.registerColumn(
			rendererKey,
			".".join( x for x in [ parameter.shader, parameter.name ] if x ),
			lambda scene, editScope : _GafferSceneUI._LightEditorInspectorColumn(
				GafferSceneUI.Private.ParameterInspector( scene, editScope, rendererKey, parameter ),
				columnName if columnName is not None else ""
			),
			section
		)

	# Registers a parameter to be available for editing. `rendererKey` is a pattern
	# that will be matched against `self.__settingsNode["attribute"]` to determine if
	# the column should be shown. `attribute` is the attribute holding the shader that
	# will be edited. If it is `None`, the attribute will be the same as `rendererKey`.
	@classmethod
	def registerShaderParameter( cls, rendererKey, parameter, shaderAttribute = None, section = None, columnName = None ) :

		parameter = cls.__parseParameter( parameter )

		shaderAttribute = shaderAttribute if shaderAttribute is not None else rendererKey

		GafferSceneUI.LightEditor.registerColumn(
			rendererKey,
			".".join( x for x in [ parameter.shader, parameter.name ] if x ),
			lambda scene, editScope : _GafferSceneUI._LightEditorInspectorColumn(
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
			lambda scene, editScope : _GafferSceneUI._LightEditorInspectorColumn(
				GafferSceneUI.Private.AttributeInspector( scene, editScope, attributeName ),
				displayName
			),
			section
		)

	# Registers a column in the Light Editor.
	# `inspectorFunction` is a callable object of the form
	# `inspectorFunction( scene, editScope )` returning a
	# `GafferSceneUI._LightEditorInspectorColumn` object.
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

	def _updateFromSet( self ) :

		# Decide what plug we're viewing.
		self.__plug = None
		self.__plugParentChangedConnection = None
		node = self._lastAddedNode()
		if node is not None :
			self.__plug = next(
				( p for p in GafferScene.ScenePlug.RecursiveOutputRange( node ) if not p.getName().startswith( "__" ) ),
				None
			)
			if self.__plug is not None :
				self.__plugParentChangedConnection = self.__plug.parentChangedSignal().connect( Gaffer.WeakMethod( self.__plugParentChanged ), scoped = True )

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

		attribute = self.__settingsNode["attribute"].getValue()
		currentSection = self.__settingsNode["section"].getValue()

		sectionColumns = []

		for rendererKey, sections in self.__columnRegistry.items() :
			if IECore.StringAlgo.match( attribute, rendererKey ) :
				section = sections.get( currentSection or None, {} )
				sectionColumns += [ c( self.__settingsNode["in"], self.__settingsNode["editScope"] ) for c in section.values() ]

		nameColumn = self.__pathListing.getColumns()[0]
		muteColumn = self.__pathListing.getColumns()[1]
		soloColumn = self.__pathListing.getColumns()[2]
		self.__pathListing.setColumns( [ nameColumn, muteColumn, soloColumn ] + sectionColumns )

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
			ContextAlgo.setSelectedPaths( self.getContext(), pathListing.getSelection()[0] )

	@GafferUI.LazyMethod( deferUntilPlaybackStops = True )
	def __transferSelectionFromContext( self ) :

		selectedPaths = ContextAlgo.getSelectedPaths( self.getContext() )
		with Gaffer.Signals.BlockedConnection( self.__selectionChangedConnection ) :
			selection = [selectedPaths] + ( [IECore.PathMatcher()] * ( len( self.__pathListing.getColumns() ) - 1 ) )
			self.__pathListing.setSelection( selection, scrollToFirst=True )

	def __buttonDoubleClick( self, pathListing, event ) :

		# A small corner area below the vertical scroll bar may pass through
		# to us, causing odd selection behavior. Check that we're within the
		# scroll area.
		if pathListing.pathAt( event.line.p0 ) is None :
			return False

		if event.button == event.Buttons.Left :
			self.__editSelectedCells( pathListing )

			return True

		return False

	def __keyPress( self, pathListing, event ) :

		if event.modifiers == event.Modifiers.None_ :

			if event.key == "Return" or event.key == "Enter" :
				self.__editSelectedCells( pathListing )
				return True

			if event.key == "D" and len( self.__disablableInspectionTweaks( pathListing ) ) > 0 :
				self.__disableEdits( pathListing )
				return True

			if (
				( event.key == "Backspace" or event.key == "Delete" ) and
				len( self.__removableAttributeInspections( pathListing ) ) > 0
			) :
				self.__removeAttributes( pathListing )
				return True

		return False

	def __editSelectedCells( self, pathListing, quickBoolean = True ) :

		# A dictionary of the form :
		# { inspector : { path1 : inspection, path2 : inspection, ... }, ... }
		inspectors = {}
		inspections = []

		with Gaffer.Context( self.getContext() ) as context :

			for selection, column in zip( pathListing.getSelection(), pathListing.getColumns() ) :
				if not isinstance( column, _GafferSceneUI._LightEditorInspectorColumn ) :
					continue
				for pathString in selection.paths() :
					path = GafferScene.ScenePlug.stringToPath( pathString )

					context["scene:path"] = path
					inspection = column.inspector().inspect()

					if inspection is not None :
						inspectors.setdefault( column.inspector(), {} )[path] = inspection
						inspections.append( inspection )

		if len( inspectors ) == 0 :
			with GafferUI.PopupWindow() as self.__popup :
				with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :
					GafferUI.Image( "warningSmall.png" )
					GafferUI.Label( "<h4>The selected cells cannot be edited in the current Edit Scope</h4>" )

			self.__popup.popup( parent = self )

			return

		nonEditable = [ i for i in inspections if not i.editable() ]

		if len( nonEditable ) == 0 :
			with Gaffer.Context( self.getContext() ) as context :
				if not quickBoolean or not self.__toggleBoolean( inspectors, inspections ) :
					edits = [ i.acquireEdit() for i in inspections ]
					warnings = "\n".join( [ i.editWarning() for i in inspections if i.editWarning() != "" ] )
					# The plugs are either not boolean, boolean with mixed values,
					# or attributes that don't exist and are not boolean. Show the popup.
					self.__popup = GafferUI.PlugPopup( edits, warning = warnings )

					if isinstance( self.__popup.plugValueWidget(), GafferUI.TweakPlugValueWidget ) :
						self.__popup.plugValueWidget().setNameVisible( False )

					self.__popup.popup( parent = self )

		else :

			with GafferUI.PopupWindow() as self.__popup :
				with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :
					GafferUI.Image( "warningSmall.png" )
					GafferUI.Label( "<h4>{}</h4>".format( nonEditable[0].nonEditableReason() ) )

			self.__popup.popup( parent = self )

	def __toggleBoolean( self, inspectors, inspections ) :

		plugs = [ i.acquireEdit() for i in inspections ]
		# Make sure all the plugs either contain, or are themselves a BoolPlug or can be edited
		# by `SetMembershipInspector.editSetMembership()`
		if not all (
			(
				isinstance( plug, ( Gaffer.TweakPlug, Gaffer.NameValuePlug ) ) and
				isinstance( plug["value"], Gaffer.BoolPlug )
			) or (
				isinstance( plug, ( Gaffer.BoolPlug ) )
			) or (
				isinstance( inspector, GafferSceneUI.Private.SetMembershipInspector )
			)
			for plug, inspector in zip( plugs, inspectors )
		) :
			return False

		currentValues = []

		# Use a single new value for all plugs.
		# First we need to find out what the new value would be for each plug in isolation.
		for inspector, pathInspections in inspectors.items() :
			for path, inspection in pathInspections.items() :
				currentValues.append( inspection.value().value if inspection.value() is not None else False )

		# Now set the value for all plugs, defaulting to `True` if they are not
		# currently all the same.
		newValue = not sole( currentValues )

		with Gaffer.UndoScope( self.scriptNode() ) :
			for inspector, pathInspections in inspectors.items() :
				for path, inspection in pathInspections.items() :
					if isinstance( inspector, GafferSceneUI.Private.SetMembershipInspector ) :
						inspector.editSetMembership(
							inspection,
							path,
							GafferScene.EditScopeAlgo.SetMembership.Added if newValue else GafferScene.EditScopeAlgo.SetMembership.Removed
						)

					else :
						plug = inspection.acquireEdit()
						if isinstance( plug, ( Gaffer.TweakPlug, Gaffer.NameValuePlug ) ) :
							plug["value"].setValue( newValue )
							plug["enabled"].setValue( True )
							if isinstance( plug, Gaffer.TweakPlug ) :
								plug["mode"].setValue( Gaffer.TweakPlug.Mode.Create )
						else :
							plug.setValue( newValue )

		return True

	def __disablableInspectionTweaks( self, pathListing ) :

		tweaks = []

		with Gaffer.Context( self.getContext() ) as context :
			for columnSelection, column in zip( pathListing.getSelection(), pathListing.getColumns() ) :
				if not isinstance( column, _GafferSceneUI._LightEditorInspectorColumn ) :
					continue
				for path in columnSelection.paths() :
					context["scene:path"] = GafferScene.ScenePlug.stringToPath( path )
					inspection = column.inspector().inspect()
					if inspection is not None and inspection.editable() :
						source = inspection.source()
						editScope = self.__settingsNode["editScope"].getInput()
						if (
							(
								(
									isinstance( source, ( Gaffer.TweakPlug, Gaffer.NameValuePlug ) ) and
									source["enabled"].getValue()
								) or
								isinstance( column.inspector(), GafferSceneUI.Private.SetMembershipInspector )
							) and
							( editScope is None or editScope.node().isAncestorOf( source ) )
						) :
							tweaks.append( ( path, column.inspector() ) )
						else :
							return []
					else :
						return []

		return tweaks

	def __disableEdits( self, pathListing ) :

		edits = self.__disablableInspectionTweaks( pathListing )

		with Gaffer.UndoScope( self.scriptNode() ), Gaffer.Context( self.getContext() ) as context :
			for path, inspector in edits :
				context["scene:path"] = GafferScene.ScenePlug.stringToPath( path )

				inspection = inspector.inspect()
				if inspection is not None and inspection.editable() :
					source = inspection.source()

					if isinstance( source, ( Gaffer.TweakPlug, Gaffer.NameValuePlug ) ) :
						source["enabled"].setValue( False )
					elif isinstance( inspector, GafferSceneUI.Private.SetMembershipInspector ) :
						inspector.editSetMembership( inspection, path, GafferScene.EditScopeAlgo.SetMembership.Unchanged )

	def __removableAttributeInspections( self, pathListing ) :

		inspections = []

		with Gaffer.Context( self.getContext() ) as context :
			for columnSelection, column in zip( pathListing.getSelection(), pathListing.getColumns() ) :
				if not isinstance( column, _GafferSceneUI._LightEditorInspectorColumn ) :
					continue
				elif not columnSelection.isEmpty() and type( column.inspector() ) != GafferSceneUI.Private.AttributeInspector :
					return []
				for path in columnSelection.paths() :
					context["scene:path"] = GafferScene.ScenePlug.stringToPath( path )
					inspection = column.inspector().inspect()
					if inspection is not None and inspection.editable() :
						source = inspection.source()
						editScope = self.__settingsNode["editScope"].getInput()
						if (
							( isinstance( source, Gaffer.TweakPlug ) and source["mode"].getValue() != Gaffer.TweakPlug.Mode.Remove ) or
							( isinstance( source, Gaffer.ValuePlug ) and len( source.children() ) == 2 and "Added" in source and "Removed" in source ) or
							editScope is not None
						) :
							inspections.append( inspection )
						else :
							return []
					else :
						return []

		return inspections

	def __removeAttributes( self, pathListing ) :

		inspections = self.__removableAttributeInspections( pathListing )

		with Gaffer.UndoScope( self.scriptNode() ) :
			for inspection in inspections :
				tweak = inspection.acquireEdit()
				tweak["enabled"].setValue( True )
				tweak["mode"].setValue( Gaffer.TweakPlug.Mode.Remove )

	def __selectedSetExpressions( self, pathListing ) :

		# A dictionary of the form :
		# { light1 : set( setExpression1, setExpression2 ), light2 : set( setExpression1 ), ... }
		result = {}

		lightPath = pathListing.getPath().copy()
		for columnSelection, column in zip( pathListing.getSelection(), pathListing.getColumns() ) :
			if (
				not columnSelection.isEmpty() and (
					not isinstance( column, _GafferSceneUI._LightEditorInspectorColumn ) or
					not (
						Gaffer.Metadata.value( "attribute:" + column.inspector().name(), "ui:scene:acceptsSetName" ) or
						Gaffer.Metadata.value( "attribute:" + column.inspector().name(), "ui:scene:acceptsSetNames" ) or
						Gaffer.Metadata.value( "attribute:" + column.inspector().name(), "ui:scene:acceptsSetExpression" )
					)
				)
			) :
				# We only return set expressions if all selected paths are in
				# columns that accept set names or set expressions.
				return {}

			for path in columnSelection.paths() :
				lightPath.setFromString( path )
				cellValue = column.cellData( lightPath ).value
				if cellValue is not None :
					result.setdefault( path, set() ).add( cellValue )
				else :
					# We only return set expressions if all selected paths are render passes.
					return {}

		return result

	def __selectAffected( self, pathListing ) :

		result = IECore.PathMatcher()

		with Gaffer.Context( self.getContext() ) as context :
			for light, setExpressions in self.__selectedSetExpressions( pathListing ).items() :
				for setExpression in setExpressions :
					result.addPaths( GafferScene.SetAlgo.evaluateSetExpression( setExpression, self.__settingsNode["in"] ) )

		GafferSceneUI.ContextAlgo.setSelectedPaths( self.getContext(), result )

	def __buttonPress( self, pathListing, event ) :

		if event.button != event.Buttons.Right or event.modifiers != event.Modifiers.None_ :
			return False

		selection = pathListing.getSelection()

		columns = pathListing.getColumns()
		cellColumn = pathListing.columnAt( event.line.p0 )
		columnIndex = -1
		for i in range( 0, len( columns ) ) :
			if cellColumn == columns[i] :
				columnIndex = i

		cellPath = pathListing.pathAt( event.line.p0 )
		if cellPath is None :
			return False

		if not selection[columnIndex].match( str( cellPath ) ) & IECore.PathMatcher.Result.ExactMatch :
			for p in selection :
				p.clear()
			selection[columnIndex].addPath( str( cellPath ) )
			pathListing.setSelection( selection, scrollToFirst = False )

		menuDefinition = IECore.MenuDefinition()

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
			inputNode = self.__settingsNode["in"].getInput().node()
			editScopeInput = self.__settingsNode["editScope"].getInput()
			if editScopeInput is not None :
				editScopeNode = editScopeInput.node()
				if inputNode != editScopeNode and editScopeNode not in Gaffer.NodeAlgo.upstreamNodes( inputNode ) :
					# Edit scope is downstream of input
					deleteEnabled = False
				elif GafferScene.EditScopeAlgo.prunedReadOnlyReason( editScopeNode ) is not None :
					# Pruning or the edit scope is read only
					deleteEnabled = False
				else :
					with self.getContext() :
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

		else :
			# Parameter cells

			menuDefinition.append(
				"Show History...",
				{
					"command" : Gaffer.WeakMethod( self.__showHistory )
				}
			)
			menuDefinition.append(
				"Edit...",
				{
					"command" : functools.partial( self.__editSelectedCells, pathListing, False ),
					"active" : pathListing.getSelection()[self.__soloColumnIndex].isEmpty(),
				}
			)
			menuDefinition.append(
				"Disable Edit",
				{
					"command" : functools.partial( self.__disableEdits, pathListing ),
					"active" : len( self.__disablableInspectionTweaks( pathListing ) ) > 0,
					"shortCut" : "D",
				}
			)
			menuDefinition.append(
				"Remove Attribute",
				{
					"command" : functools.partial( self.__removeAttributes, pathListing ),
					"active" : len( self.__removableAttributeInspections( pathListing ) ) > 0,
					"shortCut" : "Backspace, Delete",
				}
			)
			if len( self.__selectedSetExpressions( pathListing ) ) > 0 :
				menuDefinition.append(
					"SelectAffectedObjectsDivider", { "divider" : True }
				)
				menuDefinition.append(
					"Select Affected Objects",
					{
						"command" : functools.partial( self.__selectAffected, pathListing ),
					}
				)

		self.__contextMenu = GafferUI.Menu( menuDefinition )
		self.__contextMenu.popup( pathListing )

		return True

	def __selectLinked (self, *unused ) :

		context = self.getContext()

		dialogue = GafferUI.BackgroundTaskDialogue( "Selecting Linked Objects" )

		# There may be multiple columns with a selection, but we only operate on the name column.
		selectedLights = self.__pathListing.getSelection()[0]

		with context :
			result = dialogue.waitForBackgroundTask(
				functools.partial(
					GafferScene.SceneAlgo.linkedObjects,
					self.__settingsNode["in"],
					selectedLights
				)
			)

		if not isinstance( result, Exception ) :
			GafferSceneUI.ContextAlgo.setSelectedPaths( context, result )

	def __deleteLights( self, *unused ) :

		# There may be multiple columns with a selection, but we only operate on the name column.
		selection = self.__pathListing.getSelection()[0]

		editScope = self.__settingsNode["editScope"].getInput().node()

		with Gaffer.UndoScope( editScope.ancestor( Gaffer.ScriptNode ) ) :
			GafferScene.EditScopeAlgo.setPruned( editScope, selection, True )

	def __showHistory( self, *unused ) :

		selection = self.__pathListing.getSelection()
		columns = self.__pathListing.getColumns()

		for i in range( 0, len( columns ) ) :
			column = columns[ i ]
			if not isinstance( column, _GafferSceneUI._LightEditorInspectorColumn ) :
				continue

			for path in selection[i].paths() :
				window = _HistoryWindow(
					column.inspector(),
					path,
					self.getContext(),
					self.ancestor( GafferUI.ScriptWindow ).scriptNode(),
					"History : {} : {}".format( path, column.headerData().value )
				)
				self.ancestor( GafferUI.Window ).addChildWindow( window, removeOnClose = True )
				window.setVisible( True )


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
			"layout:width", 225,

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
