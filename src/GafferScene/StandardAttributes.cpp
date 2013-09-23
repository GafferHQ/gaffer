//////////////////////////////////////////////////////////////////////////
//  
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

#include "GafferScene/StandardAttributes.h"

using namespace GafferScene;

IE_CORE_DEFINERUNTIMETYPED( StandardAttributes );

StandardAttributes::StandardAttributes( const std::string &name )
	:	Attributes( name )
{
	Gaffer::CompoundDataPlug *attributes = attributesPlug();
	
	attributes->addOptionalMember( "gaffer:visibility", new IECore::BoolData( true ), "visibility", Gaffer::Plug::Default, false );
	attributes->addOptionalMember( "doubleSided", new IECore::BoolData( true ), "doubleSided", Gaffer::Plug::Default, false );
	
	// motion blur
	
	attributes->addOptionalMember( "gaffer:transformBlur", new IECore::BoolData( true ), "transformBlur", Gaffer::Plug::Default, false );
	attributes->addOptionalMember( "gaffer:transformBlurSegments", new Gaffer::IntPlug( "value", Gaffer::Plug::In, 1, 1 ), "transformBlurSegments", false );
	
	attributes->addOptionalMember( "gaffer:deformationBlur", new IECore::BoolData( true ), "deformationBlur", Gaffer::Plug::Default, false );
	attributes->addOptionalMember( "gaffer:deformationBlurSegments", new Gaffer::IntPlug( "value", Gaffer::Plug::In, 1, 1 ), "deformationBlurSegments", false );
	
}

StandardAttributes::~StandardAttributes()
{
}
