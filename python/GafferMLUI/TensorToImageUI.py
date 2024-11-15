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
import GafferML

Gaffer.Metadata.registerNode(

	GafferML.TensorToImage,

	plugs = {

		"tensor" : [

			"description",
			"""
			The input tensor to be turned into an image. Typically this would be connected
			to the output of an Inference node that is doing image processing.
			""",

			"plugValueWidget:type", "",
			"nodule:type", "GafferUI::StandardNodule",

		],

		"channels" : [

			"description",
			"""
			The names to give to the channels in the output image. These
			channels are unpacked from the tensor in the order in which they are
			specified. For example, an order of `[ "B", "G", "R" ]` might be
			needed for use with models trained on images using OpenCV
			conventions. An empty channel name may be used to skip a channel
			when unpacking.
			""",

		],

		"interleavedChannels" : [

			"description",
			"""
			Indicates that the channels are interleaved in the input tensor, in
			which case they will be deinterleaved when converting to the output
			image. Whether or not channels are interleaved will depend on the
			model from which the tensor is obtained.
			""",

		],

		"out" : [

			"description",
			"""
			The output image.
			""",

		],

	}
)
