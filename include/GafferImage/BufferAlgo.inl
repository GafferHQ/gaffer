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

#pragma once

#include <cassert>

namespace GafferImage
{

namespace BufferAlgo
{

//////////////////////////////////////////////////////////////////////////
// Window/Box utilities
//////////////////////////////////////////////////////////////////////////

inline bool empty( const Imath::Box2i &window )
{
	for( int i = 0; i < 2; ++i )
	{
		if( window.max[i] <= window.min[i] )
		{
			return true;
		}
	}
	return false;
}

inline bool intersects( const Imath::Box2i &window1, const Imath::Box2i &window2 )
{
	for( int i = 0; i < 2; ++i )
	{
		if( window1.max[i] <= window2.min[i] )
		{
			return false;
		}
		if( window1.min[i] >= window2.max[i] )
		{
			return false;
		}
	}
	return true;
}

inline Imath::Box2i intersection( const Imath::Box2i &window1, const Imath::Box2i &window2 )
{
	Imath::Box2i result;
	for( int i = 0; i < 2; ++i )
	{
		result.min[i] = std::max( window1.min[i], window2.min[i] );
		result.max[i] = std::min( window1.max[i], window2.max[i] );
	}

	return result;
}

inline bool contains( const Imath::Box2i &window, const Imath::V2i &point )
{
	for( int i = 0; i < 2; ++i )
	{
		if( point[i] < window.min[i] || point[i] >= window.max[i] )
		{
			return false;
		}
	}
	return true;
}

inline bool contains( const Imath::Box2i &window, const Imath::Box2i &area )
{
	for( int i = 0; i < 2; ++i )
	{
		if( area.min[i] < window.min[i] || area.max[i] > window.max[i] )
		{
			return false;
		}
	}
	return true;
}

inline Imath::V2i clamp( const Imath::V2i &point, const Imath::Box2i &window )
{
	return Imath::V2i(
		std::max( std::min( point.x, window.max.x - 1 ), window.min.x ),
		std::max( std::min( point.y, window.max.y - 1 ), window.min.y )
	);
}

inline size_t index( const Imath::V2i &p, const Imath::Box2i &b )
{
	assert( contains( b, p ) );
	return
		( p.y - b.min.y ) * b.size().x +
		( p.x - b.min.x );
}

} // namespace BufferAlgo

} // namespace GafferImage
