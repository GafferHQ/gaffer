##########################################################################
#
#  Copyright (c) 2019, Cinesite VFX Ltd. All rights reserved.
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

import imath

import IECore

import Gaffer
import GafferUI

Gaffer.Metadata.registerNode(

	Gaffer.EditScope,

	"description",
	"""
	A container that interactive tools may make nodes in
	as necessary.
	""",

	"icon", "editScopeNode.png",

	"graphEditor:childrenViewable", True,

	# Add + buttons for setting up via the GraphEditor

	"noduleLayout:customGadget:setupButtonTop:gadgetType", "GafferUI.EditScopeUI.PlugAdder",
	"noduleLayout:customGadget:setupButtonTop:section", "top",

	"noduleLayout:customGadget:setupButtonBottom:gadgetType", "GafferUI.EditScopeUI.PlugAdder",
	"noduleLayout:customGadget:setupButtonBottom:section", "bottom",

	# Hide the Box + buttons until the node has been set up. Two sets of buttons at
	# the same time is way too confusing.

	"noduleLayout:customGadget:addButtonTop:visible", lambda node : "in" in node,
	"noduleLayout:customGadget:addButtonBottom:visible", lambda node : "in" in node,
	"noduleLayout:customGadget:addButtonLeft:visible", lambda node : "in" in node,
	"noduleLayout:customGadget:addButtonRight:visible", lambda node : "in" in node,

	plugs = {

		"in" : [

			"renameable", False,
			"deletable", False,

		],

		"out" : [

			"renameable", False,
			"deletable", False,

		],

	},

)

# Disable editing of `EditScope.BoxIn` and `EditScope.BoxOut`

Gaffer.Metadata.registerValue( Gaffer.EditScope, "BoxIn.name", "readOnly", True )
Gaffer.Metadata.registerValue( Gaffer.EditScope, "BoxOut.name", "readOnly", True )
Gaffer.Metadata.registerValue( Gaffer.BoxIn, "renameable", lambda node : not isinstance( node.parent(), Gaffer.EditScope ) or node.getName() != "BoxIn" )
Gaffer.Metadata.registerValue( Gaffer.BoxOut, "renameable", lambda node : not isinstance( node.parent(), Gaffer.EditScope ) or node.getName() != "BoxOut" )
