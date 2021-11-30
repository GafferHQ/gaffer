##########################################################################
#
#  Copyright (c) 2014, Esteban Tovagliari. All rights reserved.
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

import appleseed

import Gaffer
import GafferSceneUI
import GafferAppleseed

# Get the light and environments metadata dictionaries from appleseed
__modelMetadata = appleseed.Light.get_model_metadata()
__modelMetadata.update( appleseed.EnvironmentEDF.get_model_metadata() )
__modelMetadata.update( appleseed.EDF.get_model_metadata() )
__inputMetadata = appleseed.Light.get_input_metadata()
__inputMetadata.update( appleseed.EnvironmentEDF.get_input_metadata() )
__inputMetadata.update( appleseed.EDF.get_input_metadata() )

def __nodeDescription( node ) :

	model = node["__model"].getValue()

	try:
		return __modelMetadata[model]['help']
	except:
		return "Loads appleseed lights."

def __plugDescription( plug ) :

	model = plug.node()["__model"].getValue()
	param = plug.getName()

	# Special case for LatLong and MirrorBall environments.
	if param == "radiance_map" :

		param = "radiance"

	try:
		return __inputMetadata[model][param]['help']
	except:
		return param

def __plugLabel( plug ) :

	model = plug.node()["__model"].getValue()
	param = plug.getName()

	# Special case for LatLong and MirrorBall environments.
	if param == "radiance_map" :

		return "Radiance Map"

	try:
		return __inputMetadata[model][param]['label']
	except:
		return param

Gaffer.Metadata.registerNode(

	GafferAppleseed.AppleseedLight,

	"description", __nodeDescription,

	plugs = {

		"parameters.*" : [

			"description", __plugDescription,
			"label", __plugLabel,

		],

		"parameters.radiance_map" : [

			"plugValueWidget:type", "GafferUI.FileSystemPathPlugValueWidget",
			"path:leaf", True,
			"path:bookmarks", "image",

		],

	},

)

# Register parameters with LightEditor. Appleseed doesn't define any useful
# section metadata, so we add some ourselves. And we only add some lights to
# the menus in LightMenu.py, so skip the ones we don't add.

__sections = {
	"inner_angle" : "Shape",
	"outer_angle" : "Shape",
	"tilt_angle" : "Shape",
	"decay_start" : "Shape",
	"decay_exponent" : "Shape",
	"light_near_start" : "Shape",
	"cast_indirect_light" : "Contribution",
	"importance_multiplier" : "Sampling",
	"radiance_map" : "Map",
	"horizontal_shift" : "Map",
	"vertical_shift" : "Map",
	"sun_theta" : "Sky",
	"sun_phi" : "Sky",
	"turbidity" : "Sky",
	"turbidity_multiplier" : "Sky",
	"luminance_multiplier" : "Sky",
	"luminance_gamma" : "Sky",
	"saturation_multiplier" : "Sky",
	"horizon_shift" : "Sky",
	"ground_albedo" : "Sky",
}

for light in [
		"diffuse_edf",
		"spot_light",
		"point_light",
		"directional_light",
		"latlong_map_environment_edf",
		"hosek_environment_edf",
	] :

	for parameter in __inputMetadata[light].keys() :
		GafferSceneUI.LightEditor.registerParameter( "as:light", parameter, __sections.get( parameter ) )
