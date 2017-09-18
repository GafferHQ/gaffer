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

#include "GafferDelight/DelightOptions.h"

using namespace Imath;
using namespace GafferDelight;

IE_CORE_DEFINERUNTIMETYPED( DelightOptions );

DelightOptions::DelightOptions( const std::string &name )
	:	GafferScene::Options( name )
{
	Gaffer::CompoundDataPlug *options = optionsPlug();

	// Rendering

	options->addOptionalMember( "dl:bucketorder", new IECore::StringData( "horizontal" ), "bucketOrder", Gaffer::Plug::Default, false );
	options->addOptionalMember( "dl:numberofthreads", new IECore::IntData( 0 ), "numberOfThreads", Gaffer::Plug::Default, false );

	// Quality

	options->addOptionalMember( "dl:oversampling", new IECore::IntData( 9 ), "oversampling", Gaffer::Plug::Default, false );
	options->addOptionalMember( "dl:quality.shadingsamples", new IECore::IntData( 64 ), "shadingSamples", Gaffer::Plug::Default, false );

	// Ray depth

	options->addOptionalMember( "dl:maximumraydepth.diffuse", new IECore::IntData( 1 ), "maximumRayDepthDiffuse", Gaffer::Plug::Default, false );
	options->addOptionalMember( "dl:maximumraydepth.hair", new IECore::IntData( 4 ), "maximumRayDepthHair", Gaffer::Plug::Default, false );
	options->addOptionalMember( "dl:maximumraydepth.reflection", new IECore::IntData( 1 ), "maximumRayDepthReflection", Gaffer::Plug::Default, false );
	options->addOptionalMember( "dl:maximumraydepth.refraction", new IECore::IntData( 4 ), "maximumRayDepthRefraction", Gaffer::Plug::Default, false );

	// Texturing

	options->addOptionalMember( "dl:texturememory", new IECore::IntData( 250 ), "textureMemory", Gaffer::Plug::Default, false );

	// Network cache

	options->addOptionalMember( "dl:networkcache.size", new IECore::IntData( 15 ), "networkCacheSize", Gaffer::Plug::Default, false );
	options->addOptionalMember( "dl:networkcache.directory", new IECore::StringData( "" ), "networkCacheDirectory", Gaffer::Plug::Default, false );

	// Licensing

	options->addOptionalMember( "dl:license.server", new IECore::StringData( "" ), "licenseServer", Gaffer::Plug::Default, false );
	options->addOptionalMember( "dl:license.wait", new IECore::BoolData( true ), "licenseWait", Gaffer::Plug::Default, false );

}

DelightOptions::~DelightOptions()
{
}
