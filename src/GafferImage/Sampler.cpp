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

#include "GafferImage/Sampler.h"

using namespace Gaffer;
using namespace IECore;
using namespace GafferImage;

Sampler::Sampler( const GafferImage::ImagePlug *plug, const std::string &channelName, const Imath::Box2i &sampleWindow, BoundingMode boundingMode )
	: m_plug( plug ),
	m_channelName( channelName ),
	m_boundingMode( boundingMode ),
	m_filter( Filter::create( Filter::defaultFilter() ) )
{
	init( sampleWindow );
}

Sampler::Sampler( const GafferImage::ImagePlug *plug, const std::string &channelName, const Imath::Box2i &sampleWindow, ConstFilterPtr filter, BoundingMode boundingMode )
	: m_plug( plug ),
	m_channelName( channelName ),
	m_boundingMode( boundingMode ),
	m_filter( filter )
{
	init( sampleWindow );
}

void Sampler::init( const Imath::Box2i &sampleWindow )
{
	// The area that we actually need to sample the area requested.
	const int filterRadius = int( ceil( m_filter->width() / 2. ) );

	// The userSampleWindow is the area within which we can sample and have image data returned.
	Imath::Box2i dataWindow( m_plug->dataWindowPlug()->getValue() );
	m_userSampleWindow = boxIntersection( dataWindow, sampleWindow );

	// Work the area we need to sample in order to be able to do sub-pixel sampling.
	m_sampleWindow = Imath::Box2i(
		Imath::V2i( sampleWindow.min.x - filterRadius, sampleWindow.min.y - filterRadius ),
		Imath::V2i( sampleWindow.max.x + filterRadius, sampleWindow.max.y + filterRadius )
	);
	m_sampleWindow = boxIntersection( dataWindow, m_sampleWindow );

	// The area that we actually have in the cache.
	// Exclusive, so max value points at the next tile over
	m_cacheWindow = Imath::Box2i(
		Imath::V2i( ImagePlug::tileOrigin( m_sampleWindow.min ) ),
		Imath::V2i( ImagePlug::tileOrigin( m_sampleWindow.max - Imath::V2i( 1 ) ) + Imath::V2i( ImagePlug::tileSize() ) )
	);

	m_cacheWidth = int( ceil( float( m_cacheWindow.size().x ) / ImagePlug::tileSize() ) );
	int cacheHeight = int( ceil( float( m_cacheWindow.size().y ) / ImagePlug::tileSize() ) );
	m_dataCache.resize( m_cacheWidth * cacheHeight, NULL );
}

void Sampler::hash( IECore::MurmurHash &h ) const
{
	for ( int x = m_cacheWindow.min.x; x < m_cacheWindow.max.x; x += GafferImage::ImagePlug::tileSize() )
	{
		for ( int y = m_cacheWindow.min.y; y < m_cacheWindow.max.y; y += GafferImage::ImagePlug::tileSize() )
		{
			h.append( m_plug->channelDataHash( m_channelName, Imath::V2i( x, y ) ) );
		}
	}
	h.append( m_boundingMode );
}

