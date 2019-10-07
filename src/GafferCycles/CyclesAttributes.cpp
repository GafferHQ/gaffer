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

	attributes->addChild( new Gaffer::NameValuePlug( "ccl:visibility:camera", new IECore::BoolData( true ), false, "cameraVisibility" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "ccl:visibility:diffuse", new IECore::BoolData( true ), false, "diffuseVisibility" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "ccl:visibility:glossy", new IECore::BoolData( true ), false, "glossyVisibility" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "ccl:visibility:transmission", new IECore::BoolData( true ), false, "transmissionVisibility" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "ccl:visibility:shadow", new IECore::BoolData( true ), false, "shadowVisibility" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "ccl:visibility:scatter", new IECore::BoolData( true ), false, "scatterVisibility" ) );

	// Shading parameters

	attributes->addChild( new Gaffer::NameValuePlug( "ccl:use_holdout", new IECore::BoolData( false ), false, "useHoldout" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "ccl:is_shadow_catcher", new IECore::BoolData( false ), false, "isShadowCatcher" ) );

	// Subdivision parameters
	attributes->addChild( new Gaffer::NameValuePlug( "ccl:max_level", new IECore::IntData( 12 ), false, "maxLevel" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "ccl:dicing_rate", new IECore::FloatData( 1.0f ), false, "dicingScale" ) );

	// Color
	attributes->addChild( new Gaffer::NameValuePlug( "Cs", new IECore::Color3fData( Imath::Color3f( 0.0f ) ), false, "color" ) );

}

CyclesAttributes::~CyclesAttributes()
{
}
