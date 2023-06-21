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

#include "GafferImage/BufferAlgo.h"

#include "OpenImageIO/fmath.h"

namespace GafferImage
{

inline float Sampler::sample( int x, int y )
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
		if( m_boundingMode == Black )
		{
			if( !BufferAlgo::contains( m_dataWindow, p ) )
			{
				return 0.0f;
			}
		}
		else
		{
			p = BufferAlgo::clamp( p, m_dataWindow );
		}
	}

	const float *tileData;
	int tilePixelIndex;
	cachedData( p, tileData, tilePixelIndex );
	return *( tileData + tilePixelIndex );
}

inline float Sampler::sample( float x, float y )
{
	int xi;
	float xf = OIIO::floorfrac( x - 0.5, &xi );
	int yi;
	float yf = OIIO::floorfrac( y - 0.5, &yi );

	constexpr int tileLowMask = ImagePlug::tileSize() - 1;
	if(
		( xi & tileLowMask ) != tileLowMask &&
		( yi & tileLowMask ) != tileLowMask &&
		xi >= m_dataWindow.min.x && xi < m_dataWindow.max.x - 1 &&
		yi >= m_dataWindow.min.y && yi < m_dataWindow.max.y - 1
	)
	{
		const float *tileData;
		int tilePixelIndex;
		cachedData( Imath::V2i( xi, yi ), tileData, tilePixelIndex );
		return OIIO::bilerp(
			tileData[tilePixelIndex], tileData[tilePixelIndex + 1],
			tileData[tilePixelIndex + ImagePlug::tileSize()], tileData[tilePixelIndex + ImagePlug::tileSize() + 1],
			xf, yf
		);
	}
	// Note that if we care about performance in the case of accessing outside the data window, we
	// could add more special cases here. If boundingMode isn't clamped, this is trivial: check
	// if fully outside bound, return 0.0 without even computing xf and yf. Clamped is trickier -
	// above or below you need just xf, to the left or right you just need yf, and in the corners
	// you need neither


	float x0y0 = sample( xi, yi );
	float x1y0 = sample( xi + 1, yi );
	float x0y1 = sample( xi, yi + 1 );
	float x1y1 = sample( xi + 1, yi + 1 );

	return OIIO::bilerp( x0y0, x1y0, x0y1, x1y1, xf, yf );
}

template<typename F>
inline void Sampler::visitPixels( const Imath::Box2i &region, F &&visitor )
{
	int x = region.min.x;
	int y = region.min.y;

	if( region.max.x == region.min.x + 1 )
	{
		// The general principle of visitPixels is to find contiguous spans in X, precompute the length
		// of the span, and then process the whole span in a very tight inner loop with minimal branching
		// where moving to the next pixel takes just an increment. When the region is just
		// one pixel wide, however, looking for X spans is really not helping, so we have a big special
		// case to instead look for vertical spans.
		while( y < region.max.y )
		{
			// Our goal is to prepare these 3 variables:
			// valuePointer or constantValue will hold the data, and count will hold how many consecutive pixels
			// we can visit without recomputing valuePointer/constantValue.
			// The default is that valuePointer is null, and constantValue is 0, meaning that visited pixels
			// will be treated as 0 unless we set one of the values.

			int count;
			const float *valuePointer = nullptr;
			float constantValue = 0.0f;

			// If we are clamping, then we will always treat x as if it is within the nearest edge of the data
			// window.
			int clampedX = x;
			if( m_boundingMode == Clamp )
			{
				clampedX = std::clamp( x, m_dataWindow.min.x, m_dataWindow.max.x - 1 );
			}

			if( clampedX < m_dataWindow.min.x || clampedX >= m_dataWindow.max.x )
			{
				// If we're outside, and haven't been clamped, then just use the default constantValue of 0.
				count = region.max.y - y;
			}
			else if( y < m_dataWindow.min.y )
			{
				// Everything before the dataWindow gets the first value in the data window, or 0 if not clamped
				if( m_boundingMode == Clamp )
				{
					const float *tileData;
					int tilePixelIndex;
					cachedData( Imath::V2i( clampedX, m_dataWindow.min.y ), tileData, tilePixelIndex );
					constantValue = tileData[ tilePixelIndex ];
				}
				count = std::min( region.max.y, m_dataWindow.min.y ) - y;
			}
			else if( y >= m_dataWindow.max.y )
			{
				// Everything after the dataWindow gets the last value in the data window, or 0 if not clamped
				if( m_boundingMode == Clamp )
				{
					const float *tileData;
					int tilePixelIndex;
					cachedData( Imath::V2i( clampedX, m_dataWindow.max.y - 1 ), tileData, tilePixelIndex );
					constantValue = tileData[ tilePixelIndex ];
				}
				count = region.max.y - y;
			}
			else
			{
				// We're actually in the data window ( or clamped to the side of it ). Need to actually
				// set valuePointer
				const float *tileData;
				int tilePixelIndex;
				cachedData( Imath::V2i( clampedX, y ), tileData, tilePixelIndex );
				int pixelY = tilePixelIndex >> ImagePlug::tileSizeLog2();
				count = std::min( std::min( m_dataWindow.max.y, region.max.y ) - y, ImagePlug::tileSize() - pixelY );
				valuePointer = &tileData[ tilePixelIndex ];
			}

			// Now we can do the nice tight inner loop where we call visitor repeatedly with valuePointer, or
			// constantValue
			if( valuePointer )
			{
				for( int i = 0; i < count; i++ )
				{
					visitor( valuePointer[i << ImagePlug::tileSizeLog2()], x, y + i );
				}
			}
			else
			{
				for( int i = 0; i < count; i++ )
				{
					visitor( constantValue, x, y + i );
				}
			}

			y += count;
		}
		return;
	}

	// We didn't take the vertical special case above, so we're going to visit horizontal scanlines
	while( y < region.max.y )
	{
		// As above, our goal is to prepare these 3 variables:
		// valuePointer or constantValue will hold the data, and count will hold how many consecutive pixels
		// we can visit without recomputing valuePointer/constantValue.
		// The default is that valuePointer is null, and constantValue is 0, meaning that visited pixels
		// will be treated as 0 unless we set one of the values.
		int count;
		const float *valuePointer = nullptr;
		float constantValue = 0.0f;

		// If we are clamping, then we will always treat y as if it is within the nearest edge of the data
		// window ( reading a scanline below the data window yields the same result as reading a scanline
		// of the bottom edge of the data window )
		int clampedY = y;
		if( m_boundingMode == Clamp )
		{
			clampedY = std::clamp( y, m_dataWindow.min.y, m_dataWindow.max.y - 1 );
		}

		if( clampedY < m_dataWindow.min.y ||  clampedY >= m_dataWindow.max.y )
		{
			// If we're outside, and haven't been clamped, then just use the default constantValue of 0.
			count = region.max.x - x;
		}
		else if( x < m_dataWindow.min.x )
		{
			// Everything left of the dataWindow gets the first value in the data window on this row, or 0 if not clamped
			if( m_boundingMode == Clamp )
			{
				const float *tileData;
				int tilePixelIndex;
				cachedData( Imath::V2i( m_dataWindow.min.x, clampedY ), tileData, tilePixelIndex );
				constantValue = tileData[ tilePixelIndex ];
			}
			count = std::min( region.max.x, m_dataWindow.min.x ) - x;
		}
		else if( x >= m_dataWindow.max.x )
		{
			// Everything right of the dataWindow gets the last value in the data window on this row, or 0 if not clamped
			if( m_boundingMode == Clamp )
			{
				const float *tileData;
				int tilePixelIndex;
				cachedData( Imath::V2i( m_dataWindow.max.x - 1, clampedY ), tileData, tilePixelIndex );
				constantValue = tileData[ tilePixelIndex ];
			}
			count = region.max.x - x;
		}
		else
		{
			// We're actually in the data window ( or clamped to the top or bottom of it ). Need to actually
			// set valuePointer
			const float *tileData;
			int tilePixelIndex;
			cachedData( Imath::V2i( x, clampedY ), tileData, tilePixelIndex );
			int tileX = tilePixelIndex & ( ImagePlug::tileSize() - 1 );
			count = std::min( std::min( m_dataWindow.max.x, region.max.x ) - x, ImagePlug::tileSize() - tileX );
			valuePointer = &tileData[ tilePixelIndex ];
		}

		// Now we can do the nice tight inner loop where we call visitor repeatedly with valuePointer, or
		// constantValue
		if( valuePointer )
		{
			for( int i = 0; i < count; i++ )
			{
				visitor( valuePointer[i], x + i, y );
			}
		}
		else
		{
			for( int i = 0; i < count; i++ )
			{
				visitor( constantValue, x + i, y );
			}
		}

		// Advance in the scanline, and advance to the next scanline if we've finished
		x += count;
		if( x == region.max.x )
		{
			y++;
			x = region.min.x;
		}
	}
}

inline void Sampler::cachedData( Imath::V2i p, const float *& tileData, int &tilePixelIndex )
{
	// Get the smart pointer to the tile we want.

	constexpr int lowMask = ( 1 << ImagePlug::tileSizeLog2() ) - 1;
	int cacheIndex = ( p.x >> ImagePlug::tileSizeLog2() ) + m_cacheWidth * ( p.y >> ImagePlug::tileSizeLog2() ) - m_cacheOriginIndex;

	tilePixelIndex = ( p.x & lowMask ) + ( ( p.y & lowMask ) << ImagePlug::tileSizeLog2() );

	const float *&cacheTileRawPtr = m_dataCacheRaw[cacheIndex];

	if ( cacheTileRawPtr == nullptr )
	{
		// Get the origin of the tile we want.
		Imath::V2i tileOrigin( p.x & ~( ImagePlug::tileSize() - 1 ), p.y & ~( ImagePlug::tileSize() - 1 ) );

		IECore::ConstFloatVectorDataPtr &cacheTilePtr = m_dataCache[ cacheIndex ];
		cacheTilePtr = m_plug->channelData( m_channelName, tileOrigin );
		cacheTileRawPtr = &cacheTilePtr->readable()[0];
	}

	tileData = cacheTileRawPtr;
}

}; // namespace GafferImage
