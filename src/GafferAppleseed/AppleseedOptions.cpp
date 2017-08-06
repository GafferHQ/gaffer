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

using namespace Imath;
using namespace GafferAppleseed;

IE_CORE_DEFINERUNTIMETYPED( AppleseedOptions );

AppleseedOptions::AppleseedOptions( const std::string &name )
	:	GafferScene::Options( name )
{
	Gaffer::CompoundDataPlug *options = optionsPlug();

	// main
	options->addOptionalMember( "as:cfg:generic_frame_renderer:passes", new IECore::IntData( 1 ), "renderPasses", Gaffer::Plug::Default, false );
	options->addOptionalMember( "as:cfg:sampling_mode", new IECore::StringData( "qmc" ), "sampler", Gaffer::Plug::Default, false );
	options->addOptionalMember( "as:cfg:uniform_pixel_renderer:samples", new IECore::IntData( 16 ), "aaSamples", Gaffer::Plug::Default, false );
	options->addOptionalMember( "as:cfg:lighting_engine", new IECore::StringData( "pt" ), "lightingEngine", Gaffer::Plug::Default, false );
	options->addOptionalMember( "as:mesh_file_format", new IECore::StringData( "binarymesh" ), "meshFileFormat", Gaffer::Plug::Default, false );
	options->addOptionalMember( "as:cfg:shading_engine:override_shading:mode", new IECore::StringData( "no_override" ), "shadingOverride", Gaffer::Plug::Default, false );

	// environment
	options->addOptionalMember( "as:environment_edf", new IECore::StringData(), "environmentEDF", Gaffer::Plug::Default, false );
	options->addOptionalMember( "as:environment_edf_background", new IECore::BoolData( false ), "environmentEDFBackground", Gaffer::Plug::Default, false );

	// path tracing
	options->addOptionalMember( "as:cfg:pt:enable_dl", new IECore::BoolData( true ), "ptDirectLighting", Gaffer::Plug::Default, false );
	options->addOptionalMember( "as:cfg:pt:enable_ibl", new IECore::BoolData( true ), "ptIBL", Gaffer::Plug::Default, false );
	options->addOptionalMember( "as:cfg:pt:enable_caustics", new IECore::BoolData( false ), "ptCaustics", Gaffer::Plug::Default, false );
	options->addOptionalMember( "as:cfg:pt:max_bounces", new IECore::IntData( -1 ), "ptMaxBounces", Gaffer::Plug::Default, false );
	options->addOptionalMember( "as:cfg:pt:max_diffuse_bounces", new IECore::IntData( -1 ), "ptMaxDiffuseBounces", Gaffer::Plug::Default, false );
	options->addOptionalMember( "as:cfg:pt:max_glossy_bounces", new IECore::IntData( -1 ), "ptMaxGlossyBounces", Gaffer::Plug::Default, false );
	options->addOptionalMember( "as:cfg:pt:max_specular_bounces", new IECore::IntData( -1 ), "ptMaxSpecularBounces", Gaffer::Plug::Default, false );
	options->addOptionalMember( "as:cfg:pt:dl_light_samples", new IECore::FloatData( 1.0f ), "ptLightingSamples", Gaffer::Plug::Default, false );
	options->addOptionalMember( "as:cfg:pt:ibl_env_samples", new IECore::FloatData( 1.0f ), "ptIBLSamples", Gaffer::Plug::Default, false );
	options->addOptionalMember( "as:cfg:pt:max_ray_intensity", new IECore::FloatData( 0.0f ), "ptMaxRayIntensity", Gaffer::Plug::Default, false );

	// sppm
	options->addOptionalMember( "as:cfg:sppm:photon_type", new IECore::StringData( "mono" ), "photonType", Gaffer::Plug::Default, false );
	options->addOptionalMember( "as:cfg:sppm:dl_type", new IECore::StringData( "rt" ), "sppmDirectLighting", Gaffer::Plug::Default, false );
	options->addOptionalMember( "as:cfg:sppm:enable_ibl", new IECore::BoolData( true ), "sppmIBL", Gaffer::Plug::Default, false );
	options->addOptionalMember( "as:cfg:sppm:enable_caustics", new IECore::BoolData( true ), "sppmCaustics", Gaffer::Plug::Default, false );
	options->addOptionalMember( "as:cfg:sppm:photon_tracing_max_bounces", new IECore::IntData( -1 ), "sppmPhotonMaxBounces", Gaffer::Plug::Default, false );
	options->addOptionalMember( "as:cfg:sppm:path_tracing_max_bounces", new IECore::IntData( -1 ), "sppmPathMaxBounces", Gaffer::Plug::Default, false );
	options->addOptionalMember( "as:cfg:sppm:light_photons_per_pass", new IECore::IntData( 1000000 ), "sppmLightPhotons", Gaffer::Plug::Default, false );
	options->addOptionalMember( "as:cfg:sppm:env_photons_per_pass", new IECore::IntData( 1000000 ), "sppmEnvPhotons", Gaffer::Plug::Default, false );
	options->addOptionalMember( "as:cfg:sppm:initial_radius", new IECore::FloatData( 1.0f ), "sppmInitialRadius", Gaffer::Plug::Default, false );
	options->addOptionalMember( "as:cfg:sppm:max_photons_per_estimate", new IECore::IntData( 100 ), "sppmMaxPhotons", Gaffer::Plug::Default, false );
	options->addOptionalMember( "as:cfg:sppm:alpha", new IECore::FloatData( 0.7f ), "sppmAlpha", Gaffer::Plug::Default, false );

	// system parameters
	options->addOptionalMember( "as:searchpath", new IECore::StringData( "" ), "searchPath", Gaffer::Plug::Default, false );
	options->addOptionalMember( "as:cfg:rendering_threads", new IECore::IntData( 0 ), "numThreads", Gaffer::Plug::Default, false );
	options->addOptionalMember( "as:cfg:progressive_frame_renderer:max_fps", new IECore::FloatData( 5.0f ), "interactiveRenderFps", Gaffer::Plug::Default, false );
	options->addOptionalMember( "as:cfg:texture_store:max_size", new IECore::IntData( 1024 * 1024 * 1024 ), "textureMem", Gaffer::Plug::Default, false );
	options->addOptionalMember( "as:cfg:generic_frame_renderer:tile_ordering", new IECore::StringData( "spiral" ), "tileOrdering", Gaffer::Plug::Default, false );

	// logging
	options->addOptionalMember( "as:log:level", new IECore::StringData( "info" ), "logLevel", Gaffer::Plug::Default, false );
	options->addOptionalMember( "as:log:filename", new IECore::StringData( "" ), "logFileName", Gaffer::Plug::Default, false );

	// currently being used by the ShaderBall preview,
	// not exposed in the options node UI,
	options->addOptionalMember( "as:cfg:progressive_frame_renderer:max_samples", new IECore::IntData( 0 ), "interactiveRenderMaxSamples", Gaffer::Plug::Default, false );
}
