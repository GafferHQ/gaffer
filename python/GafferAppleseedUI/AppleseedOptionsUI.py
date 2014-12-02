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

import Gaffer
import GafferScene
import GafferUI
import GafferAppleseed

def __mainSummary( plug ) :

	info = []
	if plug["renderPasses"]["enabled"].getValue() :
		info.append( "Passes %d" % plug["renderPasses"]["value"].getValue() )
	if plug["aaSamples"]["enabled"].getValue() :
		info.append( "AA Samples %d" % plug["aaSamples"]["value"].getValue() )
	if plug["forceAA"]["enabled"].getValue() and plug["forceAA"]["value"].getValue() :
		info.append( "Force AA" )
	if plug["decorrelatePixels"]["enabled"].getValue() and plug["decorrelatePixels"]["value"].getValue() :
		info.append( "Decorrelate Pixels" )
	if plug["lightingEngine"]["enabled"].getValue() :
		info.append( "Lighting Engine %s" % plug["lightingEngine"]["value"].getValue() )
	if plug["meshFileFormat"]["enabled"].getValue() :
		info.append( "Mesh File Format %s" % plug["meshFileFormat"]["value"].getValue() )

	return ", ".join( info )

def __environmentSummary( plug ) :

	info = []
	if plug["environmentEDF"]["enabled"].getValue() :
		info.append( "Environment %s" % plug["environmentEDF"]["value"].getValue() )
	if plug["environmentEDFBackground"]["enabled"].getValue() and plug["environmentEDFBackground"]["value"].getValue() :
		info.append( "Visible in Background" )

	return ", ".join( info )

def __drtSummary( plug ) :

	info = []
	if plug["drtIBL"]["enabled"].getValue() and plug["drtIBL"]["value"].getValue() :
		info.append( "IBL" )
	if plug["drtMaxBounces"]["enabled"].getValue() :
		info.append( "Max Bounces %d" % plug["drtMaxBounces"]["value"].getValue() )
	if plug["drtRRStartBounce"]["enabled"].getValue() :
		info.append( "Min Bounces %d" % plug["drtRRStartBounce"]["value"].getValue() )
	if plug["drtLighingSamples"]["enabled"].getValue() :
		info.append( "Lighting samples %d" % plug["drtLighingSamples"]["value"].getValue() )
	if plug["drtIBLSamples"]["enabled"].getValue() :
		info.append( "IBL samples %d" % plug["drtIBLSamples"]["value"].getValue() )

	return ", ".join( info )

def __ptSummary( plug ) :

	info = []
	if plug["ptDirectLighting"]["enabled"].getValue() and plug["ptDirectLighting"]["value"].getValue() :
		info.append( "Direct Lighting" )
	if plug["ptIBL"]["enabled"].getValue() and plug["ptIBL"]["value"].getValue() :
		info.append( "IBL" )
	if plug["ptCaustics"]["enabled"].getValue() and plug["ptCaustics"]["value"].getValue() :
		info.append( "Caustics" )
	if plug["ptMaxBounces"]["enabled"].getValue() :
		info.append( "Max Bounces %d" % plug["ptMaxBounces"]["value"].getValue() )
	if plug["ptRRStartBounce"]["enabled"].getValue() :
		info.append( "Min Bounces %d" % plug["ptRRStartBounce"]["value"].getValue() )
	if plug["ptNextEvent"]["enabled"].getValue() and plug["ptNextEvent"]["value"].getValue() :
		info.append( "Next Event Estimation" )
	if plug["ptLighingSamples"]["enabled"].getValue() :
		info.append( "Lighting Samples %d" % plug["ptLighingSamples"]["value"].getValue() )
	if plug["ptIBLSamples"]["enabled"].getValue() :
		info.append( "IBL Samples %d" % plug["ptIBLSamples"]["value"].getValue() )
	if plug["ptMaxRayIntensity"]["enabled"].getValue() :
		info.append( "Max Ray Intensity %f" % plug["ptMaxRayIntensity"]["value"].getValue() )

	return ", ".join( info )

def __sppmSummary( plug ) :

	info = []
	if plug["photonType"]["enabled"].getValue() :
		info.append( "Photon Type %s" % plug["photonType"]["value"].getValue() )
	if plug["sppmDirectLighing"]["enabled"].getValue() and plug["sppmDirectLighing"]["value"].getValue() != 'off' :
		info.append( "Direct Lighting %s" % plug["sppmDirectLighing"]["value"].getValue() )
	if plug["sppmIBL"]["enabled"].getValue() and plug["sppmIBL"]["value"].getValue() :
		info.append( "IBL" )
	if plug["sppmCaustics"]["enabled"].getValue() and plug["sppmCaustics"]["value"].getValue() :
		info.append( "Caustics" )
	if plug["sppmPhotonMaxBounces"]["enabled"].getValue() :
		info.append( "Max Photon Bounces %d" % plug["sppmPhotonMaxBounces"]["value"].getValue() )
	if plug["sppmPhotonRRStartBounce"]["enabled"].getValue() :
		info.append( "Min Photon Bounces %d" % plug["sppmPhotonRRStartBounce"]["value"].getValue() )
	if plug["sppmPathMaxBounces"]["enabled"].getValue() :
		info.append( "Max Path Bounces %d" % plug["sppmPathMaxBounces"]["value"].getValue() )
	if plug["sppmPathRRStartBounce"]["enabled"].getValue() :
		info.append( "Min Path Bounces %d" % plug["sppmPathRRStartBounce"]["value"].getValue() )
	if plug["sppmLightPhotons"]["enabled"].getValue() :
		info.append( "Light Photons %d" % plug["sppmLightPhotons"]["value"].getValue() )
	if plug["sppmEnvPhotons"]["enabled"].getValue() :
		info.append( "Environment Photons %d" % plug["sppmEnvPhotons"]["value"].getValue() )
	if plug["sppmInitialRadius"]["enabled"].getValue() :
		info.append( "Initial Radius %d" % plug["sppmInitialRadius"]["value"].getValue() )
	if plug["sppmMaxPhotons"]["enabled"].getValue() :
		info.append( "Max Photons %d" % plug["sppmMaxPhotons"]["value"].getValue() )
	if plug["sppmAlpha"]["enabled"].getValue() :
		info.append( "Alpha %f" % plug["sppmAlpha"]["value"].getValue() )

	return ", ".join( info )

def __systemSummary( plug ) :

	info = []
	if plug["searchPath"]["enabled"].getValue() :
		info.append( "Searchpath %s" % plug["searchPath"]["value"].getValue() )
	if plug["numThreads"]["enabled"].getValue() :
		info.append( "Threads %d" % plug["numThreads"]["value"].getValue() )
	if plug["textureMem"]["enabled"].getValue() :
		info.append( "Texture Mem %d MB" % plug["textureMem"]["value"].getValue() )
	if plug["tileOrdering"]["enabled"].getValue() :
		info.append( "Tile Ordering %s" % plug["tileOrdering"]["value"].getValue().capitalize() )

	return ", ".join( info )

GafferUI.PlugValueWidget.registerCreator(

	GafferAppleseed.AppleseedOptions,
	"options",
	GafferUI.SectionedCompoundDataPlugValueWidget,
	sections = (
		{
			"label" : "Main",
			"summary" : __mainSummary,
			"namesAndLabels" : (
				( "as:mesh_file_format", "Mesh File Format" ),
				( "as:cfg:generic_frame_renderer:passes", "Passes" ),
				( "as:cfg:uniform_pixel_renderer:samples", "AA Samples" ),
				( "as:cfg:uniform_pixel_renderer:force_antialiasing", "Force Antialiasing" ),
				( "as:cfg:uniform_pixel_renderer:decorrelate_pixels", "Decorrelate Pixels" ),
				( "as:cfg:lighting_engine", "Lighting Engine" ),
			),
		},
		{
			"label" : "Environment",
			"summary" : __environmentSummary,
			"namesAndLabels" : (
				( "as:environment_edf", "Environment Light" ),
				( "as:environment_edf_background", "Visible in Background" ),
			),
		},
		{
			"label" : "Distribution Ray Tracer",
			"summary" : __drtSummary,
			"namesAndLabels" : (
				( "as:cfg:drt:enable_ibl", "Image Based Lighting" ),
				( "as:cfg:drt:max_path_lenght", "Max Bounces" ),
				( "as:cfg:drt:rr_min_path_length", "RR Start Bounce" ),
				( "as:cfg:drt:dl_light_samples", "Direct Lighing Samples" ),
				( "as:cfg:drt:ibl_env_samples", "IBL Samples" ),
			),
		},
		{
			"label" : "Unidirectional Path Tracer",
			"summary" : __ptSummary,
			"namesAndLabels" : (
				( "as:cfg:pt:enable_dl", "Direct Lighting" ),
				( "as:cfg:pt:enable_ibl", "Image Based Lighting" ),
				( "as:cfg:pt:enable_caustics", "Caustics" ),
				( "as:cfg:pt:max_path_lenght", "Max Bounces" ),
				( "as:cfg:pt:rr_min_path_length", "RR Start Bounce" ),
				( "as:cfg:pt:next_event_estimation", "Next Event Estimation" ),
				( "as:cfg:pt:dl_light_samples", "Direct Lighing Samples" ),
				( "as:cfg:pt:ibl_env_samples", "IBL Samples" ),
				( "as:cfg:pt:max_ray_intensity", "Max Ray Intensity" ),
			),
		},
		{
			"label" : "SPPM",
			"summary" : __sppmSummary,
			"namesAndLabels" : (
				( "as:cfg:sppm:photon_type", "Photon Type" ),
				( "as:cfg:sppm:dl_type", "Direct Lighting" ),
				( "as:cfg:sppm:enable_ibl", "Image Based Lighting" ),
				( "as:cfg:sppm:enable_caustics", "Caustics" ),
				( "as:cfg:sppm:photon_tracing_max_path_length", "Max Photon Bounces" ),
				( "as:cfg:sppm:photon_tracing_rr_min_path_length", "Photon RR Start Bounce" ),
				( "as:cfg:sppm:path_tracing_max_path_length", "Max Path Bounces" ),
				( "as:cfg:sppm:path_tracing_rr_min_path_length", "Path RR Start Bounce" ),
				( "as:cfg:sppm:light_photons_per_pass", "Light Photons" ),
				( "as:cfg:sppm:env_photons_per_pass", "Environment Photons" ),
				( "as:cfg:sppm:initial_radius", "Initial Radius" ),
				( "as:cfg:sppm:max_photons_per_estimate", "Max Photons" ),
				( "as:cfg:sppm:alpha", "Alpha" ),
			),
		},
		{
			"label" : "System",
			"summary" : __systemSummary,
			"namesAndLabels" : (
				( "as:searchpath", "Searchpath" ),
				( "as:num_threads", "Threads" ),
				( "as:texture_mem", "Texture Cache Size" ),
				( "as:cfg:generic_frame_renderer:tile_ordering", "Tile Ordering" ),
			),
		},
	),
)

GafferUI.PlugValueWidget.registerCreator(
	GafferAppleseed.AppleseedOptions,
	"options.meshFileFormat.value",
	GafferUI.EnumPlugValueWidget,
	labelsAndValues = (
		( "BinaryMesh", "binarymesh" ),
		( "Obj", "obj" ),
	),
)

GafferUI.PlugValueWidget.registerCreator(
	GafferAppleseed.AppleseedOptions,
	"options.lightingEngine.value",
	GafferUI.EnumPlugValueWidget,
	labelsAndValues = (
		( "Distribution Ray Tracer", "drt" ),
		( "Unidirectional Path Tracer", "pt" ),
		( "SPPM", "sppm" ),
	),
)

GafferUI.PlugValueWidget.registerCreator(
	GafferAppleseed.AppleseedOptions,
	"options.environmentEDF.value",
	lambda plug : GafferUI.PathPlugValueWidget(
		plug,
		path = GafferScene.ScenePath( plug.node()["in"], plug.node().scriptNode().context(), "/" ),
	),
)

GafferUI.PlugValueWidget.registerCreator(
	GafferAppleseed.AppleseedOptions,
	"options.photonType.value",
	GafferUI.EnumPlugValueWidget,
	labelsAndValues = (
		( "Monochromatic", "mono" ),
		( "Polychromatic", "poly" ),
	),
)

GafferUI.PlugValueWidget.registerCreator(
	GafferAppleseed.AppleseedOptions,
	"options.sppmDirectLighing.value",
	GafferUI.EnumPlugValueWidget,
	labelsAndValues = (
		( "Ray Tracing", "rt" ),
		( "SPPM", "sppm" ),
		( "None", "off" ),
	),
)

GafferUI.PlugValueWidget.registerCreator(
	GafferAppleseed.AppleseedOptions,
	"options.tileOrdering.value",
	GafferUI.EnumPlugValueWidget,
	labelsAndValues = (
		( "Linear", "linear" ),
		( "Spiral", "spiral" ),
		( "Hilbert", "hilbert" ),
		( "Random", "random" ),
	),
)
