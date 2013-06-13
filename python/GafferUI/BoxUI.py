##########################################################################
#  
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

import re
import os

import IECore

import Gaffer
import GafferUI

## A command suitable for use with NodeMenu.append(), to add a menu
# item for the creation of a Box from the current selection. We don't
# actually append it automatically, but instead let the startup files
# for particular applications append it if it suits their purposes.
def nodeMenuCreateCommand( menu ) :

	nodeGraph = menu.ancestor( GafferUI.NodeGraph )
	assert( nodeGraph is not None )
	
	script = nodeGraph.scriptNode()
	graphGadget = nodeGraph.graphGadgetWidget().getViewportGadget().getChild()
	
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

def __showContents( nodeGraph, box ) :

	GafferUI.NodeGraph.acquire( box )

# NodeUI
##########################################################################

class BoxNodeUI( GafferUI.StandardNodeUI ) :

	def __init__( self, node, displayMode = None, **kw ) :
	
		GafferUI.StandardNodeUI.__init__( self, node, displayMode, **kw )
		
		## \todo Maybe this should become a customisable part of the StandardNodeUI - if so then
		# perhaps we need to integrate it with the existing presets menu in ParameterisedHolderNodeUI.
		toolButton = GafferUI.MenuButton( image = "gear.png", hasFrame=False )
		toolButton.setMenu( GafferUI.Menu( Gaffer.WeakMethod( self._toolMenuDefinition ) ) )

		self._tabbedContainer().setCornerWidget( toolButton )
	
	def _toolMenuDefinition( self ) :
	
		result = IECore.MenuDefinition()
		result.append( "/Export for referencing...", { "command" : Gaffer.WeakMethod( self.__exportForReferencing ) } )
		
		return result
		
	def __exportForReferencing( self ) :
	
		path = Gaffer.FileSystemPath( os.getcwd() )
		
		path.setFilter( Gaffer.FileSystemPath.createStandardFilter( [ "grf" ] ) )

		dialogue = GafferUI.PathChooserDialogue( path, title="Export for referencing", confirmLabel="Export" )
		path = dialogue.waitForPath( parentWindow = self.ancestor( GafferUI.Window ) )

		if not path :
			return

		path = str( path )
		if not path.endswith( ".grf" ) :
			path += ".grf"

		self.node().exportForReference( path )
	
GafferUI.NodeUI.registerNodeUI( Gaffer.Box.staticTypeId(), BoxNodeUI )

# PlugValueWidget registrations
##########################################################################

GafferUI.PlugValueWidget.registerCreator( Gaffer.Box.staticTypeId(), re.compile( "in[0-9]*" ), None )
GafferUI.PlugValueWidget.registerCreator( Gaffer.Box.staticTypeId(), re.compile( "out[0-9]*" ), None )

# Plug promotion
##########################################################################

def __promoteToBox( box, plug ) :

	with Gaffer.UndoContext( box.ancestor( Gaffer.ScriptNode.staticTypeId() ) ) :
		box.promotePlug( plug )

def __unpromoteFromBox( box, plug ) :

	with Gaffer.UndoContext( box.ancestor( Gaffer.ScriptNode.staticTypeId() ) ) :
		box.unpromotePlug( plug )

def __plugPopupMenu( menuDefinition, plugValueWidget ) :
	
	plug = plugValueWidget.getPlug()
	node = plug.node()
	if node is None :
		return

	box = node.ancestor( Gaffer.Box.staticTypeId() )
	if box is None :
		return

	if box.canPromotePlug( plug ) :
		
		menuDefinition.append( "/BoxDivider", { "divider" : True } )
		menuDefinition.append( "/Promote to %s" % box.getName(), { "command" : IECore.curry( __promoteToBox, box, plug ) } )

	elif box.plugIsPromoted( plug ) :
	
		# Add a menu item to unpromote the plug, replacing the "Remove input" menu item if it exists
		
		with IECore.IgnoredExceptions( Exception ) :
			menuDefinition.remove( "/Remove input" )
			
		menuDefinition.append( "/BoxDivider", { "divider" : True } )
		menuDefinition.append( "/Unpromote from %s" % box.getName(), { "command" : IECore.curry( __unpromoteFromBox, box, plug ) } )
			
__plugPopupMenuConnection = GafferUI.PlugValueWidget.popupMenuSignal().connect( __plugPopupMenu )
