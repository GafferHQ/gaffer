##########################################################################
#
#  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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
import GafferUI
import GafferScene

##########################################################################
# Metadata
##########################################################################

Gaffer.Metadata.registerNode(

	GafferScene.Instancer,

	"description",
	"""
	Copies from an input scene onto the vertices of a target
	object, making one copy per vertex. Additional primitive
	variables on the target object can be used to choose between
	multiple instances, and to specify their orientation and
	scale. Note the target object will be removed from the scene.
	""",

	"layout:section:Settings.General:collapsed", False,
	"layout:section:Settings.Transforms:collapsed", False,
	"layout:section:Settings.Attributes:collapsed", False,

	"layout:activator:modeIsIndexedRootsList", lambda node : node["prototypeMode"].getValue() == GafferScene.Instancer.PrototypeMode.IndexedRootsList,
	"layout:activator:modeIsNotIndexedRootsList", lambda node : node["prototypeMode"].getValue() != GafferScene.Instancer.PrototypeMode.IndexedRootsList,
	"layout:activator:modeIsNotRootPerVertex", lambda node : node["prototypeMode"].getValue() != GafferScene.Instancer.PrototypeMode.RootPerVertex,

	plugs = {

		"parent" : [

			"description",
			"""
			The object on which to make the instances. The
			position, orientation and scale of the instances
			are taken from per-vertex primitive variables on
			this object. This is ignored when a filter is
			connected, in which case the filter specifies
			multiple objects to make the instances from.
			""",

			"layout:section", "Settings.General",

		],

		"name" : [

			"description",
			"""
			The name of the location the instances will be
			generated below. This will be parented directly
			under the parent location.
			""",

			"layout:section", "Settings.General",

		],

		"prototypes" : [

			"description",
			"""
			The scene containing the prototypes to be applied to
			each vertex. Use the `prototypeMode` and associated
			plugs to control the mapping between prototypes and
			instances.

			Note that the prototypes are not limited to being a single
			object - they can have arbitrary child hierarchies.
			""",

			"plugValueWidget:type", "",

		],

		"prototypeMode" : [

			"description",
			"""
			The method used to define how the prototypes map
			onto each instance.

			- In "Indexed (Roots List)" mode, the `prototypeIndex`
			  primitive variable must be an integer per-vertex.
			  Optionally, a path in the prototypes scene corresponding
			  to each index can be specified via the `prototypeRootsList`
			  plug. If no roots are specified, an index of 0 applies the
			  first location from the prototypes scene, an index of 1
			  applies the second, and so on.

			- In "Indexed (Roots Variable)" mode, the `prototypeIndex`
			  primitive variable must be an integer per-vertex, and
			  the `prototypeRoots` primitive variable must be a separate
			  constant string array specifying a path in the prototypes
			  scene corresponding to each index.

			- In "Root per Vertex" mode, the `prototypeRoots` primitive
			  variable must be a string per-vertex which will be used to
			  specify a path in the prototypes scene for each instance.

			  > Note : it is advisable to provide an indexed string
			  array in order to limit the number of unique prototypes.
			""",

			"preset:Indexed (Roots List)", GafferScene.Instancer.PrototypeMode.IndexedRootsList,
			"preset:Indexed (Roots Variable)", GafferScene.Instancer.PrototypeMode.IndexedRootsVariable,
			"preset:Root per Vertex", GafferScene.Instancer.PrototypeMode.RootPerVertex,
			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
			"layout:section", "Prototypes",

		],

		"prototypeIndex" : [

			"description",
			"""
			The name of a per-vertex integer primitive variable used
			to determine which prototype is applied to the vertex.
			This plug is used in "Indexed (Roots List)" mode as well
			as "Indexed (Roots Variable)" mode.
			""",

			"userDefault", "prototypeIndex",
			"layout:section", "Prototypes",
			"layout:visibilityActivator", "modeIsNotRootPerVertex",

		],

		"prototypeRoots" : [

			"description",
			"""
			If `prototypeMode` is set to "Indexed (Roots Variable)",
			then this should specify the name of a constant string
			array primitive variable used to map between `prototypeIndex`
			and paths in the prototypes scene.

			If `prototypeMode` is set to "Root per Vertex", then this
			should specify the name of a per-vertex string primitive
			variable used to specify a path in the prototypes scene
			for each instance.

			This plug is not used in "Indexed (Roots List)" mode.
			""",

			"layout:section", "Prototypes",
			"layout:visibilityActivator", "modeIsNotIndexedRootsList",

		],

		"prototypeRootsList" : [

			"description",
			"""
			An explicit list of paths used to map between `prototypeIndex`
			and paths in the prototypes scene. This plug is only used in
			"Indexed (Roots List)" mode.
			""",

			"layout:section", "Prototypes",
			"layout:visibilityActivator", "modeIsIndexedRootsList",

		],

		"id" : [

			"description",
			"""
			The name of a per-vertex integer primitive variable
			used to give each instance a unique identity. This
			is useful when points are added and removed over time,
			as is often the case in a particle simulation. The
			id is used to name the instance in the output scene.
			""",

			"layout:section", "Settings.General",

		],

		"position" : [

			"description",
			"""
			The name of the per-vertex primitive variable used
			to specify the position of each instance.
			""",

			"layout:section", "Settings.Transforms",

		],

		"orientation" : [

			"description",
			"""
			The name of the per-vertex primitive variable used
			to specify the orientation of each instance. This
			must be provided as a quaternion : use an upstream
			Orientation node to convert from other representations
			before instancing.
			""",

			"userDefault", "orientation",
			"layout:section", "Settings.Transforms",

		],

		"scale" : [

			"description",
			"""
			The name of the per-vertex primitive variable used
			to specify the scale of each instance. Scale can be
			provided as a float for uniform scaling, or as a vector
			to define different scaling in each axis.
			""",

			"userDefault", "scale",
			"layout:section", "Settings.Transforms",

		],

		"attributes" : [

			"description",
			"""
			The names of per-vertex primitive variables to be
			turned into per-instance attributes. Names should
			be separated by spaces and can use Gaffer's
			standard wildcards.
			""",

			"layout:section", "Settings.Attributes",

		],

		"attributePrefix" : [

			"description",
			"""
			A prefix added to all per-instance attributes specified
			via the \"attributes\" plug.
			""",

			"userDefault", "user:",
			"layout:section", "Settings.Attributes",

		],

		"encapsulateInstanceGroups" : [

			"description",
			"""
			Converts each group of instances into a capsule, which won't
			be expanded until you Unencapsulate or render. When keeping
			these locations encapsulated, downstream nodes can't see the
			instance locations, which prevents editing but improves
			performance. This option should be preferred to a downstream
			Encapsulate node because it has the following benefits :

			- Substantially improved performance when the prototypes
			  define sets.
			- Fewer unnecessary updates during interactive rendering.
			""",
			"label", "Instance Groups",

			"layout:section", "Settings.Encapsulation",

		],

	}

)
