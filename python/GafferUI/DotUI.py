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

import contextlib
import functools
import imath

import IECore

import Gaffer
import GafferUI

##########################################################################
# Public methods
##########################################################################

## May be called to connect the DotUI functionality to an application
# instance. This isn't done automatically because some applications
# may have graphs for which it doesn't make sense to use Dots. Typically
# this function would be called from an application startup file.
def connect( applicationRoot ) :

	applicationRoot.__dotUIConnected = True

##########################################################################
# Metadata
##########################################################################

Gaffer.Metadata.registerNode(

	Gaffer.Dot,

	"description",
	"""
	A utility node which can be used for organising large graphs.
	""",

	"nodeGadget:minWidth", 0.0,
	"nodeGadget:padding", 0.5,
	"nodeGadget:shape", "oval",

	"layout:activator:labelTypeIsCustom", lambda node : node["labelType"].getValue() == node.LabelType.Custom,

	plugs = {

		"in" : [

			"plugValueWidget:type", ""

		],

		"out" : [

			"plugValueWidget:type", ""

		],

		"labelType" : [

			"description",
			"""
			The method used to apply an optional label
			to the dot. Using a node name is recommended,
			because it encourages the use of descriptive node
			names, and updates automatically when nodes are
			renamed or upstream connections change. The custom
			label does however provide more flexibility, since
			node names are restricted in the characters they
			can use.
			""",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
			"nodule:type", "",

			"preset:None", Gaffer.Dot.LabelType.None_,
			"preset:Node Name", Gaffer.Dot.LabelType.NodeName,
			"preset:Upstream Node Name", Gaffer.Dot.LabelType.UpstreamNodeName,
			"preset:Custom", Gaffer.Dot.LabelType.Custom,

		],

		"label" : [

			"description",
			"""
			The label displayed when the type is set to custom.
			""",

			"nodule:type", "",
			"layout:activator", "labelTypeIsCustom",

		],

	},

)

##########################################################################
# GraphEditor menus
##########################################################################

def __insertDot( menu, destinationPlug ) :

	graphEditor = menu.ancestor( GafferUI.GraphEditor )
	gadgetWidget  = graphEditor.graphGadgetWidget()
	graphGadget = graphEditor.graphGadget()

	with Gaffer.UndoScope( destinationPlug.ancestor( Gaffer.ScriptNode ) ) :

		node = Gaffer.Dot()
		graphGadget.getRoot().addChild( node )

		node.setup( destinationPlug )
		node["in"].setInput( destinationPlug.getInput() )
		destinationPlug.setInput( node["out"] )

		menuPosition = menu.popupPosition( relativeTo = gadgetWidget )
		position = gadgetWidget.getViewportGadget().rasterToGadgetSpace(
			imath.V2f( menuPosition.x, menuPosition.y ),
			gadget = graphGadget
		).p0

		graphGadget.setNodePosition( node, imath.V2f( position.x, position.y ) )

def __connectionContextMenu( graphEditor, destinationPlug, menuDefinition ) :

	applicationRoot = graphEditor.scriptNode().ancestor( Gaffer.ApplicationRoot )
	connected = False
	with contextlib.suppress( AttributeError ) :
		connected = applicationRoot.__dotUIConnected

	if not connected :
		return

	if len( menuDefinition.items() ) :
		menuDefinition.append( "/DotDivider", { "divider" : True } )

	menuDefinition.append(
		"/Insert Dot",
		{
			"command" : functools.partial( __insertDot, destinationPlug = destinationPlug ),
			"active" : not Gaffer.MetadataAlgo.readOnly( destinationPlug ),
		}
	)

GafferUI.GraphEditor.connectionContextMenuSignal().connect( __connectionContextMenu, scoped = False )

def __setPlugMetadata( plug, key, value ) :

	with Gaffer.UndoScope( plug.ancestor( Gaffer.ScriptNode ) ) :
		Gaffer.Metadata.registerValue( plug, key, value )

def __graphEditorPlugContextMenu( graphEditor, plug, menuDefinition ) :

	if isinstance( plug.node(), Gaffer.Dot ) :

		## \todo This duplicates functionality from BoxUI. Is there some way
		# we could share it?
		currentEdge = Gaffer.Metadata.value( plug, "noduleLayout:section" )
		if not currentEdge :
			currentEdge = "top" if plug.direction() == plug.Direction.In else "bottom"

		readOnly = Gaffer.MetadataAlgo.readOnly( plug )
		for edge in ( "top", "bottom", "left", "right" ) :
			menuDefinition.append(
				"/Move To/" + edge.capitalize(),
				{
					"command" : functools.partial( __setPlugMetadata, plug, "noduleLayout:section", edge ),
					"active" : edge != currentEdge and not readOnly,
				}
			)

GafferUI.GraphEditor.plugContextMenuSignal().connect( __graphEditorPlugContextMenu, scoped = False )
