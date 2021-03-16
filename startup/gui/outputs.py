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
		"light_groups",
		"motionvector",
	] :

		label = aov.replace( "_", " " ).title().replace( " ", "_" )

		data = aov
		if data == "light_groups":
			data = "RGBA_*"

		if aov == "motionvector" :
			parameters = {
				"filter" : "closest"
			}
		else :
			parameters = {}

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
				"color " + data,
				interactiveParameters
			)
		)

		GafferScene.Outputs.registerOutput(
			"Batch/Arnold/" + label,
			IECoreScene.Output(
				"${project:rootDirectory}/renders/${script:name}/%s/%s.####.exr" % ( aov, aov ),
				"exr",
				"color " + data,
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
