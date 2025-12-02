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

import functools

import IECore

import Gaffer
import GafferUI
import GafferScene
import GafferSceneUI

Gaffer.Metadata.registerNode(

	GafferScene.CustomOptions,

	"description",

	"""
	Applies arbitrary user-defined options to the root of the scene. Note
	that for most common cases the StandardOptions or renderer-specific options
	nodes should be preferred, as they provide predefined sets of options with customised
	user interfaces. The CustomOptions node is of most use when needing to set am
	option not supported by the specialised nodes.
	""",

	plugs = {

		"options" : {

			"description" :
			"""
			The options to be applied - arbitrary numbers of user defined options may be added
			as children of this plug via the user interface, or using the CompoundDataPlug API via
			python.
			""",

			"plugCreationWidget:excludedTypes" : "Gaffer.ObjectPlug",
			"compoundDataPlugValueWidget:editable" : True,
			"ui:scene:acceptsOptions" : True,

		},

		"options.*" : {

			"nameValuePlugPlugValueWidget:ignoreNamePlug" : False,
			"layout:section" : "",

		},

		"prefix" : {

			"description" :
			"""
			A prefix applied to the name of each option. For example, a prefix
			of "myCategory:" and a name of "test" will create an option named
			"myCategory:test".
			""",

			"layout:section" : "Advanced",

		},

		"extraOptions" : {

			"plugValueWidget:type" : None,

		},

	}

)

##########################################################################
# PlugCreationWidget menu extension
##########################################################################

def __addFromGlobalsMenuDefinition( menu ) :

	plugCreationWidget = menu.ancestor( GafferUI.PlugCreationWidget )
	node = plugCreationWidget.plugParent().node()
	assert( isinstance( node, GafferScene.SceneNode ) )

	result = IECore.MenuDefinition()

	options = node["in"]["globals"].getValue()
	existingNames = { plug["name"].getValue() for plug in plugCreationWidget.plugParent() }

	prefix = "option:"

	for name, value in [ ( k[len(prefix):], v ) for k, v in options.items() if k.startswith( prefix ) ] :
		result.append(
			"/{}".format( name ),
			{
				"command" : functools.partial( __createPlug, name = name, value = value ),
				"active" : name not in existingNames
			}
		)

	if not len( result.items() ) :
		result.append(
			"/No Options Found", { "active" : False }
		)
		return result

	return result

def __createPlug( menu, name, value ) :

	plugCreationWidget = menu.ancestor( GafferUI.PlugCreationWidget )
	plugCreationWidget.createPlug(
		Gaffer.PlugAlgo.createPlugFromData( "plug0", Gaffer.Plug.Direction.In, Gaffer.Plug.Flags.Default, value ),
		name = name
	)

def __plugCreationMenu( menuDefinition, widget ) :

	if not Gaffer.Metadata.value( widget.plugParent(), "ui:scene:acceptsOptions" ) :
		return

	menuDefinition.prepend( "/FromSceneDivider", { "divider" : True } )

	menuDefinition.prepend(
		"/From Scene",
		{
			"subMenu" : __addFromGlobalsMenuDefinition
		}
	)

GafferUI.PlugCreationWidget.plugCreationMenuSignal().connect( __plugCreationMenu )

##########################################################################
# PlugCreationWidget drag & drop extension
##########################################################################

def __filteredOptions( widget, dragDropEvent ) :

	options = GafferSceneUI.SceneInspector.draggedOptions( dragDropEvent )
	if not options :
		return None

	existingNames = { plug["name"].getValue() for plug in widget.plugParent() }
	return {
		k : v for k, v in options.items()
		if k not in existingNames
	}

def __optionsDropHandler( widget, dragDropEvent ) :

	options = __filteredOptions( widget, dragDropEvent )
	if not options :
		GafferUI.PopupWindow.showWarning( "Options added already", parent = widget )

	with Gaffer.UndoScope( widget.plugParent().ancestor( Gaffer.ScriptNode ) ) :
		for name, value in options.items() :
			plug = Gaffer.PlugAlgo.createPlugFromData( "value", Gaffer.Plug.Direction.In, Gaffer.Plug.Flags.Default, value )
			widget.createPlug( plug, name = name )

def __plugCreationDragEnter( widget, dragDropEvent ) :

	if not Gaffer.Metadata.value( widget.plugParent(), "ui:scene:acceptsOptions" ) :
		return

	if __filteredOptions( widget, dragDropEvent ) is not None :
		return __optionsDropHandler

	return None

GafferUI.PlugCreationWidget.plugCreationDragEnterSignal().connect( __plugCreationDragEnter )
