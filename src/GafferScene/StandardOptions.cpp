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

#include "IECoreScene/Camera.h"

#include "GafferScene/StandardOptions.h"

using namespace Gaffer;
using namespace GafferScene;

GAFFER_NODE_DEFINE_TYPE( StandardOptions );

StandardOptions::StandardOptions( const std::string &name )
	:	Options( name )
{
	CompoundDataPlug *options = optionsPlug();

	// Camera

	options->addChild( new Gaffer::NameValuePlug( "render:camera", new IECore::StringData(), false, "renderCamera" ) );
	options->addChild( new Gaffer::NameValuePlug( "render:filmFit", new IECore::IntData( IECoreScene::Camera::Horizontal ), false, "filmFit" ) );
	options->addChild( new Gaffer::NameValuePlug( "render:resolution", new IECore::V2iData( Imath::V2i( 1024, 778 ) ), false, "renderResolution" ) );
	options->addChild( new Gaffer::NameValuePlug( "render:pixelAspectRatio", new IECore::FloatData( 1.0f ), false, "pixelAspectRatio" ) );
	options->addChild( new Gaffer::NameValuePlug( "render:resolutionMultiplier", new IECore::FloatData( 1.0f ), false, "resolutionMultiplier" ) );
	options->addChild( new Gaffer::NameValuePlug( "render:cropWindow", new Box2fPlug( "value", Plug::In, Imath::Box2f( Imath::V2f( 0 ), Imath::V2f( 1 ) ), Imath::V2f( 0 ), Imath::V2f( 1 ) ), false, "renderCropWindow" ) );

	options->addChild( new Gaffer::NameValuePlug( "render:overscan", new IECore::BoolData( false ), false, "overscan" ) );
	options->addChild( new Gaffer::NameValuePlug( "render:overscanTop", new FloatPlug( "value", Plug::In, 0.1f, 0.0f, 1.0f ), false, "overscanTop" ) );
	options->addChild( new Gaffer::NameValuePlug( "render:overscanBottom", new FloatPlug( "value", Plug::In, 0.1f, 0.0f, 1.0f ), false, "overscanBottom" ) );
	options->addChild( new Gaffer::NameValuePlug( "render:overscanLeft", new FloatPlug( "value", Plug::In, 0.1f, 0.0f, 1.0f ), false, "overscanLeft" ) );
	options->addChild( new Gaffer::NameValuePlug( "render:overscanRight", new FloatPlug( "value", Plug::In, 0.1f, 0.0f, 1.0f ), false, "overscanRight" ) );
	options->addChild( new Gaffer::NameValuePlug( "render:depthOfField", new IECore::BoolData( false ), false, "depthOfField" ) );

	// Motion blur

	options->addChild( new Gaffer::NameValuePlug( "render:cameraBlur", new IECore::BoolData( false ), false, "cameraBlur" ) );
	options->addChild( new Gaffer::NameValuePlug( "render:transformBlur", new IECore::BoolData( false ), false, "transformBlur" ) );
	options->addChild( new Gaffer::NameValuePlug( "render:deformationBlur", new IECore::BoolData( false ), false, "deformationBlur" ) );
	options->addChild( new Gaffer::NameValuePlug( "render:shutter", new IECore::V2fData( Imath::V2f( -0.25, 0.25 ) ), false, "shutter" ) );
	options->addChild( new Gaffer::NameValuePlug( "sampleMotion", new IECore::BoolData( true ), false, "sampleMotion" ) );

	// Statistics

	options->addChild( new Gaffer::NameValuePlug( "render:performanceMonitor", new IECore::BoolData( false ), false, "performanceMonitor" ) );

}

StandardOptions::~StandardOptions()
{
}
