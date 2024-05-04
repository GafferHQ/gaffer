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

import itertools

import Gaffer
import GafferImage

Gaffer.Metadata.registerNode(

	GafferImage.ContactSheetCore,

	"description",
	"""
	Collects multiple input images, transforming them into tiles within
	the output image. Provides the core functionality of the ContactSheet
	node, and may be reused for making similar nodes.
	""",

	plugs = {

		"format" : [

			"description",
			"""
			The resolution and aspect ratio of the output image.
			""",

		],

		"tiles" : [

			"description",
			"""
			The bounding boxes of each tile.

			> Note : Each input image will be scaled to fit entirely within its tile
			> while preserving aspect ratio.
			""",

		],

		"tileVariable" : [

			"description",
			"""
			Context variable used to pass the index of the current tile to the upstream
			node network. This should be used to provide a different input image per tile.
			""",

		],

		"filter" : [

			"description",
			"""
			The pixel filter used when resizing the input images. Each
			filter provides different tradeoffs between sharpness and
			the danger of aliasing or ringing.
			""",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

			"preset:Default", "",
			"preset:Nearest", "nearest",

		] + list( itertools.chain(

			*[ ( "preset:" + x.title(), x ) for x in GafferImage.FilterAlgo.filterNames() ]

		) ),

	}

)
