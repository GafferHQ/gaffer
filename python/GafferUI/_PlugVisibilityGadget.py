##########################################################################
#
#  Copyright (c) 2026, Cinesite VFX Ltd. All rights reserved.
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

import Gaffer
import GafferUI

# This file adds context menu items associated with the PlugVisibilityGadget,
# the rest of which is implemented in `src/GafferUI/PlugVisibilityGadget.cpp`.

def __setPlugMetadata( plug, key, value ) :

	with Gaffer.UndoScope( plug.ancestor( Gaffer.ScriptNode ) ) :
		Gaffer.Metadata.registerValue( plug, key, value )

def __hasVisibilityGadget( plug ) :

	parent = plug.parent()
	while True :
		for key in Gaffer.Metadata.registeredValues( parent ) :
			if key.endswith( ":gadgetType" ) and Gaffer.Metadata.value( parent, key ) == "GafferUI.PlugVisibilityGadget" :
				return True
		parent = parent.parent()
		if parent is None or isinstance( parent, Gaffer.Node ) :
			return False

def __nodeHasVisibilityGadget( node ) :

	for p in Gaffer.Plug.RecursiveRange( node ) :
		for key in Gaffer.Metadata.registeredValues( p ) :
			if key.endswith( ":gadgetType" ) and Gaffer.Metadata.value( p, key ) == "GafferUI.PlugVisibilityGadget" :
				return True
	return False

def __hidablePlugs( node ) :

	result = []
	for plug in Gaffer.Plug.RecursiveRange( node ) :
		if (
			not __hasVisibilityGadget( plug ) or
			not Gaffer.Metadata.value( plug, "plugVisibilityGadget:showable" ) or
			Gaffer.Metadata.value( plug, "nodule:type" ) == "" or
			Gaffer.Metadata.value( plug, "noduleLayout:visible" ) == False
		) :
			continue
		result.append( plug )

	return result

def __graphEditorPlugContextMenu( graphEditor, plug, menuDefinition ) :

	if not __hasVisibilityGadget( plug ) or not Gaffer.Metadata.value( plug, "plugVisibilityGadget:showable" ) :
		return

	if len( menuDefinition.items() ) :
		menuDefinition.append( "/HideDivider", { "divider" : True } )

	if plug.direction() == plug.Direction.In :
		numConnections = 1 if plug.getInput() else 0
	else :
		numConnections = len( plug.outputs() )

	menuDefinition.append(

		"/Hide",
		{
			"command" : functools.partial( __setPlugMetadata, plug, "noduleLayout:visible", False ),
			"active" : numConnections == 0 and not Gaffer.MetadataAlgo.readOnly( plug ),
		}

	)

GafferUI.GraphEditor.plugContextMenuSignal().connect( __graphEditorPlugContextMenu )

##########################################################################
# GraphEditor context menu
##########################################################################

def __hideUnconnectedWalk( gadget ) :

	if isinstance( gadget, GafferUI.Nodule ) :

		plug = gadget.plug()

		if ( plug.direction() == plug.Direction.In and plug.getInput() ) or ( plug.direction() == plug.Direction.Out and len( plug.outputs() ) > 0 ) :
			return True

		if any( __hideUnconnectedWalk( g ) for g in gadget.children() ) :
			return True

		if (
			not Gaffer.MetadataAlgo.readOnly( plug ) and
			__hasVisibilityGadget( plug ) and
			Gaffer.Metadata.value( plug, "plugVisibilityGadget:showable" ) and
			Gaffer.Metadata.value( plug, "noduleLayout:visible" ) != False
		) :
			Gaffer.Metadata.registerValue( plug, "noduleLayout:visible", False )

		return False

	return sum( __hideUnconnectedWalk( c ) for c in gadget.children() ) > 0

def __hideUnconnected( graphGadget, nodeList ) :

	with Gaffer.UndoScope( graphGadget.getRoot().scriptNode() ) :
		for node in nodeList :
			nodeGadget = graphGadget.nodeGadget( node )
			if nodeGadget is None :
				continue

			__hideUnconnectedWalk( nodeGadget )

def __canHideUnconnectedPlugs( nodeList ) :

	nodeReadOnly = any( Gaffer.MetadataAlgo.readOnly( n ) for n in nodeList )
	hidablePlugs = [ p for n in nodeList for p in __hidablePlugs( n ) ]
	plugReadOnly = any( Gaffer.MetadataAlgo.readOnly( p ) for p in hidablePlugs )

	return not nodeReadOnly and not plugReadOnly and all( __nodeHasVisibilityGadget( n ) for n in nodeList )

def __editorKeyPress( editor, event ) :

	selection = editor.scriptNode().selection()
	if event.key == "Slash" and event.modifiers == event.Modifiers.None_ and __canHideUnconnectedPlugs( selection ) :
		__hideUnconnected( editor.graphGadget(), selection )
		return True

	return False

def appendNodeContextMenuDefinitions( graphEditor, nodeList, menuDefinition ) :

	def plugNodulesWalk( gadget ) :
		if isinstance( gadget, GafferUI.Nodule ) :
			return True
		return any( plugNodulesWalk( c ) for c in gadget.children() )

	graphGadget = graphEditor.graphGadget()
	for node in nodeList :
		if plugNodulesWalk( graphGadget.nodeGadget( node ) ) :

			menuDefinition.append(
				"/Connections/Hide Unconnected Plugs",
				{
					"command" : functools.partial( __hideUnconnected, graphGadget, nodeList ),
					"shortCut" : "/",
					"active" : __canHideUnconnectedPlugs( nodeList ),
				}
			)
			return

def connectToGraphEditor( editor ) :

	assert( isinstance( editor, GafferUI.GraphEditor ) )
	editor.keyPressSignal().connect( __editorKeyPress )
