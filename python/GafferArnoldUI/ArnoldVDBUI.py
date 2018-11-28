##########################################################################
#
#  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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
import GafferArnold

Gaffer.Metadata.registerNode(

	GafferArnold.ArnoldVDB,

	"description",
	"""
	Creates an external procedural for rendering
	VDB volumes in Arnold.
	""",

	plugs = {

		"fileName" : [

			"description",
			"""
			The name of the VDB file to be loaded.
			""",

			"path:leaf", True,
			"path:valid", True,
			"path:bookmarks", "vdb",
			"fileSystemPath:extensions", "vdb",
			"fileSystemPath:extensionsLabel", "Show only VDB files",

		],

		"grids" : [

			"description",
			"""
			A space separated list of grids to be loaded and made available as
			channels in the volume shader.
			""",

		],

		"velocityGrids" : [

			"description",
			"""
			A space separated list of grids used to be used to generate motion
			blur. Should either contain a single vector grid or 3 float grids.
			"""

		],

		"velocityScale" : [

			"description",
			"""
			A scale factor applied to the velocity grids, to either increase
			or decrease motion blur.
			""",

		],

		"stepSize" : [

			"description",
			"""
			The ray marching step size. This should be small enough to capture
			the smallest details in the volume. Values which are too large will
			cause aliasing artifacts, and values which are too small will cause
			rendering to be excessively slow. The default value of 0 causes the
			size to be calculated automatically based on the resolution of the
			VDB file. The step scale can then be used to make relative adjustments
			on top of this automatic size.
			""",

		],

		"stepScale" : [

			"description",
			"""
			A multiplier applied to the step size. This is most useful when the
			step size is computed automatically. Typically stepScale would be
			increased above 1 to give improved render times when it is known that
			the VDB file doesn't have a lot of fine detail at the voxel level -
			a value of 4 might be a good starting point for such a file.
			""",

		],

	}

)
