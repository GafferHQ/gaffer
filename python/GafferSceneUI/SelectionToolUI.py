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

import imath

import IECore

import Gaffer
import GafferUI
import GafferSceneUI

Gaffer.Metadata.registerNode(

	GafferSceneUI.SelectionTool,

	"description",
	"""
	Tool for selecting objects.

	- Click or drag to set selection
	- Shift-click or shift-drag to add to selection
	- Drag and drop selected objects
		- Drag to Python Editor to get their names
		- Drag to PathFilter or Set node to add/remove their paths
	""",

	"nodeToolbar:bottom:type", "GafferUI.StandardNodeToolbar.bottom",

	"viewer:shortCut", "Q",
	"order", 0,

	# So we don't obscure the corner gnomon
	"toolbarLayout:customWidget:LeftSpacer:widgetType", "GafferSceneUI.SelectionToolUI._LeftSpacer",
	"toolbarLayout:customWidget:LeftSpacer:section", "Bottom",
	"toolbarLayout:customWidget:LeftSpacer:index", 0,

	# So our layout doesn't jump around too much when our selection widget changes size
	"toolbarLayout:customWidget:RightSpacer:widgetType", "GafferSceneUI.SelectionToolUI._RightSpacer",
	"toolbarLayout:customWidget:RightSpacer:section", "Bottom",
	"toolbarLayout:customWidget:RightSpacer:index", -1,

	plugs = {

		"selectMode" : [

			"description",
			"""
			Determines the scene location that is ultimately selected or deselected,
			which may differ from what is originally selected.
			""",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

			"label", "Select",

			"toolbarLayout:section", "Bottom",
			"toolbarLayout:width", 150,

		],
	},

)

class _LeftSpacer( GafferUI.Spacer ) :

	def __init__( self, imageView, **kw ) :

		GafferUI.Spacer.__init__( self, size = imath.V2i( 40, 1 ), maximumSize = imath.V2i( 40, 1 ) )

class _RightSpacer( GafferUI.Spacer ) :

	def __init__( self, imageView, **kw ) :

		GafferUI.Spacer.__init__( self, size = imath.V2i( 0, 0 ) )
