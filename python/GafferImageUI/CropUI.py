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
import GafferUI
import GafferImage

## A function suitable as the postCreator in a NodeMenu.append() call. It
# sets the area for the node to cover the entire format.
def postCreate( node, menu ) :

	with node.scriptNode().context() :
		if node["in"].getInput() :
			cropFormat = node["in"]["format"].getValue()
		else:
			cropFormat = GafferImage.FormatPlug.getDefaultFormat( node.scriptNode().context() )

	node['area'].setValue( cropFormat.getDisplayWindow() )

Gaffer.Metadata.registerNode(

	GafferImage.Crop,

	"description",
	"""
	Modifies the Data and/or Display Window, in a way that is
	either user-defined, or can be driven by the existing Data
	or Display Window.
	""",

	"layout:activator:areaSourceIsArea", lambda node : node["areaSource"].getValue() == GafferImage.Crop.AreaSource.Area,
	"layout:activator:areaSourceIsFormat", lambda node : node["areaSource"].getValue() == GafferImage.Crop.AreaSource.Format,
	"layout:activator:affectDisplayWindowIsOn", lambda node : node["affectDisplayWindow"].getValue(),
	"layout:activator:areaSourceIsFormatAndAffectDisplayWindowIsOn", lambda node : node["areaSource"].getValue() == GafferImage.Crop.AreaSource.Format and node["affectDisplayWindow"].getValue(),

	plugs = {

		"areaSource" : [

			"description",
			"""
			Where to source the actual area to use. If this is
			set to DataWindow, it will use the input's Data Window,
			if it is set to DisplayWindow, it will use the input's
			Display Window, and if it is set to Area, it will use
			the Area plug.
			""",

			"preset:Area", GafferImage.Crop.AreaSource.Area,
			"preset:Format", GafferImage.Crop.AreaSource.Format,
			"preset:DataWindow", GafferImage.Crop.AreaSource.DataWindow,
			"preset:DisplayWindow", GafferImage.Crop.AreaSource.DisplayWindow,

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		"area" : [

			"description",
			"""
			The custom area to set the Data/Display Window to.
			This plug is only used if 'Area Source' is set to
			Area.
			""",

			"layout:activator", "areaSourceIsArea",

		],

		"format" : [

			"description",
			"""
			The Format to use as the area to set the Data/Display
			Window to. This plug is only used if 'Area Source' is
			set to Format.
			""",

			"layout:activator", "areaSourceIsFormat",

		],

		"formatCenter" : [

			"description",
			"""
			Whether to center the output image (based on the
			existing display window) inside the new display
			window format. This plug is only used if
			'Area Source' is set to Format, and 'Affect Display
			Window' it checked.
			""",

			"layout:activator", "areaSourceIsFormatAndAffectDisplayWindowIsOn",
			"layout:divider", True

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

		"resetOrigin" : [

			"description",
			"""
			Shifts the cropped image area back to the origin, so that
			the bottom left of the display window is at ( 0, 0 ).
			""",

			"layout:activator", "affectDisplayWindowIsOn",

		]

	}

)
