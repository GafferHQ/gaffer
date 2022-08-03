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

from GafferUI.PlugValueWidget import sole

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

		self.__plugInputChangedConnections = [ node.plugInputChangedSignal().connect( Gaffer.WeakMethod( self.__plugInputChanged ), scoped = True ) for node in selection ]
		self.__nameChangedConnections = []

	def _filter( self, paths, canceller ) :

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
				path.property( "graphComponent:graphComponent" ).nameChangedSignal().connect( Gaffer.WeakMethod( self.__nameChanged ), scoped = True )
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
			selectionMode = GafferUI.PathListingWidget.SelectionMode.Rows,
		)

		self.__curveList._qtWidget().setMinimumSize( 160, 0 )
		self.__curveList._qtWidget().setSizePolicy( QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Ignored )
		self.__curveList.expansionChangedSignal().connect( Gaffer.WeakMethod( self.__updateGadgetSets ), scoped = False )
		self.__selectionChangedConnection = self.__curveList.selectionChangedSignal().connect( Gaffer.WeakMethod( self.__updateGadgetSets ), scoped = False )

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
		self.__curveEditor = _CurveEditor( self.__animationGadget )

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

		self.__pathChangedConnection = self.__curveList.getPath().pathChangedSignal().connect( Gaffer.WeakMethod( self.__updateGadgetSets ), scoped = True )
		self.__updateGadgetSets()

	def _updateFromContext( self, modifiedItems ) :

		self.__animationGadget.setContext( self.getContext() )

	def __updateGadgetSets( self, unused = None ) :

		visiblePlugs = set()
		path = self.__curveList.getPath().copy()
		for name in self.__curveList.getExpansion().paths() :
			path.setFromString( name )
			for childPath in path.children() :
				child = childPath.property( "graphComponent:graphComponent" )
				if isinstance( child, Gaffer.ValuePlug ) and Gaffer.Animation.isAnimated( child ) :
					visiblePlugs.add( child )

		visible = self.__animationGadget.visiblePlugs()
		visible.clear()
		for plug in visiblePlugs :
			visible.add( self.__sourceCurvePlug( plug ) )

		editablePlugs = set()
		for name in self.__curveList.getSelection().paths() :
			path.setFromString( name )
			try :
				# NOTE : path.property() will throw a KeyError exception if the parent
				#        node has been deleted since we last updated in which case we
				#        dont want to add the curve to the editable set so we pass.
				# TODO : Could path.property() return None instead of raising an exception?
				graphComponent = path.property( "graphComponent:graphComponent" )
			except KeyError :
				pass
			else :
				if isinstance( graphComponent, Gaffer.ValuePlug ) and Gaffer.Animation.isAnimated( graphComponent ) :
					editablePlugs.add( graphComponent )
				for child in graphComponent.children() :
					if isinstance( child, Gaffer.ValuePlug ) and Gaffer.Animation.isAnimated( child ) :
						editablePlugs.add( child )

		editable = self.__animationGadget.editablePlugs()
		curves = set( self.__sourceCurvePlug( plug ) for plug in editablePlugs & visiblePlugs )
		with Gaffer.Signals.BlockedConnection( self.__editablePlugsConnections ) :
			for curve in list( editable ) :
				if curve in curves :
					curves.remove( curve )
				else :
					editable.remove( curve )
			for curve in curves :
				editable.add( curve )

	def __editablePlugAdded( self, standardSet, curvePlug ) :

		root = self.__curveList.getPath().property( "graphComponent:graphComponent" )

		selection = self.__curveList.getSelection()
		for output in curvePlug["out"].outputs() :
			selection.addPath(
				output.relativeName( root ).replace( ".", "/" )
			)

		with Gaffer.Signals.BlockedConnection( self.__selectionChangedConnection ) :
			self.__curveList.setSelection( selection )

	def __editablePlugRemoved( self, standardSet, curvePlug ) :

		root = self.__curveList.getPath().property( "graphComponent:graphComponent" )

		selection = self.__curveList.getSelection()
		for output in curvePlug["out"].outputs() :
			selection.removePath(
				output.relativeName( root ).replace( ".", "/" )
			)

		with Gaffer.Signals.BlockedConnection( self.__selectionChangedConnection ) :
			self.__curveList.setSelection( selection )

	def __sourceCurvePlug( self, plug ) :

		result = plug.source().parent()
		assert( isinstance( result, Gaffer.Animation.CurvePlug ) )
		return result

	def __animationGadgetContextMenu( self, *unused ) :

		import IECore
		import functools

		# convert mouse position to event line
		line = self.__gadgetWidget.getViewportGadget().rasterToGadgetSpace(
			imath.V2f( GafferUI.Widget.mousePosition( relativeTo = self.__gadgetWidget ) ), gadget = self.__animationGadget )

		# only show context menu when mouse not above axis
		if self.__animationGadget.onTimeAxis( line ) or self.__animationGadget.onValueAxis( line ) :
			return False

		# check there are selected keys
		emptySelectedKeys = not self.__animationGadget.selectedKeys()

		# tie mode for selected keys
		tieMode = None if emptySelectedKeys else self.__curveEditor.keyWidget().getTieModeForSelectedKeys()

		# key interpolation for selected keys
		interpolation = None if emptySelectedKeys else self.__curveEditor.keyWidget().getInterpolationForSelectedKeys()

		# build context menu
		menuDefinition = IECore.MenuDefinition()

		for mode in sorted( Gaffer.Animation.Interpolation.values.values() ) :
			menuDefinition.append(
				"/Interpolation/%s" % ( mode.name ),
				{
					"command" : functools.partial(
						Gaffer.WeakMethod( self.__setSelectedKeysInterpolation ),
						mode=mode
					),
					"active" : not emptySelectedKeys,
					"checkBox" : interpolation == mode
				}
			)

		for mode in sorted( Gaffer.Animation.TieMode.values.values() ) :
			menuDefinition.append(
				"/Tie Mode/%s" % ( mode.name ),
				{
					"command" : functools.partial(
						Gaffer.WeakMethod( self.__setSelectedKeysTieMode ),
						mode=mode
					),
					"active" : not emptySelectedKeys,
					"checkBox" : tieMode == mode
				}
			)

		self.__popupMenu = GafferUI.Menu( menuDefinition, title="Selected Keys" )
		self.__popupMenu.popup( parent = self )

		return True

	def __setSelectedKeysInterpolation( self, unused, mode ) :

		with Gaffer.UndoScope( self.scriptNode() ) :
			for key in self.__animationGadget.selectedKeys() :
				key.setInterpolation( mode )

	def __setSelectedKeysTieMode( self, unused, mode ) :

		with Gaffer.UndoScope( self.scriptNode() ) :
			for key in self.__animationGadget.selectedKeys() :
				key.setTieMode( mode )

	def __repr__( self ) :

		return "GafferUI.AnimationEditor( scriptNode )"

# Private implementation - tab widget
class _CurveEditor( GafferUI.TabbedContainer ) :

	def __init__( self, curveGadget ) :

		GafferUI.TabbedContainer.__init__( self )

		# store curve set and gadget
		self.__curveGadget = curveGadget

		# create widgets
		self.__keyWidget = _KeyWidget()

		# set tab ordering
		self.append( self.__keyWidget, "Key" )

		# set up signals
		self.__curveGadget.selectedKeys().memberAddedSignal().connect(
			Gaffer.WeakMethod( self.__selectedKeysKeyAdded ), scoped = False )
		self.__curveGadget.selectedKeys().memberRemovedSignal().connect(
			Gaffer.WeakMethod( self.__selectedKeysKeyRemoved ), scoped = False )
		self.__curveGadget.editablePlugs().memberAddedSignal().connect(
			Gaffer.WeakMethod( self.__curveSelected ), scoped = False ),
		self.__curveGadget.editablePlugs().memberRemovedSignal().connect(
			Gaffer.WeakMethod( self.__curveDeselected ), scoped = False )

		# update all tabs
		for tab in self :
			tab.update()

	def curveGadget( self ) :
		return self.__curveGadget

	def keyWidget( self ) :
		return self.__keyWidget

	def __selectedKeysChanged( self ) :
		self.__keyWidget.update()

	@GafferUI.LazyMethod()
	def __selectedKeysKeyAdded( self, set, key ) :
		self.__selectedKeysChanged()

	@GafferUI.LazyMethod()
	def __selectedKeysKeyRemoved( self, set, key ) :
		self.__selectedKeysChanged()

	def __curveSelected( self, unused, curve ) :
		for tab in self :
			tab.connect( curve )

	def __curveDeselected( self, unused, curve ) :
		for tab in self :
			tab.disconnect( curve )

# Private implementation - key widget
class _KeyWidget( GafferUI.GridContainer ) :

	from collections import namedtuple
	Connections = namedtuple( "Connections", ("frame", "value", "interpolation", "tieMode", "tangent") )

	def __init__( self ) :

		import IECore
		import functools

		GafferUI.GridContainer.__init__( self, spacing=4, borderWidth=4 )

		# tool tips
		frameToolTip = "# Frame\n\nThe frame of the currently selected keys."
		valueToolTip = "# Value\n\nThe value of the currently selected keys."
		interpolationToolTip = "# Interpolation\n\nThe interpolation of the currently selected keys."
		tieModeToolTip = "# Tie Mode\n\nThe tie mode of the currently selected keys."
		slopeToolTip = "# Slope\n\nThe slope of the %stangents of the currently selected keys."
		scaleToolTip = "# Scale\n\nThe scale of the %stangents of the currently selected keys."

		# create labels
		frameLabel = GafferUI.Label( text="Frame", toolTip=frameToolTip )
		valueLabel = GafferUI.Label( text="Value", toolTip=valueToolTip )
		interpolationLabel = GafferUI.Label( text="Interpolation", toolTip=interpolationToolTip )
		tieModeLabel = GafferUI.Label( text="Tie Mode", toolTip=tieModeToolTip )
		slopeLabel = GafferUI.Label( text="Slope", toolTip=( slopeToolTip % "" ) )
		scaleLabel = GafferUI.Label( text="Scale", toolTip=( scaleToolTip % "" ) )

		# create editors
		# NOTE: initial value type (e.g. int or float) determines validated value type of widget
		self.__frameEditor = GafferUI.NumericWidget( value=int(0), toolTip=frameToolTip )
		self.__valueEditor = GafferUI.NumericWidget( value=float(0), toolTip=valueToolTip )
		self.__interpolationEditor = GafferUI.MenuButton( toolTip=interpolationToolTip )
		self.__tieModeEditor = GafferUI.MenuButton( toolTip=tieModeToolTip )
		self.__slopeEditor = (
			GafferUI.NumericWidget( value=float(0), toolTip=( slopeToolTip % "in " ) ),
			GafferUI.NumericWidget( value=float(0), toolTip=( slopeToolTip % "out " ) ) )
		self.__scaleEditor = (
			GafferUI.NumericWidget( value=float(0), toolTip=( scaleToolTip % "in " ) ),
			GafferUI.NumericWidget( value=float(0), toolTip=( scaleToolTip % "out " ) ) )

		# build interpolation menu
		im = IECore.MenuDefinition()
		for mode in sorted( Gaffer.Animation.Interpolation.values.values() ) :
			im.append( "%s" % ( mode.name ), {
				"command" : functools.partial( Gaffer.WeakMethod( self.__setInterpolation ), mode=mode ),
				"checkBox" : functools.partial( Gaffer.WeakMethod( self.__checkBoxStateForKeyInterpolation ), mode=mode ) } )
		self.__interpolationEditor.setMenu( GafferUI.Menu( im ) )

		# build tie mode menu
		tm = IECore.MenuDefinition()
		for mode in sorted( Gaffer.Animation.TieMode.values.values() ) :
			tm.append( "%s" % ( mode.name ), {
				"command" : functools.partial( Gaffer.WeakMethod( self.__setTieMode ), mode=mode ),
				"checkBox" : functools.partial( Gaffer.WeakMethod( self.__checkBoxStateForTieMode ), mode=mode ) } )
		self.__tieModeEditor.setMenu( GafferUI.Menu( tm ) )

		# setup editor connections
		self.__frameConnection = self.__frameEditor.valueChangedSignal().connect(
			Gaffer.WeakMethod( self.__setFrame ), scoped = False )
		self.__valueConnection = self.__valueEditor.valueChangedSignal().connect(
			Gaffer.WeakMethod( self.__setValue ), scoped = False )
		self.__slopeConnection = (
			self.__slopeEditor[ Gaffer.Animation.Direction.In ].valueChangedSignal().connect(
				functools.partial( Gaffer.WeakMethod( self.__setSlope ), Gaffer.Animation.Direction.In ), scoped = False ),
			self.__slopeEditor[ Gaffer.Animation.Direction.Out ].valueChangedSignal().connect(
				functools.partial( Gaffer.WeakMethod( self.__setSlope ), Gaffer.Animation.Direction.Out ), scoped = False ) )
		self.__scaleConnection = (
			self.__scaleEditor[ Gaffer.Animation.Direction.In ].valueChangedSignal().connect(
				functools.partial( Gaffer.WeakMethod( self.__setScale ), Gaffer.Animation.Direction.In ), scoped = False ),
			self.__scaleEditor[ Gaffer.Animation.Direction.Out ].valueChangedSignal().connect(
				functools.partial( Gaffer.WeakMethod( self.__setScale ), Gaffer.Animation.Direction.Out ), scoped = False ) )

		# layout widgets
		alignment = ( GafferUI.HorizontalAlignment.Right, GafferUI.VerticalAlignment.Center )
		self.addChild( frameLabel, index=( 0, 0 ), alignment=alignment )
		self[ 1:3, 0 ] = self.__frameEditor
		self.addChild( valueLabel, index=( 0, 1 ), alignment=alignment )
		self[ 1:3, 1 ] = self.__valueEditor
		self.addChild( interpolationLabel, index=( 0, 2 ), alignment=alignment )
		self[ 1:3, 2 ] = self.__interpolationEditor
		self.addChild( tieModeLabel, index=( 0, 3 ), alignment=alignment )
		self[ 1:3, 3 ] = self.__tieModeEditor
		self[ 0:3, 4 ] = GafferUI.Divider()
		self.addChild( slopeLabel, index=( 0, 5 ), alignment=alignment )
		self[ 1, 5 ] = self.__slopeEditor[ Gaffer.Animation.Direction.In ]
		self[ 2, 5 ] = self.__slopeEditor[ Gaffer.Animation.Direction.Out ]
		self.addChild( scaleLabel, index=( 0, 6 ), alignment=alignment )
		self[ 1, 6 ] = self.__scaleEditor[ Gaffer.Animation.Direction.In ]
		self[ 2, 6 ] = self.__scaleEditor[ Gaffer.Animation.Direction.Out ]

		# curve connections
		self.__connections = {}

		# numeric widget undo queue state
		self.__lastChangedReasonValue = None
		self.__lastChangedReasonFrame = None
		self.__lastChangedReasonSlope = [ None, None ]
		self.__lastChangedReasonScale = [ None, None ]
		self.__mergeGroupIdValue = 0
		self.__mergeGroupIdFrame = 0
		self.__mergeGroupIdSlope = [ 0, 0 ]
		self.__mergeGroupIdScale = [ 0, 0 ]

		# scale of selected keys at start of merge group
		self.__selectedKeysMergeGroupScale = [ {}, {} ]

	def connect( self, curve ) :
		if curve not in self.__connections :
			self.__connections[ curve ] = _KeyWidget.Connections(
				frame = curve.keyTimeChangedSignal().connect( Gaffer.WeakMethod( self.__keyFrameChanged ), scoped = False ),
				value = curve.keyValueChangedSignal().connect( Gaffer.WeakMethod( self.__keyValueChanged ), scoped = False ),
				interpolation = curve.keyInterpolationChangedSignal().connect( Gaffer.WeakMethod( self.__keyInterpolationChanged ), scoped = False ),
				tieMode = curve.keyTieModeChangedSignal().connect( Gaffer.WeakMethod( self.__keyTieModeChanged ), scoped = False ),
				tangent = curve.node().plugDirtiedSignal().connect( Gaffer.WeakMethod( self.__keyTangentChanged ), scoped = False ) )

	def disconnect( self, curve ) :
		if curve in self.__connections :
			for connection in self.__connections[ curve ] :
				connection.disconnect()
			del self.__connections[ curve ]

	def update( self ) :
		self.__updateKeyFrame()
		self.__updateKeyValue()
		self.__updateKeyInterpolation()
		self.__updateKeyTieMode()
		self.__updateKeyTangents()

	def getTieModeForSelectedKeys( self ) :
		# if multiple keys selected check if all have same tie mode otherwise return None
		return sole( key.getTieMode() for key in self.parent().curveGadget().selectedKeys() )

	def getInterpolationForSelectedKeys( self ) :
		# if multiple keys selected check if all have same interpolation otherwise return None
		return sole( key.getInterpolation() for key in self.parent().curveGadget().selectedKeys() )

	def __keyFrameChanged( self, curve, key ) :
		if self.parent().curveGadget().selectedKeys().contains( key ) :
			self.__updateKeyFrame()

	def __keyValueChanged( self, curve, key ) :
		if self.parent().curveGadget().selectedKeys().contains( key ) :
			self.__updateKeyValue()

	def __keyInterpolationChanged( self, curve, key ) :
		if self.parent().curveGadget().selectedKeys().contains( key ) :
			self.__updateKeyInterpolation()

	def __keyTieModeChanged( self, curve, key ) :
		if self.parent().curveGadget().selectedKeys().contains( key ) :
			self.__updateKeyTieMode()

	@GafferUI.LazyMethod()
	def __keyTangentChanged( self, unused ) :
		self.__updateKeyTangents()

	def __updateKeyFrame( self ) :

		# if multiple keys selected display "---" unless all selected keys have same value
		# which can only happen when all the keys have different parent curves
		selectedKeys = self.parent().curveGadget().selectedKeys()
		time = sole( key.getTime() for key in selectedKeys )
		if time is not None :
			context = selectedKeys[ 0 ].parent().ancestor( Gaffer.ScriptNode ).context()
			frame = int( round( time * context.getFramesPerSecond() ) )
			with Gaffer.Signals.BlockedConnection( self.__frameConnection ) :
				self.__frameEditor.setValue( frame )
		else :
			with Gaffer.Signals.BlockedConnection( self.__frameConnection ) :
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
		value = sole( key.getValue() for key in selectedKeys )
		if value is not None :
			with Gaffer.Signals.BlockedConnection( self.__valueConnection ) :
				self.__valueEditor.setValue( value )
		else :
			with Gaffer.Signals.BlockedConnection( self.__valueConnection ) :
				self.__valueEditor.setText( "" )
				self.__valueEditor._qtWidget().setPlaceholderText( "---" )

		# set disabled when no selected keys
		self.__valueEditor.setEnabled( bool( selectedKeys ) )

	def __updateKeyInterpolation( self ) :

		mode = self.getInterpolationForSelectedKeys()
		self.__interpolationEditor.setText( "---" if mode is None else mode.name )

		# set disabled when no selected keys
		self.__interpolationEditor.setEnabled( bool( self.parent().curveGadget().selectedKeys() ) )

	def __updateKeyTieMode( self ) :

		mode = self.getTieModeForSelectedKeys()
		self.__tieModeEditor.setText( "---" if mode is None else mode.name )

		# set disabled when no selected keys
		self.__tieModeEditor.setEnabled( bool( self.parent().curveGadget().selectedKeys() ) )

	def __updateKeyTangents( self ) :

		for direction in Gaffer.Animation.Direction.names.values() :
			self.__updateTangentSlope( direction )
			self.__updateTangentScale( direction )

	def __updateTangentSlope( self, direction ) :

		# if multiple keys selected display "---" unless all selected keys have same slope for tangent direction
		selectedKeys = self.parent().curveGadget().selectedKeys()
		value = sole( key.tangent( direction ).getSlope() for key in selectedKeys )
		if value is not None :
			with Gaffer.Signals.BlockedConnection( self.__slopeConnection[ direction ] ) :
				self.__slopeEditor[ direction ].setValue( value )
		else :
			with Gaffer.Signals.BlockedConnection( self.__slopeConnection[ direction ] ) :
				self.__slopeEditor[ direction ].setText( "" )
				self.__slopeEditor[ direction ]._qtWidget().setPlaceholderText( "---" )

		# set disabled when no selected keys or slope is constrained by interpolation mode
		enabled = bool( selectedKeys )
		for key in selectedKeys :
			if key.tangent( direction ).slopeIsConstrained() :
				enabled = False
				break
		self.__slopeEditor[ direction ].setEnabled( enabled )

	def __updateTangentScale( self, direction ) :

		# if multiple keys selected display "---" unless all selected keys have same scale for tangent direction
		selectedKeys = self.parent().curveGadget().selectedKeys()
		value = sole( key.tangent( direction ).getScale() for key in selectedKeys )
		if value is not None :
			with Gaffer.Signals.BlockedConnection( self.__scaleConnection[ direction ] ) :
				self.__scaleEditor[ direction ].setValue( value )
		else :
			with Gaffer.Signals.BlockedConnection( self.__scaleConnection[ direction ] ) :
				self.__scaleEditor[ direction ].setText( "" )
				self.__scaleEditor[ direction ]._qtWidget().setPlaceholderText( "---" )

		# set disabled when no selected keys or scale is constrained by interpolation mode
		enabled = bool( selectedKeys )
		for key in selectedKeys :
			if key.tangent( direction ).scaleIsConstrained() :
				enabled = False
				break
		self.__scaleEditor[ direction ].setEnabled( enabled )

	def __setInterpolation( self, unused, mode ) :

		# set interpolation for all selected keys
		selectedKeys = self.parent().curveGadget().selectedKeys()
		if selectedKeys :
			with Gaffer.UndoScope( selectedKeys[0].parent().ancestor( Gaffer.ScriptNode ) ) :
				for key in selectedKeys :
					with Gaffer.Signals.BlockedConnection( self.__connections[ key.parent() ].interpolation ) :
						key.setInterpolation( mode )
		self.__interpolationEditor.setText( mode.name )

	def __setTieMode( self, unused, mode ) :

		# set tie mode for all selected keys
		selectedKeys = self.parent().curveGadget().selectedKeys()
		if selectedKeys :
			with Gaffer.UndoScope( selectedKeys[0].parent().ancestor( Gaffer.ScriptNode ) ) :
				for key in selectedKeys :
					with Gaffer.Signals.BlockedConnection( self.__connections[ key.parent() ].tieMode ) :
						key.setTieMode( mode )
		self.__tieModeEditor.setText( mode.name )

	def __setFrame( self, widget, reason ) :

		# check for invalid edit
		if reason == GafferUI.NumericWidget.ValueChangedReason.InvalidEdit :
			self.__updateKeyFrame()
			return

		# handle undo queue
		if not widget.changesShouldBeMerged( self.__lastChangedReasonFrame, reason ) :
			curves = self.parent().curveGadget().editablePlugs()
			if curves :
				scriptNode = curves[0].ancestor( Gaffer.ScriptNode )
				with Gaffer.UndoScope( scriptNode, mergeGroup=str( self.__mergeGroupIdFrame ) ) :
					for curve in curves :
						curve.removeInactiveKeys()
			self.__mergeGroupIdFrame += 1
		self.__lastChangedReasonFrame = reason

		# set frame for selected keys
		selectedKeys = self.parent().curveGadget().selectedKeys()
		if selectedKeys :
			try :
				value = int( widget.getValue() )
			except ValueError :
				return
			scriptNode = selectedKeys[0].parent().ancestor( Gaffer.ScriptNode )
			time = value / scriptNode.context().getFramesPerSecond()
			with Gaffer.UndoScope( scriptNode, mergeGroup=str( self.__mergeGroupIdFrame ) ) :
				for key in selectedKeys :
					with Gaffer.Signals.BlockedConnection( self.__connections[ key.parent() ].frame ) :
						key.setTime( time )
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
					with Gaffer.Signals.BlockedConnection( self.__connections[ key.parent() ].value ) :
						key.setValue( value )
			widget.clearUndo()

	def __setSlope( self, direction, widget, reason ) :

		# check for invalid edit
		if reason == GafferUI.NumericWidget.ValueChangedReason.InvalidEdit :
			self.__updateTangentSlope( direction )
			return

		# handle undo queue
		selectedKeys = self.parent().curveGadget().selectedKeys()
		if not widget.changesShouldBeMerged( self.__lastChangedReasonSlope[ direction ], reason ) :
			self.__mergeGroupIdSlope[ direction ] += 1
			self.__selectedKeysMergeGroupScale[ direction ].clear()
			for key in selectedKeys :
				self.__selectedKeysMergeGroupScale[ direction ][ key ] = key.tangent( direction ).getScale()
		self.__lastChangedReasonSlope[ direction ] = reason

		# set slope for all selected keys in specified direction
		if selectedKeys :
			try :
				value = widget.getValue()
			except ValueError :
				return
			with Gaffer.UndoScope( selectedKeys[0].parent().ancestor( Gaffer.ScriptNode ), mergeGroup=str( self.__mergeGroupIdSlope[ direction ] ) ) :
				for key in selectedKeys :
					with Gaffer.Signals.BlockedConnection( self.__connections[ key.parent() ].tangent ) :
						key.tangent( direction ).setSlopeAndScale( value,
							self.__selectedKeysMergeGroupScale[ direction ][ key ] )
			widget.clearUndo()

		# ensure editors are up to date
		for direction in Gaffer.Animation.Direction.names.values() :
			self.__updateTangentSlope( direction )
			self.__updateTangentScale( direction )

	def __setScale( self, direction, widget, reason ) :

		# check for invalid edit
		if reason == GafferUI.NumericWidget.ValueChangedReason.InvalidEdit :
			self.__updateTangentScale( direction )
			return

		# handle undo queue
		if not widget.changesShouldBeMerged( self.__lastChangedReasonScale[ direction ], reason ) :
			self.__mergeGroupIdScale[ direction ] += 1
		self.__lastChangedReasonScale[ direction ] = reason

		# set scale for all selected keys in specified direction
		selectedKeys = self.parent().curveGadget().selectedKeys()
		if selectedKeys :
			try :
				value = max( widget.getValue(), float(0) )
			except ValueError :
				return
			with Gaffer.UndoScope( selectedKeys[0].parent().ancestor( Gaffer.ScriptNode ), mergeGroup=str( self.__mergeGroupIdScale[ direction ] ) ) :
				for key in selectedKeys :
					with Gaffer.Signals.BlockedConnection( self.__connections[ key.parent() ].tangent ) :
						key.tangent( direction ).setScale( value )
			widget.clearUndo()

		# ensure editors are up to date
		for direction in Gaffer.Animation.Direction.names.values() :
			self.__updateTangentScale( direction )

	def __checkBoxStateForKeyInterpolation( self, mode ) :

		# check if mode equals common mode of selected keys
		commonMode = self.getInterpolationForSelectedKeys()
		return None if commonMode is None else commonMode == mode

	def __checkBoxStateForTieMode( self, mode ) :

		# check if tie mode equals common tie mode of selected keys
		commonMode = self.getTieModeForSelectedKeys()
		return None if commonMode is None else commonMode == mode

GafferUI.Editor.registerType( "AnimationEditor", AnimationEditor )
