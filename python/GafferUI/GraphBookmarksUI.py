##########################################################################
#
#  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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
import weakref

import IECore

import Gaffer
import GafferUI

##########################################################################
# Public methods
##########################################################################

## May be called to connect the GraphBookmarksUI functionality to an application
# instance. This isn't done automatically because some applications may decide
# to not use bookmarks. Typically this function would be called from an
# application startup file.
def connect( applicationRoot ) :

	applicationRoot.__graphBookmarksUIConnected = True

def appendNodeContextMenuDefinitions( graphEditor, node, menuDefinition ) :

	if not __isConnected( graphEditor ) :
		return

	if len( menuDefinition.items() ) :
		menuDefinition.append( "/GraphBookmarksDivider", { "divider" : True } )

	menuDefinition.append(
		"/Bookmarked",
		{
			"checkBox" : Gaffer.MetadataAlgo.getBookmarked( node ),
			"command" : functools.partial( __setBookmarked, node ),
			"active" : not Gaffer.MetadataAlgo.readOnly( node ),
		}
	)

	for i in range( 1, 10 ) :
	  menuDefinition.append(
		  "/Numeric Bookmark/%s" % i,
		  {
			  "command" : functools.partial( assignNumericBookmark, graphEditor, i ),
			  "shortCut" : "Ctrl+%i" % i,
		  }
	  )

	menuDefinition.append(
		"/Numeric Bookmark/Remove",
		{
			"command" : functools.partial( assignNumericBookmark, graphEditor, 0 ),
			"shortCut" : "Ctrl+0",
			"active" : Gaffer.MetadataAlgo.numericBookmark( node )
		}
	)

GafferUI.GraphEditor.nodeContextMenuSignal().connect( appendNodeContextMenuDefinitions, scoped = False )

def appendPlugContextMenuDefinitions( graphEditor, plug, menuDefinition ) :

	if not __isConnected( graphEditor ) :
		return

	parent = graphEditor.graphGadget().getRoot()
	dividerAdded = False
	for bookmark in Gaffer.MetadataAlgo.bookmarks( parent ) :

		nodeGadget = graphEditor.graphGadget().nodeGadget( bookmark )
		if nodeGadget is None :
			continue

		compatibleConnections = []
		for nodule in __nodules( nodeGadget ) :
			inPlug, outPlug = __connection( plug, nodule.plug() )
			if inPlug is not None :
				compatibleConnections.append( ( inPlug, outPlug ) )

		if not compatibleConnections :
			continue

		if not dividerAdded :
			if len( menuDefinition.items() ) :
				menuDefinition.append( "/BookmarksDivider", { "divider" : True } )
			dividerAdded = True

		for inPlug, outPlug in compatibleConnections :
			label = bookmark.getName()
			if len( compatibleConnections ) > 1 :
				bookmarkPlug = outPlug if inPlug.isSame( plug ) else inPlug
				label += "/"  + bookmarkPlug.relativeName( bookmark )
			menuDefinition.append(
				"/Connect Bookmark/" + label,
				{
					"command" : functools.partial( __connect, inPlug, outPlug ),
					"active" : not outPlug.isSame( inPlug.getInput() ) and not Gaffer.MetadataAlgo.readOnly( inPlug )
				}
			)

GafferUI.GraphEditor.plugContextMenuSignal().connect( appendPlugContextMenuDefinitions, scoped = False )

def appendNodeSetMenuDefinitions( editor, menuDefinition ) :

	if len( editor.getNodeSet() ) :
		primaryNode = editor.getNodeSet()[-1]
	else :
		primaryNode = None

	menuDefinition.append(
		"/Bookmarked",
		{
			"checkBox" : primaryNode is not None and Gaffer.MetadataAlgo.getBookmarked( primaryNode ),
			"command" : functools.partial( __setBookmarked, primaryNode ),
			"active" : primaryNode is not None and not Gaffer.MetadataAlgo.readOnly( primaryNode ),
		}
	)

	for i in range( 1, 10 ) :
	  menuDefinition.append(
		  "/Numeric Bookmark/%s" % i,
		  {
			  "command" : functools.partial( findNumericBookmark, editor, i ),
		  }
	  )

	bookmarks = __findableBookmarks( editor )
	menuDefinition.append(
		"/Find Bookmark...",
		{
			"command" : functools.partial( __findBookmark, editor, bookmarks ),
			"active" : len( bookmarks ),
			"shortCut" : "Ctrl+B",
		}
	)

def popupFindBookmarkMenu( editor ) :

	__findBookmark( editor )

def assignNumericBookmark( editor, numericBookmark ) :

	if not isinstance( editor, GafferUI.GraphEditor ) :
		return False

	selection = editor.scriptNode().selection()
	node = None
	if len( selection ) == 1 :
		node = selection[0]
	else :
		backdrops = [n for n in selection if isinstance( n, Gaffer.Backdrop )]
		if len( backdrops ) == 1 :
			node = backdrops[0]

	if not node :
		return False

	with Gaffer.UndoScope( node.scriptNode() ) :
		if numericBookmark == 0:  # Remove the current numeric bookmark from selection
			current = Gaffer.MetadataAlgo.numericBookmark( node )
			if current :
				Gaffer.MetadataAlgo.setNumericBookmark( editor.scriptNode(), current, None )
		else :
			Gaffer.MetadataAlgo.setNumericBookmark( editor.scriptNode(), numericBookmark, node )

	return True

def findNumericBookmark( editor, numericBookmark ) :

	if not isinstance( editor, ( GafferUI.NodeSetEditor, GafferUI.GraphEditor ) ) :
		return False

	# Don't modify the contents of floating windows, because these are
	# expected to be locked to one node.
	if editor.ancestor( GafferUI.CompoundEditor ) is  None :
		return False

	node = Gaffer.MetadataAlgo.getNumericBookmark( editor.scriptNode(), numericBookmark )

	if not node :
		return False

	if isinstance( editor, GafferUI.GraphEditor ) :
		editor.graphGadget().setRoot( node.parent() )
		editor.frame( [ node ] )
	else :
		editor.setNodeSet( Gaffer.StandardSet( [ node ] ) )

	return True

##########################################################################
# Internal implementation
##########################################################################

def __isConnected( editor ) :

	applicationRoot = editor.scriptNode().ancestor( Gaffer.ApplicationRoot )
	connected = False
	with IECore.IgnoredExceptions( AttributeError ) :
		connected = applicationRoot.__graphBookmarksUIConnected

	return connected

def __setBookmarked( node, bookmarked ) :

	with Gaffer.UndoScope( node.scriptNode() ) :
		Gaffer.MetadataAlgo.setBookmarked( node, bookmarked )

## \todo Perhaps this functionality should be provided by the
# GraphGadget or NodeGadget class?
def __nodules( nodeGadget ) :

	result = []
	def walk( graphComponent ) :

		if isinstance( graphComponent, Gaffer.Plug ) :
			nodule = nodeGadget.nodule( graphComponent )
			if nodule is not None :
				result.append( nodule )

		for c in graphComponent.children( Gaffer.Plug ) :
			walk( c )

	walk( nodeGadget.node() )
	return result

## \todo This is similar to the private
# StandardNodule::connection() method. Perhaps we
# should find a single sensible place to put it?
# Maybe on the GraphGadget class? Or in a new
# PlugAlgo.h file?
def __connection( plug1, plug2 ) :

	if plug1.node().isSame( plug2.node() ) :
		return None, None

	if plug1.direction() == plug2.direction() :
		return None, None

	if plug1.direction() == plug1.Direction.In :
		inPlug, outPlug = plug1, plug2
	else :
		inPlug, outPlug = plug2, plug1

	if inPlug.acceptsInput( outPlug ) :
		return inPlug, outPlug

	return None, None

def __connect( inPlug, outPlug ) :

	with Gaffer.UndoScope( inPlug.ancestor( Gaffer.ScriptNode ) ) :
		inPlug.setInput( outPlug )

def __editBookmark( editorWeakRef, bookmark ) :

	editor = editorWeakRef()

	if isinstance( editor, GafferUI.GraphEditor ) :
		editor.graphGadget().setRoot( bookmark.parent() )
		editor.frame( [ bookmark ] )
	else :
		editor.setNodeSet( Gaffer.StandardSet( [ bookmark ] ) )

def __findableBookmarks( editor ) :

	# Prefer this over manual recursion through the graph because it is _much_
	# faster.
	bookmarks = Gaffer.Metadata.nodesWithMetadata( editor.scriptNode(), "bookmarked", instanceOnly = True )
	return [ b for b in bookmarks if b.ancestor( Gaffer.Reference ) is None ]

def __findBookmark( editor, bookmarks = None ) :

	if not isinstance( editor, ( GafferUI.NodeSetEditor, GafferUI.GraphEditor ) ) :
		return False

	# Don't modify the contents of floating windows, because these are
	# expected to be locked to one node.
	if editor.ancestor( GafferUI.CompoundEditor ) is  None :
		return False

	if bookmarks is None :
		bookmarks = __findableBookmarks( editor )

	if not bookmarks :
		return False

	scriptNode = editor.scriptNode()
	pathsAndNodes = [
		( "/" + b.relativeName( scriptNode ).replace( ".", "/" ), b )
		for b in bookmarks
	]

	pathsAndNodes.sort( key = lambda x : x[0] )

	menuDefinition = IECore.MenuDefinition()
	for i, ( path, node ) in enumerate( pathsAndNodes ) :

		haveDescendantBookmarks = False
		if i < len( pathsAndNodes ) - 1 :
			nextPath = pathsAndNodes[i+1][0]
			if nextPath[len(path):len(path)+1] == "/" :
				haveDescendantBookmarks = True

		command = functools.partial( __editBookmark, weakref.ref( editor ), node )
		if haveDescendantBookmarks :
			menuDefinition.append( path + "/This Node", { "command" : command, "searchText" : node.getName() } )
			menuDefinition.append( path + "/__BookmarksParentDivider__", { "divider" : True } )
		else :
			menuDefinition.append( path, { "command" : command } )

	editor.__findBookmarksMenu = GafferUI.Menu( menuDefinition, title = "Find Bookmark", searchable = True )
	editor.__findBookmarksMenu.popup()

	return True

def __editorKeyPress( editor, event ) :

	if event.key == "B" and event.modifiers == event.modifiers.Control :
		return GafferUI.GraphBookmarksUI.popupFindBookmarkMenu( editor )

	if event.key == '0' :
		if isinstance( editor, GafferUI.GraphEditor ) :
			return GafferUI.GraphBookmarksUI.setNumericBookmark( editor, 0 )
		if isinstance( editor, GafferUI.NodeSetEditor ) :
			editor.setNodeSet( editor.scriptNode().selection() )
			return True

	if event.key in map( str, range( 1, 10 ) ) :
		if event.modifiers == event.modifiers.Control :
			return GafferUI.GraphBookmarksUI.assignNumericBookmark( editor, int( event.key ) )
		else :
			return GafferUI.GraphBookmarksUI.findNumericBookmark( editor, int( event.key ) )

	return False

def __editorCreated( editor ) :

	if not __isConnected( editor ) :
		return

	editor.keyPressSignal().connect( __editorKeyPress, scoped = False )

GafferUI.Editor.instanceCreatedSignal().connect( __editorCreated, scoped = False )

def __nodeSetMenu( editor, menuDefinition ) :

	if not __isConnected( editor ) :
		return

	GafferUI.GraphBookmarksUI.appendNodeSetMenuDefinitions( editor, menuDefinition )

GafferUI.CompoundEditor.nodeSetMenuSignal().connect( __nodeSetMenu, scoped = False )
