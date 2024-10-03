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

Gaffer.Metadata.registerNode(

	Gaffer.Loop,

	"description",
	"""
	Applies a node network to an input iteratively.

	> Caution : This should _not_ be your first choice of tool.
	> For many use cases the Instancer, CollectScenes and CollectImages
	> nodes are more suitable and offer _significantly_ better performance.
	""",

	# Add + buttons for creating new plugs in the GraphEditor
	"noduleLayout:customGadget:addButtonTop:gadgetType", "GafferUI.LoopUI.PlugAdder",
	"noduleLayout:customGadget:addButtonTop:section", "top",
	"noduleLayout:customGadget:addButtonBottom:gadgetType", "GafferUI.LoopUI.PlugAdder",
	"noduleLayout:customGadget:addButtonBottom:section", "bottom",

	plugs = {

		"in" : [

			"description",
			"The initial starting point for the loop."

		],

		"out" : [

			"description",
			"The final result of the loop.",

		],

		"previous" : [

			"description",
			"""
			The result from the previous iteration of the loop, or
			the primary input if no iterations have been performed yet.
			The content of the loop is defined by feeding this previous
			result through the processing nodes of choice and back
			around into the next plug.
			""",

		],

		"next" : [

			"description",
			"""
			The input to be used as the start of the next iteration of
			the loop.
			""",

		],

		"iterations" : [

			"description",
			"""
			The number of times the loop is applied to form the output.
			""",

			"nodule:type", "",

		],

		"indexVariable" : [

			"description",
			"""
			The name of a Context Variable used to specify the index
			of the current iteration. This can be referenced from
			expressions within the loop network to modify the operations
			performed during each iteration of the loop.
			""",

			"nodule:type", "",

		],

	}

)

def __createLoop( node ) :

	edges = [ "top", "right", "bottom", "left" ]

	def opposite( edge ) :
		return edges[ ( edges.index( edge ) + 2 ) % 4 ]

	def rotate( edge ) :
		return edges[ ( edges.index( edge ) + 1 ) % 4 ]

	with Gaffer.UndoScope( node.scriptNode() ) :

		plug = node["previous"]
		edge = Gaffer.Metadata.value( plug, "noduleLayout:section" ) or "bottom"

		for i in range( 0, 4 ) :

			dot = Gaffer.Dot()
			dot.setup( plug )
			dot["in"].setInput( plug )
			node.parent().addChild( dot )

			edge = opposite( edge )
			Gaffer.Metadata.registerValue( dot["in"], "noduleLayout:section", edge )

			edge = rotate( edge )
			Gaffer.Metadata.registerValue( dot["out"], "noduleLayout:section", edge )

			plug = dot["out"]

		node["next"].setInput( plug )

def __graphEditorPlugContextMenu( graphEditor, plug, menuDefinition ) :

	node = plug.node()
	if not isinstance( node, Gaffer.Loop ) :
		return

	if plug not in { node["previous"], node["next"] } :
		return

	menuDefinition.append(
		"/Connect to {0}".format( "Previous" if plug == node["next"] else "Next" ),
		{
			"command" : functools.partial( __createLoop, node = node ),
			"active" : (
				node["next"].getInput() is None
				and len( node["previous"].outputs() ) == 0
				and Gaffer.MetadataAlgo.readOnly( node["next"] ) == False
				and Gaffer.MetadataAlgo.readOnly( node["previous"] ) == False
			)
		}
	)

GafferUI.GraphEditor.plugContextMenuSignal().connect( __graphEditorPlugContextMenu )
