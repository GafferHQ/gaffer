##########################################################################
#
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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
import GafferUI

##########################################################################
# Metadata
##########################################################################

Gaffer.Metadata.registerNode(

	GafferScene.Sphere,

	"description",
	"""
	Produces scenes containing a sphere.
	""",

	"layout:activator:typeIsMesh", lambda node : node["type"].getValue() == GafferScene.Sphere.Type.Mesh,

	plugs = {

		"type" : {

			"description" :
			"""
			The type of object to produce. May be a SpherePrimitive or a Mesh.
			""",

			"preset:Primitive" : GafferScene.Sphere.Type.Primitive,
			"preset:Mesh" : GafferScene.Sphere.Type.Mesh,

			"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",

		},

		"radius" : {

			"description" :
			"""
			Radius of the sphere.
			""",

		},

		"zMin" : {

			"description" :
			"""
			Limits the extent of the sphere along the lower pole.
			Valid values are in the range [-1,1] and should always
			be less than zMax.
			""",

		},

		"zMax" : {

			"description" :
			"""
			Limits the extent of the sphere along the upper pole.
			Valid values are in the range [-1,1] and should always
			be greater than zMin.
			""",

		},

		"thetaMax" : {

			"description" :
			"""
			Limits the extent of the sphere around the pole axis.
			Valid values are in the range [0,360].
			""",

		},

		"divisions" : {

			"description" :
			"""
			Controls tesselation of the sphere when type is Mesh.
			""",

			"layout:activator" : "typeIsMesh",

		},

	}

)
