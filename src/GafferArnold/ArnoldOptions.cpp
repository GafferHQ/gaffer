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

IE_CORE_DEFINERUNTIMETYPED( ArnoldOptions );

ArnoldOptions::ArnoldOptions( const std::string &name )
	:	GafferScene::Options( name )
{
	Gaffer::CompoundDataPlug *options = optionsPlug();

	// Rendering parameters

	options->addOptionalMember( "ai:bucket_size", new IECore::IntData( 64 ), "bucketSize", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:bucket_scanning", new IECore::StringData( "spiral" ), "bucketScanning", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:parallel_node_init", new IECore::BoolData( true ), "parallelNodeInit", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:threads", new IECore::IntData( 0 ), "threads", Gaffer::Plug::Default, false );

	// Sampling parameters

	options->addOptionalMember( "ai:AA_samples", new IECore::IntData( 3 ), "aaSamples", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:GI_diffuse_samples", new IECore::IntData( 2 ), "giDiffuseSamples", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:GI_specular_samples", new IECore::IntData( 2 ), "giSpecularSamples", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:GI_transmission_samples", new IECore::IntData( 2 ), "giTransmissionSamples", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:GI_sss_samples", new IECore::IntData( 2 ), "giSSSSamples", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:GI_volume_samples", new IECore::IntData( 2 ), "giVolumeSamples", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:AA_seed", new IECore::IntData( 1 ), "aaSeed", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:AA_sample_clamp", new IECore::FloatData( 10 ), "aaSampleClamp", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:AA_sample_clamp_affects_aovs", new IECore::BoolData( false ), "aaSampleClampAffectsAOVs", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:indirect_sample_clamp", new IECore::FloatData( 10 ), "indirectSampleClamp", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:low_light_threshold", new IECore::FloatData( 0.001 ), "lowLightThreshold", Gaffer::Plug::Default, false );

	// Adaptive sampling parameters
	options->addOptionalMember( "ai:enable_adaptive_sampling", new IECore::BoolData( false ), "enableAdaptiveSampling", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:AA_samples_max", new IECore::IntData( 0 ), "aaSamplesMax", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:AA_adaptive_threshold", new IECore::FloatData( 0.05 ), "aaAdaptiveThreshold", Gaffer::Plug::Default, false );

	// Ray depth parameters

	options->addOptionalMember( "ai:GI_total_depth", new IECore::IntData( 10 ), "giTotalDepth", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:GI_diffuse_depth", new IECore::IntData( 2 ), "giDiffuseDepth", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:GI_specular_depth", new IECore::IntData( 2 ), "giSpecularDepth", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:GI_transmission_depth", new IECore::IntData( 2 ), "giTransmissionDepth", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:GI_volume_depth", new IECore::IntData( 0 ), "giVolumeDepth", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:auto_transparency_depth", new IECore::IntData( 10 ), "autoTransparencyDepth", Gaffer::Plug::Default, false );

	// Subdivision

	options->addOptionalMember( "ai:max_subdivisions", new IECore::IntData(999), "maxSubdivisions", Gaffer::Plug::Default, false );

	// Texturing parameters

	options->addOptionalMember( "ai:texture_max_memory_MB", new IECore::FloatData( 2048 ), "textureMaxMemoryMB", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:texture_per_file_stats", new IECore::BoolData( false ), "texturePerFileStats", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:texture_max_sharpen", new IECore::FloatData( 1.5 ), "textureMaxSharpen", Gaffer::Plug::Default, false );

	// Ignore parameters

	options->addOptionalMember( "ai:ignore_textures", new IECore::BoolData( false ), "ignoreTextures", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:ignore_shaders", new IECore::BoolData( false ), "ignoreShaders", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:ignore_atmosphere", new IECore::BoolData( false ), "ignoreAtmosphere", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:ignore_lights", new IECore::BoolData( false ), "ignoreLights", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:ignore_shadows", new IECore::BoolData( false ), "ignoreShadows", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:ignore_subdivision", new IECore::BoolData( false ), "ignoreSubdivision", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:ignore_displacement", new IECore::BoolData( false ), "ignoreDisplacement", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:ignore_bump", new IECore::BoolData( false ), "ignoreBump", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:ignore_motion_blur", new IECore::BoolData( false ), "ignoreMotionBlur", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:ignore_sss", new IECore::BoolData( false ), "ignoreSSS", Gaffer::Plug::Default, false );

	// Searchpath parameters

	options->addOptionalMember( "ai:texture_searchpath", new IECore::StringData( "" ), "textureSearchPath", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:procedural_searchpath", new IECore::StringData( "" ), "proceduralSearchPath", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:plugin_searchpath", new IECore::StringData( "" ), "pluginSearchPath", Gaffer::Plug::Default, false );

	// Error handling

	options->addOptionalMember( "ai:abort_on_error", new IECore::BoolData( true ), "abortOnError", Gaffer::Plug::Default,  false);
	options->addOptionalMember( "ai:error_color_bad_texture", new IECore::Color3fData( Color3f( 1, 0, 0 ) ), "errorColorBadTexture", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:error_color_bad_pixel", new IECore::Color3fData( Color3f( 0, 0, 1 ) ), "errorColorBadPixel", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:error_color_bad_shader", new IECore::Color3fData( Color3f( 1, 0, 1 ) ), "errorColorBadShader", Gaffer::Plug::Default, false );

	// Logging

	options->addOptionalMember( "ai:log:filename", new IECore::StringData( "" ), "logFileName", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:log:max_warnings", new IECore::IntData( 100 ), "logMaxWarnings", Gaffer::Plug::Default, false );

	options->addOptionalMember( "ai:log:info", new IECore::BoolData( true ), "logInfo", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:log:warnings", new IECore::BoolData( true ), "logWarnings", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:log:errors", new IECore::BoolData( true ), "logErrors", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:log:debug", new IECore::BoolData( true ), "logDebug", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:log:ass_parse", new IECore::BoolData( true ), "logAssParse", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:log:plugins", new IECore::BoolData( true ), "logPlugins", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:log:progress", new IECore::BoolData( true ), "logProgress", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:log:nan", new IECore::BoolData( true ), "logNAN", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:log:timestamp", new IECore::BoolData( true ), "logTimestamp", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:log:stats", new IECore::BoolData( true ), "logStats", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:log:backtrace", new IECore::BoolData( true ), "logBacktrace", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:log:memory", new IECore::BoolData( true ), "logMemory", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:log:color", new IECore::BoolData( true ), "logColor", Gaffer::Plug::Default, false );

	options->addOptionalMember( "ai:console:info", new IECore::BoolData( false ), "consoleInfo", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:console:warnings", new IECore::BoolData( true ), "consoleWarnings", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:console:errors", new IECore::BoolData( true ), "consoleErrors", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:console:debug", new IECore::BoolData( false ), "consoleDebug", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:console:ass_parse", new IECore::BoolData( false ), "consoleAssParse", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:console:plugins", new IECore::BoolData( false ), "consolePlugins", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:console:progress", new IECore::BoolData( false ), "consoleProgress", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:console:nan", new IECore::BoolData( false ), "consoleNAN", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:console:timestamp", new IECore::BoolData( true ), "consoleTimestamp", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:console:stats", new IECore::BoolData( false ), "consoleStats", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:console:backtrace", new IECore::BoolData( true ), "consoleBacktrace", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:console:memory", new IECore::BoolData( true ), "consoleMemory", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:console:color", new IECore::BoolData( true ), "consoleColor", Gaffer::Plug::Default, false );

	// Statistics
	options->addOptionalMember( "ai:statisticsFileName", new IECore::StringData( "" ), "statisticsFileName", Gaffer::Plug::Default, false );

	// Licensing

	options->addOptionalMember( "ai:abort_on_license_fail", new IECore::BoolData( false ), "abortOnLicenseFail", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:skip_license_check", new IECore::BoolData( false ), "skipLicenseCheck", Gaffer::Plug::Default, false );

	// GPU

	options->addOptionalMember( "ai:render_device", new IECore::StringData( "CPU" ), "renderDevice", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:gpu_max_texture_resolution", new IECore::IntData( 0 ), "gpuMaxTextureResolution", Gaffer::Plug::Default, false );

}

ArnoldOptions::~ArnoldOptions()
{
}
