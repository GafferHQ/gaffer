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

import Gaffer
import GafferUI
import GafferImage

Gaffer.Metadata.registerNode(

	GafferImage.CollectImages,

	"description",
	"""
	Forms a series of image layers by repeatedly evaluating the input with different Contexts.
	Useful for networks that need to dynamically build an unknown number of image layers.
	""",

	"ui:spreadsheet:activeRowNamesConnection", "rootLayers",
	"ui:spreadsheet:selectorContextVariablePlug", "layerVariable",

	plugs = {

		"in" : [

			"description",
			"""
			The image which will be evaluated for each layer.
			""",

		],

		"rootLayers" : [

			"description",
			"""
			A list of the new layers to create.
			""",

		],

		"layerVariable" : [

			"description",
			"""
			This Context Variable will be set with the current layer name when evaluating the in plug.
			This allows you to vary the upstream processing for each new layer.
			""",

		],

		"mergeMetadata" : [

			"description",
			"""
			Controls how the output metadata is generated from the collected
			images. By default, the metadata from the first image alone
			is passed through. When `mergeMetadata` is on, the metadata from
			all collected images is merged, with the last image winning
			in the case of multiple image specifying the same piece of metadata.
			""",

		],
	}

)
