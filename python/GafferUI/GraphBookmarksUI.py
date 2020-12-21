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

def appendNodeContextMenuDefinitions( graphEditor, node, menuDefinition ) :

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

	script = node.ancestor( Gaffer.ScriptNode )
	for i in range( 1, 10 ) :
		name = nodeSetLabel( script, i )
		title = "%d : %s" % ( i, name ) if name else str(i)
		menuDefinition.append(
			"/Node Set/%s" % title,
			{
				"command" : functools.partial( __assignNumericBookmark, node, i ),
				"shortCut" : "Ctrl+%i" % i,
				"active" : not Gaffer.MetadataAlgo.readOnly( node ),
			}
		)

	menuDefinition.append(
		"/Node Set/Remove",
		{
			"command" : functools.partial( __assignNumericBookmark, node, 0 ),
			"shortCut" : "Ctrl+0",
			"active" : Gaffer.MetadataAlgo.numericBookmark( node )
		}
	)

def appendPlugContextMenuDefinitions( graphEditor, plug, menuDefinition ) :

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

def appendNodeSetMenuDefinitions( editor, menuDefinition ) :

	weakEditor = weakref.ref( editor )

	# Follow bookmarks

	def followBookmark( number, weakEditor, _ ) :
		editor = weakEditor()
		if editor is not None :
			b = Gaffer.NumericBookmarkSet( editor.scriptNode(), number )
			editor.setNodeSet( b )

	n = editor.getNodeSet()

	script = editor.ancestor( GafferUI.ScriptWindow ).scriptNode()

	menuDefinition.append( "/NodeSet", { "divider" : True, "label" : "Node Set" } )

	for i in range( 1, 10 ) :
		name = nodeSetLabel( script, i )
		title = "%d : %s" % ( i, name ) if name else str(i)
		isCurrent = isinstance( n, Gaffer.NumericBookmarkSet ) and n.getBookmark() == i
		menuDefinition.append( "%s" % title, {
			"command" : functools.partial( followBookmark, i, weakEditor ),
			"checkBox" : isCurrent,
			"shortCut" : "%d" % i
		} )

def connectToEditor( editor ) :

	editor.keyPressSignal().connect( __editorKeyPress, scoped = False )

def connect( applicationRoot ) :

	def add( scriptsPlug, script ) :
		__addNodeSetSettings( script )

	applicationRoot["scripts"].childAddedSignal().connect( add, scoped = False )

def nodeSetLabel( script, setNumber ) :

	settings = __nodeSetSettings( script )
	return settings["label%d" % setNumber ].getValue() if settings is not None else ""

##########################################################################
# Internal implementation
##########################################################################

def __nodeSetSettings( script ) :

	if "nodeSets" in script :
		return script["nodeSets"]

	return None

def __addNodeSetSettings( script ) :

	if __nodeSetSettings( script ) is not None :
		return

	dynamicFlags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic

	p = Gaffer.Plug( flags = dynamicFlags )
	for i in range( 1, 10 ) :
		p[ "label%d" % i ] = Gaffer.StringPlug( flags = dynamicFlags )

	script["nodeSets"] = p

	for c in script["nodeSets"].children() :
		Gaffer.NodeAlgo.applyUserDefault( c )

Gaffer.Metadata.registerValue( Gaffer.ScriptNode, "nodeSets", "plugValueWidget:type", "GafferUI.LayoutPlugValueWidget" )
Gaffer.Metadata.registerValue( Gaffer.ScriptNode, "nodeSets", "layout:section", "Node Sets" )

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
		return

	# Don't modify the contents of floating windows, because these are
	# expected to be locked to one node.
	if editor.ancestor( GafferUI.CompoundEditor ) is None :
		return

	if bookmarks is None :
		bookmarks = __findableBookmarks( editor )

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

	if not len( bookmarks ) :
		menuDefinition.append( "/No bookmarks available", { "active" : False, "searchText" : "" } )

	editor.__findBookmarksMenu = GafferUI.Menu( menuDefinition, title = "Find Bookmark", searchable = True )
	editor.__findBookmarksMenu.popup()

def __assignNumericBookmark( node, numericBookmark ) :

	with Gaffer.UndoScope( node.scriptNode() ) :
		if numericBookmark == 0 : # Remove the current numeric bookmark from selection
			current = Gaffer.MetadataAlgo.numericBookmark( node )
			if current :
				Gaffer.MetadataAlgo.setNumericBookmark( node.scriptNode(), current, None )
		else :
			Gaffer.MetadataAlgo.setNumericBookmark( node.scriptNode(), numericBookmark, node )

def __findNumericBookmark( editor, numericBookmark ) :

	if not isinstance( editor, ( GafferUI.NodeSetEditor, GafferUI.GraphEditor ) ) :
		return False

	# Don't modify the contents of floating windows, because these are
	# expected to be locked to one node.
	if editor.ancestor( GafferUI.CompoundEditor ) is None :
		return False

	node = Gaffer.MetadataAlgo.getNumericBookmark( editor.scriptNode(), numericBookmark )
	if not node :
		return False

	if isinstance( editor, GafferUI.GraphEditor ) :
		editor.graphGadget().setRoot( node.parent() )
		editor.frame( [ node ] )
	else :
		s = Gaffer.NumericBookmarkSet( editor.scriptNode(), numericBookmark )
		editor.setNodeSet( s )

	return True

def __editorKeyPress( editor, event ) :

	if event.key == "B" :
		__findBookmark( editor )
		return True

	if event.key in [ str( x ) for x in range( 0, 10 ) ] :

		numericBookmark = int( event.key )

		if event.modifiers == event.modifiers.Control :

			# Assign

			node = None
			if isinstance( editor, GafferUI.GraphEditor ) :
				selection = editor.scriptNode().selection()
				if len( selection ) == 1 :
					node = selection[0]
				else :
					backdrops = [ n for n in selection if isinstance( n, Gaffer.Backdrop ) ]
					if len( backdrops ) == 1 :
						node = backdrops[0]
			elif isinstance( editor, GafferUI.NodeSetEditor ) :
				nodeSet = editor.getNodeSet()
				node = nodeSet[-1] if len( nodeSet ) else None

			if node is not None :
				__assignNumericBookmark( node, numericBookmark )

		elif not event.modifiers :

			# Find

			# For linked editors, its more intuitive for the user if we update
			# the driving editor, rather than breaking the link.

			if numericBookmark != 0 :
				__findNumericBookmark( editor, numericBookmark )
			elif isinstance( editor, GafferUI.NodeSetEditor ) :
				editor.setNodeSet( editor.scriptNode().selection() )

		return True


