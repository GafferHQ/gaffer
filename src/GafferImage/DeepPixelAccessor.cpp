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

#include "GafferImage/DeepPixelAccessor.h"

#include "GafferImage/ImageAlgo.h"

using namespace IECore;
using namespace Imath;
using namespace Gaffer;
using namespace GafferImage;

DeepPixelAccessor::DeepPixelAccessor( const GafferImage::ImagePlug *plug, const std::string &channelName, const Imath::Box2i &sampleWindow, Sampler::BoundingMode boundingMode )
	: m_plug( plug ),
	m_channelName( channelName ),
	m_boundingMode( boundingMode )
{
	{
		ImagePlug::GlobalScope c( Context::current() );
		m_dataWindow = m_plug->dataWindowPlug()->getValue();
	}

	// We only store the sample window to be able to perform
	// validation of the calls made to sample() in debug builds.
	m_sampleWindow = sampleWindow;

	if( BufferAlgo::contains( m_dataWindow, m_sampleWindow ) )
	{
		// If the sample window is fully contained in the data window, then
		// we don't need to worry about bounds. Bounding mode -1 disables
		// all bounds checking.
		m_boundingMode = -1;
	}
	else if( BufferAlgo::empty( m_dataWindow ) )
	{
		m_boundingMode = Sampler::Black;
	}

	// Compute the area we need to cache in order to
	// be able to service calls within m_sampleWindow
	// when taking into account m_boundingMode and m_dataWindow.

	m_cacheWindow = BufferAlgo::intersection( m_sampleWindow, m_dataWindow );
	if( BufferAlgo::empty( m_cacheWindow ) && m_boundingMode == Sampler::Clamp )
	{
		// The area being sampled is entirely outside the
		// data window, but we still need to cache the region
		// into which we will clamp the queries.
		m_cacheWindow = Box2i();
		m_cacheWindow.extendBy( BufferAlgo::clamp( m_sampleWindow.min, m_dataWindow ) );
		m_cacheWindow.extendBy( BufferAlgo::clamp( m_sampleWindow.max, m_dataWindow ) );
		m_cacheWindow.extendBy( BufferAlgo::clamp( V2i( m_sampleWindow.min.x, m_sampleWindow.max.y ), m_dataWindow ) );
		m_cacheWindow.extendBy( BufferAlgo::clamp( V2i( m_sampleWindow.max.x, m_sampleWindow.min.y ), m_dataWindow ) );
		m_cacheWindow.max += V2i( 1 ); // max is exclusive.
	}

	// Our cache is composed of tiles, so the window for
	// the cache contents needs expanding to the nearest
	// tile boundary. As elsewhere in GafferImage, max is
	// exclusive, so is actually inside the next tile over.
	m_cacheWindow = Imath::Box2i(
		Imath::V2i( ImagePlug::tileOrigin( m_cacheWindow.min ) ),
		Imath::V2i( ImagePlug::tileOrigin( m_cacheWindow.max - Imath::V2i( 1 ) ) + Imath::V2i( ImagePlug::tileSize() ) )
	);

	m_cacheWidth = int( ceil( float( m_cacheWindow.size().x ) / ImagePlug::tileSize() ) );
	int cacheHeight = int( ceil( float( m_cacheWindow.size().y ) / ImagePlug::tileSize() ) );

	if( m_channelName.size() )
	{
		m_dataCache.resize( m_cacheWidth * cacheHeight, nullptr );
	}
	m_offsetsCache.resize( m_cacheWidth * cacheHeight, nullptr );

	m_cacheOriginIndex = ( m_cacheWindow.min.x >> ImagePlug::tileSizeLog2() ) + m_cacheWidth * ( m_cacheWindow.min.y >> ImagePlug::tileSizeLog2() );
}

DeepPixelAccessor::DeepPixelAccessor( const DeepPixelAccessor &source, const std::string &channelName )
	: m_plug( source.m_plug ),
	m_channelName( channelName ),
	m_sampleWindow( source.m_sampleWindow ), m_dataWindow( source.m_dataWindow ),
	m_offsetsCache( source.m_offsetsCache ), m_cacheWindow( source.m_cacheWindow ),
	m_cacheOriginIndex( source.m_cacheOriginIndex ), m_cacheWidth( source.m_cacheWidth ),
	m_boundingMode( source.m_boundingMode )
{
	if( m_channelName.size() )
	{
		m_dataCache.resize( source.m_offsetsCache.size() );
	}
}

void DeepPixelAccessor::populate()
{
	ImageAlgo::parallelProcessTiles(
		m_plug,
		[&] ( const ImagePlug *imagePlug, const V2i &tileOrigin ) {
			const float *tileData;
			const int *tileOffsets;
			int tilePixelIndex;
			cachedData( tileOrigin, tileData, tileOffsets, tilePixelIndex );
			assert( tilePixelIndex == 0 );
		},
		m_cacheWindow
	);
}

void DeepPixelAccessor::hash( IECore::MurmurHash &h ) const
{
	for ( int x = m_cacheWindow.min.x; x < m_cacheWindow.max.x; x += GafferImage::ImagePlug::tileSize() )
	{
		for ( int y = m_cacheWindow.min.y; y < m_cacheWindow.max.y; y += GafferImage::ImagePlug::tileSize() )
		{
			if( m_channelName.size() )
			{
				h.append( m_plug->channelDataHash( m_channelName, Imath::V2i( x, y ) ) );
			}
			h.append( m_plug->sampleOffsetsHash( Imath::V2i( x, y ) ) );
		}
	}
	h.append( m_boundingMode );
	h.append( m_dataWindow );
	h.append( m_sampleWindow );
}

IECore::MurmurHash DeepPixelAccessor::hash() const
{
	IECore::MurmurHash h;
	hash( h );
	return h;
}
