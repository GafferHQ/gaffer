##########################################################################
#
#  Copyright (c) 2022, Cinesite VFX Ltd. All rights reserved.
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

import Gaffer
import GafferArnold

Gaffer.Metadata.registerNode(

	GafferArnold.ArnoldImager,

	"description",
	"""
	Assigns an imager. This is stored as an `ai:imager` option in Gaffer's
	globals, and applied to all render outputs.

	> Tip : Use the `layer_selection` parameter on each imager to control
	> which AOVs the imager applies to.
	""",

	plugs = {

		"imager" : [

			"description",
			"""
			The imager to be assigned. The output of an ArnoldShader node
			holding an imager should be connected here. Multiple imagers may be
			assigned at once by chaining them together via their `input`
			parameters, and then assigning the final imager via the ArnoldImager
			node.
			""",

			"noduleLayout:section", "left",
			"nodule:type", "GafferUI::StandardNodule",

		],

		"mode" : [

			"description",
			"""
			The mode used to combine the `imager` input with any imagers that
			already exist in the globals.

			- Replace : Removes all pre-existing imagers, and replaces them with
			  the new ones.
			- InsertFirst : Inserts the new imagers so that they will be run before
			  any pre-existing imagers.
			- InsertLast : Inserts the new imagers so that they will be run after
			  any pre-existing imagers.
			""",

			"preset:Replace", GafferArnold.ArnoldImager.Mode.Replace,
			"preset:InsertFirst", GafferArnold.ArnoldImager.Mode.InsertFirst,
			"preset:InsertLast", GafferArnold.ArnoldImager.Mode.InsertLast,
			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

	}

)
