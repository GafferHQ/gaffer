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

import enum
import imath
import functools
from collections import deque

import IECore

import Gaffer
import GafferUI

import GafferScene
import GafferSceneUI

##########################################################################
# Metadata
##########################################################################

Gaffer.Metadata.registerNode(

	GafferScene.PathFilter,

	"description",
	"""
	Chooses locations by matching them against a list of
	paths.
	""",

	"ui:spreadsheet:enabledRowNamesConnection", "paths",
	"ui:spreadsheet:selectorValue", "${scene:path}",

	plugs = {

		"paths" : [

			"description",
			"""
			The list of paths to the locations to be matched by the filter.
			A path is formed by a sequence of names separated by `/`, and
			specifies the hierarchical position of a location within the scene.
			Paths may use Gaffer's standard wildcard characters to match
			multiple locations.

			The `*` wildcard matches any sequence of characters within
			an individual name, but never matches across names separated
			by a `/`.

			 - `/robot/*Arm` matches `/robot/leftArm`, `/robot/rightArm` and
			   `/robot/Arm`. But does not match `/robot/limbs/leftArm` or
			   `/robot/arm`.

			The `...` wildcard matches any sequence of names, and can be
			used to match locations no matter where they are parented in
			the hierarchy.

			 - `/.../house` matches `/house`, `/street/house` and `/city/street/house`.
			""",

			"nodule:type", "",
			"ui:scene:acceptsPaths", True,

			"vectorDataPlugValueWidget:dragPointer", "objects",

			"plugValueWidget:type", "GafferSceneUI.PathFilterUI._PathsPlugValueWidget",

		],

		"roots" : [

			"description",
			"""
			An optional filter input used to provide multiple root locations
			which the `paths` are relative to. This can be useful when working
			on a single asset in isolation, and then placing it into multiple
			locations within a layout. When no filter is connected, all `paths`
			are treated as being relative to `/`, the true scene root.
			""",

			"plugValueWidget:type", "",

		],

	}

)

##########################################################################
# VectorDataPlugValueWidget customisation
###########################################################################

def __targetFilterPlug( plug ) :

	return Gaffer.PlugAlgo.findDestination(
		plug,
		lambda plug : plug if isinstance( plug.parent(), GafferScene.PathFilter ) and plug.getName() == "paths" else None
	)

def _selectAffected( plug, selection ) :

	inPlugs = []

	rowPlug = plug.ancestor( Gaffer.Spreadsheet.RowPlug )

	targetPlug = __targetFilterPlug( plug )

	if targetPlug is not None :
		inPlugs = [ n["in"] for n in GafferScene.SceneAlgo.filteredNodes( targetPlug.node() ) ]
	elif rowPlug is not None :
		for output in rowPlug.node()["out"] :
			targetPlug = Gaffer.PlugAlgo.findDestination(
				output,
				lambda plug : plug.node()["out"] if isinstance( plug.node(), GafferScene.SceneNode ) else None
			)
			if targetPlug is not None :
				inPlugs = [ targetPlug ]
				break

	if targetPlug is None :
		return

	scenes = [ s[0] if isinstance( s, Gaffer.ArrayPlug ) else s for s in inPlugs ]

	result = IECore.PathMatcher()
	context = targetPlug.ancestor( Gaffer.ScriptNode ).context()
	with context :
		for scene in scenes :
			GafferScene.SceneAlgo.matchingPaths( selection, scene, result )

	GafferSceneUI.ContextAlgo.setSelectedPaths( context, result )

class _PathsPlugValueWidget( GafferUI.VectorDataPlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		GafferUI.VectorDataPlugValueWidget.__init__( self, plug, **kw )

		self.vectorDataWidget().dataMenuSignal().connect( Gaffer.WeakMethod( self.__dataMenu ), scoped = False )

	def __dataMenu( self, vectorDataWidget, menuDefinition ) :

		selectedIndices = vectorDataWidget.selectedIndices()

		filterData = vectorDataWidget.getData()[0]
		selection = IECore.PathMatcher( [ filterData[row] for column, row in selectedIndices ] )

		menuDefinition.append( "/selectDivider", { "divider" : True } )
		menuDefinition.append(
			"/Select Affected Objects",
			{
				"command" : functools.partial( _selectAffected, self.getPlug(), selection ),
				"active" : len( selectedIndices ) > 0,
			}
		)

##########################################################################
# Popup menu for Spreadsheet cells
##########################################################################

def __popupMenu( menuDefinition, plugValueWidget ) :

	selection = None

	plug = plugValueWidget.getPlug()
	if plug is None:
		return

	node = plug.node()

	if isinstance( node, Gaffer.Spreadsheet ) :
		rowPlug = plug.ancestor( Gaffer.Spreadsheet.RowPlug )

		with plugValueWidget.getContext() :
			if __targetFilterPlug( plug ) is not None :
				cellPlug = plug.ancestor( Gaffer.Spreadsheet.CellPlug )
				if cellPlug is None :
					return

				selection = IECore.PathMatcher( plugValueWidget.vectorDataWidget().getData()[0] )

			elif rowPlug and plug == rowPlug["name"] and node["selector"].getValue() == "${scene:path}" :
				selection = IECore.PathMatcher( [ plugValueWidget.getPlug().getValue() ] )

	if selection is None :
		return

	menuDefinition.prepend( "/selectAffectedDivider", { "divider" : True } )
	menuDefinition.prepend(
		"/Select Affected Objects",
		{
			"command" : functools.partial( _selectAffected, plug, selection )
		}
	)

GafferUI.PlugValueWidget.popupMenuSignal().connect( __popupMenu, scoped = False )

##########################################################################
# NodeGadget drop handler
##########################################################################

GafferUI.Pointer.registerPointer( "addObjects", GafferUI.Pointer( "addObjects.png", imath.V2i( 53, 14 ) ) )
GafferUI.Pointer.registerPointer( "removeObjects", GafferUI.Pointer( "removeObjects.png", imath.V2i( 53, 14 ) ) )
GafferUI.Pointer.registerPointer( "replaceObjects", GafferUI.Pointer( "replaceObjects.png", imath.V2i( 53, 14 ) ) )

__DropMode = enum.Enum( "__DropMode", [ "None_", "Add", "Remove", "Replace" ] )

__originalDragPointer = None

def __pathsPlug( node ) :

	for plug in node.children( Gaffer.Plug ) :
		if Gaffer.Metadata.value( plug, "ui:scene:acceptsPaths" ) :
			return plug

	return None

def __dropMode( nodeGadget, event ) :

	if __pathsPlug( nodeGadget.node() ) is None :
		filter = None
		if nodeGadget.node()["filter"].getInput() is not None :
			filter = nodeGadget.node()["filter"].source().node()
		if filter is None :
			return __DropMode.Replace
		elif not isinstance( filter, GafferScene.PathFilter ) :
			return __DropMode.None_

	if event.modifiers & event.Modifiers.Shift :
		return __DropMode.Add
	elif event.modifiers & event.Modifiers.Control :
		return __DropMode.Remove
	else :
		return __DropMode.Replace

def __dropPaths( paths, pathsPlug ) :

	if pathsPlug is None :
		return paths

	if not isinstance( pathsPlug.node(), GafferScene.PathFilter ) :
		return paths

	pathFilter = pathsPlug.node()
	if not pathFilter["roots"].getInput() :
		return paths

	with pathsPlug.ancestor( Gaffer.ScriptNode ).context() :
		rootPaths = IECore.PathMatcher()
		for node in GafferScene.SceneAlgo.filteredNodes( pathFilter ) :
			scene = node["in"][0] if isinstance( node["in"], Gaffer.ArrayPlug ) else node["in"]
			GafferScene.SceneAlgo.matchingPaths( pathFilter["roots"], scene, rootPaths )

	paths = IECore.PathMatcher( paths )
	relativePaths = IECore.PathMatcher()
	for rootPath in rootPaths.paths() :
		relativePaths.addPaths(
			paths.subTree( rootPath )
		)

	return relativePaths.paths()

def __dragEnter( nodeGadget, event ) :

	if not isinstance( event.data, IECore.StringVectorData ) :
		return False

	if not len( event.data ) :
		return False

	if not event.data[0].startswith( "/" ) :
		return False

	if __dropMode( nodeGadget, event ) == __DropMode.None_ :
		return False

	global __originalDragPointer
	__originalDragPointer = GafferUI.Pointer.getCurrent()

	return True

def __dragLeave( nodeGadget, event ) :

	global __originalDragPointer

	GafferUI.Pointer.setCurrent( __originalDragPointer )
	__originalDragPointer = None

	return True

def __dragMove( nodeGadget, event ) :

	global __originalDragPointer
	if __originalDragPointer is None :
		return False

	GafferUI.Pointer.setCurrent( __dropMode( nodeGadget, event ).name.lower() + "Objects" )

	return True

def __drop( nodeGadget, event ) :

	global __originalDragPointer
	if __originalDragPointer is None :
		return False

	pathsPlug = __pathsPlug( nodeGadget.node() )
	if pathsPlug is None :
		pathsPlug = __pathsPlug( nodeGadget.node()["filter"].source().node() )

	dropPaths = __dropPaths( event.data, pathsPlug )

	dropMode = __dropMode( nodeGadget, event )
	if dropMode == __DropMode.Replace :
		paths = sorted( dropPaths )
	elif dropMode == __DropMode.Add :
		paths = set( pathsPlug.getValue() )
		paths.update( dropPaths )
		paths = sorted( paths )
	else :
		paths = set( pathsPlug.getValue() )
		paths.difference_update( dropPaths )
		paths = sorted( paths )

	with Gaffer.UndoScope( nodeGadget.node().ancestor( Gaffer.ScriptNode ) ) :

		if pathsPlug is None :

			pathFilter = GafferScene.PathFilter()
			nodeGadget.node().parent().addChild( pathFilter )
			nodeGadget.node()["filter"].setInput( pathFilter["out"] )

			pathsPlug = pathFilter["paths"]

		pathsPlug.setValue( IECore.StringVectorData( paths ) )

	GafferUI.Pointer.setCurrent( __originalDragPointer )
	__originalDragPointer = None

	return True

def addObjectDropTarget( nodeGadget ) :

	nodeGadget.dragEnterSignal().connect( __dragEnter, scoped = False )
	nodeGadget.dragLeaveSignal().connect( __dragLeave, scoped = False )
	nodeGadget.dragMoveSignal().connect( __dragMove, scoped = False )
	nodeGadget.dropSignal().connect( __drop, scoped = False )

def __nodeGadget( pathFilter ) :

	nodeGadget = GafferUI.StandardNodeGadget( pathFilter )
	addObjectDropTarget( nodeGadget )

	return nodeGadget

GafferUI.NodeGadget.registerNodeGadget( GafferScene.PathFilter, __nodeGadget )
