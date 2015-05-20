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
	if plug["sampler"]["enabled"].getValue() :
		info.append( "Sampler %s" % plug["sampler"]["value"].getValue() )
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
	if plug["drtLightingSamples"]["enabled"].getValue() :
		info.append( "Lighting samples %d" % plug["drtLightingSamples"]["value"].getValue() )
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
	if plug["ptLightingSamples"]["enabled"].getValue() :
		info.append( "Lighting Samples %d" % plug["ptLightingSamples"]["value"].getValue() )
	if plug["ptIBLSamples"]["enabled"].getValue() :
		info.append( "IBL Samples %d" % plug["ptIBLSamples"]["value"].getValue() )
	if plug["ptMaxRayIntensity"]["enabled"].getValue() :
		info.append( "Max Ray Intensity %f" % plug["ptMaxRayIntensity"]["value"].getValue() )

	return ", ".join( info )

def __sppmSummary( plug ) :

	info = []
	if plug["photonType"]["enabled"].getValue() :
		info.append( "Photon Type %s" % plug["photonType"]["value"].getValue() )
	if plug["sppmDirectLighting"]["enabled"].getValue() and plug["sppmDirectLighting"]["value"].getValue() != 'off' :
		info.append( "Direct Lighting %s" % plug["sppmDirectLighting"]["value"].getValue() )
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
	if plug["interactiveRenderFps"]["enabled"].getValue() :
		info.append( "Interactive Render Fps %d" % plug["interactiveRenderFps"]["value"].getValue() )
	if plug["textureMem"]["enabled"].getValue() :
		info.append( "Texture Mem %d Kb" % plug["textureMem"]["value"].getValue() )
	if plug["tileOrdering"]["enabled"].getValue() :
		info.append( "Tile Ordering %s" % plug["tileOrdering"]["value"].getValue().capitalize() )

	return ", ".join( info )

Gaffer.Metadata.registerNode(

	GafferAppleseed.AppleseedOptions,

	plugs = {

		# Sections

		"options" : [

			"layout:section:Main:summary", __mainSummary,
			"layout:section:Environment:summary", __environmentSummary,
			"layout:section:Distribution Ray Tracer:summary", __drtSummary,
			"layout:section:Unidirectional Path Tracer:summary", __ptSummary,
			"layout:section:SPPM:summary", __sppmSummary,
			"layout:section:System:summary", __systemSummary,

		],

		# Main

		"options.renderPasses" : [

			"layout:section", "Main",
			"label", "Passes",

		],

		"options.sampler" : [

			"layout:section", "Main",

		],

		"options.sampler.value" : [

			"preset:Random", "rng",
			"preset:QMC", "qmc",

		],

		"options.aaSamples" : [

			"layout:section", "Main",
			"label", "AA Samples",

		],

		"options.forceAA" : [

			"layout:section", "Main",
			"label", "Force Antialiasing",

		],

		"options.decorrelatePixels" : [

			"layout:section", "Main",

		],

		"options.lightingEngine" : [

			"layout:section", "Main",

		],

		"options.lightingEngine.value" : [

			"preset:Distribution Ray Tracer", "drt",
			"preset:Unidirectional Path Tracer", "pt",
			"preset:SPPM", "sppm",

		],

		"options.meshFileFormat" : [

			"layout:section", "Main",

		],

		"options.meshFileFormat.value" : [

			"preset:BinaryMesh", "binarymesh",
			"preset:Obj", "obj",

		],

		# Environment

		"options.environmentEDF" : [

			"layout:section", "Environment",
			"label", "Environment Light",

		],

		"options.environmentEDFBackground" : [

			"layout:section", "Environment",
			"label", "Visible in Background",

		],

		# Distribution Ray Tracer

		"options.drtIBL" : [

			"layout:section", "Distribution Ray Tracer",
			"label", "Image Based Lighting",

		],

		"options.drtMaxBounces" : [

			"layout:section", "Distribution Ray Tracer",
			"label", "Max Bounces",

		],

		"options.drtRRStartBounce" : [

			"layout:section", "Distribution Ray Tracer",
			"label", "RR Start Bounce",

		],

		"options.drtLightingSamples" : [

			"layout:section", "Distribution Ray Tracer",
			"label", "Direct Lighting Samples",

		],

		"options.drtIBLSamples" : [

			"layout:section", "Distribution Ray Tracer",
			"label", "IBL Samples",

		],

		# Unidirectional Path Tracer

		"options.ptDirectLighting" : [

			"layout:section", "Unidirectional Path Tracer",
			"label", "Direct Lighting",

		],

		"options.ptIBL" : [

			"layout:section", "Unidirectional Path Tracer",
			"label", "Image Based Lighting",

		],

		"options.ptCaustics" : [

			"layout:section", "Unidirectional Path Tracer",
			"label", "Caustics",

		],

		"options.ptMaxBounces" : [

			"layout:section", "Unidirectional Path Tracer",
			"label", "Max Bounces",

		],

		"options.ptRRStartBounce" : [

			"layout:section", "Unidirectional Path Tracer",
			"label", "RR Start Bounce",

		],

		"options.ptNextEvent" : [

			"layout:section", "Unidirectional Path Tracer",
			"label", "Next Event Estimation",

		],

		"options.ptLightingSamples" : [

			"layout:section", "Unidirectional Path Tracer",
			"label", "Direct Lighting Samples",

		],

		"options.ptIBLSamples" : [

			"layout:section", "Unidirectional Path Tracer",
			"label", "IBL Samples",

		],

		"options.ptMaxRayIntensity" : [

			"layout:section", "Unidirectional Path Tracer",
			"label", "Max Ray Intensity",

		],

		# SPPM

		"options.photonType" : [

			"layout:section", "SPPM",
			"label", "Photon Type",

		],

		"options.photonType.value" : [

			"preset:Monochromatic", "mono",
			"preset:Polychromatic", "poly",

		],

		"options.sppmDirectLighting" : [

			"layout:section", "SPPM",
			"label", "Direct Lighting",

		],

		"options.sppmDirectLighting.value" : [

			"preset:Ray Tracing", "rt",
			"preset:SPPM", "sppm",
			"preset:None", "off",

		],

		"options.sppmIBL" : [

			"layout:section", "SPPM",
			"label", "Image Based Lighting",

		],

		"options.sppmCaustics" : [

			"layout:section", "SPPM",
			"label", "Caustics",

		],

		"options.sppmPhotonMaxBounces" : [

			"layout:section", "SPPM",
			"label", "Max Photon Bounces",

		],

		"options.sppmPhotonRRStartBounce" : [

			"layout:section", "SPPM",
			"label", "Photon RR Start Bounce",

		],

		"options.sppmPathMaxBounces" : [

			"layout:section", "SPPM",
			"label", "Max Path Bounces",

		],

		"options.sppmPathRRStartBounce" : [

			"layout:section", "SPPM",
			"label", "Path RR Start Bounce",

		],

		"options.sppmLightPhotons" : [

			"layout:section", "SPPM",
			"label", "Light Photons",

		],

		"options.sppmEnvPhotons" : [

			"layout:section", "SPPM",
			"label", "Environment Photons",

		],

		"options.sppmInitialRadius" : [

			"layout:section", "SPPM",
			"label", "Initial Radius",

		],

		"options.sppmMaxPhotons" : [

			"layout:section", "SPPM",
			"label", "Max Photons",

		],

		"options.sppmAlpha" : [

			"layout:section", "SPPM",
			"label", "Alpha",

		],

		# System

		"options.searchPath" : [

			"layout:section", "System",

		],

		"options.numThreads" : [

			"layout:section", "System",
			"label", "Threads",

		],

		"options.interactiveRenderFps" : [

			"layout:section", "System",

		],

		"options.textureMem" : [

			"layout:section", "System",
			"label", "Texture Cache Size",

		],

		"options.tileOrdering" : [

			"layout:section", "System",

		],

		"options.tileOrdering.value" : [

			"preset:Linear", "linear",
			"preset:Spiral", "spiral",
			"preset:Hilbert", "hilbert",
			"preset:Random", "random",

		],

	}

)

GafferUI.PlugValueWidget.registerCreator(
	GafferAppleseed.AppleseedOptions,
	"options.meshFileFormat.value",
	GafferUI.PresetsPlugValueWidget,
)

GafferUI.PlugValueWidget.registerCreator(
	GafferAppleseed.AppleseedOptions,
	"options.lightingEngine.value",
	GafferUI.PresetsPlugValueWidget,
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
	GafferUI.PresetsPlugValueWidget,
)

GafferUI.PlugValueWidget.registerCreator(
	GafferAppleseed.AppleseedOptions,
	"options.sppmDirectLighting.value",
	GafferUI.PresetsPlugValueWidget,
)

GafferUI.PlugValueWidget.registerCreator(
	GafferAppleseed.AppleseedOptions,
	"options.tileOrdering.value",
	GafferUI.PresetsPlugValueWidget,
)

GafferUI.PlugValueWidget.registerCreator(
	GafferAppleseed.AppleseedOptions,
	"options.sampler.value",
	GafferUI.PresetsPlugValueWidget,
)
