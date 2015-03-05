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

import Gaffer

##########################################################################
# Public methods
##########################################################################

def appendNodeContextMenuDefinitions( nodeGraph, node, menuDefinition ) :

	if len( menuDefinition.items() ) :
		menuDefinition.append( "/GraphBookmarksDivider", { "divider" : True } )

	menuDefinition.append(
		"/Bookmarked",
		{
			"checkBox" : __getBookmarked( node ),
			"command" : functools.partial( __setBookmarked, node ),
			"active" : node.ancestor( Gaffer.Reference ) is None,
		}
	)

def appendPlugContextMenuDefinitions( nodeGraph, plug, menuDefinition ) :

	parent = nodeGraph.graphGadget().getRoot()
	dividerAdded = False
	for bookmark in __bookmarks( parent ) :
		
		nodeGadget = nodeGraph.graphGadget().nodeGadget( bookmark )
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
					"active" : not outPlug.isSame( inPlug.getInput() )
				}
			)

##########################################################################
# Internal implementation
##########################################################################

def __getBookmarked( node ) :

	return Gaffer.Metadata.nodeValue( node, "graphBookmarks:bookmarked" ) or False

def __setBookmarked( node, bookmarked ) :

	with Gaffer.UndoContext( node.scriptNode() ) :
		Gaffer.Metadata.registerNodeValue( node, "graphBookmarks:bookmarked", bookmarked )

def __bookmarks( parent ) :

	return [ n for n in parent.children( Gaffer.Node ) if __getBookmarked( n ) ]

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

	with Gaffer.UndoContext( inPlug.ancestor( Gaffer.ScriptNode ) ) :
		inPlug.setInput( outPlug )