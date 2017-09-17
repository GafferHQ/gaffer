//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, John Haddon. All rights reserved.
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

#include "Gaffer/StringPlug.h"

#include "GafferDelight/DelightAttributes.h"

using namespace Gaffer;
using namespace GafferDelight;

IE_CORE_DEFINERUNTIMETYPED( DelightAttributes );

DelightAttributes::DelightAttributes( const std::string &name )
	:	GafferScene::Attributes( name )
{
	Gaffer::CompoundDataPlug *attributes = attributesPlug();

	// Visibility parameters

	attributes->addOptionalMember( "dl:visibility.camera", new IECore::BoolData( true ), "cameraVisibility", Gaffer::Plug::Default, false );
	attributes->addOptionalMember( "dl:visibility.diffuse", new IECore::BoolData( true ), "diffuseVisibility", Gaffer::Plug::Default, false );
	attributes->addOptionalMember( "dl:visibility.hair", new IECore::BoolData( true ), "hairVisibility", Gaffer::Plug::Default, false );
	attributes->addOptionalMember( "dl:visibility.reflection", new IECore::BoolData( true ), "reflectionVisibility", Gaffer::Plug::Default, false );
	attributes->addOptionalMember( "dl:visibility.refraction", new IECore::BoolData( true ), "refractionVisibility", Gaffer::Plug::Default, false );
	attributes->addOptionalMember( "dl:visibility.shadow", new IECore::BoolData( true ), "shadowVisibility", Gaffer::Plug::Default, false );
	attributes->addOptionalMember( "dl:visibility.specular", new IECore::BoolData( true ), "specularVisibility", Gaffer::Plug::Default, false );

	// Shading parameters

	attributes->addOptionalMember( "dl:matte", new IECore::BoolData( false ), "matte", Gaffer::Plug::Default, false );

}

DelightAttributes::~DelightAttributes()
{
}
