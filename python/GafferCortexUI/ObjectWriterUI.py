##########################################################################
#
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
#  Copyright (c) 2012-2014, Image Engine Design Inc. All rights reserved.
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
import GafferCortex
import GafferCortexUI

Gaffer.Metadata.registerNode(

	GafferCortex.ObjectWriter,

	"description",
	"""
	Saves objects to disk using the writers provided by
	the Cortex project.
	""",

	plugs = {

		"in" : [

			"description",
			"""
			The object to be written to disk.
			""",

			"plugValueWidget:type", "",

		],

		"fileName" : [

			"description",
			"""
			The name of the file to write.
			""",

			"nodule:type", "",
			"plugValueWidget:type", "GafferUI.FileSystemPathPlugValueWidget",
			"path:leaf", True,
			"path:bookmarks", "cortex",
			"fileSystemPath:extensions", " ".join( IECore.Reader.supportedExtensions() ),
			"fileSystemPath:extensionsLabel", "Show only supported files",

		],

		"parameters" : [

			"description",
			"""
			Additional parameters specific to the format of the
			file being written. These are created automatically
			based on the extension when the fileName is specified.
			""",

			"nodule:type", "",
			"plugValueWidget:type", "GafferCortexUI.ObjectWriterUI.__createParameterWidget",

		],

	}

)

def __createParameterWidget( plug ) :

	return GafferCortexUI.CompoundParameterValueWidget( plug.node().parameterHandler(), collapsible=False )
