##########################################################################
#
#  Copyright (c) 2018, Alex Fuller. All rights reserved.
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

import Gaffer
import GafferUI
import GafferCycles

def __deviceSummary( plug ) :

	# We don't have enough space to display the full device string, but the
	# `:00` device indices are kindof confusing. Just strip off the
	# indices so we're showing a list of device types.
	devices = set(
		d.partition( ":" )[0]
		for d in plug.getValue().split()
	)

	return " + ".join( devices )

def __optionSummary( plug, options ) :

	info = []

	for option in options :
		if plug[f"cycles:{option}"]["enabled"].getValue() :
			if Gaffer.Metadata.value( f"option:cycles:{option}", "plugValueWidget:type" ) == "GafferUI.PresetsPlugValueWidget" :
				value = Gaffer.NodeAlgo.currentPreset( plug[f"cycles:{option}"]["value"] )
			else :
				value = plug[f"cycles:{option}"]["value"].getValue()
				if isinstance( value, bool ) :
					value = "On" if value else "Off"

			info.append( "{} {}".format( Gaffer.Metadata.value( f"option:cycles:{option}", "label" ), value ) )

	return info

def __sessionSummary( plug ) :

	info = []

	if plug["cycles:device"]["enabled"].getValue() :
		info.append( __deviceSummary( plug["cycles:device"]["value"] ) )

	options = [
		"shadingsystem",
		"session:threads",
		"session:tile_size",
		"session:pixel_size",
		"session:time_limit",
	]
	info.extend( __optionSummary( plug, options ) )

	return ", ".join( info )

def __sceneSummary( plug ) :

	options = [
		"scene:bvh_layout",
		"scene:use_bvh_spatial_split",
		"scene:use_bvh_unaligned_nodes",
		"scene:num_bvh_time_steps",
		"scene:hair_subdivisions",
		"scene:hair_shape",
		"scene:texture_limit",
	]

	return ", ".join( __optionSummary( plug, options ) )

def __samplingSummary( plug ) :

	options = [
		"integrator:use_adaptive_sampling",
		"session:samples",
		"integrator:light_sampling_threshold",
		"integrator:adaptive_threshold",
		"integrator:adaptive_min_samples",
		"integrator:filter_glossy",
		"integrator:seed",
		"integrator:sample_clamp_direct",
		"integrator:sample_clamp_indirect",
		"integrator:start_sample"
	]

	return ", ".join( __optionSummary( plug, options ) )

def __pathGuidingSummary( plug ) :

	options = [
		"integrator:use_guiding",
		"integrator:use_surface_guiding",
		"integrator:use_volume_guiding",
		"integrator:guiding_training_samples",
	]

	return ", ".join( __optionSummary( plug, options ) )

def __rayDepthSummary( plug ) :

	options = [
		"integrator:min_bounce",
		"integrator:max_bounce",
		"integrator:transparent_min_bounce",
		"integrator:transparent_max_bounce",
	]

	info = __optionSummary( plug, options )

	for rayType in ( "diffuse", "glossy", "transmission", "volume" ) :
		childName = f"cycles:integrator:max_{rayType}_bounce"
		if plug[childName]["enabled"].getValue() :
			info.append(
				"{} {}".format( rayType.capitalize(), plug[childName]["value"].getValue() )
			)

	return ", ".join( info )

def __volumesSummary( plug ) :

	options = [
		"integrator:volume_ray_marching",
		"integrator:volume_max_steps",
		"integrator:volume_step_rate",
	]

	return ", ".join( __optionSummary( plug, options ) )

def __causticsSummary( plug ) :

	return ", ".join( __optionSummary( plug, [ "integrator:caustics_reflective", "integrator:caustics_refractive" ] ) )

def __subdivisionSummary( plug ) :

	return ", ".join( __optionSummary( plug, [ "dicing_camera" ] ) )

def __filmSummary( plug ) :

	options = [
		"film:exposure",
		"film:pass_alpha_threshold",
		"film:filter_type",
		"film:filter_width",
		"film:mist_start",
		"film:mist_depth",
		"film:mist_falloff",
		"film:cryptomatte_depth",
	]

	return ", ".join( __optionSummary( plug, options ) )

def __denoisingSummary( plug ) :

	info = []

	if plug["cycles:denoise_device"]["enabled"].getValue() :
		info.append( "Device {}".format( __deviceSummary( plug["cycles:denoise_device"]["value"] ) ) )

	options = [
		"integrator:denoiser_type",
		"integrator:denoise_start_sample",
		"integrator:use_denoise_pass_albedo",
		"integrator:use_denoise_pass_normal",
		"integrator:denoiser_prefilter",
	]
	info.extend( __optionSummary( plug, options ) )

	return ", ".join( info )

def __backgroundSummary( plug ) :

	options = [
		"integrator:ao_factor",
		"integrator:ao_distance",
		"background:use_shader",
		"background:transparent",
		"background:transparent_glass",
		"background:transparent_roughness_threshold",
	]
	info = __optionSummary( plug, options )

	for childName in ( "camera", "diffuse", "glossy", "transmission", "shadow", "scatter" ) :
		if plug[f"cycles:background:visibility:{childName}"]["enabled"].getValue() :
			info.append( childName.capitalize() + ( " On" if plug[f"cycles:background:visibility:{childName}"]["value"].getValue() else " Off" ) )

	return ", ".join( info )

def __logSummary( plug ) :

	return ", ".join( __optionSummary( plug, [ "log_level" ] ) )

## \todo The following metadata registrations may be better moved to `cyclesOptions.py`
# as function-based metadata that only imports IECoreCycles the first time they are called.
def __registerDevicePresets() :

	presetNames = [ "CPU" ]
	presetValues = [ "CPU" ]

	typeIndices = {}
	for device in GafferCycles.devices.values() :

		if device["type"].value == "CPU" :
			continue

		typeIndex = typeIndices.setdefault( device["type"], 0 )
		typeIndices[device["type"]] += 1

		presetNames.append( "{}/{}".format( device["type"], device["description"] ) )
		presetValues.append( "{}:{:02}".format( device["type"], typeIndex ) )

		presetNames.append( "{}/{} + CPU".format( device["type"], device["description"] ) )
		presetValues.append( "CPU {}:{:02}".format( device["type"], typeIndex ) )

	for deviceType, count in typeIndices.items() :

		if count <= 1 :
			continue

		presetNames.append( "{}/All".format( deviceType ) )
		presetValues.append( "{}:*".format( deviceType ) )

	Gaffer.Metadata.registerValue( "option:cycles:device", "presetNames", IECore.StringVectorData( presetNames ) )
	Gaffer.Metadata.registerValue( "option:cycles:device", "presetValues", IECore.StringVectorData( presetValues ) )

def __registerDenoiseDevicePresets() :

	presetNames = [ "Automatic" ]
	presetValues = [ "*" ]

	typeIndices = {}
	for device in GafferCycles.devices.values() :

		# Ignore devices that don't support any denoisers
		if device["denoisers"].value == 0 :
			continue

		if device["type"].value == "CPU" and "CPU" not in presetNames :
			presetNames.append( "CPU" )
			presetValues.append( "CPU" )
			continue

		typeIndex = typeIndices.setdefault( device["type"], 0 )
		typeIndices[device["type"]] += 1

		presetNames.append( "{}/{}".format( device["type"], device["description"] ) )
		presetValues.append( "{}:{:02}".format( device["type"], typeIndex ) )

	for deviceType, count in typeIndices.items() :

		if count <= 1 :
			continue

		presetNames.append( "{}/All".format( deviceType ) )
		presetValues.append( "{}:*".format( deviceType ) )

	Gaffer.Metadata.registerValue( "option:cycles:denoise_device", "presetNames", IECore.StringVectorData( presetNames ) )
	Gaffer.Metadata.registerValue( "option:cycles:denoise_device", "presetValues", IECore.StringVectorData( presetValues ) )

def __registerDenoiserPresets() :

	presetNames = []
	presetValues = []

	if GafferCycles.hasOptixDenoise :
		presetNames.append( "OptiX Denoiser" )
		presetValues.append( "optix" )

	if GafferCycles.hasOpenImageDenoise :
		presetNames.append( "Open Image Denoise" )
		presetValues.append( "openimagedenoise" )

	Gaffer.Metadata.registerValue( "option:cycles:integrator:denoiser_type", "presetNames", IECore.StringVectorData( presetNames ) )
	Gaffer.Metadata.registerValue( "option:cycles:integrator:denoiser_type", "presetValues", IECore.StringVectorData( presetValues ) )

def __registerPassPresets() :

	presetNames = []
	presetValues = []

	for _pass in sorted( GafferCycles.passes.keys() ) :
		presetNames.append( _pass.replace( "_", " " ).title() )
		presetValues.append( _pass )

	Gaffer.Metadata.registerValue( "option:cycles:film:display_pass", "presetNames", IECore.StringVectorData( presetNames ) )
	Gaffer.Metadata.registerValue( "option:cycles:film:display_pass", "presetValues", IECore.StringVectorData( presetValues ) )

Gaffer.Metadata.registerNode(

	GafferCycles.CyclesOptions,

	"description",
	"""
	Sets global scene options applicable to the Cycles
	renderer. Use the StandardOptions node to set
	global options applicable to all renderers.
	""",

	plugs = {

		# Sections

		"options" : {

			"layout:section:Session:summary" : __sessionSummary,
			"layout:section:Scene:summary" : __sceneSummary,
			"layout:section:Sampling:summary" : __samplingSummary,
			"layout:section:Path-Guiding:summary" : __pathGuidingSummary,
			"layout:section:Ray Depth:summary" : __rayDepthSummary,
			"layout:section:Volumes:summary" : __volumesSummary,
			"layout:section:Caustics:summary" : __causticsSummary,
			"layout:section:Subdivision:summary" : __subdivisionSummary,
			"layout:section:Film:summary" : __filmSummary,
			"layout:section:Denoising:summary" : __denoisingSummary,
			"layout:section:Background:summary" : __backgroundSummary,
			"layout:section:Log:summary" : __logSummary,

			"layout:customWidget:optionFilter:widgetType" : "GafferUI.PlugLayout.StandardFilterWidget",
			"layout:customWidget:optionFilter:index" : 0,

		},

	}
)

__registerDevicePresets()
__registerDenoiseDevicePresets()
__registerDenoiserPresets()
__registerPassPresets()

# Used by `startup/gui/cyclesViewerSettings.gfr`.
class ViewerDevicePlugValueWidget( GafferUI.PresetsPlugValueWidget ) :

	def __init__( self, plugs, **kw ) :

		GafferUI.PresetsPlugValueWidget.__init__( self, plugs, **kw )

		self.getPlug().node().plugSetSignal().connect( Gaffer.WeakMethod( self.__plugSet ) )

	def __plugSet( self, plug ) :

		if plug != self.getPlug() :
			return

		if plug.getValue() != "CPU" :
			# Switch to SVM shading to prevent CyclesRenderer falling back
			# to CPU shading due to OSL not being available.
			## \todo Change CyclesRenderer to fall back to SVM rather than
			# fall back to CPU.
			plug.parent()["shadingSystem"].setValue( "SVM" )

		# Cycles can't switch device after render has started, so we need to
		# force a restart (somewhat hackily). This does cause the SceneView to
		# create and destroy an OpenGL renderer unnecessarily, but it doesn't
		# actually get populated with a scene because that doesn't happen until
		# the viewport is drawn, and we've switched back to Cycles before that
		# happens.

		if plug.node()["renderer"]["name"].getValue() == "Cycles" :
			plug.node()["renderer"]["name"].setValue( "OpenGL" )
			plug.node()["renderer"]["name"].setValue( "Cycles" )
