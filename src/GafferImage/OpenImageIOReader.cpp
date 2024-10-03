//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
//  Copyright (c) 2012-2019, Image Engine Design Inc. All rights reserved.
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

#include "GafferImage/OpenImageIOReader.h"

// The nested TaskMutex needs to be the first to include tbb
#include "Gaffer/Private/IECorePreview/LRUCache.h"

#include "GafferImage/FormatPlug.h"
#include "GafferImage/ImageAlgo.h"
#include "GafferImage/ImageReader.h"

#include "Gaffer/Context.h"
#include "Gaffer/StringPlug.h"

#include "IECoreImage/OpenImageIOAlgo.h"

#include "IECore/Export.h"
#include "IECore/FileSequence.h"
#include "IECore/FileSequenceFunctions.h"
#include "IECore/MessageHandler.h"

#include "OpenImageIO/imagecache.h"
#include "OpenImageIO/deepdata.h"

#include <boost/algorithm/string.hpp>
#include "boost/bind/bind.hpp"
#include "boost/regex.hpp"

#include "tbb/parallel_for.h"
#include "tbb/enumerable_thread_specific.h"

#include <memory>

OIIO_NAMESPACE_USING

using namespace std;
using namespace boost::placeholders;
using namespace tbb;
using namespace Imath;
using namespace IECore;
using namespace GafferImage;
using namespace Gaffer;

namespace
{

// \todo - this should become unnecessary once we find a better data type for channel data
//
//
// We don't want to waste time setting a bunch of memory to 0 before we launch the threads that
// will actually fill that memory, but STL vector is designed to prevent us from allocating memory
// without wasting time initializing it. The long term solution is probably to choose a new type
// for channel data ( we'd probably want to change the API for ChannelDataProcessor at the same
// time to avoid copying channel data before we modify it ).
//
// In the mean time, I'm hacking around the STL behaviour by using a non-standards compliant
// reinterpret_cast to pretend that the vector is a vector of a custom class with the same size as
// our target, but without any initialization behaviour.
//
// This reduces runtime from 0.6 seconds to 0.37 seconds on a test with an 8K x 8K half float
// scanline exr.
template<typename T>
void podVectorResizeUninitialized( std::vector<T> &v, size_t s )
{
	struct TNoInit
	{
		T data;
		TNoInit() noexcept {
		}
	};

#ifdef NDEBUG
	reinterpret_cast< std::vector< TNoInit >* >( &v )->resize( s );
#else
	// Actually leaving things uninitialized is great for performance, but not so great for reliably
	// tracking down bugs. In debug mode, where we don't care about performance, set everything to a
	// sentinel value that will make it obvious if something uses an uninitialized value.
	v.resize( s, 777 );
#endif
}

const IECore::InternedString g_tileBatchOriginContextName( "__tileBatchOrigin" );
const IECore::InternedString g_noView( "" );

const std::string g_oiioCompression( "compression" );

struct ChannelMapEntry
{
	ChannelMapEntry( int subImage, int channelIndex )
		: subImage( subImage ), channelIndex( channelIndex )
	{}

	ChannelMapEntry( const ChannelMapEntry & ) = default;

	ChannelMapEntry()
		: subImage( 0 ), channelIndex( 0 )
	{}

	ChannelMapEntry& operator=( const ChannelMapEntry &rhs ) = default;

	int subImage;
	int channelIndex;
};

// This function transforms an input region to account for the display window being flipped.
// This is similar to Format::fromEXRSpace/toEXRSpace but those functions mix in switching
// between inclusive/exclusive bounds, so in order to use them we would have to add a bunch
// of confusing offsets by 1.  In this class, we always interpret ranges as [ minPixel, onePastMaxPixel )
Box2i flopDisplayWindow( const Box2i &b, const ImageSpec &spec )
{
	return Box2i(
		V2i( b.min.x, spec.full_y + spec.full_y + spec.full_height - b.max.y ),
		V2i( b.max.x, spec.full_y + spec.full_y + spec.full_height - b.min.y )
	);
}

// A divide that always rounds down, instead of towards zero
//  ( note that b is assumed positive )
int coordinateDivide( int a, int b )
{
	int result = a / b;
	int remainder = a - result * b;
	return result - ( remainder < 0 );
}

V2i coordinateDivide( V2i a, V2i b )
{
	return V2i( coordinateDivide( a.x, b.x ), coordinateDivide( a.y, b.y ) );
}

std::string channelNameFromEXR( std::string view, std::string part, std::string channel, bool useHeuristics, bool singlePartMultiView )
{
	if( !useHeuristics )
	{
		// This is correct way to do things, according to the EXR spec.  The channel name is the channel name,
		// and is not affected by anything else.  The only special case we need to handle is removing the view
		// from the name in the case of single part multi-view files.

		if( view.size() && singlePartMultiView )
		{
			std::vector< std::string > channelTokens;
			boost::split( channelTokens, channel, boost::is_any_of(".") );
			if( channelTokens.size() >= 2 && channelTokens[ channelTokens.size() - 2 ] == view )
			{
				channelTokens.erase( channelTokens.end() - 2 );
				return boost::algorithm::join( channelTokens, "." );
			}
		}
		return channel;
	}

	// But if useHeuristics is on, try to figure out which of the dozen incorrect interpretations of the EXR spec
	// this might adhere to
	std::vector< std::string > layerTokens;
	bool partUnderscoreSplit = false;
	string baseName;

	std::string layer = ImageAlgo::layerName( channel );
	if( layer.size() )
	{
		// If there is a layer name in the channel, then we can assume that it at least follows the EXR
		// spec that far, and we don't need to consider prefixing on the part name
		baseName = ImageAlgo::baseName( channel );
		boost::split( layerTokens, layer, boost::is_any_of(".") );
	}
	else
	{
		baseName = channel;

		// No layer name in the channel, so try setting the layer name from the part name
		boost::split( layerTokens, part, boost::is_any_of(".") );
		if( layerTokens.size() == 1 )
		{
			// There are no period seperators in the part name.  We've seen a few examples
			// of underscore seperators used in part names, so try that
			boost::split( layerTokens, part, boost::is_any_of("_") );
			partUnderscoreSplit = layerTokens.size() > 1;
		}
	}

	layerTokens.erase( std::remove_if( layerTokens.begin(), layerTokens.end(),
		[ view, baseName ](const std::string &i )
		{
			// Remove any tokens from the layer name that are useless.  This is usually
			// because they are alternate names for the default layer - Nuke puts channels
			// from the default layer in layers named "rgba", "depth", or "other", depending
			// on the channel name.  If a token matches the view name, we assume it's a view
			// token, and can be removed ( we represent views seperately ).
			std::string lower = boost::algorithm::to_lower_copy( i);
			return lower == "main" || lower == "rgb" || lower == "rgba" || lower == "other"
				|| ( lower == "depth" && baseName == "Z" ) || i == view || lower == "";
		}
	), layerTokens.end() );

	// Nuke uses non-standard "red", "green", "blue" and "alpha", and other
	// packages use lower case "r", "g", "b", "a". In some cases I suspect the
	// latter is a workaround to thwart unwanted DWAA compression, which only
	// applies to the uppercased names. And perhaps that is also the reason why
	// the Cryptomatte specification uses lowercase names? Fix everything up so
	// that Gaffer will recognise them as standard RGBA channels.
	if( baseName == "red" || baseName == "r" )
	{
		baseName = "R";
	}
	else if( baseName == "green" || baseName == "g" )
	{
		baseName = "G";
	}
	else if( baseName == "blue" || baseName == "b" )
	{
		baseName = "B";
	}
	else if( baseName == "alpha" || baseName == "a" )
	{
		baseName = "A";
	}

	if( layerTokens.size() == 0 )
	{
		// If we've removed all tokens, that means the channels are actually in the main layer, even though
		// they may have had a weird name in the file.
		return baseName;
	}
	else if( partUnderscoreSplit )
	{
		// It doesn't really make sense to split on underscores, they're not really layer seperators, but
		// we have seen some software that uses underscores in the part names.  This is actually totally fair
		// according to the spec, since part names don't actually mean anything - it would load fine with
		// channelInterpretation = Specification.  But it would go wrong in the Default heuristic mode, because
		// we would think that the part name is a weird Nuke layer name if it doesn't match one of the default
		// part names we recognize.  So we split on underscores, and hopefully what we're left with is a part
		// name and view name we recognize, and we hit the previous branch ( an example we've seen where this
		// would work is rgba_main ).  But if we aren't able to fully get rid of the layerTokens, we shouldn't
		// output half of a name with an underscore in it ( that would be confusing ).  So fall back to just
		// concatenating part name and base name
		return part + "." + baseName;
	}
	else
	{
		// In the default case, we reassemble a name using any layer tokens we haven't discarded as useless.
		return boost::algorithm::join( layerTokens, "." ) + "." + baseName;
	}

}

inline void basicBlit(
	int width, int height,
	const float* src, int srcStrideX, int srcStrideY,
	float* dst, int dstStrideX, int dstStrideY
)
{
	/*
	This is a very standard blit. It could be implemented by calling an OIIO function like
	this:

	OIIO::convert_image (
		1, width, height, 1,
		src, TypeDesc::FLOAT, srcStrideX * sizeof( float ), srcStrideY * sizeof( float ), 0,
		dst, TypeDesc::FLOAT, dstStrideX * sizeof( float ), dstStrideY * sizeof( float ), 0
	);

	However, that is somehow slower than a manual implementation ... it's possible that
	treating the memory as floats is somehow faster than than treating it as generic bytes?
	Maybe OIIO will fix their performance at some point, and then we can remove this function.

	If we were using the OIIO function, we would have the option of not forcing the intermediate
	buffer to be float, and instead using whatever the native data format is ... I thought that
	might make things faster, but instead in testing in made them even slower.
	*/

	for( int i = 0; i < height; i++ )
	{
		float *dstStart = dst + dstStrideY * i;
		float *dstEnd = dstStart + width * dstStrideX;

		const float *curSrc = src + srcStrideY * i;

		for( float *p = dstStart; p < dstEnd; p += dstStrideX )
		{
			*p = *curSrc;
			curSrc += srcStrideX;
		}
	}
}

// Similar to the basic blit, but copies sample counts from OIIO::DeepData
// The x strides are hardcoded to 1, since this fits all our usage
inline void sampleCountBlit(
	int width, int height,
	const OIIO::DeepData &src, int srcStartIndex, int srcStrideY,
	int* dst, int dstStrideY
)
{
	for( int i = 0; i < height; i++ )
	{
		int *dstStart = dst + dstStrideY * i;
		int *dstEnd = dstStart + width;

		int curSrc = srcStartIndex + srcStrideY * i;

		for( int *p = dstStart; p < dstEnd; p++ )
		{
			*p = src.samples( curSrc );
			curSrc++;
		}
	}
}

// Similar to the basic blit, but copies all deep samples in each pixel.
// The x strides are hardcoded to 1, since this fits all our usage, and
// allows for optimization
inline void deepBlit(
	int width, int height,
	const OIIO::DeepData &src, int channel, int srcStartIndex, int srcStrideY,
	const int* dstOffsets, int dstStartIndex, int dstStrideY, float *dst
)
{
	for( int i = 0; i < height; i++ )
	{
		int prevOffset = 0;
		if( dstStartIndex + dstStrideY * i > 0 )
		{
			prevOffset = dstOffsets[ dstStartIndex + dstStrideY * i - 1 ];
		}
		float *curDst = dst + prevOffset;

		int rowLast = srcStartIndex + srcStrideY * i + width;
		for( int j = srcStartIndex + srcStrideY * i; j < rowLast; j++ )
		{
			int numSamples = src.samples( j );
			for( int k = 0; k < numSamples; k++ )
			{
				*curDst = src.deep_value( j, channel, k );
				curDst++;
			}
		}
	}
}

// Copies data from an intermediate buffer into the Gaffer tiles, accounting for differences in storage
// between OIIO and Gaffer.
//
// The source data in OIIO format has the channels interleaved, and is flipped in Y relative to Gaffer.
// The Gaffer targets are a series of tiles of a fixed size, with separate tiles for each channel.

void blitOIIORectToTileBatch(
		int numChannels, float* buffer, const Box2i &rect,
		const V2i &tileBatchSize, const V3i &tileBatchOrigin, std::vector< float* > &tilePointers,
		const vector< Box2i > &tileDataWindows
)
{
	const unsigned int tileBatchChannelSize = tileBatchSize.x * tileBatchSize.y;

	const V2i rectSize = rect.size();
	for( int ty = 0; ty < tileBatchSize.y; ty++ )
	{
		int tileRelMinY = rect.min.y - ( tileBatchOrigin.y + ImagePlug::tileSize() * ty );
		int clampedMinY = std::max( tileRelMinY, 0 );
		int height = std::min( tileRelMinY + rectSize.y, ImagePlug::tileSize() ) - clampedMinY;

		if( height <= 0 )
		{
			// If there is no vertical overlap between the source rectangle and this row of tiles,
			// skip the whole row
			continue;
		}

		for( int tx = 0; tx < tileBatchSize.x; tx++ )
		{
			int tileRelMinX = rect.min.x - ( tileBatchOrigin.x + ImagePlug::tileSize() * tx );

			int clampedMinX = std::max( tileRelMinX, 0 );
			int width = std::min( tileRelMinX + rectSize.x, ImagePlug::tileSize() ) - clampedMinX;

			if( width <= 0 )
			{
				continue;
			}

			int tileBatchIndex = ty * tileBatchSize.x + tx;

			int tileStartIndex = clampedMinY * ImagePlug::tileSize() + clampedMinX;

			// Note that in order to account for the OIIO rect being upside down relative to Gaffer,
			// we offset this start index to the last row of the source rect, and pass a negative
			// srcStrideY to basicBlit.
			int rectStartIndex = clampedMinX - tileRelMinX +
				( rectSize.y - 1 - ( clampedMinY - tileRelMinY ) ) * rectSize.x;

			for( int channel = 0; channel < numChannels; channel++ )
			{
				basicBlit(
					width, height, &buffer[rectStartIndex * numChannels + channel ],
					numChannels, -numChannels * rectSize.x,
					&tilePointers[ channel * tileBatchChannelSize + tileBatchIndex ][ tileStartIndex ],
					1, ImagePlug::tileSize()
				);
			}

			// This is a bit irregular, but we don't want to initialize tiles up front before threading
			// can get started ... but we do want to set to 0 anything outside the data window ( in case
			// a different part of a multipart file has a different data window, this data could end up
			// being used ). In order to ensure that this cost is spread reasonably between threads,
			// and happens exactly once, whoever blits to the pixel at the minimum of the data window
			// of a partially covered tile, is responsible for zeroing out all the parts of that tile
			// outside the data window.
			if(
				!(
					tileDataWindows[tileBatchIndex].min.x == 0 &&
					tileDataWindows[tileBatchIndex].min.y == 0 &&
					tileDataWindows[tileBatchIndex].max.x == ImagePlug::tileSize() &&
					tileDataWindows[tileBatchIndex].max.y == ImagePlug::tileSize()
				)
			)
			{
				const Box2i &tileDataWindow = tileDataWindows[tileBatchIndex];
				if( tileStartIndex == tileDataWindow.min.y * ImagePlug::tileSize() + tileDataWindow.min.x )
				{
					for( int channel = 0; channel < numChannels; channel++ )
					{
						float *tilePtr = tilePointers[ channel * tileBatchChannelSize + tileBatchIndex ];
						for( int y = 0; y < ImagePlug::tileSize(); y++ )
						{
							if( y < tileDataWindow.min.y || y >= tileDataWindow.max.y )
							{
								memset(
									&tilePtr[ y * ImagePlug::tileSize() ], 0,
									sizeof( float ) * ImagePlug::tileSize()
								);
								continue;
							}

							if( tileDataWindow.min.x > 0 )
							{
								memset(
									&tilePtr[ y * ImagePlug::tileSize() ], 0,
									sizeof( float ) * tileDataWindow.min.x
								);
							}

							if( tileDataWindow.max.x < ImagePlug::tileSize() )
							{
								memset(
									&tilePtr[ y * ImagePlug::tileSize() + tileDataWindow.max.x ], 0,
									sizeof( float ) * ( ImagePlug::tileSize() - tileDataWindow.max.x )
								);
							}
						}
					}
				}
			}
		}
	}
}

void blitOIIOSampleCountsToTileBatch(
	const OIIO::DeepData &deepData, const Box2i &rect,
	const V2i &tileBatchSize, const V3i &tileBatchOrigin, std::vector< int* > &tilePointers
)
{
	const V2i rectSize = rect.size();
	for( int ty = 0; ty < tileBatchSize.y; ty++ )
	{
		int tileRelMinY = rect.min.y - ( tileBatchOrigin.y + ImagePlug::tileSize() * ty );
		int clampedMinY = std::max( tileRelMinY, 0 );
		int height = std::min( tileRelMinY + rectSize.y, ImagePlug::tileSize() ) - clampedMinY;

		if( height <= 0 )
		{
			// If there is no vertical overlap between the source rectangle and this row of tiles,
			// skip the whole row
			continue;
		}

		for( int tx = 0; tx < tileBatchSize.x; tx++ )
		{
			int tileRelMinX = rect.min.x - ( tileBatchOrigin.x + ImagePlug::tileSize() * tx );

			int clampedMinX = std::max( tileRelMinX, 0 );
			int width = std::min( tileRelMinX + rectSize.x, ImagePlug::tileSize() ) - clampedMinX;

			if( width <= 0 )
			{
				continue;
			}

			int tileBatchIndex = ty * tileBatchSize.x + tx;

			int tileStartIndex = clampedMinY * ImagePlug::tileSize() + clampedMinX;

			// Note that in order to account for the OIIO rect being upside down relative to Gaffer,
			// we offset this start index to the last row of the source rect, and pass a negative
			// srcStrideY to basicBlit.
			int rectStartIndex = clampedMinX - tileRelMinX +
				( rectSize.y - 1 - ( clampedMinY - tileRelMinY ) ) * rectSize.x;

			sampleCountBlit(
				width, height, deepData, rectStartIndex,
				-rectSize.x,
				&tilePointers[ tileBatchIndex ][ tileStartIndex ],
				ImagePlug::tileSize()
			);
		}
	}
}

void blitDeepOIIORectToTileBatch(
	int numChannels, const OIIO::DeepData &deepData, const Box2i &rect,
	const V2i &tileBatchSize, const V3i &tileBatchOrigin, std::vector< float* > &tileChannelPointers,
	const std::vector< int* > &tileOffsetPointers
)
{
	const unsigned int tileBatchChannelSize = tileBatchSize.x * tileBatchSize.y;

	const V2i rectSize = rect.size();
	for( int ty = 0; ty < tileBatchSize.y; ty++ )
	{
		int tileRelMinY = rect.min.y - ( tileBatchOrigin.y + ImagePlug::tileSize() * ty );
		int clampedMinY = std::max( tileRelMinY, 0 );
		int height = std::min( tileRelMinY + rectSize.y, ImagePlug::tileSize() ) - clampedMinY;

		if( height <= 0 )
		{
			// If there is no vertical overlap between the source rectangle and this row of tiles,
			// skip the whole row
			continue;
		}

		for( int tx = 0; tx < tileBatchSize.x; tx++ )
		{
			int tileRelMinX = rect.min.x - ( tileBatchOrigin.x + ImagePlug::tileSize() * tx );

			int clampedMinX = std::max( tileRelMinX, 0 );
			int width = std::min( tileRelMinX + rectSize.x, ImagePlug::tileSize() ) - clampedMinX;

			if( width <= 0 )
			{
				continue;
			}

			int tileBatchIndex = ty * tileBatchSize.x + tx;

			int tileStartIndex = clampedMinY * ImagePlug::tileSize() + clampedMinX;

			// Note that in order to account for the OIIO rect being upside down relative to Gaffer,
			// we offset this start index to the last row of the source rect, and pass a negative
			// srcStrideY to basicBlit.
			int rectStartIndex = clampedMinX - tileRelMinX +
				( rectSize.y - 1 - ( clampedMinY - tileRelMinY ) ) * rectSize.x;

			for( int channel = 0; channel < numChannels; channel++ )
			{
				deepBlit(
					width, height,
					deepData, channel, rectStartIndex, -rectSize.x,
					tileOffsetPointers[ tileBatchIndex ], tileStartIndex, ImagePlug::tileSize(),
					tileChannelPointers[ channel * tileBatchChannelSize + tileBatchIndex ]
				);
			}
		}
	}
}

// Convert a count in each pixel into a running sampleOffset. Only counts within
// the dataWindow are required to be initialized - counts outside the dataWindow
// are assumed to be 0 without being read.
void accumulateSampleOffsets( int *sampleOffsets, const Box2i &tileDataWindow )
{
	int accum = 0;

	if(
		tileDataWindow.min.x == 0 &&
		tileDataWindow.min.y == 0 &&
		tileDataWindow.max.x == ImagePlug::tileSize() &&
		tileDataWindow.max.y == ImagePlug::tileSize()
	)
	{
		// Whole tile is within data window, we are just doing a running sum of everything.
		int *last = sampleOffsets + ImagePlug::tilePixels();
		for( int *cur = sampleOffsets; cur < last; cur++ )
		{
			accum += *cur;
			*cur = accum;
		}
		return;
	}

	for( int y = 0; y < ImagePlug::tileSize(); y++ )
	{
		int *rowLast = sampleOffsets + ( y + 1 ) * ImagePlug::tileSize();
		int *cur = sampleOffsets + y * ImagePlug::tileSize();
		if( y < tileDataWindow.min.y || y >= tileDataWindow.max.y )
		{
			for( ; cur < rowLast; cur++ )
			{
				*cur = accum;
			}
			continue;
		}

		int *dataStart = sampleOffsets + y * ImagePlug::tileSize() + tileDataWindow.min.x;
		int *dataEnd = sampleOffsets + y * ImagePlug::tileSize() + tileDataWindow.max.x;
		for( ; cur < dataStart; cur++ )
		{
			*cur = accum;
		}
		for( ; cur < dataEnd; cur++ )
		{
			accum += *cur;
			*cur = accum;
		}
		for( ; cur < rowLast; cur++ )
		{
			*cur = accum;
		}
	}
}

// Compute the region of each tile that is within the data window
std::vector< Box2i > calculateTileDataWindows(
	int tileBatchNumTiles, const V3i &tileBatchOrigin, const V2i &tileBatchSize, const Box2i &gafferDataWindow
)
{
	std::vector< Box2i > result( tileBatchNumTiles );
	for( int subIndex = 0; subIndex < tileBatchNumTiles; subIndex++ )
	{
		int tx = subIndex % tileBatchSize.x;
		int ty = subIndex / tileBatchSize.x;
		V2i tileOrigin(
			tileBatchOrigin.x + tx * ImagePlug::tileSize(),
			tileBatchOrigin.y + ty * ImagePlug::tileSize()
		);

		Box2i tileRelativeBound( gafferDataWindow.min - tileOrigin, gafferDataWindow.max - tileOrigin );
		result[ subIndex ] = BufferAlgo::intersection(
			tileRelativeBound,
			Box2i( V2i( 0 ), V2i( ImagePlug::tileSize() ) )
		);
	}
	return result;
}

Box2i expandToGrid( Box2i region, V2i gridOrigin, V2i gridSize )
{
	return Box2i(
		coordinateDivide( region.min - gridOrigin, gridSize ) * gridSize + gridOrigin,
		coordinateDivide( region.max - gridOrigin + gridSize - V2i(1), gridSize ) * gridSize + gridOrigin
	);
}


// This class handles storing a file handle, and reading data from it in a way compatible with how we want
// to store it on plugs.
//
// The primary complexity is that Gaffer will request channel data a single tile at a time for a single channel,
// but the OpenImageIO will usually be forced to read a larger chunk of information in order to access that one
// tile - it will read all channels that are stored interleaved, and either full scanlines, or all overlapping
// tiles if the file is tiled on disk.
//
// To avoid repeatedly loading large chunks of data, and then discarding most of it, we group data into
// "tile batches".  A tile batch is an ObjectVector containing an array of separate channelData tiles.  It is
// a large enough chunk of data that it can be read from the file with minimal waste.  We cache tile batches
// on OpenImageIOReader::tileBatchPlug, and then OpenImageIOReader::computeChannelData just needs to select the
// correct tile batch, access tileBatchPlug, and then return the tile at the correct tileBatchSubIndex.
//
// For scanline images, a tile batch is one tile high, and the full width of the image.
// For tiled images, a tile batch is a fairly large fixed size ( current 512 pixels, or the tile size of the
// image, whichever is larger ).  This amortizes the waste from tiles which lie over the edge of a tile batch,
// and need to be read multiple times.
// Either way, a tile batch contains all channels stored in the subimage which contains the desired channel.
// For deep images, the tile batch also contains an extra channel worth of tiles at the end which store the
// samples offsets.
//
// Tile batches are selected using V3i "tileBatchOrigin".  The Z component is the subimage to load channels from.
// The X and Y components are the pixel coordinates of the origin of the first tile.
//
class File
{

	public:

		// Create a File handle object for an image input and image spec
		File( std::unique_ptr<ImageInput> imageInput, const std::string &infoFileName, ImageReader::ChannelInterpretation channelNaming )
			: m_imageInput( std::move( imageInput ) )
		{
			m_viewNamesData = new StringVectorData();
			auto &viewNames = m_viewNamesData->writable();

			bool singlePartMultiView = false;
			ImageSpec currentSpec;
			for( int subImageIndex = 0; ; subImageIndex++ )
			{
				currentSpec = m_imageInput->spec( subImageIndex, 0 );
				if( currentSpec.format == TypeUnknown )
				{
					// Gone past last subimage
					break;
				}

				if( currentSpec.depth != 1 )
				{
					throw IECore::Exception( "OpenImageIOReader : " + infoFileName + " : GafferImage does not support 3D pixel arrays " );
				}

				std::string viewName = currentSpec.get_string_attribute( "view", "" );

				if( viewName == "" && subImageIndex == 0 )
				{
					ParamValue *multiViewAttr = currentSpec.find_attribute( "multiView" );
					if( multiViewAttr )
					{
						if( multiViewAttr->type().basetype != TypeDesc::STRING || multiViewAttr->type().arraylen <= 0 )
						{
							IECore::msg(
								IECore::Msg::Warning, "OpenImageIOReader",
								fmt::format(
									"Ignoring invalid \"multiView\" attribute in \"{}\".",
									infoFileName
								)
							);
						}
						else
						{
							singlePartMultiView = true;

							for( int i = 0; i < multiViewAttr->type().arraylen; i++ )
							{
								viewNames.push_back( *((&multiViewAttr->get< char* >())+i) );
							}

							for( const std::string &view : viewNames )
							{
								m_views[view] = std::make_unique<View>( currentSpec, 0 );
							}
						}
					}
				}

				View *currentView = nullptr;
				if( !singlePartMultiView )
				{
					if( viewName == "" )
					{
						viewName = ImagePlug::defaultViewName;
					}

					auto [ viewPair, isNewView ] = m_views.emplace( viewName, nullptr );

					if( isNewView )
					{
						viewNames.push_back( viewName );

						viewPair->second = std::make_unique<View>( currentSpec, subImageIndex );
						currentView = viewPair->second.get();
					}
					else
					{
						currentView = viewPair->second.get();
						if( currentView->imageSpec.deep )
						{
							// We require the same sampleOffsets for all channels, so we don't really support
							// multiple subimages for deep.
							IECore::msg(
								IECore::Msg::Warning, "OpenImageIOReader",
								fmt::format(
									"Ignoring subimage {} of \"{}\" because we only support one part per view for deep images.",
									subImageIndex, infoFileName
								)
							);

							continue;
						}

						// \todo - rather than expanding the dataWindow in this format, it would probably be
						// better to not use the data window stored in view->imageSpec, and instead use
						// a data window we store ourselves as a Box2i.  Maybe the View constructor should set
						// imageSpec.width and height to 0 to enforce this?
						int maxDataX = std::max( currentSpec.x + currentSpec.width,
							currentView->imageSpec.x + currentView->imageSpec.width
						);
						int maxDataY = std::max( currentSpec.y + currentSpec.height,
							currentView->imageSpec.y + currentView->imageSpec.height
						);
						int minDataX = std::min( currentSpec.x, currentView->imageSpec.x );
						int minDataY = std::min( currentSpec.y, currentView->imageSpec.y );
						currentView->imageSpec.x = minDataX;
						currentView->imageSpec.y = minDataY;
						currentView->imageSpec.width = maxDataX - minDataX;
						currentView->imageSpec.height = maxDataY - minDataY;
					}
				}

				OIIO::string_view subImageName = currentSpec.get_string_attribute( "name", "" );

				for( const auto &n : currentSpec.channelnames )
				{
					std::string channelViewName;
					View *channelView;
					if( singlePartMultiView )
					{
						std::vector< std::string > possibleViewTokens;
						boost::split( possibleViewTokens, n, boost::is_any_of(".") );

						if( possibleViewTokens.size() == 1 )
						{
							// If we have a bare channel name, the single part multi-view spec says that
							// belongs to the first view ( EXR refers to this as the default view, but this
							// is different from our "default" view, which we use for channels not in any view )
							channelViewName = viewNames[0];
						}
						else
						{
							for( int i = possibleViewTokens.size() - 1; i >= 0; i-- )
							{
								auto multiViewIter = std::find( viewNames.begin(), viewNames.end(), possibleViewTokens[i] );
								if( multiViewIter != viewNames.end() )
								{
									channelViewName = possibleViewTokens[i];
									break;
								}
							}

							if( !channelViewName.size() )
							{
								// If there is a layer name in the channel name, but no view, according to
								// single part multi view spec, that means the channel does not belong to a view.
								channelViewName = ImagePlug::defaultViewName;

								if( m_views.find( ImagePlug::defaultViewName ) == m_views.end() )
								{
									m_views[ImagePlug::defaultViewName] = std::make_unique<View>( currentSpec, 0 );
									viewNames.push_back( ImagePlug::defaultViewName );
								}
							}
						}
						channelView = m_views[channelViewName].get();
					}
					else
					{
						channelViewName = viewName;
						channelView = currentView;
					}

					std::string channelName;
					if( channelNaming == ImageReader::ChannelInterpretation::Legacy )
					{
						// ImageAlgo::channelName just sticks together the layer and channel name
						// It's wrong in general to pass the subImageName as the layer, since the EXR spec
						// says the layer name is included in the channel name, and the subImageName should
						// not be meaningful to the channel name.  This just matches what we used to do -
						// with a minimal effort to clear out sub image name if it is main.
						// channelNameFromEXR has a more thorough heuristic for the Default channelNaming mode
						std::string legacySubImageName = subImageName;

						if( boost::iequals( legacySubImageName, "RGBA" ) || boost::iequals( legacySubImageName, "RGB" ) || boost::iequals( legacySubImageName, "depth" ) )
						{
							legacySubImageName = "";
						}

						channelName = ImageAlgo::channelName( legacySubImageName, n );
					}
					else
					{
						channelName = channelNameFromEXR(
							channelViewName, subImageName.str(), n,
							channelNaming != ImageReader::ChannelInterpretation::Specification,
							singlePartMultiView
						);
					}

					auto mapEntry = channelView->channelMap.find( channelName );
					if( mapEntry != channelView->channelMap.end() )
					{
						std::string m = fmt::format(
							"Ignoring channel \"{}\" in subimage \"{}\" of \"{}\" because it's already in subimage \"{}\"",
							channelName, subImageIndex, infoFileName, mapEntry->second.subImage
						);
						if( viewName != "" )
						{
							m += " for view <" + viewName +">.";
						}
						else
						{
							m += ".";
						}
						IECore::msg( IECore::Msg::Warning, "OpenImageIOReader", m );
					}
					else
					{
						channelView->channelMap[ channelName ] = ChannelMapEntry( subImageIndex, &n - &currentSpec.channelnames[0] );
						channelView->channelNames.push_back( channelName );
					}
				}
			}

			if( channelNaming != ImageReader::ChannelInterpretation::Specification && viewNames.size() == 1 && viewNames[0] == "main" )
			{
				// When Nuke writes images without specific views to EXR, it creates a single view named "main".
				// We want to treat this like a default EXR that doesn't specify anything about views, so we
				// rename it to "default".
				viewNames[0] = ImagePlug::defaultViewName;
				auto nodeHandle = m_views.extract( "main" );
				nodeHandle.key() = ImagePlug::defaultViewName;
				m_views.insert( std::move( nodeHandle ) );
			}
		}

		// Read a chunk of data from the file, formatted as a tile batch that will be stored on the tile batch plug
		ConstObjectVectorPtr readTileBatch( const Context *c, V3i tileBatchOrigin )
		{
			const View& view = lookupView( c );

			const ImageSpec spec = m_imageInput->spec( tileBatchOrigin.z, 0 );

			const int tileBatchNumTileChannels = spec.nchannels * view.tileBatchSize.y * view.tileBatchSize.x;
			const int tileBatchNumTiles = view.tileBatchSize.y * view.tileBatchSize.x;

			ObjectVectorPtr resultChannels = new ObjectVector();
			resultChannels->members().resize( tileBatchNumTileChannels );
			std::vector< float* > tileChannelPointers( tileBatchNumTileChannels );

			// Only used by deep images. These will initially hold sample counts, and then we will do
			// a running sum to convert these to the sampleOffsets expected for ImagePlug.
			ObjectVectorPtr resultOffsets;
			std::vector< int* > tileOffsetPointers;

			// Convert the data window from the file into Gaffer coordinates
			const V2i fileDataOrigin( spec.x, spec.y );
			const Box2i fileDataWindow( fileDataOrigin, fileDataOrigin + V2i( spec.width, spec.height ) );
			const Box2i gafferDataWindow = flopDisplayWindow( fileDataWindow, spec );

			// The region of each tile that is within the data window
			const std::vector< Box2i > tileDataWindows = calculateTileDataWindows(
				tileBatchNumTiles, tileBatchOrigin, view.tileBatchSize, gafferDataWindow
			);

			if( !spec.deep )
			{
				// For flat images we can allocate all the outputs from the start
				for( int subIndex = 0; subIndex < tileBatchNumTileChannels; subIndex++ )
				{
					if( !BufferAlgo::empty( tileDataWindows[ subIndex % tileBatchNumTiles ] ) )
					{
						FloatVectorDataPtr tileAlloc = new IECore::FloatVectorData();
						podVectorResizeUninitialized<float>( tileAlloc->writable(), ImagePlug::tilePixels() );
						tileChannelPointers[ subIndex ] = &tileAlloc->writable()[0];
						resultChannels->members()[ subIndex ] = std::move( tileAlloc );
					}
					else
					{
						// If this subImage has a smaller data window than other subImages for this view,
						// there may be tiles in the tile batch that are fully outside the data window.
						// We can just use black tiles for them.
						//
						// The const_cast is safe because we will never write to these tiles, and our output
						// is treated as const.
						resultChannels->members()[ subIndex ] = const_cast<IECore::FloatVectorData*>( ImagePlug::blackTile() );

						// To ensure that we never write to the tiles that must be treated as const, we set
						// the pointer used for writing these tiles to a nullptr.
						tileChannelPointers[ subIndex ] = nullptr;
					}
				}
			}
			else
			{
				// For deep images, we allocate the sample offsets, but can't allocate any of the channel
				// data until we know how many samples there are
				resultOffsets = new ObjectVector();
				resultOffsets->members().resize( tileBatchNumTiles );
				tileOffsetPointers.resize( tileBatchNumTiles );

				for( int subIndex = 0; subIndex < tileBatchNumTiles; subIndex++ )
				{
					if( !BufferAlgo::empty( tileDataWindows[ subIndex % tileBatchNumTiles ] ) )
					{
						IntVectorDataPtr tileAlloc = new IECore::IntVectorData();
						podVectorResizeUninitialized<int>( tileAlloc->writable(), ImagePlug::tilePixels() );
						tileOffsetPointers[ subIndex ] = &tileAlloc->writable()[0];
						resultOffsets->members()[ subIndex ] = std::move( tileAlloc );
					}
					else
					{
						// This is a bit of a weird case : we don't support multiple subImages for deep images,
						// so we will never use any tiles outside the data window. But for tiled images, the tile
						// batch size is constant, and the image could be smaller than that, resulting in tiles
						// outside the data window that are never used, and it's better not to have uninitialized
						// data lying around, so we do the same trick as we do for flat images here:
						resultOffsets->members()[ subIndex ] = const_cast<IECore::IntVectorData*>( ImagePlug::emptyTileSampleOffsets() );
						tileOffsetPointers[ subIndex ] = nullptr;
					}

				}
			}

			// Find the portion of the data window that intersects with the current tile batch,
			// and convert it from Gaffer coordinates to file coordinates.
			const V2i tileBatchOriginXY( tileBatchOrigin.x, tileBatchOrigin.y );
			const Box2i targetRegion = BufferAlgo::intersection(
				Box2i( tileBatchOriginXY, tileBatchOriginXY + view.tileBatchSize * ImagePlug::tileSize() ),
				gafferDataWindow
			);
			const Box2i fileTargetRegion = flopDisplayWindow( targetRegion, view.imageSpec );

			// It would probably be more efficient if we just did two separate traversals of the input regions,
			// with the first one setting EXR_DECODE_SAMPLE_DATA_ONLY, rather than decoding everything up front,
			// and having to hold it in memory while we compute our sample offsets before we can actually use it.
			// OIIO does not expose any way to do this though ... it would really make sense if passing chend = 0
			// would get you just the sample counts.
			std::vector< OIIO::DeepData > deepRectsData;
			std::vector< Box2i > deepRects;

			bool usingExrCore =
				strcmp( m_imageInput->format_name(), "openexr" ) == 0 &&
				OIIO::get_int_attribute( "openexr:core" );

			tbb::enumerable_thread_specific< std::vector< float > > threadBuffers;
			tbb::task_group_context taskGroupContext( tbb::task_group_context::isolated );

			const std::string compression = spec.get_string_attribute( g_oiioCompression );

			const V2i tileSize( spec.tile_width, spec.tile_height );

			if( tileSize == V2i( 0 ) && ( !usingExrCore || compression == "dwab" ) )
			{
				// If we are using compression other than EXR, or we're using the massive 256 scanline blocks
				// of DWAB, then we can't benefit from splitting the decompression over multiple threads -
				// we'll just use one thread for the whole batch. Would be nice if more of these cases
				// were efficiently threaded, but the current approach works well for "zips" compression,
				// or tiled images.
				//
				// Note this means scanline DWAB is a very poor match for our compute model in Gaffer.
				// Tiled DWAB works great though.

				if( spec.deep )
				{
					deepRects.resize( 1 );
					deepRectsData.resize( 1 );
				}

				std::vector<float> buffer;
				processFileRegionScanline(
					spec, tileBatchOrigin, fileTargetRegion, buffer,
					view.tileBatchSize, tileChannelPointers, tileDataWindows,
					deepRectsData.size() ? &deepRectsData[0] : nullptr,
					deepRects.size() ? &deepRects[0] : nullptr, tileOffsetPointers
				);
			}
			else if( tileSize == V2i( 0 ) )
			{
				// The standard case for scanline - we're using ExrCore, and we've got an exr that we
				// should be able to multithread

				// We need to batch together scanlines that are compressed together, otherwise we end up
				// repeating the work of decoding the whole compressed block for each scanline we need to access.
				// A batch of 16 scanlines works for the "zip" compression type, which compresses blocks of
				// 16 scanlines, and is a reasonable default if we encounter a compression type we haven't
				// accounted for.
				int compressionBatch = 16;

				if( compression == "zips" )
				{
					// For single-scanline zip compression, we can decode 1 scanline at a time, and benefit from
					// full multithreading.
					compressionBatch = 1;
				}
				else if( compression == "dwaa" )
				{
					// DWAA uses 32 scanline blocks
					// ( DWAB uses 256, so we just completely disable using multiple threads below )
					compressionBatch = 32;
				}

				// scanlineBatch and scanlineBatchOffset control how many scanlines we process at once,
				// and how they are aligned. In order to avoid decompressing the same EXR chunk multiple times,
				// it's important that these batches are aligned to the data origin in EXR space, not aligned
				// to the Gaffer tiles.
				int scanlineBatch = compressionBatch;
				int scanlineBatchOffset = ( ( fileTargetRegion.min.y - fileDataOrigin.y ) / compressionBatch ) * compressionBatch + fileDataOrigin.y;

				// Compute how many batches are needed to cover the size of the target region
				const int numScanlineBatches = ( fileTargetRegion.max.y - scanlineBatchOffset + scanlineBatch - 1 ) / scanlineBatch;

				if( spec.deep )
				{
					deepRects.resize( numScanlineBatches );
					deepRectsData.resize( numScanlineBatches );
				}

				tbb::parallel_for(
					tbb::blocked_range<int>( 0, numScanlineBatches ),
					[&] ( const tbb::blocked_range<int> &range )
					{
						std::vector<float> &buffer = threadBuffers.local();
						for( int i = range.begin(); i < range.end(); i++ )
						{
							const int y = i * scanlineBatch + scanlineBatchOffset;
							const int yEnd = std::min( y + scanlineBatch, fileTargetRegion.max.y );

							const Box2i batchRect(
								Imath::V2i( fileTargetRegion.min.x, y ),
								Imath::V2i( fileTargetRegion.max.x, yEnd )
							);

							processFileRegionScanline(
								spec, tileBatchOrigin, batchRect, buffer,
								view.tileBatchSize, tileChannelPointers, tileDataWindows,
								deepRectsData.size() ? &deepRectsData[i] : nullptr,
								deepRects.size() ? &deepRects[i] : nullptr, tileOffsetPointers
							);
						}
					},
					taskGroupContext
				);
			}
			else if( !usingExrCore )
			{
				// A tiled image that we can't use our threading on

				if( spec.deep )
				{
					deepRects.resize( 1 );
					deepRectsData.resize( 1 );
				}

				// Round the target region coordinates outwards to the tile boundaries in the file
				const Box2i fileTileRegion = expandToGrid( fileTargetRegion, fileDataOrigin, tileSize );

				std::vector<float> buffer;
				processFileRegionTiled(
					spec, tileBatchOrigin, BufferAlgo::intersection( fileTileRegion, fileDataWindow ), buffer,
					view.tileBatchSize, tileChannelPointers, tileDataWindows,
					deepRectsData.size() ? &deepRectsData[0] : nullptr,
					deepRects.size() ? &deepRects[0] : nullptr, tileOffsetPointers
				);
			}
			else
			{
				// A tiled image that we can multithread

				// Round the target region coordinates outwards to the tile boundaries in the file
				const Box2i fileTileRegion = expandToGrid( fileTargetRegion, fileDataOrigin, tileSize );

				const V2i fileTileCounts = fileTileRegion.size() / tileSize;

				const unsigned int numFileTiles = fileTileCounts.x * fileTileCounts.y;

				if( spec.deep )
				{
					deepRects.resize( numFileTiles );
					deepRectsData.resize( numFileTiles );
				}

				tbb::parallel_for(
					tbb::blocked_range<int>( 0, numFileTiles ),
					[&] ( const tbb::blocked_range<int> &range )
					{
						std::vector<float> &buffer = threadBuffers.local();
						for( int i = range.begin(); i < range.end(); i++ )
						{
							// For a tiled image, each tile can be it's own batch of processing, so we
							// get good parallelism.
							const V2i fileTile = fileTileRegion.min + V2i( i % fileTileCounts.x, i / fileTileCounts.x ) * tileSize;
							const Box2i batchRect = BufferAlgo::intersection( fileDataWindow, Imath::Box2i (
								Imath::V2i( fileTile.x, fileTile.y ),
								Imath::V2i( fileTile.x + tileSize.x, fileTile.y + tileSize.y )
							) );

							processFileRegionTiled(
								spec, tileBatchOrigin, batchRect, buffer,
								view.tileBatchSize, tileChannelPointers, tileDataWindows,
								deepRectsData.size() ? &deepRectsData[i] : nullptr,
								deepRects.size() ? &deepRects[i] : nullptr, tileOffsetPointers
							);
						}
					},
					taskGroupContext
				);
			}

			if( spec.deep )
			{
				// For a deep image, all we can actually do in the initial pass is set initial sample counts
				// ... we've still got lots of work to do to actually get the data in place.

				// This parallel loop over the tiles converts from sample counts to sample offsets,
				// and allocates all the channel data
				tbb::parallel_for(
					tbb::blocked_range<int>( 0, tileBatchNumTiles ),
					[&] ( const tbb::blocked_range<int> &range )
					{
						for( int i = range.begin(); i < range.end(); i++ )
						{
							if( !tileOffsetPointers[i] )
							{
								// Empty tiles outside the data window are never used, but we still need to make
								// sure we don't crash while processing them, so we might as well do something
								// reasonable.
								for( int c = 0; c < spec.nchannels; c++ )
								{
									resultChannels->members()[ c * tileBatchNumTiles + i ] = const_cast<IECore::FloatVectorData*>( ImagePlug::emptyTile() );
									tileChannelPointers[ c * tileBatchNumTiles + i ] = nullptr;
								}
								continue;
							}

							accumulateSampleOffsets( tileOffsetPointers[ i ], tileDataWindows[ i ] );

							int totalSamples = tileOffsetPointers[i][ ImagePlug::tilePixels() - 1 ];
							for( int c = 0; c < spec.nchannels; c++ )
							{
								FloatVectorDataPtr tileAlloc = new IECore::FloatVectorData();
								podVectorResizeUninitialized<float>( tileAlloc->writable(), totalSamples );

								tileChannelPointers[ c * tileBatchNumTiles + i ] = &tileAlloc->writable()[0];
								resultChannels->members()[ c * tileBatchNumTiles + i ] = std::move( tileAlloc );

							}
						}
					},
					taskGroupContext
				);

				// Now we can finally do one last parallel loop over the batches of OIIO data, and actually
				// copy the channel data into the right places in the Gaffer tiles.
				tbb::parallel_for(
					tbb::blocked_range<int>( 0, deepRects.size() ),
					[&] ( const tbb::blocked_range<int> &range )
					{
						for( int i = range.begin(); i < range.end(); i++ )
						{
							blitDeepOIIORectToTileBatch(
								spec.nchannels, deepRectsData[i], deepRects[i],
								view.tileBatchSize, tileBatchOrigin, tileChannelPointers,
								tileOffsetPointers
							);
						}
					},
					taskGroupContext
				);

			}

			ObjectVectorPtr result = new ObjectVector();
			result->members().resize( 2 );
			result->members()[0] = resultChannels;
			result->members()[1] = spec.deep ? resultOffsets : nullptr;

			return result;
		}

		// Given a channelName and tileOrigin, return the information necessary to look up the data for this tile.
		// The tileBatchOrigin is used to find a tileBatch, and then the tileBatchSubIndex tells you the index
		// within that tile to use
		void findTile( const Context *c, const std::string &channelName, const Imath::V2i &tileOrigin, V3i &batchOrigin, int &batchSubIndex ) const
		{
			const View& view = lookupView( c );
			if( !channelName.size() )
			{
				// For computing sample offsets
				// This is a bit of a weird interface, I should probably fix it
				batchOrigin = tileBatchOrigin( view, view.firstSubImage, tileOrigin );
				batchSubIndex = tileBatchSubIndex( view, 0, tileOrigin - V2i( batchOrigin.x, batchOrigin.y ) );
			}
			else
			{
				auto findIt = view.channelMap.find( channelName );
				if( findIt == view.channelMap.end() )
				{
					throw IECore::Exception( "OpenImageIOReader : No channel named \"" + channelName + "\"" );
				}
				ChannelMapEntry channelMapEntry = findIt->second;
				batchOrigin = tileBatchOrigin( view, channelMapEntry.subImage, tileOrigin );
				batchSubIndex = tileBatchSubIndex( view, channelMapEntry.channelIndex, tileOrigin - V2i( batchOrigin.x, batchOrigin.y ) );
			}
		}

		void processFileRegionScanline(
			const ImageSpec &spec, const V3i &tileBatchOrigin, const Box2i &regionRect, std::vector<float> &buffer,
			const V2i &tileBatchSize, std::vector< float* > &tileChannelPointers,
			const std::vector< Box2i > &tileDataWindows,
			OIIO::DeepData *deepRectData, Box2i *deepRect, std::vector< int* > &tileOffsetPointers
		)
		{
			Box2i gafferRegionRect = flopDisplayWindow( regionRect, spec );

			if( !spec.deep )
			{
				podVectorResizeUninitialized<float>(
					buffer, spec.nchannels * regionRect.size().x * regionRect.size().y
				);

				// Tell OIIO to do the actual read/decompress to the temp buffer
				if( !m_imageInput->read_scanlines(
					tileBatchOrigin.z, 0,
					regionRect.min.y, regionRect.max.y, 0, 0, spec.nchannels, TypeDesc::FLOAT, &buffer[0]
				) )
				{
					handleOIIOError( "Failed to read scanlines", gafferRegionRect );
				}

				// Copy the data from the temp buffer to whatever tiles it belongs in
				blitOIIORectToTileBatch(
					spec.nchannels, &buffer[0], gafferRegionRect,
					tileBatchSize, tileBatchOrigin, tileChannelPointers,
					tileDataWindows
				);
			}
			else
			{
				// For deep, we unfortunately don't currently have a way to tell OIIO to read
				// just the sample counts, so this read will pull in all the data, and we need
				// to remember it for later.
				if( !m_imageInput->read_native_deep_scanlines(
					tileBatchOrigin.z, 0,
					regionRect.min.y, regionRect.max.y, 0, 0, spec.nchannels, *deepRectData
				) )
				{
					handleOIIOError( "Failed to read deep scanlines", gafferRegionRect );
				}

				// Remember the region covered by this data so we can put it in the right place
				// later
				*deepRect = gafferRegionRect;

				// Set the sample counts from this chunk of data
				blitOIIOSampleCountsToTileBatch(
					*deepRectData, gafferRegionRect,
					tileBatchSize, tileBatchOrigin, tileOffsetPointers
				);
			}
		}

		void processFileRegionTiled(
			const ImageSpec &spec, const V3i &tileBatchOrigin, const Box2i &regionRect, std::vector<float> &buffer,
			const V2i &tileBatchSize, std::vector< float* > &tileChannelPointers,
			const std::vector< Box2i > &tileDataWindows,
			OIIO::DeepData *deepRectData, Box2i *deepRect, std::vector< int* > &tileOffsetPointers
		)
		{
			Box2i gafferRegionRect = flopDisplayWindow( regionRect, spec );

			if( !spec.deep )
			{
				podVectorResizeUninitialized<float>(
					buffer, spec.nchannels * regionRect.size().x * regionRect.size().y
				);

				// Tell OIIO to do the actual read/decompress to the temp buffer
				if( ! m_imageInput->read_tiles(
					tileBatchOrigin.z, 0,
					regionRect.min.x, regionRect.max.x, regionRect.min.y, regionRect.max.y,
					0, 1, 0, spec.nchannels, TypeDesc::FLOAT, &buffer[0]
				) )
				{
					handleOIIOError( "Failed to read tiles", gafferRegionRect );
				}

				// Copy the data from the temp buffer to whatever tiles it belongs in
				blitOIIORectToTileBatch(
					spec.nchannels, &buffer[0], gafferRegionRect,
					tileBatchSize, tileBatchOrigin, tileChannelPointers,
					tileDataWindows
				);
			}
			else
			{
				// For deep, we unfortunately don't currently have a way to tell OIIO to read
				// just the sample counts, so this read will pull in all the data, and we need
				// to remember it for later.
				if( !m_imageInput->read_native_deep_tiles (
					tileBatchOrigin.z, 0,
					regionRect.min.x, regionRect.max.x, regionRect.min.y, regionRect.max.y,
					0, 1, 0, spec.nchannels, *deepRectData
				) )
				{
					handleOIIOError( "Failed to read deep tiles", gafferRegionRect );
				}

				// Remember the region covered by this data so we can put it in the right place
				// later
				*deepRect = gafferRegionRect;

				// Set the sample counts from this chunk of data
				blitOIIOSampleCountsToTileBatch(
					*deepRectData, gafferRegionRect,
					tileBatchSize, tileBatchOrigin, tileOffsetPointers
				);
			}
		}

		const ImageSpec &imageSpec( const Context *c ) const
		{
			return lookupView( c ).imageSpec;
		}

		std::string formatName() const
		{
			return m_imageInput->format_name();
		}

		ConstStringVectorDataPtr channelNamesData( const Context *c )
		{
			return lookupView( c ).channelNamesData;
		}

		ConstStringVectorDataPtr viewNamesData()
		{
			return m_viewNamesData;
		}

	private:

		struct View
		{
			View( const ImageSpec &spec, int firstSubImage ) :
				imageSpec( spec ),
				tiled( !( spec.tile_width == 0 && spec.tile_height == 0 ) ),
				tileBatchSize( computeTileBatchSize( spec, tiled ) ),
				channelNamesData( new StringVectorData() ),
				channelNames( channelNamesData->writable() ),
				firstSubImage( firstSubImage )
			{
			}

			ImageSpec imageSpec;
			const bool tiled;
			const Imath::V2i tileBatchSize;
			StringVectorDataPtr channelNamesData;
			std::vector< std::string > &channelNames;
			std::map<std::string, ChannelMapEntry> channelMap;
			int firstSubImage;

		private:

			static V2i computeTileBatchSize( const ImageSpec &spec, bool tiled )
			{
				if( !tiled )
				{
					// Set up a tile batch that is one tile high, and wide enough to hold everything
					// from the beginning of a scanline to the end
					return V2i( 0, 1 ) +
						ImagePlug::tileIndex( V2i( spec.x + spec.width + ImagePlug::tileSize() - 1, 0 ) ) -
						ImagePlug::tileIndex( V2i( spec.x, 0 ) );
				}

				// Our tiling will usually not line up exactly with the file format's tiling - especially because
				// our origin is lower left instead of upper left.  This means that there will almost always be
				// OpenImageIO tiles that lie across the edge of a Gaffer tile batch, and get loaded multiple times.
				// In order to amortize this cost, we make the tile batches for tiled source images a fairly large
				// fixed size.
				const int batchTargetSize = std::max( 512, std::max( spec.tile_width, spec.tile_height ) );
				const int batchTileCount = ( batchTargetSize + ImagePlug::tileSize() - 1 ) / ImagePlug::tileSize();
				return Imath::V2i( batchTileCount );
			}
		};

		// Given a subImage index, and a tile origin, return an origin to identify the tile batch
		// where this channel data will be found
		V3i tileBatchOrigin( const View &view, int subImage, V2i tileOrigin ) const
		{
			V2i o;

			if( view.tiled )
			{
				// For tiled images, we find which batch we are in by rounding down by the size of a tile batch
				o = coordinateDivide( ImagePlug::tileIndex( tileOrigin ), view.tileBatchSize ) * view.tileBatchSize * ImagePlug::tileSize();
			}
			else
			{
				// For scanline images, each tile batch is 1 tile high, and the width of the image,
				// so the batch for this tile has the current Y origin, and the X is the tile origin
				// of the left of the image
				o = ImagePlug::tileOrigin( Imath::V2i( view.imageSpec.x, tileOrigin.y ) );
			}

			return V3i( o.x, o.y, subImage );
		}

		// Given a channel index, and a tile origin, return the index within a tile batch where the correct
		// tile will be found.
		int tileBatchSubIndex( const View &view, int channelIndex, V2i tileOffset ) const
		{
			int tilePlaneSize = view.tileBatchSize.x * view.tileBatchSize.y;
			V2i subXY = ImagePlug::tileIndex( tileOffset );
			return channelIndex * tilePlaneSize + subXY.y * view.tileBatchSize.x + subXY.x;
		}

		inline const View &lookupView( const Context *c ) const
		{
			std::string viewName = c->get<std::string>( ImagePlug::viewNameContextName, ImagePlug::defaultViewName );
			try
			{
				return *m_views.at( viewName );
			}
			catch( const std::out_of_range & )
			{
				try
				{
					return *m_views.at( ImagePlug::defaultViewName );
				}
				catch( const std::out_of_range & )
				{
				}
			}

			throw IECore::Exception( "OpenImageIOReader : Error in downstream node - incorrect request for invalid view \"" + viewName + "\"" );
		}

		void handleOIIOError( const std::string &description, const Box2i &bound )
		{
			std::string error;
			if( m_imageInput->has_error() )
			{
				error = m_imageInput->geterror();
			}
			else
			{
				// The OIIO spec implies that an error should be set whenever a call reports failure
				// by returning false ... in practice however, there seem to be plenty of things that
				// are reported as failure without an error set.
				error = "OIIO error not specified";
			}

			throw IECore::Exception(
				fmt::format(
					"OpenImageIOReader : {} : {},{} to {},{}. Error : {}",
					description,
					bound.min.x, bound.min.y,
					bound.max.x, bound.max.y,
					error
				)
			);
		}

		std::unique_ptr<ImageInput> m_imageInput;
		StringVectorDataPtr m_viewNamesData;
		std::map<std::string, std::unique_ptr< View > > m_views;
};

using FilePtr = std::shared_ptr<File>;

// For success, file should be set, and error left null
// For failure, file should be left null, and error should be set
struct CacheEntry
{
	FilePtr file;
	std::shared_ptr<std::string> error;
};


CacheEntry fileCacheGetter( const std::pair< std::string, ImageReader::ChannelInterpretation> &fileNameAndChannelInterpretation, size_t &cost, const IECore::Canceller *canceller )
{
	cost = 1;

	CacheEntry result;

	const std::string &fileName = fileNameAndChannelInterpretation.first;

	std::unique_ptr<ImageInput> imageInput( ImageInput::create( fileName ) );
	if( !imageInput )
	{
		result.error.reset( new std::string( "OpenImageIOReader : Could not create ImageInput : " + OIIO::geterror() ) );
		return result;
	}

	ImageSpec firstPartSpec;
	if( !imageInput->open( fileName, firstPartSpec ) )
	{
		result.error.reset( new std::string( "OpenImageIOReader : Could not open ImageInput : " + imageInput->geterror() ) );
		return result;
	}

	result.file.reset( new File( std::move( imageInput ), fileName, fileNameAndChannelInterpretation.second ) );

	return result;
}

using FileHandleCache = IECorePreview::LRUCache< std::pair< std::string, ImageReader::ChannelInterpretation >, CacheEntry>;

FileHandleCache *fileCache()
{
	static FileHandleCache *c = new FileHandleCache( fileCacheGetter, 200 );
	return c;
}

boost::container::flat_set<ustring> g_metadataBlacklist = {
	// These two attributes are used by OIIO/EXR to specify the names of
	// subimages. We don't want to load them because :
	//
	// - We already account for them when generating `channelNames`, so the same
	//   information is available elsewhere.
	// - We can only have one metadata item called `name` or
	//   `oiio:subimagename`, which is ambiguous when there are multiple
	//   subimages.
	// - They will quickly get out of sync as channels are added/removed/renamed
	//   in Gaffer.
	// - The OIIO ImageOutput classes react to them, causing ImageWriter to
	//   write out channels with the wrong name.
	ustring( "name" ),
	ustring( "oiio:subimagename" ),
	// This attribute is used by OIIO to say how many subimages there are. This
	// isn't very meaningful in Gaffer where we deal in layers and channel
	// names.
	ustring( "oiio:subimages" ),
	// We handle the view metadata by loading as multi-view images, so we don't
	// need to load it as metadata
	ustring( "view" ),
	ustring( "multiView" )
};

} // namespace

//////////////////////////////////////////////////////////////////////////
// OpenImageIOReader implementation
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( OpenImageIOReader );

size_t OpenImageIOReader::g_firstPlugIndex = 0;

OpenImageIOReader::OpenImageIOReader( const std::string &name )
	:	ImageNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild(
		new StringPlug(
			"fileName", Plug::In, "",
			/* flags */ Plug::Default,
			/* substitutions */ IECore::StringAlgo::AllSubstitutions & ~IECore::StringAlgo::FrameSubstitutions
		)
	);
	addChild( new IntPlug( "refreshCount" ) );
	addChild( new IntPlug( "missingFrameMode", Plug::In, Error, /* min */ Error, /* max */ Hold ) );
	addChild( new IntVectorDataPlug( "availableFrames", Plug::Out, new IntVectorData ) );
	addChild( new BoolPlug( "fileValid", Plug::Out ) );
	addChild( new IntPlug( "channelInterpretation", Plug::In, (int)ImageReader::ChannelInterpretation::Default, /* min */ (int)ImageReader::ChannelInterpretation::Legacy, /* max */ (int)ImageReader::ChannelInterpretation::Specification ) );
	addChild( new ObjectVectorPlug( "__tileBatch", Plug::Out, new ObjectVector ) );

	plugSetSignal().connect( boost::bind( &OpenImageIOReader::plugSet, this, ::_1 ) );
}

OpenImageIOReader::~OpenImageIOReader()
{
}

Gaffer::StringPlug *OpenImageIOReader::fileNamePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *OpenImageIOReader::fileNamePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::IntPlug *OpenImageIOReader::refreshCountPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::IntPlug *OpenImageIOReader::refreshCountPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

Gaffer::IntPlug *OpenImageIOReader::missingFrameModePlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::IntPlug *OpenImageIOReader::missingFrameModePlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 2 );
}

Gaffer::IntVectorDataPlug *OpenImageIOReader::availableFramesPlug()
{
	return getChild<IntVectorDataPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::IntVectorDataPlug *OpenImageIOReader::availableFramesPlug() const
{
	return getChild<IntVectorDataPlug>( g_firstPlugIndex + 3 );
}

Gaffer::BoolPlug *OpenImageIOReader::fileValidPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::BoolPlug *OpenImageIOReader::fileValidPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 4 );
}

Gaffer::IntPlug *OpenImageIOReader::channelInterpretationPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 5 );
}

const Gaffer::IntPlug *OpenImageIOReader::channelInterpretationPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 5 );
}

Gaffer::ObjectVectorPlug *OpenImageIOReader::tileBatchPlug()
{
	return getChild<ObjectVectorPlug>( g_firstPlugIndex + 6 );
}

const Gaffer::ObjectVectorPlug *OpenImageIOReader::tileBatchPlug() const
{
	return getChild<ObjectVectorPlug>( g_firstPlugIndex + 6 );
}

void OpenImageIOReader::setOpenFilesLimit( size_t maxOpenFiles )
{
	fileCache()->setMaxCost( maxOpenFiles );
}

size_t OpenImageIOReader::getOpenFilesLimit()
{
	return fileCache()->getMaxCost();
}

size_t OpenImageIOReader::supportedExtensions( std::vector<std::string> &extensions )
{
	std::string attr;
	if( !getattribute( "extension_list", attr ) )
	{
		return extensions.size();
	}

	using Tokenizer = boost::tokenizer<boost::char_separator<char> >;
	Tokenizer formats( attr, boost::char_separator<char>( ";" ) );
	for( Tokenizer::const_iterator fIt = formats.begin(), eFIt = formats.end(); fIt != eFIt; ++fIt )
	{
		size_t colonPos = fIt->find( ':' );
		if( colonPos != string::npos )
		{
			std::string formatExtensions = fIt->substr( colonPos + 1 );
			Tokenizer extTok( formatExtensions, boost::char_separator<char>( "," ) );
			std::copy( extTok.begin(), extTok.end(), std::back_inserter( extensions ) );
		}
	}

	return extensions.size();
}

void OpenImageIOReader::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ImageNode::affects( input, outputs );

	if( input == fileNamePlug() || input == refreshCountPlug() )
	{
		outputs.push_back( availableFramesPlug() );
	}

	if( input == fileNamePlug() || input == refreshCountPlug() || input == channelInterpretationPlug() )
	{
		outputs.push_back( fileValidPlug() );
	}

	if( input == fileNamePlug() || input == refreshCountPlug() || input == missingFrameModePlug() || input == channelInterpretationPlug() )
	{
		outputs.push_back( tileBatchPlug() );
		for( ValuePlug::Iterator it( outPlug() ); !it.done(); ++it )
		{
			outputs.push_back( it->get() );
		}
	}

	if( input == fileValidPlug() )
	{
		outputs.push_back( outPlug()->metadataPlug() );
	}
}

void OpenImageIOReader::hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const
{
	ImageNode::hash( output, context, h );

	if ( output == fileValidPlug() )
	{
		refreshCountPlug()->hash( h );
		channelInterpretationPlug()->hash( h );
		hashFileName( context, h );
	}
	else if( output == availableFramesPlug() )
	{
		fileNamePlug()->hash( h );
		refreshCountPlug()->hash( h );
	}
	else if( output == tileBatchPlug() )
	{
		h.append( context->get<V3i>( g_tileBatchOriginContextName ) );
		h.append( context->get<std::string>( ImagePlug::viewNameContextName, ImagePlug::defaultViewName ) );

		Gaffer::Context::EditableScope c( context );
		c.remove( g_tileBatchOriginContextName );

		hashFileName( c.context(), h );
		refreshCountPlug()->hash( h );
		missingFrameModePlug()->hash( h );
		channelInterpretationPlug()->hash( h );
	}
}

void OpenImageIOReader::compute( ValuePlug *output, const Context *context ) const
{
	if ( output == fileValidPlug() )
	{
		std::string fileName = fileNamePlug()->getValue();
		if( fileName.empty() )
		{
			static_cast<BoolPlug *>( output )->setValue( false );
			return;
		}

		ImageReader::ChannelInterpretation channelNaming = (ImageReader::ChannelInterpretation)channelInterpretationPlug()->getValue();

		const std::string resolvedFileName = context->substitute( fileName );

		FileHandleCache *cache = fileCache();
		CacheEntry cacheEntry = cache->get( std::make_pair( resolvedFileName, channelNaming ) );

		static_cast<BoolPlug *>( output )->setValue( bool( cacheEntry.file ) );
	}
	else if( output == availableFramesPlug() )
	{
		FileSequencePtr fileSequence = nullptr;
		// In case the image sequence is simply missing, the availableFrames should be set to 0
		// that allows, in practice, tool building on the ImageReader to gracefully handle that case
		// when running template workflows.
		try
		{
			IECore::ls( fileNamePlug()->getValue(), fileSequence, /* minSequenceSize */ 1 );
		}
		catch( const std::exception & )
		{
			// Fall through to `setToDefault()`.
		}

		if( fileSequence )
		{
			IntVectorDataPtr resultData = new IntVectorData;
			std::vector<FrameList::Frame> frames;
			fileSequence->getFrameList()->asList( frames );
			std::vector<int> &result = resultData->writable();
			result.resize( frames.size() );
			std::copy( frames.begin(), frames.end(), result.begin() );
			static_cast<IntVectorDataPlug *>( output )->setValue( resultData );
		}
		else
		{
			static_cast<IntVectorDataPlug *>( output )->setToDefault();
		}
	}
	else if( output == tileBatchPlug() )
	{
		V3i tileBatchOrigin = context->get<V3i>( g_tileBatchOriginContextName );

		Gaffer::Context::EditableScope c( context );
		c.remove( g_tileBatchOriginContextName );

		FilePtr file = std::static_pointer_cast<File>( retrieveFile( c.context() ) );

		if( !file )
		{
			throw IECore::Exception( "OpenImageIOReader - trying to evaluate tileBatchPlug() with invalid file, this should never happen." );
		}

		static_cast<ObjectVectorPlug *>( output )->setValue(
			file->readTileBatch( context, tileBatchOrigin )
		);
	}
	else
	{
		ImageNode::compute( output, context );
	}
}

Gaffer::ValuePlug::CachePolicy OpenImageIOReader::computeCachePolicy( const Gaffer::ValuePlug *output ) const
{
	if( output == tileBatchPlug() )
	{
		// For our most common case, reading Exrs using ExrCore, we are able to have multiple threads join
		// and help with reading ( the actual file reads probably don't benefit too much from multithreading,
		// but decompression benefits a lot )
		return ValuePlug::CachePolicy::TaskCollaboration;
	}
	else if( output == outPlug()->channelDataPlug() )
	{
		// Disable caching on channelDataPlug, since it is just a redirect to the correct tile of
		// the private tileBatchPlug, which is already being cached.
		return ValuePlug::CachePolicy::Uncached;
	}
	return ImageNode::computeCachePolicy( output );
}

void OpenImageIOReader::hashFileName( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	// since fileName excludes frame substitutions
	// but we internally vary the result output by
	// frame, we need to explicitly hash the frame
	// when the value contains FrameSubstitutions.
	const std::string fileName = fileNamePlug()->getValue();
	h.append( fileName );
	if( IECore::StringAlgo::substitutions( fileName ) & IECore::StringAlgo::FrameSubstitutions )
	{
		h.append( context->getFrame() );
	}
}

void OpenImageIOReader::hashViewNames( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageNode::hashViewNames( parent, context, h );
	hashFileName( context, h );
	refreshCountPlug()->hash( h );
	missingFrameModePlug()->hash( h );
	channelInterpretationPlug()->hash( h );  // Affects whether "main" is interpreted as "default"
}

IECore::ConstStringVectorDataPtr OpenImageIOReader::computeViewNames( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	FilePtr file = std::static_pointer_cast<File>( retrieveFile( context ) );
	if( !file )
	{
		return ImagePlug::defaultViewNames();
	}
	return file->viewNamesData();
}

void OpenImageIOReader::hashFormat( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageNode::hashFormat( output, context, h );
	hashFileName( context, h );
	refreshCountPlug()->hash( h );
	missingFrameModePlug()->hash( h );
	GafferImage::Format format = FormatPlug::getDefaultFormat( context );
	h.append( format.getDisplayWindow() );
	h.append( format.getPixelAspect() );
	h.append( context->get<std::string>( ImagePlug::viewNameContextName, ImagePlug::defaultViewName ) );
}

GafferImage::Format OpenImageIOReader::computeFormat( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	// when we're in MissingFrameMode::Black we still want to
	// match the format of the Hold frame, so pass true for holdForBlack.
	FilePtr file = std::static_pointer_cast<File>( retrieveFile( context, true ) );
	if( !file )
	{
		return FormatPlug::getDefaultFormat( context );
	}

	const ImageSpec &spec = file->imageSpec( context );
	return GafferImage::Format(
		Imath::Box2i(
			Imath::V2i( spec.full_x, spec.full_y ),
			Imath::V2i( spec.full_x + spec.full_width, spec.full_y + spec.full_height )
		),
		spec.get_float_attribute( "PixelAspectRatio", 1.0f )
	);
}

void OpenImageIOReader::hashDataWindow( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageNode::hashDataWindow( output, context, h );
	hashFileName( context, h );
	refreshCountPlug()->hash( h );
	missingFrameModePlug()->hash( h );
	h.append( context->get<std::string>( ImagePlug::viewNameContextName, ImagePlug::defaultViewName ) );
}

Imath::Box2i OpenImageIOReader::computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	FilePtr file = std::static_pointer_cast<File>( retrieveFile( context ) );
	if( !file )
	{
		return parent->dataWindowPlug()->defaultValue();
	}

	const ImageSpec &spec = file->imageSpec( context );

	Imath::Box2i dataWindow( Imath::V2i( spec.x, spec.y ), Imath::V2i( spec.width + spec.x, spec.height + spec.y ) );
	return flopDisplayWindow( dataWindow, spec );
}

void OpenImageIOReader::hashMetadata( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageNode::hashMetadata( output, context, h );
	hashFileName( context, h );
	refreshCountPlug()->hash( h );
	missingFrameModePlug()->hash( h );
	fileValidPlug()->hash( h );
	h.append( context->get<std::string>( ImagePlug::viewNameContextName, ImagePlug::defaultViewName ) );
}

IECore::ConstCompoundDataPtr OpenImageIOReader::computeMetadata( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	CompoundDataPtr result = new CompoundData;

	FilePtr file = std::static_pointer_cast<File>( retrieveFile( context ) );
	if( !file )
	{
		result->writable()["fileValid"] = new BoolData( false );
		return result;
	}
	const ImageSpec &spec = file->imageSpec( context );

	// Add data type

	std::string dataType = spec.format.c_str();
	if( dataType == "uint16")
	{
		// DPX supports uint10/uint12 storage, which is loaded as uint16 by OIIO.
		// Here we use the "oiio:BitsPerSample" metadata that tells us how many
		// bits were actually stored in the file.
		const int bitsPerSample = spec.get_int_attribute( "oiio:BitsPerSample", 0 );
		if( bitsPerSample )
		{
			dataType = fmt::format( "uint{}", bitsPerSample );
		}
	}
	else if( dataType == "uint" )
	{
		dataType = "uint32";
	}
	result->writable()["dataType"] = new StringData( dataType );

	// Add file format
	result->writable()["fileFormat"] = new StringData( file->formatName() );

	// Add on any custom metadata provided by the file format

	for( const auto &attrib : spec.extra_attribs )
	{
		if( g_metadataBlacklist.count( attrib.name() ) )
		{
			continue;
		}
		if( DataPtr data = IECoreImage::OpenImageIOAlgo::data( attrib ) )
		{
			result->writable()[attrib.name().string()] = data;
		}
	}

	// Add `fileValid` metadata.

	if( !fileValidPlug()->getValue() )
	{
		result->writable()["fileValid"] = new BoolData( false );
	}

	return result;
}

void OpenImageIOReader::hashChannelNames( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageNode::hashChannelNames( output, context, h );
	hashFileName( context, h );
	refreshCountPlug()->hash( h );
	missingFrameModePlug()->hash( h );
	channelInterpretationPlug()->hash( h );
	h.append( context->get<std::string>( ImagePlug::viewNameContextName, ImagePlug::defaultViewName ) );
}

IECore::ConstStringVectorDataPtr OpenImageIOReader::computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	FilePtr file = std::static_pointer_cast<File>( retrieveFile( context ) );
	if( !file )
	{
		return parent->channelNamesPlug()->defaultValue();
	}
	return file->channelNamesData( context );
}

void OpenImageIOReader::hashDeep( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageNode::hashDeep( output, context, h );
	hashFileName( context, h );
	refreshCountPlug()->hash( h );
	missingFrameModePlug()->hash( h );
	h.append( context->get<std::string>( ImagePlug::viewNameContextName, ImagePlug::defaultViewName ) );
}

bool OpenImageIOReader::computeDeep( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	FilePtr file = std::static_pointer_cast<File>( retrieveFile( context ) );
	if( !file )
	{
		return false;
	}
	return file->imageSpec( context ).deep;
}

void OpenImageIOReader::hashSampleOffsets( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageNode::hashSampleOffsets( output, context, h );

	h.append( context->get<V2i>( ImagePlug::tileOriginContextName ) );
	h.append( context->get<std::string>( ImagePlug::viewNameContextName, ImagePlug::defaultViewName ) );

	{
		ImagePlug::GlobalScope c( context );
		hashFileName( context, h );
		refreshCountPlug()->hash( h );
		missingFrameModePlug()->hash( h );
		channelInterpretationPlug()->hash( h );
	}
}

IECore::ConstIntVectorDataPtr OpenImageIOReader::computeSampleOffsets( const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	ImagePlug::GlobalScope c( context );
	FilePtr file = std::static_pointer_cast<File>( retrieveFile( context ) );

	if( !file || !file->imageSpec( context ).deep )
	{
		return ImagePlug::flatTileSampleOffsets();
	}
	else
	{

		Box2i dataWindow = outPlug()->dataWindowPlug()->getValue();
		const Box2i tileBound( tileOrigin, tileOrigin + V2i( ImagePlug::tileSize() ) );
		if( !BufferAlgo::intersects( dataWindow, tileBound ) )
		{
			throw IECore::Exception(
				fmt::format(
					"OpenImageIOReader : Invalid tile ({},{}) -> ({},{}) not within data window ({},{}) -> ({},{}).",
					tileBound.min.x, tileBound.min.y, tileBound.max.x, tileBound.max.y,
					dataWindow.min.x, dataWindow.min.y, dataWindow.max.x, dataWindow.max.y
				)
			);
		}

		V3i tileBatchOrigin;
		int subIndex;
		std::string channelName(""); // TODO - should have better interface for selecting sampleOffsets
		file->findTile( context, channelName, tileOrigin, tileBatchOrigin, subIndex );

		c.set( g_tileBatchOriginContextName, &tileBatchOrigin );

		ConstObjectVectorPtr tileBatch = tileBatchPlug()->getValue();

		ConstObjectPtr curTileSampleOffsets = IECore::runTimeCast< const ObjectVector >( tileBatch->members()[1] )->members()[ subIndex ];
		return IECore::runTimeCast< const IntVectorData >( curTileSampleOffsets );
	}
}

void OpenImageIOReader::hashChannelData( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageNode::hashChannelData( output, context, h );
	h.append( context->get<V2i>( ImagePlug::tileOriginContextName ) );
	h.append( context->get<std::string>( ImagePlug::channelNameContextName ) );
	h.append( context->get<std::string>( ImagePlug::viewNameContextName, ImagePlug::defaultViewName ) );

	{
		ImagePlug::GlobalScope c( context );
		hashFileName( context, h );
		refreshCountPlug()->hash( h );
		missingFrameModePlug()->hash( h );
		channelInterpretationPlug()->hash( h );
	}
}

IECore::ConstFloatVectorDataPtr OpenImageIOReader::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	ImagePlug::GlobalScope c( context );
	FilePtr file = std::static_pointer_cast<File>( retrieveFile( context ) );

	if( !file )
	{
		return parent->channelDataPlug()->defaultValue();
	}

	Box2i dataWindow = outPlug()->dataWindowPlug()->getValue();
	const Box2i tileBound( tileOrigin, tileOrigin + V2i( ImagePlug::tileSize() ) );
	if( !BufferAlgo::intersects( dataWindow, tileBound ) )
	{
		throw IECore::Exception(
			fmt::format(
				"OpenImageIOReader : Invalid tile ({},{}) -> ({},{}) not within data window ({},{}) -> ({},{}).",
				tileBound.min.x, tileBound.min.y, tileBound.max.x, tileBound.max.y,
				dataWindow.min.x, dataWindow.min.y, dataWindow.max.x, dataWindow.max.y
			)
		);
	}

	V3i tileBatchOrigin;
	int subIndex;
	file->findTile( context, channelName, tileOrigin, tileBatchOrigin, subIndex );

	c.set( g_tileBatchOriginContextName, &tileBatchOrigin );

	ConstObjectVectorPtr tileBatch = tileBatchPlug()->getValue();
	ConstObjectPtr curTileChannel = IECore::runTimeCast< const ObjectVector >(
			tileBatch->members()[0]
	)->members()[ subIndex ];

	return IECore::runTimeCast< const FloatVectorData >( curTileChannel );
}

void OpenImageIOReader::plugSet( Gaffer::Plug *plug )
{
	// this clears the cache every time the refresh count is updated, so you don't get entries
	// from old files hanging around.
	if( plug == refreshCountPlug() )
	{
		fileCache()->clear();
	}
}

// Returns the file handle container for the current context, by evaluating the appropriate plugs.
// Throws if the file is invalid, and returns null if the filename is empty.
std::shared_ptr<void> OpenImageIOReader::retrieveFile( const Context *context, bool holdForBlack ) const
{
	std::string fileName = fileNamePlug()->getValue();
	if( fileName.empty() )
	{
		return nullptr;
	}

	MissingFrameMode mode = (MissingFrameMode)missingFrameModePlug()->getValue();
	if( holdForBlack && mode == Black )
	{
		// For some outputs, like "format", we need to hold the value of an adjacent frame when we're
		// going to return black pixels
		mode = Hold;
	}
	ImageReader::ChannelInterpretation channelNaming = (ImageReader::ChannelInterpretation)channelInterpretationPlug()->getValue();

	const std::string resolvedFileName = context->substitute( fileName );

	FileHandleCache *cache = fileCache();
	CacheEntry cacheEntry = cache->get( std::make_pair( resolvedFileName, channelNaming ) );
	if( !cacheEntry.file )
	{
		if( mode == OpenImageIOReader::Black )
		{
			// we can simply return nullptr and rely on the
			// compute methods to return default plug values.
			return nullptr;
		}
		else if( mode == OpenImageIOReader::Hold )
		{
			ConstIntVectorDataPtr frameData = availableFramesPlug()->getValue();
			const std::vector<int> &frames = frameData->readable();
			if( frames.size() )
			{
				std::vector<int>::const_iterator fIt = std::lower_bound( frames.begin(), frames.end(), (int)context->getFrame() );

				// decrement to get the previous frame, unless
				// this is the first frame, in which case we
				// hold to the beginning of the sequence
				if( fIt != frames.begin() )
				{
					fIt--;
				}

				// setup a context with the new frame
				Context::EditableScope holdScope( context );
				holdScope.setFrame( *fIt );

				const std::string resolvedFileNameHeld = holdScope.context()->substitute( fileName );
				cacheEntry = cache->get( std::make_pair( resolvedFileNameHeld, channelNaming ) );
			}

			// if we got here, there was no suitable file sequence, or we weren't able to open the held frame
			if( !cacheEntry.file )
			{
				throw IECore::Exception( *(cacheEntry.error) );
			}
		}
		else
		{
			throw IECore::Exception( *(cacheEntry.error) );
		}
	}

	return cacheEntry.file;
}
