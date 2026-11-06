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

import GafferArnold

for aov in [
	"beauty",
	"direct",
	"indirect",
	"emission",
	"background",
	"diffuse",
	"specular",
	"coat",
	"transmission",
	"sss",
	"volume",
	"albedo",
	"diffuse_direct",
	"diffuse_indirect",
	"diffuse_albedo",
	"specular_direct",
	"specular_indirect",
	"specular_albedo",
	"coat_direct",
	"coat_indirect",
	"coat_albedo",
	"transmission_direct",
	"transmission_indirect",
	"transmission_albedo",
	"sss_direct",
	"sss_indirect",
	"sss_albedo",
	"volume_direct",
	"volume_indirect",
	"volume_albedo",
	"motionvector",
	"normal",
	"depth",
] :

	label = aov.replace( "_", " " ).title().replace( " ", "_" )
	if aov == "beauty":
		data = "rgba"
	elif aov == "depth":
		data = "float Z"
	elif aov == "normal":
		data = "color N"
	else:
		data = "color " + aov

	if aov == "motionvector" :
		parameters = {
			"filter" : "closest"
		}
	else :
		parameters = {}

	if aov == "depth":
		parameters["layerName"] = "Z"

	if aov not in { "motionvector", "emission", "background" } :
		parameters["layerPerLightGroup"] = False

	interactiveParameters = parameters.copy()
	interactiveParameters.update(
		{
			"driverType" : "ClientDisplayDriver",
			"displayHost" : "localhost",
			"displayPort" : "${image:catalogue:port}",
			"remoteDisplayType" : "GafferScene::GafferDisplayDriver",
		}
	)

	GafferScene.Outputs.registerOutput(
		"Interactive/Arnold/" + label,
		IECoreScene.Output(
			aov,
			"ieDisplay",
			data,
			interactiveParameters
		)
	)

	GafferScene.Outputs.registerOutput(
		"Batch/Arnold/" + label,
		IECoreScene.Output(
			"${project:rootDirectory}/renders/${script:name}/${renderPass}/%s/%s.####.exr" % ( aov, aov ),
			"exr",
			data,
			parameters,
		)
	)

