##########################################################################
#
#  Copyright (c) 2025, Image Engine Design Inc. All rights reserved.
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


Gaffer.Metadata.registerNode(

	GafferImage.DiskBlur,

	"description",
	"""
	A special disk blur node which efficiently supports large radius blurs, and allows for a
	variable radius. Works by rendering each input pixel as a disk in the output, using special
	acceleration structures that make rendering large disks fast. Suitable as a building block
	for focal blur.
	""",

	plugs = {

		"radius" : {

			"description" :
			"""
			The radius of the disk to blur by in pixels.
			""",

		},

		"radiusChannel" : {

			"description" :
			"""
			An optional input image channel which defines a blur radius per pixel, allowing the radius to be
			varied across the image. The per-pixel radius is multiplied with the main radius control.
			""",
			"plugValueWidget:type" : "GafferImageUI.ChannelPlugValueWidget",
			"channelPlugValueWidget:extraChannels" : IECore.StringVectorData( [ "" ] ),
			"channelPlugValueWidget:extraChannelLabels" : IECore.StringVectorData( [ "None" ] ),
		},

		"approximationThreshold" : {

			"description" :
			"""
			The maximum acceptable error caused by omitting anti-aliasing for a particular disk. Since very
			large disks often contribute very little to each individual output pixel, omitting anti-aliasing
			for them can provide a substantial speed improvement.
			""",
			"layout:section" : "Advanced"

		},

		"maxRadius" : {

			"description" :
			"""
			An upper limit on the disk radius (`radiusChannel * radius`). Larger disks will be clamped to this
			size. Used to accelerate rendering, so higher-than-necessary settings may reduce speed.
			""",

		},

		"boundingMode" : {

			"description" :
			"""
			The method used at the boundaries of the input data window, to compensate for the lack of
			information outside it :

			- Black : Treats the input as black outside the data window, causing darkening at the edges of the image.
			- Mirror : Treats the input as mirrored across the data window boundary.
			""",

			"preset:Black" : GafferImage.DiskBlur.BoundingMode.Black,
			"preset:Mirror" : GafferImage.DiskBlur.BoundingMode.Mirror,

			"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",

		},

		"layerBoundaries" : {

			"description" :
			"""
			Defines a series of layers which are alpha-composited to generate the final image. Each layer
			contains all the disks within a specific radius range, allowing "foreground" disks to occlude
			"background" disks. Intended for use in approximating focal blur.

			The layers are defined by the radius values at their boundaries, which must be specified from
			low to high. Occlusion occurs between disks that are separated by at least 2 boundaries.
			Negative radii are accepted, allowing blurring to be represented both in front of and behind a
			focal plane. A reasonable value for the simulation of focal blur is therefore an exponential
			series from -maxRadius to +maxRadius, for example [ -32, -16, -8, -4, -2, -1, 1, 2, 4, 8, 16, 32 ]

			> Tip : The FocalBlur node provides a simpler and more intuitive method for defining occlusion
			layers (it uses the DiskBlur node internally).
			""",

			"layout:section" : "Advanced"

		},

	}

)
