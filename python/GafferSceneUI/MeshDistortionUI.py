##########################################################################
#
#  Copyright (c) 2018, Image Engine Design Inc. All rights reserved.
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

	GafferScene.MeshDistortion,

	"description",
	"""
	Measures how much a mesh has been distorted from a reference shape.
	The distortion is calculated by comparing edge lengths between the
	reference and deformed shapes. Compressed areas have negative distortion
	values, stretched areas have positive distortion values, and areas with
	no deformation have distortion values of zero. The calculated distortion
	is output as primitive variables on the mesh.
	""",

	plugs = {

		"position" : {

			"description" :
			"""
			The name of the primitive variable which contains the deformed vertex
			positions for the mesh.
			""",

		},

		"referencePosition" : {

			"description" :
			"""
			The name of the primitive variable which contains the undeformed vertex
			positions for the mesh.
			""",

		},

		"uvSet" : {

			"description" :
			"""
			The name of the primitive variable which contains the UV set used to
			calculate UV distortion.
			""",

		},

		"distortion" : {

			"description" :
			"""
			The name of the primitive variable created to store the distortion
			values. This will contain a float per vertex.
			""",

		},

		"uvDistortion" : {

			"description" :
			"""
			The name of the primitive variable created to store the UV distortion
			values. This will contain a V2f with separate distortion values for the
			U and V directions.
			""",

		},

	}

)
