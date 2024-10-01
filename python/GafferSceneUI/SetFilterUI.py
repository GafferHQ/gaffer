##########################################################################
#
#  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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

import Gaffer
import GafferUI
import GafferScene
import GafferSceneUI

import IECore

##########################################################################
# Metadata
##########################################################################

Gaffer.Metadata.registerNode(

	GafferScene.SetFilter,

	"description",
	"""
	A filter which uses sets to define which locations are matched.
	""",

	plugs = {

		"setExpression" : [

			"description",
			"""
			A set expression that computes a set that defines
			the locations to be matched.

			For example, the expression `mySpheresSet | myCubesSet`
			will create a set that contains all objects in
			`mySpheresSet` and `myCubesSet`.

			Gaffer supports the union operator (`|`) as shown in the
			example and also provides intersection (`&`) and difference (`-`)
			operations for set expressions. Names of locations
			can be used to represent a set that contains only
			that one location.

			In addition, the `in` and `containing` operators can be
			used to query descendant and ancestor matches. For example,
			`materialA in assetB` will select all locations in the `materialA`
			set that are at or below locations in the `assetB` set. This
			allows leaf matches to be made against sets that only contain
			root or parent locations. `allAssets containing glass` will
			selection locations in `allAssets` that have children in the
			`glass` set.

			For more examples please consult the Scripting Reference
			section in Gaffer's documentation.

			The context menu of the set expression text field provides
			entries that help construct set expressions.
			""",

			"ui:scene:acceptsSetExpression", True,
			"plugValueWidget:type", "GafferSceneUI.SetExpressionPlugValueWidget",
			"nodule:type", "",

		],

	}

)

##########################################################################
# NodeGadget drop handler
##########################################################################

GafferUI.Pointer.registerPointer( "sets", GafferUI.Pointer( "pointerSets.png", imath.V2i( 53, 14 ) ) )
GafferUI.Pointer.registerPointer( "addSets", GafferUI.Pointer( "pointerAddSets.png", imath.V2i( 53, 14 ) ) )
GafferUI.Pointer.registerPointer( "removeSets", GafferUI.Pointer( "pointerRemoveSets.png", imath.V2i( 53, 14 ) ) )
GafferUI.Pointer.registerPointer( "replaceSets", GafferUI.Pointer( "pointerReplaceSets.png", imath.V2i( 53, 14 ) ) )

__DropMode = enum.Enum( "__DropMode", [ "None_", "Add", "Remove", "Replace" ] )

__originalDragPointer = None

def __setsPlug( node ) :

	for plug in Gaffer.Plug.InputRange( node ) :
		if Gaffer.Metadata.value( plug, "ui:scene:acceptsSetNames" ) or Gaffer.Metadata.value( plug, "ui:scene:acceptsSetExpression" ) :
			return plug

	return None

def __editable( plug ) :
	if Gaffer.MetadataAlgo.readOnly( plug ) or not plug.settable() :
		return False

	if Gaffer.Metadata.value( plug, "ui:scene:acceptsSetNames" ) or Gaffer.Metadata.value( plug, "ui:scene:acceptsSetExpression" ) :
		plugValue = plug.getValue()
		if any( i in plugValue for i in [ "(", ")", "|", "-", "&"] ) :
			return False

		plugTokens = plugValue.split( " " )
		if any( i in plugTokens for i in [ "in", "containing" ] ) :
			return False

	return True

def __dropMode( nodeGadget, event ) :

	setsPlug = __setsPlug( nodeGadget.node() )
	if setsPlug is None :
		filter = None
		if nodeGadget.node()["filter"].getInput() is not None :
			filter = nodeGadget.node()["filter"].source().node()
		if filter is None :
			return __DropMode.Replace if __editable( nodeGadget.node()["filter"] ) else __DropMode.None_
		elif not isinstance( filter, GafferScene.SetFilter ) :
			return __DropMode.None_
		setsPlug = filter["setExpression"]

	if not __editable( setsPlug ) :
		return __DropMode.None_

	if event.modifiers & event.Modifiers.Shift :
		return __DropMode.Add
	elif event.modifiers & event.Modifiers.Control :
		return __DropMode.Remove
	else :
		return __DropMode.Replace

def __dragEnter( nodeGadget, event ) :

	if not isinstance( event.data, IECore.StringVectorData ) :
		return False

	if not (
		all( i.startswith( "/" ) for i in event.data ) or
		event.sourceWidget.ancestor( GafferSceneUI.SetEditor ) is not None
	) :
		return False

	if not len ( event.data ) :
		return False

	if __dropMode( nodeGadget, event ) == __DropMode.None_ :
		return False

	global __originalDragPointer
	__originalDragPointer = GafferUI.Pointer.getCurrent()

	return True

def __dragLeave( nodeGadget, event ) :

	global __originalDragPointer

	if __originalDragPointer is None :
		return False

	GafferUI.Pointer.setCurrent( __originalDragPointer )
	__originalDragPointer = None

	return True

def __dragMove( nodeGadget, event ) :

	global __originalDragPointer
	if __originalDragPointer is None :
		return False

	GafferUI.Pointer.setCurrent( __dropMode( nodeGadget, event ).name.lower() + "Sets" )

	return True

def __drop( nodeGadget, event ) :

	global __originalDragPointer
	if __originalDragPointer is None :
		return False

	setsPlug = __setsPlug( nodeGadget.node() )
	if setsPlug is None :
		setsPlug = __setsPlug( nodeGadget.node()["filter"].source().node() )

	dropSets = event.data

	dropMode = __dropMode( nodeGadget, event )
	if dropMode == __DropMode.Replace :
		sets = sorted( dropSets )
	elif dropMode == __DropMode.Add :
		sets = set( setsPlug.getValue().split( " " ) )
		sets.update( dropSets )
		sets = sorted( sets )
	else :
		sets = set( setsPlug.getValue().split( " " ) )
		sets.difference_update( dropSets )
		sets = sorted( sets )

	with Gaffer.UndoScope( nodeGadget.node().ancestor( Gaffer.ScriptNode ) ) :

		if setsPlug is None :

			setFilter = GafferScene.SetFilter()
			nodeGadget.node().parent().addChild( setFilter )
			nodeGadget.node()["filter"].setInput( setFilter["out"] )

			setsPlug = setFilter["setExpression"]

		setsPlug.setValue( " ".join( sets ) )

	GafferUI.Pointer.setCurrent( __originalDragPointer )
	__originalDragPointer = None

	return True

def addSetDropTarget( nodeGadget ) :

	nodeGadget.dragEnterSignal().connect( __dragEnter, scoped = False )
	nodeGadget.dragLeaveSignal().connect( __dragLeave, scoped = False )
	nodeGadget.dragMoveSignal().connect( __dragMove, scoped = False )
	nodeGadget.dropSignal().connect( __drop, scoped = False )

def __nodeGadget( setFilter ) :

	nodeGadget = GafferUI.StandardNodeGadget( setFilter )
	addSetDropTarget( nodeGadget )

	return nodeGadget

GafferUI.NodeGadget.registerNodeGadget( GafferScene.SetFilter, __nodeGadget )
