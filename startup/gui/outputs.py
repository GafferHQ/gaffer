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
		"${project:rootDirectory}/renders/${script:name}/${renderPass}/beauty/beauty.####.exr",
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
				"${project:rootDirectory}/renders/${script:name}/${renderPass}/%s/%s.####.exr" % ( aov, aov ),
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

	# Should be kept up to date with
	# https://gitlab.com/3Delight/3delight-for-houdini/-/blob/master/ui/aov.cpp
	# See `contrib/scripts/3delightOutputs.py` in this repository for a helper script.

	GafferScene.Outputs.registerOutput(
		"Interactive/3Delight/Beauty_3Delight",
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
				"scalarformat" : "half",
				"colorprofile" : "linear",
				"filter" : "blackman-harris",
				"filtersize" : 3.0,
			}
		)
	)

	GafferScene.Outputs.registerOutput(
		"Batch/3Delight/Beauty_3Delight",
		IECoreScene.Output(
			"${project:rootDirectory}/renders/${script:name}/beauty/beauty.####.exr",
			"exr",
			"rgba",
			{
				"scalarformat" : "half",
				"colorprofile" : "linear",
				"filter" : "blackman-harris",
				"filtersize" : 3.0,
			}
		)
	)

	GafferScene.Outputs.registerOutput(
		"Batch/3Delight/Crypto/Surface_Shader_Cryptomatte_Header",
		IECoreScene.Output(
			"${project:rootDirectory}/renders/${script:name}/id.surfaceshader/id.surfaceshader.####.exr",
			"exr",
			"color builtin:id.surfaceshader",
			{
				"scalarformat" : "half",
				"sortkey" : 1,
				"filter" : "cryptomatteheader",
			}
		)
	)

	GafferScene.Outputs.registerOutput(
		"Batch/3Delight/Crypto/Surface_Shader_Cryptomatte_Layer0",
		IECoreScene.Output(
			"${project:rootDirectory}/renders/${script:name}/id.surfaceshader/id.surfaceshader.####.exr",
			"exr",
			"quad builtin:id.surfaceshader",
			{
				"scalarformat" : "float",
				"sortkey" : 2,
				"filter" : "cryptomattelayer0",
				"customdrivername" : "Batch/3Delight/Crypto/Surface_Shader_Cryptomatte_Header",
			}
		)
	)

	GafferScene.Outputs.registerOutput(
		"Batch/3Delight/Crypto/Surface_Shader_Cryptomatte_Layer2",
		IECoreScene.Output(
			"${project:rootDirectory}/renders/${script:name}/id.surfaceshader/id.surfaceshader.####.exr",
			"exr",
			"quad builtin:id.surfaceshader",
			{
				"scalarformat" : "float",
				"sortkey" : 3,
				"filter" : "cryptomattelayer2",
				"customdrivername" : "Batch/3Delight/Crypto/Surface_Shader_Cryptomatte_Header",
			}
		)
	)

	GafferScene.Outputs.registerOutput(
		"Batch/3Delight/Crypto/Geometry_Cryptomatte_Header",
		IECoreScene.Output(
			"${project:rootDirectory}/renders/${script:name}/id.geometry/id.geometry.####.exr",
			"exr",
			"color builtin:id.geometry",
			{
				"scalarformat" : "half",
				"sortkey" : 1,
				"filter" : "cryptomatteheader",
			}
		)
	)

	GafferScene.Outputs.registerOutput(
		"Batch/3Delight/Crypto/Geometry_Cryptomatte_Layer0",
		IECoreScene.Output(
			"${project:rootDirectory}/renders/${script:name}/id.geometry/id.geometry.####.exr",
			"exr",
			"quad builtin:id.geometry",
			{
				"scalarformat" : "float",
				"sortkey" : 2,
				"filter" : "cryptomattelayer0",
				"customdrivername" : "Batch/3Delight/Crypto/Geometry_Cryptomatte_Header",
			}
		)
	)

	GafferScene.Outputs.registerOutput(
		"Batch/3Delight/Crypto/Geometry_Cryptomatte_Layer2",
		IECoreScene.Output(
			"${project:rootDirectory}/renders/${script:name}/id.geometry/id.geometry.####.exr",
			"exr",
			"quad builtin:id.geometry",
			{
				"scalarformat" : "float",
				"sortkey" : 3,
				"filter" : "cryptomattelayer2",
				"customdrivername" : "Batch/3Delight/Crypto/Geometry_Cryptomatte_Header",
			}
		)
	)

	GafferScene.Outputs.registerOutput(
		"Batch/3Delight/Crypto/Scene_Path_Cryptomatte_Header",
		IECoreScene.Output(
			"${project:rootDirectory}/renders/${script:name}/id.scenepath/id.scenepath.####.exr",
			"exr",
			"color builtin:id.scenepath",
			{
				"scalarformat" : "half",
				"sortkey" : 1,
				"filter" : "cryptomatteheader",
			}
		)
	)

	GafferScene.Outputs.registerOutput(
		"Batch/3Delight/Crypto/Scene_Path_Cryptomatte_Layer0",
		IECoreScene.Output(
			"${project:rootDirectory}/renders/${script:name}/id.scenepath/id.scenepath.####.exr",
			"exr",
			"quad builtin:id.scenepath",
			{
				"scalarformat" : "float",
				"sortkey" : 2,
				"filter" : "cryptomattelayer0",
				"customdrivername" : "Batch/3Delight/Crypto/Scene_Path_Cryptomatte_Header",
			}
		)
	)

	GafferScene.Outputs.registerOutput(
		"Batch/3Delight/Crypto/Scene_Path_Cryptomatte_Layer2",
		IECoreScene.Output(
			"${project:rootDirectory}/renders/${script:name}/id.scenepath/id.scenepath.####.exr",
			"exr",
			"quad builtin:id.scenepath",
			{
				"scalarformat" : "float",
				"sortkey" : 3,
				"filter" : "cryptomattelayer2",
				"customdrivername" : "Batch/3Delight/Crypto/Scene_Path_Cryptomatte_Header",
			}
		)
	)

	for name, displayName, source, dataType in [
		( "Ci", "Ci", "shader", "color" ),
		( "Ci.direct", "Ci_(direct)", "shader", "color" ),
		( "Ci.indirect", "Ci_(indirect)", "shader", "color" ),
		( "diffuse", "Diffuse", "shader", "color" ),
		( "diffuse.direct", "Diffuse_(direct)", "shader", "color" ),
		( "diffuse.indirect", "Diffuse_(indirect)", "shader", "color" ),
		( "hair", "Hair_and_Fur", "shader", "color" ),
		( "subsurface", "Subsurface_Scattering", "shader", "color" ),
		( "reflection", "Reflection", "shader", "color" ),
		( "reflection.direct", "Reflection_(direct)", "shader", "color" ),
		( "reflection.indirect", "Reflection_(indirect)", "shader", "color" ),
		( "refraction", "Refraction", "shader", "color" ),
		( "volume", "Volume_Scattering", "shader", "color" ),
		( "volume.direct", "Volume_Scattering_(direct)", "shader", "color" ),
		( "volume.indirect", "Volume_Scattering_(indirect)", "shader", "color" ),
		( "incandescence", "Incandescence", "shader", "color" ),
		( "toon_base", "Toon_Base", "shader", "color" ),
		( "toon_diffuse", "Toon_Diffuse", "shader", "color" ),
		( "toon_specular", "Toon_Specular", "shader", "color" ),
		( "toon_matte", "Toon_Matte", "shader", "color" ),
		( "toon_tint", "Toon_Tint", "shader", "color" ),
		( "outlines", "Outlines", "shader", "quad" ),
		( "albedo", "Albedo", "shader", "color" ),
		( "z", "Z_(depth)", "builtin", "float" ),
		( "P.camera", "Camera_Space_Position", "builtin", "point" ),
		( "N.camera", "Camera_Space_Normal", "builtin", "point" ),
		( "P.world", "World_Space_Position", "builtin", "point" ),
		( "N.world", "World_Space_Normal", "builtin", "point" ),
		( "Pref", "Reference_Position", "attribute", "point" ),
		( "shadow_mask", "Shadow_Mask", "shader", "color" ),
		( "st", "UV", "attribute", "point" ),
		( "relighting_multiplier", "Relighting_Multiplier", "shader", "color" ),
		( "relighting_reference", "Relighting_Reference", "shader", "color" ),
		( "motionvector", "Motion_Vector", "builtin", "point" ),
		( "occlusion", "Ambient_Occlusion", "shader", "color" ),
	] :
		GafferScene.Outputs.registerOutput(
			"Interactive/3Delight/{}/{}".format( source.capitalize(), displayName ),
			IECoreScene.Output(
				name,
				"ieDisplay",
				"{} {}:{}".format( dataType, source, name ),
				{
					"driverType" : "ClientDisplayDriver",
					"displayHost" : "localhost",
					"displayPort" : "${image:catalogue:port}",
					"remoteDisplayType" : "GafferImage::GafferDisplayDriver",
					"scalarformat" : "half",
					"colorprofile" : "linear",
					"filter" : "blackman-harris",
					"filtersize" : 3.0,
					"customdrivername" : "",
					"lightgroup" : "",
				}
			)
		)

		GafferScene.Outputs.registerOutput(
			"Batch/3Delight/{}/{}".format( source.capitalize(), displayName ),
			IECoreScene.Output(
				"${project:rootDirectory}/renders/${script:name}/%s/%s.####.exr" % ( name, name ),
				"exr",
				"{} {}:{}".format( dataType, source, name ),
				{
					"scalarformat" : "half",
					"colorprofile" : "linear",
					"filter" : "blackman-harris",
					"filtersize" : 3.0,
					"customdrivername" : "",
					"lightgroup" : "",
				}
			)
		)

# Add standard cycles AOVs

if os.environ.get( "CYCLES_ROOT" ) and os.environ.get( "GAFFERCYCLES_HIDE_UI", "" ) != "1" :

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
					data = "lg lightgroup"
					label = "Light_Group"

				if data == "aov_color" :
					data = "color aov_color"

				if data == "aov_value" :
					data = "float aov_value"

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
						"${project:rootDirectory}/renders/${script:name}/${renderPass}/%s/%s.####.exr" % ( aov, aov ),
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
							"${project:rootDirectory}/renders/${script:name}/${renderPass}/%s/%s_denoised.####.exr" % ( aov, aov ),
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
							"${project:rootDirectory}/renders/${script:name}/${renderPass}/beauty/beauty_denoised.####.exr",
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
