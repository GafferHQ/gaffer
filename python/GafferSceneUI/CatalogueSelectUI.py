##########################################################################
#
#  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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
import GafferScene

def __imageNames( plug ) :
	node = plug.node()
	imagePlug = node["in"]

	while imagePlug is not None and not isinstance( imagePlug.node(), GafferScene.Catalogue ) :
		imagePlug = imagePlug.getInput()

	if imagePlug is None :
		return []

	return imagePlug.node()["images"].keys()

def __imagePresetNames( plug ) :

	return IECore.StringVectorData(
		[ "Selected", "Output/1", "Output/2", "Output/3", "Output/4" ] +
		[ "Image/" + i for i in __imageNames( plug ) ]
	)

def __imagePresetValues( plug ) :

	return IECore.StringVectorData(
		[ "", "output:1", "output:2", "output:3", "output:4" ] +
		__imageNames( plug )
	)

Gaffer.Metadata.registerNode(

	GafferScene.CatalogueSelect,

	"description",
	"Finds an image in a directly connected Catalogue by name.",

	plugs = {

		"imageName" : [

			"description",
			"The name of the image to extract.",

			"presetNames", __imagePresetNames,
			"presetValues", __imagePresetValues,
			# Don't promote presets so they are still computed dynamically for
			# the promoted plug rather than being baked.
			"presetNames:promotable", False,
			"presetValues:promotable", False,
			"presetsPlugValueWidget:allowCustom", True,
			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		]
	}
)
