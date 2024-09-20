//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2024, Cinesite VFX Ltd. All rights reserved.
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

#include "GafferML/ImageToTensor.h"

#include "GafferImage/BufferAlgo.h"
#include "GafferImage/ImageAlgo.h"
#include "GafferImage/Sampler.h"

#include "Gaffer/Context.h"

#include "boost/container/flat_map.hpp"

#include "onnxruntime_cxx_api.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;
using namespace GafferML;

GAFFER_NODE_DEFINE_TYPE( ImageToTensor );

size_t ImageToTensor::g_firstPlugIndex = 0;

ImageToTensor::ImageToTensor( const std::string &name )
	:	ComputeNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ImagePlug( "image", Plug::In ) );
	addChild( new StringVectorDataPlug( "channels", Plug::In, new StringVectorData( { "R", "G", "B" } ) ) );
	addChild( new TensorPlug( "tensor", Plug::Out ) );
}

ImageToTensor::~ImageToTensor()
{
}

GafferImage::ImagePlug *ImageToTensor::imagePlug()
{
	return getChild<ImagePlug>( g_firstPlugIndex );
}

const GafferImage::ImagePlug *ImageToTensor::imagePlug() const
{
	return getChild<ImagePlug>( g_firstPlugIndex );
}

Gaffer::StringVectorDataPlug *ImageToTensor::channelsPlug()
{
	return getChild<StringVectorDataPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringVectorDataPlug *ImageToTensor::channelsPlug() const
{
	return getChild<StringVectorDataPlug>( g_firstPlugIndex + 1 );
}

TensorPlug *ImageToTensor::tensorPlug()
{
	return getChild<TensorPlug>( g_firstPlugIndex + 2 );
}

const TensorPlug *ImageToTensor::tensorPlug() const
{
	return getChild<TensorPlug>( g_firstPlugIndex + 2 );
}

void ImageToTensor::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ComputeNode::affects( input, outputs );

	if(
		input == imagePlug()->dataWindowPlug() ||
		input == imagePlug()->channelNamesPlug() ||
		input == imagePlug()->channelDataPlug() ||
		input == channelsPlug()
	)
	{
		outputs.push_back( tensorPlug() );
	}
}

void ImageToTensor::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( output == tensorPlug() )
	{
		ComputeNode::hash( output, context, h );

		const Box2i dataWindow = imagePlug()->dataWindow();
		ConstStringVectorDataPtr inChannels = imagePlug()->channelNamesPlug()->getValue();
		ConstStringVectorDataPtr channels = channelsPlug()->getValue();

		ImageAlgo::parallelGatherTiles(
			imagePlug(),
			channels->readable(),
			// Tile
			[&] ( const ImagePlug *image, const string &channelName, const Imath::V2i &tileOrigin )
			{
				if( !ImageAlgo::channelExists( inChannels->readable(), channelName ) )
				{
					throw IECore::Exception( fmt::format( "Channel \"{}\" does not exist", channelName ) );
				}
				return image->channelDataPlug()->hash();
			},
			// Gather
			[&] ( const ImagePlug *image, const string &channelName, const Imath::V2i &tileOrigin, const IECore::MurmurHash &tileHash )
			{
				h.append( tileHash );
			},
			dataWindow,
			ImageAlgo::TopToBottom
		);

		h.append( dataWindow );
	}
	else
	{
		ComputeNode::hash( output, context, h );
	}
}

void ImageToTensor::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output == tensorPlug() )
	{
		const Box2i dataWindow = imagePlug()->dataWindow();
		ConstStringVectorDataPtr inChannels = imagePlug()->channelNamesPlug()->getValue();
		ConstStringVectorDataPtr channelsData = channelsPlug()->getValue();
		const auto &channels = channelsData->readable();

		const size_t numPixels = dataWindow.size().x * dataWindow.size().y;

		FloatVectorDataPtr bufferData = new FloatVectorData;
		vector<float> &buffer = bufferData->writable();
		buffer.resize( numPixels * channels.size() );

		boost::container::flat_map<std::string, float *> channelBuffers;
		for( size_t i = 0; i < channels.size(); ++i )
		{
			channelBuffers[channels[i]] = buffer.data() + numPixels * i;
		}

		ImageAlgo::parallelProcessTiles(
			imagePlug(),
			channels,
			[&] ( const ImagePlug *image, const string &channelName, const Imath::V2i &tileOrigin )
			{
				if( !ImageAlgo::channelExists( inChannels->readable(), channelName ) )
				{
					throw IECore::Exception( fmt::format( "Channel \"{}\" does not exist", channelName ) );
				}

				ConstFloatVectorDataPtr channelData = image->channelDataPlug()->getValue();
				const Box2i tileBound( tileOrigin, tileOrigin + V2i( ImagePlug::tileSize() ) );
				const Box2i validTileBound = BufferAlgo::intersection( tileBound, dataWindow );
				float *channelBuffer = channelBuffers[channelName];

				for( V2i p = validTileBound.min; p.y < validTileBound.max.y; ++p.y )
				{
					const size_t dstIndex = BufferAlgo::index( V2i( p.x, dataWindow.max.y - p.y - 1 ), dataWindow );
					const size_t srcIndex = BufferAlgo::index( p, tileBound );
					std::copy(
						channelData->readable().begin() + srcIndex,
						channelData->readable().begin() + srcIndex + validTileBound.size().x,
						channelBuffer + dstIndex
					);
				}
			}
		);

		ConstTensorDataPtr tensorData = new TensorData(
			bufferData, { 1, (int64_t)channels.size(), dataWindow.size().x, dataWindow.size().y }
		);
		static_cast<TensorPlug *>( output )->setValue( tensorData );
	}

	ComputeNode::compute( output, context );
}

Gaffer::ValuePlug::CachePolicy ImageToTensor::hashCachePolicy( const Gaffer::ValuePlug *output ) const
{
	if( output == tensorPlug() )
	{
		return ValuePlug::CachePolicy::TaskCollaboration;
	}
	return ComputeNode::hashCachePolicy( output );
}

Gaffer::ValuePlug::CachePolicy ImageToTensor::computeCachePolicy( const Gaffer::ValuePlug *output ) const
{
	if( output == tensorPlug() )
	{
		return ValuePlug::CachePolicy::TaskCollaboration;
	}
	return ComputeNode::computeCachePolicy( output );
}

