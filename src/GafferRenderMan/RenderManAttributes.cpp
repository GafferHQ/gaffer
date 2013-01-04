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

#include "GafferRenderMan/RenderManAttributes.h"

using namespace GafferRenderMan;

IE_CORE_DEFINERUNTIMETYPED( RenderManAttributes );

RenderManAttributes::RenderManAttributes( const std::string &name )
	:	GafferScene::Attributes( name, Gaffer::Plug::Default )
{
	Gaffer::CompoundDataPlug *attributes = attributesPlug();
	
	// visibility and hit mode parameters
	
	attributes->addOptionalMember( "ri:visibility:camera", new IECore::BoolData( true ), "cameraVisibility", false );
	attributes->addOptionalMember( "ri:shade:camerahitmode", new IECore::StringData( "shader" ), "cameraHitMode", false );
	
	attributes->addOptionalMember( "ri:visibility:transmission", new IECore::BoolData( false ), "transmissionVisibility", false );
	attributes->addOptionalMember( "ri:shade:transmissionhitmode", new IECore::StringData( "shader" ), "transmissionHitMode", false );
	
	attributes->addOptionalMember( "ri:visibility:diffuse", new IECore::BoolData( false ), "diffuseVisibility", false );
	attributes->addOptionalMember( "ri:shade:diffusehitmode", new IECore::StringData( "primitive" ), "diffuseHitMode", false );

	attributes->addOptionalMember( "ri:visibility:specular", new IECore::BoolData( false ), "specularVisibility", false );
	attributes->addOptionalMember( "ri:shade:specularhitmode", new IECore::StringData( "shader" ), "specularHitMode", false );
	
	attributes->addOptionalMember( "ri:visibility:photon", new IECore::BoolData( false ), "photonVisibility", false );
	attributes->addOptionalMember( "ri:shade:photonhitmode", new IECore::StringData( "shader" ), "photonHitMode", false );
	
}

RenderManAttributes::~RenderManAttributes()
{
}
