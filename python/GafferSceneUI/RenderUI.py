##########################################################################
#
#  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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
import GafferScene

from GafferUI.PlugValueWidget import sole

def rendererPresetNames( plug ) :

	blacklist = { "Capturing" }
	return IECore.StringVectorData(
		sorted(
			t for t in GafferScene.Private.IECoreScenePreview.Renderer.types()
			if t not in blacklist
		)
	)

Gaffer.Metadata.registerNode(

	GafferScene.Render,

	"description",
	"""
	Performs offline batch rendering using any of the
	available renderer backends, or optionally writes
	scene descriptions to disk for later rendering via
	a SystemCommand node.
	""",

	"layout:activator:modeIsSceneDescription", lambda node : node["mode"].getValue() == node.Mode.SceneDescriptionMode,

	plugs = {

		"in" : [

			"description",
			"""
			The scene to be rendered.
			""",

			"nodule:type", "GafferUI::StandardNodule",

		],

		"renderer" : [

			"description",
			"""
			The renderer to use. Default mode uses the `render:defaultRenderer` option from
			the input scene globals to choose the renderer. This can be authored using
			the StandardOptions node.
			""",

			"plugValueWidget:type", "GafferSceneUI.RenderUI.RendererPlugValueWidget",

			"preset:Default", "",
			"presetNames", rendererPresetNames,
			"presetValues", rendererPresetNames,

		],

		"mode" : [

			"description",
			"""
			The type of render to perform.
			""",

			"preset:Render", GafferScene.Render.Mode.RenderMode,
			"preset:Scene Description", GafferScene.Render.Mode.SceneDescriptionMode,

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		"fileName" : [

			"description",
			"""
			The name of the file to be generated when in scene description mode.
			""",

			"plugValueWidget:type", "GafferUI.FileSystemPathPlugValueWidget",
			"path:leaf", True,

			"layout:activator", "modeIsSceneDescription",

		],

		"out" : [

			"description",
			"""
			A direct pass-through of the input scene.
			""",

		],

	}
)

# Augments PresetsPlugValueWidget label with the renderer name
# when preset is "Default". Since this involves computing the
# scene globals, we do the work in the background via an auxiliary
# plug passed to `_valuesForUpdate()`.
class RendererPlugValueWidget( GafferUI.PresetsPlugValueWidget ) :

	def __init__( self, plugs, **kw ) :

		GafferUI.PresetsPlugValueWidget.__init__( self, plugs, **kw )

	@staticmethod
	def _valuesForUpdate( plugs, auxiliaryPlugs ) :

		presets = GafferUI.PresetsPlugValueWidget._valuesForUpdate( plugs, [ [] for p in plugs ] )

		result = []
		for preset, globalsPlugs in zip( presets, auxiliaryPlugs ) :

			defaultRenderer = ""
			if len( globalsPlugs ) and preset == "Default" :
				with IECore.IgnoredExceptions( Gaffer.ProcessException ) :
					defaultRenderer = globalsPlugs[0].getValue().get( "option:render:defaultRenderer" )
					defaultRenderer = defaultRenderer.value if defaultRenderer is not None else ""

			result.append( {
				"preset" : preset,
				"defaultRenderer" : defaultRenderer
			} )

		return result

	def _updateFromValues( self, values, exception ) :

		GafferUI.PresetsPlugValueWidget._updateFromValues( self, [ v["preset"] for v in values ], exception )

		if self.menuButton().getText() == "Default" :
			defaultRenderer = sole( v["defaultRenderer"] for v in values )
			self.menuButton().setText(
				"Default ({})".format(
					defaultRenderer if defaultRenderer else
					( "None" if defaultRenderer == "" else "---" )
				)
			)

	def _auxiliaryPlugs( self, plug ) :

		node = plug.node()
		if isinstance( node, ( GafferScene.Render, GafferScene.InteractiveRender ) ) :
			return [ node["in"]["globals"] ]
