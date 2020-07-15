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

float Sampler::sample( int x, int y )
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
			if( BufferAlgo::empty( m_dataWindow ) )
			{
				return 0.0f;
			}
			p = BufferAlgo::clamp( p, m_dataWindow );
		}
	}

	const float *tileData;
	Imath::V2i tileIndex;
	cachedData( p, tileData, tileIndex );
	return *(tileData + tileIndex.y * ImagePlug::tileSize() + tileIndex.x);
}

float Sampler::sample( float x, float y )
{
	int xi;
	float xf = OIIO::floorfrac( x - 0.5, &xi );
	int yi;
	float yf = OIIO::floorfrac( y - 0.5, &yi );

	float x0y0 = sample( xi, yi );
	float x1y0 = sample( xi + 1, yi );
	float x0y1 = sample( xi, yi + 1 );
	float x1y1 = sample( xi + 1, yi + 1 );

	return OIIO::bilerp( x0y0, x1y0, x0y1, x1y1, xf, yf );
}

void Sampler::cachedData( Imath::V2i p, const float *& tileData, Imath::V2i &tilePixelIndex )
{
	// Get the smart pointer to the tile we want.
	Imath::V2i relP = p - m_cacheWindow.min;
	Imath::V2i cacheIndex = ImagePlug::tileIndex( relP );

	tilePixelIndex = relP - cacheIndex * ImagePlug::tileSize();

	int cacheI = cacheIndex.x + cacheIndex.y * m_cacheWidth;
	const float *&cacheTileRawPtr = m_dataCacheRaw[cacheI];

	if ( cacheTileRawPtr == nullptr )
	{
		// Get the origin of the tile we want.
		Imath::V2i tileOrigin = ( ImagePlug::tileIndex( m_cacheWindow.min ) + cacheIndex ) * ImagePlug::tileSize();

		IECore::ConstFloatVectorDataPtr &cacheTilePtr = m_dataCache[ cacheI ];
		cacheTilePtr = m_plug->channelData( m_channelName, tileOrigin );
		cacheTileRawPtr = &cacheTilePtr->readable()[0];
	}

	tileData = cacheTileRawPtr;
}

}; // namespace GafferImage
