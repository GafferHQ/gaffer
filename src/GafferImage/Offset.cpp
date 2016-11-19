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

#include "Gaffer/Context.h"

#include "GafferImage/Offset.h"
#include "GafferImage/ImageAlgo.h"
#include "GafferImage/BufferAlgo.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

//////////////////////////////////////////////////////////////////////////
// Utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

// Index of pixel within a buffer.
/// \todo Move to ImageAlgo?
size_t bufferIndex( const V2i &p, const Box2i &b )
{
	assert( contains( b, p ) );
	return
		( p.y - b.min.y ) * b.size().x +
		( p.x - b.min.x );
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// Offset node
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( Offset );

size_t Offset::g_firstPlugIndex = 0;

Offset::Offset( const std::string &name )
	:	ImageProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new V2iPlug( "offset" ) );

	outPlug()->formatPlug()->setInput( inPlug()->formatPlug() );
	outPlug()->metadataPlug()->setInput( inPlug()->metadataPlug() );
	outPlug()->channelNamesPlug()->setInput( inPlug()->channelNamesPlug() );
	outPlug()->deepStatePlug()->setInput( inPlug()->deepStatePlug() );
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
		input == inPlug()->sampleOffsetsPlug() ||
		input == inPlug()->deepStatePlug() ||
		input == inPlug()->dataWindowPlug() ||
		input == outPlug()->sampleOffsetsPlug()
	)
	{
		outputs.push_back( outPlug()->channelDataPlug() );
	}

	if(
		input->parent<Plug>() == offsetPlug() ||
		input == inPlug()->sampleOffsetsPlug() ||
		input == inPlug()->deepStatePlug() ||
		input == inPlug()->dataWindowPlug()
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
	const V2i offset = offsetPlug()->getValue();
	dataWindow.min += offset;
	dataWindow.max += offset;
	return dataWindow;
}

void Offset::hashSampleOffsets( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ContextPtr offsetContext = new Context( *context, Context::Borrowed );
	Context::Scope scope( offsetContext.get() );

	const V2i offset = offsetPlug()->getValue();
	const V2i tileOrigin = context->get<V2i>( ImagePlug::tileOriginContextName );
	if( offset.x % ImagePlug::tileSize() == 0 && offset.y % ImagePlug::tileSize() == 0 )
	{
		offsetContext->set( ImagePlug::tileOriginContextName, tileOrigin - offset );
		h = inPlug()->sampleOffsetsPlug()->hash();
	}
	else
	{
		ImageProcessor::hashSampleOffsets( parent, context, h );

		inPlug()->deepStatePlug()->hash( h );

		const Box2i outTileBound( tileOrigin, tileOrigin + V2i( ImagePlug::tileSize() ) );
		const Box2i inBound( outTileBound.min - offset, outTileBound.max - offset );

		V2i inTileOrigin;
		for( inTileOrigin.y = ImagePlug::tileOrigin( inBound.min ).y; inTileOrigin.y < inBound.max.y; inTileOrigin.y += ImagePlug::tileSize() )
		{
			for( inTileOrigin.x = ImagePlug::tileOrigin( inBound.min ).x; inTileOrigin.x < inBound.max.x; inTileOrigin.x += ImagePlug::tileSize() )
			{
				offsetContext->set( ImagePlug::tileOriginContextName, inTileOrigin );
				inPlug()->dataWindowPlug()->hash( h );
				inPlug()->sampleOffsetsPlug()->hash( h );
			}
		}

		h.append( offset );
	}
}

IECore::ConstIntVectorDataPtr Offset::computeSampleOffsets( const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	ContextPtr offsetContext = new Context( *context, Context::Borrowed );
	Context::Scope scope( offsetContext.get() );

	const V2i offset = offsetPlug()->getValue();
	if(
		( offset.x % ImagePlug::tileSize() == 0 && offset.y % ImagePlug::tileSize() == 0 ) )
	{
		offsetContext->set( ImagePlug::tileOriginContextName, tileOrigin - offset );
		return inPlug()->sampleOffsetsPlug()->getValue();
	}
	else
	{
		if( inPlug()->deepStatePlug()->getValue() == ImagePlug::Flat )
		{
			return inPlug()->sampleOffsetsPlug()->getValue();
		}
		else
		{
			return computeDeepSampleOffsets( tileOrigin, context, parent );
		}
	}
}

IECore::ConstIntVectorDataPtr Offset::computeDeepSampleOffsets( const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	ContextPtr offsetContext = new Context( *context, Context::Borrowed );
	Context::Scope scope( offsetContext.get() );

	const V2i offset = offsetPlug()->getValue();

	const Box2i outTileBound( tileOrigin, tileOrigin + V2i( ImagePlug::tileSize() ) );
	const Box2i inBound( outTileBound.min - offset, outTileBound.max - offset );

	IntVectorDataPtr outData = new IntVectorData;
	std::vector<int> &out = outData->writable();
	out.resize( ImagePlug::tileSize() * ImagePlug::tileSize(), 0 );

	V2i inTileOrigin;
	for( inTileOrigin.y = ImagePlug::tileOrigin( inBound.min ).y; inTileOrigin.y < inBound.max.y; inTileOrigin.y += ImagePlug::tileSize() )
	{
		for( inTileOrigin.x = ImagePlug::tileOrigin( inBound.min ).x; inTileOrigin.x < inBound.max.x; inTileOrigin.x += ImagePlug::tileSize() )
		{
			offsetContext->set( ImagePlug::tileOriginContextName, inTileOrigin );
			ConstIntVectorDataPtr inData = inPlug()->sampleOffsetsPlug()->getValue();
			const std::vector<int> &in = inData->readable();

			const Imath::Box2i &inDataWindow = inPlug()->dataWindowPlug()->getValue();

			V2i inPoint;
			for( inPoint.y = std::max( outTileBound.min.y - offset.y, inTileOrigin.y ); inPoint.y < std::min( outTileBound.max.y - offset.y, inTileOrigin.y + ImagePlug::tileSize() ); ++inPoint.y )
			{
				for( inPoint.x = std::max( outTileBound.min.x - offset.x, inTileOrigin.x ); inPoint.x < std::min( outTileBound.max.x - offset.x, inTileOrigin.x + ImagePlug::tileSize() ); ++inPoint.x )
				{
					if( contains( inDataWindow, inPoint ) )
					{
						V2i outPoint = inPoint + offset;
						const int numSamples = sampleCount( in, inPoint );
						out[tileIndex( outPoint - tileOrigin )] = numSamples;
					}
				}
			}
		}
	}

	// out data is initially sample counts per pixel. These need to be
	// turned into sample offsets.
	int lastOffset = 0;
	for( std::vector<int>::iterator outIt = out.begin(); outIt != out.end(); ++outIt )
	{
		*outIt += lastOffset;
		lastOffset = *outIt;
	}

	return outData;
}

void Offset::hashChannelData( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ContextPtr offsetContext = new Context( *context, Context::Borrowed );
	Context::Scope scope( offsetContext.get() );

	const V2i offset = offsetPlug()->getValue();
	const V2i tileOrigin = context->get<V2i>( ImagePlug::tileOriginContextName );
	if( offset.x % ImagePlug::tileSize() == 0 && offset.y % ImagePlug::tileSize() == 0 )
	{
		offsetContext->set( ImagePlug::tileOriginContextName, tileOrigin - offset );
		h = inPlug()->channelDataPlug()->hash();
	}
	else
	{
		ImageProcessor::hashChannelData( parent, context, h );

		inPlug()->deepStatePlug()->hash( h );
		outPlug()->sampleOffsetsPlug()->hash( h );

		const Box2i outTileBound( tileOrigin, tileOrigin + V2i( ImagePlug::tileSize() ) );
		const Box2i inBound( outTileBound.min - offset, outTileBound.max - offset );

		V2i inTileOrigin;
		for( inTileOrigin.y = ImagePlug::tileOrigin( inBound.min ).y; inTileOrigin.y < inBound.max.y; inTileOrigin.y += ImagePlug::tileSize() )
		{
			for( inTileOrigin.x = ImagePlug::tileOrigin( inBound.min ).x; inTileOrigin.x < inBound.max.x; inTileOrigin.x += ImagePlug::tileSize() )
			{
				offsetContext->set( ImagePlug::tileOriginContextName, inTileOrigin );
				inPlug()->dataWindowPlug()->hash( h );
				inPlug()->sampleOffsetsPlug()->hash( h );
				inPlug()->channelDataPlug()->hash( h );
			}
		}

		h.append( offset );
	}
}

IECore::ConstFloatVectorDataPtr Offset::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	const V2i offset = offsetPlug()->getValue();
	if( offset.x % ImagePlug::tileSize() == 0 && offset.y % ImagePlug::tileSize() == 0 )
	{
		ContextPtr offsetContext = new Context( *context, Context::Borrowed );
		Context::Scope scope( offsetContext.get() );

		offsetContext->set( ImagePlug::tileOriginContextName, tileOrigin - offset );
		return inPlug()->channelDataPlug()->getValue();
	}
	else
	{
		if( inPlug()->deepStatePlug()->getValue() == ImagePlug::Flat )
		{
			return computeFlatChannelData( channelName, tileOrigin, context, parent );
		}
		else
		{
			return computeDeepChannelData( channelName, tileOrigin, context, parent );
		}
	}
}

IECore::ConstFloatVectorDataPtr Offset::computeDeepChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	ContextPtr offsetContext = new Context( *context, Context::Borrowed );
	Context::Scope scope( offsetContext.get() );

	const V2i offset = offsetPlug()->getValue();

	const Box2i outTileBound( tileOrigin, tileOrigin + V2i( ImagePlug::tileSize() ) );
	const Box2i inBound( outTileBound.min - offset, outTileBound.max - offset );

	FloatVectorDataPtr outData = new FloatVectorData;
	std::vector<float> &out = outData->writable();

	out.reserve( outPlug()->sampleOffsets( tileOrigin )->readable().back() );

	std::vector<ConstFloatSampleRange> outPixels;
	outPixels.resize( ImagePlug::tileSize() * ImagePlug::tileSize() );

	std::vector<bool> outPixelsSet;
	outPixelsSet.resize( ImagePlug::tileSize() * ImagePlug::tileSize(), false );

	// This vector is to store the input data to ensure that it isn't
	// destroyed until we are finished with it.
	std::vector<ConstFloatVectorDataPtr> inDataVector;

	V2i inTileOrigin;
	for( inTileOrigin.y = ImagePlug::tileOrigin( inBound.min ).y; inTileOrigin.y < inBound.max.y; inTileOrigin.y += ImagePlug::tileSize() )
	{
		for( inTileOrigin.x = ImagePlug::tileOrigin( inBound.min ).x; inTileOrigin.x < inBound.max.x; inTileOrigin.x += ImagePlug::tileSize() )
		{
			offsetContext->set( ImagePlug::tileOriginContextName, inTileOrigin );
			ConstFloatVectorDataPtr inData = inPlug()->channelDataPlug()->getValue();
			const std::vector<float> &in = inData->readable();
			inDataVector.push_back( inData );

			const Imath::Box2i &inDataWindow = inPlug()->dataWindowPlug()->getValue();

			ConstIntVectorDataPtr inSampleOffsetsData = inPlug()->sampleOffsetsPlug()->getValue();
			const std::vector<int> &inSampleOffsets = inSampleOffsetsData->readable();

			V2i inPoint;
			for( inPoint.y = std::max( outTileBound.min.y - offset.y, inTileOrigin.y ); inPoint.y < std::min( outTileBound.max.y - offset.y, inTileOrigin.y + ImagePlug::tileSize() ); ++inPoint.y )
			{
				for( inPoint.x = std::max( outTileBound.min.x - offset.x, inTileOrigin.x ); inPoint.x < std::min( outTileBound.max.x - offset.x, inTileOrigin.x + ImagePlug::tileSize() ); ++inPoint.x )
				{
					if( contains( inDataWindow, inPoint ) )
					{
						V2i outPoint = inPoint + offset;
						outPixels[tileIndex( outPoint - tileOrigin )] = sampleRange( in, inSampleOffsets, inPoint );
						outPixelsSet[tileIndex( outPoint - tileOrigin )] = true;
					}
				}
			}
		}
	}

	std::vector<bool>::iterator outPixelsSetIt = outPixelsSet.begin();
	for( std::vector<ConstFloatSampleRange>::iterator outPixelsIt = outPixels.begin(); outPixelsIt != outPixels.end(); ++outPixelsIt, ++outPixelsSetIt )
	{
		if( (*outPixelsSetIt) )
		{
			out.insert( out.end(), outPixelsIt->begin(), outPixelsIt->end() );
		}
	}

	return outData;
}

IECore::ConstFloatVectorDataPtr Offset::computeFlatChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	ContextPtr offsetContext = new Context( *context, Context::Borrowed );
	Context::Scope scope( offsetContext.get() );

	const V2i offset = offsetPlug()->getValue();

	const Box2i outTileBound( tileOrigin, tileOrigin + V2i( ImagePlug::tileSize() ) );
	const Box2i inBound( outTileBound.min - offset, outTileBound.max - offset );

	FloatVectorDataPtr outData = new FloatVectorData;
	outData->writable().resize( ImagePlug::tileSize() * ImagePlug::tileSize() );
	float *out = &outData->writable().front();

	V2i inTileOrigin;
	for( inTileOrigin.y = ImagePlug::tileOrigin( inBound.min ).y; inTileOrigin.y < inBound.max.y; inTileOrigin.y += ImagePlug::tileSize() )
	{
		for( inTileOrigin.x = ImagePlug::tileOrigin( inBound.min ).x; inTileOrigin.x < inBound.max.x; inTileOrigin.x += ImagePlug::tileSize() )
		{
			offsetContext->set( ImagePlug::tileOriginContextName, inTileOrigin );
			ConstFloatVectorDataPtr inData = inPlug()->channelDataPlug()->getValue();
			const float *in = &inData->readable().front();

			const Box2i inTileBound( inTileOrigin, inTileOrigin + V2i( ImagePlug::tileSize() ) );
			const Box2i inRegion = intersection(
				inBound,
				inTileBound
			);

			V2i inScanlineOrigin = inRegion.min;
			const size_t scanlineLength = inRegion.size().x;
			while( inScanlineOrigin.y < inRegion.max.y )
			{
				memcpy(
					// to
					out + bufferIndex( inScanlineOrigin + offset, outTileBound ),
					// from
					in + bufferIndex( inScanlineOrigin, inTileBound ),
					sizeof( float ) * scanlineLength
				);
				++inScanlineOrigin.y;
			}
		}
	}

	return outData;
}
