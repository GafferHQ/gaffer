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

Box2i dataWindow( const TensorData *tensor )
{
	/// \todo Does this need to be configurable?
	const auto shape = tensor->value.GetTensorTypeAndShapeInfo().GetShape();
	if( shape.size() == 3 )
	{
		return Box2i( V2i( 0 ), V2i( shape[1], shape[2] ) );
	}
	else if( shape.size() == 4 )
	{
		return Box2i( V2i( 0 ), V2i( shape[2], shape[3] ) );
	}
	else
	{
		throw IECore::Exception( "Expected tensor with 3 or 4 dimensions" );
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

void TensorToImage::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	FlatImageSource::affects( input, outputs );

	if( input == channelsPlug() )
	{
		outputs.push_back( outPlug()->channelNamesPlug() );
	}

	if( input == tensorPlug() )
	{
		outputs.push_back( outPlug()->dataWindowPlug() );
	}

	if( input == tensorPlug() || input == channelsPlug() )
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
}

Imath::Box2i TensorToImage::computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	ConstTensorDataPtr tensor = tensorPlug()->getValue();
	return dataWindow( tensor.get() );
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
	}

	h.append( context->get<string>( ImagePlug::channelNameContextName ) );
	h.append( context->get<V2i>( ImagePlug::tileOriginContextName ) );
}

IECore::ConstFloatVectorDataPtr TensorToImage::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	ConstTensorDataPtr tensorData;
	ConstStringVectorDataPtr channelsData;
	{
		ImagePlug::GlobalScope globalScope( context );
		tensorData = tensorPlug()->getValue();
		channelsData = channelsPlug()->getValue();
	}

	const auto channelIt = std::find( channelsData->readable().begin(), channelsData->readable().end(), channelName );
	if( channelIt == channelsData->readable().end() )
	{
		throw IECore::Exception( fmt::format( "Invalid channel \"{}\"", channelName ) );
	}
	const size_t channelIndex = channelIt - channelsData->readable().begin();

	FloatVectorDataPtr outData = new FloatVectorData;
	vector<float> &out = outData->writable();

	const Box2i dataWindow = ::dataWindow( tensorData.get() );
	const Box2i tileBound( tileOrigin, tileOrigin + V2i( ImagePlug::tileSize() ) );
	const Box2i validTileBound = BufferAlgo::intersection( dataWindow, tileBound );
	out.resize( ImagePlug::tileSize() * ImagePlug::tileSize() );

	const size_t channelOffset = dataWindow.size().x * dataWindow.size().y * channelIndex;
	const float *sourceData = tensorData->value.GetTensorData<float>() + channelOffset;

	for( V2i p = validTileBound.min; p.y < validTileBound.max.y ; ++p.y )
	{
		const size_t srcIndex = BufferAlgo::index( V2i( p.x, dataWindow.max.y - p.y - 1 ), dataWindow );
		const size_t dstIndex = BufferAlgo::index( p, tileBound );
		std::copy(
			sourceData + srcIndex,
			sourceData + srcIndex + validTileBound.size().x,
			out.begin() + dstIndex
		);
	}

	return outData;
}
