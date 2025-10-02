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
import IECoreScene


## To deprecate the uTangent and vTangent we hide them and feed in the new plugs.
def postCreate( node, menu ) :
	node["uTangent"].setInput( node['tangent'] )
	node["vTangent"].setInput( node['biTangent'] )
	Gaffer.Metadata.registerValue( node['uTangent'], 'plugValueWidget:type', '' )
	Gaffer.Metadata.registerValue( node['vTangent'], 'plugValueWidget:type', '' )
	Gaffer.Metadata.registerValue( node['tangent'], 'layout:activator', 'alwaysActive' )
	Gaffer.Metadata.registerValue( node['biTangent'], 'layout:activator', 'alwaysActive' )


Gaffer.Metadata.registerNode(

	GafferScene.MeshTangents,

	"description",
	"""
	Adds surface tangent primitive variables to the mesh based on either UV or topology information.
	""",

	"layout:activator:uvActivator", lambda parent : parent["mode"].getValue() == int(GafferScene.MeshTangents.Mode.UV),
	"layout:activator:uvDeactivator", lambda parent : parent["mode"].getValue() != int(GafferScene.MeshTangents.Mode.UV),
	"layout:activator:leftHandedActivator", lambda parent : parent["orthogonal"].getValue() == True,
	"layout:activator:alwaysActive", lambda x : True,

	plugs = {

		"mode" : {

			"description" :
			"""
			The style of how to calculate the Tangents.
			(UV) calculates the tangents based on the gradient of the the corresponding UVs
			(FirstEdge) defines the vector to the first neighbor as tangent and the bitangent orthogonal to tangent and normal
			(TwoEdges) defines the vector between the first two neighbors as tangent and the bitangent orthogonal to tangent and normal
			(PrimitiveCentroid) points the tangent towards the primitive centroid and the bitangent orthogonal to tangent and normal
			""",

			"preset:UV" : GafferScene.MeshTangents.Mode.UV,
			"preset:FirstEdge" : GafferScene.MeshTangents.Mode.FirstEdge,
			"preset:TwoEdges" : GafferScene.MeshTangents.Mode.TwoEdges,
			"preset:PrimitiveCentroid" : GafferScene.MeshTangents.Mode.PrimitiveCentroid,

			"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",
		},

		"orthogonal" : {
			"description" :
			"""
			Adjusts vTangent to be orthogonal to the uTangent.
			""",
		},

		"leftHanded" : {
			"description" :
			"""
			Make the local coordinate frame left handed
			""",
			"layout:activator" : "leftHandedActivator",
		},

		"position" : {
			"description" :
			"""
			Name of the primitive variable which contains the position data used to calculate tangents & binormals.
			For example 'Pref' would compute tangents using the reference positions (if defined)
			""",
			"layout:section" : "Settings.Input",
		},

		"normal" : {
			"description" :
			"""
			Name of the primitive variable which contains the normals used to calculate tangents & binormals.
			""",
			"layout:section" : "Settings.Input",
			"layout:activator" : "uvDeactivator",
		},

		"uvSet" : {
			"description" :
			"""
			Name of the UV set primitive variable used to calculate uTangent & vTangent.
			""",
			"layout:section" : "Settings.Input",
			"layout:activator" : "uvActivator",
		},

		"uTangent" : {
			"description" :
			"""
			Name of the primitive variable which will contain the uTangent data.
			""",
			"layout:section" : "Settings.Output",
			"layout:activator" : "uvActivator",
		},

		"vTangent" : {
			"description" :
			"""
			Name of the primitive variable which will contain the vTangent data.
			""",
			"layout:section" : "Settings.Output",
			"layout:activator" : "uvActivator",
		},

		"tangent" : {
			"description" :
			"""
			Name of the primitive variable which will contain the tangent data.
			""",
			"layout:section" : "Settings.Output",
			"layout:activator" : "uvDeactivator",
		},

		"biTangent" : {
			"description" :
			"""
			Name of the primitive variable which will contain the biTangent data.
			""",
			"layout:section" : "Settings.Output",
			"layout:activator" : "uvDeactivator",
		}
	}

)
