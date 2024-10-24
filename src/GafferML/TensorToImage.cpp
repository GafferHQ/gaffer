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

#include "GafferML/TensorToImage.h"

#include "GafferImage/BufferAlgo.h"
#include "GafferImage/ImageAlgo.h"
#include "GafferImage/Sampler.h"

#include "Gaffer/Context.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;
using namespace GafferML;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

struct ImageShape
{
	Box2i dataWindow;
	int numChannels;
};

ImageShape imageShape( const Tensor *tensor, bool interleavedChannels )
{
	const auto shape = tensor->value().GetTensorTypeAndShapeInfo().GetShape();
	if( shape.size() < 3 )
	{
		throw IECore::Exception( "Expected tensor with at least 3 dimensions" );
	}

	size_t i = shape.size() - 3;
	for( size_t d = 0; d < i; ++d )
	{
		if( shape[d] != 1 )
		{
			throw IECore::Exception(
				fmt::format(
					"Expected {} dimensional tensor to have size 1 in dimension {}",
					shape.size(), d
				)
			);
		}
	}

	if( interleavedChannels )
	{
		return {
			Box2i( V2i( 0 ), V2i( (int)shape[i], (int)shape[i+1] ) ),
			(int)shape[i+2]
		};
	}
	else
	{
		return {
			Box2i( V2i( 0 ), V2i( (int)shape[i+1], (int)shape[i+2] ) ),
			(int)shape[i]
		};
	}
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// TensorToImage
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( TensorToImage );

size_t TensorToImage::g_firstPlugIndex = 0;

TensorToImage::TensorToImage( const std::string &name )
	:	FlatImageSource( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new TensorPlug( "tensor" ) );
	addChild( new StringVectorDataPlug( "channels", Plug::In, new StringVectorData( { "R", "G", "B" } ) ) );
	addChild( new BoolPlug( "interleavedChannels" ) );
}

TensorToImage::~TensorToImage()
{
}

TensorPlug *TensorToImage::tensorPlug()
{
	return getChild<TensorPlug>( g_firstPlugIndex );
}

const TensorPlug *TensorToImage::tensorPlug() const
{
	return getChild<TensorPlug>( g_firstPlugIndex );
}

Gaffer::StringVectorDataPlug *TensorToImage::channelsPlug()
{
	return getChild<StringVectorDataPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringVectorDataPlug *TensorToImage::channelsPlug() const
{
	return getChild<StringVectorDataPlug>( g_firstPlugIndex + 1 );
}

Gaffer::BoolPlug *TensorToImage::interleavedChannelsPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::BoolPlug *TensorToImage::interleavedChannelsPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 2 );
}

void TensorToImage::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	FlatImageSource::affects( input, outputs );

	if( input == channelsPlug() )
	{
		outputs.push_back( outPlug()->channelNamesPlug() );
	}

	if( input == tensorPlug() || input == interleavedChannelsPlug() )
	{
		outputs.push_back( outPlug()->dataWindowPlug() );
	}

	if( input == tensorPlug() || input == channelsPlug() || input == interleavedChannelsPlug() )
	{
		outputs.push_back( outPlug()->channelDataPlug() );
	}

	if( input == outPlug()->dataWindowPlug() )
	{
		outputs.push_back( outPlug()->formatPlug() );
	}
}

void TensorToImage::hashMetadata( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	h = outPlug()->metadataPlug()->defaultHash();
}

IECore::ConstCompoundDataPtr TensorToImage::computeMetadata( const Gaffer::Context *context, const GafferImage::ImagePlug *parent ) const
{
	return outPlug()->metadataPlug()->defaultValue();
}

void TensorToImage::hashFormat( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	FlatImageSource::hashFormat( parent, context, h );
	outPlug()->dataWindowPlug()->hash( h );
}

GafferImage::Format TensorToImage::computeFormat( const Gaffer::Context *context, const GafferImage::ImagePlug *parent ) const
{
	return Format( outPlug()->dataWindowPlug()->getValue() );
}

void TensorToImage::hashDataWindow( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	FlatImageSource::hashDataWindow( parent, context, h );
	tensorPlug()->hash( h );
	interleavedChannelsPlug()->hash( h );
}

Imath::Box2i TensorToImage::computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	ConstTensorPtr tensor = tensorPlug()->getValue();
	return imageShape( tensor.get(), interleavedChannelsPlug()->getValue() ).dataWindow;
}

void TensorToImage::hashChannelNames( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	FlatImageSource::hashChannelNames( parent, context, h );
	channelsPlug()->hash( h );
}

IECore::ConstStringVectorDataPtr TensorToImage::computeChannelNames( const Gaffer::Context *context, const GafferImage::ImagePlug *parent ) const
{
	ConstStringVectorDataPtr channels = channelsPlug()->getValue()->copy();
	// `channels` might be in a non-standard order, to facilitate unpacking from
	// a shuffled buffer, and could contain duplicates since it's easy to create
	// them while shuffling the list in the UI. Sort into a more natural order
	// and remove duplicates.
	StringVectorDataPtr result = new StringVectorData( ImageAlgo::sortedChannelNames( channels->readable() ) );
	result->writable().erase(
		std::unique(
			result->writable().begin(),
			result->writable().end()
		),
		result->writable().end()
	);
	return result;
}

void TensorToImage::hashChannelData( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	FlatImageSource::hashChannelData( parent, context, h );
	{
		ImagePlug::GlobalScope globalScope( context );
		tensorPlug()->hash( h );
		channelsPlug()->hash( h );
		interleavedChannelsPlug()->hash( h );
	}

	h.append( context->get<string>( ImagePlug::channelNameContextName ) );
	h.append( context->get<V2i>( ImagePlug::tileOriginContextName ) );
}

IECore::ConstFloatVectorDataPtr TensorToImage::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	ConstTensorPtr tensorData;
	ConstStringVectorDataPtr channelsData;
	bool interleavedChannels;
	{
		ImagePlug::GlobalScope globalScope( context );
		tensorData = tensorPlug()->getValue();
		channelsData = channelsPlug()->getValue();
		interleavedChannels = interleavedChannelsPlug()->getValue();
	}

	const auto channelIt = std::find( channelsData->readable().begin(), channelsData->readable().end(), channelName );
	if( channelIt == channelsData->readable().end() )
	{
		throw IECore::Exception( fmt::format( "Invalid channel \"{}\"", channelName ) );
	}
	const size_t channelIndex = channelIt - channelsData->readable().begin();

	const ImageShape imageShape = ::imageShape( tensorData.get(), interleavedChannels );
	// TODO : ERROR IF CHANNEL INDEX IS OUTSIDE OF TENSOR BOUNDS
	// AND ALLOW EMPTY CHANNEL NAME TO SKIP CHANNELS.

	FloatVectorDataPtr outData = new FloatVectorData;
	vector<float> &out = outData->writable();

	const Box2i dataWindow = imageShape.dataWindow;
	const Box2i tileBound( tileOrigin, tileOrigin + V2i( ImagePlug::tileSize() ) );
	const Box2i validTileBound = BufferAlgo::intersection( dataWindow, tileBound );
	out.resize( ImagePlug::tileSize() * ImagePlug::tileSize() );

	const float *sourceData = tensorData->value().GetTensorData<float>();
	size_t sourceStride;
	if( interleavedChannels )
	{
		sourceData += channelIndex;
		sourceStride = imageShape.numChannels;
	}
	else
	{
		sourceData += dataWindow.size().x * dataWindow.size().y * channelIndex;
		sourceStride = 1;
	}
	float *dstData = out.data();

	for( V2i p = validTileBound.min; p.y < validTileBound.max.y ; ++p.y )
	{
		size_t srcIndex = BufferAlgo::index( V2i( p.x, dataWindow.max.y - p.y - 1 ), dataWindow ) * sourceStride;
		size_t dstIndex = BufferAlgo::index( p, tileBound );

		for( int x = validTileBound.min.x; x < validTileBound.max.x; ++x )
		{
			dstData[dstIndex++] = sourceData[srcIndex];
			srcIndex += sourceStride;
		}
	}

	return outData;
}
