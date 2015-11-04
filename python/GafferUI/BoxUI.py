##########################################################################
#
#  Copyright (c) 2013-2015, Image Engine Design Inc. All rights reserved.
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

import re
import os
import functools

import IECore

import Gaffer
import GafferUI

Gaffer.Metadata.registerNode(

	Gaffer.Box,

	"description",
	"""
	A container for "subgraphs" - node networks which exist inside the
	Box and can be exposed by promoting selected internal plugs onto the
	outside of the Box.

	Boxes can be used as an organisational tool for simplifying large
	graphs by collapsing them into sections which perform distinct tasks.
	They are also used for authoring files to be used with the Reference
	node.
	""",

	# Add a + button for creating new plugs in the Settings tab.
	"layout:customWidget:addButton:widgetType", "GafferUI.UserPlugs.plugCreationWidget",
	"layout:customWidget:addButton:section", "Settings",
	"layout:customWidget:addButton:index", -2,

	plugs = {

		"user" : [

			# Disable the + button added by NodeUI, since
			# we want users to use the button in the Settings
			# tab instead.
			"layout:customWidget:addButton:widgetType", "",

		],

	}

)

##########################################################################
# Public functions
##########################################################################

## A command suitable for use with NodeMenu.append(), to add a menu
# item for the creation of a Box from the current selection. We don't
# actually append it automatically, but instead let the startup files
# for particular applications append it if it suits their purposes.
def nodeMenuCreateCommand( menu ) :

	nodeGraph = menu.ancestor( GafferUI.NodeGraph )
	assert( nodeGraph is not None )

	script = nodeGraph.scriptNode()
	graphGadget = nodeGraph.graphGadget()

	return Gaffer.Box.create( graphGadget.getRoot(), script.selection() )

## A callback suitable for use with NodeGraph.nodeContextMenuSignal - it provides
# menu options specific to Boxes. We don't actually register it automatically,
# but instead let the startup files for particular applications register
# it if it suits their purposes.
def appendNodeContextMenuDefinitions( nodeGraph, node, menuDefinition ) :

	if not isinstance( node, Gaffer.Box ) :
		return

	menuDefinition.append( "/BoxDivider", { "divider" : True } )
	menuDefinition.append( "/Show Contents...", { "command" : IECore.curry( __showContents, nodeGraph, node ) } )

## A callback suitable for use with NodeEditor.toolMenuSignal() - it provides
# menu options specific to Boxes. We don't actually register it automatically,
# but instead let the startup files for particular applications register
# it if it suits their purposes.
def appendNodeEditorToolMenuDefinitions( nodeEditor, node, menuDefinition ) :

	if not isinstance( node, Gaffer.Box ) :
		return

	menuDefinition.append( "/BoxDivider", { "divider" : True } )
	menuDefinition.append( "/Export for referencing...", { "command" : functools.partial( __exportForReferencing, node = node ) } )

def __showContents( nodeGraph, box ) :

	GafferUI.NodeGraph.acquire( box )

def __exportForReferencing( menu, node ) :

	bookmarks = GafferUI.Bookmarks.acquire( node, category="reference" )

	path = Gaffer.FileSystemPath( bookmarks.getDefault( menu ) )
	path.setFilter( Gaffer.FileSystemPath.createStandardFilter( [ "grf" ] ) )

	dialogue = GafferUI.PathChooserDialogue( path, title="Export for referencing", confirmLabel="Export", leaf=True, bookmarks=bookmarks )
	path = dialogue.waitForPath( parentWindow = menu.ancestor( GafferUI.Window ) )

	if not path :
		return

	path = str( path )
	if not path.endswith( ".grf" ) :
		path += ".grf"

	node.exportForReference( path )

# PlugValueWidget registrations
##########################################################################

GafferUI.PlugValueWidget.registerCreator( Gaffer.Box, re.compile( "in[0-9]*" ), None )
GafferUI.PlugValueWidget.registerCreator( Gaffer.Box, re.compile( "out[0-9]*" ), None )

# Shared menu code
##########################################################################

def __deletePlug( plug ) :

	with Gaffer.UndoContext( plug.ancestor( Gaffer.ScriptNode ) ) :
		plug.parent().removeChild( plug )

def __appendPlugDeletionMenuItems( menuDefinition, plug, readOnly = False ) :

	if not isinstance( plug.node(), Gaffer.Box ) :
		return

	menuDefinition.append( "/DeleteDivider", { "divider" : True } )
	menuDefinition.append( "/Delete", {
		"command" : functools.partial( __deletePlug, plug ),
		"active" : not readOnly,
	} )

def __promoteToBox( box, plug ) :

	with Gaffer.UndoContext( box.ancestor( Gaffer.ScriptNode ) ) :
		box.promotePlug( plug )

def __unpromoteFromBox( box, plug ) :

	with Gaffer.UndoContext( box.ancestor( Gaffer.ScriptNode ) ) :
		box.unpromotePlug( plug )

def __promoteToBoxEnabledPlug( box, plug ) :

	with Gaffer.UndoContext( box.ancestor( Gaffer.ScriptNode ) ) :
		enabledPlug = box.getChild( "enabled" )
		if enabledPlug is None :
			enabledPlug = Gaffer.BoolPlug( "enabled", defaultValue = True, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		box["enabled"] = enabledPlug
		plug.setInput( enabledPlug )

def __appendPlugPromotionMenuItems( menuDefinition, plug, readOnly = False ) :

	node = plug.node()
	if node is None :
		return

	box = node.ancestor( Gaffer.Box )
	if box is None :
		return

	if box.canPromotePlug( plug ) :

		if len( menuDefinition.items() ) :
			menuDefinition.append( "/BoxDivider", { "divider" : True } )

		menuDefinition.append( "/Promote to %s" % box.getName(), {
			"command" : IECore.curry( __promoteToBox, box, plug ),
			"active" : not readOnly,
		} )

		if isinstance( plug.parent(), Gaffer.ArrayPlug ) and box.canPromotePlug( plug.parent() ) :
			menuDefinition.append( "/Promote %s array to %s" % ( plug.parent().getName(), box.getName() ), {
				"command" : IECore.curry( __promoteToBox, box, plug.parent() ),
				"active" : not readOnly,
			} )

		if isinstance( node, Gaffer.DependencyNode ) :
			if plug.isSame( node.enabledPlug() ) :
				menuDefinition.append( "/Promote to %s.enabled" % box.getName(), {
					"command" : IECore.curry( __promoteToBoxEnabledPlug, box, plug ),
					"active" : not readOnly,
				} )

	elif box.plugIsPromoted( plug ) :

		# Add a menu item to unpromote the plug, replacing the "Remove input" menu item if it exists

		with IECore.IgnoredExceptions( Exception ) :
			menuDefinition.remove( "/Remove input" )

		if len( menuDefinition.items() ) :
			menuDefinition.append( "/BoxDivider", { "divider" : True } )

		if isinstance( plug.parent(), Gaffer.ArrayPlug ) and box.plugIsPromoted( plug.parent() ) :
			menuDefinition.append( "/Unpromote %s array from %s" % ( plug.parent().getName(), box.getName() ), {
				"command" : IECore.curry( __unpromoteFromBox, box, plug.parent() ),
				"active" : not readOnly,
			} )
		else :
			# we dont want to allow unpromoting for children of promoted arrays as it
			# causes unpredicted behaviour, and it doesn't seem useful in general.
			menuDefinition.append( "/Unpromote from %s" % box.getName(), {
				"command" : IECore.curry( __unpromoteFromBox, box, plug ),
				"active" : not readOnly,
			} )

# PlugValueWidget menu
##########################################################################

def __plugPopupMenu( menuDefinition, plugValueWidget ) :

	__appendPlugDeletionMenuItems( menuDefinition, plugValueWidget.getPlug(), readOnly = plugValueWidget.getReadOnly() )
	__appendPlugPromotionMenuItems( menuDefinition, plugValueWidget.getPlug(), readOnly = plugValueWidget.getReadOnly() )

__plugPopupMenuConnection = GafferUI.PlugValueWidget.popupMenuSignal().connect( __plugPopupMenu )

# NodeGraph plug context menu
##########################################################################

def __renamePlug( menu, plug ) :

	d = GafferUI.TextInputDialogue( initialText = plug.getName(), title = "Enter name", confirmLabel = "Rename" )
	name = d.waitForText( parentWindow = menu.ancestor( GafferUI.Window ) )

	if not name :
		return

	with Gaffer.UndoContext( plug.ancestor( Gaffer.ScriptNode ) ) :
		plug.setName( name )

def __setPlugMetadata( plug, key, value ) :

	with Gaffer.UndoContext( plug.ancestor( Gaffer.ScriptNode ) ) :
		Gaffer.Metadata.registerPlugValue( plug, key, value )

def __edgePlugs( nodeGraph, plug ) :

	nodeGadget = nodeGraph.graphGadget().nodeGadget( plug.node() )
	nodule = nodeGadget.nodule( plug )
	return [ n.plug() for n in nodule.parent().children( GafferUI.Nodule ) ]

def __reorderPlugs( plugs, plug, newIndex ) :

	plugs.remove( plug )
	plugs.insert( newIndex, plug )
	with Gaffer.UndoContext( plug.ancestor( Gaffer.ScriptNode ) ) :
		for index, plug in enumerate( plugs ) :
			Gaffer.Metadata.registerPlugValue( plug, "nodeGadget:noduleIndex", index )

def __nodeGraphPlugContextMenu( nodeGraph, plug, menuDefinition ) :

	if isinstance( plug.node(), Gaffer.Box ) :

		menuDefinition.append( "/Rename...", { "command" : functools.partial( __renamePlug, plug = plug ) } )

		menuDefinition.append( "/MoveDivider", { "divider" : True } )

		currentEdge = Gaffer.Metadata.plugValue( plug, "nodeGadget:nodulePosition" )
		if not currentEdge :
			currentEdge = "top" if plug.direction() == plug.Direction.In else "bottom"

		for edge in ( "top", "bottom", "left", "right" ) :
			menuDefinition.append(
				"/Move To/" + edge.capitalize(),
				{
					"command" : functools.partial( __setPlugMetadata, plug, "nodeGadget:nodulePosition", edge ),
					"active" : edge != currentEdge,
				}
			)

		edgePlugs = __edgePlugs( nodeGraph, plug )
		edgeIndex = edgePlugs.index( plug )
		menuDefinition.append(
			"/Move " + ( "Up" if currentEdge in ( "left", "right" ) else "Left" ),
			{
				"command" : functools.partial( __reorderPlugs, edgePlugs, plug, edgeIndex - 1 ),
				"active" : edgeIndex > 0,
			}
		)

		menuDefinition.append(
			"/Move " + ( "Down" if currentEdge in ( "left", "right" ) else "Right" ),
			{
				"command" : functools.partial( __reorderPlugs, edgePlugs, plug, edgeIndex + 1 ),
				"active" : edgeIndex < len( edgePlugs ) - 1,
			}
		)

	__appendPlugDeletionMenuItems( menuDefinition, plug )
	__appendPlugPromotionMenuItems( menuDefinition, plug )

__nodeGraphPlugContextMenuConnection = GafferUI.NodeGraph.plugContextMenuSignal().connect( __nodeGraphPlugContextMenu )
