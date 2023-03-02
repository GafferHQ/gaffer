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

#include "IECore/Export.h"

IECORE_PUSH_DEFAULT_VISIBILITY
#include "OpenEXR/ImathBox.h"
IECORE_POP_DEFAULT_VISIBILITY

namespace GafferImage
{

namespace BufferAlgo
{

/// Image window utility functions. The GafferImage convention is that
/// the minimum coordinate is included within the window and the
/// maximum coordinate is outside it - these functions take that into
/// account and should therefore be used in favour of the Imath equivalents.
////////////////////////////////////////////////////////////////////////////

/// Returns true if the window contains no pixels, and false otherwise.
bool empty( const Imath::Box2i &window );

/// Returns true if the image windows intersect.
bool intersects( const Imath::Box2i &window1, const Imath::Box2i &window2 );

/// Return the intersection of the two image windows.
Imath::Box2i intersection( const Imath::Box2i &window1, const Imath::Box2i &window2 );

/// Returns true if the given point is inside the window.
bool contains( const Imath::Box2i &window, const Imath::V2i &point );

/// Returns true if the given area is inside the window.
bool contains( const Imath::Box2i &window, const Imath::Box2i &area );

/// Clamps the point so that it is contained inside the window.
Imath::V2i clamp( const Imath::V2i &point, const Imath::Box2i &window );

/// Returns the index of point p within a buffer with bounds b.
size_t index( const Imath::V2i &p, const Imath::Box2i &b );

} // namespace BufferAlgo

} // namespace GafferImage

#include "GafferImage/BufferAlgo.inl"
