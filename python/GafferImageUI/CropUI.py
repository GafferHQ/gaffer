##########################################################################
#
#  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
#  Copyright (c) 2015, Nvizible Ltd. All rights reserved.
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
import GafferImage
import GafferUI

## A command suitable for use with NodeMenu.definition().append(), to add a menu
# item for the creation of a crop node
def postCreateCrop( node, menu ) :

	with node.scriptNode().context() :
		if node["in"].getInput() :
			cropFormat = node["in"]["format"].getValue()
		else:
			cropFormat = node.scriptNode()["defaultFormat"].getValue()

	node['area'].setValue( cropFormat.getDisplayWindow() )

Gaffer.Metadata.registerNode(

	GafferImage.Crop,

	"description",
	"""
	Modifies the Data and/or Display Window, in a way that is
	either user-defined, or can be driven by the existing Data
	or Display Window.
	""",

	"layout:activator:areaSourceIsCustom", lambda node : node["areaSource"].getValue() == GafferImage.Crop.AreaSource.Custom,

	plugs = {

		"area" : [

			"description",
			"""
			The custom area to set the Data/Display Window to.
			This plug is only used if 'Area Source' is set to
			Custom.
			""",

			"layout:activator", "areaSourceIsCustom",

		],

		"areaSource" : [

			"description",
			"""
			Where to source the actual area to use. If this is
			set to DataWindow, it will use the input's Data Window,
			if it is set to DisplayWindow, it will use the input's
			Display Window, and if it is set to Custom, it will use
			the Area plug.
			""",

			"preset:DataWindow", GafferImage.Crop.AreaSource.DataWindow,
			"preset:DisplayWindow", GafferImage.Crop.AreaSource.DisplayWindow,
			"preset:Custom", GafferImage.Crop.AreaSource.Custom,

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		"affectDataWindow" : [

			"description",
			"""
			Whether to intersect the defined area with the input Data
			Window. It will never pad black onto the Data Window, it
			will only ever reduce the existing Data Window.
			""",

		],

		"affectDisplayWindow" : [

			"description",
			"""
			Whether to assign a new Display Window based on the defined
			area.
			""",

		],

	}

)
