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

	// sampling parameters

	options->addOptionalMember( "ai:AA_samples", new IECore::IntData( 3 ), "aaSamples", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:GI_diffuse_samples", new IECore::IntData( 2 ), "giDiffuseSamples", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:GI_glossy_samples", new IECore::IntData( 2 ), "giGlossySamples", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:GI_refraction_samples", new IECore::IntData( 2 ), "giRefractionSamples", Gaffer::Plug::Default, false );

	// ignore parameters

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

	// searchpath parameters

	options->addOptionalMember( "ai:texture_searchpath", new IECore::StringData( "" ), "textureSearchPath", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:procedural_searchpath", new IECore::StringData( "" ), "proceduralSearchPath", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:shader_searchpath", new IECore::StringData( "" ), "shaderSearchPath", Gaffer::Plug::Default, false );

	// error colours

	options->addOptionalMember( "ai:error_color_bad_texture", new IECore::Color3fData( Color3f( 1, 0, 0 ) ), "errorColorBadTexture", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:error_color_bad_mesh", new IECore::Color3fData( Color3f( 0, 1, 0 ) ), "errorColorBadMesh", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:error_color_bad_pixel", new IECore::Color3fData( Color3f( 0, 0, 1 ) ), "errorColorBadPixel", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ai:error_color_bad_shader", new IECore::Color3fData( Color3f( 1, 0, 1 ) ), "errorColorBadShader", Gaffer::Plug::Default, false );

}

ArnoldOptions::~ArnoldOptions()
{
}
