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
import itertools

import Gaffer
import GafferUI

# This file adds context menu items associated with the PlugVisibilityGadget,
# the rest of which is implemented in `src/GafferUI/PlugVisibilityGadget.cpp`.

def __hide( plugs ) :

	with Gaffer.UndoScope( next( iter( plugs ) ).ancestor( Gaffer.ScriptNode ) ) :
		for plug in plugs :
			Gaffer.Metadata.registerValue( plug, "noduleLayout:visible", False )

def __managedPlugs( parent ) :

	for key in Gaffer.Metadata.registeredValues( parent ) :
		if key.endswith( ":gadgetType" ) and Gaffer.Metadata.value( parent, key ) == "GafferUI.PlugVisibilityGadget" :
			return [
				p for p in Gaffer.Metadata.plugsWithMetadata( parent, "plugVisibilityGadget:showable" )
				if Gaffer.Metadata.value( p, "plugVisibilityGadget:showable" )
			]

	result = []
	for child in Gaffer.GraphComponent.Range( parent ) :
		result.extend( __managedPlugs( child ) )

	return result

def __unconnected( plug ) :

	if plug.direction() == plug.Direction.In :
		return plug.getInput() is None and all( p.getInput() is None for p in Gaffer.Plug.RecursiveRange( plug ) )
	else :
		return len( plug.outputs() ) == 0 and all( len( p.outputs() ) == 0 for p in Gaffer.Plug.RecursiveRange( plug ) )

def __visible( plug ) :

	return Gaffer.Metadata.value( plug, "noduleLayout:visible" ) != False and Gaffer.Metadata.value( plug, "nodule:type" ) != ""

def __graphEditorPlugContextMenu( graphEditor, plug, menuDefinition ) :

	if plug not in __managedPlugs( plug.node() ) :
		return

	if len( menuDefinition.items() ) :
		menuDefinition.append( "/HideDivider", { "divider" : True } )

	menuDefinition.append(

		"/Hide",
		{
			"command" : functools.partial( __hide, [ plug ] ),
			"active" : __unconnected( plug ) and not Gaffer.MetadataAlgo.readOnly( plug ),
		}

	)

def __graphEditorKeyPress( editor, event ) :

	assert( isinstance( editor, GafferUI.GraphEditor ) )
	if event.key == "Slash" and event.modifiers == event.Modifiers.None_ :

		nodes = [ n for n in editor.scriptNode().selection() if n.parent() == editor.graphGadget().getRoot() ]
		toHide = []
		for node in nodes :
			toHide.extend( [ p for p in __managedPlugs( node ) if __unconnected( p ) and __visible( p ) ] )

		if toHide and not any( Gaffer.MetadataAlgo.readOnly( p ) for p in toHide ) :
			__hide( toHide )

		return True

	return False

def __graphEditorNodeContextMenu( graphEditor, nodeList, menuDefinition ) :

	managedPlugs = [ __managedPlugs( node ) for node in nodeList ]
	if all( managedPlugs ) :
		toHide = [ p for p in itertools.chain( *managedPlugs ) if __unconnected( p ) and __visible( p ) ]
		menuDefinition.append(
			"/Connections/Hide Unconnected Plugs",
			{
				"command" : functools.partial( __hide, toHide ),
				"shortCut" : "/",
				"active" : len( toHide ) and not any( Gaffer.MetadataAlgo.readOnly( p ) for p in toHide ),
			}
		)
		return

def connectToEditor( editor ) :

	if not isinstance( editor, GafferUI.GraphEditor ) :
		return

	editor.plugContextMenuSignal().connect( __graphEditorPlugContextMenu )
	editor.nodeContextMenuSignal( True ).connect( __graphEditorNodeContextMenu )
	editor.keyPressSignal().connect( __graphEditorKeyPress )
