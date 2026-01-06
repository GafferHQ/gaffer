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

	GafferScene.CustomAttributes,

	"description",
	"""
	Applies arbitrary user-defined attributes to locations in the scene. Note
	that for most common cases the StandardAttributes or renderer-specific
	attributes nodes should be preferred, as they provide predefined sets of
	attributes with customised user interfaces. The CustomAttributes node is
	of most use when needing to set an attribute not supported by the
	specialised nodes.
	""",

	plugs = {

		"attributes" : {

			"plugCreationWidget:excludedTypes" : "Gaffer.ObjectPlug",
			"layout:customWidget:addButton:visibilityActivator" : True,
			"ui:scene:acceptsAttributes" : True,

		},

		"attributes.*" : {

			"nameValuePlugPlugValueWidget:ignoreNamePlug" : False,
			"layout:section" : "",

		},

		"attributes.*.name" : {

			"ui:scene:acceptsAttributeName" : True,

		},

		"extraAttributes" : {

			"plugValueWidget:type" : None,

		},

	}

)

##########################################################################
# Right click menu for adding attribute names to plugs
# This is driven by metadata so it can be used for plugs on other
# nodes too.
##########################################################################

def __setValue( plug, value, *unused ) :

	with Gaffer.UndoScope( plug.ancestor( Gaffer.ScriptNode ) ) :
		plug.setValue( value )

def __attributePopupMenu( menuDefinition, plugValueWidget ) :

	plug = plugValueWidget.getPlug()
	if plug is None :
		return

	acceptsAttributeName = Gaffer.Metadata.value( plug, "ui:scene:acceptsAttributeName" )
	acceptsAttributeNames = Gaffer.Metadata.value( plug, "ui:scene:acceptsAttributeNames" )
	if not acceptsAttributeName and not acceptsAttributeNames :
		return

	selectedPaths = GafferSceneUI.ScriptNodeAlgo.getSelectedPaths( plugValueWidget.scriptNode() ).paths()
	if not selectedPaths :
		return

	node = plug.node()
	if isinstance( node, GafferScene.Filter ) :
		nodes = [ o.node() for o in node["out"].outputs() ]
	else :
		nodes = [ node ]

	attributeNames = set()
	if acceptsAttributeNames :
		currentNames = set( plug.getValue().split() )
	else :
		currentNames = set( [ plug.getValue() ] )

	for node in nodes :
		for path in selectedPaths :
			attributes = node["in"].attributes( path, _copy=False )
			attributeNames.update( attributes.keys() )

	if not attributeNames :
		return

	menuDefinition.prepend( "/AttributesDivider", { "divider" : True } )

	for attributeName in reversed( sorted( list( attributeNames ) ) ) :

		newNames = set( currentNames ) if acceptsAttributeNames else set()

		if attributeName not in currentNames :
			newNames.add( attributeName )
		else :
			newNames.discard( attributeName )

		menuDefinition.prepend(
			"/Attributes/%s" % attributeName,
			{
				"command" : functools.partial( __setValue, plug, " ".join( sorted( newNames ) ) ),
				"checkBox" : attributeName in currentNames,
				"active" : plug.settable() and not Gaffer.MetadataAlgo.readOnly( plug ),
			}
		)

GafferUI.PlugValueWidget.popupMenuSignal().connect( __attributePopupMenu )

##########################################################################
# PlugCreationWidget menu extensions
##########################################################################

def __addFromAffectedMenuDefinition( menu ) :

	plugCreationWidget = menu.ancestor( GafferUI.PlugCreationWidget )
	node = plugCreationWidget.plugParent().node()
	assert( isinstance( node, GafferScene.FilteredSceneProcessor ) )

	pathMatcher = IECore.PathMatcher()
	GafferScene.SceneAlgo.matchingPaths( node["filter"], node["in"], pathMatcher )

	return __addFromPathsMenuDefinition( menu, pathMatcher.paths() )

def __addFromSelectedMenuDefinition( menu ) :

	plugCreationWidget = menu.ancestor( GafferUI.PlugCreationWidget )

	return __addFromPathsMenuDefinition(
		menu,
		GafferSceneUI.ScriptNodeAlgo.getSelectedPaths(
			plugCreationWidget.plugParent().ancestor( Gaffer.ScriptNode )
		).paths()
	)

def __addFromPathsMenuDefinition( menu, paths ) :

	plugCreationWidget = menu.ancestor( GafferUI.PlugCreationWidget )
	node = plugCreationWidget.plugParent().node()

	attributes = {}
	for path in paths :
		attr = node["in"].fullAttributes( path, withGlobalAttributes = True )
		attributes.update( attr )
	existingNames = { plug["name"].getValue() for plug in plugCreationWidget.plugParent() }

	attributes = dict( sorted( attributes.items() ) )

	result = IECore.MenuDefinition()
	for key, value in attributes.items() :
		result.append(
			"/" + key,
			{
				"command" : functools.partial( __createPlug, name = key, value = value ),
				"active" : key not in existingNames
			}
		)

	if not len( result.items() ) :
		result.append(
			"/No Attributes Found", { "active" : False }
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

	if not Gaffer.Metadata.value( widget.plugParent(), "ui:scene:acceptsAttributes" ) :
		return

	menuDefinition.prepend( "/FromPathsDivider", { "divider" : True } )

	menuDefinition.prepend(
		"/From Selection",
		{
			"subMenu" : __addFromSelectedMenuDefinition
		}
	)

	menuDefinition.prepend(
		"/From Affected",
		{
			"subMenu" : __addFromAffectedMenuDefinition
		}
	)

GafferUI.PlugCreationWidget.plugCreationMenuSignal().connect( __plugCreationMenu )

##########################################################################
# PlugCreationWidget drag & drop extension
##########################################################################

def __filteredAttributes( widget, dragDropEvent ) :

	attributes = GafferSceneUI.SceneInspector.draggedAttributes( dragDropEvent )
	if not attributes :
		return None

	existingNames = { plug["name"].getValue() for plug in widget.plugParent() }
	return {
		k : v for k, v in attributes.items()
		if k not in existingNames
	}

def __attributesDropHandler( widget, dragDropEvent ) :

	attributes = __filteredAttributes( widget, dragDropEvent )
	if not attributes :
		GafferUI.PopupWindow.showWarning( "Attributes added already", parent = widget )

	with Gaffer.UndoScope( widget.plugParent().ancestor( Gaffer.ScriptNode ) ) :
		for name, value in attributes.items() :
			plug = Gaffer.PlugAlgo.createPlugFromData( "value", Gaffer.Plug.Direction.In, Gaffer.Plug.Flags.Default, value )
			widget.createPlug( plug, name = name )

def __plugCreationDragEnter( widget, dragDropEvent ) :

	if not Gaffer.Metadata.value( widget.plugParent(), "ui:scene:acceptsAttributes" ) :
		return

	if __filteredAttributes( widget, dragDropEvent ) is not None :
		return __attributesDropHandler

	return None

GafferUI.PlugCreationWidget.plugCreationDragEnterSignal().connect( __plugCreationDragEnter )
