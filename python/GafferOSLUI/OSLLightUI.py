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

import functools

import IECore

import Gaffer
import GafferOSL

Gaffer.Metadata.registerNode(

	GafferOSL.OSLLight,

	"description",
	"""
	Creates lights by assigning an emissive OSL shader to some simple geometry.
	""",

	"layout:activator:shapeHasRadius", lambda node : node["shape"].getValue() != node.Shape.Geometry,
	"layout:activator:shapeIsGeometry", lambda node : node["shape"].getValue() == node.Shape.Geometry,

	plugs = {

		"parameters" : [

			"layout:index", -1, # Move after shape parameters

		],

		"shaderName" : [

			"description",
			"""
			The OSL shader to be assigned to the light
			geometry.
			""",

			"plugValueWidget:type", "",

		],

		"shape" : [

			"description",
			"""
			The shape of the light. Typically, disks
			should be used with spotlight shaders and spheres
			should be used with point light shaders. The "Geometry"
			shape allows the use of custom geometry specific to a
			particular renderer.
			""",

			"preset:Disk", GafferOSL.OSLLight.Shape.Disk,
			"preset:Sphere", GafferOSL.OSLLight.Shape.Sphere,
			"preset:Geometry", GafferOSL.OSLLight.Shape.Geometry,

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		"radius" : [

			"description",
			"""
			The radius of the disk or sphere shape. Has no effect for
			other shapes.
			""",

			"layout:visibilityActivator", "shapeHasRadius",

		],

		"geometryType" : [

			"description",
			"""
			The type of geometry to create when shape is set
			to "Geometry". This should contain the name of a geometry
			type specific to the renderer being used.
			""",

			"layout:visibilityActivator", "shapeIsGeometry",

		],

		"geometryBound" : [

			"description",
			"""
			The bounding box of the geometry. Only relevant when the
			shape is set to "Geometry".
			""",

			"layout:visibilityActivator", "shapeIsGeometry",

		],

		"geometryParameters" : [

			"description",
			"""
			Arbitary parameters which specify the features of the "Geometry"
			shape type.
			""",

			"layout:section", "Settings.Geometry",
			"layout:visibilityActivator", "shapeIsGeometry",

		],

	}

)

# Defer parameter metadata lookups to the internal shader
# node.

def __parameterMetadata( plug, key ) :

	node = plug.node()
	return Gaffer.Metadata.value( node["__shader"]["parameters"].descendant( plug.relativeName( node["parameters"] ) ), key )

for key in [
	"description",
	"label",
	"noduleLayout:label",
	"layout:divider",
	"layout:section",
	"presetNames",
	"presetValues",
	"plugValueWidget:type",
	"nodule:type",
	"noduleLayout:visible",
	"noduleLayout:label",
] :
	Gaffer.Metadata.registerValue( GafferOSL.OSLLight, "parameters.*", key, functools.partial( __parameterMetadata, key = key ) )
