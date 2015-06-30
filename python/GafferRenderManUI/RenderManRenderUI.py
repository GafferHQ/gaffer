##########################################################################
#
#  Copyright (c) 2012-2014, Image Engine Design Inc. All rights reserved.
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
import GafferRenderMan

Gaffer.Metadata.registerNode(

	GafferRenderMan.RenderManRender,

	"description",
	"""
	Performs offline batch rendering using a
	RenderMan renderer. This is done in two
	phases - first a RIB file is generated and
	then the renderer is invoked to render it in
	a separate process. Note though that the RIB
	file is lightweight, and contains a single
	procedural which will invoke Gaffer to generate
	the scene on demand at runtime. The RIB therefore
	requires very little disk space.
	""",

	plugs = {

		"mode" : [


			"description",
			"""
			When in "Render" mode, a RIB file is generated
			and then renderered by running the renderer on
			it. In "Generate RIB only" mode, only the RIB
			is generated, and a subsequent node could be used
			to post-process or launch the render in another
			way - a SystemCommand node may be useful for this.
			""",

			"preset:Render", "render",
			"preset:Generate RIB only", "generate",

			"nodule:type", "",
			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",


		],

		"ribFileName" : [

			"description",
			"""
			The name of the RIB file to be generated.
			""",

			"nodule:type", "",
			"plugValueWidget:type", "GafferUI.FileSystemPathPlugValueWidget",
			"pathPlugValueWidget:leaf", True,
			"pathPlugValueWidget:bookmarks", "rib",
			"fileSystemPathPlugValueWidget:extensions", IECore.StringVectorData( [ "rib" ] ),

		],

		"command" : [

			"description",
			"""
			The system command used to invoke the renderer - this
			can be edited to add any custom flags that are necessary,
			or to use a different renderer. The rib filename is
			automatically appended to the command before it is invoked.
			""",

			"nodule:type", "",

		],

	},

)
