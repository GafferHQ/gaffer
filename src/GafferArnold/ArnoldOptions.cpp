//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
//
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//
//      * Redistributions of source code must retain the above
//        copyright notice, this list of conditions and the following
//        disclaimer.
//
//      * Redistributions in binary form must reproduce the above
//        copyright notice, this list of conditions and the following
//        disclaimer in the documentation and/or other materials provided with
//        the distribution.
//
//      * Neither the name of John Haddon nor the names of
//        any other contributors to this software may be used to endorse or
//        promote products derived from this software without specific prior
//        written permission.
//
//  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
//  IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
//  THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
//  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
//  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
//  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
//  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
//  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
//  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
//  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
//  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
//
//////////////////////////////////////////////////////////////////////////

#include "GafferArnold/ArnoldOptions.h"

using namespace Imath;
using namespace GafferArnold;

GAFFER_NODE_DEFINE_TYPE( ArnoldOptions );

ArnoldOptions::ArnoldOptions( const std::string &name )
	:	GafferScene::Options( name )
{
	Gaffer::CompoundDataPlug *options = optionsPlug();

	// Rendering parameters

	options->addChild( new Gaffer::NameValuePlug( "ai:bucket_size", new IECore::IntData( 64 ), false, "bucketSize" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:bucket_scanning", new IECore::StringData( "spiral" ), false, "bucketScanning" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:parallel_node_init", new IECore::BoolData( true ), false, "parallelNodeInit" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:threads", new IECore::IntData( 0 ), false, "threads" ) );

	// Sampling parameters

	options->addChild( new Gaffer::NameValuePlug( "ai:AA_samples", new IECore::IntData( 3 ), false, "aaSamples" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:GI_diffuse_samples", new IECore::IntData( 2 ), false, "giDiffuseSamples" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:GI_specular_samples", new IECore::IntData( 2 ), false, "giSpecularSamples" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:GI_transmission_samples", new IECore::IntData( 2 ), false, "giTransmissionSamples" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:GI_sss_samples", new IECore::IntData( 2 ), false, "giSSSSamples" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:GI_volume_samples", new IECore::IntData( 2 ), false, "giVolumeSamples" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:AA_seed", new IECore::IntData( 1 ), false, "aaSeed" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:AA_sample_clamp", new IECore::FloatData( 10 ), false, "aaSampleClamp" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:AA_sample_clamp_affects_aovs", new IECore::BoolData( false ), false, "aaSampleClampAffectsAOVs" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:indirect_sample_clamp", new IECore::FloatData( 10 ), false, "indirectSampleClamp" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:low_light_threshold", new IECore::FloatData( 0.001 ), false, "lowLightThreshold" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:dielectric_priorities", new IECore::BoolData( true ), false, "dielectricPriorities" ) );

	// Adaptive sampling parameters

	options->addChild( new Gaffer::NameValuePlug( "ai:enable_adaptive_sampling", new IECore::BoolData( false ), false, "enableAdaptiveSampling" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:AA_samples_max", new IECore::IntData( 0 ), false, "aaSamplesMax" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:AA_adaptive_threshold", new IECore::FloatData( 0.05 ), false, "aaAdaptiveThreshold" ) );

	// Interactive rendering parameters

	options->addChild( new Gaffer::NameValuePlug( "ai:enable_progressive_render", new IECore::BoolData( true ), false, "enableProgressiveRender" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:progressive_min_AA_samples", new Gaffer::IntPlug( "value", Gaffer::Plug::In, -4, -10, 0 ), false, "progressiveMinAASamples" ) );

	// Ray depth parameters

	options->addChild( new Gaffer::NameValuePlug( "ai:GI_total_depth", new IECore::IntData( 10 ), false, "giTotalDepth" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:GI_diffuse_depth", new IECore::IntData( 2 ), false, "giDiffuseDepth" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:GI_specular_depth", new IECore::IntData( 2 ), false, "giSpecularDepth" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:GI_transmission_depth", new IECore::IntData( 2 ), false, "giTransmissionDepth" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:GI_volume_depth", new IECore::IntData( 0 ), false, "giVolumeDepth" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:auto_transparency_depth", new IECore::IntData( 10 ), false, "autoTransparencyDepth" ) );

	// Subdivision

	options->addChild( new Gaffer::NameValuePlug( "ai:max_subdivisions", new IECore::IntData(999), false, "maxSubdivisions" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:subdiv_dicing_camera", new IECore::StringData( "" ), false, "subdivDicingCamera" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:subdiv_frustum_culling", new IECore::BoolData( false ), false, "subdivFrustumCulling" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:subdiv_frustum_padding", new IECore::FloatData( 0.0f ), false, "subdivFrustumPadding" ) );

	// Texturing parameters

	options->addChild( new Gaffer::NameValuePlug( "ai:texture_max_memory_MB", new IECore::FloatData( 2048 ), false, "textureMaxMemoryMB" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:texture_per_file_stats", new IECore::BoolData( false ), false, "texturePerFileStats" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:texture_max_sharpen", new IECore::FloatData( 1.5 ), false, "textureMaxSharpen" ) );

	// Ignore parameters

	options->addChild( new Gaffer::NameValuePlug( "ai:ignore_textures", new IECore::BoolData( false ), false, "ignoreTextures" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:ignore_shaders", new IECore::BoolData( false ), false, "ignoreShaders" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:ignore_atmosphere", new IECore::BoolData( false ), false, "ignoreAtmosphere" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:ignore_lights", new IECore::BoolData( false ), false, "ignoreLights" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:ignore_shadows", new IECore::BoolData( false ), false, "ignoreShadows" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:ignore_subdivision", new IECore::BoolData( false ), false, "ignoreSubdivision" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:ignore_displacement", new IECore::BoolData( false ), false, "ignoreDisplacement" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:ignore_bump", new IECore::BoolData( false ), false, "ignoreBump" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:ignore_sss", new IECore::BoolData( false ), false, "ignoreSSS" ) );

	// Searchpath parameters

	options->addChild( new Gaffer::NameValuePlug( "ai:texture_searchpath", new IECore::StringData( "" ), false, "textureSearchPath" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:procedural_searchpath", new IECore::StringData( "" ), false, "proceduralSearchPath" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:plugin_searchpath", new IECore::StringData( "" ), false, "pluginSearchPath" ) );

	// Error handling

	options->addChild( new Gaffer::NameValuePlug( "ai:abort_on_error", new IECore::BoolData( true ), false, "abortOnError" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:error_color_bad_texture", new IECore::Color3fData( Color3f( 1, 0, 0 ) ), false, "errorColorBadTexture" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:error_color_bad_pixel", new IECore::Color3fData( Color3f( 0, 0, 1 ) ), false, "errorColorBadPixel" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:error_color_bad_shader", new IECore::Color3fData( Color3f( 1, 0, 1 ) ), false, "errorColorBadShader" ) );

	// Logging

	options->addChild( new Gaffer::NameValuePlug( "ai:log:filename", new IECore::StringData( "" ), false, "logFileName" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:log:max_warnings", new IECore::IntData( 100 ), false, "logMaxWarnings" ) );

	options->addChild( new Gaffer::NameValuePlug( "ai:log:info", new IECore::BoolData( true ), false, "logInfo" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:log:warnings", new IECore::BoolData( true ), false, "logWarnings" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:log:errors", new IECore::BoolData( true ), false, "logErrors" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:log:debug", new IECore::BoolData( true ), false, "logDebug" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:log:ass_parse", new IECore::BoolData( true ), false, "logAssParse" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:log:plugins", new IECore::BoolData( true ), false, "logPlugins" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:log:progress", new IECore::BoolData( true ), false, "logProgress" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:log:nan", new IECore::BoolData( true ), false, "logNAN" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:log:timestamp", new IECore::BoolData( true ), false, "logTimestamp" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:log:stats", new IECore::BoolData( true ), false, "logStats" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:log:backtrace", new IECore::BoolData( true ), false, "logBacktrace" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:log:memory", new IECore::BoolData( true ), false, "logMemory" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:log:color", new IECore::BoolData( true ), false, "logColor" ) );

	options->addChild( new Gaffer::NameValuePlug( "ai:console:info", new IECore::BoolData( false ), false, "consoleInfo" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:console:warnings", new IECore::BoolData( true ), false, "consoleWarnings" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:console:errors", new IECore::BoolData( true ), false, "consoleErrors" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:console:debug", new IECore::BoolData( false ), false, "consoleDebug" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:console:ass_parse", new IECore::BoolData( false ), false, "consoleAssParse" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:console:plugins", new IECore::BoolData( false ), false, "consolePlugins" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:console:progress", new IECore::BoolData( false ), false, "consoleProgress" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:console:nan", new IECore::BoolData( false ), false, "consoleNAN" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:console:timestamp", new IECore::BoolData( true ), false, "consoleTimestamp" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:console:stats", new IECore::BoolData( false ), false, "consoleStats" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:console:backtrace", new IECore::BoolData( true ), false, "consoleBacktrace" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:console:memory", new IECore::BoolData( true ), false, "consoleMemory" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:console:color", new IECore::BoolData( true ), false, "consoleColor" ) );

	// Statistics
	options->addChild( new Gaffer::NameValuePlug( "ai:statisticsFileName", new IECore::StringData( "" ), false, "statisticsFileName" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:profileFileName", new IECore::StringData( "" ), false, "profileFileName" ) );

	// Licensing

	options->addChild( new Gaffer::NameValuePlug( "ai:abort_on_license_fail", new IECore::BoolData( false ), false, "abortOnLicenseFail" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:skip_license_check", new IECore::BoolData( false ), false, "skipLicenseCheck" ) );

	// GPU

	options->addChild( new Gaffer::NameValuePlug( "ai:render_device", new IECore::StringData( "CPU" ), false, "renderDevice" ) );
	options->addChild( new Gaffer::NameValuePlug( "ai:gpu_max_texture_resolution", new IECore::IntData( 0 ), false, "gpuMaxTextureResolution" ) );

}

ArnoldOptions::~ArnoldOptions()
{
}
