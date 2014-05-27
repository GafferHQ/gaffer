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

#include "GafferScene/StandardOptions.h"

using namespace Gaffer;
using namespace GafferScene;

IE_CORE_DEFINERUNTIMETYPED( StandardOptions );

StandardOptions::StandardOptions( const std::string &name )
	:	Options( name )
{
	CompoundDataPlug *options = optionsPlug();
	
	// camera
	
	options->addOptionalMember( "render:camera", new IECore::StringData(), "renderCamera", Plug::Default, false );
	options->addOptionalMember( "render:resolution", new IECore::V2iData( Imath::V2i( 1024, 778 ) ), "renderResolution", Plug::Default, false );
	options->addOptionalMember( "render:cropWindow", new IECore::Box2fData( Imath::Box2f( Imath::V2f( 0 ), Imath::V2f( 1 ) ) ), "renderCropWindow", Plug::Default, false );

	// motion blur
	
	options->addOptionalMember( "render:cameraBlur", new IECore::BoolData( false ), "cameraBlur", Gaffer::Plug::Default, false );
	options->addOptionalMember( "render:transformBlur", new IECore::BoolData( false ), "transformBlur", Gaffer::Plug::Default, false );
	options->addOptionalMember( "render:deformationBlur", new IECore::BoolData( false ), "deformationBlur", Gaffer::Plug::Default, false );
	options->addOptionalMember( "render:shutter", new IECore::V2fData( Imath::V2f( -0.25, 0.25 ) ), "shutter", Gaffer::Plug::Default, false );

}

StandardOptions::~StandardOptions()
{
}
