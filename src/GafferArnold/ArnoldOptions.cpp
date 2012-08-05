//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2012, John Haddon. All rights reserved.
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
	:	GafferScene::Options( name, Gaffer::Plug::Default )
{
	GafferScene::ParameterListPlug *options = optionsPlug();
	
	// sampling parameters
	
	options->addParameter( "ai:AA_samples", new IECore::IntData( 3 ) );
	options->addParameter( "ai:GI_diffuse_samples", new IECore::IntData( 2 ) );
	options->addParameter( "ai:GI_glossy_samples", new IECore::IntData( 2 ) );
	options->addParameter( "ai:GI_refraction_samples", new IECore::IntData( 2 ) );

	// ignore parameters
	
	options->addParameter( "ai:ignore_textures", new IECore::BoolData( false ) );
	options->addParameter( "ai:ignore_shaders", new IECore::BoolData( false ) );
	options->addParameter( "ai:ignore_atmosphere", new IECore::BoolData( false ) );
	options->addParameter( "ai:ignore_lights", new IECore::BoolData( false ) );
	options->addParameter( "ai:ignore_shadows", new IECore::BoolData( false ) );
	options->addParameter( "ai:ignore_subdivision", new IECore::BoolData( false ) );
	options->addParameter( "ai:ignore_displacement", new IECore::BoolData( false ) );
	options->addParameter( "ai:ignore_bump", new IECore::BoolData( false ) );
	options->addParameter( "ai:ignore_motion_blur", new IECore::BoolData( false ) );
	options->addParameter( "ai:ignore_sss", new IECore::BoolData( false ) );

	// error colours
	
	options->addParameter( "ai:error_color_bad_texture", new IECore::Color3fData( Color3f( 1, 0, 0 ) ) );
	options->addParameter( "ai:error_color_bad_mesh", new IECore::Color3fData( Color3f( 0, 1, 0 ) ) );
	options->addParameter( "ai:error_color_bad_pixel", new IECore::Color3fData( Color3f( 0, 0, 1 ) ) );
	options->addParameter( "ai:error_color_bad_shader", new IECore::Color3fData( Color3f( 1, 0, 1 ) ) );
	
}

ArnoldOptions::~ArnoldOptions()
{
}
