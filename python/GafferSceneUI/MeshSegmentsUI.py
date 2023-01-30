##########################################################################
#
#  Copyright (c) 2023, Image Engine Design Inc. All rights reserved.
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

	GafferScene.MeshSegments,

	"description",
	"""
	Creates a uniform primitive variable of integer indices indicating which
	connected segment each face belongs to.  May create segments based on
	what is connected in the mesh's topology, or based on an indexed
	primitive variable ( for example, you may segment based on which faces
	share UVs in order to segment into UV islands ).
	""",

	"layout:section:Settings.Inputs:collapsed", False,
	"layout:section:Settings.Outputs:collapsed", False,

	plugs = {


		"connectivity" : [

			"description",
			"""
			The name of the primitive variable which will determine the segmentation.
			You may specify an empty string, or any vertex primitive variable to use
			the vertex topology to determine segments, or use an indexed face-varying
			primitive variable - this will segment based on which face-vertices are
			connected ( for example, using indexed UVs will produce UV islands ).
			Uniform and constant primitive variables are also supported for consistency,
			but they just output which faces have the same uniform value, or put all
			faces in one segment.
			""",
			"layout:section", "Settings.Inputs"
		],

		"segment" : [

			"description",
			"""
			The name of the uniform primitive variable which will be created to hold
			the segment index for each face.
			""",
			"layout:section", "Settings.Outputs"
		],

	}

)
