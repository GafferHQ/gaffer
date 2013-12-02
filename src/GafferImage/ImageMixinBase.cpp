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

#include "IECore/Exception.h"

#include "GafferImage/ImageMixinBase.h"

using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

IE_CORE_DEFINERUNTIMETYPED( ImageMixinBase );

ImageMixinBase::ImageMixinBase( const std::string &name )
	:	ImageProcessor( name )
{
}

ImageMixinBase::~ImageMixinBase()
{
}

void ImageMixinBase::hashFormat( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	throw Exception( "Unexpected call to ImageMixinBase::hashFormat" );
}

void ImageMixinBase::hashDataWindow( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	throw Exception( "Unexpected call to ImageMixinBase::hashDataWindow" );
}

void ImageMixinBase::hashChannelNames( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	throw Exception( "Unexpected call to ImageMixinBase::hashChannelNames" );
}

void ImageMixinBase::hashChannelData( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	throw Exception( "Unexpected call to ImageMixinBase::hashChannelData" );
}

GafferImage::Format ImageMixinBase::computeFormat( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	throw Exception( "Unexpected call to ImageMixinBase::computeFormat" );
}

Imath::Box2i ImageMixinBase::computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	throw Exception( "Unexpected call to ImageMixinBase::computeDataWindow" );
}

IECore::ConstStringVectorDataPtr ImageMixinBase::computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	throw Exception( "Unexpected call to ImageMixinBase::computeChannelNames" );
}

IECore::ConstFloatVectorDataPtr ImageMixinBase::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	throw Exception( "Unexpected call to ImageMixinBase::computeChannelData" );
}
