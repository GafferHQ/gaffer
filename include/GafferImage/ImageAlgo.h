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

#ifndef GAFFERIMAGE_IMAGEALGO_H
#define GAFFERIMAGE_IMAGEALGO_H

#include "OpenEXR/ImathBox.h"

namespace GafferImage
{

/// Image window utility functions. The GafferImage convention is that
/// the minimum coordinate is included within the window and the
/// maximum coordinate is outside it - these functions take that into
/// account and should therefore be used in favour of the Imath equivalents.
////////////////////////////////////////////////////////////////////////////

/// Returns true if the window contains no pixels, and false otherwise.
inline bool empty( const Imath::Box2i &window );

/// Returns true if the image windows intersect.
inline bool intersects( const Imath::Box2i &window1, const Imath::Box2i &window2 );

/// Return the intersection of the two image windows.
inline Imath::Box2i intersection( const Imath::Box2i &window1, const Imath::Box2i &window2 );

/// Returns true if the given point is inside the window.
inline bool contains( const Imath::Box2i &window, const Imath::V2i &point );

/// Clamps the point so that it is contained inside the window.
inline Imath::V2i clamp( const Imath::V2i &point, const Imath::Box2i &window );

/// Channel name utility functions.
///
/// Gaffer follows the OpenEXR convention for channel names, as documented at
/// http://openexr.com/InterpretingDeepPixels.pdf. Briefly :
///
/// - Channels are grouped into layers by prefixing the
///   channel name with the layer name followed by a '.'.
/// - The part of the channel name after the layer name
///   encodes the interpretation of the channel as either
///   a colour channel, alpha channel, depth channel or
///   auxiliary channel. This is referred to as the baseName.
///     - "R" is the red component of the colour
///     - "G" is the green component of the colour
///	    - "B" is the blue component of the colour
///     - "A" is the alpha channel
///     - "Z" is the depth channel
///
////////////////////////////////////////////////////////////////////////////

/// Returns the name of the layer the channel belongs to.
/// This is simply the portion of the channelName up to the
/// last '.', or "" if no such separator exists.
inline std::string layerName( const std::string &channelName );

/// Returns the base name for a channel - the portion of
/// the name following the last '.', or the whole name
/// if no separator exists.
inline std::string baseName( const std::string &channelName );

/// Returns 0, 1, 2 and 3 for base names "R", "G", "B"
/// and "A" respectively. Returns -1 for all other base names.
inline int colorIndex( const std::string &channelName );

} // namespace GafferImage

#include "GafferImage/ImageAlgo.inl"

#endif // GAFFERIMAGE_IMAGEALGO_H
