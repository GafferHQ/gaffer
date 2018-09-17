//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2018, Alex Fuller. All rights reserved.
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

#include "GafferCycles/CyclesAttributes.h"

#include "Gaffer/StringPlug.h"

using namespace Gaffer;
using namespace GafferCycles;

IE_CORE_DEFINERUNTIMETYPED( CyclesAttributes );

CyclesAttributes::CyclesAttributes( const std::string &name )
	:	GafferScene::Attributes( name )
{
	Gaffer::CompoundDataPlug *attributes = attributesPlug();

	// Visibility parameters

	attributes->addOptionalMember( "ccl:visibility:camera", new IECore::BoolData( true ), "cameraVisibility", Gaffer::Plug::Default, false );
	attributes->addOptionalMember( "ccl:visibility:diffuse", new IECore::BoolData( true ), "diffuseVisibility", Gaffer::Plug::Default, false );
	attributes->addOptionalMember( "ccl:visibility:glossy", new IECore::BoolData( true ), "glossyVisibility", Gaffer::Plug::Default, false );
	attributes->addOptionalMember( "ccl:visibility:transmission", new IECore::BoolData( true ), "transmissionVisibility", Gaffer::Plug::Default, false );
	attributes->addOptionalMember( "ccl:visibility:shadow", new IECore::BoolData( true ), "shadowVisibility", Gaffer::Plug::Default, false );
	attributes->addOptionalMember( "ccl:visibility:scatter", new IECore::BoolData( true ), "scatterVisibility", Gaffer::Plug::Default, false );

	// Shading parameters

	attributes->addOptionalMember( "ccl:matte", new IECore::BoolData( false ), "matte", Gaffer::Plug::Default, false );
	attributes->addOptionalMember( "ccl:is_shadow_catcher", new IECore::BoolData( false ), "isShadowCatcher", Gaffer::Plug::Default, false );

	// Subdivision parameters
	attributes->addOptionalMember( "ccl:use_adaptive_subdivision", new IECore::BoolData( false ), "useAdaptiveSubdivision", Gaffer::Plug::Default, false );
	attributes->addOptionalMember( "ccl:dicing_rate", new IECore::FloatData( 1.0f ), "dicingScale", Gaffer::Plug::Default, false );

}

CyclesAttributes::~CyclesAttributes()
{
}
