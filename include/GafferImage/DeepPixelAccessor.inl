//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2023, Image Engine Design Inc. All rights reserved.
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

#include "GafferImage/BufferAlgo.h"

#include "OpenImageIO/fmath.h"

namespace GafferImage
{

inline boost::span<const float> DeepPixelAccessor::sample( int x, int y )
{
	Imath::V2i p( x, y );

#ifndef NDEBUG

	// It is the caller's responsibility to ensure that sampling
	// is only performed within the sample window.
	assert( BufferAlgo::contains( m_sampleWindow, p ) );

#endif

	if( m_boundingMode != -1 )
	{
		// Deal with lookups outside of the data window.
		if( m_boundingMode == Sampler::Black )
		{
			if( !BufferAlgo::contains( m_dataWindow, p ) )
			{
				return boost::span<const float>();
			}
		}
		else
		{
			p = BufferAlgo::clamp( p, m_dataWindow );
		}
	}

	const float *tileData;
	const int *tileOffsets;
	int tilePixelIndex;
	cachedData( p, tileData, tileOffsets, tilePixelIndex );

	assert( tileData );
	int prev = tilePixelIndex > 0 ? tileOffsets[ tilePixelIndex - 1 ] : 0;
	return boost::span<const float>( &tileData[ prev ], &tileData[ tileOffsets[ tilePixelIndex ] ] );
}

inline unsigned int DeepPixelAccessor::sampleCount( int x, int y )
{
	Imath::V2i p( x, y );

#ifndef NDEBUG

	// It is the caller's responsibility to ensure that sampling
	// is only performed within the sample window.
	assert( BufferAlgo::contains( m_sampleWindow, p ) );

#endif

	if( m_boundingMode != -1 )
	{
		// Deal with lookups outside of the data window.
		if( m_boundingMode == Sampler::Black )
		{
			if( !BufferAlgo::contains( m_dataWindow, p ) )
			{
				return 0;
			}
		}
		else
		{
			p = BufferAlgo::clamp( p, m_dataWindow );
		}
	}

	const float *tileData;
	const int *tileOffsets;
	int tilePixelIndex;
	cachedData( p, tileData, tileOffsets, tilePixelIndex );

	int prev = tilePixelIndex > 0 ? tileOffsets[ tilePixelIndex - 1 ] : 0;
	return tileOffsets[ tilePixelIndex ] - prev;
}

inline void DeepPixelAccessor::cachedData( Imath::V2i p, const float *& tileData, const int *& tileOffsets, int &tilePixelIndex )
{
	// Get the smart pointer to the tile we want.

	constexpr int lowMask = ( 1 << ImagePlug::tileSizeLog2() ) - 1;
	int cacheIndex = ( p.x >> ImagePlug::tileSizeLog2() ) + m_cacheWidth * ( p.y >> ImagePlug::tileSizeLog2() ) - m_cacheOriginIndex;

	tilePixelIndex = ( p.x & lowMask ) + ( ( p.y & lowMask ) << ImagePlug::tileSizeLog2() );

	if( m_channelName.size() && !m_dataCache[cacheIndex] )
	{
		// Get the origin of the tile we want.
		Imath::V2i tileOrigin( p.x & ~( ImagePlug::tileSize() - 1 ), p.y & ~( ImagePlug::tileSize() - 1 ) );

		m_dataCache[ cacheIndex ] = m_plug->channelData( m_channelName, tileOrigin );

		if( !m_offsetsCache[ cacheIndex ] )
		{
			m_offsetsCache[ cacheIndex ] = m_plug->sampleOffsets( tileOrigin );
		}
	}
	else
	{
		if( !m_offsetsCache[ cacheIndex ] )
		{
			// Get the origin of the tile we want.
			Imath::V2i tileOrigin( p.x & ~( ImagePlug::tileSize() - 1 ), p.y & ~( ImagePlug::tileSize() - 1 ) );
			m_offsetsCache[ cacheIndex ] = m_plug->sampleOffsets( tileOrigin );
		}
	}

	if( m_channelName.size() )
	{
		tileData = &m_dataCache[cacheIndex]->readable()[0];
	}
	else
	{
		tileData = nullptr;
	}
	tileOffsets = &m_offsetsCache[cacheIndex]->readable()[0];
}

}; // namespace GafferImage
