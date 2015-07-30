//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
//  Copyright (c) 2013-2015, Image Engine Design Inc. All rights reserved.
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
#include "GafferBindings/ExecutableNodeBinding.h"

#include "GafferImage/Display.h"
#include "GafferImage/ChannelDataProcessor.h"
#include "GafferImage/OpenColorIO.h"
#include "GafferImage/ObjectToImage.h"
#include "GafferImage/Grade.h"
#include "GafferImage/Clamp.h"
#include "GafferImage/Constant.h"
#include "GafferImage/Reformat.h"
#include "GafferImage/ImageWriter.h"
#include "GafferImage/ImageTransform.h"
#include "GafferImage/ImageStats.h"
#include "GafferImage/ImageSampler.h"
#include "GafferImage/MetadataProcessor.h"
#include "GafferImage/ImageMetadata.h"
#include "GafferImage/DeleteImageMetadata.h"
#include "GafferImage/CopyImageMetadata.h"

#include "GafferImageBindings/ImageNodeBinding.h"
#include "GafferImageBindings/ImageProcessorBinding.h"
#include "GafferImageBindings/ImagePlugBinding.h"
#include "GafferImageBindings/FormatBinding.h"
#include "GafferImageBindings/FormatPlugBinding.h"
#include "GafferImageBindings/SamplerBinding.h"
#include "GafferImageBindings/FilterPlugBindings.h"
#include "GafferImageBindings/FilterBinding.h"
#include "GafferImageBindings/DeleteChannelsBinding.h"
#include "GafferImageBindings/ChannelMaskPlugBindings.h"
#include "GafferImageBindings/MergeBinding.h"
#include "GafferImageBindings/MixinBinding.h"
#include "GafferImageBindings/FormatDataBinding.h"
#include "GafferImageBindings/ImageReaderBinding.h"
#include "GafferImageBindings/ShuffleBinding.h"

using namespace boost::python;
using namespace GafferImage;

BOOST_PYTHON_MODULE( _GafferImage )
{

	GafferImageBindings::bindImagePlug();

	GafferImageBindings::bindImageNode();
	GafferImageBindings::bindImageProcessor();
	GafferBindings::DependencyNodeClass<ImagePrimitiveNode>();
	GafferBindings::DependencyNodeClass<Display>()
		.def( "dataReceivedSignal", &Display::dataReceivedSignal, return_value_policy<reference_existing_object>() ).staticmethod( "dataReceivedSignal" )
		.def( "imageReceivedSignal", &Display::imageReceivedSignal, return_value_policy<reference_existing_object>() ).staticmethod( "imageReceivedSignal" )
	;
	GafferBindings::DependencyNodeClass<ChannelDataProcessor>();
	GafferBindings::DependencyNodeClass<ColorProcessor>();
	GafferBindings::DependencyNodeClass<OpenColorIO>();
	GafferBindings::DependencyNodeClass<ObjectToImage>();
	GafferBindings::DependencyNodeClass<Grade>();
	GafferBindings::DependencyNodeClass<Clamp>();
	GafferBindings::DependencyNodeClass<Constant>();
	GafferBindings::DependencyNodeClass<Reformat>();
	GafferBindings::DependencyNodeClass<ImageTransform>();
	GafferBindings::DependencyNodeClass<ImageStats>();
	GafferBindings::DependencyNodeClass<ImageSampler>();
	GafferBindings::DependencyNodeClass<MetadataProcessor>();
	GafferBindings::DependencyNodeClass<ImageMetadata>();
	GafferBindings::DependencyNodeClass<DeleteImageMetadata>();
	GafferBindings::DependencyNodeClass<CopyImageMetadata>();

	GafferImageBindings::bindDeleteChannels();
	GafferImageBindings::bindFormat();
	GafferImageBindings::bindFormatPlug();
	GafferImageBindings::bindChannelMaskPlug();
	GafferImageBindings::bindFilterPlug();
	GafferImageBindings::bindSampler();
	GafferImageBindings::bindFilters();
	GafferImageBindings::bindMixin();
	GafferImageBindings::bindFormatData();
	GafferImageBindings::bindImageReader();
	GafferImageBindings::bindMerge();
	GafferImageBindings::bindShuffle();

	GafferBindings::ExecutableNodeClass<ImageWriter>();
}

