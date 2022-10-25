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

import Gaffer
import GafferArnold

Gaffer.Metadata.registerNode(

	GafferArnold.ArnoldDisplacement,

	"description",
	"""
	Creates displacements to be applied to meshes for
	rendering in Arnold. A displacement consists of a
	shader to provide the displacement map and several
	attributes to control the height and other displacement
	properties.

	Use an ArnoldAttributes node to control the subdivision
	settings of the mesh, which in turn controls the detail
	of the displacement. Use a ShaderAssignment node to assign
	the ArnoldDisplacement to specific objects.
	""",

	"layout:activator:autoBumpVisibility", lambda node : not node["autoBump"].isSetToDefault(),

	plugs = {

		"name" : [

			# The `name` plug is inherited from Shader, but unused by ArnoldDisplacement.
			# Hide it to avoid confusion. See comments in ArnoldDisplacement.h.
			"plugValueWidget:type", "",

		],

		"map" : [

			"description",
			"""
			The Arnold shader that provides the displacement
			map. Connect a float or colour input to displace
			along the object normals or a vector input to displace
			in a specific direction.
			""",

			"nodule:type", "GafferUI::StandardNodule",
			"noduleLayout:section", "left",

		],

		"height" : [

			"description",
			"""
			Controls the amount of displacement. Only used when
			performing displacement along the normal.
			""",

			"nodule:type", "",

		],

		"padding" : [

			"description",
			"""
			Padding added to an object's bounding box to take
			into account displacement. Arnold will subdivide
			and displace an object the first time a ray intersects
			its bounding box, so if the padding is too small,
			parts of the object will be clipped. If the padding
			is too large, rendertime will suffer and Arnold
			will emit a warning message.
			""",

			"nodule:type", "",

		],

		"zeroValue" : [

			"description",
			"""
			Defines a value that will cause no displacement to
			occur. For instance, if the displacement map contains
			a greyscale noise between 0 and 1, a zero value of 0.5
			will mean that the displacement pushes into the object
			in some places and out in others.
			""",

			"nodule:type", "",

		],

		"autoBump" : [

			"description",
			"""
			Automatically turns the details of the displacement map
			into bump, wherever the mesh is not subdivided enough
			to properly capture them.
			""",

			"nodule:type", "",
			"layout:visibilityActivator", "autoBumpVisibility",

		],

	}

)
