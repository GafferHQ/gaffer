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

import inspect
import itertools

import Gaffer
import GafferUI
import GafferImage
import GafferImageUI

Gaffer.Metadata.registerNode(

	GafferImage.Resize,

	"description",
	"""
	Resizes the image to a new resolution, scaling the
	contents to fit the new size.
	""",

	"layout:customWidget:filterDeepWarning:widgetType", "GafferImageUI.ResampleUI._FilterDeepWarningWidget",
	"layout:customWidget:filterDeepWarning:section", "Settings",
	"layout:customWidget:filterDeepWarning:accessory", True,
	"layout:customWidget:filterDeepWarning:visibilityActivator", lambda node : node["filterDeep"].getValue(),

	plugs = {

		"format" : [

			"description",
			"""
			The new format (resolution and pixel aspect ratio)
			of the output image.
			""",

		],

		"fitMode" : [

			"description",
			"""
			Determines how the image is scaled to fit the new
			resolution. If the aspect ratios of the input and
			the output images are the same, then this has no
			effect, otherwise it dictates what method is used
			to preserve the aspect ratio of the data.

			Horizontal
			:	The image is scaled so that it fills the full
				width of the output resolution and aspect ratio
				is preserved.

			Vertical
			:	The image is scaled so that it fills the full
				height of the output resolution and aspect ratio
				is preserved.

			Fit
			:	Automatically picks Horizontal or Vertical such
				that all of the input image is contained within
				the output image. Padding is applied top and
				bottom or left and right as necessary.

			Fill
			:	Automatically picks Horizontal or Vertical such
				that the full output resolution is covered. The
				image contents will extend outside the top and
				bottom or left and right of the display window
				as necessary.

			Distort
			:	Distorts the image so that the input display
				window is fitted exactly to the output display
				window.
			""",

			"preset:Horizontal", GafferImage.Resize.FitMode.Horizontal,
			"preset:Vertical", GafferImage.Resize.FitMode.Vertical,
			"preset:Fit", GafferImage.Resize.FitMode.Fit,
			"preset:Fill", GafferImage.Resize.FitMode.Fill,
			"preset:Distort", GafferImage.Resize.FitMode.Distort,

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		"filter" : [

			"description",
			"""
			The filter used when transforming the image. Each
			filter provides different tradeoffs between sharpness and
			the danger of aliasing or ringing.
			""",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

			"preset:Default", "",
			"preset:Nearest", "nearest",

		] + list( itertools.chain(

			# Disk doesn't make much sense as a resizing filter, and also causes artifacts because
			# its default width is small enough to fall into the gaps between pixels.
			*[ ( "preset:" + x.title(), x ) for x in GafferImage.FilterAlgo.filterNames() if x != "disk" ]

		) ),

		"filterDeep" : [

			"description",
			inspect.cleandoc(
				"""
				When on, deep images are resized accurately using the same filter
				as flat images. When off, deep images are resized using the Nearest
				filter.

				Filters with negative lobes ( such as Lanczos3 which is the Default
				for downscaling ) cannot be represented at all depths with perfect
				accuracy, because deep alpha must be between 0 and 1, and must be
				non-decreasing. In extreme cases, involving bright segments
				with very low alpha, it may be preferable to choose a softer filter
				without negative lobes ( like Blackman-Harris ).

				"""
			) + GafferImageUI.ResampleUI._filterDeepWarning,

		],

	}

)
