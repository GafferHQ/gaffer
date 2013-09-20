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

import IECore

import Gaffer
import GafferUI

## A command suitable for use with NodeMenu.definition().append(), to add a menu
# item for the creation of a backdrop for the current selection. We don't
# actually append it automatically, but instead let the startup files
# for particular applications append it if it suits their purposes.
def nodeMenuCreateCommand( menu ) :

	nodeGraph = menu.ancestor( GafferUI.NodeGraph )
	assert( nodeGraph is not None )
	
	script = nodeGraph.scriptNode()
	
	with Gaffer.UndoContext( script ) :
	
		backdrop = Gaffer.Backdrop()
		nodeGraph.graphGadget().getRoot().addChild( backdrop )
	
		if script.selection() :
			nodeGadget = nodeGraph.graphGadget().nodeGadget( backdrop )
			nodeGadget.frame( [ x for x in script.selection() ] )
	
	return backdrop

##########################################################################
# Metadata
##########################################################################

GafferUI.Metadata.registerNodeDescription(

Gaffer.Backdrop,

"""A utility node which allows the positioning of other nodes on a coloured backdrop with optional text. Selecting a backdrop in the ui selects all the nodes positioned on it, and moving it moves them with it.""",

"title",
"The title for the backdrop - this will be displayed at the top of the backdrop.",

"scale",
"Controls the size of the backdrop text.",

"description",
"Text describing the contents of the backdrop - this will be displayed below the title.",

)

##########################################################################
# PlugValueWidget registrations
##########################################################################

GafferUI.PlugValueWidget.registerCreator(
	Gaffer.Backdrop.staticTypeId(), "title", GafferUI.StringPlugValueWidget, continuousUpdate=True
)

GafferUI.PlugValueWidget.registerCreator(
	Gaffer.Backdrop.staticTypeId(), "description", GafferUI.MultiLineStringPlugValueWidget, continuousUpdate=True
)
