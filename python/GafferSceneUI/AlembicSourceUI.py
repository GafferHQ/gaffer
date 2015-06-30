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

import IECore

import Gaffer
import GafferUI
import GafferScene

Gaffer.Metadata.registerNode(

	GafferScene.AlembicSource,

	"description",
	"""
	Loads Alembic caches. Please note that Gaffer requires
	a bounding box to be computable for every location in the
	scene. Alembic files can store such bounding boxes, but
	in practice they often don't. In this case Gaffer must perform
	a full scene traversal to compute the appropriate bounding box.
	It is recommended that if performance is a priority, bounding
	boxes should be stored explicitly in the Alembic cache, or the
	Cortex SceneCache (.scc) format should be used instead, since it
	always stores accurate bounds.
	""",

	plugs = {

		"fileName" : [

			"description",
			"""
			The path to the .abc file to load. Both
			older HDF5 and newer Ogawa caches are supported.
			""",

			"plugValueWidget:type", "GafferUI.FileSystemPathPlugValueWidget",
			"pathPlugValueWidget:leaf", True,
			"pathPlugValueWidget:valid", True,
			"pathPlugValueWidget:bookmarks", "sceneCache",
			"fileSystemPathPlugValueWidget:extensions", IECore.StringVectorData( [ "abc" ] ),

		],

		"refreshCount" : [

			"description",
			"""
			Can be incremented to invalidate Gaffer's memory
			cache and force a reload if the .abc file is
			changed on disk.
			""",

		],

	}

)

##########################################################################
# PlugValueWidgets
##########################################################################

GafferUI.PlugValueWidget.registerCreator(
	GafferScene.AlembicSource,
	"refreshCount",
	GafferUI.IncrementingPlugValueWidget,
	label = "Refresh",
	undoable = False
)
