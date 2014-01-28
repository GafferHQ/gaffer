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

#include "boost/python.hpp"

#include "IECorePython/ScopedGILRelease.h"

#include "GafferBindings/DependencyNodeBinding.h"
#include "GafferBindings/ExecutableBinding.h"

#include "GafferImage/ImageNode.h"
#include "GafferImage/Display.h"
#include "GafferImage/ImageProcessor.h"
#include "GafferImage/FilterProcessor.h"
#include "GafferImage/ChannelDataProcessor.h"
#include "GafferImage/OpenColorIO.h"
#include "GafferImage/ObjectToImage.h"
#include "GafferImage/Merge.h"
#include "GafferImage/Grade.h"
#include "GafferImage/Clamp.h"
#include "GafferImage/Constant.h"
#include "GafferImage/Select.h"
#include "GafferImage/Reformat.h"
#include "GafferImage/ImageWriter.h"
#include "GafferImage/ImageTransform.h"
#include "GafferImage/ImageStats.h"
#include "GafferImage/ImageSampler.h"

#include "GafferImageBindings/FormatBinding.h"
#include "GafferImageBindings/FormatPlugBinding.h"
#include "GafferImageBindings/SamplerBinding.h"
#include "GafferImageBindings/FilterPlugBindings.h"
#include "GafferImageBindings/FilterBinding.h"
#include "GafferImageBindings/RemoveChannelsBinding.h"
#include "GafferImageBindings/ChannelMaskPlugBindings.h"
#include "GafferImageBindings/MixinBinding.h"
#include "GafferImageBindings/FormatDataBinding.h"
#include "GafferImageBindings/ImageReaderBinding.h"

using namespace boost::python;
using namespace GafferImage;

static IECore::FloatVectorDataPtr channelData( const ImagePlug &plug,  const std::string &channelName, const Imath::V2i &tile  )
{
	IECore::ConstFloatVectorDataPtr d = plug.channelData( channelName, tile );
	return d ? d->copy() : 0;
}

static IECore::ImagePrimitivePtr image( const ImagePlug &plug )
{
	IECorePython::ScopedGILRelease gilRelease;
	return plug.image();
}

BOOST_PYTHON_MODULE( _GafferImage )
{
	
	IECorePython::RunTimeTypedClass<ImagePlug>()
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
		.def( "channelData", &channelData )
		.def( "channelDataHash", &ImagePlug::channelDataHash )
		.def( "image", &image )
		.def( "imageHash", &ImagePlug::imageHash )
		.def( "tileSize", &ImagePlug::tileSize ).staticmethod( "tileSize" )
		.def( "tileBound", &ImagePlug::tileBound ).staticmethod( "tileBound" )
		.def( "tileOrigin", &ImagePlug::tileOrigin ).staticmethod( "tileOrigin" )
	;

	GafferBindings::DependencyNodeClass<ImageNode>();
	GafferBindings::DependencyNodeClass<ImagePrimitiveNode>();
	GafferBindings::DependencyNodeClass<Display>()
		.def( "dataReceivedSignal", &Display::dataReceivedSignal, return_value_policy<reference_existing_object>() ).staticmethod( "dataReceivedSignal" )
		.def( "imageReceivedSignal", &Display::imageReceivedSignal, return_value_policy<reference_existing_object>() ).staticmethod( "imageReceivedSignal" )
	;
	GafferBindings::DependencyNodeClass<ImageProcessor>();
	GafferBindings::DependencyNodeClass<FilterProcessor>();
	GafferBindings::DependencyNodeClass<ChannelDataProcessor>();
	GafferBindings::DependencyNodeClass<ColorProcessor>();
	GafferBindings::DependencyNodeClass<OpenColorIO>();
	GafferBindings::DependencyNodeClass<ObjectToImage>();
	GafferBindings::DependencyNodeClass<Merge>();
	GafferBindings::DependencyNodeClass<Grade>();
	GafferBindings::DependencyNodeClass<Clamp>();
	GafferBindings::DependencyNodeClass<Constant>();
	GafferBindings::DependencyNodeClass<Select>();
	GafferBindings::DependencyNodeClass<Reformat>();
	GafferBindings::DependencyNodeClass<ImageTransform>();
	GafferBindings::DependencyNodeClass<ImageStats>();
	GafferBindings::DependencyNodeClass<ImageSampler>();

	GafferImageBindings::bindRemoveChannels();
	GafferImageBindings::bindFormat();
	GafferImageBindings::bindFormatPlug();
	GafferImageBindings::bindChannelMaskPlug();
	GafferImageBindings::bindFilterPlug();
	GafferImageBindings::bindSampler();
	GafferImageBindings::bindFilters();
	GafferImageBindings::bindMixin();
	GafferImageBindings::bindFormatData();
	GafferImageBindings::bindImageReader();
	
	GafferBindings::NodeClass<ImageWriter> imageWriter;
	GafferBindings::ExecutableBinding< GafferBindings::NodeClass<ImageWriter>, ImageWriter>::bind( imageWriter );
}

