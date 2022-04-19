//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013-2019, Image Engine Design Inc. All rights reserved.
//  Copyright (c) 2015, Nvizible Ltd. All rights reserved.
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

#include "GafferImage/ImageWriter.h"

#include "GafferImage/BufferAlgo.h"
#include "GafferImage/ColorSpace.h"
#include "GafferImage/FormatPlug.h"
#include "GafferImage/ImageAlgo.h"
#include "GafferImage/ImagePlug.h"

#include "Gaffer/Context.h"
#include "Gaffer/Metadata.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/StringPlug.h"
#include "Gaffer/Version.h"

#include "IECoreImage/OpenImageIOAlgo.h"

#include "IECore/MessageHandler.h"
#include "IECore/StringAlgo.h"

#include "OpenImageIO/imageio.h"
#include "OpenImageIO/deepdata.h"

#include "OpenColorIO/OpenColorIO.h"

#include "boost/algorithm/string.hpp"
#include "boost/filesystem.hpp"
#include "boost/functional/hash.hpp"

#include "tbb/spin_mutex.h"

#include <memory>

#ifndef _MSC_VER
#include <sys/utsname.h>
#else
#define WIN32_LEAN_AND_MEAN
#include <Windows.h>
#endif
#include <zlib.h>

OIIO_NAMESPACE_USING

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferDispatch;
using namespace GafferImage;

static InternedString g_modePlugName( "mode" );
static InternedString g_compressionPlugName( "compression" );
static InternedString g_compressionQualityPlugName( "compressionQuality" );
static InternedString g_chromaSubSamplingPlugName( "chromaSubSampling" );
static InternedString g_compressionLevelPlugName( "compressionLevel" );
static InternedString g_dataTypePlugName( "dataType" );
static InternedString g_depthDataTypePlugName( "depthDataType" );
static InternedString g_dwaCompressionLevelPlugName( "dwaCompressionLevel" );

namespace
{

// Integer division, rounding to negative infinity ( assumes b is positive )
inline int divFloor( int a, int b )
{
	return a / b - ( ( a % b ) < 0 );
}

void copyBufferArea( const float *inData, const Imath::Box2i &inArea, float *outData, const Imath::Box2i &outArea, const size_t outOffset = 0, const size_t outInc = 1, const bool outYDown = false, Imath::Box2i copyArea = Imath::Box2i() )
{
	if( BufferAlgo::empty( copyArea ) )
	{
		copyArea = BufferAlgo::intersection( inArea, outArea );
	}

	assert( BufferAlgo::contains( inArea, copyArea ) );
	assert( BufferAlgo::contains( outArea, copyArea ) );

	for( int y = copyArea.min.y; y < copyArea.max.y; ++y )
	{
		size_t yOffsetIn = y - inArea.min.y;
		size_t yOffsetOut = y - outArea.min.y;

		if( outYDown )
		{
			yOffsetOut = outArea.max.y - y - 1;
		}

		const float *inPtr = inData + ( yOffsetIn * inArea.size().x ) + ( copyArea.min.x - inArea.min.x );
		float *outPtr = outData + ( ( ( yOffsetOut * outArea.size().x ) + ( copyArea.min.x - outArea.min.x ) ) * outInc ) + outOffset;

		for( int x = copyArea.min.x; x < copyArea.max.x; x++, outPtr += outInc )
		{
			*outPtr = *inPtr++;
		}
	}
}

void copyDeepArea(
	const int *offsetData, const float *tileData, const int inOffsetPos, const Imath::V2i &size,
	DeepData &outData, const int outStartIndex, const int outStride, const int channel
)
{
	for( int y = 0; y < size.y; y++ )
	{
		int offsetPos = inOffsetPos + y * ImagePlug::tileSize();
		assert( offsetPos < ImagePlug::tilePixels() );
		int offset = offsetPos > 0 ? offsetData[ offsetPos - 1 ] : 0;
		const float *inPtr = &tileData[ offset ];
		int outIndex = outStartIndex + ( size.y - y - 1 ) * outStride;

		assert( outData.samples( outIndex ) == offsetData[ offsetPos ] - offset );
		int sum = 0;
		for( int x = 0; x < size.x; x++ )
		{
			assert( outIndex < outData.pixels() );
			sum += outData.samples( outIndex );
			for( int j = 0; j < outData.samples( outIndex ); j++ )
			{
				outData.set_deep_value( outIndex, channel, j, *inPtr++ );
			}
			outIndex++;
		}
		assert( sum == offsetData[ offsetPos + size.x - 1 ] - offset );
	}
}

using ImageOutputPtr = std::shared_ptr<ImageOutput>;

class TileSampleOffsetsProcessor
{
	public:
		using Result = ConstIntVectorDataPtr;

		TileSampleOffsetsProcessor() {}

		Result operator()( const ImagePlug *imagePlug, const V2i &tileOrigin ) const
		{
			return imagePlug->sampleOffsetsPlug()->getValue();
		}
};

class TileChannelDataProcessor
{
	public:
		using Result = ConstFloatVectorDataPtr;

		TileChannelDataProcessor() {}

		ConstFloatVectorDataPtr operator()( const ImagePlug *imagePlug, const string &channelName, const V2i &tileOrigin ) const
		{
			return imagePlug->channelDataPlug()->getValue();
		}
};

struct V2iHash
{
	std::size_t operator()( const V2i &i ) const
	{
		using Hashable = std::pair<float, float>;
		return boost::hash<Hashable>()( Hashable( i.x, i.y ) );
	}
};

class SampleOffsetsAccumulator
{
	public:
		using Result = std::unordered_map<Imath::V2i, ConstIntVectorDataPtr, V2iHash>;

		void operator()( const ImagePlug *imagePlug, const V2i &tileOrigin, ConstIntVectorDataPtr sampleOffsets )
		{
			m_sampleOffsets[tileOrigin] = sampleOffsets;
		}

		Result m_sampleOffsets;
};

class FlatTileWriter
{
	// This class is created to be used by parallelGatherTiles, and called
	// in series for each Gaffer tile/channel from the top down.
	//
	// This class has been designed to support any size of output tile. Because
	// only rare cases of output image will involve the output tiles lining up
	// exactly with the Gaffer tiles, it would already need to collect the
	// tile data as it goes, and so there was not a massive amount of extra
	// complexity to not assume the same tile size, allowing for the
	// possibility that multiple output tiles may be contained within a single
	// Gaffer tile.
	//
	// The instance of the class stores a vector of tile data storage vectors,
	// all of which start off empty. We only allocate the space for the tiles
	// when we need to start filling them, and free the space once the tiles
	// have been written to the ImageOutput. We also store a vector of bool
	// values (m_tilesFilled) to determine which output tiles have been filled
	// with data, and are therefore ready to write.
	//
	// The instance stores the index (m_nextTileIndex) of the next output tile
	// that it is expecting to write. This is because some formats require
	// tiles to be written in order, and we are holding to that for all
	// formats.
	//
	// As Gaffer tiles are passed in, the data is copied into any output tiles
	// they intersect with. Once that is done, any output tiles whose bottom
	// right corners are above and to the left (or equal) to the bottom right
	// corner of the tile we've just written can be considered to be filled,
	// so set the appropriate m_tilesFilled value.
	//
	// After flagging filled tiles, it iterates through tiles, starting at
	// m_nextTileIndex, and for each tile, if the tile is marked as filled,
	// write it, and if the tile does not intersect the region covered by the
	// input tiles, write a black tile. If neither of these is the case, stop,
	// and set m_nextTileIndex to the tile that it stopped on, which is the
	// next tile to write.
	//
	// Once all Gaffer tiles have been processed, there may still be partially
	// unfilled tiles, which will be fine, as their unfilled areas will be
	// black, which is what we want. So iterate over the remaining tiles, and
	// if memory has been allocated for that tile, write it to the file, and if
	// nothing has been allocated, write a black tile.
	public:
		FlatTileWriter(
				ImageOutputPtr out,
				const std::string &fileName,
				const Imath::Box2i &processWindow,
				const GafferImage::Format &format,
				const std::vector< std::string > &channels
			) :
				m_out( out ),
				m_fileName( fileName ),
				m_format( format ),
				m_channels( channels ),
				m_spec( m_out->spec() ),
				m_processWindow( processWindow ),
				m_inputTilesBounds( Imath::Box2i( ImagePlug::tileOrigin( processWindow.min ), ImagePlug::tileOrigin( processWindow.max - Imath::V2i( 1 ) ) + Imath::V2i( ImagePlug::tileSize() ) ) ),
				m_outputDataWindow( m_format.fromEXRSpace( Imath::Box2i( Imath::V2i( m_spec.x, m_spec.y ), Imath::V2i( m_spec.x + m_spec.width - 1, m_spec.y + m_spec.height - 1 ) ) ) ),
				m_numTiles( Imath::V2i( (int)ceil( float( m_spec.width ) / m_spec.tile_width ), (int)ceil( float( m_spec.height ) / m_spec.tile_height ) ) ),
				m_nextTileIndex( 0 ),
				m_blackTile( nullptr )
		{
			m_tilesData.resize( m_numTiles.x * m_numTiles.y );
			m_tilesFilled.resize( m_numTiles.x * m_numTiles.y, false );

			for( size_t i = 0; i < m_tilesData.size(); ++i )
			{
				m_tilesData[i] = new FloatVectorData;
			}
		}

		void finish()
		{
			for( size_t tileIndex = m_nextTileIndex; tileIndex < m_tilesData.size(); ++tileIndex )
			{
				Imath::V2i tileOrigin = outTileOrigin( tileIndex );
				if( !m_tilesData[tileIndex]->readable().empty() )
				{
					writeTile( tileOrigin, m_tilesData[tileIndex] );
				}
				else
				{
					// If the tileData object hasn't been resized, then
					// we have never even tried to write data to this
					// tile, so write the static black tile.
					writeTile( tileOrigin, blackTile() );
				}
			}
		}

		void operator()( const ImagePlug *imagePlug, const string &channelName, const V2i &tileOrigin, ConstFloatVectorDataPtr data )
		{
			const size_t channelIndex = std::find( m_channels.begin(), m_channels.end(), channelName ) - m_channels.begin();

			const Imath::Box2i inTileBounds( tileOrigin, tileOrigin + Imath::V2i( ImagePlug::tileSize() ) );

			Box2i writeRegion = BufferAlgo::intersection( m_outputDataWindow, inTileBounds );
			const Imath::V2i outTileSize( m_spec.tile_width, m_spec.tile_height );
			Box2i tilesWrite(
				outTileOriginContaining( writeRegion.min ),
				outTileOriginContaining( writeRegion.max - Imath::V2i( 1 ) ) + outTileSize
			);

			Imath::V2i outTileOrig( tilesWrite.min.x, tilesWrite.max.y - m_spec.tile_height );

			for( ; outTileOrig.y >= tilesWrite.min.y; outTileOrig.y -= m_spec.tile_height )
			{
				for( outTileOrig.x = tilesWrite.min.x; outTileOrig.x < tilesWrite.max.x; outTileOrig.x += m_spec.tile_width )
				{
					size_t tileIndex = outTileIndex( outTileOrig );
					Imath::Box2i outTileBnds = outTileBounds( tileIndex );

					vector<float> &tile = m_tilesData[tileIndex]->writable();
					if( tile.empty() )
					{
						tile.resize( m_spec.tile_width * m_spec.tile_height * m_channels.size(), 0. );
					}

					Imath::Box2i copyArea( BufferAlgo::intersection( m_processWindow, BufferAlgo::intersection( inTileBounds, outTileBnds ) ) );

					copyBufferArea( &data->readable()[0], inTileBounds, &tile[0], outTileBnds, channelIndex, m_channels.size(), true, copyArea );
				}
			}

			if( lastChannelOfTile( channelIndex ) )
			{
				flagFilledTiles( inTileBounds );
			}

			writeFilledTiles();
		}

	private:

		inline ConstFloatVectorDataPtr blackTile()
		{
			if( m_blackTile == nullptr )
			{
				m_blackTile = new IECore::FloatVectorData( std::vector<float>( m_spec.tile_width * m_spec.tile_height * m_channels.size(), 0. ) );
			}

			return m_blackTile;
		}

		inline size_t outTileIndex( const Imath::V2i &tileOrigin ) const
		{
			return ( ( ( m_outputDataWindow.max.y - m_spec.tile_height - tileOrigin.y ) / m_spec.tile_height ) * m_numTiles.x ) + ( ( tileOrigin.x - m_outputDataWindow.min.x ) / m_spec.tile_width );
		}

		inline Imath::V2i outTileOrigin( const size_t tileIndex ) const
		{
			return Imath::V2i( ( ( tileIndex % m_numTiles.x ) * m_spec.tile_width ) + m_outputDataWindow.min.x, m_outputDataWindow.max.y - m_spec.tile_height - ( ( tileIndex / m_numTiles.x ) * m_spec.tile_height ) );
		}

		inline Imath::V2i outTileOriginContaining( const Imath::V2i &point ) const
		{
			Imath::V2i tempPoint = point - Imath::V2i( m_outputDataWindow.min.x, m_outputDataWindow.max.y );
			Imath::V2i tileOrigin(
				divFloor( tempPoint.x, m_spec.tile_width ) * m_spec.tile_width,
				divFloor( tempPoint.y, m_spec.tile_height ) * m_spec.tile_height
			);
			return tileOrigin + Imath::V2i( m_outputDataWindow.min.x, m_outputDataWindow.max.y );
		}

		inline Imath::Box2i outTileBounds( const size_t tileIndex ) const
		{
			Imath::V2i origin = outTileOrigin( tileIndex );
			return Imath::Box2i( origin, origin + Imath::V2i( m_spec.tile_width, m_spec.tile_height ) );
		}

		inline bool lastChannelOfTile( const size_t channelIndex )
		{
			return channelIndex == ( m_channels.size() - 1 );
		}

		void flagFilledTiles( const Imath::Box2i &inTileBounds )
		{
			for( size_t i = m_nextTileIndex; i < m_tilesData.size(); ++i )
			{
				if( !m_tilesFilled[i] )
				{
					Imath::Box2i outTileBnds( outTileBounds( i ) );
					if( inTileBounds.max.x >= outTileBnds.max.x && inTileBounds.min.y <= outTileBnds.min.y )
					{
						m_tilesFilled[i] = true;
					}
					else
					{
						break;
					}
				}
			}
		}

		void writeFilledTiles()
		{
			size_t tileIndex;
			for( tileIndex = m_nextTileIndex; tileIndex < m_tilesData.size(); ++tileIndex )
			{
				Imath::V2i tileOrigin = outTileOrigin( tileIndex );

				if( m_tilesFilled[tileIndex] )
				{
					writeTile( tileOrigin, m_tilesData[tileIndex] );
					m_tilesData[tileIndex].reset();
				}
				else if( !BufferAlgo::intersects( m_inputTilesBounds, outTileBounds( tileIndex ) ) )
				{
					writeTile( tileOrigin, blackTile() );
				}
				else
				{
					break;
				}
			}

			m_nextTileIndex = tileIndex;
		}


		void writeTile( const Imath::V2i &tileOrigin, ConstFloatVectorDataPtr tileData ) const
		{
			Imath::V2i exrTileOrigin = m_format.toEXRSpace( tileOrigin + Imath::V2i( 0, m_spec.tile_height - 1 ) );

			if( !m_out->write_tile( exrTileOrigin.x, exrTileOrigin.y, 0, TypeDesc::FLOAT, &tileData->readable()[0] ) )
			{
				throw IECore::Exception( boost::str( boost::format( "Could not write tile to \"%s\", error = %s" ) % m_fileName % m_out->geterror() ) );
			}
		}

		ImageOutputPtr m_out;
		const std::string &m_fileName;
		const GafferImage::Format &m_format;
		const std::vector< std::string > &m_channels;
		const ImageSpec m_spec;
		const Imath::Box2i m_processWindow;
		const Imath::Box2i m_inputTilesBounds;
		const Imath::Box2i m_outputDataWindow;
		const Imath::V2i m_numTiles;
		size_t m_nextTileIndex;
		std::vector<FloatVectorDataPtr> m_tilesData;
		std::vector<bool> m_tilesFilled;
		ConstFloatVectorDataPtr m_blackTile;
};

class FlatScanlineWriter
{
	// This class is created to be used by parallelGatherTiles and called in
	// series for each Gaffer tile/channel from the top down.
	//
	// When it is first created, it writes to the ImageOutput object any blank
	// scanlines that fall between the start of the image and the start of the
	// data that it is going to be given.
	//
	// It stores a vector of floats big enough to hold ImagePlug::tileSize()
	// scanlines. As it receives each tile, it copies the data into the
	// appropriate location in the buffer. When it's copied the last channel
	// of the last tile of each row, it writes all of the data from the buffer
	// into the ImageOutput object.
	public:
		FlatScanlineWriter(
				ImageOutputPtr out,
				const std::string &fileName,
				const Imath::Box2i &processWindow,
				const GafferImage::Format &format,
				const std::vector< std::string > &channels
			) :
				m_out( out ),
				m_fileName( fileName ),
				m_format( format ),
				m_channels( channels ),
				m_spec( m_out->spec() ),
				m_processWindow( processWindow ),
				m_tilesBounds( Imath::Box2i( ImagePlug::tileOrigin( processWindow.min ), ImagePlug::tileOrigin( processWindow.max - Imath::V2i( 1 ) ) + Imath::V2i( ImagePlug::tileSize() ) ) )
		{
			m_scanlinesData.resize( m_spec.width * ImagePlug::tileSize() * m_channels.size(), 0.0 );

			writeInitialBlankScanlines();
		}

		void finish()
		{
			if( BufferAlgo::empty( m_processWindow ) )
			{
				// If the source data window is empty, we handle everything during construct
				return;
			}

			const int scanlinesEnd = m_format.toEXRSpace( m_tilesBounds.min.y - 1 );
			if( scanlinesEnd < ( m_spec.y + m_spec.height ) )
			{
				writeBlankScanlines( scanlinesEnd, m_spec.y + m_spec.height );
			}
		}

		void operator()( const ImagePlug *imagePlug, const string &channelName, const V2i &tileOrigin, ConstFloatVectorDataPtr data )
		{
			const size_t channelIndex = std::find( m_channels.begin(), m_channels.end(), channelName ) - m_channels.begin();

			const Imath::Box2i inTileBounds( tileOrigin, tileOrigin + Imath::V2i( ImagePlug::tileSize() ) );
			const Imath::Box2i exrInTileBounds( m_format.toEXRSpace( inTileBounds ) );

			const Imath::Box2i exrScanlinesBounds( Imath::V2i( m_spec.x, exrInTileBounds.min.y ), Imath::V2i( m_spec.x + m_spec.width - 1, exrInTileBounds.max.y ) );
			const Imath::Box2i scanlinesBounds( m_format.fromEXRSpace( exrScanlinesBounds ) );

			if( firstTileOfRow( channelIndex, tileOrigin ) )
			{
				std::fill( m_scanlinesData.begin(), m_scanlinesData.end(), 0.0 );
			}

			Imath::Box2i copyArea( BufferAlgo::intersection( m_processWindow, BufferAlgo::intersection( inTileBounds, scanlinesBounds ) ) );

			copyBufferArea( &data->readable()[0], inTileBounds, &m_scanlinesData[0], scanlinesBounds, channelIndex, m_channels.size(), true, copyArea );

			if( lastTileOfRow( channelIndex, tileOrigin ) )
			{
				writeScanlines(
					std::max( exrInTileBounds.min.y, m_spec.y ),
					std::min( exrInTileBounds.max.y + 1, m_spec.y + m_spec.height ),
					std::max( m_spec.y - exrInTileBounds.min.y, 0 )
				);
			}
		}

	private:

		inline bool firstTileOfRow( const size_t channelIndex, const Imath::V2i &tileOrigin ) const
		{
			return channelIndex == 0 && tileOrigin.x == m_tilesBounds.min.x;
		}

		inline bool lastTileOfRow( const size_t channelIndex, const Imath::V2i &tileOrigin ) const
		{
			return channelIndex == ( m_channels.size() - 1 ) && tileOrigin.x == ( m_tilesBounds.max.x - ImagePlug::tileSize() ) ;
		}

		void writeScanlines( const int exrYBegin, const int exrYEnd, const int scanlinesYOffset = 0 ) const
		{
			if ( !m_out->write_scanlines( exrYBegin, exrYEnd, 0, TypeDesc::FLOAT, &m_scanlinesData[0] + ( scanlinesYOffset * m_spec.width * m_channels.size() ) ) )
			{
				throw IECore::Exception( boost::str( boost::format( "Could not write scanline to \"%s\", error = %s" ) % m_fileName % m_out->geterror() ) );
			}
		}

		void writeBlankScanlines( int yBegin, int yEnd )
		{
			float *scanlines = &m_scanlinesData[0];
			memset( scanlines, 0, sizeof(float) * m_spec.width * std::min( ImagePlug::tileSize(), yEnd - yBegin ) * m_channels.size() );
			while( yBegin < yEnd )
			{
				const int numLines = std::min( yEnd - yBegin, ImagePlug::tileSize() );
				writeScanlines( yBegin, yBegin + numLines );
				yBegin += numLines;
			}
		}

		void writeInitialBlankScanlines()
		{
			if( BufferAlgo::empty( m_processWindow ) )
			{
				// There is no data to process, so everything should be blank
				writeBlankScanlines( m_spec.y, m_spec.y + m_spec.height );
			}
			else
			{
				const int scanlinesBegin = m_format.toEXRSpace( m_tilesBounds.max.y - 1 );
				if( scanlinesBegin > m_spec.y )
				{
					writeBlankScanlines( m_spec.y, scanlinesBegin );
				}
			}
		}

		ImageOutputPtr m_out;
		const std::string &m_fileName;
		const GafferImage::Format &m_format;
		const std::vector< std::string > &m_channels;
		const ImageSpec m_spec;
		const Imath::Box2i &m_processWindow;
		const Imath::Box2i m_tilesBounds;
		vector<float> m_scanlinesData;
};

class DeepTileWriter
{
	// This class is created to be used by parallelGatherTiles, and called
	// in series for each Gaffer tile/channel from the top down.
	//
	// The tile traversal logic is identical to FlatTileWriter above, with the
	// difference that all tiles will be fully covered by input tiles ( because
	// the data windows are expected to match, since EXR supports setting the
	// data window ).

	public:
		DeepTileWriter(
				ImageOutputPtr out,
				const std::string &fileName,
				const Imath::Box2i &processWindow,
				const GafferImage::Format &format,
				const std::vector< std::string > &channels,
				const SampleOffsetsAccumulator::Result &sampleOffsets
			) :
				m_out( out ),
				m_fileName( fileName ),
				m_format( format ),
				m_channels( channels ),
				m_spec( m_out->spec() ),
				m_processWindow( processWindow ),
				m_sampleOffsets( sampleOffsets ),
				m_outputDataWindow( m_format.fromEXRSpace( Imath::Box2i( Imath::V2i( m_spec.x, m_spec.y ), Imath::V2i( m_spec.x + m_spec.width - 1, m_spec.y + m_spec.height - 1 ) ) ) ),
				m_numTiles( Imath::V2i( (int)ceil( float( m_spec.width ) / m_spec.tile_width ), (int)ceil( float( m_spec.height ) / m_spec.tile_height ) ) ),
				m_nextTileIndex( 0 ),
				m_tilesData( m_numTiles.x * m_numTiles.y),
				m_tilesFilled( m_numTiles.x * m_numTiles.y, false )
		{
			if( BufferAlgo::empty( m_processWindow ) )
			{
				// With deep, we do not support any formats that don't have data windows.  So the one
				// case where we need to worry about inventing extra blank data we don't store is when
				// our data window is empty, and we've added one empty pixel since EXR doesn't allow an
				// empty data window.
				assert( m_spec.width == 1 && m_spec.height == 1 );

				prepOutTile( 0 );
				writeDeepTile( outTileOrigin( 0 ), m_tilesData[0] );
			}
		}

		void operator()( const ImagePlug *imagePlug, const string &channelName, const V2i &tileOrigin, ConstFloatVectorDataPtr data )
		{
			const size_t channelIndex = std::find( m_channels.begin(), m_channels.end(), channelName ) - m_channels.begin();

			const Imath::Box2i inTileBounds( tileOrigin, tileOrigin + Imath::V2i( ImagePlug::tileSize() ) );

			Box2i writeRegion = BufferAlgo::intersection( m_outputDataWindow, inTileBounds );
			const Imath::V2i outTileSize( m_spec.tile_width, m_spec.tile_height );
			Box2i tilesWrite(
				outTileOriginContaining( writeRegion.min ),
				outTileOriginContaining( writeRegion.max - Imath::V2i( 1 ) ) + outTileSize
			);

			Imath::V2i outTileOrig( tilesWrite.min.x, tilesWrite.max.y - m_spec.tile_height );

			const std::vector<int> &sampleOffsets = m_sampleOffsets.at( tileOrigin )->readable();
			assert( sampleOffsets.back() == (int)data->readable().size() );

			// For any output tiles that overlap this input tile, copy the overlapping area into
			// the output tile
			for( ; outTileOrig.y >= tilesWrite.min.y; outTileOrig.y -= m_spec.tile_height )
			{
				for( outTileOrig.x = tilesWrite.min.x; outTileOrig.x < tilesWrite.max.x; outTileOrig.x += m_spec.tile_width )
				{
					size_t tileIndex = outTileIndex( outTileOrig );

					if( !m_tilesData[tileIndex].pixels() )
					{
						prepOutTile( tileIndex );
					}

					Imath::Box2i outTileBnds = outTileBounds( tileIndex );
					Imath::Box2i copyArea( BufferAlgo::intersection( m_processWindow, BufferAlgo::intersection( inTileBounds, outTileBnds ) ) );

					V2i offset = copyArea.min - tileOrigin;
					const int inOffsetPos = offset.y * ImagePlug::tileSize() + offset.x;

					const int outStartIndex = ( outTileBnds.max.y - copyArea.max.y ) * outTileBnds.size().x + copyArea.min.x - outTileBnds.min.x;
					copyDeepArea(
						&sampleOffsets[0], &data->readable()[0], inOffsetPos, copyArea.size(),
						m_tilesData[tileIndex], outStartIndex, outTileBnds.size().x, channelIndex
					);
				}
			}

			if( channelIndex == ( m_channels.size() - 1 ) )
			{
				flagFilledTiles( inTileBounds );
				writeFilledTiles();
			}
		}

	private:

		inline size_t outTileIndex( const Imath::V2i &tileOrigin ) const
		{
			return ( ( ( m_outputDataWindow.max.y - m_spec.tile_height - tileOrigin.y ) / m_spec.tile_height ) * m_numTiles.x ) + ( ( tileOrigin.x - m_outputDataWindow.min.x ) / m_spec.tile_width );
		}

		inline Imath::V2i outTileOrigin( const size_t tileIndex ) const
		{
			return Imath::V2i( ( ( tileIndex % m_numTiles.x ) * m_spec.tile_width ) + m_outputDataWindow.min.x, m_outputDataWindow.max.y - m_spec.tile_height - ( ( tileIndex / m_numTiles.x ) * m_spec.tile_height ) );
		}

		inline Imath::V2i outTileOriginContaining( const Imath::V2i &point ) const
		{
			Imath::V2i tempPoint = point - Imath::V2i( m_outputDataWindow.min.x, m_outputDataWindow.max.y );
			Imath::V2i tileOrigin(
				divFloor( tempPoint.x, m_spec.tile_width ) * m_spec.tile_width,
				divFloor( tempPoint.y, m_spec.tile_height ) * m_spec.tile_height
			);
			return tileOrigin + Imath::V2i( m_outputDataWindow.min.x, m_outputDataWindow.max.y );
		}

		inline Imath::Box2i outTileBounds( const size_t tileIndex ) const
		{
			Imath::V2i origin = outTileOrigin( tileIndex );
			return BufferAlgo::intersection( m_outputDataWindow, Imath::Box2i( origin, origin + Imath::V2i( m_spec.tile_width, m_spec.tile_height ) ) );
		}


		void flagFilledTiles( const Imath::Box2i &inTileBounds )
		{
			for( size_t i = m_nextTileIndex; i < m_tilesData.size(); ++i )
			{
				if( !m_tilesFilled[i] )
				{
					Imath::Box2i outTileBnds( outTileBounds( i ) );
					if( inTileBounds.max.x >= outTileBnds.max.x && inTileBounds.min.y <= outTileBnds.min.y )
					{
						m_tilesFilled[i] = true;
					}
					else
					{
						break;
					}
				}
			}
		}

		void writeFilledTiles()
		{
			size_t tileIndex;
			for( tileIndex = m_nextTileIndex; tileIndex < m_tilesData.size(); ++tileIndex )
			{
				Imath::V2i tileOrigin = outTileOrigin( tileIndex );

				if( m_tilesFilled[tileIndex] )
				{
					writeDeepTile( tileOrigin, m_tilesData[tileIndex] );
					m_tilesData[tileIndex].clear();
				}
				else
				{
					break;
				}
			}

			m_nextTileIndex = tileIndex;
		}

		// Prepare the deep data for an outputTile.  We need to set all the pixel sizes before setting any
		// channel data, because changing pixel sizes after setting data would trigger a full reallocation
		void prepOutTile( int tileIndex )
		{
			const Imath::V2i targetTileSize( m_spec.tile_width, m_spec.tile_height );

			Box2i outTileBnds = outTileBounds( tileIndex );

			int numPixels = outTileBnds.size().x * outTileBnds.size().y;

			DeepData &curTile = m_tilesData[tileIndex];
			if (int(m_spec.channelformats.size()) == m_spec.nchannels)
			{
				// Init with format specified per channel
				curTile.init(
					numPixels, m_channels.size(),
					m_spec.channelformats, m_channels
				);
			}
			else
			{
				// Init with global format
				curTile.init(
					numPixels, m_channels.size(),
					m_spec.format, m_channels
				);
			}

			if( BufferAlgo::empty( m_processWindow ) )
			{
				// No data, don't initialize offsets
				return;
			}

			// Loop through all the pixels in tile, setting up all the sample counts
			// We repeatedly find the sampleOffsets for the tile containing the current
			// pixel, and then instead of transferring one pixel, we transfer a scanline
			// of pixels until we reach the end of the input tile or the output tile - this
			// avoids repeating the lookup of sampleOffsets too often
			int i = 0;
			V2i pixelCoord;
			for( pixelCoord.y = outTileBnds.max.y - 1; pixelCoord.y >= outTileBnds.min.y; pixelCoord.y-- )
			{
				pixelCoord.x = outTileBnds.min.x;
				while( pixelCoord.x < outTileBnds.max.x)
				{
					V2i tileOrigin = ImagePlug::tileOrigin( pixelCoord );
					V2i pixelOffset = pixelCoord - tileOrigin;
					int pixelIndex = pixelOffset.y * ImagePlug::tileSize() + pixelOffset.x;

					const vector<int> &offsets = m_sampleOffsets.at(tileOrigin)->readable();

					int subScanlineLength = std::min( ImagePlug::tileSize() - pixelOffset.x, outTileBnds.max.x - pixelCoord.x );
					int prevOffset = pixelIndex > 0 ? offsets[pixelIndex - 1] : 0;
					for( int j = 0; j < subScanlineLength; j++ )
					{
						int offset = offsets[ pixelIndex + j ];
						curTile.set_samples( i, offset - prevOffset);
						prevOffset = offset;
						i++;
					}
					pixelCoord.x += subScanlineLength;
				}
			}
		}

		void writeDeepTile( const Imath::V2i &tileOrigin, const DeepData &tileData ) const
		{
			Imath::V2i exrTileOrigin = m_format.toEXRSpace( tileOrigin + Imath::V2i( 0, m_spec.tile_height - 1 ) );

			if( !m_out->write_deep_tiles(
				exrTileOrigin.x, std::min( m_spec.width + m_spec.x, exrTileOrigin.x + m_spec.tile_width ),
				exrTileOrigin.y, std::min( m_spec.height + m_spec.y, exrTileOrigin.y + m_spec.tile_height ),
				0, 1,
				tileData
			) )
			{
				throw IECore::Exception( boost::str( boost::format( "Could not write tile to \"%s\", error = %s" ) % m_fileName % m_out->geterror() ) );
			}
		}

		ImageOutputPtr m_out;
		const std::string &m_fileName;
		const GafferImage::Format &m_format;
		const std::vector< std::string > &m_channels;
		const ImageSpec m_spec;
		const Imath::Box2i m_processWindow;
		const SampleOffsetsAccumulator::Result &m_sampleOffsets;
		const Imath::Box2i m_outputDataWindow;
		const Imath::V2i m_numTiles;
		size_t m_nextTileIndex;
		std::vector<DeepData> m_tilesData;
		std::vector<bool> m_tilesFilled;
};

class DeepScanlineWriter
{
	// This class is created to be used by parallelGatherTiles and called in
	// series for each Gaffer tile/channel from the top down.
	//
	// The deep variant assumes that the dataWindow of the file matches the
	// Gaffer data window ( since the only deep format we support is EXR, and
	// EXR allows us to set the data window ).
	//
	// It stores an OpenImageIO::DeepData big enough to hold ImagePlug::tileSize()
	// scanlines. As it receives each tile, it copies the data into the
	// appropriate location in the buffer. When it's copied the last channel
	// of the last tile of each row, it writes all of the data from the buffer
	// into the ImageOutput object.

	public:
		DeepScanlineWriter(
				ImageOutputPtr out,
				const std::string &fileName,
				const Imath::Box2i &processWindow,
				const GafferImage::Format &format,
				const std::vector< std::string > &channels,
				const SampleOffsetsAccumulator::Result &sampleOffsets
			) :
				m_out( out ),
				m_fileName( fileName ),
				m_format( format ),
				m_channels( channels ),
				m_spec( m_out->spec() ),
				m_processWindow( processWindow ),
				m_sampleOffsets( sampleOffsets )
		{
			if( BufferAlgo::empty( m_processWindow ) )
			{
				// With deep, we do not support any formats that don't have data windows.  So the one
				// case where we need to worry about inventing extra blank data we don't store is when
				// our data window is empty, and we've added one empty pixel since EXR doesn't allow an
				// empty data window.
				//
				m_chunkY = m_spec.y;
				prepChunk();

				assert( m_spec.width == 1 && m_spec.height == 1 );

				writeDeepScanlines();
			}
			else
			{
				m_chunkY = m_format.toEXRSpace( ImagePlug::tileOrigin( processWindow.max - V2i( 1 ) ).y + ImagePlug::tileSize() ) + 1;
				prepChunk();
			}
		}

		void operator()( const ImagePlug *imagePlug, const string &channelName, const V2i &tileOrigin, ConstFloatVectorDataPtr data )
		{
			const size_t channelIndex = std::find( m_channels.begin(), m_channels.end(), channelName ) - m_channels.begin();

			const Imath::Box2i inTileBounds( tileOrigin, tileOrigin + Imath::V2i( ImagePlug::tileSize() ) );

			Imath::Box2i copyArea( BufferAlgo::intersection( m_processWindow, inTileBounds ) );

			const std::vector<int> &sampleOffsets = m_sampleOffsets.at( tileOrigin )->readable();
			assert( sampleOffsets.back() == (int)data->readable().size() );
			V2i offset = copyArea.min - tileOrigin;
			const int inOffsetPos = offset.y * ImagePlug::tileSize() + offset.x;

			// Copy into the chunk the region of this tile that overlaps the process window ( which for
			// deep is always the data window )
			copyDeepArea(
				&sampleOffsets[0], &data->readable()[0], inOffsetPos, copyArea.size(), m_deepData,
				copyArea.min.x - m_processWindow.min.x, m_spec.width, channelIndex
			);

			// Do the write once we receive the final tile for this row
			V2i maxTileOrigin = ImagePlug::tileOrigin( m_processWindow.max - V2i( 1 ) );
			if( channelIndex == ( m_channels.size() - 1 ) && tileOrigin.x == maxTileOrigin.x )
			{
				writeDeepScanlines();
			}
		}

	private:
		std::pair<int,int> scanlineRange()
		{
			return std::pair<int,int>( std::max( m_chunkY, m_spec.y ), std::min( m_chunkY + ImagePlug::tileSize(), m_spec.height + m_spec.y ) );
		}

		// Prepare the next chunk of scanlines.  This is a piece of DeepData which is up to tileSize pixels tall,
		// and the width of the image.  We need to set all the pixel sizes before set any channel data, because
		// changing pixel sizes after setting data would trigger a full reallocation
		void prepChunk()
		{
			auto range = scanlineRange();
			int nextScanlines = range.second - range.first;

			if( nextScanlines <= 0 )
			{
				return;
			}

			if (int(m_spec.channelformats.size()) == m_spec.nchannels)
			{
				// Init with format specified per channel
				m_deepData.init(
					m_spec.width * nextScanlines, m_channels.size(),
					m_spec.channelformats, m_channels
				);
			}
			else
			{
				// Init with global format
				m_deepData.init(
					m_spec.width * nextScanlines, m_channels.size(),
					m_spec.format, m_channels
				);
			}

			if( BufferAlgo::empty( m_processWindow ) )
			{
				// No data, don't initialize offsets
				return;
			}

			// Loop through all the pixels in chunk, setting up all the sample counts
			// We repeatedly find the sampleOffsets for the tile containing the current
			// pixel, and then instead of transferring one pixel, we transfer a scanline
			// of pixels until we reach the end of the input tile - this avoids
			// repeating the lookup of sampleOffsets too often
			int i = 0;
			for( int y = 0; y < nextScanlines; y++ )
			{
				int x = 0;
				while( x < m_spec.width)
				{
					V2i pixelCoord = m_format.fromEXRSpace( V2i( m_spec.x + x, range.first + y ) );
					V2i tileOrigin = ImagePlug::tileOrigin( pixelCoord );
					V2i pixelOffset = pixelCoord - tileOrigin;
					int pixelIndex = pixelOffset.y * ImagePlug::tileSize() + pixelOffset.x;

					const vector<int> &offsets = m_sampleOffsets.at(tileOrigin)->readable();

					int subScanlineLength = std::min( ImagePlug::tileSize() - pixelOffset.x, m_spec.width - x );
					int prevOffset = pixelIndex > 0 ? offsets[pixelIndex - 1] : 0;
					for( int j = 0; j < subScanlineLength; j++ )
					{
						int offset = offsets[ pixelIndex + j ];
						m_deepData.set_samples( i, offset - prevOffset);
						prevOffset = offset;
						i++;
					}
					x += subScanlineLength;
				}
			}
		}

		void writeDeepScanlines()
		{
			auto range = scanlineRange();
			if ( !m_out->write_deep_scanlines( range.first, range.second, 0, m_deepData ) )
			{
				throw IECore::Exception( boost::str( boost::format( "Could not write scanline to \"%s\", error = %s" ) % m_fileName % m_out->geterror() ) );
			}

			// Advance to next chunk
			m_chunkY += ImagePlug::tileSize();
			prepChunk();
		}

		ImageOutputPtr m_out;
		const std::string &m_fileName;
		const GafferImage::Format &m_format;
		const std::vector< std::string > &m_channels;
		const ImageSpec m_spec;
		const Imath::Box2i m_processWindow;
		const SampleOffsetsAccumulator::Result &m_sampleOffsets;
		int m_chunkY;
		DeepData m_deepData;
};

//////////////////////////////////////////////////////////////////////////
// Utility for converting IECore::Data types to OIIO::TypeDesc types.
//////////////////////////////////////////////////////////////////////////

// See associated blacklist in OpenImageIOReader.
boost::container::flat_set<InternedString> g_metadataBlacklist = {
	"name",
	"oiio:subimagename",
	"oiio:subimages"
};

void metadataToImageSpecAttributes( const CompoundData *metadata, ImageSpec &spec )
{
	const CompoundData::ValueType &members = metadata->readable();
	for( CompoundData::ValueType::const_iterator it = members.begin(); it != members.end(); ++it )
	{
		if( g_metadataBlacklist.count( it->first ) )
		{
			IECore::msg(
				IECore::Msg::Warning, "ImageWriter",
				boost::format( "Ignoring metadata \"%1%\" because it conflicts with OpenImageIO." ) % it->first
			);
			continue;
		}

		const IECoreImage::OpenImageIOAlgo::DataView dataView( it->second.get() );
		if( dataView.data )
		{
			spec.attribute( it->first.c_str(), dataView.type, dataView.data );
		}
	}
}

void setImageSpecFormatChannelOptions( const ImageWriter *node, ImageSpec *spec, const std::string &fileFormatName )
{
	const ValuePlug *optionsPlug = node->getChild<ValuePlug>( fileFormatName );

	if( optionsPlug == nullptr)
	{
		return;
	}

	const StringPlug *deepDataTypePlug = optionsPlug->getChild<StringPlug>( g_depthDataTypePlugName );

	if( deepDataTypePlug != nullptr )
	{
		if( deepDataTypePlug->getValue() == "float" )
		{
			spec->channelformats.resize( spec->nchannels, spec->format );

			for( int i = 0; i < spec->nchannels; i++ )
			{
				if( spec->channelnames[ i ] == "Z" || spec->channelnames[ i ] == "ZBack" )
				{
					spec->channelformats[ i ] = TypeDesc::FLOAT;
				}
			}
		}
	}
}


void setImageSpecFormatOptions( const ImageWriter *node, ImageSpec *spec, const std::string &fileFormatName )
{
	const ValuePlug *optionsPlug = node->getChild<ValuePlug>( fileFormatName );

	if( optionsPlug == nullptr)
	{
		return;
	}

	const StringPlug *dataTypePlug = optionsPlug->getChild<StringPlug>( g_dataTypePlugName );
	std::string dataType;

	if( dataTypePlug != nullptr )
	{
		dataType = dataTypePlug->getValue();

		if( dataType == "int8" )
		{
			spec->set_format( TypeDesc::INT8 );
		}
		else if( dataType == "int16" )
		{
			spec->set_format( TypeDesc::INT16 );
		}
		else if( dataType == "int32" )
		{
			spec->set_format( TypeDesc::INT32 );
		}
		else if( dataType == "int64" )
		{
			spec->set_format( TypeDesc::INT64 );
		}
		else if( dataType == "uint8" )
		{
			spec->set_format( TypeDesc::UINT8 );
		}
		else if( dataType == "uint16" )
		{
			spec->set_format( TypeDesc::UINT16 );
		}
		else if( dataType == "uint32" )
		{
			spec->set_format( TypeDesc::UINT32 );
		}
		else if( dataType == "uint64" )
		{
			spec->set_format( TypeDesc::UINT64 );
		}
		else if( dataType == "half" )
		{
			spec->set_format( TypeDesc::HALF );
		}
		else if( dataType == "float" )
		{
			spec->set_format( TypeDesc::FLOAT );
		}
		else if( dataType == "double" )
		{
			spec->set_format( TypeDesc::DOUBLE );
		}
	}

	const IntPlug *modePlug = optionsPlug->getChild<IntPlug>( g_modePlugName );

	if( modePlug != nullptr && modePlug->getValue() == ImageWriter::Tile )
	{
		spec->tile_width = spec->tile_height = ImagePlug::tileSize();
	}

	const StringPlug *compressionPlug = optionsPlug->getChild<StringPlug>( g_compressionPlugName );
	if( compressionPlug != nullptr )
	{
		spec->attribute( "compression", compressionPlug->getValue() );
	}

	if( fileFormatName == "openexr" )
	{
		const string compression = compressionPlug->getValue();
		if( compression == "dwaa" || compression == "dwab" )
		{
			const float level = optionsPlug->getChild<FloatPlug>( g_dwaCompressionLevelPlugName )->getValue();
			spec->attribute( "compression", compression + ":" + to_string( level ) );
		}
	}
	else if( fileFormatName == "jpeg" )
	{
		spec->attribute( "CompressionQuality", optionsPlug->getChild<IntPlug>( g_compressionQualityPlugName )->getValue() );
		std::string subSampling = optionsPlug->getChild<StringPlug>( g_chromaSubSamplingPlugName )->getValue();
		if( subSampling != "" ){
			spec->attribute( "jpeg:subsampling", subSampling );
		}
	}
	else if( fileFormatName == "dpx" )
	{
		if( dataType == "uint10" )
		{
			spec->set_format( TypeDesc::UINT16 );
			spec->attribute ("oiio:BitsPerSample", 10);
		}
		else if( dataType == "uint12" )
		{
			spec->set_format( TypeDesc::UINT16 );
			spec->attribute ("oiio:BitsPerSample", 12);
		}
	}
	else if( fileFormatName == "png" )
	{
		spec->attribute( "png:compressionLevel", optionsPlug->getChild<IntPlug>( g_compressionLevelPlugName )->getValue() );
	}
	else if( fileFormatName == "webp" )
	{
		spec->attribute( "CompressionQuality", optionsPlug->getChild<IntPlug>( g_compressionQualityPlugName )->getValue() );
	}
}

ImageSpec createImageSpec( const ImageWriter *node, const ImageOutput *out, const Imath::Box2i &dataWindow, const Imath::Box2i &displayWindow )
{
	const std::string fileFormatName = out->format_name();
	const bool supportsDisplayWindow = out->supports( "displaywindow" ) && fileFormatName != "dpx";

	ImageSpec spec( TypeDesc::UNKNOWN );

	// Specify the display window.
	spec.full_x = displayWindow.min.x;
	spec.full_y = displayWindow.min.y;
	spec.full_width = displayWindow.size().x + 1;
	spec.full_height = displayWindow.size().y + 1;

	if ( supportsDisplayWindow )
	{
		spec.x = dataWindow.min.x;
		spec.y = dataWindow.min.y;
		spec.width = dataWindow.size().x + 1;
		spec.height = dataWindow.size().y + 1;
	}
	else
	{
		spec.x = spec.full_x;
		spec.y = spec.full_y;
		spec.width = spec.full_width;
		spec.height = spec.full_height;
	}

	// Add the metadata to the spec, removing metadata that could affect the resulting channel data,
	// and file-format-specific metadata created by the OpenImageIOReader.
	CompoundDataPtr metadata = node->inPlug()->metadataPlug()->getValue()->copy();

	metadata->writable().erase( "oiio:ColorSpace" );
	metadata->writable().erase( "oiio:Gamma" );
	metadata->writable().erase( "oiio:UnassociatedAlpha" );
	metadata->writable().erase( "fileFormat" );
	metadata->writable().erase( "dataType" );

	metadataToImageSpecAttributes( metadata.get(), spec );

	// Apply the spec format options. Note this must happen
	// after we transfer the input metadata to ensure the
	// settings override anything from upstream data.
	setImageSpecFormatOptions( node, &spec, fileFormatName );

	// Add common attribs to the spec
	spec.attribute( "Software", std::string( "Gaffer " ) + Gaffer::versionString() );
#ifndef _MSC_VER
	struct utsname info;
	if ( !uname( &info ) )
	{
		spec.attribute( "HostComputer", info.nodename );
	}
	if ( const char *artist = getenv( "USER" ) )
	{
		spec.attribute( "Artist", artist );
	}
#else
	char computerName[MAX_COMPUTERNAME_LENGTH + 1];
	DWORD computerNameSize = sizeof( computerName ) / sizeof( computerName[0] );
	bool computerNameSuccess = GetComputerNameA( computerName, &computerNameSize );
	if( computerNameSuccess )
	{
		spec.attribute("HostComputer", computerName );
	}
	if ( const char *artist = getenv( "USERNAME" ) )
	{
		spec.attribute( "Artist", artist );
	}
#endif
	std::string document = "untitled";
	if ( const ScriptNode *script = node->ancestor<ScriptNode>() )
	{
		const std::string scriptFile = script->fileNamePlug()->getValue();
		document = ( scriptFile == "" ) ? document : scriptFile;
	}
	spec.attribute( "DocumentName", document );

	// PixelAspectRatio must be defined by the FormatPlug
	spec.attribute( "PixelAspectRatio", (float)node->inPlug()->formatPlug()->getValue().getPixelAspect() );

	return spec;
}

// Remove leading, trailing, or repeated dot seperators
std::string cleanExcessDots( std::string name )
{
	auto last = std::unique( name.begin(), name.end(), []( char a, char b ) {
		return a == '.' && b == '.';
	} );
	name.erase( last, name.end() );

	boost::trim_right_if( name, boost::is_any_of(".") );
	boost::trim_left_if( name, boost::is_any_of(".") );

	return name;
}

// Get the EXR names for the view, part, and channel for a Gaffer channel
std::tuple< std::string, std::string, std::string > viewPartChannelName( const ImageWriter *node, const std::string &view, const std::string &gafferChannel )
{
	std::string layer = ImageAlgo::layerName( gafferChannel );
	std::string baseName = ImageAlgo::baseName( gafferChannel );

	std::string nukeViewName = view;
	if( nukeViewName == "" )
	{
		nukeViewName = "main";
	}

	// "imageWriter:nukeBaseName" is a base channel name matching Nuke - in complete contradiction to the spec,
	// layers other than the main one have the channel names RGBA written as "red", "green", "blue", "alpha"
	string nukeBaseName = baseName;
	string nukeLayerName = layer;
	if( layer.size() )
	{
		if( nukeBaseName == "R" ) nukeBaseName = "red";
		else if( nukeBaseName == "G" ) nukeBaseName = "green";
		else if( nukeBaseName == "B" ) nukeBaseName = "blue";
		else if( nukeBaseName == "A" ) nukeBaseName = "alpha";
	}
	else
	{
		if( baseName == "Z" )
		{
			nukeLayerName = "depth";
		}
		else if(
			baseName == "R" ||
			baseName == "G" ||
			baseName == "B" ||
			baseName == "A"
		)
		{
			// Nuke actually lets these layers be in the default part
		}
		else
		{
			nukeLayerName = "other";
		}
	}

	// For use in naming parts, it's useful to have a layer name that is set to "rgba" for channels that
	// are in the default layer.
	std::string standardPartName = layer.size() ? layer : "rgba";
	std::string nukePartName = nukeLayerName.size() ? nukeLayerName : "rgba";

	Context::EditableScope namingContext( Context::current() );
	namingContext.set( "imageWriter:viewName", &view );
	namingContext.set( "imageWriter:channelName", &gafferChannel );
	namingContext.set( "imageWriter:standardPartName", &standardPartName );
	namingContext.set( "imageWriter:layerName", &layer );
	namingContext.set( "imageWriter:baseName", &baseName );
	namingContext.set( "imageWriter:nukeViewName", &nukeViewName );
	namingContext.set( "imageWriter:nukePartName", &nukePartName );
	namingContext.set( "imageWriter:nukeLayerName", &nukeLayerName );
	namingContext.set( "imageWriter:nukeBaseName", &nukeBaseName );

	return std::make_tuple(
		cleanExcessDots( node->layoutViewNamePlug()->getValue() ),
		cleanExcessDots( node->layoutPartNamePlug()->getValue() ),
		cleanExcessDots( node->layoutChannelNamePlug()->getValue() )
	);
}

struct MetadataRegistration
{
	void registerPreset( const std::string &name, const std::string &view, const std::string &part, const std::string &channel )
	{
		Gaffer::Metadata::registerValue( ImageWriter::staticTypeId(), "layout.viewName", name, new IECore::StringData( view ) );
		Gaffer::Metadata::registerValue( ImageWriter::staticTypeId(), "layout.partName", name, new IECore::StringData( part ) );
		Gaffer::Metadata::registerValue( ImageWriter::staticTypeId(), "layout.channelName", name, new IECore::StringData( channel ) );
	}

	MetadataRegistration()
	{
		// These presets are useful in testing and scripting when the UI isn't loaded, so we register
		// them here instead of in the UI file

		registerPreset( "preset:Part per Layer",
			"${imageWriter:viewName}",
			"${imageWriter:standardPartName}.${imageWriter:viewName}",
			"${imageWriter:layerName}.${imageWriter:baseName}"
		);

		registerPreset( "preset:Part per View",
			"${imageWriter:viewName}",
			"${imageWriter:viewName}",
			"${imageWriter:layerName}.${imageWriter:baseName}"
		);

		registerPreset( "preset:Single Part",
			"",
			"",
			"${imageWriter:layerName}.${imageWriter:viewName}.${imageWriter:baseName}"
		);

		registerPreset( "preset:Nuke/Interleave Channels",
			"${imageWriter:viewName}",
			"${imageWriter:nukePartName}.${imageWriter:nukeViewName}",
			"${imageWriter:nukeBaseName}"
		);

		registerPreset( "preset:Nuke/Interleave Channels and Layers",
			"${imageWriter:viewName}",
			"${imageWriter:nukeViewName}",
			"${imageWriter:nukeLayerName}.${imageWriter:nukeBaseName}"
		);

		registerPreset( "preset:Nuke/Interleave Channels, Layers and Views",
			"",
			"",
			"${imageWriter:viewName}.${imageWriter:nukeLayerName}.${imageWriter:nukeBaseName}"
		);
	}
};

MetadataRegistration g_metadataRegistration;

} // namespace

//////////////////////////////////////////////////////////////////////////
// ImageWriter implementation
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( ImageWriter );

size_t ImageWriter::g_firstPlugIndex = 0;

ImageWriter::ImageWriter( const std::string &name )
	:	TaskNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ImagePlug( "in" ) );
	addChild( new StringPlug( "fileName" ) );
	addChild( new StringPlug( "channels", Gaffer::Plug::In, "*" ) );
	addChild( new StringPlug( "colorSpace" ) );
	addChild( new ImagePlug( "out", Plug::Out, Plug::Default & ~Plug::Serialisable ) );
	outPlug()->setInput( inPlug() );

	ColorSpacePtr colorSpaceUnpremultedChild = new ColorSpace( "__colorSpaceUnpremulted" );
	colorSpaceUnpremultedChild->processUnpremultipliedPlug()->setValue( true );
	addChild( colorSpaceUnpremultedChild );

	ColorSpacePtr colorSpaceChild = new ColorSpace( "__colorSpace" );
	addChild( colorSpaceChild );

	OCIO_NAMESPACE::ConstConfigRcPtr config = OCIO_NAMESPACE::GetCurrentConfig();
	colorSpaceUnpremultedChild->inputSpacePlug()->setValue( config->getColorSpace( OCIO_NAMESPACE::ROLE_SCENE_LINEAR )->getName() );
	colorSpaceUnpremultedChild->inPlug()->setInput( inPlug() );
	colorSpaceUnpremultedChild->outputSpacePlug()->setValue( "${__imageWriter:colorSpace}" );

	colorSpaceChild->inputSpacePlug()->setValue( config->getColorSpace( OCIO_NAMESPACE::ROLE_SCENE_LINEAR )->getName() );
	colorSpaceChild->inPlug()->setInput( inPlug() );

	colorSpaceChild->outputSpacePlug()->setValue( "${__imageWriter:colorSpace}" );

	ValuePlugPtr layoutPlug = new ValuePlug( "layout" );
	layoutPlug->addChild( new StringPlug( "viewName", Plug::In, "${imageWriter:viewName}" ) );
	layoutPlug->addChild( new StringPlug( "partName", Plug::In, "${imageWriter:standardPartName}.${imageWriter:viewName}" ) );
	layoutPlug->addChild( new StringPlug( "channelName", Plug::In, "${imageWriter:layerName}.${imageWriter:baseName}" ) );
	addChild( layoutPlug );

	createFileFormatOptionsPlugs();
}

ImageWriter::~ImageWriter()
{
}

void ImageWriter::createFileFormatOptionsPlugs()
{
	ValuePlug *exrOptionsPlug = new ValuePlug( "openexr" );
	addChild( exrOptionsPlug );
	exrOptionsPlug->addChild( new IntPlug( g_modePlugName, Plug::In, Scanline ) );
	exrOptionsPlug->addChild( new StringPlug( g_compressionPlugName, Plug::In, "zips" ) );
	// OIIO clamps to the 10-250000 range, so don't allow the authoring of values outside that range.
	exrOptionsPlug->addChild( new FloatPlug( g_dwaCompressionLevelPlugName, Plug::In, 45, 10, 250000 ) );
	exrOptionsPlug->addChild( new StringPlug( g_dataTypePlugName, Plug::In, "half" ) );
	exrOptionsPlug->addChild( new StringPlug( g_depthDataTypePlugName, Plug::In, "float" ) );

	ValuePlug *dpxOptionsPlug = new ValuePlug( "dpx" );
	addChild( dpxOptionsPlug );
	dpxOptionsPlug->addChild( new StringPlug( g_dataTypePlugName, Plug::In, "uint10" ) );

	ValuePlug *tifOptionsPlug = new ValuePlug( "tiff" );
	addChild( tifOptionsPlug );
	tifOptionsPlug->addChild( new IntPlug( g_modePlugName, Plug::In, Scanline ) );
	tifOptionsPlug->addChild( new StringPlug( g_compressionPlugName, Plug::In, "zip" ) );
	tifOptionsPlug->addChild( new StringPlug( g_dataTypePlugName, Plug::In, "uint8" ) );

	ValuePlug *f3dOptionsPlug = new ValuePlug( "field3d" );
	addChild( f3dOptionsPlug );
	f3dOptionsPlug->addChild( new IntPlug( g_modePlugName, Plug::In, Scanline ) );
	f3dOptionsPlug->addChild( new StringPlug( g_dataTypePlugName, Plug::In, "float" ) );

	ValuePlug *fitsOptionsPlug = new ValuePlug( "fits" );
	addChild( fitsOptionsPlug );
	fitsOptionsPlug->addChild( new StringPlug( g_dataTypePlugName, Plug::In, "float" ) );

	ValuePlug *iffOptionsPlug = new ValuePlug( "iff" );
	addChild( iffOptionsPlug );
	iffOptionsPlug->addChild( new IntPlug( g_modePlugName, Plug::In, Tile ) );

	ValuePlug *jpgOptionsPlug = new ValuePlug( "jpeg" );
	addChild( jpgOptionsPlug );
	jpgOptionsPlug->addChild( new IntPlug( g_compressionQualityPlugName, Plug::In, 98, 0, 100 ) );
	jpgOptionsPlug->addChild( new StringPlug( g_chromaSubSamplingPlugName ) );

	ValuePlug *jpeg2000OptionsPlug = new ValuePlug( "jpeg2000" );
	addChild( jpeg2000OptionsPlug );
	jpeg2000OptionsPlug->addChild( new StringPlug( g_dataTypePlugName, Plug::In, "uint8" ) );

	ValuePlug *pngOptionsPlug = new ValuePlug( "png" );
	addChild( pngOptionsPlug );
	pngOptionsPlug->addChild( new StringPlug( g_compressionPlugName, Plug::In, "filtered" ) );
	pngOptionsPlug->addChild( new IntPlug( g_compressionLevelPlugName, Plug::In, 6, Z_NO_COMPRESSION, Z_BEST_COMPRESSION ) );

	ValuePlug *rlaOptionsPlug = new ValuePlug( "rla" );
	addChild( rlaOptionsPlug );
	rlaOptionsPlug->addChild( new StringPlug( g_dataTypePlugName, Plug::In, "uint8" ) );

	ValuePlug *sgiOptionsPlug = new ValuePlug( "sgi" );
	addChild( sgiOptionsPlug );
	sgiOptionsPlug->addChild( new StringPlug( g_dataTypePlugName, Plug::In, "uint8" ) );

	ValuePlug *targaOptionsPlug = new ValuePlug( "targa" );
	addChild( targaOptionsPlug );
	targaOptionsPlug->addChild( new StringPlug( g_compressionPlugName, Plug::In, "rle" ) );

	ValuePlug *webpOptionsPlug = new ValuePlug( "webp" );
	addChild( webpOptionsPlug );
	webpOptionsPlug->addChild( new IntPlug( g_compressionQualityPlugName, Plug::In, 100, 0, 100 ) );
}

GafferImage::ImagePlug *ImageWriter::inPlug()
{
	return getChild<ImagePlug>( g_firstPlugIndex );
}

const GafferImage::ImagePlug *ImageWriter::inPlug() const
{
	return getChild<ImagePlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *ImageWriter::fileNamePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex+1 );
}

const Gaffer::StringPlug *ImageWriter::fileNamePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex+1 );
}

Gaffer::StringPlug *ImageWriter::channelsPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex+2 );
}

const Gaffer::StringPlug *ImageWriter::channelsPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex+2 );
}

Gaffer::StringPlug *ImageWriter::colorSpacePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex+3 );
}

const Gaffer::StringPlug *ImageWriter::colorSpacePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex+3 );
}

GafferImage::ImagePlug *ImageWriter::outPlug()
{
	return getChild<ImagePlug>( g_firstPlugIndex+4 );
}

const GafferImage::ImagePlug *ImageWriter::outPlug() const
{
	return getChild<ImagePlug>( g_firstPlugIndex+4 );
}

GafferImage::ColorSpace *ImageWriter::colorSpaceUnpremultedNode()
{
	return getChild<ColorSpace>( g_firstPlugIndex+5 );
}

const GafferImage::ColorSpace *ImageWriter::colorSpaceUnpremultedNode() const
{
	return getChild<ColorSpace>( g_firstPlugIndex+5 );
}

GafferImage::ColorSpace *ImageWriter::colorSpaceNode()
{
	return getChild<ColorSpace>( g_firstPlugIndex+6 );
}

const GafferImage::ColorSpace *ImageWriter::colorSpaceNode() const
{
	return getChild<ColorSpace>( g_firstPlugIndex+6 );
}

Gaffer::StringPlug *ImageWriter::layoutViewNamePlug()
{
	return getChild<ValuePlug>( g_firstPlugIndex+7 )->getChild<StringPlug>( 0 );
}

const Gaffer::StringPlug *ImageWriter::layoutViewNamePlug() const
{
	return getChild<ValuePlug>( g_firstPlugIndex+7 )->getChild<StringPlug>( 0 );
}

Gaffer::StringPlug *ImageWriter::layoutPartNamePlug()
{
	return getChild<ValuePlug>( g_firstPlugIndex+7 )->getChild<StringPlug>( 1 );
}

const Gaffer::StringPlug *ImageWriter::layoutPartNamePlug() const
{
	return getChild<ValuePlug>( g_firstPlugIndex+7 )->getChild<StringPlug>( 1 );
}

Gaffer::StringPlug *ImageWriter::layoutChannelNamePlug()
{
	return getChild<ValuePlug>( g_firstPlugIndex+7 )->getChild<StringPlug>( 2 );
}

const Gaffer::StringPlug *ImageWriter::layoutChannelNamePlug() const
{
	return getChild<ValuePlug>( g_firstPlugIndex+7 )->getChild<StringPlug>( 2 );
}

Gaffer::ValuePlug *ImageWriter::fileFormatSettingsPlug( const std::string &fileFormat )
{
	return getChild<ValuePlug>( fileFormat );
}

const Gaffer::ValuePlug *ImageWriter::fileFormatSettingsPlug( const std::string &fileFormat ) const
{
	return getChild<ValuePlug>( fileFormat );
}

const std::string ImageWriter::currentFileFormat() const
{
	const std::string fileName = Context::current()->substitute( fileNamePlug()->getValue() );
	ImageOutputPtr out( ImageOutput::create( fileName.c_str() ) );
	if( out != nullptr )
	{
		return out->format_name();
	}
	else
	{
		return "";
	}
}

void ImageWriter::setDefaultColorSpaceFunction( DefaultColorSpaceFunction f )
{
	defaultColorSpaceFunction() = f;
}

ImageWriter::DefaultColorSpaceFunction ImageWriter::getDefaultColorSpaceFunction()
{
	return defaultColorSpaceFunction();
}

ImageWriter::DefaultColorSpaceFunction &ImageWriter::defaultColorSpaceFunction()
{
	// We deliberately make no attempt to free this, because typically a python
	// function is registered here, and we can't free that at exit because python
	// is already shut down by then.
	static DefaultColorSpaceFunction *g_colorSpaceFunction = new DefaultColorSpaceFunction;
	return *g_colorSpaceFunction;
}

std::string ImageWriter::colorSpace() const
{
	std::string colorSpace = colorSpacePlug()->getValue();
	if( colorSpace != "" )
	{
		return colorSpace;
	}

	const std::string fileFormat = currentFileFormat();
	if( fileFormat.empty() )
	{
		return "";
	}

	std::string dataType;
	if( const ValuePlug *optionsPlug = this->getChild<ValuePlug>( fileFormat ) )
	{
		if( const StringPlug *dataTypePlug = optionsPlug->getChild<StringPlug>( g_dataTypePlugName ) )
		{
			dataType = dataTypePlug->getValue();
		}
	}

	ConstCompoundDataPtr metadata = inPlug()->metadataPlug()->getValue();

	return defaultColorSpaceFunction()(
		fileNamePlug()->getValue(),
		fileFormat,
		dataType,
		metadata.get()
	);
}

IECore::MurmurHash ImageWriter::hash( const Context *context ) const
{
	Context::Scope scope( context );
	if ( ( fileNamePlug()->getValue() == "" ) || inPlug()->source<ImagePlug>() == inPlug() )
	{
		return IECore::MurmurHash();
	}

	IECore::MurmurHash h = TaskNode::hash( context );
	h.append( fileNamePlug()->hash() );
	h.append( channelsPlug()->hash() );
	h.append( colorSpacePlug()->hash() );
	const std::string fileFormat = currentFileFormat();

	if( fileFormat != "" )
	{
		const ValuePlug *fmtSettingsPlug = fileFormatSettingsPlug( fileFormat );
		if( fmtSettingsPlug != nullptr )
		{
			h.append( fmtSettingsPlug->hash() );
		}
	}

	return h;
}

void ImageWriter::execute() const
{
	// Set up a context to pass the right colorspace to
	// `colorSpaceNode()`.

	Context::EditableScope colorSpaceScope( Context::current() );
	std::string colorSpaceStr = colorSpace();
	colorSpaceScope.set( "__imageWriter:colorSpace", &colorSpaceStr );

	// Create an OIIO::ImageOutput

	if( !inPlug()->getInput<ImagePlug>() )
	{
		throw IECore::Exception( "No input image." );
	}

	const std::string fileName = fileNamePlug()->getValue();

	ImageOutputPtr out( ImageOutput::create( fileName.c_str() ) );
	if( !out )
	{
		throw IECore::Exception( OIIO::geterror() );
	}

	bool deep = inPlug()->deep();
	if( deep && !out->supports( "deepdata" ) )
	{
		throw IECore::Exception( boost::str( boost::format( "Deep data is not supported by %s files." ) % out->format_name() ) );
	}

	// Create an OIIO::ImageSpec describing what we'll write
	const Format imageFormat = inPlug()->formatPlug()->getValue();
	const Imath::Box2i dataWindow = inPlug()->dataWindowPlug()->getValue();
	Imath::Box2i exrDataWindow;

	if( !BufferAlgo::empty( dataWindow ) )
	{
		exrDataWindow = imageFormat.toEXRSpace( dataWindow );
	}
	else
	{
		// Exr doesn't allow images with no pixel, so if the actual data window is empty,
		// we make one pixel at the origin
		exrDataWindow = Imath::Box2i( Imath::V2i( 0 ) );
	}

	const Imath::Box2i exrDisplayWindow = imageFormat.toEXRSpace( imageFormat.getDisplayWindow() );

	ImageSpec spec = createImageSpec( this, out.get(), exrDataWindow, exrDisplayWindow );
	spec.deep = deep;

	// Decide what channels to write and update the spec with them

	IECore::ConstStringVectorDataPtr channelNamesData = inPlug()->channelNamesPlug()->getValue();
	const vector<string> &channelNames = channelNamesData->readable();
	const string channels = channelsPlug()->getValue();

	const bool supportsNChannels = out->supports( "nchannels" );
	const bool supportsAlpha = out->supports( "alpha" );

	vector<string> channelsToWrite;
	for( vector<string>::const_iterator it = channelNames.begin(), eIt = channelNames.end(); it != eIt; ++it )
	{
		if( !StringAlgo::matchMultiple( *it, channels ) )
		{
			continue;
		}
		if( !supportsNChannels && *it != "R" && *it != "G" && *it != "B" && *it != "A" )
		{
			continue;
		}
		if( !supportsAlpha && *it == "A" )
		{
			continue;
		}
		channelsToWrite.push_back( *it );
	}

	if( channelsToWrite.empty() )
	{
		throw IECore::Exception( "No channels to write" );
	}

	// Sort the channel names so that they get written in a consistent order, with the
	// basic RGBA channels coming first
	ImageAlgo::sortChannelNames( channelsToWrite );

	// Create the directory we need and open the file

	boost::filesystem::path directory = boost::filesystem::path( fileName ).parent_path();
	if( !directory.empty() )
	{
		boost::filesystem::create_directories( directory );
	}

	// Write out the channel data

	const Imath::Box2i extImageDataWindow( Imath::V2i( spec.x, spec.y ), Imath::V2i( spec.x + spec.width - 1, spec.y + spec.height - 1 ) );
	const Imath::Box2i imageDataWindow( imageFormat.fromEXRSpace( extImageDataWindow ) );
	const Imath::Box2i processDataWindow( BufferAlgo::intersection( imageDataWindow, dataWindow ) );

	struct Part
	{
		std::string name;
		std::string view;
		std::vector< std::string > channels;
		std::vector< std::string > channelNames;
	};

	std::vector< Part > parts;

	std::string currentView = "";

	for( const string &i : channelsToWrite )
	{
		const auto & [ viewName, partName, channelName ] = viewPartChannelName( this, currentView, i );

		// Note that `partName = partName` is a hack to get around an issue with capturing from a
		// structured binding.  GCC allows it, but the C++17 spec doesn't, and it doesn't work in our
		// Mac compiler.  Once we're on C++20, it is explicitly supported, and we can remove the ` = partName`
		size_t partIndex = std::distance(
			parts.begin(),
			std::find_if( parts.begin(), parts.end(), [partName = partName] (Part const& p) { return p.name == partName; } )
		);

		if( partIndex >= parts.size() )
		{
			parts.push_back( { partName, viewName, {}, {} } );
		}
		else
		{
			if( parts[partIndex].view != viewName )
			{
				throw IECore::Exception( boost::str( boost::format( "Cannot write views \"%s\" and \"%s\" both to image part \"%s\"" ) % parts[partIndex].view % viewName % partName ) );
			}
		}

		parts[ partIndex ].channels.push_back( i );
		parts[ partIndex ].channelNames.push_back( channelName );
	}

	if( parts.size() > 1 && !out->supports( "multiimage" ) )
	{
		throw IECore::Exception( boost::str( boost::format( "Cannot write multiple parts to this image format: \"%s\"" ) % fileName ) );
	}

	bool hasAlpha = false;
	std::vector< ImageSpec > specs;
	for( const Part &part : parts )
	{
		specs.push_back( spec );
		if( part.view.size() )
		{
			specs.back().attribute("view", part.view );
		}
		if( part.name.size() )
		{
			specs.back().attribute("oiio:subimagename", part.name );
		}
		specs.back().nchannels = part.channels.size();
		specs.back().channelnames.clear();
		for( size_t channelIndex = 0; channelIndex < part.channelNames.size(); channelIndex++ )
		{
			const std::string& channelName = part.channelNames[channelIndex];
			specs.back().channelnames.push_back( channelName );
			// OIIO has a special attribute for the Alpha and Z channels. If we find some, we should tag them...
			if( channelName == "A" )
			{
				hasAlpha = true;
				specs.back().alpha_channel = channelIndex;
			}
			else if( channelName == "Z" )
			{
				specs.back().z_channel = channelIndex;
			}
		}

		setImageSpecFormatChannelOptions( this, &specs.back(), out->format_name() );
	}

	const ColorSpace *appropriateColorSpaceNode = hasAlpha ? colorSpaceUnpremultedNode() : colorSpaceNode();

	bool success;
	if( parts.size() > 1 )
	{
		success = out->open( fileName, specs.size(), &specs[0] );
	}
	else
	{
		success = out->open( fileName, specs[0] );
	}

	if( success )
	{
		IECore::msg( IECore::MessageHandler::Info, this->relativeName( this->scriptNode() ), "Writing " + fileName );
	}
	else
	{
		throw IECore::Exception( boost::str( boost::format( "Could not open \"%s\", error = %s" ) % fileName % out->geterror() ) );
	}

	for( size_t partIndex = 0; partIndex < parts.size(); partIndex++ )
	{
		if( partIndex != 0 )
		{
			out->open( fileName, specs[partIndex], ImageOutput::AppendSubimage );
		}

		if( !deep )
		{
			TileChannelDataProcessor processor;

			if ( specs[partIndex].tile_width == 0 )
			{
				FlatScanlineWriter flatScanlineWriter( out, fileName, processDataWindow, imageFormat, parts[partIndex].channels );
				ImageAlgo::parallelGatherTiles( appropriateColorSpaceNode->outPlug(), parts[partIndex].channels, processor, flatScanlineWriter, processDataWindow, ImageAlgo::TopToBottom );
				flatScanlineWriter.finish();
			}
			else
			{
				FlatTileWriter flatTileWriter( out, fileName, processDataWindow, imageFormat, parts[partIndex].channels );
				ImageAlgo::parallelGatherTiles( appropriateColorSpaceNode->outPlug(), parts[partIndex].channels, processor, flatTileWriter, processDataWindow, ImageAlgo::TopToBottom );
				flatTileWriter.finish();
			}

		}
		else
		{
			TileSampleOffsetsProcessor sampleOffsetsProcessor;

			SampleOffsetsAccumulator sampleOffsetsAccumulator;
			ImageAlgo::parallelGatherTiles( appropriateColorSpaceNode->outPlug(), sampleOffsetsProcessor, sampleOffsetsAccumulator, processDataWindow );

			TileChannelDataProcessor channelDataProcessor = TileChannelDataProcessor();

			if( specs[partIndex].tile_width == 0 )
			{
				DeepScanlineWriter deepScanlineWriter( out, fileName, processDataWindow, imageFormat, parts[partIndex].channels, sampleOffsetsAccumulator.m_sampleOffsets );
				ImageAlgo::parallelGatherTiles( appropriateColorSpaceNode->outPlug(), parts[partIndex].channels, channelDataProcessor, deepScanlineWriter, processDataWindow, ImageAlgo::TopToBottom );
			}
			else
			{
				DeepTileWriter deepTileWriter( out, fileName, processDataWindow, imageFormat, parts[partIndex].channels, sampleOffsetsAccumulator.m_sampleOffsets );
				ImageAlgo::parallelGatherTiles( appropriateColorSpaceNode->outPlug(), parts[partIndex].channels, channelDataProcessor, deepTileWriter, processDataWindow, ImageAlgo::TopToBottom );
			}
		}
	}

	out->close();
}
