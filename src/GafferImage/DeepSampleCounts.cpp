//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2019, Image Engine Design Inc. All rights reserved.
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

#include "GafferImage/DeepSampleCounts.h"

#include "Gaffer/Context.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

GAFFER_NODE_DEFINE_TYPE( DeepSampleCounts );

size_t DeepSampleCounts::g_firstPlugIndex = 0;

DeepSampleCounts::DeepSampleCounts( const std::string &name )
	:	ImageProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	outPlug()->viewNamesPlug()->setInput( inPlug()->viewNamesPlug() );
	outPlug()->formatPlug()->setInput( inPlug()->formatPlug() );
	outPlug()->metadataPlug()->setInput( inPlug()->metadataPlug() );
	outPlug()->dataWindowPlug()->setInput( inPlug()->dataWindowPlug() );
}

DeepSampleCounts::~DeepSampleCounts()
{
}

void DeepSampleCounts::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ImageProcessor::affects( input, outputs );

	if( input == inPlug()->sampleOffsetsPlug() )
	{
		outputs.push_back( outPlug()->channelDataPlug() );
	}
	if( input == inPlug()->deepPlug() )
	{
		outputs.push_back( outPlug()->channelDataPlug() );
	}
}

void DeepSampleCounts::hashDeep( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hashDeep( parent, context, h );
}

bool DeepSampleCounts::computeDeep( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return false;
}

void DeepSampleCounts::hashChannelNames( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hashChannelNames( parent, context, h );
}

IECore::ConstStringVectorDataPtr DeepSampleCounts::computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return new StringVectorData( std::vector<std::string>( 1, "R" ) );
}

void DeepSampleCounts::hashChannelData( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hashChannelData( parent, context, h );

	ImagePlug::ChannelDataScope scope( context );
	scope.remove( ImagePlug::channelNameContextName );
	inPlug()->sampleOffsetsPlug()->hash( h );
	scope.remove( ImagePlug::tileOriginContextName );
	inPlug()->deepPlug()->hash( h );
}

IECore::ConstFloatVectorDataPtr DeepSampleCounts::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	ImagePlug::ChannelDataScope scope( context );
	scope.remove( ImagePlug::tileOriginContextName );
	scope.remove( ImagePlug::channelNameContextName );
	if( !inPlug()->deepPlug()->getValue() )
	{
		return ImagePlug::whiteTile();
	}

	scope.setTileOrigin( &tileOrigin );
	ConstIntVectorDataPtr sampleOffsetsData = inPlug()->sampleOffsetsPlug()->getValue();

	FloatVectorDataPtr resultData = new FloatVectorData();
	auto &result = resultData->writable();
	result.resize( ImagePlug::tilePixels() );

	int prevOffset = 0;
	for( int i = 0; i < ImagePlug::tilePixels(); i++ )
	{
		int offset = sampleOffsetsData->readable()[i];
		result[i] = float( offset - prevOffset );
		prevOffset = offset;
	}

	return resultData;
}

void DeepSampleCounts::hashSampleOffsets( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	h = ImagePlug::flatTileSampleOffsets()->Object::hash();
}

IECore::ConstIntVectorDataPtr DeepSampleCounts::computeSampleOffsets( const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return ImagePlug::flatTileSampleOffsets();
}
