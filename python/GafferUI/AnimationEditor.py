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
import imath

import Gaffer
import GafferScene
import GafferUI

from Qt import QtWidgets

# In order to have Widgets that depend on this filter update properly, we
# conceptually treat all selected nodes as part of the filter. That makes sense
# as the filtering result depends on the nodes' inputs. We can then emit the
# filterChangedSignal if an AnimationNode was added or removed as input to the
# filtered node.
# We use the same mechanism to signal to Widgets that the name of a component
# of a path has changed. That probably makes less sense and should be looked into. \todo
class _AnimationPathFilter( Gaffer.PathFilter ) :

	def __init__( self, scriptNode, userData = {}, selection = None ) :

		Gaffer.PathFilter.__init__( self, userData )

		self.__scriptNode = scriptNode
		self.__selection = selection or []

		self.__plugInputChangedConnections = []
		self.__nameChangedConnections = []

	def setSelection( self, selection ) :
		self.__selection = selection
		self.__plugInputChangedConnections = [ node.plugInputChangedSignal().connect( Gaffer.WeakMethod( self.__plugInputChanged ) ) for node in selection ]

		self.changedSignal()( self )

	def __hasAnimatedChild( self, graphComponent ) :

		for child in graphComponent.children() :

			if isinstance( child, Gaffer.ValuePlug ) and Gaffer.Animation.isAnimated( child ) :
				return True

			if self.__hasAnimatedChild( child ) :
				return True

		return False

	def __plugInputChanged( self, plug ) :
		# TODO: We can be a bit more selective here and only trigger updates
		# when an AnimationNode is involved.
		self.changedSignal()( self )

	def __nameChanged( self, graphComponent ) :
		# TODO: Conceptually it doesn't make a lot of sense to have this here. I'm sure there's a better way.
		self.changedSignal()( self )

	def _filter( self, paths ) :
		result = []

		for path in paths :
			candidateGraphComponent = self.__scriptNode.descendant( str( path )[1:].replace('/', '.') )

			if not isinstance( candidateGraphComponent, ( Gaffer.Node, Gaffer.Plug ) ) :
				continue

			for selected in self.__selection :

				if not candidateGraphComponent == selected and not selected.isAncestorOf( candidateGraphComponent ) and not candidateGraphComponent.isAncestorOf( selected ) :
					continue

				if ( isinstance( candidateGraphComponent, Gaffer.ValuePlug ) and Gaffer.Animation.isAnimated( candidateGraphComponent ) ) or self.__hasAnimatedChild( candidateGraphComponent ) :
					# If we show this component, we should be aware when its name is changes.
					self.__nameChangedConnections.append( candidateGraphComponent.nameChangedSignal().connect( Gaffer.WeakMethod( self.__nameChanged ) ) )
					result.append( path )

		return result

class AnimationEditor( GafferUI.NodeSetEditor ) :

	def __init__( self, scriptNode, **kw ) :

		self.__main = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, borderWidth = 5, spacing = 5 )
		self.__scriptNode = scriptNode

		GafferUI.NodeSetEditor.__init__( self, self.__main, self.__scriptNode, **kw )

		# Set up widget for curve names on the left
		self.__animationFilter = _AnimationPathFilter( scriptNode )
		self.__curveList = GafferUI.PathListingWidget(
			Gaffer.GraphComponentPath( scriptNode, '/', filter = self.__animationFilter ),
			columns = ( GafferUI.PathListingWidget.defaultNameColumn, ),
			displayMode = GafferUI.PathListingWidget.DisplayMode.Tree,
			allowMultipleSelection=True
		)

		self.__curveList._qtWidget().setMinimumSize( 160, 0 )
		self.__curveList._qtWidget().setSizePolicy( QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Ignored )
		self.__expansionChangedConnection = self.__curveList.expansionChangedSignal().connect( Gaffer.WeakMethod( self.__expansionChanged ) )
		self.__selectionChangedConnection = self.__curveList.selectionChangedSignal().connect( Gaffer.WeakMethod( self.__selectionChanged ) )

		# Set up the widget responsible for actual curve drawing
		self.__animationGadget = GafferUI.AnimationGadget()

		# Set up signals needed to update selection state in PathListingWidget
		editable = self.__animationGadget.editablePlugs()
		self.__editablePlugAddedConnection = editable.memberAddedSignal().connect( Gaffer.WeakMethod( self.__editablePlugAdded ) )

		self.__gadgetWidget = GafferUI.GadgetWidget(
			bufferOptions = set(
				[ GafferUI.GLWidget.BufferOptions.Depth,
				  GafferUI.GLWidget.BufferOptions.Double, ] ), )

		self.__gadgetWidget.getViewportGadget().setPrimaryChild( self.__animationGadget )
		self.__gadgetWidget.getViewportGadget().setDragTracking( True )
		self.__gadgetWidget.getViewportGadget().setVariableAspectZoom( True )

		# Assemble UI
		self.__splitter = GafferUI.SplitContainer( orientation=GafferUI.SplitContainer.Orientation.Horizontal )
		self.__main.addChild( self.__splitter )

		self.__splitter.append( self.__curveList )
		self.__splitter.append( self.__gadgetWidget )

		# Initial allocation of screen space:
		#   If there's enough space for the list to get 160 pixels give the rest to the AnimationGadget.
		#   If that's not the case, divide the space 50/50
		# \todo: do we want to preserve that ratio when maximizing the window as being done currently?
		self.__splitter.setSizes( (1, 1) )
		currentSizes = self.__splitter.getSizes()
		if currentSizes[0] > 160 :
			total = sum(currentSizes)
			betterSize = [float(x) / total for x in [160, total - 160]]
			self.__splitter.setSizes( betterSize )

		# set initial state
		self.__visiblePlugs = None
		self.__editablePlugs = None
		self._updateFromSet()
		self._updateFromContext( [ "frame" ] )
		self.__curveList._qtWidget().adjustSize()

		# \todo: is this a reasonable initial framing?
		bound = imath.Box3f( imath.V3f( -1, -1, 0 ), imath.V3f( 10, 10, 0 ) )
		self.__gadgetWidget.getViewportGadget().frame( bound )

	def connectedCurvePlug( self, plug ) :
		return plug.getInput().parent()

	def _updateFromSet( self ) :

		GafferUI.NodeSetEditor._updateFromSet( self )

		nodeList = list( self.getNodeSet() )
		self.__animationFilter.setSelection( nodeList )

	def _updateFromContext( self, modifiedItems ) :

		self.__animationGadget.setContext( self.getContext() )

	def __expansionChanged( self, pathListing ) :

		assert( pathListing is self.__curveList )

		paths = pathListing.getExpandedPaths()

		plugList = []

		for path in paths:
			graphComponent = self.__scriptNode.descendant( str( path ).replace( '/', '.' ) )
			for child in graphComponent.children() :
				if isinstance( child, Gaffer.ValuePlug ) and Gaffer.Animation.isAnimated( child ) :
					plugList.append( child )

		self.__visiblePlugs = set( plugList )

		visible = self.__animationGadget.visiblePlugs()
		editable = self.__animationGadget.editablePlugs()

		visible.clear()
		for plug in plugList :
			curvePlug = self.connectedCurvePlug( plug )
			if curvePlug :
				visible.add( curvePlug )

		with Gaffer.BlockedConnection( self.__editablePlugAddedConnection ) :

			editable.clear()
			for plug in ( self.__editablePlugs or set() ) & self.__visiblePlugs :
				curvePlug = self.connectedCurvePlug( plug )
				if curvePlug :
					editable.add( curvePlug )

	def __selectionChanged( self, pathListing ) :

		assert( pathListing is self.__curveList )

		paths = pathListing.getSelectedPaths()

		plugList = []

		for path in paths :
			graphComponent = self.__scriptNode.descendant( str( path ).replace( '/', '.' ) )

			if isinstance( graphComponent, Gaffer.ValuePlug ) and Gaffer.Animation.isAnimated( graphComponent ) :
				plugList.append( graphComponent )

			for child in graphComponent.children() :
				if isinstance( child, Gaffer.ValuePlug ) and Gaffer.Animation.isAnimated( child ) :
					plugList.append( child )

		self.__editablePlugs = set( plugList )

		editable = self.__animationGadget.editablePlugs()

		with Gaffer.BlockedConnection( self.__editablePlugAddedConnection ) :

			editable.clear()
			for plug in plugList :
				if plug in editable :
					continue

				curvePlug = self.connectedCurvePlug( plug )
				if curvePlug :
					editable.add( curvePlug )

	def __editablePlugAdded( self, standardSet, curvePlug ) :

		curves = curvePlug.children()
		if not curves :
			return

		connected = curves[0].outputs()

		if not connected :
			return

		previousSelection = self.__curveList.getSelectedPaths()
		newPath =  Gaffer.GraphComponentPath( self.__scriptNode, connected[0].relativeName( self.__scriptNode ).replace( '.', '/' ) )
		previousSelection.append( newPath )

	 	self.__curveList.setSelectedPaths( previousSelection )

	def __repr__( self ) :

		return "GafferUI.AnimationEditor( scriptNode )"

GafferUI.Editor.registerType( "AnimationEditor", AnimationEditor )
