//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013 Image Engine Design Inc. All rights reserved.
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

#pragma once

#include "GafferImage/BufferAlgo.h"

namespace GafferImage
{

inline Format::Format()
	:	m_pixelAspect( 1. )
{
}

inline Format::Format( const Imath::Box2i &displayWindow, double pixelAspect, bool fromEXRSpace )
	:	m_displayWindow( displayWindow ),
		m_pixelAspect( pixelAspect )
{
	if( fromEXRSpace )
	{
		m_displayWindow.max += Imath::V2i( 1 );
	}
}

inline Format::Format( int width, int height, double pixelAspect )
	:	m_pixelAspect( pixelAspect )
{
	width = std::max( 0, width );
	height = std::max( 0, height );
	m_displayWindow = Imath::Box2i( Imath::V2i( 0, 0 ), Imath::V2i( width, height ) );
}

inline const Imath::Box2i &Format::getDisplayWindow() const
{
	return m_displayWindow;
}

inline void Format::setDisplayWindow( const Imath::Box2i &window )
{
	m_displayWindow = window;
}

inline int Format::width() const
{
	if( m_displayWindow.isEmpty() )
	{
		return 0;
	}
	return m_displayWindow.max.x - m_displayWindow.min.x;
}

inline int Format::height() const
{
	if( m_displayWindow.isEmpty() )
	{
		return 0;
	}
	return m_displayWindow.max.y - m_displayWindow.min.y;
}

inline double Format::getPixelAspect() const
{
	return m_pixelAspect;
}

inline void Format::setPixelAspect( double pixelAspect )
{
	m_pixelAspect = pixelAspect;
}

inline bool Format::operator == ( const Format& rhs ) const
{
	return m_displayWindow == rhs.m_displayWindow && m_pixelAspect == rhs.m_pixelAspect;
}

inline bool Format::operator != ( const Format& rhs ) const
{
	return m_displayWindow != rhs.m_displayWindow || m_pixelAspect != rhs.m_pixelAspect;
}

inline int Format::fromEXRSpace( int exrSpace ) const
{
	const int distanceFromTop = exrSpace - m_displayWindow.min.y;
	return m_displayWindow.max.y - 1 - distanceFromTop;
}

inline Imath::V2i Format::fromEXRSpace( const Imath::V2i &exrSpace ) const
{
	return Imath::V2i( exrSpace.x, fromEXRSpace( exrSpace.y ) );
}

inline Imath::Box2i Format::fromEXRSpace( const Imath::Box2i &exrSpace ) const
{
	if( exrSpace.isEmpty() )
	{
		return Imath::Box2i();
	}

	return Imath::Box2i(
		Imath::V2i( exrSpace.min.x, fromEXRSpace( exrSpace.max.y ) ),
		Imath::V2i( exrSpace.max.x + 1, fromEXRSpace( exrSpace.min.y ) + 1 )
	);
}

inline int Format::toEXRSpace( int internalSpace ) const
{
	const int distanceFromTop = m_displayWindow.max.y - 1 - internalSpace;
	return m_displayWindow.min.y + distanceFromTop;
}

inline Imath::V2i Format::toEXRSpace( const Imath::V2i &internalSpace ) const
{
	return Imath::V2i( internalSpace.x, toEXRSpace( internalSpace.y ) );
}

inline Imath::Box2i Format::toEXRSpace( const Imath::Box2i &internalSpace ) const
{
	if( BufferAlgo::empty( internalSpace ) )
	{
		return Imath::Box2i();
	}

	return Imath::Box2i(
		Imath::V2i( internalSpace.min.x, toEXRSpace( internalSpace.max.y - 1 ) ),
		Imath::V2i( internalSpace.max.x - 1, toEXRSpace( internalSpace.min.y ) )
	);
}

inline void murmurHashAppend( IECore::MurmurHash &h, const GafferImage::Format &data )
{
	h.append( data.getDisplayWindow() );
	h.append( data.getPixelAspect() );
}

} // namespace GafferImage
