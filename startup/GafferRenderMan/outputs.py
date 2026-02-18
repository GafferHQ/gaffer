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

import GafferRenderMan

# Add standard RenderMan outputs.

if os.environ.get( "GAFFERRENDERMAN_HIDE_UI", "" ) != "1" :

	for name, data, accumulationRule in [
		( "albedo", "lpe nothruput;noinfinitecheck;noclamp;unoccluded;overwrite;C<.S'passthru'>*((U2L)|O)", "filter" ),
		( "albedo_mse", "lpe nothruput;noinfinitecheck;noclamp;unoccluded;overwrite;C<.S'passthru'>*((U2L)|O)", "mse" ),
		( "beauty", "rgba", "filter" ),
		( "matteID0", "color MatteID0", "filter" ),
		( "matteID1", "color MatteID1", "filter" ),
		( "matteID2", "color MatteID2", "filter" ),
		( "matteID3", "color MatteID3", "filter" ),
		( "matteID4", "color MatteID4", "filter" ),
		( "matteID5", "color MatteID5", "filter" ),
		( "matteID6", "color MatteID6", "filter" ),
		( "matteID7", "color MatteID7", "filter" ),
		( "mse", "rgb", "mse" ),
		( "cpuTime", "float cpuTime", "sum" ),
		( "depth", "float z", "zmin" ),
		( "emission", "lpe C[<L.>O]", "filter" ),
		( "diffuse", "lpe C(D[DS]*[LO])|[LO]", "filter" ),
		( "diffuse_mse", "lpe C(D[DS]*[LO])|[LO]", "mse" ),
		( "directDiffuse", "lpe C<RD>[<L.>O]", "filter" ),
		( "directSpecular", "lpe C<RS>[<L.>O]", "filter" ),
		( "indirectDiffuse", "lpe C<RD>.+[<L.>O]", "filter" ),
		( "indirectSpecular", "lpe C<RS>.+[<L.>O]", "filter" ),
		( "normal", "lpe nothruput;noinfinitecheck;noclamp;unoccluded;overwrite;CU6L", "filter" ),
		( "normal_mse", "lpe nothruput;noinfinitecheck;noclamp;unoccluded;overwrite;CU6L", "mse" ),
		( "sampleCount", "float sampleCount", "sum" ),
		( "specular", "lpe CS[DS]*[LO]", "filter" ),
		( "specular_mse", "lpe CS[DS]*[LO]", "mse" ),
		( "subsurface", "lpe C<TD>.*[<L.>O]", "filter" ),
		( "transmission", "lpe C<TS>.*[<L.>O]", "filter" ),
	] :

		label = IECore.CamelCase.toSpaced( name )
		parameters = {
			"ri:accumulationRule" : accumulationRule,
			"ri:relativePixelVariance" : 0.0,
		}

		if data == "float z" :
			parameters["layerName"] = "Z"
		elif data != "rgba" :
			parameters["layerName"] = name

		interactiveParameters = parameters.copy()
		interactiveParameters.update( {
				"driverType" : "ClientDisplayDriver",
				"displayHost" : "localhost",
				"displayPort" : "${image:catalogue:port}",
				"remoteDisplayType" : "GafferScene::GafferDisplayDriver",
		} )

		GafferScene.Outputs.registerOutput(
			"Interactive/RenderMan/" + label,
			IECoreScene.Output(
				name,
				"ieDisplay",
				data,
				interactiveParameters
			)
		)

		GafferScene.Outputs.registerOutput(
			"Batch/RenderMan/" + label,
			IECoreScene.Output(
				"${project:rootDirectory}/renders/${script:name}/${renderPass}/%s/%s.####.exr" % ( name, name ),
				"exr",
				data,
				parameters,
			)
		)

	# Add presets for accumulation rule

	Gaffer.Metadata.registerValue( GafferScene.Outputs, "outputs.*.parameters.ri_accumulationRule.value", "plugValueWidget:type", "GafferUI.PresetsPlugValueWidget" )
	for rule in [
		"filter", "average", "min", "max", "zmin", "zmax", "sum", "variance", "mse", "even", "odd"
	] :
		Gaffer.Metadata.registerValue( GafferScene.Outputs, "outputs.*.parameters.ri_accumulationRule.value", f"preset:{rule}", rule )
