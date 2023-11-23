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

import contextlib
import inspect
import imath

import IECore

import Gaffer
import GafferUI

## The NodeMenu class provides a menu for the creation of new nodes. To allow
# different applications to coexist happily in the same process, separate node
# menus are maintained per application, and NodeMenu.acquire() is used to
# obtain the appropriate menu.
class NodeMenu( object ) :

	## Chances are you want to use acquire() to get the NodeMenu for a
	# specific application, rather than construct one directly.
	def __init__( self ) :

		self.__definition = IECore.MenuDefinition()

	## Acquires the NodeMenu for the specified application.
	@staticmethod
	def acquire( applicationOrApplicationRoot ) :

		if isinstance( applicationOrApplicationRoot, Gaffer.Application ) :
			applicationRoot = applicationOrApplicationRoot.root()
		else :
			assert( isinstance( applicationOrApplicationRoot, Gaffer.ApplicationRoot ) )
			applicationRoot = applicationOrApplicationRoot

		nodeMenu = getattr( applicationRoot, "_nodeMenu", None )
		if nodeMenu :
			return nodeMenu

		nodeMenu = NodeMenu()
		applicationRoot._nodeMenu = nodeMenu

		return nodeMenu

	## Returns a menu definition used for the creation of nodes. This is
	# initially empty but is expected to be populated during the gaffer
	# startup routine.
	def definition( self ) :

		return self.__definition

	## Utility function to append a menu item to definition.
	# nodeCreator must be a callable that returns a Gaffer.Node.
	def append( self, path, nodeCreator, plugValues={}, postCreator=None, **kw ) :

		item = IECore.MenuItemDefinition( command = self.nodeCreatorWrapper( nodeCreator=nodeCreator, plugValues=plugValues, postCreator=postCreator ), **kw )
		self.definition().append( path, item )

	## Utility function which takes a callable that creates a node, and returns a new
	# callable which will add the node to the graph.
	@staticmethod
	def nodeCreatorWrapper( nodeCreator, plugValues={}, postCreator=None ) :

		def f( menu ) :

			graphEditor = menu.ancestor( GafferUI.GraphEditor )
			assert( graphEditor is not None )
			gadgetWidget = graphEditor.graphGadgetWidget()
			graphGadget = graphEditor.graphGadget()

			script = graphEditor.scriptNode()

			commandArgs = []
			with contextlib.suppress( TypeError ) :
				commandArgs = inspect.getfullargspec( nodeCreator ).args

			with Gaffer.UndoScope( script ) :

				if "menu" in commandArgs :
					node = nodeCreator( menu = menu )
				else :
					node = nodeCreator()

				if node is None :
					return

				Gaffer.NodeAlgo.applyUserDefaults( node )

				for plugName, plugValue in plugValues.items() :
					node.descendant( plugName ).setValue( plugValue )

				if node.parent() is None :
					graphGadget.getRoot().addChild( node )

				graphGadget.getLayout().connectNode( graphGadget, node, script.selection() )

			# if no connections were made, we can't expect the graph layout to
			# know where to put the node, so we'll position it based on
			# the click location that opened the menu.
			menuPosition = menu.popupPosition( relativeTo = gadgetWidget )
			fallbackPosition = gadgetWidget.getViewportGadget().rasterToGadgetSpace(
				imath.V2f( menuPosition.x, menuPosition.y ),
				gadget = graphGadget
			).p0
			fallbackPosition = imath.V2f( fallbackPosition.x, fallbackPosition.y )

			graphGadget.getLayout().positionNode( graphGadget, node, fallbackPosition )

			script.selection().clear()
			script.selection().add( node )

			graphEditor.frame( [ node ], extend = True )

			if postCreator is not None :
				postCreator( node, menu )

		return f
