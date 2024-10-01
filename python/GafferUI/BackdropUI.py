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

import imath

import IECore

import Gaffer
import GafferUI

## A command suitable for use with NodeMenu.definition().append(), to add a menu
# item for the creation of a backdrop for the current selection. We don't
# actually append it automatically, but instead let the startup files
# for particular applications append it if it suits their purposes.
def nodeMenuCreateCommand( menu ) :

	graphEditor = menu.ancestor( GafferUI.GraphEditor )
	assert( graphEditor is not None )
	gadgetWidget = graphEditor.graphGadgetWidget()
	graphGadget = graphEditor.graphGadget()

	script = graphEditor.scriptNode()

	with Gaffer.UndoScope( script ) :

		backdrop = Gaffer.Backdrop()
		Gaffer.NodeAlgo.applyUserDefaults( backdrop )

		graphGadget.getRoot().addChild( backdrop )

		if script.selection() :
			nodeGadget = graphGadget.nodeGadget( backdrop )
			nodeGadget.frame( [ x for x in script.selection() ] )
		else :
			menuPosition = menu.popupPosition( relativeTo = gadgetWidget )
			nodePosition = gadgetWidget.getViewportGadget().rasterToGadgetSpace(
				imath.V2f( menuPosition.x, menuPosition.y ),
				gadget = graphGadget
			).p0
			graphGadget.setNodePosition( backdrop, imath.V2f( nodePosition.x, nodePosition.y ) )

	return backdrop

##########################################################################
# Metadata
##########################################################################

Gaffer.Metadata.registerNode(

	Gaffer.Backdrop,

	"description",
	"""
	A utility node which allows the positioning of other nodes on a
	coloured backdrop with optional text. Selecting a backdrop in the
	ui selects all the nodes positioned on it, and moving it moves
	them with it.
	""",

	plugs = {

		"title" : [

			"description",
			"""
			The title for the backdrop - this will be displayed at
			the top of the backdrop.
			""",

			"stringPlugValueWidget:continuousUpdate", True,

		],

		"scale" : [

			"description",
			"""
			Controls the size of the backdrop text.
			""",

		],

		"description" : [

			"description",
			"""
			Text describing the contents of the backdrop -
			this will be displayed below the title.
			""",

			"plugValueWidget:type", "GafferUI.MultiLineStringPlugValueWidget",
			"multiLineStringPlugValueWidget:continuousUpdate", True,

		],

		"depth" : [

			"description",
			"""
			Determines the drawing order of overlapping backdrops.

			> Note : Larger backdrops are _automatically_ drawn behind smaller ones,
			> so it is only necessary to manually assign a depth in rare cases where
			> this is not desirable.
			""",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
			"preset:Back", -1,
			"preset:Middle", 0,
			"preset:Front", 1,


		],

	}

)
