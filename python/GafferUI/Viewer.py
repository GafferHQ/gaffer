##########################################################################
#
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
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
				GafferUI.GLWidget.BufferOptions.Double )
			),
		)

		GafferUI.NodeSetEditor.__init__( self, self.__gadgetWidget, scriptNode, **kw )

		self.__nodeToolbars = []
		self.__viewToolbars = []

		with GafferUI.GridContainer( borderWidth = 2, spacing = 0 ) as overlay :

			with GafferUI.ListContainer(
				orientation = GafferUI.ListContainer.Orientation.Horizontal,
				parenting = {
					"index" : ( slice( 0, 5 ), 0 ),
					"alignment" : ( GafferUI.HorizontalAlignment.None, GafferUI.VerticalAlignment.Top )
				}
			) :

				self.__toolMenuButton = GafferUI.MenuButton(
					menu = GafferUI.Menu( Gaffer.WeakMethod( self.__toolMenuDefinition ) ),
					hasFrame = False,
				)

				GafferUI.Spacer( IECore.V2i( 0 ), parenting = { "expand" : True } )

				self.__viewToolbars.append(
					_Toolbar( GafferUI.Edge.Top, parenting = { "verticalAlignment" : GafferUI.VerticalAlignment.Top } )
				)

			self.__nodeToolbars.append(
				_Toolbar(
					GafferUI.Edge.Top,
					parenting = {
						"index" : ( slice( 0, 5 ), 1 ),
						"alignment" : ( GafferUI.HorizontalAlignment.Center, GafferUI.VerticalAlignment.Top ),
					}
				)
			)

			self.__viewToolbars.append(
				_Toolbar( GafferUI.Edge.Left,
					parenting = {
						"index" : ( 0, 2 ),
						"alignment" : ( GafferUI.HorizontalAlignment.Left, GafferUI.VerticalAlignment.Center ),
					}
				)
			)

			self.__nodeToolbars.append(
				_Toolbar( GafferUI.Edge.Left,
					parenting = {
						"index" : ( 1, 2 ),
						"alignment" : ( GafferUI.HorizontalAlignment.Left, GafferUI.VerticalAlignment.Center ),
					}
				)
			)

			self.__nodeToolbars.append(
				_Toolbar( GafferUI.Edge.Right,
					parenting = {
						"index" : ( 3, 2 ),
						"alignment" : ( GafferUI.HorizontalAlignment.Right, GafferUI.VerticalAlignment.Center ),
					}
				)
			)

			self.__viewToolbars.append(
				_Toolbar( GafferUI.Edge.Right,
					parenting = {
						"index" : ( 4, 2 ),
						"alignment" : ( GafferUI.HorizontalAlignment.Right, GafferUI.VerticalAlignment.Center ),
					}
				)
			)

			self.__nodeToolbars.append(
				_Toolbar( GafferUI.Edge.Bottom,
					parenting = {
						"index" : ( slice( 0, 5 ), 3 ),
						"alignment" : ( GafferUI.HorizontalAlignment.Center, GafferUI.VerticalAlignment.Bottom ),
					}
				)
			)

			self.__viewToolbars.append(
				_Toolbar( GafferUI.Edge.Bottom,
					parenting = {
						"index" : ( slice( 0, 5 ), 4 ),
						"alignment" : ( GafferUI.HorizontalAlignment.Center, GafferUI.VerticalAlignment.Bottom ),
					}
				)
			)

		## \todo Consider public API for this in the GridContainer class.
		overlay._qtWidget().layout().setRowStretch( 2, 1 )
		overlay._qtWidget().layout().setColumnStretch( 2, 1 )

		self.__gadgetWidget.setOverlay( overlay )

		self.__views = []
		# Indexed by view instance. We would prefer to simply
		# store tools as python attributes on the view instances
		# themselves, but we can't because that would create
		# circular references. Maybe it makes sense to be able to
		# query tools from a view anyway?
		self.__viewTools = {}
		self.__currentView = None

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
							self.__viewTools[self.__currentView] = [ GafferUI.Tool.create( n, self.__currentView ) for n in GafferUI.Tool.registeredTools( self.__currentView.typeId() ) ]
							self.__viewTools[self.__currentView].sort( key = lambda v : Gaffer.Metadata.value( v, "order" ) if Gaffer.Metadata.value( v, "order" ) is not None else 999 )
							if len( self.__viewTools[self.__currentView] ) :
								self.__activateTool( self.__viewTools[self.__currentView][0] )
							self.__views.append( self.__currentView )
					# if we succeeded in getting a suitable view, then
					# don't bother checking the other plugs
					if self.__currentView is not None :
						break

		for toolbar in self.__nodeToolbars :
			toolbar.setNode( node )

		for toolbar in self.__viewToolbars :
			toolbar.setNode( self.__currentView )

		if self.__currentView is not None :
			self.__gadgetWidget.setViewportGadget( self.__currentView.viewportGadget() )
			self.__toolMenuButton.setVisible( len( self.__viewTools[self.__currentView] ) != 0 )
		else :
			self.__gadgetWidget.setViewportGadget( GafferUI.ViewportGadget() )
			self.__toolMenuButton.setVisible( False )

	def _titleFormat( self ) :

		return GafferUI.NodeSetEditor._titleFormat( self, _maxNodes = 1, _reverseNodes = True, _ellipsis = False )

	def __toolMenuDefinition( self ) :

		m = IECore.MenuDefinition()
		if self.__currentView is None :
			return m

		for tool in self.__viewTools[self.__currentView] :
			m.append(
				"/" + IECore.CamelCase.toSpaced( tool.typeName().rpartition( ":" )[2] ),
				{
					"checkBox" : tool["active"].getValue(),
					"active" : not tool["active"].getValue(),
					"command" : IECore.curry( Gaffer.WeakMethod( self.__activateTool ), tool ),
					"description" : self.__toolDescription( tool )
				}
			)

		return m

	def __activateTool( self, tool, *unused ) :

		for t in self.__viewTools[self.__currentView] :
			t["active"].setValue( t.isSame( tool ) )

		iconName = tool.typeName().replace( ":", "" )
		iconName = iconName[:1].lower() + iconName[1:] + ".png"
		self.__toolMenuButton.setImage( iconName )

		self.__toolMenuButton.setToolTip( self.__toolDescription( tool ) )

	def __toolDescription( self, tool ) :

		result = tool.getName()
		description = Gaffer.Metadata.nodeDescription( tool )
		if description :
			result += "\n\n" + IECore.StringUtil.wrap( description, 80 )

		return result

GafferUI.EditorWidget.registerType( "Viewer", Viewer )

# Internal widget to simplify the management of node toolbars.
class _Toolbar( GafferUI.Frame ) :

	def __init__( self, edge, **kw ) :

		GafferUI.Frame.__init__( self, borderWidth = 0, borderStyle = GafferUI.Frame.BorderStyle.None, **kw )

		# We store the 5 most recently used toolbars in a cache,
		# to avoid unnecessary reconstruction when switching back and
		# forth between the same set of nodes.
		self.__nodeToolbarCache = IECore.LRUCache( self.__cacheGetter, 5 )

		self.__edge = edge
		self.__node = []

	def setNode( self, node ) :

		if node == self.__node :
			return

		self.__node = node
		if self.__node is not None :
			self.setChild( self.__nodeToolbarCache.get( ( self.__node, self.__edge ) ) )
		else :
			self.setChild( None )

	def getNode( self ) :

		return self.__node

	@staticmethod
	def __cacheGetter( nodeAndEdge ) :

		return ( GafferUI.NodeToolbar.create( nodeAndEdge[0], nodeAndEdge[1] ), 1 )
