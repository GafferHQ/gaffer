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

import IECore

import Gaffer
import GafferUI
import GafferScene

Gaffer.Metadata.registerNode(

	GafferScene.UDIMQuery,

	"description",
	"""
	Gathering information about what UDIMs are present in meshes matching
	the input scene and filter, and which meshes they belong to.

	The output is a three level dictionary ( stored as CompoundObjects ), containing information about the selected UDIMs.

	The keys of the top level are all the UDIMs containing part of the target meshes.
	The keys of the second level are the meshes which touch that UDIM.
	The keys of the third level are any attributes on that mesh which match extraAttributes, and the values of the third-level dictionary are the attribute values.

	An example result, with two udims, and "attributes" set to "bake:resolution", might look like this:

	```
	{
			"1001" : {
				"/mesh1" : { "bake:resolution", 512 },
				"/mesh2" : { "bake:resolution", 1024 },
			},
			"1002" : {
				"/mesh1" : { "bake:resolution", 512 },
			},
	}
	```
	""",

	plugs = {

		"in" : [

			"description",
			"""
			The scene to query UDIMs from.
			""",

		],

		"filter" : [

			"description",
			"""
			The filter used to control which parts of the scene are
			processed. A Filter node should be connected here.
			""",

			"layout:section", "Filter",
			"noduleLayout:section", "right",
			"layout:index", -3, # Just before the enabled plug,
			"nodule:type", "GafferUI::StandardNodule",
			"plugValueWidget:type", "GafferSceneUI.FilterPlugValueWidget",

		],

		"uvSet" : [

			"description",
			"""
			The name of the primitive variable which drives the UVs to compute UDIMs from.
			Should be a Face-Varying or Vertex interpolated V2f.
			""",
			"nodule:type", "",

		],

		"attributes" : [

			"description",
			"""
			A space separated list of attribute names ( may use wildcards ), to collect from meshes
			which have UDIMs, and return as part of the output.  Inherited attributes are included.
			""",
			"nodule:type", "",

		],

		"out" : [

			"description",
			"""
			A 3 level dictionary of results stored in a CompoundObject, as described in the node description.
			""",

			"nodule:type", "GafferUI::StandardNodule",

		],

	}

)
