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

#include "Gaffer/Context.h"
#include "GafferImage/Sampler.h"
#include "IECore/BoxAlgo.h"
#include "IECore/BoxOps.h"

using namespace Gaffer;
using namespace IECore;
using namespace GafferImage;

Sampler::Sampler( const GafferImage::ImagePlug *plug, const std::string &channelName, const Imath::Box2i &userSampleWindow, ConstFilterPtr filter, BoundingMode boundingMode )
	: m_plug( plug ),
	m_channelName( channelName ),
	m_boundingMode( boundingMode ),
	m_filter( filter )
{
	const int filterRadius = int( ceil( m_filter->width() / 2. ) );
	m_filterSampleWindow = Imath::Box2i(
		Imath::V2i( userSampleWindow.min.x - filterRadius, userSampleWindow.min.y - filterRadius ),
		Imath::V2i( userSampleWindow.max.x + filterRadius, userSampleWindow.max.y + filterRadius )
	);

	m_userSampleWindow = boxIntersection( m_filterSampleWindow, plug->dataWindowPlug()->getValue() );

	m_cacheWindow = Imath::Box2i(
		Imath::V2i( GafferImage::ImagePlug::tileOrigin( m_userSampleWindow.min ) / Imath::V2i( ImagePlug::tileSize() ) ),
		Imath::V2i( GafferImage::ImagePlug::tileOrigin( m_userSampleWindow.max ) / Imath::V2i( ImagePlug::tileSize() ) )
	);

	m_valid = m_filterSampleWindow.hasVolume() && m_userSampleWindow.hasVolume();
	
	if ( m_valid )
	{
		m_dataCache.resize( ( m_cacheWindow.size().x + 1 ) * ( m_cacheWindow.size().y + 1 ), NULL );
	}
}

float Sampler::sample( int x, int y )
{
	if ( !m_valid ) return 0.;
	
	// Return 0 for pixels outside of our sample window.
	if ( m_boundingMode == Black )
	{
		if ( x < m_userSampleWindow.min.x || x > m_userSampleWindow.max.x )
		{
			return 0.;
		}

		if ( y < m_userSampleWindow.min.y || y > m_userSampleWindow.max.y )
		{
			return 0.;
		}
	}
	else if ( m_boundingMode == Clamp )
	{
		x = std::max( std::min( x, m_userSampleWindow.max.x ), m_userSampleWindow.min.x );
		y = std::max( std::min( y, m_userSampleWindow.max.y ), m_userSampleWindow.min.y );
	}

	// Get the smart pointer to the tile we want.
	Imath::V2i p( x, y );
	Imath::V2i tileOrigin( GafferImage::ImagePlug::tileOrigin( p ) );
	Imath::V2i cacheIndex = tileOrigin / Imath::V2i( ImagePlug::tileSize() ) - m_cacheWindow.min;
	ConstFloatVectorDataPtr &cacheTilePtr = m_dataCache[ cacheIndex.x + cacheIndex.y * ( m_cacheWindow.size().x + 1 ) ];
	
	// Get the origin of the tile we want.
	if ( cacheTilePtr == NULL ) cacheTilePtr = m_plug->channelData( m_channelName, tileOrigin );

	return *((&cacheTilePtr->readable()[0]) + (y - tileOrigin.y) * ImagePlug::tileSize() + (x - tileOrigin.x));
}	

float Sampler::sample( float x, float y )
{
	if ( m_boundingMode == Black )
	{
		if ( x < m_filterSampleWindow.min.x || x > m_filterSampleWindow.max.x )
		{
			return 0.;
		}

		if ( y < m_filterSampleWindow.min.y || y > m_filterSampleWindow.max.y )
		{
			return 0.;
		}
	}
	else if ( m_boundingMode == Clamp )
	{
		x = std::max( std::min( int(x), m_filterSampleWindow.max.x ), m_filterSampleWindow.min.x );
		y = std::max( std::min( int(y), m_filterSampleWindow.max.y ), m_filterSampleWindow.min.y );
	}

	int tapX = m_filter->tap( x );
	const int width = m_filter->width();
	double weightsX[width];
	
	for ( int i = 0; i < width; ++i )
	{
		weightsX[i] = m_filter->weight( x, tapX+i );
	}

	int tapY = m_filter->tap( y );
	const int height = m_filter->width();
	double weightsY[height];
	
	for ( int i = 0; i < height; ++i )
	{
		weightsY[i] = m_filter->weight( y, tapY+i );
	}

	double weightedSum = 0.;
	float colour = 0.f;
	for ( int y = 0; y < height; ++y )
	{
		int absY = tapY + y;
		for ( int x = 0; x < width; ++x )
		{
			int absX = tapX + x;
			float c = 0.;
			double w = weightsX[x] * weightsY[y];		
			c = sample( absX, absY );
			weightedSum += w;
			colour += c * w;
		}
	}
	
	colour /= weightedSum;
	return colour;
}

void Sampler::hash( IECore::MurmurHash &h ) const
{
	for ( int x = m_filterSampleWindow.min.x; x <= m_filterSampleWindow.max.x; x += GafferImage::ImagePlug::tileSize() )
	{
		for ( int y = m_filterSampleWindow.min.y; y <= m_filterSampleWindow.max.y; y += GafferImage::ImagePlug::tileSize() )
		{
			Imath::V2i tileOrigin( GafferImage::ImagePlug::tileOrigin( Imath::V2i( x, y ) ) );
			h.append( m_plug->channelDataHash( m_channelName, tileOrigin ) );
		}
	}
}

