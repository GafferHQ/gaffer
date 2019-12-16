##########################################################################
#
#  Copyright (c) 2018, Alex Fuller. All rights reserved.
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
import IECoreScene

import Gaffer
import GafferScene
import GafferImage

# Add standard cycles AOVs

with IECore.IgnoredExceptions( ImportError ) :

	# If cycles isn't available for any reason, this will fail
	# and we won't add any unnecessary output definitions.
	import GafferCycles

	for aov in [
		"depth",
		"normal",
		"uv",
		"object_id",
		"material_id",
		"motion",
		"motion_weight",
		"render_time",
		"cryptomatte",
		"mist",
		"emission",
		"background",
		"ao",
		"shadow",
		"diffuse_direct",
		"diffuse_indirect",
		"diffuse_color",
		"glossy_direct",
		"glossy_indirect",
		"glossy_color",
		"transmission_direct",
		"transmission_indirect",
		"transmission_color",
		"subsurface_direct",
		"subsurface_indirect",
		"subsurface_color",
		"volume_direct",
		"volume_indirect",
		"cryptomatte_asset",
		"cryptomatte_object",
		"cryptomatte_material",
		"denoise_rgba",
		"denoise_normal",
		"denoise_albedo",
		"denoise_depth",
		"denoise_shadowing",
		"denoise_variance",
		"denoise_intensity",
		"denoise_clean",
		"aov_color",
		"aov_value",
		"lightgroups",
	] :

		label = aov.replace( "_", " " ).title().replace( " ", "_" )

		data = aov
		if data == "lightgroups":
			data = "lightgroup<8>"

		GafferScene.Outputs.registerOutput(
			"Interactive/Cycles/" + label,
			IECoreScene.Output(
				aov,
				"ieDisplay",
				data,
				{
					"driverType" : "ClientDisplayDriver",
					"displayHost" : "localhost",
					"displayPort" : "${image:catalogue:port}",
					"remoteDisplayType" : "GafferImage::GafferDisplayDriver",
				}
			)
		)

		GafferScene.Outputs.registerOutput(
			"Batch/Cycles/" + label,
			IECoreScene.Output(
				"${project:rootDirectory}/renders/${script:name}/%s/%s.####.exr" % ( aov, data ),
				"exr",
				data,
			)
		)
