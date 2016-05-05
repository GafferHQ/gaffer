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

import IECore

import Gaffer
import GafferUI

Gaffer.Metadata.registerNode(

	Gaffer.Reference,

	"description",
	"""
	References a node network stored in another file. This can be used
	to share resources among scripts, build powerful non-linear workflows,
	and as the basis for custom asset management.

	To generate a file to be referenced, build a network inside a Box
	node and then export it for referencing.
	""",

	"layout:customWidget:fileName:widgetType", "GafferUI.ReferenceUI._FileNameWidget"

)

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

	fileName = _waitForFileName( parentWindow = menu.ancestor( GafferUI.Window ) )

	node = Gaffer.Reference()
	nodeGraph.graphGadget().getRoot().addChild( node )

	if fileName :
		_load( node, fileName, parentWindow = nodeGraph.ancestor( GafferUI.Window ) )

	return node

##########################################################################
# Custom widget for the filename - this forms the header for the node ui.
##########################################################################

class _FileNameWidget( GafferUI.Widget ) :

	def __init__( self, node, **kw ) :

		row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 )

		GafferUI.Widget.__init__( self, row, **kw )

		self.__node = node

		with row :

			label = GafferUI.Label( "File", horizontalAlignment = GafferUI.Label.HorizontalAlignment.Right )
			label._qtWidget().setFixedWidth( GafferUI.PlugWidget.labelWidth() )

			self.__textWidget = GafferUI.TextWidget( node.fileName(), editable = False )

			loadButton = GafferUI.Button( image = "pathChooser.png", hasFrame=False )
			loadButton.setToolTip( "Load" )
			self.__loadButtonClickedConnection = loadButton.clickedSignal().connect( Gaffer.WeakMethod( self.__loadClicked ) )

			self.__reloadButton = GafferUI.Button( image = "refresh.png", hasFrame=False )
			self.__reloadButton.setToolTip( "Reload" )
			self.__reloadButtonClickedConnection = self.__reloadButton.clickedSignal().connect( Gaffer.WeakMethod( self.__reloadClicked ) )

		self.__referenceLoadedConnection = node.referenceLoadedSignal().connect( Gaffer.WeakMethod( self.__referenceLoaded ) )

	def __loadClicked( self, button ) :

		fileName = _waitForFileName( self.__node.fileName(), parentWindow = self.ancestor( GafferUI.Window ) )
		if not fileName :
			return

		with Gaffer.UndoContext( self.__node.scriptNode() ) :
			_load( self.__node, fileName, self.ancestor( GafferUI.Window ) )

	def __reloadClicked( self, button ) :

		with Gaffer.UndoContext( self.__node.scriptNode() ) :
			_load( self.__node, self.__node.fileName(), self.ancestor( GafferUI.Window ) )

	def __referenceLoaded( self, node ) :

		self.__textWidget.setText( node.fileName() )

##########################################################################
# Utilities
##########################################################################

def _waitForFileName( initialFileName="", parentWindow=None ) :

	bookmarks = None
	if parentWindow is not None :
		bookmarks = GafferUI.Bookmarks.acquire( parentWindow, category="reference" )

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

def _load( node, fileName, parentWindow ) :

	messageWidget = GafferUI.MessageWidget()
	with messageWidget.messageHandler() as mh :
		try :
			node.load( fileName )
		except Exception as e :
			mh.handle( mh.Level.Error, "Loading Reference", str( e ) )

	if sum( [ messageWidget.messageCount( level ) for level in ( IECore.Msg.Level.Error, IECore.Msg.Level.Warning ) ] ) :
		dialogue = GafferUI.Dialogue( "Errors Occurred During Loading" )
		## \todo These dialogue methods should be available publicly.
		# Alternatively, we could make the ErrorDialogue class handle
		# messages as well as exceptions and use that here. Bear in mind
		# that we're doing the same thing in FileMenu.__open(), so we
		# definitely have a need for something like this.
		dialogue._setWidget( messageWidget )
		dialogue._addButton( "Oy vey" )
		dialogue.waitForButton( parentWindow=parentWindow )
