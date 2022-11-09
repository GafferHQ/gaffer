//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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

#include "boost/python.hpp"

#include "ImageGadgetBinding.h"

#include "GafferImageUI/ImageGadget.h"

#include "GafferImage/ImagePlug.h"

#include "GafferUIBindings/GadgetBinding.h"

#include "GafferBindings/SignalBinding.h"

#include "Gaffer/Context.h"

#include "IECorePython/ExceptionAlgo.h"
#include "IECorePython/ScopedGILRelease.h"

using namespace boost::python;
using namespace IECorePython;
using namespace Gaffer;
using namespace GafferBindings;
using namespace GafferUIBindings;
using namespace GafferImage;
using namespace GafferImageUI;

namespace
{

ImagePlugPtr getImage( const ImageGadget &v )
{
	return ImagePlugPtr( const_cast<ImagePlug *>( v.getImage() ) );
}

void setPaused( ImageGadget &g, bool paused )
{
	ScopedGILRelease gilRelease;
	g.setPaused( paused );
}

Imath::V2f pixelAt( const ImageGadget &g, const IECore::LineSegment3f &lineInGadgetSpace )
{
	// Need GIL release because this method may trigger a compute of the format.
	IECorePython::ScopedGILRelease gilRelease;
	return g.pixelAt( lineInGadgetSpace );
}

Imath::V2f getWipePosition( const ImageGadget &g )
{
	return g.getWipePosition();
}

struct ImageGadgetSlotCaller
{
	void operator()( boost::python::object slot, ImageGadgetPtr g )
	{
		try
		{
			slot( g );
		}
		catch( const error_already_set &e )
		{
			ExceptionAlgo::translatePythonException();
		}
	}
};

} // namespace

void GafferImageUIModule::bindImageGadget()
{
	scope s = GadgetClass<ImageGadget>()
		.def( init<>() )
		.def( "setImage", &ImageGadget::setImage )
		.def( "getImage", &getImage )
		.def( "setContext", &ImageGadget::setContext )
		.def( "getContext", (Context *(ImageGadget::*)())&ImageGadget::getContext, return_value_policy<CastToIntrusivePtr>() )
		.def( "setSoloChannel", &ImageGadget::setSoloChannel )
		.def( "getSoloChannel", &ImageGadget::getSoloChannel )
		.def( "setPaused", &setPaused )
		.def( "getPaused", &ImageGadget::getPaused )
		.def( "tileUpdateCount", &ImageGadget::tileUpdateCount )
		.staticmethod( "tileUpdateCount" )
		.def( "resetTileUpdateCount", &ImageGadget::resetTileUpdateCount )
		.staticmethod( "resetTileUpdateCount" )
		.def( "state", &ImageGadget::state )
		.def( "stateChangedSignal", &ImageGadget::stateChangedSignal, return_internal_reference<1>() )
		.def( "pixelAt", &pixelAt )
		.def( "setWipeEnabled", &ImageGadget::setWipeEnabled )
		.def( "getWipeEnabled", &ImageGadget::getWipeEnabled )
		.def( "setWipePosition", &ImageGadget::setWipePosition )
		.def( "getWipePosition", &getWipePosition )
		.def( "setWipeAngle", &ImageGadget::setWipeAngle )
		.def( "getWipeAngle", &ImageGadget::getWipeAngle )
	;

	enum_<ImageGadget::State>( "State" )
		.value( "Paused", ImageGadget::Paused )
		.value( "Running", ImageGadget::Running )
		.value( "Complete", ImageGadget::Complete )
	;

	SignalClass<ImageGadget::ImageGadgetSignal, DefaultSignalCaller<ImageGadget::ImageGadgetSignal>, ImageGadgetSlotCaller>( "ImageGadgetSignal" );
}
