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
	Instances an input scene onto the vertices of a target
	object, making one copy per vertex. Note that in Gaffer,
	the instances are not limited to being a single object,
	and each instance need not be identical. Instances can
	instead include entire hierarchies and can be varied
	from point to point, and individual instances may be
	modified downstream without affecting the others. Gaffer
	ensure's that where instances happen to be identical,
	they share memory, and performs automatic instancing at
	the object level when exporting to the renderer (this
	occurs for all nodes, not just the Instancer).

	Per-instance variation can be achieved using the
	${instancer:id} variable in the upstream instance graph.
	A common use case is to use this to randomise the index
	on a SceneSwitch node, to choose randomly between several
	instances, but it can be used to drive _any_ property of
	the upstream graph.
	""",

	plugs = {

		"parent" : [

			"description",
			"""
			The object on which to make the instances. This
			must have a "P" primitive variable specifying the
			location of each instance.
			"""

		],

		"name" : [

			"description",
			"""
			The name of the location the instances will be
			generated below. This will be parented directly
			under the parent location.
			"""

		],

		"instance" : [

			"description",
			"""
			The scene to be instanced. Use the ${instancer:id}
			variable in the upstream graph to create per-instance
			variations.
			""",

		],

	}

)

##########################################################################
# Widgets and nodules
##########################################################################

GafferUI.PlugValueWidget.registerCreator( GafferScene.Instancer, "instance", None )
