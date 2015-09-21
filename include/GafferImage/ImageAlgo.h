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

#include <vector>
#include "boost/range.hpp"
#include "OpenEXR/ImathBox.h"

namespace GafferImage
{

class ImagePlug;

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

/// Returns true if the specified channel exists in image
inline bool channelExists( const ImagePlug *image, const std::string &channelName );

/// Returns true if the specified channel exists in channelNames
inline bool channelExists( const std::vector<std::string> &channelNames, const std::string &channelName );

enum TileOrder
{
	Unordered,
	BottomToTop,
	TopToBottom
};

// Call the functor in parallel, once per tile
template <class ThreadableFunctor>
void parallelProcessTiles(
	const ImagePlug *imagePlug,
	ThreadableFunctor &functor, // Signature : void functor( const ImagePlug *imagePlug, const V2i &tileOrigin )
	const Imath::Box2i &window = Imath::Box2i() // Uses dataWindow if not specified.
);

// Call the functor in parallel, once per tile per channel
template <class ThreadableFunctor>
void parallelProcessTiles(
	const ImagePlug *imagePlug,
	const std::vector<std::string> &channelNames,
	ThreadableFunctor &functor, // Signature : void functor( const ImagePlug *imagePlug, const string &channelName, const V2i &tileOrigin )
	const Imath::Box2i &window = Imath::Box2i() // Uses dataWindow if not specified.
);

// Process all tiles in parallel using TileFunctor, passing the
// results in series to GatherFunctor.
template <class TileFunctor, class GatherFunctor>
void parallelGatherTiles(
	const ImagePlug *image,
	TileFunctor &tileFunctor, // Signature : TileFunctor::Result tileFunctor( const ImagePlug *imagePlug, const V2i &tileOrigin )
	GatherFunctor &gatherFunctor, // Signature : void gatherFunctor( const ImagePlug *imagePlug, const V2i &tileOrigin, TileFunctor::Result )
	const Imath::Box2i &window = Imath::Box2i(), // Uses dataWindow if not specified.
	TileOrder tileOrder = Unordered
);

// Process all tiles in parallel using TileFunctor, passing the
// results in series to GatherFunctor.
template <class TileFunctor, class GatherFunctor>
void parallelGatherTiles(
	const ImagePlug *image,
	const std::vector<std::string> &channelNames,
	TileFunctor &tileFunctor, // Signature : TileFunctor::Result tileFunctor( const ImagePlug *imagePlug, const string &channelName, const V2i &tileOrigin )
	GatherFunctor &gatherFunctor, // Signature : void gatherFunctor( const ImagePlug *imagePlug, const string &channelName, const V2i &tileOrigin, TileFunctor::Result )
	const Imath::Box2i &window = Imath::Box2i(), // Uses dataWindow if not specified.
	TileOrder tileOrder = Unordered
);


template <typename T>
struct SampleRange
{
    typedef boost::iterator_range<typename std::vector<T>::iterator> Type;
};

template <typename T>
struct ConstSampleRange
{
    typedef boost::iterator_range<typename std::vector<T>::const_iterator> Type;
};

typedef SampleRange<float>::Type FloatSampleRange;
typedef SampleRange<int>::Type IntSampleRange;

typedef ConstSampleRange<float>::Type ConstFloatSampleRange;
typedef ConstSampleRange<int>::Type ConstIntSampleRange;

/// Get the number of samples that are in a specific pixel
inline int sampleCount( const std::vector<int>::const_iterator &sampleOffset, const std::vector<int>::const_iterator &sampleOffsetBegin );
inline int sampleCount( const std::vector<int> &sampleOffsets, const Imath::V2i &tilePos );

/// Get an iterator range for the samples defined by the pixel ID.
template<typename T>
inline typename SampleRange<T>::Type sampleRange( std::vector<T> &channelData, const std::vector<int>::const_iterator &sampleOffset, const std::vector<int>::const_iterator &sampleOffsetBegin );
template<typename T>
inline typename SampleRange<T>::Type sampleRange( std::vector<T> &channelData, const std::vector<int> &sampleOffsets, const Imath::V2i &tilePos );

template<typename T>
inline typename ConstSampleRange<T>::Type sampleRange( const std::vector<T> &channelData, const std::vector<int>::const_iterator &sampleOffset, const std::vector<int>::const_iterator &sampleOffsetBegin );
template<typename T>
inline typename ConstSampleRange<T>::Type sampleRange( const std::vector<T> &channelData, const std::vector<int> &sampleOffsets, const Imath::V2i &tilePos );

/// Get the existing channel from channelNames that should be used as the associated
/// alpha channel for channelName. If this returns an empty string, then there is either
/// no alpha channel in channelNames or channelName is an alpha or depth channel.
inline std::string channelAlpha( const std::string &channelName, const std::vector<std::string> &channelNames );

inline int tileIndex( const Imath::V2i &tilePos );

} // namespace GafferImage

#include "GafferImage/ImageAlgo.inl"

#endif // GAFFERIMAGE_IMAGEALGO_H
