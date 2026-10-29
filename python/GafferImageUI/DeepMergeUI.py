##########################################################################
#
#  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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
import GafferImage

Gaffer.Metadata.registerNode(

	GafferImage.DeepMerge,

	"description",
	"""
	Merges the samples from two or more images into a single deep image.
	The source images may be deep or flat.
	""",

	"layout:activator:modeCollect", lambda node : node["mode"].getValue() == GafferImage.DeepMerge.Mode.Collect,
	"ui:spreadsheet:enabledRowNamesConnection", "contextValues",
	"ui:spreadsheet:selectorContextVariablePlug", "contextVariable",

	plugs = {

		"in.*" : {

			"description" :
			"""
			A deep or flat image input.
			""",

		},

		"mode" : {

			"description" :
			"""
			Defines how inputs are selected for merging :

			- Standard : Each input plug is used once.
			- Collect : Each input plug is evaluated for each value in `contextValues`.
			""",

			"preset:Standard" : GafferImage.DeepMerge.Mode.Standard,
			"preset:Collect" : GafferImage.DeepMerge.Mode.Collect,

			"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",
		},

		"contextValues" : {

			"description" :
			"""
			The values to use for the `contextVariable` when in `Collect` mode. Each input will be evaluated for
			each value, forming multiple layers in the merge. This value will be passed to `contextVariable`, and
			the length of this list determines the number of times each input is evaluated.
			""",

			"layout:visibilityActivator" : "modeCollect",
		},

		"contextVariable" : {

			"description" :
			"""
			Name of the context variable that takes values from `contextValues` in Collect mode. May be used
			upstream to vary the multiple layers being taken from each input.
			""",

			"layout:visibilityActivator" : "modeCollect",

		},

		"indexContextVariable" : {

			"description" :
			"""
			Name of the context variable that contains the index of the current context value when in Collect
			mode. Ranges from 0 to `len( contextValues ) - 1`. May be used upstream to vary the multiple
			layers being taken from each input.
			""",

			"layout:visibilityActivator" : "modeCollect",

		},

	}

)
