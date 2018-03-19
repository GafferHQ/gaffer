##########################################################################
#
#  Copyright (c) 2011-2016, John Haddon. All rights reserved.
#  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
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
import collections

import IECore

import Gaffer
import GafferUI

# import lazily to improve startup of apps which don't use GL functionality
IECoreGL = Gaffer.lazyImport( "IECoreGL" )

##########################################################################
# Viewer implementation
##########################################################################

## The Viewer provides the primary means of visualising the output
# of Nodes. It defers responsibility for the generation of content to
# the View classes, which are registered against specific types of
# Plug.
## \todo Support split screening two Views together and overlaying
# them etc. Hopefully we can support that entirely within the Viewer
# without modifying the Views themselves.
class Viewer( GafferUI.NodeSetEditor ) :

	def __init__( self, scriptNode, **kw ) :

		self.__gadgetWidget = GafferUI.GadgetWidget(
			bufferOptions = set( (
				GafferUI.GLWidget.BufferOptions.Depth,
				GafferUI.GLWidget.BufferOptions.Double,
				GafferUI.GLWidget.BufferOptions.AntiAlias )
			),
		)

		GafferUI.NodeSetEditor.__init__( self, self.__gadgetWidget, scriptNode, **kw )

		self.__nodeToolbars = []
		self.__viewToolbars = []
		self.__toolToolbars = []

		with GafferUI.ListContainer( borderWidth = 2, spacing = 0 ) as horizontalToolbars :

			# Top toolbars

			with GafferUI.ListContainer(
				orientation = GafferUI.ListContainer.Orientation.Vertical,
				parenting = {
					"horizontalAlignment" : GafferUI.HorizontalAlignment.Center,
					"verticalAlignment" : GafferUI.VerticalAlignment.Top,
				}
			) :

				for toolbarContainer in [ self.__viewToolbars, self.__nodeToolbars, self.__toolToolbars ] :
					toolbarContainer.append( _Toolbar( GafferUI.Edge.Top, self.getContext() ) )

			# Bottom toolbars

			with GafferUI.ListContainer(
				spacing = 0,
				orientation = GafferUI.ListContainer.Orientation.Vertical,
				parenting = {
					"horizontalAlignment" : GafferUI.HorizontalAlignment.Center,
					"verticalAlignment" : GafferUI.VerticalAlignment.Bottom,
				}
			) :

				for toolbarContainer in [ self.__toolToolbars, self.__nodeToolbars, self.__viewToolbars ] :
					toolbarContainer.append( _Toolbar( GafferUI.Edge.Bottom, self.getContext() ) )

		with GafferUI.ListContainer( borderWidth = 2, spacing = 0, orientation = GafferUI.ListContainer.Orientation.Horizontal ) as verticalToolbars :

			# Left toolbars

			with GafferUI.ListContainer(
				orientation = GafferUI.ListContainer.Orientation.Horizontal,
				parenting = {
					"horizontalAlignment" : GafferUI.HorizontalAlignment.Left,
					"verticalAlignment" : GafferUI.VerticalAlignment.Center,
				}
			) :

				self.__toolChooser = _ToolChooser()
				self.__toolChangedConnection = self.__toolChooser.toolChangedSignal().connect(
					Gaffer.WeakMethod( self.__toolChanged )
				)

				for toolbarContainer in [ self.__viewToolbars, self.__nodeToolbars, self.__toolToolbars ] :
					toolbarContainer.append( _Toolbar( GafferUI.Edge.Left, self.getContext() ) )

			# Right toolbars

			with GafferUI.ListContainer(
				orientation = GafferUI.ListContainer.Orientation.Horizontal,
				parenting = {
					"horizontalAlignment" : GafferUI.HorizontalAlignment.Right,
					"verticalAlignment" : GafferUI.VerticalAlignment.Center,
				}
			) :

				for toolbarContainer in [ self.__toolToolbars, self.__nodeToolbars, self.__viewToolbars ] :
					toolbarContainer.append( _Toolbar( GafferUI.Edge.Right, self.getContext() ) )

		self.__gadgetWidget.addOverlay( horizontalToolbars )
		self.__gadgetWidget.addOverlay( verticalToolbars )

		self.__views = []
		# Indexed by view instance. We would prefer to simply
		# store tools as python attributes on the view instances
		# themselves, but we can't because that would create
		# circular references. Maybe it makes sense to be able to
		# query tools from a view anyway?
		self.__currentView = None

		self.__keyPressConnection = self.keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPress ) )

		self._updateFromSet()

	def view( self ) :

		return self.__currentView

	def viewGadgetWidget( self ) :

		return self.__gadgetWidget

	def __repr__( self ) :

		return "GafferUI.Viewer( scriptNode )"

	def _updateFromSet( self ) :

		GafferUI.NodeSetEditor._updateFromSet( self )

		self.__currentView = None

		node = self._lastAddedNode()
		if node :
			for plug in node.children( Gaffer.Plug ) :
				if plug.direction() == Gaffer.Plug.Direction.Out and not plug.getName().startswith( "__" ) :
					# try to reuse an existing view
					for view in self.__views :
						if view["in"].acceptsInput( plug ) :
							self.__currentView = view
							viewInput = self.__currentView["in"].getInput()
							if not viewInput or not viewInput.isSame( plug ) :
								self.__currentView["in"].setInput( plug )
							break # break out of view loop
					# if that failed then try to make a new one
					if self.__currentView is None :
						self.__currentView = GafferUI.View.create( plug )
						if self.__currentView is not None:
							self.__currentView.setContext( self.getContext() )
							self.__views.append( self.__currentView )
					# if we succeeded in getting a suitable view, then
					# don't bother checking the other plugs
					if self.__currentView is not None :
						break

		for toolbar in self.__nodeToolbars :
			toolbar.setNode( node )

		for toolbar in self.__viewToolbars :
			toolbar.setNode( self.__currentView )

		self.__toolChooser.setView( self.__currentView )

		if self.__currentView is not None :
			self.__gadgetWidget.setViewportGadget( self.__currentView.viewportGadget() )
		else :
			self.__gadgetWidget.setViewportGadget( GafferUI.ViewportGadget() )

	def _titleFormat( self ) :

		return GafferUI.NodeSetEditor._titleFormat( self, _maxNodes = 1, _reverseNodes = True, _ellipsis = False )

	def __toolChanged( self, toolChooser ) :

		for toolbar in self.__toolToolbars :
			toolbar.setNode( self.__toolChooser.getTool() )

	def __keyPress( self, widget, event ) :

		if event.modifiers :
			return False

		for t in self.__toolChooser.tools() :
			if Gaffer.Metadata.nodeValue( t, "viewer:shortCut" ) == event.key :
				self.__toolChooser.setTool( t )
				return True

		return False

GafferUI.EditorWidget.registerType( "Viewer", Viewer )

# Internal widget to simplify the management of node toolbars.
class _Toolbar( GafferUI.Frame ) :

	def __init__( self, edge, context, **kw ) :

		GafferUI.Frame.__init__( self, borderWidth = 0, borderStyle = GafferUI.Frame.BorderStyle.None, **kw )

		# We store the 5 most recently used toolbars in a cache,
		# to avoid unnecessary reconstruction when switching back and
		# forth between the same set of nodes.
		self.__nodeToolbarCache = IECore.LRUCache( self.__cacheGetter, 5 )

		self.__edge = edge
		self.__context = context
		self.__node = []

	def setNode( self, node ) :

		if node == self.__node :
			return

		self.__node = node
		if self.__node is not None :
			toolbar = self.__nodeToolbarCache.get( ( self.__node, self.__edge ) )
			if toolbar is not None :
				toolbar.setContext( self.__context )
			self.setChild( toolbar )
		else :
			self.setChild( None )

		self.setVisible( self.getChild() is not None )

	def getNode( self ) :

		return self.__node

	@staticmethod
	def __cacheGetter( nodeAndEdge ) :

		return ( GafferUI.NodeToolbar.create( nodeAndEdge[0], nodeAndEdge[1] ), 1 )

# Internal widget to present the available tools for a view.
class _ToolChooser( GafferUI.Frame ) :

	__ViewEntry = collections.namedtuple( "__ViewEntry", [ "tools", "widgets" ] )

	def __init__( self, **kw ) :

		GafferUI.Frame.__init__( self, borderWidth = 0, borderStyle = GafferUI.Frame.BorderStyle.None, **kw )

		self.__view = None
		self.__toolChangedSignal = GafferUI.WidgetSignal()

		# Mapping from View to __ViewEntry
		self.__viewEntries = {}

	def tools( self ) :

		if self.__view is not None :
			return self.__viewEntries[self.__view].tools
		else :
			return []

	def setTool( self, tool ) :

		if self.__view is None :
			assert( tool is None )

		if tool is not None and tool not in self.__viewEntries[self.__view].tools :
			raise ValueError

		for i, t in enumerate( self.__viewEntries[self.__view].tools ) :
			active = t.isSame( tool )
			t["active"].setValue( active )
			widget = self.__viewEntries[self.__view].widgets[i]
			with Gaffer.BlockedConnection( widget.__stateChangedConnection ) :
				widget.setState( active )

		self.toolChangedSignal()( self )

	def getTool( self ) :

		if self.__view is None :
			return None

		return next( ( t for t in self.__viewEntries[self.__view].tools if t["active"].getValue() ), None )

	def toolChangedSignal( self ) :

		return self.__toolChangedSignal

	def setView( self, view ) :

		if view == self.__view :
			return

		if view not in self.__viewEntries :

			if view is not None :
				tools = [ GafferUI.Tool.create( n, view ) for n in GafferUI.Tool.registeredTools( view.typeId() ) ]
				tools.sort( key = lambda v : Gaffer.Metadata.nodeValue( v, "order" ) if Gaffer.Metadata.nodeValue( v, "order" ) is not None else 999 )
			else :
				tools = []

			with GafferUI.ListContainer( spacing = 1 ) as widgets :

				for tool in tools :

					image = tool.typeName().replace( ":", "" )
					image = image[:1].lower() + image[1:] + ".png"

					toolTip = tool.getName()
					description = Gaffer.Metadata.nodeDescription( tool )
					if description :
						toolTip += "\n\n" + IECore.StringUtil.wrap( description, 80 )

					shortCut = Gaffer.Metadata.value( tool, "viewer:shortCut" )
					if shortCut is not None :
						toolTip += "\n\nShortcut : " + shortCut

					widget = GafferUI.BoolWidget( image = image, toolTip = toolTip, displayMode = GafferUI.BoolWidget.DisplayMode.Tool )
					widget.__stateChangedConnection = widget.stateChangedSignal().connect(
						functools.partial( Gaffer.WeakMethod( self.__stateChanged ), tool = tool )
					)

			GafferUI.WidgetAlgo.joinEdges( widgets )

			self.__viewEntries[view] = self.__ViewEntry( tools, widgets )

		self.setChild( self.__viewEntries[view].widgets )
		self.__view = view

		if self.getTool() :
			self.toolChangedSignal()( self )
		elif len( self.tools() ) :
			self.setTool( self.tools()[0] )
		else :
			self.setTool( None )

	def getView( self ) :

		return self.__view

	def __stateChanged( self, widget, tool ) :

		self.setTool( tool )
