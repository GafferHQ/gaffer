##########################################################################
#
#  Copyright (c) 2020, Don Boogert. All rights reserved.
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
#      * Neither the name of Don Boogert nor the names of
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

import GafferUI
import GafferVDB

GafferUI.Metadata.registerNode(
	GafferVDB.ScatterPoints,
	'description',
	"""Scatter points into active voxels of VDB grid""",

	"layout:activator:nonuniform", lambda node : node["nonuniform"].getValue(),
	"layout:activator:uniform", lambda node : not node["nonuniform"].getValue(),
	plugs={

		'outputType' : [
			'description',
			"""
			Type of primitive to generate 
			""",
			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
			"preset:Points Primitive", 0,
			"preset:VDB Points", 1
		],
		'grid' : [
			'description',
			"""
			Name of grid in VDBObject in which points will be scattered
			""",
		],

		'nonuniform' : [
			'description',
			"""
			If nonuniform the grid value is used to weight the number of points
			""",
		],
		'pointCount' : [
			'description',
			"""
			If 'uniform' the total number of points to generate.
			""",
			"layout:activator", "uniform",
		],
		'probability' : [
			'description',
			"""
			If 'nonuniform' the global probability which is used with the voxel value to weight the number of points generated in that voxel. 
			""",
			"layout:activator", "nonuniform",
		],

	}
)
