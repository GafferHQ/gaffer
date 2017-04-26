##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

import GafferScene
import GafferImageUI

GafferScene.Outputs.registerOutput(
	"Interactive/Beauty",
	IECore.Display(
		"beauty",
		"ieDisplay",
		"rgba",
		{
			"driverType" : "ClientDisplayDriver",
			"displayHost" : "localhost",
			"displayPort" : "${image:catalogue:port}",
			"remoteDisplayType" : "GafferImage::GafferDisplayDriver",
			"quantize" : IECore.IntVectorData( [ 0, 0, 0, 0 ] ),
		}
	)
)

GafferScene.Outputs.registerOutput(
	"Batch/Beauty",
	IECore.Display(
		"${project:rootDirectory}/renders/${script:name}/beauty/beauty.####.exr",
		"exr",
		"rgba",
		{
			"quantize" : IECore.IntVectorData( [ 0, 0, 0, 0 ] ),
		}
	)
)

# Publish the Catalogue port number as a context variable, so we can refer
# to it easily in output definitions.

def __scriptAdded( parent, script ) :

	if "imageCataloguePort" not in script["variables"] :
		portNumberPlug = script["variables"].addMember( "image:catalogue:port", 0, "imageCataloguePort" )
		Gaffer.MetadataAlgo.setReadOnly( portNumberPlug, True )
	else :
		portNumberPlug = script["variables"]["imageCataloguePort"]

	portNumberPlug["value"].setValue( GafferImage.Catalogue.displayDriverServer().portNumber() )

application.root()["scripts"].childAddedSignal().connect( __scriptAdded, scoped = False )

Gaffer.Metadata.registerValue( Gaffer.ScriptNode, "variables.imageCataloguePort", "plugValueWidget:type", "" )

# Store render catalogues in the project.

Gaffer.Metadata.registerValue( GafferImage.Catalogue, "directory", "userDefault", "${project:rootDirectory}/catalogues/${script:name}" )
