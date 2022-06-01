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

#include "GafferImage/Mix.h"

#include "GafferImage/ImageAlgo.h"

#include "Gaffer/ArrayPlug.h"
#include "Gaffer/Context.h"

#include "IECore/BoxOps.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

GAFFER_NODE_DEFINE_TYPE( Mix );

size_t Mix::g_firstPlugIndex = 0;

Mix::Mix( const std::string &name )
	:	ImageProcessor( name, 2, 2 )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ImagePlug( "mask", Gaffer::Plug::In ) );

	addChild( new FloatPlug( "mix", Plug::In, 1.0f, 0.0f, 1.0f ) );

	addChild( new StringPlug( "maskChannel", Plug::In, "A") );

	// We don't ever want to change these, so we make pass-through connections.
	outPlug()->formatPlug()->setInput( inPlug()->formatPlug() );
	outPlug()->metadataPlug()->setInput( inPlug()->metadataPlug() );
}

Mix::~Mix()
{
}

GafferImage::ImagePlug *Mix::maskPlug()
{
	return getChild<ImagePlug>( g_firstPlugIndex );
}

const GafferImage::ImagePlug *Mix::maskPlug() const
{
	return getChild<ImagePlug>( g_firstPlugIndex );
}

Gaffer::FloatPlug *Mix::mixPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::FloatPlug *Mix::mixPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 1 );
}

Gaffer::StringPlug *Mix::maskChannelPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::StringPlug *Mix::maskChannelPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

void Mix::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ImageProcessor::affects( input, outputs );

	if( input == maskChannelPlug() || input == mixPlug() || input == maskPlug()->channelDataPlug() )
	{
		outputs.push_back( outPlug()->channelDataPlug() );

		// The data window and channel names are only affected by the mix
		// because of the pass through if mix is 0, or mix is 1 and mask is unconnected
		outputs.push_back( outPlug()->dataWindowPlug() );
		outputs.push_back( outPlug()->channelNamesPlug() );
	}
	else if( input == maskPlug()->dataWindowPlug() )
	{
		outputs.push_back( outPlug()->dataWindowPlug() );
		outputs.push_back( outPlug()->channelDataPlug() );
	}
	else if( input == maskPlug()->deepPlug() || input == maskPlug()->sampleOffsetsPlug() )
	{
		outputs.push_back( outPlug()->channelDataPlug() );
	}
	else if( input == outPlug()->deepPlug() || input == outPlug()->sampleOffsetsPlug() )
	{
		outputs.push_back( outPlug()->channelDataPlug() );
	}
	else if( const ImagePlug *inputImage = input->parent<ImagePlug>() )
	{
		if( inputImage->parent<ArrayPlug>() == inPlugs() )
		{
			outputs.push_back( outPlug()->getChild<ValuePlug>( input->getName() ) );
			if( input == inputImage->dataWindowPlug() )
			{
				outputs.push_back( outPlug()->channelDataPlug() );
			}
		}
	}
}

void Mix::hashDataWindow( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	const float mix = mixPlug()->getValue();
	if( mix == 0.0f )
	{
		h = inPlugs()->getChild< ImagePlug>( 0 )->dataWindowPlug()->hash();
		return;
	}
	else if( mix == 1.0f && !maskPlug()->getInput<ValuePlug>() )
	{
		h = inPlugs()->getChild< ImagePlug >( 1 )->dataWindowPlug()->hash();
		return;
	}

	ImageProcessor::hashDataWindow( output, context, h );

	for( ImagePlug::Iterator it( inPlugs() ); !it.done(); ++it )
	{
		(*it)->dataWindowPlug()->hash( h );
	}
}

Imath::Box2i Mix::computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	const float mix = mixPlug()->getValue();
	if( mix == 0.0f )
	{
		return inPlugs()->getChild< ImagePlug>( 0 )->dataWindowPlug()->getValue();
	}
	else if( mix == 1.0f && !maskPlug()->getInput<ValuePlug>() )
	{
		return inPlugs()->getChild< ImagePlug >( 1 )->dataWindowPlug()->getValue();
	}

	Imath::Box2i dataWindow;
	for( ImagePlug::Iterator it( inPlugs() ); !it.done(); ++it )
	{
		// We don't need to check that the plug is connected here as unconnected plugs don't have data windows.
		dataWindow.extendBy( (*it)->dataWindowPlug()->getValue() );
	}


	return dataWindow;
}

void Mix::hashChannelNames( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	const float mix = mixPlug()->getValue();
	if( mix == 0.0f )
	{
		h = inPlugs()->getChild< ImagePlug>( 0 )->channelNamesPlug()->hash();
		return;
	}
	else if( mix == 1.0f && !maskPlug()->getInput<ValuePlug>() )
	{
		h = inPlugs()->getChild< ImagePlug >( 1 )->channelNamesPlug()->hash();
		return;
	}

	ImageProcessor::hashChannelNames( output, context, h );

	for( ImagePlug::Iterator it( inPlugs() ); !it.done(); ++it )
	{
		if( (*it)->getInput<ValuePlug>() )
		{
			(*it)->channelNamesPlug()->hash( h );
		}
	}
}

IECore::ConstStringVectorDataPtr Mix::computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	const float mix = mixPlug()->getValue();
	if( mix == 0.0f )
	{
		return inPlugs()->getChild< ImagePlug>( 0 )->channelNamesPlug()->getValue();
	}
	else if( mix == 1.0f && !maskPlug()->getInput<ValuePlug>() )
	{
		return inPlugs()->getChild< ImagePlug >( 1 )->channelNamesPlug()->getValue();
	}

	IECore::StringVectorDataPtr outChannelStrVectorData( new IECore::StringVectorData() );
	std::vector<std::string> &outChannels( outChannelStrVectorData->writable() );

	for( ImagePlug::Iterator it( inPlugs() ); !it.done(); ++it )
	{
		if( (*it)->getInput<ValuePlug>() )
		{
			IECore::ConstStringVectorDataPtr inChannelStrVectorData((*it)->channelNamesPlug()->getValue() );
			const std::vector<std::string> &inChannels( inChannelStrVectorData->readable() );
			for ( std::vector<std::string>::const_iterator cIt( inChannels.begin() ); cIt != inChannels.end(); ++cIt )
			{
				if ( std::find( outChannels.begin(), outChannels.end(), *cIt ) == outChannels.end() )
				{
					outChannels.push_back( *cIt );
				}
			}
		}
	}

	if ( !outChannels.empty() )
	{
		return outChannelStrVectorData;
	}

	return inPlug()->channelNamesPlug()->defaultValue();
}

void Mix::hashChannelData( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	const float mix = mixPlug()->getValue();

	const ImagePlug *inputs[2] = { inPlugs()->getChild< ImagePlug>( 0 ), inPlugs()->getChild< ImagePlug >( 1 ) };

	if( mix == 0.0f )
	{
		h = inputs[0]->channelDataPlug()->hash();
		return;
	}
	else if( mix == 1.0f && !maskPlug()->getInput<ValuePlug>() )
	{
		h = inputs[1]->channelDataPlug()->hash();
		return;
	}

	ImageProcessor::hashChannelData( output, context, h );
	h.append( mix );

	const std::string channelName = context->get<std::string>( ImagePlug::channelNameContextName );
	const V2i tileOrigin = context->get<V2i>( ImagePlug::tileOriginContextName );
	const Box2i tileBound( tileOrigin, tileOrigin + V2i( ImagePlug::tileSize() ) );

	std::string maskChannel;
	Box2i maskValidBound;
	Box2i validBound[2] = { Box2i(), Box2i() };

	{
		// Start by grabbing all the plug values we need that are global
		ImagePlug::ChannelDataScope c( Context::current() );
		c.remove( ImagePlug::channelNameContextName );
		c.remove( ImagePlug::tileOriginContextName );
		maskChannel = maskChannelPlug()->getValue();
		if( maskPlug()->getInput<ValuePlug>() &&
			ImageAlgo::channelExists( maskPlug()->channelNamesPlug()->getValue()->readable(), maskChannel ) )
		{
			maskValidBound = boxIntersection( tileBound, maskPlug()->dataWindowPlug()->getValue() );
		}
		h.append( maskValidBound.min - tileOrigin );
		h.append( maskValidBound.max - tileOrigin );

		for( int i = 0; i < 2; i++ )
		{
			if(
				inputs[i]->getInput<ValuePlug>() &&
				ImageAlgo::channelExists( inputs[i]->channelNamesPlug()->getValue()->readable(), channelName )
			)
			{
				validBound[i] = boxIntersection( tileBound, inputs[i]->dataWindowPlug()->getValue() );
			}

			// The hash of the per tile channel data we include below represents just the data in
			// the tile itself, and takes no account of the possibility that parts of the
			// tile may be outside of the data window. This simplifies the implementation of
			// nodes like Constant (where all tiles are identical, even the edge tiles) and
			// Crop (which does no processing of tiles at all). For most nodes this doesn't
			// matter, because they don't change the data window, or they use a Sampler to
			// deal with invalid pixels. But because our data window is the union of all
			// input data windows, we may be using/revealing the invalid parts of a tile. We
			// deal with this in computeChannelData() by treating the invalid parts as black,
			// and must therefore hash in the valid bound here to take that into account.
			//
			// Note that validBound only matters in relation to the channel data for this tile though,
			// so we can hash it in relation to the tile origin, providing a small speedup by allowing
			// reuse of constant tiles ( 20% speedup in testFuzzDataWindows )
			h.append( validBound[i].min - tileOrigin );
			h.append( validBound[i].max - tileOrigin );
		}
		outPlug()->deepPlug()->hash( h );
		maskPlug()->deepPlug()->hash( h );

		// The sample offsets need to be accessed in a context with tileOrigin, but without the channel name
		c.setTileOrigin( &tileOrigin );
		outPlug()->sampleOffsetsPlug()->hash( h );
		maskPlug()->sampleOffsetsPlug()->hash( h );
	}

	ConstFloatVectorDataPtr maskData = nullptr;
	if( !BufferAlgo::empty( maskValidBound ) )
	{
		h.append(  maskPlug()->channelDataHash( maskChannel, tileOrigin ) );
	}

	for( int i = 0; i < 2; i++ )
	{
		if( !BufferAlgo::empty( validBound[i] ) )
		{
			inputs[i]->channelDataPlug()->hash( h );
		}
	}
}

IECore::ConstFloatVectorDataPtr Mix::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{

	const float mix = mixPlug()->getValue();

	const ImagePlug *inputs[2] = { inPlugs()->getChild< ImagePlug>( 0 ), inPlugs()->getChild< ImagePlug >( 1 ) };

	if( mix == 0.0f )
	{
		return inputs[ 0 ]->channelDataPlug()->getValue();
	}
	else if( mix == 1.0f && !maskPlug()->getInput<ValuePlug>() )
	{
		return inputs[ 1 ]->channelDataPlug()->getValue();
	}

	const Box2i tileBound( tileOrigin, tileOrigin + V2i( ImagePlug::tileSize() ) );

	bool deep;
	IECore::ConstIntVectorDataPtr sampleOffsetsData;
	Box2i validBound[2] = { Box2i(), Box2i() };

	std::string maskChannel;
	Box2i maskValidBound;
	bool hasMask = false;
	bool maskDeep;
	{
		// Start by grabbing all the plug values we need that are global
		ImagePlug::ChannelDataScope c( Context::current() );
		c.remove( ImagePlug::channelNameContextName );
		c.remove( ImagePlug::tileOriginContextName );

		deep = outPlug()->deepPlug()->getValue();
		maskDeep = maskPlug()->deepPlug()->getValue();
		if( maskDeep )
		{
			if( !deep )
			{
				throw IECore::Exception( "Cannot use deep mask when Mixing flat images." );
			}
		}

		for( int i = 0; i < 2; i++ )
		{
			if( ImageAlgo::channelExists( inputs[i]->channelNamesPlug()->getValue()->readable(), channelName ) )
			{
				validBound[i] = boxIntersection( tileBound, inputs[i]->dataWindowPlug()->getValue() );
			}
		}

		maskChannel = maskChannelPlug()->getValue();
		if( maskPlug()->getInput<ValuePlug>() &&
			ImageAlgo::channelExists( maskPlug()->channelNamesPlug()->getValue()->readable(), maskChannel ) )
		{
			hasMask = true;
			maskValidBound = boxIntersection( tileBound, maskPlug()->dataWindowPlug()->getValue() );
			if( BufferAlgo::empty( maskValidBound ) )
			{
				if( BufferAlgo::empty( validBound[0] ) )
				{
					return ImagePlug::blackTile();
				}
				else if( validBound[0] == tileBound )
				{
					// If the whole tile is within the input data window, we can just pass through
					// the input. Otherwise, we need to hit the slower path below to trim out the
					// part of the input which is outside the input's data window.
					return inputs[ 0 ]->channelData( channelName, tileOrigin );
				}
			}
		}

		// The sample offsets need to be accessed in a context with tileOrigin, but without the channel name
		c.setTileOrigin( &tileOrigin );

		if( deep )
		{
			sampleOffsetsData = outPlug()->sampleOffsetsPlug()->getValue();
		}

		if( maskDeep )
		{
			IECore::ConstIntVectorDataPtr maskSampleOffsetsData = maskPlug()->sampleOffsetsPlug()->getValue();
			ImageAlgo::throwIfSampleOffsetsMismatch( sampleOffsetsData.get(), maskSampleOffsetsData.get(), tileOrigin, "Mix : When using a deep mask, samples must match the inputs." );
		}
	}

	ConstFloatVectorDataPtr maskData = nullptr;
	if( !BufferAlgo::empty( maskValidBound ) )
	{
		maskData = maskPlug()->channelData( maskChannel, tileOrigin );
	}

	ConstFloatVectorDataPtr channelData[2] = { nullptr, nullptr };

	for( int i = 0; i < 2; i++ )
	{
		if( !BufferAlgo::empty( validBound[i] ) )
		{
			channelData[i] = inputs[i]->channelDataPlug()->getValue();
		}
	}


	FloatVectorDataPtr resultData = new FloatVectorData();
	int resultSize = channelData[0] ? channelData[0]->readable().size() : ImagePlug::tilePixels();
	resultData->writable().resize( resultSize, 0.0f );
	float *R = &resultData->writable().front();
	const float *A = channelData[0] ? &channelData[0]->readable().front() : nullptr;
	const float *B = channelData[1] ? &channelData[1]->readable().front() : nullptr;
	const float *M = maskData ? &maskData->readable().front() : nullptr;

	// For the common case where we're completely filled, we don't need to worry about
	// the bounds, and can use a much simpler loop
	bool useFastPath = validBound[0] == tileBound && validBound[1] == tileBound;
	if( maskData )
	{
		useFastPath &= maskValidBound == tileBound;
	}

	// For deep images, the logic is different.  We don't modify the sample offsets, so we
	// always process the full tile.  We use the simple path unless we are promoting
	// the mask from flat to deep
	if( deep )
	{
		useFastPath = maskData ? maskDeep : true;
	}

	if( useFastPath )
	{
		if( M )
		{
			if( A && B )
			{
				for( int j = 0; j < resultSize; j++ )
				{
					float m = mix * std::max( 0.0f, std::min( 1.0f, *M ) );
					*R = *A * ( 1 - m ) + *B * m;
					++R; ++A; ++B; ++M;
				}
			}
			else if( A )
			{
				for( int j = 0; j < resultSize; j++ )
				{
					float m = mix * std::max( 0.0f, std::min( 1.0f, *M ) );
					*R = *A * ( 1 - m );
					++R; ++A; ++M;
				}
			}
			else if( B )
			{
				for( int j = 0; j < resultSize; j++ )
				{
					float m = mix * std::max( 0.0f, std::min( 1.0f, *M ) );
					*R = *B * m;
					++R; ++B; ++M;
				}
			}
		}
		else
		{
			if( A && B )
			{
				for( int j = 0; j < resultSize; j++ )
				{
					*R = *A * ( 1 - mix ) + *B * mix;
					++R; ++A; ++B;
				}
			}
			else if( A )
			{
				for( int j = 0; j < resultSize; j++ )
				{
					*R = *A * ( 1 - mix );
					++R; ++A;
				}
			}
			else if( B )
			{
				for( int j = 0; j < resultSize; j++ )
				{
					*R = *B * mix;
					++R; ++B;
				}
			}
		}
	}
	else if( !deep )
	{
		for( int y = tileBound.min.y; y < tileBound.max.y; ++y )
		{
			const bool yValidIn0 = y >= validBound[0].min.y && y < validBound[0].max.y;
			const bool yValidIn1 = y >= validBound[1].min.y && y < validBound[1].max.y;
			const bool yValidMask = y >= maskValidBound.min.y && y < maskValidBound.max.y;

			for( int x = tileBound.min.x; x < tileBound.max.x; ++x )
			{
				float a = 0;
				if( yValidIn0 && x >= validBound[0].min.x && x < validBound[0].max.x )
				{
					a = *A;
				}

				float b = 0;
				if( yValidIn1 && x >= validBound[1].min.x && x < validBound[1].max.x )
				{
					b = *B;
				}

				float m = hasMask ? 0.0f : mix;
				if( M )
				{
					if( yValidMask && x >= maskValidBound.min.x && x < maskValidBound.max.x )
					{
						m = mix * std::max( 0.0f, std::min( 1.0f, *M ) );
					}
					++M;
				}

				*R = a * ( 1 - m ) + b * m;

				++R; ++A; ++B;
			}
		}
	}
	else
	{
		const int *S = &sampleOffsetsData->readable().front();
		int prevOffset = 0;
		for( int y = tileBound.min.y; y < tileBound.max.y; ++y )
		{
			const bool yValidMask = y >= maskValidBound.min.y && y < maskValidBound.max.y;

			for( int x = tileBound.min.x; x < tileBound.max.x; ++x )
			{
				int offset = *S;

				// Here, we can assume that we are using a flat mask, because otherwise we
				// would have taken the simple path above
				float m = 0;
				if( yValidMask && x >= maskValidBound.min.x && x < maskValidBound.max.x )
				{
					m = mix * std::max( 0.0f, std::min( 1.0f, *M ) );
				}

				if( A && B )
				{
					for( int j = prevOffset; j < offset; j++ )
					{
						*R = (*A) * ( 1 - m ) + (*B) * m;
						++R; ++A; ++B;
					}
				}
				else if( A )
				{
					for( int j = prevOffset; j < offset; j++ )
					{
						*R = (*A) * ( 1 - m );
						++R; ++A;
					}
				}
				else if( B )
				{
					for( int j = prevOffset; j < offset; j++ )
					{
						*R = (*B) * m;
						++R; ++B;
					}
				}

				prevOffset = offset;
				++M; ++S;
			}
		}
	}

	return resultData;
}

void Mix::hashDeep( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hashDeep( parent, context, h );

	inPlugs()->getChild< ImagePlug >( 0 )->deepPlug()->hash( h );
	inPlugs()->getChild< ImagePlug >( 1 )->deepPlug()->hash( h );
}

bool Mix::computeDeep( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	int deepA = inPlugs()->getChild< ImagePlug >( 0 )->deepPlug()->getValue();
	int deepB = inPlugs()->getChild< ImagePlug >( 1 )->deepPlug()->getValue();
	if( deepA != deepB )
	{
		throw IECore::Exception( "Cannot mix between deep and flat image." );
	}
	return deepA;
}

void Mix::hashSampleOffsets( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hashSampleOffsets( parent, context, h );

	inPlugs()->getChild< ImagePlug >( 0 )->sampleOffsetsPlug()->hash( h );
	inPlugs()->getChild< ImagePlug >( 1 )->sampleOffsetsPlug()->hash( h );
}

IECore::ConstIntVectorDataPtr Mix::computeSampleOffsets( const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	IECore::ConstIntVectorDataPtr sampleOffsetsDataA = inPlugs()->getChild< ImagePlug >( 0 )->sampleOffsetsPlug()->getValue();
	IECore::ConstIntVectorDataPtr sampleOffsetsDataB = inPlugs()->getChild< ImagePlug >( 1 )->sampleOffsetsPlug()->getValue();

	ImageAlgo::throwIfSampleOffsetsMismatch( sampleOffsetsDataA.get(), sampleOffsetsDataB.get(), tileOrigin, "SampleOffsets on inputs to Mix must match." );

	return sampleOffsetsDataA;
}
