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

#include "GafferBindings/PlugBinding.h"

#include "GafferImage/ImagePlug.h"

#include "GafferImageBindings/ImagePlugBinding.h"

using namespace boost::python;
using namespace GafferBindings;
using namespace GafferImage;

namespace
{

IECore::FloatVectorDataPtr channelData( const ImagePlug &plug,  const std::string &channelName, const Imath::V2i &tile, bool copy  )
{
	IECorePython::ScopedGILRelease gilRelease;
	IECore::ConstFloatVectorDataPtr d = plug.channelData( channelName, tile );
	return copy ? d->copy() : boost::const_pointer_cast<IECore::FloatVectorData>( d );
}

IECore::ImagePrimitivePtr image( const ImagePlug &plug )
{
	IECorePython::ScopedGILRelease gilRelease;
	return plug.image();
}

} // namespace

void GafferImageBindings::bindImagePlug()
{

	PlugClass<ImagePlug>()
		.def(
			init< const std::string &, Gaffer::Plug::Direction, unsigned >
			(
				(
					arg( "name" ) = Gaffer::GraphComponent::defaultName<ImagePlug>(),
					arg( "direction" ) = Gaffer::Plug::In,
					arg( "flags" ) = Gaffer::Plug::Default
				)
			)
		)
		.def( "channelData", &channelData, ( arg( "_copy" ) = true ) )
		.def( "channelDataHash", &ImagePlug::channelDataHash )
		.def( "image", &image )
		.def( "imageHash", &ImagePlug::imageHash )
		.def( "tileSize", &ImagePlug::tileSize ).staticmethod( "tileSize" )
		.def( "tileOrigin", &ImagePlug::tileOrigin ).staticmethod( "tileOrigin" )
	;

}
