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

import os

import IECore
import IECoreScene

import Gaffer
import GafferScene
import GafferImage

# Add standard beauty output that should be supported by
# all renderers.

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
			"remoteDisplayType" : "GafferImage::GafferDisplayDriver",
			"quantize" : IECore.IntVectorData( [ 0, 0, 0, 0 ] ),
		}
	)
)

GafferScene.Outputs.registerOutput(
	"Batch/Beauty",
	IECoreScene.Output(
		"${project:rootDirectory}/renders/${script:name}/beauty/beauty.####.exr",
		"exr",
		"rgba",
		{
			"quantize" : IECore.IntVectorData( [ 0, 0, 0, 0 ] ),
		}
	)
)

# Add standard AOVs as they are defined in the aiStandard and alSurface shaders

with IECore.IgnoredExceptions( ImportError ) :

	# If Arnold isn't available for any reason, this will fail
	# and we won't add any unnecessary output definitions.
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
	] :

		label = aov.replace( "_", " " ).title().replace( " ", "_" )
		data = "color " + aov if aov != "beauty" else "rgba"

		if aov == "motionvector" :
			parameters = {
				"filter" : "closest"
			}
		else :
			parameters = {}

		if aov not in { "motionvector", "emission", "background" } :
			parameters["layerPerLightGroup"] = False

		interactiveParameters = parameters.copy()
		interactiveParameters.update(
			{
				"driverType" : "ClientDisplayDriver",
				"displayHost" : "localhost",
				"displayPort" : "${image:catalogue:port}",
				"remoteDisplayType" : "GafferImage::GafferDisplayDriver",
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
				"${project:rootDirectory}/renders/${script:name}/%s/%s.####.exr" % ( aov, aov ),
				"exr",
				data,
				parameters,
			)
		)

# Add standard AOVs as they are defined in the 3Delight shaders

with IECore.IgnoredExceptions( ImportError ) :

	# If 3Delight isn't available for any reason, this will fail
	# and we won't add any unnecessary output definitions.
	import GafferDelight

	for aov in [
		"diffuse",
		"subsurface",
		"reflection",
		"refraction",
		"incandescence",
	] :

		label = aov.title()

		GafferScene.Outputs.registerOutput(
			"Interactive/3Delight/" + label,
			IECoreScene.Output(
				aov,
				"ieDisplay",
				"color " + aov,
				{
					"driverType" : "ClientDisplayDriver",
					"displayHost" : "localhost",
					"displayPort" : "${image:catalogue:port}",
					"remoteDisplayType" : "GafferImage::GafferDisplayDriver",
				}
			)
		)

		GafferScene.Outputs.registerOutput(
			"Batch/3Delight/" + label,
			IECoreScene.Output(
				"${project:rootDirectory}/renders/${script:name}/%s/%s.####.exr" % ( aov, aov ),
				"exr",
				"color " + aov,
			)
		)


# Add standard appleseed AOVs

if os.environ.get( "GAFFERAPPLESEED_HIDE_UI", "" ) != "1" :

	with IECore.IgnoredExceptions( ImportError ) :

		# If appleseed isn't available for any reason, this will fail
		# and we won't add any unnecessary output definitions.
		import GafferAppleseed

		for aov in [
			"diffuse",
			"glossy",
			"emission",
			"direct_diffuse",
			"indirect_diffuse",
			"direct_glossy",
			"indirect_glossy",
			"albedo",

			"npr_contour",
			"npr_shading",

			"depth",
			"normal",
			"position",
			"uv",

			"pixel_variation",
			"pixel_sample_count",
			"pixel_time",
			"invalid_samples"
		] :

			label = aov.replace( "_", " " ).title().replace( " ", "_" )
			aovModel = aov + "_aov"

			GafferScene.Outputs.registerOutput(
				"Interactive/Appleseed/" + label,
				IECoreScene.Output(
					aov,
					"ieDisplay",
					aovModel,
					{
						"driverType" : "ClientDisplayDriver",
						"displayHost" : "localhost",
						"displayPort" : "${image:catalogue:port}",
						"remoteDisplayType" : "GafferImage::GafferDisplayDriver",
					}
				)
			)

			GafferScene.Outputs.registerOutput(
				"Batch/Appleseed/" + label,
				IECoreScene.Output(
					"${project:rootDirectory}/renders/${script:name}/%s/%s.####.exr" % ( aov, aov ),
					"exr",
					aovModel
				)
			)

# Add standard cycles AOVs

with IECore.IgnoredExceptions( ImportError ) :

	# If cycles isn't available for any reason, this will fail
	# and we won't add any unnecessary output definitions.
	import GafferCycles

	lightPasses = [
		"emission",
		"background",
		"ao",
		"shadow",
		"diffuse_direct",
		"diffuse_indirect",
		"glossy_direct",
		"glossy_indirect",
		"transmission",
		"transmission_direct",
		"transmission_indirect",
		"volume_direct",
		"volume_indirect",
		"lightgroup",
	]

	dataPasses = [
		"depth",
		"position",
		"normal",
		"roughness",
		"uv",
		"object_id",
		"material_id",
		"motion",
		"motion_weight",
		"render_time",
		"cryptomatte_asset",
		"cryptomatte_object",
		"cryptomatte_material",
		"aov_color",
		"aov_value",
		"adaptive_aux_buffer",
		"sample_count",
		"diffuse_color",
		"glossy_color",
		"transmission_color",
		"mist",
		"denoising_normal",
		"denoising_albedo",

		"shadow_catcher",
		"shadow_catcher_sample_count",
		"shadow_catcher_matte",

		"bake_primitive",
		"bake_differential",
	]

	def __registerOutputs( aovs, halfFloat = False, denoise = False ) :
		for aov in aovs :

			label = aov.replace( "_", " " ).title().replace( " ", "_" )

			data = aov

			interactiveOutput = {
				"driverType" : "ClientDisplayDriver",
				"displayHost" : "localhost",
				"displayPort" : "${image:catalogue:port}",
				"remoteDisplayType" : "GafferImage::GafferDisplayDriver",
				"quantize" : IECore.IntVectorData( [ 0, 0, 0, 0 ] ),
			}
			batchOutput = {
				"quantize" : IECore.IntVectorData( [ 0, 0, 0, 0 ] ),
				"halfFloat" : halfFloat
			}

			if data == "lightgroup":
				if not GafferCycles.withLightGroups :
					continue
				data = "lg lightgroup"
				label = "Light_Group"

			if data == "aov_color" :
				data = "aovc aov_color"

			if data == "aov_value" :
				data = "aovv aov_value"

			if data.startswith( "cryptomatte" ) :
				data = data.replace( "_", " " )

			GafferScene.Outputs.registerOutput(
				"Interactive/Cycles/" + label,
				IECoreScene.Output(
					aov,
					"ieDisplay",
					data,
					interactiveOutput
				)
			)

			GafferScene.Outputs.registerOutput(
								"Batch/Cycles/" + label,
				IECoreScene.Output(
					"${project:rootDirectory}/renders/${script:name}/%s/%s.####.exr" % ( aov, aov ),
					"exr",
					data,
					batchOutput
				)
			)

			if denoise:
				interactiveOutput["denoise"] = True
				batchOutput["denoise"] = True

				# Denoised variants
				GafferScene.Outputs.registerOutput(
					"Interactive/Cycles/" + label + "_Denoised",
					IECoreScene.Output(
						aov + "_denoised",
						"ieDisplay",
						data,
						interactiveOutput
					)
				)

				GafferScene.Outputs.registerOutput(
					"Batch/Cycles/" + label + "_Denoised",
					IECoreScene.Output(
						"${project:rootDirectory}/renders/${script:name}/%s/%s_denoised.####.exr" % ( aov, aov ),
						"exr",
						data,
						batchOutput
					)
				)


				GafferScene.Outputs.registerOutput(
					"Interactive/Cycles/Beauty_Denoised",
					IECoreScene.Output(
						"beauty_denoised",
						"ieDisplay",
						"rgba",
						{
							"driverType" : "ClientDisplayDriver",
							"displayHost" : "localhost",
							"displayPort" : "${image:catalogue:port}",
							"remoteDisplayType" : "GafferImage::GafferDisplayDriver",
							"quantize" : IECore.IntVectorData( [ 0, 0, 0, 0 ] ),
							"denoise" : True
						}
					)
				)

				GafferScene.Outputs.registerOutput(
					"Batch/Cycles/Beauty_Denoised",
					IECoreScene.Output(
						"${project:rootDirectory}/renders/${script:name}/beauty/beauty_denoised.####.exr",
						"exr",
						"rgba",
						{
							"quantize" : IECore.IntVectorData( [ 0, 0, 0, 0 ] ),
							"denoise" : True,
							"halfFloat" : True
						}
					)
				)

	__registerOutputs( lightPasses, True )
	__registerOutputs( dataPasses )

# Publish the Catalogue port number as a context variable, so we can refer
# to it easily in output definitions.

def __scriptAdded( parent, script ) :

	if "imageCataloguePort" not in script["variables"] :
		portNumberPlug = Gaffer.NameValuePlug( "image:catalogue:port", 0, "imageCataloguePort", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		script["variables"].addChild( portNumberPlug )
		Gaffer.MetadataAlgo.setReadOnly( portNumberPlug, True )
	else :
		portNumberPlug = script["variables"]["imageCataloguePort"]

	portNumberPlug["value"].setValue( GafferImage.Catalogue.displayDriverServer().portNumber() )

application.root()["scripts"].childAddedSignal().connect( __scriptAdded, scoped = False )

Gaffer.Metadata.registerValue( Gaffer.ScriptNode, "variables.imageCataloguePort", "plugValueWidget:type", "" )

# Store render catalogues in the project.

Gaffer.Metadata.registerValue( GafferImage.Catalogue, "directory", "userDefault", "${project:rootDirectory}/catalogues/${script:name}" )
