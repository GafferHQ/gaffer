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

#include "GafferAppleseed/AppleseedAttributes.h"

using namespace Imath;
using namespace Gaffer;
using namespace GafferAppleseed;

IE_CORE_DEFINERUNTIMETYPED( AppleseedAttributes );

AppleseedAttributes::AppleseedAttributes( const std::string &name )
	:	GafferScene::Attributes( name )
{
	Gaffer::CompoundDataPlug *attributes = attributesPlug();

	// visibility parameters
	attributes->addOptionalMember( "as:visibility:camera", new IECore::BoolData( true ), "cameraVisibility", Gaffer::Plug::Default, false );
	attributes->addOptionalMember( "as:visibility:light", new IECore::BoolData( true ), "lightVisibility", Gaffer::Plug::Default, false );
	attributes->addOptionalMember( "as:visibility:shadow", new IECore::BoolData( true ), "shadowVisibility", Gaffer::Plug::Default, false );
	attributes->addOptionalMember( "as:visibility:transparency", new IECore::BoolData( true ), "transparencyVisibility", Gaffer::Plug::Default, false );
	attributes->addOptionalMember( "as:visibility:probe", new IECore::BoolData( true ), "probeVisibility", Gaffer::Plug::Default, false );
	attributes->addOptionalMember( "as:visibility:diffuse", new IECore::BoolData( true ), "diffuseVisibility", Gaffer::Plug::Default, false );
	attributes->addOptionalMember( "as:visibility:specular", new IECore::BoolData( true ), "specularVisibility", Gaffer::Plug::Default, false );
	attributes->addOptionalMember( "as:visibility:glossy", new IECore::BoolData( true ), "glossyVisibility", Gaffer::Plug::Default, false );

	// shading parameters
	attributes->addOptionalMember( "as:shading_samples", new IECore::IntData( 1.0f ), "shadingSamples", Gaffer::Plug::Default, false );

	// alpha map parameters
	attributes->addOptionalMember( "as:alpha_map", new IECore::StringData(), "alphaMap", Gaffer::Plug::Default, false );

	// photon target parameters
	attributes->addOptionalMember( "as:photon_target", new IECore::BoolData( false ), "photonTarget", Gaffer::Plug::Default, false );
}

AppleseedAttributes::~AppleseedAttributes()
{
}
