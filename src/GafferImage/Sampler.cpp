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

Sampler::Sampler( const GafferImage::ImagePlug *plug, const std::string &channelName, const Imath::Box2i &sampleWindow, const std::string &filter )
	: m_plug( plug ),
	m_channelName( channelName ),
	m_filter( Filter::create( filter ) )
{
	// Get the new sample bounds that includes all intersecting tiles.	
	m_sampleWindow = Imath::Box2i( 
		GafferImage::ImagePlug::tileOrigin( sampleWindow.min ),
		GafferImage::ImagePlug::tileOrigin( sampleWindow.max ) + Imath::V2i( ImagePlug::tileSize() ) - Imath::V2i(1)
	);
		
	// Intersect the data window and the sample window.
	m_sampleWindow = boxIntersection( m_sampleWindow, plug->formatPlug()->getValue().getDisplayWindow() );

	m_valid = m_sampleWindow.hasVolume();
	
	if ( m_valid )
	{
		m_dataCache.resize( ( ( m_sampleWindow.max.x - m_sampleWindow.min.x ) / ImagePlug::tileSize() + 1 ) * ( ( m_sampleWindow.max.y - m_sampleWindow.min.y ) / ImagePlug::tileSize() + 1 ), NULL );
	}
}

float Sampler::sample( int x, int y )
{
	if ( !m_valid ) return 0.;

	// Return 0 for pixels outside of our sample window.	
	if ( x < m_sampleWindow.min.x || x > m_sampleWindow.max.x )
	{
		return 0.;
	}
	
	if ( y < m_sampleWindow.min.y || y > m_sampleWindow.max.y )
	{
		return 0.;
	}

	// Get the smart pointer to the tile we want.
	int cacheIndexX = ( x - m_sampleWindow.min.x ) / ImagePlug::tileSize();
	int cacheIndexY = ( y - m_sampleWindow.min.y ) / ImagePlug::tileSize();
	ConstFloatVectorDataPtr &cacheTilePtr = m_dataCache[ cacheIndexX + cacheIndexY * ( ( m_sampleWindow.max.x - m_sampleWindow.min.x ) / ImagePlug::tileSize() + 1 ) ];
	
	// Get the origin of the tile we want.
	Imath::V2i tileOrigin( ( x / ImagePlug::tileSize() ) * ImagePlug::tileSize(), ( y / ImagePlug::tileSize() ) * ImagePlug::tileSize() );
	if ( cacheTilePtr == NULL ) cacheTilePtr = m_plug->channelData( m_channelName, tileOrigin );

	x -= tileOrigin.x;
	y -= tileOrigin.y;

	return *((&cacheTilePtr->readable()[0]) + y * ImagePlug::tileSize() + x);
}	

float Sampler::sample( float x, float y )
{
	if ( !m_valid ) return 0.;

	m_filter->setScale( 1. );
	int tapX = m_filter->construct( x );
	const std::vector<double> weightsX = m_filter->weights();
	const int width = weightsX.size();
	
	int tapY = m_filter->construct( y );
	const std::vector<double> &weightsY = m_filter->weights();
	const int height = weightsY.size();

	double weightedSum = 0.;
	float colour = 0.f;
	for ( int y = 0; y < height; ++y )
	{
		for ( int x = 0; x < width; ++x )
		{
			float c = sample( tapX + x, tapY + y );
			double w = weightsX[x] * weightsY[y];
			weightedSum += w;
			colour += c * w;
		}
	}
	colour /= weightedSum;
	return colour;
}

