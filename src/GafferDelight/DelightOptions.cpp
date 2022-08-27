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

#include "Gaffer/FilePathPlug.h"

using namespace Imath;
using namespace GafferDelight;

GAFFER_NODE_DEFINE_TYPE( DelightOptions );

DelightOptions::DelightOptions( const std::string &name )
	:	GafferScene::Options( name )
{
	Gaffer::CompoundDataPlug *options = optionsPlug();

	// Rendering

	options->addChild( new Gaffer::NameValuePlug( "dl:bucketorder", new IECore::StringData( "horizontal" ), false, "bucketOrder" ) );
	options->addChild( new Gaffer::NameValuePlug( "dl:numberofthreads", new IECore::IntData( 0 ), false, "numberOfThreads" ) );

	// Quality

	options->addChild( new Gaffer::NameValuePlug( "dl:oversampling", new IECore::IntData( 9 ), false, "oversampling" ) );
	options->addChild( new Gaffer::NameValuePlug( "dl:quality.shadingsamples", new IECore::IntData( 64 ), false, "shadingSamples" ) );

	// Ray depth

	options->addChild( new Gaffer::NameValuePlug( "dl:maximumraydepth.diffuse", new IECore::IntData( 1 ), false, "maximumRayDepthDiffuse" ) );
	options->addChild( new Gaffer::NameValuePlug( "dl:maximumraydepth.hair", new IECore::IntData( 4 ), false, "maximumRayDepthHair" ) );
	options->addChild( new Gaffer::NameValuePlug( "dl:maximumraydepth.reflection", new IECore::IntData( 1 ), false, "maximumRayDepthReflection" ) );
	options->addChild( new Gaffer::NameValuePlug( "dl:maximumraydepth.refraction", new IECore::IntData( 4 ), false, "maximumRayDepthRefraction" ) );

	// Texturing

	options->addChild( new Gaffer::NameValuePlug( "dl:texturememory", new IECore::IntData( 250 ), false, "textureMemory" ) );

	// Network cache

	options->addChild( new Gaffer::NameValuePlug( "dl:networkcache.size", new IECore::IntData( 15 ), false, "networkCacheSize" ) );
	options->addChild( new Gaffer::NameValuePlug( "dl:networkcache.directory", new Gaffer::FilePathPlug(), false, "networkCacheDirectory" ) );

	// Licensing

	options->addChild( new Gaffer::NameValuePlug( "dl:license.server", new IECore::StringData( "" ), false, "licenseServer" ) );
	options->addChild( new Gaffer::NameValuePlug( "dl:license.wait", new IECore::BoolData( true ), false, "licenseWait" ) );

}

DelightOptions::~DelightOptions()
{
}
