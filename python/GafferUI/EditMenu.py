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

from __future__ import with_statement

import IECore

import Gaffer
import GafferUI

def appendDefinitions( menuDefinition, prefix="" ) :

	menuDefinition.append( prefix + "/Undo", { "command" : undo, "shortCut" : "Ctrl+Z", "active" : __undoAvailable } )
	menuDefinition.append( prefix + "/Redo", { "command" : redo, "shortCut" : "Shift+Ctrl+Z", "active" : __redoAvailable } )
	menuDefinition.append( prefix + "/UndoDivider", { "divider" : True } )
	
	menuDefinition.append( prefix + "/Cut", { "command" : cut, "shortCut" : "Ctrl+X", "active" : __selectionAvailable } )
	menuDefinition.append( prefix + "/Copy", { "command" : copy, "shortCut" : "Ctrl+C", "active" : __selectionAvailable } )
	menuDefinition.append( prefix + "/Paste", { "command" : paste, "shortCut" : "Ctrl+V", "active" : __pasteAvailable } )
	menuDefinition.append( prefix + "/Delete", { "command" : delete, "shortCut" : "Backspace, Delete", "active" : __selectionAvailable } )
	menuDefinition.append( prefix + "/CutCopyPasteDeleteDivider", { "divider" : True } )

	menuDefinition.append( prefix + "/Select All", { "command" : selectAll, "shortCut" : "Ctrl+A" } )
	menuDefinition.append( prefix + "/Select None", { "command" : selectNone, "shortCut" : "Shift+Ctrl+A", "active" : __selectionAvailable } )

	menuDefinition.append( prefix + "/Select Connected/Inputs", { "command" : selectInputs, "active" : __selectionAvailable } )
	menuDefinition.append( prefix + "/Select Connected/Add Inputs", { "command" : selectAddInputs, "active" : __selectionAvailable } )
	menuDefinition.append( prefix + "/Select Connected/InputsDivider", { "divider" : True } )
	menuDefinition.append( prefix + "/Select Connected/Outputs", { "command" : selectOutputs, "active" : __selectionAvailable } )
	menuDefinition.append( prefix + "/Select Connected/Add Outputs", { "command" : selectAddOutputs, "active" : __selectionAvailable } )

## A function suitable as the command for an Edit/Undo menu item. It must
# be invoked from a menu that has a ScriptWindow in its ancestry.
def undo( menu ) :

	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )
	script = scriptWindow.scriptNode()
	script.undo()
	
## A function suitable as the command for an Edit/Redo menu item. It must
# be invoked from a menu that has a ScriptWindow in its ancestry.
def redo( menu ) :

	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )
	script = scriptWindow.scriptNode()
	script.redo()

## A function suitable as the command for an Edit/Cut menu item. It must
# be invoked from a menu that has a ScriptWindow in its ancestry.
def cut( menu ) :

	script, parent = __scriptAndParent( menu )
	with Gaffer.UndoContext( script ) :
		script.cut( parent, script.selection() )

## A function suitable as the command for an Edit/Copy menu item. It must
# be invoked from a menu that has a ScriptWindow in its ancestry.
def copy( menu ) :

	script, parent = __scriptAndParent( menu )
	script.copy( parent, script.selection() )

## A function suitable as the command for an Edit/Paste menu item. It must
# be invoked from a menu that has a ScriptWindow in its ancestry.
def paste( menu ) :

	script, parent = __scriptAndParent( menu )
	originalSelection = Gaffer.StandardSet( iter( script.selection() ) )
	
	with Gaffer.UndoContext( script ) :
		
		script.paste( parent )
	
		# try to get the new nodes connected to the original selection
		nodeGraph = __nodeGraph( menu, focussedOnly=False )
		if nodeGraph is None :
			return

		nodeGraph.graphGadget().getLayout().connectNodes( nodeGraph.graphGadget(), script.selection(), originalSelection )

		# position the new nodes sensibly

		bound = nodeGraph.bound()
		mousePosition = GafferUI.Widget.mousePosition()
		if bound.intersects( mousePosition ) :
			fallbackPosition = mousePosition - bound.min
		else :
			fallbackPosition = bound.center() - bound.min

		fallbackPosition = nodeGraph.graphGadgetWidget().getViewportGadget().rasterToGadgetSpace(
			IECore.V2f( fallbackPosition.x, fallbackPosition.y ),
			gadget = nodeGraph.graphGadget()
		).p0
		fallbackPosition = IECore.V2f( fallbackPosition.x, fallbackPosition.y )

		nodeGraph.graphGadget().getLayout().positionNodes( nodeGraph.graphGadget(), script.selection(), fallbackPosition )
	
## A function suitable as the command for an Edit/Delete menu item. It must
# be invoked from a menu that has a ScriptWindow in its ancestry.
def delete( menu ) :

	script, parent = __scriptAndParent( menu )
	with Gaffer.UndoContext( script ) :
		script.deleteNodes( parent, script.selection() )
	
## A function suitable as the command for an Edit/Select All menu item. It must
# be invoked from a menu that has a ScriptWindow in its ancestry.
def selectAll( menu ) :

	script, parent = __scriptAndParent( menu )
	for c in parent.children( Gaffer.Node.staticTypeId() ) :
		script.selection().add( c )
			
## A function suitable as the command for an Edit/Select None menu item. It must
# be invoked from a menu that has a ScriptWindow in its ancestry.
def selectNone( menu ) :

	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )
	script = scriptWindow.scriptNode()
	
	script.selection().clear()				

## The command function for the default "Edit/Select Connected/Inputs" menu item. It must
# be invoked from a menu that has a ScriptWindow in its ancestry.
def selectInputs( menu ) :

	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )
	script = scriptWindow.scriptNode()
	
	inputs = Gaffer.StandardSet()
	for node in script.selection() :
		__inputNodes( node, inputs )
	
	selection = script.selection()
	selection.clear()
	for node in inputs :
		selection.add( node )

## The command function for the default "Edit/Select Connected/Add Inputs" menu item. It must
# be invoked from a menu that has a ScriptWindow in its ancestry.
def selectAddInputs( menu ) :

	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )
	script = scriptWindow.scriptNode()
	
	inputs = Gaffer.StandardSet()
	for node in script.selection() :
		__inputNodes( node, inputs )
		
	selection = script.selection()
	for node in inputs :
		selection.add( node )

## The command function for the default "Edit/Select Connected/Outputs" menu item. It must
# be invoked from a menu that has a ScriptWindow in its ancestry.
def selectOutputs( menu ) :

	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )
	script = scriptWindow.scriptNode()
	
	outputs = Gaffer.StandardSet()
	for node in script.selection() :
		__outputNodes( node, outputs )
	
	selection = script.selection()
	selection.clear()
	for node in outputs :
		selection.add( node )

## The command function for the default "Edit/Select Connected/Add Outputs" menu item. It must
# be invoked from a menu that has a ScriptWindow in its ancestry.
def selectAddOutputs( menu ) :

	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )
	script = scriptWindow.scriptNode()
	
	outputs = Gaffer.StandardSet()
	for node in script.selection() :
		__outputNodes( node, outputs )
	
	selection = script.selection()
	for node in outputs :
		selection.add( node )
				
def __selectionAvailable( menu ) :

	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )
	return True if scriptWindow.scriptNode().selection().size() else False
	
def __pasteAvailable( menu ) :

	scriptNode = menu.ancestor( GafferUI.ScriptWindow ).scriptNode()
	root = scriptNode.ancestor( Gaffer.ApplicationRoot.staticTypeId() )
	return isinstance( root.getClipboardContents(), IECore.StringData )

def __nodeGraph( menu, focussedOnly=True ) :

	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )

	nodeGraph = None
	## \todo Does this belong as a Window.focussedChild() method?
	focusWidget = GafferUI.Widget._owner( scriptWindow._qtWidget().focusWidget() )
	if focusWidget is not None :
		nodeGraph = focusWidget.ancestor( GafferUI.NodeGraph )
	
	if nodeGraph is not None or focussedOnly :
		return nodeGraph
			
	nodeGraphs = scriptWindow.getLayout().editors( GafferUI.NodeGraph )
	return nodeGraphs[0] if nodeGraphs else None

def __scriptAndParent( menu ) :

	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )
	script = scriptWindow.scriptNode()
	
	nodeGraph = __nodeGraph( menu )
	if nodeGraph is not None :
		parent = nodeGraph.graphGadget().getRoot()
	else :
		parent = script
	
	return script, parent

def __undoAvailable( menu ) :

	scriptNode = menu.ancestor( GafferUI.ScriptWindow ).scriptNode()
	return scriptNode.undoAvailable()
	
def __redoAvailable( menu ) :

	scriptNode = menu.ancestor( GafferUI.ScriptWindow ).scriptNode()
	return scriptNode.redoAvailable()

def __inputNodes( node, inputNodes ) :
	
	def __walkPlugs( parent ) :
	
		for plug in parent :
			if isinstance( plug, Gaffer.Plug ) :
				inputPlug = plug.getInput()
				if inputPlug is not None :
					inputNode = inputPlug.node()
					if inputNode is not None and not inputNode.isSame( node ) :
						inputNodes.add( inputNode )
				else :
					__walkPlugs( plug )

	__walkPlugs( node )

def __outputNodes( node, outputNodes ) :
	
	def __walkPlugs( parent ) :
	
		for plug in parent :
			if isinstance( plug, Gaffer.Plug ) :
				outputPlugs = plug.outputs()
				if outputPlugs :
					for outputPlug in outputPlugs :
						outputNode = outputPlug.node()
						if outputNode is not None and not outputNode.isSame( node ) :
							outputNodes.add( outputNode )
				else :
					__walkPlugs( plug )

	__walkPlugs( node )
