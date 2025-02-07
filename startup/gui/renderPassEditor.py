##########################################################################
#
#  Copyright (c) 2023, Cinesite VFX Ltd. All rights reserved.
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
import Gaffer
import GafferUI
import GafferSceneUI

GafferSceneUI.RenderPassEditor.registerOption( "*", "renderPass:enabled" )
GafferSceneUI.RenderPassEditor.registerOption( "*", "renderPass:type" )
GafferSceneUI.RenderPassEditor.registerOption( "*", "render:inclusions" )
GafferSceneUI.RenderPassEditor.registerOption( "*", "render:exclusions" )
GafferSceneUI.RenderPassEditor.registerOption( "*", "render:additionalLights" )
GafferSceneUI.RenderPassEditor.registerOption( "*", "render:cameraInclusions" )
GafferSceneUI.RenderPassEditor.registerOption( "*", "render:cameraExclusions" )
GafferSceneUI.RenderPassEditor.registerOption( "*", "render:matteInclusions" )
GafferSceneUI.RenderPassEditor.registerOption( "*", "render:matteExclusions" )

GafferSceneUI.RenderPassEditor.registerOption( "*", "render:defaultRenderer", "Render" )
GafferSceneUI.RenderPassEditor.registerOption( "*", "render:camera", "Render" )
GafferSceneUI.RenderPassEditor.registerOption( "*", "render:resolution", "Render" )
GafferSceneUI.RenderPassEditor.registerOption( "*", "render:resolutionMultiplier", "Render" )
GafferSceneUI.RenderPassEditor.registerOption( "*", "render:deformationBlur", "Render" )
GafferSceneUI.RenderPassEditor.registerOption( "*", "render:transformBlur", "Render" )
GafferSceneUI.RenderPassEditor.registerOption( "*", "render:shutter", "Render" )

if os.environ.get( "CYCLES_ROOT" ) and os.environ.get( "GAFFERCYCLES_HIDE_UI", "" ) != "1" :

	Gaffer.Metadata.registerValue( GafferSceneUI.RenderPassEditor.Settings, "tabGroup", "preset:Cycles", "Cycles" )
	Gaffer.Metadata.registerValue( GafferSceneUI.RenderPassEditor.Settings, "tabGroup", "userDefault", "Cycles" )

	GafferSceneUI.RenderPassEditor.registerOption( "Cycles", "cycles:session:samples", "Sampling" )
	GafferSceneUI.RenderPassEditor.registerOption( "Cycles", "cycles:integrator:use_adaptive_sampling", "Sampling" )
	GafferSceneUI.RenderPassEditor.registerOption( "Cycles", "cycles:integrator:adaptive_threshold", "Sampling" )
	GafferSceneUI.RenderPassEditor.registerOption( "Cycles", "cycles:integrator:use_guiding", "Sampling" )

	GafferSceneUI.RenderPassEditor.registerOption( "Cycles", "cycles:integrator:min_bounce", "Ray Depth" )
	GafferSceneUI.RenderPassEditor.registerOption( "Cycles", "cycles:integrator:max_bounce", "Ray Depth" )
	GafferSceneUI.RenderPassEditor.registerOption( "Cycles", "cycles:integrator:max_diffuse_bounce", "Ray Depth" )
	GafferSceneUI.RenderPassEditor.registerOption( "Cycles", "cycles:integrator:max_glossy_bounce", "Ray Depth" )
	GafferSceneUI.RenderPassEditor.registerOption( "Cycles", "cycles:integrator:max_transmission_bounce", "Ray Depth" )
	GafferSceneUI.RenderPassEditor.registerOption( "Cycles", "cycles:integrator:max_volume_bounce", "Ray Depth" )
	GafferSceneUI.RenderPassEditor.registerOption( "Cycles", "cycles:integrator:transparent_max_bounce", "Ray Depth" )

with IECore.IgnoredExceptions( ImportError ) :

	# This import appears unused, but it is intentional; it prevents us from
	# registering when 3Delight isn't available.
	import GafferDelight

	Gaffer.Metadata.registerValue( GafferSceneUI.RenderPassEditor.Settings, "tabGroup", "preset:3Delight", "3Delight" )
	Gaffer.Metadata.registerValue( GafferSceneUI.RenderPassEditor.Settings, "tabGroup", "userDefault", "3Delight" )

	GafferSceneUI.RenderPassEditor.registerOption( "3Delight", "dl:oversampling", "Sampling" )
	GafferSceneUI.RenderPassEditor.registerOption( "3Delight", "dl:quality.shadingsamples", "Sampling" )
	GafferSceneUI.RenderPassEditor.registerOption( "3Delight", "dl:quality.volumesamples", "Sampling" )

	GafferSceneUI.RenderPassEditor.registerOption( "3Delight", "dl:maximumraydepth.diffuse", "Ray Depth" )
	GafferSceneUI.RenderPassEditor.registerOption( "3Delight", "dl:maximumraydepth.hair", "Ray Depth" )
	GafferSceneUI.RenderPassEditor.registerOption( "3Delight", "dl:maximumraydepth.reflection", "Ray Depth" )
	GafferSceneUI.RenderPassEditor.registerOption( "3Delight", "dl:maximumraydepth.refraction", "Ray Depth" )
	GafferSceneUI.RenderPassEditor.registerOption( "3Delight", "dl:maximumraydepth.volume", "Ray Depth" )

with IECore.IgnoredExceptions( ImportError ) :

	# This import appears unused, but it is intentional; it prevents us from
	# registering when Arnold isn't available.
	import GafferArnold

	Gaffer.Metadata.registerValue( GafferSceneUI.RenderPassEditor.Settings, "tabGroup", "preset:Arnold", "Arnold" )
	Gaffer.Metadata.registerValue( GafferSceneUI.RenderPassEditor.Settings, "tabGroup", "userDefault", "Arnold" )

	GafferSceneUI.RenderPassEditor.registerOption( "Arnold", "ai:AA_samples", "Sampling" )
	GafferSceneUI.RenderPassEditor.registerOption( "Arnold", "ai:enable_adaptive_sampling", "Sampling", "Adaptive Sampling" )
	GafferSceneUI.RenderPassEditor.registerOption( "Arnold", "ai:AA_samples_max", "Sampling" )
	GafferSceneUI.RenderPassEditor.registerOption( "Arnold", "ai:AA_adaptive_threshold", "Sampling", "Adaptive Threshold" )

	GafferSceneUI.RenderPassEditor.registerOption( "Arnold", "ai:GI_diffuse_samples", "Sampling", "Diffuse" )
	GafferSceneUI.RenderPassEditor.registerOption( "Arnold", "ai:GI_specular_samples", "Sampling", "Specular" )
	GafferSceneUI.RenderPassEditor.registerOption( "Arnold", "ai:GI_transmission_samples", "Sampling", "Transmission" )
	GafferSceneUI.RenderPassEditor.registerOption( "Arnold", "ai:GI_sss_samples", "Sampling", "SSS" )
	GafferSceneUI.RenderPassEditor.registerOption( "Arnold", "ai:GI_volume_samples", "Sampling", "Volume" )
	GafferSceneUI.RenderPassEditor.registerOption( "Arnold", "ai:light_samples", "Sampling", "Light" )

	GafferSceneUI.RenderPassEditor.registerOption( "Arnold", "ai:GI_total_depth", "Ray Depth", "Total" )
	GafferSceneUI.RenderPassEditor.registerOption( "Arnold", "ai:GI_diffuse_depth", "Ray Depth", "Diffuse" )
	GafferSceneUI.RenderPassEditor.registerOption( "Arnold", "ai:GI_specular_depth", "Ray Depth", "Specular" )
	GafferSceneUI.RenderPassEditor.registerOption( "Arnold", "ai:GI_transmission_depth", "Ray Depth", "Transmission" )
	GafferSceneUI.RenderPassEditor.registerOption( "Arnold", "ai:GI_volume_depth", "Ray Depth", "Volume" )
	GafferSceneUI.RenderPassEditor.registerOption( "Arnold", "ai:auto_transparency_depth", "Ray Depth", "Transparency" )

# Register the default grouping function used to display render passes in a hierarchy.
# This groups render passes based on the first token in their name delimited by "_".
def __defaultPathGroupingFunction( renderPassName ) :

	return renderPassName.split( "_" )[0] if "_" in renderPassName else ""

GafferSceneUI.RenderPassEditor.registerPathGroupingFunction( __defaultPathGroupingFunction )

def __compoundEditorCreated( editor ) :

	applicationRoot = editor.scriptNode().ancestor( Gaffer.ApplicationRoot )
	if applicationRoot and applicationRoot.getName() == "gui" :

		Gaffer.Metadata.registerValue( editor.settings(), "layout:customWidget:renderPassSelector:widgetType", "GafferSceneUI.RenderPassEditor.RenderPassChooserWidget" )
		Gaffer.Metadata.registerValue( editor.settings(), "layout:customWidget:renderPassSelector:section", "Settings" )
		Gaffer.Metadata.registerValue( editor.settings(), "layout:customWidget:renderPassSelector:index", 0 )
		Gaffer.Metadata.registerValue( editor.settings(), "layout:customWidget:renderPassSelector:width", 185 )

GafferUI.CompoundEditor.instanceCreatedSignal().connect( __compoundEditorCreated )
