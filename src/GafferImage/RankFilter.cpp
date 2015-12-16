//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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

#include "GafferImage/RankFilter.h"

#include "GafferImage/Sampler.h"

#include "Gaffer/Context.h"

#include <algorithm>
#include <climits>

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( RankFilter );

size_t RankFilter::g_firstPlugIndex = 0;

RankFilter::RankFilter( const std::string &name, Mode mode )
	:   FlatImageProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new V2iPlug( "radius", Plug::In, V2i( 0 ), V2i( 0 ) ) );
	addChild( new IntPlug( "boundingMode", Plug::In, Sampler::Black, Sampler::Black, Sampler::Clamp ) );
	addChild( new BoolPlug( "expandDataWindow" ) );
	addChild( new StringPlug( "masterChannel" ) );
	addChild( new V2iVectorDataPlug( "__pixelOffsets", Plug::Out, new V2iVectorData ) );

	outPlug()->formatPlug()->setInput( inPlug()->formatPlug() );
	outPlug()->metadataPlug()->setInput( inPlug()->metadataPlug() );
	outPlug()->channelNamesPlug()->setInput( inPlug()->channelNamesPlug() );
	m_mode = mode;
}

RankFilter::~RankFilter()
{
}

Gaffer::V2iPlug *RankFilter::radiusPlug()
{
	return getChild<V2iPlug>( g_firstPlugIndex );
}

const Gaffer::V2iPlug *RankFilter::radiusPlug() const
{
	return getChild<V2iPlug>( g_firstPlugIndex );
}

Gaffer::IntPlug *RankFilter::boundingModePlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::IntPlug *RankFilter::boundingModePlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

Gaffer::BoolPlug *RankFilter::expandDataWindowPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::BoolPlug *RankFilter::expandDataWindowPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 2 );
}

Gaffer::StringPlug *RankFilter::masterChannelPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::StringPlug *RankFilter::masterChannelPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 3 );
}

Gaffer::V2iVectorDataPlug *RankFilter::pixelOffsetsPlug()
{
	return getChild<V2iVectorDataPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::V2iVectorDataPlug *RankFilter::pixelOffsetsPlug() const
{
	return getChild<V2iVectorDataPlug>( g_firstPlugIndex + 4 );
}


void RankFilter::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	FlatImageProcessor::affects( input, outputs );

	if(
		input == expandDataWindowPlug() ||
		input == inPlug()->dataWindowPlug() ||
		input->parent<V2iPlug>() == radiusPlug()
	)
	{
		outputs.push_back( outPlug()->dataWindowPlug() );
	}

	if(
		input == inPlug()->channelDataPlug() ||
		input->parent<V2iPlug>() == radiusPlug() ||
		input == boundingModePlug() ||
		input == masterChannelPlug()
	)
	{
		outputs.push_back( pixelOffsetsPlug() );
		outputs.push_back( outPlug()->channelDataPlug() );
	}
}

void RankFilter::hashDataWindow( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	const V2i radius = radiusPlug()->getValue();
	if( radius == V2i( 0 ) || !expandDataWindowPlug()->getValue() )
	{
		h = inPlug()->dataWindowPlug()->hash();
		return;
	}

	FlatImageProcessor::hashDataWindow( parent, context, h );
	h.append( radius );
}

Imath::Box2i RankFilter::computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	const V2i radius = radiusPlug()->getValue();
	if( radius == V2i( 0 ) || !expandDataWindowPlug()->getValue() )
	{
		return inPlug()->dataWindowPlug()->getValue();
	}

	Box2i dataWindow = inPlug()->dataWindowPlug()->getValue();
	if( !BufferAlgo::empty( dataWindow ) )
	{
		dataWindow.min -= radius;
		dataWindow.max += radius;
	}
	return dataWindow;
}

void RankFilter::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	FlatImageProcessor::hash( output, context, h );
	if( output == pixelOffsetsPlug() )
	{
		const V2i radius = radiusPlug()->getValue();
		const V2i tileOrigin = context->get<V2i>( ImagePlug::tileOriginContextName );
		const Box2i tileBound( tileOrigin, tileOrigin + V2i( ImagePlug::tileSize() ) );
		const Box2i inputBound( tileBound.min - radius, tileBound.max + radius );

		Sampler sampler(
			inPlug(),
			// This plug should only be evaluated with channel name already set to the driver channel
			context->get<std::string>( ImagePlug::channelNameContextName ),
			inputBound,
			(Sampler::BoundingMode)boundingModePlug()->getValue()
		);
		sampler.hash( h );
		h.append( radius );
		h.append( tileOrigin );
	}
}

void RankFilter::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output == pixelOffsetsPlug() )
	{
		const V2i radius = radiusPlug()->getValue();
		const V2i tileOrigin = context->get<V2i>( ImagePlug::tileOriginContextName );
		const Box2i tileBound( tileOrigin, tileOrigin + V2i( ImagePlug::tileSize() ) );
		const Box2i inputBound( tileBound.min - radius, tileBound.max + radius );

		Sampler sampler(
			inPlug(),
			// This plug should only be evaluated with channel name already set to the driver channel
			context->get<std::string>( ImagePlug::channelNameContextName ),
			inputBound,
			(Sampler::BoundingMode)boundingModePlug()->getValue()
		);

		V2iVectorDataPtr resultData = new V2iVectorData;
		vector<V2i> &result = resultData->writable();
		result.reserve( ImagePlug::tileSize() * ImagePlug::tileSize() );

		vector<float> pixels( ( 1 + 2 * radius.x ) * ( 1 + 2 * radius.y ) );
		vector<float> sortPixels( ( 1 + 2 * radius.x ) * ( 1 + 2 * radius.y ) );
		vector<float>::iterator resultIt = sortPixels.begin() + sortPixels.size() / 2;

		V2i p;
		for( p.y = tileBound.min.y; p.y < tileBound.max.y; ++p.y )
		{
			for( p.x = tileBound.min.x; p.x < tileBound.max.x; ++p.x )
			{
				IECore::Canceller::check( context->canceller() );

				// Fill array with all nearby samples
				V2i o;
				vector<float>::iterator pixelsIt = pixels.begin();
				for( o.y = -radius.y; o.y <= radius.y; ++o.y )
				{
					for( o.x = -radius.x; o.x <= radius.x; ++o.x )
					{
						*pixelsIt++ = sampler.sample( p.x + o.x, p.y + o.y );
					}
				}

				switch( m_mode )
				{
					case MedianRank :
						// To compute the pixel offset to the rank in this channel,
						// we first compute the rank as usual
						std::copy (pixels.begin(), pixels.end(), sortPixels.begin());
						nth_element( sortPixels.begin(), resultIt, sortPixels.end() );
						break;
					case ErodeRank:
						resultIt = min_element( pixels.begin(), pixels.end() );
						break;
					case DilateRank:
						resultIt = max_element( pixels.begin(), pixels.end() );
						break;
				}
				// Now we rescan the array to find where the rank occured
				// In case there are multiple instances of an identical value,
				// we take whichever one is closest to the center
				V2i r( INT_MAX, INT_MAX );

				int closestMatch = INT_MAX;
				pixelsIt = pixels.begin();
				for( o.y = -radius.y; o.y <= radius.y; ++o.y )
				{
					for( o.x = -radius.x; o.x <= radius.x; ++o.x )
					{
						// If we've found a pixel which matches the rank value
						if( *pixelsIt++ == *resultIt )
						{
							int absX = abs( o.x );
							int absY = abs( o.y );

							// Simple heuristic for distance from the center
							// Weight Chebyshev distance heavily, followed by Manhattan distance to resolve ties
							// The specifics don't matter too much as long as we generally prefer points near the
							// center in case of ties.  Chebyshev distance of N is equivalent to saying "This
							// would be within the range of a rank filter of radius N"
							int distance = 100 * max( absX, absY ) + absX + absY;

							if( distance < closestMatch )
							{
								closestMatch = distance;

								// Store the offset to the rank pixel
								r = o;
							}
						}
					}
				}

				// One of the pixels must match the rank
				assert( r != V2i( INT_MAX, INT_MAX ) );

				result.push_back( r );
			}
		}

		static_cast<V2iVectorDataPlug *>( output )->setValue( resultData );
		return;
	}
	else
	{
		FlatImageProcessor::compute( output, context );
	}
}


void RankFilter::hashChannelData( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	const V2i radius = radiusPlug()->getValue();
	if( radius == V2i( 0 ) )
	{
		h = inPlug()->channelDataPlug()->hash();
		return;
	}

	FlatImageProcessor::hashChannelData( parent, context, h );

	const V2i tileOrigin = context->get<V2i>( ImagePlug::tileOriginContextName );
	const Box2i tileBound( tileOrigin, tileOrigin + V2i( ImagePlug::tileSize() ) );
	const Box2i inputBound( tileBound.min - radius, tileBound.max + radius );

	Sampler sampler(
		inPlug(),
		context->get<std::string>( ImagePlug::channelNameContextName ),
		inputBound,
		(Sampler::BoundingMode)boundingModePlug()->getValue()
	);
	sampler.hash( h );
	h.append( radius );
	h.append( tileOrigin );

	const std::string &masterChannel = masterChannelPlug()->getValue();
	if( masterChannel != "" )
	{
		ImagePlug::ChannelDataScope pixelOffsetsScope( context );
		pixelOffsetsScope.setChannelName( masterChannel );

		pixelOffsetsPlug()->hash( h );
	}

}

IECore::ConstFloatVectorDataPtr RankFilter::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	const V2i radius = radiusPlug()->getValue();
	if( radius == V2i( 0 ) )
	{
		return inPlug()->channelDataPlug()->getValue();
	}

	const Box2i tileBound( tileOrigin, tileOrigin + V2i( ImagePlug::tileSize() ) );
	const Box2i inputBound( tileBound.min - radius, tileBound.max + radius );

	Sampler sampler(
		inPlug(),
		channelName,
		inputBound,
		(Sampler::BoundingMode)boundingModePlug()->getValue()
	);

	FloatVectorDataPtr resultData = new FloatVectorData;
	vector<float> &result = resultData->writable();
	result.reserve( ImagePlug::tileSize() * ImagePlug::tileSize() );

	const std::string &masterChannel = masterChannelPlug()->getValue();
	if( masterChannel != "" )
	{
		ConstV2iVectorDataPtr pixelOffsets;
		{
			ImagePlug::ChannelDataScope pixelOffsetsScope( context );
			pixelOffsetsScope.setChannelName( masterChannel );

			pixelOffsets = pixelOffsetsPlug()->getValue();
		}

		vector<V2i>::const_iterator offsetsIt = pixelOffsets->readable().begin();
		V2i p;
		for( p.y = tileBound.min.y; p.y < tileBound.max.y; ++p.y )
		{
			for( p.x = tileBound.min.x; p.x < tileBound.max.x; ++p.x )
			{
				const V2i &offset = *offsetsIt++;
				V2i sourcePixel = p + offset;
				result.push_back( sampler.sample( sourcePixel.x, sourcePixel.y ) );
			}
		}

		return resultData;
	}

	vector<float> pixels( ( 1 + 2 * radius.x ) * ( 1 + 2 * radius.y ) );
	vector<float>::iterator resultIt = pixels.begin() + pixels.size() / 2;

	V2i p;
	for( p.y = tileBound.min.y; p.y < tileBound.max.y; ++p.y )
	{
		for( p.x = tileBound.min.x; p.x < tileBound.max.x; ++p.x )
		{
			IECore::Canceller::check( context->canceller() );

			V2i o;
			vector<float>::iterator pixelsIt = pixels.begin();
			for( o.y = -radius.y; o.y <= radius.y; ++o.y )
			{
				for( o.x = -radius.x; o.x <= radius.x; ++o.x )
				{
					*pixelsIt++ = sampler.sample( p.x + o.x, p.y + o.y );
				}
			}
			switch( m_mode )
			{
				case MedianRank:
					nth_element( pixels.begin(), resultIt, pixels.end() );
					break;
				case ErodeRank:
					resultIt = min_element( pixels.begin(), pixels.end() );
					break;
				case DilateRank:
					resultIt = max_element( pixels.begin(), pixels.end() );
					break;
			}
			result.push_back( *resultIt );
		}
	}

	return resultData;
}
