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

import math
import functools

import Gaffer
import GafferUI
import GafferScene
import GafferSceneUI

##########################################################################
# Metadata
##########################################################################

Gaffer.Metadata.registerNode(

	GafferScene.Camera,

	"description",
	"""
	Produces scenes containing a camera. To choose which camera is
	used for rendering, use a StandardOptions node.
	""",

	plugs = {

		"projection" : [

			"description",
			"""
			The basic camera type.
			""",

			"preset:Perspective", "perspective",
			"preset:Orthographic", "orthographic",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		"fieldOfView" : [

			"description",
			"""
			The field of view, specified in degrees, and interpreted
			as defined in the RenderMan specification. This is only
			relevant for perspective cameras.
			""",

		],

		"clippingPlanes" : [

			"description",
			"""
			The near and far clipping planes.
			""",

		],

	}

)

##########################################################################
# NodeEditor tool menu
##########################################################################

def __copyCamera( node, camera ) :

	with Gaffer.UndoContext( node.scriptNode() ) :

		s, h, r, t = camera.getTransform().transform().extractSHRT()
		node["transform"]["translate"].setValue( t )
		node["transform"]["rotate"].setValue( r * 180.0 / math.pi )
		node["transform"]["scale"].setValue( s )

def __nodeEditorToolMenu( nodeEditor, node, menuDefinition ) :

	if not isinstance( node, GafferScene.Camera ) :
		return

	layout = nodeEditor.ancestor( GafferUI.CompoundEditor )
	if layout is None :
		return

	viewers = [ v for v in layout.editors( GafferUI.Viewer ) if isinstance( v.view(), GafferSceneUI.SceneView ) ]
	if not viewers :
		return

	for viewer in viewers :

		menuDefinition.append(

			"/Copy From Viewer" + ( "/" + viewer.getTitle() if len( viewers ) > 1 else "" ),
			{
				"command" : functools.partial( __copyCamera, node, viewer.view().viewportGadget().getCamera() ),
				"active" : not Gaffer.MetadataAlgo.readOnly( node["transform"] ),
			}

		)

__nodeEditorToolMenuConnection = GafferUI.NodeEditor.toolMenuSignal().connect( __nodeEditorToolMenu )
