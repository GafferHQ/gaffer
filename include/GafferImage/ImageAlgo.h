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

#include "IECoreImage/ImagePrimitive.h"

#include "GafferImage/Export.h"

#include "Gaffer/Context.h"

#include "IECore/CompoundObject.h"
#include "IECore/Export.h"

IECORE_PUSH_DEFAULT_VISIBILITY
#include "OpenEXR/OpenEXRConfig.h"
#if OPENEXR_VERSION_MAJOR < 3
#include "OpenEXR/ImathBox.h"
#else
#include "Imath/ImathBox.h"
#endif
IECORE_POP_DEFAULT_VISIBILITY

#include <vector>

namespace GafferImage
{

class ImagePlug;

namespace ImageAlgo
{

/// Channel name utility functions
/// ==============================
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

/// Returns the names of all layers present in the specified channels.
GAFFERIMAGE_API std::vector<std::string> layerNames( const std::vector<std::string> &channelNames );

/// Returns the name of the layer the channel belongs to.
/// This is simply the portion of the channelName up to the
/// last '.', or "" if no such separator exists.
std::string layerName( const std::string &channelName );

/// Returns the base name for a channel - the portion of
/// the name following the last '.', or the whole name
/// if no separator exists.
std::string baseName( const std::string &channelName );

/// Joins a layer name and base name to form a channel name.
std::string channelName( const std::string &layerName, const std::string &baseName );

/// Returns 0, 1, 2 and 3 for base names "R", "G", "B"
/// and "A" respectively. Returns -1 for all other base names.
int colorIndex( const std::string &channelName );

/// Returns true if the specified channel exists in image
bool channelExists( const ImagePlug *image, const std::string &channelName );

/// Returns true if the specified channel exists in channelNames
bool channelExists( const std::vector<std::string> &channelNames, const std::string &channelName );

/// We don't usually need to sort channel names, but it's useful to put them in a
/// consistent order when displaying in the UI or writing to file.
/// Our sort rules are:
/// * channels not in a layer come first
/// * the channels RGBA are sorted in that order, and come before any other channels in the same layer
/// * otherwise, things are sorted using a natural ordering
GAFFERIMAGE_API std::vector<std::string> sortedChannelNames( const std::vector<std::string> &channelNames );

/// Default channel names
/// ==============================
///
/// You can just use your own strings, but it can be convenient to use these

GAFFERIMAGE_API extern const std::string channelNameA;
GAFFERIMAGE_API extern const std::string channelNameR;
GAFFERIMAGE_API extern const std::string channelNameG;
GAFFERIMAGE_API extern const std::string channelNameB;
GAFFERIMAGE_API extern const std::string channelNameZ;
GAFFERIMAGE_API extern const std::string channelNameZBack;

/// Parallel processing functions
/// ==============================
///

enum TileOrder
{
	Unordered,
	BottomToTop,
	TopToBottom
};

// Call the functor in parallel, once per tile
template <class TileFunctor>
void parallelProcessTiles(
	const ImagePlug *imagePlug,
	TileFunctor &&functor, // Signature : void functor( const ImagePlug *imagePlug, const V2i &tileOrigin )
	const Imath::Box2i &window = Imath::Box2i(), // Uses dataWindow if not specified ( requires a valid view in the context )
	TileOrder tileOrder = Unordered
);

// Call the functor in parallel, once per tile per channel
template <class TileFunctor>
void parallelProcessTiles(
	const ImagePlug *imagePlug,
	const std::vector<std::string> &channelNames,
	TileFunctor &&functor, // Signature : void functor( const ImagePlug *imagePlug, const string &channelName, const V2i &tileOrigin )
	const Imath::Box2i &window = Imath::Box2i(), // Uses dataWindow if not specified ( requires a valid view in the context )
	TileOrder tileOrder = Unordered
);

// Process all tiles in parallel using TileFunctor, passing the
// results in series to GatherFunctor.
template <class TileFunctor, class GatherFunctor>
void parallelGatherTiles(
	const ImagePlug *image,
	const TileFunctor &tileFunctor, // Signature : T tileFunctor( const ImagePlug *imagePlug, const V2i &tileOrigin )
	GatherFunctor &&gatherFunctor, // Signature : void gatherFunctor( const ImagePlug *imagePlug, const V2i &tileOrigin, T &tileFunctorResult )
	const Imath::Box2i &window = Imath::Box2i(), // Uses dataWindow if not specified ( requires a valid view in the context )
	TileOrder tileOrder = Unordered
);

// Process all tiles in parallel using TileFunctor, passing the
// results in series to GatherFunctor.
template <class TileFunctor, class GatherFunctor>
void parallelGatherTiles(
	const ImagePlug *image,
	const std::vector<std::string> &channelNames,
	const TileFunctor &tileFunctor, // Signature : T tileFunctor( const ImagePlug *imagePlug, const string &channelName, const V2i &tileOrigin )
	GatherFunctor &&gatherFunctor, // Signature : void gatherFunctor( const ImagePlug *imagePlug, const string &channelName, const V2i &tileOrigin, T &tileFunctorResult )
	const Imath::Box2i &window = Imath::Box2i(), // Uses dataWindow if not specified ( requires a valid view in the context )
	TileOrder tileOrder = Unordered
);

/// Whole view operations
/// ==============================
///
/// The functions process a whole view of an image at once.  Not generally used in core Gaffer processing, since we
/// prefer to process just one tile at a time, but useful for testing and interoperability.
/// If the view is not specified, it must be set in the current Context.

/// Returns a pointer to an IECore::ImagePrimitive. Note that the image's
/// coordinate system will be converted to the OpenEXR and Cortex specification
/// and have it's origin in the top left of it's display window with the positive
/// Y axis pointing downwards rather than Gaffer's internal representation where
/// the origin is in the bottom left of the display window with the Y axis
/// ascending towards the top of the display window.
GAFFERIMAGE_API IECoreImage::ImagePrimitivePtr image( const ImagePlug *imagePlug, const std::string *viewName = nullptr );

/// Return a hash that will vary if any aspect of the return from image( ... ) varies
GAFFERIMAGE_API IECore::MurmurHash imageHash( const ImagePlug *imagePlug, const std::string *viewName = nullptr );

/// Return all pixel data as a big CompoundData with entries for each channel
/// and tile.  Among other things, this makes it possible to efficiently test
/// from Python whether two ImagePlugs have identical pixel data.  Unlike the
/// image() method above, it works on deep images.
GAFFERIMAGE_API IECore::ConstCompoundObjectPtr tiles( const ImagePlug *imagePlug, const std::string *viewName = nullptr );

/// Deep Utils
/// ==============================

/// If the provided sample offsets do not match, raise an exception that indicates where the mismatch occured.
GAFFERIMAGE_API void throwIfSampleOffsetsMismatch( const IECore::IntVectorData* sampleOffsetsA, const IECore::IntVectorData* sampleOffsetsB, const Imath::V2i &tileOrigin, const std::string &message );


/// Multi-View Utils
/// ==============================

// Return true if the current view in the context is one of the viewNames, or is covered by a default view
GAFFERIMAGE_API bool viewIsValid( const Gaffer::Context *context, const std::vector< std::string > &viewNames );

} // namespace ImageAlgo

} // namespace GafferImage

#include "GafferImage/ImageAlgo.inl"
