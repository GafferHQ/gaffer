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

import Gaffer
import GafferUI
import GafferImage

Gaffer.Metadata.registerNode(

	GafferImage.DiskBlur,

	"description",
	"""
	A special disk blur node which efficiently supports large radius blurs, and allows
	for a variable radius. Suitable as a building block for focal blur.
	""",

	plugs = {

		"radius" : [

			"description",
			"""
			The radius of the disk to blur by in pixels.
			""",

		],

		"radiusChannel" : [

			"description",
			"""
			If specified, this channel which will be multiplied on to the radius, allowing for variable
			radius blur.
			""",

		],

		"approximationThreshold" : [

			"description",
			"""
			How much error you are will to accept in the edges of disks. This allows disabling anti-aliasing
			for edges that are too soft to notice. It can be a substantial speed improvement in images where a
			large background region is completely out of focus.
			""",

		],

		"maxRadius" : [

			"description",
			"""
			Used to allow expensive computations to be precomputed. Should not be driven dynamically - just
			set it to something that you know is larger than what you need.
			""",

		],

		"planeDividers" : [

			"description",
			"""
			This is a rather technical plug intended for use inside a focal blur node. If set, the disks will
			be rendered to a series of depth planes, based on whether their radius is greater or less than
			the plane divider values. The planes are then composited over each other, with alpha occlusion
			between disks that are separated by at least one plane. This allows for more accurate occlusion,
			for example an in-focus foreground blocking out an out-of-focus background. The plane divider values
			must given in order from low to high ( foreground to background ). Negative radii are supported,
			and receive the same blur as the positive radius, so you can represent blurred pixels in front of,
			as well as behind the focal plane. A reasonable value for this plug, that would give reasonable
			occlusion in a focal blur, would be an exponential series from -maxRadius to +maxRadius, for example, something like [ -64, -32, -16, -8, -4, -2, -1, 1, 2, 4, 8, 16, 32, 6 ]
			""",

			"layout:section", "Advanced"

		],

	}

)
