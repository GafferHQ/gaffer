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

#include "Gaffer/Context.h"
#include "GafferImage/Sampler.h"
#include "GafferImage/Filter.h"
#include "IECore/BoxAlgo.h"
#include "IECore/BoxOps.h"

using namespace Gaffer;
using namespace IECore;
using namespace GafferImage;

Sampler::Sampler( const GafferImage::ImagePlug *plug, const std::string &channelName )
	: m_plug( plug ),
	m_dataWindow( plug->formatPlug()->getValue().getDisplayWindow() ),
	m_channelName( channelName ),
	m_cacheSize( m_dataWindow.max / ImagePlug::tileSize() )
{
	///\todo: Find out why sometimes Sampler can be called from computeChannelData() that has a negative data window
	/// which results in the sampler (created within computeChannelData ) being called.
	/// If we can work that out then maybe we don't need the m_valid bool!.
	m_valid = !m_dataWindow.isEmpty();
	
	if ( m_valid )
	{
		m_cacheSize.x = std::max( m_cacheSize.x, 0 );
		m_cacheSize.y = std::max( m_cacheSize.y, 0 );
		m_dataCache.resize( ( m_cacheSize.x + 1 ) * ( m_cacheSize.y + 1 ), NULL );
	}
}

float Sampler::sample( int x, int y )
{
	if ( !m_valid ) return 1.;

	x = std::max( m_dataWindow.min.x, std::min( m_dataWindow.max.x, x ) );
	y = std::max( m_dataWindow.min.y, std::min( m_dataWindow.max.y, y ) );

	int cacheIndexX = x / ImagePlug::tileSize();
	int cacheIndexY = y / ImagePlug::tileSize();

	Imath::V2i tileOrigin( cacheIndexX * ImagePlug::tileSize(), cacheIndexY * ImagePlug::tileSize() );
	ConstFloatVectorDataPtr &cacheTilePtr = m_dataCache[ cacheIndexX + cacheIndexY * ( m_cacheSize.y + 1 ) ];
	if ( cacheTilePtr == NULL ) cacheTilePtr = m_plug->channelData( m_channelName, tileOrigin );

	x -= tileOrigin.x;
	y -= tileOrigin.y;

	return *((&cacheTilePtr->readable()[0]) + y * ImagePlug::tileSize() + x);
}	




