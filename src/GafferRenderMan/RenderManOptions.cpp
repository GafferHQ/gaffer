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

#include "GafferRenderMan/RenderManOptions.h"

using namespace Imath;
using namespace GafferRenderMan;

IE_CORE_DEFINERUNTIMETYPED( RenderManOptions );

RenderManOptions::RenderManOptions( const std::string &name )
	:	GafferScene::Options( name )
{
	Gaffer::CompoundDataPlug *options = optionsPlug();

	options->addOptionalMember( "ri:pixelSamples", new IECore::V2iData( V2i( 3 ) ), "pixelSamples", Gaffer::Plug::Default, false );

	// hider parameters

	options->addOptionalMember( "ri:hider", new IECore::StringData( "hidden" ), "hider", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ri:hider:depthfilter", new IECore::StringData( "min" ), "hiderDepthFilter", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ri:hider:jitter", new IECore::BoolData( true ), "hiderJitter", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ri:hider:samplemotion", new IECore::BoolData( true ), "hiderSampleMotion", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ri:hider:extrememotiondof", new IECore::BoolData( false ), "hiderExtremeMotionDOF", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ri:hider:progressive", new IECore::BoolData( false ), "hiderProgressive", Gaffer::Plug::Default, false );

	// statistics parameters

	options->addOptionalMember( "ri:statistics:endofframe", new IECore::IntData( 0 ), "statisticsLevel", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ri:statistics:filename", new IECore::StringData( "" ), "statisticsFileName", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ri:statistics:progress", new IECore::BoolData( false ), "statisticsProgress", Gaffer::Plug::Default, false );

	// searchpath parameters

	options->addOptionalMember( "ri:searchpath:shader", new IECore::StringData( "" ), "shaderSearchPath", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ri:searchpath:texture", new IECore::StringData( "" ), "textureSearchPath", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ri:searchpath:display", new IECore::StringData( "" ), "displaySearchPath", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ri:searchpath:archive", new IECore::StringData( "" ), "archiveSearchPath", Gaffer::Plug::Default, false );
	options->addOptionalMember( "ri:searchpath:procedural", new IECore::StringData( "" ), "proceduralSearchPath", Gaffer::Plug::Default, false );

}

RenderManOptions::~RenderManOptions()
{
}
