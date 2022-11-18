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

		"attributes" : [

			"compoundDataPlugValueWidget:editable", True,

		],

		"attributes.*" : [

			"nameValuePlugPlugValueWidget:ignoreNamePlug", False,

		],

		"attributes.*.name" : [

			"ui:scene:acceptsAttributeName", True,

		],

		"extraAttributes" : [

			"plugValueWidget:type", None,

		],

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

	selectedPaths = GafferSceneUI.ContextAlgo.getSelectedPaths( plugValueWidget.getContext() ).paths()
	if not selectedPaths :
		return

	node = plug.node()
	if isinstance( node, GafferScene.Filter ) :
		nodes = [ o.node() for o in node["out"].outputs() ]
	else :
		nodes = [ node ]

	attributeNames = set()
	with plugValueWidget.getContext() :

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

GafferUI.PlugValueWidget.popupMenuSignal().connect( __attributePopupMenu, scoped = False )
