##########################################################################
#
#  Copyright (c) 2018, Matti Gruener. All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are
#  met:
#
#	   * Redistributions of source code must retain the above
#		 copyright notice, this list of conditions and the following
#		 disclaimer.
#
#	   * Redistributions in binary form must reproduce the above
#		 copyright notice, this list of conditions and the following
#		 disclaimer in the documentation and/or other materials provided with
#		 the distribution.
#
#	   * Neither the name of John Haddon nor the names of
#		 any other contributors to this software may be used to endorse or
#		 promote products derived from this software without specific prior
#		 written permission.
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

import Gaffer
import GafferUI

import imath

from Qt import QtWidgets

# In order to have Widgets that depend on this filter update properly, we
# conceptually treat all selected nodes as part of the filter. That makes sense
# as the filtering result depends on the nodes' inputs. We can then emit the
# filterChangedSignal if an AnimationNode was added or removed as input to the
# filtered node.
# We use the same mechanism to signal to Widgets that the name of a component
# of a path has changed. That probably makes less sense and should be looked into. \todo
class _AnimationPathFilter( Gaffer.PathFilter ) :

	def __init__( self, selection, userData = {} ) :

		Gaffer.PathFilter.__init__( self, userData )

		self.__selection = selection

		self.__selectionAncestors = set()
		for node in self.__selection :
			while True :
				node = node.parent()
				if node is not None :
					self.__selectionAncestors.add( node )
				else :
					break

		self.__plugInputChangedConnections = [ node.plugInputChangedSignal().connect( Gaffer.WeakMethod( self.__plugInputChanged ) ) for node in selection ]
		self.__nameChangedConnections = []

	def _filter( self, paths ) :

		def shouldKeep( path ) :

			graphComponent = path.property( "graphComponent:graphComponent" )
			if isinstance( graphComponent, Gaffer.Node ) :

				return (
					graphComponent in self.__selectionAncestors or
					( graphComponent in self.__selection and self.__hasAnimation( graphComponent ) )
				)

			else :

				assert( isinstance( graphComponent, Gaffer.Plug ) )
				return graphComponent.node() in self.__selection and self.__hasAnimation( graphComponent )

		result = []
		for path in paths :

			if not shouldKeep( path ) :
				continue

			result.append( path )

			# Hack to report name changes on paths we keep. Really this
			# should be dealt with for us by GraphComponentPath.
			self.__nameChangedConnections.append(
				path.property( "graphComponent:graphComponent" ).nameChangedSignal().connect( Gaffer.WeakMethod( self.__nameChanged ) )
			)

		return result

	def __hasAnimation( self, graphComponent ) :

		if isinstance( graphComponent, Gaffer.ValuePlug ) and Gaffer.Animation.isAnimated( graphComponent ) :
			return True
		else :
			# We recurse only to child plugs, because for our purposes we don't
			# consider the presence of animated child nodes to mean that the parent
			# node is animated. This makes the curve listing more intuitive, and avoids
			# potentially huge recursion through deeply nested node graphs.
			for childPlug in graphComponent.children( Gaffer.Plug ) :
				if self.__hasAnimation( childPlug ) :
					return True

		return False

	def __plugInputChanged( self, plug ) :
		# TODO: We can be a bit more selective here and only trigger updates
		# when an AnimationNode is involved.
		self.changedSignal()( self )

	def __nameChanged( self, graphComponent ) :

		self.changedSignal()( self )

class AnimationEditor( GafferUI.NodeSetEditor ) :

	def __init__( self, scriptNode, **kw ) :

		mainRow = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, borderWidth = 5, spacing = 5 )

		GafferUI.NodeSetEditor.__init__( self, mainRow, scriptNode, **kw )

		# Set up widget for curve names on the left
		self.__curveList = GafferUI.PathListingWidget(
			Gaffer.DictPath( {}, "/" ), # placeholder, updated in `_updateFromSet()`.
			columns = ( GafferUI.PathListingWidget.defaultNameColumn, ),
			displayMode = GafferUI.PathListingWidget.DisplayMode.Tree,
			allowMultipleSelection=True
		)

		self.__curveList._qtWidget().setMinimumSize( 160, 0 )
		self.__curveList._qtWidget().setSizePolicy( QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Ignored )
		self.__curveList.expansionChangedSignal().connect( Gaffer.WeakMethod( self.__expansionChanged ), scoped = False )
		self.__selectionChangedConnection = self.__curveList.selectionChangedSignal().connect( Gaffer.WeakMethod( self.__selectionChanged ), scoped = False )

		# Set up the widget responsible for actual curve drawing
		self.__animationGadget = GafferUI.AnimationGadget()

		# Set up signals needed to update selection state in PathListingWidget
		editable = self.__animationGadget.editablePlugs()
		self.__editablePlugsConnections = [
			editable.memberAddedSignal().connect( Gaffer.WeakMethod( self.__editablePlugAdded ), scoped = False ),
			editable.memberRemovedSignal().connect( Gaffer.WeakMethod( self.__editablePlugRemoved ), scoped = False )
		]

		self.__gadgetWidget = GafferUI.GadgetWidget(
			bufferOptions = {
				GafferUI.GLWidget.BufferOptions.Depth,
				GafferUI.GLWidget.BufferOptions.Double
			}
		)

		self.__gadgetWidget.getViewportGadget().setPrimaryChild( self.__animationGadget )
		self.__gadgetWidget.getViewportGadget().setVariableAspectZoom( True )

		# Set up the widget responsible for curve editing
		self.__curveEditor = _CurveEditor( editable, self.__animationGadget )

		# Assemble UI
		self.__splitMain = GafferUI.SplitContainer( orientation=GafferUI.SplitContainer.Orientation.Horizontal )
		self.__splitSide = GafferUI.SplitContainer( orientation=GafferUI.SplitContainer.Orientation.Vertical )
		mainRow.addChild( self.__splitMain )

		self.__splitSide.append( self.__curveList )
		self.__splitSide.append( self.__curveEditor )
		self.__splitMain.append( self.__splitSide )
		self.__splitMain.append( self.__gadgetWidget )

		# Initial allocation of screen space:
		#   If there's enough space for the list to get 160 pixels give the rest to the AnimationGadget.
		#   If that's not the case, divide the space 50/50
		# \todo: do we want to preserve that ratio when maximizing the window as being done currently?
		self.__splitMain.setSizes( (1, 1) )
		currentSizes = self.__splitMain.getSizes()
		if currentSizes[0] > 160 :
			total = sum(currentSizes)
			betterSize = [float(x) / total for x in [160, total - 160]]
			self.__splitMain.setSizes( betterSize )

		# set initial state
		self.__editablePlugs = None
		self._updateFromSet()
		self._updateFromContext( [ "frame" ] )
		self.__curveList._qtWidget().adjustSize()

		# \todo: is this a reasonable initial framing?
		bound = imath.Box3f( imath.V3f( -1, -1, 0 ), imath.V3f( 10, 10, 0 ) )
		self.__gadgetWidget.getViewportGadget().frame( bound )

		# connect context menu for animation gadget
		self.__gadgetWidget.contextMenuSignal().connect( Gaffer.WeakMethod( self.__animationGadgetContextMenu ), scoped = False )

	def _updateFromSet( self ) :

		GafferUI.NodeSetEditor._updateFromSet( self )

		nodeSet = self.getNodeSet()
		if len( nodeSet ) == 0 :
			pathRoot = self.scriptNode()
		else :
			pathRoot = nodeSet[0].parent()
			for node in nodeSet[1:] :
				if not pathRoot.isAncestorOf( node ) :
					pathRoot = pathRoot.commonAncestor( node )

		self.__curveList.setPath(
			Gaffer.GraphComponentPath(
				pathRoot, "/",
				filter = _AnimationPathFilter( nodeSet )
			)
		)

		# Trigger sychronization onto self.__animationGadget
		self.__expansionChanged( self.__curveList )

	def _updateFromContext( self, modifiedItems ) :

		self.__animationGadget.setContext( self.getContext() )

	def __expansionChanged( self, pathListing ) :

		assert( pathListing is self.__curveList )

		paths = pathListing.getExpandedPaths()

		visiblePlugs = set()
		for path in paths:
			for childPath in path.children() :
				child = childPath.property( "graphComponent:graphComponent" )
				if isinstance( child, Gaffer.ValuePlug ) and Gaffer.Animation.isAnimated( child ) :
					visiblePlugs.add( child )

		visible = self.__animationGadget.visiblePlugs()
		editable = self.__animationGadget.editablePlugs()

		visible.clear()
		for plug in visiblePlugs :
			visible.add( self.__sourceCurvePlug( plug ) )

		with Gaffer.BlockedConnection( self.__editablePlugsConnections ) :

			editable.clear()
			for plug in ( self.__editablePlugs or set() ) & visiblePlugs :
				editable.add( self.__sourceCurvePlug( plug ) )

	def __selectionChanged( self, pathListing ) :

		assert( pathListing is self.__curveList )

		paths = pathListing.getSelectedPaths()

		plugList = []

		for path in paths :
			graphComponent = path.property( "graphComponent:graphComponent" )

			if isinstance( graphComponent, Gaffer.ValuePlug ) and Gaffer.Animation.isAnimated( graphComponent ) :
				plugList.append( graphComponent )

			for child in graphComponent.children() :
				if isinstance( child, Gaffer.ValuePlug ) and Gaffer.Animation.isAnimated( child ) :
					plugList.append( child )

		self.__editablePlugs = set( plugList )

		editable = self.__animationGadget.editablePlugs()

		with Gaffer.BlockedConnection( self.__editablePlugsConnections ) :

			editable.clear()
			for plug in plugList :
				editable.add( self.__sourceCurvePlug( plug ) )

	def __editablePlugAdded( self, standardSet, curvePlug ) :

		root = self.__curveList.getPath().property( "graphComponent:graphComponent" )

		selection = self.__curveList.getSelection()
		for output in curvePlug["out"].outputs() :
			selection.addPath(
				output.relativeName( root ).replace( ".", "/" )
			)

		with Gaffer.BlockedConnection( self.__selectionChangedConnection ) :
			self.__curveList.setSelection( selection )

	def __editablePlugRemoved( self, standardSet, curvePlug ) :

		root = self.__curveList.getPath().property( "graphComponent:graphComponent" )

		selection = self.__curveList.getSelection()
		for output in curvePlug["out"].outputs() :
			selection.removePath(
				output.relativeName( root ).replace( ".", "/" )
			)

		with Gaffer.BlockedConnection( self.__selectionChangedConnection ) :
			self.__curveList.setSelection( selection )

	def __sourceCurvePlug( self, plug ) :

		result = plug.source().parent()
		assert( isinstance( result, Gaffer.Animation.CurvePlug ) )
		return result

	def __animationGadgetContextMenu( self, *unused ) :

		import IECore
		import functools

		# convert mouse position to event line
		position = GafferUI.Widget.mousePosition( relativeTo = self.__gadgetWidget )
		#viewport = self.__gadgetWidget.getViewportGadget()
		#line = viewport.rasterToGadgetSpace( imath.V2f( position.x, position.y ), gadget = self.__animationGadget )

		# only show context menu when mouse not above axis
		if self.__animationGadget.onTimeAxis( position ) or self.__animationGadget.onValueAxis( position ) :
			return False

		# check there are selected keys
		emptySelectedKeys = not self.__animationGadget.selectedKeys()

		# tie state for selected keys
		tieMode = None if emptySelectedKeys else self.__curveEditor.keyTab().getTieModeForSelectedKeys()

		# interpolator name for selected keys
		interpolatorName = None if emptySelectedKeys else self.__curveEditor.keyTab().getInterpolatorNameForSelectedKeys()

		# build context menu
		menuDefinition = IECore.MenuDefinition()

		for name in Gaffer.Animation.Interpolator.getFactory().getNames() :
			menuDefinition.append(
				"/Set Interpolator/%s" % ( name ),
				{
					"command" : functools.partial(
						Gaffer.WeakMethod( self.__setSelectedKeysInterpolator ),
						name=name
					),
					"active" : not emptySelectedKeys,
					"checkBox" : None if interpolatorName is None else interpolatorName == name
				}
			)

		for mode in sorted( Gaffer.Animation.Tangent.TieMode.values.values() ) :
			menuDefinition.append(
				"/Tie Mode/%s" % ( mode.name ),
				{
					"command" : functools.partial(
						Gaffer.WeakMethod( self.__setSelectedKeysTieMode ),
						tieMode=mode
					),
					"active" : not emptySelectedKeys,
					"checkBox" : tieMode == mode
				}
			)

		self.__popupMenu = GafferUI.Menu( menuDefinition, title="Selected Keys" )
		self.__popupMenu.popup( parent = self )

		return True

	def __setSelectedKeysInterpolator( self, unused, name ) :

		with Gaffer.UndoScope( self.scriptNode() ) :
			for key in self.__animationGadget.selectedKeys() :
				key.setInterpolator( name )

	def __setSelectedKeysTieMode( self, unused, tieMode ) :

		with Gaffer.UndoScope( self.scriptNode() ) :
			for key in self.__animationGadget.selectedKeys() :
				key.setTieMode( tieMode )

	def __repr__( self ) :

		return "GafferUI.AnimationEditor( scriptNode )"

# Private implementation - tab widget
class _CurveEditor( GafferUI.TabbedContainer ) :

	def __init__( self, curveSet, curveGadget ) :

		GafferUI.TabbedContainer.__init__( self )

		# store curve set and gadget
		self.__curveSet = curveSet
		self.__curveGadget = curveGadget

		# create tab widgets
		self.__keyTab = _KeyTab()
		self.__tangentTab = _TangentTab()
		self.__curveTab = _CurveTab()

		# set tab ordering
		self.append( self.__tangentTab, "Tangent" )
		self.append( self.__keyTab, "Key" )
		self.append( self.__curveTab, "Curve" )

		# set up signals
		self.__selectedKeysChangedConnection = self.__curveGadget.selectedKeysChangedSignal().connect(
			Gaffer.WeakMethod( self.__selectedKeysChanged ), scoped = False )
		self.__curveSelectedConnection = self.__curveSet.memberAddedSignal().connect(
			Gaffer.WeakMethod( self.__curveSelected ), scoped = False ),
		self.__curveDeselectedConnection = self.__curveSet.memberRemovedSignal().connect(
			Gaffer.WeakMethod( self.__curveDeselected ), scoped = False )

		# update all tabs
		for tab in self :
			tab.update()

	def curveSet( self ) :
		return self.__curveSet

	def curveGadget( self ) :
		return self.__curveGadget

	def keyTab( self ) :
		return self.__keyTab

	def __selectedKeysChanged( self, unused ) :
		# update key and tangent tabs
		self.__keyTab.update()
		self.__tangentTab.update()

	def __curveSelected( self, unused, curve ) :
		for tab in self :
			tab.connect( curve )

	def __curveDeselected( self, unused, curve ) :
		for tab in self :
			tab.disconnect( curve )

# Private implementation - key tab
class _KeyTab( GafferUI.GridContainer ) :

	from collections import namedtuple
	Connections = namedtuple( "Connections", ("frame", "value", "tieMode", "interp") )

	def __init__( self ) :

		import IECore
		import functools

		GafferUI.GridContainer.__init__( self, spacing=4 )

		# create labels
		self.__frameLabel = GafferUI.Label( text="Frame" )
		self.__valueLabel = GafferUI.Label( text="Value" )
		self.__interpLabel = GafferUI.Label( text="Interpolator" )
		self.__tieModeLabel = GafferUI.Label( text="Tie Mode" )

		# create editors
		# NOTE: initial value type (e.g. int or float) determines validated value type of widget
		self.__frameEditor = GafferUI.NumericWidget( value=int(0) )
		self.__valueEditor = GafferUI.NumericWidget( value=float(0) )
		self.__interpEditor = GafferUI.MenuButton()
		self.__tieModeEditor = GafferUI.MenuButton()

		# build interpolator menu
		im = IECore.MenuDefinition()
		for name in Gaffer.Animation.Interpolator.getFactory().getNames() :
			im.append( "%s" % ( name ), {
				"command" : functools.partial( Gaffer.WeakMethod( self.__setInterpolator ), name=name ),
				"checkBox" : functools.partial( Gaffer.WeakMethod( self.__checkBoxStateForInterpolatorName ), name=name ) } )
		self.__interpEditor.setMenu( GafferUI.Menu( im ) )

		# build tie mode menu
		tm = IECore.MenuDefinition()
		for mode in sorted( Gaffer.Animation.Tangent.TieMode.values.values() ) :
			tm.append( "%s" % ( mode.name ), {
				"command" : functools.partial( Gaffer.WeakMethod( self.__setTieMode ), mode=mode ),
				"checkBox" : functools.partial( Gaffer.WeakMethod( self.__checkBoxStateForTieMode ), mode=mode ) } )
		self.__tieModeEditor.setMenu( GafferUI.Menu( tm ) )

		# setup editor connections
		self.__frameConnection = self.__frameEditor.valueChangedSignal().connect(
			Gaffer.WeakMethod( self.__setFrame ), scoped = False )
		self.__valueConnection = self.__valueEditor.valueChangedSignal().connect(
			Gaffer.WeakMethod( self.__setValue ), scoped = False )

		# layout widgets
		self.addChild( self.__frameLabel, ( 0, 0 ) )
		self.addChild( self.__frameEditor, ( 1, 0 ) )
		self.addChild( self.__valueLabel, ( 0, 1 ) )
		self.addChild( self.__valueEditor, ( 1, 1 ) )
		self.addChild( self.__interpLabel, ( 0, 2 ) )
		self.addChild( self.__interpEditor, ( 1, 2 ) )
		self.addChild( self.__tieModeLabel, ( 0, 3 ) )
		self.addChild( self.__tieModeEditor, ( 1, 3 ) )

		# curve connections
		self.__connections = {}

		# numeric widget undo queue state
		self.__lastChangedReasonValue = None
		self.__lastChangedReasonFrame = None
		self.__mergeGroupIdValue = 0
		self.__mergeGroupIdFrame = 0

	def connect( self, curve ) :
		if curve not in self.__connections :
			self.__connections[ curve ] = _KeyTab.Connections(
				frame = curve.keyTimeChangedSignal().connect( Gaffer.WeakMethod( self.__keyFrameChanged ), scoped = False ),
				value = curve.keyValueChangedSignal().connect( Gaffer.WeakMethod( self.__keyValueChanged ), scoped = False ),
				tieMode = curve.keyTieModeChangedSignal().connect( Gaffer.WeakMethod( self.__keyTieModeChanged ), scoped = False ),
				interp = curve.keyInterpolatorChangedSignal().connect( Gaffer.WeakMethod( self.__keyInterpolatorChanged ), scoped = False ) )

	def disconnect( self, curve ) :
		if curve in self.__connections :
			for connection in self.__connections[ curve ] :
				connection.disconnect()
			del self.__connections[ curve ]

	def update( self ) :
		self.__updateKeyFrame()
		self.__updateKeyValue()
		self.__updateKeyInterpolator()
		self.__updateKeyTieMode()

	def getTieModeForSelectedKeys( self ) :
		# if multiple keys selected check if all have same tie mode state otherwise return Indeterminate state
		selectedKeys = self.parent().curveGadget().selectedKeys()
		mode = None
		if len( selectedKeys ) > 1 :
			mode = selectedKeys[ 0 ].getTieMode()
			for key in selectedKeys[1:] :
				if mode != key.getTieMode() :
					mode = None
					break
		elif selectedKeys :
			mode = selectedKeys[ 0 ].getTieMode()
		return mode

	def getInterpolatorNameForSelectedKeys( self ) :
		# if multiple keys selected check if all have same interpolator otherwise return None
		selectedKeys = self.parent().curveGadget().selectedKeys()
		name = None
		if len( selectedKeys ) > 1 :
			name = selectedKeys[ 0 ].getInterpolator().getName()
			for key in selectedKeys[1:] :
				if name != key.getInterpolator().getName() :
					name = None
					break
		elif selectedKeys :
			name = selectedKeys[ 0 ].getInterpolator().getName()
		return name

	def __keyFrameChanged( self, curve, key ) :
		if self.parent().curveGadget().isSelectedKey( key ) :
			self.__updateKeyFrame()

	def __keyValueChanged( self, curve, key ) :
		if self.parent().curveGadget().isSelectedKey( key ) :
			self.__updateKeyValue()

	def __keyTieModeChanged( self, curve, key ) :
		if self.parent().curveGadget().isSelectedKey( key ) :
			self.__updateKeyTieMode()

	def __keyInterpolatorChanged( self, curve, key ) :
		if self.parent().curveGadget().isSelectedKey( key ) :
			self.__updateKeyInterpolator()

	def __updateKeyFrame( self ) :

		# if multiple keys selected display "---" unless all selected keys have same value
		# which can only happen when all the keys have different parent curves
		selectedKeys = self.parent().curveGadget().selectedKeys()
		time = None
		if len( selectedKeys ) > 1 :
			time = selectedKeys[ 0 ].getTime()
			for key in selectedKeys[1:] :
				if time != key.getTime() :
					time = None
					break
		elif selectedKeys :
			time = selectedKeys[ 0 ].getTime()
		if time :
			context = selectedKeys[ 0 ].parent().ancestor( Gaffer.ScriptNode ).context()
			frame = int( time.getReal( context.getFramesPerSecond() ) )
			with Gaffer.BlockedConnection( self.__frameConnection ) :
				self.__frameEditor.setValue( frame )
		else :
			with Gaffer.BlockedConnection( self.__frameConnection ) :
				self.__frameEditor.setText( "" )
				self.__frameEditor._qtWidget().setPlaceholderText( "---" )

		# set enabled when all selected keys have different parent curves
		enabled = bool( selectedKeys )
		curves = set()
		for key in selectedKeys :
			if key.parent() in curves :
				enabled = False
				break
			curves.add( key.parent() )
		self.__frameEditor.setEnabled( enabled )

	def __updateKeyValue( self ) :

		# if multiple keys selected display "---" unless all selected keys have same value
		selectedKeys = self.parent().curveGadget().selectedKeys()
		value = None
		if len( selectedKeys ) > 1 :
			value = selectedKeys[ 0 ].getValue()
			for key in selectedKeys[1:] :
				if not Gaffer.Animation.equivalentValues( value, key.getValue() ) :
					value = None
					break
		elif selectedKeys :
			value = selectedKeys[ 0 ].getValue()
		if not value is None :
			with Gaffer.BlockedConnection( self.__valueConnection ) :
				self.__valueEditor.setValue( value )
		else :
			with Gaffer.BlockedConnection( self.__valueConnection ) :
				self.__valueEditor.setText( "" )
				self.__valueEditor._qtWidget().setPlaceholderText( "---" )

		# set disabled when no selected keys
		self.__valueEditor.setEnabled( bool( selectedKeys ) )

	def __updateKeyTieMode( self ) :

		mode = self.getTieModeForSelectedKeys()
		self.__tieModeEditor.setText( "---" if mode is None else mode.name )

		# set disabled when no selected keys
		self.__tieModeEditor.setEnabled( bool( self.parent().curveGadget().selectedKeys() ) )

	def __updateKeyInterpolator( self ) :

		name = self.getInterpolatorNameForSelectedKeys()
		self.__interpEditor.setText( "---" if name is None else name )

		# set disabled when no selected keys
		self.__interpEditor.setEnabled( bool( self.parent().curveGadget().selectedKeys() ) )

	def __setInterpolator( self, unused, name ) :

		# set interpolator for all selected keys
		selectedKeys = self.parent().curveGadget().selectedKeys()
		if selectedKeys :
			with Gaffer.UndoScope( selectedKeys[0].parent().ancestor( Gaffer.ScriptNode ) ) :
				for key in selectedKeys :
					with Gaffer.BlockedConnection( self.__connections[ key.parent() ].interp ) :
						key.setInterpolator( name )
		self.__interpEditor.setText( name )

	def __setTieMode( self, unused, mode ) :

		# set interpolator for all selected keys
		selectedKeys = self.parent().curveGadget().selectedKeys()
		if selectedKeys :
			with Gaffer.UndoScope( selectedKeys[0].parent().ancestor( Gaffer.ScriptNode ) ) :
				for key in selectedKeys :
					with Gaffer.BlockedConnection( self.__connections[ key.parent() ].tieMode ) :
						key.setTieMode( mode )
		self.__tieModeEditor.setText( mode.name )

	def __setFrame( self, widget, reason ) :

		# check for invalid edit
		if reason == GafferUI.NumericWidget.ValueChangedReason.InvalidEdit :
			self.__updateKeyFrame()
			return

		# handle undo queue
		if not widget.changesShouldBeMerged( self.__lastChangedReasonFrame, reason ) :
			self.__mergeGroupIdFrame += 1
		self.__lastChangedReasonFrame = reason

		# only set frame for multiple keys if all selected keys have different parent curves
		# as setting two keys on the same curve to the same frame will delete all but one of the keys.
		selectedKeys = self.parent().curveGadget().selectedKeys()
		if selectedKeys :
			curves = set()
			for key in selectedKeys :
				if key.parent() in curves :
					return
				curves.add( key.parent() )
			try :
				value = int( widget.getValue() )
			except ValueError :
				return
			scriptNode = selectedKeys[0].parent().ancestor( Gaffer.ScriptNode )
			with Gaffer.UndoScope( scriptNode, mergeGroup=str( self.__mergeGroupIdFrame ) ) :
				for key in selectedKeys :
					with Gaffer.BlockedConnection( self.__connections[ key.parent() ].frame ) :
						key.setTime( Gaffer.Animation.Time( value, scriptNode.context().getFramesPerSecond() ) )
			widget.clearUndo()

	def __setValue( self, widget, reason ) :

		# check for invalid edit
		if reason == GafferUI.NumericWidget.ValueChangedReason.InvalidEdit :
			self.__updateKeyValue()
			return

		# handle undo queue
		if not widget.changesShouldBeMerged( self.__lastChangedReasonValue, reason ) :
			self.__mergeGroupIdValue += 1
		self.__lastChangedReasonValue = reason

		# set value for all selected keys
		selectedKeys = self.parent().curveGadget().selectedKeys()
		if selectedKeys :
			try :
				value = widget.getValue()
			except ValueError :
				return
			with Gaffer.UndoScope( selectedKeys[0].parent().ancestor( Gaffer.ScriptNode ), mergeGroup=str( self.__mergeGroupIdValue ) ) :
				for key in selectedKeys :
					with Gaffer.BlockedConnection( self.__connections[ key.parent() ].value ) :
						key.setValue( value )
			widget.clearUndo()

	def __checkBoxStateForInterpolatorName( self, name ) :

		# check if name equals common name of selected keys
		commonName = self.getInterpolatorNameForSelectedKeys()
		return None if commonName is None else commonName == name

	def __checkBoxStateForTieMode( self, mode ) :

		# check if tie mode equals common tie mode of selected keys
		commonMode = self.getTieModeForSelectedKeys()
		return None if commonMode is None else commonMode == mode

# Private implementation - tangent tab
class _TangentTab( GafferUI.GridContainer ) :

	from collections import namedtuple
	Connections = namedtuple( "Connections", ("angle", "weight", "autoMode") )

	def __init__( self ) :

		import functools

		GafferUI.GridContainer.__init__( self, spacing=4 )

		self.__intoLabel = GafferUI.Label( text="Into" )
		self.__fromLabel = GafferUI.Label( text="From" )
		self.__angleLabel = GafferUI.Label( text="Angle" )
		self.__weightLabel = GafferUI.Label( text="Weight" )
		#self.__modeLabel = GafferUI.Label( text="Auto mode" )

		# create editors
		# NOTE: initial value type (e.g. int or float) determines validated value type of widget
		self.__angleEditor = (
			GafferUI.NumericWidget( value=float(0) ),
			GafferUI.NumericWidget( value=float(0) ) )
		self.__weightEditor = (
			GafferUI.NumericWidget( value=float(0) ),
			GafferUI.NumericWidget( value=float(0) ) )
		#self.__intoModeEditor = GafferUI.Button()
		#self.__fromModeEditor = GafferUI.Button()

		# setup editor connections
		self.__angleConnection = (
			self.__angleEditor[ Gaffer.Animation.Tangent.Direction.Into ].valueChangedSignal().connect(
				functools.partial( Gaffer.WeakMethod( self.__setAngle ), Gaffer.Animation.Tangent.Direction.Into ), scoped = False ),
			self.__angleEditor[ Gaffer.Animation.Tangent.Direction.From ].valueChangedSignal().connect(
				functools.partial( Gaffer.WeakMethod( self.__setAngle ), Gaffer.Animation.Tangent.Direction.From ), scoped = False ) )
		self.__weightConnection = (
			self.__weightEditor[ Gaffer.Animation.Tangent.Direction.Into ].valueChangedSignal().connect(
				functools.partial( Gaffer.WeakMethod( self.__setWeight ), Gaffer.Animation.Tangent.Direction.Into ), scoped = False ),
			self.__weightEditor[ Gaffer.Animation.Tangent.Direction.From ].valueChangedSignal().connect(
				functools.partial( Gaffer.WeakMethod( self.__setWeight ), Gaffer.Animation.Tangent.Direction.From ), scoped = False ) )

		# layout widgets
		self.addChild( self.__intoLabel, ( 1, 0 ) )
		self.addChild( self.__fromLabel, ( 2, 0 ) )
		self.addChild( self.__angleLabel, ( 0, 1 ) )
		self.addChild( self.__angleEditor[ Gaffer.Animation.Tangent.Direction.Into ], ( 1, 1 ) )
		self.addChild( self.__angleEditor[ Gaffer.Animation.Tangent.Direction.From ], ( 2, 1 ) )
		self.addChild( self.__weightLabel, ( 0, 2 ) )
		self.addChild( self.__weightEditor[ Gaffer.Animation.Tangent.Direction.Into ], ( 1, 2 ) )
		self.addChild( self.__weightEditor[ Gaffer.Animation.Tangent.Direction.From ], ( 2, 2 ) )
		#self.addChild( self.__modeLabel, ( 0, 3 ) )
		#self.addChild( self.__intoModeEditor, ( 1, 3 ) )
		#self.addChild( self.__fromModeEditor, ( 2, 3 ) )

		# curve connections
		self.__connections = {}

		# numeric widget undo queue state
		self.__lastChangedReasonAngle = [ None, None ]
		self.__lastChangedReasonWeight = [ None, None ]
		self.__mergeGroupIdAngle = [ 0, 0 ]
		self.__mergeGroupIdWeight = [ 0, 0 ]

		# weight of selected keys at start of merge group
		self.__selectedKeysMergeGroupWeight = [ {}, {} ]

	def connect( self, curve ) :
		if curve not in self.__connections :
			self.__connections[ curve ] = _TangentTab.Connections(
				angle = curve.keyTangentAngleChangedSignal().connect( Gaffer.WeakMethod( self.__keyTangentAngleChanged ), scoped = False ),
				weight = curve.keyTangentWeightChangedSignal().connect( Gaffer.WeakMethod( self.__keyTangentWeightChanged ), scoped = False ),
				autoMode = curve.keyTangentAutoModeChangedSignal().connect( Gaffer.WeakMethod( self.__keyTangentAutoModeChanged ), scoped = False ) )

	def disconnect( self, curve ) :
		if curve in self.__connections :
			for connection in self.__connections[ curve ] :
				connection.disconnect()
			del self.__connections[ curve ]

	def update( self ) :
		for direction in Gaffer.Animation.Tangent.Direction.names.values() :
			self.__updateTangentAngle( direction )
			self.__updateTangentWeight( direction )
			#self.__updateTangentAutoMode( direction )

	def __keyTangentAngleChanged( self, curve, key, direction ) :
		if self.parent().curveGadget().isSelectedKey( key ) :
			self.__updateTangentAngle( direction )

	def __keyTangentWeightChanged( self, curve, key, direction ) :
		if self.parent().curveGadget().isSelectedKey( key ) :
			self.__updateTangentWeight( direction )

	def __keyTangentAutoModeChanged( self, curve, key, direction ) :
		if self.parent().curveGadget().isSelectedKey( key ) :
			self.__updateTangentAutoMode( direction )

	def __updateTangentAngle( self, direction ) :

		# if multiple keys selected display "---" unless all selected keys have same angle for tangent direction
		selectedKeys = self.parent().curveGadget().selectedKeys()
		value = None
		if len( selectedKeys ) > 1 :
			value = selectedKeys[ 0 ].getTangent( direction ).getAngle()
			for key in selectedKeys[1:] :
				if not Gaffer.Animation.equivalentValues( value, key.getTangent( direction ).getAngle() ) :
					value = None
					break
		elif selectedKeys :
			value = selectedKeys[ 0 ].getTangent( direction ).getAngle()
		if not value is None :
			with Gaffer.BlockedConnection( self.__angleConnection[ direction ] ) :
				self.__angleEditor[ direction ].setValue( value )
		else :
			with Gaffer.BlockedConnection( self.__angleConnection[ direction ] ) :
				self.__angleEditor[ direction ].setText( "" )
				self.__angleEditor[ direction ]._qtWidget().setPlaceholderText( "---" )

		# set disabled when no selected keys or angle is not used
		enabled = bool( selectedKeys )
		for key in selectedKeys :
			if not key.getTangent( direction ).angleIsUsed() :
				enabled = False
				break
		self.__angleEditor[ direction ].setEnabled( enabled )

	def __updateTangentWeight( self, direction ) :

		# if multiple keys selected display "---" unless all selected keys have same weight for tangent direction
		selectedKeys = self.parent().curveGadget().selectedKeys()
		value = None
		if len( selectedKeys ) > 1 :
			value = selectedKeys[ 0 ].getTangent( direction ).getWeight()
			for key in selectedKeys[1:] :
				if not Gaffer.Animation.equivalentValues( value, key.getTangent( direction ).getWeight() ) :
					value = None
					break
		elif selectedKeys :
			value = selectedKeys[ 0 ].getTangent( direction ).getWeight()
		if not value is None :
			with Gaffer.BlockedConnection( self.__weightConnection[ direction ] ) :
				self.__weightEditor[ direction ].setValue( value )
		else :
			with Gaffer.BlockedConnection( self.__weightConnection[ direction ] ) :
				self.__weightEditor[ direction ].setText( "" )
				self.__weightEditor[ direction ]._qtWidget().setPlaceholderText( "---" )

		# set disabled when no selected keys or weight is not used
		enabled = bool( selectedKeys )
		for key in selectedKeys :
			if not key.getTangent( direction ).weightIsUsed() :
				enabled = False
				break
		self.__weightEditor[ direction ].setEnabled( enabled )

	def __updateTangentAutoMode( self, direction ) :
		pass

	def __setAngle( self, direction, widget, reason ) :

		# check for invalid edit
		if reason == GafferUI.NumericWidget.ValueChangedReason.InvalidEdit :
			self.__updateTangentAngle( direction )
			return

		# handle undo queue
		selectedKeys = self.parent().curveGadget().selectedKeys()
		if not widget.changesShouldBeMerged( self.__lastChangedReasonAngle[ direction ], reason ) :
			self.__mergeGroupIdAngle[ direction ] += 1
			self.__selectedKeysMergeGroupWeight[ direction ].clear()
			for key in selectedKeys :
				self.__selectedKeysMergeGroupWeight[ direction ][ key ] = key.getTangent( direction ).getWeight()
		self.__lastChangedReasonAngle[ direction ] = reason

		# set angle for all selected keys in specified direction
		if selectedKeys :
			try :
				value = widget.getValue()
			except ValueError :
				return
			with Gaffer.UndoScope( selectedKeys[0].parent().ancestor( Gaffer.ScriptNode ), mergeGroup=str( self.__mergeGroupIdAngle[ direction ] ) ) :
				for key in selectedKeys :
					with Gaffer.BlockedConnection( self.__connections[ key.parent() ].angle ) :
						key.getTangent( direction ).setAngleWithWeight( value,
							self.__selectedKeysMergeGroupWeight[ direction ][ key ] )
			widget.clearUndo()

		# ensure editors are up to date
		for direction in Gaffer.Animation.Tangent.Direction.names.values() :
			self.__updateTangentAngle( direction )
			self.__updateTangentWeight( direction )

	def __setWeight( self, direction, widget, reason ) :

		# check for invalid edit
		if reason == GafferUI.NumericWidget.ValueChangedReason.InvalidEdit :
			self.__updateTangentWeight( direction )
			return

		# handle undo queue
		if not widget.changesShouldBeMerged( self.__lastChangedReasonWeight[ direction ], reason ) :
			self.__mergeGroupIdWeight[ direction ] += 1
		self.__lastChangedReasonWeight[ direction ] = reason

		# set weight for all selected keys in specified direction
		selectedKeys = self.parent().curveGadget().selectedKeys()
		if selectedKeys :
			try :
				value = max( widget.getValue(), float(0) )
			except ValueError :
				return
			with Gaffer.UndoScope( selectedKeys[0].parent().ancestor( Gaffer.ScriptNode ), mergeGroup=str( self.__mergeGroupIdWeight[ direction ] ) ) :
				for key in selectedKeys :
					with Gaffer.BlockedConnection( self.__connections[ key.parent() ].weight ) :
						key.getTangent( direction ).setWeight( value )
			widget.clearUndo()

		# ensure editors are up to date
		for direction in Gaffer.Animation.Tangent.Direction.names.values() :
			self.__updateTangentWeight( direction )

# Private implementation - curve tab
class _CurveTab( GafferUI.GridContainer ) :

	from collections import namedtuple
	Connections = namedtuple( "Connections", ("color", "extrap") )

	def __init__( self ) :

		GafferUI.GridContainer.__init__( self, spacing=4 )

		# curve connections
		self.__connections = {}

	def connect( self, curve ) :
		if curve not in self.__connections :
			self.__connections[ curve ] = _CurveTab.Connections(
				color = curve.colorChangedSignal().connect( Gaffer.WeakMethod( self.__colorChanged ), scoped = False ),
				extrap = curve.extrapolatorChangedSignal().connect( Gaffer.WeakMethod( self.__extrapolatorChanged ), scoped = False ) )

	def disconnect( self, curve ) :
		if curve in self.__connections :
			for connection in self.__connections[ curve ] :
				connection.disconnect()
			del self.__connections[ curve ]

	def update( self ) :
		self.__updateColor()
		for direction in Gaffer.Animation.Tangent.Direction.names.values() :
			self.__updateExtrapolator( direction )

	def __colorChanged( self, curve ) :
		self.__updateColor()

	def __extrapolatorChanged( self, curve, direction ) :
		self.__updateExtrapolator( direction )

	def __updateColor( self ) :
		pass

	def __updateExtrapolator( self, direction ) :
		pass

GafferUI.Editor.registerType( "AnimationEditor", AnimationEditor )
