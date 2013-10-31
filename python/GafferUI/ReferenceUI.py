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

import os
import re

import IECore

import Gaffer
import GafferUI

##########################################################################
# Public functions
##########################################################################

## A command suitable for use with NodeMenu.append(), to add a menu
# item for the creation of a Reference by selecting a file. We don't
# actually append it automatically, but instead let the startup files
# for particular applications append it if it suits their purposes.
def nodeMenuCreateCommand( menu ) :

	nodeGraph = menu.ancestor( GafferUI.NodeGraph )
	assert( nodeGraph is not None )
	graphGadget = nodeGraph.graphGadgetWidget().getViewportGadget().getChild()
	
	fileName = _waitForFileName( parentWindow = menu.ancestor( GafferUI.Window ) )

	node = Gaffer.Reference()
	graphGadget.getRoot().addChild( node )
	
	if fileName :
		node.load( fileName )
		
	return node

##########################################################################
# PlugValueWidget for the filename - this forms the header for the node ui.
##########################################################################

class __FileNamePlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :
	
		row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal )
	
		GafferUI.PlugValueWidget.__init__( self, row, plug, **kw )

		with row :
		
			self.__label = GafferUI.Label( "" )
			
			GafferUI.Spacer( IECore.V2i( 1, 30 ), expand = True )
		
			loadButton = GafferUI.Button( image = "pathChooser.png", hasFrame=False )
			loadButton.setToolTip( "Load" )
			self.__loadButtonClickedConnection = loadButton.clickedSignal().connect( Gaffer.WeakMethod( self.__loadClicked ) )
			
			self.__reloadButton = GafferUI.Button( image = "refresh.png", hasFrame=False )
			self.__reloadButton.setToolTip( "Reload" )
			self.__reloadButtonClickedConnection = self.__reloadButton.clickedSignal().connect( Gaffer.WeakMethod( self.__reloadClicked ) )
		
		self._updateFromPlug()

	def hasLabel( self ) :
	
		return True
		
	def _updateFromPlug( self ) :
	
		with self.getContext() :
	
			fileName = self.getPlug().getValue()
			self.__label.setText( "<h4>Filename : <small>" + fileName + "</small></h4>" )
			
			self.__reloadButton.setEnabled( True if fileName != "" else False )
			
	def __loadClicked( self, button ) :
	
		with self.getContext() :
			fileName = self.getPlug().getValue()
		
		fileName = _waitForFileName( fileName, parentWindow = self.ancestor( GafferUI.Window ) )
		if not fileName :
			return
			
		with Gaffer.UndoContext( self.getPlug().node().scriptNode() ) :
			self.getPlug().node().load( fileName )
		
	def __reloadClicked( self, button ) :
	
		with Gaffer.UndoContext( self.getPlug().node().scriptNode() ) :
			self.getPlug().node().load( self.getPlug().getValue() )
			
GafferUI.PlugValueWidget.registerCreator( Gaffer.Reference.staticTypeId(), "fileName", __FileNamePlugValueWidget )
GafferUI.Metadata.registerPlugValue( Gaffer.Reference, "fileName", "nodeUI:section", "header" )

GafferUI.PlugValueWidget.registerCreator( Gaffer.Reference.staticTypeId(), re.compile( "in[0-9]*" ), None )
GafferUI.PlugValueWidget.registerCreator( Gaffer.Reference.staticTypeId(), re.compile( "out[0-9]*" ), None )
GafferUI.PlugValueWidget.registerCreator( Gaffer.Reference.staticTypeId(), "user", GafferUI.UserPlugValueWidget, editable=False )

##########################################################################
# Utilities
##########################################################################

def _waitForFileName( initialFileName="", parentWindow=None ) :

	bookmarks = None
	if parentWindow is not None :
		if isinstance( parentWindow, GafferUI.ScriptWindow ) :
			scriptWindow = parentWindow
		else :
			scriptWindow = parentWindow.ancestor( GafferUI.ScriptWindow )
		if scriptWindow is not None :
			bookmarks = GafferUI.Bookmarks.acquire( scriptWindow.scriptNode().ancestor( Gaffer.ApplicationRoot.staticTypeId() ), category="reference" )

	if initialFileName :
		path = Gaffer.FileSystemPath( os.path.dirname( os.path.abspath( initialFileName ) ) )
	else :
		path = Gaffer.FileSystemPath( bookmarks.getDefault( parentWindow ) if bookmarks is not None else os.getcwd() )

	path.setFilter( Gaffer.FileSystemPath.createStandardFilter( [ "grf" ] ) )

	dialogue = GafferUI.PathChooserDialogue( path, title = "Load reference", confirmLabel = "Load", valid = True, leaf = True, bookmarks = bookmarks )
	path = dialogue.waitForPath( parentWindow = parentWindow )
	
	if not path :
		return ""
	
	return str( path )

##########################################################################
# Nodules
##########################################################################

GafferUI.Nodule.registerNodule( Gaffer.Reference.staticTypeId(), "fileName", lambda plug : None )

##########################################################################
# Metadata
##########################################################################

GafferUI.Metadata.registerPlugValue( Gaffer.Reference, "user", "nodeUI:section", "Settings" )
