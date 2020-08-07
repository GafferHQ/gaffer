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
import GafferUI

import GafferScene
import GafferSceneUI

Gaffer.Metadata.registerNode(

	GafferScene.Set,

	"description",
	"""
	Creates and edits sets of objects. Each set contains a list of paths
	to locations within the scene. After creation, sets can be used
	by the SetFilter to limit scene operations to only the members of
	a particular set.
	""",

	"layout:activator:pathsInUse", lambda node : node["paths"].getInput() is not None or len( node["paths"].getValue() ),

	plugs = {

		"mode" : [

			"description",
			"""
			Create mode creates a new set containing only the
			specified paths. If a set with the same name already
			exists, it is replaced.

			Add mode adds the specified paths to an existing set,
			keeping the paths already in the set. If the set does
			not exist yet, this is the same as create mode.

			Remove mode removes the specified paths from an
			existing set. If the set does not exist yet, nothing
			is done.
			""",

			"preset:Create", GafferScene.Set.Mode.Create,
			"preset:Add", GafferScene.Set.Mode.Add,
			"preset:Remove", GafferScene.Set.Mode.Remove,

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		"name" : [

			"description",
			"""
			The name of the set that will be created or edited.
			You can create multiple set names at once by separating them with spaces.
			""",

			"ui:scene:acceptsSetName", True,

		],

		"paths" : [

			"description",
			"""
			The paths to be added to or removed from the set.

			> Caution : This plug is deprecated and will be removed
			in a future release. No validity checks are performed on
			these paths, so it is possible to accidentally generate
			invalid sets.
			""",

			"vectorDataPlugValueWidget:dragPointer", "objects",
			"layout:visibilityActivator", "pathsInUse",

		],

		"filter" : [

			"description",
			"""
			Defines the locations to be added to or removed from the set.
			""",

		],

	}

)

##########################################################################
# Right click menu for sets
# This is driven by metadata so it can be used for plugs on other
# nodes too.
##########################################################################

def __setValue( plug, value, *unused ) :

	with Gaffer.UndoScope( plug.ancestor( Gaffer.ScriptNode ) ) :
		plug.setValue( value )

def __downstreamNodes( plug ) :

	result = set()
	outputs = plug.outputs()
	if outputs :
		for output in outputs :
			result |= __downstreamNodes( output )
	else :
		if plug.node() :
			result.add( plug.node() )

	return result

def __scenePlugs( node ) :

	result = []
	for plug in node.children( Gaffer.Plug ) :
		if plug.direction() != plug.Direction.In :
			continue
		if isinstance( plug, Gaffer.ArrayPlug ) and len( plug ) :
			plug = plug[0]
		if isinstance( plug, GafferScene.ScenePlug ) :
			result.append( plug )

	return result

def __setsPopupMenu( menuDefinition, plugValueWidget ) :

	plug = plugValueWidget.getPlug()
	if plug is None :
		return

	# Some operations require a text widget so we can manipulate insertion position, etc...
	hasTextWidget = hasattr( plugValueWidget, 'textWidget' )

	# get required data
	acceptsSetName = Gaffer.Metadata.value( plug, "ui:scene:acceptsSetName" )
	acceptsSetNames = Gaffer.Metadata.value( plug, "ui:scene:acceptsSetNames" )
	acceptsSetExpression = hasTextWidget and Gaffer.Metadata.value( plug, "ui:scene:acceptsSetExpression" )
	if not acceptsSetName and not acceptsSetNames and not acceptsSetExpression :
		return

	with plugValueWidget.getContext() :
		if acceptsSetNames :
			currentNames = set( plug.getValue().split() )
		elif acceptsSetName :
			currentNames = set( [ plug.getValue() ] )
		else :
			currentExpression = plug.getValue()

	if acceptsSetExpression :
		textSelection = plugValueWidget.textWidget().getSelection()
		cursorPosition = plugValueWidget.textWidget().getCursorPosition()

		insertAt = textSelection
		if insertAt == (0, 0) :  # if there's no selection to be replaced, use position of cursor
			insertAt = (cursorPosition, cursorPosition)

	node = plug.node()
	if isinstance( node, GafferScene.Filter ) :
		nodes = __downstreamNodes( node["out"] )
	else :
		nodes = { node }

	setNames = set()
	with plugValueWidget.getContext() :
		for node in nodes :
			for scenePlug in __scenePlugs( node ) :
				setNames.update( [ str( n ) for n in scenePlug["setNames"].getValue() if not str( n ).startswith( "__" ) ] )

	if not setNames :
		return

	# build the menus
	menuDefinition.prepend( "/SetsDivider", { "divider" : True } )

	if acceptsSetExpression:
		for name, operator in zip( ("Union", "Intersection", "Difference"), ("|", "&", "-") ) :
			newValue = ''.join( [ currentExpression[:insertAt[0]], operator, currentExpression[insertAt[1]:] ] )
			menuDefinition.prepend( "/Operators/%s" % name, { "command" : functools.partial( __setValue, plug, newValue ) } )

	for setName in reversed( sorted( list( setNames ) ) ) :

		if acceptsSetExpression :
			newValue = ''.join( [ currentExpression[:insertAt[0]], setName, currentExpression[insertAt[1]:]] )
			parameters = { "command" : functools.partial( __setValue, plug, newValue ) }

		else :
			newNames = set( currentNames ) if acceptsSetNames else set()

			if setName not in currentNames :
				newNames.add( setName )
			else :
				newNames.discard( setName )

			parameters = {
				"command" : functools.partial( __setValue, plug, " ".join( sorted( newNames ) ) ),
				"checkBox" : setName in currentNames,
				"active" : plug.settable() and not plugValueWidget.getReadOnly() and not Gaffer.MetadataAlgo.readOnly( plug ),
			}

		# Group sets based on any underscores or colons in their names
		# eg: RND:prop_table -> RND > prop > table
		nameParts = setName.replace( ":", "_" ).split( "_" )
		path = "/".join( nameParts )

		menuDefinition.prepend( "/Sets/%s" % path, parameters )

GafferUI.PlugValueWidget.popupMenuSignal().connect( __setsPopupMenu, scoped = False )

##########################################################################
# Gadgets
##########################################################################

def __nodeGadget( node ) :

	nodeGadget = GafferUI.StandardNodeGadget( node )
	GafferSceneUI.PathFilterUI.addObjectDropTarget( nodeGadget )

	return nodeGadget

GafferUI.NodeGadget.registerNodeGadget( GafferScene.Set, __nodeGadget )
