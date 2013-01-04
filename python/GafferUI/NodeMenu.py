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
def append( path, nodeCreator ) :

	definition().append( path, { "command" : nodeCreatorWrapper( nodeCreator=nodeCreator ) } )

## Utility function which takes a callable that creates a node, and returns a new
# callable which will add the node to the graph.
def nodeCreatorWrapper( nodeCreator ) :

	def f( menu ) :
				
		editor = menu.ancestor( GafferUI.EditorWidget )
		script = editor.scriptNode()

		node = nodeCreator()

		with Gaffer.UndoContext( script ) :
			script.addChild( node )
			__connectNode( node, menu )

		__positionNode( node, menu )
			
		script.selection().clear()
		script.selection().add( node )

	return f

## \todo This should probably go somewhere in a public API - maybe the
# same place as __positionNode(). Maybe they just belong as methods
# on the GraphGadget? Or in a GraphLayout class which is given a GraphGadget
# to work with?
def __connectNode( node, menu ) :

	graphEditor = menu.ancestor( GafferUI.GraphEditor )
	if graphEditor is None :
		return
	graphGadget = graphEditor.graphGadget()

	# we only want to autoconnect plugs which are visible in the ui - otherwise
	# things will get very confusing for the user.
	
	# get all visible output plugs we could potentially connect in to our node
	script = node.scriptNode()
	selectedNodeGadgets = [ graphGadget.nodeGadget( selectedNode ) for selectedNode in script.selection() ]
	selectedNodeGadgets = [ x for x in selectedNodeGadgets if x is not None ]
	outputPlugs = []
	for nodeGadget in selectedNodeGadgets :
		for child in nodeGadget.node().children() :
			if isinstance( child, Gaffer.Plug ) and child.direction()==Gaffer.Plug.Direction.Out :
				if nodeGadget.nodule( child ) is not None :
					outputPlugs.append( child )
	
	if not outputPlugs :
		return
		
	# get the gadget for the target node
	nodeGadget = graphGadget.nodeGadget( node )
	if nodeGadget is None :
		return

	# iterate over the output plugs, connecting them in to the node if we can
	def unconnectedInputPlugs( nodeGadget ) :
	
		result = []
		for child in nodeGadget.node().children() :
			if isinstance( child, Gaffer.Plug ) and child.direction()==Gaffer.Plug.Direction.In :
				if child.getInput() is None and nodeGadget.nodule( child ) is not None :
					result.append( child )
	
		return result
	
	inputPlugs = unconnectedInputPlugs( nodeGadget )
	for outputPlug in outputPlugs :
		for inputPlug in inputPlugs :
			if inputPlug.acceptsInput( outputPlug ) :
				inputPlug.setInput( outputPlug )
				# some nodes dynamically add new inputs when we connect
				# existing inputs, so we recalculate the input plugs
				# to take account
				inputPlugs = unconnectedInputPlugs( nodeGadget )
				break
				
## \todo There's some really terrible positioning code in GraphGadget, and
# this is pretty ad-hoc too. Maybe we need some centralised place for doing
# positioning, possibly with nice graph layout algorithms too.
def __positionNode( node, menu ) :

	# we can't do anything without a GraphEditor
	graphEditor = menu.ancestor( GafferUI.GraphEditor )
	if graphEditor is None :
		return
	
	gadgetWidget = graphEditor.graphGadgetWidget()
	graphGadget = gadgetWidget.getViewportGadget().getChild()
	nodeGadget = graphGadget.nodeGadget( node )
	if nodeGadget is None :
		return

	# try to figure out the node position based on its input connections
	nodePosition = None
	connections = []
	for child in nodeGadget.node().children() :
		if isinstance( child, Gaffer.Plug ) and child.direction()==Gaffer.Plug.Direction.In :
			connection = graphGadget.connectionGadget( child )
			if connection :
				connections.append( connection )
	
	if connections :
		srcNoduleCentroid = IECore.V3f( 0 )
		floorPos = IECore.V2f( IECore.V2f.baseTypeMin(), IECore.V2f.baseTypeMax() )
		for connection in connections :
			srcNodule = connection.srcNodule()
			srcNodulePos = srcNodule.transformedBound( None ).center()
			srcNoduleCentroid += srcNodulePos
			srcNodeGadget = srcNodule.ancestor( GafferUI.NodeGadget.staticTypeId() )
			srcTangent = srcNodeGadget.noduleTangent( srcNodule )
			if srcTangent.dot( IECore.V3f( 0, -1, 0 ) ) > 0.5 :
				floorPos.y = min( floorPos.y, srcNodulePos.y - 10.0 )
			if srcTangent.dot( IECore.V3f( 1, 0, 0 ) ) > 0.5 :
				floorPos.x = max( floorPos.x, srcNodulePos.x + 10.0 )
		srcNoduleCentroid /= len( connections )
		nodePosition = IECore.V2f(
			max( srcNoduleCentroid.x, floorPos.x ),
			min( srcNoduleCentroid.y, floorPos.y ),
		)
			
	# if that failed, then just put the position where the menu was launched
	if nodePosition is None :
		## \todo This positioning doesn't work very well when the menu min
		# is not where the mouse was clicked to open the window (when the menu
		# has been moved to keep it on screen).
		menuPosition = menu.bound( relativeTo=gadgetWidget ).min
		nodePosition = gadgetWidget.getViewportGadget().rasterToGadgetSpace(
			IECore.V2f( menuPosition.x, menuPosition.y ),
			gadget = graphGadget
		).p0

	# apply the position
	
	xPlug = node.getChild( "__uiX" )
	yPlug = node.getChild( "__uiY" )
	if xPlug is None :
		xPlug = Gaffer.FloatPlug( "__uiX" )
		node.addChild( xPlug )
	if yPlug is None :
		yPlug = Gaffer.FloatPlug( "__uiY" )
		node.addChild( yPlug )
	
	xPlug.setValue( nodePosition.x )
	yPlug.setValue( nodePosition.y )
		
## Utility function to append menu items to definition. One item will
# be created for each class found on the specified search path.
def appendParameterisedHolders( path, parameterisedHolderType, searchPathEnvVar ) :

	definition().append( path, { "subMenu" : IECore.curry( __parameterisedHolderMenu, parameterisedHolderType, searchPathEnvVar ) } )

def __parameterisedHolderCreator( parameterisedHolderType, className, classVersion, searchPathEnvVar ) :

	nodeName = className.rpartition( "/" )[-1]
	node = parameterisedHolderType( nodeName )
	node.setParameterised( className, classVersion, searchPathEnvVar )

	return node

def __parameterisedHolderMenu( parameterisedHolderType, searchPathEnvVar ) :

	c = IECore.ClassLoader.defaultLoader( searchPathEnvVar )
	d = IECore.MenuDefinition()
	for n in c.classNames() :
		nc = "/".join( [ IECore.CamelCase.toSpaced( x ) for x in n.split( "/" ) ] )
		v = c.getDefaultVersion( n )
		d.append( "/" + nc, { "command" : nodeCreatorWrapper( IECore.curry( __parameterisedHolderCreator, parameterisedHolderType, n, v, searchPathEnvVar ) ) } )

	return d
