##########################################################################
#
#  Copyright (c) 2017, John Haddon. All rights reserved.
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
import GafferSceneUI

Gaffer.Metadata.registerNode(

	GafferSceneUI.RotateTool,

	"description",
	"""
	Tool for editing object rotation.
	""",

	"nodeToolbar:bottom:type", "GafferUI.StandardNodeToolbar.bottom",

	"viewer:shortCut", "E",
	"order", 2,

	"ui:transformTool:toolTip", "Hold 'V' and click to aim at target",

	plugs = {

		"orientation" : [

			"description",
			"""
			The space used to define the orientation of the XYZ
			rotation handles. Note that this is independent
			of the space setting on a Transform node - each
			setting can be mixed and matched freely.
			""",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

			"toolbarLayout:section", "Bottom",
			"toolbarLayout:width", 100,

			"preset:Local", GafferSceneUI.TransformTool.Orientation.Local,
			"preset:Parent", GafferSceneUI.TransformTool.Orientation.Parent,
			"preset:World", GafferSceneUI.TransformTool.Orientation.World,

		],

	}
)
