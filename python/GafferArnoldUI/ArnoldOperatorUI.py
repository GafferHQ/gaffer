##########################################################################
#
#  Copyright (c) 2024, Cinesite VFX Ltd. All rights reserved.
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

	GafferArnold.ArnoldOperator,

	"description",
	"""
	Assigns an operator. This is stored as an `ai:operator` option in Gaffer's
	globals.
	""",

	plugs = {

		"operator" : [

			"description",
			"""
			The operator to be assigned. The output of an ArnoldShader node
			holding an operator should be connected here. Multiple operators may be
			assigned at once by chaining them together via their `input`
			parameters, and then assigning the final operator via the ArnoldOperator
			node.
			""",

			"noduleLayout:section", "left",
			"nodule:type", "GafferUI::StandardNodule",

		],

		"mode" : [

			"description",
			"""
			The mode used to combine the `operator` input with any operators that
			already exist in the globals.

			- Replace : Removes all pre-existing operators, and replaces them with
			the new ones.
			- InsertFirst : Inserts the new operators so that they will be run before
			any pre-existing operators.
			- InsertLast : Inserts the new operators so that they will be run after
			any pre-existing operators.
			""",

			"preset:Replace", GafferArnold.ArnoldOperator.Mode.Replace,
			"preset:InsertFirst", GafferArnold.ArnoldOperator.Mode.InsertFirst,
			"preset:InsertLast", GafferArnold.ArnoldOperator.Mode.InsertLast,
			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

	}

)
