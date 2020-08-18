##########################################################################
#
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

import sys
import collections
import imath

import IECore

import Gaffer
import GafferUI

def appendDefinitions( menuDefinition, prefix="" ) :

	menuDefinition.append( prefix + "/Undo", { "command" : undo, "shortCut" : "Ctrl+Z", "active" : __undoAvailable } )
	menuDefinition.append( prefix + "/Redo", { "command" : redo, "shortCut" : "Shift+Ctrl+Z", "active" : __redoAvailable } )
	menuDefinition.append( prefix + "/UndoDivider", { "divider" : True } )

	menuDefinition.append( prefix + "/Cut", { "command" : cut, "shortCut" : "Ctrl+X", "active" : __mutableSelectionAvailable } )
	menuDefinition.append( prefix + "/Copy", { "command" : copy, "shortCut" : "Ctrl+C", "active" : selectionAvailable } )
	menuDefinition.append( prefix + "/Paste", { "command" : paste, "shortCut" : "Ctrl+V", "active" : __pasteAvailable } )
	menuDefinition.append( prefix + "/Delete", { "command" : delete, "shortCut" : "Backspace, Delete", "active" : __mutableSelectionAvailable } )
	menuDefinition.append( prefix + "/Unplug", { "command" : unplug, "shortCut" : "Ctrl+U", "active" : __mutableSelectionAvailable } )
	menuDefinition.append( prefix + "/CutCopyPasteDeleteDivider", { "divider" : True } )

	menuDefinition.append( prefix + "/Find...", { "command" : find, "shortCut" : "Ctrl+F" } )
	menuDefinition.append( prefix + "/FindDivider", { "divider" : True } )

	menuDefinition.append( prefix + "/Arrange", { "command" : arrange, "shortCut" : "Ctrl+L", "active" : __arrangeAvailable } )
	menuDefinition.append( prefix + "/ArrangeDivider", { "divider" : True } )

	menuDefinition.append( prefix + "/Select All", { "command" : selectAll, "shortCut" : "Ctrl+A" } )
	menuDefinition.append( prefix + "/Select None", { "command" : selectNone, "shortCut" : "Shift+Ctrl+A", "active" : selectionAvailable } )

	menuDefinition.append( prefix + "/Select Connected/Inputs", { "command" : selectInputs, "active" : selectionAvailable } )
	menuDefinition.append( prefix + "/Select Connected/Add Inputs", { "command" : selectAddInputs, "active" : selectionAvailable } )
	menuDefinition.append( prefix + "/Select Connected/InputsDivider", { "divider" : True } )

	menuDefinition.append( prefix + "/Select Connected/Upstream", { "command" : selectUpstream, "active" : selectionAvailable } )
	menuDefinition.append( prefix + "/Select Connected/Add Upstream", { "command" : selectAddUpstream, "active" : selectionAvailable } )
	menuDefinition.append( prefix + "/Select Connected/UpstreamDivider", { "divider" : True } )

	menuDefinition.append( prefix + "/Select Connected/Outputs", { "command" : selectOutputs, "active" : selectionAvailable } )
	menuDefinition.append( prefix + "/Select Connected/Add Outputs", { "command" : selectAddOutputs, "active" : selectionAvailable } )
	menuDefinition.append( prefix + "/Select Connected/OutputsDivider", { "divider" : True } )

	menuDefinition.append( prefix + "/Select Connected/Downstream", { "command" : selectDownstream, "active" : selectionAvailable } )
	menuDefinition.append( prefix + "/Select Connected/Add Downstream", { "command" : selectAddDownstream, "active" : selectionAvailable } )
	menuDefinition.append( prefix + "/Select Connected/DownstreamDivider", { "divider" : True } )

	menuDefinition.append( prefix + "/Select Connected/Add All", { "command" : selectConnected, "active" : selectionAvailable } )

## \todo: Remove nodeGraph fallback when all client code has been updated
__Scope = collections.namedtuple( "Scope", [ "scriptWindow", "script", "parent", "graphEditor", "nodeGraph" ] )

## Returns the scope in which an edit menu item should operate. The return
# value has "scriptWindow", "script", "parent" and "graphEditor" attributes.
# The "graphEditor" attribute may be None if no GraphEditor can be found. Note
# that in many cases user expectation is that an operation will only apply
# to nodes currently visible within the GraphEditor, and that nodes can be
# filtered within the GraphEditor.
def scope( menu ) :

	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )

	graphEditor = None

	if isinstance( scriptWindow.getLayout(), GafferUI.CompoundEditor ) :
		graphEditor = scriptWindow.getLayout().editor( GafferUI.GraphEditor, focussedOnly = False )

	if graphEditor is not None :
		parent = graphEditor.graphGadget().getRoot()
	else :
		parent = scriptWindow.scriptNode()

	return __Scope( scriptWindow, scriptWindow.scriptNode(), parent, graphEditor, graphEditor )

## Returns True if nodes are currently selected in the scope returned by scope().
# This can be used for the "active" field in a menu item definition to disable
# a menu item when no nodes are selected.
def selectionAvailable( menu ) :

	return True if scope( menu ).script.selection().size() else False

## A function suitable as the command for an Edit/Undo menu item. It must
# be invoked from a menu that has a ScriptWindow in its ancestry.
def undo( menu ) :

	scope( menu ).script.undo()

## A function suitable as the command for an Edit/Redo menu item. It must
# be invoked from a menu that has a ScriptWindow in its ancestry.
def redo( menu ) :

	scope( menu ).script.redo()

## A function suitable as the command for an Edit/Cut menu item. It must
# be invoked from a menu that has a ScriptWindow in its ancestry.
def cut( menu ) :

	s = scope( menu )
	with Gaffer.UndoScope( s.script ) :
		s.script.cut( s.parent, s.script.selection() )

## A function suitable as the command for an Edit/Copy menu item. It must
# be invoked from a menu that has a ScriptWindow in its ancestry.
def copy( menu ) :

	s = scope( menu )
	s.script.copy( s.parent, s.script.selection() )

## A function suitable as the command for an Edit/Paste menu item. It must
# be invoked from a menu that has a ScriptWindow in its ancestry.
def paste( menu ) :

	s = scope( menu )
	originalSelection = Gaffer.StandardSet( iter( s.script.selection() ) )

	errorHandler = GafferUI.ErrorDialogue.ErrorHandler(
		title = "Errors Occurred During Pasting",
		closeLabel = "Oy vey",
		parentWindow = s.scriptWindow
	)

	with Gaffer.UndoScope( s.script ), errorHandler :

		s.script.paste( s.parent, continueOnError = True )

		# try to get the new nodes connected to the original selection
		if s.graphEditor is None :
			return

		s.graphEditor.graphGadget().getLayout().connectNodes( s.graphEditor.graphGadget(), s.script.selection(), originalSelection )

		# position the new nodes sensibly

		bound = s.graphEditor.bound()
		mousePosition = GafferUI.Widget.mousePosition()
		if bound.intersects( mousePosition ) :
			fallbackPosition = mousePosition - bound.min()
		else :
			fallbackPosition = bound.center() - bound.min()

		fallbackPosition = s.graphEditor.graphGadgetWidget().getViewportGadget().rasterToGadgetSpace(
			imath.V2f( fallbackPosition.x, fallbackPosition.y ),
			gadget = s.graphEditor.graphGadget()
		).p0
		fallbackPosition = imath.V2f( fallbackPosition.x, fallbackPosition.y )

		# First position the nodes sensibly as a group, keeping their relative positions.
		# Usually this is all we need to do, because typically they were laid out when they
		# were cut/copied.
		nodesNeedingLayout = [ x for x in s.script.selection() if not s.graphEditor.graphGadget().hasNodePosition( x ) ]
		s.graphEditor.graphGadget().getLayout().positionNodes( s.graphEditor.graphGadget(), s.script.selection(), fallbackPosition )
		# Second, do an auto-layout for any nodes which weren't laid out properly when they
		# were cut/copied.
		s.graphEditor.graphGadget().getLayout().layoutNodes( s.graphEditor.graphGadget(), Gaffer.StandardSet( nodesNeedingLayout ) )

		s.graphEditor.frame( s.script.selection(), extend = True )

## A function suitable as the command for an Edit/Delete menu item. It must
# be invoked from a menu that has a ScriptWindow in its ancestry.
def delete( menu ) :

	s = scope( menu )
	with Gaffer.UndoScope( s.script ) :
		s.script.deleteNodes( s.parent, s.script.selection() )

# A function suitable as the command for an Edit/Unplug menu item. It must
# be invoked from a menu that has a ScriptWindow in its ancestry.
def unplug( menu ) :

	s = scope( menu )
	with Gaffer.UndoScope( s.script ) :

		s.script.cut( s.parent, s.script.selection() )
		s.script.paste( s.parent )

		for node in s.script.selection() :
			position = s.nodeGraph.graphGadget().getNodePosition( node )
			s.nodeGraph.graphGadget().setNodePosition( node, imath.V2f( position.x+2, position.y+2 ) )

## A function suitable as the command for an Edit/Find menu item.  It must
# be invoked from a menu that has a ScriptWindow in its ancestry.
def find( menu ) :

	s = scope( menu )

	try :
		findDialogue = s.scriptWindow.__findDialogue
	except AttributeError :
		findDialogue = GafferUI.NodeFinderDialogue( s.parent )
		s.scriptWindow.addChildWindow( findDialogue )
		s.scriptWindow.__findDialogue = findDialogue

	findDialogue.setScope( s.parent )
	findDialogue.setVisible( True )

## A function suitable as the command for an Edit/Arrange menu item.  It must
# be invoked from a menu that has a ScriptWindow in its ancestry.
def arrange( menu ) :

	s = scope( menu )
	if not s.graphEditor :
		return

	graph = s.graphEditor.graphGadget()

	nodes = s.script.selection()
	if not nodes :
		nodes = Gaffer.StandardSet( graph.getRoot().children( Gaffer.Node ) )

	with Gaffer.UndoScope( s.script ) :
		graph.getLayout().layoutNodes( graph, nodes )

## A function suitable as the command for an Edit/Select All menu item. It must
# be invoked from a menu that has a ScriptWindow in its ancestry.
def selectAll( menu ) :

	s = scope( menu )
	if s.graphEditor is None :
		return

	graphGadget = s.graphEditor.graphGadget()
	for node in s.parent.children( Gaffer.Node ) :
		if graphGadget.nodeGadget( node ) is not None :
			s.script.selection().add( node )

## A function suitable as the command for an Edit/Select None menu item. It must
# be invoked from a menu that has a ScriptWindow in its ancestry.
def selectNone( menu ) :

	scope( menu ).script.selection().clear()

## The command function for the default "Edit/Select Connected/Inputs" menu item. It must
# be invoked from a menu that has a ScriptWindow in its ancestry.
def selectInputs( menu ) :

	__selectConnected( menu, Gaffer.Plug.Direction.In, degreesOfSeparation = 1, add = False )

## The command function for the default "Edit/Select Connected/Add Inputs" menu item. It must
# be invoked from a menu that has a ScriptWindow in its ancestry.
def selectAddInputs( menu ) :

	__selectConnected( menu, Gaffer.Plug.Direction.In, degreesOfSeparation = 1, add = True )

## The command function for the default "Edit/Select Connected/Upstream" menu item. It must
# be invoked from a menu that has a ScriptWindow in its ancestry.
def selectUpstream( menu ) :

	__selectConnected( menu, Gaffer.Plug.Direction.In, degreesOfSeparation = sys.maxsize, add = False )

## The command function for the default "Edit/Select Connected/Add Upstream" menu item. It must
# be invoked from a menu that has a ScriptWindow in its ancestry.
def selectAddUpstream( menu ) :

	__selectConnected( menu, Gaffer.Plug.Direction.In, degreesOfSeparation = sys.maxsize, add = True )

## The command function for the default "Edit/Select Connected/Outputs" menu item. It must
# be invoked from a menu that has a ScriptWindow in its ancestry.
def selectOutputs( menu ) :

	__selectConnected( menu, Gaffer.Plug.Direction.Out, degreesOfSeparation = 1, add = False )

## The command function for the default "Edit/Select Connected/Add Outputs" menu item. It must
# be invoked from a menu that has a ScriptWindow in its ancestry.
def selectAddOutputs( menu ) :

	__selectConnected( menu, Gaffer.Plug.Direction.Out, degreesOfSeparation = 1, add = True )

## The command function for the default "Edit/Select Connected/Downstream" menu item. It must
# be invoked from a menu that has a ScriptWindow in its ancestry.
def selectDownstream( menu ) :

	__selectConnected( menu, Gaffer.Plug.Direction.Out, degreesOfSeparation = sys.maxsize, add = False )

## The command function for the default "Edit/Select Connected/Add Downstream" menu item. It must
# be invoked from a menu that has a ScriptWindow in its ancestry.
def selectAddDownstream( menu ) :

	__selectConnected( menu, Gaffer.Plug.Direction.Out, degreesOfSeparation = sys.maxsize, add = True )

## The command function for the default "Edit/Select Connected/Add All" menu item. It must
# be invoked from a menu that has a ScriptWindow in its ancestry.
def selectConnected( menu ) :

	__selectConnected( menu, Gaffer.Plug.Direction.Invalid, degreesOfSeparation = sys.maxsize, add = True )

def __selectConnected( menu, direction, degreesOfSeparation, add ) :

	s = scope( menu )
	if s.graphEditor is None :
		return

	connected = Gaffer.StandardSet()
	for node in s.script.selection() :
		connected.add( [ g.node() for g in s.graphEditor.graphGadget().connectedNodeGadgets( node, direction, degreesOfSeparation ) ] )

	selection = s.script.selection()
	if not add :
		selection.clear()
	selection.add( connected )

def __mutableSelectionAvailable( menu ) :

	if not selectionAvailable( menu ) :
		return False

	return not (Gaffer.MetadataAlgo.getChildNodesAreReadOnly( scope( menu ).parent ) or	Gaffer.MetadataAlgo.readOnly( scope( menu ).parent ) )

def __pasteAvailable( menu ) :

	s = scope( menu )
	if Gaffer.MetadataAlgo.getChildNodesAreReadOnly( scope( menu ).parent ) or Gaffer.MetadataAlgo.readOnly( scope( menu ).parent ):
		return False

	root = s.script.ancestor( Gaffer.ApplicationRoot )
	return isinstance( root.getClipboardContents(), IECore.StringData )

def __arrangeAvailable( menu ) :

	return not (Gaffer.MetadataAlgo.getChildNodesAreReadOnly( scope( menu ).parent ) or	Gaffer.MetadataAlgo.readOnly( scope( menu ).parent ) )

def __undoAvailable( menu ) :

	return scope( menu ).script.undoAvailable()

def __redoAvailable( menu ) :

	return scope( menu ).script.redoAvailable()
