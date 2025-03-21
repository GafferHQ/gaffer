##########################################################################
#
#  Copyright (c) 2024, Cinesite VFX Ltd. All rights reserved.
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
import pathlib

import IECore

import Gaffer

# Pull all the option definitions out of RenderMan's `PRManOptions.args` file
# and register them using Gaffer's standard metadata conventions. This is then
# used to populate the RenderManOptions node and the RenderPassEditor etc.

with IECore.IgnoredExceptions( ImportError ) :

	import GafferRenderMan.ArgsFileAlgo

	rmanTree = pathlib.Path( os.environ["RMANTREE"] )

	GafferRenderMan.ArgsFileAlgo.registerMetadata(
		rmanTree / "lib" / "defaults" / "PRManOptions.args", "option:ri:",
		parametersToIgnore = {
			# Gaffer handles all of these in a renderer-agnostic manner.
			"Ri:Frame",
			"Ri:FrameAspectRatio",
			"Ri:ScreenWindow",
			"Ri:CropWindow",
			"Ri:FormatPixelAspectRatio",
			"Ri:FormatResolution",
			"Ri:Shutter",
			"hider:samplemotion",
			# These are for back-compatibility with a time before Gaffer
			# supported RenderMan, so we don't need them. The fewer settings
			# people have to wrestle with, the better.
			"statistics:displace_ratios",
			"statistics:filename",
			"statistics:level",
			"statistics:maxdispwarnings",
			"statistics:shaderprofile",
			"statistics:stylesheet",
			"statistics:texturestatslevel",
			"statistics:xmlfilename",
			"trace:incorrectCurveBias",
			"shade:chiangCompatibilityVersion",
			"shade:subsurfaceTypeDefaultFromVersion24",
			# https://rmanwiki-26.pixar.com/space/REN26/19661831/Sampling+Modes#Adaptive-Sampling-Error-Metrics
			# implies that this is only used by the obsolete adaptive metrics.
			"hider:darkfalloff",
			# These are XPU-only, and we don't yet support XPU. They also
			# sound somewhat fudgy.
			"interactive:displacementupdatemode",
			"interactive:displacementupdatedebug",
			# These just don't make much sense in Gaffer.
			"ribparse:varsubst",
			# These aren't documented, and will cause GafferRenderManUITest.DocumentationTest
			# to fail if we load them. We'll let them back in if we determine they are relevant
			# and can come up with a sensible documentation string of our own.
			"limits:gridsize",
			"limits:proceduralbakingclumpsize",
			"limits:ptexturemaxfiles",
			"limits:textureperthreadmemoryratio",
		}
	)

	# Omit obsolete adaptive metrics.

	for key in [ "presetNames", "presetValues" ] :
		Gaffer.Metadata.registerValue(
			"option:ri:hider:adaptivemetric", key,
			IECore.StringVectorData( [
				x for x in Gaffer.Metadata.value( "option:ri:hider:adaptivemetric", key )
				if "v22" not in x
			] )
		)

	# Omit pixel filters with negative lobes, since they are not compatible
	# with filter importance sampling (we don't expose weighted sampling).

	for key in [ "presetNames", "presetValues" ] :
		Gaffer.Metadata.registerValue(
			"option:ri:Ri:PixelFilterName", key,
			IECore.StringVectorData( [
				x for x in Gaffer.Metadata.value( "option:ri:Ri:PixelFilterName", key )
				if x.lower() not in { "catmull-rom", "separable-catmull-rom", "mitchell", "sinc", "bessel", "lanczos" }
			] )
		)

	# Move some stray options into a more logical section of the layout.

	for option in [
		"shade:debug",
		"shade:roughnessmollification",
		"shade:shadowBumpTerminator",
	] :
		Gaffer.Metadata.registerValue( f"option:ri:{option}", "layout:section", "Shading" )

	# Add options used to define custom LPE lobes. RenderMan does understand these, but they aren't
	# reported in `PRManOptions.args` for some reason, and don't actually have the
	# default values that are documented here :
	#
	#    https://rmanwiki-26.pixar.com/space/REN26/19661883/Light+Path+Expressions#Per-Lobe-LPEs
	#
	# Furthermore, the documented defaults are different from the defaults used in other bridge
	# products, which include additional lobes for compatibility with Lama shaders. The defaults
	# we use below are the superset of those from the documentation and RenderMan for Blender. This
	# reportedly also matches RenderMan for Maya.
	#
	# > Note : These must be kept in sync with the list in `src/IECoreRenderMan/Globals.cpp`, where
	# > we actually apply the "defaults".

	for name, lobe, defaultValue in [
		# RfB adds "diffuse,translucent,hair4,irradiance"
		( "lpe:diffuse2", "D2", "Diffuse,HairDiffuse,diffuse,translucent,hair4,irradiance" ),
		# RfB adds "subsurface"
		( "lpe:diffuse3", "D3", "Subsurface,subsurface" ),
		( "lpe:diffuse4", "D4", "" ),
		# RfB adds "specular,hair1"
		( "lpe:specular2", "S2", "Specular,HairSpecularR,specular,hair1" ),
		# RfB adds "hair3"
		( "lpe:specular3", "S3", "RoughSpecular,HairSpecularTRT,hair3" ),
		( "lpe:specular4", "S4", "Clearcoat" ),
		( "lpe:specular5", "S5", "Iridescence" ),
		( "lpe:specular6", "S6", "Fuzz,HairSpecularGLINTS" ),
		# RfB adds "hair2"
		( "lpe:specular7", "S7", "SingleScatter,HairSpecularTT,hair2" ),
		# RfB adds "specular"
		( "lpe:specular8", "S8", "Glass,specular" ),
		( "lpe:user2", "U2", "Albedo,DiffuseAlbedo,SubsurfaceAlbedo,HairAlbedo" ),
		# Not defined in RfB
		( "lpe:user3", "U3", "Position" ),
		# Not defined in RfB
		( "lpe:user4", "U4", "UserColor" ),
		( "lpe:user5", "U5", "" ),
		# Not defined in RfB, but required by the default denoising outputs.
		( "lpe:user6", "U6", "Normal,DiffuseNormal,HairTangent,SubsurfaceNormal,SpecularNormal,RoughSpecularNormal,SingleScatterNormal,FuzzNormal,IridescenceNormal,GlassNormal" ),
		( "lpe:user7", "U7", "" ),
		( "lpe:user8", "U8", "" ),
		# RfB goes up to 12, but if folks really need to indulge that much
		# they can use a CustomOptions node.
	] :

		Gaffer.Metadata.registerValue( f"option:ri:{name}", "defaultValue", defaultValue )
		Gaffer.Metadata.registerValue( f"option:ri:{name}", "description",
			f"""
			Defines the contents of the `{lobe}` custom LPE lobe.
			"""
		)
		Gaffer.Metadata.registerValue( f"option:ri:{name}", "label", lobe )
		Gaffer.Metadata.registerValue( f"option:ri:{name}", "layout:section", "Custom LPE Lobes" )

	# Add widgets and presets that are missing from the `.args` file.

	Gaffer.Metadata.registerValue( "option:ri:volume:aggregatespace", "plugValueWidget:type", "GafferUI.PresetsPlugValueWidget" )
	Gaffer.Metadata.registerValue( "option:ri:volume:aggregatespace", "presetNames", IECore.StringVectorData( [ "World", "Camera" ] ) )
	Gaffer.Metadata.registerValue( "option:ri:volume:aggregatespace", "presetValues", IECore.StringVectorData( [ "world", "camera" ] ) )

	# Add options used by GafferRenderMan._InteractiveDenoiserAdaptor. These don't mean
	# anything to RenderMan, but we still use the "ri:" prefix to keep things consistent
	# for the end user.
	## \todo Should we use a different prefix?

	Gaffer.Metadata.registerValue( "option:ri:interactiveDenoiser:enabled", "defaultValue", False )
	Gaffer.Metadata.registerValue( "option:ri:interactiveDenoiser:enabled", "description",
		"""
		Enables interactive denoising using RenderMan's `quicklyNoiseless` display driver. When on, all
		required denoising AOVs are added to the render automatically.
		"""
	)
	Gaffer.Metadata.registerValue( "option:ri:interactiveDenoiser:enabled", "label", "Enabled" )
	Gaffer.Metadata.registerValue( "option:ri:interactiveDenoiser:enabled", "layout:section", "Interactive Denoiser" )

	Gaffer.Metadata.registerValue( "option:ri:interactiveDenoiser:cheapPass", "defaultValue", True )
	Gaffer.Metadata.registerValue( "option:ri:interactiveDenoiser:cheapPass", "description",
		"""
		When on, the first pass will use a cheaper (slightly faster but lower
		quality) heuristic. This can be useful if rendering something that is
		converging very quickly and you want to prioritize getting a denoised
		result faster.
		"""
	)
	Gaffer.Metadata.registerValue( "option:ri:interactiveDenoiser:cheapPass", "label", "Cheap First Pass" )
	Gaffer.Metadata.registerValue( "option:ri:interactiveDenoiser:cheapPass", "layout:section", "Interactive Denoiser" )

	Gaffer.Metadata.registerValue( "option:ri:interactiveDenoiser:interval", "defaultValue", 4.0 )
	Gaffer.Metadata.registerValue( "option:ri:interactiveDenoiser:interval", "description",
		"""
		The time interval in between denoise runs (in seconds).
		"""
	)
	Gaffer.Metadata.registerValue( "option:ri:interactiveDenoiser:interval", "label", "Interval" )
	Gaffer.Metadata.registerValue( "option:ri:interactiveDenoiser:interval", "layout:section", "Interactive Denoiser" )

	Gaffer.Metadata.registerValue( "option:ri:interactiveDenoiser:minSamples", "defaultValue", 2 )
	Gaffer.Metadata.registerValue( "option:ri:interactiveDenoiser:minSamples", "description",
		"""
		The minimum number of average samples per bucket before the interactive denoiser runs for the first time.
		Changing this preference requires the render to be restarted for this option to be respected.
		"""
	)
	Gaffer.Metadata.registerValue( "option:ri:interactiveDenoiser:minSamples", "label", "Min Samples" )
	Gaffer.Metadata.registerValue( "option:ri:interactiveDenoiser:minSamples", "layout:section", "Interactive Denoiser" )

	# Add an option to allow checkpoint recovery - this is handled by `IECoreRenderMan::Session::Session()`
	# since it is not an official RenderMan option.

	Gaffer.Metadata.registerValue( "option:ri:checkpoint:recover", "label", "Checkpoint Recover" )
	Gaffer.Metadata.registerValue( "option:ri:checkpoint:recover", "description", "Enables recovery from a checkpoint created by a previous render." )
	Gaffer.Metadata.registerValue( "option:ri:checkpoint:recover", "defaultValue", 0 )
	Gaffer.Metadata.registerValue( "option:ri:checkpoint:recover", "layout:section", "Display" )
	Gaffer.Metadata.registerValue( "option:ri:checkpoint:recover", "plugValueWidget:type", "GafferUI.BoolPlugValueWidget" )
