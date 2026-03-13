##########################################################################
#
#  Copyright (c) 2026, Cinesite VFX Ltd. All rights reserved.
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
import GafferScene

Gaffer.Metadata.registerNode(

	GafferScene.ReflectionConstraint,

	"description",
	"""
	Transforms objects to be reflected in the target when viewed from a chosen
	camera. Best used with UV or Vertex target modes, since they provide a suitable
	normal to drive the reflection.
	""",

	"layout:activator:aimIsEnabled", lambda node : node["aimEnabled"].getValue(),

	plugs = {

		"referenceFrame" : {

			"divider" : True,

		},

		"camera" : {

			"description" :
			"""
			The camera used to calculate the reflection position.

			> Tip : Only the position - and not the orientation, scale or
			> projection - of the camera is relevant, so a scene location
			> of any type may be used.
			""",

			"plugValueWidget:type" : "GafferSceneUI.ScenePathPlugValueWidget",

		},

		"distanceMode" : {

			"description" :
			"""
			The method used to set the constrained object's distance from
			the target.

			- Camera : Matches the distance from the camera to the target.
			- Constant : Uses a constant distance specified by the `distance` plug.
			""",

			"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",
			"preset:Camera" : GafferScene.ReflectionConstraint.DistanceMode.Camera,
			"preset:Constant" : GafferScene.ReflectionConstraint.DistanceMode.Constant,

		},

		"distance" : {

			"description" :
			"""
			Specifies the distance between the constrained object and the target.
			Only used when `distanceMode` is Constant.
			""",

			"layout:activator" : lambda plug : plug.node()["distanceMode"].getValue() == GafferScene.ReflectionConstraint.DistanceMode.Constant,

		},

		"aimEnabled" : {

			"description" :
			"""
			Enables an additional aim constraint, which orients the object to
			face the target.
			"""

		},

		"aim" : {

			"description" :
			"""
			The aim vector, specified in object space. The object will be
			transformed so that this vector points at the target.
			""",

			"layout:activator" : "aimIsEnabled",

		},

		"up" : {

			"description" :
			"""
			The up vector, specified in object space. The object will be
			transformed so that this vector points up in world space, as far as
			is possible.
			""",

			"layout:activator" : "aimIsEnabled",

		},

	}

)
