//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2014, Esteban Tovagliari. All rights reserved.
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

#include "GafferAppleseed/AppleseedOptions.h"

#include "Gaffer/FilePathPlug.h"

using namespace Imath;
using namespace GafferAppleseed;

GAFFER_NODE_DEFINE_TYPE( AppleseedOptions );

AppleseedOptions::AppleseedOptions( const std::string &name )
	:	GafferScene::Options( name )
{
	Gaffer::CompoundDataPlug *options = optionsPlug();

	// main
	options->addChild( new Gaffer::NameValuePlug( "as:cfg:passes", new IECore::IntData( 1 ), false, "renderPasses" ) );
	options->addChild( new Gaffer::NameValuePlug( "as:cfg:sampler", new IECore::StringData( "adaptive" ), false, "sampler" ) );
	options->addChild( new Gaffer::NameValuePlug( "as:cfg:adaptive_tile_renderer:min_samples", new IECore::IntData( 0 ), false, "minAASamples" ) );
	options->addChild( new Gaffer::NameValuePlug( "as:cfg:adaptive_tile_renderer:max_samples", new IECore::IntData( 32 ), false, "maxAASamples" ) );
	options->addChild( new Gaffer::NameValuePlug( "as:cfg:adaptive_tile_renderer:batch_size", new IECore::IntData( 16 ), false, "aaBatchSampleSize" ) );
	options->addChild( new Gaffer::NameValuePlug( "as:cfg:adaptive_tile_renderer:noise_threshold", new IECore::FloatData( 1.0f ), false, "aaNoiseThresh" ) );

	options->addChild( new Gaffer::NameValuePlug( "as:cfg:lighting_engine", new IECore::StringData( "pt" ), false, "lightingEngine" ) );
	options->addChild( new Gaffer::NameValuePlug( "as:cfg:shading_engine:override_shading:mode", new IECore::StringData( "no_override" ), false, "shadingOverride" ) );

	// environment
	options->addChild( new Gaffer::NameValuePlug( "as:environment_edf", new IECore::StringData(), false, "environmentEDF" ) );
	options->addChild( new Gaffer::NameValuePlug( "as:environment_edf_background", new IECore::BoolData( false ), false, "environmentEDFBackground" ) );

	// path tracing
	options->addChild( new Gaffer::NameValuePlug( "as:cfg:pt:enable_dl", new IECore::BoolData( true ), false, "ptDirectLighting" ) );
	options->addChild( new Gaffer::NameValuePlug( "as:cfg:pt:enable_ibl", new IECore::BoolData( true ), false, "ptIBL" ) );
	options->addChild( new Gaffer::NameValuePlug( "as:cfg:pt:enable_caustics", new IECore::BoolData( false ), false, "ptCaustics" ) );
	options->addChild( new Gaffer::NameValuePlug( "as:cfg:pt:max_bounces", new IECore::IntData( -1 ), false, "ptMaxBounces" ) );
	options->addChild( new Gaffer::NameValuePlug( "as:cfg:pt:max_diffuse_bounces", new IECore::IntData( -1 ), false, "ptMaxDiffuseBounces" ) );
	options->addChild( new Gaffer::NameValuePlug( "as:cfg:pt:max_glossy_bounces", new IECore::IntData( -1 ), false, "ptMaxGlossyBounces" ) );
	options->addChild( new Gaffer::NameValuePlug( "as:cfg:pt:max_specular_bounces", new IECore::IntData( -1 ), false, "ptMaxSpecularBounces" ) );
	options->addChild( new Gaffer::NameValuePlug( "as:cfg:pt:dl_light_samples", new IECore::FloatData( 1.0f ), false, "ptLightingSamples" ) );
	options->addChild( new Gaffer::NameValuePlug( "as:cfg:pt:ibl_env_samples", new IECore::FloatData( 1.0f ), false, "ptIBLSamples" ) );
	options->addChild( new Gaffer::NameValuePlug( "as:cfg:pt:max_ray_intensity", new IECore::FloatData( 0.0f ), false, "ptMaxRayIntensity" ) );
	options->addChild( new Gaffer::NameValuePlug( "as:cfg:pt:clamp_roughness", new IECore::BoolData( false ), false, "ptClampRoughness" ) );

	// sppm
	options->addChild( new Gaffer::NameValuePlug( "as:cfg:sppm:photon_type", new IECore::StringData( "mono" ), false, "photonType" ) );
	options->addChild( new Gaffer::NameValuePlug( "as:cfg:sppm:dl_type", new IECore::StringData( "rt" ), false, "sppmDirectLighting" ) );
	options->addChild( new Gaffer::NameValuePlug( "as:cfg:sppm:enable_ibl", new IECore::BoolData( true ), false, "sppmIBL" ) );
	options->addChild( new Gaffer::NameValuePlug( "as:cfg:sppm:enable_caustics", new IECore::BoolData( true ), false, "sppmCaustics" ) );
	options->addChild( new Gaffer::NameValuePlug( "as:cfg:sppm:photon_tracing_max_bounces", new IECore::IntData( -1 ), false, "sppmPhotonMaxBounces" ) );
	options->addChild( new Gaffer::NameValuePlug( "as:cfg:sppm:path_tracing_max_bounces", new IECore::IntData( -1 ), false, "sppmPathMaxBounces" ) );
	options->addChild( new Gaffer::NameValuePlug( "as:cfg:sppm:light_photons_per_pass", new IECore::IntData( 1000000 ), false, "sppmLightPhotons" ) );
	options->addChild( new Gaffer::NameValuePlug( "as:cfg:sppm:env_photons_per_pass", new IECore::IntData( 1000000 ), false, "sppmEnvPhotons" ) );
	options->addChild( new Gaffer::NameValuePlug( "as:cfg:sppm:initial_radius", new IECore::FloatData( 1.0f ), false, "sppmInitialRadius" ) );
	options->addChild( new Gaffer::NameValuePlug( "as:cfg:sppm:max_photons_per_estimate", new IECore::IntData( 100 ), false, "sppmMaxPhotons" ) );
	options->addChild( new Gaffer::NameValuePlug( "as:cfg:sppm:alpha", new IECore::FloatData( 0.7f ), false, "sppmAlpha" ) );

	// denoiser
	options->addChild( new Gaffer::NameValuePlug( "as:frame:denoiser", new IECore::StringData( "off" ), false, "denoiserMode" ) );
	options->addChild( new Gaffer::NameValuePlug( "as:frame:skip_denoised", new IECore::BoolData( true ), false, "denoiserSkipPixels" ) );
	options->addChild( new Gaffer::NameValuePlug( "as:frame:random_pixel_order", new IECore::BoolData( true ), false, "denoiserRandomPixelOrder" ) );
	options->addChild( new Gaffer::NameValuePlug( "as:frame:denoise_scales", new IECore::IntData( 3 ), false, "denoiserScales" ) );

	// system parameters
	options->addChild( new Gaffer::NameValuePlug( "as:searchpath", new IECore::StringData( "" ), false, "searchPath" ) );
	options->addChild( new Gaffer::NameValuePlug( "as:cfg:rendering_threads", new IECore::IntData( 0 ), false, "numThreads" ) );
	options->addChild( new Gaffer::NameValuePlug( "as:cfg:progressive_frame_renderer:max_fps", new IECore::FloatData( 5.0f ), false, "interactiveRenderFps" ) );
	options->addChild( new Gaffer::NameValuePlug( "as:cfg:texture_store:max_size", new IECore::IntData( 1024 ), false, "textureMem" ) );
	options->addChild( new Gaffer::NameValuePlug( "as:cfg:generic_frame_renderer:tile_ordering", new IECore::StringData( "spiral" ), false, "tileOrdering" ) );

	// logging
	options->addChild( new Gaffer::NameValuePlug( "as:log:level", new IECore::StringData( "info" ), false, "logLevel" ) );
	options->addChild( new Gaffer::NameValuePlug( "as:log:filename", new Gaffer::FilePathPlug(), false, "logFileName" ) );

	// currently being used by the ShaderBall preview,
	// not exposed in the options node UI,
	options->addChild( new Gaffer::NameValuePlug( "as:cfg:progressive_frame_renderer:max_samples", new IECore::IntData( 0 ), false, "interactiveRenderMaxSamples" ) );
}
