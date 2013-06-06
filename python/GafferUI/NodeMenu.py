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

## Returns a menu definition used for the creation of nodes. This is
# initially empty but is expected to be populated during the gaffer
# startup routine.
def definition() :

	return __definition

__definition = IECore.MenuDefinition()

## Utility function to append a menu item to definition.
# nodeCreator must be a callable that returns a Gaffer.Node.	
def append( path, nodeCreator, **kw ) :

	item = IECore.MenuItemDefinition( command = nodeCreatorWrapper( nodeCreator=nodeCreator ), **kw )
	definition().append( path, item )

## Utility function which takes a callable that creates a node, and returns a new
# callable which will add the node to the graph.
def nodeCreatorWrapper( nodeCreator ) :

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

	return f
				
## Utility function to append menu items to definition. One item will
# be created for each class found on the specified search path.
def appendParameterisedHolders( path, parameterisedHolderType, searchPathEnvVar, matchExpression = re.compile( ".*" ) ) :
	
	if isinstance( matchExpression, str ) :
		matchExpression = re.compile( fnmatch.translate( matchExpression ) )
	
	definition().append( path, { "subMenu" : IECore.curry( __parameterisedHolderMenu, parameterisedHolderType, searchPathEnvVar, matchExpression ) } )

def __parameterisedHolderCreator( parameterisedHolderType, className, classVersion, searchPathEnvVar ) :

	nodeName = className.rpartition( "/" )[-1]
	node = parameterisedHolderType( nodeName )
	node.setParameterised( className, classVersion, searchPathEnvVar )

	return node

def __parameterisedHolderMenu( parameterisedHolderType, searchPathEnvVar, matchExpression ) :

	c = IECore.ClassLoader.defaultLoader( searchPathEnvVar )
	d = IECore.MenuDefinition()
	for n in c.classNames() :
		if matchExpression.match( n ) :
			nc = "/".join( [ IECore.CamelCase.toSpaced( x ) for x in n.split( "/" ) ] )
			v = c.getDefaultVersion( n )
			d.append( "/" + nc, { "command" : nodeCreatorWrapper( IECore.curry( __parameterisedHolderCreator, parameterisedHolderType, n, v, searchPathEnvVar ) ) } )

	return d
