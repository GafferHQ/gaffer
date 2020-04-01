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
import GafferImage
import IECore

Gaffer.Metadata.registerNode(

	GafferImage.FlatToDeep,

	"description",
	"""
	Sets the deep flag on a flat image, and makes sure that it has a Z channel ( and optionally a ZBack channel )
	so that it can be used in deep compositing.
	""",

	"layout:activator:zConstant", lambda node : node["zMode"].getValue() == GafferImage.FlatToDeep.ZMode.Constant,
	"layout:activator:zChannel", lambda node : node["zMode"].getValue() == GafferImage.FlatToDeep.ZMode.Channel,
	"layout:activator:zBackThickness", lambda node : node["zBackMode"].getValue() == GafferImage.FlatToDeep.ZBackMode.Thickness,
	"layout:activator:zBackChannel", lambda node : node["zBackMode"].getValue() == GafferImage.FlatToDeep.ZBackMode.Channel,


	plugs = {
		"zMode" : [
			"description",
			"""
			Deep images must have a Z channel - it can be set either as a fixed depth, or using a channel.
			""",

			"preset:Constant", GafferImage.FlatToDeep.ZMode.Constant,
			"preset:Channel", GafferImage.FlatToDeep.ZMode.Channel,

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		"depth" : [

			"description",
			"""
			A constant depth value to place the whole image at.
			""",
			"layout:visibilityActivator", "zConstant",
		],

		"zChannel" : [

			"description",
			"""
			Uses this channel as a Z channel, defining the depth each pixel is at.
			""",
			"plugValueWidget:type", "GafferImageUI.ChannelPlugValueWidget",
			"layout:visibilityActivator", "zChannel",
		],

		"zBackMode" : [
			"description",
			"""
			Deep images may optionally have a ZBack channel - for transparent samples, this specifies
			the depth range over which the opacity gradually increases from 0 to the alpha value.
			""",

			"preset:None", GafferImage.FlatToDeep.ZBackMode.None_,
			"preset:Thickness", GafferImage.FlatToDeep.ZBackMode.Thickness,
			"preset:Channel", GafferImage.FlatToDeep.ZBackMode.Channel,

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		"thickness" : [

			"description",
			"""
			A constant thickness value for the whole image.  Transparent images will be
			interpreted as fog where the density increases over this range.
			""",
			"layout:visibilityActivator", "zBackThickness",
		],

		"zBackChannel" : [

			"description",
			"""
			Uses this channel as a ZBack channel, defining the end of the depth range for each
			pixel.
			""",
			"plugValueWidget:type", "GafferImageUI.ChannelPlugValueWidget",
			"layout:visibilityActivator", "zBackChannel",
		],

	}

)
