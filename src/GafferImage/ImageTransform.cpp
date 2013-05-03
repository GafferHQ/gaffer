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
//      * Neither the name of Image Engine Design nor the names of
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

#include "Gaffer/Context.h"
#include "GafferImage/ImageTransform.h"
#include "GafferImage/ImageTransform.h"
#include "GafferImage/Filter.h"
#include "GafferImage/FormatPlug.h"
#include "GafferImage/ImagePlug.h"
#include "GafferImage/Sampler.h"
#include "IECore/BoxAlgo.h"
#include "IECore/BoxOps.h"

using namespace Gaffer;
using namespace IECore;
using namespace GafferImage;

IE_CORE_DEFINERUNTIMETYPED( ImageTransform );

size_t ImageTransform::g_firstPlugIndex = 0;

ImageTransform::ImageTransform( const std::string &name )
	:	ImageProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new Gaffer::TransformPlug( "transform" ) );
	addChild( new Gaffer::V2fPlug( "center" ) );
}

ImageTransform::~ImageTransform()
{
}

Gaffer::TransformPlug *ImageTransform::transformPlug()
{
	return getChild<Gaffer::TransformPlug>( g_firstPlugIndex );
}

const Gaffer::TransformPlug *ImageTransform::transformPlug() const
{
	return getChild<Gaffer::TransformPlug>( g_firstPlugIndex );
}

Gaffer::V2fPlug *ImageTransform::centerPlug()
{
	return getChild<Gaffer::V2fPlug>( g_firstPlugIndex+1 );
}

const Gaffer::V2fPlug *ImageTransform::centerPlug() const
{
	return getChild<Gaffer::V2fPlug>( g_firstPlugIndex+1 );
}

void ImageTransform::affects( const Gaffer::ValuePlug *input, AffectedPlugsContainer &outputs ) const
{
	ImageProcessor::affects( input, outputs );

	if ( input == transformPlug()->scalePlug() ||
		 input == transformPlug()->translatePlug() ||
		 input == transformPlug()->rotatePlug() ||
		 input == centerPlug()
		)
	{
		outputs.push_back( outPlug()->dataWindowPlug() );
		outputs.push_back( outPlug()->channelDataPlug() );
	}
}

bool ImageTransform::enabled() const
{
	if ( !ImageProcessor::enabled() )
	{
		return false;
	}

	///\todo test whether we have the transform has no effect.	
	return true;
}

void ImageTransform::hashFormatPlug( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	Format format( inPlug()->formatPlug()->getValue() );
	h.append( format.getDisplayWindow() );
	h.append( format.getPixelAspect() );
}

void ImageTransform::hashDataWindowPlug( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	inPlug()->dataWindowPlug()->hash( h );
	transformPlug()->scalePlug()->hash( h );
	transformPlug()->rotatePlug()->hash( h );
	transformPlug()->translatePlug()->hash( h );
	centerPlug()->hash( h );
}

void ImageTransform::hashChannelNamesPlug( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	inPlug()->channelNamesPlug()->hash( h );
}

void ImageTransform::hashChannelDataPlug( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	inPlug()->channelDataPlug()->hash( h );
	inPlug()->dataWindowPlug()->hash( h );
	transformPlug()->scalePlug()->hash( h );
	transformPlug()->rotatePlug()->hash( h );
	transformPlug()->translatePlug()->hash( h );
	centerPlug()->hash( h );
}

Imath::Box2i ImageTransform::computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	///\todo: Work out the new data window by transforming the input data window.
	// Work out the scale factor of the output image and scale the input data window.


	Imath::Box2i dataWindow( inPlug()->dataWindowPlug()->getValue() );
	Imath::V2f min( dataWindow.min );
	Imath::V2f max( dataWindow.max );
/*
	std::cerr << min.x << ", " << min.y << ", " << max.x << ", " << max.y << std::endl;
	Imath::V2f center( centerPlug()->getValue() );
	min -= center;
	max -= center;
	min = transformPlug()->matrix() * min;
	max = transformPlug()->matrix() * max;
	std::cerr << min.x << ", " << min.y << ", " << max.x << ", " << max.y << std::endl;
	*/
	return dataWindow;
}

GafferImage::Format ImageTransform::computeFormat( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return inPlug()->formatPlug()->getValue();
}

IECore::ConstStringVectorDataPtr ImageTransform::computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return inPlug()->channelNamesPlug()->getValue();
}

IECore::ConstFloatVectorDataPtr ImageTransform::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	// Allocate the new tile
	FloatVectorDataPtr outDataPtr = new FloatVectorData;
	std::vector<float> &out = outDataPtr->writable();
	out.resize( ImagePlug::tileSize() * ImagePlug::tileSize() );

	// Create some useful variables...
	Imath::Box2i tile( tileOrigin, Imath::V2i( tileOrigin.x + ImagePlug::tileSize() - 1, tileOrigin.y + ImagePlug::tileSize() - 1 ) );

	return outDataPtr;
}

