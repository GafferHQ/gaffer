##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
#  Copyright (c) 2025, Image Engine Design Inc. All rights reserved.
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

import os

import IECore
import IECoreScene

import Gaffer
import GafferScene

# Add standard beauty and ID outputs that should be supported by all renderers.

GafferScene.Outputs.registerOutput(
	"Interactive/Beauty",
	IECoreScene.Output(
		"beauty",
		"ieDisplay",
		"rgba",
		{
			"catalogue:imageName" : "Image",
			"driverType" : "ClientDisplayDriver",
			"displayHost" : "localhost",
			"displayPort" : "${image:catalogue:port}",
			"remoteDisplayType" : "GafferScene::GafferDisplayDriver",
			"quantize" : IECore.IntVectorData( [ 0, 0, 0, 0 ] ),
		}
	)
)

GafferScene.Outputs.registerOutput(
	"Batch/Beauty",
	IECoreScene.Output(
		"${project:rootDirectory}/renders/${script:name}/${renderPass}/beauty/beauty.####.exr",
		"exr",
		"rgba",
		{
			"quantize" : IECore.IntVectorData( [ 0, 0, 0, 0 ] ),
		}
	)
)

GafferScene.Outputs.registerOutput(
	"Interactive/ID",
	IECoreScene.Output(
		"id",
		"ieDisplay",
		"float id",
		{
			"catalogue:imageName" : "Image",
			"driverType" : "ClientDisplayDriver",
			"displayHost" : "localhost",
			"displayPort" : "${image:catalogue:port}",
			"remoteDisplayType" : "GafferScene::GafferDisplayDriver",
			"filter" : "closest",
			"layerName" : "id",
			"updateInteractively" : True,
		}
	)
)

GafferScene.Outputs.registerOutput(
	"Batch/ID",
	IECoreScene.Output(
		"${project:rootDirectory}/renders/${script:name}/${renderPass}/id/id.####.exr",
		"exr",
		"float id",
		{
			"filter" : "closest",
			"layerName" : "id",
		}
	)
)

GafferScene.Outputs.registerOutput(
	"Interactive/InstanceID",
	IECoreScene.Output(
		"instanceID",
		"ieDisplay",
		"float instanceID",
		{
			"catalogue:imageName" : "Image",
			"driverType" : "ClientDisplayDriver",
			"displayHost" : "localhost",
			"displayPort" : "${image:catalogue:port}",
			"remoteDisplayType" : "GafferScene::GafferDisplayDriver",
			"filter" : "closest",
			"layerName" : "instanceID",
			"updateInteractively" : True,
		}
	)
)

GafferScene.Outputs.registerOutput(
	"Batch/InstanceID",
	IECoreScene.Output(
		"${project:rootDirectory}/renders/${script:name}/${renderPass}/instanceID/instanceID.####.exr",
		"exr",
		"float instanceID",
		{
			"filter" : "closest",
			"layerName" : "instanceID",
		}
	)
)

Gaffer.Metadata.registerValue( GafferScene.StandardOptions, "options.render:manifestFilePath.value", "userDefault", "${project:rootDirectory}/renders/${script:name}/${renderPass}/renderManifest/renderManifest.####.exr" )
