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

from __future__ import with_statement

import re
import fnmatch
import inspect

import IECore

import Gaffer
import GafferUI

## The NodeMenu class provides a menu for the creation of new nodes. To allow
# different applications to coexist happily in the same process, separate node
# menus are maintained per application, and NodeMenu.acquire() is used to
# obtain the appropriate menu.
class NodeMenu :

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
	def append( self, path, nodeCreator, plugValues={}, **kw ) :

		item = IECore.MenuItemDefinition( command = self.nodeCreatorWrapper( nodeCreator=nodeCreator, plugValues=plugValues ), **kw )
		self.definition().append( path, item )

	## Utility function which takes a callable that creates a node, and returns a new
	# callable which will add the node to the graph.
	@staticmethod
	def nodeCreatorWrapper( nodeCreator, plugValues={} ) :

		def f( menu ) :

			nodeGraph = menu.ancestor( GafferUI.NodeGraph )
			assert( nodeGraph is not None )
			gadgetWidget = nodeGraph.graphGadgetWidget()
			graphGadget = gadgetWidget.getViewportGadget().getChild()

			script = nodeGraph.scriptNode()

			commandArgs = []
			with IECore.IgnoredExceptions( TypeError ) :
				commandArgs = inspect.getargspec( nodeCreator )[0]

			with Gaffer.UndoContext( script ) :

				if "menu" in commandArgs :
					node = nodeCreator( menu = menu )
				else :
					node = nodeCreator()

				if node is None :
					return
				
				for plugName, plugValue in plugValues.items() :
					node.descendant( plugName ).setValue( plugValue )
				
				if node.parent() is None :
					graphGadget.getRoot().addChild( node )

				graphGadget.getLayout().connectNode( graphGadget, node, script.selection() )

			# if no connections were made, we can't expect the graph layout to
			# know where to put the node, so we'll try to position it based on
			# the click location that opened the menu.
			## \todo This positioning doesn't work very well when the menu min
			# is not where the mouse was clicked to open the window (when the menu
			# has been moved to keep it on screen).
			menuPosition = menu.bound( relativeTo=gadgetWidget ).min
			fallbackPosition = gadgetWidget.getViewportGadget().rasterToGadgetSpace(
				IECore.V2f( menuPosition.x, menuPosition.y ),
				gadget = graphGadget
			).p0
			fallbackPosition = IECore.V2f( fallbackPosition.x, fallbackPosition.y )

			graphGadget.getLayout().positionNode( graphGadget, node, fallbackPosition )

			script.selection().clear()
			script.selection().add( node )

			nodeGraph.frame( [ node ], extend = True )

		return f

	## Utility function to append menu items to definition. One item will
	# be created for each class found on the specified search path.
	def appendParameterisedHolders( self, path, parameterisedHolderType, searchPathEnvVar, matchExpression = re.compile( ".*" ) ) :

		if isinstance( matchExpression, str ) :
			matchExpression = re.compile( fnmatch.translate( matchExpression ) )

		self.definition().append( path, { "subMenu" : IECore.curry( self.__parameterisedHolderMenu, parameterisedHolderType, searchPathEnvVar, matchExpression ) } )

	@staticmethod
	def __parameterisedHolderCreator( parameterisedHolderType, className, classVersion, searchPathEnvVar ) :

		nodeName = className.rpartition( "/" )[-1]
		node = parameterisedHolderType( nodeName )
		node.setParameterised( className, classVersion, searchPathEnvVar )

		return node

	@staticmethod
	def __parameterisedHolderMenu( parameterisedHolderType, searchPathEnvVar, matchExpression ) :

		c = IECore.ClassLoader.defaultLoader( searchPathEnvVar )
		d = IECore.MenuDefinition()
		for n in c.classNames() :
			if matchExpression.match( n ) :
				nc = "/".join( [ IECore.CamelCase.toSpaced( x ) for x in n.split( "/" ) ] )
				v = c.getDefaultVersion( n )
				d.append( "/" + nc, { "command" : NodeMenu.nodeCreatorWrapper( IECore.curry( NodeMenu.__parameterisedHolderCreator, parameterisedHolderType, n, v, searchPathEnvVar ) ) } )

		return d
