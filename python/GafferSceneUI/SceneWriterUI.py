##########################################################################
#
#  Copyright (c) 2013-2014, Image Engine Design inc. All rights reserved.
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
import IECoreScene

import Gaffer
import GafferUI
import GafferScene

Gaffer.Metadata.registerNode(

	GafferScene.SceneWriter,

	"description",
	"""
	Writes scenes to cache files on disk. Gaffer's native file format is the .scc
	(SceneCache) format provided by Cortex, but other formats may be supported by
	registering a new implementation of Cortex's abstract SceneInterface.
	""",

	plugs = {

		"fileName" : [

			"description",
			"""
			The name of the file to be written. Note that unlike
			image sequences, many scene formats write animation into
			a single file, so using # characters to specify a frame
			number is generally not necessary.
			""",

			"path:leaf", True,
			"path:bookmarks", "sceneCache",
			"fileSystemPath:extensions", " ".join( IECoreScene.SceneInterface.supportedExtensions( IECore.IndexedIO.OpenMode.Write ) ),
			"fileSystemPath:extensionsLabel", "Show only cache files",

		],

		"in" : [

			"description",
			"""
			The scene to be written.
			""",

			"nodule:type", "GafferUI::StandardNodule",

		],

		"out" : [

			"description",
			"""
			A direct pass-through of the input scene.
			""",

		],

	}

)
