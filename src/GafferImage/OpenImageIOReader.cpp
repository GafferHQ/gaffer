//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
//  Copyright (c) 2012-2015, Image Engine Design Inc. All rights reserved.
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

#include "Gaffer/Context.h"
#include "Gaffer/StringPlug.h"

#include "IECoreImage/OpenImageIOAlgo.h"

#include "IECore/Export.h"
#include "IECore/FileSequence.h"
#include "IECore/FileSequenceFunctions.h"
#include "IECore/MessageHandler.h"

#include "OpenImageIO/imagecache.h"

#include "boost/bind.hpp"
#include "boost/filesystem/path.hpp"
#include "boost/regex.hpp"

#include "tbb/mutex.h"

#include <memory>

OIIO_NAMESPACE_USING

using namespace std;
using namespace tbb;
using namespace Imath;
using namespace IECore;
using namespace GafferImage;
using namespace Gaffer;

namespace
{

const IECore::InternedString g_tileBatchIndexContextName( "__tileBatchIndex" );

struct ChannelMapEntry
{
	ChannelMapEntry( int subImage, int channelIndex )
		: subImage( subImage ), channelIndex( channelIndex )
	{}

	ChannelMapEntry( const ChannelMapEntry & ) = default;

	ChannelMapEntry()
		: subImage( 0 ), channelIndex( 0 )
	{}

	int subImage;
	int channelIndex;
};

// This function transforms an input region to account for the display window being flipped.
// This is similar to Format::fromEXRSpace/toEXRSpace but those functions mix in switching
// between inclusive/exclusive bounds, so in order to use them we would have to add a bunch
// of confusing offsets by 1.  In this class, we always interpret ranges as [ minPixel, onePastMaxPixel )
Box2i flopDisplayWindow( Box2i b, int displayOriginY, int displayHeight )
{
	return Box2i(
		V2i( b.min.x, displayOriginY + displayOriginY + displayHeight - b.max.y ),
		V2i( b.max.x, displayOriginY + displayOriginY + displayHeight - b.min.y )
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
// correct tile batch index, access tileBatchPlug, and then return the tile at the correct tileBatchSubIndex.
//
// For scanline images, a tile batch is one tile high, and the full width of the image.
// For tiled images, a tile batch is a fairly large fixed size ( current 512 pixels, or the tile size of the
// image, whichever is larger ).  This amortizes the waste from tiles which lie over the edge of a tile batch,
// and need to be read multiple times.
// Either way, a tile batch contains all channels stored in the subimage which contains the desired channel.
//
// Tile batches are selected using V3i "tileBatchIndex".  The Z component is the subimage to load channels from.
// The X and Y component select a region of the image.
// For tiled images, the <0,0> tileBatch is at the origin of the image, and the X and Y components specify
// how many tile batches to offset from that, horizontally and vertically.
// For scanline images, Y works the same, but X is always 0, and the tile batch always covers the whole width
// of the image horizontally ( this means that the left of the tileBatch is aligned to the data window, not
// the origin ).
//
//
class File
{

	public:

		// Create a File handle object for an image input and image spec
		File( std::unique_ptr<ImageInput> imageInput, ImageSpec imageSpec, const std::string &infoFileName )
			: m_imageInput( std::move( imageInput ) ), m_imageSpec( imageSpec )
		{
			std::vector<std::string> channelNames;

			// \todo - for stereo images, we would need to take note of which view a subimage is for,
			// and drive loading based on that.  This might require reorganizing this structure where
			// we store m_imageSpec together with m_imageInput, since a stero image would have one
			// m_imageInput, but could need two separate image specs ( different data windows for the two eyes seem
			// reasonable )
			ImageSpec currentSpec = m_imageSpec;
			int subImageIndex = 0;
			do {
				if( !(
					currentSpec.x == m_imageSpec.x &&
					currentSpec.y == m_imageSpec.y &&
					currentSpec.z == m_imageSpec.z &&
					currentSpec.width == m_imageSpec.width &&
					currentSpec.height == m_imageSpec.height &&
					currentSpec.depth == m_imageSpec.depth &&
					currentSpec.tile_width == m_imageSpec.tile_width &&
					currentSpec.tile_height == m_imageSpec.tile_height &&
					currentSpec.tile_depth == m_imageSpec.tile_depth
				) )
				{
					IECore::msg( IECore::Msg::Warning, "OpenImageIOReader",
						boost::format( "Ignoring subimage %i of \"%s\" because spec does not match first subimage." )
						% subImageIndex % infoFileName
					);
					subImageIndex++;
					continue;
				}

				const OIIO::string_view subImageName = currentSpec.get_string_attribute( "name", "" );

				for( const auto &n : currentSpec.channelnames )
				{
					std::string channelName = ImageAlgo::channelName( subImageName, n );
					auto mapEntry = m_channelMap.find( channelName );
					if( mapEntry != m_channelMap.end() )
					{
						IECore::msg( IECore::Msg::Warning, "OpenImageIOReader",
							boost::format( "Ignoring channel \"%s\" in subimage \"%i\" of \"%s\" because it's already in subimage \"%i\"." )
							% channelName % subImageIndex % infoFileName % mapEntry->second.subImage
						);
					}
					else
					{
						m_channelMap[ channelName ] = ChannelMapEntry( subImageIndex, &n - &currentSpec.channelnames[0] );
						channelNames.push_back( channelName );
					}
				}
				subImageIndex++;
			} while( m_imageInput->seek_subimage( subImageIndex, 0, currentSpec ) );

			m_channelNamesData = new StringVectorData( channelNames );

			if( m_imageSpec.tile_width == 0 && m_imageSpec.tile_height == 0 )
			{
				m_tiled = false;

				// Set up a tile batch that is one tile high, and wide enough to hold everything from the beginning
				// of a scanline to the end
				m_tileBatchSize = V2i( 0, 1 ) +
					ImagePlug::tileIndex( V2i( m_imageSpec.x + m_imageSpec.width + ImagePlug::tileSize() - 1, 0 ) ) -
					ImagePlug::tileIndex( V2i( m_imageSpec.x, 0 ) );
			}
			else
			{
				m_tiled = true;

				// Our tiling will usually not line up exactly with the file format's tiling - especially because
				// our origin is lower left instead of upper left.  This means that there will almost always be
				// OpenImageIO tiles that lie across the edge of a Gaffer tile batch, and get loaded multiple times.
				// In order to amortize this cost, we make the tile batches for tiled source images a fairly large
				// fixed size.
				const int batchTargetSize = std::max( 512, std::max( m_imageSpec.tile_width, m_imageSpec.tile_height ) );
				const int batchTileCount = ( batchTargetSize + ImagePlug::tileSize() - 1 ) / ImagePlug::tileSize();
				m_tileBatchSize = Imath::V2i( batchTileCount );
			}
		}

		// Read a chunk of data from the file, formatted as a tile batch that will be stored on the tile batch plug
		ConstObjectVectorPtr readTileBatch( V3i tileBatchIndex )
		{
			V2i batchFirstTile = V2i( tileBatchIndex.x, tileBatchIndex.y ) * m_tileBatchSize;
			Box2i targetRegion = Box2i( batchFirstTile * ImagePlug::tileSize(),
				( batchFirstTile + m_tileBatchSize ) * ImagePlug::tileSize()
			);

			if( !m_tiled )
			{
				// For scanline images, we always treat the tile batch as starting from the left of the data window
				batchFirstTile.x = ImagePlug::tileIndex( V2i( m_imageSpec.x, 0 ) ).x;

				targetRegion.min.x = m_imageSpec.x;
				targetRegion.max.x = m_imageSpec.x + m_imageSpec.width;
			}

			// Do the actual read of data
			std::vector<float> fileData;
			Box2i fileDataRegion;
			const int nchannels = readRegion( tileBatchIndex.z, targetRegion, fileData, fileDataRegion );

			// Pull data apart into tiles ( separate for each channel instead of interleaved )
			int tileBatchNumElements = nchannels * m_tileBatchSize.y * m_tileBatchSize.x;
			ObjectVectorPtr result = new ObjectVector();
			result->members().resize( tileBatchNumElements );

			for( int c = 0; c < nchannels; c++ )
			{
				for( int ty = batchFirstTile.y; ty < batchFirstTile.y + m_tileBatchSize.y; ty++ )
				{
					for( int tx = batchFirstTile.x; tx < batchFirstTile.x + m_tileBatchSize.x; tx++ )
					{
						V2i tileOffset = ImagePlug::tileSize() * V2i( tx, ty );
						Box2i tileRelativeFileRegion( fileDataRegion.min - tileOffset, fileDataRegion.max - tileOffset );
						Box2i tileRegion = BufferAlgo::intersection(
							Box2i( V2i( 0 ), V2i( ImagePlug::tileSize() ) ), tileRelativeFileRegion
						);

						if( BufferAlgo::empty( tileRegion ) )
						{
							// Result will be treated as const as soon as we set it on the plug, and we're not
							// going to modify any elements after setting them, so it's safe to store a const
							// value in one of the elements
							result->members()[ tileBatchSubIndex( c, tileOffset ) ] =
								const_cast<FloatVectorData*>( ImagePlug::blackTile() );
							continue;
						}

						FloatVectorDataPtr tileData = new IECore::FloatVectorData(
							std::vector<float>( ImagePlug::tileSize()*ImagePlug::tileSize() )
						);
						vector<float> &tile = tileData->writable();

						for( int y = tileRegion.min.y; y < tileRegion.max.y; ++y )
						{

							float *tileIndex = &tile[ y * ImagePlug::tileSize() + tileRegion.min.x ];
							int scanline = fileDataRegion.size().y - 1 - (y - tileRelativeFileRegion.min.y);
							float *dataIndex = &fileData[
								( scanline * fileDataRegion.size().x + tileRegion.min.x - tileRelativeFileRegion.min.x
								) * nchannels + c
							];
							for( int x = tileRegion.min.x; x < tileRegion.max.x; x++ )
							{
								*tileIndex = *dataIndex;
								tileIndex++;
								dataIndex += nchannels;
							}
						}


						result->members()[ tileBatchSubIndex( c, tileOffset ) ] = tileData;
					}
				}
			}

			return result;
		}

		// Given a channelName and tileOrigin, return the information necessary to look up the data for this tile.
		// The tileBatchIndex is used to find a tileBatch, and then the tileBatchSubIndex tells you the index
		// within that tile to use
		void findTile( const std::string &channelName, const Imath::V2i &tileOrigin, V3i &batchIndex, int &batchSubIndex ) const
		{
			ChannelMapEntry channelMapEntry = m_channelMap.at( channelName );
			batchIndex = tileBatchIndex( channelMapEntry.subImage, tileOrigin );
			batchSubIndex = tileBatchSubIndex( channelMapEntry.channelIndex, tileOrigin );
		}

		const ImageSpec &imageSpec() const
		{
			return m_imageSpec;
		}

		std::string formatName() const
		{
			return m_imageInput->format_name();
		}

		ConstStringVectorDataPtr channelNamesData()
		{
			return m_channelNamesData;
		}

	private:

		// Fill the data array with all data for the specified subImage and target region,
		// setting the dataRegion to represent the actual bounds of the data read ( which may have had to
		// be enlarged to match tile boundaries ), and returning the number of channels read.
		int readRegion( int subImage, const Box2i &targetRegion, std::vector<float> &data, Box2i &dataRegion )
		{
			/// \todo OIIO 2.0 introduces thread-safe `read_*()` methods that
			/// are passed the subimage directly. Upgrade to use those and remove
			/// this lock entirely.
			tbb::mutex::scoped_lock lock( m_mutex );

			ImageSpec subImageSpec;
			m_imageInput->seek_subimage( subImage, 0, subImageSpec );

			const V2i fileDataOrigin( m_imageSpec.x, m_imageSpec.y );
			const Box2i fileDataWindow( fileDataOrigin,
				fileDataOrigin + V2i( m_imageSpec.width, m_imageSpec.height )
			);

			// Convert target region in Gaffer into a region of the file that we are trying to read
			const Box2i fileTargetRegion = BufferAlgo::intersection(
				flopDisplayWindow( targetRegion, m_imageSpec.full_y, m_imageSpec.full_height ), fileDataWindow
			);

			Box2i fileDataRegion;

			if( !m_tiled )
			{
				fileDataRegion = fileTargetRegion;

				data.resize( subImageSpec.nchannels * fileDataRegion.size().x * fileDataRegion.size().y );

				if( !m_imageInput->read_scanlines( fileDataRegion.min.y, fileDataRegion.max.y, 0, TypeDesc::FLOAT, &data[0] ) )
				{
					throw IECore::Exception( boost::str (
						boost::format( "OpenImageIOReader : Failed to read scanlines %i to %i.  Error: %s" ) %
						fileDataRegion.min.y % fileDataRegion.max.y %
						m_imageInput->geterror()
					) );
				}
			}
			else
			{
				V2i tileSize( m_imageSpec.tile_width, m_imageSpec.tile_height );

				// Round the target region coordinates outwards to the tile boundaries in the file
				// ( these are sized based on m_imageSpec.tile_(width/height), and spaced relative to
				// the data window origin ).
				//
				// Then clamp them back to the data window.
				// ( read_tiles requires that the coordinates lie on either a tile boundary OR the image boundary )

				fileDataRegion = BufferAlgo::intersection( fileDataWindow, Box2i(
					coordinateDivide( fileTargetRegion.min - fileDataOrigin, tileSize ) * tileSize + fileDataOrigin,
					coordinateDivide( fileTargetRegion.max - fileDataOrigin + tileSize - V2i(1), tileSize ) * tileSize + fileDataOrigin
				) );

				data.resize( subImageSpec.nchannels * fileDataRegion.size().x * fileDataRegion.size().y );

				if( !m_imageInput->read_tiles (
					fileDataRegion.min.x, fileDataRegion.max.x,
					fileDataRegion.min.y, fileDataRegion.max.y, 0, 1, TypeDesc::FLOAT, &data[0]
				) )
				{
					throw IECore::Exception( boost::str (
						boost::format( "OpenImageIOReader : Failed to read tiles %i,%i to %i,%i.  Error: %s" ) %
						fileDataRegion.min.x % fileDataRegion.min.y %
						fileDataRegion.max.x % fileDataRegion.max.y %
						m_imageInput->geterror()
					) );
				}
			}

			dataRegion = flopDisplayWindow( fileDataRegion, m_imageSpec.full_y, m_imageSpec.full_height );

			return subImageSpec.nchannels;
		}

		// Given a subImage index, and a tile origin, return an index to identify the tile batch which
		// where this channel data will be found
		V3i tileBatchIndex( int subImage, V2i tileOrigin ) const
		{
			V2i tileBatchOrigin = coordinateDivide( ImagePlug::tileIndex( tileOrigin ), m_tileBatchSize );
			if( !m_tiled )
			{
				tileBatchOrigin.x = 0;
			}
			return V3i( tileBatchOrigin.x, tileBatchOrigin.y, subImage );
		}

		// Given a channel index, and a tile origin, return the index within a tile batch where the correct
		// tile will be found.
		int tileBatchSubIndex( int channelIndex, V2i tileOrigin ) const
		{
			int tilePlaneSize = m_tileBatchSize.x * m_tileBatchSize.y;

			V2i tileIndex = ImagePlug::tileIndex( tileOrigin );
			V2i subIndex = tileIndex - coordinateDivide( tileIndex, m_tileBatchSize ) * m_tileBatchSize;
			if( !m_tiled )
			{
				// For scanline images, horizontal index relative to data window
				subIndex.x = tileIndex.x - ImagePlug::tileIndex( V2i( m_imageSpec.x, m_imageSpec.y ) ).x;
			}

			return channelIndex * tilePlaneSize + subIndex.y * m_tileBatchSize.x + subIndex.x;
		}

		std::unique_ptr<ImageInput> m_imageInput;
		ImageSpec m_imageSpec;
		ConstStringVectorDataPtr m_channelNamesData;
		std::map<std::string, ChannelMapEntry> m_channelMap;
		Imath::V2i m_tileBatchSize;
		tbb::mutex m_mutex;
		bool m_tiled;
};



typedef std::shared_ptr<File> FilePtr;

// For success, file should be set, and error left null
// For failure, file should be left null, and error should be set
struct CacheEntry
{
	FilePtr file;
	std::shared_ptr<std::string> error;
};


CacheEntry fileCacheGetter( const std::string &fileName, size_t &cost )
{
	cost = 1;

	CacheEntry result;

	ImageSpec imageSpec;
	std::unique_ptr<ImageInput> imageInput( ImageInput::create( fileName ) );
	if( !imageInput )
	{
		result.error.reset( new std::string( "OpenImageIOReader : Could not create ImageInput : " + OIIO::geterror() ) );
		return result;
	}

	if( !imageInput->open( fileName, imageSpec ) )
	{
		result.error.reset( new std::string( "OpenImageIOReader : Could not open ImageInput : " + imageInput->geterror() ) );
		return result;
	}

	if( imageSpec.depth != 1 )
	{
		throw IECore::Exception( "OpenImageIOReader : " + fileName + " : GafferImage does not support 3D pixel arrays " );
	}

	result.file.reset( new File( std::move( imageInput ), imageSpec, fileName ) );

	return result;
}

typedef IECorePreview::LRUCache<std::string, CacheEntry> FileHandleCache;

FileHandleCache *fileCache()
{
	static FileHandleCache *c = new FileHandleCache( fileCacheGetter, 200 );
	return c;
}

// Returns the file handle container for the given filename in the current
// context. Throws if the file is invalid, and returns null if
// the filename is empty.
FilePtr retrieveFile( std::string &fileName, OpenImageIOReader::MissingFrameMode mode, const OpenImageIOReader *node, const Context *context )
{
	if( fileName.empty() )
	{
		return nullptr;
	}

	const std::string resolvedFileName = context->substitute( fileName );

	FileHandleCache *cache = fileCache();
	CacheEntry cacheEntry = cache->get( resolvedFileName );
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
			ConstIntVectorDataPtr frameData = node->availableFramesPlug()->getValue();
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
				ContextPtr holdContext = new Context( *context, Context::Shared );
				holdContext->setFrame( *fIt );

				return retrieveFile( fileName, OpenImageIOReader::Error, node, holdContext.get() );
			}

			// if we got here, there was no suitable file sequence
			throw IECore::Exception( *(cacheEntry.error) );
		}
		else
		{
			throw IECore::Exception( *(cacheEntry.error) );
		}
	}

	return cacheEntry.file;
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// OpenImageIOReader implementation
//////////////////////////////////////////////////////////////////////////

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( OpenImageIOReader );

size_t OpenImageIOReader::g_firstPlugIndex = 0;

OpenImageIOReader::OpenImageIOReader( const std::string &name )
	:	ImageNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild(
		new StringPlug(
			"fileName", Plug::In, "",
			/* flags */ Plug::Default,
			/* substitutions */ Context::AllSubstitutions & ~Context::FrameSubstitutions
		)
	);
	addChild( new IntPlug( "refreshCount" ) );
	addChild( new IntPlug( "missingFrameMode", Plug::In, Error, /* min */ Error, /* max */ Hold ) );
	addChild( new IntVectorDataPlug( "availableFrames", Plug::Out, new IntVectorData ) );
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

Gaffer::ObjectVectorPlug *OpenImageIOReader::tileBatchPlug()
{
	return getChild<ObjectVectorPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::ObjectVectorPlug *OpenImageIOReader::tileBatchPlug() const
{
	return getChild<ObjectVectorPlug>( g_firstPlugIndex + 4 );
}

size_t OpenImageIOReader::supportedExtensions( std::vector<std::string> &extensions )
{
	std::string attr;
	if( !getattribute( "extension_list", attr ) )
	{
		return extensions.size();
	}

	typedef boost::tokenizer<boost::char_separator<char> > Tokenizer;
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

	if( input == fileNamePlug() || input == refreshCountPlug() || input == missingFrameModePlug() )
	{
		for( ValuePlugIterator it( outPlug() ); !it.done(); ++it )
		{
			outputs.push_back( it->get() );
		}
	}
}

void OpenImageIOReader::hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const
{
	ImageNode::hash( output, context, h );

	if( output == availableFramesPlug() )
	{
		fileNamePlug()->hash( h );
		refreshCountPlug()->hash( h );
	}
	else if( output == tileBatchPlug() )
	{
		h.append( context->get<V3i>( g_tileBatchIndexContextName ) );
		{
			ImagePlug::GlobalScope c( context );
			hashFileName( context, h );
			refreshCountPlug()->hash( h );
			missingFrameModePlug()->hash( h );
		}
	}
}

void OpenImageIOReader::compute( ValuePlug *output, const Context *context ) const
{
	if( output == availableFramesPlug() )
	{
		FileSequencePtr fileSequence = nullptr;
		IECore::ls( fileNamePlug()->getValue(), fileSequence, /* minSequenceSize */ 1 );

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
		V3i tileBatchIndex = context->get<V3i>( g_tileBatchIndexContextName );

		std::string fileName = fileNamePlug()->getValue();
		FilePtr file = retrieveFile( fileName, (MissingFrameMode)missingFrameModePlug()->getValue(), this, context );
		if( !file )
		{
			throw IECore::Exception( "OpenImageIOReader - trying to evaluate tileBatchPlug() with invalid file, this should never happen." );
		}

		static_cast<ObjectVectorPlug *>( output )->setValue(
			file->readTileBatch( tileBatchIndex )
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
		// Request blocking compute for tile batches, to avoid concurrent threads loading
		// the same batch redundantly.
		return ValuePlug::CachePolicy::Standard;
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
	if( Context::substitutions( fileName ) & Context::FrameSubstitutions )
	{
		h.append( context->getFrame() );
	}
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
}

GafferImage::Format OpenImageIOReader::computeFormat( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	std::string fileName = fileNamePlug()->getValue();
	// when we're in MissingFrameMode::Black we still want to
	// match the format of the Hold frame.
	MissingFrameMode mode = (MissingFrameMode)missingFrameModePlug()->getValue();
	mode = ( mode == Black ) ? Hold : mode;
	FilePtr file = retrieveFile( fileName, mode, this, context );
	if( !file )
	{
		return FormatPlug::getDefaultFormat( context );
	}

	const ImageSpec &spec = file->imageSpec();
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
}

Imath::Box2i OpenImageIOReader::computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	std::string fileName = fileNamePlug()->getValue();
	FilePtr file = retrieveFile( fileName, (MissingFrameMode)missingFrameModePlug()->getValue(), this, context );
	if( !file )
	{
		return parent->dataWindowPlug()->defaultValue();
	}

	const ImageSpec &spec = file->imageSpec();

	Imath::Box2i dataWindow( Imath::V2i( spec.x, spec.y ), Imath::V2i( spec.width + spec.x, spec.height + spec.y ) );
	return flopDisplayWindow( dataWindow, spec.full_y, spec.full_height );
}

void OpenImageIOReader::hashMetadata( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageNode::hashMetadata( output, context, h );
	hashFileName( context, h );
	refreshCountPlug()->hash( h );
	missingFrameModePlug()->hash( h );
}

IECore::ConstCompoundDataPtr OpenImageIOReader::computeMetadata( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	std::string fileName = fileNamePlug()->getValue();
	FilePtr file = retrieveFile( fileName, (MissingFrameMode)missingFrameModePlug()->getValue(), this, context );
	if( !file )
	{
		return parent->metadataPlug()->defaultValue();
	}
	const ImageSpec &spec = file->imageSpec();

	CompoundDataPtr result = new CompoundData;

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
			dataType = boost::str( boost::format( "uint%d"  ) % bitsPerSample );
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
		if( DataPtr data = IECoreImage::OpenImageIOAlgo::data( attrib ) )
		{
			result->writable()[attrib.name().string()] = data;
		}
	}

	return result;
}

void OpenImageIOReader::hashChannelNames( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageNode::hashChannelNames( output, context, h );
	hashFileName( context, h );
	refreshCountPlug()->hash( h );
	missingFrameModePlug()->hash( h );
}

IECore::ConstStringVectorDataPtr OpenImageIOReader::computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	std::string fileName = fileNamePlug()->getValue();
	FilePtr file = retrieveFile( fileName, (MissingFrameMode)missingFrameModePlug()->getValue(), this, context );
	if( !file )
	{
		return parent->channelNamesPlug()->defaultValue();
	}
	return file->channelNamesData();
}

void OpenImageIOReader::hashChannelData( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageNode::hashChannelData( output, context, h );
	h.append( context->get<V2i>( ImagePlug::tileOriginContextName ) );
	h.append( context->get<std::string>( ImagePlug::channelNameContextName ) );

	{
		ImagePlug::GlobalScope c( context );
		hashFileName( context, h );
		refreshCountPlug()->hash( h );
		missingFrameModePlug()->hash( h );
	}
}

IECore::ConstFloatVectorDataPtr OpenImageIOReader::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	ImagePlug::GlobalScope c( context );
	std::string fileName = fileNamePlug()->getValue();
	FilePtr file = retrieveFile( fileName, (MissingFrameMode)missingFrameModePlug()->getValue(), this, context );

	if( !file )
	{
		return parent->channelDataPlug()->defaultValue();
	}

	Box2i dataWindow = outPlug()->dataWindowPlug()->getValue();
	const Box2i tileBound( tileOrigin, tileOrigin + V2i( ImagePlug::tileSize() ) );
	if( !BufferAlgo::intersects( dataWindow, tileBound ) )
	{
		throw IECore::Exception( boost::str(
			boost::format( "OpenImageIOReader : Invalid tile (%i,%i) -> (%i,%i) not within data window (%i,%i) -> (%i,%i)." ) %
			tileBound.min.x % tileBound.min.y % tileBound.max.x % tileBound.max.y %
			dataWindow.min.x % dataWindow.min.y % dataWindow.max.x % dataWindow.max.y
		) );
	}

	V3i tileBatchIndex;
	int subIndex;
	file->findTile( channelName, tileOrigin, tileBatchIndex, subIndex );

	c.set( g_tileBatchIndexContextName, tileBatchIndex );

	ConstObjectVectorPtr tileBatch = tileBatchPlug()->getValue();
	ConstObjectPtr curTileChannel = tileBatch->members()[ subIndex ];
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
