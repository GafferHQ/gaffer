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
import GafferScene

Gaffer.Metadata.registerNode(

	GafferScene.MeshTangents,

	"description",
	"""
	Adds tangent and binormal primitive variables to the mesh using the specified positions and UVSet.
	The primitive variables are named d[position]d[u|v].
	For example if the default 'st' UV set is specifed then two new primitive variables are added called dPds & dPdt. Where dPds is the tangent & dPdt is the binormal.
	If a non default UV set is specifed, for example 'test' then dPdtest_s & dPdtest_t primitive variables are created.
	If the position is set to 'Pref' then dPrefds & dPrefdt primitive variables are created.   
	""",

	plugs = {

		"uvSet" : [
			"description",
			"""
			Name of the UV set primitive variable used to calculate the tangents & binormals. 
			""",
		],

		"position" : [
			"description",
			"""
			Name of the primitive variable which contains the position data used calculate tangents & binormals. 
			For example Pref would compute tangents using the reference positions (if defined)
			""",
		],

		"orthogonal" : [
			"description",
			"""
			Adjusts binormals (dPds) to be orthogonal to the tangents (dPdt). 
			""",
		],


	}

)
