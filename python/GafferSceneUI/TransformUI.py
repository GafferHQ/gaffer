##########################################################################
#
#  Copyright (c) 2013-2014, Image Engine Design Inc. All rights reserved.
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

import GafferScene

Gaffer.Metadata.registerNode(

	GafferScene.Transform,

	"description",
	"""
	Applies a transformation to the local matrix
	of all locations matched by the filter.
	""",

	plugs = {

		"space" : {

			"description" :
			"""
			The space in which the transformation is specified.
			Note that no matter which space is chosen, only the
			local matrices of the filtered locations are ever modified.
			They are simply modified in such as way as to emulate a
			modification in the chosen space.

			Local
			:	The transformation is specified in local space and
				is therefore post-multiplied onto the local matrix.

			Parent
			:	The transformation is specified in parent space and
				is therefore pre-multiplied onto the local matrix.

			World
			:	The transformation is specified in world space and
				will therefore be applied as if the whole world was
				moved. This effect is then applied on a per-location
				basis to each of the filtered locations.

			Reset Local
			:	The local matrix is replaced with the specified transform.

			Reset World
			:	The transformation is specified as an absolute matrix
				in world space. Each of the filtered locations will
				be moved to this absolute position.
			""",

			"preset:Local" : GafferScene.Transform.Space.Local,
			"preset:Parent" : GafferScene.Transform.Space.Parent,
			"preset:World" : GafferScene.Transform.Space.World,
			"preset:Reset Local" : GafferScene.Transform.Space.ResetLocal,
			"preset:Reset World" : GafferScene.Transform.Space.ResetWorld,


			"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",

		},

		"transform" : {

			"description" :
			"""
			The transform to be applied.
			""",

		}

	}

)
