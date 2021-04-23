//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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

#include "GafferImage/Offset.h"

#include "GafferImage/ImageAlgo.h"
#include "GafferImage/BufferAlgo.h"

#include "Gaffer/Context.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

//////////////////////////////////////////////////////////////////////////
// Offset node
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( Offset );

size_t Offset::g_firstPlugIndex = 0;

Offset::Offset( const std::string &name )
	:	ImageProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new V2iPlug( "offset" ) );

	outPlug()->formatPlug()->setInput( inPlug()->formatPlug() );
	outPlug()->metadataPlug()->setInput( inPlug()->metadataPlug() );
	outPlug()->channelNamesPlug()->setInput( inPlug()->channelNamesPlug() );
	outPlug()->deepPlug()->setInput( inPlug()->deepPlug() );
}

Offset::~Offset()
{
}

Gaffer::V2iPlug *Offset::offsetPlug()
{
	return getChild<V2iPlug>( g_firstPlugIndex );
}

const Gaffer::V2iPlug *Offset::offsetPlug() const
{
	return getChild<V2iPlug>( g_firstPlugIndex );
}

void Offset::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ImageProcessor::affects( input, outputs );

	if(
		input->parent<Plug>() == offsetPlug() ||
		input == inPlug()->channelDataPlug() ||
		input == inPlug()->dataWindowPlug() ||
		input == inPlug()->deepPlug()
	)
	{
		outputs.push_back( outPlug()->channelDataPlug() );
	}

	if(
		input->parent<Plug>() == offsetPlug() ||
		input == inPlug()->sampleOffsetsPlug() ||
		input == inPlug()->dataWindowPlug() ||
		input == inPlug()->deepPlug()
	)
	{
		outputs.push_back( outPlug()->sampleOffsetsPlug() );
	}

	if(
		input->parent<Plug>() == offsetPlug() ||
		input == inPlug()->dataWindowPlug()
	)
	{
		outputs.push_back( outPlug()->dataWindowPlug() );
	}
}

void Offset::hashDataWindow( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	const V2i offset = offsetPlug()->getValue();
	if( offset == V2i( 0 ) )
	{
		h = inPlug()->dataWindowPlug()->hash();
	}
	else
	{
		ImageProcessor::hashDataWindow( parent, context, h );
		inPlug()->dataWindowPlug()->hash( h );
		offsetPlug()->hash( h );
	}
}

Imath::Box2i Offset::computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	Box2i dataWindow = inPlug()->dataWindowPlug()->getValue();
	if( !dataWindow.isEmpty() )
	{
		const V2i offset = offsetPlug()->getValue();
		dataWindow.min += offset;
		dataWindow.max += offset;
	}
	return dataWindow;
}

void Offset::hashChannelData( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImagePlug::ChannelDataScope offsetScope( context );

	const V2i offset = offsetPlug()->getValue();
	const V2i tileOrigin = context->get<V2i>( ImagePlug::tileOriginContextName );
	if( offset.x % ImagePlug::tileSize() == 0 && offset.y % ImagePlug::tileSize() == 0 )
	{
		V2i offsetOrigin = tileOrigin - offset;
		offsetScope.setTileOrigin( &offsetOrigin );
		h = inPlug()->channelDataPlug()->hash();
	}
	else
	{
		ImageProcessor::hashChannelData( parent, context, h );

		const Box2i inDataWindow = inPlug()->dataWindow();
		const Box2i outTileBound( tileOrigin, tileOrigin + V2i( ImagePlug::tileSize() ) );
		const Box2i inBound = BufferAlgo::intersection(
			inDataWindow,
			Box2i( outTileBound.min - offset, outTileBound.max - offset )
		);

		// Note that two differing output tiles could depend on the same input tile, for
		// example if the input image is small enough that there is a single valid tile.
		// Hash in the bound to distinguish the output tiles in this case
		h.append( inBound );

		V2i inTileOrigin;
		for( inTileOrigin.y = ImagePlug::tileOrigin( inBound.min ).y; inTileOrigin.y < inBound.max.y; inTileOrigin.y += ImagePlug::tileSize() )
		{
			for( inTileOrigin.x = ImagePlug::tileOrigin( inBound.min ).x; inTileOrigin.x < inBound.max.x; inTileOrigin.x += ImagePlug::tileSize() )
			{
				offsetScope.setTileOrigin( &inTileOrigin );
				inPlug()->channelDataPlug()->hash( h );
			}
		}

		h.append( offset );

		// For performance reasons, instead of including hashing sampleOffsets for every input tile, we
		// just include the output sample offsets, which already depends on the input sample offsets and
		// the deep plug
		offsetScope.setTileOrigin( &tileOrigin );
		offsetScope.remove( ImagePlug::channelNameContextName );
		outPlug()->sampleOffsetsPlug()->hash( h );
	}
}

IECore::ConstFloatVectorDataPtr Offset::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	ImagePlug::ChannelDataScope offsetScope( context );

	const V2i offset = offsetPlug()->getValue();
	if( offset.x % ImagePlug::tileSize() == 0 && offset.y % ImagePlug::tileSize() == 0 )
	{
		V2i offsetOrigin = tileOrigin - offset;
		offsetScope.setTileOrigin( &offsetOrigin );
		return inPlug()->channelDataPlug()->getValue();
	}

	bool deep = inPlug()->deep();

	const Box2i inDataWindow = inPlug()->dataWindow();

	const Box2i inBound = BufferAlgo::intersection(
		inDataWindow,
		Box2i( tileOrigin - offset, tileOrigin + V2i( ImagePlug::tileSize() ) - offset )
	);

	FloatVectorDataPtr outData = new FloatVectorData;
	ConstIntVectorDataPtr outSampleOffsetsData;
	if( !deep )
	{
		outData->writable().resize( ImagePlug::tilePixels() );
	}
	else
	{
		offsetScope.remove( ImagePlug::channelNameContextName );
		outSampleOffsetsData = outPlug()->sampleOffsetsPlug()->getValue();
		offsetScope.setChannelName( &channelName );
		outData->writable().resize( outSampleOffsetsData->readable().back() );
	}

	float *out = &outData->writable().front();

	V2i inTileOrigin;
	for( inTileOrigin.y = ImagePlug::tileOrigin( inBound.min ).y; inTileOrigin.y < inBound.max.y; inTileOrigin.y += ImagePlug::tileSize() )
	{
		for( inTileOrigin.x = ImagePlug::tileOrigin( inBound.min ).x; inTileOrigin.x < inBound.max.x; inTileOrigin.x += ImagePlug::tileSize() )
		{
			offsetScope.setTileOrigin( &inTileOrigin );
			ConstFloatVectorDataPtr inData = inPlug()->channelDataPlug()->getValue();
			const float *in = &inData->readable().front();

			const Box2i inTileBound( inTileOrigin, inTileOrigin + V2i( ImagePlug::tileSize() ) );
			const Box2i inRegion = BufferAlgo::intersection(
				inBound,
				inTileBound
			);

			const size_t scanlineLength = inRegion.size().x;
			if( !deep )
			{
				for( V2i inScanlineOrigin = inRegion.min; inScanlineOrigin.y < inRegion.max.y; inScanlineOrigin.y++ )
				{
					int inIndex = ImagePlug::pixelIndex( inScanlineOrigin, inTileOrigin );
					int outIndex = ImagePlug::pixelIndex( inScanlineOrigin + offset, tileOrigin );
					memcpy(
						// to
						out + outIndex,
						// from
						in + inIndex,
						sizeof( float ) * scanlineLength
					);
				}
			}
			else
			{
				offsetScope.remove( ImagePlug::channelNameContextName );
				ConstIntVectorDataPtr inSampleOffsetsData = inPlug()->sampleOffsetsPlug()->getValue();
				offsetScope.setChannelName( &channelName );
				const std::vector<int> &inSampleOffsets = inSampleOffsetsData->readable();
				const std::vector<int> &outSampleOffsets = outSampleOffsetsData->readable();
				for( V2i inScanlineOrigin = inRegion.min; inScanlineOrigin.y < inRegion.max.y; inScanlineOrigin.y++ )
				{
					int inIndex = ImagePlug::pixelIndex( inScanlineOrigin, inTileOrigin );
					int outIndex = ImagePlug::pixelIndex( inScanlineOrigin + offset, tileOrigin );

					int outOffset = outIndex > 0 ? outSampleOffsets[ outIndex - 1 ] : 0;
					int inOffset = inIndex > 0 ? inSampleOffsets[ inIndex - 1 ] : 0;

					int scanlineSamples = outSampleOffsets[outIndex + scanlineLength - 1] - outOffset;

					memcpy(
						// to
						out + outOffset,
						// from
						in + inOffset,
						sizeof( float ) * scanlineSamples
					);
				}
			}
		}
	}

	return outData;
}

void Offset::hashSampleOffsets( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImagePlug::ChannelDataScope offsetScope( context );

	if( !inPlug()->deep() )
	{
		h = ImagePlug::flatTileSampleOffsets()->Object::hash();
		return;
	}

	const V2i offset = offsetPlug()->getValue();
	const V2i tileOrigin = context->get<V2i>( ImagePlug::tileOriginContextName );
	if( offset.x % ImagePlug::tileSize() == 0 && offset.y % ImagePlug::tileSize() == 0 )
	{
		V2i offsetOrigin = tileOrigin - offset;
		offsetScope.setTileOrigin( &offsetOrigin );
		h = inPlug()->sampleOffsetsPlug()->hash();
	}
	else
	{
		ImageProcessor::hashSampleOffsets( parent, context, h );

		h.append( inPlug()->deepHash() );
		const Box2i inDataWindow = inPlug()->dataWindow();

		const Box2i outTileBound( tileOrigin, tileOrigin + V2i( ImagePlug::tileSize() ) );
		const Box2i inBound = BufferAlgo::intersection(
			inDataWindow,
			Box2i( outTileBound.min - offset, outTileBound.max - offset )
		);

		// Note that two differing output tiles could depend on the same input tile, for
		// example if the input image is small enough that there is a single valid tile.
		// Hash in the bound to distinguish the output tiles in this case
		h.append( inBound );

		V2i inTileOrigin;
		for( inTileOrigin.y = ImagePlug::tileOrigin( inBound.min ).y; inTileOrigin.y < inBound.max.y; inTileOrigin.y += ImagePlug::tileSize() )
		{
			for( inTileOrigin.x = ImagePlug::tileOrigin( inBound.min ).x; inTileOrigin.x < inBound.max.x; inTileOrigin.x += ImagePlug::tileSize() )
			{
				offsetScope.setTileOrigin( &inTileOrigin );
				inPlug()->sampleOffsetsPlug()->hash( h );
			}
		}

		h.append( offset );
	}
}

IECore::ConstIntVectorDataPtr Offset::computeSampleOffsets( const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	ImagePlug::ChannelDataScope offsetScope( context );

	if( !inPlug()->deep() )
	{
		return ImagePlug::flatTileSampleOffsets();
	}

	const V2i offset = offsetPlug()->getValue();
	if( ( offset.x % ImagePlug::tileSize() == 0 && offset.y % ImagePlug::tileSize() == 0 ) )
	{
		V2i offsetOrigin = tileOrigin - offset;
		offsetScope.setTileOrigin( &offsetOrigin );
		return inPlug()->sampleOffsetsPlug()->getValue();
	}


	Box2i inDataWindow = inPlug()->dataWindow();

	const Box2i inBound = BufferAlgo::intersection(
		inDataWindow,
		Box2i( tileOrigin - offset, tileOrigin + V2i( ImagePlug::tileSize() ) - offset )
	);

	IntVectorDataPtr outData = new IntVectorData;
	std::vector<int> &out = outData->writable();
	out.resize( ImagePlug::tilePixels(), 0 );

	V2i inTileOrigin;
	for( inTileOrigin.y = ImagePlug::tileOrigin( inBound.min ).y; inTileOrigin.y < inBound.max.y; inTileOrigin.y += ImagePlug::tileSize() )
	{
		for( inTileOrigin.x = ImagePlug::tileOrigin( inBound.min ).x; inTileOrigin.x < inBound.max.x; inTileOrigin.x += ImagePlug::tileSize() )
		{
			offsetScope.setTileOrigin( &inTileOrigin );
			ConstIntVectorDataPtr inData = inPlug()->sampleOffsetsPlug()->getValue();
			const std::vector<int> &in = inData->readable();

			const Box2i inTileBound( inTileOrigin, inTileOrigin + V2i( ImagePlug::tileSize() ) );
			const Box2i inRegion = BufferAlgo::intersection(
				inBound,
				inTileBound
			);

			const size_t scanlineLength = inRegion.size().x;
			for( V2i inScanlineOrigin = inRegion.min; inScanlineOrigin.y < inRegion.max.y; inScanlineOrigin.y++ )
			{
				int inIndex = ImagePlug::pixelIndex( inScanlineOrigin, inTileOrigin );
				int outIndex = ImagePlug::pixelIndex( inScanlineOrigin + offset, tileOrigin );
				int prevOffset = inIndex > 0 ? in[ inIndex - 1 ] : 0;
				for( unsigned int j = 0; j < scanlineLength; j++ )
				{
					int offset = in[ inIndex + j ];
					out[ outIndex + j ] = offset - prevOffset;
					prevOffset = offset;
				}
			}
		}
	}

	// out data is initially sample counts per pixel. These need to be turned into sample offsets.
	int prevOffset = 0;
	for( int i = 0; i < ImagePlug::tilePixels(); i++ )
	{
		prevOffset += out[i];
		out[i] = prevOffset;
	}

	return outData;
}
